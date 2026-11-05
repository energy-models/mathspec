# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 78: a cycle limit on a store — the discharge over the horizon is at most `cycles_max` times the build, fixed or chosen."""

from __future__ import annotations

import spine


def build():
    """The spine plus a fixed and an extendable store on the south bus, each with a cycle limit, under a swinging load."""
    n = spine.build()
    n.add('Store', 'cell78', bus='south', e_nom=30, e_cyclic=True, cycles_max=0.5)
    n.add('Store', 'pack78', bus='south', e_nom_extendable=True, capital_cost=1, e_cyclic=True, cycles_max=0.5)
    n.add('Load', 'swing78', bus='south', p_set=[0, 60, 0, 70])
    return n
