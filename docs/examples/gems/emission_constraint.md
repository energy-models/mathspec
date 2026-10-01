<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Emission caps

One of the [ten fragments](index.md) of the GEMS port: the GEMS `emission_constraint` model. It reads `Emission_port_co2`, the CO2 that the connected generators release over the horizon, and caps it in each scenario.

<!-- gallery:begin -->
```yaml
description: >-
  GEMS `emission_constraint`. A cap on the CO2 that the connected ports
  release over the horizon, in each scenario.
dimensions:
  scenario: { dtype: int, description: scenarios of the data }
  emission_limit: { description: "`emission_constraint` components: system-wide CO2 caps" }
parameters:
  Emission_limit: { dims: [emission_limit], description: largest CO2 release over the horizon }
given:
  expressions:
    Emission_port_co2:
      dims: [scenario, emission_limit]
      description: "`sum_connections(emission_port.co2)`: what the connected ports release"
constraints:
  Emission_limit_co2_constraint:
    dims: [scenario, emission_limit]
    description: "`emission_constraint.co2_constraint`"
    expression: Emission_port_co2 <= Emission_limit
```

GEMS `emission_constraint`. A cap on the CO2 that the connected ports release over the horizon, in each scenario.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{E}`$ | index $`e`$ — `emission_limit` — `emission_constraint` components: system-wide CO2 caps |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Emission\_limit}`$ | `Emission_limit` over $`\mathcal{E}`$ — largest CO2 release over the horizon |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Emission\_port\_co2}`$ | `Emission_port_co2` over $`\mathcal{S} \times \mathcal{E}`$, an expression another file defines — `sum_connections(emission_port.co2)`: what the connected ports release |

#### Subject to

**`Emission_limit_co2_constraint`**

```math
\mathit{Emission\_port\_co2}_{s,e} \le \mathrm{Emission\_limit}_{e} \qquad \forall\, s \in \mathcal{S},\ e \in \mathcal{E}
```
<!-- gallery:end -->
