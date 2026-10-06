# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The checked-in JSON Schema for what ``Program.to_dict()`` writes.

    pixi run python -m tools.program_schema   # rewrite schema/mathspec.program.schema.json

Read off the type annotations of the dataclasses a ``Program`` reaches, so a
field added to a node lands in the schema on the next run. A reader in another
language needs this file and no Python class.
"""

from __future__ import annotations

import datetime
import json
import sys
import types
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Literal, Union, get_args, get_origin, get_type_hints

from mathspec import program as p
from mathspec._program_json import _BY_NAME
from tools._page import ROOT
from tools._page import main as page_main

PATH = ROOT / 'schema' / 'mathspec.program.schema.json'
DIALECT = 'https://json-schema.org/draft/2020-12/schema'

#: The unions a field names by alias, kept as one definition each rather than spelled out at every field.
ALIASES: dict[str, tuple[object, ...]] = {'Expression': get_args(p.Expression), 'Predicate': get_args(p.Predicate)}

#: The tagged scalars JSON cannot spell, keyed by tag.
TAGGED: dict[str, dict[str, object]] = {
    'float': {'enum': ['inf', '-inf']},
    'date': {'type': 'string', 'format': 'date'},
    'datetime': {'type': 'string', 'format': 'date-time'},
}


def _ref(name: str) -> dict[str, object]:
    return {'$ref': f'#/$defs/{name}'}


def _tag(tag: str, properties: dict[str, object]) -> dict[str, object]:
    """An object whose ``node`` key is *tag*, with every one of *properties* required."""
    return {
        'type': 'object',
        'properties': {'node': {'const': tag}, **properties},
        'required': ['node', *properties],
        'additionalProperties': False,
    }


def _members(schema: dict[str, object]) -> list[dict[str, object]]:
    """The alternatives *schema* stands for, so a union of unions is one flat ``anyOf``."""
    nested = schema.get('anyOf')
    return list(nested) if isinstance(nested, list) else [schema]


class _Schema:
    """One walk over the annotations from ``Program`` down, collecting a definition per node class it meets."""

    def __init__(self) -> None:
        self.defs: dict[str, object] = {name: _tag(name, {'value': shape}) for name, shape in TAGGED.items()}
        self.defs |= {name: {'anyOf': [self.of(member) for member in members]} for name, members in ALIASES.items()}

    def of(self, hint: object) -> dict[str, object]:
        """The schema of one annotation."""
        origin, args = get_origin(hint), get_args(hint)
        if origin in {Union, types.UnionType}:
            members = self._union(args)
            return members[0] if len(members) == 1 else {'anyOf': members}
        if origin is Literal:
            return {'enum': list(args)}
        if origin is tuple:
            if args[1:] == (Ellipsis,):
                return {'type': 'array', 'items': self.of(args[0])}
            items = [self.of(arg) for arg in args]
            return {'type': 'array', 'prefixItems': items, 'minItems': len(items), 'maxItems': len(items)}
        if origin is Mapping:
            return _tag('Mapping', {'entries': {'type': 'object', 'additionalProperties': self.of(args[1])}})
        if isinstance(hint, type) and is_dataclass(hint):
            self._define(hint)
            return _ref(hint.__name__)
        return self._scalar(hint)

    def _union(self, args: tuple[object, ...]) -> list[dict[str, object]]:
        """Each member's schema, an alias's members folded into one reference to it."""
        rest = list(args)
        out: list[dict[str, object]] = []
        for name, members in ALIASES.items():
            if set(members) <= set(rest):
                rest = [arg for arg in rest if arg not in members]
                out.append(_ref(name))
        out += [self.of(arg) for arg in rest]
        return [flat for member in out for flat in _members(member)]

    def _scalar(self, hint: object) -> dict[str, object]:
        """A scalar, and the tagged forms its value may take."""
        if hint is datetime.date:
            return {'anyOf': [_ref('date'), _ref('datetime')]}
        scalars: dict[object, dict[str, object]] = {
            type(None): {'type': 'null'},
            bool: {'type': 'boolean'},
            int: {'type': 'integer'},
            float: {'anyOf': [{'type': 'number'}, _ref('float')]},
            str: {'type': 'string'},
        }
        return scalars[hint]

    def _define(self, cls: type) -> None:
        """Add *cls*, its name reserved first: a node reaches itself through its own fields."""
        if cls.__name__ in self.defs:
            return
        self.defs[cls.__name__] = {}
        hints = get_type_hints(cls, localns={'datetime': datetime})
        skip = 'relation' if cls in _BY_NAME else None
        properties = {f.name: self.of(hints[f.name]) for f in fields(cls) if f.name != skip}
        self.defs[cls.__name__] = _tag(cls.__name__, properties)


def rendered() -> str:
    """The schema document, byte for byte as it lives in the repo."""
    schema = _Schema()
    document = {
        '$schema': DIALECT,
        'title': 'mathspec program',
        'description': 'What Program.to_dict() writes: every node is an object whose "node" key names its class.',
        **schema.of(p.Program),
        '$defs': schema.defs,
    }
    return json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + '\n'


def main(argv: list[str] | None = None) -> int:
    return page_main(argv, {PATH: lambda _: rendered()}, 'program_schema')


if __name__ == '__main__':
    sys.exit(main())
