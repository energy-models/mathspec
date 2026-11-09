<!--
SPDX-FileCopyrightText: math-spec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A curve that is not convex

The dispatch of [the convex page](piecewise.md), with a cost curve that is not
convex. Minimising the cost no longer puts the weights on one segment, so the
entry takes the default method, `adjacency`. Its expansion adds binaries and
rows that require the non-zero weights to lie on one segment.

The typesetter prints the curve as a piecewise-linear function,
$`\mathrm{pwl}`$, with no assumption about its shape. When the spec is
expanded, `cost_curve_seg` is one binary per breakpoint. `cost_curve_pick`
requires at most one of them to be 1. `cost_curve_adjacency` requires each
weight to be zero unless the binary at its breakpoint or the one before is 1.
The non-zero weights then lie at the picked breakpoint and the one after it.

<!-- gallery:begin -->
```yaml
description: >-
  The same least-cost dispatch as `piecewise.yaml`, with a cost curve that is
  not convex. Under the default method, the expansion states binaries and rows
  that require the non-zero weights to lie on one segment.

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
      cost read off the generator's curve. The curve bends both ways, so
      nothing but the restriction keeps the weights on one segment: a binary
      per segment picks the one they may sit on
    along: bp
    dims: [snapshot, generator]
    links:
      dispatch: [dispatch, bp_x]
      op_cost: [op_cost, bp_y]
    method: adjacency

constraints:
  balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  description: total operating cost, taken off the curves rather than from a marginal rate
  expression: sum(op_cost)
```

The same least-cost dispatch as `piecewise.yaml`, with a cost curve that is not convex. Under the default method, the expansion states binaries and rows that require the non-zero weights to lie on one segment.

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
