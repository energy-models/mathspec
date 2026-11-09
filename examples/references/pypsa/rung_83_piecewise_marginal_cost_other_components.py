# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 83: a piecewise `marginal_cost` curve on a link, a process, a storage unit and a store — each curve is convex and no unit with one is committable, so PyPSA states each as the line of each segment."""

from __future__ import annotations

import spine


def build():
    """The spine plus a cheap north generator, a curve on each of the four other components that take one, and a south load that walks them up their segments.

    The link's curve starts at full reverse flow and the store's at full charging, so each costs something at zero.
    """
    n = spine.build()
    n.add('Generator', 'north83', bus='north', p_nom=200, marginal_cost=5)
    n.add(
        'Link',
        'curve83',
        bus0='north',
        bus1='south',
        p_nom=60,
        p_min_pu=-1,
        efficiency=0.95,
        marginal_cost={-1.0: 0.0, 0.0: 1.0, 0.5: 4.0, 1.0: 9.0},
    )
    n.add(
        'Process',
        'process83',
        bus0='north',
        bus1='south',
        rate0=-1,
        rate1=0.9,
        p_nom=50,
        marginal_cost={0.0: 0.0, 0.4: 6.0, 1.0: 14.0},
    )
    n.add('StorageUnit', 'battery83', bus='south', p_nom=30, max_hours=2, marginal_cost={0.0: 0.0, 0.5: 2.0, 1.0: 6.0})
    n.add(
        'Store', 'tank83', bus='south', e_nom=40, e_initial=20, marginal_cost={-1.0: 0.0, 0.0: 0.5, 0.5: 3.0, 1.0: 7.0}
    )
    n.add('Load', 'south_peak83', bus='south', p_set=[10, 60, 110, 160])
    return n
