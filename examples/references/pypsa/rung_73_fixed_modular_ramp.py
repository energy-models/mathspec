# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 73: the ramp of a fixed modular committable unit — each running module ramps by its own share, and a unit that came in running counts all its modules on at the first snapshot."""

from __future__ import annotations

import spine


def build():
    """The spine plus a step bus served by a fixed committable modular unit that came in running at a `p_init`, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'step')
    n.add(
        'Generator',
        'modramp73',
        bus='step',
        committable=True,
        p_nom=60,
        p_nom_mod=20,
        p_min_pu=0.2,
        marginal_cost=2,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        ramp_limit_start_up=0.5,
        ramp_limit_shut_down=0.5,
        p_init=15,
    )
    n.add('Generator', 'step_backup', bus='step', p_nom=200, marginal_cost=100)
    n.add('Load', 'step_load', bus='step', p_set=[60, 20, 55, 30])
    return n
