<!--
SPDX-FileCopyrightText: math-spec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A curve by convex combination

A generator's cost curve, tied to its dispatch by a
[`piecewise`](../reference/language/piecewise.md) entry under
`method: convex`. The three pages after it state the same dispatch with
another method.

The typesetter prints the curve as the convex hull of its breakpoints,
$`\mathrm{conv}`$, which also contains points off the curve. The objective
minimises the cost, so each point lies on the lower edge of the hull. Where
dispatch increases along `bp` and the cost curve is convex, that edge is the
curve. The cost then lies on the curve without a binary. The assumptions
`cost_curve_increasing` and `cost_curve_curvature` state that dispatch
increases and that the curve bends one way only.

When the spec is expanded, the entry becomes the weights `cost_curve_lam`, a
row that makes them sum to one, and one row per link.
[See what a piecewise curve expands to](../howto/see-an-expansion.md) shows
how to print an expansion.

<!-- gallery:begin -->
```yaml
description: >-
  Least-cost dispatch where each generator's cost curve is piecewise-linear in
  its output, and the curve is the convex hull of its breakpoints.

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
      cost read off the generator's curve — convex, so the weights need no
      binaries to keep them on one segment
    along: bp
    dims: [snapshot, generator]
    links:
      dispatch: [dispatch, bp_x]
      op_cost: [op_cost, bp_y]
    method: convex

constraints:
  balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  description: total operating cost, taken off the curves rather than from a marginal rate
  expression: sum(op_cost)
```

Least-cost dispatch where each generator's cost curve is piecewise-linear in its output, and the curve is the convex hull of its breakpoints.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — dispatchable units |
| $`\mathcal{B}`$ | index $`b`$ — `bp` — breakpoints of the cost curve |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{G}`$ — maximum dispatch |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |
| $`\mathrm{x}`$ | `bp_x` over $`\mathcal{G} \times \mathcal{B}`$ — breakpoint dispatch levels, one curve per generator |
| $`\mathrm{y}`$ | `bp_y` over $`\mathcal{G} \times \mathcal{B}`$ — cost at each breakpoint, one curve per generator |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{T} \times \mathcal{G}`$ — dispatched power |
| $`\mathit{op\_cost}`$ | `op_cost` over $`\mathcal{T} \times \mathcal{G}`$ — operating cost, piecewise-linear in dispatch |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\lvert \mathcal{T} \rvert`$ | the size of $`\mathcal{T}`$; $`\lvert \mathcal{T} \rvert - 1`$ is the last position |

#### Variable domains

**`dispatch`**

```math
0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

**`op_cost`**

```math
\mathit{op\_cost}_{t,g} \ge 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Objective

```math
\min \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{op\_cost}_{t,g}
```

#### Subject to

**`balance`**

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

**`cost_curve`**

```math
\left( \mathit{dispatch}_{t,g},\ \mathit{op\_cost}_{t,g} \right) \in \mathrm{conv}_{b \in \mathcal{B}}(\mathrm{x}_{g,b},\ \mathrm{y}_{g,b}) \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Assumptions

**`cost_curve_complete`**

```math
\mathrm{x}_{g,b} \text{ is defined} \wedge \mathrm{y}_{g,b} \text{ is defined} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B}
```

**`cost_curve_increasing`**

```math
\mathrm{x}_{g,b \boxminus_{0} 1} < \mathrm{x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) > 0
```

**`cost_curve_curvature`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{g,b} - \mathrm{y}_{g,b \boxminus_{0} 1} \right) \cdot \left( \mathrm{x}_{g,b \boxplus_{0} 1} - \mathrm{x}_{g,b} \right) > \left( \mathrm{y}_{g,b \boxplus_{0} 1} - \mathrm{y}_{g,b} \right) \cdot \left( \mathrm{x}_{g,b} - \mathrm{x}_{g,b \boxminus_{0} 1} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \vee \lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{g,b} - \mathrm{y}_{g,b \boxminus_{0} 1} \right) \cdot \left( \mathrm{x}_{g,b \boxplus_{0} 1} - \mathrm{x}_{g,b} \right) < \left( \mathrm{y}_{g,b \boxplus_{0} 1} - \mathrm{y}_{g,b} \right) \cdot \left( \mathrm{x}_{g,b} - \mathrm{x}_{g,b \boxminus_{0} 1} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \qquad \forall\, g \in \mathcal{G}
```
<!-- gallery:end -->
