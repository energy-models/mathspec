# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`rename`: one fragment written over placeholder names, serving several classes.

A name is renamed wherever the spec writes it, and nothing that only looks
like it is: a longer name, a call's keyword, a quoted label, an exponent, a
description, a label of `one_of:`, the name of a case or of a piecewise link,
or a macro's formal. A map that renames nothing the spec has, or lands two
names on one, is refused before anything is built. A function in place of the
map is asked for the new name of each name the spec has.
"""

from __future__ import annotations

import re

import pytest

from mathspec import merge, rename, to_spec
from mathspec.errors import LanguageError

#: One class written over placeholder names: the `unit` dimension and the
#: `unit_` entries. Every place a name can stand appears once.
UNIT = {
    'dimensions': {'snapshot': {'dtype': 'int', 'ordered': True}, 'unit': {'dtype': 'str'}, 'bus': {'dtype': 'str'}},
    'relations': {'unit_link': {'dims': ['bus', 'unit'], 'missing': 'absent'}},
    'maps': {'unit': {'bus': 'bus', 'bus0': 'bus'}},
    'given': {'expressions': {'total_cost': {'dims': []}}},
    'parameters': {
        'unit_p_max': {'dims': ['unit'], 'description': 'the most a unit_p reaches'},
        'unit_cost': {'dims': ['snapshot', 'unit'], 'dtype': 'float'},
    },
    'conditions': {'unit_on': {'condition': 'unit_p_max > 0'}},
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
        'unit_at_bus': 'sum(unit_p, over=unit, by=unit[bus])',
        'unit_at_end': 'sum(unit_p, over=unit, by=unit[bus0])',
    },
    'constraints': {
        'unit_ramp': {
            'dims': ['snapshot', 'unit'],
            'expression': 'unit_p - unit_previous\n<= unit_twice(unit_p_max)',
        },
    },
    'assumptions': {'unit_bounded': {'holds': 'unit_p_max < 1000', 'where': 'unit_on'}},
    'macros': {
        'unit_twice': {'args': ['unit_p'], 'template': '2 * unit_p'},
        'unit_scaled': {'args': ['x'], 'template': 'x * unit_cost'},
    },
}

#: The placeholder names, as a class takes them.
PLACEHOLDERS = (
    *(
        name
        for section in ('relations', 'parameters', 'conditions', 'variables', 'expressions')
        for name in UNIT[section]
    ),
    'unit_ramp',
    'unit_bounded',
    'unit_twice',
    'unit_scaled',
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
        pytest.param(lambda s: list(s['dimensions']), ['bus', 'generator', 'snapshot'], id='dimension'),
        pytest.param(
            lambda s: s['relations']['Generator_link'],
            {'dims': ['bus', 'generator'], 'missing': 'absent'},
            id='relation',
        ),
        pytest.param(lambda s: s['maps'], {'generator': {'bus': 'bus', 'bus0': 'bus'}}, id='map'),
        pytest.param(lambda s: s['parameters']['Generator_cost']['dims'], ['generator', 'snapshot'], id='dims'),
        pytest.param(lambda s: s['variables']['Generator_p']['where'], 'Generator_on', id='where'),
        pytest.param(lambda s: s['variables']['Generator_p']['bounds']['upper'], 'Generator_p_max', id='bound'),
        pytest.param(lambda s: s['expressions']['Generator_spend']['adds_to'], 'total_cost', id='kept-adds-to'),
        pytest.param(lambda s: s['macros']['Generator_scaled']['template'], 'x * Generator_cost', id='macro-template'),
        pytest.param(
            lambda s: s['expressions']['Generator_previous']['otherwise'],
            'shift(Generator_p, along=snapshot, offset=1)',
            id='call',
        ),
        pytest.param(
            lambda s: s['expressions']['Generator_at_bus'],
            'sum(Generator_p, over=generator, by=generator[bus])',
            id='one-line-expression',
        ),
        pytest.param(
            lambda s: s['expressions']['Generator_at_end'],
            'sum(Generator_p, over=generator, by=generator[bus0])',
            id='map-not-renamed',
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
            {'args': ['unit_p'], 'template': '2 * unit_p'},
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
        'maps': {'tech': {'gas': 'gas'}},
        'conditions': {'fossil': {'condition': "tech[gas] == 'gas'"}},
    }
    renamed = rename(spec, {'gas': 'fuel'})
    assert renamed.conditions['fossil'].condition == "tech[fuel] == 'gas'"


def test_a_fixed_choice_spelt_like_a_renamed_name_stays():
    """`domain: integer` is one of the words the schema offers, not the parameter `integer`."""
    spec = {
        'dimensions': {'t': {'dtype': 'int'}},
        'parameters': {'integer': {'dims': ['t']}},
        'variables': {'n': {'dims': ['t'], 'domain': 'integer', 'bounds': {'upper': 'integer'}}},
    }
    renamed = rename(spec, {'integer': 'n_max'})
    assert (renamed.variables['n'].domain, renamed.variables['n'].bounds.upper) == ('integer', 'n_max')


@pytest.mark.parametrize(
    ('where', 'expected'),
    [
        pytest.param(lambda s: s['dimensions']['tech']['one_of'], ['gas', 'wind'], id='one-of'),
        pytest.param(
            lambda s: s['piecewise']['curve']['links'],
            {'cost': ['cost', 'cost_bp'], 'gas': ['fuel', 'gas_bp']},
            id='link-name',
        ),
    ],
)
def test_a_label_spelt_like_a_renamed_name_stays(where, expected):
    """`one_of:` lists labels of the data, and the name of a link labels its row."""
    spec = {
        'dimensions': {'tech': {'dtype': 'str', 'one_of': ['gas', 'wind']}, 'bp': {'dtype': 'int', 'ordered': True}},
        'parameters': {'gas_bp': {'dims': ['tech', 'bp']}, 'cost_bp': {'dims': ['tech', 'bp']}},
        'variables': {'gas': {'dims': ['tech']}, 'cost': {'dims': ['tech']}},
        'piecewise': {
            'curve': {'along': 'bp', 'dims': ['tech'], 'links': {'gas': ['gas', 'gas_bp'], 'cost': ['cost', 'cost_bp']}}
        },
    }
    assert where(rename(spec, {'gas': 'fuel'}).to_dict()) == expected


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


@pytest.mark.parametrize(
    'where',
    [
        pytest.param(lambda s: s['expressions']['unit_spend']['adds_to'], id='adds-to'),
        pytest.param(lambda s: next(iter(s['given']['expressions'])), id='given'),
    ],
)
def test_a_sum_read_under_given_is_renamed(where):
    assert where(rename(UNIT, {'total_cost': 'system_cost'}).to_dict()) == 'system_cost'


def test_two_names_may_swap():
    renamed = rename(UNIT, {'unit_p_max': 'unit_cost', 'unit_cost': 'unit_p_max'})
    assert renamed.variables['unit_p'].bounds.upper == 'unit_cost'
    assert renamed.parameters['unit_p_max'].dims == ('snapshot', 'unit')


def _generator(name: str) -> str | None:
    """The new name of a placeholder name, and `None` for a name every class shares."""
    if name == 'unit':
        return 'generator'
    return f'Generator{name.removeprefix("unit")}' if name.startswith('unit_') else None


SWAP = {'unit_p_max': 'unit_cost', 'unit_cost': 'unit_p_max'}


@pytest.mark.parametrize(
    ('rule', 'names'),
    [
        pytest.param(_generator, GENERATOR, id='by-prefix'),
        pytest.param(SWAP.get, SWAP, id='swap'),
        pytest.param(lambda name: None, {}, id='none-keeps'),
        pytest.param(lambda name: name, {}, id='the-same-name-keeps'),
    ],
)
def test_a_function_renames_as_the_map_of_its_results_does(rule, names):
    assert rename(UNIT, rule) == rename(UNIT, names)


@pytest.mark.parametrize('names', [{'unit_p': None}, {'unit_p': 'unit_p'}], ids=['none', 'the-same-name'])
def test_a_map_keeps_a_name_it_maps_to_none_or_to_itself(names):
    assert rename(UNIT, names) == to_spec(UNIT)


def test_names_that_are_neither_a_map_nor_a_function_are_refused():
    with pytest.raises(TypeError, match='rename takes a mapping or a function as names, not str'):
        rename(UNIT, 'unit_p')


def test_a_function_is_asked_once_for_each_name_the_spec_has():
    asked: list[str] = []
    rename(UNIT, asked.append)
    assert sorted(asked) == sorted({'snapshot', 'unit', 'bus', 'total_cost', *PLACEHOLDERS}), (
        'every name the spec declares or reads under given:, each once'
    )


@pytest.mark.parametrize(
    ('names', 'message'),
    [
        pytest.param(
            {'unit_pmax': 'Generator_p_max'},
            r"rename cannot change 'unit_pmax', which the spec neither declares nor lists under 'given:'\. "
            r"Did you mean 'unit_p_max'\?",
            id='a-name-the-spec-lacks',
        ),
        pytest.param(
            {'unit_cost': 'unit_p_max'},
            r"rename gives the parameter 'unit_cost' the name 'unit_p_max', which the parameter 'unit_p_max' "
            r'already has\. Rename that one too',
            id='a-name-the-spec-keeps',
        ),
        pytest.param(
            {'unit': 'bus'},
            r"rename gives the dimension 'unit' the name 'bus', which the dimension 'bus' already has\.",
            id='a-dimension-with-maps-is-named-as-a-dimension',
        ),
        pytest.param(
            {'unit_cost': 'Generator_cost', 'unit_p_max': 'Generator_cost'},
            r"rename gives 'unit_cost' and 'unit_p_max' the one name 'Generator_cost'\.",
            id='two-names-on-one',
        ),
        pytest.param({'unit_p': 'sum'}, r'sum', id='a-name-the-language-keeps'),
        pytest.param(
            {'unit_cost': 'x'},
            r"rename gives the parameter 'unit_cost' the name 'x', which is an argument of the macro 'unit_scaled', "
            r"whose template uses 'unit_cost'\. Choose another name\.",
            id='an-argument-of-a-macro-that-uses-the-name',
        ),
        pytest.param(
            {'unit_cost': 'bus0'},
            r"rename changes 'unit_cost' to 'bus0', and 'bus0' is also a map of 'unit'\. "
            r'Give it another name in the file, or choose another name\.',
            id='a-new-name-that-is-a-map',
        ),
        pytest.param(
            {'unit_cost': 'unit_p_max'}.get,
            r"rename gives the parameter 'unit_cost' the name 'unit_p_max', which the parameter 'unit_p_max' already",
            id='a-function-onto-a-name-the-spec-keeps',
        ),
        pytest.param(
            lambda name: 'unit_p_max' if name in ('unit_cost', 'unit_p_max') else None,
            r"rename gives the parameter 'unit_cost' the name 'unit_p_max', which the parameter 'unit_p_max' already",
            id='a-function-that-keeps-the-name-it-gives',
        ),
        pytest.param(
            lambda name: 'Generator_cost' if name in SWAP else None,
            r"rename gives 'unit_cost' and 'unit_p_max' the one name 'Generator_cost'\.",
            id='a-function-with-two-names-on-one',
        ),
    ],
)
def test_a_map_the_spec_cannot_take_is_refused(names, message):
    with pytest.raises(LanguageError, match=message):
        rename(UNIT, names)


@pytest.mark.parametrize(
    ('old', 'message'),
    [
        pytest.param('bus0', "'bus0' is also a map of 'line'", id='a-map'),
        pytest.param('from_bus', "'from_bus' is also a column of the relation 'corridor'", id='a-relation-column'),
    ],
)
def test_a_name_that_is_also_a_map_or_a_relation_column_is_refused(old, message):
    """`line[bus0]` reads a map, and a rename of the parameter `bus0` would change it too."""
    spec = {
        'dimensions': {'line': {'dtype': 'str'}, 'bus': {'dtype': 'str'}},
        'relations': {'corridor': {'dims': {'from_bus': 'bus', 'to_bus': 'bus'}}},
        'maps': {'line': {'bus0': 'bus', 'bus1': 'bus'}},
        'parameters': {'bus0': {'dims': ['bus']}, 'from_bus': {'dims': ['bus']}},
        'variables': {'flow': {'dims': ['line']}},
        'expressions': {'sent': 'sum(flow, over=line, by=line[bus0])'},
    }
    with pytest.raises(LanguageError, match=re.escape(message)):
        rename(spec, {old: 'price'})


def test_a_missing_row_read_by_a_map_follows_the_rename():
    """`by:` names a subject and its map, and `fill:` names labels of the data.

    The rename kept the whole `missing:`, since a reading may be a fixed word,
    so `by: g[h]` named a subject the renamed spec no longer had.
    """
    spec = {
        'dimensions': {'g': {}, 'h': {'one_of': ['north', 'south']}, 'north': {}},
        'maps': {'g': {'h': 'h'}},
        'parameters': {'c': {'dims': ['g'], 'missing': {'by': 'g[h]', 'fill': {'north': 0}, 'otherwise': 'absent'}}},
    }
    renamed = rename(spec, {'g': 'gen', 'h': 'zone', 'north': 'n'})
    assert renamed.to_dict()['parameters']['c']['missing'] == {
        'by': 'gen[zone]',
        'fill': {'north': 0.0},
        'otherwise': 'absent',
    }, 'the subject and the map are renamed, and the label stays'
