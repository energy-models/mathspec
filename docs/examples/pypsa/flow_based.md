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
    Bus_injection: { dims: [scenario, snapshot, bus] }

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

relations:
  Bus_flow_based_domain:
    description: >-
      the flow-based domain a zone bus belongs to: the domain whose rows set
      the bus's `ptdf_<bus>` column, data prep. A bus that is no zone has no
      row
    key: bus
    values: flow_based_domain
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
    description: what a zone bus exports to its flow-based domain leaves the bus (`constraints.py:1508`)
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
    expression: sum(FlowBased_net_position, over=bus, by=Bus_flow_based_domain[flow_based_domain]) == 0

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
| $`\mathrm{type}`$ | `GlobalConstraint_type` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{sense}`$ | `GlobalConstraint_sense` over $`\Xi \times \mathcal{G}`$, data another file declares |
| $`\mathrm{in}`$ | `GlobalConstraint_counts_snapshot` over $`\Xi \times \mathcal{G} \times \mathcal{T}`$, data another file declares |
| $`f`$ | `Link_p` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$, an expression this file adds `FlowBased_injection` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Bus\_flow\_based\_domain}: \mathcal{N} \to \mathcal{O}`$, `Bus_flow_based_domain` is `absent` where the data has no row — network nodes |
| $`\mathcal{L}`$ | index $`l`$ — `link` — controllable connections, each from one bus to the buses it delivers to |
| $`\mathcal{G}`$ | index $`g`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{O}`$ | index $`o`$ — `flow_based_domain` with $`\mathrm{Bus\_flow\_based\_domain}: \mathcal{N} \to \mathcal{O}`$, `Bus_flow_based_domain` is `absent` where the data has no row — the flow-based domains, each with its own zero-sum balance of net positions (PyPSA's `domain` of a `flow_based` row), data prep. A run whose flow-based rows name no domain has one. A run without them has none |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{RAM}`$ | `GlobalConstraint_ram` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `absent` where the data has no row — the remaining available margin of a `flow_based` row, one critical network element (CNEC). It may differ by snapshot. No value drops the row in that snapshot (`flow_based.py:201`) |
| $`\mathrm{PTDF}^{z}`$ | `GlobalConstraint_zonal_ptdf` over $`\Xi \times \mathcal{T} \times \mathcal{G} \times \mathcal{N}`$, $`0`$ where the data has no row — the zonal power transfer distribution factor of a `flow_based` row for a zone bus: PyPSA's `ptdf_<bus>` column read long, data prep. It may differ by snapshot. No value is zero, as PyPSA fills it |
| $`\mathrm{PTDF}^{f}`$ | `GlobalConstraint_link_ptdf` over $`\Xi \times \mathcal{T} \times \mathcal{G} \times \mathcal{L}`$, $`0`$ where the data has no row — the factor of a `flow_based` row for a corridor link, whose flow enters the row: PyPSA's `ptdf_<link>` column read long, data prep. No value is zero |
| $`\mathrm{zone}`$ | `Bus_flow_based_zone` over $`\mathcal{N}`$ — whether a bus is a zone of a flow-based domain: some `flow_based` row has its `ptdf_<bus>` column, data prep |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{NP}`$ | `FlowBased_net_position` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$, $`0`$ where the mask leaves it out — `FlowBased-net_position` — what a zone bus exports to the flow-based domain, unbounded. It leaves the zone's nodal balance (`flow_based.py:207-234`). A bus that is no zone has none |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{NP}^{\mathrm{inj}}`$ | `FlowBased_injection` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$ — what a zone bus exports to its flow-based domain leaves the bus (`constraints.py:1508`) |

#### Variable domains

**`FlowBased_net_position`**

```math
\mathit{NP}_{\xi,t,n} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ n \in \mathcal{N} \,:\, \mathrm{zone}_{n}
```

#### Definitions

**`FlowBased_injection`**

```math
\mathit{NP}^{\mathrm{inj}}_{\xi,t,n} = -\mathit{NP}_{\xi,t,n} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ n \in \mathcal{N}
```

#### Subject to

**`GlobalConstraint_flow_based_ub`**

```math
\sum_{n \in \mathcal{N}} \mathrm{PTDF}^{z}_{\xi,t,g,n} \cdot \mathit{NP}_{\xi,t,n} + \sum_{l \in \mathcal{L}} \mathrm{PTDF}^{f}_{\xi,t,g,l} \cdot f_{\xi,t,l} \le \mathrm{RAM}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{type}_{g} = \text{'}\mathrm{flow\_based}\text{'} \wedge \mathrm{sense}_{\xi,g} = \text{'}\mathrm{<=}\text{'} \wedge \mathrm{RAM}_{\xi,t,g} \text{ is defined} \wedge \mathrm{in}_{\xi,g,t}
```

**`FlowBased_balance`**

```math
\sum_{n \in \mathcal{N} \,:\, \mathrm{Bus\_flow\_based\_domain}(n) = o} \mathit{NP}_{\xi,t,n} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ o \in \mathcal{O}
```

#### Assumptions

**`GlobalConstraint_flow_based_sense_is_le`**

```math
\mathrm{sense}_{\xi,g} = \text{'}\mathrm{<=}\text{'} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{type}_{g} = \text{'}\mathrm{flow\_based}\text{'}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
