<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Monthly peak flow charge

An extension of [Calliope in fragments](../index.md). Calliope's example `monthly_peak_flow_charge.yaml`: a cost on the peak outflow of each month. Calliope restates `cost_operation_fixed` to add it; here it is a term. The month of a time step is a relation, so the row is one per time step, not one per time step and month.

<!-- gallery:begin -->
```yaml
dimensions:
  nodes:
    description: Calliope's `nodes` — the places technologies stand at
  techs:
    description: Calliope's `techs` — technologies
  carriers:
    description: Calliope's `carriers` — energy and commodity carriers
  costs:
    description: Calliope's `costs` — cost classes, such as monetary and CO2
  timesteps:
    description: Calliope's `timesteps` — time steps, in order
    dtype: datetime
  months:
    description: Calliope's `months` — the months of the year
    dtype: int

relations:
  lookup_month:
    description: >-
      `lookup_month` — the month a time step falls in. Calliope ships it as a
      boolean table over time step and month, and builds its row over both;
      as a relation the row is one per time step
    key: timesteps
    values: months

parameters:
  monthly_peak_mode:
    description: "`monthly_peak_mode` — whether a technology's peak outflow in a month is priced"
    dims: [nodes, techs, carriers]
    dtype: bool
  cost_month_peak:
    description: "`cost_month_peak` — the cost of one unit of peak outflow in a month"
    dims: [nodes, techs, costs]

variables:
  flow_peak_month:
    description: "`flow_peak_month` — a technology's peak outflow in a month"
    dims: [nodes, techs, carriers, months]
    where: carrier_out AND monthly_peak_mode
    bounds: { lower: 0, upper: flow_cap_max }
    absence: zero

expressions:
  cost_month_peak_charge:
    description: "`sum(cost_month_peak * flow_peak_month, over=[carriers, months])` — the term Calliope writes into `cost_operation_fixed`, by restating it whole"
    expression: sum(cost_month_peak * flow_peak_month, over=[carriers, months])

given:
  parameters:
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
    flow_cap_max: { dims: [nodes, techs] }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
  expressions:
    cost_operation_fixed: { dims: [nodes, techs, costs], term: cost_month_peak_charge }

constraints:
  set_peak_month_flow:
    description: "`set_peak_month_flow` — the peak outflow in a month is at least the outflow in each of its time steps"
    dims: [nodes, techs, carriers, timesteps]
    where: at(flow_peak_month, by=lookup_month, over=months, into=timesteps)
    expression: flow_out <= at(flow_peak_month, by=lookup_month, over=months, into=timesteps)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` with $`\mathrm{lookup\_month}: \mathcal{T} \to \mathcal{M}`$ — Calliope's `timesteps` — time steps, in order |
| $`\mathcal{M}`$ | index $`m`$ — `months` with $`\mathrm{lookup\_month}: \mathcal{T} \to \mathcal{M}`$ — Calliope's `months` — the months of the year |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{monthly\_peak\_mode}`$ | `monthly_peak_mode` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `monthly_peak_mode` — whether a technology's peak outflow in a month is priced |
| $`\mathrm{cost\_month\_peak}`$ | `cost_month_peak` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_month_peak` — the cost of one unit of peak outflow in a month |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_peak\_month}`$ | `flow_peak_month` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{M}`$ — `flow_peak_month` — a technology's peak outflow in a month |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{flow\_cap\_max}`$ | `flow_cap_max` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{cost\_operation\_fixed}`$ | `cost_operation_fixed` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `cost_month_peak_charge` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{cost\_month\_peak\_charge}`$ | `cost_month_peak_charge` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `sum(cost_month_peak * flow_peak_month, over=[carriers, months])` — the term Calliope writes into `cost_operation_fixed`, by restating it whole |

Upright is what the data supplies — a parameter such as $`\mathrm{monthly\_peak\_mode}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{flow\_peak\_month}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`set_peak_month_flow`**

```math
\mathit{flow\_out}_{n,i,c,t} \le \mathit{flow\_peak\_month}_{n,i,c,\mathrm{lookup\_month}(t)} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_peak\_month}_{n,i,c,\mathrm{lookup\_month}(t)} \text{ exists}
```

#### Definitions

**`cost_month_peak_charge`**

```math
\mathit{cost\_month\_peak\_charge}_{n,i,k} = \sum_{c \in \mathcal{C},\ m \in \mathcal{M}} \mathrm{cost\_month\_peak}_{n,i,k} \cdot \mathit{flow\_peak\_month}_{n,i,c,m} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

#### Variable domains

**`flow_peak_month`**

```math
0 \le \mathit{flow\_peak\_month}_{n,i,c,m} \le \mathrm{flow\_cap\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ m \in \mathcal{M} \,:\, \mathrm{carrier\_out}_{n,i,c} \wedge \mathrm{monthly\_peak\_mode}_{n,i,c}
```
<!-- gallery:end -->
