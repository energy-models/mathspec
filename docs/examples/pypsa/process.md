<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Processes

This file states PyPSA's `Process`, with its unit commitment, its ramp limits and its maintenance. It is one of the [14 fragments](index.md) that merge back into `examples/pypsa.yaml`. It adds a term to each of these sums: `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions` and `Bus_injection`. It reads `CVaR_omega`, `period_weight_objective`, `scenario_weight`, `snapshot_weightings_generators` and `snapshot_weightings_objective`, which other fragments declare, and lists them under [`given`](../../reference/language/parameters-variables-constraints.md#given).

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
  process:
    description: generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate
  process_output:
    description: >-
      a process's ports, one label per port a process declares — PyPSA's
      `bus0`, `bus1`, … each carry a signed `rate`, so a process of any number
      of ports is one term in the balance, data prep
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
  Process_carrier:
    description: the carrier a process converts from
    key: process
    values: carrier
  Process_output_process:
    description: the process a port belongs to
    key: process_output
    values: process
  Process_output_bus:
    description: >-
      the bus a port draws from or delivers to — PyPSA's `bus0`, `bus1`, …
      columns. A process of three ports is three labels here rather than a
      third relation, so the file states any number of them
    key: process_output
    values: bus
  Process_maintenance_cover:
    description: >-
      the snapshots a maintenance event covers, by the snapshot it starts in —
      in a scenario, the start and the snapshots after it, until their
      generator weightings reach that scenario's `maintenance_duration`, data prep; no
      rows for a process that is
      not maintainable
    key: { scenario: scenario, process: process, start: snapshot, covered: snapshot }
    missing: absent

parameters:
  Process_p_nom:
    description: nominal internal power
    dims: [scenario, process]
  Process_p_nom_extendable:
    description: whether the nominal internal power is a decision
    dims: [process]
    dtype: bool
  Process_p_min_pu:
    description: least internal power, per unit of nominal power — negative for a process that runs both ways
    dims: [scenario, snapshot, process]
  Process_p_max_pu:
    description: most internal power, per unit of nominal power
    dims: [scenario, snapshot, process]
  Process_rate:
    description: >-
      the energy a port draws or delivers per unit of internal power, PyPSA's
      `rate0`, `rate1`, … read long — negative where the port withdraws,
      positive where it injects; a link is a process whose `bus0` rate is minus
      one and whose output rates are its efficiencies. Read at the snapshot the
      transfer arrives, so a delayed port transfers at its arrival snapshot's
      rate (`constraints.py:1498`)
    dims: [scenario, snapshot, process_output]
  Process_output_delay:
    description: >-
      snapshots a port's transfer lags its process's internal power — PyPSA's
      `delay0`, `delay1`, … read long, divided by the
      `snapshot_weightings.generators` value and rounded up in data prep; zero
      for a port that transfers at once. A port has the same delay in every
      scenario, as a link's port has
    dims: [process_output]
    dtype: int
  Process_output_cyclic_delay:
    description: >-
      whether a delayed port's transfer wraps from the end of its investment
      period — PyPSA's `cyclic_delay0`, `cyclic_delay1`, …; where it does not,
      the energy still in transit at each period's first snapshots is lost.
      The flag is the same in every scenario, as the delay is
    dims: [process_output]
    dtype: bool
  Process_marginal_cost:
    description: cost of one unit of internal power
    dims: [scenario, snapshot, process]
  Process_marginal_cost_quadratic:
    description: cost of the square of one unit of internal power
    dims: [scenario, snapshot, process]
  Process_ramp_limit_up:
    description: most a process may raise its internal power between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time
    dims: [scenario, snapshot, process]
    missing: neutral
  Process_ramp_limit_down:
    description: most a process may lower its internal power between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time
    dims: [scenario, snapshot, process]
    missing: neutral
  Process_p_set:
    description: a given internal power schedule; a process without one has no row here
    dims: [scenario, snapshot, process]
    missing: neutral
  Process_p_nom_min:
    description: least nominal power an extendable process may be built at
    dims: [scenario, process]
  Process_p_nom_max:
    description: most nominal power an extendable process may be built at
    dims: [scenario, process]
  Process_capital_cost:
    description: >-
      cost of one unit of nominal power for the modelled horizon —
      PyPSA's `periodized_cost`: `overnight_cost` as an annuity over
      `lifetime` at `discount_rate`, times `nyears`, where it is given, and
      `capital_cost` where it is not, plus `fom_cost`
      (`components.py:1126-1147`, `costs.py:102-203`), data prep
    dims: [scenario, process]
  Process_p_nom_set:
    description: a given nominal power for an extendable process; one without a value has no row here
    dims: [process]
    missing: neutral
  Process_committable:
    description: whether internal power is gated by an on/off status decision
    dims: [process]
    dtype: bool
  Process_ramp_limit_start_up:
    description: most internal power in the snapshot a process starts, per unit of nominal power; no value means no limit
    dims: [scenario, process]
    missing: neutral
  Process_ramp_limit_shut_down:
    description: most internal power in the snapshot before a process stops, per unit of nominal power; no value means no limit
    dims: [scenario, process]
    missing: neutral
  Process_min_up_time:
    description: least snapshots a process stays on once started
    dims: [scenario, process]
    dtype: int
  Process_min_down_time:
    description: least snapshots a process stays off once stopped
    dims: [scenario, process]
    dtype: int
  Process_status_initial:
    description: one where the process was on before the first snapshot, zero where off — PyPSA's `up_time_before > 0`, data prep
    dims: [scenario, process]
    dtype: int
  Process_p_init:
    description: >-
      the internal power a process brought into the horizon — PyPSA's `p_init`, read
      only where the process came in running; no value means it is unknown, so
      the process carries no ramp row at the first snapshot
    dims: [scenario, process]
    missing: neutral
  Process_must_stay_up:
    description: >-
      true while the up time a process brought into the horizon still binds —
      data prep, since `position()` compares against a literal rather than a
      parameter
    dims: [scenario, snapshot, process]
    dtype: bool
  Process_must_stay_down:
    description: >-
      true while the down time a process brought into the horizon still binds —
      PyPSA's `min_down_time - down_time_before` snapshots, where
      `down_time_before > 0`, data prep for the same reason
    dims: [scenario, snapshot, process]
    dtype: bool
  Process_start_up_cost:
    description: cost of one start in this snapshot
    dims: [scenario, snapshot, process]
  Process_shut_down_cost:
    description: cost of one stop in this snapshot
    dims: [scenario, snapshot, process]
  Process_stand_by_cost:
    description: cost of one snapshot spent on
    dims: [scenario, snapshot, process]
  Process_p_nom_mod:
    description: the module size a build comes in whole numbers of; no value means the build is continuous
    dims: [process]
    missing: neutral
  Process_modules_installed:
    description: >-
      how many whole modules a committable build has in place: `Process_p_nom
      / Process_p_nom_mod` where a fixed build is modular, one where it is
      not, data prep. PyPSA refuses a fixed modular build whose nominal power
      is not a whole number of modules
    dims: [scenario, process]
  Process_big_m:
    description: >-
      the bound a committed extendable process's big-M rows release it by — the
      build cap `p_nom_max` times the highest `p_max_pu`, where the cap is
      finite and positive. Elsewhere it is `committable_big_m` times the
      highest `p_max_pu`, and where that keyword is not given, ten times the
      largest of the peak total load and the component's largest finite
      `p_nom` and `p_nom_max`, or 1e6 where there is none of them
      (`components.py:1050-1121`). Below the internal power a solve wants, it caps that
      internal power; data prep
    dims: [scenario, process]
    missing: neutral
  Process_p_min_pu_nonneg:
    description: >-
      true where none of the process's own minimums-per-unit is negative —
      PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep
    dims: [process]
    dtype: bool
  Process_maintainable:
    description: >-
      whether a process must be taken off for maintenance within the horizon — in
      any scenario, as PyPSA takes the union over them (`components.py:1016-1019`)
    dims: [process]
    dtype: bool
  Process_maintenance_pu:
    description: the share of the build a maintenance event takes off
    dims: [scenario, process]
  Process_maintenance_events:
    description: how many maintenance events the horizon holds
    dims: [scenario, process]
    dtype: int
  Process_maintenance_duration:
    description: >-
      the hours of generator weightings one maintenance event covers —
      PyPSA's `maintenance_duration`; no value where the process is not
      maintainable. No row reads it: data prep turns it into
      `Process_maintenance_cover` and `Process_maintenance_start_blocked`, and the
      assumptions hold it to the horizon
    dims: [scenario, process]
    missing: neutral
  Process_maintenance_start_blocked:
    description: >-
      true where no maintenance event may start, because the snapshots it
      would cover run past the end of the horizon or into one the process does
      not stand in — PyPSA's `active & ~valid`, from `maintenance_duration`
      and the generator weightings, data prep
    dims: [scenario, snapshot, process]
    dtype: bool
  Process_active:
    description: whether a process stands in a snapshot's period — PyPSA's `active`, data prep
    dims: [snapshot, process]
    dtype: bool
  Process_active_asset:
    description: >-
      whether a process is one of PyPSA's `active_assets` — its `active` flag
      alone, without build year and lifetime, so a unit that stands in no
      snapshot of the horizon still counts. PyPSA refuses one that differs
      by scenario (`constants.py:51`)
    dims: [process]
    dtype: bool
  Process_capital_weight:
    description: the sum of period weights a process stands in — PyPSA's `active * period_weighting`, summed, data prep
    dims: [process]
  Process_first_active:
    description: >-
      one in the first period a process stands in, zero elsewhere, data prep.
      PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`)
    dims: [period, process]
  Process_tech_capacity_weight:
    description: >-
      one where the process is in the row's carrier-and-bus set — data prep; one
      outside it, or one that does not stand in the row's `investment_period`,
      has no row
    dims: [global_constraint, process]
    missing: neutral

variables:
  Process_p:
    description: >-
      `Process-p` — PyPSA's internal power `p`: a positive value drives every
      port at its own rate, withdrawing where the rate is negative and injecting
      where it is positive
    dims: [scenario, snapshot, process]
    where: Process_active
  Process_n_mod:
    description: "`Process-n_mod` — how many modules of an extendable modular build; none for a unit that is not active"
    dims: [process]
    where: Process_p_nom_extendable AND Process_p_nom_mod > 0 AND Process_active_asset
    domain: integer
    bounds:
      lower: 0
  Process_status:
    description: >-
      `Process-status` — how much of a committable process is on: an integer
      the rows below cap at one, or at the module count where the build is
      modular
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
  Process_start_up:
    description: "`Process-start_up` — how much of a committable process turns on this snapshot, capped as the status is"
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
  Process_shut_down:
    description: "`Process-shut_down` — how much of a committable process turns off this snapshot, capped as the status is"
    dims: [scenario, snapshot, process]
    where: Process_committed
    domain: integer
    bounds:
      lower: 0
  Process_maintenance:
    description: >-
      `Process-maintenance` — whether a maintainable process is in maintenance:
      continuous, and one exactly where an event covers the snapshot
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_active
    missing: neutral
    bounds:
      lower: 0
      upper: 1
  Process_maintenance_start:
    description: "`Process-maintenance_start` — whether a maintenance event starts in this snapshot"
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_active
    missing: neutral
    domain: binary
  Process_maintenance_capacity:
    description: >-
      `Process-maintenance_capacity` — the chosen build while in maintenance, zero
      otherwise: the product the `maintcap` rows linearize
    dims: [scenario, snapshot, process]
    where: Process_maint_ext
    missing: neutral
    bounds:
      lower: 0
  Process_maintenance_status:
    description: >-
      `Process-maintenance_status` — the status while in maintenance, zero
      otherwise: the product the `maint-status` rows linearize, so a unit in
      maintenance may also be off
    dims: [scenario, snapshot, process]
    where: >-
      Process_maintainable
      AND Process_committed
      AND NOT (Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0))
    missing: neutral
    bounds:
      lower: 0
  Process_p_nom_ext:
    description: >-
      `Process-p_nom` — nominal internal power where it is a decision, for a
      process that is active; the parameter of the same PyPSA name carries
      the fixed regime
    dims: [process]
    where: Process_p_nom_extendable AND Process_active_asset

expressions:
  Process_p_nom_effective:
    description: the build a process's limits are taken against — the chosen one where it is extendable, the given one otherwise
    dims: [scenario, process]
    cases:
      extendable: { when: Process_p_nom_extendable, expression: Process_p_nom_ext }
    otherwise: Process_p_nom
  Process_previous_status:
    description: >-
      the commitment state a process carries into a snapshot — off at the
      first snapshot it stands in past the first of the horizon, as PyPSA
      reads a status it did not build (`constraints.py:298`), and the state
      carried over otherwise
    dims: [scenario, snapshot, process]
    cases:
      opening_late: { when: "position(snapshot) > 0 AND NOT shift(Process_active, along=snapshot, offset=1)", expression: 0 }
    otherwise: Process_status_carried_over
  Process_status_carried_over:
    description: >-
      the state a process carries over into a snapshot — the state it brought
      into the horizon at the first, the previous snapshot's after that
    dims: [scenario, snapshot, process]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Process_status_initial }
    otherwise: shift(Process_status, along=snapshot, offset=1)
  Process_previous_p:
    description: >-
      the internal power a process carries into a snapshot — at the first, the
      `p_init` it brought in where it came in running and nothing where it
      came in off; the previous snapshot's after that
    dims: [scenario, snapshot, process]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Process_status_initial * Process_p_init }
    otherwise: shift(Process_p, along=snapshot, offset=1)
  Process_ramp_up_rate:
    description: >-
      the ramp limit a process's up row reads — PyPSA's `ramp_limit_up`, or the
      full build where it has none, since a start-up ramp alone builds the row
    dims: [scenario, snapshot, process]
    cases:
      given: { when: Process_ramp_limit_up, expression: Process_ramp_limit_up }
    otherwise: 1
  Process_ramp_down_rate:
    description: >-
      the ramp limit a process's down row reads — PyPSA's `ramp_limit_down`, or
      the full build where it has none, since a shut-down ramp alone builds the row
    dims: [scenario, snapshot, process]
    cases:
      given: { when: Process_ramp_limit_down, expression: Process_ramp_limit_down }
    otherwise: 1
  Process_start_up_rate:
    description: >-
      the start-up ramp a process's up row reads — PyPSA's `ramp_limit_start_up`,
      or the full build where it has none
    dims: [scenario, process]
    cases:
      given: { when: Process_ramp_limit_start_up, expression: Process_ramp_limit_start_up }
    otherwise: 1
  Process_shut_down_rate:
    description: >-
      the shut-down ramp a process's down row reads — PyPSA's
      `ramp_limit_shut_down`, or the full build where it has none
    dims: [scenario, process]
    cases:
      given: { when: Process_ramp_limit_shut_down, expression: Process_ramp_limit_shut_down }
    otherwise: 1
  Process_p_nom_committed:
    description: >-
      the build a committed process's ramp rows are taken against — one module
      where the build is extendable and modular, the given build otherwise
    dims: [scenario, process]
    cases:
      modular_build: { when: Process_p_nom_extendable AND Process_p_nom_mod > 0, expression: Process_p_nom_mod }
    otherwise: Process_p_nom
  Process_ramp_up_allowance:
    description: >-
      how far a process may raise internal power between two snapshots — its ramp
      limit of the build while it stays on, plus its start-up ramp in the
      snapshot it turns on
    dims: [scenario, snapshot, process]
    cases:
      committed:
        when: Process_committable
        expression: >-
          Process_ramp_up_rate * Process_p_nom_committed * Process_previous_status
          + Process_start_up_rate * Process_p_nom_committed
          * (Process_status - Process_previous_status)
    otherwise: Process_ramp_up_rate * Process_p_nom_effective
  Process_ramp_down_allowance:
    description: >-
      how far a process may lower internal power between two snapshots — its ramp
      limit of the build while it stays on, plus its shut-down ramp in the
      snapshot it turns off
    dims: [scenario, snapshot, process]
    cases:
      committed:
        when: Process_committable
        expression: >-
          Process_ramp_down_rate * Process_p_nom_committed * Process_status
          + Process_shut_down_rate * Process_p_nom_committed
          * (Process_previous_status - Process_status)
    otherwise: Process_ramp_down_rate * Process_p_nom_effective
  Process_output_arrival:
    description: >-
      what a process transfers at a port at a snapshot — its internal power
      delayed by the port's `delay` within its investment period, times the
      port's rate at the snapshot the transfer arrives; where the port is
      `cyclic_delay` the delayed transfer wraps from the period's end, and
      where it is not the energy still in transit at the period's first
      snapshots is lost. A port that does not
      delay (`delay` zero) transfers at once, cyclic or not
    dims: [scenario, snapshot, process_output]
    cases:
      wrapping:
        when: Process_output_cyclic_delay
        expression: shift(at(Process_p, by=Process_output_process[process]), along=snapshot, offset=Process_output_delay, edge='wrap', within=snapshot_period[period]) * Process_rate
    otherwise: shift(at(Process_p, by=Process_output_process[process]), along=snapshot, offset=Process_output_delay, edge=0, within=snapshot_period[period]) * Process_rate
  Process_tech_capacity_expansion:
    expression: sum(Process_p_nom_ext * Process_tech_capacity_weight, over=process)
    adds_to: tech_capacity_expansion
  Process_opex:
    expression: >-
      sum(sum(((Process_p * Process_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
      + sum(sum((((Process_p * Process_p) * Process_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
    adds_to: scenario_opex
  Process_commitment_opex:
    expression: >-
      sum(sum(((Process_status * Process_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
      + sum(sum(Process_start_up * Process_start_up_cost, over=process), over=snapshot)
      + sum(sum(Process_shut_down * Process_shut_down_cost, over=process), over=snapshot)
    adds_to: scenario_opex
  Process_capex:
    expression: sum(scenario_weight * Process_p_nom_ext * Process_capital_cost * Process_capital_weight)
    adds_to: total_cost
  Process_additions:
    expression: >-
      sum(Process_p_nom_ext * Process_first_active, over=process, by=Process_carrier[carrier])
    adds_to: Carrier_additions
  Process_injection:
    expression: >-
      sum(Process_output_arrival, over=process_output, by=Process_output_bus[bus])
    adds_to: Bus_injection

masks:
  Process_com_ext:
    description: >-
      a committable process with an extendable, non-modular build that stands
      in the snapshot's period — PyPSA's `com-ext` rows, whose status is
      relaxed against the chosen build
    where: >-
      Process_committable
      AND Process_p_nom_extendable
      AND NOT (Process_p_nom_mod > 0)
      AND Process_active
  Process_maint_ext:
    description: >-
      a maintainable process with an extendable build, unless it is
      committable and modular, that stands in the snapshot's period — the
      maintenance rows against the chosen build
    where: >-
      Process_maintainable
      AND Process_p_nom_extendable
      AND NOT (Process_committable AND Process_p_nom_mod > 0)
      AND Process_active
  Process_committed:
    description: >-
      a committable process that stands in the snapshot's period — every
      unit-commitment row's set
    where: Process_committable AND Process_active
  Process_ramps_from_previous:
    description: >-
      a snapshot whose ramp reads a previous output — any snapshot but its
      period's first, and the horizon's first where the process comes in off
      or carries an initial output
    where: >-
      position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
      (Process_status_initial == 0 OR Process_p_init))

constraints:
  Process_fix_p_lower:
    description: "`Process-fix-p-lower` — a fixed process runs at least its minimum, negative for the other way"
    dims: [scenario, snapshot, process]
    where: not Process_p_nom_extendable AND not Process_committable AND Process_active
    expression: Process_p >= Process_p_min_pu * Process_p_nom * (1 - Process_maintenance_pu * Process_maintenance)
  Process_fix_p_upper:
    description: "`Process-fix-p-upper` — a fixed process runs at most its nominal power"
    dims: [scenario, snapshot, process]
    where: not Process_p_nom_extendable AND not Process_committable AND Process_active
    expression: Process_p <= Process_p_max_pu * Process_p_nom * (1 - Process_maintenance_pu * Process_maintenance)
  Process_ext_p_lower:
    description: "`Process-ext-p-lower` — an extendable process runs at least its minimum of the chosen build, negative for the other way"
    dims: [scenario, snapshot, process]
    where: Process_p_nom_extendable AND not Process_committable AND Process_active
    expression: Process_p >= Process_p_min_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
  Process_ext_p_upper:
    description: "`Process-ext-p-upper` — an extendable process runs at most the chosen build"
    dims: [scenario, snapshot, process]
    where: Process_p_nom_extendable AND not Process_committable AND Process_active
    expression: Process_p <= Process_p_max_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
  Process_ext_p_nom_lower:
    description: "`Process-ext-p_nom-lower` — the chosen build is at least its floor in every scenario"
    dims: [scenario, process]
    where: Process_p_nom_extendable AND Process_active_asset
    expression: Process_p_nom_ext >= Process_p_nom_min
  Process_ext_p_nom_upper:
    description: "`Process-ext-p_nom-upper` — the chosen build is at most its cap in every scenario; a cap of infinity is no row"
    dims: [scenario, process]
    where: Process_p_nom_extendable AND Process_active_asset AND Process_p_nom_max
    expression: Process_p_nom_ext <= Process_p_nom_max
  Process_p_nom_set:
    description: "`Process-p_nom_set` — the chosen build pinned, wherever a value is given"
    dims: [process]
    where: Process_p_nom_extendable AND Process_active_asset AND Process_p_nom_set
    expression: Process_p_nom_ext == Process_p_nom_set
  Process_com_p_lower:
    description: "`Process-com-p-lower` — a committed process runs at least its minimum; off, at least nothing"
    dims: [scenario, snapshot, process]
    where: Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
    expression: Process_p >= Process_p_min_pu * Process_p_nom * (Process_status - Process_maintenance_pu * Process_maintenance_status)
  Process_com_p_upper:
    description: "`Process-com-p-upper` — a committed process runs at most what is available; off, at most nothing"
    dims: [scenario, snapshot, process]
    where: Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
    expression: Process_p <= Process_p_max_pu * Process_p_nom * (Process_status - Process_maintenance_pu * Process_maintenance_status)
  Process_com_transition_start_up:
    description: "`Process-com-transition-start-up` — turning on is a start, counted against the state the process carried into the snapshot"
    dims: [scenario, snapshot, process]
    where: Process_committed
    expression: Process_start_up >= Process_status - Process_previous_status
  Process_com_transition_shut_down:
    description: "`Process-com-transition-shut-down` — turning off is a stop, counted against the state the process carried into the snapshot"
    dims: [scenario, snapshot, process]
    where: Process_committed
    expression: Process_shut_down >= Process_previous_status - Process_status
  Process_com_up_time:
    description: >-
      `Process-com-up-time` — a process started within its own minimum up time
      is still on. The first snapshot's share of the window is the brought-in
      up time's, which the must-stay-up mask carries
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_min_up_time > 0 AND position(snapshot) > 0
    expression: sum_back(Process_start_up, along=snapshot, window=Process_min_up_time) <= Process_status
  Process_com_down_time:
    description: >-
      `Process-com-down-time` — a process stopped within its own minimum down
      time is still off. The first snapshot's share of the window is the
      brought-in down time's, which the must-stay-down mask carries
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_min_down_time > 0 AND position(snapshot) > 0
    expression: sum_back(Process_shut_down, along=snapshot, window=Process_min_down_time) <= 1 - Process_status
  Process_com_status_must_stay_up:
    description: "`Process-com-status-min_up_time_must_stay_up` — a process still serving the up time it brought in stays on"
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_must_stay_up
    expression: Process_status == 1
  Process_com_status_must_stay_down:
    description: >-
      `Process-com-status-min_down_time_must_stay_up` — a process still serving
      the down time it brought in stays off; PyPSA names the row `_must_stay_up`
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_must_stay_down
    expression: Process_status == 0
  Process_p_ramp_limit_up_run_big_m:
    description: >-
      `Process-p-ramp_limit_up-run-bigM` — a committed extendable process
      raises internal power no faster than its limit of the chosen build; the big M
      releases the row in the snapshot it turns on
    dims: [scenario, snapshot, process]
    where: Process_com_ext AND (Process_ramp_limit_up OR Process_ramp_limit_start_up) AND Process_ramps_from_previous
    expression: >-
      Process_p - Process_previous_p <=
      Process_ramp_up_rate * Process_p_nom_ext
      + Process_big_m - Process_big_m * Process_previous_status
  Process_p_ramp_limit_up_start_big_m:
    description: >-
      `Process-p-ramp_limit_up-start-bigM` — in the snapshot it turns on, a
      committed extendable process ramps no further than its start-up ramp of
      the chosen build; the big M releases the row everywhere else
    dims: [scenario, snapshot, process]
    where: Process_com_ext AND (Process_ramp_limit_up OR Process_ramp_limit_start_up) AND Process_ramps_from_previous
    expression: >-
      Process_p - Process_previous_p <=
      Process_start_up_rate * Process_p_nom_ext
      + Process_big_m - Process_big_m * Process_start_up
  Process_p_ramp_limit_down_run_big_m:
    description: >-
      `Process-p-ramp_limit_down-run-bigM` — a committed extendable process
      lowers internal power no faster than its limit of the chosen build; the big M
      releases the row in the snapshot it turns off
    dims: [scenario, snapshot, process]
    where: >-
      Process_com_ext
      AND (Process_ramp_limit_down OR Process_ramp_limit_shut_down)
      AND Process_ramps_from_previous
    expression: >-
      Process_previous_p - Process_p <=
      Process_ramp_down_rate * Process_p_nom_ext
      + Process_big_m - Process_big_m * Process_status
  Process_p_ramp_limit_down_shut_big_m:
    description: >-
      `Process-p-ramp_limit_down-shut-bigM` — in the snapshot it turns off,
      a committed extendable process ramps no further than its shut-down ramp of
      the chosen build; the big M releases the row everywhere else
    dims: [scenario, snapshot, process]
    where: >-
      Process_com_ext
      AND (Process_ramp_limit_down OR Process_ramp_limit_shut_down)
      AND Process_ramps_from_previous
    expression: >-
      Process_previous_p - Process_p <=
      Process_shut_down_rate * Process_p_nom_ext
      + Process_big_m - Process_big_m * Process_shut_down
  Process_p_nom_modularity:
    description: "`Process-p_nom_modularity` — the chosen build is a whole number of modules"
    dims: [process]
    where: Process_p_nom_extendable AND Process_p_nom_mod > 0 AND Process_active_asset
    expression: Process_p_nom_ext == Process_p_nom_mod * Process_n_mod
  Process_com_ext_p_upper_cap:
    description: >-
      `Process-com-ext-p-upper-cap` — a committed extendable process runs
      at most what is available of the chosen build, whatever its status
    dims: [scenario, snapshot, process]
    where: Process_com_ext
    expression: Process_p <= Process_p_max_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
  Process_com_ext_p_upper_big_m:
    description: "`Process-com-ext-p-upper-bigM` — off, a process does not run; on, the big M is no bound"
    dims: [scenario, snapshot, process]
    where: Process_com_ext
    expression: Process_p <= Process_big_m * Process_status
  Process_com_ext_p_lower:
    description: >-
      `Process-com-ext-p-lower` — a committed extendable process runs at
      least its minimum of the chosen build; off, the big M releases the row
    dims: [scenario, snapshot, process]
    where: Process_com_ext
    expression: >-
      Process_p >=
      Process_p_min_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
      + Process_big_m * Process_status - Process_big_m
  Process_com_ext_p_lower_nonneg:
    description: >-
      `Process-com-ext-p-lower-nonneg` — where no minimum-per-unit is
      negative, internal power is also plainly non-negative, a row the big-M lower
      cannot assert while the process is off
    dims: [scenario, snapshot, process]
    where: Process_com_ext AND Process_p_min_pu_nonneg
    expression: Process_p >= 0
  Process_com_mod_p_lower:
    description: >-
      `Process-com-mod-p-lower` — a committed modular process runs at least
      its minimum of one module, whether the build is fixed or a decision
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_p_nom_mod > 0
    expression: Process_p >= Process_p_min_pu * Process_p_nom_mod * (Process_status - Process_maintenance_pu * Process_maintenance_status)
  Process_com_mod_p_upper:
    description: >-
      `Process-com-mod-p-upper` — a committed modular process runs at most
      one module's share, whether the build is fixed or a decision
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_p_nom_mod > 0
    expression: Process_p <= Process_p_max_pu * Process_p_nom_mod * (Process_status - Process_maintenance_pu * Process_maintenance_status)
  Process_status_p_fixed_upper:
    description: >-
      `Process-status-p-fixed-upper` — a status is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, process]
    where: Process_committed AND NOT (Process_p_nom_extendable AND Process_p_nom_mod > 0)
    expression: Process_status <= Process_modules_installed
  Process_start_up_p_fixed_upper:
    description: >-
      `Process-start_up-p-fixed-upper` — a start is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, process]
    where: Process_committed AND NOT (Process_p_nom_extendable AND Process_p_nom_mod > 0)
    expression: Process_start_up <= Process_modules_installed
  Process_shut_down_p_fixed_upper:
    description: >-
      `Process-shut_down-p-fixed-upper` — a stop is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, process]
    where: Process_committed AND NOT (Process_p_nom_extendable AND Process_p_nom_mod > 0)
    expression: Process_shut_down <= Process_modules_installed
  Process_status_p_nom_variable_upper:
    description: "`Process-status-p_nom-variable-upper` — a modular process is on only where a module is built"
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_p_nom_extendable AND Process_p_nom_mod > 0
    expression: Process_status <= Process_n_mod
  Process_start_up_p_nom_variable_upper:
    description: "`Process-start_up-p_nom-variable-upper` — a modular process starts only where a module is built"
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_p_nom_extendable AND Process_p_nom_mod > 0
    expression: Process_start_up <= Process_n_mod
  Process_shut_down_p_nom_variable_upper:
    description: "`Process-shut_down-p_nom-variable-upper` — a modular process stops only where a module is built"
    dims: [scenario, snapshot, process]
    where: Process_committed AND Process_p_nom_extendable AND Process_p_nom_mod > 0
    expression: Process_shut_down <= Process_n_mod
  Process_maint_event_count:
    description: "`Process-maint-event-count` — a maintainable process holds its number of maintenance events over the horizon"
    dims: [scenario, process]
    where: Process_maintainable
    expression: sum(Process_maintenance_start, over=snapshot) == Process_maintenance_events
  Process_maint_window:
    description: >-
      `Process-maint-window` — a process is in maintenance exactly where an event it
      started covers the snapshot; two events do not overlap, since the
      maintenance status is at most one
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_active
    expression: Process_maintenance == sum(Process_maintenance_start, over=start, by=Process_maintenance_cover[covered])
  Process_maint_start_horizon:
    description: "`Process-maint-start-horizon` — no event starts where it could not run its whole duration"
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_active AND Process_maintenance_start_blocked
    expression: Process_maintenance_start == 0
  Process_maintcap_upper:
    description: >-
      `Process-maintcap_upper` — the build taken off is at most the chosen build in
      maintenance, and at most the build less its floor out of it
    dims: [scenario, snapshot, process]
    where: Process_maint_ext
    expression: Process_maintenance_capacity <= Process_p_nom_ext - Process_p_nom_min * (1 - Process_maintenance)
  Process_maintcap_upper_nommax:
    description: "`Process-maintcap_upper_nommax` — out of maintenance, no build is taken off"
    dims: [scenario, snapshot, process]
    where: Process_maint_ext
    expression: Process_maintenance_capacity <= Process_p_nom_max * Process_maintenance
  Process_maintcap_lower_nommax:
    description: "`Process-maintcap_lower_nommax` — in maintenance, the whole chosen build is taken off"
    dims: [scenario, snapshot, process]
    where: Process_maint_ext
    expression: Process_maintenance_capacity >= Process_p_nom_ext - Process_p_nom_max * (1 - Process_maintenance)
  Process_maintcap_lower_nommin:
    description: "`Process-maintcap_lower_nommin` — in maintenance, at least the floor of the build is taken off"
    dims: [scenario, snapshot, process]
    where: Process_maint_ext AND Process_p_nom_min > 0
    expression: Process_maintenance_capacity >= Process_p_nom_min * Process_maintenance
  Process_maint_status_le_status:
    description: "`Process-maint-status-le-status` — the status in maintenance is at most the status"
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
    expression: Process_maintenance_status <= Process_status
  Process_maint_status_le_maint:
    description: "`Process-maint-status-le-maint` — out of maintenance, the status in maintenance is zero"
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
    expression: Process_maintenance_status <= Process_maintenance
  Process_maint_status_lb:
    description: "`Process-maint-status-lb` — on and in maintenance, the status in maintenance is one"
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
    expression: Process_maintenance_status >= Process_status + Process_maintenance - 1
  Process_maint_modstatus_le_status:
    description: "`Process-maint-modstatus-le-status` — the modules on in maintenance are at most the modules on"
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_committed AND Process_p_nom_mod > 0
    expression: Process_maintenance_status <= Process_status
  Process_maint_modstatus_le_maint:
    description: >-
      `Process-maint-modstatus-le-maint` — out of maintenance, no module is on in
      maintenance; in it, at most the modules the build cap holds
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_committed AND Process_p_nom_mod > 0
    expression: Process_maintenance_status <= Process_p_nom_max / Process_p_nom_mod * Process_maintenance
  Process_maint_modstatus_lb:
    description: "`Process-maint-modstatus-lb` — in maintenance, every module on is on in maintenance"
    dims: [scenario, snapshot, process]
    where: Process_maintainable AND Process_committed AND Process_p_nom_mod > 0
    expression: Process_maintenance_status >= Process_status - Process_p_nom_max / Process_p_nom_mod * (1 - Process_maintenance)
  Process_p_ramp_limit_up:
    description: >-
      `Process-p-ramp_limit_up` — a process raises internal power no faster than
      its ramp limit of the build, and a committed one no further than its
      start-up ramp in the snapshot it turns on. A process that came into the
      horizon running carries a row at the first snapshot only where its
      `p_init` gives the internal power it brought in, and no process carries one at
      the start of a later investment period — nor does any process a big M releases instead
    dims: [scenario, snapshot, process]
    where: >-
      (Process_ramp_limit_up OR Process_ramp_limit_start_up)
      AND NOT (Process_committable AND Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0))
      AND Process_ramps_from_previous
      AND Process_active
    expression: Process_p - Process_previous_p <= Process_ramp_up_allowance
  Process_p_ramp_limit_down:
    description: >-
      `Process-p-ramp_limit_down` — a process lowers internal power no faster than
      its ramp limit of the build, and a committed one no further than its
      shut-down ramp in the snapshot it turns off. A process that came into the
      horizon running carries a row at the first snapshot only where its
      `p_init` gives the internal power it brought in, and no process carries one at
      the start of a later investment period — nor does any process a big M releases instead
    dims: [scenario, snapshot, process]
    where: >-
      (Process_ramp_limit_down OR Process_ramp_limit_shut_down)
      AND NOT (Process_committable AND Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0))
      AND Process_ramps_from_previous
      AND Process_active
    expression: Process_previous_p - Process_p <= Process_ramp_down_allowance
  Process_p_set:
    description: "`Process-p_set` — internal power pinned to the given schedule, wherever one is given"
    dims: [scenario, snapshot, process]
    where: Process_p_set AND Process_active
    expression: Process_p == Process_p_set

assumptions:
  Process_maintenance_events_positive:
    holds: "Process_maintenance_events > 0"
    where: "Process_maintainable"
    description: >-
      a maintainable process with no event schedules no maintenance —
      PyPSA refuses it (`consistency.py:1493`)
  Process_maintenance_duration_positive:
    holds: "Process_maintenance_duration > 0"
    where: "Process_maintainable"
    description: >-
      an event that covers no hours is no maintenance window — PyPSA
      refuses it (`consistency.py:1483`)
  Process_maintenance_duration_fits_the_horizon:
    holds: "Process_maintenance_duration <= sum(snapshot_weightings_generators, over=snapshot)"
    where: "Process_maintainable"
    description: >-
      one event longer than the horizon, in generator weightings, blocks
      every start and makes the event count infeasible — PyPSA refuses it
      (`consistency.py:1504`)
  Process_maintenance_events_fit_the_horizon:
    holds: "Process_maintenance_duration * Process_maintenance_events <= sum(snapshot_weightings_generators, over=snapshot)"
    where: "Process_maintainable"
    description: >-
      the events together longer than the horizon, in generator
      weightings, cannot all be scheduled — PyPSA refuses it
      (`consistency.py:1516`)
  Process_maintenance_build_cap_is_finite:
    holds: "Process_p_nom_max < inf"
    where: "Process_maintainable AND Process_p_nom_extendable"
    description: >-
      the `maintcap` rows hold the chosen build in maintenance against
      `p_nom_max`, so an infinite cap is an infinite coefficient — PyPSA
      refuses it (`consistency.py:1528`)
  Process_maintenance_module_count_is_finite:
    holds: "Process_p_nom_max < inf"
    where: "Process_maintainable AND Process_committable AND NOT Process_p_nom_extendable AND Process_p_nom_mod > 0"
    description: >-
      the `maint-modstatus` rows bound the modules on in maintenance by
      `p_nom_max / p_nom_mod`, so an infinite cap is an infinite
      coefficient. PyPSA does not check it, and HiGHS refuses the model
      (`constraints.py:504-507`)
  Process_output_delay_under_uniform_weighting:
    holds: "snapshot_weightings_generators == shift(snapshot_weightings_generators, along=snapshot, offset=1, edge='wrap')"
    where: "Process_output_delay > 0"
    description: >-
      the same for a delayed process port (#299)
  Process_marginal_cost_quadratic_without_risk_preference:
    holds: "Process_marginal_cost_quadratic == 0"
    where: "CVaR_omega"
    description: >-
      a quadratic cost puts a square into every `CVaR-excess` row, and PyPSA
      refuses quadratic costs under any risk preference
      (`optimize.py:470-477`), `omega = 0` included. Data prep writes a
      `CVaR_omega` row only where a risk preference is set
  Process_came_in_running_unless_committable:
    holds: "Process_status_initial == 1"
    where: "NOT Process_committable AND (Process_ramp_limit_up OR Process_ramp_limit_down OR Process_ramp_limit_start_up OR Process_ramp_limit_shut_down)"
    description: >-
      PyPSA reads `up_time_before` of a process that is not committable in its
      ramp rows, which a ramp limit, a start-up ramp or a shut-down ramp
      alone builds (`constraints.py:1018-1019`). Where it is zero, PyPSA
      builds a row at the first snapshot with nothing carried in, and caps
      the process there at zero, or at its start-up ramp where another process of
      the component is committable with a fixed build
      (`constraints.py:1063-1066`, `1082-1084`). PyPSA documents
      the attribute as read only for a committable process and does not check
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
| $`\mathit{tech\_capacity\_expansion}`$ | `tech_capacity_expansion` over $`\mathcal{G}`$, an expression this file adds `Process_tech_capacity_expansion` to |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Process_opex`, `Process_commitment_opex` to |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `Process_capex` to |
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{Y} \times \mathcal{I}`$, an expression this file adds `Process_additions` to |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$, an expression this file adds `Process_injection` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` with $`\mathrm{Process\_maintenance\_cover} \subseteq \Xi \times \mathcal{J} \times \mathcal{T} \times \mathcal{T}`$, `Process_maintenance_cover` is `absent` where the data has no row — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y},\ \mathrm{Process\_maintenance\_cover} \subseteq \Xi \times \mathcal{J} \times \mathcal{T} \times \mathcal{T}`$, `Process_maintenance_cover` is `absent` where the data has no row — dispatch periods |
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Process\_output\_bus}: \mathcal{R} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{J}`$ | index $`j`$ — `process` with $`\mathrm{Process\_carrier}: \mathcal{J} \to \mathcal{I},\ \mathrm{Process\_output\_process}: \mathcal{R} \to \mathcal{J},\ \mathrm{Process\_maintenance\_cover} \subseteq \Xi \times \mathcal{J} \times \mathcal{T} \times \mathcal{T}`$, `Process_maintenance_cover` is `absent` where the data has no row — generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate |
| $`\mathcal{R}`$ | index $`r`$ — `process_output` with $`\mathrm{Process\_output\_process}: \mathcal{R} \to \mathcal{J},\ \mathrm{Process\_output\_bus}: \mathcal{R} \to \mathcal{N}`$ — a process's ports, one label per port a process declares — PyPSA's `bus0`, `bus1`, … each carry a signed `rate`, so a process of any number of ports is one term in the balance, data prep |
| $`\mathcal{G}`$ | index $`g`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods — PyPSA's `investment_periods` |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` with $`\mathrm{Process\_carrier}: \mathcal{J} \to \mathcal{I}`$ — energy carriers, what a growth limit is set per |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{z}^{\mathrm{nom}}`$ | `Process_p_nom` over $`\Xi \times \mathcal{J}`$ — nominal internal power |
| $`\mathrm{ext}^{z}`$ | `Process_p_nom_extendable` over $`\mathcal{J}`$ — whether the nominal internal power is a decision |
| $`\underline{\mathrm{z}}`$ | `Process_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — least internal power, per unit of nominal power — negative for a process that runs both ways |
| $`\overline{\mathrm{z}}`$ | `Process_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — most internal power, per unit of nominal power |
| $`\alpha`$ | `Process_rate` over $`\Xi \times \mathcal{T} \times \mathcal{R}`$ — the energy a port draws or delivers per unit of internal power, PyPSA's `rate0`, `rate1`, … read long — negative where the port withdraws, positive where it injects; a link is a process whose `bus0` rate is minus one and whose output rates are its efficiencies. Read at the snapshot the transfer arrives, so a delayed port transfers at its arrival snapshot's rate (`constraints.py:1498`) |
| $`\mathrm{d}^{z}`$ | `Process_output_delay` over $`\mathcal{R}`$ — snapshots a port's transfer lags its process's internal power — PyPSA's `delay0`, `delay1`, … read long, divided by the `snapshot_weightings.generators` value and rounded up in data prep; zero for a port that transfers at once. A port has the same delay in every scenario, as a link's port has |
| $`\mathrm{cyc}^{z}`$ | `Process_output_cyclic_delay` over $`\mathcal{R}`$ — whether a delayed port's transfer wraps from the end of its investment period — PyPSA's `cyclic_delay0`, `cyclic_delay1`, …; where it does not, the energy still in transit at each period's first snapshots is lost. The flag is the same in every scenario, as the delay is |
| $`\mathrm{c}^{z}`$ | `Process_marginal_cost` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — cost of one unit of internal power |
| $`\mathrm{c}^{z,(2)}`$ | `Process_marginal_cost_quadratic` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — cost of the square of one unit of internal power |
| $`\mathrm{ru}^{z}`$ | `Process_ramp_limit_up` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, `neutral` where the data has no row — most a process may raise its internal power between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time |
| $`\mathrm{rd}^{z}`$ | `Process_ramp_limit_down` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, `neutral` where the data has no row — most a process may lower its internal power between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time |
| $`\mathrm{z}^{\mathrm{set}}`$ | `Process_p_set` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, `neutral` where the data has no row — a given internal power schedule; a process without one has no row here |
| $`\underline{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_min` over $`\Xi \times \mathcal{J}`$ — least nominal power an extendable process may be built at |
| $`\overline{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_max` over $`\Xi \times \mathcal{J}`$ — most nominal power an extendable process may be built at |
| $`\mathrm{c}^{\mathrm{cap},z}`$ | `Process_capital_cost` over $`\Xi \times \mathcal{J}`$ — cost of one unit of nominal power for the modelled horizon — PyPSA's `periodized_cost`: `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where it is given, and `capital_cost` where it is not, plus `fom_cost` (`components.py:1126-1147`, `costs.py:102-203`), data prep |
| $`\mathrm{z}^{\mathrm{nom,set}}`$ | `Process_p_nom_set` over $`\mathcal{J}`$, `neutral` where the data has no row — a given nominal power for an extendable process; one without a value has no row here |
| $`\mathrm{com}^{z}`$ | `Process_committable` over $`\mathcal{J}`$ — whether internal power is gated by an on/off status decision |
| $`\mathrm{ru}^{z,\mathrm{up}}`$ | `Process_ramp_limit_start_up` over $`\Xi \times \mathcal{J}`$, `neutral` where the data has no row — most internal power in the snapshot a process starts, per unit of nominal power; no value means no limit |
| $`\mathrm{rd}^{z,\mathrm{dn}}`$ | `Process_ramp_limit_shut_down` over $`\Xi \times \mathcal{J}`$, `neutral` where the data has no row — most internal power in the snapshot before a process stops, per unit of nominal power; no value means no limit |
| $`\mathrm{UT}^{z}`$ | `Process_min_up_time` over $`\Xi \times \mathcal{J}`$ — least snapshots a process stays on once started |
| $`\mathrm{DT}^{z}`$ | `Process_min_down_time` over $`\Xi \times \mathcal{J}`$ — least snapshots a process stays off once stopped |
| $`\mathrm{u}^{z,0}`$ | `Process_status_initial` over $`\Xi \times \mathcal{J}`$ — one where the process was on before the first snapshot, zero where off — PyPSA's `up_time_before > 0`, data prep |
| $`\mathrm{z}^{0}`$ | `Process_p_init` over $`\Xi \times \mathcal{J}`$, `neutral` where the data has no row — the internal power a process brought into the horizon — PyPSA's `p_init`, read only where the process came in running; no value means it is unknown, so the process carries no ramp row at the first snapshot |
| $`\mathrm{hold}^{z}`$ | `Process_must_stay_up` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — true while the up time a process brought into the horizon still binds — data prep, since `position()` compares against a literal rather than a parameter |
| $`\mathrm{rest}^{z}`$ | `Process_must_stay_down` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — true while the down time a process brought into the horizon still binds — PyPSA's `min_down_time - down_time_before` snapshots, where `down_time_before > 0`, data prep for the same reason |
| $`\mathrm{c}^{z,\mathrm{up}}`$ | `Process_start_up_cost` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — cost of one start in this snapshot |
| $`\mathrm{c}^{z,\mathrm{dn}}`$ | `Process_shut_down_cost` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — cost of one stop in this snapshot |
| $`\mathrm{c}^{z,\mathrm{on}}`$ | `Process_stand_by_cost` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — cost of one snapshot spent on |
| $`\mathrm{z}^{\mathrm{mod}}`$ | `Process_p_nom_mod` over $`\mathcal{J}`$, `neutral` where the data has no row — the module size a build comes in whole numbers of; no value means the build is continuous |
| $`\mathrm{N}^{z,\mathrm{fix}}`$ | `Process_modules_installed` over $`\Xi \times \mathcal{J}`$ — how many whole modules a committable build has in place: `Process_p_nom / Process_p_nom_mod` where a fixed build is modular, one where it is not, data prep. PyPSA refuses a fixed modular build whose nominal power is not a whole number of modules |
| $`\mathrm{M}^{z}`$ | `Process_big_m` over $`\Xi \times \mathcal{J}`$, `neutral` where the data has no row — the bound a committed extendable process's big-M rows release it by — the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu`, and where that keyword is not given, ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`, or 1e6 where there is none of them (`components.py:1050-1121`). Below the internal power a solve wants, it caps that internal power; data prep |
| $`\mathrm{nonneg}^{z}`$ | `Process_p_min_pu_nonneg` over $`\mathcal{J}`$ — true where none of the process's own minimums-per-unit is negative — PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep |
| $`\mathrm{mnt}^{z}`$ | `Process_maintainable` over $`\mathcal{J}`$ — whether a process must be taken off for maintenance within the horizon — in any scenario, as PyPSA takes the union over them (`components.py:1016-1019`) |
| $`\gamma^{z}`$ | `Process_maintenance_pu` over $`\Xi \times \mathcal{J}`$ — the share of the build a maintenance event takes off |
| $`\mathrm{n}^{z,\mathrm{mnt}}`$ | `Process_maintenance_events` over $`\Xi \times \mathcal{J}`$ — how many maintenance events the horizon holds |
| $`\tau^{z,\mathrm{mnt}}`$ | `Process_maintenance_duration` over $`\Xi \times \mathcal{J}`$, `neutral` where the data has no row — the hours of generator weightings one maintenance event covers — PyPSA's `maintenance_duration`; no value where the process is not maintainable. No row reads it: data prep turns it into `Process_maintenance_cover` and `Process_maintenance_start_blocked`, and the assumptions hold it to the horizon |
| $`\mathrm{blk}^{z}`$ | `Process_maintenance_start_blocked` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — true where no maintenance event may start, because the snapshots it would cover run past the end of the horizon or into one the process does not stand in — PyPSA's `active & ~valid`, from `maintenance_duration` and the generator weightings, data prep |
| $`\mathrm{on}^{z}`$ | `Process_active` over $`\mathcal{T} \times \mathcal{J}`$ — whether a process stands in a snapshot's period — PyPSA's `active`, data prep |
| $`\mathrm{act}^{z}`$ | `Process_active_asset` over $`\mathcal{J}`$ — whether a process is one of PyPSA's `active_assets` — its `active` flag alone, without build year and lifetime, so a unit that stands in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:51`) |
| $`\mathrm{W}^{z}`$ | `Process_capital_weight` over $`\mathcal{J}`$ — the sum of period weights a process stands in — PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{new}^{z}`$ | `Process_first_active` over $`\mathcal{Y} \times \mathcal{J}`$ — one in the first period a process stands in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`) |
| $`\mathrm{m}^{z}`$ | `Process_tech_capacity_weight` over $`\mathcal{G} \times \mathcal{J}`$, `neutral` where the data has no row — one where the process is in the row's carrier-and-bus set — data prep; one outside it, or one that does not stand in the row's `investment_period`, has no row |

#### Masks

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z,\mathrm{com,ext}}`$ | `Process_com_ext` over $`\mathcal{T} \times \mathcal{J}`$ — a committable process with an extendable, non-modular build that stands in the snapshot's period — PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |
| $`\mathrm{on}^{z,\mathrm{mnt,ext}}`$ | `Process_maint_ext` over $`\mathcal{T} \times \mathcal{J}`$ — a maintainable process with an extendable build, unless it is committable and modular, that stands in the snapshot's period — the maintenance rows against the chosen build |
| $`\mathrm{on}^{z,\mathrm{com}}`$ | `Process_committed` over $`\mathcal{T} \times \mathcal{J}`$ — a committable process that stands in the snapshot's period — every unit-commitment row's set |
| $`\mathrm{prev}^{z}`$ | `Process_ramps_from_previous` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — a snapshot whose ramp reads a previous output — any snapshot but its period's first, and the horizon's first where the process comes in off or carries an initial output |

#### Variables

| Symbol | Meaning |
|---|---|
| $`z`$ | `Process_p` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-p` — PyPSA's internal power `p`: a positive value drives every port at its own rate, withdrawing where the rate is negative and injecting where it is positive |
| $`N^{z}`$ | `Process_n_mod` over $`\mathcal{J}`$ — `Process-n_mod` — how many modules of an extendable modular build; none for a unit that is not active |
| $`u^{z}`$ | `Process_status` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-status` — how much of a committable process is on: an integer the rows below cap at one, or at the module count where the build is modular |
| $`\mathit{up}^{z}`$ | `Process_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-start_up` — how much of a committable process turns on this snapshot, capped as the status is |
| $`\mathit{dn}^{z}`$ | `Process_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-shut_down` — how much of a committable process turns off this snapshot, capped as the status is |
| $`\mu^{z}`$ | `Process_maintenance` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, `neutral` where the mask leaves it out — `Process-maintenance` — whether a maintainable process is in maintenance: continuous, and one exactly where an event covers the snapshot |
| $`\mu^{z,\mathrm{up}}`$ | `Process_maintenance_start` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, `neutral` where the mask leaves it out — `Process-maintenance_start` — whether a maintenance event starts in this snapshot |
| $`\mu^{z,\mathrm{nom}}`$ | `Process_maintenance_capacity` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, `neutral` where the mask leaves it out — `Process-maintenance_capacity` — the chosen build while in maintenance, zero otherwise: the product the `maintcap` rows linearize |
| $`\mu^{z,u}`$ | `Process_maintenance_status` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, `neutral` where the mask leaves it out — `Process-maintenance_status` — the status while in maintenance, zero otherwise: the product the `maint-status` rows linearize, so a unit in maintenance may also be off |
| $`Z`$ | `Process_p_nom_ext` over $`\mathcal{J}`$ — `Process-p_nom` — nominal internal power where it is a decision, for a process that is active; the parameter of the same PyPSA name carries the fixed regime |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\widetilde{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_effective` over $`\Xi \times \mathcal{J}`$ — the build a process's limits are taken against — the chosen one where it is extendable, the given one otherwise |
| $`\overleftarrow{u}^{z}`$ | `Process_previous_status` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — the commitment state a process carries into a snapshot — off at the first snapshot it stands in past the first of the horizon, as PyPSA reads a status it did not build (`constraints.py:298`), and the state carried over otherwise |
| $`\overleftarrow{u}^{\circ z}`$ | `Process_status_carried_over` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — the state a process carries over into a snapshot — the state it brought into the horizon at the first, the previous snapshot's after that |
| $`\overleftarrow{z}`$ | `Process_previous_p` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — the internal power a process carries into a snapshot — at the first, the `p_init` it brought in where it came in running and nothing where it came in off; the previous snapshot's after that |
| $`\widetilde{\mathrm{ru}}^{z}`$ | `Process_ramp_up_rate` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — the ramp limit a process's up row reads — PyPSA's `ramp_limit_up`, or the full build where it has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}^{z}`$ | `Process_ramp_down_rate` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — the ramp limit a process's down row reads — PyPSA's `ramp_limit_down`, or the full build where it has none, since a shut-down ramp alone builds the row |
| $`\widetilde{\mathrm{ru}}^{z,\mathrm{up}}`$ | `Process_start_up_rate` over $`\Xi \times \mathcal{J}`$ — the start-up ramp a process's up row reads — PyPSA's `ramp_limit_start_up`, or the full build where it has none |
| $`\widetilde{\mathrm{rd}}^{z,\mathrm{dn}}`$ | `Process_shut_down_rate` over $`\Xi \times \mathcal{J}`$ — the shut-down ramp a process's down row reads — PyPSA's `ramp_limit_shut_down`, or the full build where it has none |
| $`\widehat{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_committed` over $`\Xi \times \mathcal{J}`$ — the build a committed process's ramp rows are taken against — one module where the build is extendable and modular, the given build otherwise |
| $`\Delta^{z,+}`$ | `Process_ramp_up_allowance` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — how far a process may raise internal power between two snapshots — its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\Delta^{z,-}`$ | `Process_ramp_down_allowance` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — how far a process may lower internal power between two snapshots — its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\overrightarrow{z}`$ | `Process_output_arrival` over $`\Xi \times \mathcal{T} \times \mathcal{R}`$ — what a process transfers at a port at a snapshot — its internal power delayed by the port's `delay` within its investment period, times the port's rate at the snapshot the transfer arrives; where the port is `cyclic_delay` the delayed transfer wraps from the period's end, and where it is not the energy still in transit at the period's first snapshots is lost. A port that does not delay (`delay` zero) transfers at once, cyclic or not |
| $`\mathit{Process\_tech\_capacity\_expansion}`$ | `Process_tech_capacity_expansion` over $`\mathcal{G}`$ |
| $`\mathit{Process\_opex}`$ | `Process_opex` over $`\Xi`$ |
| $`\mathit{Process\_commitment\_opex}`$ | `Process_commitment_opex` over $`\Xi`$ |
| $`\mathit{Process\_capex}`$ | `Process_capex` (scalar) |
| $`\mathit{Process\_additions}`$ | `Process_additions` over $`\mathcal{Y} \times \mathcal{I}`$ |
| $`\mathit{Process\_injection}`$ | `Process_injection` over $`\Xi \times \mathcal{T} \times \mathcal{N}`$ |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`t \ominus^{\mathrm{relation}(t)} k`$ | `within=relation[...]` — $`t-k`$ inside the group of $`t`$ |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |

#### Masks

**`Process_com_ext`**

```math
\mathrm{on}^{z,\mathrm{com,ext}}_{t,j} \iff \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \wedge \mathrm{on}^{z}_{t,j} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_maint_ext`**

```math
\mathrm{on}^{z,\mathrm{mnt,ext}}_{t,j} \iff \mathrm{mnt}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \wedge \mathrm{on}^{z}_{t,j} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_committed`**

```math
\mathrm{on}^{z,\mathrm{com}}_{t,j} \iff \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_ramps_from_previous`**

```math
\mathrm{prev}^{z}_{\xi,t,j} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{z,0}_{\xi,j} = 0 \vee \mathrm{z}^{0}_{\xi,j} \text{ is defined} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

#### Variable domains

**`Process_p`**

```math
z_{\xi,t,j} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z}_{t,j}
```

**`Process_n_mod`**

```math
N^{z}_{j} \ge 0, N^{z}_{j} \in \mathbb{Z} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \wedge \mathrm{act}^{z}_{j}
```

**`Process_status`**

```math
u^{z}_{\xi,t,j} \ge 0, u^{z}_{\xi,t,j} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_start_up`**

```math
\mathit{up}^{z}_{\xi,t,j} \ge 0, \mathit{up}^{z}_{\xi,t,j} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_shut_down`**

```math
\mathit{dn}^{z}_{\xi,t,j} \ge 0, \mathit{dn}^{z}_{\xi,t,j} \in \mathbb{Z} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_maintenance`**

```math
0 \le \mu^{z}_{\xi,t,j} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_maintenance_start`**

```math
\mu^{z,\mathrm{up}}_{\xi,t,j} \in \{0, 1\} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_maintenance_capacity`**

```math
\mu^{z,\mathrm{nom}}_{\xi,t,j} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{t,j}
```

**`Process_maintenance_status`**

```math
\mu^{z,u}_{\xi,t,j} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right)
```

**`Process_p_nom_ext`**

```math
Z_{j} \in \mathbb{R} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j}
```

#### Definitions

**`Process_p_nom_effective`**

```math
\widetilde{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} = \begin{cases} Z_{j} & \text{if } \mathrm{ext}^{z}_{j} \\ \mathrm{z}^{\mathrm{nom}}_{\xi,j} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J}
```

**`Process_previous_status`**

```math
\overleftarrow{u}^{z}_{\xi,t,j} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{z}_{t - 1,j} \\ \overleftarrow{u}^{\circ z}_{\xi,t,j} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_status_carried_over`**

```math
\overleftarrow{u}^{\circ z}_{\xi,t,j} = \begin{cases} \mathrm{u}^{z,0}_{\xi,j} & \text{if } \mathrm{pos}(t) = 0 \\ u^{z}_{\xi,t - 1,j} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_previous_p`**

```math
\overleftarrow{z}_{\xi,t,j} = \begin{cases} \mathrm{u}^{z,0}_{\xi,j} \cdot \mathrm{z}^{0}_{\xi,j} & \text{if } \mathrm{pos}(t) = 0 \\ z_{\xi,t - 1,j} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_ramp_up_rate`**

```math
\widetilde{\mathrm{ru}}^{z}_{\xi,t,j} = \begin{cases} \mathrm{ru}^{z}_{\xi,t,j} & \text{if } \mathrm{ru}^{z}_{\xi,t,j} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_ramp_down_rate`**

```math
\widetilde{\mathrm{rd}}^{z}_{\xi,t,j} = \begin{cases} \mathrm{rd}^{z}_{\xi,t,j} & \text{if } \mathrm{rd}^{z}_{\xi,t,j} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_start_up_rate`**

```math
\widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{\xi,j} = \begin{cases} \mathrm{ru}^{z,\mathrm{up}}_{\xi,j} & \text{if } \mathrm{ru}^{z,\mathrm{up}}_{\xi,j} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J}
```

**`Process_shut_down_rate`**

```math
\widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} = \begin{cases} \mathrm{rd}^{z,\mathrm{dn}}_{\xi,j} & \text{if } \mathrm{rd}^{z,\mathrm{dn}}_{\xi,j} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J}
```

**`Process_p_nom_committed`**

```math
\widehat{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} = \begin{cases} \mathrm{z}^{\mathrm{mod}}_{j} & \text{if } \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \\ \mathrm{z}^{\mathrm{nom}}_{\xi,j} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J}
```

**`Process_ramp_up_allowance`**

```math
\Delta^{z,+}_{\xi,t,j} = \begin{cases} \widetilde{\mathrm{ru}}^{z}_{\xi,t,j} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot \overleftarrow{u}^{z}_{\xi,t,j} + \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{\xi,j} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot \left( u^{z}_{\xi,t,j} - \overleftarrow{u}^{z}_{\xi,t,j} \right) & \text{if } \mathrm{com}^{z}_{j} \\ \widetilde{\mathrm{ru}}^{z}_{\xi,t,j} \cdot \widetilde{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_ramp_down_allowance`**

```math
\Delta^{z,-}_{\xi,t,j} = \begin{cases} \widetilde{\mathrm{rd}}^{z}_{\xi,t,j} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t,j} + \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot \left( \overleftarrow{u}^{z}_{\xi,t,j} - u^{z}_{\xi,t,j} \right) & \text{if } \mathrm{com}^{z}_{j} \\ \widetilde{\mathrm{rd}}^{z}_{\xi,t,j} \cdot \widetilde{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J}
```

**`Process_output_arrival`**

```math
\overrightarrow{z}_{\xi,t,r} = \begin{cases} z_{\xi,t \ominus^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{z},\mathrm{Process\_output\_process}(r)} \cdot \alpha_{\xi,t,r} & \text{if } \mathrm{cyc}^{z}_{r} \\ z_{\xi,t \boxminus_{0}^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{z},\mathrm{Process\_output\_process}(r)} \cdot \alpha_{\xi,t,r} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ r \in \mathcal{R}
```

**`Process_tech_capacity_expansion`**

```math
\mathit{Process\_tech\_capacity\_expansion}_{g} = \sum_{j \in \mathcal{J}} Z_{j} \cdot \mathrm{m}^{z}_{g,j} \qquad \forall\, g \in \mathcal{G}
```

**`Process_opex`**

```math
\mathit{Process\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} z_{\xi,t,j} \cdot \mathrm{c}^{z}_{\xi,t,j} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} z_{\xi,t,j} \cdot z_{\xi,t,j} \cdot \mathrm{c}^{z,(2)}_{\xi,t,j} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

**`Process_commitment_opex`**

```math
\mathit{Process\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} u^{z}_{\xi,t,j} \cdot \mathrm{c}^{z,\mathrm{on}}_{\xi,t,j} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} \mathit{up}^{z}_{\xi,t,j} \cdot \mathrm{c}^{z,\mathrm{up}}_{\xi,t,j} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} \mathit{dn}^{z}_{\xi,t,j} \cdot \mathrm{c}^{z,\mathrm{dn}}_{\xi,t,j} \qquad \forall\, \xi \in \Xi
```

**`Process_capex`**

```math
\mathit{Process\_capex} = \sum_{\xi \in \Xi,\ j \in \mathcal{J}} \pi_{\xi} \cdot Z_{j} \cdot \mathrm{c}^{\mathrm{cap},z}_{\xi,j} \cdot \mathrm{W}^{z}_{j}
```

**`Process_additions`**

```math
\mathit{Process\_additions}_{y,i} = \sum_{j \in \mathcal{J} \,:\, \mathrm{Process\_carrier}(j) = i} Z_{j} \cdot \mathrm{new}^{z}_{y,j} \qquad \forall\, y \in \mathcal{Y},\ i \in \mathcal{I}
```

**`Process_injection`**

```math
\mathit{Process\_injection}_{\xi,t,n} = \sum_{r \in \mathcal{R} \,:\, \mathrm{Process\_output\_bus}(r) = n} \overrightarrow{z}_{\xi,t,r} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ n \in \mathcal{N}
```

#### Subject to

**`Process_fix_p_lower`**

```math
z_{\xi,t,j} \ge \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot \left( 1 - \gamma^{z}_{\xi,j} \cdot \mu^{z}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \neg \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_fix_p_upper`**

```math
z_{\xi,t,j} \le \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot \left( 1 - \gamma^{z}_{\xi,j} \cdot \mu^{z}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \neg \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_ext_p_lower`**

```math
z_{\xi,t,j} \ge \underline{\mathrm{z}}_{\xi,t,j} \cdot \left( Z_{j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,\mathrm{nom}}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_ext_p_upper`**

```math
z_{\xi,t,j} \le \overline{\mathrm{z}}_{\xi,t,j} \cdot \left( Z_{j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,\mathrm{nom}}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_ext_p_nom_lower`**

```math
Z_{j} \ge \underline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j}
```

**`Process_ext_p_nom_upper`**

```math
Z_{j} \le \overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j} \wedge \overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \text{ is defined}
```

**`Process_p_nom_set`**

```math
Z_{j} = \mathrm{z}^{\mathrm{nom,set}}_{j} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j} \wedge \mathrm{z}^{\mathrm{nom,set}}_{j} \text{ is defined}
```

**`Process_com_p_lower`**

```math
z_{\xi,t,j} \ge \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot \left( u^{z}_{\xi,t,j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,u}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_com_p_upper`**

```math
z_{\xi,t,j} \le \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot \left( u^{z}_{\xi,t,j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,u}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_com_transition_start_up`**

```math
\mathit{up}^{z}_{\xi,t,j} \ge u^{z}_{\xi,t,j} - \overleftarrow{u}^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_com_transition_shut_down`**

```math
\mathit{dn}^{z}_{\xi,t,j} \ge \overleftarrow{u}^{z}_{\xi,t,j} - u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_com_up_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}^{z}} \mathit{up}^{z}_{\xi,t',j} \le u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{UT}^{z}_{\xi,j} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Process_com_down_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}^{z}} \mathit{dn}^{z}_{\xi,t',j} \le 1 - u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{DT}^{z}_{\xi,j} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Process_com_status_must_stay_up`**

```math
u^{z}_{\xi,t,j} = 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{hold}^{z}_{\xi,t,j}
```

**`Process_com_status_must_stay_down`**

```math
u^{z}_{\xi,t,j} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{rest}^{z}_{\xi,t,j}
```

**`Process_p_ramp_limit_up_run_big_m`**

```math
z_{\xi,t,j} - \overleftarrow{z}_{\xi,t,j} \le \widetilde{\mathrm{ru}}^{z}_{\xi,t,j} \cdot Z_{j} + \mathrm{M}^{z}_{\xi,j} - \mathrm{M}^{z}_{\xi,j} \cdot \overleftarrow{u}^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j} \wedge \left( \mathrm{ru}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{\xi,j} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{\xi,t,j}
```

**`Process_p_ramp_limit_up_start_big_m`**

```math
z_{\xi,t,j} - \overleftarrow{z}_{\xi,t,j} \le \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{\xi,j} \cdot Z_{j} + \mathrm{M}^{z}_{\xi,j} - \mathrm{M}^{z}_{\xi,j} \cdot \mathit{up}^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j} \wedge \left( \mathrm{ru}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{\xi,j} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{\xi,t,j}
```

**`Process_p_ramp_limit_down_run_big_m`**

```math
\overleftarrow{z}_{\xi,t,j} - z_{\xi,t,j} \le \widetilde{\mathrm{rd}}^{z}_{\xi,t,j} \cdot Z_{j} + \mathrm{M}^{z}_{\xi,j} - \mathrm{M}^{z}_{\xi,j} \cdot u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j} \wedge \left( \mathrm{rd}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{\xi,j} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{\xi,t,j}
```

**`Process_p_ramp_limit_down_shut_big_m`**

```math
\overleftarrow{z}_{\xi,t,j} - z_{\xi,t,j} \le \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot Z_{j} + \mathrm{M}^{z}_{\xi,j} - \mathrm{M}^{z}_{\xi,j} \cdot \mathit{dn}^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j} \wedge \left( \mathrm{rd}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{\xi,j} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{\xi,t,j}
```

**`Process_p_nom_modularity`**

```math
Z_{j} = \mathrm{z}^{\mathrm{mod}}_{j} \cdot N^{z}_{j} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \wedge \mathrm{act}^{z}_{j}
```

**`Process_com_ext_p_upper_cap`**

```math
z_{\xi,t,j} \le \overline{\mathrm{z}}_{\xi,t,j} \cdot \left( Z_{j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,\mathrm{nom}}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j}
```

**`Process_com_ext_p_upper_big_m`**

```math
z_{\xi,t,j} \le \mathrm{M}^{z}_{\xi,j} \cdot u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j}
```

**`Process_com_ext_p_lower`**

```math
z_{\xi,t,j} \ge \underline{\mathrm{z}}_{\xi,t,j} \cdot \left( Z_{j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,\mathrm{nom}}_{\xi,t,j} \right) + \mathrm{M}^{z}_{\xi,j} \cdot u^{z}_{\xi,t,j} - \mathrm{M}^{z}_{\xi,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j}
```

**`Process_com_ext_p_lower_nonneg`**

```math
z_{\xi,t,j} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{t,j} \wedge \mathrm{nonneg}^{z}_{j}
```

**`Process_com_mod_p_lower`**

```math
z_{\xi,t,j} \ge \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{mod}}_{j} \cdot \left( u^{z}_{\xi,t,j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,u}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_com_mod_p_upper`**

```math
z_{\xi,t,j} \le \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{mod}}_{j} \cdot \left( u^{z}_{\xi,t,j} - \gamma^{z}_{\xi,j} \cdot \mu^{z,u}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_status_p_fixed_upper`**

```math
u^{z}_{\xi,t,j} \le \mathrm{N}^{z,\mathrm{fix}}_{\xi,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_start_up_p_fixed_upper`**

```math
\mathit{up}^{z}_{\xi,t,j} \le \mathrm{N}^{z,\mathrm{fix}}_{\xi,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_shut_down_p_fixed_upper`**

```math
\mathit{dn}^{z}_{\xi,t,j} \le \mathrm{N}^{z,\mathrm{fix}}_{\xi,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_status_p_nom_variable_upper`**

```math
u^{z}_{\xi,t,j} \le N^{z}_{j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_start_up_p_nom_variable_upper`**

```math
\mathit{up}^{z}_{\xi,t,j} \le N^{z}_{j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_shut_down_p_nom_variable_upper`**

```math
\mathit{dn}^{z}_{\xi,t,j} \le N^{z}_{j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_maint_event_count`**

```math
\sum_{t \in \mathcal{T}} \mu^{z,\mathrm{up}}_{\xi,t,j} = \mathrm{n}^{z,\mathrm{mnt}}_{\xi,j} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j}
```

**`Process_maint_window`**

```math
\mu^{z}_{\xi,t,j} = \sum_{t' \in \mathcal{T} \,:\, \left( \xi,\ j,\ t',\ t \right) \in \mathrm{Process\_maintenance\_cover}} \mu^{z,\mathrm{up}}_{\xi,t',j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_maint_start_horizon`**

```math
\mu^{z,\mathrm{up}}_{\xi,t,j} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{t,j} \wedge \mathrm{blk}^{z}_{\xi,t,j}
```

**`Process_maintcap_upper`**

```math
\mu^{z,\mathrm{nom}}_{\xi,t,j} \le Z_{j} - \underline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot \left( 1 - \mu^{z}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{t,j}
```

**`Process_maintcap_upper_nommax`**

```math
\mu^{z,\mathrm{nom}}_{\xi,t,j} \le \overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot \mu^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{t,j}
```

**`Process_maintcap_lower_nommax`**

```math
\mu^{z,\mathrm{nom}}_{\xi,t,j} \ge Z_{j} - \overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot \left( 1 - \mu^{z}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{t,j}
```

**`Process_maintcap_lower_nommin`**

```math
\mu^{z,\mathrm{nom}}_{\xi,t,j} \ge \underline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} \cdot \mu^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{t,j} \wedge \underline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} > 0
```

**`Process_maint_status_le_status`**

```math
\mu^{z,u}_{\xi,t,j} \le u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_maint_status_le_maint`**

```math
\mu^{z,u}_{\xi,t,j} \le \mu^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_maint_status_lb`**

```math
\mu^{z,u}_{\xi,t,j} \ge u^{z}_{\xi,t,j} + \mu^{z}_{\xi,t,j} - 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_maint_modstatus_le_status`**

```math
\mu^{z,u}_{\xi,t,j} \le u^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_maint_modstatus_le_maint`**

```math
\mu^{z,u}_{\xi,t,j} \le \frac{\overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j}}{\mathrm{z}^{\mathrm{mod}}_{j}} \cdot \mu^{z}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_maint_modstatus_lb`**

```math
\mu^{z,u}_{\xi,t,j} \ge u^{z}_{\xi,t,j} - \frac{\overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j}}{\mathrm{z}^{\mathrm{mod}}_{j}} \cdot \left( 1 - \mu^{z}_{\xi,t,j} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{t,j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_p_ramp_limit_up`**

```math
z_{\xi,t,j} - \overleftarrow{z}_{\xi,t,j} \le \Delta^{z,+}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \left( \mathrm{ru}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{\xi,j} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right) \wedge \mathrm{prev}^{z}_{\xi,t,j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_p_ramp_limit_down`**

```math
\overleftarrow{z}_{\xi,t,j} - z_{\xi,t,j} \le \Delta^{z,-}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \left( \mathrm{rd}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{\xi,j} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right) \wedge \mathrm{prev}^{z}_{\xi,t,j} \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_p_set`**

```math
z_{\xi,t,j} = \mathrm{z}^{\mathrm{set}}_{\xi,t,j} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{z}^{\mathrm{set}}_{\xi,t,j} \text{ is defined} \wedge \mathrm{on}^{z}_{t,j}
```

#### Assumptions

**`Process_maintenance_events_positive`**

```math
\mathrm{n}^{z,\mathrm{mnt}}_{\xi,j} > 0 \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j}
```

**`Process_maintenance_duration_positive`**

```math
\tau^{z,\mathrm{mnt}}_{\xi,j} > 0 \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j}
```

**`Process_maintenance_duration_fits_the_horizon`**

```math
\tau^{z,\mathrm{mnt}}_{\xi,j} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j}
```

**`Process_maintenance_events_fit_the_horizon`**

```math
\tau^{z,\mathrm{mnt}}_{\xi,j} \cdot \mathrm{n}^{z,\mathrm{mnt}}_{\xi,j} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j}
```

**`Process_maintenance_build_cap_is_finite`**

```math
\overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} < \infty \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{ext}^{z}_{j}
```

**`Process_maintenance_module_count_is_finite`**

```math
\overline{\mathrm{z}}^{\mathrm{nom}}_{\xi,j} < \infty \qquad \forall\, \xi \in \Xi,\ j \in \mathcal{J} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_output_delay_under_uniform_weighting`**

```math
\mathrm{w}^{\mathrm{gen}}_{t} = \mathrm{w}^{\mathrm{gen}}_{t \ominus 1} \qquad \forall\, t \in \mathcal{T},\ r \in \mathcal{R} \,:\, \mathrm{d}^{z}_{r} > 0
```

**`Process_marginal_cost_quadratic_without_risk_preference`**

```math
\mathrm{c}^{z,(2)}_{\xi,t,j} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \omega \text{ is defined}
```

**`Process_came_in_running_unless_committable`**

```math
\mathrm{u}^{z,0}_{\xi,j} = 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \neg \mathrm{com}^{z}_{j} \wedge \left( \mathrm{ru}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{rd}^{z}_{\xi,t,j} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{\xi,j} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{\xi,j} \text{ is defined} \right)
```
<!-- gallery:end -->
