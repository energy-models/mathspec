<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Supply with storage

One of the base fragments of [Calliope in fragments](index.md). Calliope's `balance_supply_with_storage`, the one row that couples a supply technology to a store. It is a file of its own so that supply and storage each compose without the other.

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
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
    source_eff: { dims: [nodes, techs, timesteps] }
  variables:
    storage: { dims: [nodes, techs, timesteps] }
    source_use: { dims: [nodes, techs, timesteps] }
  expressions:
    storage_previous_step: { dims: [nodes, techs, timesteps] }
    flow_out_inc_eff: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  balance_supply_with_storage:
    description: >-
      `balance_supply_with_storage` — a supply technology with a store puts
      in what it takes from its source and draws out what it puts out
    dims: [nodes, techs, carriers, timesteps]
    where: carrier_out AND storage AND base_tech == 'supply'
    expression: storage == storage_previous_step + source_use * source_eff - flow_out_inc_eff
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
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{source\_eff}`$ | `source_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$, data another file declares |
| $`\mathit{storage}`$ | `storage` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ |
| $`\mathit{source\_use}`$ | `source_use` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ |
| $`\mathit{storage}^{\mathrm{previous,step}}`$ | `storage_previous_step` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |

#### Subject to

**`balance_supply_with_storage`**

```math
\mathit{storage}_{n,i,t} = \mathit{storage}^{\mathrm{previous,step}}_{n,i,t} + \mathit{source\_use}_{n,i,t} \cdot \mathrm{source\_eff}_{n,i,t} - \mathit{flow\_out\_inc\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_out}_{n,i,c} \wedge \mathit{storage}_{n,i,t} \text{ exists} \wedge \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'}
```
<!-- gallery:end -->
