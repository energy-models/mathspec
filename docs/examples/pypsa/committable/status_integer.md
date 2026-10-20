<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Committable classes, the integer status

This file states the status, the starts and the stops of a committable `Generator`, `Link` and `Process` as integers, as a plain `n.optimize()` builds them. It is written once and each class takes it under its own names, as [the commitment](commitment.md) says. Each of those is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. The math below prints the generator's. A model with [the commitment](commitment.md) takes this file or [the relaxed status](status_relaxed.md), never both. It reads `Unit_committed`, which other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
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

variables:
  Unit_status:
    description: >-
      `-status` — how much of a committable unit is on: an integer
      the rows below cap at one, or at the module count where the build is
      modular
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    domain: integer
    bounds:
      lower: 0
  Unit_start_up:
    description: "`-start_up` — how much of a committable unit turns on this snapshot, capped as the status is"
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    domain: integer
    bounds:
      lower: 0
  Unit_shut_down:
    description: "`-shut_down` — how much of a committable unit turns off this snapshot, capped as the status is"
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    domain: integer
    bounds:
      lower: 0
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{\mathrm{com}}`$ | `Generator_committed` over $`\mathcal{T} \times \mathcal{G}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — the units of the class this layer is renamed for |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `-status` — how much of a committable unit is on: an integer the rows below cap at one, or at the module count where the build is modular |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `-start_up` — how much of a committable unit turns on this snapshot, capped as the status is |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `-shut_down` — how much of a committable unit turns off this snapshot, capped as the status is |

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
<!-- gallery:end -->
