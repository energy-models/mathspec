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
| $`\mathcal{B}`$ | index $`b`$ — `bp` — breakpoints of the cost curve, as many as the longest curve needs |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — dispatchable units |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{committable}`$ | `committable` over $`\mathcal{G}`$ — whether the generator has a status that switches it on and off |
| $`\mathrm{cost}^{\mathrm{bp}}`$ | `cost_bp` over $`\mathcal{B} \times \mathcal{G}`$, `absent` where the data has no row — cost of the dispatch at each breakpoint |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |
| $`\mathrm{marginal\_cost}`$ | `marginal_cost` over $`\mathcal{G}`$, $`0`$ where the data has no row — linear cost of output, for a generator with no curve |
| $`\mathrm{on\_curve}`$ | `on_curve` over $`\mathcal{B} \times \mathcal{G}`$ — which breakpoints this generator's curve runs through, true over one consecutive run; false everywhere for a generator with no curve |
| $`\mathrm{p}^{\mathrm{bp}}`$ | `p_bp` over $`\mathcal{B} \times \mathcal{G}`$, `absent` where the data has no row — dispatch at each breakpoint |
| $`\mathrm{p}^{\mathrm{nom}}`$ | `p_nom` over $`\mathcal{G}`$ — installed capacity |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{has\_curve}`$ | `has_curve` over $`\mathcal{G}`$ — the generator pays along a cost curve |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{cost}`$ | `cost` over $`\mathcal{G} \times \mathcal{T}`$ — operating cost, held above the generator's curve |
| $`p`$ | `p` over $`\mathcal{G} \times \mathcal{T}`$ — dispatched power |
| $`\mathit{status}`$ | `status` over $`\mathcal{G} \times \mathcal{T}`$ — whether a committable generator is on |

#### Conditions

**`has_curve`**

```math
\mathrm{has\_curve}_{g} \iff \lvert \{ b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{b,g} \} \rvert > 0 \qquad \forall\, g \in \mathcal{G}
```

#### Variable domains

**`cost`**

```math
\mathit{cost}_{g,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{has\_curve}_{g}
```

**`p`**

```math
0 \le p_{g,t} \le \mathrm{p}^{\mathrm{nom}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

**`status`**

```math
\mathit{status}_{g,t} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{committable}_{g}
```

#### Objective

```math
\min \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} \mathit{cost}_{g,t} + \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} \mathrm{marginal\_cost}_{g} \cdot p_{g,t}
```

#### Subject to

**`balance`**

```math
\sum_{g \in \mathcal{G}} p_{g,t} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

**`committed`**

```math
p_{g,t} \le \mathrm{p}^{\mathrm{nom}}_{g} \cdot \mathit{status}_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{committable}_{g}
```

**`cost_curve`**

```math
\mathit{cost}_{g,t} \ge \begin{cases} \mathit{status}_{g,t} & \text{if } \mathrm{committable}_{g} \\ 1 & \text{otherwise} \end{cases} \cdot \mathrm{pwl}_{b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{b,g}}(\mathrm{p}^{\mathrm{bp}}_{b,g},\ \mathrm{cost}^{\mathrm{bp}}_{b,g})(p_{g,t}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Assumptions

**`cost_curve_complete`**

```math
\mathrm{p}^{\mathrm{bp}}_{b,g} \text{ is defined} \wedge \mathrm{cost}^{\mathrm{bp}}_{b,g} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{on\_curve}_{b,g}
```

**`cost_curve_contiguous`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{b,g} \wedge \neg \mathrm{on\_curve}_{b - 1,g} \} \rvert = 1 \qquad \forall\, g \in \mathcal{G} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{on\_curve}_{b,g} \} \rvert > 0
```
<!-- gallery:end -->
