# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 76: stores that cover a storage unit — a power rating through `max_hours`, an efficiency each way, inflow and spill, and a cost each way."""

from __future__ import annotations

import spine


def build():
    """The spine plus four stores: a rated battery with two efficiencies, a reservoir with inflow, an extendable lossy store and an unrated extendable one, under a swinging load."""
    n = spine.build()
    n.add(
        'Store',
        'battery76',
        bus='south',
        e_nom=40,
        max_hours=2,
        efficiency_store=0.9,
        efficiency_dispatch=0.95,
        marginal_cost_dispatch=1,
        e_cyclic=True,
    )
    n.add(
        'Store',
        'reservoir76',
        bus='south',
        e_nom=60,
        max_hours=4,
        p_min_pu=0,
        inflow=[20, 20, 20, 20],
        spill_cost=2,
        e_initial=50,
    )
    n.add(
        'Store',
        'ext76',
        bus='south',
        e_nom_extendable=True,
        e_nom_max=80,
        capital_cost=1,
        max_hours=4,
        efficiency_store=0.8,
        marginal_cost_store=0.5,
        e_cyclic=True,
    )
    n.add('Store', 'plain76', bus='north', e_nom_extendable=True, capital_cost=3, e_cyclic=True)
    n.add('Load', 'swing76', bus='south', p_set=[0, 60, 0, 70])
    return n
