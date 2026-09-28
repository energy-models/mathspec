<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Settings

One of the base fragments of [Calliope in fragments](index.md). The weightings every topic reads, and the objective. The objective is the system cost plus a penalty, and both are sums other files add to, so this file names no technology.

<!-- gallery:begin -->
```yaml
dimensions:
  timesteps:
    description: Calliope's `timesteps` — time steps, in order
    dtype: datetime
  costs:
    description: Calliope's `costs` — cost classes, such as monetary and CO2

parameters:
  timestep_resolution:
    description: >-
      `timestep_resolution` — hours a time step lasts. Calliope's default is
      1, and data prep fills it
    dims: [timesteps]
  timestep_weights:
    description: >-
      `timestep_weights` — how many times a time step counts, as after
      clustering. Calliope's default is 1, and data prep fills it
    dims: [timesteps]
  objective_cost_weights:
    description: >-
      `objective_cost_weights` — what one unit of a cost class weighs in the
      objective. Calliope's default is 1, and data prep fills it
    dims: [costs]
  bigM:
    description: >-
      `bigM` — a number larger than any decision can take. Calliope's
      default is 1e6, and data prep fills it
    dims: []

expressions:
  system_cost:
    description: >-
      the weighted cost of the system, over every cost class — Calliope's
      `min_cost_optimisation` less its unmet-demand penalty. The cost file and
      every file that prices something outside a technology add to it
    dims: []
    empty: true
  penalty:
    description: >-
      what the objective adds to the system cost to keep a model feasible —
      Calliope's `$unmet_demand` sub-expression. It is zero, and a file that
      keeps a model feasible adds to it
    dims: []
    expression: "0"

objective:
  description: >-
    `min_cost_optimisation` — the weighted cost of installing and operating
    every technology, plus the penalty on unmet demand
  sense: minimize
  expression: system_cost + penalty
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$ — `timestep_resolution` — hours a time step lasts. Calliope's default is 1, and data prep fills it |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$ — `timestep_weights` — how many times a time step counts, as after clustering. Calliope's default is 1, and data prep fills it |
| $`\mathrm{objective\_cost\_weights}`$ | `objective_cost_weights` over $`\mathcal{K}`$ — `objective_cost_weights` — what one unit of a cost class weighs in the objective. Calliope's default is 1, and data prep fills it |
| $`\mathrm{bigM}`$ | `bigM` (scalar) — `bigM` — a number larger than any decision can take. Calliope's default is 1e6, and data prep fills it |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathrm{penalty}`$ | `penalty` (scalar) — what the objective adds to the system cost to keep a model feasible — Calliope's `$unmet_demand` sub-expression. It is zero, and a file that keeps a model feasible adds to it |
| $`\mathit{system\_cost}`$ | `system_cost` (scalar) — the weighted cost of the system, over every cost class — Calliope's `min_cost_optimisation` less its unmet-demand penalty. The cost file and every file that prices something outside a technology add to it |

#### Objective

```math
\min \mathit{system\_cost} + \mathrm{penalty}
```

#### Definitions

**`penalty`**

```math
\mathrm{penalty} = 0
```

**`system_cost`**

```math
\mathit{system\_cost} = \cdots
```
<!-- gallery:end -->
