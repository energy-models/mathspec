<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A sparse set, read four ways

Units feed buses through the ports they have, and each runs only in the
periods it is active. `connection` lists the ports of each unit and the bus
each feeds, and `active` lists the periods of each unit. Each constraint reads
the sets in one way:

- `port_limit` reads `capacity`, a parameter of each unit, at each port.
- `split` sums the flows of a unit over its ports, one column of
  `connection`.
- `ramp_up` steps `output` along `period` inside the periods of `active`.
- `balance` sums over every row of `connection`, grouped by the bus each port
  feeds.

`efficiency` and `flow` name the set `connection` in `dims:`, so they are over
`unit` and `port` where it lists a port, `missing: 1` fills only those ports,
and a data row for a port that `connection` does not list is refused.
[#1019](https://github.com/energy-models/mathspec/issues/1019) compares how
three designs for sparse sets write this spec.

<!-- gallery:begin -->
```yaml
description: >-
  Units that feed buses through the ports they have, and run only in the
  periods they are active: two sparse sets, read four ways.

dimensions:
  unit: { description: a converter }
  port: { description: an output of a unit }
  bus: { description: a node of the network }
  period: { dtype: int, ordered: true, description: a step of the horizon }

sets:
  connection:
    description: the ports a unit has
    dims: [unit, port]
    missing: absent
  active:
    description: the periods a unit runs in
    dims: [unit, period]
    missing: absent

maps:
  connection:
    bus: { dim: bus, description: the bus a port feeds }

parameters:
  efficiency: { dims: [connection, period], missing: 1, description: share of the output a port delivers }
  capacity: { dims: [unit], description: the most a unit produces in a period }
  ramp: { dims: [unit], description: the most a unit's output rises from one period to the next }
  load: { dims: [bus, period], description: demand to be met }

variables:
  output: { dims: [active], bounds: { lower: 0 }, description: what a unit produces }
  flow: { dims: [connection, period], bounds: { lower: 0 }, description: what a port takes of it }

constraints:
  port_limit:
    description: a port takes no more than the unit's capacity
    dims: [connection, period]
    expression: flow <= capacity
  split:
    description: the ports of a unit take what it produces
    dims: [unit, period]
    expression: sum(flow, over=port) == output
  ramp_up:
    description: output rises by at most the ramp from one active period to the next
    dims: [active]
    expression: output - shift(output, along=period, offset=1) <= ramp
  balance:
    description: what the ports deliver to a bus meets its load
    dims: [bus, period]
    expression: sum(efficiency * flow, over=connection, by=connection[bus]) >= load

objective:
  sense: minimize
  expression: sum(output)
```

Units that feed buses through the ports they have, and run only in the periods they are active: two sparse sets, read four ways.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{bus}: \mathrm{connection} \to \mathcal{B}`$ — a node of the network |
| $`\mathcal{T}`$ | index $`t`$ — `period` with $`\mathrm{active} \subseteq \mathcal{T} \times \mathcal{U}`$, `active` is `absent` where the data has no row — a step of the horizon |
| $`\mathcal{O}`$ | index $`o`$ — `port` with $`\mathrm{connection} \subseteq \mathcal{O} \times \mathcal{U},\ \mathrm{bus}: \mathrm{connection} \to \mathcal{B}`$, `connection` is `absent` where the data has no row — an output of a unit |
| $`\mathcal{U}`$ | index $`u`$ — `unit` with $`\mathrm{active} \subseteq \mathcal{T} \times \mathcal{U},\ \mathrm{connection} \subseteq \mathcal{O} \times \mathcal{U},\ \mathrm{bus}: \mathrm{connection} \to \mathcal{B}`$, `active` is `absent` where the data has no row, `connection` is `absent` where the data has no row — a converter |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{U}`$ — the most a unit produces in a period |
| $`\mathrm{efficiency}`$ | `efficiency` over $`\left( o,\ u \right) \in \mathrm{connection},\ t \in \mathcal{T}`$, $`1`$ where the data has no row — share of the output a port delivers |
| $`\mathrm{load}`$ | `load` over $`\mathcal{B} \times \mathcal{T}`$ — demand to be met |
| $`\mathrm{ramp}`$ | `ramp` over $`\mathcal{U}`$ — the most a unit's output rises from one period to the next |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow}`$ | `flow` over $`\left( o,\ u \right) \in \mathrm{connection},\ t \in \mathcal{T}`$ — what a port takes of it |
| $`\mathit{output}`$ | `output` over $`\left( t,\ u \right) \in \mathrm{active}`$ — what a unit produces |

#### Variable domains

**`flow`**

```math
\mathit{flow}_{t,o,u} \ge 0 \qquad \forall\, \left( o,\ u \right) \in \mathrm{connection},\ t \in \mathcal{T}
```

**`output`**

```math
\mathit{output}_{t,u} \ge 0 \qquad \forall\, \left( t,\ u \right) \in \mathrm{active}
```

#### Objective

```math
\min \sum_{t \in \mathcal{T},\ u \in \mathcal{U}} \mathit{output}_{t,u}
```

#### Subject to

**`balance`**

```math
\sum_{o \in \mathcal{O},\ u \in \mathcal{U} \,:\, \mathrm{bus}(o,\ u) = b} \mathrm{efficiency}_{t,o,u} \cdot \mathit{flow}_{t,o,u} \ge \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

**`port_limit`**

```math
\mathit{flow}_{t,o,u} \le \mathrm{capacity}_{u} \qquad \forall\, t \in \mathcal{T},\ o \in \mathcal{O},\ u \in \mathcal{U} \,:\, \left( o,\ u \right) \in \mathrm{connection}
```

**`ramp_up`**

```math
\mathit{output}_{t,u} - \mathit{output}_{t - 1,u} \le \mathrm{ramp}_{u} \qquad \forall\, t \in \mathcal{T},\ u \in \mathcal{U} \,:\, \left( t,\ u \right) \in \mathrm{active}
```

**`split`**

```math
\sum_{o \in \mathcal{O}} \mathit{flow}_{t,o,u} = \mathit{output}_{t,u} \qquad \forall\, t \in \mathcal{T},\ u \in \mathcal{U}
```
<!-- gallery:end -->
