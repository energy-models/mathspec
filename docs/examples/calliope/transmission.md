<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Transmission

One of the base fragments of [Calliope in fragments](index.md). Links between nodes: a link carries what it takes in at one end to the other, and has one capacity at both ends.

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

relations:
  link_from:
    description: >-
      `link_from` — the node a transmission technology links from. Calliope
      reads it as `map_dim(nodes, link_from)`, a mask over technology and
      node, which is the relation's own row test
    key: [techs, nodes]
  link_to:
    description: >-
      `link_to` — the node a transmission technology links to, read as
      `link_from` is
    key: [techs, nodes]

expressions:
  flow_cap_from:
    description: "`where(flow_cap, map_dim(nodes, link_from))` — a link's flow capacity at the node it links from"
    dims: [nodes, techs, carriers]
    cases:
      from:
        when: link_from
        expression: flow_cap
    otherwise: 0
  flow_cap_to:
    description: "`where(flow_cap, map_dim(nodes, link_to))` — a link's flow capacity at the node it links to"
    dims: [nodes, techs, carriers]
    cases:
      to:
        when: link_to
        expression: flow_cap
    otherwise: 0

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
  variables:
    flow_cap: { dims: [nodes, techs, carriers] }
  expressions:
    flow_out_inc_eff: { dims: [nodes, techs, carriers, timesteps] }
    flow_in_inc_eff: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  balance_transmission:
    description: "`balance_transmission` — a link puts out at one end, before losses, what it takes in at the other after them"
    dims: [techs, timesteps]
    where: base_tech == 'transmission'
    expression: >-
      sum(flow_out_inc_eff, over=[nodes, carriers])
      == sum(flow_in_inc_eff, over=[nodes, carriers])
  symmetric_transmission:
    description: "`symmetric_transmission` — a link has the same flow capacity at both ends"
    dims: [techs, carriers]
    where: count(carrier_out, over=nodes) >= 1 AND base_tech == 'transmission'
    expression: sum(flow_cap_from, over=nodes) == sum(flow_cap_to, over=nodes)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` with $`\mathrm{link\_from} \subseteq \mathcal{I} \times \mathcal{N},\ \mathrm{link\_to} \subseteq \mathcal{I} \times \mathcal{N}`$ — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` with $`\mathrm{link\_from} \subseteq \mathcal{I} \times \mathcal{N},\ \mathrm{link\_to} \subseteq \mathcal{I} \times \mathcal{N}`$ — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{flow\_in\_inc\_eff}`$ | `flow_in_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{flow\_cap\_from}`$ | `flow_cap_from` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `where(flow_cap, map_dim(nodes, link_from))` — a link's flow capacity at the node it links from |
| $`\mathit{flow\_cap\_to}`$ | `flow_cap_to` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ — `where(flow_cap, map_dim(nodes, link_to))` — a link's flow capacity at the node it links to |

#### Subject to

**`balance_transmission`**

```math
\sum_{n \in \mathcal{N},\ c \in \mathcal{C}} \mathit{flow\_out\_inc\_eff}_{n,i,c,t} = \sum_{n \in \mathcal{N},\ c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \qquad \forall\, i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'}
```

**`symmetric_transmission`**

```math
\sum_{n \in \mathcal{N}} \mathit{flow\_cap\_from}_{n,i,c} = \sum_{n \in \mathcal{N}} \mathit{flow\_cap\_to}_{n,i,c} \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathrm{carrier\_out}_{n,i,c} \} \rvert \ge 1 \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{transmission}\text{'}
```

#### Definitions

**`flow_cap_from`**

```math
\mathit{flow\_cap\_from}_{n,i,c} = \begin{cases} \mathit{flow\_cap}_{n,i,c} & \text{if } \left( i,\ n \right) \in \mathrm{link\_from} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C}
```

**`flow_cap_to`**

```math
\mathit{flow\_cap\_to}_{n,i,c} = \begin{cases} \mathit{flow\_cap}_{n,i,c} & \text{if } \left( i,\ n \right) \in \mathrm{link\_to} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C}
```
<!-- gallery:end -->
