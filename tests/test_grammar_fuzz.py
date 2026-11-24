# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Both grammars read every string as the frozen pyparsing grammars do: the same tree, or a refusal for the same cause.

Three differences are deliberate, and [`excused`][] names each:

- a string pyparsing ran out of stack on is read, and held to the depth cap
  (#1041);
- a where string that uses ``AND``, ``OR``, ``NOT``, ``True`` or ``False``,
  in any case, as a name is refused, since those words are reserved there
  (#1040);
- a ``count(...)`` compared with what pyparsing's arithmetic read only the
  start of, as ``count(x, over=g) > rel[c]``, parses as an arithmetic call,
  which resolution refuses with the rewrite.

The oracle reads quoted labels by the rule the reference states, so labels
are compared and not excused.

The strings are seeded, so a failure names a string that fails again. Set
``MATHSPEC_GRAMMAR_FUZZ`` to a number of rounds to run more of them than the
suite does.
"""

from __future__ import annotations

import dataclasses
import os
from collections import Counter
from collections.abc import Iterator, Mapping
from functools import cache
from random import Random

import pytest
from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from mathspec._condition_parser import RESERVED, UnresolvedComparisonNode, _read, parse_condition
from mathspec._expression_parser import FunctionCallNode, ReadError, Syntax, _expression, parse_expression, unquoter
from mathspec.errors import SchemaError
from tests.grammar.generate import example_strings, nested_shapes, strings
from tests.grammar.oracle import Grammar, Refused, oracle
from tools.grammar import expression_grammar, where_grammar

ROUNDS = int(os.environ.get('MATHSPEC_GRAMMAR_FUZZ', '1'))

CHUNKS = 16

PER_CHUNK = 400

GRAMMARS: tuple[Grammar, ...] = ('expression', 'condition')

NAME_FIELDS = frozenset({'name', 'relation', 'column', 'columns', 'names'})


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


def arithmetic_counts(node: object) -> Iterator[object]:
    """Every comparison in *node* whose left side is ``count`` read as an arithmetic call."""
    if (
        isinstance(node, UnresolvedComparisonNode)
        and isinstance(node.left, FunctionCallNode)
        and node.left.name.upper() == 'COUNT'
    ):
        yield node
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        for field in dataclasses.fields(node):
            yield from arithmetic_counts(getattr(node, field.name))
    elif isinstance(node, Mapping):
        for value in node.values():
            yield from arithmetic_counts(value)
    elif isinstance(node, tuple):
        for item in node:
            yield from arithmetic_counts(item)


def excused(grammar: Grammar, old: object, new: object) -> bool:
    """Whether the two part in one of the three ways the module docstring names."""
    if isinstance(old, Refused) and old.why == 'out of stack':
        return True
    if old == Refused('syntax') and not isinstance(new, Refused) and any(arithmetic_counts(new)):
        return True
    return (
        grammar == 'condition'
        and not isinstance(old, Refused)
        and new == Refused('syntax')
        and any(name.upper() in RESERVED for name in names_in(old))
    )


def disagreement(grammar: Grammar, text: str) -> str | None:
    """Where the package and the oracle part on *text*, outside the excused differences, as a line to print."""
    old, new = oracle(grammar, text), package(grammar, text)
    if shape(old) == shape(new) or excused(grammar, old, new):
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


@cache
def _documented(grammar: Grammar, ambiguity: str) -> Lark:
    """The grammar the language reference prints, as Lark's Earley parser reads it."""
    text = expression_grammar() if grammar == 'expression' else where_grammar()
    return Lark(text, parser='earley', lexer='dynamic', ambiguity=ambiguity)


def _unquoted(syntax: Syntax, grammar: Grammar) -> Syntax:
    """*syntax* with its labels unquoted as the parser's lexer unquotes them, which Earley's dynamic lexer cannot do."""
    if isinstance(syntax, Token):
        return unquoter(escapes=grammar == 'condition')(syntax) if syntax.type == 'STRING' else syntax
    return Tree(syntax.data, [_unquoted(child, grammar) if child is not None else None for child in syntax.children])


def _ambiguities(tree: object) -> Iterator[Tree[Token]]:
    """Every place *tree* reads two ways, other than a ``count(...)`` the parser reads as a count and not a call."""
    if isinstance(tree, Tree):
        if tree.data == '_ambig' and not any(
            isinstance(c, Tree) and c.data == 'cmp' and _counts(c) for c in tree.children
        ):
            yield tree
        for child in tree.children:
            yield from _ambiguities(child)


def _counts(compare: Tree[Token]) -> bool:
    left = compare.children[0]
    return isinstance(left, Tree) and left.data == 'call' and str(left.children[0]).upper() == 'COUNT'


def _documented_reading(grammar: Grammar, text: str) -> object:
    """What the reference's grammar makes of *text*, read into nodes by the parser's own reader.

    ``'several'`` where it reads *text* more than one way, a [`Refused`][] where
    it does not read it, and ``None`` where Earley runs out of stack.
    """
    try:
        if any(_ambiguities(_documented(grammar, 'explicit').parse(text))):
            return 'several'
        tree = _unquoted(_documented(grammar, 'resolve').parse(text), grammar)
    except RecursionError:
        return None
    except LarkError:
        return Refused('syntax')
    try:
        return _read(tree, 0) if grammar == 'condition' else _expression(tree, 0)
    except ReadError:
        return 'read'


@pytest.mark.parametrize('chunk', range(4))
def test_the_reference_s_grammars_read_each_string_as_the_parser_does(chunk):
    """The where grammar the reference prints is not the parser's, which a reader narrows, so it is held here.

    Each grammar accepts what the parser accepts, reads it one way, and its
    tree, read by the parser's own reader, is the parser's node: so its rules
    state the precedence the parser applies. A keyword given twice and a
    nesting past the cap are refused by the parser and admitted by any
    grammar, so those strings are left out.
    """
    found = []
    for grammar, text in strings(Random(f'documented:{chunk}'), PER_CHUNK // 2):
        new = package(grammar, text)
        if new == Refused('too deep') or 'twice' in _message(grammar, text):
            continue
        documented = _documented_reading(grammar, text)
        if documented is not None and shape(documented) != shape(new):
            found.append(f'{grammar} {text!r}\n    parser:    {new!r}\n    reference: {documented!r}')
    assert not found, _report(found)


def _message(grammar: Grammar, text: str) -> str:
    """The parser's refusal of *text*, or the empty string where it reads it."""
    parse = parse_expression if grammar == 'expression' else parse_condition
    try:
        parse.__wrapped__(text)
    except SchemaError as error:
        return str(error)
    return ''
