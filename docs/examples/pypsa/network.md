<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The network

This file states the buses and the balance at each bus. It is one of the 24 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It lists the sum `Bus_injection` under [`given`](../../reference/language/parameters-variables-constraints.md#given) and adds nothing to it. Every component adds its injection to that sum. `Bus_nodal_balance` is the row `Bus_injection == 0`.

<!-- gallery:begin -->
```yaml
given:
  expressions:
    Bus_injection:
      dims: [scenario, snapshot, bus]
      description: >-
        what every component puts into a bus, less what it takes out of it.
        PyPSA writes each term into the balance, and a load on its right-hand
        side

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  bus:
    description: network nodes

constraints:
  Bus_nodal_balance:
    description: >-
      `Bus-nodal_balance` — what is generated at a bus meets the load there,
      less half of every incident line's and transformer's loss. What is
      generated includes storage dispatch and stores. It is net of what the
      links take away, plus what arrives over them after losses and any delay
      at every port they deliver to. Each process port draws or delivers at
      its own rate, and each passive branch carries its flow. PyPSA dissipates
      a branch's loss half at either end. Each generator, storage unit, store
      and load term enters with its component's `sign`
      (`constraints.py:1404-1405`, `:1514`), and an inactive load not at all.
      A bus nothing is attached to has no row. PyPSA refuses one that carries
      load. The file states no assumption for it.
    dims: [scenario, snapshot, bus]
    expression: Bus_injection == 0
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$, an expression another file defines — what every component puts into a bus, less what it takes out of it. PyPSA writes each term into the balance, and a load on its right-hand side |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{N}`$ | index $`n`$ — `bus` — network nodes |

#### Subject to

**`Bus_nodal_balance`**

```math
\mathit{Bus\_injection}_{\xi,t,n} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ n \in \mathcal{N}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 24 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
