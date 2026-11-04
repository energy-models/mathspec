<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Generators

This [fragment](../../reference/glossary.md#fragment) states `Generator` from
an open-source power system framework ([PyPSA](https://pypsa.org)). The file declares its three dimensions, the
relation `Generator_port`, two parameters and the variable `Generator_p`. The file
lists `Port_p` and `total_cost` under [`given`](../../reference/language/parameters-variables-constraints.md#given), and
[the surface](surface.md) declares them. `Generator_cost` is a
[named expression](../../reference/language/named.md#expressions) that adds to
`total_cost` (a [term](../../reference/glossary.md#term)). `Generator_injection` equates `Generator_p` with the flow at the port through
[`at`](../../reference/language/operators.md#at), so the balance of the
surface contains no generator variable.

<!-- gallery:begin -->
```yaml
description: >-
  PyPSA's `Generator`, wired to a port rather than straight to a bus, and cut
  to what a dispatch spec needs: a fixed capacity, no availability profile, no
  ramp limits.
given:
  variables:
    Port_p:
      dims: [snapshot, port]
      description: declared by the surface, and fixed at each generator's port by `Generator_injection`
  expressions:
    total_cost: { dims: [] }
dimensions:
  snapshot: { dtype: datetime, description: dispatch periods }
  port: { dtype: str, description: "the connections components make, one label per connection" }
  generator: { dtype: str, description: "generating units, each on one port" }
relations:
  Generator_port: { key: generator, values: port }
parameters:
  Generator_p_nom: { dims: [generator], description: nominal power }
  Generator_marginal_cost: { dims: [generator], description: cost of one unit of output }
variables:
  Generator_p:
    dims: [snapshot, generator]
    bounds: { lower: 0, upper: Generator_p_nom }
    description: "`Generator-p` — what a generator produces in a snapshot"
constraints:
  Generator_injection:
    description: >-
      What a generator produces is what its port injects. PyPSA has no row for
      this constraint, because PyPSA writes the generator into the balance.
    dims: [snapshot, generator]
    expression: at(Port_p, by=Generator_port[port]) == Generator_p
expressions:
  Generator_cost:
    expression: sum(Generator_p * Generator_marginal_cost)
    adds_to: total_cost
```

PyPSA's `Generator`, wired to a port rather than straight to a bus, and cut to what a dispatch spec needs: a fixed capacity, no availability profile, no ramp limits.

#### Given

| Symbol | Meaning |
|---|---|
| $`f`$ | `Port_p` over $`\mathcal{T} \times \mathcal{J}`$ — declared by the surface, and fixed at each generator's port by `Generator_injection` |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `Generator_cost` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J}`$ — the connections components make, one label per connection |
| $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J}`$ — generating units, each on one port |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\mathcal{G}`$ — nominal power |
| $`\mathrm{c}`$ | `Generator_marginal_cost` over $`\mathcal{G}`$ — cost of one unit of output |

#### Variables

| Symbol | Meaning |
|---|---|
| $`p`$ | `Generator_p` over $`\mathcal{T} \times \mathcal{G}`$ — `Generator-p` — what a generator produces in a snapshot |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Generator\_cost}`$ | `Generator_cost` (scalar) |

#### Variable domains

**`Generator_p`**

```math
0 \le p_{t,g} \le \mathrm{p}^{\mathrm{nom}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Definitions

**`Generator_cost`**

```math
\mathit{Generator\_cost} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \mathrm{c}_{g}
```

#### Subject to

**`Generator_injection`**

```math
f_{t,\mathrm{Generator\_port}(g)} = p_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```
<!-- gallery:end -->

!!! info "See also"

    - [The coupling surface](surface.md), for the entries this file lists under
      `given`
    - [The composed spec](composed.md), for the spec once `merge` joins this file
      with the surface and the loads
    - [PyPSA in one file](../pypsa_ladder.md), for the generator with every attribute
      PyPSA has
