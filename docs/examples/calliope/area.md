<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Area

One of the base fragments of [Calliope in fragments](index.md). Area use, its limits, its tie to flow capacity, and its cost.

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

parameters:
  area_use_min:
    description: "`area_use_min` — least area use. Calliope's default is 0, and data prep fills it"
    dims: [nodes, techs]
  area_use_max:
    description: "`area_use_max` — most area use. Calliope's default is `.inf`, and data prep fills it"
    dims: [nodes, techs]
  area_use_per_flow_cap:
    description: "`area_use_per_flow_cap` — area use per unit of flow capacity; given only where set"
    dims: [nodes, techs]
  available_area:
    description: "`available_area` — the area every technology at a node may use; given only where set"
    dims: [nodes]
  cost_area_use:
    description: "`cost_area_use` — the cost of one unit of area use"
    dims: [nodes, techs, costs]

variables:
  area_use:
    description: >-
      `area_use` — the area a technology uses. Calliope builds it where
      `area_use_min` is given at all; the least area use is data here, so
      it is built where that is above zero
    dims: [nodes, techs]
    where: area_use_min > 0 OR area_use_max OR area_use_per_flow_cap OR sink_unit == per_area OR source_unit == per_area
    bounds: { lower: area_use_min, upper: area_use_max }
    absence: zero

expressions:
  cost_investment_area_use:
    description: "`cost_investment_area_use` — the investment cost of area use"
    expression: cost_area_use * area_use

given:
  parameters:
    flow_cap_max: { dims: [nodes, techs] }
    sink_unit: { dims: [nodes, techs], dtype: str }
    source_unit: { dims: [nodes, techs], dtype: str }
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
  expressions:
    cost_investment: { dims: [nodes, techs, costs], term: cost_investment_area_use }

constraints:
  force_zero_area_use:
    description: "`force_zero_area_use` — a technology with no flow capacity uses no area"
    dims: [nodes, techs]
    where: area_use AND flow_cap_max == 0
    expression: area_use == 0
  area_use_per_flow_capacity:
    description: "`area_use_per_flow_capacity` — area use follows flow capacity, where set"
    dims: [nodes, techs, carriers]
    where: flow_cap AND area_use AND area_use_per_flow_cap
    expression: area_use == flow_cap * area_use_per_flow_cap
  area_use_capacity_per_loc:
    description: >-
      `area_use_capacity_per_loc` — the technologies at a node use at most
      its available area. Calliope's `where: area_use` over a node reads as
      any technology there using area
    dims: [nodes]
    where: count(area_use, over=techs) >= 1 AND available_area
    expression: sum(area_use, over=techs) <= available_area

assumptions:
  unbounded_area_use_cost:
    description: Calliope's `unbounded_area_use_cost` — a negative area cost needs a finite maximum
    holds: NOT cost_area_use < 0 OR area_use_max
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{area\_use\_min}`$ | `area_use_min` over $`\mathcal{N} \times \mathcal{I}`$ — `area_use_min` — least area use. Calliope's default is 0, and data prep fills it |
| $`\mathrm{area\_use\_max}`$ | `area_use_max` over $`\mathcal{N} \times \mathcal{I}`$ — `area_use_max` — most area use. Calliope's default is `.inf`, and data prep fills it |
| $`\mathrm{area\_use\_per\_flow\_cap}`$ | `area_use_per_flow_cap` over $`\mathcal{N} \times \mathcal{I}`$ — `area_use_per_flow_cap` — area use per unit of flow capacity; given only where set |
| $`\mathrm{available\_area}`$ | `available_area` over $`\mathcal{N}`$ — `available_area` — the area every technology at a node may use; given only where set |
| $`\mathrm{cost\_area\_use}`$ | `cost_area_use` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_area_use` — the cost of one unit of area use |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{area\_use}`$ | `area_use` over $`\mathcal{N} \times \mathcal{I}`$ — `area_use` — the area a technology uses. Calliope builds it where `area_use_min` is given at all; the least area use is data here, so it is built where that is above zero |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{flow\_cap\_max}`$ | `flow_cap_max` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{sink\_unit}`$ | `sink_unit` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{source\_unit}`$ | `source_unit` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{cost\_investment}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `cost_investment_area_use` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{cost\_investment\_area\_use}`$ | `cost_investment_area_use` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_investment_area_use` — the investment cost of area use |

Upright is what the data supplies — a parameter such as $`\mathrm{area\_use\_min}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{area\_use}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`force_zero_area_use`**

```math
\mathit{area\_use}_{n,i} = 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathit{area\_use}_{n,i} \text{ exists} \wedge \mathrm{flow\_cap\_max}_{n,i} = 0
```

**`area_use_per_flow_capacity`**

```math
\mathit{area\_use}_{n,i} = \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{area\_use\_per\_flow\_cap}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathit{area\_use}_{n,i} \text{ exists} \wedge \mathrm{area\_use\_per\_flow\_cap}_{n,i} \text{ is defined}
```

**`area_use_capacity_per_loc`**

```math
\sum_{i \in \mathcal{I}} \mathit{area\_use}_{n,i} \le \mathrm{available\_area}_{n} \qquad \forall\, n \in \mathcal{N} \,:\, \lvert \{ i \in \mathcal{I} \,:\, \mathit{area\_use}_{n,i} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{available\_area}_{n} \text{ is defined}
```

#### Definitions

**`cost_investment_area_use`**

```math
\mathit{cost\_investment\_area\_use}_{n,i,k} = \mathrm{cost\_area\_use}_{n,i,k} \cdot \mathit{area\_use}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

#### Variable domains

**`area_use`**

```math
\mathrm{area\_use\_min}_{n,i} \le \mathit{area\_use}_{n,i} \le \mathrm{area\_use\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{area\_use\_min}_{n,i} > 0 \vee \mathrm{area\_use\_max}_{n,i} \text{ is defined} \vee \mathrm{area\_use\_per\_flow\_cap}_{n,i} \text{ is defined} \vee \mathrm{sink\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'} \vee \mathrm{source\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'}
```

#### Assumptions

**`unbounded_area_use_cost`**

```math
\neg \left( \mathrm{cost\_area\_use}_{n,i,k} < 0 \right) \vee \mathrm{area\_use\_max}_{n,i} \text{ is defined} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```
<!-- gallery:end -->
