<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Committable classes, no commitment

This file states that a model builds no unit commitment for `Generator`, `Link` and `Process`. It is written once and each class takes it under its own names, as [the commitment](commitment.md) says. Each of those is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. The math below prints the generator's. It declares the names that [the ramping](ramping.md) and [the maintenance](maintenance.md) read from [the commitment](commitment.md), and masks each of them empty. Its assumption refuses data in which a unit is committable, because such a unit would have no output limits. A model takes this file or the commitment, never both. It reads `Unit_committed` and `Unit_p_nom_extendable`, which other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Unit_p_nom_extendable: { dims: [unit], dtype: bool }
  masks:
    Unit_committed: { dims: [snapshot, unit] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  unit:
    description: the units of the class this layer is renamed for

parameters:
  Unit_committable:
    description: whether a unit is committable; this model builds no unit commitment, so none is
    dims: [unit]
    dtype: bool
    missing: neutral
  Unit_status_initial:
    description: the status a unit carried into the horizon; none here, since no unit is committable
    dims: [scenario, unit]
    dtype: int
    missing: neutral
  Unit_big_m:
    description: the bound a committed extendable unit is released by; none here, since no unit is committable
    dims: [scenario, unit]
    missing: neutral

variables:
  Unit_status:
    description: how much of a committable unit is on; no column here, since no unit is committable
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    domain: integer
    bounds:
      lower: 0
  Unit_start_up:
    description: how much of a committable unit turns on; no column here, since no unit is committable
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    domain: integer
    bounds:
      lower: 0
  Unit_shut_down:
    description: how much of a committable unit turns off; no column here, since no unit is committable
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    domain: integer
    bounds:
      lower: 0

expressions:
  Unit_previous_status:
    description: the status a unit carried into the snapshot; nothing here, since no unit is committable
    dims: [scenario, snapshot, unit]
    expression: Unit_status
  Unit_status_available:
    description: how much of a committed unit is on and can run; nothing here, since no unit is committable
    dims: [scenario, snapshot, unit]
    expression: Unit_status

masks:
  Unit_com_ext:
    description: a committable unit with an extendable build; none here, since no unit is committable
    where: Unit_committed AND Unit_p_nom_extendable

assumptions:
  Unit_none_committable:
    holds: "NOT Unit_committable"
    description: >-
      this model leaves the unit commitment of this class out, so a committable
      unit would have no output limits. Take `committable/commitment.yaml` in place
      of `committable/commitment_none.yaml`
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{ext}`$ | `Generator_p_nom_extendable` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{on}^{\mathrm{com}}`$ | `Generator_committed` over $`\mathcal{T} \times \mathcal{G}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — the units of the class this layer is renamed for |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{com}`$ | `Generator_committable` over $`\mathcal{G}`$, `neutral` where the data has no row — whether a unit is committable; this model builds no unit commitment, so none is |
| $`\mathrm{u}^{0}`$ | `Generator_status_initial` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — the status a unit carried into the horizon; none here, since no unit is committable |
| $`\mathrm{M}`$ | `Generator_big_m` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — the bound a committed extendable unit is released by; none here, since no unit is committable |

#### Masks

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{\mathrm{com,ext}}`$ | `Generator_com_ext` over $`\mathcal{T} \times \mathcal{G}`$ — a committable unit with an extendable build; none here, since no unit is committable |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how much of a committable unit is on; no column here, since no unit is committable |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how much of a committable unit turns on; no column here, since no unit is committable |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how much of a committable unit turns off; no column here, since no unit is committable |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{u}`$ | `Generator_previous_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the status a unit carried into the snapshot; nothing here, since no unit is committable |
| $`u^{\mathrm{av}}`$ | `Generator_status_available` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how much of a committed unit is on and can run; nothing here, since no unit is committable |

#### Masks

**`Generator_com_ext`**

```math
\mathrm{on}^{\mathrm{com,ext}}_{t,g} \iff \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{ext}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Variable domains

**`Generator_status`**

```math
u_{\xi,t,g} \ge 0, u_{\xi,t,g} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_start_up`**

```math
\mathit{up}_{\xi,t,g} \ge 0, \mathit{up}_{\xi,t,g} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_shut_down`**

```math
\mathit{dn}_{\xi,t,g} \ge 0, \mathit{dn}_{\xi,t,g} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

#### Definitions

**`Generator_previous_status`**

```math
\overleftarrow{u}_{\xi,t,g} = u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_status_available`**

```math
u^{\mathrm{av}}_{\xi,t,g} = u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Assumptions

**`Generator_none_committable`**

```math
\neg \mathrm{com}_{g} \qquad \forall\, g \in \mathcal{G}
```
<!-- gallery:end -->
