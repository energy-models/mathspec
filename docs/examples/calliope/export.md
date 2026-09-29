<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Export

One of the base fragments of [Calliope in fragments](index.md). Export out of the system: a technology may export a carrier it produces, and the export leaves the balance and has a cost.

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
  costs:
    description: Calliope's `costs` — cost classes, such as monetary and CO2

parameters:
  carrier_export:
    description: "`carrier_export` — whether a technology may export a carrier it produces out of the system"
    dims: [nodes, techs, carriers]
    dtype: bool
  export_min:
    description: "`export_min` — least export. Calliope's default is 0, and data prep fills it"
    dims: [nodes, techs, carriers]
  export_max:
    description: "`export_max` — most export. Calliope's default is `.inf`, and data prep fills it"
    dims: [nodes, techs, carriers]
  cost_export:
    description: "`cost_export` — the cost of one unit of export, usually negative"
    dims: [nodes, techs, costs, timesteps]

variables:
  flow_export:
    description: "`flow_export` — what a technology exports out of the system in a time step"
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_export
    bounds: { lower: export_min, upper: export_max }
    absence: zero

expressions:
  export_carrier_flow: -sum(flow_export, over=techs)
  export_cost_operation_variable: timestep_weights * sum(cost_export * flow_export, over=carriers)

given:
  parameters:
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
    timestep_weights: { dims: [timesteps] }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
  expressions:
    carrier_flow: { dims: [nodes, carriers, timesteps], term: export_carrier_flow }
    cost_operation_variable: { dims: [nodes, techs, costs, timesteps], term: export_cost_operation_variable }

constraints:
  export_balance:
    description: "`export_balance` — a technology exports at most what it puts out"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_export
    expression: flow_out >= flow_export

assumptions:
  export_only_for_outflows:
    description: Calliope's `export_only_for_outflows` — an exported carrier is one the technology produces
    holds: NOT carrier_export OR count(carrier_out, over=nodes) >= 1
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{carrier\_export}`$ | `carrier_export` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `carrier_export` — whether a technology may export a carrier it produces out of the system |
| $`\mathrm{export\_min}`$ | `export_min` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `export_min` — least export. Calliope's default is 0, and data prep fills it |
| $`\mathrm{export\_max}`$ | `export_max` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `export_max` — most export. Calliope's default is `.inf`, and data prep fills it |
| $`\mathrm{cost\_export}`$ | `cost_export` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$ — `cost_export` — the cost of one unit of export, usually negative |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_export}`$ | `flow_export` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_export` — what a technology exports out of the system in a time step |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{carrier\_flow}`$ | `carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$, an expression this file adds `export_carrier_flow` to |
| $`\mathit{cost\_operation\_variable}`$ | `cost_operation_variable` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$, an expression this file adds `export_cost_operation_variable` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{export\_carrier\_flow}`$ | `export_carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{export\_cost\_operation\_variable}`$ | `export_cost_operation_variable` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T} \times \mathcal{K}`$ |

Upright is what the data supplies — a parameter such as $`\mathrm{carrier\_export}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{flow\_export}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`export_balance`**

```math
\mathit{flow\_out}_{n,i,c,t} \ge \mathit{flow\_export}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_export}_{n,i,c,t} \text{ exists}
```

#### Definitions

**`export_carrier_flow`**

```math
\mathit{export\_carrier\_flow}_{n,c,t} = -\left( \sum_{i \in \mathcal{I}} \mathit{flow\_export}_{n,i,c,t} \right) \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`export_cost_operation_variable`**

```math
\mathit{export\_cost\_operation\_variable}_{n,i,t,k} = \mathrm{timestep\_weights}_{t} \cdot \left( \sum_{c \in \mathcal{C}} \mathrm{cost\_export}_{n,i,k,t} \cdot \mathit{flow\_export}_{n,i,c,t} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T},\ k \in \mathcal{K}
```

#### Variable domains

**`flow_export`**

```math
\mathrm{export\_min}_{n,i,c} \le \mathit{flow\_export}_{n,i,c,t} \le \mathrm{export\_max}_{n,i,c} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_export}_{n,i,c}
```

#### Assumptions

**`export_only_for_outflows`**

```math
\neg \mathrm{carrier\_export}_{n,i,c} \vee \lvert \{ n' \in \mathcal{N} \,:\, \mathrm{carrier\_out}_{n',i,c} \} \rvert \ge 1 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C}
```
<!-- gallery:end -->
