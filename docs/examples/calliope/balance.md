<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# The balance

One of the base fragments of [Calliope in fragments](index.md). Calliope's `system_balance`: at each node, in each time step, a carrier's production equals its consumption. The file declares the sum `carrier_flow` empty, and every file that moves a carrier adds its term.

<!-- gallery:begin -->
```yaml
dimensions:
  nodes:
    description: Calliope's `nodes` — the places technologies stand at
  techs:
    description: Calliope's `techs` — technologies
  carriers:
    description: Calliope's `carriers` — energy and commodity carriers
  timesteps:
    description: Calliope's `timesteps` — time steps, in order
    dtype: datetime

given:
  parameters:
    carrier_in:
      description: whether a technology consumes a carrier at a node
      dims: [nodes, techs, carriers]
      dtype: bool
    carrier_out:
      description: whether a technology produces a carrier at a node
      dims: [nodes, techs, carriers]
      dtype: bool

expressions:
  carrier_flow:
    description: >-
      what every technology and every other file puts into a node's carrier,
      less what it takes out
    dims: [nodes, carriers, timesteps]
    empty: true

constraints:
  system_balance:
    description: >-
      `system_balance` — at every node, in every time step, a carrier's
      production equals its consumption. Built where a technology at the
      node produces or consumes the carrier
    dims: [nodes, carriers, timesteps]
    where: count(carrier_in, over=techs) >= 1 OR count(carrier_out, over=techs) >= 1
    expression: carrier_flow == 0
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{carrier\_in}`$ | `carrier_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares — whether a technology consumes a carrier at a node |
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares — whether a technology produces a carrier at a node |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{carrier\_flow}`$ | `carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ — what every technology and every other file puts into a node's carrier, less what it takes out |

#### Subject to

**`system_balance`**

```math
\mathit{carrier\_flow}_{n,c,t} = 0 \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \lvert \{ i \in \mathcal{I} \,:\, \mathrm{carrier\_in}_{n,i,c} \} \rvert \ge 1 \vee \lvert \{ i \in \mathcal{I} \,:\, \mathrm{carrier\_out}_{n,i,c} \} \rvert \ge 1
```

#### Definitions

**`carrier_flow`**

```math
\mathit{carrier\_flow}_{n,c,t} = \cdots \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T}
```
<!-- gallery:end -->
