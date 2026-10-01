<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Renewables

One of the [ten fragments](index.md) of the GEMS port: the GEMS `renewable` model. It adds its fixed generation to `Bus_balance_port_flow`.

<!-- gallery:begin -->
```yaml
description: GEMS `renewable`. A fixed generation, given through its `balance_port`.
dimensions:
  time: { dtype: int, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  bus: { description: "`bus` components: nodes where flows balance" }
  renewable: { description: "`renewable` components: fixed generation" }
relations:
  Renewable_balance_port:
    key: [renewable, bus]
    description: "connections from a renewable's `balance_port` to a bus"
parameters:
  Renewable_generation: { dims: [time, scenario, renewable], description: generation }
given:
  expressions:
    Bus_balance_port_flow: { dims: [time, scenario, bus] }
expressions:
  Renewable_balance_port_flow:
    description: "`balance_port.flow` of a renewable, `generation`"
    expression: sum(Renewable_generation, by=Renewable_balance_port, over=renewable, into=bus)
    adds_to: Bus_balance_port_flow
```

GEMS `renewable`. A fixed generation, given through its `balance_port`.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{Renewable\_balance\_port} \subseteq \mathcal{R} \times \mathcal{B}`$ — `bus` components: nodes where flows balance |
| $`\mathcal{R}`$ | index $`r`$ — `renewable` with $`\mathrm{Renewable\_balance\_port} \subseteq \mathcal{R} \times \mathcal{B}`$ — `renewable` components: fixed generation |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Renewable\_generation}`$ | `Renewable_generation` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{R}`$ — generation |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_balance\_port\_flow}`$ | `Bus_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$, an expression this file adds `Renewable_balance_port_flow` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathrm{Renewable\_balance\_port\_flow}`$ | `Renewable_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — `balance_port.flow` of a renewable, `generation` |

#### Definitions

**`Renewable_balance_port_flow`**

```math
\mathrm{Renewable\_balance\_port\_flow}_{t,s,b} = \sum_{r \in \mathcal{R} \,:\, \left( r,\ b \right) \in \mathrm{Renewable\_balance\_port}} \mathrm{Renewable\_generation}_{t,s,r} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```
<!-- gallery:end -->
