# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The condition grammar and the ``Unresolved*`` nodes it emits, package-private.

A condition is a boolean algebra over comparisons, and a comparison's
sides are the expression grammar's own arithmetic. What a side *is* — a
parameter, a dimension, a relation column, a ``position()`` — only the spec
knows, so the grammar hands both sides over bare and
[`mathspec._resolution`][] reads them. The resolved vocabulary lives in
[`mathspec.program`][].
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cache, lru_cache
from typing import TYPE_CHECKING, cast

from lark import Token, Tree

from mathspec._expression_parser import (
    NAME,
    ArithmeticNode,
    KeywordNode,
    NameListNode,
    NameNode,
    ReadError,
    Syntax,
    arguments,
    arithmetic,
    children,
    grammar_parser,
    keywords,
    label,
    nest,
    parse_text,
    start,
    unquoter,
)
from mathspec._frozen import Frozen
from mathspec.program import (
    And,
    BooleanLiteral,
    ComparisonOperator,
    Condition,
    Connective,
    Not,
    Or,
    condition_children,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lark import Lark

# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnNode:
    """``relation[column]`` on a side of a comparison, which reads one column at the frame's coordinates."""

    relation: str
    column: str

    @property
    def shown(self) -> str:
        """The column as the file wrote it, for an error message."""
        return f'{self.relation}[{self.column}]'


@dataclass(frozen=True)
class UnresolvedConditionCallNode:
    """``<name>(<condition>[, <kwarg>…])`` — an operator reading a condition rather than arithmetic.

    The expression grammar cannot carry this shape: its call rule takes
    arithmetic arguments, and a condition is not arithmetic. So the where
    grammar reads it, and resolution decides which operator the name is and
    what the kwargs mean. ``kwargs`` is held and hashed as
    [`FunctionCallNode`][mathspec._expression_parser.FunctionCallNode] holds its own.
    """

    name: str
    operand: Condition | UnresolvedConditionNode
    kwargs: Mapping[str, ArithmeticNode] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'kwargs', Frozen(self.kwargs))


@dataclass(frozen=True)
class UnresolvedCountNode:
    """``count(<condition>, over=<dim>) <op> <number>`` — a count against a literal.

    Its own node rather than an [`UnresolvedComparisonNode`][] with a call
    on the left: every other comparison has arithmetic on both sides, and
    widening that one to carry a condition would widen every reader of a side
    with it.
    """

    call: UnresolvedConditionCallNode
    op: ComparisonOperator
    value: ArithmeticNode


@dataclass(frozen=True)
class UnresolvedComparisonNode:
    """``side <op> side`` before the sides are read; ``_condition_resolver.py`` decides what each is.

    A side is the expression grammar's arithmetic, so a name, a number and a
    ``position(...)`` call all arrive as the nodes an expression would carry
    them in, a quoted label as the [`KeywordNode`][] a quoted kwarg is, and a
    relation column in a node of its own.
    """

    left: ArithmeticNode | ColumnNode
    op: ComparisonOperator
    right: ArithmeticNode | ColumnNode | KeywordNode


UnresolvedConditionNode = NameNode | UnresolvedComparisonNode | UnresolvedConditionCallNode | UnresolvedCountNode

ParsedCondition = Condition | UnresolvedConditionNode | ArithmeticNode | ColumnNode | KeywordNode


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

#: The characters a reserved word may not touch on either side: whatever
#: ``str.upper`` turns into a letter, a digit, ``_`` or ``$``. So ``0AND``
#: holds no ``AND``.
_KEYWORD_EDGE = r'[A-Za-z0-9_$\u0131\u017f]'

#: The words of the where language, in any case. A name spelled as one of
#: them is the word, wherever it stands.
RESERVED = ('AND', 'OR', 'NOT', 'TRUE', 'FALSE')

_CONDITION_RULES = r"""
start: or_
?or_: and_ (_OR and_)*
?and_: not_ (_AND not_)*
?not_: _NOT not_ -> negation
     | cmp
?cmp: sum (COMP sum)?
?atom: NAME
     | NUMBER
     | DOTINF
     | STRING
     | TRUE
     | FALSE
     | NAME LSQB names _RSQB -> columns
     | LSQB names _RSQB -> namelist
     | NAME LPAR [args] _RPAR -> call
     | LPAR or_ _RPAR -> paren
args: arg (_COMMA arg)*
?arg: NAME _EQUAL or_ -> kwarg
    | or_
COMP: /<=|>=|==|!=|<|>/
STRING: /'(?:\\.|[^'\n\r\\])*'|"(?:\\.|[^"\n\r\\])*"/
""" + ''.join(
    f'{"" if word in ("TRUE", "FALSE") else "_"}{word}.2: '
    f'/(?<!{_KEYWORD_EDGE})(?i:{word.lower()})(?!{_KEYWORD_EDGE})/\n'
    for word in RESERVED
)


@cache
def _condition_parser() -> Lark:
    """Built on first use, as the expression parser is."""
    return grammar_parser(_CONDITION_RULES, unquoter(escapes=True))


def _read(syntax: Syntax, parens: int) -> Condition | UnresolvedConditionNode:
    """The whole where string: the one condition ``start`` holds."""
    return _condition(cast('Tree[Token]', syntax).children[0], parens)


def _condition(syntax: Syntax, parens: int) -> Condition | UnresolvedConditionNode:
    """*syntax* as a condition: ``OR`` over ``AND`` over ``NOT``, each folded left."""
    match syntax:
        case Tree(data='or_', children=items):
            return _fold(Or, [_condition(item, parens) for item in items])
        case Tree(data='and_', children=items):
            return _fold(And, [_condition(item, parens) for item in items])
        case Tree(data='negation', children=[operand]):
            return Not(cast('Condition', _atom(operand, parens)))
        case _:
            return _atom(syntax, parens)


def _fold(
    node_type: type[And] | type[Or], items: list[Condition | UnresolvedConditionNode]
) -> Condition | UnresolvedConditionNode:
    result = items[0]
    for item in items[1:]:
        result = node_type(cast('Condition', result), cast('Condition', item))
    return result


def _atom(syntax: Syntax, parens: int) -> Condition | UnresolvedConditionNode:
    """One operand of a connective: a literal, a comparison, a condition call, a name, or a bracketed condition.

    ``NOT`` takes one atom, and a second ``NOT`` is no atom.
    """
    match syntax:
        case Token(type='TRUE' | 'FALSE'):
            return BooleanLiteral(syntax.type == 'TRUE')
        case Token(type='NAME'):
            return NameNode(str(syntax))
        case Tree(data='cmp'):
            return _comparison(syntax, parens)
        case Tree(data='call', children=[name, _, args]):
            return _condition_call(arguments(args), str(name), start(syntax), parens)
        case Tree(data='paren', children=[_, inner]):
            return _condition(inner, nest(parens))
        case _:
            raise ReadError(start(syntax), 'a condition')


def _condition_call(args: list[Syntax], name: str, pos: int, parens: int) -> UnresolvedConditionCallNode:
    """``<name>(<condition>[, <kwarg>…])``, the one call whose first argument is a condition."""
    if not args or _is_kwarg(args[0]):
        raise ReadError(pos, 'a condition as the first argument')
    operand = _condition(args[0], parens)
    pairs: list[tuple[str, ArithmeticNode]] = []
    for arg in args[1:]:
        if not _is_kwarg(arg):
            raise ReadError(start(arg), 'a keyword argument')
        key, value = cast('Tree[Token]', arg).children
        pairs.append((str(key), _call_keyword(value, parens)))
    return UnresolvedConditionCallNode(name, operand, keywords(name, pairs))


def _is_kwarg(syntax: Syntax) -> bool:
    return isinstance(syntax, Tree) and syntax.data == 'kwarg'


def _call_keyword(syntax: Syntax, parens: int) -> ArithmeticNode:
    """A condition call's keyword value: a quoted label, a relation's columns, or arithmetic, and no list of names."""
    found = label(syntax)
    return arithmetic(syntax, parens) if found is None or isinstance(found, NameListNode) else found


def _comparison(compare: Tree[Token], parens: int) -> UnresolvedConditionNode:
    """``side <op> side``, or a count against arithmetic, which is tried first.

    A ``count(...)`` whose first argument is no condition, or whose right side
    starts with no arithmetic, is an arithmetic call compared like any other
    side. Once the right side starts as arithmetic, the count is kept, and a
    right side that does not stay arithmetic is refused.
    """
    left, sign, right = compare.children
    op = cast('ComparisonOperator', str(sign))
    match left:
        case Tree(data='call', children=[Token() as name, _, args]) if name.upper() == 'COUNT':
            try:
                call = _condition_call(arguments(args), 'count', start(left), parens)
            except ReadError:
                call = None
            if call is not None and not _starts_unarithmetic(right):
                return UnresolvedCountNode(call, op, arithmetic(right, parens))
        case _:
            pass
    return UnresolvedComparisonNode(_side(left, parens), op, _right_side(right, parens))


def _starts_unarithmetic(syntax: Syntax) -> bool:
    """Whether *syntax* is written starting with a quoted label or a list of names, where arithmetic cannot start."""
    while isinstance(syntax, Tree) and syntax.data in ('sum', 'product', 'power'):
        syntax = syntax.children[0]
    return (isinstance(syntax, Token) and syntax.type == 'STRING') or (
        isinstance(syntax, Tree) and syntax.data == 'namelist'
    )


def _side(syntax: Syntax, parens: int) -> ArithmeticNode | ColumnNode:
    """A comparison's left side: one column of a relation, or arithmetic."""
    if isinstance(syntax, Tree) and syntax.data == 'columns':
        relation, bracket, names = syntax.children
        columns = cast('Tree[Token]', names).children
        if len(columns) != 1:
            raise ReadError(cast('Token', bracket).start_pos or 0, 'one column')
        return ColumnNode(str(relation), str(columns[0]))
    return arithmetic(syntax, parens)


def _right_side(syntax: Syntax, parens: int) -> ArithmeticNode | ColumnNode | KeywordNode:
    """A comparison's right side: a quoted label too."""
    if isinstance(syntax, Token) and syntax.type == 'STRING':
        return KeywordNode(str(syntax))
    return _side(syntax, parens)


def _named_rewrite(text: str, loc: int) -> str | None:
    """The rewrite for a connective habit of pandas or C, a comparison of several columns, a reserved word, or ``None``.

    ``!=``, ``<`` and ``>`` are legal here, so only the tokens no condition
    admits are diagnosed. The grammar gives up at the bracket of
    ``relation[a, b]``, since a comparison reads one column. A reserved word
    written as a name stops the grammar at the word, or, for ``NOT``,
    ``True`` and ``False``, at what follows it.
    """
    rest = text[loc:].lstrip()
    if rest.startswith('&'):
        return "'&' is not a condition operator. Write AND."
    if rest.startswith('|'):
        return "'|' is not a condition operator. Write OR."
    if rest.startswith(('~', '!')) and not rest.startswith('!='):
        return f"'{rest[0]}' is not a condition operator. Write NOT before the condition."
    if rest.startswith('=') and not rest.startswith('=='):
        return "'=' is not a comparison. Write ==."
    if (listed := re.match(rf'\[\s*({NAME}(?:\s*,\s*{NAME})+)\s*\]', rest)) and (
        before := re.search(rf'({NAME})\s*$', text[:loc])
    ):
        relation, columns = before.group(1), [c.strip() for c in listed.group(1).split(',')]
        each = ' AND '.join(f'{relation}[{column}] == …' for column in columns)
        return f"a comparison reads one column of '{relation}'. Compare each column on its own: {each}."
    return _reserved_rewrite(text, loc, rest)


def _reserved_rewrite(text: str, loc: int, rest: str) -> str | None:
    at = re.match(NAME, rest)
    before = re.search(rf'({NAME})\s*$', text[:loc])
    if at and at.group().upper() in RESERVED and not text[:loc].endswith(tuple('0123456789')):
        word = at.group()
    elif before and before.group(1).upper() in ('NOT', 'TRUE', 'FALSE'):
        word = before.group(1)
    else:
        return None
    return (
        f"'{word}' is one of AND, OR, NOT, True and False, which a where string reserves in any case, "
        f'so it names no entry here. If an entry has that name, rename it.'
    )


_DEEP_REWRITE = (
    'Declare a parameter or relation carrying part of the test and name that here, or split the '
    'entry into two, each masked by one half.'
)


def nested(node: ParsedCondition) -> tuple[ParsedCondition, ...]:
    """What a condition nests through: a connective's operands, a comparison's sides, and a call's condition."""
    if isinstance(node, UnresolvedCountNode):
        return (node.call, node.value)
    if isinstance(node, UnresolvedConditionCallNode):
        return (node.operand, *node.kwargs.values())
    if isinstance(node, UnresolvedComparisonNode):
        return (node.left, node.right)
    if isinstance(node, ArithmeticNode):
        return children(node)
    if isinstance(node, Connective):
        return condition_children(node)
    return ()


@lru_cache(maxsize=4096)
def parse_condition(text: str) -> Condition | UnresolvedConditionNode:
    """Parse a condition into an AST, its leaves still unresolved.

    The connectives and literals are the resolved vocabulary's own; the leaves
    naming entries are a bare [`NameNode`][] or an ``Unresolved*``
    node, which only [`resolve_condition`][mathspec._resolution.resolve_condition] takes.

    Raises:
        SchemaError: If *text* is not a condition of the language. A
            predictable mistake — ``&``/``|``/``~``/``!`` for a connective, a
            lone ``=`` — is named with its rewrite beside the grammar's own
            complaint. A side nesting past what an expression may is refused
            as an expression is.
    """
    return cast(
        'Condition | UnresolvedConditionNode',
        parse_text(_condition_parser(), _read, text, 'condition', _named_rewrite, nested, _DEEP_REWRITE),
    )
