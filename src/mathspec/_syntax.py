# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The syntax tree every string of the language parses to, package-private.

One tree holds an expression and a condition alike, and says only what was
written. What a node may be where it stands — a number, a truth value, a
dimension, the columns of a relation — only the spec knows, so
[`mathspec._resolution`][] reads the tree into the [`mathspec.program`][]
vocabulary and refuses there what does not fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, assert_never

from mathspec._frozen import Frozen

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from mathspec.program import ComparisonOperator

UnaryOperator = Literal['+', '-']

BinaryOperator = Literal['+', '-', '*', '/', '**']

MAX_DEPTH = 100


@dataclass(frozen=True)
class NumberNode:
    value: float

    def __str__(self) -> str:
        """A whole number without its fraction, which is how a file writes one and how it parses back."""
        return str(int(self.value)) if self.value.is_integer() else str(self.value)


@dataclass(frozen=True)
class NameNode:
    """A bare name whose kind only the spec knows; resolution rewrites every one into a program node."""

    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class BooleanNode:
    """``True`` or ``False``, which only a where string reserves."""

    value: bool

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class KeywordNode:
    """A quoted label — ``shift(..., edge='wrap')``, ``tech == 'wind'``.

    Unresolved: which labels a place accepts is resolution's business.
    """

    value: str

    def __str__(self) -> str:
        """In single quotes, with the escapes that read back as the same label."""
        return f"'{''.join(_ESCAPED.get(char, char) for char in self.value)}'"


_ESCAPED = {'\\': '\\\\', "'": "\\'", '\t': '\\t', '\n': '\\n', '\f': '\\f', '\r': '\\r'}


@dataclass(frozen=True)
class NameListNode:
    """A bracketed list of names — ``sum(x, over=[a, b])``.

    Unresolved: which kind of name a place admits is the operator's business.
    """

    names: tuple[str, ...]

    def __str__(self) -> str:
        return shown(self.names)


@dataclass(frozen=True)
class ColumnsNode:
    """Columns of one relation — ``sum(x, over=g, by=gen_bus[bus])``, ``ends[bus0] != ends[bus1]``.

    The relation is written once and its columns after it, so one selection
    cannot name columns of two tables. Unresolved: which columns a place
    admits, and how many, is resolution's business.
    """

    relation: str
    columns: tuple[str, ...]

    def __str__(self) -> str:
        return f'{self.relation}[{", ".join(self.columns)}]'


@dataclass(frozen=True)
class UnaryOperatorNode:
    op: UnaryOperator
    operand: ParsedNode

    def __str__(self) -> str:
        return f'{self.op}{operand(self.operand)}'


@dataclass(frozen=True)
class BinaryOperatorNode:
    op: BinaryOperator
    left: ParsedNode
    right: ParsedNode

    def __str__(self) -> str:
        return f'{operand(self.left)} {self.op} {operand(self.right)}'


@dataclass(frozen=True)
class FunctionCallNode:
    """An operator or macro call.

    ``kwargs`` is held behind a read-only view and excluded from the hash;
    equal nodes still hash equal on ``name`` and ``args``.
    """

    name: str
    args: tuple[ParsedNode, ...] = ()
    kwargs: Mapping[str, ParsedNode] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'kwargs', Frozen(self.kwargs))

    def __str__(self) -> str:
        passed = [*(str(arg) for arg in self.args), *(f'{key}={value}' for key, value in self.kwargs.items())]
        return f'{self.name}({", ".join(passed)})'


@dataclass(frozen=True)
class ComparisonNode:
    op: ComparisonOperator
    left: ParsedNode
    right: ParsedNode

    def __str__(self) -> str:
        """Both sides bare where they are arithmetic: the comparison binds looser than every operator in them."""
        return f'{_bracketed(self.left, _CONDITIONS)} {self.op} {_bracketed(self.right, _CONDITIONS)}'


@dataclass(frozen=True)
class NotNode:
    operand: ParsedNode

    def __str__(self) -> str:
        """The operand in brackets unless it is a leaf or a call, so a negated comparison is not read as a negated name."""
        return f'NOT {operand(self.operand)}'


@dataclass(frozen=True)
class AndNode:
    left: ParsedNode
    right: ParsedNode

    def __str__(self) -> str:
        return f'{_bracketed(self.left, (OrNode,))} AND {_bracketed(self.right, (AndNode, OrNode))}'


@dataclass(frozen=True)
class OrNode:
    left: ParsedNode
    right: ParsedNode

    def __str__(self) -> str:
        return f'{self.left} OR {_bracketed(self.right, (OrNode,))}'


ParsedNode = (
    NumberNode
    | NameNode
    | BooleanNode
    | KeywordNode
    | NameListNode
    | ColumnsNode
    | UnaryOperatorNode
    | BinaryOperatorNode
    | FunctionCallNode
    | ComparisonNode
    | NotNode
    | AndNode
    | OrNode
)
"""Every node of a parsed tree."""

_CONDITIONS = (ComparisonNode, NotNode, AndNode, OrNode)


def shown(names: tuple[str, ...]) -> str:
    """Names as a kwarg value is written: bare when one, bracketed when several."""
    return names[0] if len(names) == 1 else f'[{", ".join(names)}]'


def operand(node: ParsedNode) -> str:
    """One operand of an operator, bracketed where reading the text back would regroup the tree.

    Whoever writes a node into a larger text — an operator, a line of a dumped
    sum — asks this rather than restating when brackets are needed.

    A leaf and a call are self-delimiting, and nothing else is. The brackets
    go on every other operand rather than only the ones precedence would
    regroup, because a node prints without knowing its parent: ``a + (b * c)``
    keeps the tree where ``a + b * c`` would rely on the reader knowing which
    binds tighter.
    """
    return _bracketed(node, (UnaryOperatorNode, BinaryOperatorNode, *_CONDITIONS))


def _bracketed(node: ParsedNode, kinds: tuple[type, ...]) -> str:
    return f'({node})' if isinstance(node, kinds) else str(node)


def children(node: ParsedNode) -> tuple[ParsedNode, ...]:
    """The nodes directly under *node* — the structural half of any walk.

    An operator's kwargs are children too — a dimension or coordinate is an
    ordinary node in a kwarg value, which is what lets a macro bind a formal.
    """
    if isinstance(node, (UnaryOperatorNode, NotNode)):
        return (node.operand,)
    if isinstance(node, (BinaryOperatorNode, ComparisonNode, AndNode, OrNode)):
        return (node.left, node.right)
    if isinstance(node, FunctionCallNode):
        return (*node.args, *node.kwargs.values())
    return ()


def nodes(*roots: ParsedNode) -> Iterator[ParsedNode]:
    """Every node under *roots*, each root itself included, parents first.

    The traversal a question about a tree is a filter of, the way
    [`mathspec.program.walk`][] is for a program.
    """
    for root in roots:
        yield root
        yield from nodes(*children(root))


def with_children(node: ParsedNode, recurse: Callable[[ParsedNode], ParsedNode]) -> ParsedNode:
    """*node* rebuilt with *recurse* applied to each of its [`children`][]; a leaf comes back as is."""
    if isinstance(node, NumberNode | NameNode | BooleanNode | KeywordNode | NameListNode | ColumnsNode):
        return node
    if isinstance(node, UnaryOperatorNode):
        return UnaryOperatorNode(node.op, recurse(node.operand))
    if isinstance(node, BinaryOperatorNode):
        return BinaryOperatorNode(node.op, recurse(node.left), recurse(node.right))
    if isinstance(node, FunctionCallNode):
        return FunctionCallNode(
            node.name,
            tuple(recurse(a) for a in node.args),
            {k: recurse(v) for k, v in node.kwargs.items()},
        )
    if isinstance(node, ComparisonNode):
        return ComparisonNode(node.op, recurse(node.left), recurse(node.right))
    if isinstance(node, NotNode):
        return NotNode(recurse(node.operand))
    if isinstance(node, AndNode):
        return AndNode(recurse(node.left), recurse(node.right))
    if isinstance(node, OrNode):
        return OrNode(recurse(node.left), recurse(node.right))
    assert_never(node)


def depth[T](node: T, child_of: Callable[[T], tuple[T, ...]]) -> int:
    """How many nodes deep *node* is, walked with an explicit stack.

    Iterative deliberately: this measurement is what refuses a tree too deep to
    recurse over, so recursing to take it would be the crash it prevents.
    """
    deepest, pending = 0, [(node, 1)]
    while pending:
        current, reached = pending.pop()
        deepest = max(deepest, reached)
        pending.extend((child, reached + 1) for child in child_of(current))
    return deepest


def names_in(value: ParsedNode) -> tuple[str, ...]:
    """The names a kwarg value carries: one bare, several bracketed, none otherwise."""
    if isinstance(value, NameNode):
        return (value.name,)
    return value.names if isinstance(value, NameListNode) else ()


def literal_number(value: ParsedNode) -> NumberNode | None:
    """The number a literal names, its sign folded in — ``None`` where *value* is not one."""
    if isinstance(value, NumberNode):
        return value
    if isinstance(value, UnaryOperatorNode) and isinstance(value.operand, NumberNode):
        return NumberNode(-value.operand.value if value.op == '-' else value.operand.value)
    return None
