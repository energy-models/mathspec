<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Demand

One of the base fragments of [Calliope in fragments](index.md). Demand technologies: the sink a technology puts into, required, capped or floored per time step. The sink scaler reads `area_use`, as the source scaler does.

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

parameters:
  sink_use_min:
    description: "`sink_use_min` — least sink use in a time step, per unit of `sink_unit`"
    dims: [nodes, techs, timesteps]
  sink_use_max:
    description: "`sink_use_max` — most sink use in a time step, per unit of `sink_unit`; given only where set"
    dims: [nodes, techs, timesteps]
  sink_use_equals:
    description: "`sink_use_equals` — the sink use required in a time step, such as a demand profile; given only where set"
    dims: [nodes, techs, timesteps]
  sink_unit:
    description: >-
      `sink_unit` — what the sink is per: `absolute`, `per_area` of area
      use, or `per_cap` of flow capacity. Calliope's default is
      `absolute`, which is what a technology with no row reads as
    dims: [nodes, techs]
    dtype: str

expressions:
  flow_cap_in:
    description: "`where(flow_cap, carrier_in)` — the flow capacity of the carriers a technology consumes"
    dims: [nodes, techs, carriers]
    cases:
      consumed:
        when: carrier_in
        expression: flow_cap
    otherwise: 0
  sink_scaler:
    description: "`$sink_scaler` — what the sink parameters are per: area use, flow capacity, or one"
    dims: [nodes, techs]
    cases:
      per_area:
        when: sink_unit == per_area
        expression: area_use
      per_cap:
        when: sink_unit == per_cap
        expression: sum(flow_cap_in, over=carriers)
    otherwise: 1

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    carrier_in: { dims: [nodes, techs, carriers], dtype: bool }
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
    area_use: { dims: [nodes, techs] }
  expressions:
    flow_in_inc_eff: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  balance_demand_equals:
    description: "`balance_demand` where `sink_use_equals` is set — a demand technology takes in what its sink requires"
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_in AND base_tech == 'demand' AND sink_use_equals
    expression: flow_in_inc_eff == sink_use_equals * sink_scaler
  balance_demand_max:
    description: "`balance_demand` where only `sink_use_max` is set — a demand technology takes in at most what its sink allows"
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_in AND base_tech == 'demand' AND NOT sink_use_equals AND sink_use_max
    expression: flow_in_inc_eff <= sink_use_max * sink_scaler
  balance_demand_min_use:
    description: "`balance_demand_min_use` — a demand technology takes in at least its least sink use"
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_in AND sink_use_min AND NOT sink_use_equals AND base_tech == 'demand'
    expression: flow_in_inc_eff >= sink_use_min * sink_scaler

assumptions:
  finite_sink_use:
    description: Calliope's `finite_source_use`, for the sink — a required use is finite
    holds: NOT sink_use_equals == inf
  sink_unit_one_of:
    description: Calliope's `one_of` on `sink_unit`
    holds: sink_unit == absolute OR sink_unit == per_area OR sink_unit == per_cap
    where: sink_unit
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{sink\_use\_min}`$ | `sink_use_min` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `sink_use_min` — least sink use in a time step, per unit of `sink_unit` |
| $`\mathrm{sink\_use\_max}`$ | `sink_use_max` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `sink_use_max` — most sink use in a time step, per unit of `sink_unit`; given only where set |
| $`\mathrm{sink\_use\_equals}`$ | `sink_use_equals` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `sink_use_equals` — the sink use required in a time step, such as a demand profile; given only where set |
| $`\mathrm{sink\_unit}`$ | `sink_unit` over $`\mathcal{N} \times \mathcal{I}`$ — `sink_unit` — what the sink is per: `absolute`, `per_area` of area use, or `per_cap` of flow capacity. Calliope's default is `absolute`, which is what a technology with no row reads as |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{carrier\_in}`$ | `carrier_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{area\_use}`$ | `area_use` over $`\mathcal{N} \times \mathcal{I}`$ |
| $`\mathit{flow\_in\_inc\_eff}`$ | `flow_in_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_cap\_in}`$ | `flow_cap_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `where(flow_cap, carrier_in)` — the flow capacity of the carriers a technology consumes |
| $`\mathit{sink\_scaler}`$ | `sink_scaler` over $`\mathcal{N} \times \mathcal{I}`$ — `$sink_scaler` — what the sink parameters are per: area use, flow capacity, or one |

#### Subject to

**`balance_demand_equals`**

```math
\mathit{flow\_in\_inc\_eff}_{n,i,c,t} = \mathrm{sink\_use\_equals}_{n,i,t} \cdot \mathit{sink\_scaler}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_in}_{n,i,c} \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{demand}\text{'} \wedge \mathrm{sink\_use\_equals}_{n,i,t} \text{ is defined}
```

**`balance_demand_max`**

```math
\mathit{flow\_in\_inc\_eff}_{n,i,c,t} \le \mathrm{sink\_use\_max}_{n,i,t} \cdot \mathit{sink\_scaler}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_in}_{n,i,c} \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{demand}\text{'} \wedge \neg \left( \mathrm{sink\_use\_equals}_{n,i,t} \text{ is defined} \right) \wedge \mathrm{sink\_use\_max}_{n,i,t} \text{ is defined}
```

**`balance_demand_min_use`**

```math
\mathit{flow\_in\_inc\_eff}_{n,i,c,t} \ge \mathrm{sink\_use\_min}_{n,i,t} \cdot \mathit{sink\_scaler}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_in}_{n,i,c} \wedge \mathrm{sink\_use\_min}_{n,i,t} \text{ is defined} \wedge \neg \left( \mathrm{sink\_use\_equals}_{n,i,t} \text{ is defined} \right) \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{demand}\text{'}
```

#### Definitions

**`flow_cap_in`**

```math
\mathit{flow\_cap\_in}_{n,i,c} = \begin{cases} \mathit{flow\_cap}_{n,i,c} & \text{if } \mathrm{carrier\_in}_{n,i,c} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C}
```

**`sink_scaler`**

```math
\mathit{sink\_scaler}_{n,i} = \begin{cases} \mathit{area\_use}_{n,i} & \text{if } \mathrm{sink\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'} \\ \sum_{c \in \mathcal{C}} \mathit{flow\_cap\_in}_{n,i,c} & \text{if } \mathrm{sink\_unit}_{n,i} = \text{'}\mathrm{per\_cap}\text{'} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I}
```

#### Assumptions

**`finite_sink_use`**

```math
\neg \left( \mathrm{sink\_use\_equals}_{n,i,t} = \infty \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T}
```

**`sink_unit_one_of`**

```math
\mathrm{sink\_unit}_{n,i} = \text{'}\mathrm{absolute}\text{'} \vee \mathrm{sink\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'} \vee \mathrm{sink\_unit}_{n,i} = \text{'}\mathrm{per\_cap}\text{'} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{sink\_unit}_{n,i} \text{ is defined}
```
<!-- gallery:end -->
