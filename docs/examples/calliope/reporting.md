<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Reporting

One of the base fragments of [Calliope in fragments](index.md). Calliope's postprocessed results: capacity factors, total generation and levelised costs. Every entry is reported, so none of it is in the math, and a quotient may divide by a variable.

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

given:
  parameters:
    timestep_resolution: { dims: [timesteps] }
    timestep_weights: { dims: [timesteps] }
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_export: { dims: [nodes, techs, carriers, timesteps] }
  expressions:
    cost: { dims: [nodes, techs, costs] }

expressions:
  capacity_factor:
    description: "`capacity_factor` — the share of its flow capacity a technology puts out in a time step"
    expression: flow_out / (flow_cap * timestep_resolution)
  systemwide_capacity_factor:
    description: "`systemwide_capacity_factor` — the share of its flow capacity a technology puts out over every node and time step"
    expression: >-
      sum(flow_out * timestep_weights, over=[nodes, timesteps])
      / (sum(flow_cap, over=nodes) * sum(timestep_resolution * timestep_weights, over=timesteps))
  total_generation:
    description: >-
      `total_generation` — outflow over every node and time step. Calliope
      weights only the export, as written here
    expression: sum(flow_out + flow_export * timestep_weights, over=[nodes, timesteps])
  systemwide_levelised_cost:
    description: "`systemwide_levelised_cost` — a technology's cost per unit of what it generates, over every node"
    expression: sum(cost, over=nodes) / total_generation
  total_levelised_cost:
    description: "`total_levelised_cost` — the system's cost per unit of a carrier generated"
    expression: sum(cost, over=[nodes, techs]) / sum(total_generation, over=techs)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_export}`$ | `flow_export` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{cost}`$ | `cost` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{K}`$, an expression another file defines |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{capacity\_factor}`$ | `capacity_factor` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `capacity_factor` — the share of its flow capacity a technology puts out in a time step |
| $`\mathit{systemwide\_capacity\_factor}`$ | `systemwide_capacity_factor` over $`\mathcal{I} \times \mathcal{C}`$ — `systemwide_capacity_factor` — the share of its flow capacity a technology puts out over every node and time step |
| $`\mathit{total\_generation}`$ | `total_generation` over $`\mathcal{I} \times \mathcal{C}`$ — `total_generation` — outflow over every node and time step. Calliope weights only the export, as written here |
| $`\mathit{systemwide\_levelised\_cost}`$ | `systemwide_levelised_cost` over $`\mathcal{I} \times \mathcal{C} \times \mathcal{K}`$ — `systemwide_levelised_cost` — a technology's cost per unit of what it generates, over every node |
| $`\mathit{total\_levelised\_cost}`$ | `total_levelised_cost` over $`\mathcal{C} \times \mathcal{K}`$ — `total_levelised_cost` — the system's cost per unit of a carrier generated |

#### Definitions

**`capacity_factor`**

```math
\mathit{capacity\_factor}_{n,i,c,t} = \frac{\mathit{flow\_out}_{n,i,c,t}}{\mathit{flow\_cap}_{n,i,c} \cdot \mathrm{timestep\_resolution}_{t}} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`systemwide_capacity_factor`**

```math
\mathit{systemwide\_capacity\_factor}_{i,c} = \frac{\sum_{n \in \mathcal{N},\ t \in \mathcal{T}} \mathit{flow\_out}_{n,i,c,t} \cdot \mathrm{timestep\_weights}_{t}}{\left( \sum_{n \in \mathcal{N}} \mathit{flow\_cap}_{n,i,c} \right) \cdot \left( \sum_{t \in \mathcal{T}} \mathrm{timestep\_resolution}_{t} \cdot \mathrm{timestep\_weights}_{t} \right)} \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C}
```

**`total_generation`**

```math
\mathit{total\_generation}_{i,c} = \sum_{n \in \mathcal{N},\ t \in \mathcal{T}} \left( \mathit{flow\_out}_{n,i,c,t} + \mathit{flow\_export}_{n,i,c,t} \cdot \mathrm{timestep\_weights}_{t} \right) \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C}
```

**`systemwide_levelised_cost`**

```math
\mathit{systemwide\_levelised\_cost}_{i,c,k} = \frac{\sum_{n \in \mathcal{N}} \mathit{cost}_{n,i,k}}{\mathit{total\_generation}_{i,c}} \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C},\ k \in \mathcal{K}
```

**`total_levelised_cost`**

```math
\mathit{total\_levelised\_cost}_{c,k} = \frac{\sum_{n \in \mathcal{N},\ i \in \mathcal{I}} \mathit{cost}_{n,i,k}}{\sum_{i \in \mathcal{I}} \mathit{total\_generation}_{i,c}} \qquad \forall\, c \in \mathcal{C},\ k \in \mathcal{K}
```
<!-- gallery:end -->
