<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Urban-scale CHP

An extension of [Calliope in fragments](../index.md). The `additional_math.yaml` of Calliope's urban-scale example model: the technology `chp` puts out heat in a fixed ratio to its electricity. The new rows are here, and [its patch](../variants/urban_scale_chp.md) keeps the base `balance_conversion` off `chp`.

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
  heat_to_power_ratio:
    description: "`heat_to_power_ratio` — the heat a combined heat and power plant puts out per unit of electricity. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs]

expressions:
  urban_electricity_out:
    description: "`flow_out[carriers=electricity]`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      electricity:
        when: carriers == electricity
        expression: flow_out
    otherwise: 0
  urban_heat_out:
    description: "`flow_out[carriers=heat]`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      heat:
        when: carriers == heat
        expression: flow_out
    otherwise: 0
  urban_electricity_out_inc_eff:
    description: "`flow_out_inc_eff[carriers=electricity]`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      electricity:
        when: carriers == electricity
        expression: flow_out_inc_eff
    otherwise: 0

given:
  parameters:
    base_tech: { dims: [techs], dtype: str }
    include_storage: { dims: [nodes, techs], dtype: bool }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
  expressions:
    flow_out_inc_eff: { dims: [nodes, techs, carriers, timesteps] }
    flow_in_inc_eff: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  link_chp_outputs:
    description: "`link_chp_outputs` — the technology `chp` puts out heat in a fixed ratio to its electricity"
    dims: [nodes, techs, timesteps]
    where: techs == chp
    expression: sum(urban_electricity_out, over=carriers) * heat_to_power_ratio == sum(urban_heat_out, over=carriers)
  balance_conversion_chp:
    description: >-
      `balance_conversion` for the technology `chp` — it puts out, before
      losses, as much electricity as it takes in fuel after them. The patch
      keeps the base row off it
    dims: [nodes, techs, timesteps]
    where: base_tech == 'conversion' AND NOT include_storage AND techs == chp
    expression: sum(urban_electricity_out_inc_eff, over=carriers) == sum(flow_in_inc_eff, over=carriers)
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
| $`\mathrm{heat\_to\_power\_ratio}`$ | `heat_to_power_ratio` over $`\mathcal{N} \times \mathcal{I}`$ — `heat_to_power_ratio` — the heat a combined heat and power plant puts out per unit of electricity. Calliope's default is 1, and data prep fills it |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{include\_storage}`$ | `include_storage` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{flow\_in\_inc\_eff}`$ | `flow_in_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{urban\_electricity\_out}`$ | `urban_electricity_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out[carriers=electricity]` |
| $`\mathit{urban\_heat\_out}`$ | `urban_heat_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out[carriers=heat]` |
| $`\mathit{urban\_electricity\_out\_inc\_eff}`$ | `urban_electricity_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_inc_eff[carriers=electricity]` |

#### Subject to

**`link_chp_outputs`**

```math
\left( \sum_{c \in \mathcal{C}} \mathit{urban\_electricity\_out}_{n,i,c,t} \right) \cdot \mathrm{heat\_to\_power\_ratio}_{n,i} = \sum_{c \in \mathcal{C}} \mathit{urban\_heat\_out}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, i = \text{'}\mathrm{chp}\text{'}
```

**`balance_conversion_chp`**

```math
\sum_{c \in \mathcal{C}} \mathit{urban\_electricity\_out\_inc\_eff}_{n,i,c,t} = \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{conversion}\text{'} \wedge \neg \mathrm{include\_storage}_{n,i} \wedge i = \text{'}\mathrm{chp}\text{'}
```

#### Definitions

**`urban_electricity_out`**

```math
\mathit{urban\_electricity\_out}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{electricity}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`urban_heat_out`**

```math
\mathit{urban\_heat\_out}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{heat}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`urban_electricity_out_inc_eff`**

```math
\mathit{urban\_electricity\_out\_inc\_eff}_{n,i,c,t} = \begin{cases} \mathit{flow\_out\_inc\_eff}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{electricity}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```
<!-- gallery:end -->
