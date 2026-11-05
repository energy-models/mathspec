# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 74: a relaxed committable unit built in the later period — its tightening rows open on a zero output and a zero status at its first snapshot."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

PATCH = 'variants/pypsa_linearized_uc.yaml'
OPTIMIZE = {'linearized_unit_commitment': True, 'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods, a cheap tightened unit built in 2030, and a dear peaker."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0, 2.0, 1.5, 2.5, 2.0]
    n.add('Bus', 'hub')
    n.add('Generator', 'peak74', bus='hub', p_nom=300, marginal_cost=50)
    n.add(
        'Generator',
        'late74',
        bus='hub',
        committable=True,
        p_nom=60,
        p_min_pu=0.2,
        marginal_cost=2,
        start_up_cost=10,
        shut_down_cost=10,
        ramp_limit_up=0.25,
        ramp_limit_down=0.25,
        ramp_limit_start_up=0.5,
        ramp_limit_shut_down=0.5,
        build_year=2030,
        lifetime=30,
    )
    n.add('Load', 'hub_load74', bus='hub', p_set=[40, 60, 70, 50, 50, 60, 55, 20])
    return n
