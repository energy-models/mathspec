<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# GEMS basic models

This spec is the `basic_models_library` 1.0.0 of
[GEMS v0.4.0](https://github.com/AntaresSimulatorTeam/GEMS/releases/tag/v0.4.0) (RTE's component modelling
language), written as one file. In GEMS, a component exposes ports, and a
system file connects ports. Here each kind of connection is a
[relation](../reference/language/relations.md), and `sum_connections` is a
[`sum`](../reference/language/operators.md#sum) through that relation. Read
`Bus_balance` first: it names every port that can reach a bus. Then read
`Storage_level_equation`. GEMS wraps `level[t+1]` at the end of the horizon
through a setting in its run configuration, and this file states the wrap with
`edge='wrap'`. The objective uses `expec`, a
[macro](../reference/language/named.md#macros), for the average over
scenarios that GEMS applies to an objective term.
[mathspec and GEMS](../about/gems.md) compares the two languages.

<!-- gallery:begin -->
```yaml
description: >-
  The `basic_models_library` 1.0.0 of GEMS v0.4.0, the nine models of RTE's
  reference library in one spec. A GEMS model is a dimension and a component is one of its
  labels. A connection is a row of a relation, and `sum_connections` is a
  `sum` through that relation. The time and scenario axes, implicit in GEMS,
  are dimensions here.

dimensions:
  time: { dtype: int, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  bus: { description: "`bus` components: nodes where flows balance" }
  load: { description: "`load` components: fixed demands" }
  link: { description: "`link` components: flows between two buses" }
  renewable: { description: "`renewable` components: fixed generation" }
  generator: { description: "`generator` components: dispatchable units" }
  storage: { description: "`storage` components: reservoirs that inject and withdraw" }
  emission_limit:
    description: "`emission_constraint` components: system-wide CO2 caps"
  energy_limit_hard:
    description: "`energy_limitation_hard_constraint_max` components: energy caps with no slack"
  energy_limit_soft:
    description: "`energy_limitation_soft_constraint_max` components: energy caps with a priced slack"

relations:
  Load_balance_port: { key: [load, bus], description: "connections from a load's `balance_port` to a bus" }
  Link_out_port: { key: [link, bus], description: "connections from a link's `out_port` to a bus" }
  Link_in_port: { key: [link, bus], description: "connections from a link's `in_port` to a bus" }
  Renewable_balance_port:
    key: [renewable, bus]
    description: "connections from a renewable's `balance_port` to a bus"
  Generator_balance_port:
    key: [generator, bus]
    description: "connections from a generator's `balance_port` to a bus"
  Generator_emission_port:
    key: [generator, emission_limit]
    description: "connections from a generator's `emission_port` to an emission cap"
  Generator_energy_port_hard:
    key: [generator, energy_limit_hard]
    description: "connections from a generator's `energy_port` to a hard energy cap"
  Generator_energy_port_soft:
    key: [generator, energy_limit_soft]
    description: "connections from a generator's `energy_port` to a soft energy cap"
  Storage_injection_port:
    key: [storage, bus]
    description: "connections from a storage's `injection_port` to a bus"

parameters:
  Scenario_weight:
    dims: [scenario]
    description: >-
      what `expec` weighs a scenario by. GEMS takes the average, so each weight
      is one over the number of scenarios
  Bus_spillage_cost: { dims: [bus], description: cost of one unit of spillage }
  Bus_unsupplied_energy_cost: { dims: [bus], description: cost of one unit of unsupplied energy }
  Load_load: { dims: [time, scenario, load], description: demand }
  Link_capacity_direct: { dims: [time, scenario, link], description: largest flow out of `out_port` }
  Link_capacity_indirect: { dims: [time, scenario, link], description: largest flow out of `in_port` }
  Renewable_generation: { dims: [time, scenario, renewable], description: generation }
  Generator_p_min: { dims: [time, scenario, generator], description: least generation }
  Generator_p_max: { dims: [time, scenario, generator], description: most generation }
  Generator_generation_cost: { dims: [generator], description: cost of one unit of generation }
  Generator_co2_emission_factor: { dims: [generator], description: CO2 released by one unit of generation }
  Storage_reservoir_capacity: { dims: [storage], description: largest level }
  Storage_injection_nominal_capacity: { dims: [storage], description: largest injection }
  Storage_withdrawal_nominal_capacity: { dims: [storage], description: largest withdrawal }
  Storage_efficiency_injection: { dims: [storage], description: share of an injection that reaches the level }
  Storage_efficiency_withdrawal: { dims: [storage], description: level taken by one unit of withdrawal }
  Storage_initial_level:
    dims: [scenario, storage]
    description: level at the first time step, as a share of the reservoir capacity
  Emission_limit: { dims: [emission_limit], description: largest CO2 release over the horizon }
  Energy_limit_hard: { dims: [energy_limit_hard], description: largest generation over the horizon }
  Energy_limit_soft: { dims: [energy_limit_soft], description: generation over the horizon above which the slack is paid }
  Energy_limit_soft_slack_penalty: { dims: [energy_limit_soft], description: cost of one unit of slack }

variables:
  Bus_spillage:
    dims: [time, scenario, bus]
    bounds: { lower: 0 }
    description: injection that the bus cannot use
  Bus_unsupplied_energy:
    dims: [time, scenario, bus]
    bounds: { lower: 0 }
    description: demand that the bus cannot meet
  Link_flow_direct:
    dims: [time, scenario, link]
    bounds: { lower: 0, upper: Link_capacity_direct }
    description: flow out of `out_port`
  Link_flow_indirect:
    dims: [time, scenario, link]
    bounds: { lower: 0, upper: Link_capacity_indirect }
    description: flow out of `in_port`
  Link_flow:
    dims: [time, scenario, link]
    bounds: { upper: Link_capacity_direct }
    description: net flow out of `out_port`
  Generator_generation:
    dims: [time, scenario, generator]
    bounds: { lower: Generator_p_min, upper: Generator_p_max }
    description: generation
  Storage_p_injection:
    dims: [time, scenario, storage]
    bounds: { lower: 0, upper: Storage_injection_nominal_capacity }
    description: power taken from the bus into the reservoir
  Storage_p_withdrawal:
    dims: [time, scenario, storage]
    bounds: { lower: 0, upper: Storage_withdrawal_nominal_capacity }
    description: power given from the reservoir to the bus
  Storage_level:
    dims: [time, scenario, storage]
    bounds: { lower: 0, upper: Storage_reservoir_capacity }
    description: energy in the reservoir
  Energy_limit_soft_slack:
    dims: [time, scenario, energy_limit_soft]
    bounds: { lower: 0 }
    description: >-
      generation above the soft cap. A GEMS variable carries time unless it
      says otherwise, so the slack is one variable per time step

expressions:
  Load_balance_port_flow:
    expression: -Load_load
    description: "`balance_port.flow` of a load"
  Link_out_port_flow:
    expression: Link_flow
    description: "`out_port.flow` of a link"
  Link_in_port_flow:
    expression: -Link_flow
    description: "`in_port.flow` of a link"
  Renewable_balance_port_flow:
    expression: Renewable_generation
    description: "`balance_port.flow` of a renewable"
  Generator_balance_port_flow:
    expression: Generator_generation
    description: "`balance_port.flow` of a generator"
  Generator_energy_port_cumulative_energy:
    expression: sum(Generator_generation, over=time)
    description: "`energy_port.cumulative_energy` of a generator"
  Generator_emission_port_co2:
    expression: sum(Generator_generation * Generator_co2_emission_factor, over=time)
    description: "`emission_port.co2` of a generator"
  Storage_injection_port_flow:
    expression: Storage_p_withdrawal - Storage_p_injection
    description: "`injection_port.flow` of a storage"

macros:
  expec:
    args: [array]
    template: sum(array * Scenario_weight, over=scenario)

constraints:
  Bus_balance:
    dims: [time, scenario, bus]
    description: "`bus.balance`: what the connected ports put in is spilled, or is short of the demand"
    expression: >-
      sum(Load_balance_port_flow, by=Load_balance_port, over=load, into=bus)
      + sum(Link_out_port_flow, by=Link_out_port, over=link, into=bus)
      + sum(Link_in_port_flow, by=Link_in_port, over=link, into=bus)
      + sum(Renewable_balance_port_flow, by=Renewable_balance_port, over=renewable, into=bus)
      + sum(Generator_balance_port_flow, by=Generator_balance_port, over=generator, into=bus)
      + sum(Storage_injection_port_flow, by=Storage_injection_port, over=storage, into=bus)
      == Bus_spillage - Bus_unsupplied_energy
  Link_flow_direct_indirect:
    dims: [time, scenario, link]
    description: "`link.flow_direct_indirect`"
    expression: Link_flow == Link_flow_direct - Link_flow_indirect
  Link_flow_floor:
    dims: [time, scenario, link]
    description: >-
      the GEMS lower bound `-capacity_indirect` on `flow`. A bound here is a
      name, so the negated bound is a row
    expression: Link_flow >= -Link_capacity_indirect
  Storage_initial_level_constraint:
    dims: [time, scenario, storage]
    where: "position(time) == 0"
    description: "`storage.initial_level_constraint`: `level[0]`"
    expression: Storage_level == Storage_initial_level * Storage_reservoir_capacity
  Storage_level_equation:
    dims: [time, scenario, storage]
    description: >-
      `storage.Level equation`, `level[t+1] = level + …`, written one step
      back. GEMS wraps `[t+1]` at the end of the horizon by default, so the
      shift wraps too
    expression: >-
      Storage_level == shift(
        Storage_level
        + Storage_efficiency_injection * Storage_p_injection
        - Storage_efficiency_withdrawal * Storage_p_withdrawal,
        along=time, offset=1, edge='wrap')
  Emission_limit_co2_constraint:
    dims: [scenario, emission_limit]
    description: "`emission_constraint.co2_constraint`"
    expression: >-
      sum(Generator_emission_port_co2, by=Generator_emission_port, over=generator, into=emission_limit)
      <= Emission_limit
  Energy_limit_hard_max_generation_hard:
    dims: [scenario, energy_limit_hard]
    description: "`energy_limitation_hard_constraint_max.max_generation_hard`"
    expression: >-
      sum(Generator_energy_port_cumulative_energy, by=Generator_energy_port_hard, over=generator, into=energy_limit_hard)
      <= Energy_limit_hard
  Energy_limit_soft_max_generation_soft:
    dims: [time, scenario, energy_limit_soft]
    description: >-
      `energy_limitation_soft_constraint_max.max_generation_soft`. The slack
      carries time, so the row repeats in each time step
    expression: >-
      sum(Generator_energy_port_cumulative_energy, by=Generator_energy_port_soft, over=generator, into=energy_limit_soft)
      <= Energy_limit_soft + Energy_limit_soft_slack

objective:
  sense: minimize
  description: >-
    the sum of every model's `objective-contributions`. Each one sums over time
    and keeps the scenario, and GEMS takes its average over the scenarios
  expression: >-
    expec(
      sum(Bus_spillage_cost * Bus_spillage + Bus_unsupplied_energy_cost * Bus_unsupplied_energy, over=[time, bus])
      + sum(Generator_generation_cost * Generator_generation, over=[time, generator])
      + sum(Energy_limit_soft_slack * Energy_limit_soft_slack_penalty, over=[time, energy_limit_soft]))
```

The `basic_models_library` 1.0.0 of GEMS v0.4.0, the nine models of RTE's reference library in one spec. A GEMS model is a dimension and a component is one of its labels. A connection is a row of a relation, and `sum_connections` is a `sum` through that relation. The time and scenario axes, implicit in GEMS, are dimensions here.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{Load\_balance\_port} \subseteq \mathcal{L} \times \mathcal{B},\ \mathrm{Link\_out\_port} \subseteq \mathcal{I} \times \mathcal{B},\ \mathrm{Link\_in\_port} \subseteq \mathcal{I} \times \mathcal{B},\ \mathrm{Renewable\_balance\_port} \subseteq \mathcal{R} \times \mathcal{B},\ \mathrm{Generator\_balance\_port} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{Storage\_injection\_port} \subseteq \mathcal{O} \times \mathcal{B}`$ — `bus` components: nodes where flows balance |
| $`\mathcal{L}`$ | index $`l`$ — `load` with $`\mathrm{Load\_balance\_port} \subseteq \mathcal{L} \times \mathcal{B}`$ — `load` components: fixed demands |
| $`\mathcal{I}`$ | index $`i`$ — `link` with $`\mathrm{Link\_out\_port} \subseteq \mathcal{I} \times \mathcal{B},\ \mathrm{Link\_in\_port} \subseteq \mathcal{I} \times \mathcal{B}`$ — `link` components: flows between two buses |
| $`\mathcal{R}`$ | index $`r`$ — `renewable` with $`\mathrm{Renewable\_balance\_port} \subseteq \mathcal{R} \times \mathcal{B}`$ — `renewable` components: fixed generation |
| $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_balance\_port} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{Generator\_emission\_port} \subseteq \mathcal{G} \times \mathcal{E},\ \mathrm{Generator\_energy\_port\_hard} \subseteq \mathcal{G} \times \mathcal{N},\ \mathrm{Generator\_energy\_port\_soft} \subseteq \mathcal{G} \times \mathcal{Y}`$ — `generator` components: dispatchable units |
| $`\mathcal{O}`$ | index $`o`$ — `storage` with $`\mathrm{Storage\_injection\_port} \subseteq \mathcal{O} \times \mathcal{B}`$ — `storage` components: reservoirs that inject and withdraw |
| $`\mathcal{E}`$ | index $`e`$ — `emission_limit` with $`\mathrm{Generator\_emission\_port} \subseteq \mathcal{G} \times \mathcal{E}`$ — `emission_constraint` components: system-wide CO2 caps |
| $`\mathcal{N}`$ | index $`n`$ — `energy_limit_hard` with $`\mathrm{Generator\_energy\_port\_hard} \subseteq \mathcal{G} \times \mathcal{N}`$ — `energy_limitation_hard_constraint_max` components: energy caps with no slack |
| $`\mathcal{Y}`$ | index $`y`$ — `energy_limit_soft` with $`\mathrm{Generator\_energy\_port\_soft} \subseteq \mathcal{G} \times \mathcal{Y}`$ — `energy_limitation_soft_constraint_max` components: energy caps with a priced slack |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Scenario\_weight}`$ | `Scenario_weight` over $`\mathcal{S}`$ — what `expec` weighs a scenario by. GEMS takes the average, so each weight is one over the number of scenarios |
| $`\mathrm{Bus\_spillage\_cost}`$ | `Bus_spillage_cost` over $`\mathcal{B}`$ — cost of one unit of spillage |
| $`\mathrm{Bus\_unsupplied\_energy\_cost}`$ | `Bus_unsupplied_energy_cost` over $`\mathcal{B}`$ — cost of one unit of unsupplied energy |
| $`\mathrm{Load\_load}`$ | `Load_load` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — demand |
| $`\mathrm{Link\_capacity\_direct}`$ | `Link_capacity_direct` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{I}`$ — largest flow out of `out_port` |
| $`\mathrm{Link\_capacity\_indirect}`$ | `Link_capacity_indirect` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{I}`$ — largest flow out of `in_port` |
| $`\mathrm{Renewable\_generation}`$ | `Renewable_generation` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{R}`$ — generation |
| $`\mathrm{Generator\_p\_min}`$ | `Generator_p_min` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{G}`$ — least generation |
| $`\mathrm{Generator\_p\_max}`$ | `Generator_p_max` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{G}`$ — most generation |
| $`\mathrm{Generator\_generation\_cost}`$ | `Generator_generation_cost` over $`\mathcal{G}`$ — cost of one unit of generation |
| $`\mathrm{Generator\_co2\_emission\_factor}`$ | `Generator_co2_emission_factor` over $`\mathcal{G}`$ — CO2 released by one unit of generation |
| $`\mathrm{Storage\_reservoir\_capacity}`$ | `Storage_reservoir_capacity` over $`\mathcal{O}`$ — largest level |
| $`\mathrm{Storage\_injection\_nominal\_capacity}`$ | `Storage_injection_nominal_capacity` over $`\mathcal{O}`$ — largest injection |
| $`\mathrm{Storage\_withdrawal\_nominal\_capacity}`$ | `Storage_withdrawal_nominal_capacity` over $`\mathcal{O}`$ — largest withdrawal |
| $`\mathrm{Storage\_efficiency\_injection}`$ | `Storage_efficiency_injection` over $`\mathcal{O}`$ — share of an injection that reaches the level |
| $`\mathrm{Storage\_efficiency\_withdrawal}`$ | `Storage_efficiency_withdrawal` over $`\mathcal{O}`$ — level taken by one unit of withdrawal |
| $`\mathrm{Storage\_initial\_level}`$ | `Storage_initial_level` over $`\mathcal{S} \times \mathcal{O}`$ — level at the first time step, as a share of the reservoir capacity |
| $`\mathrm{Emission\_limit}`$ | `Emission_limit` over $`\mathcal{E}`$ — largest CO2 release over the horizon |
| $`\mathrm{Energy\_limit\_hard}`$ | `Energy_limit_hard` over $`\mathcal{N}`$ — largest generation over the horizon |
| $`\mathrm{Energy\_limit\_soft}`$ | `Energy_limit_soft` over $`\mathcal{Y}`$ — generation over the horizon above which the slack is paid |
| $`\mathrm{Energy\_limit\_soft\_slack\_penalty}`$ | `Energy_limit_soft_slack_penalty` over $`\mathcal{Y}`$ — cost of one unit of slack |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_spillage}`$ | `Bus_spillage` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — injection that the bus cannot use |
| $`\mathit{Bus\_unsupplied\_energy}`$ | `Bus_unsupplied_energy` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — demand that the bus cannot meet |
| $`\mathit{Link\_flow\_direct}`$ | `Link_flow_direct` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{I}`$ — flow out of `out_port` |
| $`\mathit{Link\_flow\_indirect}`$ | `Link_flow_indirect` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{I}`$ — flow out of `in_port` |
| $`\mathit{Link\_flow}`$ | `Link_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{I}`$ — net flow out of `out_port` |
| $`\mathit{Generator\_generation}`$ | `Generator_generation` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{G}`$ — generation |
| $`\mathit{Storage\_p\_injection}`$ | `Storage_p_injection` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{O}`$ — power taken from the bus into the reservoir |
| $`\mathit{Storage\_p\_withdrawal}`$ | `Storage_p_withdrawal` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{O}`$ — power given from the reservoir to the bus |
| $`\mathit{Storage\_level}`$ | `Storage_level` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{O}`$ — energy in the reservoir |
| $`\mathit{Energy\_limit\_soft\_slack}`$ | `Energy_limit_soft_slack` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{Y}`$ — generation above the soft cap. A GEMS variable carries time unless it says otherwise, so the slack is one variable per time step |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathrm{Load\_balance\_port\_flow}`$ | `Load_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — `balance_port.flow` of a load |
| $`\mathit{Link\_out\_port\_flow}`$ | `Link_out_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{I}`$ — `out_port.flow` of a link |
| $`\mathit{Link\_in\_port\_flow}`$ | `Link_in_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{I}`$ — `in_port.flow` of a link |
| $`\mathrm{Renewable\_balance\_port\_flow}`$ | `Renewable_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{R}`$ — `balance_port.flow` of a renewable |
| $`\mathit{Generator\_balance\_port\_flow}`$ | `Generator_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{G}`$ — `balance_port.flow` of a generator |
| $`\mathit{Generator\_energy\_port\_cumulative\_energy}`$ | `Generator_energy_port_cumulative_energy` over $`\mathcal{S} \times \mathcal{G}`$ — `energy_port.cumulative_energy` of a generator |
| $`\mathit{Generator\_emission\_port\_co2}`$ | `Generator_emission_port_co2` over $`\mathcal{S} \times \mathcal{G}`$ — `emission_port.co2` of a generator |
| $`\mathit{Storage\_injection\_port\_flow}`$ | `Storage_injection_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{O}`$ — `injection_port.flow` of a storage |

Upright is what the data supplies — a parameter such as $`\mathrm{Scenario\_weight}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{Bus\_spillage}`$. An index is italic too, being what a quantifier chooses, and a set is script.

$`t \ominus k`$ denotes cyclic translation: index $`t-k`$ taken modulo the size of the dimension (`roll`). Plain $`t-k`$ (`shift`) has no wraparound — terms translated past the edge are simply absent.

$`\mathrm{pos}(t)`$ denotes where index $`t`$ sits along its dimension's own order — the order `shift` steps along, not the order labels sort in — counted from $`0`$. The index itself stays the coordinate, so $`t`$ compares against labels and $`\mathrm{pos}(t)`$ against positions.

#### Objective

```math
\min \sum_{s \in \mathcal{S}} \left( \sum_{t \in \mathcal{T},\ b \in \mathcal{B}} \left( \mathrm{Bus\_spillage\_cost}_{b} \cdot \mathit{Bus\_spillage}_{t,s,b} + \mathrm{Bus\_unsupplied\_energy\_cost}_{b} \cdot \mathit{Bus\_unsupplied\_energy}_{t,s,b} \right) + \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathrm{Generator\_generation\_cost}_{g} \cdot \mathit{Generator\_generation}_{t,s,g} + \sum_{t \in \mathcal{T},\ y \in \mathcal{Y}} \mathit{Energy\_limit\_soft\_slack}_{t,s,y} \cdot \mathrm{Energy\_limit\_soft\_slack\_penalty}_{y} \right) \cdot \mathrm{Scenario\_weight}_{s}
```

#### Subject to

**`Bus_balance`**

```math
\sum_{l \in \mathcal{L} \,:\, \left( l,\ b \right) \in \mathrm{Load\_balance\_port}} \mathrm{Load\_balance\_port\_flow}_{t,s,l} + \sum_{i \in \mathcal{I} \,:\, \left( i,\ b \right) \in \mathrm{Link\_out\_port}} \mathit{Link\_out\_port\_flow}_{t,s,i} + \sum_{i \in \mathcal{I} \,:\, \left( i,\ b \right) \in \mathrm{Link\_in\_port}} \mathit{Link\_in\_port\_flow}_{t,s,i} + \sum_{r \in \mathcal{R} \,:\, \left( r,\ b \right) \in \mathrm{Renewable\_balance\_port}} \mathrm{Renewable\_balance\_port\_flow}_{t,s,r} + \sum_{g \in \mathcal{G} \,:\, \left( g,\ b \right) \in \mathrm{Generator\_balance\_port}} \mathit{Generator\_balance\_port\_flow}_{t,s,g} + \sum_{o \in \mathcal{O} \,:\, \left( o,\ b \right) \in \mathrm{Storage\_injection\_port}} \mathit{Storage\_injection\_port\_flow}_{t,s,o} = \mathit{Bus\_spillage}_{t,s,b} - \mathit{Bus\_unsupplied\_energy}_{t,s,b} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

**`Link_flow_direct_indirect`**

```math
\mathit{Link\_flow}_{t,s,i} = \mathit{Link\_flow\_direct}_{t,s,i} - \mathit{Link\_flow\_indirect}_{t,s,i} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ i \in \mathcal{I}
```

**`Link_flow_floor`**

```math
\mathit{Link\_flow}_{t,s,i} \ge -\mathrm{Link\_capacity\_indirect}_{t,s,i} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ i \in \mathcal{I}
```

**`Storage_initial_level_constraint`**

```math
\mathit{Storage\_level}_{t,s,o} = \mathrm{Storage\_initial\_level}_{s,o} \cdot \mathrm{Storage\_reservoir\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O} \,:\, \mathrm{pos}(t) = 0
```

**`Storage_level_equation`**

```math
\mathit{Storage\_level}_{t,s,o} = \mathit{Storage\_level}_{t \ominus 1,s,o} + \mathrm{Storage\_efficiency\_injection}_{o} \cdot \mathit{Storage\_p\_injection}_{t \ominus 1,s,o} - \mathrm{Storage\_efficiency\_withdrawal}_{o} \cdot \mathit{Storage\_p\_withdrawal}_{t \ominus 1,s,o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

**`Emission_limit_co2_constraint`**

```math
\sum_{g \in \mathcal{G} \,:\, \left( g,\ e \right) \in \mathrm{Generator\_emission\_port}} \mathit{Generator\_emission\_port\_co2}_{s,g} \le \mathrm{Emission\_limit}_{e} \qquad \forall\, s \in \mathcal{S},\ e \in \mathcal{E}
```

**`Energy_limit_hard_max_generation_hard`**

```math
\sum_{g \in \mathcal{G} \,:\, \left( g,\ n \right) \in \mathrm{Generator\_energy\_port\_hard}} \mathit{Generator\_energy\_port\_cumulative\_energy}_{s,g} \le \mathrm{Energy\_limit\_hard}_{n} \qquad \forall\, s \in \mathcal{S},\ n \in \mathcal{N}
```

**`Energy_limit_soft_max_generation_soft`**

```math
\sum_{g \in \mathcal{G} \,:\, \left( g,\ y \right) \in \mathrm{Generator\_energy\_port\_soft}} \mathit{Generator\_energy\_port\_cumulative\_energy}_{s,g} \le \mathrm{Energy\_limit\_soft}_{y} + \mathit{Energy\_limit\_soft\_slack}_{t,s,y} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ y \in \mathcal{Y}
```

#### Definitions

**`Load_balance_port_flow`**

```math
\mathrm{Load\_balance\_port\_flow}_{t,s,l} = -\mathrm{Load\_load}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ l \in \mathcal{L}
```

**`Link_out_port_flow`**

```math
\mathit{Link\_out\_port\_flow}_{t,s,i} = \mathit{Link\_flow}_{t,s,i} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ i \in \mathcal{I}
```

**`Link_in_port_flow`**

```math
\mathit{Link\_in\_port\_flow}_{t,s,i} = -\mathit{Link\_flow}_{t,s,i} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ i \in \mathcal{I}
```

**`Renewable_balance_port_flow`**

```math
\mathrm{Renewable\_balance\_port\_flow}_{t,s,r} = \mathrm{Renewable\_generation}_{t,s,r} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ r \in \mathcal{R}
```

**`Generator_balance_port_flow`**

```math
\mathit{Generator\_balance\_port\_flow}_{t,s,g} = \mathit{Generator\_generation}_{t,s,g} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ g \in \mathcal{G}
```

**`Generator_energy_port_cumulative_energy`**

```math
\mathit{Generator\_energy\_port\_cumulative\_energy}_{s,g} = \sum_{t \in \mathcal{T}} \mathit{Generator\_generation}_{t,s,g} \qquad \forall\, s \in \mathcal{S},\ g \in \mathcal{G}
```

**`Generator_emission_port_co2`**

```math
\mathit{Generator\_emission\_port\_co2}_{s,g} = \sum_{t \in \mathcal{T}} \mathit{Generator\_generation}_{t,s,g} \cdot \mathrm{Generator\_co2\_emission\_factor}_{g} \qquad \forall\, s \in \mathcal{S},\ g \in \mathcal{G}
```

**`Storage_injection_port_flow`**

```math
\mathit{Storage\_injection\_port\_flow}_{t,s,o} = \mathit{Storage\_p\_withdrawal}_{t,s,o} - \mathit{Storage\_p\_injection}_{t,s,o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

#### Variable domains

**`Bus_spillage`**

```math
\mathit{Bus\_spillage}_{t,s,b} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

**`Bus_unsupplied_energy`**

```math
\mathit{Bus\_unsupplied\_energy}_{t,s,b} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

**`Link_flow_direct`**

```math
0 \le \mathit{Link\_flow\_direct}_{t,s,i} \le \mathrm{Link\_capacity\_direct}_{t,s,i} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ i \in \mathcal{I}
```

**`Link_flow_indirect`**

```math
0 \le \mathit{Link\_flow\_indirect}_{t,s,i} \le \mathrm{Link\_capacity\_indirect}_{t,s,i} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ i \in \mathcal{I}
```

**`Link_flow`**

```math
\mathit{Link\_flow}_{t,s,i} \le \mathrm{Link\_capacity\_direct}_{t,s,i} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ i \in \mathcal{I}
```

**`Generator_generation`**

```math
\mathrm{Generator\_p\_min}_{t,s,g} \le \mathit{Generator\_generation}_{t,s,g} \le \mathrm{Generator\_p\_max}_{t,s,g} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ g \in \mathcal{G}
```

**`Storage_p_injection`**

```math
0 \le \mathit{Storage\_p\_injection}_{t,s,o} \le \mathrm{Storage\_injection\_nominal\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

**`Storage_p_withdrawal`**

```math
0 \le \mathit{Storage\_p\_withdrawal}_{t,s,o} \le \mathrm{Storage\_withdrawal\_nominal\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

**`Storage_level`**

```math
0 \le \mathit{Storage\_level}_{t,s,o} \le \mathrm{Storage\_reservoir\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

**`Energy_limit_soft_slack`**

```math
\mathit{Energy\_limit\_soft\_slack}_{t,s,y} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ y \in \mathcal{Y}
```
<!-- gallery:end -->
