# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The syntax tree the expression grammar builds, and the grammar — package-private.

Only expansion and resolution read it: resolution rewrites it into the
[`mathspec.program`][] vocabulary, which every pass after reads. Arithmetic
nests anywhere; a comparison appears only at the top of a parsed expression.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cache, lru_cache
from typing import TYPE_CHECKING, Literal, assert_never, cast, get_args

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedInput, UnexpectedToken

from mathspec._frozen import Frozen
from mathspec.errors import SchemaError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

Sense = Literal['<=', '>=', '==']

UnaryOperator = Literal['+', '-']

BinaryOperator = Literal['+', '-', '*', '/', '**']

NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'

REAL = r'\d+\.\d*([eE][+-]?\d+)?|\d+[eE][+-]?\d+'

# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------


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
class NameListNode:
    """A bracketed list of names in a kwarg value — ``sum(x, by=[a, b])``.

    Unresolved: which kind of name the kwarg admits is the operator's business.
    """

    names: tuple[str, ...]

    def __str__(self) -> str:
        return shown(self.names)


@dataclass(frozen=True)
class ColumnsNode:
    """Columns of one relation in a kwarg value — ``sum(x, over=g, by=gen_bus[bus])``.

    The relation is written once and its columns after it, so one call cannot
    name columns of two tables. Unresolved: which columns the kwarg admits is
    the operator's business.
    """

    relation: str
    columns: tuple[str, ...]

    def __str__(self) -> str:
        return f'{self.relation}[{", ".join(self.columns)}]'


@dataclass(frozen=True)
class KeywordNode:
    """A quoted closed keyword in a kwarg value — ``shift(..., edge='wrap')``.

    Unresolved: which keywords the kwarg accepts is the operator's business.
    """

    value: str

    def __str__(self) -> str:
        return f"'{self.value}'"


@dataclass(frozen=True)
class UnaryOperatorNode:
    op: UnaryOperator
    operand: ArithmeticNode

    def __str__(self) -> str:
        return f'{self.op}{operand(self.operand)}'


@dataclass(frozen=True)
class BinaryOperatorNode:
    op: BinaryOperator
    left: ArithmeticNode
    right: ArithmeticNode

    def __str__(self) -> str:
        return f'{operand(self.left)} {self.op} {operand(self.right)}'


@dataclass(frozen=True)
class FunctionCallNode:
    """An operator or macro call.

    ``kwargs`` is held behind a read-only view and excluded from the hash;
    equal nodes still hash equal on ``name`` and ``args``.
    """

    name: str
    args: tuple[ArithmeticNode, ...] = ()
    kwargs: Mapping[str, ArithmeticNode] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'kwargs', Frozen(self.kwargs))

    def __str__(self) -> str:
        passed = [*(str(arg) for arg in self.args), *(f'{key}={value}' for key, value in self.kwargs.items())]
        return f'{self.name}({", ".join(passed)})'


ArithmeticNode = (
    NumberNode
    | NameNode
    | NameListNode
    | ColumnsNode
    | KeywordNode
    | UnaryOperatorNode
    | BinaryOperatorNode
    | FunctionCallNode
)


@dataclass(frozen=True)
class ComparisonNode:
    op: Sense
    left: ArithmeticNode
    right: ArithmeticNode

    def __str__(self) -> str:
        """Both sides bare: a comparison is not an [`ArithmeticNode`][], so nothing can take one as an operand."""
        return f'{self.left} {self.op} {self.right}'


ParsedNode = ArithmeticNode | ComparisonNode


def shown(names: tuple[str, ...]) -> str:
    """Names as a kwarg value is written: bare when one, bracketed when several."""
    return names[0] if len(names) == 1 else f'[{", ".join(names)}]'


def operand(node: ArithmeticNode) -> str:
    """One operand of an operator, bracketed where reading the text back would regroup the tree.

    Whoever writes a node into a larger text — an operator, a line of a dumped
    sum — asks this rather than restating when brackets are needed.

    A leaf and a call are self-delimiting, and an operator node is not. The brackets go on every operator operand rather than only the
    ones precedence would regroup, because a node prints without knowing its
    parent: ``a + (b * c)`` keeps the tree where ``a + b * c`` would rely on the
    reader knowing which binds tighter.
    """
    return f'({node})' if isinstance(node, (UnaryOperatorNode, BinaryOperatorNode)) else str(node)


def children(node: ParsedNode) -> tuple[ArithmeticNode, ...]:
    """The sub-expressions of *node* — the structural half of any walk.

    An operator's kwargs are children too — a dimension or coordinate is an
    ordinary node in a kwarg value, which is what lets a macro bind a formal.
    """
    if isinstance(node, UnaryOperatorNode):
        return (node.operand,)
    if isinstance(node, (BinaryOperatorNode, ComparisonNode)):
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


def with_children(node: ArithmeticNode, recurse: Callable[[ArithmeticNode], ArithmeticNode]) -> ArithmeticNode:
    """*node* rebuilt with *recurse* applied to each of its [`children`][]; a leaf comes back as is."""
    if isinstance(node, NumberNode | NameNode | NameListNode | ColumnsNode | KeywordNode):
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
    assert_never(node)


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

#: The rules and terminals both grammars share: arithmetic below the
#: comparison, and the tokens it is written in.
ARITHMETIC_RULES = (
    r"""
?sum: product (ADD product)*
?product: unary (MUL unary)*
?unary: ADD unary -> neg
      | power
?power: atom (_POW unary)?
names: NAME (_COMMA NAME)*

"""
    + f'NAME: /{NAME}/\nNUMBER: /{REAL}|\\d+/\n'
    + r"""DOTINF: /(?<![A-Za-z0-9_$])\.inf(?![A-Za-z0-9_$])/
ADD: /[+-]/
MUL: /[*\/]/
_POW: "**"
LPAR: "("
_RPAR: ")"
LSQB: "["
_RSQB: "]"
_COMMA: ","
_EQUAL: "="
%ignore /[ \t\r\n]+/
"""
)

_EXPRESSION_RULES = r"""
start: sum (SENSE sum)?
?atom: NAME
     | NUMBER
     | DOTINF
     | NAME LPAR [args] _RPAR -> call
     | LPAR sum _RPAR -> paren
args: arg (_COMMA arg)*
?arg: NAME _EQUAL value -> kwarg
    | sum
?value: STRING
      | NAME LSQB names _RSQB -> columns
      | LSQB names _RSQB -> namelist
      | sum
SENSE: /<=|>=|==/
STRING: /'[^'\n\r]*'|"[^"\n\r]*"/
"""

type Syntax = Tree[Token] | Token
"""What Lark builds: a rule's tree, or a token where a rule holds one token alone."""


class ReadError(Exception):
    """A structure the parser builds and the language does not hold, at *pos*, where *expected* was."""

    def __init__(self, pos: int, expected: str) -> None:
        super().__init__(expected)
        self.pos = pos
        self.expected = expected


class _TooDeepError(Exception):
    """Parentheses nested past [`MAX_DEPTH`][], which add no node to the tree but would deepen the walk over it."""


_WHITESPACE_ESCAPES = {'t': '\t', 'n': '\n', 'f': '\f', 'r': '\r'}


def unquoter(*, escapes: bool) -> Callable[[Token], Token]:
    r"""What a quoted label stands for: the text between its quotes, with ``\t``, ``\n``, ``\f`` and ``\r`` as the character.

    With *escapes*, as the where grammar's labels have, a backslash before
    any other character stands for that character, so ``'it\'s'`` is
    ``it's``. Without, any other backslash is itself. Applied as Lark lexes
    the token, so the label reaches the reader unquoted.
    """
    scan = re.compile(r'\\(.)' if escapes else r'\\([tnfr])')

    def escaped(match: re.Match[str]) -> str:
        return _WHITESPACE_ESCAPES.get(match[1], match[1])

    def unquote(token: Token) -> Token:
        inner = token[1:-1]
        return Token.new_borrow_pos('STRING', scan.sub(escaped, inner) if '\\' in inner else inner, token)

    return unquote


def grammar_parser(rules: str, unquote: Callable[[Token], Token]) -> Lark:
    """An LALR parser over *rules* and the arithmetic, its quoted labels unquoted as they lex."""
    return Lark(rules + ARITHMETIC_RULES, parser='lalr', lexer='basic', lexer_callbacks={'STRING': unquote})


@cache
def _expression_parser() -> Lark:
    """Built on first use, not at import: building the tables is a cost a load that parses nothing should not pay."""
    return grammar_parser(_EXPRESSION_RULES, unquoter(escapes=False))


def keywords[V](name: str, pairs: Iterable[tuple[str, V]]) -> dict[str, V]:
    """A call's keywords, in the order written; a keyword given twice is refused, in both grammars."""
    kwargs: dict[str, V] = {}
    for key, value in pairs:
        if key in kwargs:
            msg = f'{name}({key}=) is given twice. Delete one of them.'
            raise SchemaError(msg)
        kwargs[key] = value
    return kwargs


def start(syntax: Syntax) -> int:
    """Where *syntax* starts in the text: its first token's position, which is where a refusal of it points."""
    first = syntax if isinstance(syntax, Token) else next(syntax.scan_values(lambda v: isinstance(v, Token)))
    return first.start_pos or 0


def nest(parens: int) -> int:
    """*parens* deepened by one pair, refused once past [`MAX_DEPTH`][]."""
    if parens >= MAX_DEPTH:
        raise _TooDeepError
    return parens + 1


def fold(children: list[Syntax], read: Callable[[Syntax], ArithmeticNode]) -> ArithmeticNode:
    """``a op b op c`` as ``(a op b) op c``, each operand *read*."""
    result = read(children[0])
    for op, operand in zip(children[1::2], children[2::2], strict=True):
        result = BinaryOperatorNode(cast('BinaryOperator', str(op)), result, read(operand))
    return result


def arithmetic(syntax: Syntax, parens: int) -> ArithmeticNode:
    """*syntax* as arithmetic, or [`ReadError`][] where it is not arithmetic.

    A bare ``inf`` is the number; as a callee it is a name.
    """
    match syntax:
        case Token(type='NAME'):
            return NumberNode(float('inf')) if syntax == 'inf' else NameNode(str(syntax))
        case Token(type='NUMBER'):
            return NumberNode(float(syntax))
        case Token(type='DOTINF'):
            return NumberNode(float('inf'))
        case Tree(data='sum' | 'product', children=children):
            return fold(children, lambda operand: arithmetic(operand, parens))
        case Tree(data='neg', children=[op, operand]):
            return UnaryOperatorNode(cast('UnaryOperator', str(op)), arithmetic(operand, parens))
        case Tree(data='power', children=[base, exponent]):
            return BinaryOperatorNode('**', arithmetic(base, parens), arithmetic(exponent, parens))
        case Tree(data='call', children=[name, _, args]):
            positional: list[ArithmeticNode] = []
            pairs: list[tuple[str, ArithmeticNode]] = []
            for arg in arguments(args):
                if isinstance(arg, Tree) and arg.data == 'kwarg':
                    key, value = arg.children
                    pairs.append((str(key), _keyword_value(value, parens)))
                else:
                    positional.append(arithmetic(arg, parens))
            return FunctionCallNode(name=str(name), args=tuple(positional), kwargs=keywords(str(name), pairs))
        case Tree(data='paren', children=[_, inner]):
            return arithmetic(inner, nest(parens))
        case _:
            raise ReadError(start(syntax), 'arithmetic')


def arguments(args: Syntax | None) -> list[Syntax]:
    """A call's arguments, in the order written; none where the parentheses are empty."""
    return [] if args is None else cast('Tree[Token]', args).children


def label(syntax: Syntax) -> KeywordNode | ColumnsNode | NameListNode | None:
    """*syntax* as a quoted label, a relation's columns or a list of names, or ``None`` where it is none of them."""
    match syntax:
        case Token(type='STRING'):
            return KeywordNode(str(syntax))
        case Tree(data='columns', children=[relation, _, Tree(children=names)]):
            return ColumnsNode(str(relation), tuple(str(n) for n in names))
        case Tree(data='namelist', children=[_, Tree(children=names)]):
            return NameListNode(tuple(str(n) for n in names))
        case _:
            return None


def _keyword_value(syntax: Syntax, parens: int) -> ArithmeticNode:
    """An arithmetic call's keyword value: a quoted label, a relation's columns, a list of names, or arithmetic."""
    found = label(syntax)
    return arithmetic(syntax, parens) if found is None else found


def _expression(syntax: Syntax, parens: int) -> ParsedNode:
    """The top of an expression: arithmetic, or one comparison of two."""
    children = cast('Tree[Token]', syntax).children
    if len(children) == 3:
        left, sense, right = children
        return ComparisonNode(cast('Sense', str(sense)), arithmetic(left, parens), arithmetic(right, parens))
    return arithmetic(children[0], parens)


def _location(error: UnexpectedInput, text: str) -> int:
    """Where Lark gave up, as an index into *text*; the end of the text where the text ran out."""
    if isinstance(error, UnexpectedToken) and error.token.type != '$END':
        return error.token.start_pos or 0
    if isinstance(error, UnexpectedCharacters):
        return error.pos_in_stream or 0
    return len(text)


_SPOKEN = {
    'NAME': 'a name',
    'NUMBER': 'a number',
    'DOTINF': "'.inf'",
    'STRING': 'a quoted label',
    'ADD': "'+' or '-'",
    'MUL': "'*' or '/'",
    'SENSE': "'<=', '>=' or '=='",
    'COMP': 'a comparison',
    'LPAR': "'('",
    'LSQB': "'['",
    'a token of the language': 'a token of the language',
    'TRUE': 'True',
    'FALSE': 'False',
    'AND': 'AND',
    'OR': 'OR',
    'NOT': 'NOT',
    'POW': "'**'",
    'RPAR': "')'",
    'RSQB': "']'",
    'COMMA': "','",
    'EQUAL': "'='",
    '$END': 'the end of the text',
}


def _expected(error: UnexpectedInput) -> Iterable[str]:
    """The terminals Lark would have taken where it gave up."""
    if isinstance(error, UnexpectedToken):
        return error.accepts or error.expected
    if isinstance(error, UnexpectedCharacters):
        return ('a token of the language',)
    if isinstance(error, UnexpectedEOF):
        return error.expected
    return ()


def _complaint(text: str, loc: int, expected: Iterable[str]) -> str:
    """The grammar's own complaint: what it expected, what it found, and where."""
    spoken = sorted({_SPOKEN.get(name.strip('_'), name.strip('_')) for name in expected}) or ['nothing more']
    found = repr(text[loc : loc + 10]) if loc < len(text) else 'the end of the text'
    line = text.count('\n', 0, loc) + 1
    column = loc - (text.rfind('\n', 0, loc) + 1) + 1
    return f'Expected {", ".join(spoken)}, found {found}  (at char {loc}), (line:{line}, col:{column})'


MAX_DEPTH = 100


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


def _too_deep(what: str, text: str, found: int | None, rewrite: str) -> str:
    """The refusal both grammars raise, so the two say the same thing about the same limit.

    *found* is ``None`` where the parser ran out of stack before a tree existed
    to measure.
    """
    shown = text if len(text) <= 60 else f'{text[:60]}…'
    measured = f'nests {found} deep' if found is not None else 'nests deeper'
    return f'The {what} {measured}, past the {MAX_DEPTH} levels the language admits: {shown!r}\n{rewrite}'


def parse_text[T](
    parser: Lark,
    read: Callable[[Syntax, int], T],
    text: str,
    what: str,
    rewrite: Callable[[str, int], str | None],
    child_of: Callable[[T], tuple[T, ...]],
    deep_rewrite: str,
) -> T:
    """Parse the whole of *text* with *parser* and *read* the result, or raise [`SchemaError`][] naming *what* failed.

    *rewrite* is asked for the predictable mistake at the failure position; its
    sentence, if any, precedes the grammar's own complaint. A tree nesting past
    [`MAX_DEPTH`][], measured through *child_of*, is refused with
    *deep_rewrite*, and so are parentheses nested past it, which would deepen
    every walk over the text without adding a node. The node comes back as the
    type *child_of* walks, which is the grammar's word for what it builds.
    """
    try:
        node = read(parser.parse(text), 0)
    except UnexpectedInput as e:
        loc = _location(e, text)
        expected = _expected(e)
        raise SchemaError(_cannot(what, text, rewrite(text, loc), _complaint(text, loc, expected))) from e
    except ReadError as e:
        raise SchemaError(_cannot(what, text, rewrite(text, e.pos), _complaint(text, e.pos, [e.expected]))) from None
    except (_TooDeepError, RecursionError):
        raise SchemaError(_too_deep(what, text, None, deep_rewrite)) from None
    found = depth(node, child_of)
    if found > MAX_DEPTH:
        raise SchemaError(_too_deep(what, text, found, deep_rewrite))
    return node


def _cannot(what: str, text: str, hint: str | None, complaint: str) -> str:
    return f'Cannot parse the {what} {text!r}.\n{f"{hint}\n" if hint is not None else ""}{complaint}'


def _named_rewrite(text: str, loc: int) -> str | None:
    """The rewrite for a predictable mistake at the token where the grammar gave up, or ``None``.

    A two-character token is tested before its one-character prefix. A sense
    is a chained comparison only where a sense came before it; inside a call,
    it is a comparison where arithmetic was expected.
    """
    rest = text[loc:].lstrip()
    if rest.startswith(get_args(Sense)):
        if any(sense in text[:loc] for sense in get_args(Sense)):
            return f"'{rest[:2]}' follows a complete comparison. Split the chain into two constraints."
        return None
    if rest.startswith('!='):
        return "'!=' is not a constraint sense. Write <=, >= or ==, or move the != test to where:."
    if rest.startswith(('<', '>')):
        return f"'{rest[0]}' is not a constraint sense. Write '{rest[0]}=' instead."
    if rest.startswith('='):
        return "A single '=' passes a keyword argument, as in sum(x, over=d). Write == for equality."
    if rest.startswith('^'):
        return "power is written '**', not '^'."
    return None


_DEEP_REWRITE = (
    'Reduce over a dimension with sum() rather than writing the terms out, or name an intermediate '
    'quantity under expressions: and refer to it by name.'
)


@lru_cache(maxsize=4096)
def parse_expression(text: str) -> ParsedNode:
    """Parse a math expression string into an AST.

    Raises:
        SchemaError: If *text* is not an expression of the language. A
            predictable mistake — a strict or chained comparison, ``!=``, a
            lone ``=``, ``^`` for power — is named with its rewrite before the
            grammar's own complaint.
    """
    return parse_text(_expression_parser(), _expression, text, 'expression', _named_rewrite, children, _DEEP_REWRITE)


def names_in(value: ArithmeticNode) -> tuple[str, ...]:
    """The names a relation kwarg carries: one bare, several bracketed, none otherwise."""
    if isinstance(value, NameNode):
        return (value.name,)
    return value.names if isinstance(value, NameListNode) else ()


def literal_number(value: ArithmeticNode) -> NumberNode | None:
    """The number a literal names, its sign folded in — ``None`` where *value* is not one."""
    if isinstance(value, NumberNode):
        return value
    if isinstance(value, UnaryOperatorNode) and isinstance(value.operand, NumberNode):
        return NumberNode(-value.operand.value if value.op == '-' else value.operand.value)
    return None
