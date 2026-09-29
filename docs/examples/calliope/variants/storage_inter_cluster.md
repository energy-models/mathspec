<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Inter-cluster storage

A patch of [Calliope in fragments](../index.md). Calliope's `storage_inter_cluster.yaml`: with clustered days, a store carries a fill between the days of the whole time series and swings within its clustered day. A patch is not a spec, so it prints as the declarations it writes, in the spec it lands on.

<!-- gallery:begin -->
```python
ms.override(
    ms.merge(base),
    ['variants/storage_inter_cluster.yaml'],
)
```

```yaml title="variants/storage_inter_cluster.yaml"
dimensions:
  clusters:
    description: Calliope's `clusters` — the representative days a clustered time series is made of
    dtype: int
  datesteps:
    description: Calliope's `datesteps` — the days of the whole time series, in order
    dtype: datetime

relations:
  timestep_cluster:
    description: "`timestep_cluster` — the cluster a time step belongs to"
    key: timesteps
    values: clusters
  lookup_datestep_cluster:
    description: "`lookup_datestep_cluster` — the cluster a day stands for"
    key: datesteps
    values: clusters
  lookup_datestep_last_cluster_timestep:
    description: "`lookup_datestep_last_cluster_timestep` — the last time step of the cluster a day stands for"
    key: datesteps
    values: timesteps

parameters:
  storage_retention:
    description: >-
      `1 - storage_loss` — the share of what a store holds that it keeps for
      an hour, data prep. Between days it is raised to 24, so it does not
      vary over time steps here
    dims: [nodes, techs]

variables:
  storage:
    description: >-
      `storage` — what a store holds within a clustered day, relative to what
      it carries between days. It may go below zero, as long as the sum does
      not
    bounds: { lower: null }
  storage_inter_cluster:
    description: "`storage_inter_cluster` — what a store carries from one day of the whole time series to the next"
    dims: [nodes, techs, datesteps]
    where: include_storage OR base_tech == 'storage'
    bounds: { lower: 0 }
    absence: zero
  storage_intra_cluster_max:
    description: "`storage_intra_cluster_max` — the most a store holds within a clustered day"
    dims: [nodes, techs, clusters]
    where: include_storage OR base_tech == 'storage'
  storage_intra_cluster_min:
    description: "`storage_intra_cluster_min` — the least a store holds within a clustered day"
    dims: [nodes, techs, clusters]
    where: include_storage OR base_tech == 'storage'

expressions:
  storage_previous_step:
    description: >-
      `$storage_previous_step` under inter-cluster storage — what a store
      carries into a time step: its initial fill at the first step of a store
      that is not cyclic, nothing at the first step of a clustered day, and
      what is left of the step before everywhere else
    cases:
      initial:
        when: position(timesteps) == 0 AND NOT cyclic_storage
        expression: storage_initial * storage_cap
      cluster_start:
        when: lookup_cluster_last_timestep AND NOT (position(timesteps) == 0 AND NOT cyclic_storage)
        expression: "0"
  storage_inter_previous_step:
    description: >-
      `$storage_previous_step` of `balance_storage_inter` — what a store
      carries into a day: its initial fill on the first day of a store that
      is not cyclic, and what is left of the day before everywhere else.
      Calliope reads the initial fill as a share, not times the capacity, as
      here
    dims: [nodes, techs, datesteps]
    cases:
      initial:
        when: position(datesteps) == 0 AND NOT cyclic_storage
        expression: storage_initial
    otherwise: storage_retention ** 24 * shift(storage_inter_cluster, along=datesteps, offset=1, edge='wrap')
  storage_intra:
    description: >-
      `$storage_intra` of `balance_storage_inter` — what the clustered day of
      the day before left at its last step, and nothing on the first day of
      a store that is not cyclic
    dims: [nodes, techs, datesteps]
    cases:
      initial:
        when: position(datesteps) == 0 AND NOT cyclic_storage
        expression: "0"
    otherwise: >-
      shift(at(storage, by=lookup_datestep_last_cluster_timestep, over=timesteps, into=datesteps),
      along=datesteps, offset=1, edge='wrap')

constraints:
  storage_max: null
  set_storage_initial:
    description: >-
      `set_storage_initial` under inter-cluster storage — a cyclic store with
      an initial fill carries it between days at the end, after a day's loss
    dims: [nodes, techs, datesteps]
    where: position(datesteps) == -1 AND storage_inter_cluster AND storage_initial AND cyclic_storage
    expression: storage_inter_cluster * storage_retention ** 24 == storage_initial * storage_cap
  storage_intra_max:
    description: "`storage_intra_max` — a store holds at most its most within its clustered day"
    dims: [nodes, techs, timesteps]
    where: include_storage OR base_tech == 'storage'
    expression: storage <= at(storage_intra_cluster_max, by=timestep_cluster, over=clusters, into=timesteps)
  storage_intra_min:
    description: "`storage_intra_min` — a store holds at least its least within its clustered day"
    dims: [nodes, techs, timesteps]
    where: include_storage OR base_tech == 'storage'
    expression: storage >= at(storage_intra_cluster_min, by=timestep_cluster, over=clusters, into=timesteps)
  storage_inter_max:
    description: "`storage_inter_max` — what a store carries between days plus the most of its day is at most its capacity"
    dims: [nodes, techs, datesteps]
    where: include_storage OR base_tech == 'storage'
    expression: >-
      storage_inter_cluster + at(storage_intra_cluster_max, by=lookup_datestep_cluster, over=clusters, into=datesteps)
      <= storage_cap
  storage_inter_min:
    description: "`storage_inter_min` — what a store carries between days, after a day's loss, plus the least of its day is not below zero"
    dims: [nodes, techs, datesteps]
    where: include_storage OR base_tech == 'storage'
    expression: >-
      storage_inter_cluster * storage_retention ** 24
      + at(storage_intra_cluster_min, by=lookup_datestep_cluster, over=clusters, into=datesteps) >= 0
  balance_storage_inter:
    description: >-
      `balance_storage_inter` — what a store carries into a day is what it
      carried into the day before, after a day's loss, plus what that day's
      cluster left
    dims: [nodes, techs, datesteps]
    where: include_storage OR base_tech == 'storage'
    expression: storage_inter_cluster == storage_inter_previous_step + storage_intra

assumptions:
  cyclic_storage_needs_inter_cluster: null
```

**`storage`**

```math
\mathit{storage}_{n,i,t} \in \mathbb{R} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage_inter_cluster`**

```math
\mathit{storage}^{\mathrm{inter,cluster}}_{n,i,d} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ d \in \mathcal{D} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage_intra_cluster_max`**

```math
\mathit{storage}^{\mathrm{intra,cluster,max}}_{n,i,l} \in \mathbb{R} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ l \in \mathcal{L} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage_intra_cluster_min`**

```math
\mathit{storage}^{\mathrm{intra,cluster,min}}_{n,i,l} \in \mathbb{R} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ l \in \mathcal{L} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage_previous_step`**

```math
\mathit{storage}^{\mathrm{previous,step}}_{n,i,t} = \begin{cases} \mathrm{storage}^{\mathrm{initial}}_{n,i} \cdot \mathit{storage}^{\mathrm{cap}}_{n,i} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{cyclic\_storage}_{n,i} \\ 0 & \text{if } \mathrm{lookup\_cluster\_last\_timestep}(t) \text{ is defined} \wedge \neg \left( \mathrm{pos}(t) = 0 \wedge \neg \mathrm{cyclic\_storage}_{n,i} \right) \\ \mathrm{storage}^{\mathrm{retention}}_{n,i}^{\mathrm{timestep\_resolution}_{t \ominus 1}} \cdot \mathit{storage}_{n,i,t \ominus 1} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T}
```

**`storage_inter_previous_step`**

```math
\mathit{storage}^{\mathrm{inter,previous,step}}_{n,i,d} = \begin{cases} \mathrm{storage}^{\mathrm{initial}}_{n,i} & \text{if } \mathrm{pos}(d) = 0 \wedge \neg \mathrm{cyclic\_storage}_{n,i} \\ \mathrm{storage}^{\mathrm{retention}}_{n,i}^{24} \cdot \mathit{storage}^{\mathrm{inter,cluster}}_{n,i,d \ominus 1} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ d \in \mathcal{D}
```

**`storage_intra`**

```math
\mathit{storage}^{\mathrm{intra}}_{n,i,d} = \begin{cases} 0 & \text{if } \mathrm{pos}(d) = 0 \wedge \neg \mathrm{cyclic\_storage}_{n,i} \\ \mathit{storage}_{n,i,\mathrm{lookup\_datestep\_last\_cluster\_timestep}(d \ominus 1)} & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ d \in \mathcal{D}
```

**`set_storage_initial`**

```math
\mathit{storage}^{\mathrm{inter,cluster}}_{n,i,d} \cdot \mathrm{storage}^{\mathrm{retention}}_{n,i}^{24} = \mathrm{storage}^{\mathrm{initial}}_{n,i} \cdot \mathit{storage}^{\mathrm{cap}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ d \in \mathcal{D} \,:\, \mathrm{pos}(d) = \lvert \mathcal{D} \rvert - 1 \wedge \mathit{storage}^{\mathrm{inter,cluster}}_{n,i,d} \text{ exists} \wedge \mathrm{storage}^{\mathrm{initial}}_{n,i} \text{ is defined} \wedge \mathrm{cyclic\_storage}_{n,i}
```

**`storage_intra_max`**

```math
\mathit{storage}_{n,i,t} \le \mathit{storage}^{\mathrm{intra,cluster,max}}_{n,i,\mathrm{timestep\_cluster}(t)} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage_intra_min`**

```math
\mathit{storage}_{n,i,t} \ge \mathit{storage}^{\mathrm{intra,cluster,min}}_{n,i,\mathrm{timestep\_cluster}(t)} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage_inter_max`**

```math
\mathit{storage}^{\mathrm{inter,cluster}}_{n,i,d} + \mathit{storage}^{\mathrm{intra,cluster,max}}_{n,i,\mathrm{lookup\_datestep\_cluster}(d)} \le \mathit{storage}^{\mathrm{cap}}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ d \in \mathcal{D} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`storage_inter_min`**

```math
\mathit{storage}^{\mathrm{inter,cluster}}_{n,i,d} \cdot \mathrm{storage}^{\mathrm{retention}}_{n,i}^{24} + \mathit{storage}^{\mathrm{intra,cluster,min}}_{n,i,\mathrm{lookup\_datestep\_cluster}(d)} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ d \in \mathcal{D} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

**`balance_storage_inter`**

```math
\mathit{storage}^{\mathrm{inter,cluster}}_{n,i,d} = \mathit{storage}^{\mathrm{inter,previous,step}}_{n,i,d} + \mathit{storage}^{\mathrm{intra}}_{n,i,d} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ d \in \mathcal{D} \,:\, \mathrm{include\_storage}_{n,i} \vee \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'}
```

Removed: `storage_max`, `cyclic_storage_needs_inter_cluster`.
<!-- gallery:end -->
