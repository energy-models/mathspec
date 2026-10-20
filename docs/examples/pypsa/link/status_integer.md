<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Links, the integer status

This file states the status, the starts and the stops of a committable `Link` as integers, as a plain `n.optimize()` builds them. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. A model with [the commitment](commitment.md) takes this file or [the relaxed status](status_relaxed.md), never both. It reads `Link_committed`, which other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  masks:
    Link_committed: { dims: [snapshot, link] }

dimensions:
  scenario: {}
  snapshot: { dtype: datetime, ordered: true }
  link: {}

variables:
  Link_status:
    description: >-
      `Link-status` — how much of a committable link is on: an integer
      the rows below cap at one, or at the module count where the build is
      modular
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0
  Link_start_up:
    description: "`Link-start_up` — how much of a committable link turns on this snapshot, capped as the status is"
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0
  Link_shut_down:
    description: "`Link-shut_down` — how much of a committable link turns off this snapshot, capped as the status is"
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f,\mathrm{com}}`$ | `Link_committed` over $`\mathcal{T} \times \mathcal{L}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` |
| $`\mathcal{L}`$ | index $`l`$ — `link` |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u^{f}`$ | `Link_status` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — `Link-status` — how much of a committable link is on: an integer the rows below cap at one, or at the module count where the build is modular |
| $`\mathit{up}^{f}`$ | `Link_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — `Link-start_up` — how much of a committable link turns on this snapshot, capped as the status is |
| $`\mathit{dn}^{f}`$ | `Link_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — `Link-shut_down` — how much of a committable link turns off this snapshot, capped as the status is |

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
<!-- gallery:end -->
