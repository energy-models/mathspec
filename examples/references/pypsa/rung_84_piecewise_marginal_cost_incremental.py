# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 84: piecewise `marginal_cost` curves stated by increments — a committable link and a committable process gate theirs by their status, and a storage unit and a store whose curves bend down have none."""

from __future__ import annotations

import spine


def build():
    """The spine plus committable links and processes with curves, storage with curves that are not convex, and a convex generator curve that stays as segment lines."""
    n = spine.build()
    n.add('Generator', 'north84', bus='north', p_nom=200, marginal_cost=5)
    n.add(
        'Link',
        'block84',
        bus0='north',
        bus1='south',
        p_nom=60,
        committable=True,
        stand_by_cost=20,
        marginal_cost={0.0: 0.0, 0.25: 8.0, 1.0: 2.0},
    )
    n.add('Link', 'curve84', bus0='north', bus1='south', p_nom=30, marginal_cost={0.0: 0.0, 0.5: 3.0, 1.0: 12.0})
    n.add(
        'Process',
        'process84',
        bus0='north',
        bus1='south',
        rate0=-1,
        rate1=0.9,
        p_nom=50,
        committable=True,
        stand_by_cost=10,
        marginal_cost={0.0: 0.0, 0.4: 9.0, 1.0: 4.0},
    )
    n.add('StorageUnit', 'battery84', bus='south', p_nom=30, max_hours=2, marginal_cost={0.0: 0.0, 0.5: 8.0, 1.0: 1.0})
    n.add('Store', 'tank84', bus='south', e_nom=40, e_initial=20, marginal_cost={-1.0: 0.0, 0.0: 5.0, 1.0: 1.0})
    n.add('Generator', 'curve84g', bus='south', p_nom=80, marginal_cost={0.0: 0.0, 0.5: 25.0, 1.0: 35.0})
    n.add('Load', 'south_peak84', bus='south', p_set=[10, 60, 110, 200])
    return n
