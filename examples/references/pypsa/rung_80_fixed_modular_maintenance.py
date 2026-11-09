# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 80: maintenance of fixed modular committable units — a generator, a link and a process of four modules each take all their modules off for one event."""

from __future__ import annotations

import spine


def build():
    """The spine plus a shop bus served by a fixed modular committable generator, link and process, each maintainable, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'shop')
    unit = {
        'p_nom': 40,
        'p_nom_mod': 10,
        'committable': True,
        'maintainable': True,
        'maintenance_duration': 1,
    }
    n.add('Generator', 'gen80', bus='shop', marginal_cost=5, **unit)
    n.add('Link', 'link80', bus0='north', bus1='shop', marginal_cost=1, **unit)
    n.add('Process', 'process80', bus0='north', bus1='shop', rate0=-1.25, marginal_cost=1, **unit)
    n.add('Generator', 'shop_backup', bus='shop', p_nom=200, marginal_cost=60)
    n.add('Load', 'shop_load', bus='shop', p_set=[70, 90, 60, 80])
    return n
