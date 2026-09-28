<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Piecewise linear efficiency

An extension of [Calliope in fragments](../index.md). Calliope's example `piecewise_linear_efficiency.yaml`: inflow at least a convex curve of outflow, which needs the available flow capacity of the MILP file.

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
  pieces:
    description: Calliope's `pieces` — the lines a piecewise curve is the upper envelope of
    dtype: int

parameters:
  flow_eff_piecewise_slopes:
    description: "`flow_eff_piecewise_slopes` — the slope of each line of a convex inflow curve"
    dims: [nodes, techs, pieces]
  flow_eff_piecewise_intercept:
    description: "`flow_eff_piecewise_intercept` — the intercept of each line of a convex inflow curve"
    dims: [nodes, techs, pieces]

given:
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_in: { dims: [nodes, techs, carriers, timesteps] }
    available_flow_cap: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  piecewise_efficiency:
    description: >-
      `piecewise_efficiency` — inflow is at least every line of the curve of
      outflow, so at least the curve. Calliope's `where: available_flow_cap`
      over a technology reads as the technology having it for some carrier
    dims: [nodes, techs, timesteps, pieces]
    where: flow_eff_piecewise_slopes AND flow_eff_piecewise_intercept AND count(available_flow_cap, over=carriers) >= 1
    expression: >-
      sum(flow_in, over=carriers) >= flow_eff_piecewise_slopes * sum(flow_out, over=carriers)
      + flow_eff_piecewise_intercept * sum(available_flow_cap, over=carriers)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |
| $`\mathcal{P}`$ | index $`p`$ — `pieces` — Calliope's `pieces` — the lines a piecewise curve is the upper envelope of |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{flow\_eff\_piecewise\_slopes}`$ | `flow_eff_piecewise_slopes` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{P}`$ — `flow_eff_piecewise_slopes` — the slope of each line of a convex inflow curve |
| $`\mathrm{flow\_eff\_piecewise\_intercept}`$ | `flow_eff_piecewise_intercept` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{P}`$ — `flow_eff_piecewise_intercept` — the intercept of each line of a convex inflow curve |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_in}`$ | `flow_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{available\_flow\_cap}`$ | `available_flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |

#### Subject to

**`piecewise_efficiency`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_in}_{n,i,c,t} \ge \mathrm{flow\_eff\_piecewise\_slopes}_{n,i,p} \cdot \left( \sum_{c \in \mathcal{C}} \mathit{flow\_out}_{n,i,c,t} \right) + \mathrm{flow\_eff\_piecewise\_intercept}_{n,i,p} \cdot \left( \sum_{c \in \mathcal{C}} \mathit{available\_flow\_cap}_{n,i,c,t} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T},\ p \in \mathcal{P} \,:\, \mathrm{flow\_eff\_piecewise\_slopes}_{n,i,p} \text{ is defined} \wedge \mathrm{flow\_eff\_piecewise\_intercept}_{n,i,p} \text{ is defined} \wedge \lvert \{ c \in \mathcal{C} \,:\, \mathit{available\_flow\_cap}_{n,i,c,t} \text{ exists} \} \rvert \ge 1
```
<!-- gallery:end -->
