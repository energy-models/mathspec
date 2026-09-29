<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# The cost

One of the base fragments of [Calliope in fragments](index.md). How Calliope prices a technology: investment, annualised; variable operation; fixed operation. It declares `cost_investment` and `cost_operation_variable` empty, and `cost_operation_fixed` with a body of its own, and each capacity or flow adds its cost.

<!-- gallery:begin -->
```yaml
dimensions:
  nodes:
    description: Calliope's `nodes` — the places technologies stand at
  techs:
    description: Calliope's `techs` — technologies
  costs:
    description: Calliope's `costs` — cost classes, such as monetary and CO2
  timesteps:
    description: Calliope's `timesteps` — time steps, in order
    dtype: datetime

parameters:
  cost_om_annual_investment_fraction:
    description: "`cost_om_annual_investment_fraction` — the annual cost of operation, as a share of the investment cost"
    dims: [nodes, techs, costs]
  cost_depreciation_rate:
    description: >-
      `cost_depreciation_rate` — the share of the investment cost a year
      carries; given only where set, and derived from the lifetime and the
      interest rate elsewhere
    dims: [nodes, techs, costs]
  cost_interest_rate:
    description: "`cost_interest_rate` — the interest rate an investment is annualised at"
    dims: [nodes, techs, costs]
  lifetime:
    description: >-
      `lifetime` — the years a technology lasts. Calliope's default is
      `.inf`, and data prep fills it
    dims: [nodes, techs]
  cost_annuity_factor:
    description: >-
      the annuity factor `r (1 + r) ** lifetime / ((1 + r) ** lifetime - 1)`
      of the interest rate `r`, data prep. mathspec refuses a sum as the
      base of `**` and as a divisor, over parameters too
    dims: [nodes, techs, costs]

given:
  parameters:
    timestep_resolution: { dims: [timesteps] }
    timestep_weights: { dims: [timesteps] }
    objective_cost_weights: { dims: [costs] }
  expressions:
    system_cost: { dims: [], term: cost_of_techs }

expressions:
  cost_investment:
    description: >-
      `cost_investment` — the investment cost of a technology: flow, storage
      and source capacity, and area use. Each file that builds a capacity
      adds its own cost
    dims: [nodes, techs, costs]
    empty: true
  cost_operation_variable:
    description: >-
      `cost_operation_variable` — the operating cost of a technology in a
      time step. Each file that builds a flow adds its own cost
    dims: [nodes, techs, costs, timesteps]
    empty: true
  cost_operation_fixed:
    description: >-
      `cost_operation_fixed` — the fixed annual operating cost of a
      technology: its share of the investment cost here, and what each file
      adds per unit of capacity
    dims: [nodes, techs, costs]
    expression: annualisation_weight * cost_investment * cost_om_annual_investment_fraction
  annualisation_weight:
    description: "`$annualisation_weight` — the share of a year the modelled time steps stand for"
    expression: sum(timestep_resolution * timestep_weights, over=timesteps) / 8760
  depreciation_rate:
    description: >-
      `$depreciation_rate` of `cost_investment_annualised` — the share of the
      investment cost a year carries: as given, one over the lifetime with
      no interest, and the annuity factor with some
    dims: [nodes, techs, costs]
    cases:
      given:
        when: cost_depreciation_rate
        expression: cost_depreciation_rate
      no_interest:
        when: NOT cost_depreciation_rate AND (NOT cost_interest_rate OR cost_interest_rate == 0)
        expression: 1 / lifetime
    otherwise: cost_annuity_factor
  cost_investment_annualised:
    description: "`cost_investment_annualised` — the investment cost, as a year's share scaled to the modelled time"
    expression: annualisation_weight * depreciation_rate * cost_investment
  cost:
    description: "`cost` — the total cost of a technology: investment, variable and fixed operation"
    expression: cost_investment_annualised + sum(cost_operation_variable, over=timesteps) + cost_operation_fixed
  cost_of_techs:
    description: "`sum(sum(cost, over=[nodes, techs]) * objective_cost_weights, over=costs)` of `min_cost_optimisation`"
    expression: sum(sum(sum(cost, over=nodes), over=techs) * objective_cost_weights)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{cost}^{\mathrm{om,annual,investment,fraction}}`$ | `cost_om_annual_investment_fraction` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_om_annual_investment_fraction` — the annual cost of operation, as a share of the investment cost |
| $`\mathrm{cost}^{\mathrm{depreciation,rate}}`$ | `cost_depreciation_rate` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_depreciation_rate` — the share of the investment cost a year carries; given only where set, and derived from the lifetime and the interest rate elsewhere |
| $`\mathrm{cost}^{\mathrm{interest,rate}}`$ | `cost_interest_rate` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_interest_rate` — the interest rate an investment is annualised at |
| $`\mathrm{lifetime}`$ | `lifetime` over $`\mathcal{N} \times \mathcal{I}`$ — `lifetime` — the years a technology lasts. Calliope's default is `.inf`, and data prep fills it |
| $`\mathrm{cost}^{\mathrm{annuity,factor}}`$ | `cost_annuity_factor` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — the annuity factor `r (1 + r) ** lifetime / ((1 + r) ** lifetime - 1)` of the interest rate `r`, data prep. mathspec refuses a sum as the base of `**` and as a divisor, over parameters too |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{objective\_cost\_weights}`$ | `objective_cost_weights` over $`\mathcal{K}`$, data another file declares |
| $`\mathit{system\_cost}`$ | `system_cost` (scalar), an expression this file adds `cost_of_techs` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{cost}^{\mathrm{operation,fixed}}`$ | `cost_operation_fixed` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_operation_fixed` — the fixed annual operating cost of a technology: its share of the investment cost here, and what each file adds per unit of capacity |
| $`\mathrm{annualisation\_weight}`$ | `annualisation_weight` (scalar) — `$annualisation_weight` — the share of a year the modelled time steps stand for |
| $`\mathrm{depreciation\_rate}`$ | `depreciation_rate` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `$depreciation_rate` of `cost_investment_annualised` — the share of the investment cost a year carries: as given, one over the lifetime with no interest, and the annuity factor with some |
| $`\mathit{cost}^{\mathrm{investment,annualised}}`$ | `cost_investment_annualised` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_investment_annualised` — the investment cost, as a year's share scaled to the modelled time |
| $`\mathit{cost}`$ | `cost` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost` — the total cost of a technology: investment, variable and fixed operation |
| $`\mathit{cost}^{\mathrm{of,techs}}`$ | `cost_of_techs` (scalar) — `sum(sum(cost, over=[nodes, techs]) * objective_cost_weights, over=costs)` of `min_cost_optimisation` |
| $`\mathit{cost}^{\mathrm{investment}}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_investment` — the investment cost of a technology: flow, storage and source capacity, and area use. Each file that builds a capacity adds its own cost |
| $`\mathit{cost}^{\mathrm{operation,variable}}`$ | `cost_operation_variable` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$ — `cost_operation_variable` — the operating cost of a technology in a time step. Each file that builds a flow adds its own cost |

#### Definitions

**`cost_operation_fixed`**

```math
\mathit{cost}^{\mathrm{operation,fixed}}_{n,i,k} = \mathrm{annualisation\_weight} \cdot \mathit{cost}^{\mathrm{investment}}_{n,i,k} \cdot \mathrm{cost}^{\mathrm{om,annual,investment,fraction}}_{n,i,k} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`annualisation_weight`**

```math
\mathrm{annualisation\_weight} = \frac{\sum_{t \in \mathcal{T}} \mathrm{timestep\_resolution}_{t} \cdot \mathrm{timestep\_weights}_{t}}{8760}
```

**`depreciation_rate`**

```math
\mathrm{depreciation\_rate}_{n,i,k} = \begin{cases} \mathrm{cost}^{\mathrm{depreciation,rate}}_{n,i,k} & \text{if } \mathrm{cost}^{\mathrm{depreciation,rate}}_{n,i,k} \text{ is defined} \\ \frac{1}{\mathrm{lifetime}_{n,i}} & \text{if } \neg \left( \mathrm{cost}^{\mathrm{depreciation,rate}}_{n,i,k} \text{ is defined} \right) \wedge \left( \neg \left( \mathrm{cost}^{\mathrm{interest,rate}}_{n,i,k} \text{ is defined} \right) \vee \mathrm{cost}^{\mathrm{interest,rate}}_{n,i,k} = 0 \right) \\ \mathrm{cost}^{\mathrm{annuity,factor}}_{n,i,k} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`cost_investment_annualised`**

```math
\mathit{cost}^{\mathrm{investment,annualised}}_{n,i,k} = \mathrm{annualisation\_weight} \cdot \mathrm{depreciation\_rate}_{n,i,k} \cdot \mathit{cost}^{\mathrm{investment}}_{n,i,k} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`cost`**

```math
\mathit{cost}_{n,i,k} = \mathit{cost}^{\mathrm{investment,annualised}}_{n,i,k} + \sum_{t \in \mathcal{T}} \mathit{cost}^{\mathrm{operation,variable}}_{n,i,k,t} + \mathit{cost}^{\mathrm{operation,fixed}}_{n,i,k} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`cost_of_techs`**

```math
\mathit{cost}^{\mathrm{of,techs}} = \sum_{k \in \mathcal{K}} \left( \sum_{i \in \mathcal{I}} \sum_{n \in \mathcal{N}} \mathit{cost}_{n,i,k} \right) \cdot \mathrm{objective\_cost\_weights}_{k}
```

**`cost_investment`**

```math
\mathit{cost}^{\mathrm{investment}}_{n,i,k} = \cdots \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`cost_operation_variable`**

```math
\mathit{cost}^{\mathrm{operation,variable}}_{n,i,k,t} = \cdots \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K},\ t \in \mathcal{T}
```
<!-- gallery:end -->
