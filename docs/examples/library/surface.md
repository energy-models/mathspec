<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The coupling surface

The [coupling surface](../../reference/glossary.md#surface) is the one file of the library (a
[fragment](../../reference/glossary.md#fragment)) that every other fragment is written against. The surface
lists `total_cost` under [`given`](../../reference/language/parameters-variables-constraints.md#given), and its objective minimises
`total_cost`.

An open-source power system framework ([PyPSA](https://pypsa.org)) gives each
class of component, such as `Generator`, a column of bus labels, and sums the
classes into `Bus-nodal_balance`. Here `Bus_nodal_balance` is the same however
many fragments [`merge`](../../reference/composition.md#merge) joins.

<!-- gallery:begin -->
```yaml
description: >-
  The coupling surface every component in this library is written against: one
  flow per port, one balance per bus, and one cost to minimise. A component is
  wired to a port, the port to a bus, and the balance contains no component class.
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
    description: "`Bus-nodal_balance` — what the ports on a bus put in sums to zero"
    dims: [snapshot, bus]
    expression: sum(Port_p, over=port, by=Port_bus[bus]) == 0
objective:
  sense: minimize
  expression: total_cost
```

The coupling surface every component in this library is written against: one flow per port, one balance per bus, and one cost to minimise. A component is wired to a port, the port to a bus, and the balance contains no component class. A flow is positive where the port injects into its bus. A component that costs something adds its cost to `total_cost`.

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression another file defines — what running the system costs |

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

#### Variable domains

**`Port_p`**

```math
f_{t,j} \in \mathbb{R} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
```

#### Objective

```math
\min \mathit{total\_cost}
```

#### Subject to

**`Bus_nodal_balance`**

```math
\sum_{j \in \mathcal{J} \,:\, \mathrm{Port\_bus}(j) = n} f_{t,j} = 0 \qquad \forall\, t \in \mathcal{T},\ n \in \mathcal{N}
```
<!-- gallery:end -->

!!! info "See also"

    - [Generators](generator.md) and [Loads](load.md), for the two component files
      written against this surface
    - [The composed spec](composed.md), for what `merge` returns for the three
      files
    - [Compose a spec from several files](../../howto/compose.md), for the same
      shape with fewer names
