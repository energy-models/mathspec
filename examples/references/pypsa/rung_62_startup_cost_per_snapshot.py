# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 62: a start-up cost per snapshot — a committable unit starts in the snapshot where a start costs least, with no snapshot weight on that cost."""

from __future__ import annotations

from datetime import datetime

SNAPSHOTS = [datetime(2015, 1, 1, hour) for hour in range(5)]
WEIGHTINGS = [2.0, 1.5, 1.0, 2.0, 1.0]
START_UP_COST = [400.0, 100.0, 900.0, 900.0, 900.0]
SHUT_DOWN_COST = [300.0, 300.0, 300.0, 300.0, 0.0]


def build():
    """A whole network, not the spine: a committable peaker the load needs in the third and fourth snapshots, cheap to start one snapshot early and free to stop in the last."""
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(SNAPSHOTS)
    n.snapshot_weightings['objective'] = WEIGHTINGS
    n.add('Bus', 'grid')
    n.add('Generator', 'base62', bus='grid', p_nom=60, marginal_cost=10)
    n.add('Generator', 'dear62', bus='grid', p_nom=100, marginal_cost=90)
    n.add(
        'Generator',
        'peak62',
        bus='grid',
        p_nom=50,
        marginal_cost=20,
        committable=True,
        p_min_pu=0.4,
        up_time_before=0,
    )
    n.generators_t.start_up_cost['peak62'] = START_UP_COST
    n.generators_t.shut_down_cost['peak62'] = SHUT_DOWN_COST
    n.add('Load', 'town62', bus='grid', p_set=[50, 50, 100, 100, 50])
    return n
