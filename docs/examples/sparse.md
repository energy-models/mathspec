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

`connection` is a dimension whose labels are the pairs of a unit and a port.
`efficiency` and `flow` are over it, so `missing: 1` fills only the ports it
lists, and a data row for a port it does not list is refused. `active` has the
ordered member `period`, along which `ramp_up` steps, so it stays a relation
that `output` reads in its `where:`.
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
  connection: { over: [unit, port], description: the ports a unit has }

relations:
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
  output: { dims: [unit, period], where: active, bounds: { lower: 0 }, description: what a unit produces }
  flow: { dims: [connection, period], bounds: { lower: 0 }, description: what a port takes of it }

constraints:
  port_limit:
    description: a port takes no more than the unit's capacity
    dims: [connection, period]
    expression: flow <= at(capacity, by=connection[unit])
  split:
    description: the ports of a unit take what it produces
    dims: [unit, period]
    expression: sum(flow, over=connection, by=connection[unit]) == output
  ramp_up:
    description: output rises by at most the ramp from one active period to the next
    dims: [unit, period]
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
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{bus}: \mathcal{C} \to \mathcal{B}`$ — a node of the network |
| $`\mathcal{C}`$ | index $`c`$ — `connection`, $`\mathcal{C} \subseteq \mathcal{O} \times \mathcal{U}`$ with $`\mathrm{bus}: \mathcal{C} \to \mathcal{B}`$ — the ports a unit has |
| $`\mathcal{T}`$ | index $`t`$ — `period` with $`\mathrm{active} \subseteq \mathcal{T} \times \mathcal{U}`$, `active` is `absent` where the data has no row — a step of the horizon |
| $`\mathcal{O}`$ | index $`o`$ — `port` — an output of a unit |
| $`\mathcal{U}`$ | index $`u`$ — `unit` with $`\mathrm{active} \subseteq \mathcal{T} \times \mathcal{U}`$, `active` is `absent` where the data has no row — a converter |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{U}`$ — the most a unit produces in a period |
| $`\mathrm{efficiency}`$ | `efficiency` over $`\mathcal{C} \times \mathcal{T}`$, $`1`$ where the data has no row — share of the output a port delivers |
| $`\mathrm{load}`$ | `load` over $`\mathcal{B} \times \mathcal{T}`$ — demand to be met |
| $`\mathrm{ramp}`$ | `ramp` over $`\mathcal{U}`$ — the most a unit's output rises from one period to the next |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow}`$ | `flow` over $`\mathcal{C} \times \mathcal{T}`$ — what a port takes of it |
| $`\mathit{output}`$ | `output` over $`\mathcal{T} \times \mathcal{U}`$ — what a unit produces |

#### Variable domains

**`flow`**

```math
\mathit{flow}_{c,t} \ge 0 \qquad \forall\, c \in \mathcal{C},\ t \in \mathcal{T}
```

**`output`**

```math
\mathit{output}_{t,u} \ge 0 \qquad \forall\, t \in \mathcal{T},\ u \in \mathcal{U} \,:\, \left( t,\ u \right) \in \mathrm{active}
```

#### Objective

```math
\min \sum_{t \in \mathcal{T},\ u \in \mathcal{U}} \mathit{output}_{t,u}
```

#### Subject to

**`balance`**

```math
\sum_{c \in \mathcal{C} \,:\, \mathrm{bus}(c) = b} \mathrm{efficiency}_{c,t} \cdot \mathit{flow}_{c,t} \ge \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

**`port_limit`**

```math
\mathit{flow}_{c,t} \le \mathrm{capacity}_{\mathrm{unit}(c)} \qquad \forall\, c \in \mathcal{C},\ t \in \mathcal{T}
```

**`ramp_up`**

```math
\mathit{output}_{t,u} - \mathit{output}_{t - 1,u} \le \mathrm{ramp}_{u} \qquad \forall\, t \in \mathcal{T},\ u \in \mathcal{U}
```

**`split`**

```math
\sum_{c \in \mathcal{C} \,:\, \mathrm{unit}(c) = u} \mathit{flow}_{c,t} = \mathit{output}_{t,u} \qquad \forall\, t \in \mathcal{T},\ u \in \mathcal{U}
```
<!-- gallery:end -->
