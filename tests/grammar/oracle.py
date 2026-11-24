# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The pyparsing grammars as they stood at 0.5.0a1, frozen as the oracle the grammar fuzzer compares the package against.

The grammar code between the banners is copied verbatim from
``src/mathspec/_expression_parser.py`` and ``src/mathspec/_condition_parser.py``.
It builds the package's own node classes, so a tree from either side
compares with ``==``. A change to what the language accepts changes this
file in the same commit, or the fuzzer reads the change as a regression.
"""

# ruff: noqa: N806

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast, get_args

import pyparsing as pp

from mathspec._condition_parser import (
    ColumnNode,
    UnresolvedComparisonNode,
    UnresolvedConditionCallNode,
    UnresolvedConditionNode,
    UnresolvedCountNode,
    nested,
)
from mathspec._expression_parser import (
    NAME,
    REAL,
    ArithmeticNode,
    BinaryOperatorNode,
    ColumnsNode,
    ComparisonNode,
    FunctionCallNode,
    KeywordNode,
    NameListNode,
    NameNode,
    NumberNode,
    Sense,
    UnaryOperatorNode,
    children,
    depth,
    keywords,
)
from mathspec.errors import SchemaError
from mathspec.program import And, BooleanLiteral, ComparisonOperator, Condition, Not, Or

if TYPE_CHECKING:
    from collections.abc import Callable

# ---------------------------------------------------------------------------
# Expression grammar, verbatim
# ---------------------------------------------------------------------------


NAME_LIST = (pp.Suppress('[') + pp.DelimitedList(pp.Regex(NAME)) + pp.Suppress(']')).set_parse_action(
    lambda t: NameListNode(tuple(str(x) for x in t))
)


def _build_grammar() -> tuple[pp.ParserElement, pp.ParserElement, pp.ParserElement]:
    """The arithmetic grammar, the expression grammar that puts one comparison over it, and a column selection.

    ``inf`` is a ``pp.Keyword`` rather than a ``pp.Literal``, which would
    match the prefix of ``inflow``.
    """
    arith = pp.Forward()

    inf_literal = (pp.Keyword('.inf') | pp.Keyword('inf')).set_parse_action(lambda: NumberNode(float('inf')))
    # pyrefly: ignore[implicit-any-lambda]
    number = inf_literal | pp.Regex(rf'{REAL}|\d+').set_parse_action(lambda t: NumberNode(float(t[0])))

    name = pp.Regex(NAME)

    quoted = (pp.QuotedString("'") | pp.QuotedString('"')).set_parse_action(lambda t: KeywordNode(str(t[0])))
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

    comparator = pp.one_of(list(get_args(Sense)))
    expression = (arith + pp.Optional(comparator + arith)).set_parse_action(
        lambda t: ComparisonNode(t[1], t[0], t[2]) if len(t) == 3 else t[0]
    )
    return arith, expression, columns


def _make_func_call(tokens: pp.ParseResults) -> FunctionCallNode:
    """The callee is cast: a ParseResults element is untyped, and the grammar guarantees an identifier in position 0."""
    name = cast('str', tokens[0])
    args: list[ArithmeticNode] = []
    pairs: list[tuple[str, ArithmeticNode]] = []
    for item in tokens[1:]:
        (pairs if isinstance(item, tuple) and len(item) == 2 else args).append(item)
    return FunctionCallNode(name=name, args=tuple(args), kwargs=keywords(name, pairs))


def _make_left_assoc(tokens: pp.ParseResults) -> ArithmeticNode:
    result: ArithmeticNode
    result, *rest = tokens
    for op, right in zip(rest[::2], rest[1::2], strict=True):
        result = BinaryOperatorNode(op, result, right)
    return result


def _make_power(tokens: pp.ParseResults) -> ArithmeticNode:
    """A base and at most one exponent — right-associative, since the exponent is itself a ``unary``."""
    items: list[ArithmeticNode] = list(tokens)
    return items[0] if len(items) == 1 else BinaryOperatorNode('**', items[0], items[2])


ARITHMETIC, _GRAMMAR, COLUMNS = _build_grammar()

# ---------------------------------------------------------------------------
# Condition grammar, verbatim
# ---------------------------------------------------------------------------


def _condition_call(tokens: pp.ParseResults) -> UnresolvedConditionCallNode:
    """The call node, with a keyword given twice refused as the arithmetic grammar refuses it."""
    name, operand, *pairs = tokens
    return UnresolvedConditionCallNode(name, operand, keywords(name, pairs))


def _build_condition_grammar() -> pp.ParserElement:
    """Build the pyparsing grammar for conditions.

    Both quote characters are accepted because YAML already owns one of them.
    ``NOT`` binds tightest, then ``AND``, then ``OR``. A comparison is tried
    before a bare name, since its left side begins with one.
    """
    condition = pp.Forward()

    true_lit = pp.CaselessKeyword('True').set_parse_action(lambda: BooleanLiteral(True))
    false_lit = pp.CaselessKeyword('False').set_parse_action(lambda: BooleanLiteral(False))

    name = pp.Regex(NAME)
    # pyrefly: ignore[implicit-any-lambda]
    column = (name + pp.Suppress('[') + name + pp.Suppress(']')).set_parse_action(lambda t: ColumnNode(t[0], t[1]))
    quoted = (pp.QuotedString("'", esc_char='\\') | pp.QuotedString('"', esc_char='\\')).set_parse_action(
        # pyrefly: ignore[implicit-any-lambda]
        lambda t: KeywordNode(t[0])
    )
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

    count_call = _call(pp.CaselessKeyword('count'))
    condition_call = _call(name.copy())

    count_comparison = (count_call + comparator + ARITHMETIC).set_parse_action(
        # pyrefly: ignore[implicit-any-lambda]
        lambda t: UnresolvedCountNode(t[0], t[1], t[2])
    )
    comparison = (
        (column | ARITHMETIC) + comparator + (quoted | column | ARITHMETIC)
        # pyrefly: ignore[implicit-any-lambda]
    ).set_parse_action(lambda t: UnresolvedComparisonNode(t[0], t[1], t[2]))
    # pyrefly: ignore[implicit-any-lambda]
    existence = name.copy().set_parse_action(lambda t: NameNode(t[0]))

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
    not_expr = (NOT + atom).set_parse_action(lambda t: Not(t[0])) | atom

    AND = pp.CaselessKeyword('AND').suppress()
    and_expr = not_expr + pp.ZeroOrMore(AND + not_expr)
    and_expr.set_parse_action(_folder(And))

    OR = pp.CaselessKeyword('OR').suppress()
    or_expr = and_expr + pp.ZeroOrMore(OR + and_expr)
    or_expr.set_parse_action(_folder(Or))

    condition <<= or_expr
    return condition


def _folder(node_type: type[And] | type[Or]) -> Callable[[pp.ParseResults], Condition | UnresolvedConditionNode]:
    """A parse action left-folding a flat operator chain into *node_type*."""

    def fold(tokens: pp.ParseResults) -> Condition | UnresolvedConditionNode:
        items: list[Condition | UnresolvedConditionNode] = list(tokens)
        result = items[0]
        for item in items[1:]:
            result = node_type(cast('Condition', result), cast('Condition', item))
        return result

    return fold


_CONDITION_GRAMMAR = _build_condition_grammar()

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
    parser, child_of = (_GRAMMAR, children) if grammar == 'expression' else (_CONDITION_GRAMMAR, nested)
    try:
        node = parser.parse_string(text, parse_all=True)[0]
    except (pp.ParseException, SchemaError):
        return Refused('syntax')
    except RecursionError:
        return Refused('out of stack')
    return Refused('too deep') if depth(node, child_of) > MAX_DEPTH else node
