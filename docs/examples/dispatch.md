<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Least-cost dispatch

This file is the smallest whole spec, and the one on the [home
page](../index.md). It has generators with a capacity, an hourly load to meet,
and a cost to minimise.

The `where:` on `dispatch` deletes the rows where a generator has no capacity
([absence](../reference/language/absence.md)). `sum(dispatch, over=generator)`
names the dimension it sums over, so the `dims` of the constraint are the
dimensions that remain.

<!-- gallery:begin -->
```yaml
description: Least-cost dispatch of a generator fleet against an hourly load.

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

Least-cost dispatch of a generator fleet against an hourly load.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{G}`$ — installed capacity |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{G}`$ — marginal cost |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{G} \times \mathcal{T}`$ — output of a generator in a snapshot |

#### Variable domains

**`dispatch`**

```math
0 \le \mathit{dispatch}_{g,t} \le \mathrm{capacity}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{capacity}_{g} > 0
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
<!-- gallery:end -->

Regenerate with `pixi run python -m tools.gallery`.
