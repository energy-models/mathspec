# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 77: energy limits on every dispatching component — `e_sum_min` and `e_sum_max` on a generator, link, process and store, with each period weighted by its years."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods of unequal years, a cheap supply on a fuel bus, and four units under energy limits feeding a hub."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [5.0, 10.0]
    n.snapshot_weightings['generators'] = [1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0]
    n.add('Bus', ['fuel', 'hub'])
    n.add('Generator', 'well77', bus='fuel', p_nom=200, marginal_cost=1)
    n.add('Generator', 'cheap77', bus='hub', p_nom=50, marginal_cost=5, e_sum_max=2500)
    n.add('Generator', 'dear77', bus='hub', p_nom=200, marginal_cost=80)
    n.add('Link', 'pipe77', bus0='fuel', bus1='hub', p_nom=40, marginal_cost=90, e_sum_min=400, e_sum_max=5000)
    n.add(
        'Process',
        'plant77',
        bus0='fuel',
        bus1='hub',
        rate0=-1.25,
        p_nom=40,
        marginal_cost=6,
        e_sum_min=100,
        e_sum_max=1800,
    )
    n.add('Store', 'pile77', bus='hub', e_nom=200, e_initial=200, marginal_cost=3, e_sum_min=-50, e_sum_max=150)
    n.add('Load', 'hub_load77', bus='hub', p_set=[90, 110, 100, 80, 100, 120, 110, 90])
    return n
