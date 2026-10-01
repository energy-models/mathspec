<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Storage

One of the [ten fragments](index.md) of the GEMS port: the GEMS `storage` model. Read `Storage_level_equation`: GEMS wraps `level[t+1]` at the end of the horizon by default, and `edge='wrap'` states that in the file.

<!-- gallery:begin -->
```yaml
description: >-
  GEMS `storage`. A reservoir that injects and withdraws through its
  `injection_port`. GEMS wraps `level[t+1]` at the end of the horizon by
  default, so the shift wraps too.
dimensions:
  time: { dtype: int, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  bus: { description: "`bus` components: nodes where flows balance" }
  storage: { description: "`storage` components: reservoirs that inject and withdraw" }
relations:
  Storage_injection_port:
    key: [storage, bus]
    description: "connections from a storage's `injection_port` to a bus"
parameters:
  Storage_reservoir_capacity: { dims: [storage], description: largest level }
  Storage_injection_nominal_capacity: { dims: [storage], description: largest injection }
  Storage_withdrawal_nominal_capacity: { dims: [storage], description: largest withdrawal }
  Storage_efficiency_injection: { dims: [storage], description: share of an injection that reaches the level }
  Storage_efficiency_withdrawal: { dims: [storage], description: level taken by one unit of withdrawal }
  Storage_initial_level:
    dims: [scenario, storage]
    description: level at the first time step, as a share of the reservoir capacity
variables:
  Storage_p_injection:
    dims: [time, scenario, storage]
    bounds: { lower: 0, upper: Storage_injection_nominal_capacity }
    description: power taken from the bus into the reservoir
  Storage_p_withdrawal:
    dims: [time, scenario, storage]
    bounds: { lower: 0, upper: Storage_withdrawal_nominal_capacity }
    description: power given from the reservoir to the bus
  Storage_level:
    dims: [time, scenario, storage]
    bounds: { lower: 0, upper: Storage_reservoir_capacity }
    description: energy in the reservoir
given:
  expressions:
    Bus_balance_port_flow: { dims: [time, scenario, bus] }
expressions:
  Storage_injection_port_flow:
    description: "`injection_port.flow` of a storage, `p_withdrawal - p_injection`"
    expression: >-
      sum(Storage_p_withdrawal - Storage_p_injection,
      by=Storage_injection_port, over=storage, into=bus)
    adds_to: Bus_balance_port_flow
constraints:
  Storage_initial_level_constraint:
    dims: [time, scenario, storage]
    where: "position(time) == 0"
    description: "`storage.initial_level_constraint`: `level[0]`"
    expression: Storage_level == Storage_initial_level * Storage_reservoir_capacity
  Storage_level_equation:
    dims: [time, scenario, storage]
    description: "`storage.Level equation`, `level[t+1] = level + …`, written one step back"
    expression: >-
      Storage_level == shift(
        Storage_level
        + Storage_efficiency_injection * Storage_p_injection
        - Storage_efficiency_withdrawal * Storage_p_withdrawal,
        along=time, offset=1, edge='wrap')
```

GEMS `storage`. A reservoir that injects and withdraws through its `injection_port`. GEMS wraps `level[t+1]` at the end of the horizon by default, so the shift wraps too.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{Storage\_injection\_port} \subseteq \mathcal{O} \times \mathcal{B}`$ — `bus` components: nodes where flows balance |
| $`\mathcal{O}`$ | index $`o`$ — `storage` with $`\mathrm{Storage\_injection\_port} \subseteq \mathcal{O} \times \mathcal{B}`$ — `storage` components: reservoirs that inject and withdraw |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Storage\_reservoir\_capacity}`$ | `Storage_reservoir_capacity` over $`\mathcal{O}`$ — largest level |
| $`\mathrm{Storage\_injection\_nominal\_capacity}`$ | `Storage_injection_nominal_capacity` over $`\mathcal{O}`$ — largest injection |
| $`\mathrm{Storage\_withdrawal\_nominal\_capacity}`$ | `Storage_withdrawal_nominal_capacity` over $`\mathcal{O}`$ — largest withdrawal |
| $`\mathrm{Storage\_efficiency\_injection}`$ | `Storage_efficiency_injection` over $`\mathcal{O}`$ — share of an injection that reaches the level |
| $`\mathrm{Storage\_efficiency\_withdrawal}`$ | `Storage_efficiency_withdrawal` over $`\mathcal{O}`$ — level taken by one unit of withdrawal |
| $`\mathrm{Storage\_initial\_level}`$ | `Storage_initial_level` over $`\mathcal{S} \times \mathcal{O}`$ — level at the first time step, as a share of the reservoir capacity |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{Storage\_p\_injection}`$ | `Storage_p_injection` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{O}`$ — power taken from the bus into the reservoir |
| $`\mathit{Storage\_p\_withdrawal}`$ | `Storage_p_withdrawal` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{O}`$ — power given from the reservoir to the bus |
| $`\mathit{Storage\_level}`$ | `Storage_level` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{O}`$ — energy in the reservoir |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_balance\_port\_flow}`$ | `Bus_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$, an expression this file adds `Storage_injection_port_flow` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Storage\_injection\_port\_flow}`$ | `Storage_injection_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — `injection_port.flow` of a storage, `p_withdrawal - p_injection` |

Upright is what the data supplies — a parameter such as $`\mathrm{Storage\_reservoir\_capacity}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{Storage\_p\_injection}`$. An index is italic too, being what a quantifier chooses, and a set is script.

$`t \ominus k`$ denotes cyclic translation: index $`t-k`$ taken modulo the size of the dimension (`roll`). Plain $`t-k`$ (`shift`) has no wraparound — terms translated past the edge are simply absent.

$`\mathrm{pos}(t)`$ denotes where index $`t`$ sits along its dimension's own order — the order `shift` steps along, not the order labels sort in — counted from $`0`$. The index itself stays the coordinate, so $`t`$ compares against labels and $`\mathrm{pos}(t)`$ against positions.

#### Subject to

**`Storage_initial_level_constraint`**

```math
\mathit{Storage\_level}_{t,s,o} = \mathrm{Storage\_initial\_level}_{s,o} \cdot \mathrm{Storage\_reservoir\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O} \,:\, \mathrm{pos}(t) = 0
```

**`Storage_level_equation`**

```math
\mathit{Storage\_level}_{t,s,o} = \mathit{Storage\_level}_{t \ominus 1,s,o} + \mathrm{Storage\_efficiency\_injection}_{o} \cdot \mathit{Storage\_p\_injection}_{t \ominus 1,s,o} - \mathrm{Storage\_efficiency\_withdrawal}_{o} \cdot \mathit{Storage\_p\_withdrawal}_{t \ominus 1,s,o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

#### Definitions

**`Storage_injection_port_flow`**

```math
\mathit{Storage\_injection\_port\_flow}_{t,s,b} = \sum_{o \in \mathcal{O} \,:\, \left( o,\ b \right) \in \mathrm{Storage\_injection\_port}} \left( \mathit{Storage\_p\_withdrawal}_{t,s,o} - \mathit{Storage\_p\_injection}_{t,s,o} \right) \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

#### Variable domains

**`Storage_p_injection`**

```math
0 \le \mathit{Storage\_p\_injection}_{t,s,o} \le \mathrm{Storage\_injection\_nominal\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

**`Storage_p_withdrawal`**

```math
0 \le \mathit{Storage\_p\_withdrawal}_{t,s,o} \le \mathrm{Storage\_withdrawal\_nominal\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```

**`Storage_level`**

```math
0 \le \mathit{Storage\_level}_{t,s,o} \le \mathrm{Storage\_reservoir\_capacity}_{o} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ o \in \mathcal{O}
```
<!-- gallery:end -->
