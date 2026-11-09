# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 72: modular down time — a committable modular unit that stops some modules keeps the others running, because its down-time row is bound by its module count, not by one."""

from __future__ import annotations

import spine


def build():
    """The spine plus a dip bus served by a fixed and an extendable committable modular unit, each with a minimum down time, and a dear backup."""
    n = spine.build()
    n.add('Bus', 'dip')
    common = {
        'committable': True,
        'p_nom_mod': 10,
        'p_min_pu': 0.8,
        'min_down_time': 2,
        'up_time_before': 0,
        'start_up_cost': 5,
    }
    n.add('Generator', 'fixed72', bus='dip', p_nom=40, marginal_cost=2, **common)
    n.add(
        'Generator',
        'ext72',
        bus='dip',
        p_nom_extendable=True,
        p_nom_max=30,
        capital_cost=1,
        marginal_cost=3,
        **common,
    )
    n.add('Generator', 'dip_backup', bus='dip', p_nom=200, marginal_cost=100)
    n.add('Load', 'dip_load', bus='dip', p_set=[60, 15, 60, 70])
    return n
