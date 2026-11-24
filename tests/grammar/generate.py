# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Strings for the grammar fuzzer: written from the grammar, mutated token by token, and read off the examples.

Every generator takes a seeded `random.Random`, so a failing case is
reproduced from its seed. Most written strings are in the language, so the
trees get compared and not only the refusals; the mutants are mostly not,
so the refusals get compared too. The vocabulary leans on the spellings
where a grammar decides by context: a keyword as a name, ``inf`` as a name,
``count``, a keyword glued to a number, quotes with escapes, and whitespace
the language does not allow.
"""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator
    from random import Random

    from tests.grammar.oracle import Grammar

EXAMPLES = Path(__file__).parents[2] / 'examples'

NAMES = (
    *('x', 'p', 'p_max', 'Generator_p', '_x', 'x1', 'rel', 'gen_bus', 'bus', 'snapshot', 'g', 'd'),
    *('sum', 'shift', 'position', 'over', 'by', 'edge', 'e', 'E', 'e5'),
    *('inf', 'infx', 'count', 'Count', 'COUNT', 'counts'),
    *('AND', 'and', 'And', 'andx', 'x_and', 'NOT', 'not', 'nota', 'OR', 'or', 'ori'),
    *('True', 'TRUE', 'true', 'Truex', 'False', 'false', 'FALSE'),
)

NUMBERS = ('0', '1', '7', '12', '1.', '1.5', '2.50', '1e5', '1E-3', '3.e+2', '0.25', '.inf', 'inf', '\u0663')

SPACES = (' ', ' ', ' ', ' ', '', '  ', '\t', '\n', '\r\n')

ODD = ('$', '\u017f', '\u0131', '\xa0', '\f', '\v', '\\', "'", '"', '[', ']', '=', '!', '&', '|', '~', '^', '.', ',')

TOKEN = re.compile(
    r"""\s+|[A-Za-z_][A-Za-z0-9_]*|\d+\.?\d*(?:[eE][+-]?\d+)?|\.inf|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|\*\*|<=|>=|==|!=|."""
)


def _keyword(rng: Random, word: str) -> str:
    """*word* in a random case, as a caseless keyword reads it."""
    return ''.join(c.upper() if rng.random() < 0.5 else c.lower() for c in word)


def _quoted(rng: Random) -> str:
    """A quoted label, sometimes carrying an escape, a quote of the other kind, or an unterminated tail."""
    quote = rng.choice(('"', "'"))
    pieces = (
        'a',
        'b',
        'x y',
        'wrap',
        '\\t',
        '\\n',
        '\\x41',
        '\\u0041',
        '\\101',
        '\\0',
        '\\\\',
        '\\',
        "'",
        '"',
        '(',
        ')',
    )
    body = ''.join(rng.choice(pieces) for _ in range(rng.randrange(4)))
    return f'{quote}{body}{quote}'


class _Writer:
    """One string written from the grammar, with whitespace and parentheses chosen as it goes."""

    def __init__(self, rng: Random) -> None:
        self.rng = rng

    def sp(self) -> str:
        return self.rng.choice(SPACES)

    def name(self) -> str:
        return self.rng.choice(NAMES) if self.rng.random() < 0.6 else self.rng.choice(NAMES[:12])

    def join(self, *parts: str) -> str:
        return ''.join(part + self.sp() for part in parts[:-1]) + parts[-1]

    def kwarg_value(self, depth: int, *, names: bool) -> str:
        roll = self.rng.random()
        if roll < 0.15:
            return _quoted(self.rng)
        if roll < 0.3:
            columns = ', '.join(self.name() for _ in range(self.rng.randrange(1, 3)))
            return f'{self.name()}[{columns}]'
        if roll < 0.4 and names:
            return '[' + ', '.join(self.name() for _ in range(self.rng.randrange(1, 3))) + ']'
        return self.arith(depth)

    def call(self, depth: int) -> str:
        args = []
        for _ in range(self.rng.randrange(4)):
            if self.rng.random() < 0.4:
                args.append(self.join(self.name(), '=', self.kwarg_value(depth, names=True)))
            else:
                args.append(self.arith(depth))
        return self.join(self.name(), '(', ', '.join(args), ')')

    def arith(self, depth: int) -> str:
        roll = self.rng.random() if depth > 0 else self.rng.random() * 0.45
        if roll < 0.25:
            return self.name()
        if roll < 0.45:
            return self.rng.choice(NUMBERS)
        if roll < 0.55:
            return self.call(depth - 1)
        if roll < 0.62:
            return self.join('(', self.arith(depth - 1), ')')
        if roll < 0.7:
            return self.join(self.rng.choice('+-'), self.arith(depth - 1))
        if roll < 0.78:
            return self.join(self.arith(depth - 1), '**', self.arith(depth - 1))
        return self.join(self.arith(depth - 1), self.rng.choice('+-*/'), self.arith(depth - 1))

    def expression(self) -> str:
        left = self.arith(self.rng.randrange(1, 5))
        if self.rng.random() < 0.4:
            return left
        sense = self.rng.choice(('<=', '>=', '==', '<=', '>=', '==', '<', '>', '!=', '='))
        return self.join(left, sense, self.arith(self.rng.randrange(1, 4)))

    def side(self, depth: int) -> str:
        roll = self.rng.random()
        if roll < 0.15:
            return f'{self.name()}[{self.name()}]'
        return self.arith(depth)

    def atom(self, depth: int) -> str:
        roll = self.rng.random() if depth > 0 else self.rng.random() * 0.5
        operator = self.rng.choice(('<=', '>=', '==', '!=', '<', '>'))
        if roll < 0.08:
            return _keyword(self.rng, self.rng.choice(('True', 'False')))
        if roll < 0.2:
            return self.name()
        if roll < 0.5:
            right = _quoted(self.rng) if self.rng.random() < 0.2 else self.side(2)
            return self.join(self.side(2), operator, right)
        if roll < 0.6:
            kwargs = [self.join(',', self.name(), '=', self.kwarg_value(1, names=False))]
            call = self.join(_keyword(self.rng, 'count'), '(', self.condition(depth - 1), *kwargs, ')')
            return self.join(call, operator, self.arith(1)) if self.rng.random() < 0.8 else call
        if roll < 0.72:
            kwargs = [
                self.join(',', self.name(), '=', self.kwarg_value(1, names=False)) for _ in range(self.rng.randrange(3))
            ]
            return self.join(self.name(), '(', self.condition(depth - 1), *kwargs, ')')
        return self.join('(', self.condition(depth - 1), ')')

    def not_expr(self, depth: int) -> str:
        atom = self.atom(depth)
        return self.join(_keyword(self.rng, 'NOT'), atom) if self.rng.random() < 0.2 else atom

    def condition(self, depth: int) -> str:
        text = self.not_expr(depth)
        for _ in range(self.rng.randrange(3) if depth > 0 else 0):
            text = self.join(text, _keyword(self.rng, self.rng.choice(('AND', 'OR'))), self.not_expr(depth - 1))
        return text


def written(rng: Random, grammar: Grammar) -> str:
    """One string written from *grammar*'s rules, most of them in the language."""
    writer = _Writer(rng)
    return writer.expression() if grammar == 'expression' else writer.condition(rng.randrange(1, 4))


def mutated(rng: Random, text: str) -> str:
    """*text* with one to three token edits: delete, duplicate, swap, insert, recase, or a character dropped or added."""
    tokens = TOKEN.findall(text) or ['']
    vocabulary = (*NAMES, *NUMBERS, *SPACES, *ODD, '(', ')', '**', '*', '/', '+', '-', '<=', '>=', '==', '<', '>')
    for _ in range(rng.randrange(1, 4)):
        at = rng.randrange(len(tokens))
        edit = rng.randrange(7)
        if edit == 0 and len(tokens) > 1:
            del tokens[at]
        elif edit == 1:
            tokens.insert(at, tokens[at])
        elif edit == 2 and at + 1 < len(tokens):
            tokens[at], tokens[at + 1] = tokens[at + 1], tokens[at]
        elif edit == 3:
            tokens.insert(at, rng.choice(vocabulary))
        elif edit == 4:
            tokens[at] = _keyword(rng, tokens[at])
        elif edit == 5 and tokens[at]:
            cut = rng.randrange(len(tokens[at]))
            tokens[at] = tokens[at][:cut] + tokens[at][cut + 1 :]
        else:
            tokens[at] = tokens[at] + rng.choice(ODD)
    return ''.join(tokens)


def nested_shapes(grammar: Grammar, n: int) -> tuple[str, ...]:
    """Strings that nest or chain *n* levels, in each way *grammar* can."""
    if grammar == 'expression':
        return (
            '(' * n + 'x' + ')' * n,
            '-' * n + 'x',
            ' + '.join(['x'] * n),
            '-(' * n + 'x' + ')' * n,
            'f(' * n + ')' * n,
        )
    return (
        '(' * n + 'x' + ')' * n,
        ' AND '.join(['x'] * n),
        '(NOT ' * n + 'x' + ')' * n,
        '(' * n + 'x > 0' + ')' * n,
        'x > ' + ' + '.join(['p'] * n),
    )


def deep(rng: Random, grammar: Grammar) -> str:
    """A string nested or chained near the depth cap, on either side of it."""
    return rng.choice(nested_shapes(grammar, rng.randrange(30, 130)))


def strings(rng: Random, count: int) -> Iterator[tuple[Grammar, str]]:
    """*count* strings per grammar: half written, half a mutant of a written one or of an example's, and a few deep."""
    pool = example_strings()
    for grammar in ('expression', 'condition'):
        for _ in range(count // 2):
            yield grammar, written(rng, grammar)
            seed = rng.choice(pool) if rng.random() < 0.5 else written(rng, grammar)
            yield grammar, mutated(rng, seed)
            if rng.random() < 0.02:
                yield grammar, deep(rng, grammar)


@cache
def example_strings() -> tuple[str, ...]:
    """Every string scalar in the example specs, keys included: the expressions and conditions, and prose to refuse."""
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, str):
            found.add(node)
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(key)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for path in sorted(EXAMPLES.rglob('*.yaml')):
        walk(yaml.safe_load(path.read_text(encoding='utf-8')))
    return tuple(sorted(found))
