<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Unit commitment

This spec adds an on/off decision per unit and a start-up ramp to [least-cost
dispatch](dispatch.md). Read `previous_status` first, then `ramp_up`.
`previous_status` is the state that a unit carries into a snapshot, and the file
states its three regimes once, under
[`cases:`](../reference/language/named.md#cases). `ramp_up` reads
`previous_status` as it reads a parameter, so one inequality covers a running
unit and a starting unit. The typesetter prints the cases once, under
**Definitions** below.

<!-- gallery:begin -->
```yaml
description: >-
  Unit commitment with a start-up ramp, the formulation `cases:` exists for.
  The state a unit carries into a snapshot has three regimes — a unit that is
  never off, the first snapshot, and every later one — and writing them at the
  constraint would fork `ramp_up` three ways. With the regimes named once, the
  inequality is written once.

dimensions:
  snapshot: { dtype: int, description: dispatch periods, ordered: true }
  generator: { description: generating units }

parameters:
  committable: { dims: [generator], dtype: bool, description: whether the unit may be switched off }
  status_initial: { dims: [generator], description: whether the unit was running before the horizon }
  capacity: { dims: [generator], description: installed capacity }
  min_output: { dims: [generator], description: output floor while running }
  ramp_limit: { dims: [generator], description: how far output may move between snapshots while running }
  start_up_limit: { dims: [generator], description: how far it may move in the snapshot it starts in }
  load: { dims: [snapshot], description: demand to be met }
  cost: { dims: [generator], description: marginal cost }

variables:
  dispatch:
    description: output of a generator in a snapshot
    dims: [snapshot, generator]
    bounds: { lower: 0, upper: capacity }
  status:
    description: whether the unit is running in a snapshot
    dims: [snapshot, generator]
    domain: binary

expressions:
  previous_status:
    description: the commitment state a unit carries into a snapshot
    dims: [snapshot, generator]
    cases:
      always_on:
        when: "not committable"
        expression: 1
      boundary:
        when: "committable and position(snapshot) == 0"
        expression: status_initial
    otherwise: shift(status, along=snapshot, offset=1)

constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load
  upper:
    description: a unit that is not running produces nothing
    dims: [snapshot, generator]
    expression: dispatch <= status * capacity
  lower:
    description: and one that is running produces at least its floor
    dims: [snapshot, generator]
    expression: dispatch >= status * min_output
  ramp_up:
    description: >-
      one inequality for both regimes — a unit already running is held to
      `ramp_limit`, a unit starting up to `start_up_limit`.
    dims: [snapshot, generator]
    expression: >-
      dispatch - shift(dispatch, along=snapshot, offset=1, edge=0)
      <= ramp_limit * previous_status + start_up_limit * (1 - previous_status)

assumptions:
  output_floor_fits_under_the_cap:
    holds: "min_output <= capacity"
    where: "committable"
    description: >-
      `lower` and `upper` hold one dispatch between them, so a floor above the
      cap makes a running unit infeasible rather than expensive. A unit that
      cannot be switched off is held to its floor in every snapshot, so the
      check is the committable ones'.

objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

Unit commitment with a start-up ramp, the formulation `cases:` exists for. The state a unit carries into a snapshot has three regimes — a unit that is never off, the first snapshot, and every later one — and writing them at the constraint would fork `ramp_up` three ways. With the regimes named once, the inequality is written once.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{committable}`$ | `committable` over $`\mathcal{G}`$ — whether the unit may be switched off |
| $`\mathrm{status}^{\mathrm{initial}}`$ | `status_initial` over $`\mathcal{G}`$ — whether the unit was running before the horizon |
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{G}`$ — installed capacity |
| $`\mathrm{min\_output}`$ | `min_output` over $`\mathcal{G}`$ — output floor while running |
| $`\mathrm{ramp\_limit}`$ | `ramp_limit` over $`\mathcal{G}`$ — how far output may move between snapshots while running |
| $`\mathrm{start\_up\_limit}`$ | `start_up_limit` over $`\mathcal{G}`$ — how far it may move in the snapshot it starts in |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{G}`$ — marginal cost |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{G} \times \mathcal{T}`$ — output of a generator in a snapshot |
| $`\mathit{status}`$ | `status` over $`\mathcal{G} \times \mathcal{T}`$ — whether the unit is running in a snapshot |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{previous\_status}`$ | `previous_status` over $`\mathcal{G} \times \mathcal{T}`$ — the commitment state a unit carries into a snapshot |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |

#### Variable domains

**`dispatch`**

```math
0 \le \mathit{dispatch}_{g,t} \le \mathrm{capacity}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

**`status`**

```math
\mathit{status}_{g,t} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Definitions

**`previous_status`**

```math
\mathit{previous\_status}_{g,t} = \begin{cases} 1 & \text{if } \neg \mathrm{committable}_{g} \\ \mathrm{status}^{\mathrm{initial}}_{g} & \text{if } \mathrm{committable}_{g} \wedge \mathrm{pos}(t) = 0 \\ \mathit{status}_{g,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Objective

```math
\min \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} \mathit{dispatch}_{g,t} \cdot \mathrm{cost}_{g}
```

#### Subject to

**`power_balance`**

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{g,t} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

**`upper`**

```math
\mathit{dispatch}_{g,t} \le \mathit{status}_{g,t} \cdot \mathrm{capacity}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

**`lower`**

```math
\mathit{dispatch}_{g,t} \ge \mathit{status}_{g,t} \cdot \mathrm{min\_output}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

**`ramp_up`**

```math
\mathit{dispatch}_{g,t} - \mathit{dispatch}_{g,t \boxminus_{0} 1} \le \mathrm{ramp\_limit}_{g} \cdot \mathit{previous\_status}_{g,t} + \mathrm{start\_up\_limit}_{g} \cdot \left( 1 - \mathit{previous\_status}_{g,t} \right) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Assumptions

**`output_floor_fits_under_the_cap`**

```math
\mathrm{min\_output}_{g} \le \mathrm{capacity}_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{committable}_{g}
```
<!-- gallery:end -->

Regenerate with `pixi run python -m tools.gallery`.
