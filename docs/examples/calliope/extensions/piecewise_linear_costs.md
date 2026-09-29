<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Piecewise linear costs

An extension of [Calliope in fragments](../index.md). Calliope's example `piecewise_linear_costs.yaml`: a convex investment cost as the upper envelope of lines, which needs the units of the MILP file. The cost is a term of `cost_investment`. It declares the variable the SOS2 example declares, so the two do not compose.

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
  pieces:
    description: Calliope's `pieces` — the lines a piecewise curve is the upper envelope of
    dtype: int

parameters:
  cost_flow_cap_piecewise_slopes:
    description: "`cost_flow_cap_piecewise_slopes` — the slope of each line of a convex investment cost curve"
    dims: [nodes, techs, costs, pieces]
  cost_flow_cap_piecewise_intercept:
    description: "`cost_flow_cap_piecewise_intercept` — the intercept of each line of a convex investment cost curve"
    dims: [nodes, techs, costs, pieces]

variables:
  piecewise_cost_investment:
    description: "`piecewise_cost_investment` — an investment cost that grows faster the more capacity is built"
    dims: [nodes, techs, costs]
    where: >-
      count(cost_flow_cap_piecewise_slopes, over=pieces) >= 1
      AND count(cost_flow_cap_piecewise_intercept, over=pieces) >= 1 AND purchased_units
    bounds: { lower: 0 }
    absence: zero

given:
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
    purchased_units: { dims: [nodes, techs] }
  expressions:
    cost_investment: { dims: [nodes, techs, costs], term: piecewise_cost_investment_term }

expressions:
  piecewise_cost_investment_term:
    description: "`+ piecewise_cost_investment` — the term Calliope writes into `cost_investment`, by restating it whole"
    expression: piecewise_cost_investment

constraints:
  piecewise_costs:
    description: "`piecewise_costs` — the investment cost is at least every line of the curve, so at least the curve"
    dims: [nodes, techs, costs, pieces]
    where: piecewise_cost_investment
    expression: >-
      piecewise_cost_investment >= sum(cost_flow_cap_piecewise_slopes * flow_cap, over=carriers)
      + cost_flow_cap_piecewise_intercept * purchased_units
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |
| $`\mathcal{P}`$ | index $`p`$ — `pieces` — Calliope's `pieces` — the lines a piecewise curve is the upper envelope of |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{cost\_flow\_cap\_piecewise\_slopes}`$ | `cost_flow_cap_piecewise_slopes` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{P}`$ — `cost_flow_cap_piecewise_slopes` — the slope of each line of a convex investment cost curve |
| $`\mathrm{cost\_flow\_cap\_piecewise\_intercept}`$ | `cost_flow_cap_piecewise_intercept` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{P}`$ — `cost_flow_cap_piecewise_intercept` — the intercept of each line of a convex investment cost curve |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{piecewise\_cost\_investment}`$ | `piecewise_cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `piecewise_cost_investment` — an investment cost that grows faster the more capacity is built |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{purchased\_units}`$ | `purchased_units` over $`\mathcal{N} \times \mathcal{I}`$ |
| $`\mathit{cost\_investment}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `piecewise_cost_investment_term` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{piecewise\_cost\_investment\_term}`$ | `piecewise_cost_investment_term` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `+ piecewise_cost_investment` — the term Calliope writes into `cost_investment`, by restating it whole |

Upright is what the data supplies — a parameter such as $`\mathrm{cost\_flow\_cap\_piecewise\_slopes}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{piecewise\_cost\_investment}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`piecewise_costs`**

```math
\mathit{piecewise\_cost\_investment}_{n,i,k} \ge \sum_{c \in \mathcal{C}} \mathrm{cost\_flow\_cap\_piecewise\_slopes}_{n,i,k,p} \cdot \mathit{flow\_cap}_{n,i,c} + \mathrm{cost\_flow\_cap\_piecewise\_intercept}_{n,i,k,p} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K},\ p \in \mathcal{P} \,:\, \mathit{piecewise\_cost\_investment}_{n,i,k} \text{ exists}
```

#### Definitions

**`piecewise_cost_investment_term`**

```math
\mathit{piecewise\_cost\_investment\_term}_{n,i,k} = \mathit{piecewise\_cost\_investment}_{n,i,k} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

#### Variable domains

**`piecewise_cost_investment`**

```math
\mathit{piecewise\_cost\_investment}_{n,i,k} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K} \,:\, \lvert \{ p \in \mathcal{P} \,:\, \mathrm{cost\_flow\_cap\_piecewise\_slopes}_{n,i,k,p} \text{ is defined} \} \rvert \ge 1 \wedge \lvert \{ p \in \mathcal{P} \,:\, \mathrm{cost\_flow\_cap\_piecewise\_intercept}_{n,i,k,p} \text{ is defined} \} \rvert \ge 1 \wedge \mathit{purchased\_units}_{n,i} \text{ exists}
```
<!-- gallery:end -->
