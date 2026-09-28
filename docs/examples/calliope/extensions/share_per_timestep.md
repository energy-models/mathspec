<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Flow share per time step

An extension of [Calliope in fragments](../index.md). Calliope's example `share_per_timestep.yaml`: the same shares, in each time step.

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

relations:
  demand_share_tech:
    description: >-
      `demand_share_tech` — the demand technology whose inflow a technology
      meets a share of. Calliope slices `flow_in` by it; a read through the
      relation is that slice
    key: techs
    values: { demand: techs }
  supply_share_carrier:
    description: >-
      `supply_share_carrier` — the carrier a technology's share of outflow is
      counted in. Calliope slices `flow_out` by it, which is a test of the
      pair
    key: [techs, carriers]

parameters:
  demand_share_per_timestep_equals:
    description: "`demand_share_per_timestep_equals` — the share of a demand technology's inflow a technology meets in each time step; given only where set"
    dims: [nodes, techs, timesteps]
  supply_share_per_timestep_equals:
    description: "`supply_share_per_timestep_equals` — the share of a node's outflow of a carrier a technology puts out in each time step; given only where set"
    dims: [nodes, techs, timesteps]

expressions:
  supply_share_timestep_flow_out:
    description: "`flow_out[carriers=$carrier]` — a technology's outflow of its share carrier"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      share_carrier:
        when: supply_share_carrier
        expression: flow_out
    otherwise: 0
  supply_share_timestep_all_flow_out:
    description: "`sum(flow_out[carriers=$carrier], over=techs)` — every technology's outflow of a technology's share carrier"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      share_carrier:
        when: supply_share_carrier
        expression: sum(flow_out, over=techs)
    otherwise: 0

given:
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_in: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  demand_share_per_timestep_equals_per_tech:
    description: "`demand_share_per_timestep_equals_per_tech` — a technology puts out its share of a demand technology's inflow in each time step"
    dims: [nodes, techs, timesteps]
    where: demand_share_per_timestep_equals
    expression: >-
      sum(flow_out, over=carriers)
      == sum(at(flow_in, by=demand_share_tech, over=demand, into=techs), over=carriers)
      * demand_share_per_timestep_equals
  supply_share_per_timestep_equals_per_tech:
    description: >-
      `supply_share_per_timestep_equals_per_tech` — a technology puts out its
      share of a node's outflow of a carrier in each time step. Calliope's
      row keeps the carrier dimension of the slice; the slice here is summed
      over the one carrier it keeps
    dims: [nodes, techs, timesteps]
    where: supply_share_per_timestep_equals
    expression: >-
      sum(supply_share_timestep_flow_out, over=carriers)
      == sum(supply_share_timestep_all_flow_out, over=carriers) * supply_share_per_timestep_equals
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` with $`\mathrm{demand\_share\_tech}: \mathcal{I} \to \mathcal{I},\ \mathrm{supply\_share\_carrier} \subseteq \mathcal{I} \times \mathcal{C}`$ — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` with $`\mathrm{supply\_share\_carrier} \subseteq \mathcal{I} \times \mathcal{C}`$ — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{demand\_share\_per\_timestep\_equals}`$ | `demand_share_per_timestep_equals` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `demand_share_per_timestep_equals` — the share of a demand technology's inflow a technology meets in each time step; given only where set |
| $`\mathrm{supply\_share\_per\_timestep\_equals}`$ | `supply_share_per_timestep_equals` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `supply_share_per_timestep_equals` — the share of a node's outflow of a carrier a technology puts out in each time step; given only where set |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_in}`$ | `flow_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{supply\_share\_timestep\_flow\_out}`$ | `supply_share_timestep_flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out[carriers=$carrier]` — a technology's outflow of its share carrier |
| $`\mathit{supply\_share\_timestep\_all\_flow\_out}`$ | `supply_share_timestep_all_flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `sum(flow_out[carriers=$carrier], over=techs)` — every technology's outflow of a technology's share carrier |

#### Subject to

**`demand_share_per_timestep_equals_per_tech`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_out}_{n,i,c,t} = \left( \sum_{c \in \mathcal{C}} \mathit{flow\_in}_{n,\mathrm{demand\_share\_tech}(i),c,t} \right) \cdot \mathrm{demand\_share\_per\_timestep\_equals}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{demand\_share\_per\_timestep\_equals}_{n,i,t} \text{ is defined}
```

**`supply_share_per_timestep_equals_per_tech`**

```math
\sum_{c \in \mathcal{C}} \mathit{supply\_share\_timestep\_flow\_out}_{n,i,c,t} = \left( \sum_{c \in \mathcal{C}} \mathit{supply\_share\_timestep\_all\_flow\_out}_{n,i,c,t} \right) \cdot \mathrm{supply\_share\_per\_timestep\_equals}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{supply\_share\_per\_timestep\_equals}_{n,i,t} \text{ is defined}
```

#### Definitions

**`supply_share_timestep_flow_out`**

```math
\mathit{supply\_share\_timestep\_flow\_out}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } \left( i,\ c \right) \in \mathrm{supply\_share\_carrier} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`supply_share_timestep_all_flow_out`**

```math
\mathit{supply\_share\_timestep\_all\_flow\_out}_{n,i,c,t} = \begin{cases} \sum_{i' \in \mathcal{I}} \mathit{flow\_out}_{n,i',c,t} & \text{if } \left( i,\ c \right) \in \mathrm{supply\_share\_carrier} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```
<!-- gallery:end -->
