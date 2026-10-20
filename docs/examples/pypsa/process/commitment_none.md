<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Processes, no commitment

This file states that a model builds no unit commitment for `Process`. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. It declares the names that [the ramping](ramping.md) and [the maintenance](maintenance.md) read from [the commitment](commitment.md), and masks each of them empty. Its assumption refuses data in which a unit is committable, because such a unit would have no output limits. A model takes this file or the commitment, never both. It reads `Process_committed` and `Process_p_nom_extendable`, which other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Process_p_nom_extendable: { dims: [process], dtype: bool }
  masks:
    Process_committed: { dims: [snapshot, process] }

dimensions:
  scenario: {}
  snapshot: { dtype: datetime, ordered: true }
  process: {}

parameters:
  Process_committable:
    description: whether a unit is committable; this model builds no unit commitment, so none is
    dims: [process]
    dtype: bool
    missing: neutral
  Process_status_initial:
    description: the status a unit carried into the horizon; none here, since no unit is committable
    dims: [scenario, process]
    dtype: int
    missing: neutral
  Process_big_m:
    description: the bound a committed extendable unit is released by; none here, since no unit is committable
    dims: [scenario, process]
    missing: neutral

variables:
  Process_status:
    description: how much of a committable unit is on; no column here, since no unit is committable
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
  Process_start_up:
    description: how much of a committable unit turns on; no column here, since no unit is committable
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
  Process_shut_down:
    description: how much of a committable unit turns off; no column here, since no unit is committable
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0

expressions:
  Process_previous_status:
    description: the status a unit carried into the snapshot; nothing here, since no unit is committable
    dims: [scenario, snapshot, process]
    expression: Process_status
  Process_status_available:
    description: how much of a committed unit is on and can run; nothing here, since no unit is committable
    dims: [scenario, snapshot, process]
    expression: Process_status

masks:
  Process_com_ext:
    description: a committable unit with an extendable build; none here, since no unit is committable
    where: Process_committed AND Process_p_nom_extendable

assumptions:
  Process_none_committable:
    holds: "NOT Process_committable"
    description: >-
      this model leaves the unit commitment of `Process` out, so a committable
      unit would have no output limits. Take `process/commitment.yaml` in place
      of `process/commitment_none.yaml`
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{ext}^{z}`$ | `Process_p_nom_extendable` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{on}^{z,\mathrm{com}}`$ | `Process_committed` over $`\mathcal{T} \times \mathcal{J}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` |
| $`\mathcal{J}`$ | index $`j`$ — `process` |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{com}^{z}`$ | `Process_committable` over $`\mathcal{J}`$, `neutral` where the data has no row — whether a unit is committable; this model builds no unit commitment, so none is |
| $`\mathrm{u}^{z,0}`$ | `Process_status_initial` over $`\Xi \times \mathcal{J}`$, `neutral` where the data has no row — the status a unit carried into the horizon; none here, since no unit is committable |
| $`\mathrm{M}^{z}`$ | `Process_big_m` over $`\Xi \times \mathcal{J}`$, `neutral` where the data has no row — the bound a committed extendable unit is released by; none here, since no unit is committable |

#### Masks

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z,\mathrm{com,ext}}`$ | `Process_com_ext` over $`\mathcal{T} \times \mathcal{J}`$ — a committable unit with an extendable build; none here, since no unit is committable |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u^{z}`$ | `Process_status` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — how much of a committable unit is on; no column here, since no unit is committable |
| $`\mathit{up}^{z}`$ | `Process_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — how much of a committable unit turns on; no column here, since no unit is committable |
| $`\mathit{dn}^{z}`$ | `Process_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — how much of a committable unit turns off; no column here, since no unit is committable |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{u}^{z}`$ | `Process_previous_status` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — the status a unit carried into the snapshot; nothing here, since no unit is committable |
| $`u^{z,\mathrm{av}}`$ | `Process_status_available` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — how much of a committed unit is on and can run; nothing here, since no unit is committable |

#### Masks

**`Process_com_ext`**

```math
\mathrm{on}^{z,\mathrm{com,ext}}_{t,j} \iff \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{ext}^{z}_{j} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
```

#### Variable domains

**`Process_status`**

```math
u^{z}_{\xi,t,j} \ge 0, u^{z}_{\xi,t,j} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_start_up`**

```math
\mathit{up}^{z}_{\xi,t,j} \ge 0, \mathit{up}^{z}_{\xi,t,j} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_shut_down`**

```math
\mathit{dn}^{z}_{\xi,t,j} \ge 0, \mathit{dn}^{z}_{\xi,t,j} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

#### Definitions

**`Process_previous_status`**

```math
\overleftarrow{u}^{z}_{\xi,t,j} = u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_status_available`**

```math
u^{z,\mathrm{av}}_{\xi,t,j} = u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

#### Assumptions

**`Process_none_committable`**

```math
\neg \mathrm{com}^{z}_{j} \qquad \forall\, j \in \mathcal{J}
```
<!-- gallery:end -->
