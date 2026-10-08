<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Hard energy caps

This file states the GEMS `energy_limitation_hard_constraint_max` model. It is one of the [ten fragments](index.md)
of the GEMS port. It reads
`Energy_limit_hard_port_energy`, which sums the energy that the connected
generators produce over the horizon, and caps it in each scenario.

<!-- gallery:begin -->
```yaml
description: >-
  GEMS `energy_limitation_hard_constraint_max`. A cap on the energy that the
  connected ports generate over the horizon, in each scenario.
dimensions:
  scenario: { dtype: int, description: scenarios of the data }
  energy_limit_hard:
    description: "`energy_limitation_hard_constraint_max` components: energy caps with no slack"
parameters:
  Energy_limit_hard: { dims: [energy_limit_hard], description: largest generation over the horizon }
given:
  expressions:
    Energy_limit_hard_port_energy:
      dims: [scenario, energy_limit_hard]
      description: "`sum_connections(energy_port.cumulative_energy)`: what the connected ports generate"
constraints:
  Energy_limit_hard_max_generation_hard:
    dims: [scenario, energy_limit_hard]
    description: "`energy_limitation_hard_constraint_max.max_generation_hard`"
    expression: Energy_limit_hard_port_energy <= Energy_limit_hard
```

GEMS `energy_limitation_hard_constraint_max`. A cap on the energy that the connected ports generate over the horizon, in each scenario.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{E}`$ | index $`e`$ — `energy_limit_hard` — `energy_limitation_hard_constraint_max` components: energy caps with no slack |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Energy\_limit\_hard}`$ | `Energy_limit_hard` over $`\mathcal{E}`$ — largest generation over the horizon |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Energy\_limit\_hard\_port\_energy}`$ | `Energy_limit_hard_port_energy` over $`\mathcal{S} \times \mathcal{E}`$, an expression another file defines — `sum_connections(energy_port.cumulative_energy)`: what the connected ports generate |

#### Subject to

**`Energy_limit_hard_max_generation_hard`**

```math
\mathit{Energy\_limit\_hard\_port\_energy}_{s,e} \le \mathrm{Energy\_limit\_hard}_{e} \qquad \forall\, s \in \mathcal{S},\ e \in \mathcal{E}
```
<!-- gallery:end -->
