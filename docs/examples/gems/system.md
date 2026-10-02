<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The system

One of the [ten fragments](index.md) of the GEMS port. It holds what a GEMS interpreter supplies around the library: the `time` and `scenario` dimensions, and the objective. The objective weighs `total_cost` in each scenario, which is the average GEMS takes.

<!-- gallery:begin -->
```yaml
description: >-
  What a GEMS interpreter supplies around the library: the time and scenario
  axes, and an objective that averages over the scenarios what each model
  adds to `total_cost`. Nothing here names a model.
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

What a GEMS interpreter supplies around the library: the time and scenario axes, and an objective that averages over the scenarios what each model adds to `total_cost`. Nothing here names a model.

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
