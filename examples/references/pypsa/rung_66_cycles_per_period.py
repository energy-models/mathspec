# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 66: cycles per period — a line that comes in with the second period closes a triangle, under a security-constrained run that outages it."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}
BRANCH_OUTAGES = ['ca66']


def build():
    """A whole network, not the spine: a path from `a` to `c` in 2020, and a triangle in 2030 once `ca66` stands."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 3.0]
    n.add('Bus', ['a', 'b', 'c'])
    n.add('Generator', 'hydro66', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel66', bus='c', p_nom=300, marginal_cost=100)
    n.add('Load', 'town66', bus='c', p_set=[80, 100, 90, 110])
    n.add('Line', 'ab66', bus0='a', bus1='b', x=0.1, s_nom=150)
    n.add('Line', 'bc66', bus0='b', bus1='c', x=0.1, s_nom=150)
    n.add('Line', 'ca66', bus0='c', bus1='a', x=0.1, s_nom=40, build_year=2030, lifetime=50)
    return n
