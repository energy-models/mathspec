<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The coupling surface

Every other file in the library is written against this surface. It declares one
`Port_p` per port, one balance per bus, and the relation that says which bus a
port sits on. It sets the objective on `total_cost`, which it reads under
[`given`](../../reference/language/declarations.md#given), and each component
that has a cost adds its cost to that sum. No name in the surface names a
component class, so you do not change this file when you add a component class.

PyPSA gives each component class a bus column and sums the classes into
`Bus-nodal_balance`. Here a component is wired to a port, and the port to a bus,
so the balance sums ports and stays as written however many fragments merge. The
[how-to guide](../../howto/compose.md) shows the same shape with fewer names.

A flow is positive where the port injects into its bus. Every component reads
that convention, and no component states it again.

<!-- gallery:begin -->
```yaml
description: >-
  The coupling surface every component in this library is written against: one
  flow per port, one balance per bus, and one cost to minimise. A component is
  wired to a port, the port to a bus, and the balance names no component class.
  A flow is positive where the port injects into its bus. A component that
  costs something adds its cost to `total_cost`.
given:
  expressions:
    total_cost: { dims: [], description: what running the system costs }
dimensions:
  snapshot: { dtype: datetime, description: dispatch periods }
  bus: { dtype: str, description: network nodes }
  port: { dtype: str, description: "the connections components make, one label per connection" }
relations:
  Port_bus: { key: port, values: bus }
variables:
  Port_p:
    dims: [snapshot, port]
    description: what a port puts into its bus in a snapshot, negative for a withdrawal
constraints:
  Bus_nodal_balance:
    description: "`Bus-nodal_balance` — what the ports on a bus put in nets to nothing"
    dims: [snapshot, bus]
    expression: sum(Port_p, over=port, by=Port_bus[bus]) == 0
objective:
  sense: minimize
  expression: total_cost
```

The coupling surface every component in this library is written against: one flow per port, one balance per bus, and one cost to minimise. A component is wired to a port, the port to a bus, and the balance names no component class. A flow is positive where the port injects into its bus. A component that costs something adds its cost to `total_cost`.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — the connections components make, one label per connection |

#### Variables

| Symbol | Meaning |
|---|---|
| $`f`$ | `Port_p` over $`\mathcal{T} \times \mathcal{J}`$ — what a port puts into its bus in a snapshot, negative for a withdrawal |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression another file defines — what running the system costs |

#### Objective

```math
\min \mathit{total\_cost}
```

#### Subject to

**`Bus_nodal_balance`**

```math
\sum_{j \in \mathcal{J} \,:\, \mathrm{Port\_bus}(j) = n} f_{t,j} = 0 \qquad \forall\, t \in \mathcal{T},\ n \in \mathcal{N}
```

#### Variable domains

**`Port_p`**

```math
f_{t,j} \in \mathbb{R} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
```
<!-- gallery:end -->
