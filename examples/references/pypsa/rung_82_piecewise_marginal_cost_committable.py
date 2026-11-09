# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 82: a piecewise `marginal_cost` curve on a committable generator — its status gates the curve, and PyPSA states every curve of the call by increments filled in order."""

from __future__ import annotations

import spine


def build():
    """Rung 81's network plus a committable generator on the south bus whose curve is not convex: its first 20 MW cost 40 and the rest 15, and every snapshot on costs 50."""
    n = spine.build()
    n.add('Generator', 'curve82', bus='south', p_nom=80, marginal_cost={0.0: 0.0, 0.25: 12.0, 0.5: 20.0, 1.0: 45.0})
    n.add(
        'Generator',
        'block82',
        bus='south',
        p_nom=100,
        committable=True,
        stand_by_cost=50,
        marginal_cost={0.0: 0.0, 0.2: 40.0, 1.0: 15.0},
    )
    n.add('Load', 'south_peak82', bus='south', p_set=[20, 60, 100, 180])
    return n
