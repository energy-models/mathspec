<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Net import share

An extension of [Calliope in fragments](../index.md). Calliope's example `net_import_share.yaml`: imports over transmission at most a share of a node's own balance, per time step, per year, and over a group of nodes.

<!-- gallery:begin -->
```yaml
dimensions:
  nodes:
    description: Calliope's `nodes` — the places technologies stand at
  techs:
    description: Calliope's `techs` — technologies
  carriers:
    description: Calliope's `carriers` — energy and commodity carriers
  timesteps:
    description: Calliope's `timesteps` — time steps, in order
    dtype: datetime

parameters:
  net_import_share:
    description: >-
      `net_import_share` — the share of a node's flows that imports may make
      up. Calliope's default is 1, and data prep fills it. Calliope reads it
      per node and in a row over a group of nodes; a parameter here has one
      shape, so it is one number
    dims: []

expressions:
  flow_out_transmission_techs:
    description: "`flow_out_transmission_techs` — the outflow of transmission technologies, that is, imports"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      transmission:
        when: carrier_out AND base_tech == 'transmission'
        expression: flow_out
    otherwise: 0
  electricity_imports:
    description: "`flow_out_transmission_techs[carriers=electricity]`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      electricity:
        when: carriers == electricity
        expression: flow_out_transmission_techs
    otherwise: 0
  electricity_balance:
    description: "`$total_energy_balance` — the outflow of electricity at a node, less its inflow"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      electricity:
        when: carriers == electricity
        expression: flow_out - flow_in
    otherwise: 0
  node_group_heat_imports:
    description: "`flow_out_transmission_techs[nodes=$node_group, carriers=$carrier]` — heat imports at nodes `a` and `c`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      group:
        when: (nodes == 'a' OR nodes == 'c') AND carriers == heat
        expression: flow_out_transmission_techs
    otherwise: 0
  node_group_heat_balance:
    description: "`$total_energy_balance` of the node group — the outflow of heat at nodes `a` and `c`, less its inflow"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      group:
        when: (nodes == 'a' OR nodes == 'c') AND carriers == heat
        expression: flow_out - flow_in
    otherwise: 0

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_in: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  net_import_share_max:
    description: >-
      `net_import_share_max` — electricity imports at a node are at most
      their share of its electricity balance in each time step. Calliope's
      `where: any(flow_out_transmission_techs, over=techs)` reads as a link
      at the node putting out any carrier
    dims: [nodes, timesteps]
    where: count(count(carrier_out, over=carriers) >= 1 AND base_tech == 'transmission', over=techs) >= 1
    expression: >-
      net_import_share * sum(sum(electricity_imports, over=techs), over=carriers)
      <= sum(sum(electricity_balance, over=techs), over=carriers)
  net_annual_import_share_max:
    description: "`net_annual_import_share_max` — electricity imports at a node are at most their share of its electricity balance over the year"
    dims: [nodes]
    where: count(count(carrier_out, over=carriers) >= 1 AND base_tech == 'transmission', over=techs) >= 1
    expression: >-
      net_import_share * sum(sum(sum(electricity_imports, over=techs), over=carriers), over=timesteps)
      <= sum(sum(sum(electricity_balance, over=techs), over=carriers), over=timesteps)
  net_annual_import_share_max_node_group:
    description: "`net_annual_import_share_max_node_group` — heat imports at nodes `a` and `c` are at most their share of the group's heat balance over the year"
    dims: []
    expression: net_import_share * sum(node_group_heat_imports) <= sum(node_group_heat_balance)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{net\_import\_share}`$ | `net_import_share` (scalar) — `net_import_share` — the share of a node's flows that imports may make up. Calliope's default is 1, and data prep fills it. Calliope reads it per node and in a row over a group of nodes; a parameter here has one shape, so it is one number |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_in}`$ | `flow_in` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_out\_transmission\_techs}`$ | `flow_out_transmission_techs` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_transmission_techs` — the outflow of transmission technologies, that is, imports |
| $`\mathit{electricity\_imports}`$ | `electricity_imports` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_transmission_techs[carriers=electricity]` |
| $`\mathit{electricity\_balance}`$ | `electricity_balance` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `$total_energy_balance` — the outflow of electricity at a node, less its inflow |
| $`\mathit{node\_group\_heat\_imports}`$ | `node_group_heat_imports` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_transmission_techs[nodes=$node_group, carriers=$carrier]` — heat imports at nodes `a` and `c` |
| $`\mathit{node\_group\_heat\_balance}`$ | `node_group_heat_balance` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `$total_energy_balance` of the node group — the outflow of heat at nodes `a` and `c`, less its inflow |

#### Subject to

**`net_import_share_max`**

```math
\mathrm{net\_import\_share} \cdot \left( \sum_{c \in \mathcal{C}} \sum_{i \in \mathcal{I}} \mathit{electricity\_imports}_{n,i,c,t} \right) \le \sum_{c \in \mathcal{C}} \sum_{i \in \mathcal{I}} \mathit{electricity\_balance}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ t \in \mathcal{T} \,:\, \lvert \{ i \in \mathcal{I} \,:\, \lvert \{ c \in \mathcal{C} \,:\, \mathrm{carrier\_out}_{n,i,c} \} \rvert \ge 1 \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \} \rvert \ge 1
```

**`net_annual_import_share_max`**

```math
\mathrm{net\_import\_share} \cdot \left( \sum_{t \in \mathcal{T}} \sum_{c \in \mathcal{C}} \sum_{i \in \mathcal{I}} \mathit{electricity\_imports}_{n,i,c,t} \right) \le \sum_{t \in \mathcal{T}} \sum_{c \in \mathcal{C}} \sum_{i \in \mathcal{I}} \mathit{electricity\_balance}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N} \,:\, \lvert \{ i \in \mathcal{I} \,:\, \lvert \{ c \in \mathcal{C} \,:\, \mathrm{carrier\_out}_{n,i,c} \} \rvert \ge 1 \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \} \rvert \ge 1
```

**`net_annual_import_share_max_node_group`**

```math
\mathrm{net\_import\_share} \cdot \left( \sum_{n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}} \mathit{node\_group\_heat\_imports}_{n,i,c,t} \right) \le \sum_{n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}} \mathit{node\_group\_heat\_balance}_{n,i,c,t}
```

#### Definitions

**`flow_out_transmission_techs`**

```math
\mathit{flow\_out\_transmission\_techs}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } \mathrm{carrier\_out}_{n,i,c} \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`electricity_imports`**

```math
\mathit{electricity\_imports}_{n,i,c,t} = \begin{cases} \mathit{flow\_out\_transmission\_techs}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{electricity}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`electricity_balance`**

```math
\mathit{electricity\_balance}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} - \mathit{flow\_in}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{electricity}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`node_group_heat_imports`**

```math
\mathit{node\_group\_heat\_imports}_{n,i,c,t} = \begin{cases} \mathit{flow\_out\_transmission\_techs}_{n,i,c,t} & \text{if } \left( n = \text{'}\mathrm{a}\text{'} \vee n = \text{'}\mathrm{c}\text{'} \right) \wedge c = \text{'}\mathrm{heat}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`node_group_heat_balance`**

```math
\mathit{node\_group\_heat\_balance}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} - \mathit{flow\_in}_{n,i,c,t} & \text{if } \left( n = \text{'}\mathrm{a}\text{'} \vee n = \text{'}\mathrm{c}\text{'} \right) \wedge c = \text{'}\mathrm{heat}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```
<!-- gallery:end -->
