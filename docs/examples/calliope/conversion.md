<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Conversion

One of the base fragments of [Calliope in fragments](index.md). Calliope's `balance_conversion`, alone: a conversion technology puts out what it takes in. It declares nothing, and reads everything it needs.

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

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    include_storage: { dims: [nodes, techs], dtype: bool }
  expressions:
    flow_out_inc_eff: { dims: [nodes, techs, carriers, timesteps] }
    flow_in_inc_eff: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  balance_conversion:
    description: "`balance_conversion` — a conversion technology puts out, before its losses, what it takes in after them"
    dims: [nodes, techs, timesteps]
    where: base_tech == 'conversion' AND NOT include_storage
    expression: sum(flow_out_inc_eff, over=carriers) == sum(flow_in_inc_eff, over=carriers)
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{include\_storage}`$ | `include_storage` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{flow\_in\_inc\_eff}`$ | `flow_in_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |

#### Subject to

**`balance_conversion`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_out\_inc\_eff}_{n,i,c,t} = \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{conversion}\text{'} \wedge \neg \mathrm{include\_storage}_{n,i}
```
<!-- gallery:end -->
