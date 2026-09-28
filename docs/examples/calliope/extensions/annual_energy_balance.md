<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Annual energy balance

An extension of [Calliope in fragments](../index.md). Calliope's example `annual_energy_balance.yaml`: limits on what a technology puts out, takes from its source or puts into its sink over the whole time.

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
  annual_flow_max:
    description: "`annual_flow_max` — the most a technology puts out over the whole time; given only where set"
    dims: [techs]
  annual_flow_max_group:
    description: >-
      `annual_flow_max` as the group row reads it — the most the group puts
      out over the whole time. Calliope reads one parameter at three shapes
      and lets the data choose; a parameter here has one, so the group's
      limit is a number of its own
    dims: []
  annual_source_max:
    description: "`annual_source_max` — the most a technology takes from its source over the whole time; given only where set"
    dims: [techs]
  annual_sink_max:
    description: "`annual_sink_max` — the most a technology puts into its sink over the whole time; given only where set"
    dims: [techs]
  flow_max_group:
    description: "`flow_max_group` — whether a technology is in the group the group limit holds for"
    dims: [techs]
    dtype: bool

expressions:
  flow_out_of_group:
    description: "`flow_out[techs=$techs]` — outflow of the technologies in the group"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      in_group:
        when: flow_max_group
        expression: flow_out
    otherwise: 0

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_in: { dims: [nodes, techs, carriers, timesteps] }
    source_use: { dims: [nodes, techs, timesteps] }

constraints:
  annual_energy_balance_per_tech_and_node:
    description: "`annual_energy_balance_per_tech_and_node` — a technology at a node puts out at most its annual limit"
    dims: [nodes, techs]
    where: annual_flow_max
    expression: sum(sum(flow_out, over=carriers), over=timesteps) <= annual_flow_max
  annual_energy_balance_global_per_tech:
    description: "`annual_energy_balance_global_per_tech` — a technology puts out at most its annual limit over every node"
    dims: [techs]
    where: annual_flow_max
    expression: sum(sum(sum(flow_out, over=nodes), over=carriers), over=timesteps) <= annual_flow_max
  annual_energy_balance_global_multi_tech:
    description: "`annual_energy_balance_global_multi_tech` — the group of technologies puts out at most its annual limit over every node"
    dims: []
    where: annual_flow_max_group
    expression: sum(flow_out_of_group) <= annual_flow_max_group
  annual_energy_balance_total_source_availability:
    description: >-
      `annual_energy_balance_total_source_availability` — a technology takes
      at most its annual limit from its source. Calliope's `where:
      source_use` over a technology reads as the technology being a supply
      one, which is where `source_use` is built
    dims: [techs]
    where: base_tech == 'supply' AND annual_source_max
    expression: sum(sum(source_use, over=nodes), over=timesteps) <= annual_source_max
  annual_energy_balance_total_sink_availability:
    description: "`annual_energy_balance_total_sink_availability` — a demand technology takes in at most its annual limit"
    dims: [techs]
    where: base_tech == 'demand' AND annual_sink_max
    expression: sum(sum(sum(flow_in, over=nodes), over=carriers), over=timesteps) <= annual_sink_max
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
| $`\mathrm{annual\_flow\_max}`$ | `annual_flow_max` over $`\mathcal{I}`$ — `annual_flow_max` — the most a technology puts out over the whole time; given only where set |
| $`\mathrm{annual\_flow\_max\_group}`$ | `annual_flow_max_group` (scalar) — `annual_flow_max` as the group row reads it — the most the group puts out over the whole time. Calliope reads one parameter at three shapes and lets the data choose; a parameter here has one, so the group's limit is a number of its own |
| $`\mathrm{annual\_source\_max}`$ | `annual_source_max` over $`\mathcal{I}`$ — `annual_source_max` — the most a technology takes from its source over the whole time; given only where set |
| $`\mathrm{annual\_sink\_max}`$ | `annual_sink_max` over $`\mathcal{I}`$ — `annual_sink_max` — the most a technology puts into its sink over the whole time; given only where set |
| $`\mathrm{flow\_max\_group}`$ | `flow_max_group` over $`\mathcal{I}`$ — `flow_max_group` — whether a technology is in the group the group limit holds for |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_in}`$ | `flow_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{source\_use}`$ | `source_use` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_out\_of\_group}`$ | `flow_out_of_group` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out[techs=$techs]` — outflow of the technologies in the group |

#### Subject to

**`annual_energy_balance_per_tech_and_node`**

```math
\sum_{t \in \mathcal{T}} \sum_{c \in \mathcal{C}} \mathit{flow\_out}_{n,i,c,t} \le \mathrm{annual\_flow\_max}_{i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{annual\_flow\_max}_{i} \text{ is defined}
```

**`annual_energy_balance_global_per_tech`**

```math
\sum_{t \in \mathcal{T}} \sum_{c \in \mathcal{C}} \sum_{n \in \mathcal{N}} \mathit{flow\_out}_{n,i,c,t} \le \mathrm{annual\_flow\_max}_{i} \qquad \forall\, i \in \mathcal{I} \,:\, \mathrm{annual\_flow\_max}_{i} \text{ is defined}
```

**`annual_energy_balance_global_multi_tech`**

```math
\sum_{n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}} \mathit{flow\_out\_of\_group}_{n,i,c,t} \le \mathrm{annual\_flow\_max\_group} \qquad \text{where } \mathrm{annual\_flow\_max\_group} \text{ is defined}
```

**`annual_energy_balance_total_source_availability`**

```math
\sum_{t \in \mathcal{T}} \sum_{n \in \mathcal{N}} \mathit{source\_use}_{n,i,t} \le \mathrm{annual\_source\_max}_{i} \qquad \forall\, i \in \mathcal{I} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'} \wedge \mathrm{annual\_source\_max}_{i} \text{ is defined}
```

**`annual_energy_balance_total_sink_availability`**

```math
\sum_{t \in \mathcal{T}} \sum_{c \in \mathcal{C}} \sum_{n \in \mathcal{N}} \mathit{flow\_in}_{n,i,c,t} \le \mathrm{annual\_sink\_max}_{i} \qquad \forall\, i \in \mathcal{I} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{demand}\text{'} \wedge \mathrm{annual\_sink\_max}_{i} \text{ is defined}
```

#### Definitions

**`flow_out_of_group`**

```math
\mathit{flow\_out\_of\_group}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } \mathrm{flow\_max\_group}_{i} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```
<!-- gallery:end -->
