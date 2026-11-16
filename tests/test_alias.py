# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A dimension that is an alias of another: the same labels under a second name, so an entry is over them twice."""

from typing import Any

import pytest
import yaml

from mathspec import to_spec, typeset
from mathspec.errors import LanguageError
from tests.fixtures import SMALL_MODEL, varied

#: `g` twice: `from_g` is an alias of it, `link` a parameter over both, and a constraint reading the far end.
TWICE: dict[str, Any] = varied(
    SMALL_MODEL,
    **{
        'dimensions.from_g': {'alias': 'g'},
        'parameters.link': {'dims': ['from_g', 'g'], 'missing': 0},
        'constraints.inflow': {'dims': ['g'], 'expression': 'p == sum(link * at(p, by=from_g[g]), over=from_g)'},
    },
)


def test_an_alias_has_the_labels_dtype_and_order_of_its_dimension():
    dimension = to_spec(TWICE).program.dimensions['from_g']
    assert dimension.alias == 'g', 'the program names the dimension whose labels the alias has'
    assert (dimension.dtype, dimension.ordered) == ('str', True), 'dtype and order come from g'


def test_an_alias_is_ordered_where_its_dimension_is():
    """`shift` along an alias steps as it does along the dimension it aliases."""
    to_spec(
        varied(
            TWICE,
            **{
                'variables.x': {'dims': ['from_g']},
                'constraints.ramp': {'dims': ['from_g'], 'expression': 'x >= shift(x, along=from_g, offset=1, edge=0)'},
            },
        )
    )


def test_an_alias_writes_back_only_its_alias():
    spec = to_spec(TWICE)
    assert yaml.safe_load(spec.to_yaml())['dimensions']['from_g'] == {'alias': 'g'}, 'the alias sets nothing else'
    assert to_spec(spec.to_yaml()) == spec, 'the file round-trips'


@pytest.mark.parametrize('fmt', ['markdown', 'latex', 'typst'])
def test_an_alias_prints_as_a_primed_index_over_the_same_set(fmt: str):
    """The read through the alias is the identity, so the far end prints at the primed index, not through a function."""
    out = typeset(to_spec(TWICE), fmt)
    assert "g'" in out, 'the alias is the index of g, primed'
    assert 'from_g(' not in out and 'g(' not in out.replace("g'", ''), 'the identity map prints no function'


@pytest.mark.parametrize(
    ('patch', 'message'),
    [
        pytest.param(
            {'dimensions.from_g': {'alias': 'g', 'dtype': 'int'}},
            "is an alias of 'g', and takes its dtype, labels and order from it. Delete dtype:, or set it on 'g'.",
            id='a-dtype-of-its-own',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'g', 'ordered': False}},
            'Delete ordered:',
            id='an-order-of-its-own',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'nope'}},
            "Dimension 'from_g': alias: 'nope' is no declared dimension.",
            id='an-undeclared-dimension',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'from_g'}},
            "Dimension 'from_g': alias: 'from_g' is the dimension itself.",
            id='itself',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'g'}, 'dimensions.to_g': {'alias': 'from_g'}},
            "Dimension 'to_g': alias: 'from_g' is an alias of 'g' itself. Write alias: g.",
            id='an-alias-of-an-alias',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'g'}, 'maps.from_g': {'g': {'dim': 'g'}}},
            "Dimension 'from_g': alias: 'g' gives 'from_g' the map 'from_g[g]' from each label to itself.",
            id='its-map-declared-again',
        ),
    ],
)
def test_an_alias_that_says_more_or_less_than_its_dimension_is_refused(patch: dict[str, Any], message: str):
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(SMALL_MODEL, **patch))
    assert message in str(caught.value)


def test_ire_flo_is_over_two_regions_and_two_commodities_at_the_links_that_exist():
    """TIMES' IRE_FLO(REG,COM,R,C): an alias for each set named twice, and `in:` for the links that exist."""
    spec = to_spec(
        {
            'dimensions': {
                'region': {},
                'commodity': {},
                'from_region': {'alias': 'region'},
                'from_commodity': {'alias': 'commodity'},
            },
            'relations': {
                'top_ire': {'dims': ['from_region', 'from_commodity', 'region', 'commodity'], 'missing': 'absent'}
            },
            'parameters': {
                'ire_flo': {'dims': ['from_region', 'from_commodity', 'region', 'commodity'], 'in': ['top_ire']}
            },
            'variables': {
                'export': {'dims': ['from_region', 'from_commodity', 'region', 'commodity'], 'in': ['top_ire']},
                'supply': {'dims': ['region', 'commodity']},
            },
            'constraints': {
                'balance': {
                    'dims': ['region', 'commodity'],
                    'expression': (
                        'supply + sum(ire_flo * export, over=[from_region, from_commodity]) '
                        '- sum(sum(sum(export, over=[region, commodity]), over=from_region, by=from_region[region]), '
                        'over=from_commodity, by=from_commodity[commodity]) >= 0'
                    ),
                }
            },
            'objective': {'expression': 'sum(supply)'},
        }
    )
    assert spec.program.parameters['ire_flo'].in_ == ('top_ire',), 'the links that exist are the index set'


def test_a_sum_inside_an_entry_over_the_alias_takes_an_index_of_its_own():
    """A sum over `g` inside a sum over its alias printed `w_{g',g'}`: its dummy took the alias's own index.

    The alias prints as `g'`, and a reduction primes its dummy once per
    enclosing use of the dimension, so the sum over `g` under `∀ g` also
    printed `g'`, and the two indices of `w` read as one.
    """
    spec = to_spec(
        varied(
            SMALL_MODEL,
            **{
                'dimensions.from_g': {'alias': 'g'},
                'variables.w': {'dims': ['from_g', 'g']},
                'constraints.out': {'dims': ['g'], 'expression': 'p == sum(sum(w, over=g), over=from_g, by=from_g[g])'},
            },
        )
    )
    assert "w_{g',g''}" in typeset(spec, 'markdown'), 'the inner sum takes g, primed past the alias'
