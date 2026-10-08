# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 69: storage that retires before the last counted snapshot closes a `primary_energy` row at the last level it holds."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: four snapshots over two periods, a store and a storage unit of an emitting carrier that retire after 2020, and a CO2 cap over the horizon."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.add('Carrier', 'gas', co2_emissions=1.0)
    n.add('Bus', 'hub')
    n.add('Generator', 'base69', bus='hub', p_nom=100, marginal_cost=10)
    n.add('Load', 'hub_load', bus='hub', p_set=10)
    n.add('Store', 'e_retire', bus='hub', carrier='gas', e_nom=30, e_initial=20, build_year=2020, lifetime=10)
    n.add(
        'StorageUnit',
        'su_retire',
        bus='hub',
        carrier='gas',
        p_nom=10,
        max_hours=3,
        state_of_charge_initial=20,
        build_year=2020,
        lifetime=10,
    )
    n.add(
        'GlobalConstraint', 'co2_cap', type='primary_energy', carrier_attribute='co2_emissions', sense='<=', constant=5
    )
    return n
