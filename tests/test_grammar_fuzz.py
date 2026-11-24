# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Both grammars read every string as the frozen pyparsing grammars do: the same tree, or a refusal for the same cause.

The strings are seeded, so a failure names a string that fails again. Set
``MATHSPEC_GRAMMAR_FUZZ`` to a number of rounds to run more of them than the
suite does.
"""

from __future__ import annotations

import dataclasses
import os
from collections import Counter
from collections.abc import Mapping
from random import Random

import pytest

from mathspec._condition_parser import parse_condition
from mathspec._expression_parser import parse_expression
from mathspec.errors import SchemaError
from tests.grammar.generate import example_strings, nested_shapes, strings
from tests.grammar.oracle import Grammar, Refused, oracle

ROUNDS = int(os.environ.get('MATHSPEC_GRAMMAR_FUZZ', '1'))

CHUNKS = 16

PER_CHUNK = 400

GRAMMARS: tuple[Grammar, ...] = ('expression', 'condition')


def package(grammar: Grammar, text: str) -> object:
    """What the package's own parser makes of *text*, past its memo, in the oracle's terms."""
    parse = parse_expression if grammar == 'expression' else parse_condition
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


def disagreement(grammar: Grammar, text: str) -> str | None:
    """Where the package and the oracle part on *text*, as a line to print, or ``None``."""
    old, new = oracle(grammar, text), package(grammar, text)
    if shape(old) == shape(new):
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
