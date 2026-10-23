<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Lines

This file states PyPSA's `Line`. It is one of the [24 fragments](index.md) that merge back into `examples/pypsa.yaml`. It adds a term to each of these sums: `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `total_cost`, `Carrier_additions`, `Bus_injection` and `Cycle_angle_sum`. It reads `scenario_weight` and `transmission_losses`, which other fragments declare, and lists them under [`given`](../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    scenario_weight: { dims: [scenario] }
    transmission_losses: { dims: [], dtype: bool }
  expressions:
    transmission_volume_expansion: { dims: [global_constraint, scenario] }
    transmission_expansion_cost: { dims: [global_constraint, scenario] }
    tech_capacity_expansion: { dims: [global_constraint] }
    total_cost: { dims: [] }
    Carrier_additions: { dims: [carrier, period] }
    Bus_injection: { dims: [bus, scenario, snapshot] }
    Cycle_angle_sum: { dims: [cycle, scenario, snapshot] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  bus:
    description: network nodes
  line:
    description: passive branches, each between two buses, their flow set by impedance
  cycle:
    description: >-
      independent cycles of the passive network graph — the cycle basis, data
      prep. Each period has its own basis, of the branches that stand in it;
      a label is a position in that period's basis, so one label names a
      different cycle in another period
  segment:
    description: >-
      the cuts a passive branch's loss curve is held above — PyPSA's tangents,
      as many as its `segments` count, or its secants, as many as its tolerance
      loop places; none in a lossless run
    dtype: int
  global_constraint:
    description: PyPSA's `GlobalConstraint` rows, one label per declared limit
  period:
    description: investment periods — PyPSA's `investment_periods`
    dtype: int
    ordered: true
  carrier:
    description: energy carriers, what a growth limit is set per

relations:
  snapshot_period:
    description: the investment period a snapshot falls in
    key: snapshot
    values: period
  Line_carrier:
    description: the carrier a line carries
    key: line
    values: carrier
  Line_bus0:
    description: the bus a line's flow is measured at
    key: line
    values: bus
  Line_bus1:
    description: the bus at a line's other end
    key: line
    values: bus

parameters:
  Line_active:
    description: whether a line stands in a snapshot's period — PyPSA's `active`, data prep
    dims: [snapshot, line]
    dtype: bool
  Line_active_asset:
    description: >-
      whether a line is one of PyPSA's `active_assets` — its `active` flag
      alone, without build year and lifetime, so a unit that stands in no
      snapshot of the horizon still counts. PyPSA refuses one that differs
      by scenario (`constants.py:51`)
    dims: [line]
    dtype: bool
  Line_capital_weight:
    description: the sum of period weights a line stands in — PyPSA's `active * period_weighting`, summed, data prep
    dims: [line]
  Line_first_active:
    description: >-
      one in the first period a line stands in, zero elsewhere, data prep.
      PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`)
    dims: [period, line]
  Line_s_nom:
    description: nominal apparent power
    dims: [scenario, line]
  Line_s_nom_extendable:
    description: whether the nominal apparent power is a decision
    dims: [line]
    dtype: bool
  Line_s_nom_mod:
    description: the module size a build comes in whole numbers of; no value means the build is continuous
    dims: [line]
    missing: neutral
  Line_s_max_pu:
    description: most flow either way, per unit of nominal apparent power
    dims: [scenario, snapshot, line]
  Line_s_nom_min:
    description: least nominal apparent power an extendable line may be built at
    dims: [scenario, line]
  Line_s_nom_max:
    description: most nominal apparent power an extendable line may be built at
    dims: [scenario, line]
  Line_capital_cost:
    description: >-
      cost of one unit of nominal apparent power for the modelled horizon —
      PyPSA's `periodized_cost`: `overnight_cost` as an annuity over
      `lifetime` at `discount_rate`, times `nyears`, where it is given, and
      `capital_cost` where it is not, plus `fom_cost`
      (`components.py:1126-1147`, `costs.py:102-203`), data prep
    dims: [scenario, line]
  Line_s_nom_set:
    description: a given nominal apparent power for an extendable line; one without a value has no row here
    dims: [line]
    missing: neutral
  Line_s_set:
    description: a given flow schedule; a line without one has no row here
    dims: [scenario, snapshot, line]
    missing: neutral
  Line_v_ang_max:
    description: >-
      the most the voltage angle difference across a line may be either way,
      in degrees — PyPSA's `v_ang_max`; infinite, and so no row, by default.
      A line whose carrier is not AC has no row either. The deprecated `v_ang_min` is
      ignored, as PyPSA ignores it with a `DeprecationWarning`
      (`constraints.py:1702-1709`)
    dims: [scenario, line]
    missing: neutral
  Line_x_pu_eff:
    description: >-
      the line's effective series reactance — PyPSA's `x_pu_eff`, `x` over
      the square of its bus's nominal voltage, data prep
    dims: [scenario, line]
  Line_cycle_weight:
    description: >-
      the line's series impedance, signed by its orientation in the cycle —
      the cycle basis, data prep; a line in no cycle has no row. PyPSA builds
      the cycle basis from the first scenario only (`networks.py:1430-1437`)
    dims: [period, line, cycle]
    missing: neutral
  Line_loss_max:
    description: the loss at a line's rating — PyPSA's `r_pu_eff * (s_max_pu * s_nom_max)**2`, data prep
    dims: [scenario, snapshot, line]
  Line_loss_slope:
    description: >-
      the slope of a cut to the loss curve — a tangent's `2 * r_pu_eff * p_k`
      at its segment's flow, a secant's `r_pu_eff * (p_k + p_k+1)` between
      consecutive breakpoints, data prep
    dims: [scenario, snapshot, line, segment]
  Line_loss_offset:
    description: >-
      where that cut meets the loss axis — a tangent's `loss_k - slope_k * p_k`,
      a secant's `-r_pu_eff * p_k * p_k+1`, negative, data prep
    dims: [scenario, snapshot, line, segment]
  Line_volume_weight:
    description: >-
      the line's length in each scenario where its carrier is in the row's
      set (`global_constraints.py:847-848`) — data prep; a
      line outside it, or one that does not stand in the row's
      `investment_period`, has no row
    dims: [scenario, global_constraint, line]
    missing: neutral
  Line_expansion_cost_weight:
    description: >-
      the line's capital cost where its carrier is in the row's set, times
      the objective weights of the periods it stands in where the row names
      no `investment_period` under `multi_investment_periods` — data prep; a
      line outside the set, or one that does not stand in the row's period,
      has no row. The capital cost is PyPSA's `capital_cost` property, which is
      `Line_capital_cost` without `fom_cost` (`components.py:1151-1169`,
      `global_constraints.py:870-879`)
    dims: [scenario, global_constraint, line]
    missing: neutral
  Line_tech_capacity_weight:
    description: >-
      one where the line is in the row's carrier-and-bus set — data prep; one
      outside it, or one that does not stand in the row's `investment_period`,
      has no row
    dims: [global_constraint, line]
    missing: neutral

variables:
  Line_s:
    description: >-
      `Line-s` — PyPSA's `p0`, the flow measured at the `Line_bus0` end: a
      positive value withdraws there and injects at `Line_bus1`, lossless
    dims: [scenario, snapshot, line]
    where: Line_active
  Line_loss:
    description: >-
      `Line-loss` — what a line dissipates carrying its flow, pushed down by the
      cost and held up by the cuts; absent, and zero in the balance, where
      the network is lossless
    dims: [scenario, snapshot, line]
    where: Line_lossy
    missing: neutral
    bounds:
      lower: 0
  Line_s_nom_ext:
    description: >-
      `Line-s_nom` — nominal apparent power where it is a decision, for a
      line that is active; the parameter of the same PyPSA name carries the
      fixed regime
    dims: [line]
    where: Line_s_nom_extendable AND Line_active_asset
  Line_n_mod:
    description: "`Line-n_mod` — how many modules of an extendable modular build; none for a unit that is not active"
    dims: [line]
    where: Line_s_nom_extendable AND Line_s_nom_mod > 0 AND Line_active_asset
    domain: integer
    bounds:
      lower: 0

expressions:
  Line_transmission_volume_expansion:
    expression: sum(Line_s_nom_ext * Line_volume_weight, over=line)
    adds_to: transmission_volume_expansion
  Line_transmission_expansion_cost:
    expression: sum(Line_s_nom_ext * Line_expansion_cost_weight, over=line)
    adds_to: transmission_expansion_cost
  Line_tech_capacity_expansion:
    expression: sum(Line_s_nom_ext * Line_tech_capacity_weight, over=line)
    adds_to: tech_capacity_expansion
  Line_capex:
    expression: sum(scenario_weight * Line_s_nom_ext * Line_capital_cost * Line_capital_weight)
    adds_to: total_cost
  Line_additions:
    expression: >-
      sum(Line_s_nom_ext * Line_first_active, over=line, by=Line_carrier[carrier])
    adds_to: Carrier_additions
  Line_s_monitored:
    description: >-
      the flow a line's post-contingency rows read — its flow where it stands,
      nothing where it does not, since PyPSA builds those rows for every
      branch of the sub-network in every snapshot
    dims: [scenario, snapshot, line]
    cases:
      standing: { when: Line_active, expression: Line_s }
    otherwise: 0
  Line_injection:
    expression: >-
      -sum(Line_s, over=line, by=Line_bus0[bus])
      + sum(Line_s, over=line, by=Line_bus1[bus])
      - (0.5 * sum(Line_loss, over=line, by=Line_bus0[bus]))
      - (0.5 * sum(Line_loss, over=line, by=Line_bus1[bus]))
    adds_to: Bus_injection
  Line_angle_sum:
    expression: sum(Line_s * at(Line_cycle_weight, by=snapshot_period[period]), over=line)
    adds_to: Cycle_angle_sum

conditions:
  Line_lossy:
    description: >-
      a line that stands in the snapshot's period, where the run models
      transmission losses
    condition: transmission_losses AND Line_active

constraints:
  Line_fix_s_lower:
    description: "`Line-fix-s-lower` — a fixed line carries at least the negative of its rating, the loss counted against it"
    dims: [scenario, snapshot, line]
    where: not Line_s_nom_extendable AND Line_active
    expression: Line_s - Line_loss >= -Line_s_max_pu * Line_s_nom
  Line_fix_s_upper:
    description: "`Line-fix-s-upper` — a fixed line carries at most its rating, the loss included"
    dims: [scenario, snapshot, line]
    where: not Line_s_nom_extendable AND Line_active
    expression: Line_s + Line_loss <= Line_s_max_pu * Line_s_nom
  Line_ext_s_lower:
    description: "`Line-ext-s-lower` — an extendable line carries at least the negative of its rating of the chosen build, the loss counted against it"
    dims: [scenario, snapshot, line]
    where: Line_s_nom_extendable AND Line_active
    expression: Line_s - Line_loss >= -Line_s_max_pu * Line_s_nom_ext
  Line_ext_s_upper:
    description: "`Line-ext-s-upper` — an extendable line carries at most its rating of the chosen build, the loss included"
    dims: [scenario, snapshot, line]
    where: Line_s_nom_extendable AND Line_active
    expression: Line_s + Line_loss <= Line_s_max_pu * Line_s_nom_ext
  Line_ext_s_nom_lower:
    description: "`Line-ext-s_nom-lower` — the chosen build is at least its floor in every scenario"
    dims: [scenario, line]
    where: Line_s_nom_extendable AND Line_active_asset
    expression: Line_s_nom_ext >= Line_s_nom_min
  Line_ext_s_nom_upper:
    description: "`Line-ext-s_nom-upper` — the chosen build is at most its cap in every scenario; a cap of infinity is no row"
    dims: [scenario, line]
    where: Line_s_nom_extendable AND Line_active_asset AND Line_s_nom_max
    expression: Line_s_nom_ext <= Line_s_nom_max
  Line_s_nom_set:
    description: "`Line-s_nom_set` — the chosen build pinned, wherever a value is given"
    dims: [line]
    where: Line_s_nom_extendable AND Line_active_asset AND Line_s_nom_set
    expression: Line_s_nom_ext == Line_s_nom_set
  Line_s_nom_modularity:
    description: "`Line-s_nom_modularity` — the chosen build is a whole number of modules"
    dims: [line]
    where: Line_s_nom_extendable AND Line_s_nom_mod > 0 AND Line_active_asset
    expression: Line_s_nom_ext == Line_s_nom_mod * Line_n_mod
  Line_s_set:
    description: "`Line-s_set` — flow pinned to the given schedule, wherever one is given"
    dims: [scenario, snapshot, line]
    where: Line_s_set AND Line_active
    expression: Line_s == Line_s_set
  Line_v_ang_lower:
    description: >-
      `Line-v_ang-lower` — an AC line carries at least the flow at which the
      voltage angle difference across it, `x_pu_eff` times the flow in
      radians, is the negative of its limit
    dims: [scenario, snapshot, line]
    where: Line_v_ang_max AND Line_carrier == 'AC' AND Line_active
    expression: Line_s >= -Line_v_ang_max * (3.141592653589793 / 180) / Line_x_pu_eff
  Line_v_ang_upper:
    description: >-
      `Line-v_ang-upper` — an AC line carries at most the flow at which the
      voltage angle difference across it reaches its limit
    dims: [scenario, snapshot, line]
    where: Line_v_ang_max AND Line_carrier == 'AC' AND Line_active
    expression: Line_s <= Line_v_ang_max * (3.141592653589793 / 180) / Line_x_pu_eff
  Line_loss_upper:
    description: "`Line-loss_upper` — a line dissipates at most the loss at its rating"
    dims: [scenario, snapshot, line]
    where: Line_lossy
    expression: Line_loss <= Line_loss_max
  Line_loss_tangents_forward:
    description: >-
      `Line-loss_tangents-{k}-1`, `Line-loss_secants-pos` — the loss sits above
      every cut to its curve for flow one way; PyPSA names one row per tangent
      `k`, or one row stacked over its `secant` axis, and this entry states them
      all over the segment dimension
    dims: [scenario, snapshot, line, segment]
    where: Line_lossy
    expression: Line_loss + Line_loss_slope * Line_s >= Line_loss_offset
  Line_loss_tangents_reverse:
    description: >-
      `Line-loss_tangents-{k}--1`, `Line-loss_secants-neg` — the same fan
      mirrored, the loss depending on the flow's magnitude
    dims: [scenario, snapshot, line, segment]
    where: Line_lossy
    expression: Line_loss - Line_loss_slope * Line_s >= Line_loss_offset
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\pi`$ | `scenario_weight` over $`\Xi`$, data another file declares |
| $`\mathrm{lossy}`$ | `transmission_losses` (scalar), data another file declares |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, an expression this file adds `Line_injection` to |
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{I} \times \mathcal{Y}`$, an expression this file adds `Line_additions` to |
| $`\mathit{Cycle\_angle\_sum}`$ | `Cycle_angle_sum` over $`\mathcal{C} \times \Xi \times \mathcal{T}`$, an expression this file adds `Line_angle_sum` to |
| $`\mathit{tech\_capacity\_expansion}`$ | `tech_capacity_expansion` over $`\mathcal{G}`$, an expression this file adds `Line_tech_capacity_expansion` to |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `Line_capex` to |
| $`\mathit{transmission\_expansion\_cost}`$ | `transmission_expansion_cost` over $`\mathcal{G} \times \Xi`$, an expression this file adds `Line_transmission_expansion_cost` to |
| $`\mathit{transmission\_volume\_expansion}`$ | `transmission_volume_expansion` over $`\mathcal{G} \times \Xi`$, an expression this file adds `Line_transmission_volume_expansion` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Line\_bus0}: \mathcal{K} \to \mathcal{N},\ \mathrm{Line\_bus1}: \mathcal{K} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` with $`\mathrm{Line\_carrier}: \mathcal{K} \to \mathcal{I}`$ — energy carriers, what a growth limit is set per |
| $`\mathcal{C}`$ | index $`c`$ — `cycle` — independent cycles of the passive network graph — the cycle basis, data prep. Each period has its own basis, of the branches that stand in it; a label is a position in that period's basis, so one label names a different cycle in another period |
| $`\mathcal{G}`$ | index $`g`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{K}`$ | index $`k`$ — `line` with $`\mathrm{Line\_bus0}: \mathcal{K} \to \mathcal{N},\ \mathrm{Line\_bus1}: \mathcal{K} \to \mathcal{N},\ \mathrm{Line\_carrier}: \mathcal{K} \to \mathcal{I}`$ — passive branches, each between two buses, their flow set by impedance |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods — PyPSA's `investment_periods` |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{E}`$ | index $`e`$ — `segment` — the cuts a passive branch's loss curve is held above — PyPSA's tangents, as many as its `segments` count, or its secants, as many as its tolerance loop places; none in a lossless run |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{s}`$ | `Line_active` over $`\mathcal{K} \times \mathcal{T}`$ — whether a line stands in a snapshot's period — PyPSA's `active`, data prep |
| $`\mathrm{act}^{s}`$ | `Line_active_asset` over $`\mathcal{K}`$ — whether a line is one of PyPSA's `active_assets` — its `active` flag alone, without build year and lifetime, so a unit that stands in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:51`) |
| $`\mathrm{c}^{\mathrm{cap},s}`$ | `Line_capital_cost` over $`\mathcal{K} \times \Xi`$ — cost of one unit of nominal apparent power for the modelled horizon — PyPSA's `periodized_cost`: `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where it is given, and `capital_cost` where it is not, plus `fom_cost` (`components.py:1126-1147`, `costs.py:102-203`), data prep |
| $`\mathrm{W}^{s}`$ | `Line_capital_weight` over $`\mathcal{K}`$ — the sum of period weights a line stands in — PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{x}`$ | `Line_cycle_weight` over $`\mathcal{C} \times \mathcal{K} \times \mathcal{Y}`$, `neutral` where the data has no row — the line's series impedance, signed by its orientation in the cycle — the cycle basis, data prep; a line in no cycle has no row. PyPSA builds the cycle basis from the first scenario only (`networks.py:1430-1437`) |
| $`\mathrm{cc}`$ | `Line_expansion_cost_weight` over $`\mathcal{G} \times \mathcal{K} \times \Xi`$, `neutral` where the data has no row — the line's capital cost where its carrier is in the row's set, times the objective weights of the periods it stands in where the row names no `investment_period` under `multi_investment_periods` — data prep; a line outside the set, or one that does not stand in the row's period, has no row. The capital cost is PyPSA's `capital_cost` property, which is `Line_capital_cost` without `fom_cost` (`components.py:1151-1169`, `global_constraints.py:870-879`) |
| $`\mathrm{new}^{s}`$ | `Line_first_active` over $`\mathcal{K} \times \mathcal{Y}`$ — one in the first period a line stands in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`) |
| $`\overline{\ell}`$ | `Line_loss_max` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — the loss at a line's rating — PyPSA's `r_pu_eff * (s_max_pu * s_nom_max)**2`, data prep |
| $`\mathrm{b}`$ | `Line_loss_offset` over $`\mathcal{K} \times \Xi \times \mathcal{E} \times \mathcal{T}`$ — where that cut meets the loss axis — a tangent's `loss_k - slope_k * p_k`, a secant's `-r_pu_eff * p_k * p_k+1`, negative, data prep |
| $`\mathrm{a}`$ | `Line_loss_slope` over $`\mathcal{K} \times \Xi \times \mathcal{E} \times \mathcal{T}`$ — the slope of a cut to the loss curve — a tangent's `2 * r_pu_eff * p_k` at its segment's flow, a secant's `r_pu_eff * (p_k + p_k+1)` between consecutive breakpoints, data prep |
| $`\overline{\mathrm{s}}`$ | `Line_s_max_pu` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — most flow either way, per unit of nominal apparent power |
| $`\mathrm{s}^{\mathrm{nom}}`$ | `Line_s_nom` over $`\mathcal{K} \times \Xi`$ — nominal apparent power |
| $`\mathrm{ext}^{s}`$ | `Line_s_nom_extendable` over $`\mathcal{K}`$ — whether the nominal apparent power is a decision |
| $`\overline{\mathrm{s}}^{\mathrm{nom}}`$ | `Line_s_nom_max` over $`\mathcal{K} \times \Xi`$ — most nominal apparent power an extendable line may be built at |
| $`\underline{\mathrm{s}}^{\mathrm{nom}}`$ | `Line_s_nom_min` over $`\mathcal{K} \times \Xi`$ — least nominal apparent power an extendable line may be built at |
| $`\mathrm{s}^{\mathrm{mod}}`$ | `Line_s_nom_mod` over $`\mathcal{K}`$, `neutral` where the data has no row — the module size a build comes in whole numbers of; no value means the build is continuous |
| $`\mathrm{s}^{\mathrm{nom,set}}`$ | `Line_s_nom_set` over $`\mathcal{K}`$, `neutral` where the data has no row — a given nominal apparent power for an extendable line; one without a value has no row here |
| $`\mathrm{s}^{\mathrm{set}}`$ | `Line_s_set` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$, `neutral` where the data has no row — a given flow schedule; a line without one has no row here |
| $`\mathrm{m}^{l}`$ | `Line_tech_capacity_weight` over $`\mathcal{G} \times \mathcal{K}`$, `neutral` where the data has no row — one where the line is in the row's carrier-and-bus set — data prep; one outside it, or one that does not stand in the row's `investment_period`, has no row |
| $`\overline{\delta}`$ | `Line_v_ang_max` over $`\mathcal{K} \times \Xi`$, `neutral` where the data has no row — the most the voltage angle difference across a line may be either way, in degrees — PyPSA's `v_ang_max`; infinite, and so no row, by default. A line whose carrier is not AC has no row either. The deprecated `v_ang_min` is ignored, as PyPSA ignores it with a `DeprecationWarning` (`constraints.py:1702-1709`) |
| $`\mathrm{len}`$ | `Line_volume_weight` over $`\mathcal{G} \times \mathcal{K} \times \Xi`$, `neutral` where the data has no row — the line's length in each scenario where its carrier is in the row's set (`global_constraints.py:847-848`) — data prep; a line outside it, or one that does not stand in the row's `investment_period`, has no row |
| $`\mathrm{x}^{\mathrm{eff}}`$ | `Line_x_pu_eff` over $`\mathcal{K} \times \Xi`$ — the line's effective series reactance — PyPSA's `x_pu_eff`, `x` over the square of its bus's nominal voltage, data prep |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{s,\mathrm{lossy}}`$ | `Line_lossy` over $`\mathcal{K} \times \mathcal{T}`$ — a line that stands in the snapshot's period, where the run models transmission losses |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\ell`$ | `Line_loss` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$, `neutral` where the mask leaves it out — `Line-loss` — what a line dissipates carrying its flow, pushed down by the cost and held up by the cuts; absent, and zero in the balance, where the network is lossless |
| $`N^{s}`$ | `Line_n_mod` over $`\mathcal{K}`$ — `Line-n_mod` — how many modules of an extendable modular build; none for a unit that is not active |
| $`s`$ | `Line_s` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — `Line-s` — PyPSA's `p0`, the flow measured at the `Line_bus0` end: a positive value withdraws there and injects at `Line_bus1`, lossless |
| $`S`$ | `Line_s_nom_ext` over $`\mathcal{K}`$ — `Line-s_nom` — nominal apparent power where it is a decision, for a line that is active; the parameter of the same PyPSA name carries the fixed regime |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Line\_additions}`$ | `Line_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Line\_angle\_sum}`$ | `Line_angle_sum` over $`\mathcal{C} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{Line\_capex}`$ | `Line_capex` (scalar) |
| $`\mathit{Line\_injection}`$ | `Line_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\check{s}`$ | `Line_s_monitored` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — the flow a line's post-contingency rows read — its flow where it stands, nothing where it does not, since PyPSA builds those rows for every branch of the sub-network in every snapshot |
| $`\mathit{Line\_tech\_capacity\_expansion}`$ | `Line_tech_capacity_expansion` over $`\mathcal{G}`$ |
| $`\mathit{Line\_transmission\_expansion\_cost}`$ | `Line_transmission_expansion_cost` over $`\mathcal{G} \times \Xi`$ |
| $`\mathit{Line\_transmission\_volume\_expansion}`$ | `Line_transmission_volume_expansion` over $`\mathcal{G} \times \Xi`$ |

#### Conditions

**`Line_lossy`**

```math
\mathrm{on}^{s,\mathrm{lossy}}_{k,t} \iff \mathrm{lossy} \wedge \mathrm{on}^{s}_{k,t} \qquad \forall\, k \in \mathcal{K},\ t \in \mathcal{T}
```

#### Variable domains

**`Line_loss`**

```math
\ell_{k,\xi,t} \ge 0 \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{s,\mathrm{lossy}}_{k,t}
```

**`Line_n_mod`**

```math
N^{s}_{k} \ge 0, N^{s}_{k} \in \mathbb{Z} \qquad \forall\, k \in \mathcal{K} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{s}^{\mathrm{mod}}_{k} > 0 \wedge \mathrm{act}^{s}_{k}
```

**`Line_s`**

```math
s_{k,\xi,t} \in \mathbb{R} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{s}_{k,t}
```

**`Line_s_nom_ext`**

```math
S_{k} \in \mathbb{R} \qquad \forall\, k \in \mathcal{K} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{act}^{s}_{k}
```

#### Definitions

**`Line_additions`**

```math
\mathit{Line\_additions}_{i,y} = \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_carrier}(k) = i} S_{k} \cdot \mathrm{new}^{s}_{k,y} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

**`Line_angle_sum`**

```math
\mathit{Line\_angle\_sum}_{c,\xi,t} = \sum_{k \in \mathcal{K}} s_{k,\xi,t} \cdot \mathrm{x}_{c,k,\mathrm{snapshot\_period}(t)} \qquad \forall\, c \in \mathcal{C},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Line_capex`**

```math
\mathit{Line\_capex} = \sum_{k \in \mathcal{K},\ \xi \in \Xi} \pi_{\xi} \cdot S_{k} \cdot \mathrm{c}^{\mathrm{cap},s}_{k,\xi} \cdot \mathrm{W}^{s}_{k}
```

**`Line_injection`**

```math
\mathit{Line\_injection}_{n,\xi,t} = -\left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus0}(k) = n} s_{k,\xi,t} \right) + \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus1}(k) = n} s_{k,\xi,t} - 0.5 \cdot \left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus0}(k) = n} \ell_{k,\xi,t} \right) - 0.5 \cdot \left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus1}(k) = n} \ell_{k,\xi,t} \right) \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Line_s_monitored`**

```math
\check{s}_{k,\xi,t} = \begin{cases} s_{k,\xi,t} & \text{if } \mathrm{on}^{s}_{k,t} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Line_tech_capacity_expansion`**

```math
\mathit{Line\_tech\_capacity\_expansion}_{g} = \sum_{k \in \mathcal{K}} S_{k} \cdot \mathrm{m}^{l}_{g,k} \qquad \forall\, g \in \mathcal{G}
```

**`Line_transmission_expansion_cost`**

```math
\mathit{Line\_transmission\_expansion\_cost}_{g,\xi} = \sum_{k \in \mathcal{K}} S_{k} \cdot \mathrm{cc}_{g,k,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

**`Line_transmission_volume_expansion`**

```math
\mathit{Line\_transmission\_volume\_expansion}_{g,\xi} = \sum_{k \in \mathcal{K}} S_{k} \cdot \mathrm{len}_{g,k,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

#### Subject to

**`Line_ext_s_lower`**

```math
s_{k,\xi,t} - \ell_{k,\xi,t} \ge -\overline{\mathrm{s}}_{k,\xi,t} \cdot S_{k} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

**`Line_ext_s_nom_lower`**

```math
S_{k} \ge \underline{\mathrm{s}}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{act}^{s}_{k}
```

**`Line_ext_s_nom_upper`**

```math
S_{k} \le \overline{\mathrm{s}}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{act}^{s}_{k} \wedge \overline{\mathrm{s}}^{\mathrm{nom}}_{k,\xi} \text{ is defined}
```

**`Line_ext_s_upper`**

```math
s_{k,\xi,t} + \ell_{k,\xi,t} \le \overline{\mathrm{s}}_{k,\xi,t} \cdot S_{k} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

**`Line_fix_s_lower`**

```math
s_{k,\xi,t} - \ell_{k,\xi,t} \ge -\overline{\mathrm{s}}_{k,\xi,t} \cdot \mathrm{s}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

**`Line_fix_s_upper`**

```math
s_{k,\xi,t} + \ell_{k,\xi,t} \le \overline{\mathrm{s}}_{k,\xi,t} \cdot \mathrm{s}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

**`Line_loss_tangents_forward`**

```math
\ell_{k,\xi,t} + \mathrm{a}_{k,\xi,e,t} \cdot s_{k,\xi,t} \ge \mathrm{b}_{k,\xi,e,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ e \in \mathcal{E},\ t \in \mathcal{T} \,:\, \mathrm{on}^{s,\mathrm{lossy}}_{k,t}
```

**`Line_loss_tangents_reverse`**

```math
\ell_{k,\xi,t} - \mathrm{a}_{k,\xi,e,t} \cdot s_{k,\xi,t} \ge \mathrm{b}_{k,\xi,e,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ e \in \mathcal{E},\ t \in \mathcal{T} \,:\, \mathrm{on}^{s,\mathrm{lossy}}_{k,t}
```

**`Line_loss_upper`**

```math
\ell_{k,\xi,t} \le \overline{\ell}_{k,\xi,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{s,\mathrm{lossy}}_{k,t}
```

**`Line_s_nom_modularity`**

```math
S_{k} = \mathrm{s}^{\mathrm{mod}}_{k} \cdot N^{s}_{k} \qquad \forall\, k \in \mathcal{K} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{s}^{\mathrm{mod}}_{k} > 0 \wedge \mathrm{act}^{s}_{k}
```

**`Line_s_nom_set`**

```math
S_{k} = \mathrm{s}^{\mathrm{nom,set}}_{k} \qquad \forall\, k \in \mathcal{K} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{act}^{s}_{k} \wedge \mathrm{s}^{\mathrm{nom,set}}_{k} \text{ is defined}
```

**`Line_s_set`**

```math
s_{k,\xi,t} = \mathrm{s}^{\mathrm{set}}_{k,\xi,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{s}^{\mathrm{set}}_{k,\xi,t} \text{ is defined} \wedge \mathrm{on}^{s}_{k,t}
```

**`Line_v_ang_lower`**

```math
s_{k,\xi,t} \ge \frac{-\overline{\delta}_{k,\xi} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff}}_{k,\xi}} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \overline{\delta}_{k,\xi} \text{ is defined} \wedge \mathrm{Line\_carrier}(k) = \text{'}\mathrm{AC}\text{'} \wedge \mathrm{on}^{s}_{k,t}
```

**`Line_v_ang_upper`**

```math
s_{k,\xi,t} \le \frac{\overline{\delta}_{k,\xi} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff}}_{k,\xi}} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \overline{\delta}_{k,\xi} \text{ is defined} \wedge \mathrm{Line\_carrier}(k) = \text{'}\mathrm{AC}\text{'} \wedge \mathrm{on}^{s}_{k,t}
```
<!-- gallery:end -->
