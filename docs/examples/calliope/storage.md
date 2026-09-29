<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Storage

One of the base fragments of [Calliope in fragments](index.md). Storage capacity, the stored carrier, and how a store carries its fill from one time step to the next, clustered days included.

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

relations:
  lookup_cluster_last_timestep:
    description: >-
      `lookup_cluster_last_timestep` — the last time step of the cluster a
      time step stands for, at the first time step of each clustered day
    key: timesteps
    values: { last: timesteps }

parameters:
  storage_cap_min:
    description: "`storage_cap_min` — least storage capacity. Calliope's default is 0, and data prep fills it"
    dims: [nodes, techs]
  storage_cap_max:
    description: "`storage_cap_max` — most storage capacity. Calliope's default is `.inf`, and data prep fills it"
    dims: [nodes, techs]
  storage_discharge_depth:
    description: "`storage_discharge_depth` — the least a store holds, as a share of its capacity"
    dims: [nodes, techs, timesteps]
  storage_initial:
    description: "`storage_initial` — what a store holds at the start, as a share of its capacity; given only where set"
    dims: [nodes, techs]
  storage_retention:
    description: >-
      `1 - storage_loss` — the share of what a store holds that it keeps
      for an hour, data prep. mathspec refuses a sum as the base of `**`,
      over parameters too
    dims: [nodes, techs, timesteps]
  cyclic_storage:
    description: >-
      `cyclic_storage` — whether a store ends where it starts. Calliope's
      default is true, and data prep fills it
    dims: [nodes, techs]
    dtype: bool
  cluster_first_timestep:
    description: "`cluster_first_timestep` — whether a time step is the first of its clustered day"
    dims: [timesteps]
    dtype: bool
  flow_cap_per_storage_cap_min:
    description: "`flow_cap_per_storage_cap_min` — least flow capacity per unit of storage capacity; given only where set"
    dims: [nodes, techs]
  flow_cap_per_storage_cap_max:
    description: "`flow_cap_per_storage_cap_max` — most flow capacity per unit of storage capacity; given only where set"
    dims: [nodes, techs]
  cost_storage_cap:
    description: "`cost_storage_cap` — the cost of one unit of storage capacity"
    dims: [nodes, techs, costs]

variables:
  storage_cap:
    description: "`storage_cap` — the most a technology can store"
    dims: [nodes, techs]
    where: include_storage OR base_tech == 'storage'
    bounds: { lower: storage_cap_min, upper: storage_cap_max }
    absence: zero
  storage:
    description: "`storage` — what a technology holds at the end of a time step"
    dims: [nodes, techs, timesteps]
    where: include_storage OR base_tech == 'storage'
    bounds: { lower: 0 }
    absence: zero

expressions:
  storage_previous_step:
    description: >-
      `$storage_previous_step` — what a store carries into a time step:
      its initial fill at the first step of a store that is not cyclic, what
      is left of the last step of its clustered day at the first step of a
      cluster, and what is left of the step before everywhere else
    dims: [nodes, techs, timesteps]
    cases:
      initial:
        when: position(timesteps) == 0 AND NOT cyclic_storage
        expression: storage_initial * storage_cap
      cluster_start:
        when: cluster_first_timestep AND NOT (position(timesteps) == 0 AND NOT cyclic_storage)
        expression: >-
          storage_retention ** at(timestep_resolution, by=lookup_cluster_last_timestep, over=last, into=timesteps)
          * at(storage, by=lookup_cluster_last_timestep, over=last, into=timesteps)
    otherwise: >-
      storage_retention ** shift(timestep_resolution, along=timesteps, offset=1, edge='wrap')
      * shift(storage, along=timesteps, offset=1, edge='wrap')
  cost_investment_storage_cap:
    description: "`cost_investment_storage_cap` — the investment cost of storage capacity"
    expression: cost_storage_cap * storage_cap

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    include_storage: { dims: [nodes, techs], dtype: bool }
    timestep_resolution: { dims: [timesteps] }
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
  expressions:
    flow_out_inc_eff: { dims: [nodes, techs, carriers, timesteps] }
    flow_in_inc_eff: { dims: [nodes, techs, carriers, timesteps] }
    cost_investment: { dims: [nodes, techs, costs], term: cost_investment_storage_cap }

constraints:
  flow_capacity_per_storage_capacity_min:
    description: "`flow_capacity_per_storage_capacity_min` — flow capacity is at least its least share of storage capacity"
    dims: [nodes, techs, carriers]
    where: flow_cap AND storage_cap AND flow_cap_per_storage_cap_min
    expression: flow_cap >= storage_cap * flow_cap_per_storage_cap_min
  flow_capacity_per_storage_capacity_max:
    description: "`flow_capacity_per_storage_capacity_max` — flow capacity is at most its most share of storage capacity"
    dims: [nodes, techs, carriers]
    where: flow_cap AND storage_cap AND flow_cap_per_storage_cap_max
    expression: flow_cap <= storage_cap * flow_cap_per_storage_cap_max
  storage_max:
    description: "`storage_max` — a store holds at most its capacity"
    dims: [nodes, techs, timesteps]
    where: storage
    expression: storage <= storage_cap
  storage_discharge_depth_limit:
    description: "`storage_discharge_depth_limit` — a store holds at least its depth of discharge"
    dims: [nodes, techs, timesteps]
    where: storage AND storage_discharge_depth
    expression: storage - storage_discharge_depth * storage_cap >= 0
  balance_storage:
    description: >-
      `balance_storage` — what a store holds at the end of a time step is
      what it carried in, less what it put out before losses, plus what it
      took in after them
    dims: [nodes, techs, timesteps]
    where: (include_storage OR base_tech == 'storage') AND NOT (base_tech == 'supply' OR base_tech == 'demand')
    expression: >-
      storage == storage_previous_step
      - sum(flow_out_inc_eff, over=carriers) + sum(flow_in_inc_eff, over=carriers)
  set_storage_initial:
    description: >-
      `set_storage_initial` — a cyclic store with an initial fill holds it
      at the end, after the last step's loss. Calliope builds one row per
      store and reads the last step; this builds that row at the last step
    dims: [nodes, techs, timesteps]
    where: position(timesteps) == -1 AND storage AND storage_initial AND cyclic_storage
    expression: storage * storage_retention ** timestep_resolution == storage_initial * storage_cap

assumptions:
  unbounded_storage_cap_cost:
    description: Calliope's `unbounded_storage_cap_cost` — a negative storage capacity cost needs a finite maximum
    holds: NOT cost_storage_cap < 0 OR storage_cap_max
  storage_initial_max:
    description: Calliope's `storage_initial_max` — the initial fill is a share
    holds: storage_initial >= 0 AND storage_initial <= 1
    where: storage_initial
  cyclic_storage_needs_inter_cluster:
    description: >-
      Calliope's `cyclic_storage_needs_inter_cluster` — a cyclic store under
      clustering needs the inter-cluster patch
    holds: NOT (cyclic_storage AND lookup_cluster_last_timestep)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` with $`\mathrm{lookup\_cluster\_last\_timestep}: \mathcal{T} \to \mathcal{T}`$ — Calliope's `timesteps` — time steps, in order |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{storage}^{\mathrm{cap,min}}`$ | `storage_cap_min` over $`\mathcal{N} \times \mathcal{I}`$ — `storage_cap_min` — least storage capacity. Calliope's default is 0, and data prep fills it |
| $`\mathrm{storage}^{\mathrm{cap,max}}`$ | `storage_cap_max` over $`\mathcal{N} \times \mathcal{I}`$ — `storage_cap_max` — most storage capacity. Calliope's default is `.inf`, and data prep fills it |
| $`\mathrm{storage}^{\mathrm{discharge,depth}}`$ | `storage_discharge_depth` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `storage_discharge_depth` — the least a store holds, as a share of its capacity |
| $`\mathrm{storage}^{\mathrm{initial}}`$ | `storage_initial` over $`\mathcal{N} \times \mathcal{I}`$ — `storage_initial` — what a store holds at the start, as a share of its capacity; given only where set |
| $`\mathrm{storage}^{\mathrm{retention}}`$ | `storage_retention` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `1 - storage_loss` — the share of what a store holds that it keeps for an hour, data prep. mathspec refuses a sum as the base of `**`, over parameters too |
| $`\mathrm{cyclic\_storage}`$ | `cyclic_storage` over $`\mathcal{N} \times \mathcal{I}`$ — `cyclic_storage` — whether a store ends where it starts. Calliope's default is true, and data prep fills it |
| $`\mathrm{cluster\_first\_timestep}`$ | `cluster_first_timestep` over $`\mathcal{T}`$ — `cluster_first_timestep` — whether a time step is the first of its clustered day |
| $`\mathrm{flow\_cap\_per\_storage\_cap\_min}`$ | `flow_cap_per_storage_cap_min` over $`\mathcal{N} \times \mathcal{I}`$ — `flow_cap_per_storage_cap_min` — least flow capacity per unit of storage capacity; given only where set |
| $`\mathrm{flow\_cap\_per\_storage\_cap\_max}`$ | `flow_cap_per_storage_cap_max` over $`\mathcal{N} \times \mathcal{I}`$ — `flow_cap_per_storage_cap_max` — most flow capacity per unit of storage capacity; given only where set |
| $`\mathrm{cost\_storage\_cap}`$ | `cost_storage_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_storage_cap` — the cost of one unit of storage capacity |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{storage}^{\mathrm{cap}}`$ | `storage_cap` over $`\mathcal{N} \times \mathcal{I}`$ — `storage_cap` — the most a technology can store |
| $`\mathit{storage}`$ | `storage` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `storage` — what a technology holds at the end of a time step |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{include\_storage}`$ | `include_storage` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{flow\_in\_inc\_eff}`$ | `flow_in_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{cost\_investment}`$ | `cost_investment` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression this file adds `cost_investment_storage_cap` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{storage}^{\mathrm{previous,step}}`$ | `storage_previous_step` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `$storage_previous_step` — what a store carries into a time step: its initial fill at the first step of a store that is not cyclic, what is left of the last step of its clustered day at the first step of a cluster, and what is left of the step before everywhere else |
| $`\mathit{cost\_investment\_storage\_cap}`$ | `cost_investment_storage_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$ — `cost_investment_storage_cap` — the investment cost of storage capacity |

Upright is what the data supplies — a parameter such as $`\mathrm{storage}^{\mathrm{cap,min}}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{storage}^{\mathrm{cap}}`$. An index is italic too, being what a quantifier chooses, and a set is script.

$`t \ominus k`$ denotes cyclic translation: index $`t-k`$ taken modulo the size of the dimension (`roll`). Plain $`t-k`$ (`shift`) has no wraparound — terms translated past the edge are simply absent.

$`\mathrm{pos}(t)`$ denotes where index $`t`$ sits along its dimension's own order — the order `shift` steps along, not the order labels sort in — counted from $`0`$. The index itself stays the coordinate, so $`t`$ compares against labels and $`\mathrm{pos}(t)`$ against positions.

$`\lvert \mathcal{T} \rvert`$ denotes the size of the set being counted along, and a position counted from the end prints against it — $`\lvert \mathcal{T} \rvert - 1`$ is the last position, one less than the size because the first is $`0`$.

#### Subject to

**`flow_capacity_per_storage_capacity_min`**

```math
\mathit{flow\_cap}_{n,i,c} \ge \mathit{storage}^{\mathrm{cap}}_{n,i} \cdot \mathrm{flow\_cap\_per\_storage\_cap\_min}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathit{storage}^{\mathrm{cap}}_{n,i} \text{ exists} \wedge \mathrm{flow\_cap\_per\_storage\_cap\_min}_{n,i} \text{ is defined}
```

**`flow_capacity_per_storage_capacity_max`**

```math
\mathit{flow\_cap}_{n,i,c} \le \mathit{storage}^{\mathrm{cap}}_{n,i} \cdot \mathrm{flow\_cap\_per\_storage\_cap\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathit{storage}^{\mathrm{cap}}_{n,i} \text{ exists} \wedge \mathrm{flow\_cap\_per\_storage\_cap\_max}_{n,i} \text{ is defined}
```

**`storage_max`**

```math
\mathit{storage}_{n,i,t} \le \mathit{storage}^{\mathrm{cap}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{storage}_{n,i,t} \text{ exists}
```

**`storage_discharge_depth_limit`**

```math
\mathit{storage}_{n,i,t} - \mathrm{storage}^{\mathrm{discharge,depth}}_{n,i,t} \cdot \mathit{storage}^{\mathrm{cap}}_{n,i} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{storage}_{n,i,t} \text{ exists} \wedge \mathrm{storage}^{\mathrm{discharge,depth}}_{n,i,t} \text{ is defined}
```

**`balance_storage`**

```math
\mathit{storage}_{n,i,t} = \mathit{storage}^{\mathrm{previous,step}}_{n,i,t} - \left( \sum_{c \in \mathcal{C}} \mathit{flow\_out\_inc\_eff}_{n,i,c,t} \right) + \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \left( \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'} \right) \wedge \neg \left( \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{demand}\text{'} \right)
```

**`set_storage_initial`**

```math
\mathit{storage}_{n,i,t} \cdot \mathrm{storage}^{\mathrm{retention}}_{n,i,t}^{\mathrm{timestep\_resolution}_{t}} = \mathrm{storage}^{\mathrm{initial}}_{n,i} \cdot \mathit{storage}^{\mathrm{cap}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{pos}(t) = \lvert \mathcal{T} \rvert - 1 \wedge \mathit{storage}_{n,i,t} \text{ exists} \wedge \mathrm{storage}^{\mathrm{initial}}_{n,i} \text{ is defined} \wedge \mathrm{cyclic\_storage}_{n,i}
```

#### Definitions

**`storage_previous_step`**

```math
\mathit{storage}^{\mathrm{previous,step}}_{n,i,t} = \begin{cases} \mathrm{storage}^{\mathrm{initial}}_{n,i} \cdot \mathit{storage}^{\mathrm{cap}}_{n,i} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{cyclic\_storage}_{n,i} \\ \mathrm{storage}^{\mathrm{retention}}_{n,i,t}^{\mathrm{timestep\_resolution}_{\mathrm{lookup\_cluster\_last\_timestep}(t)}} \cdot \mathit{storage}_{n,i,\mathrm{lookup\_cluster\_last\_timestep}(t)} & \text{if } \mathrm{cluster\_first\_timestep}_{t} \wedge \neg \left( \mathrm{pos}(t) = 0 \wedge \neg \mathrm{cyclic\_storage}_{n,i} \right) \\ \mathrm{storage}^{\mathrm{retention}}_{n,i,t}^{\mathrm{timestep\_resolution}_{t \ominus 1}} \cdot \mathit{storage}_{n,i,t \ominus 1} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T}
```

**`cost_investment_storage_cap`**

```math
\mathit{cost\_investment\_storage\_cap}_{n,i,k} = \mathrm{cost\_storage\_cap}_{n,i,k} \cdot \mathit{storage}^{\mathrm{cap}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

#### Variable domains

**`storage_cap`**

```math
\mathrm{storage}^{\mathrm{cap,min}}_{n,i} \le \mathit{storage}^{\mathrm{cap}}_{n,i} \le \mathrm{storage}^{\mathrm{cap,max}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage`**

```math
\mathit{storage}_{n,i,t} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

#### Assumptions

**`unbounded_storage_cap_cost`**

```math
\neg \left( \mathrm{cost\_storage\_cap}_{n,i,k} < 0 \right) \vee \mathrm{storage}^{\mathrm{cap,max}}_{n,i} \text{ is defined} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`storage_initial_max`**

```math
\mathrm{storage}^{\mathrm{initial}}_{n,i} \ge 0 \wedge \mathrm{storage}^{\mathrm{initial}}_{n,i} \le 1 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{storage}^{\mathrm{initial}}_{n,i} \text{ is defined}
```

**`cyclic_storage_needs_inter_cluster`**

```math
\neg \left( \mathrm{cyclic\_storage}_{n,i} \wedge \mathrm{lookup\_cluster\_last\_timestep}(t) \text{ is defined} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T}
```
<!-- gallery:end -->
