# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`rename`: one fragment written over placeholder names, serving several classes.

A name is renamed wherever the spec writes it, and nothing that only looks
like it is: a longer name, a call's keyword, a quoted label, an exponent, a
description, a case's label, or a macro's formal. A map that renames nothing
the spec has, or lands two names on one, is refused before anything is built.
"""

from __future__ import annotations

import pytest

from mathspec import merge, rename, to_spec
from mathspec.errors import LanguageError

#: One class written over placeholder names: the `unit` dimension and the
#: `unit_` entries. Every place a name can stand appears once.
UNIT = {
    'dimensions': {'snapshot': {'dtype': 'int', 'ordered': True}, 'unit': {'dtype': 'str'}, 'bus': {'dtype': 'str'}},
    'relations': {
        'unit_bus': {'key': 'unit', 'values': 'bus'},
        'unit_ends': {'key': {'unit': 'unit'}, 'values': {'bus0': 'bus'}},
    },
    'given': {'expressions': {'total_cost': {'dims': []}}},
    'parameters': {
        'unit_p_max': {'dims': ['unit'], 'description': 'the most a unit_p reaches'},
        'unit_cost': {'dims': ['snapshot', 'unit'], 'dtype': 'float'},
    },
    'masks': {'unit_on': {'where': 'unit_p_max > 0'}},
    'variables': {
        'unit_p': {'dims': ['snapshot', 'unit'], 'where': 'unit_on', 'bounds': {'lower': 0, 'upper': 'unit_p_max'}},
    },
    'expressions': {
        'unit_spend': {'expression': 'sum(unit_p * unit_cost)', 'adds_to': 'total_cost'},
        'unit_previous': {
            'dims': ['snapshot', 'unit'],
            'cases': {'unit_p': {'when': 'position(snapshot) == 0', 'expression': 0}},
            'otherwise': 'shift(unit_p, along=snapshot, offset=1)',
        },
        'unit_at_bus': 'sum(unit_p, over=unit, by=unit_bus[bus])',
        'unit_at_end': 'sum(unit_p, over=unit, by=unit_ends[bus0])',
    },
    'constraints': {
        'unit_ramp': {
            'dims': ['snapshot', 'unit'],
            'expression': 'unit_p - unit_previous\n<= unit_twice(unit_p_max)',
        },
    },
    'assumptions': {'unit_bounded': {'holds': 'unit_p_max < 1000', 'where': 'unit_on'}},
    'macros': {'unit_twice': {'args': ['unit_p'], 'template': '2 * unit_p'}},
}

#: The placeholder names, as a class takes them.
PLACEHOLDERS = (
    *(name for section in ('relations', 'parameters', 'masks', 'variables', 'expressions') for name in UNIT[section]),
    'unit_ramp',
    'unit_bounded',
    'unit_twice',
)


def _as(prefix: str, dim: str) -> dict[str, str]:
    """The map that gives the placeholder class the names of one class."""
    return {'unit': dim} | {name: f'{prefix}{name.removeprefix("unit")}' for name in PLACEHOLDERS}


GENERATOR = _as('Generator', 'generator')
LINK = _as('Link', 'link')

#: The objective the classes add their cost to.
COST = {
    'given': {'expressions': {'total_cost': {'dims': []}}},
    'objective': {'sense': 'minimize', 'expression': 'total_cost'},
}


@pytest.mark.parametrize(
    ('where', 'expected'),
    [
        pytest.param(lambda s: list(s['dimensions']), ['snapshot', 'generator', 'bus'], id='dimension'),
        pytest.param(lambda s: s['relations']['Generator_bus'], {'key': 'generator', 'values': 'bus'}, id='relation'),
        pytest.param(
            lambda s: s['relations']['Generator_ends'],
            {'key': {'generator': 'generator'}, 'values': {'bus0': 'bus'}},
            id='relation-column',
        ),
        pytest.param(lambda s: s['parameters']['Generator_cost']['dims'], ['snapshot', 'generator'], id='dims'),
        pytest.param(lambda s: s['variables']['Generator_p']['where'], 'Generator_on', id='where'),
        pytest.param(lambda s: s['variables']['Generator_p']['bounds']['upper'], 'Generator_p_max', id='bound'),
        pytest.param(lambda s: s['expressions']['Generator_spend']['adds_to'], 'total_cost', id='adds-to'),
        pytest.param(
            lambda s: s['expressions']['Generator_previous']['otherwise'],
            'shift(Generator_p, along=snapshot, offset=1)',
            id='call',
        ),
        pytest.param(
            lambda s: s['expressions']['Generator_at_bus'],
            'sum(Generator_p, over=generator, by=Generator_bus[bus])',
            id='one-line-expression',
        ),
        pytest.param(
            lambda s: s['expressions']['Generator_at_end'],
            'sum(Generator_p, over=generator, by=Generator_ends[bus0])',
            id='column-not-renamed',
        ),
        pytest.param(
            lambda s: s['constraints']['Generator_ramp']['expression'],
            'Generator_p - Generator_previous\n<= Generator_twice(Generator_p_max)',
            id='layout-kept',
        ),
        pytest.param(
            lambda s: s['assumptions']['Generator_bounded']['holds'], 'Generator_p_max < 1000', id='assumption'
        ),
        pytest.param(
            lambda s: s['parameters']['Generator_p_max']['description'], 'the most a unit_p reaches', id='description'
        ),
        pytest.param(lambda s: list(s['expressions']['Generator_previous']['cases']), ['unit_p'], id='case-label'),
        pytest.param(
            lambda s: s['macros']['Generator_twice'],
            {'args': ['unit_p'], 'kwargs': [], 'template': '2 * unit_p'},
            id='macro-formal',
        ),
    ],
)
def test_a_name_is_renamed_wherever_the_spec_writes_it(where, expected):
    assert where(rename(UNIT, GENERATOR).to_dict()) == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        pytest.param('sum(p_max * p)', 'sum(p_max * cap)', id='longer-name'),
        pytest.param(
            'shift(p, along=t, offset=offset, edge=0)', 'shift(cap, along=t, offset=lag, edge=0)', id='keyword'
        ),
        pytest.param('sum(p, over=t) * 1e6', 'sum(cap, over=t) * 1e6', id='exponent'),
    ],
)
def test_a_token_that_only_looks_like_a_renamed_name_stays(text, expected):
    """`p_max` holds `p`, `offset=` is the keyword of `shift`, and the `e6` of `1e6` is an exponent."""
    spec = {
        'dimensions': {'t': {'dtype': 'int', 'ordered': True}},
        'parameters': {'p_max': {'dims': ['t']}, 'offset': {'dims': [], 'dtype': 'int'}, 'e6': {'dims': []}},
        'variables': {'p': {'dims': ['t']}},
        'expressions': {'x': text},
    }
    renamed = rename(spec, {'p': 'cap', 'offset': 'lag', 'e6': 'scale'})
    assert renamed.to_dict()['expressions']['x'] == expected


def test_a_quoted_label_spelt_like_a_renamed_name_stays():
    """A label is data: `'gas'` names a coordinate, not the dimension `gas`."""
    spec = {
        'dimensions': {'gas': {'dtype': 'str'}, 'tech': {'dtype': 'str'}},
        'relations': {'tech_gas': {'key': 'tech', 'values': 'gas'}},
        'masks': {'fossil': {'where': "tech_gas[gas] == 'gas'"}},
    }
    renamed = rename(spec, {'gas': 'fuel'})
    assert renamed.masks['fossil'].where == "tech_gas[fuel] == 'gas'"


def test_a_fixed_choice_spelt_like_a_renamed_name_stays():
    """`domain: integer` is one of the words the schema offers, not the parameter `integer`."""
    spec = {
        'dimensions': {'t': {'dtype': 'int'}},
        'parameters': {'integer': {'dims': ['t']}},
        'variables': {'n': {'dims': ['t'], 'domain': 'integer', 'bounds': {'upper': 'integer'}}},
    }
    renamed = rename(spec, {'integer': 'n_max'})
    assert (renamed.variables['n'].domain, renamed.variables['n'].bounds.upper) == ('integer', 'n_max')


def test_one_fragment_serves_two_classes_in_one_merge():
    composed = merge([COST, rename(UNIT, GENERATOR), rename(UNIT, LINK)])
    assert sorted(composed.variables) == ['Generator_p', 'Link_p'], 'each class builds its own column'
    assert composed.expressions['total_cost'].expression == 'Generator_spend + Link_spend', (
        'each class adds its own term to the sum the objective reads'
    )


def test_an_empty_map_returns_the_source_loaded():
    assert rename(UNIT, {}) == to_spec(UNIT)


def test_renaming_back_returns_the_canonical_form():
    inverse = {new: old for old, new in GENERATOR.items()}
    assert rename(rename(UNIT, GENERATOR), inverse).to_yaml(canonical=True) == to_spec(UNIT).to_yaml(canonical=True)


def test_two_names_may_swap():
    renamed = rename(UNIT, {'unit_p_max': 'unit_cost', 'unit_cost': 'unit_p_max'})
    assert renamed.variables['unit_p'].bounds.upper == 'unit_cost'
    assert renamed.parameters['unit_p_max'].dims == ['snapshot', 'unit']


@pytest.mark.parametrize(
    ('names', 'message'),
    [
        pytest.param(
            {'unit_pmax': 'Generator_p_max'},
            r"rename names 'unit_pmax', which the spec neither declares nor reads under 'given:'\. "
            r"Did you mean 'unit_p_max'\?",
            id='a-name-the-spec-lacks',
        ),
        pytest.param(
            {'unit_cost': 'unit_p_max'},
            r"rename gives the parameter 'unit_cost' the name 'unit_p_max', which the spec keeps for its "
            r"parameter 'unit_p_max'\. Rename that one too",
            id='a-name-the-spec-keeps',
        ),
        pytest.param(
            {'unit_cost': 'Generator_cost', 'unit_p_max': 'Generator_cost'},
            r"rename gives 'unit_cost' and 'unit_p_max' the one name 'Generator_cost'\.",
            id='two-names-on-one',
        ),
        pytest.param({'unit_p': 'sum'}, r'sum', id='a-name-the-language-keeps'),
    ],
)
def test_a_map_the_spec_cannot_take_is_refused(names, message):
    with pytest.raises(LanguageError, match=message):
        rename(UNIT, names)
