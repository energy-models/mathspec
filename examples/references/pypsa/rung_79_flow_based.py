# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 79: flow-based market coupling — three zones trade through their net positions under two critical network elements, one of them with a corridor link."""

from __future__ import annotations

import math

import pandas as pd


def build():
    """A whole network, not the spine: three zone buses with their own supply and load, a corridor link from one to another, and a two-row flow-based domain."""
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(pd.date_range('2015-01-01', periods=4, freq='h'))
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 3.0]
    n.add('Bus', ['north79', 'centre79', 'south79'])
    n.add('Generator', 'hydro79', bus='north79', p_nom=200, marginal_cost=5)
    n.add('Generator', 'coal79', bus='centre79', p_nom=200, marginal_cost=30)
    n.add('Generator', 'gas79', bus='south79', p_nom=200, marginal_cost=60)
    n.add('Load', 'north_load79', bus='north79', p_set=20)
    n.add('Load', 'centre_load79', bus='centre79', p_set=[40, 50, 60, 50])
    n.add('Load', 'south_load79', bus='south79', p_set=[80, 90, 100, 70])
    n.add('Link', 'hvdc79', bus0='north79', bus1='south79', p_nom=30, p_min_pu=-1)
    ptdf = pd.DataFrame(
        {'north79': [0.6, 0.2], 'centre79': [0.1, 0.5], 'south79': [-0.3, -0.2], 'hvdc79': [-0.4, 0.0]},
        index=['ns79', 'cs79'],
    )
    ram = pd.DataFrame({'ns79': [40.0, 40.0, 40.0, 40.0], 'cs79': [30.0, math.nan, 25.0, 30.0]}, index=n.snapshots)
    n.c.global_constraints.add_flow_based(ptdf, ram=ram, domain='core79')
    return n
