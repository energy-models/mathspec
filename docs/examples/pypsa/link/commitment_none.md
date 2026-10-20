<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Links, no commitment

This file states that a model builds no unit commitment for `Link`. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml`. It declares the names that [the ramping](ramping.md) and [the maintenance](maintenance.md) read from [the commitment](commitment.md), and masks each of them empty. Its assumption refuses data in which a unit is committable, because such a unit would have no output limits. A model takes this file or the commitment, never both. It reads `Link_committed` and `Link_p_nom_extendable`, which other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Link_p_nom_extendable: { dims: [link], dtype: bool }
  masks:
    Link_committed: { dims: [snapshot, link] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  link:
    description: controllable connections, each from one bus to the buses it delivers to

parameters:
  Link_committable:
    description: whether a unit is committable; this model builds no unit commitment, so none is
    dims: [link]
    dtype: bool
    missing: neutral
  Link_status_initial:
    description: the status a unit carried into the horizon; none here, since no unit is committable
    dims: [scenario, link]
    dtype: int
    missing: neutral
  Link_big_m:
    description: the bound a committed extendable unit is released by; none here, since no unit is committable
    dims: [scenario, link]
    missing: neutral

variables:
  Link_status:
    description: how much of a committable unit is on; no column here, since no unit is committable
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0
  Link_start_up:
    description: how much of a committable unit turns on; no column here, since no unit is committable
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0
  Link_shut_down:
    description: how much of a committable unit turns off; no column here, since no unit is committable
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0

expressions:
  Link_previous_status:
    description: the status a unit carried into the snapshot; nothing here, since no unit is committable
    dims: [scenario, snapshot, link]
    expression: Link_status
  Link_status_available:
    description: how much of a committed unit is on and can run; nothing here, since no unit is committable
    dims: [scenario, snapshot, link]
    expression: Link_status

masks:
  Link_com_ext:
    description: a committable unit with an extendable build; none here, since no unit is committable
    where: Link_committed AND Link_p_nom_extendable

assumptions:
  Link_none_committable:
    holds: "NOT Link_committable"
    description: >-
      this model leaves the unit commitment of `Link` out, so a committable
      unit would have no output limits. Take `link/commitment.yaml` in place
      of `link/commitment_none.yaml`
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{ext}^{f}`$ | `Link_p_nom_extendable` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{on}^{f,\mathrm{com}}`$ | `Link_committed` over $`\mathcal{T} \times \mathcal{L}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{L}`$ | index $`l`$ — `link` — controllable connections, each from one bus to the buses it delivers to |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{com}^{f}`$ | `Link_committable` over $`\mathcal{L}`$, `neutral` where the data has no row — whether a unit is committable; this model builds no unit commitment, so none is |
| $`\mathrm{u}^{f,0}`$ | `Link_status_initial` over $`\Xi \times \mathcal{L}`$, `neutral` where the data has no row — the status a unit carried into the horizon; none here, since no unit is committable |
| $`\mathrm{M}^{f}`$ | `Link_big_m` over $`\Xi \times \mathcal{L}`$, `neutral` where the data has no row — the bound a committed extendable unit is released by; none here, since no unit is committable |

#### Masks

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f,\mathrm{com,ext}}`$ | `Link_com_ext` over $`\mathcal{T} \times \mathcal{L}`$ — a committable unit with an extendable build; none here, since no unit is committable |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u^{f}`$ | `Link_status` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — how much of a committable unit is on; no column here, since no unit is committable |
| $`\mathit{up}^{f}`$ | `Link_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — how much of a committable unit turns on; no column here, since no unit is committable |
| $`\mathit{dn}^{f}`$ | `Link_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — how much of a committable unit turns off; no column here, since no unit is committable |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{u}^{f}`$ | `Link_previous_status` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — the status a unit carried into the snapshot; nothing here, since no unit is committable |
| $`u^{f,\mathrm{av}}`$ | `Link_status_available` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — how much of a committed unit is on and can run; nothing here, since no unit is committable |

#### Masks

**`Link_com_ext`**

```math
\mathrm{on}^{f,\mathrm{com,ext}}_{t,l} \iff \mathrm{on}^{f,\mathrm{com}}_{t,l} \wedge \mathrm{ext}^{f}_{l} \qquad \forall\, t \in \mathcal{T},\ l \in \mathcal{L}
```

#### Variable domains

**`Link_status`**

```math
u^{f}_{\xi,t,l} \ge 0, u^{f}_{\xi,t,l} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

**`Link_start_up`**

```math
\mathit{up}^{f}_{\xi,t,l} \ge 0, \mathit{up}^{f}_{\xi,t,l} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

**`Link_shut_down`**

```math
\mathit{dn}^{f}_{\xi,t,l} \ge 0, \mathit{dn}^{f}_{\xi,t,l} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

#### Definitions

**`Link_previous_status`**

```math
\overleftarrow{u}^{f}_{\xi,t,l} = u^{f}_{\xi,t,l} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L}
```

**`Link_status_available`**

```math
u^{f,\mathrm{av}}_{\xi,t,l} = u^{f}_{\xi,t,l} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L}
```

#### Assumptions

**`Link_none_committable`**

```math
\neg \mathrm{com}^{f}_{l} \qquad \forall\, l \in \mathcal{L}
```
<!-- gallery:end -->
