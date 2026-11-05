# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 64: commitment edges — a committable generator, link and process built in the later period start up when they open, and a committable unit without a build cap is released by an inferred big M."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods, three committable units built in 2030, an uncapped committable build, and a dear peaker."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0, 2.0, 1.5, 2.5, 2.0]
    n.add('Bus', ['hub', 'fuel'])
    n.add('Generator', 'well64', bus='fuel', p_nom=200, marginal_cost=1)
    n.add('Generator', 'peak64', bus='hub', p_nom=300, marginal_cost=50)
    late = {'committable': True, 'p_nom': 30, 'p_min_pu': 0.25, 'build_year': 2030, 'lifetime': 30}
    n.add('Generator', 'late_gen64', bus='hub', marginal_cost=2, start_up_cost=100, **late)
    n.add('Link', 'late_link64', bus0='fuel', bus1='hub', marginal_cost=1, start_up_cost=70, **late)
    n.add('Process', 'late_proc64', bus0='fuel', bus1='hub', rate0=-1.25, start_up_cost=40, **late)
    n.add(
        'Generator',
        'uncapped64',
        bus='hub',
        committable=True,
        p_nom_extendable=True,
        capital_cost=20,
        marginal_cost=10,
        p_min_pu=0.2,
        up_time_before=0,
        start_up_cost=30,
    )
    n.add('Load', 'hub_load64', bus='hub', p_set=[40, 60, 70, 50, 120, 140, 150, 130])
    return n
