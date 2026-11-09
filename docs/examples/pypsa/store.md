<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Stores

This file states PyPSA's `Store`. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It adds a [term](../../reference/language/named.md#adds_to) to each of these sums: `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions` and `Bus_injection`. `Store_energy_carried_in` is the energy a store opens each snapshot with, for a cyclic store, an opening level and a later build alike.

<!-- gallery:begin -->
```yaml
given:
  parameters:
    snapshot_weightings_objective: { dims: [snapshot] }
    scenario_weight: { dims: [scenario] }
    CVaR_omega: { dims: [] }
    period_weight_objective: { dims: [period] }
    period_weight_years: { dims: [period] }
    snapshot_weightings_stores: { dims: [snapshot] }
    GlobalConstraint_counts_snapshot: { dims: [scenario, global_constraint, snapshot], dtype: bool }
  expressions:
    energy_limit_weight: { dims: [snapshot] }
    primary_energy: { dims: [global_constraint, scenario] }
    operational_limit: { dims: [global_constraint, scenario] }
    tech_capacity_expansion: { dims: [global_constraint] }
    scenario_opex: { dims: [scenario] }
    total_cost: { dims: [] }
    Carrier_additions: { dims: [carrier, period] }
    Bus_injection: { dims: [bus, scenario, snapshot] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  bus:
    description: network nodes
  store:
    description: pure energy stores, each on one bus
  global_constraint:
    description: PyPSA's `GlobalConstraint` rows, one label per declared limit
  period:
    description: investment periods. It is PyPSA's `investment_periods`
    dtype: int
    ordered: true
  carrier:
    description: energy carriers, what a growth limit is set per
  breakpoint:
    description: >-
      the corners of a piecewise-linear curve, in order. A curve runs over the
      breakpoints its data has rows for, so curves may differ in length
    dtype: int
    ordered: true

relations:
  snapshot_period:
    description: the investment period a snapshot falls in
    key: snapshot
    values: period
  Store_carrier:
    description: the carrier a store holds
    key: store
    values: carrier
  Store_bus:
    description: the bus a store sits on
    key: store
    values: bus

parameters:
  Store_active:
    description: whether a store is active in a snapshot's period. It is PyPSA's `active`, data prep
    dims: [snapshot, store]
    dtype: bool
  Store_active_asset:
    description: >-
      whether a store is one of PyPSA's `active_assets`, by its `active` flag
      alone, without build year and lifetime. A unit that is active in no
      snapshot of the horizon still counts. PyPSA refuses one that differs by
      scenario (`constants.py:54`)
    dims: [store]
    dtype: bool
  Store_capital_weight:
    description: the sum of period weights a store is active in. It is PyPSA's `active * period_weighting`, summed, data prep
    dims: [store]
  Store_first_active:
    description: >-
      one in the first period a store is active in, zero elsewhere, data prep.
      PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`)
    dims: [period, store]
  Store_e_nom_min:
    description: least nominal capacity an extendable store may be built at
    dims: [scenario, store]
  Store_e_nom_max:
    description: most nominal capacity an extendable store may be built at
    dims: [scenario, store]
  Store_capital_cost:
    description: >-
      cost of one unit of nominal capacity for the modelled horizon (PyPSA's
      `periodized_cost`), data prep. It is `overnight_cost` as an annuity over
      `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is
      given, and `capital_cost` where it is not. Both add `fom_cost`
      (`components.py:1176-1197`, `costs.py:102-203`)
    dims: [scenario, store]
  Store_e_nom_set:
    description: a given nominal capacity for an extendable store. One without a value has no row here
    dims: [store]
    missing: absent
  Store_e_nom:
    description: nominal energy capacity
    dims: [scenario, store]
  Store_e_nom_extendable:
    description: whether the nominal energy capacity is a decision
    dims: [store]
    dtype: bool
  Store_e_nom_mod:
    description: the module size a build comes in whole numbers of. No value means the build is continuous
    dims: [store]
    missing: absent
  Store_e_min_pu:
    description: "least energy held, per unit of nominal capacity: negative for a store that may go short"
    dims: [scenario, snapshot, store]
  Store_e_max_pu:
    description: most energy held, per unit of nominal capacity
    dims: [scenario, snapshot, store]
  Store_sign:
    description: >-
      the sign the power a store delivers enters its bus's balance with. It is
      PyPSA's `sign`, `1` unless given. PyPSA refuses one that differs by
      scenario (`constants.py:46`)
    dims: [store]
  Store_retention:
    description: share of energy kept over a snapshot. It is PyPSA's `(1 - standing_loss) ** elapsed hours`, data prep
    dims: [scenario, snapshot, store]
  Store_e_initial:
    description: energy held before the first snapshot
    dims: [scenario, store]
  Store_e_cyclic:
    description: whether the horizon closes on itself instead of opening on the initial energy
    dims: [scenario, store]
    dtype: bool
  Store_e_cyclic_per_period:
    description: >-
      whether each investment period closes on itself instead of carrying its
      energy on to the next. It overrides `e_cyclic` and
      `e_initial_per_period`. PyPSA reads it only under
      `multi_investment_periods`. Otherwise you feed false in data prep
    dims: [scenario, store]
    dtype: bool
  Store_e_initial_per_period:
    description: >-
      whether each investment period opens on the initial energy instead of
      carrying the previous period's. PyPSA reads it only under
      `multi_investment_periods`. Otherwise you feed false in data prep
    dims: [scenario, store]
    dtype: bool
  Store_opens_late:
    description: >-
      whether a snapshot is the first a store is active in, where that is not the
      first of the horizon, data prep. It is PyPSA's `active.cumsum() == 1`
      over the snapshots it is active in, past the first snapshot. It is false in
      a run where every store is active throughout
    dims: [snapshot, store]
    dtype: bool
  Store_inactive_snapshots:
    description: >-
      how many snapshots a store is not active in. It is PyPSA's
      `(~active).sum()`, data prep. A cyclic store reaches back this many
      snapshots further, so it closes on the last snapshot it is active in
    dims: [store]
    dtype: int
  Store_marginal_cost:
    description: cost of one unit of power delivered
    dims: [scenario, snapshot, store]
  Store_marginal_cost_quadratic:
    description: cost of the square of the net power delivered, so charging costs as much as delivering
    dims: [scenario, snapshot, store]
  Store_marginal_cost_curve_p:
    description: >-
      the power at each breakpoint of a store's piecewise `marginal_cost`
      curve: PyPSA's `p_pu` breakpoints times `e_nom`, not the power rating
      `e_nom / max_hours` that bounds `p`, data prep. A store with no curve
      has no rows
    dims: [store, breakpoint]
    missing: absent
  Store_marginal_cost_curve_cost:
    description: >-
      the running cost at each breakpoint of a store's piecewise
      `marginal_cost` curve: zero at the first, then each segment's width in
      power times the `marginal_cost` at its upper breakpoint, summed, data
      prep. It is linopy's `Slopes(...).to_breakpoints`
      (`piecewise.py:303-305`). A curve that starts below zero, in charging,
      costs more than nothing at zero power
    dims: [store, breakpoint]
    missing: absent
  Store_marginal_cost_storage:
    description: cost of one unit of energy held over one snapshot
    dims: [scenario, snapshot, store]
  Store_e_set:
    description: a given energy schedule. A store without one has no row here
    dims: [scenario, snapshot, store]
    missing: absent
  Store_p_set:
    description: a given schedule of power delivered. A store without one has no row here
    dims: [scenario, snapshot, store]
    missing: absent
  Store_max_hours:
    description: >-
      energy capacity, as hours of discharge at the power rating. The rating is
      `e_nom / max_hours`. No value means PyPSA's default of infinity, and the
      store's power is then unbounded
    dims: [scenario, store]
    missing: absent
  Store_p_min_pu:
    description: >-
      most charging, per unit of the power rating, negated. It is PyPSA's
      `p_min_pu`, `-1` unless given, read only where `max_hours` has a value
    dims: [scenario, snapshot, store]
  Store_p_max_pu:
    description: >-
      most discharge, per unit of the power rating. It is PyPSA's `p_max_pu`,
      `1` unless given, read only where `max_hours` has a value
    dims: [scenario, snapshot, store]
  Store_efficiency_store:
    description: share of the power drawn from the bus that becomes energy held
    dims: [scenario, snapshot, store]
  Store_efficiency_dispatch:
    description: share of the energy drawn down that reaches the bus
    dims: [scenario, snapshot, store]
  Store_inflow:
    description: energy arriving per hour, a river into a reservoir
    dims: [scenario, snapshot, store]
  Store_spill_cost:
    description: cost of one unit of inflow passed on unused
    dims: [scenario, snapshot, store]
  Store_marginal_cost_dispatch:
    description: cost of one unit of discharge, `p + p_store`
    dims: [scenario, snapshot, store]
  Store_marginal_cost_store:
    description: cost of one unit of charging, `p_store`
    dims: [scenario, snapshot, store]
  Store_split_dispatch:
    description: >-
      whether a store charges through `p_store` apart from its net dispatch
      `p`. It is PyPSA's `split_dispatch()`: true where an efficiency differs
      from one, a cost applies to one direction only, or `cycles_max` is
      finite, in any snapshot (`stores.py:88-116`), data prep. Where it is
      false, `p_store` is held at zero and the charging bound applies to `p`
    dims: [scenario, store]
    dtype: bool
  Store_e_sum_min:
    description: least energy of its net dispatch over the horizon. It is minus infinity where no floor is meant
    dims: [scenario, store]
  Store_e_sum_max:
    description: most energy of its net dispatch over the horizon. It is infinity where no cap is meant
    dims: [scenario, store]
  Store_cycles_max:
    description: >-
      most equivalent full cycles over the horizon: discharge divided by
      `e_nom`. No value means PyPSA's default of infinity, and no limit
    dims: [scenario, store]
    missing: absent
  Store_primary_energy_weight:
    description: the constrained attribute per unit of energy depleted, data prep. An unweighted store has no row
    dims: [scenario, global_constraint, store]
    missing: absent
  Store_operational_limit_weight:
    description: one where the store is in the row's set, data prep. One outside it has no row
    dims: [scenario, global_constraint, store]
    missing: absent
  Store_tech_capacity_weight:
    description: >-
      one where the store is in the row's carrier-and-bus set, data prep. One
      outside it, or one that is not active in the row's `investment_period`,
      has no row
    dims: [global_constraint, store]
    missing: absent

variables:
  Store_e:
    description: "`Store-e` — energy held at the end of a snapshot"
    dims: [scenario, snapshot, store]
    where: Store_active
  Store_p:
    description: "`Store-p` — net power delivered to the bus. Charging is negative"
    dims: [scenario, snapshot, store]
    where: Store_active
  Store_marginal_cost_piecewise:
    description: >-
      `Store-marginal_cost_piecewise` — the running cost of a store that pays
      along a curve, held above the curve
    dims: [scenario, snapshot, store]
    where: Store_marginal_cost_curve AND Store_active
  Store_p_store:
    description: >-
      `Store-p_store` — power drawn from the bus to charge, so that `p +
      p_store` is the discharge. It is held at zero by its rows where the store
      does not split its dispatch
    dims: [scenario, snapshot, store]
    where: Store_active
  Store_spill:
    description: >-
      `Store-spill` — inflow passed on unused. It is zero where there is no
      inflow, so the balance keeps its row there. The bounds are PyPSA's, on
      the variable rather than as rows
    dims: [scenario, snapshot, store]
    where: "Store_inflow > 0 AND Store_active"
    missing: 0
    bounds:
      lower: 0
      upper: Store_inflow
  Store_e_nom_ext:
    description: >-
      `Store-e_nom` — nominal capacity where it is a decision, for a store
      that is active. A fixed build is the parameter of the same PyPSA name
    dims: [store]
    where: Store_e_nom_extendable AND Store_active_asset
  Store_n_mod:
    description: "`Store-n_mod` — how many modules of an extendable modular build. A unit that is not active has none"
    dims: [store]
    where: Store_e_nom_extendable AND Store_e_nom_mod > 0 AND Store_active_asset
    domain: integer
    bounds:
      lower: 0

expressions:
  Store_energy_carried_in:
    description: >-
      the energy a store opens a snapshot with. At the first snapshot it
      is active in, it is its last such snapshot's less standing loss where it is
      cyclic. Where it is not, it is the given initial energy, which no
      standing loss has touched yet. Otherwise it is the previous snapshot's
      less standing loss. A store built in a later period opens in that
      period, and a cyclic one that retires closes on its own last snapshot.
      Per period, the same holds with each investment period as the horizon
    dims: [scenario, snapshot, store]
    cases:
      cyclic:
        when: >-
          Store_e_cyclic AND NOT Store_e_cyclic_per_period AND NOT Store_e_initial_per_period
          AND (position(snapshot) == 0 OR Store_opens_late)
        expression: >-
          Store_retention
          * shift(shift(Store_e, along=snapshot, offset=1, edge='wrap'), along=snapshot, offset=Store_inactive_snapshots, edge='wrap')
      opening:
        when: >-
          NOT Store_e_cyclic AND NOT Store_e_cyclic_per_period AND NOT Store_e_initial_per_period
          AND (position(snapshot) == 0 OR Store_opens_late)
        expression: Store_e_initial
      period_cyclic:
        when: Store_e_cyclic_per_period
        expression: Store_retention * shift(Store_e, along=snapshot, offset=1, edge='wrap', within=snapshot_period[period])
      period_opening:
        when: Store_e_initial_per_period AND NOT Store_e_cyclic_per_period AND position(snapshot, within=snapshot_period[period]) == 0
        expression: Store_e_initial
    otherwise: Store_retention * shift(Store_e, along=snapshot, offset=1)
  Store_e_nom_effective:
    description: "the build a store's limits are taken against: the chosen one where it is extendable, the given one otherwise"
    dims: [scenario, store]
    cases:
      extendable: { when: Store_e_nom_extendable, expression: Store_e_nom_ext }
    otherwise: Store_e_nom
  Store_discharge_floor_pu:
    description: >-
      the least discharge, per unit of `e_nom`. It is zero for a store that
      splits its dispatch, so `p_store` carries the charge. Otherwise it is the
      most charging as a negative discharge, `p_min_pu / max_hours`
      (`stores.py:79-86`)
    dims: [scenario, snapshot, store]
    cases:
      split: { when: Store_split_dispatch, expression: 0 }
    otherwise: Store_p_min_pu / Store_max_hours
  Store_charge_cap_pu:
    description: >-
      the most charging through `p_store`, per unit of `e_nom`. It is
      `-p_min_pu / max_hours` for a store that splits its dispatch, and zero
      otherwise (`stores.py:79-86`)
    dims: [scenario, snapshot, store]
    cases:
      split: { when: Store_split_dispatch, expression: -Store_p_min_pu / Store_max_hours }
    otherwise: 0
  Store_last_counted_active:
    description: >-
      one at the last snapshot a row counts where a store is active, and zero
      elsewhere. A store that retires before the last counted snapshot closes
      on its last active level. PyPSA forward-fills the level over the counted
      snapshots (`global_constraints.py:528-531`)
    dims: [scenario, global_constraint, snapshot, store]
    cases:
      last:
        when: >-
          GlobalConstraint_counts_snapshot AND Store_active
          AND NOT shift(GlobalConstraint_counts_snapshot AND Store_active, along=snapshot, offset=-1)
        expression: 1
    otherwise: 0
  Store_closing_weight:
    description: >-
      what the energy a store holds at a snapshot counts for in a row as its
      closing level. Where the store reopens per period, it is the years of
      the period at the last snapshot of each counted period. Where it does
      not, it is one at the last counted snapshot it is active in. It is nothing
      elsewhere
    dims: [scenario, global_constraint, snapshot, store]
    cases:
      per_period:
        when: Store_e_initial_per_period AND GlobalConstraint_counts_snapshot AND position(snapshot, within=snapshot_period[period]) == -1
        expression: at(period_weight_years, by=snapshot_period[period])
      carried_over:
        when: NOT Store_e_initial_per_period
        expression: Store_last_counted_active
    otherwise: 0
  Store_primary_energy:
    expression: >-
      -sum(sum((Store_e * Store_closing_weight) * Store_primary_energy_weight, over=snapshot), over=store)
    adds_to: primary_energy
  Store_operational_limit:
    expression: >-
      -sum(sum((Store_e * Store_closing_weight) * Store_operational_limit_weight, over=snapshot), over=store)
    adds_to: operational_limit
  Store_tech_capacity_expansion:
    expression: sum(Store_e_nom_ext * Store_tech_capacity_weight, over=store)
    adds_to: tech_capacity_expansion
  Store_running_cost:
    description: >-
      what a store's power costs in a snapshot: the value read off its
      piecewise curve where it has one, and its linear `marginal_cost`
      otherwise. A curve replaces the linear cost, as PyPSA drops the unit
      from that term (`optimize.py:333-348`)
    dims: [scenario, snapshot, store]
    cases:
      curve: { when: Store_marginal_cost_curve, expression: Store_marginal_cost_piecewise }
    otherwise: Store_p * Store_marginal_cost
  Store_opex:
    expression: >-
      sum(sum((Store_running_cost * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
      + sum(sum((((Store_p * Store_p) * Store_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
      + sum(sum(((Store_e * Store_marginal_cost_storage) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
      + sum(sum((((Store_p + Store_p_store) * Store_marginal_cost_dispatch) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
      + sum(sum(((Store_p_store * Store_marginal_cost_store) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
      + sum(sum(((Store_spill * Store_spill_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
    adds_to: scenario_opex
  Store_capex:
    expression: sum(scenario_weight * Store_e_nom_ext * Store_capital_cost * Store_capital_weight)
    adds_to: total_cost
  Store_additions:
    expression: >-
      sum(Store_e_nom_ext * Store_first_active, over=store, by=Store_carrier[carrier])
    adds_to: Carrier_additions
  Store_injection:
    expression: sum(Store_sign * Store_p, over=store, by=Store_bus[bus])
    adds_to: Bus_injection

conditions:
  Store_marginal_cost_curve:
    description: >-
      a store that pays along a piecewise `marginal_cost` curve: one of
      PyPSA's `active_assets` with curve data (`optimize.py:307`,
      `piecewise.py:223-250`)
    condition: count(Store_marginal_cost_curve_p, over=breakpoint) > 0 AND Store_active_asset
  Store_marginal_cost_curve_bends_down:
    description: >-
      a breakpoint where a store's cost curve gets less steep: the segment
      after it rises less per unit of power than the one before
    condition: >-
      Store_marginal_cost_curve_p
      AND shift(Store_marginal_cost_curve_p, along=breakpoint, offset=1)
      AND shift(Store_marginal_cost_curve_p, along=breakpoint, offset=-1)
      AND (Store_marginal_cost_curve_cost - shift(Store_marginal_cost_curve_cost, along=breakpoint, offset=1, edge=0))
      * (shift(Store_marginal_cost_curve_p, along=breakpoint, offset=-1, edge=0) - Store_marginal_cost_curve_p)
      > (shift(Store_marginal_cost_curve_cost, along=breakpoint, offset=-1, edge=0) - Store_marginal_cost_curve_cost)
      * (Store_marginal_cost_curve_p - shift(Store_marginal_cost_curve_p, along=breakpoint, offset=1, edge=0))
  Store_marginal_cost_as_lp:
    description: >-
      linopy's choice of method for all store cost curves at once
      (`method="auto"`): the segment lines where every curve is convex, the
      incremental rows otherwise. PyPSA calls linopy once per component, so
      this choice is apart from every other component's. A store has no
      status, so no gate (`optimize.py:314-318`, `piecewise.py:193-217`)
    condition: >-
      count(Store_marginal_cost_curve AND count(Store_marginal_cost_curve_bends_down, over=breakpoint) > 0, over=store) == 0

piecewise:
  Store_marginal_cost_lp:
    description: >-
      `Store-marginal_cost_piecewise` — the running cost of a store with a
      curve is at least the curve at its power, stated as the line of each
      segment, where linopy chooses the segment lines
    along: breakpoint
    dims: [scenario, snapshot, store]
    where: Store_marginal_cost_as_lp AND Store_marginal_cost_curve AND Store_active AND Store_marginal_cost_curve_p
    method: lp
    links:
      p: [Store_p, Store_marginal_cost_curve_p]
      cost: [Store_marginal_cost_piecewise, Store_marginal_cost_curve_cost, ">="]
  Store_marginal_cost_incremental:
    description: >-
      `Store-marginal_cost_piecewise` — the running cost of a store with a
      curve is at least the curve at its power, stated by segments filled in
      order, where linopy chooses the incremental rows
    along: breakpoint
    dims: [scenario, snapshot, store]
    where: NOT Store_marginal_cost_as_lp AND Store_marginal_cost_curve AND Store_active AND Store_marginal_cost_curve_p
    method: incremental
    links:
      p: [Store_p, Store_marginal_cost_curve_p]
      cost: [Store_marginal_cost_piecewise, Store_marginal_cost_curve_cost, ">="]

constraints:
  Store_e_sum_min:
    description: "`Store-e_sum_min` — net energy delivered over the horizon, each period weighted by its years, is at least its floor. A floor of minus infinity is no row"
    dims: [scenario, store]
    where: Store_e_sum_min
    expression: sum(Store_p * energy_limit_weight, over=snapshot) >= Store_e_sum_min
  Store_e_sum_max:
    description: "`Store-e_sum_max` — net energy delivered over the horizon, each period weighted by its years, is at most its budget. A budget of infinity is no row"
    dims: [scenario, store]
    where: Store_e_sum_max
    expression: sum(Store_p * energy_limit_weight, over=snapshot) <= Store_e_sum_max
  Store_fix_e_lower:
    description: "`Store-fix-e-lower` — a fixed store holds at least its floor"
    dims: [scenario, snapshot, store]
    where: not Store_e_nom_extendable AND Store_active
    expression: Store_e >= Store_e_min_pu * Store_e_nom
  Store_fix_e_upper:
    description: "`Store-fix-e-upper` — a fixed store holds at most its nominal capacity"
    dims: [scenario, snapshot, store]
    where: not Store_e_nom_extendable AND Store_active
    expression: Store_e <= Store_e_max_pu * Store_e_nom
  Store_ext_e_lower:
    description: "`Store-ext-e-lower` — an extendable store holds at least its floor of the chosen build"
    dims: [scenario, snapshot, store]
    where: Store_e_nom_extendable AND Store_active
    expression: Store_e >= Store_e_min_pu * Store_e_nom_ext
  Store_ext_e_upper:
    description: "`Store-ext-e-upper` — an extendable store holds at most the chosen build"
    dims: [scenario, snapshot, store]
    where: Store_e_nom_extendable AND Store_active
    expression: Store_e <= Store_e_max_pu * Store_e_nom_ext
  Store_ext_e_nom_lower:
    description: "`Store-ext-e_nom-lower` — the chosen build is at least its floor in every scenario"
    dims: [scenario, store]
    where: Store_e_nom_extendable AND Store_active_asset
    expression: Store_e_nom_ext >= Store_e_nom_min
  Store_ext_e_nom_upper:
    description: "`Store-ext-e_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
    dims: [scenario, store]
    where: Store_e_nom_extendable AND Store_active_asset AND Store_e_nom_max
    expression: Store_e_nom_ext <= Store_e_nom_max
  Store_e_nom_set:
    description: "`Store-e_nom_set` — the chosen build pinned, wherever a value is given"
    dims: [store]
    where: Store_e_nom_extendable AND Store_active_asset AND Store_e_nom_set
    expression: Store_e_nom_ext == Store_e_nom_set
  Store_e_nom_modularity:
    description: "`Store-e_nom_modularity` — the chosen build is a whole number of modules"
    dims: [store]
    where: Store_e_nom_extendable AND Store_e_nom_mod > 0 AND Store_active_asset
    expression: Store_e_nom_ext == Store_e_nom_mod * Store_n_mod
  Store_fix_p_lower:
    description: >-
      `Store-fix-p-lower` — a fixed store discharges at least its floor, which is
      zero where it splits its dispatch and its most charging otherwise. A
      store that does not split and has no `max_hours` has no row
    dims: [scenario, snapshot, store]
    where: NOT Store_e_nom_extendable AND Store_active AND (Store_split_dispatch OR Store_max_hours)
    expression: Store_p + Store_p_store >= Store_discharge_floor_pu * Store_e_nom
  Store_fix_p_upper:
    description: "`Store-fix-p-upper` — a fixed store discharges at most its power rating. A store without `max_hours` has no row"
    dims: [scenario, snapshot, store]
    where: NOT Store_e_nom_extendable AND Store_active AND Store_max_hours
    expression: Store_p + Store_p_store <= Store_p_max_pu / Store_max_hours * Store_e_nom
  Store_fix_p_store_lower:
    description: "`Store-fix-p_store-lower` — charging is non-negative"
    dims: [scenario, snapshot, store]
    where: NOT Store_e_nom_extendable AND Store_active
    expression: Store_p_store >= 0
  Store_fix_p_store_upper:
    description: >-
      `Store-fix-p_store-upper` — a fixed store charges at most its power rating where it
      splits its dispatch, and not at all where it does not. A store that splits
      and has no `max_hours` has no row
    dims: [scenario, snapshot, store]
    where: NOT Store_e_nom_extendable AND Store_active AND (NOT Store_split_dispatch OR Store_max_hours)
    expression: Store_p_store <= Store_charge_cap_pu * Store_e_nom
  Store_ext_p_lower:
    description: >-
      `Store-ext-p-lower` — an extendable store discharges at least its floor, which is
      zero where it splits its dispatch and its most charging otherwise. A
      store that does not split and has no `max_hours` has no row
    dims: [scenario, snapshot, store]
    where: Store_e_nom_extendable AND Store_active AND (Store_split_dispatch OR Store_max_hours)
    expression: Store_p + Store_p_store >= Store_discharge_floor_pu * Store_e_nom_ext
  Store_ext_p_upper:
    description: "`Store-ext-p-upper` — an extendable store discharges at most the power rating of the chosen build. A store without `max_hours` has no row"
    dims: [scenario, snapshot, store]
    where: Store_e_nom_extendable AND Store_active AND Store_max_hours
    expression: Store_p + Store_p_store <= Store_p_max_pu / Store_max_hours * Store_e_nom_ext
  Store_ext_p_store_lower:
    description: "`Store-ext-p_store-lower` — charging is non-negative"
    dims: [scenario, snapshot, store]
    where: Store_e_nom_extendable AND Store_active
    expression: Store_p_store >= 0
  Store_ext_p_store_upper:
    description: >-
      `Store-ext-p_store-upper` — an extendable store charges at most the power rating of the chosen build where it
      splits its dispatch, and not at all where it does not. A store that splits
      and has no `max_hours` has no row
    dims: [scenario, snapshot, store]
    where: Store_e_nom_extendable AND Store_active AND (NOT Store_split_dispatch OR Store_max_hours)
    expression: Store_p_store <= Store_charge_cap_pu * Store_e_nom_ext
  Store_energy_balance:
    description: >-
      `Store-energy_balance` — the energy carried in, less the discharge drawn
      down before its efficiency, plus the charge after its own, plus inflow
      not spilled. The net dispatch `p` is the discharge less `p_store`, so
      `p_store` enters with both efficiencies (`constraints.py:2472-2476`)
    dims: [scenario, snapshot, store]
    where: Store_active
    expression: >-
      Store_e ==
      Store_energy_carried_in
      - Store_p * snapshot_weightings_stores / Store_efficiency_dispatch
      + (Store_efficiency_store - 1 / Store_efficiency_dispatch) * Store_p_store * snapshot_weightings_stores
      + (Store_inflow - Store_spill) * snapshot_weightings_stores
  Store_cycles_max:
    description: >-
      `Store-cycles_max` — the discharge over the horizon, `p + p_store`
      weighted by the stores weighting, is at most `cycles_max` times the
      build. A store without `cycles_max` has no row
      (`constraints.py:2607-2633`)
    dims: [scenario, store]
    where: Store_cycles_max AND Store_active_asset
    expression: sum((Store_p + Store_p_store) * snapshot_weightings_stores, over=snapshot) <= Store_cycles_max * Store_e_nom_effective
  Store_e_set:
    description: "`Store-e_set` — energy pinned to the given schedule, wherever one is given"
    dims: [scenario, snapshot, store]
    where: Store_e_set AND Store_active
    expression: Store_e == Store_e_set
  Store_p_set:
    description: "`Store-p_set` — power delivered pinned to the given schedule, wherever one is given"
    dims: [scenario, snapshot, store]
    where: Store_p_set AND Store_active
    expression: Store_p == Store_p_set

assumptions:
  Store_marginal_cost_curve_on_a_fixed_build:
    holds: "NOT Store_e_nom_extendable AND Store_e_nom > 0 AND Store_e_nom < inf"
    where: "Store_marginal_cost_curve"
    description: >-
      a store's cost curve is given per unit of a fixed, positive, finite
      `e_nom`, which scales it to power. PyPSA refuses an extendable unit and
      a zero, missing or infinite `e_nom` (`piecewise.py:277-297`), and takes
      a negative one, which the file does not state
  Store_stands_in_one_run:
    holds: "count(Store_active AND NOT shift(Store_active, along=snapshot, offset=1), over=snapshot) <= 1"
    description: >-
      the snapshots a store is active in are one unbroken run, as a build
      year and a lifetime make them. The opening row holds at the first
      of them only, and a cyclic store reaches back
      `Store_inactive_snapshots` further to the last of them
  Store_opens_late_only_where_it_opens:
    holds: "Store_active AND NOT shift(Store_active, along=snapshot, offset=1) AND position(snapshot) > 0"
    where: "Store_opens_late"
    description: >-
      `Store_opens_late` marks the first snapshot the store is active in, past
      the first of the horizon, and no other
  Store_opens_late_where_it_opens:
    holds: "Store_opens_late"
    where: "Store_active AND NOT shift(Store_active, along=snapshot, offset=1) AND position(snapshot) > 0"
    description: >-
      a store that opens past the first snapshot of the horizon opens on its
      initial level, or its last level where it is cyclic. This holds only
      where `Store_opens_late` is true at the snapshot
  Store_primary_energy_per_period_without_scenarios:
    holds: "NOT Store_e_initial_per_period"
    where: "Store_primary_energy_weight AND count(scenario_weight, over=scenario) > 1"
    description: >-
      PyPSA reads the closing energy of a store that reopens per period by
      snapshot alone, and fails on a network with scenarios
      (`global_constraints.py:542`, PyPSA/PyPSA#2113). It fails with or without
      an `investment_period`. A tool refuses the store only where there is
      more than one scenario, since the spec cannot tell one scenario from
      none
  Store_operational_limit_per_period_without_scenarios:
    holds: "NOT Store_e_initial_per_period"
    where: "Store_operational_limit_weight AND count(scenario_weight, over=scenario) > 1"
    description: >-
      the same for an `operational_limit` row, which fails the same way
      (`global_constraints.py:741`, PyPSA/PyPSA#2113)
  Store_primary_energy_carried_over_has_unit_years:
    holds: "period_weight_years == 1"
    where: "Store_primary_energy_weight AND NOT Store_e_initial_per_period"
    description: >-
      a store that carries its energy from one period to the next closes once,
      at the last counted snapshot. No period's years weighs that level. PyPSA
      refuses it where any period's years is not one
      (`global_constraints.py:516`)
  Store_operational_limit_carried_over_has_unit_years:
    holds: "at(period_weight_years == 1, by=snapshot_period[period])"
    where: "Store_operational_limit_weight AND NOT Store_e_initial_per_period AND GlobalConstraint_counts_snapshot"
    description: >-
      the same for an `operational_limit` row, over the periods it counts.
      PyPSA refuses it (`global_constraints.py:718`)
  Store_marginal_cost_quadratic_without_risk_preference:
    holds: "Store_marginal_cost_quadratic == 0"
    where: "CVaR_omega"
    description: >-
      a quadratic cost puts a square into every `CVaR-excess` row. PyPSA
      refuses quadratic costs under any risk preference, `omega = 0` included
      (`optimize.py:506-513`). In data prep you write a `CVaR_omega` row only
      where a risk preference is set
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\omega`$ | `CVaR_omega` (scalar), data another file declares |
| $`\mathrm{in}`$ | `GlobalConstraint_counts_snapshot` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, data another file declares |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$, data another file declares |
| $`\mathrm{w}^{\mathrm{yr}}`$ | `period_weight_years` over $`\mathcal{Y}`$, data another file declares |
| $`\pi`$ | `scenario_weight` over $`\Xi`$, data another file declares |
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{w}^{\mathrm{sto}}`$ | `snapshot_weightings_stores` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, an expression this file adds `Store_injection` to |
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{I} \times \mathcal{Y}`$, an expression this file adds `Store_additions` to |
| $`\mathit{w}^{E}`$ | `energy_limit_weight` over $`\mathcal{T}`$, an expression another file defines |
| $`\mathit{operational\_limit}`$ | `operational_limit` over $`\mathcal{G} \times \Xi`$, an expression this file adds `Store_operational_limit` to |
| $`\mathit{primary\_energy}`$ | `primary_energy` over $`\mathcal{G} \times \Xi`$, an expression this file adds `Store_primary_energy` to |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Store_opex` to |
| $`\mathit{tech\_capacity\_expansion}`$ | `tech_capacity_expansion` over $`\mathcal{G}`$, an expression this file adds `Store_tech_capacity_expansion` to |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `Store_capex` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{B}`$ | index $`b`$ — `breakpoint` — the corners of a piecewise-linear curve, in order. A curve runs over the breakpoints its data has rows for, so curves may differ in length |
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Store\_bus}: \mathcal{V} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` with $`\mathrm{Store\_carrier}: \mathcal{V} \to \mathcal{I}`$ — energy carriers, what a growth limit is set per |
| $`\mathcal{G}`$ | index $`g`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods. It is PyPSA's `investment_periods` |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |
| $`\mathcal{V}`$ | index $`v`$ — `store` with $`\mathrm{Store\_bus}: \mathcal{V} \to \mathcal{N},\ \mathrm{Store\_carrier}: \mathcal{V} \to \mathcal{I}`$ — pure energy stores, each on one bus |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{e}`$ | `Store_active` over $`\mathcal{T} \times \mathcal{V}`$ — whether a store is active in a snapshot's period. It is PyPSA's `active`, data prep |
| $`\mathrm{act}^{e}`$ | `Store_active_asset` over $`\mathcal{V}`$ — whether a store is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{c}^{\mathrm{cap},e}`$ | `Store_capital_cost` over $`\Xi \times \mathcal{V}`$ — cost of one unit of nominal capacity for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1176-1197`, `costs.py:102-203`) |
| $`\mathrm{W}^{e}`$ | `Store_capital_weight` over $`\mathcal{V}`$ — the sum of period weights a store is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{cyc}^{\max}`$ | `Store_cycles_max` over $`\Xi \times \mathcal{V}`$, `absent` where the data has no row — most equivalent full cycles over the horizon: discharge divided by `e_nom`. No value means PyPSA's default of infinity, and no limit |
| $`\mathrm{cyc}^{e}`$ | `Store_e_cyclic` over $`\Xi \times \mathcal{V}`$ — whether the horizon closes on itself instead of opening on the initial energy |
| $`\mathrm{cyc}^{e,y}`$ | `Store_e_cyclic_per_period` over $`\Xi \times \mathcal{V}`$ — whether each investment period closes on itself instead of carrying its energy on to the next. It overrides `e_cyclic` and `e_initial_per_period`. PyPSA reads it only under `multi_investment_periods`. Otherwise you feed false in data prep |
| $`\mathrm{e}^{0}`$ | `Store_e_initial` over $`\Xi \times \mathcal{V}`$ — energy held before the first snapshot |
| $`\mathrm{reset}^{e}`$ | `Store_e_initial_per_period` over $`\Xi \times \mathcal{V}`$ — whether each investment period opens on the initial energy instead of carrying the previous period's. PyPSA reads it only under `multi_investment_periods`. Otherwise you feed false in data prep |
| $`\overline{\mathrm{e}}`$ | `Store_e_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — most energy held, per unit of nominal capacity |
| $`\underline{\mathrm{e}}`$ | `Store_e_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — least energy held, per unit of nominal capacity: negative for a store that may go short |
| $`\mathrm{e}^{\mathrm{nom}}`$ | `Store_e_nom` over $`\Xi \times \mathcal{V}`$ — nominal energy capacity |
| $`\mathrm{ext}^{e}`$ | `Store_e_nom_extendable` over $`\mathcal{V}`$ — whether the nominal energy capacity is a decision |
| $`\overline{\mathrm{e}}^{\mathrm{nom}}`$ | `Store_e_nom_max` over $`\Xi \times \mathcal{V}`$ — most nominal capacity an extendable store may be built at |
| $`\underline{\mathrm{e}}^{\mathrm{nom}}`$ | `Store_e_nom_min` over $`\Xi \times \mathcal{V}`$ — least nominal capacity an extendable store may be built at |
| $`\mathrm{e}^{\mathrm{mod}}`$ | `Store_e_nom_mod` over $`\mathcal{V}`$, `absent` where the data has no row — the module size a build comes in whole numbers of. No value means the build is continuous |
| $`\mathrm{e}^{\mathrm{nom,set}}`$ | `Store_e_nom_set` over $`\mathcal{V}`$, `absent` where the data has no row — a given nominal capacity for an extendable store. One without a value has no row here |
| $`\mathrm{e}^{\mathrm{set}}`$ | `Store_e_set` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$, `absent` where the data has no row — a given energy schedule. A store without one has no row here |
| $`\overline{\mathrm{E}}^{q}`$ | `Store_e_sum_max` over $`\Xi \times \mathcal{V}`$ — most energy of its net dispatch over the horizon. It is infinity where no cap is meant |
| $`\underline{\mathrm{E}}^{q}`$ | `Store_e_sum_min` over $`\Xi \times \mathcal{V}`$ — least energy of its net dispatch over the horizon. It is minus infinity where no floor is meant |
| $`\eta^{e,+}`$ | `Store_efficiency_dispatch` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — share of the energy drawn down that reaches the bus |
| $`\eta^{e,-}`$ | `Store_efficiency_store` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — share of the power drawn from the bus that becomes energy held |
| $`\mathrm{new}^{e}`$ | `Store_first_active` over $`\mathcal{Y} \times \mathcal{V}`$ — one in the first period a store is active in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`) |
| $`\mathrm{idle}^{e}`$ | `Store_inactive_snapshots` over $`\mathcal{V}`$ — how many snapshots a store is not active in. It is PyPSA's `(~active).sum()`, data prep. A cyclic store reaches back this many snapshots further, so it closes on the last snapshot it is active in |
| $`\mathrm{inflow}^{e}`$ | `Store_inflow` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — energy arriving per hour, a river into a reservoir |
| $`\mathrm{c}^{q}`$ | `Store_marginal_cost` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of power delivered |
| $`\mathrm{C}^{q,\mathrm{curve}}`$ | `Store_marginal_cost_curve_cost` over $`\mathcal{B} \times \mathcal{V}`$, `absent` where the data has no row — the running cost at each breakpoint of a store's piecewise `marginal_cost` curve: zero at the first, then each segment's width in power times the `marginal_cost` at its upper breakpoint, summed, data prep. It is linopy's `Slopes(...).to_breakpoints` (`piecewise.py:303-305`). A curve that starts below zero, in charging, costs more than nothing at zero power |
| $`\mathrm{q}^{\mathrm{curve}}`$ | `Store_marginal_cost_curve_p` over $`\mathcal{B} \times \mathcal{V}`$, `absent` where the data has no row — the power at each breakpoint of a store's piecewise `marginal_cost` curve: PyPSA's `p_pu` breakpoints times `e_nom`, not the power rating `e_nom / max_hours` that bounds `p`, data prep. A store with no curve has no rows |
| $`\mathrm{c}^{q,+}`$ | `Store_marginal_cost_dispatch` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of discharge, `p + p_store` |
| $`\mathrm{c}^{q,(2)}`$ | `Store_marginal_cost_quadratic` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of the square of the net power delivered, so charging costs as much as delivering |
| $`\mathrm{c}^{e}`$ | `Store_marginal_cost_storage` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of energy held over one snapshot |
| $`\mathrm{c}^{q,-}`$ | `Store_marginal_cost_store` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of charging, `p_store` |
| $`\mathrm{T}^{e}`$ | `Store_max_hours` over $`\Xi \times \mathcal{V}`$, `absent` where the data has no row — energy capacity, as hours of discharge at the power rating. The rating is `e_nom / max_hours`. No value means PyPSA's default of infinity, and the store's power is then unbounded |
| $`\mathrm{open}^{e}`$ | `Store_opens_late` over $`\mathcal{T} \times \mathcal{V}`$ — whether a snapshot is the first a store is active in, where that is not the first of the horizon, data prep. It is PyPSA's `active.cumsum() == 1` over the snapshots it is active in, past the first snapshot. It is false in a run where every store is active throughout |
| $`\mathrm{b}^{e}`$ | `Store_operational_limit_weight` over $`\mathcal{G} \times \Xi \times \mathcal{V}`$, `absent` where the data has no row — one where the store is in the row's set, data prep. One outside it has no row |
| $`\overline{\mathrm{q}}`$ | `Store_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — most discharge, per unit of the power rating. It is PyPSA's `p_max_pu`, `1` unless given, read only where `max_hours` has a value |
| $`\underline{\mathrm{q}}`$ | `Store_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — most charging, per unit of the power rating, negated. It is PyPSA's `p_min_pu`, `-1` unless given, read only where `max_hours` has a value |
| $`\mathrm{q}^{\mathrm{set}}`$ | `Store_p_set` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$, `absent` where the data has no row — a given schedule of power delivered. A store without one has no row here |
| $`\mathrm{a}^{e}`$ | `Store_primary_energy_weight` over $`\mathcal{G} \times \Xi \times \mathcal{V}`$, `absent` where the data has no row — the constrained attribute per unit of energy depleted, data prep. An unweighted store has no row |
| $`\rho^{e}`$ | `Store_retention` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — share of energy kept over a snapshot. It is PyPSA's `(1 - standing_loss) ** elapsed hours`, data prep |
| $`\mathrm{sgn}^{q}`$ | `Store_sign` over $`\mathcal{V}`$ — the sign the power a store delivers enters its bus's balance with. It is PyPSA's `sign`, `1` unless given. PyPSA refuses one that differs by scenario (`constants.py:46`) |
| $`\mathrm{c}^{\mathrm{spill},e}`$ | `Store_spill_cost` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of inflow passed on unused |
| $`\mathrm{split}^{e}`$ | `Store_split_dispatch` over $`\Xi \times \mathcal{V}`$ — whether a store charges through `p_store` apart from its net dispatch `p`. It is PyPSA's `split_dispatch()`: true where an efficiency differs from one, a cost applies to one direction only, or `cycles_max` is finite, in any snapshot (`stores.py:88-116`), data prep. Where it is false, `p_store` is held at zero and the charging bound applies to `p` |
| $`\mathrm{m}^{e}`$ | `Store_tech_capacity_weight` over $`\mathcal{G} \times \mathcal{V}`$, `absent` where the data has no row — one where the store is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{lp}^{q}`$ | `Store_marginal_cost_as_lp` (scalar) — linopy's choice of method for all store cost curves at once (`method="auto"`): the segment lines where every curve is convex, the incremental rows otherwise. PyPSA calls linopy once per component, so this choice is apart from every other component's. A store has no status, so no gate (`optimize.py:314-318`, `piecewise.py:193-217`) |
| $`\mathrm{curve}^{q}`$ | `Store_marginal_cost_curve` over $`\mathcal{V}`$ — a store that pays along a piecewise `marginal_cost` curve: one of PyPSA's `active_assets` with curve data (`optimize.py:307`, `piecewise.py:223-250`) |
| $`\mathrm{bend}^{q}`$ | `Store_marginal_cost_curve_bends_down` over $`\mathcal{B} \times \mathcal{V}`$ — a breakpoint where a store's cost curve gets less steep: the segment after it rises less per unit of power than the one before |

#### Variables

| Symbol | Meaning |
|---|---|
| $`e`$ | `Store_e` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — `Store-e` — energy held at the end of a snapshot |
| $`E`$ | `Store_e_nom_ext` over $`\mathcal{V}`$ — `Store-e_nom` — nominal capacity where it is a decision, for a store that is active. A fixed build is the parameter of the same PyPSA name |
| $`C^{q,\mathrm{curve}}`$ | `Store_marginal_cost_piecewise` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — `Store-marginal_cost_piecewise` — the running cost of a store that pays along a curve, held above the curve |
| $`N^{e}`$ | `Store_n_mod` over $`\mathcal{V}`$ — `Store-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`q`$ | `Store_p` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — `Store-p` — net power delivered to the bus. Charging is negative |
| $`q^{-}`$ | `Store_p_store` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — `Store-p_store` — power drawn from the bus to charge, so that `p + p_store` is the discharge. It is held at zero by its rows where the store does not split its dispatch |
| $`\mathit{spill}^{e}`$ | `Store_spill` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$, $`0`$ where the mask leaves it out — `Store-spill` — inflow passed on unused. It is zero where there is no inflow, so the balance keeps its row there. The bounds are PyPSA's, on the variable rather than as rows |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Store\_additions}`$ | `Store_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Store\_capex}`$ | `Store_capex` (scalar) |
| $`\overline{\mathrm{q}}^{-}`$ | `Store_charge_cap_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — the most charging through `p_store`, per unit of `e_nom`. It is `-p_min_pu / max_hours` for a store that splits its dispatch, and zero otherwise (`stores.py:79-86`) |
| $`\mathit{w}^{e}`$ | `Store_closing_weight` over $`\mathcal{G} \times \Xi \times \mathcal{T} \times \mathcal{V}`$ — what the energy a store holds at a snapshot counts for in a row as its closing level. Where the store reopens per period, it is the years of the period at the last snapshot of each counted period. Where it does not, it is one at the last counted snapshot it is active in. It is nothing elsewhere |
| $`\underline{\mathrm{q}}^{+}`$ | `Store_discharge_floor_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — the least discharge, per unit of `e_nom`. It is zero for a store that splits its dispatch, so `p_store` carries the charge. Otherwise it is the most charging as a negative discharge, `p_min_pu / max_hours` (`stores.py:79-86`) |
| $`\widetilde{\mathrm{e}}^{\mathrm{nom}}`$ | `Store_e_nom_effective` over $`\Xi \times \mathcal{V}`$ — the build a store's limits are taken against: the chosen one where it is extendable, the given one otherwise |
| $`\overleftarrow{e}`$ | `Store_energy_carried_in` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — the energy a store opens a snapshot with. At the first snapshot it is active in, it is its last such snapshot's less standing loss where it is cyclic. Where it is not, it is the given initial energy, which no standing loss has touched yet. Otherwise it is the previous snapshot's less standing loss. A store built in a later period opens in that period, and a cyclic one that retires closes on its own last snapshot. Per period, the same holds with each investment period as the horizon |
| $`\mathit{Store\_injection}`$ | `Store_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{last}^{e}`$ | `Store_last_counted_active` over $`\mathcal{G} \times \Xi \times \mathcal{T} \times \mathcal{V}`$ — one at the last snapshot a row counts where a store is active, and zero elsewhere. A store that retires before the last counted snapshot closes on its last active level. PyPSA forward-fills the level over the counted snapshots (`global_constraints.py:528-531`) |
| $`\mathit{Store\_operational\_limit}`$ | `Store_operational_limit` over $`\mathcal{G} \times \Xi`$ |
| $`\mathit{Store\_opex}`$ | `Store_opex` over $`\Xi`$ |
| $`\mathit{Store\_primary\_energy}`$ | `Store_primary_energy` over $`\mathcal{G} \times \Xi`$ |
| $`C^{q,\mathrm{run}}`$ | `Store_running_cost` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — what a store's power costs in a snapshot: the value read off its piecewise curve where it has one, and its linear `marginal_cost` otherwise. A curve replaces the linear cost, as PyPSA drops the unit from that term (`optimize.py:333-348`) |
| $`\mathit{Store\_tech\_capacity\_expansion}`$ | `Store_tech_capacity_expansion` over $`\mathcal{G}`$ |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`t \ominus^{\mathrm{relation}(t)} k`$ | `within=relation[...]` — $`t-k`$ inside the group of $`t`$ |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |
| $`\lvert \mathcal{T} \rvert`$ | the size of $`\mathcal{T}`$; $`\lvert \mathcal{T} \rvert - 1`$ is the last position |

#### Conditions

**`Store_marginal_cost_as_lp`**

```math
\mathrm{lp}^{q} \iff \lvert \{ v \in \mathcal{V} \,:\, \mathrm{curve}^{q}_{v} \wedge \lvert \{ b \in \mathcal{B} \,:\, \mathrm{bend}^{q}_{b,v} \} \rvert > 0 \} \rvert = 0
```

**`Store_marginal_cost_curve`**

```math
\mathrm{curve}^{q}_{v} \iff \lvert \{ b \in \mathcal{B} \,:\, \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \} \rvert > 0 \wedge \mathrm{act}^{e}_{v} \qquad \forall\, v \in \mathcal{V}
```

**`Store_marginal_cost_curve_bends_down`**

```math
\mathrm{bend}^{q}_{b,v} \iff \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \wedge \mathrm{q}^{\mathrm{curve}}_{b - 1,v} \text{ is defined} \wedge \mathrm{q}^{\mathrm{curve}}_{b + 1,v} \text{ is defined} \wedge \left( \mathrm{C}^{q,\mathrm{curve}}_{b,v} - \mathrm{C}^{q,\mathrm{curve}}_{b \boxminus_{0} 1,v} \right) \cdot \left( \mathrm{q}^{\mathrm{curve}}_{b \boxplus_{0} 1,v} - \mathrm{q}^{\mathrm{curve}}_{b,v} \right) > \left( \mathrm{C}^{q,\mathrm{curve}}_{b \boxplus_{0} 1,v} - \mathrm{C}^{q,\mathrm{curve}}_{b,v} \right) \cdot \left( \mathrm{q}^{\mathrm{curve}}_{b,v} - \mathrm{q}^{\mathrm{curve}}_{b \boxminus_{0} 1,v} \right) \qquad \forall\, b \in \mathcal{B},\ v \in \mathcal{V}
```

#### Variable domains

**`Store_e`**

```math
e_{\xi,t,v} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v}
```

**`Store_e_nom_ext`**

```math
E_{v} \in \mathbb{R} \qquad \forall\, v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v}
```

**`Store_marginal_cost_piecewise`**

```math
C^{q,\mathrm{curve}}_{\xi,t,v} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_n_mod`**

```math
N^{e}_{v} \ge 0, N^{e}_{v} \in \mathbb{Z} \qquad \forall\, v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{e}^{\mathrm{mod}}_{v} > 0 \wedge \mathrm{act}^{e}_{v}
```

**`Store_p`**

```math
q_{\xi,t,v} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v}
```

**`Store_p_store`**

```math
q^{-}_{\xi,t,v} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v}
```

**`Store_spill`**

```math
0 \le \mathit{spill}^{e}_{\xi,t,v} \le \mathrm{inflow}^{e}_{\xi,t,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{inflow}^{e}_{\xi,t,v} > 0 \wedge \mathrm{on}^{e}_{t,v}
```

#### Definitions

**`Store_additions`**

```math
\mathit{Store\_additions}_{i,y} = \sum_{v \in \mathcal{V} \,:\, \mathrm{Store\_carrier}(v) = i} E_{v} \cdot \mathrm{new}^{e}_{y,v} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

**`Store_capex`**

```math
\mathit{Store\_capex} = \sum_{\xi \in \Xi,\ v \in \mathcal{V}} \pi_{\xi} \cdot E_{v} \cdot \mathrm{c}^{\mathrm{cap},e}_{\xi,v} \cdot \mathrm{W}^{e}_{v}
```

**`Store_charge_cap_pu`**

```math
\overline{\mathrm{q}}^{-}_{\xi,t,v} = \begin{cases} \frac{-\underline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} & \text{if } \mathrm{split}^{e}_{\xi,v} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

**`Store_closing_weight`**

```math
\mathit{w}^{e}_{g,\xi,t,v} = \begin{cases} \mathit{last}^{e}_{g,\xi,t,v} & \text{if } \neg \mathrm{reset}^{e}_{\xi,v} \\ \mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} & \text{if } \mathrm{reset}^{e}_{\xi,v} \wedge \mathrm{in}_{g,\xi,t} \wedge \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) = \lvert \mathcal{T}_{\mathrm{snapshot\_period}(t)} \rvert - 1 \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

**`Store_discharge_floor_pu`**

```math
\underline{\mathrm{q}}^{+}_{\xi,t,v} = \begin{cases} 0 & \text{if } \mathrm{split}^{e}_{\xi,v} \\ \frac{\underline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

**`Store_e_nom_effective`**

```math
\widetilde{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} = \begin{cases} E_{v} & \text{if } \mathrm{ext}^{e}_{v} \\ \mathrm{e}^{\mathrm{nom}}_{\xi,v} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V}
```

**`Store_energy_carried_in`**

```math
\overleftarrow{e}_{\xi,t,v} = \begin{cases} \rho^{e}_{\xi,t,v} \cdot e_{\xi,\left( t \ominus \mathrm{idle}^{e} \right) \ominus 1,v} & \text{if } \mathrm{cyc}^{e}_{\xi,v} \wedge \neg \mathrm{cyc}^{e,y}_{\xi,v} \wedge \neg \mathrm{reset}^{e}_{\xi,v} \wedge \left( \mathrm{pos}(t) = 0 \vee \mathrm{open}^{e}_{t,v} \right) \\ \mathrm{e}^{0}_{\xi,v} & \text{if } \neg \mathrm{cyc}^{e}_{\xi,v} \wedge \neg \mathrm{cyc}^{e,y}_{\xi,v} \wedge \neg \mathrm{reset}^{e}_{\xi,v} \wedge \left( \mathrm{pos}(t) = 0 \vee \mathrm{open}^{e}_{t,v} \right) \\ \rho^{e}_{\xi,t,v} \cdot e_{\xi,t \ominus^{\mathrm{snapshot\_period}(t)} 1,v} & \text{if } \mathrm{cyc}^{e,y}_{\xi,v} \\ \mathrm{e}^{0}_{\xi,v} & \text{if } \mathrm{reset}^{e}_{\xi,v} \wedge \neg \mathrm{cyc}^{e,y}_{\xi,v} \wedge \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) = 0 \\ \rho^{e}_{\xi,t,v} \cdot e_{\xi,t - 1,v} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

**`Store_injection`**

```math
\mathit{Store\_injection}_{n,\xi,t} = \sum_{v \in \mathcal{V} \,:\, \mathrm{Store\_bus}(v) = n} \mathrm{sgn}^{q}_{v} \cdot q_{\xi,t,v} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Store_last_counted_active`**

```math
\mathit{last}^{e}_{g,\xi,t,v} = \begin{cases} 1 & \text{if } \mathrm{in}_{g,\xi,t} \wedge \mathrm{on}^{e}_{t,v} \wedge \neg \left( \mathrm{in}_{g,\xi,t + 1} \wedge \mathrm{on}^{e}_{t + 1,v} \right) \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

**`Store_operational_limit`**

```math
\mathit{Store\_operational\_limit}_{g,\xi} = -\left( \sum_{v \in \mathcal{V}} \sum_{t \in \mathcal{T}} e_{\xi,t,v} \cdot \mathit{w}^{e}_{g,\xi,t,v} \cdot \mathrm{b}^{e}_{g,\xi,v} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

**`Store_opex`**

```math
\mathit{Store\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} C^{q,\mathrm{run}}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} q_{\xi,t,v} \cdot q_{\xi,t,v} \cdot \mathrm{c}^{q,(2)}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} e_{\xi,t,v} \cdot \mathrm{c}^{e}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} \left( q_{\xi,t,v} + q^{-}_{\xi,t,v} \right) \cdot \mathrm{c}^{q,+}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} q^{-}_{\xi,t,v} \cdot \mathrm{c}^{q,-}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} \mathit{spill}^{e}_{\xi,t,v} \cdot \mathrm{c}^{\mathrm{spill},e}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

**`Store_primary_energy`**

```math
\mathit{Store\_primary\_energy}_{g,\xi} = -\left( \sum_{v \in \mathcal{V}} \sum_{t \in \mathcal{T}} e_{\xi,t,v} \cdot \mathit{w}^{e}_{g,\xi,t,v} \cdot \mathrm{a}^{e}_{g,\xi,v} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

**`Store_running_cost`**

```math
C^{q,\mathrm{run}}_{\xi,t,v} = \begin{cases} C^{q,\mathrm{curve}}_{\xi,t,v} & \text{if } \mathrm{curve}^{q}_{v} \\ q_{\xi,t,v} \cdot \mathrm{c}^{q}_{\xi,t,v} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

**`Store_tech_capacity_expansion`**

```math
\mathit{Store\_tech\_capacity\_expansion}_{g} = \sum_{v \in \mathcal{V}} E_{v} \cdot \mathrm{m}^{e}_{g,v} \qquad \forall\, g \in \mathcal{G}
```

#### Subject to

**`Store_cycles_max`**

```math
\sum_{t \in \mathcal{T}} \left( q_{\xi,t,v} + q^{-}_{\xi,t,v} \right) \cdot \mathrm{w}^{\mathrm{sto}}_{t} \le \mathrm{cyc}^{\max}_{\xi,v} \cdot \widetilde{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{cyc}^{\max}_{\xi,v} \text{ is defined} \wedge \mathrm{act}^{e}_{v}
```

**`Store_e_nom_modularity`**

```math
E_{v} = \mathrm{e}^{\mathrm{mod}}_{v} \cdot N^{e}_{v} \qquad \forall\, v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{e}^{\mathrm{mod}}_{v} > 0 \wedge \mathrm{act}^{e}_{v}
```

**`Store_e_nom_set`**

```math
E_{v} = \mathrm{e}^{\mathrm{nom,set}}_{v} \qquad \forall\, v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v} \wedge \mathrm{e}^{\mathrm{nom,set}}_{v} \text{ is defined}
```

**`Store_e_set`**

```math
e_{\xi,t,v} = \mathrm{e}^{\mathrm{set}}_{\xi,t,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{e}^{\mathrm{set}}_{\xi,t,v} \text{ is defined} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_e_sum_max`**

```math
\sum_{t \in \mathcal{T}} q_{\xi,t,v} \cdot \mathit{w}^{E}_{t} \le \overline{\mathrm{E}}^{q}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \overline{\mathrm{E}}^{q}_{\xi,v} \text{ is defined}
```

**`Store_e_sum_min`**

```math
\sum_{t \in \mathcal{T}} q_{\xi,t,v} \cdot \mathit{w}^{E}_{t} \ge \underline{\mathrm{E}}^{q}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \underline{\mathrm{E}}^{q}_{\xi,v} \text{ is defined}
```

**`Store_energy_balance`**

```math
e_{\xi,t,v} = \overleftarrow{e}_{\xi,t,v} - \frac{q_{\xi,t,v} \cdot \mathrm{w}^{\mathrm{sto}}_{t}}{\eta^{e,+}_{\xi,t,v}} + \left( \eta^{e,-}_{\xi,t,v} - \frac{1}{\eta^{e,+}_{\xi,t,v}} \right) \cdot q^{-}_{\xi,t,v} \cdot \mathrm{w}^{\mathrm{sto}}_{t} + \left( \mathrm{inflow}^{e}_{\xi,t,v} - \mathit{spill}^{e}_{\xi,t,v} \right) \cdot \mathrm{w}^{\mathrm{sto}}_{t} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v}
```

**`Store_ext_e_lower`**

```math
e_{\xi,t,v} \ge \underline{\mathrm{e}}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_ext_e_nom_lower`**

```math
E_{v} \ge \underline{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v}
```

**`Store_ext_e_nom_upper`**

```math
E_{v} \le \overline{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v} \wedge \overline{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \text{ is defined}
```

**`Store_ext_e_upper`**

```math
e_{\xi,t,v} \le \overline{\mathrm{e}}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_ext_p_lower`**

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \ge \underline{\mathrm{q}}^{+}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

**`Store_ext_p_store_lower`**

```math
q^{-}_{\xi,t,v} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_ext_p_store_upper`**

```math
q^{-}_{\xi,t,v} \le \overline{\mathrm{q}}^{-}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \neg \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

**`Store_ext_p_upper`**

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \le \frac{\overline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{T}^{e}_{\xi,v} \text{ is defined}
```

**`Store_fix_e_lower`**

```math
e_{\xi,t,v} \ge \underline{\mathrm{e}}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_fix_e_upper`**

```math
e_{\xi,t,v} \le \overline{\mathrm{e}}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_fix_p_lower`**

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \ge \underline{\mathrm{q}}^{+}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

**`Store_fix_p_store_lower`**

```math
q^{-}_{\xi,t,v} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_fix_p_store_upper`**

```math
q^{-}_{\xi,t,v} \le \overline{\mathrm{q}}^{-}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \neg \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

**`Store_fix_p_upper`**

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \le \frac{\overline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{T}^{e}_{\xi,v} \text{ is defined}
```

**`Store_p_set`**

```math
q_{\xi,t,v} = \mathrm{q}^{\mathrm{set}}_{\xi,t,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{q}^{\mathrm{set}}_{\xi,t,v} \text{ is defined} \wedge \mathrm{on}^{e}_{t,v}
```

**`Store_marginal_cost_incremental`**

```math
C^{q,\mathrm{curve}}_{\xi,t,v} \ge \mathrm{pwl}_{b \in \mathcal{B} \,:\, \neg \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined}}(\mathrm{q}^{\mathrm{curve}}_{b,v},\ \mathrm{C}^{q,\mathrm{curve}}_{b,v})(q_{\xi,t,v}) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

**`Store_marginal_cost_lp`**

```math
C^{q,\mathrm{curve}}_{\xi,t,v} \ge \mathrm{pwl}_{b \in \mathcal{B} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined}}(\mathrm{q}^{\mathrm{curve}}_{b,v},\ \mathrm{C}^{q,\mathrm{curve}}_{b,v})(q_{\xi,t,v}) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

#### Assumptions

**`Store_marginal_cost_curve_on_a_fixed_build`**

```math
\neg \mathrm{ext}^{e}_{v} \wedge \mathrm{e}^{\mathrm{nom}}_{\xi,v} > 0 \wedge \mathrm{e}^{\mathrm{nom}}_{\xi,v} < \infty \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{curve}^{q}_{v}
```

**`Store_marginal_cost_quadratic_without_risk_preference`**

```math
\mathrm{c}^{q,(2)}_{\xi,t,v} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \omega \text{ is defined}
```

**`Store_opens_late_only_where_it_opens`**

```math
\mathrm{on}^{e}_{t,v} \wedge \neg \mathrm{on}^{e}_{t - 1,v} \wedge \mathrm{pos}(t) > 0 \qquad \forall\, t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{open}^{e}_{t,v}
```

**`Store_opens_late_where_it_opens`**

```math
\mathrm{open}^{e}_{t,v} \qquad \forall\, t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v} \wedge \neg \mathrm{on}^{e}_{t - 1,v} \wedge \mathrm{pos}(t) > 0
```

**`Store_operational_limit_carried_over_has_unit_years`**

```math
\mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} = 1 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{b}^{e}_{g,\xi,v} \text{ is defined} \wedge \neg \mathrm{reset}^{e}_{\xi,v} \wedge \mathrm{in}_{g,\xi,t}
```

**`Store_operational_limit_per_period_without_scenarios`**

```math
\neg \mathrm{reset}^{e}_{\xi,v} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{b}^{e}_{g,\xi,v} \text{ is defined} \wedge \lvert \{ \xi' \in \Xi \,:\, \pi_{\xi'} \text{ is defined} \} \rvert > 1
```

**`Store_primary_energy_carried_over_has_unit_years`**

```math
\mathrm{w}^{\mathrm{yr}}_{y} = 1 \qquad \forall\, g \in \mathcal{G},\ y \in \mathcal{Y},\ \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{a}^{e}_{g,\xi,v} \text{ is defined} \wedge \neg \mathrm{reset}^{e}_{\xi,v}
```

**`Store_primary_energy_per_period_without_scenarios`**

```math
\neg \mathrm{reset}^{e}_{\xi,v} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{a}^{e}_{g,\xi,v} \text{ is defined} \wedge \lvert \{ \xi' \in \Xi \,:\, \pi_{\xi'} \text{ is defined} \} \rvert > 1
```

**`Store_stands_in_one_run`**

```math
\lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{e}_{t,v} \wedge \neg \mathrm{on}^{e}_{t - 1,v} \} \rvert \le 1 \qquad \forall\, v \in \mathcal{V}
```

**`Store_marginal_cost_incremental_complete`**

```math
\mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \wedge \mathrm{C}^{q,\mathrm{curve}}_{b,v} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined}
```

**`Store_marginal_cost_incremental_contiguous`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \neg \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \wedge \neg \left( \neg \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b - 1,v} \text{ is defined} \right) \} \rvert = 1 \qquad \forall\, t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \neg \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \} \rvert > 0
```

**`Store_marginal_cost_lp_complete`**

```math
\mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \wedge \mathrm{C}^{q,\mathrm{curve}}_{b,v} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined}
```

**`Store_marginal_cost_lp_increasing`**

```math
\mathrm{q}^{\mathrm{curve}}_{b \boxminus_{0} 1,v} < \mathrm{q}^{\mathrm{curve}}_{b,v} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \wedge \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b - 1,v} \text{ is defined}
```

**`Store_marginal_cost_lp_curvature`**

```math
\left( \mathrm{C}^{q,\mathrm{curve}}_{b,v} - \mathrm{C}^{q,\mathrm{curve}}_{b \boxminus_{0} 1,v} \right) \cdot \left( \mathrm{q}^{\mathrm{curve}}_{b \boxplus_{0} 1,v} - \mathrm{q}^{\mathrm{curve}}_{b,v} \right) \le \left( \mathrm{C}^{q,\mathrm{curve}}_{b \boxplus_{0} 1,v} - \mathrm{C}^{q,\mathrm{curve}}_{b,v} \right) \cdot \left( \mathrm{q}^{\mathrm{curve}}_{b,v} - \mathrm{q}^{\mathrm{curve}}_{b \boxminus_{0} 1,v} \right) \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \wedge \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b - 1,v} \text{ is defined} \wedge \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b + 1,v} \text{ is defined}
```

**`Store_marginal_cost_lp_breakpoints`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \} \rvert \ge 2 \qquad \forall\, t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \} \rvert > 0
```

**`Store_marginal_cost_lp_contiguous`**

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \wedge \neg \left( \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b - 1,v} \text{ is defined} \right) \} \rvert = 1 \qquad \forall\, t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{lp}^{q} \wedge \mathrm{curve}^{q}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{q}^{\mathrm{curve}}_{b,v} \text{ is defined} \} \rvert > 0
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
