<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Feasibility

One of the base fragments of [Calliope in fragments](index.md). Unmet demand and unused supply at a high price, so a model that cannot balance still solves. Calliope builds them under `config.ensure_feasibility`; here the switch is whether this file is composed.

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

variables:
  unmet_demand:
    description: >-
      `unmet_demand` — a source of any carrier at any node, at a high price,
      so a model that cannot meet its demand still solves. Calliope builds
      it under `config.ensure_feasibility`; here it is this file
    dims: [nodes, carriers, timesteps]
    where: count(carrier_in, over=techs) >= 1 OR count(carrier_out, over=techs) >= 1
    bounds: { lower: 0 }
    absence: zero
  unused_supply:
    description: "`unused_supply` — a sink of any carrier at any node, at a high price, the counterpart of `unmet_demand`"
    dims: [nodes, carriers, timesteps]
    where: count(carrier_in, over=techs) >= 1 OR count(carrier_out, over=techs) >= 1
    bounds: { upper: 0 }
    absence: zero

expressions:
  feasibility_carrier_flow: unmet_demand + unused_supply
  unmet_demand_penalty:
    description: "`$unmet_demand` of `min_cost_optimisation` — what unmet demand and unused supply cost"
    expression: sum(sum(unmet_demand - unused_supply, over=[carriers, nodes]) * timestep_weights) * bigM
  unmet_sum:
    description: "`unmet_sum` — net unmet demand; reported"
    expression: unmet_demand + unused_supply

given:
  parameters:
    carrier_in: { dims: [nodes, techs, carriers], dtype: bool }
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
    timestep_weights: { dims: [timesteps] }
    bigM: { dims: [] }
  expressions:
    carrier_flow: { dims: [nodes, carriers, timesteps], term: feasibility_carrier_flow }
    penalty: { dims: [], term: unmet_demand_penalty }
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{unmet\_demand}`$ | `unmet_demand` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ — `unmet_demand` — a source of any carrier at any node, at a high price, so a model that cannot meet its demand still solves. Calliope builds it under `config.ensure_feasibility`; here it is this file |
| $`\mathit{unused\_supply}`$ | `unused_supply` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ — `unused_supply` — a sink of any carrier at any node, at a high price, the counterpart of `unmet_demand` |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{carrier\_in}`$ | `carrier_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{bigM}`$ | `bigM` (scalar), data another file declares |
| $`\mathit{carrier\_flow}`$ | `carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$, an expression this file adds `feasibility_carrier_flow` to |
| $`\mathit{penalty}`$ | `penalty` (scalar), an expression this file adds `unmet_demand_penalty` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{feasibility\_carrier\_flow}`$ | `feasibility_carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{unmet\_demand\_penalty}`$ | `unmet_demand_penalty` (scalar) — `$unmet_demand` of `min_cost_optimisation` — what unmet demand and unused supply cost |
| $`\mathit{unmet\_sum}`$ | `unmet_sum` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ — `unmet_sum` — net unmet demand; reported |

#### Definitions

**`feasibility_carrier_flow`**

```math
\mathit{feasibility\_carrier\_flow}_{n,c,t} = \mathit{unmet\_demand}_{n,c,t} + \mathit{unused\_supply}_{n,c,t} \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`unmet_demand_penalty`**

```math
\mathit{unmet\_demand\_penalty} = \left( \sum_{t \in \mathcal{T}} \left( \sum_{n \in \mathcal{N},\ c \in \mathcal{C}} \left( \mathit{unmet\_demand}_{n,c,t} - \mathit{unused\_supply}_{n,c,t} \right) \right) \cdot \mathrm{timestep\_weights}_{t} \right) \cdot \mathrm{bigM}
```

**`unmet_sum`**

```math
\mathit{unmet\_sum}_{n,c,t} = \mathit{unmet\_demand}_{n,c,t} + \mathit{unused\_supply}_{n,c,t} \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

#### Variable domains

**`unmet_demand`**

```math
\mathit{unmet\_demand}_{n,c,t} \ge 0 \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \lvert \{ i \in \mathcal{I} \,:\, \mathrm{carrier\_in}_{n,i,c} \} \rvert \ge 1 \vee \lvert \{ i \in \mathcal{I} \,:\, \mathrm{carrier\_out}_{n,i,c} \} \rvert \ge 1
```

**`unused_supply`**

```math
\mathit{unused\_supply}_{n,c,t} \le 0 \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \lvert \{ i \in \mathcal{I} \,:\, \mathrm{carrier\_in}_{n,i,c} \} \rvert \ge 1 \vee \lvert \{ i \in \mathcal{I} \,:\, \mathrm{carrier\_out}_{n,i,c} \} \rvert \ge 1
```
<!-- gallery:end -->
