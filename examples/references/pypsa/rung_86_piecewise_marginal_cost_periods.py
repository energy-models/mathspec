# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 86: a piecewise `marginal_cost` curve under `multi_investment_periods` — the curve holds at every snapshot of every period, and each period weighs its cost."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: four snapshots over two periods, a generator with rung 81's curve, and a dear backup unit."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.add('Bus', 'hub')
    n.add('Generator', 'curve86', bus='hub', p_nom=80, marginal_cost={0.0: 0.0, 0.25: 12.0, 0.5: 20.0, 1.0: 45.0})
    n.add('Generator', 'backup86', bus='hub', p_nom=200, marginal_cost=50)
    n.add('Load', 'town86', bus='hub', p_set=[30, 60, 50, 100])
    return n
