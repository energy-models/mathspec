<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Least-cost dispatch

Least-cost dispatch is the smallest specification of an optimisation model
([a spec](../reference/glossary.md#spec)) with a balance, a bound and a cost.
The [home page](../index.md) has the same spec. Wherever a generator has no
capacity, the [`where:`](../reference/language/absence.md#where) on `dispatch`
leaves the [variable](../reference/language/parameters-variables-constraints.md#variables) with no row there
([absent](../reference/language/absence.md)).
[`sum(dispatch, over=generator)`](../reference/language/operators.md#sum) sums
over `generator` and keeps `snapshot`, which is the one
[dimension](../reference/language/dimensions.md) that
`power_balance` declares.

<!-- gallery:begin -->
```yaml
description: Least-cost dispatch of a generator fleet against a load in each dispatch period.

dimensions:
  snapshot: { dtype: int, description: dispatch periods }
  generator: { description: generating units }

parameters:
  capacity: { dims: [generator], description: installed capacity }
  load: { dims: [snapshot], description: demand to be met }
  cost: { dims: [generator], description: marginal cost }

variables:
  dispatch:
    description: output of a generator in a snapshot
    dims: [snapshot, generator]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }

constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

Least-cost dispatch of a generator fleet against a load in each dispatch period.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{G}`$ — installed capacity |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{G}`$ — marginal cost |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{T} \times \mathcal{G}`$ — output of a generator in a snapshot |

#### Variable domains

**`dispatch`**

```math
0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{capacity}_{g} > 0
```

#### Objective

```math
\min \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
```

#### Subject to

**`power_balance`**

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```
<!-- gallery:end -->

!!! info "See also"

    - [Absence](../reference/language/absence.md), for what an absent variable
      does to the expressions that use it
    - [`sum`](../reference/language/operators.md#sum), for every form of the call
    - [Unit commitment](commitment.md), for the same dispatch with an on/off
      decision for each unit
