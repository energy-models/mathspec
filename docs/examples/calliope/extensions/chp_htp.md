<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# CHP plants

An extension of [Calliope in fragments](../index.md). Calliope's example `chp_htp.yaml`: the operating region of combined heat and power plants with extraction or backpressure turbines. Calliope rewrites `balance_conversion` for these plants; the new row is here, and [the CHP patch](../variants/chp_htp.md) keeps the base row off them.

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
  turbine_type:
    description: "`turbine_type` — `extraction` or `backpressure`: the kind of turbine a combined heat and power plant has"
    dims: [nodes, techs]
    dtype: str
  power_loss_factor:
    description: "`power_loss_factor` — `cv`, the power an extraction turbine loses per unit of heat. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs]
  power_to_heat_ratio:
    description: "`power_to_heat_ratio` — `cb`, the backpressure ratio. Calliope's default is 1, and data prep fills it"
    dims: [nodes, techs]
  boiler_eff:
    description: "`boiler_eff` — the efficiency of the boiler fuel may be diverted to; given only where set"
    dims: [nodes, techs]

expressions:
  chp_electricity_out:
    description: "`flow_out[carriers=electricity]`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      electricity:
        when: carriers == electricity
        expression: flow_out
    otherwise: 0
  chp_heat_out:
    description: "`flow_out[carriers=heat]`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      heat:
        when: carriers == heat
        expression: flow_out
    otherwise: 0
  chp_electricity_out_eff:
    description: "`flow_out_eff[carriers=electricity]`"
    dims: [nodes, techs, carriers, timesteps]
    cases:
      electricity:
        when: carriers == electricity
        expression: flow_out_eff
    otherwise: 0
  chp_electricity_out_inc_eff:
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
    flow_out_eff: { dims: [nodes, techs, carriers, timesteps] }
  variables:
    flow_out: { dims: [nodes, techs, carriers, timesteps] }
  expressions:
    flow_out_inc_eff: { dims: [nodes, techs, carriers, timesteps] }
    flow_in_inc_eff: { dims: [nodes, techs, carriers, timesteps] }

constraints:
  balance_conversion_backpressure:
    description: >-
      `balance_conversion` for a backpressure plant with no boiler — the
      plant puts out, before losses, as much electricity as it takes in fuel
      after them. The patch keeps the base row off these plants
    dims: [nodes, techs, timesteps]
    where: base_tech == 'conversion' AND NOT include_storage AND turbine_type == backpressure AND NOT boiler_eff
    expression: sum(chp_electricity_out_inc_eff, over=carriers) == sum(flow_in_inc_eff, over=carriers)
  chp_extraction_line:
    description: "`chp_extraction_line` — an extraction plant puts out at most the electricity its fuel gives, less what the heat costs"
    dims: [nodes, techs, timesteps]
    where: turbine_type == extraction
    expression: >-
      sum(chp_electricity_out, over=carriers)
      <= sum(flow_in_inc_eff, over=carriers) * sum(chp_electricity_out_eff, over=carriers)
      - sum(chp_heat_out, over=carriers) * power_loss_factor
  chp_backpressure_line_min:
    description: "`chp_backpressure_line_min` — an extraction plant puts out at least the backpressure ratio of electricity per unit of heat"
    dims: [nodes, techs, timesteps]
    where: turbine_type == extraction
    expression: sum(chp_electricity_out, over=carriers) >= sum(chp_heat_out, over=carriers) * power_to_heat_ratio
  chp_backpressure_line_max:
    description: "`chp_backpressure_line_max` — a backpressure plant with a boiler puts out at most the backpressure ratio of electricity per unit of heat"
    dims: [nodes, techs, timesteps]
    where: turbine_type == backpressure AND boiler_eff
    expression: sum(chp_electricity_out, over=carriers) <= sum(chp_heat_out, over=carriers) * power_to_heat_ratio
  chp_divert_fuel_to_boiler:
    description: "`chp_divert_fuel_to_boiler` — a backpressure plant with a boiler puts out at most the heat its fuel gives through turbine and boiler"
    dims: [nodes, techs, timesteps]
    where: turbine_type == backpressure AND boiler_eff
    expression: >-
      sum(chp_heat_out, over=carriers)
      <= sum(flow_in_inc_eff, over=carriers) * boiler_eff
      - sum(chp_electricity_out, over=carriers)
      * (boiler_eff / sum(chp_electricity_out_eff, over=carriers) - 1 / power_to_heat_ratio)
  chp_backpressure_line_equals:
    description: "`chp_backpressure_line_equals` — a backpressure plant with no boiler puts out the backpressure ratio of electricity per unit of heat"
    dims: [nodes, techs, timesteps]
    where: turbine_type == backpressure AND NOT boiler_eff
    expression: sum(chp_electricity_out, over=carriers) == sum(chp_heat_out, over=carriers) * power_to_heat_ratio

assumptions:
  turbine_type_one_of:
    description: Calliope's `one_of` on `turbine_type`
    holds: turbine_type == extraction OR turbine_type == backpressure
    where: turbine_type
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
| $`\mathrm{turbine\_type}`$ | `turbine_type` over $`\mathcal{N} \times \mathcal{I}`$ — `turbine_type` — `extraction` or `backpressure`: the kind of turbine a combined heat and power plant has |
| $`\mathrm{power\_loss\_factor}`$ | `power_loss_factor` over $`\mathcal{N} \times \mathcal{I}`$ — `power_loss_factor` — `cv`, the power an extraction turbine loses per unit of heat. Calliope's default is 1, and data prep fills it |
| $`\mathrm{power\_to\_heat\_ratio}`$ | `power_to_heat_ratio` over $`\mathcal{N} \times \mathcal{I}`$ — `power_to_heat_ratio` — `cb`, the backpressure ratio. Calliope's default is 1, and data prep fills it |
| $`\mathrm{boiler\_eff}`$ | `boiler_eff` over $`\mathcal{N} \times \mathcal{I}`$ — `boiler_eff` — the efficiency of the boiler fuel may be diverted to; given only where set |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{base\_tech}`$ | `base_tech` over $`\mathcal{I}`$, data another file declares |
| $`\mathrm{include\_storage}`$ | `include_storage` over $`\mathcal{N} \times \mathcal{I}`$, data another file declares |
| $`\mathrm{flow\_out\_eff}`$ | `flow_out_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, data another file declares |
| $`\mathit{flow\_out}`$ | `flow_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ |
| $`\mathit{flow\_out\_inc\_eff}`$ | `flow_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{flow\_in\_inc\_eff}`$ | `flow_in_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$, an expression another file defines |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{chp\_electricity\_out}`$ | `chp_electricity_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out[carriers=electricity]` |
| $`\mathit{chp\_heat\_out}`$ | `chp_heat_out` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out[carriers=heat]` |
| $`\mathrm{chp\_electricity\_out\_eff}`$ | `chp_electricity_out_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_eff[carriers=electricity]` |
| $`\mathit{chp\_electricity\_out\_inc\_eff}`$ | `chp_electricity_out_inc_eff` over $`\mathcal{N} \times \mathcal{I} \times \mathcal{C} \times \mathcal{T}`$ — `flow_out_inc_eff[carriers=electricity]` |

#### Subject to

**`balance_conversion_backpressure`**

```math
\sum_{c \in \mathcal{C}} \mathit{chp\_electricity\_out\_inc\_eff}_{n,i,c,t} = \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{conversion}\text{'} \wedge \neg \mathrm{include\_storage}_{n,i} \wedge \mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{backpressure}\text{'} \wedge \neg \left( \mathrm{boiler\_eff}_{n,i} \text{ is defined} \right)
```

**`chp_extraction_line`**

```math
\sum_{c \in \mathcal{C}} \mathit{chp\_electricity\_out}_{n,i,c,t} \le \left( \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \right) \cdot \left( \sum_{c \in \mathcal{C}} \mathrm{chp\_electricity\_out\_eff}_{n,i,c,t} \right) - \left( \sum_{c \in \mathcal{C}} \mathit{chp\_heat\_out}_{n,i,c,t} \right) \cdot \mathrm{power\_loss\_factor}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{extraction}\text{'}
```

**`chp_backpressure_line_min`**

```math
\sum_{c \in \mathcal{C}} \mathit{chp\_electricity\_out}_{n,i,c,t} \ge \left( \sum_{c \in \mathcal{C}} \mathit{chp\_heat\_out}_{n,i,c,t} \right) \cdot \mathrm{power\_to\_heat\_ratio}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{extraction}\text{'}
```

**`chp_backpressure_line_max`**

```math
\sum_{c \in \mathcal{C}} \mathit{chp\_electricity\_out}_{n,i,c,t} \le \left( \sum_{c \in \mathcal{C}} \mathit{chp\_heat\_out}_{n,i,c,t} \right) \cdot \mathrm{power\_to\_heat\_ratio}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{backpressure}\text{'} \wedge \mathrm{boiler\_eff}_{n,i} \text{ is defined}
```

**`chp_divert_fuel_to_boiler`**

```math
\sum_{c \in \mathcal{C}} \mathit{chp\_heat\_out}_{n,i,c,t} \le \left( \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \right) \cdot \mathrm{boiler\_eff}_{n,i} - \left( \sum_{c \in \mathcal{C}} \mathit{chp\_electricity\_out}_{n,i,c,t} \right) \cdot \left( \frac{\mathrm{boiler\_eff}_{n,i}}{\sum_{c \in \mathcal{C}} \mathrm{chp\_electricity\_out\_eff}_{n,i,c,t}} - \frac{1}{\mathrm{power\_to\_heat\_ratio}_{n,i}} \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{backpressure}\text{'} \wedge \mathrm{boiler\_eff}_{n,i} \text{ is defined}
```

**`chp_backpressure_line_equals`**

```math
\sum_{c \in \mathcal{C}} \mathit{chp\_electricity\_out}_{n,i,c,t} = \left( \sum_{c \in \mathcal{C}} \mathit{chp\_heat\_out}_{n,i,c,t} \right) \cdot \mathrm{power\_to\_heat\_ratio}_{n,i} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{backpressure}\text{'} \wedge \neg \left( \mathrm{boiler\_eff}_{n,i} \text{ is defined} \right)
```

#### Definitions

**`chp_electricity_out`**

```math
\mathit{chp\_electricity\_out}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{electricity}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`chp_heat_out`**

```math
\mathit{chp\_heat\_out}_{n,i,c,t} = \begin{cases} \mathit{flow\_out}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{heat}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`chp_electricity_out_eff`**

```math
\mathrm{chp\_electricity\_out\_eff}_{n,i,c,t} = \begin{cases} \mathrm{flow\_out\_eff}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{electricity}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`chp_electricity_out_inc_eff`**

```math
\mathit{chp\_electricity\_out\_inc\_eff}_{n,i,c,t} = \begin{cases} \mathit{flow\_out\_inc\_eff}_{n,i,c,t} & \text{if } c = \text{'}\mathrm{electricity}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

#### Assumptions

**`turbine_type_one_of`**

```math
\mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{extraction}\text{'} \vee \mathrm{turbine\_type}_{n,i} = \text{'}\mathrm{backpressure}\text{'} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I} \,:\, \mathrm{turbine\_type}_{n,i} \text{ is defined}
```
<!-- gallery:end -->
