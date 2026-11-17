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

!!! warning "A workaround"

    mathspec refuses an entry over one dimension twice. This spec declares a
    dimension `trade_link`, whose labels the data invents, one per link, and
    the relation `link_ends` gives each link its two regions and two
    commodities. Nothing refuses two labels for the same link, and a row of
    `ire_flo` for a process that does not carry the link is dropped, not
    refused. Issue [#969](https://github.com/energy-models/mathspec/issues/969)
    (gap 1) and [#1019](https://github.com/energy-models/mathspec/issues/1019)
    track the designs that would state `IRE_FLO` over the regions and
    commodities themselves.

The relation `top_ire` lists the processes that carry each link, as TIMES'
`TOP_IRE` does. The vintage and the timeslice of `IRE_FLO` are left out.

<!-- gallery:begin -->
```yaml
description: >-
  Trade between regions from TIMES: IRE_FLO, the efficiency of a flow from one
  region and commodity to another through a process, with each link a label of
  its own.

dimensions:
  region: { description: a region of the model }
  commodity: { description: an energy carrier or a material }
  process: { description: a technology that carries trade }
  trade_link: { description: "one link from a region and commodity to another, a label the data invents" }

relations:
  link_ends:
    description: the region and commodity at each end of a link
    key: trade_link
    values: { from_commodity: commodity, from_region: region, to_commodity: commodity, to_region: region }
  top_ire:
    description: the processes that carry each link (TOP_IRE)
    key: [trade_link, process]
    missing: absent

parameters:
  ire_flo: { dims: [trade_link, process], where: top_ire, description: the share of an export that arrives as an import (IRE_FLO) }
  demand: { dims: [commodity, region], description: what a region needs of a commodity }
  supply_cost: { dims: [commodity, region], description: the cost of a unit produced in a region }
  trade_cost: { dims: [trade_link, process], where: top_ire, description: the cost of a unit exported along a link }

variables:
  supply: { dims: [commodity, region], bounds: { lower: 0 }, description: what a region produces of a commodity }
  export:
    description: what leaves along a link through a process (VAR_IRE)
    dims: [trade_link, process]
    where: top_ire
    bounds: { lower: 0 }

constraints:
  balance:
    description: production and imports less exports meet the demand of each region and commodity
    dims: [commodity, region]
    expression: >-
      supply
      + sum(ire_flo * export, over=[trade_link, process], by=link_ends[to_commodity, to_region])
      - sum(export, over=[trade_link, process], by=link_ends[from_commodity, from_region])
      >= demand

objective:
  sense: minimize
  expression: sum(supply_cost * supply) + sum(trade_cost * export)
```

Trade between regions from TIMES: IRE\_FLO, the efficiency of a flow from one region and commodity to another through a process, with each link a label of its own.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{C}`$ | index $`c`$ — `commodity` with $`\mathrm{link\_ends}: \mathcal{L} \to \mathcal{C} \times \mathcal{R} \times \mathcal{C} \times \mathcal{R}`$ — an energy carrier or a material |
| $`\mathcal{P}`$ | index $`p`$ — `process` with $`\mathrm{top\_ire} \subseteq \mathcal{P} \times \mathcal{L}`$, `top_ire` is `absent` where the data has no row — a technology that carries trade |
| $`\mathcal{R}`$ | index $`r`$ — `region` with $`\mathrm{link\_ends}: \mathcal{L} \to \mathcal{C} \times \mathcal{R} \times \mathcal{C} \times \mathcal{R}`$ — a region of the model |
| $`\mathcal{L}`$ | index $`l`$ — `trade_link` with $`\mathrm{link\_ends}: \mathcal{L} \to \mathcal{C} \times \mathcal{R} \times \mathcal{C} \times \mathcal{R},\ \mathrm{top\_ire} \subseteq \mathcal{P} \times \mathcal{L}`$, `top_ire` is `absent` where the data has no row — one link from a region and commodity to another, a label the data invents |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{demand}`$ | `demand` over $`\mathcal{C} \times \mathcal{R}`$ — what a region needs of a commodity |
| $`\mathrm{ire\_flo}`$ | `ire_flo` over $`\mathcal{P} \times \mathcal{L}`$, only where $`\left( p,\ l \right) \in \mathrm{top\_ire}`$ — the share of an export that arrives as an import (IRE\_FLO) |
| $`\mathrm{supply}^{\mathrm{cost}}`$ | `supply_cost` over $`\mathcal{C} \times \mathcal{R}`$ — the cost of a unit produced in a region |
| $`\mathrm{trade\_cost}`$ | `trade_cost` over $`\mathcal{P} \times \mathcal{L}`$, only where $`\left( p,\ l \right) \in \mathrm{top\_ire}`$ — the cost of a unit exported along a link |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{export}`$ | `export` over $`\mathcal{P} \times \mathcal{L}`$ — what leaves along a link through a process (VAR\_IRE) |
| $`\mathit{supply}`$ | `supply` over $`\mathcal{C} \times \mathcal{R}`$ — what a region produces of a commodity |

#### Variable domains

**`export`**

```math
\mathit{export}_{p,l} \ge 0 \qquad \forall\, p \in \mathcal{P},\ l \in \mathcal{L} \,:\, \left( p,\ l \right) \in \mathrm{top\_ire}
```

**`supply`**

```math
\mathit{supply}_{c,r} \ge 0 \qquad \forall\, c \in \mathcal{C},\ r \in \mathcal{R}
```

#### Objective

```math
\min \sum_{c \in \mathcal{C},\ r \in \mathcal{R}} \mathrm{supply}^{\mathrm{cost}}_{c,r} \cdot \mathit{supply}_{c,r} + \sum_{p \in \mathcal{P},\ l \in \mathcal{L}} \mathrm{trade\_cost}_{p,l} \cdot \mathit{export}_{p,l}
```

#### Subject to

**`balance`**

```math
\mathit{supply}_{c,r} + \sum_{p \in \mathcal{P}} \sum_{l \in \mathcal{L} \,:\, \mathrm{link\_ends.to\_commodity}(l) = c \wedge \mathrm{link\_ends.to\_region}(l) = r} \mathrm{ire\_flo}_{p,l} \cdot \mathit{export}_{p,l} - \left( \sum_{p \in \mathcal{P}} \sum_{l \in \mathcal{L} \,:\, \mathrm{link\_ends.from\_commodity}(l) = c \wedge \mathrm{link\_ends.from\_region}(l) = r} \mathit{export}_{p,l} \right) \ge \mathrm{demand}_{c,r} \qquad \forall\, c \in \mathcal{C},\ r \in \mathcal{R}
```
<!-- gallery:end -->
