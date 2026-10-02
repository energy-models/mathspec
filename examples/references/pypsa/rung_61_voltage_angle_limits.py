# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 61: voltage angle limits — a line, a transformer with a fixed phase shift and one with a decided shift, each holding the angle difference across it within its `v_ang_max`.

A line beside the spine's link may carry only the flow that keeps the angle
across it within one degree, so the lossy link carries the rest. Two triangles
carry cheap upstream power to a town past a costly local unit. In the first a
transformer has a fixed shift, in the second the shift is a decision; the
angle cap on each transformer binds before its thermal rating does, so the
local unit runs. In one cycle the angle caps of all branches couple, so each
triangle carries one cap only. No scenario: with scenarios PyPSA builds no
angle row.
"""

from __future__ import annotations

import spine


def build():
    """The spine plus a line beside its link and two triangles, each with one voltage angle limit that binds, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Line', 'north_south61', bus0='north', bus1='south', carrier='AC', x=0.002, s_nom=100, v_ang_max=1)
    n.add('Bus', ['a', 'b', 'c'])
    n.add('Generator', 'hydro61', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel61', bus='c', p_nom=300, marginal_cost=200)
    n.add('Load', 'town61', bus='c', p_set=[90, 75, 120, 105])
    n.add('Line', 'ab61', bus0='a', bus1='b', carrier='AC', x=0.002, s_nom=200)
    n.add('Line', 'bc61', bus0='b', bus1='c', carrier='AC', x=0.002, s_nom=200)
    n.add('Transformer', 'ca61', bus0='c', bus1='a', x=0.4, s_nom=200, phase_shift=2, v_ang_max=2.5)
    n.add('Bus', ['d', 'e', 'f'])
    n.add('Generator', 'hydro61_shift', bus='d', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel61_shift', bus='f', p_nom=300, marginal_cost=200)
    n.add('Load', 'town61_shift', bus='f', p_set=[90, 75, 120, 105])
    n.add('Line', 'de61', bus0='d', bus1='e', carrier='AC', x=0.002, s_nom=200)
    n.add('Line', 'ef61', bus0='e', bus1='f', carrier='AC', x=0.002, s_nom=200)
    n.add(
        'Transformer',
        'fd61',
        bus0='f',
        bus1='d',
        x=0.4,
        s_nom=80,
        phase_shift_min=-30,
        phase_shift_max=30,
        v_ang_max=5,
    )
    return n
