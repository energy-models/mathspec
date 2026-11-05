<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A curve filled segment by segment

Dispatch where some generators pay along a cost curve under
`method: incremental`. When the spec is expanded, each segment has a filled
fraction, `cost_curve_delta`, and a binary, `cost_curve_order`. A segment
fills only once the one before it is full. The modelling library
[linopy](https://linopy.readthedocs.io) writes the same rows for a curve that
a gate switches or that is not convex.

The curves have different lengths, so `where: on_curve` is over `bp`, and a
generator with no curve has none. `activity: status` switches the curve of a
committable generator. The other generators have no status, so their curves
run ungated. The expansion writes each link row twice: `cost_curve_p` where
the status exists, and `cost_curve_p_ungated` where it is absent.

<!-- gallery:begin -->
```yaml
description: >-
  Least-cost dispatch where some generators pay along a piecewise-linear cost
  curve, as PyPSA's piecewise marginal cost does. The curves have different
  lengths, and a generator with no curve pays a linear marginal cost. A
  committable generator switches its curve off with its status, and the
  others run on their curve ungated. The curve is stated incrementally, as
  linopy states a gated or non-convex curve: each segment is filled only once
  the one before it is full.

dimensions:
  snapshot:
    description: dispatch periods
    dtype: int
    ordered: true
  generator:
    description: dispatchable units
    dtype: str
  bp:
    description: breakpoints of the cost curve, as many as the longest curve needs
    dtype: int
    ordered: true

parameters:
  p_nom:
    description: installed capacity
    dims: [generator]
  load:
    description: demand to be met
    dims: [snapshot]
  marginal_cost:
    description: linear cost of output, for a generator with no curve
    dims: [generator]
    missing: 0
  committable:
    description: whether the generator has a status that switches it on and off
    dims: [generator]
    dtype: bool
  on_curve:
    description: >-
      which breakpoints this generator's curve runs through, true over one
      consecutive run; false everywhere for a generator with no curve
    dims: [generator, bp]
    dtype: bool
  p_bp:
    description: dispatch at each breakpoint
    dims: [generator, bp]
    missing: absent
  cost_bp:
    description: cost of the dispatch at each breakpoint
    dims: [generator, bp]
    missing: absent

conditions:
  has_curve:
    description: the generator pays along a cost curve
    condition: count(on_curve, over=bp) > 0

variables:
  p:
    description: dispatched power
    dims: [snapshot, generator]
    bounds:
      lower: 0
      upper: p_nom
  status:
    description: whether a committable generator is on
    dims: [snapshot, generator]
    where: committable
    domain: binary
  cost:
    description: operating cost, held above the generator's curve
    dims: [snapshot, generator]
    where: has_curve
    bounds:
      lower: 0

piecewise:
  cost_curve:
    description: >-
      a curve per generator that has one, switched by the status where the
      generator has one
    along: bp
    dims: [snapshot, generator]
    where: on_curve
    method: incremental
    activity: status
    links:
      p: [p, p_bp]
      cost: [cost, cost_bp, ">="]

constraints:
  balance:
    dims: [snapshot]
    expression: sum(p, over=generator) == load
  committed:
    description: a committable generator runs only while it is on
    dims: [snapshot, generator]
    where: committable
    expression: p <= p_nom * status

objective:
  sense: minimize
  description: the cost on each curve, and the linear cost of every other generator
  expression: sum(cost) + sum(marginal_cost * p)
```

Least-cost dispatch where some generators pay along a piecewise-linear cost curve, as PyPSA's piecewise marginal cost does. The curves have different lengths, and a generator with no curve pays a linear marginal cost. A committable generator switches its curve off with its status, and the others run on their curve ungated. The curve is stated incrementally, as linopy states a gated or non-convex curve: each segment is filled only once the one before it is full.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — dispatchable units |
| $`\mathcal{B}`$ | index $`b`$ — `bp` — breakpoints of the cost curve, as many as the longest curve needs |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{p}^{\mathrm{nom}}`$ | `p_nom` over $`\mathcal{G}`$ — installed capacity |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |
| $`\mathrm{marginal\_cost}`$ | `marginal_cost` over $`\mathcal{G}`$, $`0`$ where the data has no row — linear cost of output, for a generator with no curve |
| $`\mathrm{committable}`$ | `committable` over $`\mathcal{G}`$ — whether the generator has a status that switches it on and off |
| $`\mathrm{on\_curve}`$ | `on_curve` over $`\mathcal{G} \times \mathcal{B}`$ — which breakpoints this generator's curve runs through, true over one consecutive run; false everywhere for a generator with no curve |
| $`\mathrm{p}^{\mathrm{bp}}`$ | `p_bp` over $`\mathcal{G} \times \mathcal{B}`$, `absent` where the data has no row — dispatch at each breakpoint |
| $`\mathrm{cost}^{\mathrm{bp}}`$ | `cost_bp` over $`\mathcal{G} \times \mathcal{B}`$, `absent` where the data has no row — cost of the dispatch at each breakpoint |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{has\_curve}`$ | `has_curve` over $`\mathcal{G}`$ — the generator pays along a cost curve |

#### Variables

| Symbol | Meaning |
|---|---|
| $`p`$ | `p` over $`\mathcal{T} \times \mathcal{G}`$ — dispatched power |
| $`\mathit{status}`$ | `status` over $`\mathcal{T} \times \mathcal{G}`$ — whether a committable generator is on |
| $`\mathit{cost}`$ | `cost` over $`\mathcal{T} \times \mathcal{G}`$ — operating cost, held above the generator's curve |

#### Conditions

**`has_curve`**

```math
\mathrm{has\_curve}_{g} \iff \lvert \{ b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{g,b} \} \rvert > 0 \qquad \forall\, g \in \mathcal{G}
```

#### Variable domains

**`p`**

```math
0 \le p_{t,g} \le \mathrm{p}^{\mathrm{nom}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

**`status`**

```math
\mathit{status}_{t,g} \in \{0, 1\} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{committable}_{g}
```

**`cost`**

```math
\mathit{cost}_{t,g} \ge 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{has\_curve}_{g}
```

#### Objective

```math
\min \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{cost}_{t,g} + \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathrm{marginal\_cost}_{g} \cdot p_{t,g}
```

#### Subject to

**`balance`**

```math
\sum_{g \in \mathcal{G}} p_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

**`committed`**

```math
p_{t,g} \le \mathrm{p}^{\mathrm{nom}}_{g} \cdot \mathit{status}_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{committable}_{g}
```

**`cost_curve`**

```math
\mathit{cost}_{t,g} \ge \begin{cases} \mathit{status}_{t,g} & \text{if } \mathrm{committable}_{g} \\ 1 & \text{otherwise} \end{cases} \cdot \mathrm{pwl}_{b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{g,b}}(\mathrm{p}^{\mathrm{bp}}_{g,b},\ \mathrm{cost}^{\mathrm{bp}}_{g,b})(p_{t,g}) \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Assumptions

**`cost_curve_complete`**

```math
\mathrm{p}^{\mathrm{bp}}_{g,b} \text{ is defined} \wedge \mathrm{cost}^{\mathrm{bp}}_{g,b} \text{ is defined} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{g,b}
```

**`cost_curve_contiguous`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{g,b} \wedge \neg \mathrm{on\_curve}_{g,b - 1} \} \rvert = 1 \qquad \forall\, g \in \mathcal{G} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{g,b} \} \rvert > 0
```
<!-- gallery:end -->
