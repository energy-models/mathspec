<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Flow-based market coupling

This file states PyPSA's flow-based domains. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It adds a [term](../../reference/language/named.md#adds_to) to the sum `Bus_injection`. `FlowBased_net_position` is what a zone bus exports to its domain. `GlobalConstraint_flow_based_ub` holds each critical network element to its remaining available margin, and `FlowBased_balance` sums each domain's net positions to zero through a [`sum`](../../reference/language/operators.md#sum) by a relation.

<!-- gallery:begin -->
```yaml
given:
  parameters:
    GlobalConstraint_type: { dims: [global_constraint], dtype: str }
    GlobalConstraint_sense: { dims: [scenario, global_constraint], dtype: str }
    GlobalConstraint_counts_snapshot: { dims: [scenario, global_constraint, snapshot], dtype: bool }
  variables:
    Link_p: { dims: [scenario, snapshot, link] }
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
  link:
    description: controllable connections, each from one bus to the buses it delivers to
  global_constraint:
    description: PyPSA's `GlobalConstraint` rows, one label per declared limit
  flow_based_domain:
    description: >-
      the flow-based domains, each with its own zero-sum balance of net
      positions (PyPSA's `domain` of a `flow_based` row), data prep. A run whose
      flow-based rows name no domain has one. A run without them has none

maps:
  bus:
    flow_based_domain:
      description: >-
        the flow-based domain a zone bus belongs to: the domain whose rows set
        the bus's `ptdf_<bus>` column, data prep. A bus that is no zone has no
        row
      refers: flow_based_domain
      missing: absent

parameters:
  GlobalConstraint_ram:
    description: >-
      the remaining available margin of a `flow_based` row, one critical
      network element (CNEC). It may differ by snapshot. No value drops the
      row in that snapshot (`flow_based.py:201`)
    dims: [scenario, snapshot, global_constraint]
    missing: absent
  GlobalConstraint_zonal_ptdf:
    description: >-
      the zonal power transfer distribution factor of a `flow_based` row for a
      zone bus: PyPSA's `ptdf_<bus>` column read long, data prep. It may differ
      by snapshot. No value is zero, as PyPSA fills it
    dims: [scenario, snapshot, global_constraint, bus]
    missing: 0
  GlobalConstraint_link_ptdf:
    description: >-
      the factor of a `flow_based` row for a corridor link, whose flow enters
      the row: PyPSA's `ptdf_<link>` column read long, data prep. No value is
      zero
    dims: [scenario, snapshot, global_constraint, link]
    missing: 0
  Bus_flow_based_zone:
    description: >-
      whether a bus is a zone of a flow-based domain: some `flow_based` row
      has its `ptdf_<bus>` column, data prep
    dims: [bus]
    dtype: bool

variables:
  FlowBased_net_position:
    description: >-
      `FlowBased-net_position` — what a zone bus exports to the flow-based
      domain, unbounded. It leaves the zone's nodal balance
      (`flow_based.py:207-234`). A bus that is no zone has none
    dims: [scenario, snapshot, bus]
    where: Bus_flow_based_zone
    missing: 0

expressions:
  FlowBased_injection:
    description: what a zone bus exports to its flow-based domain leaves the bus (`constraints.py:1578`)
    dims: [scenario, snapshot, bus]
    expression: -FlowBased_net_position
    adds_to: Bus_injection

constraints:
  GlobalConstraint_flow_based_ub:
    description: >-
      `flow_based` — a CNEC's flow, the zones' net positions and the corridor
      links' flows each times its factor, is at most its remaining available
      margin. PyPSA names the rows `GlobalConstraint-ram`, one per CNEC and
      snapshot, and reads no `constant` (`flow_based.py:262-293`)
    dims: [scenario, snapshot, global_constraint]
    where: >-
      GlobalConstraint_type == 'flow_based' AND GlobalConstraint_sense == '<='
      AND GlobalConstraint_ram AND GlobalConstraint_counts_snapshot
    expression: >-
      sum(GlobalConstraint_zonal_ptdf * FlowBased_net_position, over=bus)
      + sum(GlobalConstraint_link_ptdf * Link_p, over=link)
      <= GlobalConstraint_ram
  FlowBased_balance:
    description: "`FlowBased-balance` — the net positions of each domain's zones sum to zero"
    dims: [scenario, snapshot, flow_based_domain]
    expression: sum(FlowBased_net_position, over=bus, by=bus[flow_based_domain]) == 0

assumptions:
  GlobalConstraint_flow_based_sense_is_le:
    holds: "GlobalConstraint_sense == '<='"
    where: "GlobalConstraint_type == 'flow_based'"
    description: >-
      PyPSA refuses a `flow_based` row whose sense is not `<=`
      (`flow_based.py:109-114`)
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{in}`$ | `GlobalConstraint_counts_snapshot` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, data another file declares |
| $`\mathrm{sense}`$ | `GlobalConstraint_sense` over $`\mathcal{G} \times \Xi`$, data another file declares |
| $`\mathrm{type}`$ | `GlobalConstraint_type` over $`\mathcal{G}`$, data another file declares |
| $`f`$ | `Link_p` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, an expression this file adds `FlowBased_injection` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{flow\_based\_domain}: \mathcal{N} \to \mathcal{L}`$, `bus[flow_based_domain]` is `absent` where the data gives no label — network nodes |
| $`\mathcal{L}`$ | index $`l`$ — `flow_based_domain` with $`\mathrm{flow\_based\_domain}: \mathcal{N} \to \mathcal{L}`$, `bus[flow_based_domain]` is `absent` where the data gives no label — the flow-based domains, each with its own zero-sum balance of net positions (PyPSA's `domain` of a `flow_based` row), data prep. A run whose flow-based rows name no domain has one. A run without them has none |
| $`\mathcal{G}`$ | index $`g`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{L}`$ | index $`l`$ — `link` — controllable connections, each from one bus to the buses it delivers to |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{zone}`$ | `Bus_flow_based_zone` over $`\mathcal{N}`$ — whether a bus is a zone of a flow-based domain: some `flow_based` row has its `ptdf_<bus>` column, data prep |
| $`\mathrm{PTDF}^{f}`$ | `GlobalConstraint_link_ptdf` over $`\mathcal{G} \times \mathcal{L} \times \Xi \times \mathcal{T}`$, $`0`$ where the data has no row — the factor of a `flow_based` row for a corridor link, whose flow enters the row: PyPSA's `ptdf_<link>` column read long, data prep. No value is zero |
| $`\mathrm{RAM}`$ | `GlobalConstraint_ram` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — the remaining available margin of a `flow_based` row, one critical network element (CNEC). It may differ by snapshot. No value drops the row in that snapshot (`flow_based.py:201`) |
| $`\mathrm{PTDF}^{z}`$ | `GlobalConstraint_zonal_ptdf` over $`\mathcal{N} \times \mathcal{G} \times \Xi \times \mathcal{T}`$, $`0`$ where the data has no row — the zonal power transfer distribution factor of a `flow_based` row for a zone bus: PyPSA's `ptdf_<bus>` column read long, data prep. It may differ by snapshot. No value is zero, as PyPSA fills it |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{NP}`$ | `FlowBased_net_position` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `FlowBased-net_position` — what a zone bus exports to the flow-based domain, unbounded. It leaves the zone's nodal balance (`flow_based.py:207-234`). A bus that is no zone has none |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{NP}^{\mathrm{inj}}`$ | `FlowBased_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ — what a zone bus exports to its flow-based domain leaves the bus (`constraints.py:1578`) |

#### Variable domains

**`FlowBased_net_position`**

```math
\mathit{NP}_{n,\xi,t} \in \mathbb{R} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{zone}_{n}
```

#### Definitions

**`FlowBased_injection`**

```math
\mathit{NP}^{\mathrm{inj}}_{n,\xi,t} = -\mathit{NP}_{n,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

#### Subject to

**`FlowBased_balance`**

```math
\sum_{n \in \mathcal{N} \,:\, \mathrm{flow\_based\_domain}(n) = l} \mathit{NP}_{n,\xi,t} = 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`GlobalConstraint_flow_based_ub`**

```math
\sum_{n \in \mathcal{N}} \mathrm{PTDF}^{z}_{n,g,\xi,t} \cdot \mathit{NP}_{n,\xi,t} + \sum_{l \in \mathcal{L}} \mathrm{PTDF}^{f}_{g,l,\xi,t} \cdot f_{l,\xi,t} \le \mathrm{RAM}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{type}_{g} = \text{'}\mathrm{flow\_based}\text{'} \wedge \mathrm{sense}_{g,\xi} = \text{'}\mathrm{<=}\text{'} \wedge \mathrm{RAM}_{g,\xi,t} \text{ is defined} \wedge \mathrm{in}_{g,\xi,t}
```

#### Assumptions

**`GlobalConstraint_flow_based_sense_is_le`**

```math
\mathrm{sense}_{g,\xi} = \text{'}\mathrm{<=}\text{'} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{type}_{g} = \text{'}\mathrm{flow\_based}\text{'}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
