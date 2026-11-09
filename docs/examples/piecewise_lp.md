<!--
SPDX-FileCopyrightText: math-spec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A curve as segment lines

The dispatch of [the convex page](piecewise.md), with each cost curve stated as
the lines that its segments lie on. Under the `>=` on the cost link, the cost
lies on or above every line. The expansion declares no variable, so the model
stays a linear program.

The assumptions are the point of this page. The lines bound the cost exactly
only where dispatch increases along `bp` and the cost curve is convex. On a
concave curve, each line lies above the curve away from its own segment, so
between breakpoints the cost must lie above the curve. With breakpoints (0, 0), (1, 2) and (2, 3)
and a dispatch of 0.5, the cost must be at least 1.5, where the curve gives 1.
The solver still reports an optimal solution. A tool checks
`cost_curve_curvature` when the data is attached.

<!-- gallery:begin -->
```yaml
description: >-
  The same least-cost dispatch as `piecewise.yaml`, with each generator's cost
  curve stated as the lines its segments lie on. The curve is convex and the
  objective pushes the cost down, so a cost above every segment line lies on
  the curve, and the expansion declares no variable.

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
    description: operating cost, held above every segment of the generator's curve
    dims: [snapshot, generator]
    bounds:
      lower: 0

piecewise:
  cost_curve:
    description: >-
      cost bounded below by the curve — the `>=` sets which side of the lines
      the cost lies on, and the curvature has to match it: the lines of a
      concave curve lie above it, and the solver reports an optimal solution
      either way
    along: bp
    dims: [snapshot, generator]
    links:
      dispatch: [dispatch, bp_x]
      op_cost: [op_cost, bp_y, ">="]
    method: lp

constraints:
  balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  description: total operating cost, taken off the curves rather than from a marginal rate
  expression: sum(op_cost)
```

The same least-cost dispatch as `piecewise.yaml`, with each generator's cost curve stated as the lines its segments lie on. The curve is convex and the objective pushes the cost down, so a cost above every segment line lies on the curve, and the expansion declares no variable.

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
| $`\mathit{op\_cost}`$ | `op_cost` over $`\mathcal{G} \times \mathcal{T}`$ — operating cost, held above every segment of the generator's curve |

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
\mathit{op\_cost}_{g,t} \ge \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{b,g},\ \mathrm{y}_{b,g})(\mathit{dispatch}_{g,t}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
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
\left( \mathrm{y}_{b,g} - \mathrm{y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{x}_{b \boxplus_{0} 1,g} - \mathrm{x}_{b,g} \right) \le \left( \mathrm{y}_{b \boxplus_{0} 1,g} - \mathrm{y}_{b,g} \right) \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1
```

**`cost_curve_breakpoints`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{x}_{b,g} \text{ is defined} \} \rvert \ge 2 \qquad \forall\, g \in \mathcal{G}
```
<!-- gallery:end -->
