# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`Spec.compile_expression` gives what the entry would compile to as one more entry of the spec.

The other way to get that node is to write the spec out with the entry
added, load it and read the entry back. Every test here holds the two to
the same node, or to a refusal of the same class.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from mathspec import to_spec
from mathspec.errors import DimensionError, LanguageError, MathSpecError, SchemaError

if TYPE_CHECKING:
    from mathspec.spec import Spec

EXAMPLES = Path(__file__).parents[1] / 'examples'

SPLICED = '_compiled'


@cache
def _loaded() -> tuple[tuple[str, Spec], ...]:
    found = []
    for path in sorted(EXAMPLES.rglob('*.yaml')):
        try:
            found.append((str(path.relative_to(EXAMPLES)), to_spec(path)))
        except MathSpecError:
            continue
    return tuple(found)


def _named_entries() -> list[pytest.ParameterSet]:
    return [
        pytest.param(spec, name, id=f'{path}:{name}')
        for path, spec in _loaded()
        for name, entry in spec.expressions.items()
        if entry.adds_to is None
    ]


def _outcome(compile_: object) -> object:
    """The node, or the class of the refusal, so a refusal compares by kind."""
    try:
        return compile_()  # type: ignore[operator]
    except LanguageError as error:
        return type(error)


def _spliced(spec: Spec, entry: object) -> object:
    """Today's way: the spec written out with *entry* added, loaded, and the entry read back."""
    written = spec.to_dict()
    written['expressions'] = {**written.get('expressions', {}), SPLICED: entry}
    return to_spec(written).program.expressions[SPLICED].expression


def _strings(spec: Spec) -> list[str]:
    """Every string the spec as written holds, whatever it is: expressions, conditions, names and prose."""
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

    walk(spec.to_dict())
    return sorted(found)


@pytest.mark.parametrize(('spec', 'name'), _named_entries())
def test_a_declared_entry_compiles_to_the_node_the_program_holds(spec, name):
    written = spec.to_dict()['expressions'][name]
    assert spec.compile_expression(written) == spec.program.expressions[name].expression


@pytest.mark.parametrize('example', ['dispatch.yaml', 'piecewise_coupling.yaml', 'library/generator.yaml'])
def test_every_string_in_a_spec_compiles_as_it_would_spliced_in(example):
    """Expressions, conditions, constraint texts and prose: most are refused, and each the same way both ways."""
    spec = dict(_loaded())[example]
    strings = _strings(spec)
    found = [
        f'{text!r}: compiled {compiled!r}, spliced {spliced!r}'
        for text in strings
        if (compiled := _outcome(lambda text=text: spec.compile_expression(text)))
        != (spliced := _outcome(lambda text=text: _spliced(spec, text)))
    ]
    assert not found, f'{len(found)} of {len(strings)} strings compile otherwise than spliced in:\n' + '\n'.join(
        found[:8]
    )


@pytest.mark.parametrize(
    ('entry', 'refused', 'message'),
    [
        pytest.param('sum(dispatch * nothing)', SchemaError, "The expression: 'nothing'", id='an-undeclared-name'),
        pytest.param(
            {'expression': 'dispatch', 'adds_to': 'total'}, SchemaError, 'makes it a term of a sum', id='adds-to'
        ),
        pytest.param(
            {'expression': 'dispatch', 'dims': ['nowhere']},
            SchemaError,
            "The expression references undeclared dimension 'nowhere'",
            id='an-undeclared-dimension',
        ),
        pytest.param(
            {'expression': 'sum(dispatch, over=snapshot)', 'dims': ['generator', 'snapshot']},
            DimensionError,
            'The expression: dims: gives',
            id='dims-the-body-is-not-indexed-over',
        ),
        pytest.param({'expression': 'dispatch', 'unknown': 1}, SchemaError, 'unknown', id='an-unknown-key'),
    ],
)
def test_an_entry_the_spec_could_not_hold_is_refused_as_the_expression(entry, refused, message):
    spec = dict(_loaded())['dispatch.yaml']
    with pytest.raises(refused, match=message):
        spec.compile_expression(entry)


def test_compiling_an_entry_leaves_the_spec_as_it_was():
    spec = dict(_loaded())['dispatch.yaml']
    before = spec.to_dict()
    spec.compile_expression('sum(dispatch * cost)')
    assert spec.to_dict() == before, 'the spec is unchanged'
    assert SPLICED not in spec.expressions, 'and holds no new entry'


def test_a_divisor_a_missing_row_makes_zero_is_refused_as_the_spec_refuses_it():
    written = dict(_loaded())['dispatch.yaml'].to_dict()
    written['parameters']['cost']['missing'] = 0
    spec = to_spec(written)
    with pytest.raises(SchemaError, match=r"The expression: .*'cost', which is declared missing: 0"):
        spec.compile_expression('dispatch / cost')
    assert _outcome(lambda: _spliced(spec, 'dispatch / cost')) is SchemaError, 'spliced in, it is refused too'
