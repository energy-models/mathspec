# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 71: a unit that is not committable comes in running — its first-snapshot ramp starts from its `p_init`, whatever its `up_time_before` and whether another unit is committable."""

from __future__ import annotations

import spine


def build():
    """The spine plus a cheap ramp-limited unit that is not committable, with `up_time_before=0` and a `p_init`, beside a committable one."""
    n = spine.build()
    n.add(
        'Generator',
        'flex71',
        bus='south',
        p_nom=40,
        marginal_cost=5,
        ramp_limit_up=0.25,
        ramp_limit_start_up=0.5,
        up_time_before=0,
        p_init=10,
    )
    n.add('Generator', 'unit71', bus='south', committable=True, p_nom=20, p_min_pu=0.5, marginal_cost=20)
    return n
