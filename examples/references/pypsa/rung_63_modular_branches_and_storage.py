# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 63: modular branches and storage — a line, a transformer, a storage unit and a store each built in whole modules, beside a modular generator, link and process that are not active."""

from __future__ import annotations

import spine


def build():
    """The spine plus an east bus fed over a modular line and a modular transformer, with a modular storage unit and store, and three inactive modular builds."""
    n = spine.build()
    n.add('Bus', 'east')
    n.add(
        'Line', 'ne63', bus0='north', bus1='east', x=0.01, r=0.001, s_nom_extendable=True, s_nom_mod=25, capital_cost=3
    )
    n.add('Transformer', 'se63', bus0='south', bus1='east', x=0.01, s_nom_extendable=True, s_nom_mod=15, capital_cost=2)
    n.add(
        'StorageUnit',
        'battery63',
        bus='east',
        p_nom_extendable=True,
        p_nom_mod=15,
        max_hours=2,
        capital_cost=5,
        cyclic_state_of_charge=True,
    )
    n.add('Store', 'tank63', bus='east', e_nom_extendable=True, e_nom_mod=40, capital_cost=2, e_cyclic=True)
    n.add('Generator', 'east_backup63', bus='east', p_nom=200, marginal_cost=200)
    n.add('Load', 'east_load63', bus='east', p_set=[20, 70, 110, 40])
    idle = {'p_nom_extendable': True, 'p_nom_mod': 20, 'capital_cost': 1, 'marginal_cost': 1, 'active': False}
    n.add('Generator', 'idle_gen63', bus='east', **idle)
    n.add('Link', 'idle_link63', bus0='north', bus1='east', **idle)
    n.add('Process', 'idle_proc63', bus0='south', bus1='east', rate0=-1.25, **idle)
    return n
