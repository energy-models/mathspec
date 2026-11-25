# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The one grammar of the language, and the two parsers over it — package-private.

An expression and a condition are written in one grammar and parse to one
tree ([`mathspec._syntax`][]). The grammar reads what was written and decides
nothing about what it means: that a constraint holds one comparison, that
``AND`` joins truth values, that ``edge=`` takes a label, are rules of
[`mathspec._resolution`][], which has the spec to say them with. The two
parsers differ in one thing: a where string reserves ``AND``, ``OR``,
``NOT``, ``True`` and ``False``, and an expression reads them as names.
"""

from __future__ import annotations

import re
from functools import cache, lru_cache, reduce
from typing import TYPE_CHECKING, Literal, cast, get_args

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
"""The words of a where string, in any case. A name spelled as one of them is the word there, wherever it stands."""

RESERVED_WORDS = 'one of AND, OR, NOT, True and False, which a where string reserves in any case'
"""How a refusal says a word is reserved."""
"""How a refusal says a word is reserved."""

Text = Literal['expression', 'condition']

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
    """A name spelled as a reserved word, in any case, as the word it is in a where string."""
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
        return NumberNode(float('inf')) if token == 'inf' else NameNode(str(token))

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
def _parser(text: Text) -> Lark:
    """The parser for one kind of text, built on first use: a load that parses nothing does not pay for the tables."""
    callbacks = {'STRING': _unquoted, **({'NAME': _reserved} if text == 'condition' else {})}
    return Lark(
        _GRAMMAR, parser='lalr', lexer='basic', transformer=_Tree(), lexer_callbacks=callbacks, maybe_placeholders=False
    )


@lru_cache(maxsize=4096)
def parse_expression(text: str) -> ParsedNode:
    """Parse a math expression string into its tree.

    Raises:
        SchemaError: If *text* is not written in the grammar, or nests past
            [`MAX_DEPTH`][mathspec._syntax.MAX_DEPTH]. A predictable mistake
            — a chained comparison, a lone ``=``, ``^`` for power — is named
            with its rewrite before the grammar's own complaint.
    """
    return _parse(text, 'expression')


@lru_cache(maxsize=4096)
def parse_condition(text: str) -> ParsedNode:
    """Parse a where string into its tree.

    Raises:
        SchemaError: If *text* is not written in the grammar, or nests past
            [`MAX_DEPTH`][mathspec._syntax.MAX_DEPTH]. A predictable mistake
            — ``&``, ``|``, ``~`` or ``!`` for a connective, a lone ``=``, a
            reserved word as a name — is named with its rewrite before the
            grammar's own complaint.
    """
    return _parse(text, 'condition')


def _parse(text: str, what: Text) -> ParsedNode:
    try:
        node = cast('ParsedNode', _parser(what).parse(text))
    except UnexpectedInput as error:
        at = _position(error, text)
        hint = _hint(what, text, at)
        complaint = _complaint(text, at, _expected(error))
        msg = f'Cannot parse the {what} {text!r}.\n{f"{hint}\n" if hint is not None else ""}{complaint}'
        raise SchemaError(msg) from error
    if (found := depth(node, children)) > MAX_DEPTH:
        shown = text if len(text) <= 60 else f'{text[:60]}…'
        msg = (
            f'The {what} nests {found} deep, past the {MAX_DEPTH} levels the language admits: {shown!r}\n'
            f'{_DEEP_REWRITE[what]}'
        )
        raise SchemaError(msg)
    return node


_DEEP_REWRITE: dict[Text, str] = {
    'expression': (
        'Reduce over a dimension with sum() rather than writing the terms out, or name an intermediate '
        'quantity under expressions: and refer to it by name.'
    ),
    'condition': (
        'Declare a parameter or relation carrying part of the test and name that here, or split the '
        'entry into two, each masked by one half.'
    ),
}


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


_HABITS: dict[Text, tuple[tuple[str, str], ...]] = {
    'expression': (
        ('=', "A single '=' passes a keyword argument, as in sum(x, over=d). Write == for equality."),
        ('^', "power is written '**', not '^'."),
    ),
    'condition': (
        ('&', "'&' is not a condition operator. Write AND."),
        ('|', "'|' is not a condition operator. Write OR."),
        ('~', "'~' is not a condition operator. Write NOT before the condition."),
        ('!', "'!' is not a condition operator. Write NOT before the condition."),
        ('=', "'=' is not a comparison. Write ==."),
    ),
}


def _hint(what: Text, text: str, at: int) -> str | None:
    """The rewrite for a predictable mistake at the token where the parser gave up, or ``None``.

    A comparator there is tested first, since ``==`` and ``!=`` begin with a
    character that is the habit of another language alone. In an expression
    it is a chained comparison where one came before it. In a where string,
    a reserved word written as a name stops the parser at the word, or, for
    ``NOT``, ``True`` and ``False``, at what follows it.
    """
    rest = text[at:].lstrip()
    comparators = get_args(ComparisonOperator)
    if (found := next((c for c in comparators if rest.startswith(c)), None)) is not None:
        if what == 'expression' and any(comparator in text[:at] for comparator in comparators):
            return f"'{found}' follows a complete comparison. Split the chain into two constraints."
        return None
    for habit, rewrite in _HABITS[what]:
        if rest.startswith(habit):
            return rewrite
    return _reserved_word(text, at, rest) if what == 'condition' else None


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
