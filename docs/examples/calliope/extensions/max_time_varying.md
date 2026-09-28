<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Time-varying flow limit

An extension of [Calliope in fragments](../index.md). Calliope's example `max_time_varying.yaml`: outflow at most a share of the flow capacity that varies in time.

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
  flow_cap_max_relative_per_ts:
    description: "`flow_cap_max_relative_per_ts` — the share of its flow capacity a technology may put out in a time step; given only where set"
    dims: [nodes, techs, timesteps]

given:
  parameters:
    flow_out_parasitic_eff: { dims: [nodes, techs, carriers, timesteps] }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_cap: { dims: [nodes, techs, carriers] }

constraints:
  max_time_varying_flow_cap:
    description: "`max_time_varying_flow_cap` — outflow is at most a share of the flow capacity that varies in time"
    dims: [nodes, techs, carriers, timesteps]
    where: flow_out AND flow_cap_max_relative_per_ts
    expression: flow_out <= flow_cap_max_relative_per_ts * flow_cap * flow_out_parasitic_eff
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
| $`\mathrm{flow\_cap\_max\_relative\_per\_ts}`$ | `flow_cap_max_relative_per_ts` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `flow_cap_max_relative_per_ts` — the share of its flow capacity a technology may put out in a time step; given only where set |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{flow\_out\_parasitic\_eff}`$ | `flow_out_parasitic_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |

#### Subject to

**`max_time_varying_flow_cap`**

```math
\mathit{flow\_out}_{n,i,c,t} \le \mathrm{flow\_cap\_max\_relative\_per\_ts}_{n,i,t} \cdot \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{flow\_out\_parasitic\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_out}_{n,i,c,t} \text{ exists} \wedge \mathrm{flow\_cap\_max\_relative\_per\_ts}_{n,i,t} \text{ is defined}
```
<!-- gallery:end -->
