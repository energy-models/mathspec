# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The Calliope port under `examples/calliope/`, held to what its pages claim.

The gallery test holds each page to its generator. What is left for here is
what the index and the port record state: every fragment stands alone, the
base and every extension compose with nothing left to provide, every variant
lands on the composition its page names, and a sum Calliope restates to add a
term gains the term instead.
"""

from __future__ import annotations

import re

import pytest

from mathspec import LanguageError, advice, merge, override, to_markdown, to_spec
from tests.fixtures import EXAMPLES
from tools import gallery

CALLIOPE = EXAMPLES / 'calliope'
BASE = sorted(CALLIOPE.glob('*.yaml'))
EXTENSIONS = {path.stem: path for path in sorted((CALLIOPE / 'extensions').glob('*.yaml'))}
VARIANTS = {path.stem: path for path in sorted((CALLIOPE / 'variants').glob('*.yaml'))}

#: The extensions that read the units the MILP fragment builds.
NEEDS_MILP = {'piecewise_linear_costs', 'piecewise_linear_efficiency', 'uptime_downtime_limits'}

#: The extensions whose new rows replace a base row a variant of the same name narrows.
REWRITES_A_BASE_ROW = {'chp_htp', 'urban_scale_chp'}


def _composed(*extensions: str):
    """The base, the MILP pair where an extension needs it, the extensions, and the variants of their rewrites."""
    milp = 'milp' in extensions or NEEDS_MILP & set(extensions)
    names = [*(['milp'] if milp and 'milp' not in extensions else []), *extensions]
    patches = [VARIANTS['milp']] if milp else []
    patches += [VARIANTS[name] for name in names if name in REWRITES_A_BASE_ROW]
    merged = merge([*BASE, *(EXTENSIONS[name] for name in names)])
    return override(merged, patches) if patches else merged


@pytest.mark.parametrize('path', [*BASE, *EXTENSIONS.values()], ids=lambda path: path.stem)
def test_every_fragment_loads_and_prints_on_its_own(path):
    assert to_markdown(to_spec(path)), f'{path.stem} rendered nothing'


def test_the_base_composes_with_nothing_left_to_provide():
    spec = merge(BASE)
    assert not spec.given, 'every name a base fragment reads is one another base fragment declares'
    assert not advice(spec), 'the composed base has no dimension out of use, no column to provide, no open variable'


@pytest.mark.parametrize('name', sorted(EXTENSIONS))
def test_every_extension_composes_onto_the_base(name):
    spec = _composed(name)
    assert not spec.given, f'{name} reads only what the base, and the MILP fragment where it needs it, declare'
    assert not advice(spec), f'{name} composed leaves nothing to advise on'


@pytest.mark.parametrize('name', sorted(VARIANTS))
def test_every_variant_is_a_patch_rather_than_a_spec(name):
    with pytest.raises(LanguageError):
        to_spec(VARIANTS[name])


@pytest.mark.parametrize('page', sorted(gallery.CALLIOPE_VARIANTS))
def test_every_variant_lands_on_the_composition_its_page_names(page):
    fragments, before = gallery.CALLIOPE_VARIANTS[page]
    name = page.removeprefix('calliope/variants/').removesuffix('.md')
    spec = override(merge(fragments), [*(VARIANTS[earlier] for earlier in before), VARIANTS[name]])
    assert not spec.given and not advice(spec), f'{name} leaves a whole spec with nothing to advise on'


def test_every_variant_has_a_page():
    paged = {page.removeprefix('calliope/variants/').removesuffix('.md') for page in gallery.CALLIOPE_VARIANTS}
    assert paged == set(VARIANTS), 'a variant with no page is a patch nobody can read as math'


def test_the_whole_port_composes_in_one_spec():
    """Every extension but the two that Calliope also offers as alternatives, with every mode but operate."""
    alternatives = {'sos2_piecewise_linear_costs', 'urban_scale_chp'}
    merged = merge([*BASE, *(path for name, path in EXTENSIONS.items() if name not in alternatives)])
    patches = ['milp', 'chp_htp', 'spores', 'storage_inter_cluster']
    spec = override(merged, [VARIANTS[name] for name in patches])
    assert not spec.given and not advice(spec), 'the port is one spec once composed'


def test_the_two_piecewise_costs_are_alternatives():
    with pytest.raises(LanguageError, match=r"both declare the variable 'piecewise_cost_investment'"):
        merge(
            [*BASE, EXTENSIONS['milp'], EXTENSIONS['piecewise_linear_costs'], EXTENSIONS['sos2_piecewise_linear_costs']]
        )


@pytest.mark.parametrize(
    ('name', 'hub', 'term'),
    [
        pytest.param('fuel_dist', 'carrier_flow', 'fuel_dist_carrier_flow', id='fuel-in-the-balance'),
        pytest.param('fuel_dist', 'system_cost', 'fuel_dist_system_cost', id='fuel-in-the-objective'),
        pytest.param('monthly_peak_flow_charge', 'cost_operation_fixed', 'cost_month_peak_charge', id='peak-charge'),
        pytest.param('milp', 'cost_investment', 'cost_investment_purchase', id='purchase-cost'),
        pytest.param(
            'piecewise_linear_costs', 'cost_investment', 'piecewise_cost_investment_term', id='piecewise-cost'
        ),
    ],
)
def test_a_sum_calliope_restates_gains_a_term_instead(name, hub, term):
    """Calliope restates the whole block to add one term; here the base file stays as it is."""
    spec = _composed(name)
    assert re.search(rf'\b{term}\b', spec.expressions[hub].expression), f'{hub} carries the term {name} adds'


def test_spores_caps_the_sums_the_objective_read():
    """Calliope restates its objective in the cap, and misses a cost an example adds to it; the cap reads the sums."""
    spec = override(_composed('fuel_dist'), [VARIANTS['spores']])
    cap = spec.constraints['total_system_cost_max'].expression
    assert 'system_cost' in cap and 'penalty' in cap, 'the cap reads the two sums the least-cost objective read'
    assert 'fuel_dist_system_cost' in spec.expressions['system_cost'].expression, 'so fuel distribution is capped too'


def test_operate_mode_turns_every_capacity_into_data():
    spec = override(_composed('milp'), [VARIANTS[name] for name in ('milp', 'operate', 'operate_milp')])
    capacities = {'flow_cap', 'area_use', 'source_cap', 'storage_cap', 'purchased_units'}
    assert capacities <= set(spec.parameters), 'each capacity is a parameter of the same name'
    assert not capacities & set(spec.variables), 'and no longer a decision'


def test_the_sos2_curve_links_a_copy_of_the_flow_capacity_masked_to_the_curve():
    """A `piecewise:` block has no `where:`, and a link over `flow_cap` pinned every technology with no curve to zero.

    The expanded link row `flow_cap == sum(lam * x)` is built at every
    coordinate of the frame. Where a technology has no breakpoints its weights
    do not exist, so the row reads `flow_cap == 0`. The link reads a copy of
    `flow_cap` that exists only where the curve does, and the row goes with it.
    """
    spec = to_spec(EXTENSIONS['sos2_piecewise_linear_costs']).expand()
    link = spec.constraints['sos2_piecewise_costs_link0'].expression
    assert link.startswith('(piecewise_flow_cap)'), 'the curve pins the masked copy, not the flow capacity itself'
    assert 'piecewise_cost_investment_x' in spec.variables['piecewise_flow_cap'].where, (
        'the copy exists only where the technology has breakpoints'
    )
