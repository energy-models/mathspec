<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Units with ports

This file connects units to buses through numbered ports, as PyPSA's `bus0`,
`bus1`, … columns do. One relation, `connection`, says which bus each port of a
unit attaches to and whether the port draws or delivers. Two ports of one unit
may attach to the same bus.

`efficiency` is declared over every unit, port and snapshot, but its `where:`
keeps only the output ports, and `missing: 1` fills only those
([a parameter's mask](../reference/language/parameters-variables-constraints.md#a-parameters-mask)).
Outside `connection`, `injection` is absent, so `balance` adds up only the ports
that attach to each bus.

<!-- gallery:begin -->
```yaml
description: Units that draw power from one bus and deliver it to others, through numbered ports.

dimensions:
  snapshot: { dtype: int, description: dispatch periods }
  bus: { description: nodes of the network }
  unit: { description: "converters, such as an electrolyser or a heat pump" }
  port: { dtype: int, description: "an attachment of a unit, numbered as PyPSA's bus0, bus1, ..." }
  role: { description: input or output }

relations:
  connection:
    description: the bus each port of a unit attaches to, and whether the port draws or delivers
    key: [unit, port]
    values: [bus, role]
    missing: absent

parameters:
  capacity: { dims: [unit], description: the most a unit can draw at its input }
  efficiency:
    description: share of the drawn power that an output port delivers
    dims: [unit, port, snapshot]
    where: "connection[role] == 'output'"
    missing: 1
  load: { dims: [bus, snapshot], description: demand to be met }
  cost: { dims: [bus], description: price of power bought at a bus }

variables:
  flow:
    description: power a unit draws at its input
    dims: [unit, snapshot]
    bounds: { lower: 0, upper: capacity }
  supply:
    description: power bought at a bus
    dims: [bus, snapshot]
    bounds: { lower: 0 }

expressions:
  injection:
    description: what a port puts into its bus
    dims: [unit, port, snapshot]
    cases:
      draws: { when: "connection[role] == 'input'", expression: -flow }
    otherwise: efficiency * flow

constraints:
  balance:
    dims: [bus, snapshot]
    expression: supply + sum(injection, over=[unit, port], by=connection[bus]) == load

objective:
  sense: minimize
  expression: sum(cost * supply)
```

Units that draw power from one bus and deliver it to others, through numbered ports.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{connection}: \mathcal{U} \times \mathcal{P} \to \mathcal{B} \times \mathcal{R}`$, `connection` is `absent` where the data has no row — nodes of the network |
| $`\mathcal{U}`$ | index $`u`$ — `unit` with $`\mathrm{connection}: \mathcal{U} \times \mathcal{P} \to \mathcal{B} \times \mathcal{R}`$, `connection` is `absent` where the data has no row — converters, such as an electrolyser or a heat pump |
| $`\mathcal{P}`$ | index $`p`$ — `port` with $`\mathrm{connection}: \mathcal{U} \times \mathcal{P} \to \mathcal{B} \times \mathcal{R}`$, `connection` is `absent` where the data has no row — an attachment of a unit, numbered as PyPSA's bus0, bus1, ... |
| $`\mathcal{R}`$ | index $`r`$ — `role` with $`\mathrm{connection}: \mathcal{U} \times \mathcal{P} \to \mathcal{B} \times \mathcal{R}`$, `connection` is `absent` where the data has no row — input or output |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{U}`$ — the most a unit can draw at its input |
| $`\mathrm{efficiency}`$ | `efficiency` over $`\mathcal{U} \times \mathcal{P} \times \mathcal{T}`$, only where $`\mathrm{connection.role}(u,\ p) = \text{'}\mathrm{output}\text{'}`$, $`1`$ where the data has no row — share of the drawn power that an output port delivers |
| $`\mathrm{load}`$ | `load` over $`\mathcal{B} \times \mathcal{T}`$ — demand to be met |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{B}`$ — price of power bought at a bus |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow}`$ | `flow` over $`\mathcal{U} \times \mathcal{T}`$ — power a unit draws at its input |
| $`\mathit{supply}`$ | `supply` over $`\mathcal{B} \times \mathcal{T}`$ — power bought at a bus |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{injection}`$ | `injection` over $`\mathcal{U} \times \mathcal{P} \times \mathcal{T}`$ — what a port puts into its bus |

#### Variable domains

**`flow`**

```math
0 \le \mathit{flow}_{u,t} \le \mathrm{capacity}_{u} \qquad \forall\, u \in \mathcal{U},\ t \in \mathcal{T}
```

**`supply`**

```math
\mathit{supply}_{b,t} \ge 0 \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

#### Definitions

**`injection`**

```math
\mathit{injection}_{u,p,t} = \begin{cases} -\mathit{flow}_{u,t} & \text{if } \mathrm{connection.role}(u,\ p) = \text{'}\mathrm{input}\text{'} \\ \mathrm{efficiency}_{u,p,t} \cdot \mathit{flow}_{u,t} & \text{otherwise} \end{cases} \qquad \forall\, u \in \mathcal{U},\ p \in \mathcal{P},\ t \in \mathcal{T}
```

#### Objective

```math
\min \sum_{t \in \mathcal{T},\ b \in \mathcal{B}} \mathrm{cost}_{b} \cdot \mathit{supply}_{b,t}
```

#### Subject to

**`balance`**

```math
\mathit{supply}_{b,t} + \sum_{u \in \mathcal{U},\ p \in \mathcal{P} \,:\, \mathrm{connection.bus}(u,\ p) = b} \mathit{injection}_{u,p,t} = \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```
<!-- gallery:end -->
