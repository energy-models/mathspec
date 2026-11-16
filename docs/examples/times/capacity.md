<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Capacity transfer and capacity–activity

This spec ports two TIMES equations for a process without vintages and
without storage, with the upper bound only.

- `eq_cpt` (TIMES `EQ_CPT`, `eqcpt.mod:18-27`) sets the installed capacity
  `cap` of each period from the new capacity of each vintage. `coef_cpt` is
  the share of a vintage that still exists in that period.
- `eq_capact_up` (TIMES `EQ_CAPACT`, `eqcapact.mod:23-50`, the form without
  vintages) limits the activity in each timeslice, summed over the
  timeslices at or below it, to the available capacity.

The GAMS conditions map to the spec as follows:

- `RTP_VINTYR` and `PRC_TS` are [relations](../../reference/language/relations.md),
  and `act` lists both under `in:`, so it exists only at the coordinates that
  both list.
- `TS_MAP(R,S,TS)` is the relation `ts_map`, which names `timeslice` twice
  under two column names.
- `COEF_AF(…,'UP')` is the `where:` of `eq_capact_up`.
- `NCAP_PASTI$PASTYEAR(V)` reads `0` where the data has no row.

The `LO` and `FX` senses of `EQ_CAPACT` are two more constraints of the same
shape. The objective stands in for `EQ_OBJ`, whose coefficients come from the
discounting loops in `eqobjinv.mod`.

<!-- gallery:begin -->
```yaml
description: >-
  Capacity transfer and capacity–activity from TIMES: EQ_CPT and the upper
  form of EQ_CAPACT, for a process without vintages and without storage.

dimensions:
  region: { description: a region of the model }
  period: { dtype: int, ordered: true, description: a milestone year }
  vintage: { dtype: int, description: the period a capacity was built in }
  process: { description: a technology }
  timeslice: { description: "a slice of the year, at any level of the timeslice tree" }

relations:
  rtp_vintyr:
    description: the vintages of a process that exist in a period (RTP_VINTYR)
    dims: [region, vintage, period, process]
    missing: absent
  prc_ts:
    description: the timeslices a process operates at (PRC_TS)
    dims: [region, process, timeslice]
    missing: absent
  ts_map:
    description: each timeslice and the timeslices at or below it (TS_MAP)
    dims: { region: region, s: timeslice, ts: timeslice }
    missing: absent

parameters:
  coef_cpt: { dims: [region, vintage, period, process], description: the share of a vintage that still exists in a period }
  ncap_pasti: { dims: [region, vintage, process], missing: 0, description: capacity built before the first period }
  coef_af_up: { dims: [region, period, process, timeslice], missing: absent, description: the upper availability factor }
  prc_capact: { dims: [region, process], description: the activity a unit of capacity can produce in a year }
  g_yrfr: { dims: [region, timeslice], description: the share of the year a timeslice covers }
  obj_icost: { dims: [region, vintage, process], description: "the cost of a unit of new capacity, discounted" }
  obj_acost: { dims: [region, period, process], description: "the cost of a unit of activity, discounted" }

variables:
  ncap: { dims: [region, vintage, process], bounds: { lower: 0 }, description: new capacity (VAR_NCAP) }
  cap: { dims: [region, period, process], bounds: { lower: 0 }, description: installed capacity (VAR_CAP) }
  act:
    description: activity of a vintage of a process in a timeslice (VAR_ACT)
    dims: [region, vintage, period, process, timeslice]
    in: [prc_ts, rtp_vintyr]
    bounds: { lower: 0 }

constraints:
  eq_cpt:
    description: the installed capacity of each period, from the new capacity of each vintage (EQ_CPT)
    dims: [region, period, process]
    expression: cap == sum(coef_cpt * (ncap + ncap_pasti), over=vintage)
  eq_capact_up:
    description: activity summed over the timeslices at or below each one, up to the available capacity (EQ_CAPACT, UP)
    dims: [region, period, process, timeslice]
    where: coef_af_up
    expression: >-
      sum(sum(act, over=vintage), over=ts, by=ts_map[s])
      <= coef_af_up * prc_capact * g_yrfr * cap

objective:
  sense: minimize
  expression: >-
    sum(obj_icost * ncap)
    + sum(obj_acost * sum(act, over=[vintage, timeslice]))
```

Capacity transfer and capacity–activity from TIMES: EQ\_CPT and the upper form of EQ\_CAPACT, for a process without vintages and without storage.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `period` with $`\mathrm{rtp\_vintyr} \subseteq \mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{V}`$, `rtp_vintyr` is `absent` where the data has no row — a milestone year |
| $`\mathcal{P}`$ | index $`p`$ — `process` with $`\mathrm{prc\_ts} \subseteq \mathcal{P} \times \mathcal{R} \times \mathcal{S},\ \mathrm{rtp\_vintyr} \subseteq \mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{V}`$, `prc_ts` is `absent` where the data has no row, `rtp_vintyr` is `absent` where the data has no row — a technology |
| $`\mathcal{R}`$ | index $`r`$ — `region` with $`\mathrm{prc\_ts} \subseteq \mathcal{P} \times \mathcal{R} \times \mathcal{S},\ \mathrm{rtp\_vintyr} \subseteq \mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{V},\ \mathrm{ts\_map} \subseteq \mathcal{R} \times \mathcal{S} \times \mathcal{S}`$, `prc_ts` is `absent` where the data has no row, `rtp_vintyr` is `absent` where the data has no row, `ts_map` is `absent` where the data has no row — a region of the model |
| $`\mathcal{S}`$ | index $`s`$ — `timeslice` with $`\mathrm{prc\_ts} \subseteq \mathcal{P} \times \mathcal{R} \times \mathcal{S},\ \mathrm{ts\_map} \subseteq \mathcal{R} \times \mathcal{S} \times \mathcal{S}`$, `prc_ts` is `absent` where the data has no row, `ts_map` is `absent` where the data has no row — a slice of the year, at any level of the timeslice tree |
| $`\mathcal{V}`$ | index $`v`$ — `vintage` with $`\mathrm{rtp\_vintyr} \subseteq \mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{V}`$, `rtp_vintyr` is `absent` where the data has no row — the period a capacity was built in |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{coef\_af\_up}`$ | `coef_af_up` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{S}`$, `absent` where the data has no row — the upper availability factor |
| $`\mathrm{coef\_cpt}`$ | `coef_cpt` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{V}`$ — the share of a vintage that still exists in a period |
| $`\mathrm{g}^{\mathrm{yrfr}}`$ | `g_yrfr` over $`\mathcal{R} \times \mathcal{S}`$ — the share of the year a timeslice covers |
| $`\mathrm{ncap}^{\mathrm{pasti}}`$ | `ncap_pasti` over $`\mathcal{P} \times \mathcal{R} \times \mathcal{V}`$, $`0`$ where the data has no row — capacity built before the first period |
| $`\mathrm{obj\_acost}`$ | `obj_acost` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R}`$ — the cost of a unit of activity, discounted |
| $`\mathrm{obj\_icost}`$ | `obj_icost` over $`\mathcal{P} \times \mathcal{R} \times \mathcal{V}`$ — the cost of a unit of new capacity, discounted |
| $`\mathrm{prc\_capact}`$ | `prc_capact` over $`\mathcal{P} \times \mathcal{R}`$ — the activity a unit of capacity can produce in a year |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{act}`$ | `act` over $`\left( p,\ r,\ s \right) \in \mathrm{prc\_ts},\ \left( t,\ p,\ r,\ v \right) \in \mathrm{rtp\_vintyr}`$ — activity of a vintage of a process in a timeslice (VAR\_ACT) |
| $`\mathit{cap}`$ | `cap` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R}`$ — installed capacity (VAR\_CAP) |
| $`\mathit{ncap}`$ | `ncap` over $`\mathcal{P} \times \mathcal{R} \times \mathcal{V}`$ — new capacity (VAR\_NCAP) |

#### Variable domains

**`act`**

```math
\mathit{act}_{t,p,r,s,v} \ge 0 \qquad \forall\, \left( p,\ r,\ s \right) \in \mathrm{prc\_ts},\ \left( t,\ p,\ r,\ v \right) \in \mathrm{rtp\_vintyr}
```

**`cap`**

```math
\mathit{cap}_{t,p,r} \ge 0 \qquad \forall\, t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R}
```

**`ncap`**

```math
\mathit{ncap}_{p,r,v} \ge 0 \qquad \forall\, p \in \mathcal{P},\ r \in \mathcal{R},\ v \in \mathcal{V}
```

#### Objective

```math
\min \sum_{p \in \mathcal{P},\ r \in \mathcal{R},\ v \in \mathcal{V}} \mathrm{obj\_icost}_{p,r,v} \cdot \mathit{ncap}_{p,r,v} + \sum_{t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R}} \mathrm{obj\_acost}_{t,p,r} \cdot \left( \sum_{s \in \mathcal{S},\ v \in \mathcal{V}} \mathit{act}_{t,p,r,s,v} \right)
```

#### Subject to

**`eq_capact_up`**

```math
\sum_{s' \in \mathcal{S} \,:\, \left( r,\ s,\ s' \right) \in \mathrm{ts\_map}} \sum_{v \in \mathcal{V}} \mathit{act}_{t,p,r,s',v} \le \mathrm{coef\_af\_up}_{t,p,r,s} \cdot \mathrm{prc\_capact}_{p,r} \cdot \mathrm{g}^{\mathrm{yrfr}}_{r,s} \cdot \mathit{cap}_{t,p,r} \qquad \forall\, t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R},\ s \in \mathcal{S} \,:\, \mathrm{coef\_af\_up}_{t,p,r,s} \text{ is defined}
```

**`eq_cpt`**

```math
\mathit{cap}_{t,p,r} = \sum_{v \in \mathcal{V}} \mathrm{coef\_cpt}_{t,p,r,v} \cdot \left( \mathit{ncap}_{p,r,v} + \mathrm{ncap}^{\mathrm{pasti}}_{p,r,v} \right) \qquad \forall\, t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R}
```
<!-- gallery:end -->
