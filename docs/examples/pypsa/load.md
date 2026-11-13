<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Loads

This file states PyPSA's `Load`. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It adds a [term](../../reference/language/named.md#adds_to) to the sum `Bus_injection`. `Load_demand` is the demand times the sign where the load is active, and nothing where it is not.

<!-- gallery:begin -->
```yaml
given:
  expressions:
    Bus_injection: { dims: [bus, scenario, snapshot] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  bus:
    description: network nodes
  load:
    description: demands, each on one bus

maps:
  load:
    bus:
      description: the bus a load sits on
      refers_to: bus

parameters:
  Load_p_set:
    description: demand
    dims: [scenario, snapshot, load]
  Load_sign:
    description: >-
      the sign a load's demand enters its bus's balance with. It is PyPSA's
      `sign`, `-1` unless given, `1` for a load that feeds its bus. PyPSA
      refuses one that differs by scenario (`constants.py:46`)
    dims: [load]
  Load_active:
    description: >-
      whether a load is active in the network, PyPSA's `active`. A load has no
      build year and no lifetime, so the flag is the same in every snapshot.
      PyPSA refuses one that differs by scenario (`constants.py:54`)
    dims: [load]
    dtype: bool

expressions:
  Load_demand:
    description: >-
      what a load draws from its bus's balance. It is its demand times its
      sign where it is active, and nothing where it is not. PyPSA drops an
      inactive load from the balance (`constraints.py:1591-1592`)
    dims: [scenario, snapshot, load]
    cases:
      active: { when: Load_active, expression: Load_sign * Load_p_set }
    otherwise: 0
  Load_injection:
    expression: sum(Load_demand, over=load, by=load[bus])
    adds_to: Bus_injection
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, an expression this file adds `Load_injection` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{bus}: \mathcal{D} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{bus}: \mathcal{D} \to \mathcal{N}`$ — demands, each on one bus |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{\mathrm{load}}`$ | `Load_active` over $`\mathcal{D}`$ — whether a load is active in the network, PyPSA's `active`. A load has no build year and no lifetime, so the flag is the same in every snapshot. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{D} \times \Xi \times \mathcal{T}`$ — demand |
| $`\mathrm{sgn}^{\mathrm{load}}`$ | `Load_sign` over $`\mathcal{D}`$ — the sign a load's demand enters its bus's balance with. It is PyPSA's `sign`, `-1` unless given, `1` for a load that feeds its bus. PyPSA refuses one that differs by scenario (`constants.py:46`) |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\check{\mathrm{load}}`$ | `Load_demand` over $`\mathcal{D} \times \Xi \times \mathcal{T}`$ — what a load draws from its bus's balance. It is its demand times its sign where it is active, and nothing where it is not. PyPSA drops an inactive load from the balance (`constraints.py:1591-1592`) |
| $`\mathrm{Load\_injection}`$ | `Load_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |

#### Definitions

**`Load_demand`**

```math
\check{\mathrm{load}}_{d,\xi,t} = \begin{cases} \mathrm{sgn}^{\mathrm{load}}_{d} \cdot \mathrm{load}_{d,\xi,t} & \text{if } \mathrm{on}^{\mathrm{load}}_{d} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, d \in \mathcal{D},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Load_injection`**

```math
\mathrm{Load\_injection}_{n,\xi,t} = \sum_{d \in \mathcal{D} \,:\, \mathrm{bus}(d) = n} \check{\mathrm{load}}_{d,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
