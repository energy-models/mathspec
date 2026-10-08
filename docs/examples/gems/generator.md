<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Generators

This file states the GEMS `generator` model. It is one of the [ten fragments](index.md)
of the GEMS port. A generator has three ports, and
they add a term to four sums: the bus balance, the CO2 cap, and the hard and
soft energy caps. The `energy_port` adds to both energy caps. The generator
also adds its generation cost to `total_cost`.

<!-- gallery:begin -->
```yaml
description: >-
  GEMS `generator`. A generator is a dispatchable unit with three ports. It
  sends its generation through `balance_port`, its energy over the horizon
  through `energy_port`, and its CO2 through `emission_port`.
dimensions:
  time: { dtype: int, ordered: true, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  bus: { description: "`bus` components: nodes where flows balance" }
  generator: { description: "`generator` components: dispatchable units" }
  emission_limit: { description: "`emission_constraint` components: system-wide CO2 caps" }
  energy_limit_hard:
    description: "`energy_limitation_hard_constraint_max` components: energy caps with no slack"
  energy_limit_soft:
    description: "`energy_limitation_soft_constraint_max` components: energy caps with a priced slack"
relations:
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
parameters:
  Generator_p_min: { dims: [time, scenario, generator], description: smallest generation }
  Generator_p_max: { dims: [time, scenario, generator], description: largest generation }
  Generator_generation_cost: { dims: [generator], description: cost of one unit of generation }
  Generator_co2_emission_factor: { dims: [generator], description: CO2 released by one unit of generation }
variables:
  Generator_generation:
    dims: [time, scenario, generator]
    bounds: { lower: Generator_p_min, upper: Generator_p_max }
    description: generation
given:
  expressions:
    Bus_balance_port_flow: { dims: [time, scenario, bus] }
    Emission_port_co2: { dims: [scenario, emission_limit] }
    Energy_limit_hard_port_energy: { dims: [scenario, energy_limit_hard] }
    Energy_limit_soft_port_energy: { dims: [scenario, energy_limit_soft] }
    total_cost: { dims: [scenario] }
expressions:
  Generator_balance_port_flow:
    description: "`balance_port.flow` of a generator, `generation`"
    expression: sum(Generator_generation, over=generator, by=Generator_balance_port[bus])
    adds_to: Bus_balance_port_flow
  Generator_emission_port_co2:
    description: "`emission_port.co2` of a generator, `sum(generation * co2_emission_factor)`"
    expression: >-
      sum(sum(Generator_generation * Generator_co2_emission_factor, over=time),
      over=generator, by=Generator_emission_port[emission_limit])
    adds_to: Emission_port_co2
  Generator_cumulative_energy_hard:
    description: "`energy_port.cumulative_energy` of a generator, `sum(generation)`, at a hard cap"
    expression: >-
      sum(sum(Generator_generation, over=time),
      over=generator, by=Generator_energy_port_hard[energy_limit_hard])
    adds_to: Energy_limit_hard_port_energy
  Generator_cumulative_energy_soft:
    description: "`energy_port.cumulative_energy` of a generator, `sum(generation)`, at a soft cap"
    expression: >-
      sum(sum(Generator_generation, over=time),
      over=generator, by=Generator_energy_port_soft[energy_limit_soft])
    adds_to: Energy_limit_soft_port_energy
  Generator_objective:
    description: "`generator.objective`"
    expression: sum(Generator_generation_cost * Generator_generation, over=[time, generator])
    adds_to: total_cost
```

GEMS `generator`. A generator is a dispatchable unit with three ports. It sends its generation through `balance_port`, its energy over the horizon through `energy_port`, and its CO2 through `emission_port`.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{Generator\_balance\_port} \subseteq \mathcal{G} \times \mathcal{B}`$ — `bus` components: nodes where flows balance |
| $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_balance\_port} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{Generator\_emission\_port} \subseteq \mathcal{G} \times \mathcal{E},\ \mathrm{Generator\_energy\_port\_hard} \subseteq \mathcal{G} \times \mathcal{N},\ \mathrm{Generator\_energy\_port\_soft} \subseteq \mathcal{G} \times \mathcal{R}`$ — `generator` components: dispatchable units |
| $`\mathcal{E}`$ | index $`e`$ — `emission_limit` with $`\mathrm{Generator\_emission\_port} \subseteq \mathcal{G} \times \mathcal{E}`$ — `emission_constraint` components: system-wide CO2 caps |
| $`\mathcal{N}`$ | index $`n`$ — `energy_limit_hard` with $`\mathrm{Generator\_energy\_port\_hard} \subseteq \mathcal{G} \times \mathcal{N}`$ — `energy_limitation_hard_constraint_max` components: energy caps with no slack |
| $`\mathcal{R}`$ | index $`r`$ — `energy_limit_soft` with $`\mathrm{Generator\_energy\_port\_soft} \subseteq \mathcal{G} \times \mathcal{R}`$ — `energy_limitation_soft_constraint_max` components: energy caps with a priced slack |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Generator\_p\_min}`$ | `Generator_p_min` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{G}`$ — smallest generation |
| $`\mathrm{Generator\_p\_max}`$ | `Generator_p_max` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{G}`$ — largest generation |
| $`\mathrm{Generator\_generation\_cost}`$ | `Generator_generation_cost` over $`\mathcal{G}`$ — cost of one unit of generation |
| $`\mathrm{Generator\_co2\_emission\_factor}`$ | `Generator_co2_emission_factor` over $`\mathcal{G}`$ — CO2 released by one unit of generation |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{Generator\_generation}`$ | `Generator_generation` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{G}`$ — generation |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_balance\_port\_flow}`$ | `Bus_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$, an expression this file adds `Generator_balance_port_flow` to |
| $`\mathit{Emission\_port\_co2}`$ | `Emission_port_co2` over $`\mathcal{S} \times \mathcal{E}`$, an expression this file adds `Generator_emission_port_co2` to |
| $`\mathit{Energy\_limit\_hard\_port\_energy}`$ | `Energy_limit_hard_port_energy` over $`\mathcal{S} \times \mathcal{N}`$, an expression this file adds `Generator_cumulative_energy_hard` to |
| $`\mathit{Energy\_limit\_soft\_port\_energy}`$ | `Energy_limit_soft_port_energy` over $`\mathcal{S} \times \mathcal{R}`$, an expression this file adds `Generator_cumulative_energy_soft` to |
| $`\mathit{total\_cost}`$ | `total_cost` over $`\mathcal{S}`$, an expression this file adds `Generator_objective` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Generator\_balance\_port\_flow}`$ | `Generator_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — `balance_port.flow` of a generator, `generation` |
| $`\mathit{Generator\_emission\_port\_co2}`$ | `Generator_emission_port_co2` over $`\mathcal{S} \times \mathcal{E}`$ — `emission_port.co2` of a generator, `sum(generation * co2_emission_factor)` |
| $`\mathit{Generator\_cumulative\_energy\_hard}`$ | `Generator_cumulative_energy_hard` over $`\mathcal{S} \times \mathcal{N}`$ — `energy_port.cumulative_energy` of a generator, `sum(generation)`, at a hard cap |
| $`\mathit{Generator\_cumulative\_energy\_soft}`$ | `Generator_cumulative_energy_soft` over $`\mathcal{S} \times \mathcal{R}`$ — `energy_port.cumulative_energy` of a generator, `sum(generation)`, at a soft cap |
| $`\mathit{Generator\_objective}`$ | `Generator_objective` over $`\mathcal{S}`$ — `generator.objective` |

Upright is what the data supplies — a parameter such as $`\mathrm{Generator\_p\_min}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{Generator\_generation}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Definitions

**`Generator_balance_port_flow`**

```math
\mathit{Generator\_balance\_port\_flow}_{t,s,b} = \sum_{g \in \mathcal{G} \,:\, \left( g,\ b \right) \in \mathrm{Generator\_balance\_port}} \mathit{Generator\_generation}_{t,s,g} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

**`Generator_emission_port_co2`**

```math
\mathit{Generator\_emission\_port\_co2}_{s,e} = \sum_{g \in \mathcal{G} \,:\, \left( g,\ e \right) \in \mathrm{Generator\_emission\_port}} \sum_{t \in \mathcal{T}} \mathit{Generator\_generation}_{t,s,g} \cdot \mathrm{Generator\_co2\_emission\_factor}_{g} \qquad \forall\, s \in \mathcal{S},\ e \in \mathcal{E}
```

**`Generator_cumulative_energy_hard`**

```math
\mathit{Generator\_cumulative\_energy\_hard}_{s,n} = \sum_{g \in \mathcal{G} \,:\, \left( g,\ n \right) \in \mathrm{Generator\_energy\_port\_hard}} \sum_{t \in \mathcal{T}} \mathit{Generator\_generation}_{t,s,g} \qquad \forall\, s \in \mathcal{S},\ n \in \mathcal{N}
```

**`Generator_cumulative_energy_soft`**

```math
\mathit{Generator\_cumulative\_energy\_soft}_{s,r} = \sum_{g \in \mathcal{G} \,:\, \left( g,\ r \right) \in \mathrm{Generator\_energy\_port\_soft}} \sum_{t \in \mathcal{T}} \mathit{Generator\_generation}_{t,s,g} \qquad \forall\, s \in \mathcal{S},\ r \in \mathcal{R}
```

**`Generator_objective`**

```math
\mathit{Generator\_objective}_{s} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathrm{Generator\_generation\_cost}_{g} \cdot \mathit{Generator\_generation}_{t,s,g} \qquad \forall\, s \in \mathcal{S}
```

#### Variable domains

**`Generator_generation`**

```math
\mathrm{Generator\_p\_min}_{t,s,g} \le \mathit{Generator\_generation}_{t,s,g} \le \mathrm{Generator\_p\_max}_{t,s,g} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ g \in \mathcal{G}
```
<!-- gallery:end -->
