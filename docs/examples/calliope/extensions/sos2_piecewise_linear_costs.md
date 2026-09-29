<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Piecewise linear costs with SOS2

An extension of [Calliope in fragments](../index.md). Calliope's example `sos2_piecewise_linear_costs.yaml`: an investment cost with economies of scale, as a curve through breakpoints stated as an SOS2 set. The cost is a term of `cost_investment`.

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
  breakpoints:
    description: Calliope's `breakpoints` — the corners of a piecewise-linear curve, in order
    dtype: int

parameters:
  piecewise_cost_investment_x:
    description: "`piecewise_cost_investment_x` — the flow capacity at each breakpoint"
    dims: [techs, breakpoints]
  piecewise_cost_investment_y:
    description: "`piecewise_cost_investment_y` — the investment cost at each breakpoint"
    dims: [techs, costs, breakpoints]

variables:
  piecewise_cost_investment:
    description: "`piecewise_cost_investment` — an investment cost that grows more slowly the more capacity is built"
    dims: [nodes, techs, carriers, costs]
    where: count(piecewise_cost_investment_x, over=breakpoints) >= 1 AND count(piecewise_cost_investment_y, over=breakpoints) >= 1
    bounds: { lower: 0 }
    absence: zero
  piecewise_flow_cap:
    description: >-
      the flow capacity, where the technology has a cost curve. A
      `piecewise:` block takes no `where:`, so its link rows would pin
      `flow_cap` to the curve at every technology; a link over this copy is
      built only where the copy is
    dims: [nodes, techs, carriers, costs]
    where: count(piecewise_cost_investment_x, over=breakpoints) >= 1 AND count(piecewise_cost_investment_y, over=breakpoints) >= 1

constraints:
  piecewise_flow_cap_is_flow_cap:
    description: the copy of the flow capacity the curve reads is the flow capacity
    dims: [nodes, techs, carriers, costs]
    where: piecewise_flow_cap
    expression: piecewise_flow_cap == flow_cap

piecewise:
  sos2_piecewise_costs:
    description: "`sos2_piecewise_costs` — the investment cost lies on the curve through the breakpoints, stated as an SOS2 set"
    over: breakpoints
    method: sos2
    points: piecewise_cost_investment_x
    links:
      - [piecewise_flow_cap, piecewise_cost_investment_x]
      - [piecewise_cost_investment, piecewise_cost_investment_y]

expressions:
  cost_investment_piecewise:
    description: "`sum(piecewise_cost_investment, over=carriers)` — the term Calliope writes into `cost_investment`"
    expression: sum(piecewise_cost_investment, over=carriers)

given:
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
  expressions:
    cost_investment: { dims: [nodes, techs, costs], term: cost_investment_piecewise }
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |
| $`\mathcal{B}`$ | index $`b`$ — `breakpoints` — Calliope's `breakpoints` — the corners of a piecewise-linear curve, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{piecewise\_cost\_investment\_x}`$ | `piecewise_cost_investment_x` over $`\mathcal{I} \times \mathcal{B}`$ — `piecewise_cost_investment_x` — the flow capacity at each breakpoint |
| $`\mathrm{piecewise\_cost\_investment\_y}`$ | `piecewise_cost_investment_y` over $`\mathcal{I} \times \mathcal{K} \times \mathcal{B}`$ — `piecewise_cost_investment_y` — the investment cost at each breakpoint |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{piecewise\_cost\_investment}`$ | `piecewise_cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{K}`$ — `piecewise_cost_investment` — an investment cost that grows more slowly the more capacity is built |
| $`\mathit{piecewise\_flow\_cap}`$ | `piecewise_flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{K}`$ — the flow capacity, where the technology has a cost curve. A `piecewise:` block takes no `where:`, so its link rows would pin `flow_cap` to the curve at every technology; a link over this copy is built only where the copy is |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{cost\_investment}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `cost_investment_piecewise` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{cost\_investment\_piecewise}`$ | `cost_investment_piecewise` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `sum(piecewise_cost_investment, over=carriers)` — the term Calliope writes into `cost_investment` |

Upright is what the data supplies — a parameter such as $`\mathrm{piecewise\_cost\_investment\_x}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{piecewise\_cost\_investment}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`piecewise_flow_cap_is_flow_cap`**

```math
\mathit{piecewise\_flow\_cap}_{n,i,c,k} = \mathit{flow\_cap}_{n,i,c} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ k \in \mathcal{K} \,:\, \mathit{piecewise\_flow\_cap}_{n,i,c,k} \text{ exists}
```

**`sos2_piecewise_costs`**

```math
\left( \mathit{piecewise\_flow\_cap}_{n,i,c,k},\ \mathit{piecewise\_cost\_investment}_{n,i,c,k} \right) \in \mathrm{pwl}_{b \in \mathcal{B} \,:\, \mathrm{piecewise\_cost\_investment\_x}_{i,b} \text{ is defined}}(\mathrm{piecewise\_cost\_investment\_x}_{i,b},\ \mathrm{piecewise\_cost\_investment\_y}_{i,k,b}) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ k \in \mathcal{K}
```

#### Definitions

**`cost_investment_piecewise`**

```math
\mathit{cost\_investment\_piecewise}_{n,i,k} = \sum_{c \in \mathcal{C}} \mathit{piecewise\_cost\_investment}_{n,i,c,k} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

#### Variable domains

**`piecewise_cost_investment`**

```math
\mathit{piecewise\_cost\_investment}_{n,i,c,k} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ k \in \mathcal{K} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{piecewise\_cost\_investment\_x}_{i,b} \text{ is defined} \} \rvert \ge 1 \wedge \lvert \{ b \in \mathcal{B} \,:\, \mathrm{piecewise\_cost\_investment\_y}_{i,k,b} \text{ is defined} \} \rvert \ge 1
```

**`piecewise_flow_cap`**

```math
\mathit{piecewise\_flow\_cap}_{n,i,c,k} \in \mathbb{R} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ k \in \mathcal{K} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{piecewise\_cost\_investment\_x}_{i,b} \text{ is defined} \} \rvert \ge 1 \wedge \lvert \{ b \in \mathcal{B} \,:\, \mathrm{piecewise\_cost\_investment\_y}_{i,k,b} \text{ is defined} \} \rvert \ge 1
```

#### Assumptions

**`sos2_piecewise_costs_complete`**

```math
\mathrm{piecewise\_cost\_investment\_x}_{i,b} \text{ is defined} \wedge \mathrm{piecewise\_cost\_investment\_y}_{i,k,b} \text{ is defined} \qquad \forall\, i \in \mathcal{I},\ k \in \mathcal{K},\ b \in \mathcal{B} \,:\, \mathrm{piecewise\_cost\_investment\_x}_{i,b} \text{ is defined}
```

**`sos2_piecewise_costs_contiguous`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{piecewise\_cost\_investment\_x}_{i,b} \text{ is defined} \wedge \neg \left( \mathrm{piecewise\_cost\_investment\_x}_{i,b - 1} \text{ is defined} \right) \} \rvert = 1 \qquad \forall\, i \in \mathcal{I}
```
<!-- gallery:end -->
