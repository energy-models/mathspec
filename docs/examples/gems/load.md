<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Loads

This file states the GEMS `load` model. It is one of the [ten fragments](index.md)
of the GEMS port. It adds `-load` to `Bus_balance_port_flow`
through the relation `Load_balance_port`, which connects each load to a bus. A
load has no variable of its own.

<!-- gallery:begin -->
```yaml
description: GEMS `load`. A load takes a fixed demand through its `balance_port`.
dimensions:
  time: { dtype: int, ordered: true, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  bus: { description: "`bus` components: nodes where flows balance" }
  load: { description: "`load` components: fixed demands" }
relations:
  Load_balance_port: { key: [load, bus], description: "connections from a load's `balance_port` to a bus" }
parameters:
  Load_load: { dims: [time, scenario, load], description: demand }
given:
  expressions:
    Bus_balance_port_flow: { dims: [time, scenario, bus] }
expressions:
  Load_balance_port_flow:
    description: "`balance_port.flow` of a load, `-load`"
    expression: sum(-Load_load, over=load, by=Load_balance_port[bus])
    adds_to: Bus_balance_port_flow
```

GEMS `load`. A load takes a fixed demand through its `balance_port`.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{Load\_balance\_port} \subseteq \mathcal{L} \times \mathcal{B}`$ — `bus` components: nodes where flows balance |
| $`\mathcal{L}`$ | index $`l`$ — `load` with $`\mathrm{Load\_balance\_port} \subseteq \mathcal{L} \times \mathcal{B}`$ — `load` components: fixed demands |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Load\_load}`$ | `Load_load` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — demand |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_balance\_port\_flow}`$ | `Bus_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$, an expression this file adds `Load_balance_port_flow` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathrm{Load\_balance\_port\_flow}`$ | `Load_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — `balance_port.flow` of a load, `-load` |

#### Definitions

**`Load_balance_port_flow`**

```math
\mathrm{Load\_balance\_port\_flow}_{t,s,b} = \sum_{l \in \mathcal{L} \,:\, \left( l,\ b \right) \in \mathrm{Load\_balance\_port}} -\mathrm{Load\_load}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```
<!-- gallery:end -->
