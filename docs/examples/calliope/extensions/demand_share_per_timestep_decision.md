<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Demand share as a decision

An extension of [Calliope in fragments](../index.md). Calliope's example `demand_share_per_timestep_decision.yaml`: a technology meets a share of a demand that the model decides, the same in every time step.

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
  decide_demand_share:
    description: >-
      `decide_demand_share` — the demand technology whose inflow a technology
      meets a share of. Calliope reads it with `select_from_lookup_arrays`,
      which is a read through the relation
    key: techs
    values: { demand: techs }
  demand_share_carrier:
    description: >-
      `demand_share_carrier` — the carrier a share of demand is counted in.
      Calliope slices `flow_out` by it, which is a test of the pair
    key: [techs, carriers]

parameters:
  demand_share_relaxation:
    description: "`demand_share_relaxation` — how far the share may stray from the one decided, as a fraction"
    dims: [nodes, techs]
  demand_share_limit:
    description: "`demand_share_limit` — the share of demand the technologies meet together; given only where set"
    dims: [nodes]

variables:
  demand_share_per_timestep_decision:
    description: "`demand_share_per_timestep_decision` — the share of demand a technology meets, the same in every time step"
    dims: [nodes, techs]
    where: decide_demand_share
    bounds: { lower: 0 }
    absence: zero

expressions:
  demand_share_flow_out:
    description: "`flow_out[carriers=$carrier]` — a technology's outflow of the carrier its share is counted in"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      share_carrier:
        when: demand_share_carrier
        expression: flow_out
    otherwise: 0
  demand_share_sink:
    description: "`select_from_lookup_arrays(sink_use_equals, techs=decide_demand_share)` — the demand a technology meets a share of"
    expression: at(sink_use_equals, by=decide_demand_share, over=demand, into=techs)

given:
  parameters:
    sink_use_equals: { dims: [nodes, techs, timesteps] }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  demand_share_per_timestep_decision_main_min:
    description: "`demand_share_per_timestep_decision_main_min` — a technology puts out at least its decided share of demand, less the relaxation"
    dims: [nodes, techs, timesteps]
    where: demand_share_per_timestep_decision
    expression: >-
      sum(demand_share_flow_out, over=carriers)
      >= (1 - demand_share_relaxation) * demand_share_sink * demand_share_per_timestep_decision
  demand_share_per_timestep_decision_main_max:
    description: "`demand_share_per_timestep_decision_main_max` — a technology puts out at most its decided share of demand, plus the relaxation"
    dims: [nodes, techs, timesteps]
    where: demand_share_per_timestep_decision
    expression: >-
      sum(demand_share_flow_out, over=carriers)
      <= (1 + demand_share_relaxation) * demand_share_sink * demand_share_per_timestep_decision
  demand_share_per_timestep_decision_sum:
    description: >-
      `demand_share_per_timestep_decision_sum` — the decided shares at a node
      add up to the limit. Calliope's `where: demand_share_per_timestep_decision`
      over a node reads as any technology there deciding a share. Calliope
      builds the row in every time step, and it is the same in each; a row
      repeated along a dimension it does not read is refused, so it is one
      row per node
    dims: [nodes]
    where: count(demand_share_per_timestep_decision, over=techs) >= 1 AND demand_share_limit
    expression: sum(demand_share_per_timestep_decision, over=techs) == demand_share_limit

assumptions:
  demand_share_is_fraction:
    description: Calliope's `demand_share_is_fraction` — the demand share limit is a fraction
    holds: demand_share_limit >= 0 AND demand_share_limit <= 1
    where: demand_share_limit
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{I}`$ | index $`i`$ — `techs` with $`\mathrm{decide\_demand\_share}: \mathcal{I} \to \mathcal{I},\ \mathrm{demand\_share\_carrier} \subseteq \mathcal{I} \times \mathcal{C}`$ — Calliope's `techs` — technologies |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` with $`\mathrm{demand\_share\_carrier} \subseteq \mathcal{I} \times \mathcal{C}`$ — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{demand\_share\_relaxation}`$ | `demand_share_relaxation` over $`\mathcal{N} \times \mathcal{I}`$ — `demand_share_relaxation` — how far the share may stray from the one decided, as a fraction |
| $`\mathrm{demand\_share\_limit}`$ | `demand_share_limit` over $`\mathcal{N}`$ — `demand_share_limit` — the share of demand the technologies meet together; given only where set |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{demand\_share\_per\_timestep\_decision}`$ | `demand_share_per_timestep_decision` over $`\mathcal{N} \times \mathcal{I}`$ — `demand_share_per_timestep_decision` — the share of demand a technology meets, the same in every time step |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{sink\_use\_equals}`$ | `sink_use_equals` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{demand\_share\_flow\_out}`$ | `demand_share_flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out[carriers=$carrier]` — a technology's outflow of the carrier its share is counted in |
| $`\mathrm{demand\_share\_sink}`$ | `demand_share_sink` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{T}`$ — `select_from_lookup_arrays(sink_use_equals, techs=decide_demand_share)` — the demand a technology meets a share of |

Upright is what the data supplies — a parameter such as $`\mathrm{demand\_share\_relaxation}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{demand\_share\_per\_timestep\_decision}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`demand_share_per_timestep_decision_main_min`**

```math
\sum_{c \in \mathcal{C}} \mathit{demand\_share\_flow\_out}_{n,i,c,t} \ge \left( 1 - \mathrm{demand\_share\_relaxation}_{n,i} \right) \cdot \mathrm{demand\_share\_sink}_{n,i,t} \cdot \mathit{demand\_share\_per\_timestep\_decision}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{demand\_share\_per\_timestep\_decision}_{n,i} \text{ exists}
```

**`demand_share_per_timestep_decision_main_max`**

```math
\sum_{c \in \mathcal{C}} \mathit{demand\_share\_flow\_out}_{n,i,c,t} \le \left( 1 + \mathrm{demand\_share\_relaxation}_{n,i} \right) \cdot \mathrm{demand\_share\_sink}_{n,i,t} \cdot \mathit{demand\_share\_per\_timestep\_decision}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathit{demand\_share\_per\_timestep\_decision}_{n,i} \text{ exists}
```

**`demand_share_per_timestep_decision_sum`**

```math
\sum_{i \in \mathcal{I}} \mathit{demand\_share\_per\_timestep\_decision}_{n,i} = \mathrm{demand\_share\_limit}_{n} \qquad \forall\, n \in \mathcal{N} \,:\, \lvert \{ i \in \mathcal{I} \,:\, \mathit{demand\_share\_per\_timestep\_decision}_{n,i} \text{ exists} \} \rvert \ge 1 \wedge \mathrm{demand\_share\_limit}_{n} \text{ is defined}
```

#### Definitions

**`demand_share_flow_out`**

```math
\mathit{demand\_share\_flow\_out}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } \left( i,\ c \right) \in \mathrm{demand\_share\_carrier} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`demand_share_sink`**

```math
\mathrm{demand\_share\_sink}_{n,i,t} = \mathrm{sink\_use\_equals}_{n,\mathrm{decide\_demand\_share}(i),t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T}
```

#### Variable domains

**`demand_share_per_timestep_decision`**

```math
\mathit{demand\_share\_per\_timestep\_decision}_{n,i} \ge 0 \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{decide\_demand\_share}(i) \text{ is defined}
```

#### Assumptions

**`demand_share_is_fraction`**

```math
\mathrm{demand\_share\_limit}_{n} \ge 0 \wedge \mathrm{demand\_share\_limit}_{n} \le 1 \qquad \forall\, n \in \mathcal{N} \,:\, \mathrm{demand\_share\_limit}_{n} \text{ is defined}
```
<!-- gallery:end -->
