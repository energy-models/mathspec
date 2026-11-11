# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 85: a primary-energy cap and an operational limit for one period over storage that reopens per period, on a network with scenarios — each scenario closes its storage at its own level."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}

#: the clean unit's marginal cost in each scenario
CLEAN_COST = {'calm': 60, 'stormy': 90}


def build():
    """Rung 75's network over two futures in which the clean unit costs 60 and 90, with a 2030 limit on the gas carrier as well."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [5.0, 10.0]
    n.add('Carrier', 'gas85', co2_emissions=0.5)
    n.add('Bus', 'hub')
    n.add('Generator', 'gas85', bus='hub', carrier='gas85', p_nom=100, marginal_cost=30)
    n.add('Generator', 'clean85', bus='hub', p_nom=200, marginal_cost=60)
    n.add(
        'StorageUnit',
        'tank85',
        bus='hub',
        carrier='gas85',
        p_nom=20,
        max_hours=4,
        state_of_charge_initial=60,
        state_of_charge_initial_per_period=True,
    )
    n.add('Store', 'pile85', bus='hub', carrier='gas85', e_nom=60, e_initial=40, e_initial_per_period=True)
    n.add('Load', 'town85', bus='hub', p_set=[60, 80, 70, 50, 90, 110, 100, 80])
    n.add(
        'GlobalConstraint',
        'co2_2030',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='<=',
        constant=600,
        investment_period=2030,
    )
    n.add(
        'GlobalConstraint',
        'gas_2030',
        type='operational_limit',
        carrier_attribute='gas85',
        sense='<=',
        constant=1100,
        investment_period=2030,
    )
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    for scenario, cost in CLEAN_COST.items():
        n.c.generators.static.loc[(scenario, 'clean85'), 'marginal_cost'] = cost
    return n
