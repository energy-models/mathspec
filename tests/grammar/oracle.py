# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The pyparsing grammars as they stood at 0.5.0a1, frozen as the oracle the grammar fuzzer compares the package against.

The grammar code between the banners is copied from
``src/mathspec/_expression_parser.py`` and ``src/mathspec/_condition_parser.py``
at 0.5.0a1, with quoted labels read by the rule the language reference now
states rather than by pyparsing's ``QuotedString``:

- the text between the quotes, with ``\\t``, ``\\n``, ``\\f``, ``\\r`` as the
  character and no numeric escape (#1039);
- a backslash before any other character is that character, in every
  label of either grammar (#1042);
- a tab is a tab, where ``parse_string`` expanded it to spaces (#1044).

The parse actions build the package's one syntax tree, so a tree from
either side compares with ``==``: a where string's connectives and
literals are the ``*Node`` classes, a comparison of either grammar is a
``ComparisonNode``, a column is a ``ColumnsNode`` of one column, and a call
that reads a condition is a ``FunctionCallNode`` holding it as its one
positional argument. A bare ``inf`` is the number wherever it stands, and
``count`` keeps the case it was written in. The grammar itself is as it
stood. A change to what the language accepts changes this file in the same
commit, or the fuzzer reads the change as a regression.
"""

# ruff: noqa: N806

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast, get_args

import pyparsing as pp

from mathspec._grammar import NAME, REAL
from mathspec._syntax import (
    AndNode,
    BinaryOperatorNode,
    BooleanNode,
    ColumnsNode,
    ComparisonNode,
    FunctionCallNode,
    KeywordNode,
    NameListNode,
    NameNode,
    NotNode,
    NumberNode,
    OrNode,
    ParsedNode,
    UnaryOperatorNode,
    children,
    depth,
)
from mathspec.errors import SchemaError
from mathspec.program import ComparisonOperator, ConstraintSense

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

# ---------------------------------------------------------------------------
# Expression grammar, verbatim
# ---------------------------------------------------------------------------


_WHITESPACE = {'t': '\t', 'n': '\n', 'f': '\f', 'r': '\r'}


def _quoted(quote: str, esc_char: str | None) -> pp.ParserElement:
    """A label delimited as ``QuotedString`` delimits it, and unquoted by the reference's rule."""
    escape = re.compile(r'\\(.)' if esc_char else r'\\([tnfr])')
    return pp.QuotedString(quote, esc_char=esc_char, unquote_results=False).set_parse_action(
        lambda t: KeywordNode(escape.sub(lambda m: _WHITESPACE.get(m[1], m[1]), str(t[0])[1:-1]))
    )


NAME_LIST = (pp.Suppress('[') + pp.DelimitedList(pp.Regex(NAME)) + pp.Suppress(']')).set_parse_action(
    lambda t: NameListNode(tuple(str(x) for x in t))
)


def _build_grammar(esc_char: str | None = None) -> tuple[pp.ParserElement, pp.ParserElement, pp.ParserElement]:
    """The arithmetic grammar, the expression grammar that puts one comparison over it, and a column selection.

    ``inf`` is a ``pp.Keyword`` rather than a ``pp.Literal``, which would
    match the prefix of ``inflow``.
    """
    arith = pp.Forward()

    inf_literal = (pp.Keyword('.inf') | pp.Keyword('inf')).set_parse_action(lambda: NumberNode(float('inf')))
    # pyrefly: ignore[implicit-any-lambda]
    number = inf_literal | pp.Regex(rf'{REAL}|\d+').set_parse_action(lambda t: NumberNode(float(t[0])))

    name = pp.Regex(NAME)

    quoted = _quoted("'", esc_char) | _quoted('"', esc_char)
    columns = (name + pp.Suppress('[') + pp.DelimitedList(name) + pp.Suppress(']')).set_parse_action(
        lambda t: ColumnsNode(str(t[0]), tuple(str(x) for x in t[1:]))
    )
    kwarg = (name + pp.Suppress('=') + (quoted | columns | NAME_LIST | arith)).set_parse_action(lambda t: (t[0], t[1]))
    pos_arg = arith
    arg_list = pp.Optional(pp.DelimitedList(kwarg | pos_arg))
    func_call = (name + pp.Suppress('(') + arg_list + pp.Suppress(')')).set_parse_action(_make_func_call)

    # pyrefly: ignore[implicit-any-lambda]
    name_node = name.copy().set_parse_action(lambda t: NameNode(t[0]))
    atom = func_call | number | name_node | (pp.Suppress('(') + arith + pp.Suppress(')'))

    unary = pp.Forward()
    power = (atom + pp.Optional(pp.Literal('**') + unary)).set_parse_action(_make_power)
    # pyrefly: ignore[implicit-any-lambda]
    unary <<= (pp.one_of('+ -') + unary).set_parse_action(lambda t: UnaryOperatorNode(t[0], t[1])) | power

    mul_div = unary + pp.ZeroOrMore(pp.one_of('* /') + unary)
    mul_div.set_parse_action(_make_left_assoc)

    add_sub = mul_div + pp.ZeroOrMore(pp.one_of('+ -') + mul_div)
    add_sub.set_parse_action(_make_left_assoc)

    arith <<= add_sub

    comparator = pp.one_of(list(get_args(ConstraintSense)))
    expression = (arith + pp.Optional(comparator + arith)).set_parse_action(
        lambda t: ComparisonNode(t[1], t[0], t[2]) if len(t) == 3 else t[0]
    )
    return arith, expression, columns


def _make_func_call(tokens: pp.ParseResults) -> FunctionCallNode:
    """The callee is cast: a ParseResults element is untyped, and the grammar guarantees an identifier in position 0."""
    name = cast('str', tokens[0])
    args: list[ParsedNode] = []
    pairs: list[tuple[str, ParsedNode]] = []
    for item in tokens[1:]:
        (pairs if isinstance(item, tuple) and len(item) == 2 else args).append(item)
    return FunctionCallNode(name=name, args=tuple(args), kwargs=keywords(name, pairs))


def keywords(name: str, pairs: Iterable[tuple[str, ParsedNode]]) -> dict[str, ParsedNode]:
    """A call's keywords, in the order written; a keyword given twice is refused, in both grammars."""
    kwargs: dict[str, ParsedNode] = {}
    for key, value in pairs:
        if key in kwargs:
            msg = f'{name}({key}=) is given twice. Delete one of them.'
            raise SchemaError(msg)
        kwargs[key] = value
    return kwargs


def _make_left_assoc(tokens: pp.ParseResults) -> ParsedNode:
    result: ParsedNode
    result, *rest = tokens
    for op, right in zip(rest[::2], rest[1::2], strict=True):
        result = BinaryOperatorNode(op, result, right)
    return result


def _make_power(tokens: pp.ParseResults) -> ParsedNode:
    """A base and at most one exponent — right-associative, since the exponent is itself a ``unary``."""
    items: list[ParsedNode] = list(tokens)
    return items[0] if len(items) == 1 else BinaryOperatorNode('**', items[0], items[2])


ARITHMETIC, _GRAMMAR, COLUMNS = _build_grammar('\\')

# ---------------------------------------------------------------------------
# Condition grammar, verbatim
# ---------------------------------------------------------------------------


def _condition_call(tokens: pp.ParseResults) -> FunctionCallNode:
    """The call node, with a keyword given twice refused as the arithmetic grammar refuses it."""
    name, operand, *pairs = tokens
    return FunctionCallNode(name, (operand,), keywords(name, pairs))


def _build_condition_grammar() -> pp.ParserElement:
    """Build the pyparsing grammar for conditions.

    Both quote characters are accepted because YAML already owns one of them.
    ``NOT`` binds tightest, then ``AND``, then ``OR``. A comparison is tried
    before a bare name, since its left side begins with one.
    """
    condition = pp.Forward()

    true_lit = pp.CaselessKeyword('True').set_parse_action(lambda: BooleanNode(True))
    false_lit = pp.CaselessKeyword('False').set_parse_action(lambda: BooleanNode(False))

    name = pp.Regex(NAME)
    # pyrefly: ignore[implicit-any-lambda]
    column = (name + pp.Suppress('[') + name + pp.Suppress(']')).set_parse_action(lambda t: ColumnsNode(t[0], (t[1],)))
    quoted = _quoted("'", '\\') | _quoted('"', '\\')
    comparator = pp.one_of(list(get_args(ComparisonOperator)))

    kwarg = (name + pp.Suppress('=') + (quoted | COLUMNS | ARITHMETIC)).set_parse_action(lambda t: (t[0], t[1]))

    def _call(head: pp.ParserElement) -> pp.ParserElement:
        """``<head>(<condition>[, <kwarg>…])`` — the one shape whose operand is a condition.

        ``count`` is spelled in the grammar rather than left to resolution, as
        ``position`` is, because only the grammar can decide to read its
        argument as a condition. Every other condition-taking call stands where
        arithmetic cannot, so the comparison above it has already been tried
        and the name is free.
        """
        return (
            head + pp.Suppress('(') + condition + pp.ZeroOrMore(pp.Suppress(',') + kwarg) + pp.Suppress(')')
        ).set_parse_action(_condition_call)

    count_call = _call(pp.original_text_for(pp.CaselessKeyword('count')))
    condition_call = _call(name.copy())

    count_comparison = (count_call + comparator + ARITHMETIC).set_parse_action(
        # pyrefly: ignore[implicit-any-lambda]
        lambda t: ComparisonNode(t[1], t[0], t[2])
    )
    comparison = (
        (column | ARITHMETIC) + comparator + (quoted | column | ARITHMETIC)
        # pyrefly: ignore[implicit-any-lambda]
    ).set_parse_action(lambda t: ComparisonNode(t[1], t[0], t[2]))
    # pyrefly: ignore[implicit-any-lambda]
    existence = name.copy().set_parse_action(lambda t: NumberNode(float('inf')) if t[0] == 'inf' else NameNode(t[0]))

    atom = (
        true_lit
        | false_lit
        | count_comparison
        | comparison
        | condition_call
        | existence
        | (pp.Suppress('(') + condition + pp.Suppress(')'))
    )

    NOT = pp.CaselessKeyword('NOT').suppress()
    # pyrefly: ignore[implicit-any-lambda]
    not_expr = (NOT + atom).set_parse_action(lambda t: NotNode(t[0])) | atom

    AND = pp.CaselessKeyword('AND').suppress()
    and_expr = not_expr + pp.ZeroOrMore(AND + not_expr)
    and_expr.set_parse_action(_folder(AndNode))

    OR = pp.CaselessKeyword('OR').suppress()
    or_expr = and_expr + pp.ZeroOrMore(OR + and_expr)
    or_expr.set_parse_action(_folder(OrNode))

    condition <<= or_expr
    return condition


def _folder(node_type: type[AndNode] | type[OrNode]) -> Callable[[pp.ParseResults], ParsedNode]:
    """A parse action left-folding a flat operator chain into *node_type*."""

    def fold(tokens: pp.ParseResults) -> ParsedNode:
        items: list[ParsedNode] = list(tokens)
        result = items[0]
        for item in items[1:]:
            result = node_type(result, item)
        return result

    return fold


_CONDITION_GRAMMAR = _build_condition_grammar()
_GRAMMAR.parse_with_tabs()
_CONDITION_GRAMMAR.parse_with_tabs()

# ---------------------------------------------------------------------------
# What the oracle says about one string
# ---------------------------------------------------------------------------

Grammar = Literal['expression', 'condition']

MAX_DEPTH = 100


@dataclass(frozen=True)
class Refused:
    """The oracle's refusal, by cause: the grammar, the depth cap, or pyparsing's own stack."""

    why: Literal['syntax', 'too deep', 'out of stack']


def oracle(grammar: Grammar, text: str) -> object:
    """The tree the frozen grammar builds for *text*, or the reason it refuses it, as ``parse_text`` decided."""
    parser = _GRAMMAR if grammar == 'expression' else _CONDITION_GRAMMAR
    try:
        node = parser.parse_string(text, parse_all=True)[0]
    except (pp.ParseException, SchemaError):
        return Refused('syntax')
    except RecursionError:
        return Refused('out of stack')
    return Refused('too deep') if depth(node, children) > MAX_DEPTH else node
