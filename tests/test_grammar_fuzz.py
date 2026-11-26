# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The grammar reads every string the frozen pyparsing grammars read, as the tree they built.

Where pyparsing built a tree, the package builds the same one. The package
has one grammar and one parser where pyparsing had two of each, and it
decides less: what a term may be where it stands is resolution's to say. So
a string pyparsing refused is refused here, or is one [`rearranged`][]
finds no new token in: parentheses around a term pyparsing read only bare, a
keyword written before the condition a call reads, or a term of a kind its
place does not take, such as a label in a sum or ``<`` in a constraint,
which resolution refuses (``tests/test_validation.py`` holds it to that).

Three more differences are deliberate, and [`excused`][] names each:

- a number written against a name is refused, as ``1.AND`` and ``٣AND``,
  which pyparsing read where it refused ``0AND``;

- a string pyparsing ran out of stack on is read, and held to the depth cap
  (#1041);
- a string that uses ``AND``, ``OR``, ``NOT``, ``True`` or ``False``, in any
  case, as a name reads it as the word, since those words are reserved
  (#1040) and no entry has one as its name (#1054).

The strings are seeded, so a failure names a string that fails again. Set
``MATHSPEC_GRAMMAR_FUZZ`` to a number of rounds to run more of them than the
suite does.
"""

from __future__ import annotations

import dataclasses
import itertools
import os
import re
from collections import Counter
from collections.abc import Iterator, Mapping
from random import Random

import pytest

from mathspec._grammar import NAME, RESERVED, _parser, parse
from mathspec.errors import SchemaError
from tests.grammar.generate import TOKEN, example_strings, nested_shapes, strings
from tests.grammar.oracle import Grammar, Refused, oracle

ROUNDS = int(os.environ.get('MATHSPEC_GRAMMAR_FUZZ', '1'))

CHUNKS = 16

PER_CHUNK = 400

GRAMMARS: tuple[Grammar, ...] = ('expression', 'condition')

NAME_FIELDS = frozenset({'name', 'relation', 'columns', 'names'})

NUMBER = re.compile(r'\d+\.?\d*(?:[eE][+-]?\d+)?|\.inf')

WORD = re.compile(NAME)


def package(text: str) -> object:
    """What the package's parser makes of *text*, past its memo, in the oracle's terms. It reads both grammars' strings."""
    try:
        return parse.__wrapped__(text)
    except SchemaError as error:
        return Refused('too deep' if 'levels the language admits' in str(error) else 'syntax')


def shape(node: object) -> object:
    """*node* as nested tuples of type names and values, so a keyword's order and a number's type count too."""
    if isinstance(node, Refused):
        return ('refused', 'too deep' if node.why == 'out of stack' else node.why)
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        return (type(node).__name__, *(shape(getattr(node, field.name)) for field in dataclasses.fields(node)))
    if isinstance(node, Mapping):
        return tuple((key, shape(value)) for key, value in node.items())
    if isinstance(node, tuple):
        return tuple(shape(item) for item in node)
    return (type(node).__name__, repr(node))


def names_in(node: object) -> Iterator[str]:
    """Every name *node* holds: of an entry, a callee, a keyword, a relation or a column."""
    if isinstance(node, Mapping):
        for key, value in node.items():
            yield key
            yield from names_in(value)
    elif isinstance(node, tuple):
        for item in node:
            yield from names_in(item)
    elif dataclasses.is_dataclass(node) and not isinstance(node, type):
        for field in dataclasses.fields(node):
            value = getattr(node, field.name)
            if field.name in NAME_FIELDS and isinstance(value, str):
                yield value
            elif field.name in NAME_FIELDS and isinstance(value, tuple):
                yield from value
            else:
                yield from names_in(value)


def rearranged(grammar: Grammar, text: str) -> bool:
    """Whether the package read *text*, which the oracle refuses, out of tokens the oracle knows.

    The package's own tokens are written back with a space between each, and
    the oracle refuses that string too: the tokens are arranged as pyparsing
    did not allow. Were it to read the string, the package would have found
    a token in *text* where pyparsing has none.
    """
    tokens = _parser().lex(text)
    return isinstance(oracle(grammar, ' '.join(text[token.start_pos : token.end_pos] for token in tokens)), Refused)


def against_a_name(text: str) -> bool:
    """Whether *text* writes a number directly before a name, or ``.inf`` directly against one, by the generator's own tokens."""
    tokens = TOKEN.findall(text)
    return any(
        (NUMBER.fullmatch(left) and WORD.fullmatch(right)) or (WORD.fullmatch(left) and right == '.inf')
        for left, right in itertools.pairwise(tokens)
    )


def excused(grammar: Grammar, text: str, old: object, new: object) -> bool:
    """Whether the two part in one of the ways the module docstring names."""
    if isinstance(old, Refused) and old.why == 'out of stack':
        return True
    if old == Refused('syntax') and not isinstance(new, Refused):
        return rearranged(grammar, text)
    if isinstance(old, Refused) or new == Refused('too deep'):
        return False
    if new == Refused('syntax') and against_a_name(text):
        return True
    return any(name.upper() in RESERVED for name in names_in(old))


def disagreement(grammar: Grammar, text: str) -> str | None:
    """Where the package and the oracle part on *text*, outside the excused differences, as a line to print."""
    old, new = oracle(grammar, text), package(text)
    if shape(old) == shape(new) or excused(grammar, text, old, new):
        return None
    return f'{grammar} {text!r}\n    oracle:  {old!r}\n    package: {new!r}'


def _report(found: list[str]) -> str:
    shown = '\n'.join(found[:12])
    return f'{len(found)} strings read differently, the first {min(len(found), 12)}:\n{shown}'


def test_every_string_in_the_examples_reads_as_the_oracle_reads_it():
    found = [line for text in example_strings() for grammar in GRAMMARS if (line := disagreement(grammar, text))]
    assert not found, _report(found)


@pytest.mark.parametrize('chunk', range(CHUNKS))
def test_written_and_mutated_strings_read_as_the_oracle_reads_them(chunk):
    found = []
    for round_ in range(ROUNDS):
        for grammar, text in strings(Random(f'{round_}:{chunk}'), PER_CHUNK):
            if line := disagreement(grammar, text):
                found.append(line)
    assert not found, _report(found)


@pytest.mark.parametrize('grammar', GRAMMARS)
def test_each_way_of_nesting_stops_where_the_oracle_stops(grammar):
    """The seeded strings land on the cap itself too rarely to pin it, so each shape is read at either side of it."""
    found = [
        line for n in range(98, 103) for text in nested_shapes(grammar, n) if (line := disagreement(grammar, text))
    ]
    assert not found, _report(found)


def test_the_strings_reach_both_trees_and_refusals():
    """A fuzzer whose strings all fail to parse compares only refusals; one whose strings all parse never sees one."""
    tally: Counter[tuple[Grammar, bool]] = Counter()
    for grammar, text in strings(Random('reach'), PER_CHUNK):
        tally[grammar, isinstance(oracle(grammar, text), Refused)] += 1
    for grammar in GRAMMARS:
        trees, refusals = tally[grammar, False], tally[grammar, True]
        assert trees >= PER_CHUNK // 4, f'{grammar}: {trees} of {PER_CHUNK} strings parse, under a quarter'
        assert refusals >= PER_CHUNK // 4, f'{grammar}: {refusals} of {PER_CHUNK} strings are refused, under a quarter'


def test_the_examples_give_the_fuzzer_real_strings():
    """The corpus is read off the YAML without the parser, so a broken walk would leave it with prose alone."""
    parsed = Counter(
        grammar for text in example_strings() for grammar in GRAMMARS if not isinstance(oracle(grammar, text), Refused)
    )
    assert parsed['expression'] >= 300, f'{parsed["expression"]} example strings parse as expressions, under 300'
    assert parsed['condition'] >= 300, f'{parsed["condition"]} example strings parse as conditions, under 300'
