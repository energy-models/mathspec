# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A parameter's `missing:` that names an expression: what loads, what the program holds, and what is refused."""

from __future__ import annotations

from typing import Any

import pytest

from mathspec import rename, to_spec
from mathspec._typesetting import to_markdown
from mathspec.errors import LanguageError
from mathspec.program import FillByLabel, MissingFrom, fill_by_label
from tests.fixtures import varied

LOAD = "entity[component] == 'Load'"

MODEL: dict[str, Any] = {
    'dimensions': {
        'entity': {},
        'component': {'one_of': ['Generator', 'Load', 'ShuntImpedance']},
        'zone': {},
        'snapshot': {'dtype': 'int'},
    },
    'maps': {'entity': {'component': {'refers_to': 'component'}, 'zone': {'refers_to': 'zone'}}},
    'parameters': {
        'sign': {'dims': ['entity'], 'missing': 'sign_default'},
        'scale': {'dims': ['entity'], 'missing': 2},
    },
    'variables': {'p': {'dims': ['entity']}},
    'expressions': {
        'sign_default': {
            'dims': ['entity'],
            'cases': {'load': {'when': f"{LOAD} OR entity[component] == 'ShuntImpedance'", 'expression': '-1'}},
            'otherwise': '1',
        }
    },
    'constraints': {'limit': {'dims': [], 'expression': 'sum(sign * p) <= 1'}},
}


def _fill(**fields: Any) -> dict[str, Any]:
    return {'expressions': {'sign_default': {**MODEL['expressions']['sign_default'], **fields}}}


def test_missing_names_an_expression() -> None:
    program = to_spec(MODEL).program
    assert program.parameters['sign'].missing == MissingFrom('sign_default')
    assert program.parameters['scale'].missing == 2, 'a plain value stays the value'


def test_a_fill_by_one_map_reads_as_a_number_per_label() -> None:
    assert fill_by_label(to_spec(MODEL).program, 'sign') == FillByLabel(
        'entity', 'component', {'Load': -1.0, 'ShuntImpedance': -1.0}, 1.0
    ), 'the labels joined with OR share one value, and otherwise: is the last region'


def test_the_fill_of_an_int_parameter_reads_as_whole_numbers() -> None:
    model = varied(MODEL, parameters={'sign': {'dims': ['entity'], 'dtype': 'int', 'missing': 'sign_default'}})
    table = fill_by_label(to_spec(model).program, 'sign')
    assert table is not None
    assert [type(v) for v in (*table.fill.values(), table.otherwise)] == [int, int, int], 'no 1.0 for an int column'


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param(
            _fill(cases={'a': {'when': f"{LOAD} AND entity[zone] == 'north'", 'expression': '-1'}}), id='two-maps'
        ),
        pytest.param(_fill(cases={'a': {'when': f'NOT {LOAD}', 'expression': '-1'}}), id='a-negation'),
        pytest.param({'parameters': {'sign': {'dims': ['entity'], 'missing': 1}}}, id='a-plain-value'),
    ],
)
def test_a_fill_of_another_form_has_no_number_per_label(patch: dict[str, Any]) -> None:
    """Such a file loads: only a tool that holds one default per label cannot take it."""
    assert fill_by_label(to_spec(varied(MODEL, **patch)).program, 'sign') is None


def test_the_legend_names_the_expression_and_the_page_defines_it() -> None:
    page = to_markdown(to_spec(MODEL))
    assert r'$`\mathrm{sign}^{\mathrm{default}}`$ where the data has no row' in page
    assert r'\mathrm{sign}^{\mathrm{default}}_{e} = \begin{cases}' in page, 'the cases print as a definition'


def test_rename_follows_the_expression_and_keeps_a_word() -> None:
    model = varied(MODEL, parameters={**MODEL['parameters'], 'held': {'dims': ['entity'], 'missing': 'absent'}})
    renamed = rename(to_spec(model), {'sign_default': 'fallback'})
    assert renamed.parameters['sign'].missing == 'fallback'
    assert renamed.parameters['held'].missing == 'absent'


def test_a_bare_int_name_is_a_row_test_under_a_fill() -> None:
    """Under `refused` the bare name is true everywhere and is refused; a fill leaves rows out, so it loads."""
    to_spec(
        varied(
            MODEL,
            parameters={'sign': {'dims': ['entity'], 'dtype': 'int', 'missing': 'sign_default'}},
            variables={'p': {'dims': ['entity'], 'where': 'sign'}},
        )
    )


@pytest.mark.parametrize(
    ('patch', 'said'),
    [
        pytest.param(
            {'parameters': {'sign': {'dims': ['entity'], 'missing': 'sign_defualt'}}},
            "names no expression. Did you mean 'sign_default'?",
            id='an-unknown-name',
        ),
        pytest.param(
            {'parameters': {'sign': {'dims': ['entity'], 'dtype': 'bool', 'missing': 'sign_default'}}},
            'names an expression on a bool parameter, and an expression gives a number. Write true or false.',
            id='a-bool-parameter',
        ),
        pytest.param(
            {'parameters': {'sign': {'dims': ['entity'], 'dtype': 'str', 'missing': 'sign_default'}}},
            'names an expression on a str parameter, and an expression gives a number. Write refused or absent.',
            id='a-str-parameter',
        ),
        pytest.param(
            _fill(cases={'load': {'when': LOAD, 'expression': 'scale'}}),
            'is not cases of plain numbers.',
            id='a-value-that-reads-a-parameter',
        ),
        pytest.param(
            {'expressions': {'sign_default': '2'}},
            'is not cases of plain numbers.',
            id='a-plain-expression',
        ),
        pytest.param(
            _fill(cases={'load': {'when': 'scale > 1', 'expression': '-1'}}),
            "reads ['scale'] in a `when:`, and a missing row is filled before any value is read.",
            id='a-when-that-reads-a-parameter',
        ),
        pytest.param(
            _fill(
                dims=['entity', 'snapshot'], cases={'first': {'when': f'{LOAD} AND snapshot == 0', 'expression': '-1'}}
            ),
            "is over ['snapshot'], and the parameter is not (dims ['entity']).",
            id='a-dimension-the-parameter-is-not-over',
        ),
        pytest.param(
            {
                **_fill(otherwise='0.5'),
                'parameters': {'sign': {'dims': ['entity'], 'dtype': 'int', 'missing': 'sign_default'}},
            },
            'states [0.5], and an int parameter takes whole numbers.',
            id='a-fraction-on-an-int',
        ),
        pytest.param(
            {**_fill(otherwise='0'), 'constraints': {'limit': {'dims': [], 'expression': 'sum(p / sign) <= 1'}}},
            "the divisor contains 'sign'",
            id='a-zero-under-a-divisor',
        ),
    ],
)
def test_a_fill_the_loader_cannot_read_is_refused(patch: dict[str, Any], said: str) -> None:
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(MODEL, **patch))
    assert said in str(caught.value)


def test_a_fill_read_under_given_is_refused() -> None:
    """A given expression has no body here, so the loader cannot check that its cases are plain numbers."""
    fragment = {k: v for k, v in MODEL.items() if k != 'expressions'}
    fragment['given'] = {'expressions': {'sign_default': {'dims': ['entity']}}}
    with pytest.raises(LanguageError, match="Declare the parameter in the file that declares 'sign_default'"):
        to_spec(fragment)
