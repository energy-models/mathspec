<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Soft energy caps

This file states the GEMS `energy_limitation_soft_constraint_max` model. It is one of the [ten fragments](index.md)
of the GEMS port. It caps
`Energy_limit_soft_port_energy` as the
[hard cap](energy_limitation_hard_constraint_max.md) does, but a slack variable
can lift the cap, at a cost that goes to `total_cost`. A GEMS variable has a
time dimension unless it says otherwise, so the slack and the cap repeat in
each time step.

<!-- gallery:begin -->
```yaml
description: >-
  GEMS `energy_limitation_soft_constraint_max`. A cap on the energy that the
  connected ports generate over the horizon, with a priced slack. A GEMS
  variable carries time unless it says otherwise, so the slack and the row
  repeat in each time step.
dimensions:
  time: { dtype: int, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  energy_limit_soft:
    description: "`energy_limitation_soft_constraint_max` components: energy caps with a priced slack"
parameters:
  Energy_limit_soft: { dims: [energy_limit_soft], description: generation over the horizon above which the slack is paid }
  Energy_limit_soft_slack_penalty: { dims: [energy_limit_soft], description: cost of one unit of slack }
variables:
  Energy_limit_soft_slack:
    dims: [time, scenario, energy_limit_soft]
    bounds: { lower: 0 }
    description: generation above the soft cap
given:
  expressions:
    Energy_limit_soft_port_energy:
      dims: [scenario, energy_limit_soft]
      description: "`sum_connections(energy_port.cumulative_energy)`: what the connected ports generate"
    total_cost: { dims: [scenario] }
expressions:
  Energy_limit_soft_objective:
    description: "`energy_limitation_soft_constraint_max.objective`"
    expression: sum(Energy_limit_soft_slack * Energy_limit_soft_slack_penalty, over=[time, energy_limit_soft])
    adds_to: total_cost
constraints:
  Energy_limit_soft_max_generation_soft:
    dims: [time, scenario, energy_limit_soft]
    description: "`energy_limitation_soft_constraint_max.max_generation_soft`"
    expression: Energy_limit_soft_port_energy <= Energy_limit_soft + Energy_limit_soft_slack
```

GEMS `energy_limitation_soft_constraint_max`. A cap on the energy that the connected ports generate over the horizon, with a priced slack. A GEMS variable carries time unless it says otherwise, so the slack and the row repeat in each time step.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{E}`$ | index $`e`$ — `energy_limit_soft` — `energy_limitation_soft_constraint_max` components: energy caps with a priced slack |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Energy\_limit\_soft}`$ | `Energy_limit_soft` over $`\mathcal{E}`$ — generation over the horizon above which the slack is paid |
| $`\mathrm{Energy\_limit\_soft\_slack\_penalty}`$ | `Energy_limit_soft_slack_penalty` over $`\mathcal{E}`$ — cost of one unit of slack |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{Energy\_limit\_soft\_slack}`$ | `Energy_limit_soft_slack` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{E}`$ — generation above the soft cap |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Energy\_limit\_soft\_port\_energy}`$ | `Energy_limit_soft_port_energy` over $`\mathcal{S} \times \mathcal{E}`$, an expression another file defines — `sum_connections(energy_port.cumulative_energy)`: what the connected ports generate |
| $`\mathit{total\_cost}`$ | `total_cost` over $`\mathcal{S}`$, an expression this file adds `Energy_limit_soft_objective` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Energy\_limit\_soft\_objective}`$ | `Energy_limit_soft_objective` over $`\mathcal{S}`$ — `energy_limitation_soft_constraint_max.objective` |

Upright is what the data supplies — a parameter such as $`\mathrm{Energy\_limit\_soft}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{Energy\_limit\_soft\_slack}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`Energy_limit_soft_max_generation_soft`**

```math
\mathit{Energy\_limit\_soft\_port\_energy}_{s,e} \le \mathrm{Energy\_limit\_soft}_{e} + \mathit{Energy\_limit\_soft\_slack}_{t,s,e} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ e \in \mathcal{E}
```

#### Definitions

**`Energy_limit_soft_objective`**

```math
\mathit{Energy\_limit\_soft\_objective}_{s} = \sum_{t \in \mathcal{T},\ e \in \mathcal{E}} \mathit{Energy\_limit\_soft\_slack}_{t,s,e} \cdot \mathrm{Energy\_limit\_soft\_slack\_penalty}_{e} \qquad \forall\, s \in \mathcal{S}
```

#### Variable domains

**`Energy_limit_soft_slack`**

```math
\mathit{Energy\_limit\_soft\_slack}_{t,s,e} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ e \in \mathcal{E}
```
<!-- gallery:end -->
