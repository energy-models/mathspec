# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 75: a primary-energy cap for one period over storage that reopens per period — the cap counts the storage change of its own period alone."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods of unequal years, a gas unit, and a gas storage unit and store that each reopen per period."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [5.0, 10.0]
    n.add('Carrier', 'gas75', co2_emissions=0.5)
    n.add('Bus', 'hub')
    n.add('Generator', 'gas75', bus='hub', carrier='gas75', p_nom=100, marginal_cost=30)
    n.add('Generator', 'clean75', bus='hub', p_nom=200, marginal_cost=60)
    n.add(
        'StorageUnit',
        'tank75',
        bus='hub',
        carrier='gas75',
        p_nom=20,
        max_hours=4,
        state_of_charge_initial=60,
        state_of_charge_initial_per_period=True,
    )
    n.add('Store', 'pile75', bus='hub', carrier='gas75', e_nom=60, e_initial=40, e_initial_per_period=True)
    n.add('Load', 'town75', bus='hub', p_set=[60, 80, 70, 50, 90, 110, 100, 80])
    n.add(
        'GlobalConstraint',
        'co2_2030',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='<=',
        constant=600,
        investment_period=2030,
    )
    return n
