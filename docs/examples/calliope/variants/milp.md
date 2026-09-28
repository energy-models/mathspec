<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The MILP patch

A patch of [Calliope in fragments](../index.md). What Calliope's `milp.yaml` changes in the base: the capacity bounds open to zero, since the minimums become rows the units scale, and the continuous flow limits hold only where no unit runs. What it adds is [the MILP fragment](../extensions/milp.md). A patch is not a spec, so it prints as the declarations it writes, in the spec it lands on.

<!-- gallery:begin -->
```python
ms.override(
    ms.merge(base + ['extensions/milp.yaml']),
    ['variants/milp.yaml'],
)
```

```yaml title="variants/milp.yaml"
parameters:
  flow_cap_min:
    description: >-
      `flow_cap_min` — least flow capacity, scaled by the units bought where
      a technology buys units; given only where set, as no bound reads it
  flow_cap_min_systemwide:
    description: >-
      `flow_cap_min_systemwide` — least flow capacity of a technology over
      every node, scaled by the units bought where it buys units; given only
      where set
  flow_out_min_relative:
    description: >-
      `flow_out_min_relative` — least outflow, per unit of flow capacity. For
      a continuous technology it holds in every time step; given only where
      set
  storage_cap_min:
    description: "`storage_cap_min` — least storage capacity; given only where set, as no bound reads it"
  area_use_min:
    description: "`area_use_min` — least area use; given only where set, as no bound reads it"
  source_cap_min:
    description: "`source_cap_min` — least source capacity; given only where set, as no bound reads it"

variables:
  flow_cap: { bounds: { lower: 0 } }
  area_use: { bounds: { lower: 0 } }
  source_cap: { bounds: { lower: 0 } }
  storage_cap: { bounds: { lower: 0 } }

constraints:
  flow_out_max:
    description: "`flow_out_max` — a continuous technology's outflow is at most its flow capacity over the time step"
    where: carrier_out AND NOT operating_units
  flow_out_min:
    description: "`flow_out_min` — a continuous technology's outflow is at least its least share of the flow capacity"
    where: flow_cap AND flow_out_min_relative AND NOT operating_units
  flow_in_max:
    description: "`flow_in_max` — a continuous technology's inflow is at most its flow capacity over the time step"
    where: carrier_in AND NOT operating_units
  flow_capacity_systemwide_min:
    description: >-
      `flow_capacity_systemwide_min` where no unit is bought — the flow
      capacity over every node is at least the system-wide minimum
    where: count(flow_cap, over=nodes) >= 1 AND flow_cap_min_systemwide AND NOT count(purchased_units, over=nodes) >= 1
```

**`flow_cap`**

```math
0 \le \mathit{flow\_cap}_{n,i,c} \le \mathrm{flow\_cap\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \mathrm{carrier\_in}_{n,i,c} \vee \mathrm{carrier\_out}_{n,i,c}
```

**`area_use`**

```math
0 \le \mathit{area\_use}_{n,i} \le \mathrm{area\_use\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{area\_use\_min}_{n,i} > 0 \vee \mathrm{area\_use\_max}_{n,i} \text{ is defined} \vee \mathrm{area\_use\_per\_flow\_cap}_{n,i} \text{ is defined} \vee \mathrm{sink\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'} \vee \mathrm{source\_unit}_{n,i} = \text{'}\mathrm{per\_area}\text{'}
```

**`source_cap`**

```math
0 \le \mathit{source\_cap}_{n,i} \le \mathrm{source\_cap\_max}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{supply}\text{'}
```

**`storage_cap`**

```math
0 \le \mathit{storage}^{\mathrm{cap}}_{n,i} \le \mathrm{storage}^{\mathrm{cap,max}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`flow_out_max`**

```math
\mathit{flow\_out}_{n,i,c,t} \le \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_out\_parasitic\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_out}_{n,i,c} \wedge \neg \left( \mathit{operating\_units}_{n,i,t} \text{ exists} \right)
```

**`flow_out_min`**

```math
\mathit{flow\_out}_{n,i,c,t} \ge \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{timestep\_resolution}_{t} \cdot \mathrm{flow\_out\_min\_relative}_{n,i,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \wedge \mathrm{flow\_out\_min\_relative}_{n,i,t} \text{ is defined} \wedge \neg \left( \mathit{operating\_units}_{n,i,t} \text{ exists} \right)
```

**`flow_in_max`**

```math
\mathit{flow\_in}_{n,i,c,t} \le \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{timestep\_resolution}_{t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{carrier\_in}_{n,i,c} \wedge \neg \left( \mathit{operating\_units}_{n,i,t} \text{ exists} \right)
```

**`flow_capacity_systemwide_min`**

```math
\sum_{n \in \mathcal{N}} \mathit{flow\_cap}_{n,i,c} \ge \mathrm{flow\_cap\_min\_systemwide}_{i,c} \qquad \forall\, i \in \mathcal{I},\ c \in \mathcal{C} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathit{flow\_cap}_{n,i,c} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{flow\_cap\_min\_systemwide}_{i,c} \text{ is defined} \wedge \neg \left( \lvert \{ n \in \mathcal{N} \,:\, \mathit{purchased\_units}_{n,i} \text{ exists} \} \rvert \ge 1 \right)
```
<!-- gallery:end -->
