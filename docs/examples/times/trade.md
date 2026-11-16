<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Trade between regions

TIMES states the efficiency of a trade flow as `IRE_FLO(REG,V,P,COM,R,C,TS)`:
an export from region `REG` and commodity `COM` arrives in region `R` as
commodity `C`. The parameter names the region twice and the commodity twice,
which TIMES writes with a second name for each set, `ALIAS(REG,R)` in
`initsys.mod`.

The spec does the same with an [alias](../../reference/language/dimensions.md#alias):
`from_region` has the labels of `region`, and `from_commodity` those of
`commodity`. The set `top_ire` lists the links that exist, and
`ire_flo`, `trade_cost` and `export` name it in `dims:`, so they are over its
four dimensions and a data row at a link that does not exist is refused. The data of
`ire_flo` has the four columns that the TIMES data already has, and no label
is invented.

`balance` adds the imports of each region and commodity over the far end of
each link. It reads the exports at the near end: it sums them to each
`from_region` and `from_commodity`, and reads those back onto `region` and
`commodity` through the map of each alias.

The vintage, the process and the timeslice of `IRE_FLO` are left out, so the
spec shows only the two ends of each link.

<!-- gallery:begin -->
```yaml
description: >-
  Trade between regions from TIMES: IRE_FLO, the efficiency of a flow from one
  region and commodity to another, over each region and commodity twice.

dimensions:
  region: { description: a region of the model }
  commodity: { description: an energy carrier or a material }
  from_region: { alias: region, description: the region an export leaves }
  from_commodity: { alias: commodity, description: the commodity an export leaves as }

sets:
  top_ire:
    description: the links that exist, from a region and commodity to another (TOP_IRE)
    dims: [from_region, from_commodity, region, commodity]
    missing: absent

parameters:
  ire_flo:
    description: the share of an export that arrives as an import (IRE_FLO)
    dims: [top_ire]
  demand: { dims: [commodity, region], description: what a region needs of a commodity }
  supply_cost: { dims: [commodity, region], description: the cost of a unit produced in a region }
  trade_cost:
    description: the cost of a unit exported along a link
    dims: [top_ire]

variables:
  supply: { dims: [commodity, region], bounds: { lower: 0 }, description: what a region produces of a commodity }
  export:
    description: what leaves along a link (VAR_IRE)
    dims: [top_ire]
    bounds: { lower: 0 }

constraints:
  balance:
    description: production and imports less exports meet the demand of each region and commodity
    dims: [commodity, region]
    expression: >-
      supply
      + sum(ire_flo * export, over=[from_region, from_commodity])
      - sum(sum(sum(export, over=[region, commodity]), over=from_region, by=from_region[region]),
        over=from_commodity, by=from_commodity[commodity])
      >= demand

objective:
  sense: minimize
  expression: sum(supply_cost * supply) + sum(trade_cost * export)
```

Trade between regions from TIMES: IRE\_FLO, the efficiency of a flow from one region and commodity to another, over each region and commodity twice.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{C}`$ | index $`c`$ — `commodity` with $`\mathrm{top\_ire} \subseteq \mathcal{C} \times \mathcal{C} \times \mathcal{R} \times \mathcal{R}`$, `top_ire` is `absent` where the data has no row — an energy carrier or a material |
| $`\mathcal{C}`$ | index $`c'`$ — `from_commodity`, an alias of `commodity` with $`\mathrm{top\_ire} \subseteq \mathcal{C} \times \mathcal{C} \times \mathcal{R} \times \mathcal{R}`$, `top_ire` is `absent` where the data has no row — the commodity an export leaves as |
| $`\mathcal{R}`$ | index $`r'`$ — `from_region`, an alias of `region` with $`\mathrm{top\_ire} \subseteq \mathcal{C} \times \mathcal{C} \times \mathcal{R} \times \mathcal{R}`$, `top_ire` is `absent` where the data has no row — the region an export leaves |
| $`\mathcal{R}`$ | index $`r`$ — `region` with $`\mathrm{top\_ire} \subseteq \mathcal{C} \times \mathcal{C} \times \mathcal{R} \times \mathcal{R}`$, `top_ire` is `absent` where the data has no row — a region of the model |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{demand}`$ | `demand` over $`\mathcal{C} \times \mathcal{R}`$ — what a region needs of a commodity |
| $`\mathrm{ire\_flo}`$ | `ire_flo` over $`\left( c,\ c',\ r',\ r \right) \in \mathrm{top\_ire}`$ — the share of an export that arrives as an import (IRE\_FLO) |
| $`\mathrm{supply}^{\mathrm{cost}}`$ | `supply_cost` over $`\mathcal{C} \times \mathcal{R}`$ — the cost of a unit produced in a region |
| $`\mathrm{trade\_cost}`$ | `trade_cost` over $`\left( c,\ c',\ r',\ r \right) \in \mathrm{top\_ire}`$ — the cost of a unit exported along a link |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{export}`$ | `export` over $`\left( c,\ c',\ r',\ r \right) \in \mathrm{top\_ire}`$ — what leaves along a link (VAR\_IRE) |
| $`\mathit{supply}`$ | `supply` over $`\mathcal{C} \times \mathcal{R}`$ — what a region produces of a commodity |

#### Variable domains

**`export`**

```math
\mathit{export}_{c,c',r',r} \ge 0 \qquad \forall\, \left( c,\ c',\ r',\ r \right) \in \mathrm{top\_ire}
```

**`supply`**

```math
\mathit{supply}_{c,r} \ge 0 \qquad \forall\, c \in \mathcal{C},\ r \in \mathcal{R}
```

#### Objective

```math
\min \sum_{c \in \mathcal{C},\ r \in \mathcal{R}} \mathrm{supply}^{\mathrm{cost}}_{c,r} \cdot \mathit{supply}_{c,r} + \sum_{c \in \mathcal{C},\ c' \in \mathcal{C},\ r' \in \mathcal{R},\ r \in \mathcal{R}} \mathrm{trade\_cost}_{c,c',r',r} \cdot \mathit{export}_{c,c',r',r}
```

#### Subject to

**`balance`**

```math
\mathit{supply}_{c,r} + \sum_{c' \in \mathcal{C},\ r' \in \mathcal{R}} \mathrm{ire\_flo}_{c,c',r',r} \cdot \mathit{export}_{c,c',r',r} - \left( \sum_{c' \in \mathcal{C} \,:\, c' = c} \sum_{r' \in \mathcal{R} \,:\, r' = r} \sum_{c'' \in \mathcal{C},\ r'' \in \mathcal{R}} \mathit{export}_{c'',c',r',r''} \right) \ge \mathrm{demand}_{c,r} \qquad \forall\, c \in \mathcal{C},\ r \in \mathcal{R}
```
<!-- gallery:end -->
