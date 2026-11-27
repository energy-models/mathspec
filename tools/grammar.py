# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The language reference's two grammars, printed from the grammars mathspec parses with.

    pixi run python -m tools.grammar           # rewrite the blocks
    pixi run python -m tools.grammar --check   # fail if they have drifted

The expression grammar is the parser's own. The where grammar the parser
builds is wider than the language, and its reader narrows it; [`WHERE_RULES`][]
states the narrowed language as a grammar, which the grammar fuzzer holds to
exactly what ``parse_condition`` accepts.
"""

from __future__ import annotations

import re

from mathspec._condition_parser import _CONDITION_RULES, _KEYWORD_EDGE, RESERVED
from mathspec._expression_parser import _EXPRESSION_RULES, ARITHMETIC_RULES, NAME
from tools._page import ROOT, splice
from tools._page import main as page_main

PAGE = ROOT / 'docs' / 'reference' / 'language' / 'expressions.md'
EXPRESSION = ('<!-- expression-grammar:begin -->', '<!-- expression-grammar:end -->')
WHERE = ('<!-- where-grammar:begin -->', '<!-- where-grammar:end -->')

#: The arithmetic an expression and a where string share, below the top
#: rule: the expression grammar's own atoms, calls and keyword values.
ARITHMETIC_ATOMS = _EXPRESSION_RULES.split('\n', 2)[2].split('\nSENSE:')[0]

#: The where language as a grammar: what the parser's grammar and its reader
#: accept together. The parser cannot use it, since LALR(1) cannot tell a
#: condition call from an arithmetic one before the ``)``; the fuzzer checks
#: it with Lark's Earley parser.
WHERE_RULES = r"""
start: or_
?or_: and_ (_OR and_)*
?and_: not_ (_AND not_)*
?not_: _NOT operand -> negation
     | operand
?operand: TRUE
        | FALSE
        | NAME
        | count
        | comparison
        | condition_call
        | LPAR or_ _RPAR -> paren
count.2: count_call COMP sum -> cmp
comparison: side COMP right_side -> cmp
?side: NAME LSQB one_name _RSQB -> columns
     | sum
?right_side: STRING
           | side
count_call: COUNT LPAR condition_args _RPAR -> call
condition_call: NAME LPAR condition_args _RPAR -> call
condition_args: or_ (_COMMA condition_kwarg)* -> args
condition_kwarg: NAME _EQUAL condition_value -> kwarg
?condition_value: STRING
                | NAME LSQB names _RSQB -> columns
                | sum
one_name: NAME -> names
"""

_RESERVED_PATTERN = '|'.join(word.lower() for word in RESERVED)


def where_grammar() -> str:
    """[`WHERE_RULES`][] with the arithmetic and the terminals of the parser's own where grammar, for Lark's Earley parser.

    ``NAME`` refuses a reserved word itself, since Earley's lexer tries a
    terminal only where the grammar expects one, and ``count`` is the one call
    the grammar reads by name.
    """
    terminals = [line for line in _CONDITION_RULES.splitlines() if re.match(r'_?[A-Z]+(\.\d+)?:', line)]
    reserved_name = (
        f'NAME: /(?!(?i:{_RESERVED_PATTERN})(?!{_KEYWORD_EDGE})){NAME}/\n'
        f'COUNT: /(?<!{_KEYWORD_EDGE})(?i:count)(?!{_KEYWORD_EDGE})/\n'
    )
    arithmetic = ARITHMETIC_RULES.replace(f'NAME: /{NAME}/\n', reserved_name)
    return '\n'.join([WHERE_RULES, arithmetic, ARITHMETIC_ATOMS, *terminals, ''])


# ---------------------------------------------------------------------------
# Printing a Lark grammar as the reference's EBNF
# ---------------------------------------------------------------------------

#: The reference's name for each rule. A rule with no row here stops the
#: print, so a new rule cannot reach the page under its code name.
RULE_NAMES = {
    'start': None,
    'sum': 'arithmetic',
    'product': 'term',
    'unary': 'factor',
    'power': 'power',
    'atom': 'atom',
    'args': 'arguments',
    'arg': 'argument',
    'value': 'keyword_value',
    'names': 'names',
    'or_': 'condition',
    'and_': 'conjunction',
    'not_': 'negation',
    'operand': 'operand',
    'count': 'count',
    'comparison': 'comparison',
    'side': 'side',
    'right_side': 'right_side',
    'count_call': 'count_call',
    'condition_call': 'condition_call',
    'condition_args': 'condition_arguments',
    'condition_kwarg': 'condition_kwarg',
    'condition_value': 'condition_value',
    'one_name': None,
}

#: How the reference writes each caseless word, which any case matches.
KEYWORDS = {'and': 'AND', 'or': 'OR', 'not': 'NOT', 'true': 'True', 'false': 'False', 'count': 'count'}

#: Terminals the reference names rather than spells, with what each is.
NAMED_TERMINALS = {
    'NAME': 'NAME',
    'NUMBER': 'NUMBER',
    'STRING': 'QUOTED',
}

#: Terminals of several literals the reference names, and defines below the rules from their pattern.
LISTED_TERMINALS = {'COMP': 'COMPARATOR', 'SENSE': 'COMPARATOR'}


def _spelled(name: str, definition: str) -> str:
    """A terminal as the reference writes it: its literal, or its literals as alternatives.

    Raises:
        KeyError: A terminal whose pattern is neither literals nor named in
            [`NAMED_TERMINALS`][], so its spelling cannot be read off it.
    """
    if name in NAMED_TERMINALS:
        return NAMED_TERMINALS[name]
    literal = re.fullmatch(r'"(.*)"', definition)
    if literal:
        return f'"{literal[1]}"'
    pattern = re.fullmatch(r'/(.*)/', definition)
    body = pattern[1] if pattern else ''
    if keyword := re.search(r'\(\?i:([a-z]+)\)', body):
        return f'"{KEYWORDS[keyword[1]]}"'
    if body.startswith('(?<!') and '\\.inf' in body:
        return '".inf"'
    if klass := re.fullmatch(r'\[([^\]]+)\]', body):
        chars = klass[1].replace('\\', '')
        return '(' + ' | '.join(f'"{c}"' for c in chars) + ')'
    if re.fullmatch(r'[^\\()\[\]?*+.]+(\|[^\\()\[\]?*+.]+)+', body):
        return '(' + ' | '.join(f'"{alt}"' for alt in body.split('|')) + ')'
    raise KeyError(f'terminal {name} has no spelling for the reference: name it in NAMED_TERMINALS')


#: One piece of the regexes the terminals are written in: an escape, a class, an operator, or a character.
_REGEX_PIECE = re.compile(r'\\d|\(\?:|\[\^?(?:\\.|[^\]])*\]|\\.|[()?*+|.]|.')

#: How a W3C character class writes what a regex class escapes.
_CLASS_ESCAPES = {'\\n': '#xA', '\\r': '#xD', '\\\\': '#x5C', '\\/': '/'}


def _literal(char: str) -> str:
    return f"'{char}'" if char == '"' else f'"{char}"'


def w3c(regex: str) -> str:
    """*regex*, of the few constructs the terminals use, in the W3C EBNF notation of XML 1.0, section 6.

    Raises:
        KeyError: A construct the notation has no spelling for, such as a
            lookaround, so the reference cannot print it.
    """
    pieces = []
    for piece in _REGEX_PIECE.findall(regex):
        if piece == '\\d':
            pieces.append('[0-9]')
        elif piece == '(?:':
            pieces.append('(')
        elif piece.startswith('['):
            inner = piece[1:-1]
            for escape, spelled in _CLASS_ESCAPES.items():
                inner = inner.replace(escape, spelled)
            if inner.endswith('-'):
                inner = '-' + inner[:-1]
            pieces.append(f'[{inner}]')
        elif piece == '.':
            pieces.append('[^#xA]')
        elif piece in '()?*+|':
            pieces.append(piece)
        elif piece.startswith('\\'):
            pieces.append(_literal(piece[1]))
        elif piece == '(?':
            raise KeyError(f'{regex} has a construct W3C EBNF cannot print')
        else:
            pieces.append(_literal(piece))
    text = ''
    for piece in pieces:
        text += piece if not text or text.endswith('(') or piece in (')', '?', '*', '+') else f' {piece}'
    return text


def _raw(grammar: str) -> dict[str, str]:
    """Each regex terminal *grammar* defines, by name, as its pattern."""
    return {m[1]: m[2] for m in re.finditer(r'^(_?[A-Z]+)(?:\.\d+)?:\s*/(.+)/$', grammar, re.MULTILINE)}


def _terminals(grammar: str) -> dict[str, str]:
    """Each terminal *grammar* defines, by name, as the reference spells it."""
    found = {}
    for line in grammar.splitlines():
        if m := re.match(r'(_?[A-Z]+)(?:\.\d+)?:\s*(.+)$', line):
            found[m[1]] = _spelled(m[1], m[2].strip())
    return found


def _rules(grammar: str) -> list[tuple[str, list[str]]]:
    """Each rule of *grammar*, in order, as its name and its alternatives as written."""
    rules: list[tuple[str, list[str]]] = []
    for line in grammar.splitlines():
        if m := re.match(r'\??([a-z_]+)(?:\.\d+)?:\s*(.*)$', line):
            rules.append((m[1], [m[2]]))
        elif line.lstrip().startswith('|') and rules:
            rules[-1][1].append(line.lstrip()[1:].strip())
    return rules


def printed(grammar: str, top: str, reserved: tuple[str, ...] = ()) -> str:
    """*grammar* in the W3C EBNF notation of XML 1.0, section 6: rule names as the reference says them, aliases gone.

    A top rule that only names another is left out, and *top* names that one.
    What the notation cannot say, that a keyword matches in any case and that
    ``NAME`` excludes the *reserved* words, is one comment under the rules.

    Raises:
        KeyError: A rule with no row in [`RULE_NAMES`][], or a terminal with no
            spelling.
    """
    terminals = _terminals(grammar)
    rules = _rules(grammar)
    passthrough = rules[0][0] == 'start' and re.fullmatch(r'[a-z_]+', rules[0][1][0])
    if passthrough:
        rules = rules[1:]
    inlined = {rule: alts[0] for rule, alts in rules if rule != 'start' and RULE_NAMES[rule] is None}
    rules = [(rule, alts) for rule, alts in rules if rule not in inlined]
    names = {rule: RULE_NAMES[rule] for rule, _ in rules}
    names[rules[0][0] if passthrough else 'start'] = top

    def shown(alternative: str) -> str:
        written = re.sub(r'\s*->\s*\w+$', '', alternative)
        written = re.sub(r'\[(\w+)\]', r'\1?', re.sub(r'\[([^\[\]]+ [^\[\]]+)\]', r'(\1)?', written))
        return re.sub(r'\b[A-Za-z_]+\b', lambda m: word(m[0]), written)

    def word(token: str) -> str:
        if token in inlined:
            return shown(inlined[token])
        if token in names:
            return names[token]
        if token in LISTED_TERMINALS:
            return LISTED_TERMINALS[token]
        if token in terminals:
            return terminals[token]
        raise KeyError(f'{token} is in the grammar and not in RULE_NAMES or its terminals')

    lines = []
    width = max(len(name) for name in names.values())
    for rule, alternatives in rules:
        first, *rest = (shown(alternative) for alternative in alternatives)
        lines.append(f'{names[rule]:<{width}} ::= {first}')
        lines.extend(f'{"":<{width}}   | {alternative}' for alternative in rest)
    body = '\n'.join(lines)
    raw = _raw(grammar)
    definitions = {
        'NAME': w3c(NAME),
        'NUMBER': w3c(raw['NUMBER']),
        'QUOTED': w3c(raw['STRING']),
        **{listed: terminals[t][1:-1] for t, listed in LISTED_TERMINALS.items() if t in terminals},
    }
    used = [name for name in definitions if re.search(rf'\b{name}\b', body)]
    width = max(len(name) for name in used)
    words = [w for w in KEYWORDS.values() if f'"{w}"' in body]
    notes = ['[0-9] is a decimal digit of any script.']
    if reserved:
        notes.append(f'{_listed(words)} match in any case.')
        notes.append(f'NAME is none of {_listed([KEYWORDS[r.lower()] for r in reserved])}, in any case.')
    comment = f'/* {" ".join(notes)} */'
    fence = '\n'.join(['```text', body, *(f'{name:<{width}} ::= {definitions[name]}' for name in used), comment, '```'])
    return f'\n{fence}\n'


def _listed(words: list[str]) -> str:
    return ', '.join(words[:-1]) + f' and {words[-1]}' if len(words) > 1 else ''.join(words)


def expression_grammar() -> str:
    """The parser's expression grammar, its rules in reading order: the top, then arithmetic, then its atoms."""
    top, rest = _EXPRESSION_RULES.split('\n', 2)[1:]
    return '\n'.join([top, ARITHMETIC_RULES, ARITHMETIC_ATOMS, 'SENSE:' + rest.split('\nSENSE:')[1]])


def rendered(page: str) -> str:
    """The reference page with both grammar blocks printed from the grammars."""
    page = splice(page, *EXPRESSION, printed(expression_grammar(), 'expression'))
    return splice(page, *WHERE, printed(where_grammar(), 'condition', RESERVED))


def main(argv: list[str] | None = None) -> int:
    return page_main(argv, {PAGE: rendered}, 'grammar')


if __name__ == '__main__':
    raise SystemExit(main())
