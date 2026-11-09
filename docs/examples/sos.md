<!--
SPDX-FileCopyrightText: math-spec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A curve as a special ordered set

The dispatch of [the adjacency page](piecewise_adjacency.md) under
`method: sos2`. At most two neighbouring weights are non-zero, as under
`adjacency`. The weights form a set that the solver handles itself (a special
ordered set of type 2).

The two pages print the same math. They differ in what
`spec.expand('piecewise')` writes. Here it writes the weights and an `sos:`
entry over them, in place of the binary `cost_curve_seg` and its two rows.

<!-- gallery:begin -->
```yaml
description: >-
  A piecewise-linear cost curve whose weights form a special ordered set, so
  the solver handles the adjacency restriction itself, without binaries.

dimensions:
  snapshot:
    description: dispatch periods
    dtype: int
  generator:
    description: dispatchable units
    dtype: str
  bp:
    description: breakpoints of the cost curve
    dtype: int
    ordered: true

parameters:
  capacity:
    description: maximum dispatch
    dims: [generator]
  load:
    description: demand to be met
    dims: [snapshot]
  bp_x:
    description: breakpoint dispatch levels, one curve per generator
    dims: [generator, bp]
  bp_y:
    description: cost at each breakpoint, one curve per generator
    dims: [generator, bp]

variables:
  dispatch:
    description: dispatched power
    dims: [snapshot, generator]
    bounds:
      lower: 0
      upper: capacity
  op_cost:
    description: operating cost, piecewise-linear in dispatch
    dims: [snapshot, generator]
    bounds:
      lower: 0

piecewise:
  cost_curve:
    description: >-
      cost read off the generator's curve, with at most two adjacent weights
      non-zero — the restriction the default method builds out of binaries,
      declared as a set instead
    along: bp
    dims: [snapshot, generator]
    links:
      dispatch: [dispatch, bp_x]
      op_cost: [op_cost, bp_y]
    method: sos2

constraints:
  balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  description: total operating cost, taken off the curves rather than from a marginal rate
  expression: sum(op_cost)
```

A piecewise-linear cost curve whose weights form a special ordered set, so the solver handles the adjacency restriction itself, without binaries.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{B}`$ | index $`b`$ — `bp` — breakpoints of the cost curve |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — dispatchable units |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{x}`$ | `bp_x` over $`\mathcal{B} \times \mathcal{G}`$ — breakpoint dispatch levels, one curve per generator |
| $`\mathrm{y}`$ | `bp_y` over $`\mathcal{B} \times \mathcal{G}`$ — cost at each breakpoint, one curve per generator |
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{G}`$ — maximum dispatch |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{G} \times \mathcal{T}`$ — dispatched power |
| $`\mathit{op\_cost}`$ | `op_cost` over $`\mathcal{G} \times \mathcal{T}`$ — operating cost, piecewise-linear in dispatch |

#### Variable domains

**`dispatch`**

```math
0 \le \mathit{dispatch}_{g,t} \le \mathrm{capacity}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

**`op_cost`**

```math
\mathit{op\_cost}_{g,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Objective

```math
\min \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} \mathit{op\_cost}_{g,t}
```

#### Subject to

**`balance`**

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{g,t} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

**`cost_curve`**

```math
\left( \mathit{dispatch}_{g,t},\ \mathit{op\_cost}_{g,t} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{b,g},\ \mathrm{y}_{b,g}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Assumptions

**`cost_curve_complete`**

```math
\mathrm{x}_{b,g} \text{ is defined} \wedge \mathrm{y}_{b,g} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G}
```
<!-- gallery:end -->
