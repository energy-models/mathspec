<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# MILP

An extension of [Calliope in fragments](../index.md). What Calliope's `milp.yaml` adds: whole units bought and run, asynchronous flow, and the capacity minimums the units scale. What it changes in the base is [the MILP patch](../variants/milp.md). The purchase cost is a term of `cost_investment`.

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
  cap_method:
    description: >-
      `cap_method` — `continuous` or `integer`: whether a technology's
      capacity is bought in whole units. Calliope's default is
      `continuous`, which is what a technology with no row reads as
    dims: [nodes, techs]
    dtype: str
  integer_dispatch:
    description: "`integer_dispatch` — whether a unit-bought technology runs in whole units"
    dims: [nodes, techs]
    dtype: bool
  force_async_flow:
    description: "`force_async_flow` — whether a technology may not take in and put out in one time step"
    dims: [nodes, techs]
    dtype: bool
  flow_cap_per_unit:
    description: "`flow_cap_per_unit` — the flow capacity of one unit; given only where set"
    dims: [nodes, techs]
  storage_cap_per_unit:
    description: "`storage_cap_per_unit` — the storage capacity of one unit; given only where set"
    dims: [nodes, techs]
  purchased_units_min:
    description: "`purchased_units_min` — least units bought. Calliope's default is 0, and data prep fills it"
    dims: [nodes, techs]
  purchased_units_max:
    description: "`purchased_units_max` — most units bought. Calliope's default is `.inf`, and data prep fills it"
    dims: [nodes, techs]
  purchased_units_min_systemwide:
    description: "`purchased_units_min_systemwide` — least units of a technology bought over every node"
    dims: [techs]
  purchased_units_max_systemwide:
    description: "`purchased_units_max_systemwide` — most units of a technology bought over every node; given only where set"
    dims: [techs]
  cost_purchase:
    description: "`cost_purchase` — the cost of one unit bought"
    dims: [nodes, techs, costs]
  cost_purchase_per_distance:
    description: "`cost_purchase_per_distance` — the cost of one unit of a link bought, per unit of distance"
    dims: [nodes, techs, costs]

variables:
  purchased_units:
    description: "`purchased_units` — how many units of a technology are bought"
    dims: [nodes, techs]
    where: cap_method == integer
    domain: integer
    bounds: { lower: purchased_units_min, upper: purchased_units_max }
    absence: zero
  operating_units:
    description: "`operating_units` — how many bought units run in a time step"
    dims: [nodes, techs, timesteps]
    where: integer_dispatch AND cap_method == integer
    domain: integer
    bounds: { lower: 0 }
    absence: zero
  async_flow_switch:
    description: "`async_flow_switch` — whether a technology puts out, rather than takes in, in a time step"
    dims: [nodes, techs, timesteps]
    where: force_async_flow
    domain: binary
    absence: zero
  available_flow_cap:
    description: "`available_flow_cap` — the flow capacity in a time step: the whole of it where the technology runs, none where it does not"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_cap AND integer_dispatch AND flow_cap_max AND NOT flow_cap_per_unit
    bounds: { lower: 0 }
    absence: zero

expressions:
  cost_investment_purchase:
    description: "`cost_investment_purchase` — the investment cost of the units bought; a link's cost is split between its two ends"
    dims: [nodes, techs, costs]
    cases:
      transmission:
        when: base_tech == 'transmission'
        expression: (cost_purchase + cost_purchase_per_distance * distance) * purchased_units * 0.5
    otherwise: cost_purchase * purchased_units

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    distance: { dims: [techs] }
    bigM: { dims: [] }
    timestep_resolution: { dims: [timesteps] }
    timestep_weights: { dims: [timesteps] }
    flow_cap_min: { dims: [nodes, techs] }
    flow_cap_max: { dims: [nodes, techs] }
    flow_cap_min_systemwide: { dims: [techs, carriers] }
    flow_out_min_relative: { dims: [nodes, techs, timesteps] }
    flow_out_parasitic_eff: { dims: [nodes, techs, carriers, timesteps] }
    storage_cap_min: { dims: [nodes, techs] }
    storage_cap_max: { dims: [nodes, techs] }
    area_use_min: { dims: [nodes, techs] }
    source_cap_min: { dims: [nodes, techs] }
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_in: { dims: [nodes, techs, carriers, timesteps] }
    storage: { dims: [nodes, techs, timesteps] }
    storage_cap: { dims: [nodes, techs] }
    area_use: { dims: [nodes, techs] }
    source_cap: { dims: [nodes, techs] }
  expressions:
    cost_investment: { dims: [nodes, techs, costs], term: cost_investment_purchase }

constraints:
  unit_commitment_milp:
    description: "`unit_commitment_milp` — at most the units bought run"
    dims: [nodes, techs, timesteps]
    where: operating_units AND purchased_units
    expression: operating_units <= purchased_units
  flow_out_max_milp:
    description: "`flow_out_max_milp` — outflow is at most what the running units can put out"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_out AND operating_units AND flow_cap_per_unit
    expression: flow_out <= operating_units * timestep_resolution * flow_cap_per_unit * flow_out_parasitic_eff
  flow_in_max_milp:
    description: "`flow_in_max_milp` — inflow is at most what the running units can take in"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_in AND operating_units AND flow_cap_per_unit
    expression: flow_in <= operating_units * timestep_resolution * flow_cap_per_unit
  flow_out_min_milp_per_unit:
    description: "`flow_out_min_milp` where `flow_cap_per_unit` is set — outflow is at least the running units' least share"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_out AND operating_units AND flow_out_min_relative AND flow_cap_per_unit
    expression: flow_out >= operating_units * timestep_resolution * flow_cap_per_unit * flow_out_min_relative
  flow_out_min_milp_available:
    description: "`flow_out_min_milp` where the available flow capacity is built — outflow is at least its least share of it"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_out AND operating_units AND flow_out_min_relative AND available_flow_cap
    expression: flow_out >= available_flow_cap * timestep_resolution * flow_out_min_relative
  storage_capacity_units_milp:
    description: "`storage_capacity_units_milp` — storage capacity is the units bought times the capacity of one"
    dims: [nodes, techs]
    where: storage_cap AND purchased_units AND storage_cap_per_unit
    expression: storage_cap == purchased_units * storage_cap_per_unit
  flow_capacity_units_milp:
    description: "`flow_capacity_units_milp` — flow capacity is the units bought times the capacity of one"
    dims: [nodes, techs, carriers]
    where: flow_cap AND purchased_units AND flow_cap_per_unit
    expression: flow_cap == purchased_units * flow_cap_per_unit
  flow_capacity_max_purchase_milp:
    description: "`flow_capacity_max_purchase_milp` where `flow_cap_max` is set — no flow capacity unless a unit is bought"
    dims: [nodes, techs, carriers]
    where: flow_cap AND purchased_units AND flow_cap_max
    expression: flow_cap <= flow_cap_max * purchased_units
  flow_capacity_max_purchase_milp_big_m:
    description: "`flow_capacity_max_purchase_milp` where `flow_cap_max` is not set — the same, with `bigM` for the maximum"
    dims: [nodes, techs, carriers]
    where: flow_cap AND purchased_units AND NOT flow_cap_max
    expression: flow_cap <= bigM * purchased_units
  storage_capacity_max_purchase_milp:
    description: "`storage_capacity_max_purchase_milp` — no storage capacity unless a unit is bought"
    dims: [nodes, techs]
    where: purchased_units AND storage_cap_max
    expression: storage_cap <= storage_cap_max * purchased_units
  unit_capacity_max_systemwide_milp:
    description: "`unit_capacity_max_systemwide_milp` — the units of a technology bought over every node are at most its system-wide maximum"
    dims: [techs]
    where: count(purchased_units, over=nodes) >= 1 AND purchased_units_max_systemwide
    expression: sum(purchased_units, over=nodes) <= purchased_units_max_systemwide
  unit_capacity_min_systemwide_milp:
    description: >-
      `unit_capacity_min_systemwide_milp` — the units of a technology bought
      over every node are at least its system-wide minimum. Calliope builds
      it where the system-wide maximum is set, as here
    dims: [techs]
    where: count(purchased_units, over=nodes) >= 1 AND purchased_units_max_systemwide
    expression: sum(purchased_units, over=nodes) >= purchased_units_min_systemwide
  async_flow_in_milp:
    description: "`async_flow_in_milp` — no inflow in a time step the switch gives to outflow"
    dims: [nodes, techs, timesteps]
    where: async_flow_switch
    expression: sum(flow_in, over=carriers) <= (1 - async_flow_switch) * bigM
  async_flow_out_milp:
    description: "`async_flow_out_milp` — no outflow in a time step the switch gives to inflow"
    dims: [nodes, techs, timesteps]
    where: async_flow_switch
    expression: sum(flow_out, over=carriers) <= async_flow_switch * bigM
  available_flow_cap_continuous:
    description: "`available_flow_cap_continuous` — the available flow capacity is at most the flow capacity"
    dims: [nodes, techs, carriers, timesteps]
    where: available_flow_cap
    expression: available_flow_cap <= flow_cap
  available_flow_cap_binary:
    description: "`available_flow_cap_binary` — the available flow capacity is zero where no unit runs"
    dims: [nodes, techs, carriers, timesteps]
    where: available_flow_cap
    expression: available_flow_cap <= flow_cap_max * operating_units
  available_flow_cap_max_binary_continuous_switch:
    description: "`available_flow_cap_max_binary_continuous_switch` — the available flow capacity is the whole flow capacity where the units run"
    dims: [nodes, techs, carriers, timesteps]
    where: available_flow_cap
    expression: available_flow_cap >= flow_cap + (operating_units - purchased_units) * flow_cap_max
  flow_capacity_minimum:
    description: "`flow_capacity_minimum` where no unit is bought — flow capacity is at least its least"
    dims: [nodes, techs, carriers]
    where: flow_cap AND flow_cap_min AND NOT purchased_units
    expression: flow_cap >= flow_cap_min
  flow_capacity_minimum_purchased:
    description: "`flow_capacity_minimum` where units are bought — flow capacity is at least its least, if a unit is bought"
    dims: [nodes, techs, carriers]
    where: flow_cap AND flow_cap_min AND purchased_units
    expression: flow_cap >= flow_cap_min * purchased_units
  storage_capacity_minimum:
    description: "`storage_capacity_minimum` where no unit is bought — storage capacity is at least its least"
    dims: [nodes, techs]
    where: storage_cap_min AND NOT purchased_units
    expression: storage_cap >= storage_cap_min
  storage_capacity_minimum_purchased:
    description: "`storage_capacity_minimum` where units are bought — storage capacity is at least its least, if a unit is bought"
    dims: [nodes, techs]
    where: storage_cap_min AND purchased_units
    expression: storage_cap >= storage_cap_min * purchased_units
  area_use_minimum:
    description: "`area_use_minimum` where no unit is bought — area use is at least its least"
    dims: [nodes, techs]
    where: area_use_min AND NOT purchased_units
    expression: area_use >= area_use_min
  area_use_minimum_purchased:
    description: "`area_use_minimum` where units are bought — area use is at least its least, if a unit is bought"
    dims: [nodes, techs]
    where: area_use_min AND purchased_units
    expression: area_use >= area_use_min * purchased_units
  source_capacity_minimum:
    description: "`source_capacity_minimum` where no unit is bought — source capacity is at least its least"
    dims: [nodes, techs]
    where: base_tech == 'supply' AND source_cap_min AND NOT purchased_units
    expression: source_cap >= source_cap_min
  source_capacity_minimum_purchased:
    description: "`source_capacity_minimum` where units are bought — source capacity is at least its least, if a unit is bought"
    dims: [nodes, techs]
    where: base_tech == 'supply' AND source_cap_min AND purchased_units
    expression: source_cap >= source_cap_min * purchased_units
  flow_capacity_systemwide_min_purchased:
    description: >-
      `flow_capacity_systemwide_min` where units are bought — the flow
      capacity over every node is at least the system-wide minimum times the
      units bought. The patch narrows the base row to where none are
    dims: [techs, carriers]
    where: count(flow_cap, over=nodes) >= 1 AND flow_cap_min_systemwide AND count(purchased_units, over=nodes) >= 1
    expression: sum(flow_cap, over=nodes) >= flow_cap_min_systemwide * sum(purchased_units, over=nodes)

assumptions:
  distance_only_for_transmission_milp:
    description: Calliope's `distance_only_for_transmission_milp` — only a link sets a per-distance purchase cost
    holds: base_tech == 'transmission' OR NOT cost_purchase_per_distance
  conflicting_flow_caps:
    description: Calliope's `conflicting_flow_caps` — a technology sets a capacity per unit or a capacity range, not both
    holds: NOT ((flow_cap_max OR flow_cap_min) AND flow_cap_per_unit)
  unit_commitment_only_for_units:
    description: Calliope's `unit_commitment_only_for_units` — integer dispatch needs integer units
    holds: NOT integer_dispatch OR cap_method == integer
  conflicting_storage_caps:
    description: Calliope's `conflicting_storage_caps` — a technology sets a storage capacity per unit or a range, not both
    holds: NOT ((storage_cap_max OR storage_cap_min) AND storage_cap_per_unit)
  cap_method_one_of:
    description: Calliope's `one_of` on `cap_method`
    holds: cap_method == continuous OR cap_method == integer
    where: cap_method
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
| $`\mathrm{cap\_method}`$ | `cap_method` over $`\mathcal{N} \times \mathcal{I}`$ — `cap_method` — `continuous` or `integer`: whether a technology's capacity is bought in whole units. Calliope's default is `continuous`, which is what a technology with no row reads as |
| $`\mathrm{integer\_dispatch}`$ | `integer_dispatch` over $`\mathcal{N} \times \mathcal{I}`$ — `integer_dispatch` — whether a unit-bought technology runs in whole units |
| $`\mathrm{force\_async\_flow}`$ | `force_async_flow` over $`\mathcal{N} \times \mathcal{I}`$ — `force_async_flow` — whether a technology may not take in and put out in one time step |
| $`\mathrm{flow\_cap\_per\_unit}`$ | `flow_cap_per_unit` over $`\mathcal{N} \times \mathcal{I}`$ — `flow_cap_per_unit` — the flow capacity of one unit; given only where set |
| $`\mathrm{storage}^{\mathrm{cap,per,unit}}`$ | `storage_cap_per_unit` over $`\mathcal{N} \times \mathcal{I}`$ — `storage_cap_per_unit` — the storage capacity of one unit; given only where set |
| $`\mathrm{purchased\_units\_min}`$ | `purchased_units_min` over $`\mathcal{N} \times \mathcal{I}`$ — `purchased_units_min` — least units bought. Calliope's default is 0, and data prep fills it |
| $`\mathrm{purchased\_units\_max}`$ | `purchased_units_max` over $`\mathcal{N} \times \mathcal{I}`$ — `purchased_units_max` — most units bought. Calliope's default is `.inf`, and data prep fills it |
| $`\mathrm{purchased\_units\_min\_systemwide}`$ | `purchased_units_min_systemwide` over $`\mathcal{I}`$ — `purchased_units_min_systemwide` — least units of a technology bought over every node |
| $`\mathrm{purchased\_units\_max\_systemwide}`$ | `purchased_units_max_systemwide` over $`\mathcal{I}`$ — `purchased_units_max_systemwide` — most units of a technology bought over every node; given only where set |
| $`\mathrm{cost\_purchase}`$ | `cost_purchase` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_purchase` — the cost of one unit bought |
| $`\mathrm{cost\_purchase\_per\_distance}`$ | `cost_purchase_per_distance` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_purchase_per_distance` — the cost of one unit of a link bought, per unit of distance |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{purchased\_units}`$ | `purchased_units` over $`\mathcal{N} \times \mathcal{I}`$ — `purchased_units` — how many units of a technology are bought |
| $`\mathit{operating\_units}`$ | `operating_units` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `operating_units` — how many bought units run in a time step |
| $`\mathit{async\_flow\_switch}`$ | `async_flow_switch` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `async_flow_switch` — whether a technology puts out, rather than takes in, in a time step |
| $`\mathit{available\_flow\_cap}`$ | `available_flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `available_flow_cap` — the flow capacity in a time step: the whole of it where the technology runs, none where it does not |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{distance}`$ | `distance` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{bigM}`$ | `bigM` (scalar), data another file declares |
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{flow\_cap\_min}`$ | `flow_cap_min` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{flow\_cap\_max}`$ | `flow_cap_max` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{flow\_cap\_min\_systemwide}`$ | `flow_cap_min_systemwide` over $`\mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{flow\_out\_min\_relative}`$ | `flow_out_min_relative` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$, data another file declares |
| $`\mathrm{flow\_out\_parasitic\_eff}`$ | `flow_out_parasitic_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, data another file declares |
| $`\mathrm{storage}^{\mathrm{cap,min}}`$ | `storage_cap_min` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{storage}^{\mathrm{cap,max}}`$ | `storage_cap_max` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{area\_use\_min}`$ | `area_use_min` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{source\_cap\_min}`$ | `source_cap_min` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_in}`$ | `flow_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{storage}`$ | `storage` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ |
| $`\mathit{storage}^{\mathrm{cap}}`$ | `storage_cap` over $`\mathcal{N} \times \mathcal{I}`$ |
| $`\mathit{area\_use}`$ | `area_use` over $`\mathcal{N} \times \mathcal{I}`$ |
| $`\mathit{source\_cap}`$ | `source_cap` over $`\mathcal{N} \times \mathcal{I}`$ |
| $`\mathit{cost\_investment}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `cost_investment_purchase` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{cost\_investment\_purchase}`$ | `cost_investment_purchase` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_investment_purchase` — the investment cost of the units bought; a link's cost is split between its two ends |

Upright is what the data supplies — a parameter such as $`\mathrm{cap\_method}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{purchased\_units}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`unit_commitment_milp`**

```math
\mathit{operating\_units}_{n,i,t} \le \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{operating\_units}_{n,i,t} \text{ exists} \wedge \mathit{purchased\_units}_{n,i} \text{ exists}
```

**`flow_out_max_milp`**

```math
\mathit{flow\_out}_{n,i,c,t} \le \mathit{operating\_units}_{n,i,t} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_cap\_per\_unit}_{n,i} \cdot \mathrm{flow\_out\_parasitic\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_out}_{n,i,c,t} \text{ exists} \wedge \mathit{operating\_units}_{n,i,t} \text{ exists} \wedge \mathrm{flow\_cap\_per\_unit}_{n,i} \text{ is defined}
```

**`flow_in_max_milp`**

```math
\mathit{flow\_in}_{n,i,c,t} \le \mathit{operating\_units}_{n,i,t} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_cap\_per\_unit}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_in}_{n,i,c,t} \text{ exists} \wedge \mathit{operating\_units}_{n,i,t} \text{ exists} \wedge \mathrm{flow\_cap\_per\_unit}_{n,i} \text{ is defined}
```

**`flow_out_min_milp_per_unit`**

```math
\mathit{flow\_out}_{n,i,c,t} \ge \mathit{operating\_units}_{n,i,t} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_cap\_per\_unit}_{n,i} \cdot \mathrm{flow\_out\_min\_relative}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_out}_{n,i,c,t} \text{ exists} \wedge \mathit{operating\_units}_{n,i,t} \text{ exists} \wedge \mathrm{flow\_out\_min\_relative}_{n,i,t} \text{ is defined} \wedge \mathrm{flow\_cap\_per\_unit}_{n,i} \text{ is defined}
```

**`flow_out_min_milp_available`**

```math
\mathit{flow\_out}_{n,i,c,t} \ge \mathit{available\_flow\_cap}_{n,i,c,t} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_out\_min\_relative}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_out}_{n,i,c,t} \text{ exists} \wedge \mathit{operating\_units}_{n,i,t} \text{ exists} \wedge \mathrm{flow\_out\_min\_relative}_{n,i,t} \text{ is defined} \wedge \mathit{available\_flow\_cap}_{n,i,c,t} \text{ exists}
```

**`storage_capacity_units_milp`**

```math
\mathit{storage}^{\mathrm{cap}}_{n,i} = \mathit{purchased\_units}_{n,i} \cdot \mathrm{storage}^{\mathrm{cap,per,unit}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathit{storage}^{\mathrm{cap}}_{n,i} \text{ exists} \wedge \mathit{purchased\_units}_{n,i} \text{ exists} \wedge \mathrm{storage}^{\mathrm{cap,per,unit}}_{n,i} \text{ is defined}
```

**`flow_capacity_units_milp`**

```math
\mathit{flow\_cap}_{n,i,c} = \mathit{purchased\_units}_{n,i} \cdot \mathrm{flow\_cap\_per\_unit}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathit{purchased\_units}_{n,i} \text{ exists} \wedge \mathrm{flow\_cap\_per\_unit}_{n,i} \text{ is defined}
```

**`flow_capacity_max_purchase_milp`**

```math
\mathit{flow\_cap}_{n,i,c} \le \mathrm{flow\_cap\_max}_{n,i} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathit{purchased\_units}_{n,i} \text{ exists} \wedge \mathrm{flow\_cap\_max}_{n,i} \text{ is defined}
```

**`flow_capacity_max_purchase_milp_big_m`**

```math
\mathit{flow\_cap}_{n,i,c} \le \mathrm{bigM} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathit{purchased\_units}_{n,i} \text{ exists} \wedge \neg \left( \mathrm{flow\_cap\_max}_{n,i} \text{ is defined} \right)
```

**`storage_capacity_max_purchase_milp`**

```math
\mathit{storage}^{\mathrm{cap}}_{n,i} \le \mathrm{storage}^{\mathrm{cap,max}}_{n,i} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathit{purchased\_units}_{n,i} \text{ exists} \wedge \mathrm{storage}^{\mathrm{cap,max}}_{n,i} \text{ is defined}
```

**`unit_capacity_max_systemwide_milp`**

```math
\sum_{n \in \mathcal{N}} \mathit{purchased\_units}_{n,i} \le \mathrm{purchased\_units\_max\_systemwide}_{i} \qquad \forall\, i \in \mathcal{I} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathit{purchased\_units}_{n,i} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{purchased\_units\_max\_systemwide}_{i} \text{ is defined}
```

**`unit_capacity_min_systemwide_milp`**

```math
\sum_{n \in \mathcal{N}} \mathit{purchased\_units}_{n,i} \ge \mathrm{purchased\_units\_min\_systemwide}_{i} \qquad \forall\, i \in \mathcal{I} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathit{purchased\_units}_{n,i} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{purchased\_units\_max\_systemwide}_{i} \text{ is defined}
```

**`async_flow_in_milp`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_in}_{n,i,c,t} \le \left( 1 - \mathit{async\_flow\_switch}_{n,i,t} \right) \cdot \mathrm{bigM} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{async\_flow\_switch}_{n,i,t} \text{ exists}
```

**`async_flow_out_milp`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_out}_{n,i,c,t} \le \mathit{async\_flow\_switch}_{n,i,t} \cdot \mathrm{bigM} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{async\_flow\_switch}_{n,i,t} \text{ exists}
```

**`available_flow_cap_continuous`**

```math
\mathit{available\_flow\_cap}_{n,i,c,t} \le \mathit{flow\_cap}_{n,i,c} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{available\_flow\_cap}_{n,i,c,t} \text{ exists}
```

**`available_flow_cap_binary`**

```math
\mathit{available\_flow\_cap}_{n,i,c,t} \le \mathrm{flow\_cap\_max}_{n,i} \cdot \mathit{operating\_units}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{available\_flow\_cap}_{n,i,c,t} \text{ exists}
```

**`available_flow_cap_max_binary_continuous_switch`**

```math
\mathit{available\_flow\_cap}_{n,i,c,t} \ge \mathit{flow\_cap}_{n,i,c} + \left( \mathit{operating\_units}_{n,i,t} - \mathit{purchased\_units}_{n,i} \right) \cdot \mathrm{flow\_cap\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{available\_flow\_cap}_{n,i,c,t} \text{ exists}
```

**`flow_capacity_minimum`**

```math
\mathit{flow\_cap}_{n,i,c} \ge \mathrm{flow\_cap\_min}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathrm{flow\_cap\_min}_{n,i} \text{ is defined} \wedge \neg \left( \mathit{purchased\_units}_{n,i} \text{ exists} \right)
```

**`flow_capacity_minimum_purchased`**

```math
\mathit{flow\_cap}_{n,i,c} \ge \mathrm{flow\_cap\_min}_{n,i} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathrm{flow\_cap\_min}_{n,i} \text{ is defined} \wedge \mathit{purchased\_units}_{n,i} \text{ exists}
```

**`storage_capacity_minimum`**

```math
\mathit{storage}^{\mathrm{cap}}_{n,i} \ge \mathrm{storage}^{\mathrm{cap,min}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{storage}^{\mathrm{cap,min}}_{n,i} \text{ is defined} \wedge \neg \left( \mathit{purchased\_units}_{n,i} \text{ exists} \right)
```

**`storage_capacity_minimum_purchased`**

```math
\mathit{storage}^{\mathrm{cap}}_{n,i} \ge \mathrm{storage}^{\mathrm{cap,min}}_{n,i} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{storage}^{\mathrm{cap,min}}_{n,i} \text{ is defined} \wedge \mathit{purchased\_units}_{n,i} \text{ exists}
```

**`area_use_minimum`**

```math
\mathit{area\_use}_{n,i} \ge \mathrm{area\_use\_min}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{area\_use\_min}_{n,i} \text{ is defined} \wedge \neg \left( \mathit{purchased\_units}_{n,i} \text{ exists} \right)
```

**`area_use_minimum_purchased`**

```math
\mathit{area\_use}_{n,i} \ge \mathrm{area\_use\_min}_{n,i} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{area\_use\_min}_{n,i} \text{ is defined} \wedge \mathit{purchased\_units}_{n,i} \text{ exists}
```

**`source_capacity_minimum`**

```math
\mathit{source\_cap}_{n,i} \ge \mathrm{source\_cap\_min}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'} \wedge \mathrm{source\_cap\_min}_{n,i} \text{ is defined} \wedge \neg \left( \mathit{purchased\_units}_{n,i} \text{ exists} \right)
```

**`source_capacity_minimum_purchased`**

```math
\mathit{source\_cap}_{n,i} \ge \mathrm{source\_cap\_min}_{n,i} \cdot \mathit{purchased\_units}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'} \wedge \mathrm{source\_cap\_min}_{n,i} \text{ is defined} \wedge \mathit{purchased\_units}_{n,i} \text{ exists}
```

**`flow_capacity_systemwide_min_purchased`**

```math
\sum_{n \in \mathcal{N}} \mathit{flow\_cap}_{n,i,c} \ge \mathrm{flow\_cap\_min\_systemwide}_{i,c} \cdot \left( \sum_{n \in \mathcal{N}} \mathit{purchased\_units}_{n,i} \right) \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{flow\_cap\_min\_systemwide}_{i,c} \text{ is defined} \wedge \lvert \{ n \in \mathcal{N} \,:\, \mathit{purchased\_units}_{n,i} \text{ exists} \} \rvert \ge 1
```

#### Definitions

**`cost_investment_purchase`**

```math
\mathit{cost\_investment\_purchase}_{n,i,k} = \begin{cases} \left( \mathrm{cost\_purchase}_{n,i,k} + \mathrm{cost\_purchase\_per\_distance}_{n,i,k} \cdot \mathrm{distance}_{i} \right) \cdot \mathit{purchased\_units}_{n,i} \cdot 0.5 & \text{if } \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \\ \mathrm{cost\_purchase}_{n,i,k} \cdot \mathit{purchased\_units}_{n,i} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

#### Variable domains

**`purchased_units`**

```math
\mathrm{purchased\_units\_min}_{n,i} \le \mathit{purchased\_units}_{n,i} \le \mathrm{purchased\_units\_max}_{n,i}, \mathit{purchased\_units}_{n,i} \in \mathbb{Z} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{cap\_method}_{n,i} = \text{'}\mathrm{integer}\text{'}
```

**`operating_units`**

```math
\mathit{operating\_units}_{n,i,t} \ge 0, \mathit{operating\_units}_{n,i,t} \in \mathbb{Z} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{integer\_dispatch}_{n,i} \wedge \mathrm{cap\_method}_{n,i} = \text{'}\mathrm{integer}\text{'}
```

**`async_flow_switch`**

```math
\mathit{async\_flow\_switch}_{n,i,t} \in \{0, 1\} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{force\_async\_flow}_{n,i}
```

**`available_flow_cap`**

```math
\mathit{available\_flow\_cap}_{n,i,c,t} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathrm{integer\_dispatch}_{n,i} \wedge \mathrm{flow\_cap\_max}_{n,i} \text{ is defined} \wedge \neg \left( \mathrm{flow\_cap\_per\_unit}_{n,i} \text{ is defined} \right)
```

#### Assumptions

**`distance_only_for_transmission_milp`**

```math
\mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \vee \neg \left( \mathrm{cost\_purchase\_per\_distance}_{n,i,k} \text{ is defined} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`conflicting_flow_caps`**

```math
\neg \left( \left( \mathrm{flow\_cap\_max}_{n,i} \text{ is defined} \vee \mathrm{flow\_cap\_min}_{n,i} \text{ is defined} \right) \wedge \mathrm{flow\_cap\_per\_unit}_{n,i} \text{ is defined} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I}
```

**`unit_commitment_only_for_units`**

```math
\neg \mathrm{integer\_dispatch}_{n,i} \vee \mathrm{cap\_method}_{n,i} = \text{'}\mathrm{integer}\text{'} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I}
```

**`conflicting_storage_caps`**

```math
\neg \left( \left( \mathrm{storage}^{\mathrm{cap,max}}_{n,i} \text{ is defined} \vee \mathrm{storage}^{\mathrm{cap,min}}_{n,i} \text{ is defined} \right) \wedge \mathrm{storage}^{\mathrm{cap,per,unit}}_{n,i} \text{ is defined} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I}
```

**`cap_method_one_of`**

```math
\mathrm{cap\_method}_{n,i} = \text{'}\mathrm{continuous}\text{'} \vee \mathrm{cap\_method}_{n,i} = \text{'}\mathrm{integer}\text{'} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{cap\_method}_{n,i} \text{ is defined}
```
<!-- gallery:end -->
