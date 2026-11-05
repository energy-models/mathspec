<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Unit commitment

Unit commitment is [least-cost dispatch](dispatch.md) with an on/off decision
for each unit in each dispatch period (a snapshot).

The file states the cases of `previous_status` once, under
[`cases:`](../reference/language/named.md#cases). `always_on` and `boundary`
each have a `when:` [condition](../reference/glossary.md#condition), and
`otherwise:` sets the value at every combination of labels
([a coordinate](../reference/glossary.md#coordinate)) that no case covers. So `otherwise:` applies only to a committable
unit after the first snapshot, where the
[`shift`](../reference/language/operators.md#shift) in `otherwise:` always has
a previous status to take. The `shift` of `dispatch` in `ramp_up` has
`edge=0`, so that constraint has a row at the first snapshot.

<!-- gallery:begin -->
```yaml
description: >-
  Unit commitment with a start-up ramp, in which one named expression sets the
  commitment state of a unit at the start of a snapshot. That state has three cases:
  a unit that is never off, the first snapshot, and every later one.

dimensions:
  snapshot: { dtype: int, description: dispatch periods, ordered: true }
  generator: { description: generating units }

parameters:
  committable: { dims: [generator], dtype: bool, description: whether the unit may be switched off }
  status_initial: { dims: [generator], description: whether the unit was running before the horizon }
  capacity: { dims: [generator], description: installed capacity }
  min_output: { dims: [generator], description: output floor while running }
  ramp_limit: { dims: [generator], description: how far output may move between snapshots while running }
  start_up_limit: { dims: [generator], description: how far output may move in the snapshot a unit starts in }
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
    description: the commitment state of a unit at the start of a snapshot
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
    description: a running unit produces at least its floor
    dims: [snapshot, generator]
    expression: dispatch >= status * min_output
  ramp_up:
    description: >-
      one inequality for a unit already running and a unit starting up: the
      first is held to `ramp_limit`, and the second to `start_up_limit`.
    dims: [snapshot, generator]
    expression: >-
      dispatch - shift(dispatch, along=snapshot, offset=1, edge=0)
      <= ramp_limit * previous_status + start_up_limit * (1 - previous_status)

assumptions:
  output_floor_fits_under_the_cap:
    holds: "min_output <= capacity"
    where: "committable"
    description: >-
      `lower` and `upper` bound one dispatch from both sides, so a floor above
      the cap makes a running unit infeasible rather than expensive. A tool
      checks the assumption only for committable units.

objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

Unit commitment with a start-up ramp, in which one named expression sets the commitment state of a unit at the start of a snapshot. That state has three cases: a unit that is never off, the first snapshot, and every later one.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{G}`$ — installed capacity |
| $`\mathrm{committable}`$ | `committable` over $`\mathcal{G}`$ — whether the unit may be switched off |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{G}`$ — marginal cost |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |
| $`\mathrm{min\_output}`$ | `min_output` over $`\mathcal{G}`$ — output floor while running |
| $`\mathrm{ramp\_limit}`$ | `ramp_limit` over $`\mathcal{G}`$ — how far output may move between snapshots while running |
| $`\mathrm{start\_up\_limit}`$ | `start_up_limit` over $`\mathcal{G}`$ — how far output may move in the snapshot a unit starts in |
| $`\mathrm{status}^{\mathrm{initial}}`$ | `status_initial` over $`\mathcal{G}`$ — whether the unit was running before the horizon |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{G} \times \mathcal{T}`$ — output of a generator in a snapshot |
| $`\mathit{status}`$ | `status` over $`\mathcal{G} \times \mathcal{T}`$ — whether the unit is running in a snapshot |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{previous\_status}`$ | `previous_status` over $`\mathcal{G} \times \mathcal{T}`$ — the commitment state of a unit at the start of a snapshot |

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

**`lower`**

```math
\mathit{dispatch}_{g,t} \ge \mathit{status}_{g,t} \cdot \mathrm{min\_output}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

**`power_balance`**

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{g,t} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

**`ramp_up`**

```math
\mathit{dispatch}_{g,t} - \mathit{dispatch}_{g,t \boxminus_{0} 1} \le \mathrm{ramp\_limit}_{g} \cdot \mathit{previous\_status}_{g,t} + \mathrm{start\_up\_limit}_{g} \cdot \left( 1 - \mathit{previous\_status}_{g,t} \right) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

**`upper`**

```math
\mathit{dispatch}_{g,t} \le \mathit{status}_{g,t} \cdot \mathrm{capacity}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Assumptions

**`output_floor_fits_under_the_cap`**

```math
\mathrm{min\_output}_{g} \le \mathrm{capacity}_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{committable}_{g}
```
<!-- gallery:end -->

!!! info "See also"

    - [`cases`](../reference/language/named.md#cases), for how mathspec checks
      that no two cases overlap, and what it refuses in them
    - [`shift`](../reference/language/operators.md#shift), for `edge=` and the
      vacated position
    - [The composed spec](library/composed.md), for commitment written as a patch
      over a component library
