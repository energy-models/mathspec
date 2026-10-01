# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The GEMS `basic_models_library` under `examples/ports/gems/`, one fragment per GEMS model.

A GEMS model knows only its own ports, and a system file connects them. Here
each model is a fragment, a port is a given expression that the connected
models add terms to, and `merge` is the system.
"""

from __future__ import annotations

import pytest

from mathspec import merge, to_markdown, to_spec
from tests.fixtures import EXAMPLES

GEMS = EXAMPLES / 'ports' / 'gems'
MODELS = (
    'bus',
    'load',
    'link',
    'renewable',
    'generator',
    'storage',
    'emission_constraint',
    'energy_limitation_hard_constraint_max',
    'energy_limitation_soft_constraint_max',
)
FRAGMENTS = {name: GEMS / f'{name}.yaml' for name in ('system', *MODELS)}


def test_every_file_is_a_fragment_of_the_library():
    assert sorted(path.stem for path in GEMS.glob('*.yaml')) == sorted(FRAGMENTS), (
        'one fragment per GEMS model, and the system around them'
    )


@pytest.mark.parametrize('name', sorted(FRAGMENTS))
def test_every_fragment_loads_and_prints_on_its_own(name):
    assert to_markdown(to_spec(FRAGMENTS[name])), f'{name} rendered nothing'


def test_the_bus_names_no_model_that_connects_to_it():
    assert sorted(to_spec(FRAGMENTS['bus']).dimensions) == ['bus', 'scenario', 'time'], (
        'a GEMS bus knows its balance port and nothing that connects to it'
    )


def test_the_library_composes_into_one_spec():
    spec = merge(list(FRAGMENTS.values()))
    assert not spec.given, 'each port read is folded into the sum the connected models write'
    assert spec.expressions['Bus_balance_port_flow'].expression == (
        'Load_balance_port_flow + Link_out_port_flow + Link_in_port_flow'
        ' + Renewable_balance_port_flow + Generator_balance_port_flow + Storage_injection_port_flow'
    ), 'every model with a flow port adds its term to the bus port, in the order the files are given in'
    assert spec.expressions['total_cost'].expression == (
        'Bus_objective + Generator_objective + Energy_limit_soft_objective'
    ), 'the three models with an objective contribution are the three terms'
