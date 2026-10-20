<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Processes, the integer status

This file states the status, the starts and the stops of a committable `Process` as integers, as a plain `n.optimize()` builds them. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. A model with [the commitment](commitment.md) takes this file or [the relaxed status](status_relaxed.md), never both. It reads `Process_committed`, which other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  masks:
    Process_committed: { dims: [snapshot, process] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  process:
    description: generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate

variables:
  Process_status:
    description: >-
      `Process-status` — how much of a committable process is on: an integer
      the rows below cap at one, or at the module count where the build is
      modular
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
  Process_start_up:
    description: "`Process-start_up` — how much of a committable process turns on this snapshot, capped as the status is"
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
  Process_shut_down:
    description: "`Process-shut_down` — how much of a committable process turns off this snapshot, capped as the status is"
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z,\mathrm{com}}`$ | `Process_committed` over $`\mathcal{T} \times \mathcal{J}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{J}`$ | index $`j`$ — `process` — generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u^{z}`$ | `Process_status` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-status` — how much of a committable process is on: an integer the rows below cap at one, or at the module count where the build is modular |
| $`\mathit{up}^{z}`$ | `Process_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-start_up` — how much of a committable process turns on this snapshot, capped as the status is |
| $`\mathit{dn}^{z}`$ | `Process_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-shut_down` — how much of a committable process turns off this snapshot, capped as the status is |

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
<!-- gallery:end -->
