<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Supply

One of the base fragments of [Calliope in fragments](index.md). Supply technologies: the source a technology takes from outside the system, its capacity and its availability. The source scaler reads `area_use`, so a model with a per-area source composes this file with the area file.

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
  source_eff:
    description: "`source_eff` — the share of the source a supply technology takes in. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs, timesteps]
  source_use_min:
    description: "`source_use_min` — least source use in a time step, per unit of `source_unit`"
    dims: [nodes, techs, timesteps]
  source_use_max:
    description: "`source_use_max` — most source use in a time step, per unit of `source_unit`; given only where set"
    dims: [nodes, techs, timesteps]
  source_use_equals:
    description: "`source_use_equals` — the source use required in a time step, per unit of `source_unit`; given only where set"
    dims: [nodes, techs, timesteps]
  source_unit:
    description: >-
      `source_unit` — what the source is per: `absolute`, `per_area` of
      area use, or `per_cap` of flow capacity. Calliope's default is
      `absolute`, which is what a technology with no row reads as
    dims: [nodes, techs]
    dtype: str
  source_cap_min:
    description: "`source_cap_min` — least source capacity. Calliope's default is 0, and data prep fills it"
    dims: [nodes, techs]
  source_cap_max:
    description: "`source_cap_max` — most source capacity. Calliope's default is `.inf`, and data prep fills it"
    dims: [nodes, techs]
  source_cap_equals_flow_cap:
    description: "`source_cap_equals_flow_cap` — whether the source capacity equals the flow capacity"
    dims: [nodes, techs]
    dtype: bool
  cost_source_use:
    description: "`cost_source_use` — the cost of one unit of source use"
    dims: [nodes, techs, costs, timesteps]
  cost_source_cap:
    description: "`cost_source_cap` — the cost of one unit of source capacity"
    dims: [nodes, techs, costs]

variables:
  source_use:
    description: "`source_use` — what a supply technology takes in from outside the system in a time step"
    dims: [nodes, techs, timesteps]
    where: base_tech == 'supply'
    bounds: { lower: 0 }
    absence: zero
  source_cap:
    description: "`source_cap` — the most a supply technology can take in from outside the system"
    dims: [nodes, techs]
    where: base_tech == 'supply'
    bounds: { lower: source_cap_min, upper: source_cap_max }
    absence: zero

expressions:
  flow_cap_out:
    description: "`where(flow_cap, carrier_out)` — the flow capacity of the carriers a technology produces"
    dims: [nodes, techs, carriers]
    cases:
      produced:
        when: carrier_out
        expression: flow_cap
    otherwise: 0
  source_scaler:
    description: "`$source_scaler` — what the source parameters are per: area use, flow capacity, or one"
    dims: [nodes, techs]
    cases:
      per_area:
        when: source_unit == per_area
        expression: area_use
      per_cap:
        when: source_unit == per_cap
        expression: sum(flow_cap_out, over=carriers)
    otherwise: 1
  cost_investment_source_cap:
    description: "`cost_investment_source_cap` — the investment cost of source capacity"
    expression: cost_source_cap * source_cap
  supply_cost_operation_variable: timestep_weights * cost_source_use * source_use
  curtailment:
    description: >-
      `curtailment` — the share of the available source a supply technology
      leaves unused in a time step; reported
    expression: 1 - source_use / (source_use_max * source_scaler)
  total_curtailment:
    description: "`total_curtailment` — the share of the available source left unused over the whole time; reported"
    expression: 1 - sum(source_use, over=timesteps) / sum(source_use_max * source_scaler, over=timesteps)

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
    include_storage: { dims: [nodes, techs], dtype: bool }
    timestep_resolution: { dims: [timesteps] }
    timestep_weights: { dims: [timesteps] }
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
    area_use: { dims: [nodes, techs] }
  expressions:
    flow_out_inc_eff: { dims: [nodes, techs, carriers, timesteps] }
    cost_investment: { dims: [nodes, techs, costs], term: cost_investment_source_cap }
    cost_operation_variable: { dims: [nodes, techs, costs, timesteps], term: supply_cost_operation_variable }

constraints:
  source_max:
    description: "`source_max` — source use is at most the source capacity over the time step"
    dims: [nodes, techs, timesteps]
    where: source_cap
    expression: source_use <= timestep_resolution * source_cap
  source_capacity_equals_flow_capacity:
    description: "`source_capacity_equals_flow_capacity` — a supply technology's source capacity equals its flow capacity, where set"
    dims: [nodes, techs, carriers]
    where: flow_cap AND source_cap AND source_cap_equals_flow_cap
    expression: source_cap == flow_cap
  balance_supply_no_storage:
    description: "`balance_supply_no_storage` — a supply technology with no store puts out what it takes from its source"
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_out AND base_tech == 'supply' AND NOT include_storage
    expression: flow_out_inc_eff == source_use * source_eff
  source_availability_supply_equals:
    description: "`source_availability_supply` where `source_use_equals` is set — source use is what is available"
    dims: [nodes, techs, timesteps]
    where: source_use AND source_use_equals
    expression: source_use == source_use_equals * source_scaler
  source_availability_supply_max:
    description: "`source_availability_supply` where only `source_use_max` is set — source use is at most what is available"
    dims: [nodes, techs, timesteps]
    where: source_use AND NOT source_use_equals AND source_use_max
    expression: source_use <= source_use_max * source_scaler
  balance_supply_min_use:
    description: "`balance_supply_min_use` — source use is at least its least use"
    dims: [nodes, techs, timesteps]
    where: source_use_min AND NOT source_use_equals AND base_tech == 'supply'
    expression: source_use >= source_use_min * source_scaler

assumptions:
  unbounded_source_use_cost:
    description: Calliope's `unbounded_source_use_cost` — a negative source capacity cost needs a finite maximum
    holds: NOT cost_source_cap < 0 OR source_cap_max
  finite_source_use:
    description: Calliope's `finite_source_use`, for the source — a required use is finite
    holds: NOT source_use_equals == inf
  source_unit_one_of:
    description: Calliope's `one_of` on `source_unit`
    holds: source_unit == absolute OR source_unit == per_area OR source_unit == per_cap
    where: source_unit
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
| $`\mathrm{source\_eff}`$ | `source_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `source_eff` — the share of the source a supply technology takes in. Calliope's default is 1, and data prep fills it |
| $`\mathrm{source\_use\_min}`$ | `source_use_min` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `source_use_min` — least source use in a time step, per unit of `source_unit` |
| $`\mathrm{source\_use\_max}`$ | `source_use_max` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `source_use_max` — most source use in a time step, per unit of `source_unit`; given only where set |
| $`\mathrm{source\_use\_equals}`$ | `source_use_equals` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `source_use_equals` — the source use required in a time step, per unit of `source_unit`; given only where set |
| $`\mathrm{source\_unit}`$ | `source_unit` over $`\mathcal{N} \times \mathcal{I}`$ — `source_unit` — what the source is per: `absolute`, `per_area` of area use, or `per_cap` of flow capacity. Calliope's default is `absolute`, which is what a technology with no row reads as |
| $`\mathrm{source\_cap\_min}`$ | `source_cap_min` over $`\mathcal{N} \times \mathcal{I}`$ — `source_cap_min` — least source capacity. Calliope's default is 0, and data prep fills it |
| $`\mathrm{source\_cap\_max}`$ | `source_cap_max` over $`\mathcal{N} \times \mathcal{I}`$ — `source_cap_max` — most source capacity. Calliope's default is `.inf`, and data prep fills it |
| $`\mathrm{source\_cap\_equals\_flow\_cap}`$ | `source_cap_equals_flow_cap` over $`\mathcal{N} \times \mathcal{I}`$ — `source_cap_equals_flow_cap` — whether the source capacity equals the flow capacity |
| $`\mathrm{cost\_source\_use}`$ | `cost_source_use` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$ — `cost_source_use` — the cost of one unit of source use |
| $`\mathrm{cost\_source\_cap}`$ | `cost_source_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_source_cap` — the cost of one unit of source capacity |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{source\_use}`$ | `source_use` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `source_use` — what a supply technology takes in from outside the system in a time step |
| $`\mathit{source\_cap}`$ | `source_cap` over $`\mathcal{N} \times \mathcal{I}`$ — `source_cap` — the most a supply technology can take in from outside the system |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{include\_storage}`$ | `include_storage` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{area\_use}`$ | `area_use` over $`\mathcal{N} \times \mathcal{I}`$ |
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{cost\_investment}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `cost_investment_source_cap` to |
| $`\mathit{cost\_operation\_variable}`$ | `cost_operation_variable` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$, an expression this file adds `supply_cost_operation_variable` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_cap\_out}`$ | `flow_cap_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `where(flow_cap, carrier_out)` — the flow capacity of the carriers a technology produces |
| $`\mathit{source\_scaler}`$ | `source_scaler` over $`\mathcal{N} \times \mathcal{I}`$ — `$source_scaler` — what the source parameters are per: area use, flow capacity, or one |
| $`\mathit{cost\_investment\_source\_cap}`$ | `cost_investment_source_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_investment_source_cap` — the investment cost of source capacity |
| $`\mathit{supply\_cost\_operation\_variable}`$ | `supply_cost_operation_variable` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T} \times \mathcal{K}`$ |
| $`\mathit{curtailment}`$ | `curtailment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `curtailment` — the share of the available source a supply technology leaves unused in a time step; reported |
| $`\mathit{total\_curtailment}`$ | `total_curtailment` over $`\mathcal{N} \times \mathcal{I}`$ — `total_curtailment` — the share of the available source left unused over the whole time; reported |

Upright is what the data supplies — a parameter such as $`\mathrm{source\_eff}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{source\_use}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`source_max`**

```math
\mathit{source\_use}_{n,i,t} \le \mathrm{timestep\_resolution}_{t} \cdot \mathit{source\_cap}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{source\_cap}_{n,i} \text{ exists}
```

**`source_capacity_equals_flow_capacity`**

```math
\mathit{source\_cap}_{n,i} = \mathit{flow\_cap}_{n,i,c} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathit{source\_cap}_{n,i} \text{ exists} \wedge \mathrm{source\_cap\_equals\_flow\_cap}_{n,i}
```

**`balance_supply_no_storage`**

```math
\mathit{flow\_out\_inc\_eff}_{n,i,c,t} = \mathit{source\_use}_{n,i,t} \cdot \mathrm{source\_eff}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_out}_{n,i,c} \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'} \wedge \neg \mathrm{include\_storage}_{n,i}
```

**`source_availability_supply_equals`**

```math
\mathit{source\_use}_{n,i,t} = \mathrm{source\_use\_equals}_{n,i,t} \cdot \mathit{source\_scaler}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{source\_use}_{n,i,t} \text{ exists} \wedge \mathrm{source\_use\_equals}_{n,i,t} \text{ is defined}
```

**`source_availability_supply_max`**

```math
\mathit{source\_use}_{n,i,t} \le \mathrm{source\_use\_max}_{n,i,t} \cdot \mathit{source\_scaler}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{source\_use}_{n,i,t} \text{ exists} \wedge \neg \left( \mathrm{source\_use\_equals}_{n,i,t} \text{ is defined} \right) \wedge \mathrm{source\_use\_max}_{n,i,t} \text{ is defined}
```

**`balance_supply_min_use`**

```math
\mathit{source\_use}_{n,i,t} \ge \mathrm{source\_use\_min}_{n,i,t} \cdot \mathit{source\_scaler}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{source\_use\_min}_{n,i,t} \text{ is defined} \wedge \neg \left( \mathrm{source\_use\_equals}_{n,i,t} \text{ is defined} \right) \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'}
```

#### Definitions

**`flow_cap_out`**

```math
\mathit{flow\_cap\_out}_{n,i,c} = \begin{cases} \mathit{flow\_cap}_{n,i,c} & \text{if } \mathrm{carrier\_out}_{n,i,c} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C}
```

**`source_scaler`**

```math
\mathit{source\_scaler}_{n,i} = \begin{cases} \mathit{area\_use}_{n,i} & \text{if } \mathrm{source\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'} \\ \sum_{c \in \mathcal{C}} \mathit{flow\_cap\_out}_{n,i,c} & \text{if } \mathrm{source\_unit}_{n,i} = \text{'}\mathrm{per\_cap}\text{'} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I}
```

**`cost_investment_source_cap`**

```math
\mathit{cost\_investment\_source\_cap}_{n,i,k} = \mathrm{cost\_source\_cap}_{n,i,k} \cdot \mathit{source\_cap}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`supply_cost_operation_variable`**

```math
\mathit{supply\_cost\_operation\_variable}_{n,i,t,k} = \mathrm{timestep\_weights}_{t} \cdot \mathrm{cost\_source\_use}_{n,i,k,t} \cdot \mathit{source\_use}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T},\ k \in \mathcal{K}
```

**`curtailment`**

```math
\mathit{curtailment}_{n,i,t} = 1 - \frac{\mathit{source\_use}_{n,i,t}}{\mathrm{source\_use\_max}_{n,i,t} \cdot \mathit{source\_scaler}_{n,i}} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T}
```

**`total_curtailment`**

```math
\mathit{total\_curtailment}_{n,i} = 1 - \frac{\sum_{t \in \mathcal{T}} \mathit{source\_use}_{n,i,t}}{\sum_{t \in \mathcal{T}} \mathrm{source\_use\_max}_{n,i,t} \cdot \mathit{source\_scaler}_{n,i}} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I}
```

#### Variable domains

**`source_use`**

```math
\mathit{source\_use}_{n,i,t} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'}
```

**`source_cap`**

```math
\mathrm{source\_cap\_min}_{n,i} \le \mathit{source\_cap}_{n,i} \le \mathrm{source\_cap\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'}
```

#### Assumptions

**`unbounded_source_use_cost`**

```math
\neg \left( \mathrm{cost\_source\_cap}_{n,i,k} < 0 \right) \vee \mathrm{source\_cap\_max}_{n,i} \text{ is defined} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`finite_source_use`**

```math
\neg \left( \mathrm{source\_use\_equals}_{n,i,t} = \infty \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T}
```

**`source_unit_one_of`**

```math
\mathrm{source\_unit}_{n,i} = \text{'}\mathrm{absolute}\text{'} \vee \mathrm{source\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'} \vee \mathrm{source\_unit}_{n,i} = \text{'}\mathrm{per\_cap}\text{'} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{source\_unit}_{n,i} \text{ is defined}
```
<!-- gallery:end -->
