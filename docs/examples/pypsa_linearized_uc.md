<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA, the relaxed commitment

`n.optimize(linearized_unit_commitment=True)` is a patch over
[PyPSA in one file](pypsa.md), `examples/variants/pypsa_linearized_uc.yaml`.
Lay it over the base:

```python
import mathspec as ms

spec = ms.override('examples/pypsa.yaml', ['examples/variants/pypsa_linearized_uc.yaml'])
```

The patch changes only what the keyword changes:

- The status, start and stop of a committable generator, link and process are
  shares in [0, 1] rather than integers (`variables.py:81-90`, `:132-141`,
  `:183-192`).
- Four rows tighten the relaxation of a unit with a fixed build whose start
  and stop cost the same in every snapshot (`constraints.py:633-733`).
- A modular committable unit is refused, as PyPSA refuses it
  (`optimize.py:772-773`).

Every other row is the integer run's, with its scenarios, periods and `active`
masks. Rungs 12, 44, 47 and 67 solve the patched spec. Each network is the
spine plus the script's own additions.

## Rung 12 — linearized unit commitment

| PyPSA | status | note |
| --- | --- | --- |
| [`Generator-status`](#generator-status), [`-start_up`](#generator-start_up), [`-shut_down`](#generator-shut_down) | done | shares in [0, 1] |
| [`Generator-com-p-before`](#generator-com-p-before) | done | where start and stop cost the same in every snapshot — a `count` over `snapshot` |
| [`Generator-com-p-current`](#generator-com-p-current) | done | |
| [`Generator-com-partly-start-up`](#generator-com-partly-start-up) | done | |
| [`Generator-com-partly-shut-down`](#generator-com-partly-shut-down) | done | |

<!-- reference:rung_12_linearized_uc:begin -->
> ✔ `pypsa 1.3.0.post1.dev23+g02bdcbbaf` solves this rung's network at objective `7775.0`, 128 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_12_linearized_uc.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 12: linearized unit commitment — the status a share in [0, 1], stated by the patch `variants/pypsa_linearized_uc.yaml`."""

from __future__ import annotations

import spine

PATCH = 'variants/pypsa_linearized_uc.yaml'
OPTIMIZE = {'linearized_unit_commitment': True}


def build():
    """The spine plus two committable units, one whose start and stop cost the same, so PyPSA tightens its relaxation."""
    n = spine.build()
    n.add(
        'Generator',
        'uc12',
        bus='north',
        committable=True,
        p_nom=50,
        marginal_cost=5,
        p_min_pu=0.4,
        min_up_time=3,
        min_down_time=2,
        up_time_before=1,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        ramp_limit_start_up=0.6,
        ramp_limit_shut_down=0.6,
        start_up_cost=100,
        shut_down_cost=100,
        stand_by_cost=5,
    )
    n.add(
        'Generator',
        'cold12',
        bus='south',
        committable=True,
        p_nom=30,
        marginal_cost=60,
        p_min_pu=0.3,
        min_up_time=2,
        min_down_time=1,
        up_time_before=0,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        ramp_limit_start_up=0.7,
        ramp_limit_shut_down=0.7,
        start_up_cost=80,
        shut_down_cost=40,
    )
    n.add('Load', 'swing12', bus='north', p_set=[25, 45, 45, 10])
    return n
```

</details>
<!-- reference:rung_12_linearized_uc:end -->

## Rung 44 — the integer file's commitment rows, relaxed

`n.optimize(linearized_unit_commitment=True)` builds the same commitment rows as
the integer run, except the four tightening rows: the keyword only relaxes the
status, start and stop to shares in [0, 1] (`variables.py:81-88`) and adds the
tightening rows (`constraints.py:656`). So the patch leaves each of these rows
to [PyPSA in one file](pypsa.md), and this rung checks them under the keyword:

- A unit still serving the down time it brought in stays off
  (`constraints.py:625-631`).
- A ramp row stands where a unit has a ramp limit or only a start-up or
  shut-down ramp, and a missing limit reads as the full build
  (`constraints.py:1052-1061`).
- A maintainable unit is taken off for its events. The maintenance start stays
  a binary under the keyword (`variables.py:234-259`), and the product of
  status and maintenance enters the commitment rows through the `maint-status`
  rows (`constraints.py:428-461`). A maintainable unit that is not committable
  loses the same share of its fixed rows (`constraints.py:138-148`).

The rung adds five cheap units under a swinging load. A start costs more than a
stop, so PyPSA does not tighten them and the rung isolates these rows. Each
binds: PyPSA solves to `7400.0`. Without the brought-in down time it solves to
`6540.0`; without the start-up ramp, to `7164.0`; with the missing start-up and
shut-down ramps read as `0`, to `8060.0`; with the committable unit not
maintainable, to `7310.0`; with the fixed unit not maintainable, to `7100.0`.

| PyPSA | status | note |
| --- | --- | --- |
| [`Generator-com-status-min_down_time_must_stay_up`](pypsa.md#generator-com-status-min_down_time_must_stay_up) | done | |
| [`Generator-p-ramp_limit_up`](pypsa.md#generator-p-ramp_limit_up), [`-down`](pypsa.md#generator-p-ramp_limit_down) for a start-up or shut-down ramp alone, and a missing limit | done | `Generator_ramp_up_rate` and the other three rates read a missing limit as `1` |
| [`Generator-maint-*`](pypsa.md#generator-maint-event-count), [`Generator-maint-status-*`](pypsa.md#generator-maint-status-le-status) | done | fixed units |
| [`Generator-com-p-lower`](pypsa.md#generator-com-p-lower), [`-upper`](pypsa.md#generator-com-p-upper), [`Generator-fix-p-lower`](pypsa.md#generator-fix-p-lower), [`-upper`](pypsa.md#generator-fix-p-upper) in maintenance | done | |

<!-- reference:rung_44_linearized_commitment:begin -->
> ✔ `pypsa 1.3.0.post1.dev23+g02bdcbbaf` solves this rung's network at objective `7400.0`, 191 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_44_linearized_commitment.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 44: linearized commitment with the rows the integer file has — a unit that must stay down, ramps read at the full build where a limit is missing, and maintenance."""

from __future__ import annotations

import spine

PATCH = 'variants/pypsa_linearized_uc.yaml'
OPTIMIZE = {'linearized_unit_commitment': True}

#: a start costs more than a stop, so PyPSA does not tighten these units and the rung isolates the rows it adds
UNTIGHTENED = {'committable': True, 'up_time_before': 0, 'start_up_cost': 1}


def build():
    """The spine plus five cheap units on a north bus with a swinging load: each carries one of the rows under review."""
    n = spine.build()
    n.add(
        'Generator',
        'down44',
        bus='north',
        p_nom=40,
        marginal_cost=2,
        min_down_time=3,
        down_time_before=1,
        **UNTIGHTENED,
    )
    n.add('Generator', 'pulse44', bus='north', p_nom=40, marginal_cost=3, ramp_limit_start_up=0.4, **UNTIGHTENED)
    n.add(
        'Generator',
        'ramp44',
        bus='north',
        p_nom=40,
        marginal_cost=4,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        **UNTIGHTENED,
    )
    n.add(
        'Generator',
        'maint44',
        bus='north',
        p_nom=40,
        p_min_pu=0.3,
        marginal_cost=5,
        maintainable=True,
        maintenance_duration=2,
        **UNTIGHTENED,
    )
    n.add('Generator', 'fixed44', bus='north', p_nom=20, marginal_cost=1, maintainable=True, maintenance_duration=1)
    n.add('Load', 'swing44', bus='north', p_set=[40, 120, 160, 60])
    return n
```

</details>
<!-- reference:rung_44_linearized_commitment:end -->

## Rung 47 — ramps and signs, as the integer file states them

This rung checks five rows under the keyword, each on fixed builds. The patch
writes the first; [PyPSA in one file](pypsa.md) states the other four:

- The four tightening rows read each ramp limit filled to the full build where
  it is missing (`constraints.py:316-321`). They read `Generator_ramp_up_rate`
  and the other three rates.
- A ramp limit is given per snapshot and read at the later of the two
  snapshots (`constraints.py:1046-1047`). A row is absent at a snapshot where
  neither the limit nor the start-up or shut-down ramp has a value
  (`constraints.py:1052-1053`, `1142`, `1160`).
- A unit that came in running with a `p_init` ramps from it into the first
  snapshot (`constraints.py:1097-1100`, `1108-1110`). Where `p_init` has no
  value, the unit carries no ramp row at the first snapshot.
- A unit that is not committable carries ramp rows with its status fixed at
  `1` (`constraints.py:1079-1085`). The assumption
  `Generator_came_in_running_unless_committable` refuses such a unit that came
  in off.
- Each generator and load term enters the bus balance with its component's
  `sign` (`constraints.py:1434-1435`, `:1544`).

The rung adds a relax bus with a tightened unit that has only start-up and
shut-down ramps, a committable unit whose ramp limit lifts at the third
snapshot, a dear committable unit that came in running at `p_init=40`, a fixed
unit with ramp limits, a unit of sign `-1`, a load of sign `1` and a dear
backup. Each binds: PyPSA solves to `12862.5`. With the missing limits read as
`0` in the two partly rows, it solves to `14085.64`. With the ramp limit at
`0.25` in every snapshot, it solves to `14554.75`. Without the `p_init`, it
solves to `8437.5`. Without the fixed unit's ramp limits, it solves to
`12800.0`. With the unit's sign at `1`, it solves to `12592.5`. With the load's
sign at `-1`, it solves to `13887.5`.

| PyPSA | status | note |
| --- | --- | --- |
| [`Generator-com-p-before`](#generator-com-p-before), [`-current`](#generator-com-p-current), [`-partly-start-up`](#generator-com-partly-start-up), [`-partly-shut-down`](#generator-com-partly-shut-down) with a missing ramp limit | done | the four rates read a missing limit as `1` |
| [`Generator-p-ramp_limit_up`](pypsa.md#generator-p-ramp_limit_up), [`-down`](pypsa.md#generator-p-ramp_limit_down) per snapshot | done | `Generator_ramp_limit_up` and `-down` over `[scenario, snapshot, generator]` |
| [`Generator-p-ramp_limit_up`](pypsa.md#generator-p-ramp_limit_up), [`-down`](pypsa.md#generator-p-ramp_limit_down) at the first snapshot from `p_init` | done | `Generator_previous_p` opens at `Generator_status_initial * Generator_p_init` |
| [`Generator-p-ramp_limit_up`](pypsa.md#generator-p-ramp_limit_up), [`-down`](pypsa.md#generator-p-ramp_limit_down) for a unit that is not committable | done | `Generator_ramp_up_allowance` and `-down` read the status as `1` |
| [`Bus-nodal_balance`](pypsa.md#bus-nodal_balance) with `sign` | done | `Generator_sign` and `Load_sign` |

<!-- reference:rung_47_linearized_ramps:begin -->
> ✔ `pypsa 1.3.0.post1.dev23+g02bdcbbaf` solves this rung's network at objective `12862.5`, 179 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_47_linearized_ramps.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 47: the relaxed file's ramps and signs — tightening at the full build, a ramp limit per snapshot, a `p_init`, a unit that is not committable, and a sign."""

from __future__ import annotations

import math

import spine

PATCH = 'variants/pypsa_linearized_uc.yaml'
OPTIMIZE = {'linearized_unit_commitment': True}


def build():
    """The spine plus a relax bus: five units that each carry one of the rows under review, a feeding load and a dear backup."""
    n = spine.build()
    n.add('Bus', 'relax')
    n.add(
        'Generator',
        'tight47',
        bus='relax',
        committable=True,
        p_nom=50,
        p_min_pu=0.2,
        marginal_cost=2,
        up_time_before=0,
        ramp_limit_start_up=0.5,
        ramp_limit_shut_down=0.5,
        start_up_cost=10,
        shut_down_cost=10,
    )
    n.add(
        'Generator',
        'steep47',
        bus='relax',
        committable=True,
        p_nom=40,
        marginal_cost=3,
        start_up_cost=1,
        ramp_limit_up=[0.25, 0.25, math.nan, 0.25],
        ramp_limit_down=[0.25, 0.25, 0.25, math.nan],
        ramp_limit_start_up=0.25,
    )
    n.add(
        'Generator',
        'warm47',
        bus='relax',
        committable=True,
        p_nom=40,
        marginal_cost=50,
        start_up_cost=1,
        p_init=40,
        ramp_limit_down=0.25,
        ramp_limit_shut_down=0.5,
    )
    n.add('Generator', 'fixed47', bus='relax', p_nom=60, marginal_cost=1, ramp_limit_up=0.25, ramp_limit_down=0.25)
    n.add('Generator', 'sink47', bus='relax', p_nom=20, p_min_pu=0.5, sign=-1)
    n.add('Generator', 'backup47', bus='relax', p_nom=300, marginal_cost=500)
    n.add('Load', 'feed47', bus='relax', p_set=10, sign=1)
    n.add('Load', 'swing47', bus='relax', p_set=[60, 60, 140, 40])
    return n
```

</details>
<!-- reference:rung_47_linearized_ramps:end -->

## Rung 67 — a committable link and process, relaxed

The keyword relaxes Link and Process as it relaxes Generator
(`optimize.py:806-810`), and builds the four tightening rows for each
(`constraints.py:656-733`). The rung adds an east bus that three committable
units serve from the north: a link and a process, each with a fixed build and
the same start and stop cost, and an extendable link. PyPSA does not tighten
the extendable link, since the rows read the build as data
(`constraints.py:652-654`). A dear backup on the east bus keeps the bus
balanced.

Each tightening binds: PyPSA solves to `47777.33`. With the link's stop
`1e-7` dearer than its start, so PyPSA does not tighten it, it solves to
`46554.0`. With the process untightened in the same way, it solves to
`47465.70`. Without the keyword, it solves to `54013.13`.

| PyPSA | status | note |
| --- | --- | --- |
| [`Link-status`](#link-status), [`-start_up`](#link-start_up), [`-shut_down`](#link-shut_down) | done | shares in [0, 1] |
| [`Process-status`](#process-status), [`-start_up`](#process-start_up), [`-shut_down`](#process-shut_down) | done | shares in [0, 1] |
| [`Link-com-p-before`](#link-com-p-before), [`-current`](#link-com-p-current), [`-partly-start-up`](#link-com-partly-start-up), [`-partly-shut-down`](#link-com-partly-shut-down) | done | a fixed build only |
| [`Process-com-p-before`](#process-com-p-before), [`-current`](#process-com-p-current), [`-partly-start-up`](#process-com-partly-start-up), [`-partly-shut-down`](#process-com-partly-shut-down) | done | a fixed build only |
| [`Link-com-ext-p-*`](pypsa.md#link-com-ext-p-upper-cap) under the keyword | done | no tightening for an extendable build |

<!-- reference:rung_67_linearized_link_process:begin -->
> ✔ `pypsa 1.3.0.post1.dev23+g02bdcbbaf` solves this rung's network at objective `47777.33333333333`, 184 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_67_linearized_link_process.py`

```python
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
```

</details>
<!-- reference:rung_67_linearized_link_process:end -->

## The file

<!-- gallery:begin -->
`n.optimize(linearized_unit_commitment=True)`, as a patch over `examples/pypsa.yaml`. The status, its starts and its stops of a committable generator, link and process are shares in [0, 1] rather than integers, and four rows PyPSA adds only under the keyword tighten the relaxation of a unit with a fixed build whose start and stop cost the same in every snapshot (`constraints.py:633-733`). A modular committable unit is refused, as PyPSA refuses it. Every other row is the integer run's.

### `Generator-status`

`Generator_status`

```yaml
Generator_status:
  description: >-
    `Generator-status` — how much of a committable unit is on, a share in [0, 1]
    rather than an integer: the relaxation the keyword solves
    (`variables.py:86-87`)
  domain: null
  bounds:
    upper: 1
```

```math
0 \le u_{\xi,t,g} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

### `Generator-start_up`

`Generator_start_up`

```yaml
Generator_start_up:
  description: "`Generator-start_up` — how much of a committable unit turns on this snapshot, a share in [0, 1] (`variables.py:137-138`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{up}_{\xi,t,g} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

### `Generator-shut_down`

`Generator_shut_down`

```yaml
Generator_shut_down:
  description: "`Generator-shut_down` — how much of a committable unit turns off this snapshot, a share in [0, 1] (`variables.py:188-189`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{dn}_{\xi,t,g} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

### `Link-status`

`Link_status`

```yaml
Link_status:
  description: >-
    `Link-status` — how much of a committable link is on, a share in [0, 1]
    rather than an integer: the relaxation the keyword solves
    (`variables.py:86-87`)
  domain: null
  bounds:
    upper: 1
```

```math
0 \le u^{f}_{\xi,t,l} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

### `Link-start_up`

`Link_start_up`

```yaml
Link_start_up:
  description: "`Link-start_up` — how much of a committable link turns on this snapshot, a share in [0, 1] (`variables.py:137-138`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{up}^{f}_{\xi,t,l} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

### `Link-shut_down`

`Link_shut_down`

```yaml
Link_shut_down:
  description: "`Link-shut_down` — how much of a committable link turns off this snapshot, a share in [0, 1] (`variables.py:188-189`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{dn}^{f}_{\xi,t,l} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

### `Process-status`

`Process_status`

```yaml
Process_status:
  description: >-
    `Process-status` — how much of a committable process is on, a share in [0, 1]
    rather than an integer: the relaxation the keyword solves
    (`variables.py:86-87`)
  domain: null
  bounds:
    upper: 1
```

```math
0 \le u^{z}_{\xi,t,j} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

### `Process-start_up`

`Process_start_up`

```yaml
Process_start_up:
  description: "`Process-start_up` — how much of a committable process turns on this snapshot, a share in [0, 1] (`variables.py:137-138`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{up}^{z}_{\xi,t,j} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

### `Process-shut_down`

`Process_shut_down`

```yaml
Process_shut_down:
  description: "`Process-shut_down` — how much of a committable process turns off this snapshot, a share in [0, 1] (`variables.py:188-189`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{dn}^{z}_{\xi,t,j} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

### `Generator-com-p-before`

`Generator_com_p_before`

```yaml
Generator_com_p_before:
  description: >-
    `Generator-com-p-before` — the output a unit had entering this snapshot fits
    the share of it still on, less the share it is shutting down at the
    shut-down ramp (`constraints.py:669-684`). The translated terms vacate
    the first snapshot, as PyPSA's `sns[1:]` does
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) == 0 AND Generator_active
  expression: >-
    shift(Generator_p, along=snapshot, offset=1)
    - Generator_shut_down_rate * Generator_p_nom * shift(Generator_status, along=snapshot, offset=1)
    - (Generator_p_max_pu * Generator_p_nom - Generator_shut_down_rate * Generator_p_nom)
    * (Generator_status - Generator_start_up) <= 0
```

```math
p_{\xi,t - 1,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t - 1,g} - \left( \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \left( u_{\xi,t,g} - \mathit{up}_{\xi,t,g} \right) \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi,t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi,t',g} \} \rvert = 0 \wedge \mathrm{on}_{t,g}
```

### `Generator-com-p-current`

`Generator_com_p_current`

```yaml
Generator_com_p_current:
  description: >-
    `Generator-com-p-current` — output fits the share on, and the share starting
    up only up to the start-up ramp (`constraints.py:686-699`)
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) == 0 AND position(snapshot) > 0 AND Generator_active
  expression: >-
    Generator_p - Generator_p_max_pu * Generator_p_nom * Generator_status
    + (Generator_p_max_pu * Generator_p_nom - Generator_start_up_rate * Generator_p_nom) * Generator_start_up <= 0
```

```math
p_{\xi,t,g} - \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t,g} + \left( \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \mathit{up}_{\xi,t,g} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi,t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi,t',g} \} \rvert = 0 \wedge \mathrm{pos}(t) > 0 \wedge \mathrm{on}_{t,g}
```

### `Generator-com-partly-start-up`

`Generator_com_partly_start_up`

```yaml
Generator_com_partly_start_up:
  description: >-
    `Generator-com-partly-start-up` — raising output while a share is starting up
    is bounded by the ramp of the share on and the start-up ramp of the
    share coming on (`constraints.py:701-716`)
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) == 0 AND Generator_active
  expression: >-
    Generator_p - shift(Generator_p, along=snapshot, offset=1)
    - (Generator_p_min_pu * Generator_p_nom + Generator_ramp_up_rate * Generator_p_nom) * Generator_status
    + Generator_p_min_pu * Generator_p_nom * shift(Generator_status, along=snapshot, offset=1)
    + (Generator_p_min_pu * Generator_p_nom + Generator_ramp_up_rate * Generator_p_nom - Generator_start_up_rate * Generator_p_nom)
    * Generator_start_up <= 0
```

```math
p_{\xi,t,g} - p_{\xi,t - 1,g} - \left( \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} + \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot u_{\xi,t,g} + \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t - 1,g} + \left( \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} + \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \mathit{up}_{\xi,t,g} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi,t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi,t',g} \} \rvert = 0 \wedge \mathrm{on}_{t,g}
```

### `Generator-com-partly-shut-down`

`Generator_com_partly_shut_down`

```yaml
Generator_com_partly_shut_down:
  description: >-
    `Generator-com-partly-shut-down` — lowering output while a share is shutting
    down is bounded likewise, by the shut-down ramp (`constraints.py:718-733`)
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) == 0 AND Generator_active
  expression: >-
    shift(Generator_p, along=snapshot, offset=1) - Generator_p
    - Generator_shut_down_rate * Generator_p_nom * shift(Generator_status, along=snapshot, offset=1)
    + (Generator_shut_down_rate * Generator_p_nom - Generator_ramp_down_rate * Generator_p_nom) * Generator_status
    - (Generator_p_min_pu * Generator_p_nom + Generator_ramp_down_rate * Generator_p_nom - Generator_shut_down_rate * Generator_p_nom)
    * Generator_start_up <= 0
```

```math
p_{\xi,t - 1,g} - p_{\xi,t,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t - 1,g} + \left( \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot u_{\xi,t,g} - \left( \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} + \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \mathit{up}_{\xi,t,g} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi,t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi,t',g} \} \rvert = 0 \wedge \mathrm{on}_{t,g}
```

### `Link-com-p-before`

`Link_com_p_before`

```yaml
Link_com_p_before:
  description: >-
    `Link-com-p-before` — the output a link had entering this snapshot fits
    the share of it still on, less the share it is shutting down at the
    shut-down ramp (`constraints.py:669-684`). The translated terms vacate
    the first snapshot, as PyPSA's `sns[1:]` does
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) == 0 AND Link_active
  expression: >-
    shift(Link_p, along=snapshot, offset=1)
    - Link_shut_down_rate * Link_p_nom * shift(Link_status, along=snapshot, offset=1)
    - (Link_p_max_pu * Link_p_nom - Link_shut_down_rate * Link_p_nom)
    * (Link_status - Link_start_up) <= 0
```

```math
f_{\xi,t - 1,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t - 1,l} - \left( \overline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \left( u^{f}_{\xi,t,l} - \mathit{up}^{f}_{\xi,t,l} \right) \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi,t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi,t',l} \} \rvert = 0 \wedge \mathrm{on}^{f}_{t,l}
```

### `Link-com-p-current`

`Link_com_p_current`

```yaml
Link_com_p_current:
  description: >-
    `Link-com-p-current` — output fits the share on, and the share starting
    up only up to the start-up ramp (`constraints.py:686-699`)
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) == 0 AND position(snapshot) > 0 AND Link_active
  expression: >-
    Link_p - Link_p_max_pu * Link_p_nom * Link_status
    + (Link_p_max_pu * Link_p_nom - Link_start_up_rate * Link_p_nom) * Link_start_up <= 0
```

```math
f_{\xi,t,l} - \overline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t,l} + \left( \overline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \mathit{up}^{f}_{\xi,t,l} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi,t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi,t',l} \} \rvert = 0 \wedge \mathrm{pos}(t) > 0 \wedge \mathrm{on}^{f}_{t,l}
```

### `Link-com-partly-start-up`

`Link_com_partly_start_up`

```yaml
Link_com_partly_start_up:
  description: >-
    `Link-com-partly-start-up` — raising output while a share is starting up
    is bounded by the ramp of the share on and the start-up ramp of the
    share coming on (`constraints.py:701-716`)
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) == 0 AND Link_active
  expression: >-
    Link_p - shift(Link_p, along=snapshot, offset=1)
    - (Link_p_min_pu * Link_p_nom + Link_ramp_up_rate * Link_p_nom) * Link_status
    + Link_p_min_pu * Link_p_nom * shift(Link_status, along=snapshot, offset=1)
    + (Link_p_min_pu * Link_p_nom + Link_ramp_up_rate * Link_p_nom - Link_start_up_rate * Link_p_nom)
    * Link_start_up <= 0
```

```math
f_{\xi,t,l} - f_{\xi,t - 1,l} - \left( \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} + \widetilde{\mathrm{ru}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot u^{f}_{\xi,t,l} + \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t - 1,l} + \left( \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} + \widetilde{\mathrm{ru}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \mathit{up}^{f}_{\xi,t,l} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi,t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi,t',l} \} \rvert = 0 \wedge \mathrm{on}^{f}_{t,l}
```

### `Link-com-partly-shut-down`

`Link_com_partly_shut_down`

```yaml
Link_com_partly_shut_down:
  description: >-
    `Link-com-partly-shut-down` — lowering output while a share is shutting
    down is bounded likewise, by the shut-down ramp (`constraints.py:718-733`)
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) == 0 AND Link_active
  expression: >-
    shift(Link_p, along=snapshot, offset=1) - Link_p
    - Link_shut_down_rate * Link_p_nom * shift(Link_status, along=snapshot, offset=1)
    + (Link_shut_down_rate * Link_p_nom - Link_ramp_down_rate * Link_p_nom) * Link_status
    - (Link_p_min_pu * Link_p_nom + Link_ramp_down_rate * Link_p_nom - Link_shut_down_rate * Link_p_nom)
    * Link_start_up <= 0
```

```math
f_{\xi,t - 1,l} - f_{\xi,t,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t - 1,l} + \left( \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{rd}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot u^{f}_{\xi,t,l} - \left( \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} + \widetilde{\mathrm{rd}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \mathit{up}^{f}_{\xi,t,l} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi,t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi,t',l} \} \rvert = 0 \wedge \mathrm{on}^{f}_{t,l}
```

### `Process-com-p-before`

`Process_com_p_before`

```yaml
Process_com_p_before:
  description: >-
    `Process-com-p-before` — the output a process had entering this snapshot fits
    the share of it still on, less the share it is shutting down at the
    shut-down ramp (`constraints.py:669-684`). The translated terms vacate
    the first snapshot, as PyPSA's `sns[1:]` does
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) == 0 AND Process_active
  expression: >-
    shift(Process_p, along=snapshot, offset=1)
    - Process_shut_down_rate * Process_p_nom * shift(Process_status, along=snapshot, offset=1)
    - (Process_p_max_pu * Process_p_nom - Process_shut_down_rate * Process_p_nom)
    * (Process_status - Process_start_up) <= 0
```

```math
z_{\xi,t - 1,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t - 1,j} - \left( \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \left( u^{z}_{\xi,t,j} - \mathit{up}^{z}_{\xi,t,j} \right) \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi,t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi,t',j} \} \rvert = 0 \wedge \mathrm{on}^{z}_{t,j}
```

### `Process-com-p-current`

`Process_com_p_current`

```yaml
Process_com_p_current:
  description: >-
    `Process-com-p-current` — output fits the share on, and the share starting
    up only up to the start-up ramp (`constraints.py:686-699`)
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) == 0 AND position(snapshot) > 0 AND Process_active
  expression: >-
    Process_p - Process_p_max_pu * Process_p_nom * Process_status
    + (Process_p_max_pu * Process_p_nom - Process_start_up_rate * Process_p_nom) * Process_start_up <= 0
```

```math
z_{\xi,t,j} - \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t,j} + \left( \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \mathit{up}^{z}_{\xi,t,j} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi,t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi,t',j} \} \rvert = 0 \wedge \mathrm{pos}(t) > 0 \wedge \mathrm{on}^{z}_{t,j}
```

### `Process-com-partly-start-up`

`Process_com_partly_start_up`

```yaml
Process_com_partly_start_up:
  description: >-
    `Process-com-partly-start-up` — raising output while a share is starting up
    is bounded by the ramp of the share on and the start-up ramp of the
    share coming on (`constraints.py:701-716`)
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) == 0 AND Process_active
  expression: >-
    Process_p - shift(Process_p, along=snapshot, offset=1)
    - (Process_p_min_pu * Process_p_nom + Process_ramp_up_rate * Process_p_nom) * Process_status
    + Process_p_min_pu * Process_p_nom * shift(Process_status, along=snapshot, offset=1)
    + (Process_p_min_pu * Process_p_nom + Process_ramp_up_rate * Process_p_nom - Process_start_up_rate * Process_p_nom)
    * Process_start_up <= 0
```

```math
z_{\xi,t,j} - z_{\xi,t - 1,j} - \left( \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} + \widetilde{\mathrm{ru}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot u^{z}_{\xi,t,j} + \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t - 1,j} + \left( \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} + \widetilde{\mathrm{ru}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \mathit{up}^{z}_{\xi,t,j} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi,t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi,t',j} \} \rvert = 0 \wedge \mathrm{on}^{z}_{t,j}
```

### `Process-com-partly-shut-down`

`Process_com_partly_shut_down`

```yaml
Process_com_partly_shut_down:
  description: >-
    `Process-com-partly-shut-down` — lowering output while a share is shutting
    down is bounded likewise, by the shut-down ramp (`constraints.py:718-733`)
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) == 0 AND Process_active
  expression: >-
    shift(Process_p, along=snapshot, offset=1) - Process_p
    - Process_shut_down_rate * Process_p_nom * shift(Process_status, along=snapshot, offset=1)
    + (Process_shut_down_rate * Process_p_nom - Process_ramp_down_rate * Process_p_nom) * Process_status
    - (Process_p_min_pu * Process_p_nom + Process_ramp_down_rate * Process_p_nom - Process_shut_down_rate * Process_p_nom)
    * Process_start_up <= 0
```

```math
z_{\xi,t - 1,j} - z_{\xi,t,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t - 1,j} + \left( \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{rd}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot u^{z}_{\xi,t,j} - \left( \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} + \widetilde{\mathrm{rd}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \mathit{up}^{z}_{\xi,t,j} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi,t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi,t',j} \} \rvert = 0 \wedge \mathrm{on}^{z}_{t,j}
```

### `Generator_committable_is_not_modular`

`Generator_committable_is_not_modular`

```yaml
Generator_committable_is_not_modular:
  holds: "NOT (Generator_p_nom_mod > 0)"
  where: "Generator_committable AND count(Generator_active, over=snapshot) > 0"
  description: >-
    a modular committable unit counts its status in modules, which the
    relaxation cannot share out — PyPSA refuses it under the keyword
    (`optimize.py:772-773`, `consistency.py:1563-1604`)
```

```math
\neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}_{t,g} \} \rvert > 0
```

### `Link_committable_is_not_modular`

`Link_committable_is_not_modular`

```yaml
Link_committable_is_not_modular:
  holds: "NOT (Link_p_nom_mod > 0)"
  where: "Link_committable AND count(Link_active, over=snapshot) > 0"
  description: >-
    a modular committable unit counts its status in modules, which the
    relaxation cannot share out — PyPSA refuses it under the keyword
    (`optimize.py:772-773`, `consistency.py:1563-1604`)
```

```math
\neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{f}_{t,l} \} \rvert > 0
```

### `Process_committable_is_not_modular`

`Process_committable_is_not_modular`

```yaml
Process_committable_is_not_modular:
  holds: "NOT (Process_p_nom_mod > 0)"
  where: "Process_committable AND count(Process_active, over=snapshot) > 0"
  description: >-
    a modular committable unit counts its status in modules, which the
    relaxation cannot share out — PyPSA refuses it under the keyword
    (`optimize.py:772-773`, `consistency.py:1563-1604`)
```

```math
\neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{z}_{t,j} \} \rvert > 0
```
<!-- gallery:end -->

Regenerate with `pixi run python -m tools.gallery`.
