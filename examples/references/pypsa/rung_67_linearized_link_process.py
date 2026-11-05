# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 67: linearized commitment of a link and a process — both tightened where start and stop cost the same, and an extendable link the tightening skips."""

from __future__ import annotations

import spine

PATCH = 'variants/pypsa_linearized_uc.yaml'
OPTIMIZE = {'linearized_unit_commitment': True}


def build():
    """The spine plus an east bus that committable links and a process serve from the north, and a dear backup there."""
    n = spine.build()
    n.add('Bus', 'east')
    n.add(
        'Link',
        'tie67',
        bus0='north',
        bus1='east',
        committable=True,
        p_nom=60,
        p_min_pu=0.3,
        marginal_cost=4,
        min_up_time=2,
        up_time_before=0,
        ramp_limit_up=0.4,
        ramp_limit_down=0.4,
        ramp_limit_start_up=0.5,
        ramp_limit_shut_down=0.5,
        start_up_cost=30,
        shut_down_cost=30,
    )
    n.add(
        'Process',
        'conv67',
        bus0='north',
        bus1='east',
        rate0=-1.25,
        committable=True,
        p_nom=50,
        p_min_pu=0.3,
        marginal_cost=3,
        min_up_time=2,
        up_time_before=0,
        ramp_limit_up=0.4,
        ramp_limit_down=0.4,
        ramp_limit_start_up=0.5,
        ramp_limit_shut_down=0.5,
        start_up_cost=20,
        shut_down_cost=20,
    )
    n.add(
        'Link',
        'ext67',
        bus0='north',
        bus1='east',
        committable=True,
        p_nom_extendable=True,
        p_nom_max=30,
        capital_cost=5,
        p_min_pu=0.2,
        marginal_cost=2,
        up_time_before=0,
        start_up_cost=10,
        shut_down_cost=10,
    )
    n.add('Generator', 'backup67', bus='east', p_nom=200, marginal_cost=400)
    n.add('Load', 'east_load', bus='east', p_set=[10, 110, 120, 20])
    return n
