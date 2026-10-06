# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 70: rung 14 with a risk preference of weight zero — PyPSA builds the CVaR columns and rows all the same."""

from __future__ import annotations

import spine


def build():
    """Rung 14's calm and stormy futures, with `omega = 0`: the optimum is the risk-neutral one."""
    n = spine.build()
    n.add('Generator', 'wind70', bus='south', p_nom_extendable=True, p_nom_max=100, marginal_cost=1, capital_cost=20)
    n.add('Load', 'port70', bus='south')
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    n.c.loads.dynamic.p_set[('calm', 'port70')] = [10, 20, 15, 10]
    n.c.loads.dynamic.p_set[('stormy', 'port70')] = [40, 60, 50, 30]
    n.c.generators.dynamic.p_max_pu[('calm', 'wind70')] = [0.9, 0.7, 0.8, 0.6]
    n.c.generators.dynamic.p_max_pu[('stormy', 'wind70')] = [0.3, 0.2, 0.4, 0.1]
    n.set_risk_preference(alpha=0.5, omega=0.0)
    return n
