<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Units with ports

Units with ports is a specification of an optimisation model
([a spec](../reference/glossary.md#spec)) in which each unit attaches to buses
through numbered ports. Each port number matches one of the `bus0`, `bus1`, …
columns of an open-source power system modelling framework
([PyPSA](https://pypsa.org)). The [relation](../reference/language/relations.md)
`connection` lists the bus and the role of each port. Its key is the unit and
the port, not the bus, so two ports of one unit may attach to the same bus.

`efficiency` is declared over every unit, port and snapshot. Its
[`where:`](../reference/language/parameters-variables-constraints.md#where)
keeps only the output ports, and `missing: 1` applies only there. Where
`connection` has no row, `injection` takes its `otherwise:` and `efficiency`
is [absent](../reference/language/absence.md), so `injection` is absent too.
The sum in `balance` therefore has a term only for the ports that attach to
each bus.

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
    dims: [unit, port]
    missing: absent

maps:
  connection: { bus: bus, role: role }

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
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{bus}: \mathrm{connection} \to \mathcal{B}`$ — nodes of the network |
| $`\mathcal{P}`$ | index $`p`$ — `port` with $`\mathrm{connection} \subseteq \mathcal{P} \times \mathcal{U},\ \mathrm{bus}: \mathrm{connection} \to \mathcal{B},\ \mathrm{role}: \mathrm{connection} \to \mathcal{R}`$, `connection` is `absent` where the data has no row — an attachment of a unit, numbered as PyPSA's bus0, bus1, ... |
| $`\mathcal{R}`$ | index $`r`$ — `role` with $`\mathrm{role}: \mathrm{connection} \to \mathcal{R}`$ — input or output |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{U}`$ | index $`u`$ — `unit` with $`\mathrm{connection} \subseteq \mathcal{P} \times \mathcal{U},\ \mathrm{bus}: \mathrm{connection} \to \mathcal{B},\ \mathrm{role}: \mathrm{connection} \to \mathcal{R}`$, `connection` is `absent` where the data has no row — converters, such as an electrolyser or a heat pump |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{U}`$ — the most a unit can draw at its input |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{B}`$ — price of power bought at a bus |
| $`\mathrm{efficiency}`$ | `efficiency` over $`\mathcal{P} \times \mathcal{T} \times \mathcal{U}`$, only where $`\mathrm{role}(p,\ u) = \text{'}\mathrm{output}\text{'}`$, $`1`$ where the data has no row — share of the drawn power that an output port delivers |
| $`\mathrm{load}`$ | `load` over $`\mathcal{B} \times \mathcal{T}`$ — demand to be met |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow}`$ | `flow` over $`\mathcal{T} \times \mathcal{U}`$ — power a unit draws at its input |
| $`\mathit{supply}`$ | `supply` over $`\mathcal{B} \times \mathcal{T}`$ — power bought at a bus |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{injection}`$ | `injection` over $`\mathcal{P} \times \mathcal{T} \times \mathcal{U}`$ — what a port puts into its bus |

#### Variable domains

**`flow`**

```math
0 \le \mathit{flow}_{t,u} \le \mathrm{capacity}_{u} \qquad \forall\, t \in \mathcal{T},\ u \in \mathcal{U}
```

**`supply`**

```math
\mathit{supply}_{b,t} \ge 0 \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

#### Definitions

**`injection`**

```math
\mathit{injection}_{p,t,u} = \begin{cases} -\mathit{flow}_{t,u} & \text{if } \mathrm{role}(p,\ u) = \text{'}\mathrm{input}\text{'} \\ \mathrm{efficiency}_{p,t,u} \cdot \mathit{flow}_{t,u} & \text{otherwise} \end{cases} \qquad \forall\, p \in \mathcal{P},\ t \in \mathcal{T},\ u \in \mathcal{U}
```

#### Objective

```math
\min \sum_{b \in \mathcal{B},\ t \in \mathcal{T}} \mathrm{cost}_{b} \cdot \mathit{supply}_{b,t}
```

#### Subject to

**`balance`**

```math
\mathit{supply}_{b,t} + \sum_{p \in \mathcal{P},\ u \in \mathcal{U} \,:\, \mathrm{bus}(p,\ u) = b} \mathit{injection}_{p,t,u} = \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```
<!-- gallery:end -->
