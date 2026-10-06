# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 68: outage factors per period — a security-constrained run outages a line that retires before the last period.

PyPSA takes the outage factors of every period from the last period's
network, so an outage of a line that is gone by then builds no rows
(PyPSA/PyPSA#1971). The network has no build to decide, so each period
solves on its own, and in a network of one period the last period is that
period: the oracle is the network once per period.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

ISSUE = 1971
OPTIMIZE = {'multi_investment_periods': True}
BRANCH_OUTAGES = ['ab_old68']
PERIODS = {2020: (1.0, [2.0, 1.5], [80, 70]), 2030: (0.5, [2.5, 3.0], [90, 60])}


def network(periods: list[int]):
    """Cheap hydro at `a`, a town with diesel at `b`, and two parallel lines; `ab_old68` retires in 2025."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples([(p, datetime(p, 1, 1, t)) for p in periods for t in range(2)])
    n.investment_periods = periods
    n.investment_period_weightings['objective'] = [PERIODS[p][0] for p in periods]
    n.investment_period_weightings['years'] = 10.0
    n.snapshot_weightings['objective'] = [w for p in periods for w in PERIODS[p][1]]
    n.add('Bus', ['a', 'b'])
    n.add('Generator', 'hydro68', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel68', bus='b', p_nom=300, marginal_cost=100)
    n.add('Load', 'town68', bus='b', p_set=[load for p in periods for load in PERIODS[p][2]])
    n.add('Line', 'ab68', bus0='a', bus1='b', x=0.1, s_nom=60)
    n.add('Line', 'ab_old68', bus0='a', bus1='b', x=0.1, s_nom=60, build_year=2000, lifetime=25)
    return n


def build():
    """Both periods: after the outage of `ab_old68`, `ab68` carries the whole import of 2020 alone."""
    return network(list(PERIODS))


def oracle():
    """Each period alone, whose last period is its own."""
    return [(1.0, network([p])) for p in PERIODS]
