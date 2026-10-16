# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Random edits of the specs in ``examples/``, from one seed.

A seed picks a spec from the corpus and applies one to three edits to it. An
edit works on the text of an expression or a ``where``, or on the shape of the
mapping, and most edits leave a file the language refuses: the refusal path is
what the loader oracle exercises, and a refusal is not a finding. The edits
that keep a file inside the language feed the oracles that need an accepted
spec. Everything is drawn from one ``random.Random(seed)``, so a seed is the
whole reproduction.
"""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mathspec._yaml import read_yaml
from tests.fixtures import SPECS

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: The text fields an edit of an expression or a predicate reaches.
TEXT_KEYS = frozenset({'expression', 'where', 'when', 'otherwise', 'lower', 'upper', 'template', 'check'})

TOKEN = re.compile(r"\*\*|<=|>=|==|!=|\.inf|'[^']*'|\"[^\"]*\"|[A-Za-z_]\w*|\d+(?:\.\d*)?(?:e-?\d+)?|\S")

OPERATORS = ('+', '-', '*', '/', '**', '<=', '>=', '==', '!=', '<', '>', ',', '(', ')', '[', ']', '=')
KEYWORDS = ('AND', 'OR', 'NOT', 'True', 'False', 'over', 'by', 'along', 'offset', 'window', 'edge', 'within')
FUNCTIONS = ('sum', 'sum_back', 'shift', 'at', 'position', 'count', 'dual')
NUMBERS = ('0', '-1', '1e308', '1e-320', 'inf', '.inf', '2.5', '99999999999999999999', '0.0', '1e5', '3')
VALUES = (None, [], {}, 0, -1, 1.5, '', 'x', True, False, [None], {'a': 1}, ['a', 'a'], float('inf'), 'nan')
#: Values a key of an entry takes inside the language, so an edit can stay inside it.
CHOICES = {
    'dtype': ('float', 'int', 'bool', 'str', 'datetime'),
    'missing': ('refused', 'absent', 'neutral', 0, 1, 2.5, True, False, '.inf'),
    'ordered': (True, False),
    'sense': ('minimize', 'maximize'),
    'domain': ('continuous', 'integer', 'binary'),
    'type': (1, 2),
}


@dataclass
class Mutant:
    """One edited spec, and the edits that made it."""

    seed: int
    source: str
    spec: dict[str, Any]
    edits: list[str]


def corpus() -> list[tuple[str, dict[str, Any]]]:
    """Every example spec as the raw mapping its file holds."""
    return [(path.name, read_yaml(path)) for path in SPECS]


def mutant(seed: int, specs: list[tuple[str, dict[str, Any]]]) -> Mutant:
    """The mutant *seed* draws from *specs*; seed ``n`` with no edit is the unedited spec ``n``."""
    rng = random.Random(seed)
    name, original = rng.choice(specs)
    spec = copy.deepcopy(original)
    edits = []
    for _ in range(rng.choice((1, 1, 1, 2, 3))):
        edit = rng.choice(EDITS)
        label = edit(spec, rng, specs)
        if label:
            edits.append(label)
    return Mutant(seed, name, spec, edits)


# ---------------------------------------------------------------------------
# where an edit lands
# ---------------------------------------------------------------------------


def _slots(node: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[tuple[Any, ...], Any]]:
    """Every (path, value) under *node*, the mappings and lists themselves included."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _slots(value, (*path, key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _slots(value, (*path, i))


def _set(spec: Any, path: tuple[Any, ...], value: Any) -> None:
    for key in path[:-1]:
        spec = spec[key]
    spec[path[-1]] = value


def _texts(spec: dict[str, Any]) -> list[tuple[tuple[Any, ...], str]]:
    """Every expression and predicate string, and every string a named section holds."""
    found = []
    for path, value in _slots(spec):
        if not isinstance(value, str) or not path:
            continue
        if path[-1] in TEXT_KEYS or (len(path) == 2 and path[0] in ('expressions', 'masks', 'assumptions', 'macros')):
            found.append((path, value))
    return found


def _names(spec: dict[str, Any]) -> list[str]:
    names = [name for section in spec.values() if isinstance(section, dict) for name in section]
    for section in spec.get('given', {}).values() if isinstance(spec.get('given'), dict) else ():
        if isinstance(section, dict):
            names += list(section)
    return names or ['x']


# ---------------------------------------------------------------------------
# the edits — each returns a label, or '' where it found nothing to edit
# ---------------------------------------------------------------------------


def _on_text(change: Callable[[list[str], random.Random, dict[str, Any]], str | None]) -> Callable[..., str]:
    def edit(spec: dict[str, Any], rng: random.Random, _: Any) -> str:
        texts = _texts(spec)
        if not texts:
            return ''
        path, text = rng.choice(texts)
        tokens = TOKEN.findall(text)
        if not tokens:
            return ''
        new = change(tokens, rng, spec)
        if new is None or new == text:
            return ''
        _set(spec, path, new)
        return f'{change.__name__} at {"/".join(map(str, path))}: {new!r}'

    edit.__name__ = change.__name__
    return edit


def delete_token(tokens: list[str], rng: random.Random, _: Any) -> str:
    del tokens[rng.randrange(len(tokens))]
    return ' '.join(tokens)


def duplicate_token(tokens: list[str], rng: random.Random, _: Any) -> str:
    i = rng.randrange(len(tokens))
    tokens.insert(i, tokens[i])
    return ' '.join(tokens)


def swap_tokens(tokens: list[str], rng: random.Random, _: Any) -> str | None:
    if len(tokens) < 2:
        return None
    i = rng.randrange(len(tokens) - 1)
    tokens[i], tokens[i + 1] = tokens[i + 1], tokens[i]
    return ' '.join(tokens)


def replace_name(tokens: list[str], rng: random.Random, spec: dict[str, Any]) -> str | None:
    at = [i for i, t in enumerate(tokens) if re.fullmatch(r'[A-Za-z_]\w*', t)]
    if not at:
        return None
    tokens[rng.choice(at)] = rng.choice([*_names(spec), *KEYWORDS, *FUNCTIONS, 'undeclared'])
    return ' '.join(tokens)


def replace_operator(tokens: list[str], rng: random.Random, _: Any) -> str | None:
    at = [i for i, t in enumerate(tokens) if t in OPERATORS]
    if not at:
        return None
    tokens[rng.choice(at)] = rng.choice(OPERATORS)
    return ' '.join(tokens)


def replace_number(tokens: list[str], rng: random.Random, _: Any) -> str | None:
    at = [i for i, t in enumerate(tokens) if re.fullmatch(r'\d.*|\.inf', t)]
    i = rng.choice(at) if at else rng.randrange(len(tokens))
    tokens[i] = rng.choice(NUMBERS)
    return ' '.join(tokens)


def wrap(tokens: list[str], rng: random.Random, spec: dict[str, Any]) -> str:
    """Wrap the text in an operator call, with arguments drawn from the spec's names."""
    text, names = ' '.join(tokens), _names(spec)
    pick = lambda: rng.choice(names)  # noqa: E731 — a draw, read where the argument is written
    return rng.choice(
        (
            f'sum({text})',
            f'sum({text}, over={pick()})',
            f'sum({text}, over=[{pick()}, {pick()}])',
            f'sum({text}, over={pick()}, by={pick()}[{pick()}])',
            f'at({text}, by={pick()}[{pick()}])',
            f'shift({text}, along={pick()}, offset={rng.choice((1, -1, 0, 2))})',
            f'shift({text}, along={pick()}, offset=1, edge={rng.choice(("0", chr(39) + "wrap" + chr(39), "1.5", pick()))})',
            f'shift({text}, along={pick()}, offset=1, within={pick()}[{pick()}])',
            f'sum_back({text}, along={pick()}, window={rng.choice((1, 2, 0, -1))})',
            f'dual({text})',
            f'({text}) / ({text})',
            f'({text}) ** ({text})',
            f'({text}) * ({text})',
            f'-({text})',
            f'position({text}) == 0',
            f'count({text}, over={pick()}) >= 1',
            f'NOT ({text})',
            f'({text}) AND ({text})',
        )
    )


def nest(tokens: list[str], rng: random.Random, _: Any) -> str:
    """Nest the text past the depth limits the reference states."""
    text, depth = ' '.join(tokens), rng.choice((99, 100, 101, 150, 301, 1000))
    return rng.choice(('(' * depth + text + ')' * depth, '-' * depth + text, 'NOT ' * depth + text))


def duplicate_keyword(tokens: list[str], rng: random.Random, _: Any) -> str | None:
    text = ' '.join(tokens)
    match = re.search(r'(\w+) = ([^,)]+)', text)
    if match is None:
        return None
    return text[: match.end()] + f' , {match.group(0)}' + text[match.end() :]


def splice(spec: dict[str, Any], rng: random.Random, specs: list[tuple[str, dict[str, Any]]]) -> str:
    """An expression from another spec of the corpus, in place of one of this one's."""
    texts, others = _texts(spec), [t for _, other in specs for t in _texts(other)]
    if not texts or not others:
        return ''
    (path, _), (_, new) = rng.choice(texts), rng.choice(others)
    _set(spec, path, new)
    return f'splice at {"/".join(map(str, path))}: {new!r}'


def delete_key(spec: dict[str, Any], rng: random.Random, _: Any) -> str:
    slots = [(p, v) for p, v in _slots(spec) if p and isinstance(v, (dict, list, str, int, float, bool))]
    path, _ = rng.choice(slots)
    parent = spec
    for key in path[:-1]:
        parent = parent[key]
    del parent[path[-1]]
    return f'delete {"/".join(map(str, path))}'


def retype(spec: dict[str, Any], rng: random.Random, _: Any) -> str:
    path, _ = rng.choice([s for s in _slots(spec) if s[0]])
    value = rng.choice(CHOICES.get(path[-1], VALUES)) if rng.random() < 0.5 else rng.choice(VALUES)
    _set(spec, path, copy.deepcopy(value))
    return f'set {"/".join(map(str, path))} = {value!r}'


def rename(spec: dict[str, Any], rng: random.Random, _: Any) -> str:
    """Rename an entry to another name the spec uses, or to a near miss of a section key."""
    sections = [s for s, v in spec.items() if isinstance(v, dict) and v]
    if not sections:
        return ''
    section = rng.choice(sections)
    old = rng.choice(list(spec[section]))
    new = rng.choice([*_names(spec), *FUNCTIONS, 'True', 'inf', 'AND', f'{old}_', '_', 'x y', '1a'])
    spec[section] = {new if k == old else k: v for k, v in spec[section].items()}
    return f'rename {section}/{old} to {new!r}'


def edit_dims(spec: dict[str, Any], rng: random.Random, _: Any) -> str:
    lists = [
        (p, v) for p, v in _slots(spec) if p and p[-1] in ('dims', 'key', 'values', 'over') and isinstance(v, list)
    ]
    if not lists:
        return ''
    path, dims = rng.choice(lists)
    dims = list(dims)
    names = list(spec.get('dimensions', {})) or ['x']
    choice = rng.randrange(4)
    if choice == 0 and dims:
        dims.pop(rng.randrange(len(dims)))
    elif choice == 1:
        dims.append(rng.choice(names))
    elif choice == 2:
        rng.shuffle(dims)
    else:
        dims.append(dims[0] if dims else 'undeclared')
    _set(spec, path, dims)
    return f'dims {"/".join(map(str, path))} = {dims}'


def add_unknown_key(spec: dict[str, Any], rng: random.Random, _: Any) -> str:
    mappings = [(p, v) for p, v in _slots(spec) if isinstance(v, dict)]
    path, mapping = rng.choice(mappings)
    key = rng.choice(('boundz', 'dim', 'expr', 'version', 'description', 'given', 'cases', 'otherwise', '<<'))
    mapping[key] = rng.choice(VALUES)
    return f'add {key!r} under {"/".join(map(str, path)) or "the top"}'


EDITS: tuple[Callable[[dict[str, Any], random.Random, list[tuple[str, dict[str, Any]]]], str], ...] = (
    *(
        _on_text(change)
        for change in (
            delete_token, duplicate_token, swap_tokens, replace_name, replace_name, replace_operator,
            replace_number, wrap, wrap, wrap, nest, duplicate_keyword,
        )
    ),
    splice, delete_key, retype, rename, edit_dims, add_unknown_key,
)  # fmt: skip
