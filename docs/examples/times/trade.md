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
`commodity`. The dimension `top_ire` lists the links that exist, each a tuple of its four
members, and `ire_flo`, `trade_cost` and `export` are over it, so a data row at
a link that does not exist is refused. The data of
`ire_flo` has the four columns that the TIMES data already has, and no label
is invented.

`balance` adds the imports of each region and commodity through the members
`region` and `commodity` of each link. It sums the exports to each
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
  top_ire:
    description: the links that exist, from a region and commodity to another (TOP_IRE)
    over: [from_region, from_commodity, region, commodity]

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
      + sum(ire_flo * export, over=top_ire, by=top_ire[commodity, region])
      - sum(sum(sum(export, over=top_ire, by=top_ire[from_commodity, from_region]),
        over=from_region, by=from_region[region]), over=from_commodity, by=from_commodity[commodity])
      >= demand

objective:
  sense: minimize
  expression: sum(supply_cost * supply) + sum(trade_cost * export)
```

Trade between regions from TIMES: IRE\_FLO, the efficiency of a flow from one region and commodity to another, over each region and commodity twice.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{C}`$ | index $`c`$ — `commodity` — an energy carrier or a material |
| $`\mathcal{C}`$ | index $`c'`$ — `from_commodity`, an alias of `commodity` — the commodity an export leaves as |
| $`\mathcal{R}`$ | index $`r'`$ — `from_region`, an alias of `region` — the region an export leaves |
| $`\mathcal{R}`$ | index $`r`$ — `region` — a region of the model |
| $`\mathcal{L}`$ | index $`l`$ — `top_ire`, $`\mathcal{L} \subseteq \mathcal{C} \times \mathcal{C} \times \mathcal{R} \times \mathcal{R}`$ — the links that exist, from a region and commodity to another (TOP\_IRE) |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{demand}`$ | `demand` over $`\mathcal{C} \times \mathcal{R}`$ — what a region needs of a commodity |
| $`\mathrm{ire\_flo}`$ | `ire_flo` over $`\mathcal{L}`$ — the share of an export that arrives as an import (IRE\_FLO) |
| $`\mathrm{supply}^{\mathrm{cost}}`$ | `supply_cost` over $`\mathcal{C} \times \mathcal{R}`$ — the cost of a unit produced in a region |
| $`\mathrm{trade\_cost}`$ | `trade_cost` over $`\mathcal{L}`$ — the cost of a unit exported along a link |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{export}`$ | `export` over $`\mathcal{L}`$ — what leaves along a link (VAR\_IRE) |
| $`\mathit{supply}`$ | `supply` over $`\mathcal{C} \times \mathcal{R}`$ — what a region produces of a commodity |

#### Variable domains

**`export`**

```math
\mathit{export}_{l} \ge 0 \qquad \forall\, l \in \mathcal{L}
```

**`supply`**

```math
\mathit{supply}_{c,r} \ge 0 \qquad \forall\, c \in \mathcal{C},\ r \in \mathcal{R}
```

#### Objective

```math
\min \sum_{c \in \mathcal{C},\ r \in \mathcal{R}} \mathrm{supply}^{\mathrm{cost}}_{c,r} \cdot \mathit{supply}_{c,r} + \sum_{l \in \mathcal{L}} \mathrm{trade\_cost}_{l} \cdot \mathit{export}_{l}
```

#### Subject to

**`balance`**

```math
\mathit{supply}_{c,r} + \sum_{l \in \mathcal{L} \,:\, \mathrm{commodity}(l) = c \wedge \mathrm{region}(l) = r} \mathrm{ire\_flo}_{l} \cdot \mathit{export}_{l} - \left( \sum_{c' \in \mathcal{C} \,:\, c' = c} \sum_{r' \in \mathcal{R} \,:\, r' = r} \sum_{l \in \mathcal{L} \,:\, \mathrm{from\_commodity}(l) = c' \wedge \mathrm{from\_region}(l) = r'} \mathit{export}_{l} \right) \ge \mathrm{demand}_{c,r} \qquad \forall\, c \in \mathcal{C},\ r \in \mathcal{R}
```
<!-- gallery:end -->
