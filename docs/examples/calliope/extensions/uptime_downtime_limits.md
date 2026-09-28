<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Uptime and downtime limits

An extension of [Calliope in fragments](../index.md). Calliope's example `uptime_downtime_limits.yaml`: capacity factors over the whole time, forced downtime, and a cap on the time steps a unit-bought technology runs in.

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
  capacity_factor_min:
    description: "`capacity_factor_min` — the least capacity factor a technology reaches over the whole time"
    dims: [nodes, techs]
  capacity_factor_max:
    description: "`capacity_factor_max` — the most capacity factor a technology reaches over the whole time; given only where set"
    dims: [nodes, techs]
  uptime_limit:
    description: "`uptime_limit` — the most time steps a technology runs in, weighted; given only where set"
    dims: [nodes, techs]
  downtime_periods:
    description: "`downtime_periods` — whether a technology is down for maintenance in a time step"
    dims: [nodes, techs, timesteps]
    dtype: bool

expressions:
  total_time:
    description: "`$total_time` — the hours the modelled time steps stand for"
    expression: sum(timestep_resolution * timestep_weights, over=timesteps)

given:
  parameters:
    carrier_out: { dims: [nodes, techs, carriers], dtype: bool }
    timestep_resolution: { dims: [timesteps] }
    timestep_weights: { dims: [timesteps] }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
    flow_cap: { dims: [nodes, techs, carriers] }
    operating_units: { dims: [nodes, techs, timesteps] }

constraints:
  annual_capacity_factor_min:
    description: "`annual_capacity_factor_min` — a technology's outflow over the whole time is at least its least capacity factor"
    dims: [nodes, techs, carriers]
    where: carrier_out AND capacity_factor_min
    expression: sum(flow_out * timestep_weights, over=timesteps) >= flow_cap * capacity_factor_min * total_time
  annual_capacity_factor_max:
    description: "`annual_capacity_factor_max` — a technology's outflow over the whole time is at most its most capacity factor"
    dims: [nodes, techs, carriers]
    where: carrier_out AND capacity_factor_max
    expression: sum(flow_out * timestep_weights, over=timesteps) <= flow_cap * capacity_factor_max * total_time
  downtime_period:
    description: "`downtime_period` — a technology puts out nothing in a time step it is down"
    dims: [nodes, techs, timesteps]
    where: downtime_periods
    expression: sum(flow_out, over=carriers) == 0
  downtime_period_decision:
    description: >-
      `downtime_period_decision` — a unit-bought technology runs in at most
      its limit of time steps. Calliope's `where: operating_units` over a
      technology reads as the technology running in whole units at all
    dims: [nodes, techs]
    where: count(operating_units, over=timesteps) >= 1 AND uptime_limit
    expression: sum(operating_units * timestep_weights, over=timesteps) <= uptime_limit
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
| $`\mathrm{capacity\_factor\_min}`$ | `capacity_factor_min` over $`\mathcal{N} \times \mathcal{I}`$ — `capacity_factor_min` — the least capacity factor a technology reaches over the whole time |
| $`\mathrm{capacity\_factor\_max}`$ | `capacity_factor_max` over $`\mathcal{N} \times \mathcal{I}`$ — `capacity_factor_max` — the most capacity factor a technology reaches over the whole time; given only where set |
| $`\mathrm{uptime\_limit}`$ | `uptime_limit` over $`\mathcal{N} \times \mathcal{I}`$ — `uptime_limit` — the most time steps a technology runs in, weighted; given only where set |
| $`\mathrm{downtime\_periods}`$ | `downtime_periods` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `downtime_periods` — whether a technology is down for maintenance in a time step |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{carrier\_out}`$ | `carrier_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$, data another file declares |
| $`\mathrm{timestep\_resolution}`$ | `timestep_resolution` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_cap}`$ | `flow_cap` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C}`$ |
| $`\mathit{operating\_units}`$ | `operating_units` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathrm{total\_time}`$ | `total_time` (scalar) — `$total_time` — the hours the modelled time steps stand for |

#### Subject to

**`annual_capacity_factor_min`**

```math
\sum_{t \in \mathcal{T}} \mathit{flow\_out}_{n,i,c,t} \cdot \mathrm{timestep\_weights}_{t} \ge \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{capacity\_factor\_min}_{n,i} \cdot \mathrm{total\_time} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathrm{carrier\_out}_{n,i,c} \wedge \mathrm{capacity\_factor\_min}_{n,i} \text{ is defined}
```

**`annual_capacity_factor_max`**

```math
\sum_{t \in \mathcal{T}} \mathit{flow\_out}_{n,i,c,t} \cdot \mathrm{timestep\_weights}_{t} \le \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{capacity\_factor\_max}_{n,i} \cdot \mathrm{total\_time} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathrm{carrier\_out}_{n,i,c} \wedge \mathrm{capacity\_factor\_max}_{n,i} \text{ is defined}
```

**`downtime_period`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_out}_{n,i,c,t} = 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{downtime\_periods}_{n,i,t}
```

**`downtime_period_decision`**

```math
\sum_{t \in \mathcal{T}} \mathit{operating\_units}_{n,i,t} \cdot \mathrm{timestep\_weights}_{t} \le \mathrm{uptime\_limit}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \lvert \{ t \in \mathcal{T} \,:\, \mathit{operating\_units}_{n,i,t} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{uptime\_limit}_{n,i} \text{ is defined}
```

#### Definitions

**`total_time`**

```math
\mathrm{total\_time} = \sum_{t \in \mathcal{T}} \mathrm{timestep\_resolution}_{t} \cdot \mathrm{timestep\_weights}_{t}
```
<!-- gallery:end -->
