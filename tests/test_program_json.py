# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A program written to JSON reads back as the same program, in the shape the schema says."""

from __future__ import annotations

import json
import math
from typing import Any

import pytest

from mathspec.__main__ import main
from mathspec._program_json import from_dict
from mathspec.program import Constant, ObjectiveDeclaration, Program
from tests.fixtures import EXAMPLES, schema_of
from tests.test_canonical import FIXTURE, SPECS
from tools import program_schema

#: The leaves no example reaches: a datetime and a date literal, a relation pair, a variable's existence, a literal mask.
LEAVES: dict[str, Any] = {
    'dimensions': {'snapshot': {'dtype': 'datetime'}, 'line': {'dtype': 'str'}, 'bus': {'dtype': 'str'}},
    'relations': {'from_bus': {'key': 'line', 'values': 'bus'}, 'to_bus': {'key': 'line', 'values': 'bus'}},
    'variables': {
        'p': {
            'dims': ['snapshot', 'line'],
            'where': "from_bus != to_bus AND snapshot >= '2030-01-01T06:00' AND snapshot < '2030-01-02'",
        },
        'q': {'dims': ['snapshot', 'line'], 'where': 'p'},
        'r': {'dims': ['line'], 'where': 'False'},
    },
}

SOURCES = [*((path.stem, path) for path in [*SPECS, FIXTURE]), ('leaves', LEAVES)]
KINDS: list[tuple[str, ...] | None] = [None, ('piecewise',), ('sos',), ()]

#: Every distinct program: as written, then each expansion that writes something out.
PROGRAMS = {
    f'{name}-{"+".join(kinds or ["expanded"]) if kinds is not None else "as-written"}': expanded.program
    for name, source in SOURCES
    for spec in [schema_of(source)]
    for kinds in KINDS
    for expanded in [spec if kinds is None else spec.expand(*kinds)]
    if kinds is None or expanded is not spec
}
SCHEMA = json.loads(program_schema.PATH.read_text())


def _resolved(schema: dict[str, Any]) -> dict[str, Any]:
    """The definition a ``$ref`` points at; a nested ``anyOf`` stays as it is."""
    return SCHEMA['$defs'][schema['$ref'].rpartition('/')[2]] if '$ref' in schema else schema


def _errors(value: object, schema: dict[str, Any], at: str = '$') -> list[str]:
    """Where *value* breaks *schema*, for the keywords the generated schema uses.

    No JSON Schema validator is a dependency, so the test reads the keywords
    the generator writes itself; ``format`` and the array sizes it reads as
    one length check.
    """
    if '$ref' in schema:
        return _errors(value, _resolved(schema), at)
    if 'anyOf' in schema:
        options = [_resolved(option) for option in schema['anyOf']]
        if isinstance(value, dict):
            options = [
                o
                for o in options
                if o.get('properties', {}).get('node', {}).get('const', value['node']) == value['node']
            ]
        return [] if any(not _errors(value, option, at) for option in options) else [f'{at}: no option fits']
    if 'const' in schema or 'enum' in schema:
        return [] if value in schema.get('enum', [schema.get('const')]) else [f'{at}: {value!r} not allowed']
    kinds = {'null': type(None), 'boolean': bool, 'string': str, 'object': dict, 'array': list}
    kind = schema['type']
    if kind in {'integer', 'number'}:
        numeric = int if kind == 'integer' else (int, float)
        return [] if isinstance(value, numeric) and not isinstance(value, bool) else [f'{at}: not a {kind}']
    if not isinstance(value, kinds[kind]):
        return [f'{at}: not a {kind}']
    if isinstance(value, list):
        shapes = schema.get('prefixItems') or [schema['items']] * len(value)
        sized = len(shapes) == len(value)
        return [e for i, item in enumerate(value) for e in _errors(item, shapes[i], f'{at}[{i}]')] if sized else [at]
    if isinstance(value, dict):
        properties = schema.get('properties', {})
        missing = [f'{at}.{key}: missing' for key in schema.get('required', []) if key not in value]
        extra = schema.get('additionalProperties', True)
        found = [
            e
            for key, item in value.items()
            for e in (
                _errors(item, properties.get(key, extra), f'{at}.{key}')
                if key in properties or isinstance(extra, dict)
                else ([] if extra else [f'{at}.{key}: not allowed'])
            )
        ]
        return missing + found
    return []


@pytest.mark.parametrize('name', PROGRAMS)
def test_a_program_reads_back_from_its_json(name):
    """Equal as a program, and written to the same text again, so an int read back as a float would still show."""
    program = PROGRAMS[name]
    text = json.dumps(program.to_dict(), allow_nan=False)
    back = from_dict(json.loads(text))
    assert back == program
    assert json.dumps(back.to_dict(), allow_nan=False) == text


@pytest.mark.parametrize('name', PROGRAMS)
def test_the_export_fits_the_schema(name):
    assert _errors(PROGRAMS[name].to_dict(), SCHEMA) == []


def test_the_examples_reach_every_node_the_schema_names():
    """Without this, a node no program holds is a schema entry nothing checks."""
    tags = {match for program in PROGRAMS.values() for match in _tags(program.to_dict())}
    defined = {name for name, shape in SCHEMA['$defs'].items() if 'properties' in shape}
    assert defined - tags == set(), 'a node kind in the schema that no program in the suite exports'


def _tags(value: object) -> set[str]:
    if isinstance(value, list):
        return {tag for item in value for tag in _tags(item)}
    if isinstance(value, dict):
        own = {value['node']} if isinstance(value.get('node'), str) else set()
        return own.union(*(_tags(item) for item in value.values()))
    return set()


def test_a_nan_has_no_json_form():
    """A NaN would print as `NaN`, which strict JSON refuses, so the export refuses it first."""
    program = Program(
        parameters={}, variables={}, constraints={}, objective=ObjectiveDeclaration('minimize', Constant(math.nan))
    )
    with pytest.raises(ValueError, match='NaN has no JSON form'):
        program.to_dict()


@pytest.mark.parametrize('expand', [False, True], ids=['as-written', 'expanded'])
def test_the_shell_prints_the_program(capsys, expand):
    spec = schema_of(EXAMPLES / 'piecewise.yaml')
    assert main(['program', *(['--expand'] * expand), str(EXAMPLES / 'piecewise.yaml')]) == 0
    assert from_dict(json.loads(capsys.readouterr().out)) == (spec.expand() if expand else spec).program
