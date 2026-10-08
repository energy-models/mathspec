<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The system

This file is one of the [ten fragments](index.md) of the GEMS port. It
declares what a GEMS interpreter supplies around the models: the `scenario`
dimension, the weight of each scenario, and the objective. The objective sums
`total_cost` over the scenarios, each multiplied by `Scenario_weight`. GEMS
takes the average, so each weight is one over the number of scenarios.

<!-- gallery:begin -->
```yaml
description: >-
  What a GEMS interpreter supplies around the library: the scenario
  dimension, and an objective. The objective averages `total_cost` over the
  scenarios, and each model adds its cost to `total_cost`. This file names no
  model.
dimensions:
  scenario: { dtype: int, description: scenarios of the data }
parameters:
  Scenario_weight:
    dims: [scenario]
    description: >-
      what a scenario weighs in the objective. GEMS takes the average, so each
      weight is one over the number of scenarios
given:
  expressions:
    total_cost:
      dims: [scenario]
      description: the objective contributions of every model, in one scenario
objective:
  sense: minimize
  expression: sum(total_cost * Scenario_weight, over=scenario)
```

What a GEMS interpreter supplies around the library: the scenario dimension, and an objective. The objective averages `total_cost` over the scenarios, and each model adds its cost to `total_cost`. This file names no model.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Scenario\_weight}`$ | `Scenario_weight` over $`\mathcal{S}`$ — what a scenario weighs in the objective. GEMS takes the average, so each weight is one over the number of scenarios |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{total\_cost}`$ | `total_cost` over $`\mathcal{S}`$, an expression another file defines — the objective contributions of every model, in one scenario |

#### Objective

```math
\min \sum_{s \in \mathcal{S}} \mathit{total\_cost}_{s} \cdot \mathrm{Scenario\_weight}_{s}
```
<!-- gallery:end -->
