<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Generators

This file states PyPSA's `Generator`, with its unit commitment, its ramp limits and its maintenance. It is one of the [14 fragments](index.md) that merge back into `examples/pypsa.yaml`. It adds a term to each of these sums: `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions` and `Bus_injection`. It reads `CVaR_omega`, `GlobalConstraint_energy_weight`, `period_weight_objective`, `scenario_weight`, `snapshot_weightings_generators` and `snapshot_weightings_objective`, which other fragments declare, and lists them under [`given`](../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    snapshot_weightings_objective: { dims: [snapshot] }
    scenario_weight: { dims: [scenario] }
    CVaR_omega: { dims: [] }
    period_weight_objective: { dims: [period] }
    snapshot_weightings_generators: { dims: [snapshot] }
  expressions:
    GlobalConstraint_energy_weight: { dims: [scenario, global_constraint, snapshot] }
    primary_energy: { dims: [scenario, global_constraint] }
    operational_limit: { dims: [scenario, global_constraint] }
    tech_capacity_expansion: { dims: [global_constraint] }
    scenario_opex: { dims: [scenario] }
    total_cost: { dims: [] }
    Carrier_additions: { dims: [period, carrier] }
    Bus_injection: { dims: [scenario, snapshot, bus] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  bus:
    description: network nodes
  generator:
    description: generating units, each on one bus
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
  Generator_carrier:
    description: the carrier a generator converts from
    key: generator
    values: carrier
  Generator_bus:
    description: the bus a generator sits on
    key: generator
    values: bus
  Generator_maintenance_cover:
    description: >-
      the snapshots a maintenance event covers, by the snapshot it starts in —
      in a scenario, the start and the snapshots after it, until their
      generator weightings reach that scenario's `maintenance_duration`, data prep; no
      rows for a generator that is
      not maintainable
    key: { scenario: scenario, generator: generator, start: snapshot, covered: snapshot }
    missing: absent

parameters:
  Generator_p_nom:
    description: nominal power
    dims: [scenario, generator]
  Generator_p_nom_extendable:
    description: whether the nominal power is a decision
    dims: [generator]
    dtype: bool
  Generator_p_min_pu:
    description: least output, per unit of nominal power
    dims: [scenario, snapshot, generator]
  Generator_p_max_pu:
    description: most output, per unit of nominal power — an availability profile
    dims: [scenario, snapshot, generator]
  Generator_marginal_cost:
    description: cost of one unit of output
    dims: [scenario, snapshot, generator]
  Generator_marginal_cost_quadratic:
    description: cost of the square of one unit of output
    dims: [scenario, snapshot, generator]
  Generator_sign:
    description: >-
      the sign output enters its bus's balance with — PyPSA's `sign`, `1`
      unless given, `-1` for a unit that draws power. PyPSA refuses one that
      differs by scenario (`constants.py:43`)
    dims: [generator]
  Generator_committable:
    description: whether output is gated by an on/off status decision
    dims: [generator]
    dtype: bool
  Generator_ramp_limit_up:
    description: most a generator may raise its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time
    dims: [scenario, snapshot, generator]
    missing: neutral
  Generator_ramp_limit_down:
    description: most a generator may lower its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time
    dims: [scenario, snapshot, generator]
    missing: neutral
  Generator_ramp_limit_start_up:
    description: most output in the snapshot a unit starts, per unit of nominal power; no value means no limit
    dims: [scenario, generator]
    missing: neutral
  Generator_ramp_limit_shut_down:
    description: most output in the snapshot before a unit stops, per unit of nominal power; no value means no limit
    dims: [scenario, generator]
    missing: neutral
  Generator_min_up_time:
    description: least snapshots a unit stays on once started
    dims: [scenario, generator]
    dtype: int
  Generator_min_down_time:
    description: least snapshots a unit stays off once stopped
    dims: [scenario, generator]
    dtype: int
  Generator_status_initial:
    description: one where the unit was on before the first snapshot, zero where off — PyPSA's `up_time_before > 0`, data prep
    dims: [scenario, generator]
    dtype: int
  Generator_p_init:
    description: >-
      the output a unit brought into the horizon — PyPSA's `p_init`, read
      only where the unit came in running; no value means it is unknown, so
      the unit carries no ramp row at the first snapshot
    dims: [scenario, generator]
    missing: neutral
  Generator_must_stay_up:
    description: >-
      true while the up time a unit brought into the horizon still binds —
      data prep, since `position()` compares against a literal rather than a
      parameter
    dims: [scenario, snapshot, generator]
    dtype: bool
  Generator_must_stay_down:
    description: >-
      true while the down time a unit brought into the horizon still binds —
      PyPSA's `min_down_time - down_time_before` snapshots, where
      `down_time_before > 0`, data prep for the same reason
    dims: [scenario, snapshot, generator]
    dtype: bool
  Generator_start_up_cost:
    description: cost of one start in this snapshot
    dims: [scenario, snapshot, generator]
  Generator_shut_down_cost:
    description: cost of one stop in this snapshot
    dims: [scenario, snapshot, generator]
  Generator_stand_by_cost:
    description: cost of one snapshot spent on
    dims: [scenario, snapshot, generator]
  Generator_p_nom_mod:
    description: the module size a build comes in whole numbers of; no value means the build is continuous
    dims: [generator]
    missing: neutral
  Generator_modules_installed:
    description: >-
      how many whole modules a committable build has in place: `Generator_p_nom
      / Generator_p_nom_mod` where a fixed build is modular, one where it is
      not, data prep. PyPSA refuses a fixed modular build whose nominal power
      is not a whole number of modules
    dims: [scenario, generator]
  Generator_big_m:
    description: >-
      the bound a committed extendable generator's big-M rows release it by — the
      build cap `p_nom_max` times the highest `p_max_pu`, where the cap is
      finite and positive. Elsewhere it is `committable_big_m` times the
      highest `p_max_pu`, and where that keyword is not given, ten times the
      largest of the peak total load and the component's largest finite
      `p_nom` and `p_nom_max`, or 1e6 where there is none of them
      (`components.py:1050-1121`). Below the output a solve wants, it caps that
      output; data prep
    dims: [scenario, generator]
    missing: neutral
  Generator_p_min_pu_nonneg:
    description: >-
      true where none of the generator's own minimums-per-unit is negative —
      PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep
    dims: [generator]
    dtype: bool
  Generator_maintainable:
    description: >-
      whether a generator must be taken off for maintenance within the horizon — in
      any scenario, as PyPSA takes the union over them (`components.py:1016-1019`)
    dims: [generator]
    dtype: bool
  Generator_maintenance_pu:
    description: the share of the build a maintenance event takes off
    dims: [scenario, generator]
  Generator_maintenance_events:
    description: how many maintenance events the horizon holds
    dims: [scenario, generator]
    dtype: int
  Generator_maintenance_duration:
    description: >-
      the hours of generator weightings one maintenance event covers —
      PyPSA's `maintenance_duration`; no value where the generator is not
      maintainable. No row reads it: data prep turns it into
      `Generator_maintenance_cover` and `Generator_maintenance_start_blocked`, and the
      assumptions hold it to the horizon
    dims: [scenario, generator]
    missing: neutral
  Generator_maintenance_start_blocked:
    description: >-
      true where no maintenance event may start, because the snapshots it
      would cover run past the end of the horizon or into one the generator does
      not stand in — PyPSA's `active & ~valid`, from `maintenance_duration`
      and the generator weightings, data prep
    dims: [scenario, snapshot, generator]
    dtype: bool
  Generator_active:
    description: whether a generator stands in a snapshot's period — PyPSA's `active`, from build year and lifetime, data prep
    dims: [snapshot, generator]
    dtype: bool
  Generator_active_asset:
    description: >-
      whether a generator is one of PyPSA's `active_assets` — its `active` flag
      alone, without build year and lifetime, so a unit that stands in no
      snapshot of the horizon still counts. PyPSA refuses one that differs
      by scenario (`constants.py:51`)
    dims: [generator]
    dtype: bool
  Generator_capital_weight:
    description: the sum of period weights a generator stands in — PyPSA's `active * period_weighting`, summed, data prep
    dims: [generator]
  Generator_first_active:
    description: >-
      one in the first period a generator stands in, zero elsewhere, data prep.
      PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`)
    dims: [period, generator]
  Generator_p_set:
    description: a given output schedule; a generator without one has no row here
    dims: [scenario, snapshot, generator]
    missing: neutral
  Generator_p_nom_min:
    description: least nominal power an extendable generator may be built at
    dims: [scenario, generator]
  Generator_p_nom_max:
    description: most nominal power an extendable generator may be built at
    dims: [scenario, generator]
  Generator_capital_cost:
    description: >-
      cost of one unit of nominal power for the modelled horizon —
      PyPSA's `periodized_cost`: `overnight_cost` as an annuity over
      `lifetime` at `discount_rate`, times `nyears`, where it is given, and
      `capital_cost` where it is not, plus `fom_cost`
      (`components.py:1126-1147`, `costs.py:102-203`), data prep
    dims: [scenario, generator]
  Generator_p_nom_set:
    description: a given nominal power for an extendable generator; one without a value has no row here
    dims: [generator]
    missing: neutral
  Generator_e_sum_min:
    description: least energy over the horizon; minus infinity where no floor is meant
    dims: [scenario, generator]
  Generator_e_sum_max:
    description: most energy over the horizon — a fuel or emission budget in energy terms; infinity where no cap is meant
    dims: [scenario, generator]
  Generator_primary_energy_weight:
    description: >-
      the constrained attribute per unit of energy at the bus — the carrier's
      `co2_emissions` over the generator's efficiency at the snapshot, data prep; a generator
      of an unweighted carrier has no row
    dims: [scenario, global_constraint, snapshot, generator]
    missing: neutral
  Generator_operational_limit_weight:
    description: one where the generator is in the row's set — data prep; one outside it has no row
    dims: [scenario, global_constraint, generator]
    missing: neutral
  Generator_tech_capacity_weight:
    description: >-
      one where the generator is in the row's carrier-and-bus set — data
      prep; one outside it, or one that does not stand in the row's
      `investment_period`, has no row
    dims: [global_constraint, generator]
    missing: neutral

variables:
  Generator_p:
    description: "`Generator-p` — output of a generator in a snapshot"
    dims: [scenario, snapshot, generator]
    where: Generator_active
  Generator_n_mod:
    description: "`Generator-n_mod` — how many modules of an extendable modular build; none for a unit that is not active"
    dims: [generator]
    where: Generator_p_nom_extendable AND Generator_p_nom_mod > 0 AND Generator_active_asset
    domain: integer
    bounds:
      lower: 0
  Generator_status:
    description: >-
      `Generator-status` — how much of a committable unit is on: an integer
      the rows below cap at one, or at the module count where the build is
      modular
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    domain: integer
    bounds:
      lower: 0
  Generator_start_up:
    description: "`Generator-start_up` — how much of a committable unit turns on this snapshot, capped as the status is"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    domain: integer
    bounds:
      lower: 0
  Generator_shut_down:
    description: "`Generator-shut_down` — how much of a committable unit turns off this snapshot, capped as the status is"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    domain: integer
    bounds:
      lower: 0
  Generator_maintenance:
    description: >-
      `Generator-maintenance` — whether a maintainable generator is in maintenance:
      continuous, and one exactly where an event covers the snapshot
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_active
    missing: neutral
    bounds:
      lower: 0
      upper: 1
  Generator_maintenance_start:
    description: "`Generator-maintenance_start` — whether a maintenance event starts in this snapshot"
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_active
    missing: neutral
    domain: binary
  Generator_maintenance_capacity:
    description: >-
      `Generator-maintenance_capacity` — the chosen build while in maintenance, zero
      otherwise: the product the `maintcap` rows linearize
    dims: [scenario, snapshot, generator]
    where: Generator_maint_ext
    missing: neutral
    bounds:
      lower: 0
  Generator_maintenance_status:
    description: >-
      `Generator-maintenance_status` — the status while in maintenance, zero
      otherwise: the product the `maint-status` rows linearize, so a unit in
      maintenance may also be off
    dims: [scenario, snapshot, generator]
    where: >-
      Generator_maintainable
      AND Generator_committed
      AND NOT (Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0))
    missing: neutral
    bounds:
      lower: 0
  Generator_p_nom_ext:
    description: >-
      `Generator-p_nom` — nominal power where it is a decision, for a
      generator that is active; the parameter of the same PyPSA name carries
      the fixed regime
    dims: [generator]
    where: Generator_p_nom_extendable AND Generator_active_asset

expressions:
  Generator_previous_status:
    description: >-
      the commitment state a generator carries into a snapshot — off at the
      first snapshot it stands in past the first of the horizon, as PyPSA
      reads a status it did not build (`constraints.py:298`), and the state
      carried over otherwise
    dims: [scenario, snapshot, generator]
    cases:
      opening_late: { when: "position(snapshot) > 0 AND NOT shift(Generator_active, along=snapshot, offset=1)", expression: 0 }
    otherwise: Generator_status_carried_over
  Generator_status_carried_over:
    description: >-
      the state a generator carries over into a snapshot — the state it brought
      into the horizon at the first, the previous snapshot's after that
    dims: [scenario, snapshot, generator]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Generator_status_initial }
    otherwise: shift(Generator_status, along=snapshot, offset=1)
  Generator_previous_p:
    description: >-
      the output a generator carries into a snapshot — at the first, the
      `p_init` it brought in where it came in running and nothing where it
      came in off; the previous snapshot's after that
    dims: [scenario, snapshot, generator]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Generator_status_initial * Generator_p_init }
    otherwise: shift(Generator_p, along=snapshot, offset=1)
  Generator_p_nom_effective:
    description: the build a generator's limits are taken against — the chosen one where it is extendable, the given one otherwise
    dims: [scenario, generator]
    cases:
      extendable: { when: Generator_p_nom_extendable, expression: Generator_p_nom_ext }
    otherwise: Generator_p_nom
  Generator_ramp_up_rate:
    description: >-
      the ramp limit a unit's up row reads — PyPSA's `ramp_limit_up`, or the
      full build where it has none, since a start-up ramp alone builds the row
    dims: [scenario, snapshot, generator]
    cases:
      given: { when: Generator_ramp_limit_up, expression: Generator_ramp_limit_up }
    otherwise: 1
  Generator_ramp_down_rate:
    description: >-
      the ramp limit a unit's down row reads — PyPSA's `ramp_limit_down`, or
      the full build where it has none, since a shut-down ramp alone builds the row
    dims: [scenario, snapshot, generator]
    cases:
      given: { when: Generator_ramp_limit_down, expression: Generator_ramp_limit_down }
    otherwise: 1
  Generator_start_up_rate:
    description: >-
      the start-up ramp a unit's up row reads — PyPSA's `ramp_limit_start_up`,
      or the full build where it has none
    dims: [scenario, generator]
    cases:
      given: { when: Generator_ramp_limit_start_up, expression: Generator_ramp_limit_start_up }
    otherwise: 1
  Generator_shut_down_rate:
    description: >-
      the shut-down ramp a unit's down row reads — PyPSA's
      `ramp_limit_shut_down`, or the full build where it has none
    dims: [scenario, generator]
    cases:
      given: { when: Generator_ramp_limit_shut_down, expression: Generator_ramp_limit_shut_down }
    otherwise: 1
  Generator_p_nom_committed:
    description: >-
      the build a committed unit's ramp rows are taken against — one module
      where the build is extendable and modular, the given build otherwise
    dims: [scenario, generator]
    cases:
      modular_build: { when: Generator_p_nom_extendable AND Generator_p_nom_mod > 0, expression: Generator_p_nom_mod }
    otherwise: Generator_p_nom
  Generator_ramp_up_allowance:
    description: >-
      how far a generator may raise output between two snapshots — its ramp
      limit of the build while it stays on, plus its start-up ramp in the
      snapshot it turns on
    dims: [scenario, snapshot, generator]
    cases:
      committed:
        when: Generator_committable
        expression: >-
          Generator_ramp_up_rate * Generator_p_nom_committed * Generator_previous_status
          + Generator_start_up_rate * Generator_p_nom_committed
          * (Generator_status - Generator_previous_status)
    otherwise: Generator_ramp_up_rate * Generator_p_nom_effective
  Generator_ramp_down_allowance:
    description: >-
      how far a generator may lower output between two snapshots — its ramp
      limit of the build while it stays on, plus its shut-down ramp in the
      snapshot it turns off
    dims: [scenario, snapshot, generator]
    cases:
      committed:
        when: Generator_committable
        expression: >-
          Generator_ramp_down_rate * Generator_p_nom_committed * Generator_status
          + Generator_shut_down_rate * Generator_p_nom_committed
          * (Generator_previous_status - Generator_status)
    otherwise: Generator_ramp_down_rate * Generator_p_nom_effective
  Generator_primary_energy:
    expression: >-
      sum(sum((Generator_p * GlobalConstraint_energy_weight) * Generator_primary_energy_weight, over=snapshot), over=generator)
    adds_to: primary_energy
  Generator_operational_limit:
    expression: >-
      sum(sum((Generator_p * GlobalConstraint_energy_weight) * Generator_operational_limit_weight, over=snapshot), over=generator)
    adds_to: operational_limit
  Generator_tech_capacity_expansion:
    expression: sum(Generator_p_nom_ext * Generator_tech_capacity_weight, over=generator)
    adds_to: tech_capacity_expansion
  Generator_opex:
    expression: >-
      sum(sum(((Generator_p * Generator_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
      + sum(sum((((Generator_p * Generator_p) * Generator_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
    adds_to: scenario_opex
  Generator_commitment_opex:
    expression: >-
      sum(sum(((Generator_status * Generator_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
      + sum(sum(Generator_start_up * Generator_start_up_cost, over=generator), over=snapshot)
      + sum(sum(Generator_shut_down * Generator_shut_down_cost, over=generator), over=snapshot)
    adds_to: scenario_opex
  Generator_capex:
    expression: sum(scenario_weight * Generator_p_nom_ext * Generator_capital_cost * Generator_capital_weight)
    adds_to: total_cost
  Generator_additions:
    expression: >-
      sum(Generator_p_nom_ext * Generator_first_active, over=generator, by=Generator_carrier[carrier])
    adds_to: Carrier_additions
  Generator_injection:
    expression: sum(Generator_sign * Generator_p, over=generator, by=Generator_bus[bus])
    adds_to: Bus_injection

masks:
  Generator_com_ext:
    description: >-
      a committable generator with an extendable, non-modular build that
      stands in the snapshot's period — PyPSA's `com-ext` rows, whose status
      is relaxed against the chosen build
    where: >-
      Generator_committable
      AND Generator_p_nom_extendable
      AND NOT (Generator_p_nom_mod > 0)
      AND Generator_active
  Generator_maint_ext:
    description: >-
      a maintainable generator with an extendable build, unless it is
      committable and modular, that stands in the snapshot's period — the
      maintenance rows against the chosen build
    where: >-
      Generator_maintainable
      AND Generator_p_nom_extendable
      AND NOT (Generator_committable AND Generator_p_nom_mod > 0)
      AND Generator_active
  Generator_committed:
    description: >-
      a committable generator that stands in the snapshot's period — every
      unit-commitment row's set
    where: Generator_committable AND Generator_active
  Generator_ramps_from_previous:
    description: >-
      a snapshot whose ramp reads a previous output — any snapshot but its
      period's first, and the horizon's first where the generator comes in off
      or carries an initial output
    where: >-
      position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
      (Generator_status_initial == 0 OR Generator_p_init))

constraints:
  Generator_fix_p_lower:
    description: "`Generator-fix-p-lower` — a fixed generator outputs at least its minimum"
    dims: [scenario, snapshot, generator]
    where: not Generator_p_nom_extendable AND not Generator_committable AND Generator_active
    expression: Generator_p >= Generator_p_min_pu * Generator_p_nom * (1 - Generator_maintenance_pu * Generator_maintenance)
  Generator_fix_p_upper:
    description: "`Generator-fix-p-upper` — a fixed generator outputs at most what is available"
    dims: [scenario, snapshot, generator]
    where: not Generator_p_nom_extendable AND not Generator_committable AND Generator_active
    expression: Generator_p <= Generator_p_max_pu * Generator_p_nom * (1 - Generator_maintenance_pu * Generator_maintenance)
  Generator_ext_p_lower:
    description: "`Generator-ext-p-lower` — an extendable generator outputs at least its minimum of the chosen build"
    dims: [scenario, snapshot, generator]
    where: Generator_p_nom_extendable AND not Generator_committable AND Generator_active
    expression: Generator_p >= Generator_p_min_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
  Generator_ext_p_upper:
    description: "`Generator-ext-p-upper` — an extendable generator outputs at most what is available of the chosen build"
    dims: [scenario, snapshot, generator]
    where: Generator_p_nom_extendable AND not Generator_committable AND Generator_active
    expression: Generator_p <= Generator_p_max_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
  Generator_ext_p_nom_lower:
    description: "`Generator-ext-p_nom-lower` — the chosen build is at least its floor in every scenario"
    dims: [scenario, generator]
    where: Generator_p_nom_extendable AND Generator_active_asset
    expression: Generator_p_nom_ext >= Generator_p_nom_min
  Generator_ext_p_nom_upper:
    description: "`Generator-ext-p_nom-upper` — the chosen build is at most its cap in every scenario; a cap of infinity is no row"
    dims: [scenario, generator]
    where: Generator_p_nom_extendable AND Generator_active_asset AND Generator_p_nom_max
    expression: Generator_p_nom_ext <= Generator_p_nom_max
  Generator_p_nom_set:
    description: "`Generator-p_nom_set` — the chosen build pinned, wherever a value is given"
    dims: [generator]
    where: Generator_p_nom_extendable AND Generator_active_asset AND Generator_p_nom_set
    expression: Generator_p_nom_ext == Generator_p_nom_set
  Generator_e_sum_min:
    description: "`Generator-e_sum_min` — energy over the horizon is at least its floor; a floor of minus infinity is no row"
    dims: [scenario, generator]
    where: Generator_e_sum_min
    expression: sum(Generator_p * snapshot_weightings_generators, over=snapshot) >= Generator_e_sum_min
  Generator_e_sum_max:
    description: "`Generator-e_sum_max` — energy over the horizon is at most its budget; a budget of infinity is no row"
    dims: [scenario, generator]
    where: Generator_e_sum_max
    expression: sum(Generator_p * snapshot_weightings_generators, over=snapshot) <= Generator_e_sum_max
  Generator_com_p_lower:
    description: "`Generator-com-p-lower` — a committed unit outputs at least its minimum; off, at least nothing"
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
    expression: Generator_p >= Generator_p_min_pu * Generator_p_nom * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
  Generator_com_p_upper:
    description: "`Generator-com-p-upper` — a committed unit outputs at most what is available; off, at most nothing"
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
    expression: Generator_p <= Generator_p_max_pu * Generator_p_nom * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
  Generator_com_transition_start_up:
    description: "`Generator-com-transition-start-up` — turning on is a start, counted against the state the unit carried into the snapshot"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    expression: Generator_start_up >= Generator_status - Generator_previous_status
  Generator_com_transition_shut_down:
    description: "`Generator-com-transition-shut-down` — turning off is a stop, counted against the state the unit carried into the snapshot"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    expression: Generator_shut_down >= Generator_previous_status - Generator_status
  Generator_com_up_time:
    description: >-
      `Generator-com-up-time` — a unit started within its own minimum up time
      is still on. The first snapshot's share of the window is the brought-in
      up time's, which the must-stay-up mask carries
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_min_up_time > 0 AND position(snapshot) > 0
    expression: sum_back(Generator_start_up, along=snapshot, window=Generator_min_up_time) <= Generator_status
  Generator_com_down_time:
    description: >-
      `Generator-com-down-time` — a unit stopped within its own minimum down
      time is still off. The first snapshot's share of the window is the
      brought-in down time's, which the must-stay-down mask carries
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_min_down_time > 0 AND position(snapshot) > 0
    expression: sum_back(Generator_shut_down, along=snapshot, window=Generator_min_down_time) <= 1 - Generator_status
  Generator_com_status_must_stay_up:
    description: "`Generator-com-status-min_up_time_must_stay_up` — a unit still serving the up time it brought in stays on"
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_must_stay_up
    expression: Generator_status == 1
  Generator_com_status_must_stay_down:
    description: >-
      `Generator-com-status-min_down_time_must_stay_up` — a unit still serving
      the down time it brought in stays off; PyPSA names the row `_must_stay_up`
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_must_stay_down
    expression: Generator_status == 0
  Generator_p_ramp_limit_up_run_big_m:
    description: >-
      `Generator-p-ramp_limit_up-run-bigM` — a committed extendable unit
      raises output no faster than its limit of the chosen build; the big M
      releases the row in the snapshot it turns on
    dims: [scenario, snapshot, generator]
    where: >-
      Generator_com_ext
      AND (Generator_ramp_limit_up OR Generator_ramp_limit_start_up)
      AND Generator_ramps_from_previous
    expression: >-
      Generator_p - Generator_previous_p <=
      Generator_ramp_up_rate * Generator_p_nom_ext
      + Generator_big_m - Generator_big_m * Generator_previous_status
  Generator_p_ramp_limit_up_start_big_m:
    description: >-
      `Generator-p-ramp_limit_up-start-bigM` — in the snapshot it turns on, a
      committed extendable unit ramps no further than its start-up ramp of
      the chosen build; the big M releases the row everywhere else
    dims: [scenario, snapshot, generator]
    where: >-
      Generator_com_ext
      AND (Generator_ramp_limit_up OR Generator_ramp_limit_start_up)
      AND Generator_ramps_from_previous
    expression: >-
      Generator_p - Generator_previous_p <=
      Generator_start_up_rate * Generator_p_nom_ext
      + Generator_big_m - Generator_big_m * Generator_start_up
  Generator_p_ramp_limit_down_run_big_m:
    description: >-
      `Generator-p-ramp_limit_down-run-bigM` — a committed extendable unit
      lowers output no faster than its limit of the chosen build; the big M
      releases the row in the snapshot it turns off
    dims: [scenario, snapshot, generator]
    where: >-
      Generator_com_ext
      AND (Generator_ramp_limit_down OR Generator_ramp_limit_shut_down)
      AND Generator_ramps_from_previous
    expression: >-
      Generator_previous_p - Generator_p <=
      Generator_ramp_down_rate * Generator_p_nom_ext
      + Generator_big_m - Generator_big_m * Generator_status
  Generator_p_ramp_limit_down_shut_big_m:
    description: >-
      `Generator-p-ramp_limit_down-shut-bigM` — in the snapshot it turns off,
      a committed extendable unit ramps no further than its shut-down ramp of
      the chosen build; the big M releases the row everywhere else
    dims: [scenario, snapshot, generator]
    where: >-
      Generator_com_ext
      AND (Generator_ramp_limit_down OR Generator_ramp_limit_shut_down)
      AND Generator_ramps_from_previous
    expression: >-
      Generator_previous_p - Generator_p <=
      Generator_shut_down_rate * Generator_p_nom_ext
      + Generator_big_m - Generator_big_m * Generator_shut_down
  Generator_p_nom_modularity:
    description: "`Generator-p_nom_modularity` — the chosen build is a whole number of modules"
    dims: [generator]
    where: Generator_p_nom_extendable AND Generator_p_nom_mod > 0 AND Generator_active_asset
    expression: Generator_p_nom_ext == Generator_p_nom_mod * Generator_n_mod
  Generator_com_ext_p_upper_cap:
    description: >-
      `Generator-com-ext-p-upper-cap` — a committed extendable unit outputs
      at most what is available of the chosen build, whatever its status
    dims: [scenario, snapshot, generator]
    where: Generator_com_ext
    expression: Generator_p <= Generator_p_max_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
  Generator_com_ext_p_upper_big_m:
    description: "`Generator-com-ext-p-upper-bigM` — off, a unit outputs nothing; on, the big M is no bound"
    dims: [scenario, snapshot, generator]
    where: Generator_com_ext
    expression: Generator_p <= Generator_big_m * Generator_status
  Generator_com_ext_p_lower:
    description: >-
      `Generator-com-ext-p-lower` — a committed extendable unit outputs at
      least its minimum of the chosen build; off, the big M releases the row
    dims: [scenario, snapshot, generator]
    where: Generator_com_ext
    expression: >-
      Generator_p >=
      Generator_p_min_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
      + Generator_big_m * Generator_status - Generator_big_m
  Generator_com_ext_p_lower_nonneg:
    description: >-
      `Generator-com-ext-p-lower-nonneg` — where no minimum-per-unit is
      negative, output is also plainly non-negative, a row the big-M lower
      cannot assert while the unit is off
    dims: [scenario, snapshot, generator]
    where: Generator_com_ext AND Generator_p_min_pu_nonneg
    expression: Generator_p >= 0
  Generator_com_mod_p_lower:
    description: >-
      `Generator-com-mod-p-lower` — a committed modular unit outputs at least
      its minimum of one module, whether the build is fixed or a decision
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_p_nom_mod > 0
    expression: Generator_p >= Generator_p_min_pu * Generator_p_nom_mod * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
  Generator_com_mod_p_upper:
    description: >-
      `Generator-com-mod-p-upper` — a committed modular unit outputs at most
      one module's share, whether the build is fixed or a decision
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_p_nom_mod > 0
    expression: Generator_p <= Generator_p_max_pu * Generator_p_nom_mod * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
  Generator_status_p_fixed_upper:
    description: >-
      `Generator-status-p-fixed-upper` — a status is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND NOT (Generator_p_nom_extendable AND Generator_p_nom_mod > 0)
    expression: Generator_status <= Generator_modules_installed
  Generator_start_up_p_fixed_upper:
    description: >-
      `Generator-start_up-p-fixed-upper` — a start is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND NOT (Generator_p_nom_extendable AND Generator_p_nom_mod > 0)
    expression: Generator_start_up <= Generator_modules_installed
  Generator_shut_down_p_fixed_upper:
    description: >-
      `Generator-shut_down-p-fixed-upper` — a stop is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND NOT (Generator_p_nom_extendable AND Generator_p_nom_mod > 0)
    expression: Generator_shut_down <= Generator_modules_installed
  Generator_status_p_nom_variable_upper:
    description: "`Generator-status-p_nom-variable-upper` — a modular unit is on only where a module is built"
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_p_nom_extendable AND Generator_p_nom_mod > 0
    expression: Generator_status <= Generator_n_mod
  Generator_start_up_p_nom_variable_upper:
    description: "`Generator-start_up-p_nom-variable-upper` — a modular unit starts only where a module is built"
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_p_nom_extendable AND Generator_p_nom_mod > 0
    expression: Generator_start_up <= Generator_n_mod
  Generator_shut_down_p_nom_variable_upper:
    description: "`Generator-shut_down-p_nom-variable-upper` — a modular unit stops only where a module is built"
    dims: [scenario, snapshot, generator]
    where: Generator_committed AND Generator_p_nom_extendable AND Generator_p_nom_mod > 0
    expression: Generator_shut_down <= Generator_n_mod
  Generator_maint_event_count:
    description: "`Generator-maint-event-count` — a maintainable generator holds its number of maintenance events over the horizon"
    dims: [scenario, generator]
    where: Generator_maintainable
    expression: sum(Generator_maintenance_start, over=snapshot) == Generator_maintenance_events
  Generator_maint_window:
    description: >-
      `Generator-maint-window` — a generator is in maintenance exactly where an event it
      started covers the snapshot; two events do not overlap, since the
      maintenance status is at most one
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_active
    expression: Generator_maintenance == sum(Generator_maintenance_start, over=start, by=Generator_maintenance_cover[covered])
  Generator_maint_start_horizon:
    description: "`Generator-maint-start-horizon` — no event starts where it could not run its whole duration"
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_active AND Generator_maintenance_start_blocked
    expression: Generator_maintenance_start == 0
  Generator_maintcap_upper:
    description: >-
      `Generator-maintcap_upper` — the build taken off is at most the chosen build in
      maintenance, and at most the build less its floor out of it
    dims: [scenario, snapshot, generator]
    where: Generator_maint_ext
    expression: Generator_maintenance_capacity <= Generator_p_nom_ext - Generator_p_nom_min * (1 - Generator_maintenance)
  Generator_maintcap_upper_nommax:
    description: "`Generator-maintcap_upper_nommax` — out of maintenance, no build is taken off"
    dims: [scenario, snapshot, generator]
    where: Generator_maint_ext
    expression: Generator_maintenance_capacity <= Generator_p_nom_max * Generator_maintenance
  Generator_maintcap_lower_nommax:
    description: "`Generator-maintcap_lower_nommax` — in maintenance, the whole chosen build is taken off"
    dims: [scenario, snapshot, generator]
    where: Generator_maint_ext
    expression: Generator_maintenance_capacity >= Generator_p_nom_ext - Generator_p_nom_max * (1 - Generator_maintenance)
  Generator_maintcap_lower_nommin:
    description: "`Generator-maintcap_lower_nommin` — in maintenance, at least the floor of the build is taken off"
    dims: [scenario, snapshot, generator]
    where: Generator_maint_ext AND Generator_p_nom_min > 0
    expression: Generator_maintenance_capacity >= Generator_p_nom_min * Generator_maintenance
  Generator_maint_status_le_status:
    description: "`Generator-maint-status-le-status` — the status in maintenance is at most the status"
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
    expression: Generator_maintenance_status <= Generator_status
  Generator_maint_status_le_maint:
    description: "`Generator-maint-status-le-maint` — out of maintenance, the status in maintenance is zero"
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
    expression: Generator_maintenance_status <= Generator_maintenance
  Generator_maint_status_lb:
    description: "`Generator-maint-status-lb` — on and in maintenance, the status in maintenance is one"
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
    expression: Generator_maintenance_status >= Generator_status + Generator_maintenance - 1
  Generator_maint_modstatus_le_status:
    description: "`Generator-maint-modstatus-le-status` — the modules on in maintenance are at most the modules on"
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_committed AND Generator_p_nom_mod > 0
    expression: Generator_maintenance_status <= Generator_status
  Generator_maint_modstatus_le_maint:
    description: >-
      `Generator-maint-modstatus-le-maint` — out of maintenance, no module is on in
      maintenance; in it, at most the modules the build cap holds
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_committed AND Generator_p_nom_mod > 0
    expression: Generator_maintenance_status <= Generator_p_nom_max / Generator_p_nom_mod * Generator_maintenance
  Generator_maint_modstatus_lb:
    description: "`Generator-maint-modstatus-lb` — in maintenance, every module on is on in maintenance"
    dims: [scenario, snapshot, generator]
    where: Generator_maintainable AND Generator_committed AND Generator_p_nom_mod > 0
    expression: Generator_maintenance_status >= Generator_status - Generator_p_nom_max / Generator_p_nom_mod * (1 - Generator_maintenance)
  Generator_p_ramp_limit_up:
    description: >-
      `Generator-p-ramp_limit_up` — a generator raises output no faster than
      its ramp limit of the build, and a committed one no further than its
      start-up ramp in the snapshot it turns on. A unit that came into the
      horizon running carries a row at the first snapshot only where its
      `p_init` gives the output it brought in, and no unit carries one at
      the start of a later investment period — nor does any unit a big M releases instead
    dims: [scenario, snapshot, generator]
    where: >-
      (Generator_ramp_limit_up OR Generator_ramp_limit_start_up)
      AND NOT (Generator_committable AND Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0))
      AND Generator_ramps_from_previous
      AND Generator_active
    expression: Generator_p - Generator_previous_p <= Generator_ramp_up_allowance
  Generator_p_ramp_limit_down:
    description: >-
      `Generator-p-ramp_limit_down` — a generator lowers output no faster than
      its ramp limit of the build, and a committed one no further than its
      shut-down ramp in the snapshot it turns off. A unit that came into the
      horizon running carries a row at the first snapshot only where its
      `p_init` gives the output it brought in, and no unit carries one at
      the start of a later investment period — nor does any unit a big M releases instead
    dims: [scenario, snapshot, generator]
    where: >-
      (Generator_ramp_limit_down OR Generator_ramp_limit_shut_down)
      AND NOT (Generator_committable AND Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0))
      AND Generator_ramps_from_previous
      AND Generator_active
    expression: Generator_previous_p - Generator_p <= Generator_ramp_down_allowance
  Generator_p_set:
    description: "`Generator-p_set` — output pinned to the given schedule, wherever one is given"
    dims: [scenario, snapshot, generator]
    where: Generator_p_set AND Generator_active
    expression: Generator_p == Generator_p_set

assumptions:
  Generator_maintenance_events_positive:
    holds: "Generator_maintenance_events > 0"
    where: "Generator_maintainable"
    description: >-
      a maintainable generator with no event schedules no maintenance —
      PyPSA refuses it (`consistency.py:1493`)
  Generator_maintenance_duration_positive:
    holds: "Generator_maintenance_duration > 0"
    where: "Generator_maintainable"
    description: >-
      an event that covers no hours is no maintenance window — PyPSA
      refuses it (`consistency.py:1483`)
  Generator_maintenance_duration_fits_the_horizon:
    holds: "Generator_maintenance_duration <= sum(snapshot_weightings_generators, over=snapshot)"
    where: "Generator_maintainable"
    description: >-
      one event longer than the horizon, in generator weightings, blocks
      every start and makes the event count infeasible — PyPSA refuses it
      (`consistency.py:1504`)
  Generator_maintenance_events_fit_the_horizon:
    holds: "Generator_maintenance_duration * Generator_maintenance_events <= sum(snapshot_weightings_generators, over=snapshot)"
    where: "Generator_maintainable"
    description: >-
      the events together longer than the horizon, in generator
      weightings, cannot all be scheduled — PyPSA refuses it
      (`consistency.py:1516`)
  Generator_maintenance_build_cap_is_finite:
    holds: "Generator_p_nom_max < inf"
    where: "Generator_maintainable AND Generator_p_nom_extendable"
    description: >-
      the `maintcap` rows hold the chosen build in maintenance against
      `p_nom_max`, so an infinite cap is an infinite coefficient — PyPSA
      refuses it (`consistency.py:1528`)
  Generator_maintenance_module_count_is_finite:
    holds: "Generator_p_nom_max < inf"
    where: "Generator_maintainable AND Generator_committable AND NOT Generator_p_nom_extendable AND Generator_p_nom_mod > 0"
    description: >-
      the `maint-modstatus` rows bound the modules on in maintenance by
      `p_nom_max / p_nom_mod`, so an infinite cap is an infinite
      coefficient. PyPSA does not check it, and HiGHS refuses the model
      (`constraints.py:504-507`)
  Generator_marginal_cost_quadratic_without_risk_preference:
    holds: "Generator_marginal_cost_quadratic == 0"
    where: "CVaR_omega"
    description: >-
      a quadratic cost puts a square into every `CVaR-excess` row, and PyPSA
      refuses quadratic costs under any risk preference
      (`optimize.py:470-477`), `omega = 0` included. Data prep writes a
      `CVaR_omega` row only where a risk preference is set
  Generator_came_in_running_unless_committable:
    holds: "Generator_status_initial == 1"
    where: "NOT Generator_committable AND (Generator_ramp_limit_up OR Generator_ramp_limit_down OR Generator_ramp_limit_start_up OR Generator_ramp_limit_shut_down)"
    description: >-
      PyPSA reads `up_time_before` of a unit that is not committable in its
      ramp rows, which a ramp limit, a start-up ramp or a shut-down ramp
      alone builds (`constraints.py:1018-1019`). Where it is zero, PyPSA
      builds a row at the first snapshot with nothing carried in, and caps
      the unit there at zero, or at its start-up ramp where another unit of
      the component is committable with a fixed build
      (`constraints.py:1063-1066`, `1082-1084`). PyPSA documents
      the attribute as read only for a committable unit and does not check
      it. PyPSA has not decided which row is intended (PyPSA/PyPSA#1943). The
      spec does not state that row, so it refuses the data
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$, data another file declares |
| $`\pi`$ | `scenario_weight` over $`\Xi`$, data another file declares |
| $`\omega`$ | `CVaR_omega` (scalar), data another file declares |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$, data another file declares |
| $`\mathrm{w}^{\mathrm{gen}}`$ | `snapshot_weightings_generators` over $`\mathcal{T}`$, data another file declares |
| $`\mathit{w}^{\mathrm{gc}}`$ | `GlobalConstraint_energy_weight` over $`\Xi \times \mathcal{L} \times \mathcal{T}`$, an expression another file defines |
| $`\mathit{primary\_energy}`$ | `primary_energy` over $`\Xi \times \mathcal{L}`$, an expression this file adds `Generator_primary_energy` to |
| $`\mathit{operational\_limit}`$ | `operational_limit` over $`\Xi \times \mathcal{L}`$, an expression this file adds `Generator_operational_limit` to |
| $`\mathit{tech\_capacity\_expansion}`$ | `tech_capacity_expansion` over $`\mathcal{L}`$, an expression this file adds `Generator_tech_capacity_expansion` to |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Generator_opex`, `Generator_commitment_opex` to |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `Generator_capex` to |
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{Y} \times \mathcal{I}`$, an expression this file adds `Generator_additions` to |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$, an expression this file adds `Generator_injection` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` with $`\mathrm{Generator\_maintenance\_cover} \subseteq \Xi \times \mathcal{G} \times \mathcal{T} \times \mathcal{T}`$, `Generator_maintenance_cover` is `absent` where the data has no row — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y},\ \mathrm{Generator\_maintenance\_cover} \subseteq \Xi \times \mathcal{G} \times \mathcal{T} \times \mathcal{T}`$, `Generator_maintenance_cover` is `absent` where the data has no row — dispatch periods |
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Generator\_bus}: \mathcal{G} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_carrier}: \mathcal{G} \to \mathcal{I},\ \mathrm{Generator\_bus}: \mathcal{G} \to \mathcal{N},\ \mathrm{Generator\_maintenance\_cover} \subseteq \Xi \times \mathcal{G} \times \mathcal{T} \times \mathcal{T}`$, `Generator_maintenance_cover` is `absent` where the data has no row — generating units, each on one bus |
| $`\mathcal{L}`$ | index $`l`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods — PyPSA's `investment_periods` |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` with $`\mathrm{Generator\_carrier}: \mathcal{G} \to \mathcal{I}`$ — energy carriers, what a growth limit is set per |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\Xi \times \mathcal{G}`$ — nominal power |
| $`\mathrm{ext}`$ | `Generator_p_nom_extendable` over $`\mathcal{G}`$ — whether the nominal power is a decision |
| $`\underline{\mathrm{p}}`$ | `Generator_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — least output, per unit of nominal power |
| $`\overline{\mathrm{p}}`$ | `Generator_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — most output, per unit of nominal power — an availability profile |
| $`\mathrm{c}`$ | `Generator_marginal_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of one unit of output |
| $`\mathrm{c}^{(2)}`$ | `Generator_marginal_cost_quadratic` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of the square of one unit of output |
| $`\mathrm{sgn}`$ | `Generator_sign` over $`\mathcal{G}`$ — the sign output enters its bus's balance with — PyPSA's `sign`, `1` unless given, `-1` for a unit that draws power. PyPSA refuses one that differs by scenario (`constants.py:43`) |
| $`\mathrm{com}`$ | `Generator_committable` over $`\mathcal{G}`$ — whether output is gated by an on/off status decision |
| $`\mathrm{ru}`$ | `Generator_ramp_limit_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the data has no row — most a generator may raise its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time |
| $`\mathrm{rd}`$ | `Generator_ramp_limit_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the data has no row — most a generator may lower its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time |
| $`\mathrm{ru}^{\mathrm{up}}`$ | `Generator_ramp_limit_start_up` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — most output in the snapshot a unit starts, per unit of nominal power; no value means no limit |
| $`\mathrm{rd}^{\mathrm{dn}}`$ | `Generator_ramp_limit_shut_down` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — most output in the snapshot before a unit stops, per unit of nominal power; no value means no limit |
| $`\mathrm{UT}`$ | `Generator_min_up_time` over $`\Xi \times \mathcal{G}`$ — least snapshots a unit stays on once started |
| $`\mathrm{DT}`$ | `Generator_min_down_time` over $`\Xi \times \mathcal{G}`$ — least snapshots a unit stays off once stopped |
| $`\mathrm{u}^{0}`$ | `Generator_status_initial` over $`\Xi \times \mathcal{G}`$ — one where the unit was on before the first snapshot, zero where off — PyPSA's `up_time_before > 0`, data prep |
| $`\mathrm{p}^{0}`$ | `Generator_p_init` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — the output a unit brought into the horizon — PyPSA's `p_init`, read only where the unit came in running; no value means it is unknown, so the unit carries no ramp row at the first snapshot |
| $`\mathrm{hold}`$ | `Generator_must_stay_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — true while the up time a unit brought into the horizon still binds — data prep, since `position()` compares against a literal rather than a parameter |
| $`\mathrm{rest}`$ | `Generator_must_stay_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — true while the down time a unit brought into the horizon still binds — PyPSA's `min_down_time - down_time_before` snapshots, where `down_time_before > 0`, data prep for the same reason |
| $`\mathrm{c}^{\mathrm{up}}`$ | `Generator_start_up_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of one start in this snapshot |
| $`\mathrm{c}^{\mathrm{dn}}`$ | `Generator_shut_down_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of one stop in this snapshot |
| $`\mathrm{c}^{\mathrm{on}}`$ | `Generator_stand_by_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of one snapshot spent on |
| $`\mathrm{p}^{\mathrm{mod}}`$ | `Generator_p_nom_mod` over $`\mathcal{G}`$, `neutral` where the data has no row — the module size a build comes in whole numbers of; no value means the build is continuous |
| $`\mathrm{N}^{\mathrm{fix}}`$ | `Generator_modules_installed` over $`\Xi \times \mathcal{G}`$ — how many whole modules a committable build has in place: `Generator_p_nom / Generator_p_nom_mod` where a fixed build is modular, one where it is not, data prep. PyPSA refuses a fixed modular build whose nominal power is not a whole number of modules |
| $`\mathrm{M}`$ | `Generator_big_m` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — the bound a committed extendable generator's big-M rows release it by — the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu`, and where that keyword is not given, ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`, or 1e6 where there is none of them (`components.py:1050-1121`). Below the output a solve wants, it caps that output; data prep |
| $`\mathrm{nonneg}`$ | `Generator_p_min_pu_nonneg` over $`\mathcal{G}`$ — true where none of the generator's own minimums-per-unit is negative — PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep |
| $`\mathrm{mnt}`$ | `Generator_maintainable` over $`\mathcal{G}`$ — whether a generator must be taken off for maintenance within the horizon — in any scenario, as PyPSA takes the union over them (`components.py:1016-1019`) |
| $`\gamma`$ | `Generator_maintenance_pu` over $`\Xi \times \mathcal{G}`$ — the share of the build a maintenance event takes off |
| $`\mathrm{n}^{\mathrm{mnt}}`$ | `Generator_maintenance_events` over $`\Xi \times \mathcal{G}`$ — how many maintenance events the horizon holds |
| $`\tau^{\mathrm{mnt}}`$ | `Generator_maintenance_duration` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — the hours of generator weightings one maintenance event covers — PyPSA's `maintenance_duration`; no value where the generator is not maintainable. No row reads it: data prep turns it into `Generator_maintenance_cover` and `Generator_maintenance_start_blocked`, and the assumptions hold it to the horizon |
| $`\mathrm{blk}`$ | `Generator_maintenance_start_blocked` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — true where no maintenance event may start, because the snapshots it would cover run past the end of the horizon or into one the generator does not stand in — PyPSA's `active & ~valid`, from `maintenance_duration` and the generator weightings, data prep |
| $`\mathrm{on}`$ | `Generator_active` over $`\mathcal{T} \times \mathcal{G}`$ — whether a generator stands in a snapshot's period — PyPSA's `active`, from build year and lifetime, data prep |
| $`\mathrm{act}`$ | `Generator_active_asset` over $`\mathcal{G}`$ — whether a generator is one of PyPSA's `active_assets` — its `active` flag alone, without build year and lifetime, so a unit that stands in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:51`) |
| $`\mathrm{W}`$ | `Generator_capital_weight` over $`\mathcal{G}`$ — the sum of period weights a generator stands in — PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{new}`$ | `Generator_first_active` over $`\mathcal{Y} \times \mathcal{G}`$ — one in the first period a generator stands in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`) |
| $`\mathrm{p}^{\mathrm{set}}`$ | `Generator_p_set` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the data has no row — a given output schedule; a generator without one has no row here |
| $`\underline{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_min` over $`\Xi \times \mathcal{G}`$ — least nominal power an extendable generator may be built at |
| $`\overline{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_max` over $`\Xi \times \mathcal{G}`$ — most nominal power an extendable generator may be built at |
| $`\mathrm{c}^{\mathrm{cap}}`$ | `Generator_capital_cost` over $`\Xi \times \mathcal{G}`$ — cost of one unit of nominal power for the modelled horizon — PyPSA's `periodized_cost`: `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where it is given, and `capital_cost` where it is not, plus `fom_cost` (`components.py:1126-1147`, `costs.py:102-203`), data prep |
| $`\mathrm{p}^{\mathrm{nom,set}}`$ | `Generator_p_nom_set` over $`\mathcal{G}`$, `neutral` where the data has no row — a given nominal power for an extendable generator; one without a value has no row here |
| $`\underline{\mathrm{E}}`$ | `Generator_e_sum_min` over $`\Xi \times \mathcal{G}`$ — least energy over the horizon; minus infinity where no floor is meant |
| $`\overline{\mathrm{E}}`$ | `Generator_e_sum_max` over $`\Xi \times \mathcal{G}`$ — most energy over the horizon — a fuel or emission budget in energy terms; infinity where no cap is meant |
| $`\mathrm{a}`$ | `Generator_primary_energy_weight` over $`\Xi \times \mathcal{L} \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the data has no row — the constrained attribute per unit of energy at the bus — the carrier's `co2_emissions` over the generator's efficiency at the snapshot, data prep; a generator of an unweighted carrier has no row |
| $`\mathrm{b}`$ | `Generator_operational_limit_weight` over $`\Xi \times \mathcal{L} \times \mathcal{G}`$, `neutral` where the data has no row — one where the generator is in the row's set — data prep; one outside it has no row |
| $`\mathrm{m}`$ | `Generator_tech_capacity_weight` over $`\mathcal{L} \times \mathcal{G}`$, `neutral` where the data has no row — one where the generator is in the row's carrier-and-bus set — data prep; one outside it, or one that does not stand in the row's `investment_period`, has no row |

#### Masks

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{\mathrm{com,ext}}`$ | `Generator_com_ext` over $`\mathcal{T} \times \mathcal{G}`$ — a committable generator with an extendable, non-modular build that stands in the snapshot's period — PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |
| $`\mathrm{on}^{\mathrm{mnt,ext}}`$ | `Generator_maint_ext` over $`\mathcal{T} \times \mathcal{G}`$ — a maintainable generator with an extendable build, unless it is committable and modular, that stands in the snapshot's period — the maintenance rows against the chosen build |
| $`\mathrm{on}^{\mathrm{com}}`$ | `Generator_committed` over $`\mathcal{T} \times \mathcal{G}`$ — a committable generator that stands in the snapshot's period — every unit-commitment row's set |
| $`\mathrm{prev}`$ | `Generator_ramps_from_previous` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — a snapshot whose ramp reads a previous output — any snapshot but its period's first, and the horizon's first where the generator comes in off or carries an initial output |

#### Variables

| Symbol | Meaning |
|---|---|
| $`p`$ | `Generator_p` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-p` — output of a generator in a snapshot |
| $`N`$ | `Generator_n_mod` over $`\mathcal{G}`$ — `Generator-n_mod` — how many modules of an extendable modular build; none for a unit that is not active |
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-status` — how much of a committable unit is on: an integer the rows below cap at one, or at the module count where the build is modular |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-start_up` — how much of a committable unit turns on this snapshot, capped as the status is |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-shut_down` — how much of a committable unit turns off this snapshot, capped as the status is |
| $`\mu`$ | `Generator_maintenance` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the mask leaves it out — `Generator-maintenance` — whether a maintainable generator is in maintenance: continuous, and one exactly where an event covers the snapshot |
| $`\mu^{\mathrm{up}}`$ | `Generator_maintenance_start` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the mask leaves it out — `Generator-maintenance_start` — whether a maintenance event starts in this snapshot |
| $`\mu^{\mathrm{nom}}`$ | `Generator_maintenance_capacity` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the mask leaves it out — `Generator-maintenance_capacity` — the chosen build while in maintenance, zero otherwise: the product the `maintcap` rows linearize |
| $`\mu^{u}`$ | `Generator_maintenance_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the mask leaves it out — `Generator-maintenance_status` — the status while in maintenance, zero otherwise: the product the `maint-status` rows linearize, so a unit in maintenance may also be off |
| $`P`$ | `Generator_p_nom_ext` over $`\mathcal{G}`$ — `Generator-p_nom` — nominal power where it is a decision, for a generator that is active; the parameter of the same PyPSA name carries the fixed regime |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{u}`$ | `Generator_previous_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the commitment state a generator carries into a snapshot — off at the first snapshot it stands in past the first of the horizon, as PyPSA reads a status it did not build (`constraints.py:298`), and the state carried over otherwise |
| $`\overleftarrow{u}^{\circ}`$ | `Generator_status_carried_over` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the state a generator carries over into a snapshot — the state it brought into the horizon at the first, the previous snapshot's after that |
| $`\overleftarrow{p}`$ | `Generator_previous_p` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the output a generator carries into a snapshot — at the first, the `p_init` it brought in where it came in running and nothing where it came in off; the previous snapshot's after that |
| $`\widetilde{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_effective` over $`\Xi \times \mathcal{G}`$ — the build a generator's limits are taken against — the chosen one where it is extendable, the given one otherwise |
| $`\widetilde{\mathrm{ru}}`$ | `Generator_ramp_up_rate` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the ramp limit a unit's up row reads — PyPSA's `ramp_limit_up`, or the full build where it has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}`$ | `Generator_ramp_down_rate` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the ramp limit a unit's down row reads — PyPSA's `ramp_limit_down`, or the full build where it has none, since a shut-down ramp alone builds the row |
| $`\widetilde{\mathrm{ru}}^{\mathrm{up}}`$ | `Generator_start_up_rate` over $`\Xi \times \mathcal{G}`$ — the start-up ramp a unit's up row reads — PyPSA's `ramp_limit_start_up`, or the full build where it has none |
| $`\widetilde{\mathrm{rd}}^{\mathrm{dn}}`$ | `Generator_shut_down_rate` over $`\Xi \times \mathcal{G}`$ — the shut-down ramp a unit's down row reads — PyPSA's `ramp_limit_shut_down`, or the full build where it has none |
| $`\widehat{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_committed` over $`\Xi \times \mathcal{G}`$ — the build a committed unit's ramp rows are taken against — one module where the build is extendable and modular, the given build otherwise |
| $`\Delta^{+}`$ | `Generator_ramp_up_allowance` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how far a generator may raise output between two snapshots — its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\Delta^{-}`$ | `Generator_ramp_down_allowance` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how far a generator may lower output between two snapshots — its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\mathit{Generator\_primary\_energy}`$ | `Generator_primary_energy` over $`\Xi \times \mathcal{L}`$ |
| $`\mathit{Generator\_operational\_limit}`$ | `Generator_operational_limit` over $`\Xi \times \mathcal{L}`$ |
| $`\mathit{Generator\_tech\_capacity\_expansion}`$ | `Generator_tech_capacity_expansion` over $`\mathcal{L}`$ |
| $`\mathit{Generator\_opex}`$ | `Generator_opex` over $`\Xi`$ |
| $`\mathit{Generator\_commitment\_opex}`$ | `Generator_commitment_opex` over $`\Xi`$ |
| $`\mathit{Generator\_capex}`$ | `Generator_capex` (scalar) |
| $`\mathit{Generator\_additions}`$ | `Generator_additions` over $`\mathcal{Y} \times \mathcal{I}`$ |
| $`\mathit{Generator\_injection}`$ | `Generator_injection` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$ |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |

#### Masks

**`Generator_com_ext`**

```math
\mathrm{on}^{\mathrm{com,ext}}_{t,g} \iff \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \wedge \mathrm{on}_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_maint_ext`**

```math
\mathrm{on}^{\mathrm{mnt,ext}}_{t,g} \iff \mathrm{mnt}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \wedge \mathrm{on}_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_committed`**

```math
\mathrm{on}^{\mathrm{com}}_{t,g} \iff \mathrm{com}_{g} \wedge \mathrm{on}_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_ramps_from_previous`**

```math
\mathrm{prev}_{\xi,t,g} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{0}_{\xi,g} = 0 \vee \mathrm{p}^{0}_{\xi,g} \text{ is defined} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Variable domains

**`Generator_p`**

```math
p_{\xi,t,g} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}_{t,g}
```

**`Generator_n_mod`**

```math
N_{g} \ge 0, N_{g} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \wedge \mathrm{act}_{g}
```

**`Generator_status`**

```math
u_{\xi,t,g} \ge 0, u_{\xi,t,g} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_start_up`**

```math
\mathit{up}_{\xi,t,g} \ge 0, \mathit{up}_{\xi,t,g} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_shut_down`**

```math
\mathit{dn}_{\xi,t,g} \ge 0, \mathit{dn}_{\xi,t,g} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_maintenance`**

```math
0 \le \mu_{\xi,t,g} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{t,g}
```

**`Generator_maintenance_start`**

```math
\mu^{\mathrm{up}}_{\xi,t,g} \in \{0, 1\} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{t,g}
```

**`Generator_maintenance_capacity`**

```math
\mu^{\mathrm{nom}}_{\xi,t,g} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{t,g}
```

**`Generator_maintenance_status`**

```math
\mu^{u}_{\xi,t,g} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \left( \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right)
```

**`Generator_p_nom_ext`**

```math
P_{g} \in \mathbb{R} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g}
```

#### Definitions

**`Generator_previous_status`**

```math
\overleftarrow{u}_{\xi,t,g} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}_{t - 1,g} \\ \overleftarrow{u}^{\circ}_{\xi,t,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_status_carried_over`**

```math
\overleftarrow{u}^{\circ}_{\xi,t,g} = \begin{cases} \mathrm{u}^{0}_{\xi,g} & \text{if } \mathrm{pos}(t) = 0 \\ u_{\xi,t - 1,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_previous_p`**

```math
\overleftarrow{p}_{\xi,t,g} = \begin{cases} \mathrm{u}^{0}_{\xi,g} \cdot \mathrm{p}^{0}_{\xi,g} & \text{if } \mathrm{pos}(t) = 0 \\ p_{\xi,t - 1,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_p_nom_effective`**

```math
\widetilde{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} = \begin{cases} P_{g} & \text{if } \mathrm{ext}_{g} \\ \mathrm{p}^{\mathrm{nom}}_{\xi,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G}
```

**`Generator_ramp_up_rate`**

```math
\widetilde{\mathrm{ru}}_{\xi,t,g} = \begin{cases} \mathrm{ru}_{\xi,t,g} & \text{if } \mathrm{ru}_{\xi,t,g} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_ramp_down_rate`**

```math
\widetilde{\mathrm{rd}}_{\xi,t,g} = \begin{cases} \mathrm{rd}_{\xi,t,g} & \text{if } \mathrm{rd}_{\xi,t,g} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_start_up_rate`**

```math
\widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} = \begin{cases} \mathrm{ru}^{\mathrm{up}}_{\xi,g} & \text{if } \mathrm{ru}^{\mathrm{up}}_{\xi,g} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G}
```

**`Generator_shut_down_rate`**

```math
\widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} = \begin{cases} \mathrm{rd}^{\mathrm{dn}}_{\xi,g} & \text{if } \mathrm{rd}^{\mathrm{dn}}_{\xi,g} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G}
```

**`Generator_p_nom_committed`**

```math
\widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} = \begin{cases} \mathrm{p}^{\mathrm{mod}}_{g} & \text{if } \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \\ \mathrm{p}^{\mathrm{nom}}_{\xi,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G}
```

**`Generator_ramp_up_allowance`**

```math
\Delta^{+}_{\xi,t,g} = \begin{cases} \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \overleftarrow{u}_{\xi,t,g} + \widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \left( u_{\xi,t,g} - \overleftarrow{u}_{\xi,t,g} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_ramp_down_allowance`**

```math
\Delta^{-}_{\xi,t,g} = \begin{cases} \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t,g} + \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \left( \overleftarrow{u}_{\xi,t,g} - u_{\xi,t,g} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_primary_energy`**

```math
\mathit{Generator\_primary\_energy}_{\xi,l} = \sum_{g \in \mathcal{G}} \sum_{t \in \mathcal{T}} p_{\xi,t,g} \cdot \mathit{w}^{\mathrm{gc}}_{\xi,l,t} \cdot \mathrm{a}_{\xi,l,t,g} \qquad \forall\, \xi \in \Xi,\ l \in \mathcal{L}
```

**`Generator_operational_limit`**

```math
\mathit{Generator\_operational\_limit}_{\xi,l} = \sum_{g \in \mathcal{G}} \sum_{t \in \mathcal{T}} p_{\xi,t,g} \cdot \mathit{w}^{\mathrm{gc}}_{\xi,l,t} \cdot \mathrm{b}_{\xi,l,g} \qquad \forall\, \xi \in \Xi,\ l \in \mathcal{L}
```

**`Generator_tech_capacity_expansion`**

```math
\mathit{Generator\_tech\_capacity\_expansion}_{l} = \sum_{g \in \mathcal{G}} P_{g} \cdot \mathrm{m}_{l,g} \qquad \forall\, l \in \mathcal{L}
```

**`Generator_opex`**

```math
\mathit{Generator\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} p_{\xi,t,g} \cdot \mathrm{c}_{\xi,t,g} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} p_{\xi,t,g} \cdot p_{\xi,t,g} \cdot \mathrm{c}^{(2)}_{\xi,t,g} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

**`Generator_commitment_opex`**

```math
\mathit{Generator\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} u_{\xi,t,g} \cdot \mathrm{c}^{\mathrm{on}}_{\xi,t,g} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} \mathit{up}_{\xi,t,g} \cdot \mathrm{c}^{\mathrm{up}}_{\xi,t,g} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} \mathit{dn}_{\xi,t,g} \cdot \mathrm{c}^{\mathrm{dn}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi
```

**`Generator_capex`**

```math
\mathit{Generator\_capex} = \sum_{\xi \in \Xi,\ g \in \mathcal{G}} \pi_{\xi} \cdot P_{g} \cdot \mathrm{c}^{\mathrm{cap}}_{\xi,g} \cdot \mathrm{W}_{g}
```

**`Generator_additions`**

```math
\mathit{Generator\_additions}_{y,i} = \sum_{g \in \mathcal{G} \,:\, \mathrm{Generator\_carrier}(g) = i} P_{g} \cdot \mathrm{new}_{y,g} \qquad \forall\, y \in \mathcal{Y},\ i \in \mathcal{I}
```

**`Generator_injection`**

```math
\mathit{Generator\_injection}_{\xi,t,n} = \sum_{g \in \mathcal{G} \,:\, \mathrm{Generator\_bus}(g) = n} \mathrm{sgn}_{g} \cdot p_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ n \in \mathcal{N}
```

#### Subject to

**`Generator_fix_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot \left( 1 - \gamma_{\xi,g} \cdot \mu_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \neg \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{t,g}
```

**`Generator_fix_p_upper`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot \left( 1 - \gamma_{\xi,g} \cdot \mu_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \neg \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{t,g}
```

**`Generator_ext_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \left( P_{g} - \gamma_{\xi,g} \cdot \mu^{\mathrm{nom}}_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{t,g}
```

**`Generator_ext_p_upper`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \left( P_{g} - \gamma_{\xi,g} \cdot \mu^{\mathrm{nom}}_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{t,g}
```

**`Generator_ext_p_nom_lower`**

```math
P_{g} \ge \underline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g}
```

**`Generator_ext_p_nom_upper`**

```math
P_{g} \le \overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g} \wedge \overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \text{ is defined}
```

**`Generator_p_nom_set`**

```math
P_{g} = \mathrm{p}^{\mathrm{nom,set}}_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g} \wedge \mathrm{p}^{\mathrm{nom,set}}_{g} \text{ is defined}
```

**`Generator_e_sum_min`**

```math
\sum_{t \in \mathcal{T}} p_{\xi,t,g} \cdot \mathrm{w}^{\mathrm{gen}}_{t} \ge \underline{\mathrm{E}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \underline{\mathrm{E}}_{\xi,g} \text{ is defined}
```

**`Generator_e_sum_max`**

```math
\sum_{t \in \mathcal{T}} p_{\xi,t,g} \cdot \mathrm{w}^{\mathrm{gen}}_{t} \le \overline{\mathrm{E}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \overline{\mathrm{E}}_{\xi,g} \text{ is defined}
```

**`Generator_com_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot \left( u_{\xi,t,g} - \gamma_{\xi,g} \cdot \mu^{u}_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_com_p_upper`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot \left( u_{\xi,t,g} - \gamma_{\xi,g} \cdot \mu^{u}_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_com_transition_start_up`**

```math
\mathit{up}_{\xi,t,g} \ge u_{\xi,t,g} - \overleftarrow{u}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_com_transition_shut_down`**

```math
\mathit{dn}_{\xi,t,g} \ge \overleftarrow{u}_{\xi,t,g} - u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_com_up_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}} \mathit{up}_{\xi,t',g} \le u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{UT}_{\xi,g} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Generator_com_down_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}} \mathit{dn}_{\xi,t',g} \le 1 - u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{DT}_{\xi,g} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Generator_com_status_must_stay_up`**

```math
u_{\xi,t,g} = 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{hold}_{\xi,t,g}
```

**`Generator_com_status_must_stay_down`**

```math
u_{\xi,t,g} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{rest}_{\xi,t,g}
```

**`Generator_p_ramp_limit_up_run_big_m`**

```math
p_{\xi,t,g} - \overleftarrow{p}_{\xi,t,g} \le \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot P_{g} + \mathrm{M}_{\xi,g} - \mathrm{M}_{\xi,g} \cdot \overleftarrow{u}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g} \wedge \left( \mathrm{ru}_{\xi,t,g} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{\xi,g} \text{ is defined} \right) \wedge \mathrm{prev}_{\xi,t,g}
```

**`Generator_p_ramp_limit_up_start_big_m`**

```math
p_{\xi,t,g} - \overleftarrow{p}_{\xi,t,g} \le \widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} \cdot P_{g} + \mathrm{M}_{\xi,g} - \mathrm{M}_{\xi,g} \cdot \mathit{up}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g} \wedge \left( \mathrm{ru}_{\xi,t,g} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{\xi,g} \text{ is defined} \right) \wedge \mathrm{prev}_{\xi,t,g}
```

**`Generator_p_ramp_limit_down_run_big_m`**

```math
\overleftarrow{p}_{\xi,t,g} - p_{\xi,t,g} \le \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot P_{g} + \mathrm{M}_{\xi,g} - \mathrm{M}_{\xi,g} \cdot u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g} \wedge \left( \mathrm{rd}_{\xi,t,g} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{\xi,g} \text{ is defined} \right) \wedge \mathrm{prev}_{\xi,t,g}
```

**`Generator_p_ramp_limit_down_shut_big_m`**

```math
\overleftarrow{p}_{\xi,t,g} - p_{\xi,t,g} \le \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot P_{g} + \mathrm{M}_{\xi,g} - \mathrm{M}_{\xi,g} \cdot \mathit{dn}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g} \wedge \left( \mathrm{rd}_{\xi,t,g} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{\xi,g} \text{ is defined} \right) \wedge \mathrm{prev}_{\xi,t,g}
```

**`Generator_p_nom_modularity`**

```math
P_{g} = \mathrm{p}^{\mathrm{mod}}_{g} \cdot N_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \wedge \mathrm{act}_{g}
```

**`Generator_com_ext_p_upper_cap`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \left( P_{g} - \gamma_{\xi,g} \cdot \mu^{\mathrm{nom}}_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g}
```

**`Generator_com_ext_p_upper_big_m`**

```math
p_{\xi,t,g} \le \mathrm{M}_{\xi,g} \cdot u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g}
```

**`Generator_com_ext_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \left( P_{g} - \gamma_{\xi,g} \cdot \mu^{\mathrm{nom}}_{\xi,t,g} \right) + \mathrm{M}_{\xi,g} \cdot u_{\xi,t,g} - \mathrm{M}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g}
```

**`Generator_com_ext_p_lower_nonneg`**

```math
p_{\xi,t,g} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g} \wedge \mathrm{nonneg}_{g}
```

**`Generator_com_mod_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{mod}}_{g} \cdot \left( u_{\xi,t,g} - \gamma_{\xi,g} \cdot \mu^{u}_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_com_mod_p_upper`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{mod}}_{g} \cdot \left( u_{\xi,t,g} - \gamma_{\xi,g} \cdot \mu^{u}_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_status_p_fixed_upper`**

```math
u_{\xi,t,g} \le \mathrm{N}^{\mathrm{fix}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_start_up_p_fixed_upper`**

```math
\mathit{up}_{\xi,t,g} \le \mathrm{N}^{\mathrm{fix}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_shut_down_p_fixed_upper`**

```math
\mathit{dn}_{\xi,t,g} \le \mathrm{N}^{\mathrm{fix}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_status_p_nom_variable_upper`**

```math
u_{\xi,t,g} \le N_{g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_start_up_p_nom_variable_upper`**

```math
\mathit{up}_{\xi,t,g} \le N_{g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_shut_down_p_nom_variable_upper`**

```math
\mathit{dn}_{\xi,t,g} \le N_{g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_maint_event_count`**

```math
\sum_{t \in \mathcal{T}} \mu^{\mathrm{up}}_{\xi,t,g} = \mathrm{n}^{\mathrm{mnt}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g}
```

**`Generator_maint_window`**

```math
\mu_{\xi,t,g} = \sum_{t' \in \mathcal{T} \,:\, \left( \xi,\ g,\ t',\ t \right) \in \mathrm{Generator\_maintenance\_cover}} \mu^{\mathrm{up}}_{\xi,t',g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{t,g}
```

**`Generator_maint_start_horizon`**

```math
\mu^{\mathrm{up}}_{\xi,t,g} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{t,g} \wedge \mathrm{blk}_{\xi,t,g}
```

**`Generator_maintcap_upper`**

```math
\mu^{\mathrm{nom}}_{\xi,t,g} \le P_{g} - \underline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \left( 1 - \mu_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{t,g}
```

**`Generator_maintcap_upper_nommax`**

```math
\mu^{\mathrm{nom}}_{\xi,t,g} \le \overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \mu_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{t,g}
```

**`Generator_maintcap_lower_nommax`**

```math
\mu^{\mathrm{nom}}_{\xi,t,g} \ge P_{g} - \overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \left( 1 - \mu_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{t,g}
```

**`Generator_maintcap_lower_nommin`**

```math
\mu^{\mathrm{nom}}_{\xi,t,g} \ge \underline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \mu_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{t,g} \wedge \underline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} > 0
```

**`Generator_maint_status_le_status`**

```math
\mu^{u}_{\xi,t,g} \le u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_maint_status_le_maint`**

```math
\mu^{u}_{\xi,t,g} \le \mu_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_maint_status_lb`**

```math
\mu^{u}_{\xi,t,g} \ge u_{\xi,t,g} + \mu_{\xi,t,g} - 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_maint_modstatus_le_status`**

```math
\mu^{u}_{\xi,t,g} \le u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_maint_modstatus_le_maint`**

```math
\mu^{u}_{\xi,t,g} \le \frac{\overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g}}{\mathrm{p}^{\mathrm{mod}}_{g}} \cdot \mu_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_maint_modstatus_lb`**

```math
\mu^{u}_{\xi,t,g} \ge u_{\xi,t,g} - \frac{\overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g}}{\mathrm{p}^{\mathrm{mod}}_{g}} \cdot \left( 1 - \mu_{\xi,t,g} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_p_ramp_limit_up`**

```math
p_{\xi,t,g} - \overleftarrow{p}_{\xi,t,g} \le \Delta^{+}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \left( \mathrm{ru}_{\xi,t,g} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{\xi,g} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{\xi,t,g} \wedge \mathrm{on}_{t,g}
```

**`Generator_p_ramp_limit_down`**

```math
\overleftarrow{p}_{\xi,t,g} - p_{\xi,t,g} \le \Delta^{-}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \left( \mathrm{rd}_{\xi,t,g} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{\xi,g} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{\xi,t,g} \wedge \mathrm{on}_{t,g}
```

**`Generator_p_set`**

```math
p_{\xi,t,g} = \mathrm{p}^{\mathrm{set}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{p}^{\mathrm{set}}_{\xi,t,g} \text{ is defined} \wedge \mathrm{on}_{t,g}
```

#### Assumptions

**`Generator_maintenance_events_positive`**

```math
\mathrm{n}^{\mathrm{mnt}}_{\xi,g} > 0 \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g}
```

**`Generator_maintenance_duration_positive`**

```math
\tau^{\mathrm{mnt}}_{\xi,g} > 0 \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g}
```

**`Generator_maintenance_duration_fits_the_horizon`**

```math
\tau^{\mathrm{mnt}}_{\xi,g} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g}
```

**`Generator_maintenance_events_fit_the_horizon`**

```math
\tau^{\mathrm{mnt}}_{\xi,g} \cdot \mathrm{n}^{\mathrm{mnt}}_{\xi,g} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g}
```

**`Generator_maintenance_build_cap_is_finite`**

```math
\overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} < \infty \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{ext}_{g}
```

**`Generator_maintenance_module_count_is_finite`**

```math
\overline{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} < \infty \qquad \forall\, \xi \in \Xi,\ g \in \mathcal{G} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_marginal_cost_quadratic_without_risk_preference`**

```math
\mathrm{c}^{(2)}_{\xi,t,g} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \omega \text{ is defined}
```

**`Generator_came_in_running_unless_committable`**

```math
\mathrm{u}^{0}_{\xi,g} = 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \neg \mathrm{com}_{g} \wedge \left( \mathrm{ru}_{\xi,t,g} \text{ is defined} \vee \mathrm{rd}_{\xi,t,g} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{\xi,g} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{\xi,g} \text{ is defined} \right)
```
<!-- gallery:end -->
