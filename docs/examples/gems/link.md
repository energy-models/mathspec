<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Links

This file states the GEMS `link` model. It is one of the [ten fragments](index.md)
of the GEMS port. It adds two terms to `Bus_balance_port_flow`,
one for each port. GEMS bounds `flow` below by `-capacity_indirect`. A
[bound](../../reference/language/declarations.md#variables) is a number or the
name of a parameter, so it cannot hold the minus sign. The file states that
bound as the constraint `Link_flow_floor` instead.

<!-- gallery:begin -->
```yaml
description: >-
  GEMS `link`. A flow between two buses, out of `out_port` and into
  `in_port`, made of a direct and an indirect part.
dimensions:
  time: { dtype: int, description: "time steps of the horizon, counted from 0" }
  scenario: { dtype: int, description: scenarios of the data }
  bus: { description: "`bus` components: nodes where flows balance" }
  link: { description: "`link` components: flows between two buses" }
relations:
  Link_out_port: { key: [link, bus], description: "connections from a link's `out_port` to a bus" }
  Link_in_port: { key: [link, bus], description: "connections from a link's `in_port` to a bus" }
parameters:
  Link_capacity_direct: { dims: [time, scenario, link], description: largest flow out of `out_port` }
  Link_capacity_indirect: { dims: [time, scenario, link], description: largest flow out of `in_port` }
variables:
  Link_flow_direct:
    dims: [time, scenario, link]
    bounds: { lower: 0, upper: Link_capacity_direct }
    description: flow out of `out_port`
  Link_flow_indirect:
    dims: [time, scenario, link]
    bounds: { lower: 0, upper: Link_capacity_indirect }
    description: flow out of `in_port`
  Link_flow:
    dims: [time, scenario, link]
    bounds: { upper: Link_capacity_direct }
    description: net flow out of `out_port`
given:
  expressions:
    Bus_balance_port_flow: { dims: [time, scenario, bus] }
expressions:
  Link_out_port_flow:
    description: "`out_port.flow` of a link, `flow`"
    expression: sum(Link_flow, by=Link_out_port, over=link, into=bus)
    adds_to: Bus_balance_port_flow
  Link_in_port_flow:
    description: "`in_port.flow` of a link, `-flow`"
    expression: sum(-Link_flow, by=Link_in_port, over=link, into=bus)
    adds_to: Bus_balance_port_flow
constraints:
  Link_flow_direct_indirect:
    dims: [time, scenario, link]
    description: "`link.flow_direct_indirect`"
    expression: Link_flow == Link_flow_direct - Link_flow_indirect
  Link_flow_floor:
    dims: [time, scenario, link]
    description: >-
      the GEMS lower bound `-capacity_indirect` on `flow`. A bound here is a
      name, so the negated bound is a row
    expression: Link_flow >= -Link_capacity_indirect
```

GEMS `link`. A flow between two buses, out of `out_port` and into `in_port`, made of a direct and an indirect part.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `time` — time steps of the horizon, counted from 0 |
| $`\mathcal{S}`$ | index $`s`$ — `scenario` — scenarios of the data |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{Link\_out\_port} \subseteq \mathcal{L} \times \mathcal{B},\ \mathrm{Link\_in\_port} \subseteq \mathcal{L} \times \mathcal{B}`$ — `bus` components: nodes where flows balance |
| $`\mathcal{L}`$ | index $`l`$ — `link` with $`\mathrm{Link\_out\_port} \subseteq \mathcal{L} \times \mathcal{B},\ \mathrm{Link\_in\_port} \subseteq \mathcal{L} \times \mathcal{B}`$ — `link` components: flows between two buses |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Link\_capacity\_direct}`$ | `Link_capacity_direct` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — largest flow out of `out_port` |
| $`\mathrm{Link\_capacity\_indirect}`$ | `Link_capacity_indirect` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — largest flow out of `in_port` |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{Link\_flow\_direct}`$ | `Link_flow_direct` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — flow out of `out_port` |
| $`\mathit{Link\_flow\_indirect}`$ | `Link_flow_indirect` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — flow out of `in_port` |
| $`\mathit{Link\_flow}`$ | `Link_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{L}`$ — net flow out of `out_port` |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_balance\_port\_flow}`$ | `Bus_balance_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$, an expression this file adds `Link_out_port_flow`, `Link_in_port_flow` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Link\_out\_port\_flow}`$ | `Link_out_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — `out_port.flow` of a link, `flow` |
| $`\mathit{Link\_in\_port\_flow}`$ | `Link_in_port_flow` over $`\mathcal{T} \times \mathcal{S} \times \mathcal{B}`$ — `in_port.flow` of a link, `-flow` |

Upright is what the data supplies — a parameter such as $`\mathrm{Link\_capacity\_direct}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{Link\_flow\_direct}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`Link_flow_direct_indirect`**

```math
\mathit{Link\_flow}_{t,s,l} = \mathit{Link\_flow\_direct}_{t,s,l} - \mathit{Link\_flow\_indirect}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ l \in \mathcal{L}
```

**`Link_flow_floor`**

```math
\mathit{Link\_flow}_{t,s,l} \ge -\mathrm{Link\_capacity\_indirect}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ l \in \mathcal{L}
```

#### Definitions

**`Link_out_port_flow`**

```math
\mathit{Link\_out\_port\_flow}_{t,s,b} = \sum_{l \in \mathcal{L} \,:\, \left( l,\ b \right) \in \mathrm{Link\_out\_port}} \mathit{Link\_flow}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

**`Link_in_port_flow`**

```math
\mathit{Link\_in\_port\_flow}_{t,s,b} = \sum_{l \in \mathcal{L} \,:\, \left( l,\ b \right) \in \mathrm{Link\_in\_port}} -\mathit{Link\_flow}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ b \in \mathcal{B}
```

#### Variable domains

**`Link_flow_direct`**

```math
0 \le \mathit{Link\_flow\_direct}_{t,s,l} \le \mathrm{Link\_capacity\_direct}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ l \in \mathcal{L}
```

**`Link_flow_indirect`**

```math
0 \le \mathit{Link\_flow\_indirect}_{t,s,l} \le \mathrm{Link\_capacity\_indirect}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ l \in \mathcal{L}
```

**`Link_flow`**

```math
\mathit{Link\_flow}_{t,s,l} \le \mathrm{Link\_capacity\_direct}_{t,s,l} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S},\ l \in \mathcal{L}
```
<!-- gallery:end -->
