# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The one grammar of the language, and its parser — package-private.

An expression and a condition are written in one grammar and parse to one
tree ([`mathspec._syntax`][]). The grammar reads what was written and decides
nothing about what it means: that a constraint holds one comparison, that
``AND`` joins truth values, that ``edge=`` takes a label, are rules of
[`mathspec._resolution`][], which has the spec to say them with.
"""

from __future__ import annotations

import re
from functools import cache, lru_cache, reduce
from typing import TYPE_CHECKING, cast, get_args

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import UnexpectedCharacters, UnexpectedInput, UnexpectedToken

from mathspec._syntax import (
    MAX_DEPTH,
    AndNode,
    BinaryOperator,
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
    UnaryOperator,
    UnaryOperatorNode,
    children,
    depth,
)
from mathspec.errors import SchemaError
from mathspec.program import ComparisonOperator

if TYPE_CHECKING:
    from collections.abc import Iterable

NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'

REAL = r'\d+\.\d*([eE][+-]?\d+)?|\d+[eE][+-]?\d+'

RESERVED = ('AND', 'OR', 'NOT', 'TRUE', 'FALSE')
"""The words of the language, in any case. A name spelled as one of them is the word, wherever it stands."""

INFINITY = 'inf'
"""The name the grammar reads as the number, wherever it stands but before a call's bracket."""

RESERVED_WORDS = 'one of AND, OR, NOT, True and False, which the language reserves in any case'
"""How a refusal says a word is reserved."""

NAME_RULE = (
    f'Start it with a letter or an underscore, then use only letters, digits or underscores. It may not be '
    f'{RESERVED_WORDS}, or inf, which is the number infinity.'
)
"""What a refusal of a name tells the file to write instead."""

_GRAMMAR = rf"""
?start: disjunction
?disjunction: conjunction (_OR conjunction)*
?conjunction: negation (_AND negation)*
?negation: _NOT comparison -> negated
         | comparison
?comparison: sum (COMPARATOR sum)?
?sum: product (ADD product)*
?product: unary (MUL unary)*
?unary: ADD unary -> signed
      | power
?power: atom (_POW unary)?
?atom: NUMBER -> number
     | DOTINF -> infinity
     | NAME -> name
     | STRING -> label
     | (TRUE | FALSE) -> boolean
     | NAME _LSQB names _RSQB -> columns
     | _LSQB names _RSQB -> name_list
     | NAME _LPAR (argument (_COMMA argument)*)? _RPAR -> call
     | _LPAR disjunction _RPAR
?argument: NAME _EQUAL disjunction -> keyword
         | disjunction
names: NAME (_COMMA NAME)*

NAME: /{NAME}/
NUMBER: /{REAL}|\d+/
DOTINF: ".inf"
STRING: /'(?:\\.|[^'\n\r\\])*'|"(?:\\.|[^"\n\r\\])*"/
COMPARATOR: /<=|>=|==|!=|<|>/
ADD: /[+-]/
MUL: /[*\/]/
_POW: "**"
_LPAR: "("
_RPAR: ")"
_LSQB: "["
_RSQB: "]"
_COMMA: ","
_EQUAL: "="
%declare _AND _OR _NOT TRUE FALSE
%ignore /[ \t\r\n]+/
"""

_WHITESPACE_ESCAPES = {'t': '\t', 'n': '\n', 'f': '\f', 'r': '\r'}


def _unquoted(token: Token) -> Token:
    r"""A quoted label as the text it stands for.

    ``\t``, ``\n``, ``\f`` and ``\r`` are the whitespace character, and a
    backslash before any other character is that character, so ``'it\'s'``
    is ``it's``.
    """
    return Token.new_borrow_pos('STRING', re.sub(r'\\(.)', _escaped, token[1:-1]), token)


def _escaped(escape: re.Match[str]) -> str:
    return _WHITESPACE_ESCAPES.get(escape[1], escape[1])


def _reserved(token: Token) -> Token:
    """A name spelled as a reserved word, in any case, as the word it is."""
    word = token.upper()
    if word not in RESERVED:
        return token
    return Token.new_borrow_pos(word if word in ('TRUE', 'FALSE') else f'_{word}', token, token)


@v_args(inline=True)
class _Tree(Transformer[Token, ParsedNode]):
    """The node each rule of the grammar builds, called as the parser reduces the rule.

    No tree stands between the text and the nodes, and nothing here recurses,
    so text nested however deep builds without touching the interpreter's
    stack. A rule holding one operand alone builds nothing: the operand is
    its node, which is how parentheses leave no trace in the tree.
    """

    def number(self, token: Token) -> NumberNode:
        return NumberNode(float(token))

    def infinity(self, _: Token) -> NumberNode:
        return NumberNode(float('inf'))

    def name(self, token: Token) -> NumberNode | NameNode:
        """A bare ``inf`` is the number; as a callee or a keyword it stays a name."""
        return NumberNode(float('inf')) if token == INFINITY else NameNode(str(token))

    def label(self, token: Token) -> KeywordNode:
        return KeywordNode(str(token))

    def boolean(self, token: Token) -> BooleanNode:
        return BooleanNode(token.type == 'TRUE')

    def names(self, *names: Token) -> tuple[str, ...]:
        return tuple(str(name) for name in names)

    def columns(self, relation: Token, columns: tuple[str, ...]) -> ColumnsNode:
        return ColumnsNode(str(relation), columns)

    def name_list(self, names: tuple[str, ...]) -> NameListNode:
        return NameListNode(names)

    def keyword(self, key: Token, value: ParsedNode) -> tuple[str, ParsedNode]:
        return str(key), value

    def call(self, callee: Token, *arguments: ParsedNode | tuple[str, ParsedNode]) -> FunctionCallNode:
        """Positional and keyword arguments, each in the order written; a keyword given twice is refused."""
        name = str(callee)
        kwargs: dict[str, ParsedNode] = {}
        for key, value in (argument for argument in arguments if isinstance(argument, tuple)):
            if key in kwargs:
                msg = f'{name}({key}=) is given twice. Delete one of them.'
                raise SchemaError(msg)
            kwargs[key] = value
        return FunctionCallNode(name, tuple(a for a in arguments if not isinstance(a, tuple)), kwargs)

    def signed(self, sign: Token, operand: ParsedNode) -> UnaryOperatorNode:
        return UnaryOperatorNode(cast('UnaryOperator', str(sign)), operand)

    def power(self, base: ParsedNode, exponent: ParsedNode) -> BinaryOperatorNode:
        return BinaryOperatorNode('**', base, exponent)

    def sum(self, first: ParsedNode, *rest: Token | ParsedNode) -> ParsedNode:
        """``a op b op c`` as ``(a op b) op c``."""
        result = first
        for op, operand in zip(rest[::2], rest[1::2], strict=True):
            result = BinaryOperatorNode(cast('BinaryOperator', str(op)), result, cast('ParsedNode', operand))
        return result

    product = sum

    def comparison(self, left: ParsedNode, op: Token, right: ParsedNode) -> ComparisonNode:
        return ComparisonNode(cast('ComparisonOperator', str(op)), left, right)

    def negated(self, operand: ParsedNode) -> NotNode:
        return NotNode(operand)

    def conjunction(self, *operands: ParsedNode) -> ParsedNode:
        """``a AND b AND c`` as ``(a AND b) AND c``."""
        return reduce(AndNode, operands)

    def disjunction(self, *operands: ParsedNode) -> ParsedNode:
        return reduce(OrNode, operands)


@cache
def _parser() -> Lark:
    """The parser, built on first use: a load that parses nothing does not pay for the tables."""
    return Lark(
        _GRAMMAR,
        parser='lalr',
        lexer='basic',
        transformer=_Tree(),
        lexer_callbacks={'STRING': _unquoted, 'NAME': _reserved},
        maybe_placeholders=False,
    )


def is_name(text: str) -> bool:
    """Whether the grammar reads *text* as one name, which is what an entry, a macro's formal and a relation's column are keyed by.

    The ``NAME`` terminal, less the spellings the grammar reads as its own: a
    reserved word, in any case, and ``inf``. Answered without the parser,
    which a spec would otherwise run once for every name it declares.
    """
    return re.fullmatch(NAME, text) is not None and text.upper() not in RESERVED and text != INFINITY


@lru_cache(maxsize=8192)
def parse(text: str) -> ParsedNode:
    """Parse an expression or a where string into its tree.

    Raises:
        SchemaError: If *text* is not written in the grammar, or nests past
            [`MAX_DEPTH`][mathspec._syntax.MAX_DEPTH]. A predictable mistake
            — a chained comparison, a lone ``=``, ``^`` for power, ``&``,
            ``|``, ``~`` or ``!`` for a connective, a reserved word as a
            name — is named with its rewrite before the grammar's own
            complaint.
    """
    try:
        node = cast('ParsedNode', _parser().parse(text))
    except UnexpectedInput as error:
        at = _position(error, text)
        hint = _hint(error, text, at)
        complaint = _complaint(text, at, _expected(error))
        msg = f'Cannot parse {text!r}.\n{f"{hint}\n" if hint is not None else ""}{complaint}'
        raise SchemaError(msg) from error
    if (found := depth(node, children)) > MAX_DEPTH:
        shown = text if len(text) <= 60 else f'{text[:60]}…'
        msg = (
            f'{shown!r} nests {found} deep, past the {MAX_DEPTH} levels the language admits.\n'
            f'Reduce over a dimension with sum() rather than writing the terms out, or name a part of it under '
            f'expressions: or conditions: and refer to it by name.'
        )
        raise SchemaError(msg)
    return node


def _position(error: UnexpectedInput, text: str) -> int:
    """Where the parser gave up, as an index into *text*; the end of the text where the text ran out."""
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
    'COMPARATOR': 'a comparison',
    'TRUE': 'True',
    'FALSE': 'False',
    'POW': "'**'",
    'LPAR': "'('",
    'RPAR': "')'",
    'LSQB': "'['",
    'RSQB': "']'",
    'COMMA': "','",
    'EQUAL': "'='",
    '$END': 'the end of the text',
}


def _expected(error: UnexpectedInput) -> Iterable[str]:
    """What the parser would have taken where it gave up, each in the words a file is written in."""
    if isinstance(error, UnexpectedCharacters):
        return ('a token of the language',)
    terminals = error.accepts or error.expected if isinstance(error, UnexpectedToken) else ()
    return (_SPOKEN.get(name.strip('_'), name.strip('_')) for name in terminals)


def _complaint(text: str, at: int, expected: Iterable[str]) -> str:
    """The grammar's own complaint: what it expected, what it found, and where."""
    found = repr(text[at : at + 10]) if at < len(text) else 'the end of the text'
    line = text.count('\n', 0, at) + 1
    column = at - (text.rfind('\n', 0, at) + 1) + 1
    return f'Expected {", ".join(sorted(set(expected)))}, found {found}  (at char {at}), (line:{line}, col:{column})'


_HABITS = (
    (
        '=',
        "'=' is not a comparison. Write == for equality. A single '=' passes a keyword argument, as in sum(x, over=d).",
    ),
    ('^', "power is written '**', not '^'."),
    ('&', "'&' is not an operator. Write AND."),
    ('|', "'|' is not an operator. Write OR."),
    ('~', "'~' is not an operator. Write NOT before the condition."),
    ('!', "'!' is not an operator. Write NOT before the condition."),
)


def _hint(error: UnexpectedInput, text: str, at: int) -> str | None:
    """The rewrite for a predictable mistake at the token where the parser gave up, or ``None``.

    A comparator there is tested first, since ``==`` and ``!=`` begin with a
    character that is the habit of another language alone. It is a chained
    comparison where the parser stood after a whole one, which is where it
    would have taken no name. A reserved word written as a name stops the
    parser at the word, or, for ``NOT``, ``True`` and ``False``, at what
    follows it.
    """
    rest = text[at:].lstrip()
    if (found := next((c for c in get_args(ComparisonOperator) if rest.startswith(c)), None)) is not None:
        if isinstance(error, UnexpectedToken) and 'NAME' not in error.expected:
            return (
                f"'{found}' follows a complete comparison. Split the chain into two comparisons: two constraints, "
                f'or two conditions joined by AND.'
            )
        return None
    for habit, rewrite in _HABITS:
        if rest.startswith(habit):
            return rewrite
    return _reserved_word(text, at, rest)


def _reserved_word(text: str, at: int, rest: str) -> str | None:
    here = re.match(NAME, rest)
    before = re.search(rf'({NAME})\s*$', text[:at])
    if here and here.group().upper() in RESERVED:
        word = here.group()
    elif before and before.group(1).upper() in ('NOT', 'TRUE', 'FALSE'):
        word = before.group(1)
    else:
        return None
    return f"'{word}' is {RESERVED_WORDS}, so it is the name of no entry. Write a name in its place, or delete it."
