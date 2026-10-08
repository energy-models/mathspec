<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Buses

This file states the GEMS `bus` model. It is one of the [ten fragments](index.md)
of the GEMS port. It reads `Bus_balance_port_flow` under
[`given`](../../reference/language/declarations.md#given). Each connected port adds a term to that sum, so
the bus names no model that connects to it. The bus adds its spillage and
unsupplied-energy costs to `total_cost`.

<!-- gallery:begin -->
```yaml
description: >-
  GEMS `bus`. When the connected ports put in more than they take out, the bus
  spills the surplus. When they take out more, the bus records the shortfall
  as unsupplied energy. The bus reads the sum of its `balance_port` and names
  no model that connects to it.
dimensions:
  time: { dtype: int, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  bus: { description: "`bus` components: nodes where flows balance" }
parameters:
  Bus_spillage_cost: { dims: [bus], description: cost of one unit of spillage }
  Bus_unsupplied_energy_cost: { dims: [bus], description: cost of one unit of unsupplied energy }
variables:
  Bus_spillage: { dims: [time, scenario, bus], bounds: { lower: 0 }, description: injection that the bus cannot use }
  Bus_unsupplied_energy: { dims: [time, scenario, bus], bounds: { lower: 0 }, description: demand that the bus cannot meet }
given:
  expressions:
    Bus_balance_port_flow:
      dims: [time, scenario, bus]
      description: "`sum_connections(balance_port.flow)`: what the connected ports put into a bus"
    total_cost: { dims: [scenario] }
expressions:
  Bus_objective:
    description: "`bus.objective`"
    expression: sum(Bus_spillage_cost * Bus_spillage + Bus_unsupplied_energy_cost * Bus_unsupplied_energy, over=[time, bus])
    adds_to: total_cost
constraints:
  Bus_balance:
    dims: [time, scenario, bus]
    description: "`bus.balance`"
    expression: Bus_balance_port_flow == Bus_spillage - Bus_unsupplied_energy
```

GEMS `bus`. When the connected ports put in more than they take out, the bus spills the surplus. When they take out more, the bus records the shortfall as unsupplied energy. The bus reads the sum of its `balance_port` and names no model that connects to it.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{B}`$ | index $`b`$ — `bus` — `bus` components: nodes where flows balance |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Bus\_spillage\_cost}`$ | `Bus_spillage_cost` over $`\mathcal{B}`$ — cost of one unit of spillage |
| $`\mathrm{Bus\_unsupplied\_energy\_cost}`$ | `Bus_unsupplied_energy_cost` over $`\mathcal{B}`$ — cost of one unit of unsupplied energy |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_spillage}`$ | `Bus_spillage` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — injection that the bus cannot use |
| $`\mathit{Bus\_unsupplied\_energy}`$ | `Bus_unsupplied_energy` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — demand that the bus cannot meet |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_balance\_port\_flow}`$ | `Bus_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$, an expression another file defines — `sum_connections(balance_port.flow)`: what the connected ports put into a bus |
| $`\mathit{total\_cost}`$ | `total_cost` over $`\mathcal{S}`$, an expression this file adds `Bus_objective` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_objective}`$ | `Bus_objective` over $`\mathcal{S}`$ — `bus.objective` |

Upright is what the data supplies — a parameter such as $`\mathrm{Bus\_spillage\_cost}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{Bus\_spillage}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`Bus_balance`**

```math
\mathit{Bus\_balance\_port\_flow}_{t,s,b} = \mathit{Bus\_spillage}_{t,s,b} - \mathit{Bus\_unsupplied\_energy}_{t,s,b} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

#### Definitions

**`Bus_objective`**

```math
\mathit{Bus\_objective}_{s} = \sum_{t \in \mathcal{T},\ b \in \mathcal{B}} \left( \mathrm{Bus\_spillage\_cost}_{b} \cdot \mathit{Bus\_spillage}_{t,s,b} + \mathrm{Bus\_unsupplied\_energy\_cost}_{b} \cdot \mathit{Bus\_unsupplied\_energy}_{t,s,b} \right) \qquad \forall\, s \in \mathcal{S}
```

#### Variable domains

**`Bus_spillage`**

```math
\mathit{Bus\_spillage}_{t,s,b} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

**`Bus_unsupplied_energy`**

```math
\mathit{Bus\_unsupplied\_energy}_{t,s,b} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```
<!-- gallery:end -->
