<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Flows

One of the base fragments of [Calliope in fragments](index.md). The core of every technology: flow capacity, outflow and inflow, their efficiencies, their limits and ramping. It adds the flows to the balance and their costs to the three cost sums.

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

relations:
  link_from:
    description: >-
      `link_from` — the node a transmission technology links from. Calliope
      reads it as `map_dim(nodes, link_from)`, a mask over technology and
      node, which is the relation's own row test
    key: [techs, nodes]
  link_to:
    description: >-
      `link_to` — the node a transmission technology links to, read as
      `link_from` is
    key: [techs, nodes]

parameters:
  base_tech:
    description: >-
      `base_tech` — the abstract class a technology derives from: demand,
      supply, conversion, storage or transmission
    dims: [techs]
    dtype: str
  carrier_in:
    description: "`carrier_in` — whether a technology consumes a carrier at a node"
    dims: [nodes, techs, carriers]
    dtype: bool
  carrier_out:
    description: "`carrier_out` — whether a technology produces a carrier at a node"
    dims: [nodes, techs, carriers]
    dtype: bool
  include_storage:
    description: >-
      `include_storage` — whether a technology that is not a storage one
      carries a store all the same
    dims: [nodes, techs]
    dtype: bool
  one_way:
    description: "`one_way` — whether a transmission technology carries flow only from `link_from` to `link_to`"
    dims: [techs]
    dtype: bool
  flow_cap_min:
    description: >-
      `flow_cap_min` — least flow capacity. Calliope's default is 0; a bound
      has a row wherever the variable has one, so data prep fills it
    dims: [nodes, techs]
  flow_cap_max:
    description: >-
      `flow_cap_max` — most flow capacity. Calliope's default is `.inf`,
      which data prep fills, and a `where` reads as not given
    dims: [nodes, techs]
  flow_cap_min_systemwide:
    description: "`flow_cap_min_systemwide` — least flow capacity of a technology over every node; given only where set"
    dims: [techs, carriers]
  flow_cap_max_systemwide:
    description: "`flow_cap_max_systemwide` — most flow capacity of a technology over every node; given only where set"
    dims: [techs, carriers]
  flow_out_min_relative:
    description: "`flow_out_min_relative` — least outflow, per unit of flow capacity; given only where set"
    dims: [nodes, techs, timesteps]
  flow_out_eff:
    description: "`flow_out_eff` — the share of flow that leaves a technology as outflow. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs, carriers, timesteps]
  flow_in_eff:
    description: "`flow_in_eff` — the share of inflow that enters a technology. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs, carriers, timesteps]
  flow_out_parasitic_eff:
    description: "`flow_out_parasitic_eff` — what is left after the plant's own use. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs, carriers, timesteps]
  flow_out_eff_per_distance:
    description: "`flow_out_eff_per_distance` — the outflow efficiency of a link per unit of distance. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs, carriers, timesteps]
  flow_in_eff_per_distance:
    description: "`flow_in_eff_per_distance` — the inflow efficiency of a link per unit of distance. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs, carriers, timesteps]
  distance:
    description: >-
      `distance` — the length of a transmission link. Calliope's default is
      1, which data prep fills, where it does not derive one from the
      coordinates of the nodes
    dims: [techs]
  flow_ramping:
    description: "`flow_ramping` — the most flow may change in an hour, per unit of flow capacity; given only where set"
    dims: [nodes, techs]
  cost_flow_cap:
    description: "`cost_flow_cap` — the cost of one unit of flow capacity"
    dims: [nodes, techs, costs]
  cost_flow_cap_per_distance:
    description: "`cost_flow_cap_per_distance` — the cost of one unit of flow capacity per unit of link distance"
    dims: [nodes, techs, costs]
  cost_flow_out:
    description: "`cost_flow_out` — the cost of one unit of outflow"
    dims: [nodes, techs, costs, timesteps]
  cost_flow_in:
    description: "`cost_flow_in` — the cost of one unit of inflow"
    dims: [nodes, techs, costs, timesteps]
  cost_om_annual:
    description: "`cost_om_annual` — the annual cost of one unit of flow capacity"
    dims: [nodes, techs, costs]

variables:
  flow_cap:
    description: "`flow_cap` — the flow capacity of a technology, its nominal or nameplate capacity"
    dims: [nodes, techs, carriers]
    where: carrier_in OR carrier_out
    bounds: { lower: flow_cap_min, upper: flow_cap_max }
    absence: zero
  flow_out:
    description: >-
      `flow_out` — the outflow of a technology in a time step. A one-way link
      has none at the node it links from
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_out AND NOT (one_way AND link_from)
    bounds: { lower: 0 }
    absence: zero
  flow_in:
    description: >-
      `flow_in` — the inflow to a technology in a time step. A one-way link
      has none at the node it links to
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_in AND NOT (one_way AND link_to)
    bounds: { lower: 0 }
    absence: zero

expressions:
  flow_out_inc_eff:
    description: "`flow_out_inc_eff` — outflow before the losses on the way out"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      transmission:
        when: base_tech == 'transmission'
        expression: flow_out / (flow_out_eff * flow_out_parasitic_eff * flow_out_eff_per_distance ** distance)
    otherwise: flow_out / (flow_out_eff * flow_out_parasitic_eff)
  flow_in_inc_eff:
    description: "`flow_in_inc_eff` — inflow after the losses on the way in"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      transmission:
        when: base_tech == 'transmission'
        expression: flow_in * flow_in_eff * flow_in_eff_per_distance ** distance
    otherwise: flow_in * flow_in_eff
  ramping_flow:
    description: >-
      `$flow` of `ramping_up` and `ramping_down` — the flow a ramping limit
      holds, per hour: outflow, inflow, or their difference where a
      technology has both
    dims: [nodes, techs, carriers, timesteps]
    cases:
      out:
        when: carrier_out AND NOT carrier_in
        expression: flow_out / timestep_resolution
      in:
        when: carrier_in AND NOT carrier_out
        expression: flow_in / timestep_resolution
    otherwise: (flow_out - flow_in) / timestep_resolution
  cost_flow_cap_sum:
    description: >-
      `$cost_sum` of `cost_investment_flow_cap` — what one unit of flow
      capacity costs; a link's cost is split between its two ends
    dims: [nodes, techs, costs]
    cases:
      transmission:
        when: base_tech == 'transmission'
        expression: (cost_flow_cap + cost_flow_cap_per_distance * distance) * 0.5
    otherwise: cost_flow_cap
  cost_investment_flow_cap:
    description: "`cost_investment_flow_cap` — the investment cost of flow capacity"
    expression: cost_flow_cap_sum * flow_cap
  flows_carrier_flow: sum(flow_out, over=techs) - sum(flow_in, over=techs)
  flows_cost_investment: sum(cost_investment_flow_cap, over=carriers)
  flows_cost_operation_variable: >-
    timestep_weights * (sum(cost_flow_out * flow_out, over=carriers) + sum(cost_flow_in * flow_in, over=carriers))
  flows_cost_operation_fixed: annualisation_weight * sum(cost_om_annual * flow_cap, over=carriers)

given:
  parameters:
    timestep_resolution: { dims: [timesteps] }
    timestep_weights: { dims: [timesteps] }
  expressions:
    annualisation_weight:
      description: the share of a year the modelled time steps stand for
      dims: []
    carrier_flow: { dims: [nodes, carriers, timesteps], term: flows_carrier_flow }
    cost_investment: { dims: [nodes, techs, costs], term: flows_cost_investment }
    cost_operation_variable: { dims: [nodes, techs, costs, timesteps], term: flows_cost_operation_variable }
    cost_operation_fixed: { dims: [nodes, techs, costs], term: flows_cost_operation_fixed }

constraints:
  flow_out_max:
    description: "`flow_out_max` — outflow is at most the flow capacity over the time step, less the plant's own use"
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_out
    expression: flow_out <= flow_cap * timestep_resolution * flow_out_parasitic_eff
  flow_out_min:
    description: "`flow_out_min` — outflow is at least its least share of the flow capacity"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_cap AND flow_out_min_relative
    expression: flow_out >= flow_cap * timestep_resolution * flow_out_min_relative
  flow_in_max:
    description: "`flow_in_max` — inflow is at most the flow capacity over the time step"
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_in
    expression: flow_in <= flow_cap * timestep_resolution
  flow_capacity_systemwide_max:
    description: "`flow_capacity_systemwide_max` — the flow capacity of a technology over every node is at most its system-wide maximum"
    dims: [techs, carriers]
    where: count(flow_cap, over=nodes) >= 1 AND flow_cap_max_systemwide
    expression: sum(flow_cap, over=nodes) <= flow_cap_max_systemwide
  flow_capacity_systemwide_min:
    description: "`flow_capacity_systemwide_min` — the flow capacity of a technology over every node is at least its system-wide minimum"
    dims: [techs, carriers]
    where: count(flow_cap, over=nodes) >= 1 AND flow_cap_min_systemwide
    expression: sum(flow_cap, over=nodes) >= flow_cap_min_systemwide
  ramping_up:
    description: "`ramping_up` — flow rises from one time step to the next by at most its ramping share of the flow capacity"
    dims: [nodes, techs, carriers, timesteps]
    where: (carrier_in OR carrier_out) AND flow_ramping AND position(timesteps) > 0
    expression: ramping_flow - shift(ramping_flow, along=timesteps, offset=1) <= flow_ramping * flow_cap
  ramping_down:
    description: "`ramping_down` — flow falls from one time step to the next by at most its ramping share of the flow capacity"
    dims: [nodes, techs, carriers, timesteps]
    where: (carrier_in OR carrier_out) AND flow_ramping AND position(timesteps) > 0
    expression: -1 * flow_ramping * flow_cap <= ramping_flow - shift(ramping_flow, along=timesteps, offset=1)

assumptions:
  must_have_base:
    description: Calliope's `must_have_base` — every technology derives from an abstract class
    holds: base_tech
  base_tech_one_of:
    description: Calliope's `one_of` on `base_tech`
    holds: >-
      base_tech == 'demand' OR base_tech == 'supply' OR base_tech == 'conversion'
      OR base_tech == 'storage' OR base_tech == 'transmission'
  distance_only_for_transmission:
    description: >-
      Calliope's `distance_only_for_transmission` — only a link sets a
      distance or a per-distance value. Data prep fills the defaults, so a
      technology that is not a link keeps them
    holds: >-
      distance == 1 AND flow_in_eff_per_distance == 1
      AND flow_out_eff_per_distance == 1 AND NOT cost_flow_cap_per_distance
    where: NOT base_tech == 'transmission'
  unbounded_flow_cap_cost:
    description: Calliope's `unbounded_flow_cap_cost` — a negative flow capacity cost needs a finite maximum
    holds: NOT cost_flow_cap < 0 OR flow_cap_max
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` with $`\mathrm{link\_from} \subseteq \mathcal{I} \times \mathcal{N},\ \mathrm{link\_to} \subseteq \mathcal{I} \times \mathcal{N}`$ — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` with $`\mathrm{link\_from} \subseteq \mathcal{I} \times \mathcal{N},\ \mathrm{link\_to} \subseteq \mathcal{I} \times \mathcal{N}`$ — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$ — `base_tech` — the abstract class a technology derives from: demand, supply, conversion, storage or transmission |
| $`\mathrm{carrier\_in}`$ | `carrier_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `carrier_in` — whether a technology consumes a carrier at a node |
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `carrier_out` — whether a technology produces a carrier at a node |
| $`\mathrm{include\_storage}`$ | `include_storage` over $`\mathcal{N} \times \mathcal{I}`$ — `include_storage` — whether a technology that is not a storage one carries a store all the same |
| $`\mathrm{one\_way}`$ | `one_way` over $`\mathcal{I}`$ — `one_way` — whether a transmission technology carries flow only from `link_from` to `link_to` |
| $`\mathrm{flow\_cap\_min}`$ | `flow_cap_min` over $`\mathcal{N} \times \mathcal{I}`$ — `flow_cap_min` — least flow capacity. Calliope's default is 0; a bound has a row wherever the variable has one, so data prep fills it |
| $`\mathrm{flow\_cap\_max}`$ | `flow_cap_max` over $`\mathcal{N} \times \mathcal{I}`$ — `flow_cap_max` — most flow capacity. Calliope's default is `.inf`, which data prep fills, and a `where` reads as not given |
| $`\mathrm{flow\_cap\_min\_systemwide}`$ | `flow_cap_min_systemwide` over $`\mathcal{I} \times \mathcal{C}`$ — `flow_cap_min_systemwide` — least flow capacity of a technology over every node; given only where set |
| $`\mathrm{flow\_cap\_max\_systemwide}`$ | `flow_cap_max_systemwide` over $`\mathcal{I} \times \mathcal{C}`$ — `flow_cap_max_systemwide` — most flow capacity of a technology over every node; given only where set |
| $`\mathrm{flow\_out\_min\_relative}`$ | `flow_out_min_relative` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `flow_out_min_relative` — least outflow, per unit of flow capacity; given only where set |
| $`\mathrm{flow\_out\_eff}`$ | `flow_out_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_eff` — the share of flow that leaves a technology as outflow. Calliope's default is 1, and data prep fills it |
| $`\mathrm{flow\_in\_eff}`$ | `flow_in_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_in_eff` — the share of inflow that enters a technology. Calliope's default is 1, and data prep fills it |
| $`\mathrm{flow\_out\_parasitic\_eff}`$ | `flow_out_parasitic_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_parasitic_eff` — what is left after the plant's own use. Calliope's default is 1, and data prep fills it |
| $`\mathrm{flow\_out\_eff\_per\_distance}`$ | `flow_out_eff_per_distance` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_eff_per_distance` — the outflow efficiency of a link per unit of distance. Calliope's default is 1, and data prep fills it |
| $`\mathrm{flow\_in\_eff\_per\_distance}`$ | `flow_in_eff_per_distance` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_in_eff_per_distance` — the inflow efficiency of a link per unit of distance. Calliope's default is 1, and data prep fills it |
| $`\mathrm{distance}`$ | `distance` over $`\mathcal{I}`$ — `distance` — the length of a transmission link. Calliope's default is 1, which data prep fills, where it does not derive one from the coordinates of the nodes |
| $`\mathrm{flow\_ramping}`$ | `flow_ramping` over $`\mathcal{N} \times \mathcal{I}`$ — `flow_ramping` — the most flow may change in an hour, per unit of flow capacity; given only where set |
| $`\mathrm{cost\_flow\_cap}`$ | `cost_flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_flow_cap` — the cost of one unit of flow capacity |
| $`\mathrm{cost\_flow\_cap\_per\_distance}`$ | `cost_flow_cap_per_distance` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_flow_cap_per_distance` — the cost of one unit of flow capacity per unit of link distance |
| $`\mathrm{cost\_flow\_out}`$ | `cost_flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$ — `cost_flow_out` — the cost of one unit of outflow |
| $`\mathrm{cost\_flow\_in}`$ | `cost_flow_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$ — `cost_flow_in` — the cost of one unit of inflow |
| $`\mathrm{cost\_om\_annual}`$ | `cost_om_annual` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_om_annual` — the annual cost of one unit of flow capacity |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `flow_cap` — the flow capacity of a technology, its nominal or nameplate capacity |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out` — the outflow of a technology in a time step. A one-way link has none at the node it links from |
| $`\mathit{flow\_in}`$ | `flow_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_in` — the inflow to a technology in a time step. A one-way link has none at the node it links to |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{annualisation\_weight}`$ | `annualisation_weight` (scalar), an expression another file defines — the share of a year the modelled time steps stand for |
| $`\mathit{carrier\_flow}`$ | `carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$, an expression this file adds `flows_carrier_flow` to |
| $`\mathit{cost\_investment}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `flows_cost_investment` to |
| $`\mathit{cost\_operation\_variable}`$ | `cost_operation_variable` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$, an expression this file adds `flows_cost_operation_variable` to |
| $`\mathit{cost\_operation\_fixed}`$ | `cost_operation_fixed` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `flows_cost_operation_fixed` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_inc_eff` — outflow before the losses on the way out |
| $`\mathit{flow\_in\_inc\_eff}`$ | `flow_in_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_in_inc_eff` — inflow after the losses on the way in |
| $`\mathit{ramping\_flow}`$ | `ramping_flow` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `$flow` of `ramping_up` and `ramping_down` — the flow a ramping limit holds, per hour: outflow, inflow, or their difference where a technology has both |
| $`\mathrm{cost\_flow\_cap\_sum}`$ | `cost_flow_cap_sum` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `$cost_sum` of `cost_investment_flow_cap` — what one unit of flow capacity costs; a link's cost is split between its two ends |
| $`\mathit{cost\_investment\_flow\_cap}`$ | `cost_investment_flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{K}`$ — `cost_investment_flow_cap` — the investment cost of flow capacity |
| $`\mathit{flows\_carrier\_flow}`$ | `flows_carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flows\_cost\_investment}`$ | `flows_cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ |
| $`\mathit{flows\_cost\_operation\_variable}`$ | `flows_cost_operation_variable` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K} \times \mathcal{T}`$ |
| $`\mathit{flows\_cost\_operation\_fixed}`$ | `flows_cost_operation_fixed` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ |

Upright is what the data supplies — a parameter such as $`\mathrm{base\_tech}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{flow\_cap}`$. An index is italic too, being what a quantifier chooses, and a set is script.

$`\mathrm{pos}(t)`$ denotes where index $`t`$ sits along its dimension's own order — the order `shift` steps along, not the order labels sort in — counted from $`0`$. The index itself stays the coordinate, so $`t`$ compares against labels and $`\mathrm{pos}(t)`$ against positions.

#### Subject to

**`flow_out_max`**

```math
\mathit{flow\_out}_{n,i,c,t} \le \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_out\_parasitic\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_out}_{n,i,c}
```

**`flow_out_min`**

```math
\mathit{flow\_out}_{n,i,c,t} \ge \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_out\_min\_relative}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathrm{flow\_out\_min\_relative}_{n,i,t} \text{ is defined}
```

**`flow_in_max`**

```math
\mathit{flow\_in}_{n,i,c,t} \le \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{timestep\_resolution}_{t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_in}_{n,i,c}
```

**`flow_capacity_systemwide_max`**

```math
\sum_{n \in \mathcal{N}} \mathit{flow\_cap}_{n,i,c} \le \mathrm{flow\_cap\_max\_systemwide}_{i,c} \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{flow\_cap\_max\_systemwide}_{i,c} \text{ is defined}
```

**`flow_capacity_systemwide_min`**

```math
\sum_{n \in \mathcal{N}} \mathit{flow\_cap}_{n,i,c} \ge \mathrm{flow\_cap\_min\_systemwide}_{i,c} \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{flow\_cap\_min\_systemwide}_{i,c} \text{ is defined}
```

**`ramping_up`**

```math
\mathit{ramping\_flow}_{n,i,c,t} - \mathit{ramping\_flow}_{n,i,c,t - 1} \le \mathrm{flow\_ramping}_{n,i} \cdot \mathit{flow\_cap}_{n,i,c} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \left( \mathrm{carrier\_in}_{n,i,c} \vee \mathrm{carrier\_out}_{n,i,c} \right) \wedge \mathrm{flow\_ramping}_{n,i} \text{ is defined} \wedge \mathrm{pos}(t) > 0
```

**`ramping_down`**

```math
-1 \cdot \mathrm{flow\_ramping}_{n,i} \cdot \mathit{flow\_cap}_{n,i,c} \le \mathit{ramping\_flow}_{n,i,c,t} - \mathit{ramping\_flow}_{n,i,c,t - 1} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \left( \mathrm{carrier\_in}_{n,i,c} \vee \mathrm{carrier\_out}_{n,i,c} \right) \wedge \mathrm{flow\_ramping}_{n,i} \text{ is defined} \wedge \mathrm{pos}(t) > 0
```

#### Definitions

**`flow_out_inc_eff`**

```math
\mathit{flow\_out\_inc\_eff}_{n,i,c,t} = \begin{cases} \frac{\mathit{flow\_out}_{n,i,c,t}}{\mathrm{flow\_out\_eff}_{n,i,c,t} \cdot \mathrm{flow\_out\_parasitic\_eff}_{n,i,c,t} \cdot \mathrm{flow\_out\_eff\_per\_distance}_{n,i,c,t}^{\mathrm{distance}_{i}}} & \text{if } \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \\ \frac{\mathit{flow\_out}_{n,i,c,t}}{\mathrm{flow\_out\_eff}_{n,i,c,t} \cdot \mathrm{flow\_out\_parasitic\_eff}_{n,i,c,t}} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`flow_in_inc_eff`**

```math
\mathit{flow\_in\_inc\_eff}_{n,i,c,t} = \begin{cases} \mathit{flow\_in}_{n,i,c,t} \cdot \mathrm{flow\_in\_eff}_{n,i,c,t} \cdot \mathrm{flow\_in\_eff\_per\_distance}_{n,i,c,t}^{\mathrm{distance}_{i}} & \text{if } \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \\ \mathit{flow\_in}_{n,i,c,t} \cdot \mathrm{flow\_in\_eff}_{n,i,c,t} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`ramping_flow`**

```math
\mathit{ramping\_flow}_{n,i,c,t} = \begin{cases} \frac{\mathit{flow\_out}_{n,i,c,t}}{\mathrm{timestep\_resolution}_{t}} & \text{if } \mathrm{carrier\_out}_{n,i,c} \wedge \neg \mathrm{carrier\_in}_{n,i,c} \\ \frac{\mathit{flow\_in}_{n,i,c,t}}{\mathrm{timestep\_resolution}_{t}} & \text{if } \mathrm{carrier\_in}_{n,i,c} \wedge \neg \mathrm{carrier\_out}_{n,i,c} \\ \frac{\mathit{flow\_out}_{n,i,c,t} - \mathit{flow\_in}_{n,i,c,t}}{\mathrm{timestep\_resolution}_{t}} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`cost_flow_cap_sum`**

```math
\mathrm{cost\_flow\_cap\_sum}_{n,i,k} = \begin{cases} \left( \mathrm{cost\_flow\_cap}_{n,i,k} + \mathrm{cost\_flow\_cap\_per\_distance}_{n,i,k} \cdot \mathrm{distance}_{i} \right) \cdot 0.5 & \text{if } \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \\ \mathrm{cost\_flow\_cap}_{n,i,k} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`cost_investment_flow_cap`**

```math
\mathit{cost\_investment\_flow\_cap}_{n,i,c,k} = \mathrm{cost\_flow\_cap\_sum}_{n,i,k} \cdot \mathit{flow\_cap}_{n,i,c} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ k \in \mathcal{K}
```

**`flows_carrier_flow`**

```math
\mathit{flows\_carrier\_flow}_{n,c,t} = \sum_{i \in \mathcal{I}} \mathit{flow\_out}_{n,i,c,t} - \left( \sum_{i \in \mathcal{I}} \mathit{flow\_in}_{n,i,c,t} \right) \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`flows_cost_investment`**

```math
\mathit{flows\_cost\_investment}_{n,i,k} = \sum_{c \in \mathcal{C}} \mathit{cost\_investment\_flow\_cap}_{n,i,c,k} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`flows_cost_operation_variable`**

```math
\mathit{flows\_cost\_operation\_variable}_{n,i,k,t} = \mathrm{timestep\_weights}_{t} \cdot \left( \sum_{c \in \mathcal{C}} \mathrm{cost\_flow\_out}_{n,i,k,t} \cdot \mathit{flow\_out}_{n,i,c,t} + \sum_{c \in \mathcal{C}} \mathrm{cost\_flow\_in}_{n,i,k,t} \cdot \mathit{flow\_in}_{n,i,c,t} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K},\ t \in \mathcal{T}
```

**`flows_cost_operation_fixed`**

```math
\mathit{flows\_cost\_operation\_fixed}_{n,i,k} = \mathit{annualisation\_weight} \cdot \left( \sum_{c \in \mathcal{C}} \mathrm{cost\_om\_annual}_{n,i,k} \cdot \mathit{flow\_cap}_{n,i,c} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

#### Variable domains

**`flow_cap`**

```math
\mathrm{flow\_cap\_min}_{n,i} \le \mathit{flow\_cap}_{n,i,c} \le \mathrm{flow\_cap\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathrm{carrier\_in}_{n,i,c} \vee \mathrm{carrier\_out}_{n,i,c}
```

**`flow_out`**

```math
\mathit{flow\_out}_{n,i,c,t} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_out}_{n,i,c} \wedge \neg \left( \mathrm{one\_way}_{i} \wedge \left( i,\ n \right) \in \mathrm{link\_from} \right)
```

**`flow_in`**

```math
\mathit{flow\_in}_{n,i,c,t} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_in}_{n,i,c} \wedge \neg \left( \mathrm{one\_way}_{i} \wedge \left( i,\ n \right) \in \mathrm{link\_to} \right)
```

#### Assumptions

**`must_have_base`**

```math
\mathrm{base\_tech}_{i} \text{ is defined} \qquad \forall\, i \in \mathcal{I}
```

**`base_tech_one_of`**

```math
\mathrm{base\_tech}_{i} = \text{'}\mathrm{demand}\text{'} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{conversion}\text{'} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \qquad \forall\, i \in \mathcal{I}
```

**`distance_only_for_transmission`**

```math
\mathrm{distance}_{i} = 1 \wedge \mathrm{flow\_in\_eff\_per\_distance}_{n,i,c,t} = 1 \wedge \mathrm{flow\_out\_eff\_per\_distance}_{n,i,c,t} = 1 \wedge \neg \left( \mathrm{cost\_flow\_cap\_per\_distance}_{n,i,k} \text{ is defined} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ k \in \mathcal{K},\ t \in \mathcal{T} \,:\, \neg \left( \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \right)
```

**`unbounded_flow_cap_cost`**

```math
\neg \left( \mathrm{cost\_flow\_cap}_{n,i,k} < 0 \right) \vee \mathrm{flow\_cap\_max}_{n,i} \text{ is defined} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```
<!-- gallery:end -->
