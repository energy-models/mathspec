<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Generators, the integer status

This file states the status, the starts and the stops of a committable `Generator` as integers, as a plain `n.optimize()` builds them. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. A model with [the commitment](commitment.md) takes this file or [the relaxed status](status_relaxed.md), never both. It reads `Generator_committed`, which other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  masks:
    Generator_committed: { dims: [snapshot, generator] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  generator:
    description: generating units, each on one bus

variables:
  Generator_status:
    description: >-
      `Generator-status` — how much of a committable unit is on: an integer
      the rows below cap at one, or at the module count where the build is
      modular
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    domain: integer
    bounds:
      lower: 0
  Generator_start_up:
    description: "`Generator-start_up` — how much of a committable unit turns on this snapshot, capped as the status is"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    domain: integer
    bounds:
      lower: 0
  Generator_shut_down:
    description: "`Generator-shut_down` — how much of a committable unit turns off this snapshot, capped as the status is"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
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
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units, each on one bus |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-status` — how much of a committable unit is on: an integer the rows below cap at one, or at the module count where the build is modular |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-start_up` — how much of a committable unit turns on this snapshot, capped as the status is |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-shut_down` — how much of a committable unit turns off this snapshot, capped as the status is |

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
