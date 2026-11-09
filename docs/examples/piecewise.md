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

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\lvert \mathcal{T} \rvert`$ | the size of $`\mathcal{T}`$; $`\lvert \mathcal{T} \rvert - 1`$ is the last position |

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
\left( \mathit{dispatch}_{g,t},\ \mathit{op\_cost}_{g,t} \right) \in \mathrm{conv}_{b \in \mathcal{B}}(\mathrm{x}_{b,g},\ \mathrm{y}_{b,g}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Assumptions

**`cost_curve_complete`**

```math
\mathrm{x}_{b,g} \text{ is defined} \wedge \mathrm{y}_{b,g} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G}
```

**`cost_curve_increasing`**

```math
\mathrm{x}_{b \boxminus_{0} 1,g} < \mathrm{x}_{b,g} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{pos}(b) > 0
```

**`cost_curve_curvature`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{b,g} - \mathrm{y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{x}_{b \boxplus_{0} 1,g} - \mathrm{x}_{b,g} \right) > \left( \mathrm{y}_{b \boxplus_{0} 1,g} - \mathrm{y}_{b,g} \right) \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \vee \lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{b,g} - \mathrm{y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{x}_{b \boxplus_{0} 1,g} - \mathrm{x}_{b,g} \right) < \left( \mathrm{y}_{b \boxplus_{0} 1,g} - \mathrm{y}_{b,g} \right) \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \qquad \forall\, g \in \mathcal{G}
```
<!-- gallery:end -->
