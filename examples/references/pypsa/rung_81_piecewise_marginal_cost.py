# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 81: a piecewise `marginal_cost` curve — a generator that is not committable pays a convex cost curve, which PyPSA states as the line of each segment."""

from __future__ import annotations

import spine


def build():
    """The spine plus a generator on the south bus whose marginal cost climbs from 12 to 20 to 45 over three segments, and a south load that walks it up every segment."""
    n = spine.build()
    n.add('Generator', 'curve81', bus='south', p_nom=80, marginal_cost={0.0: 0.0, 0.25: 12.0, 0.5: 20.0, 1.0: 45.0})
    n.add('Load', 'south_peak81', bus='south', p_set=[20, 60, 100, 170])
    return n
