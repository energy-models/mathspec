<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Processes

This file states PyPSA's `Process`. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It adds a [term](../../reference/language/named.md#adds_to) to each of these sums: `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions` and `Bus_injection`. `Process_output_arrival` is what a process transfers at a port: its internal power, delayed by the port's `delay` within its investment period.

<!-- gallery:begin -->
```yaml
given:
  parameters:
    snapshot_weightings_objective: { dims: [snapshot] }
    Process_committable: { dims: [process], dtype: bool }
    Process_maintenance_pu: { dims: [scenario, process] }
    scenario_weight: { dims: [scenario] }
    CVaR_omega: { dims: [] }
    period_weight_objective: { dims: [period] }
    snapshot_weightings_generators: { dims: [snapshot] }
  variables:
    Process_maintenance: { dims: [scenario, snapshot, process] }
    Process_maintenance_capacity: { dims: [scenario, snapshot, process] }
  expressions:
    energy_limit_weight: { dims: [snapshot] }
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
  process:
    description: generalised multi-port converters, each with an internal power that every port draws or delivers at its own rate
  process_output:
    description: >-
      a process's ports, one label per port a process declares. The labels are
      PyPSA's `bus0`, `bus1`, …, each with a signed `rate`, data prep. A
      process of any number of ports is then one term in the balance
  global_constraint:
    description: PyPSA's `GlobalConstraint` rows, one label per declared limit
  period:
    description: investment periods. It is PyPSA's `investment_periods`
    dtype: int
    ordered: true
  carrier:
    description: energy carriers, what a growth limit is set per

maps:
  snapshot:
    period:
      description: the investment period a snapshot falls in
      refers: period
  process:
    carrier:
      description: the carrier a process converts from
      refers: carrier
  process_output:
    process:
      description: the process a port belongs to
      refers: process
    bus:
      description: >-
        the bus a port draws from or delivers to. It is PyPSA's `bus0`, `bus1`,
        … columns. A process of three ports is three labels here rather than a
        third relation, so the file states any number of them
      refers: bus

parameters:
  Process_p_nom:
    description: nominal internal power
    dims: [scenario, process]
  Process_p_nom_extendable:
    description: whether the nominal internal power is a decision
    dims: [process]
    dtype: bool
  Process_p_min_pu:
    description: "least internal power, per unit of nominal power: negative for a process that runs both ways"
    dims: [scenario, snapshot, process]
  Process_p_max_pu:
    description: most internal power, per unit of nominal power
    dims: [scenario, snapshot, process]
  Process_rate:
    description: >-
      the energy a port draws or delivers per unit of internal power (PyPSA's
      `rate0`, `rate1`, … read long). It is negative where the port withdraws
      and positive where it injects. A link is a process whose `bus0` rate is
      minus one and whose output rates are its efficiencies. The rate at the
      snapshot the transfer arrives applies, so a delayed port transfers at
      its arrival snapshot's rate (`constraints.py:1575`)
    dims: [scenario, snapshot, process_output]
  Process_output_delay:
    description: >-
      snapshots a port's transfer lags its process's internal power (PyPSA's
      `delay0`, `delay1`, … read long). In data prep you divide it by the
      `snapshot_weightings.generators` value and round it up. It is zero for a
      port that transfers at once. A port has the same delay in every
      scenario, as a link's port has
    dims: [process_output]
    dtype: int
  Process_output_cyclic_delay:
    description: >-
      whether a delayed port's transfer wraps from the end of its investment
      period (PyPSA's `cyclic_delay0`, `cyclic_delay1`, …). Where it does not,
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
  Process_p_set:
    description: a given internal power schedule. A process without one has no row here
    dims: [scenario, snapshot, process]
    missing: absent
  Process_e_sum_min:
    description: least energy of its internal power over the horizon. It is minus infinity where no floor is meant
    dims: [scenario, process]
  Process_e_sum_max:
    description: most energy of its internal power over the horizon. It is infinity where no cap is meant
    dims: [scenario, process]
  Process_p_nom_min:
    description: least nominal power an extendable process may be built at
    dims: [scenario, process]
  Process_p_nom_max:
    description: most nominal power an extendable process may be built at
    dims: [scenario, process]
  Process_capital_cost:
    description: >-
      cost of one unit of nominal power for the modelled horizon (PyPSA's
      `periodized_cost`), data prep. It is `overnight_cost` as an annuity over
      `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is
      given, and `capital_cost` where it is not. Both add `fom_cost`
      (`components.py:1157-1178`, `costs.py:102-203`)
    dims: [scenario, process]
  Process_p_nom_set:
    description: a given nominal power for an extendable process. One without a value has no row here
    dims: [process]
    missing: absent
  Process_p_nom_mod:
    description: the module size a build comes in whole numbers of. No value means the build is continuous
    dims: [process]
    missing: absent
  Process_modules_installed:
    description: >-
      how many whole modules a committable build has in place, data prep. It
      is `Process_p_nom / Process_p_nom_mod` where a fixed build is modular,
      and one where it is not. PyPSA refuses a fixed modular build whose
      nominal power is not a whole number of modules
    dims: [scenario, process]
  Process_p_min_pu_nonneg:
    description: >-
      true where none of the process's own minimums-per-unit is negative. It
      is PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and
      scenario, data prep
    dims: [process]
    dtype: bool
  Process_active:
    description: whether a process is active in a snapshot's period. It is PyPSA's `active`, data prep
    dims: [snapshot, process]
    dtype: bool
  Process_active_asset:
    description: >-
      whether a process is one of PyPSA's `active_assets`, by its `active`
      flag alone, without build year and lifetime. A unit that is active in no
      snapshot of the horizon still counts. PyPSA refuses one that differs by
      scenario (`constants.py:54`)
    dims: [process]
    dtype: bool
  Process_capital_weight:
    description: the sum of period weights a process is active in. It is PyPSA's `active * period_weighting`, summed, data prep
    dims: [process]
  Process_first_active:
    description: >-
      one in the first period a process is active in, zero elsewhere, data prep.
      PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`)
    dims: [period, process]
  Process_tech_capacity_weight:
    description: >-
      one where the process is in the row's carrier-and-bus set, data prep.
      One outside it, or one that is not active in the row's
      `investment_period`, has no row
    dims: [global_constraint, process]
    missing: absent

variables:
  Process_p:
    description: >-
      `Process-p` — PyPSA's internal power `p`. A positive value drives every
      port at its own rate, withdrawing where the rate is negative and
      injecting where it is positive
    dims: [scenario, snapshot, process]
    where: Process_active
  Process_n_mod:
    description: "`Process-n_mod` — how many modules of an extendable modular build. A unit that is not active has none"
    dims: [process]
    where: Process_p_nom_extendable AND Process_p_nom_mod > 0 AND Process_active_asset
    domain: integer
    bounds:
      lower: 0
  Process_p_nom_ext:
    description: >-
      `Process-p_nom` — nominal internal power where it is a decision, for a
      process that is active. A fixed build is the parameter of the same PyPSA
      name
    dims: [process]
    where: Process_p_nom_extendable AND Process_active_asset

expressions:
  Process_p_nom_effective:
    description: "the build a process's limits are taken against: the chosen one where it is extendable, the given one otherwise"
    dims: [scenario, process]
    cases:
      extendable: { when: Process_p_nom_extendable, expression: Process_p_nom_ext }
    otherwise: Process_p_nom
  Process_modules:
    description: >-
      how many modules a committed process's status counts: the chosen number
      where the build is extendable and modular, and the modules installed
      otherwise (`constraints.py:656-661`)
    dims: [scenario, process]
    cases:
      chosen: { when: Process_p_nom_extendable AND Process_p_nom_mod > 0, expression: Process_n_mod }
    otherwise: Process_modules_installed
  Process_p_nom_committed:
    description: >-
      the build a committed process's ramp rows are taken against: one module
      where the build is modular, since its status counts modules, and the
      given build otherwise (`constraints.py:1131-1134`)
    dims: [scenario, process]
    cases:
      modular_build: { when: "Process_p_nom_mod > 0", expression: Process_p_nom_mod }
    otherwise: Process_p_nom
  Process_output_arrival:
    description: >-
      what a process transfers at a port at a snapshot. It is its internal
      power delayed by the port's `delay` within its investment period. It is
      multiplied by the port's rate at the snapshot the transfer arrives.
      Where the port is `cyclic_delay`, the delayed transfer wraps from the
      period's end. Where it is not, the energy still in transit at the
      period's first snapshots is lost. A port that does not delay (`delay`
      zero) transfers at once, cyclic or not
    dims: [scenario, snapshot, process_output]
    cases:
      wrapping:
        when: Process_output_cyclic_delay
        expression: shift(at(Process_p, by=process_output[process]), along=snapshot, offset=Process_output_delay, edge='wrap', within=snapshot[period]) * Process_rate
    otherwise: shift(at(Process_p, by=process_output[process]), along=snapshot, offset=Process_output_delay, edge=0, within=snapshot[period]) * Process_rate
  Process_tech_capacity_expansion:
    expression: sum(Process_p_nom_ext * Process_tech_capacity_weight, over=process)
    adds_to: tech_capacity_expansion
  Process_opex:
    expression: >-
      sum(sum(((Process_p * Process_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot[period]), over=process), over=snapshot)
      + sum(sum((((Process_p * Process_p) * Process_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot[period]), over=process), over=snapshot)
    adds_to: scenario_opex
  Process_capex:
    expression: sum(scenario_weight * Process_p_nom_ext * Process_capital_cost * Process_capital_weight)
    adds_to: total_cost
  Process_additions:
    expression: >-
      sum(Process_p_nom_ext * Process_first_active, over=process, by=process[carrier])
    adds_to: Carrier_additions
  Process_injection:
    expression: >-
      sum(Process_output_arrival, over=process_output, by=process_output[bus])
    adds_to: Bus_injection

conditions:
  Process_committed:
    description: >-
      a committable process that is active in the snapshot's period: every
      unit-commitment row's set
    condition: Process_committable AND Process_active

constraints:
  Process_e_sum_min:
    description: "`Process-e_sum_min` — energy of the internal power over the horizon, each period weighted by its years, is at least its floor. A floor of minus infinity is no row, and so is a process active in no snapshot"
    dims: [scenario, process]
    where: Process_e_sum_min AND count(Process_active, over=snapshot) > 0
    expression: sum(Process_p * energy_limit_weight, over=snapshot) >= Process_e_sum_min
  Process_e_sum_max:
    description: "`Process-e_sum_max` — energy of the internal power over the horizon, each period weighted by its years, is at most its budget. A budget of infinity is no row, and so is a process active in no snapshot"
    dims: [scenario, process]
    where: Process_e_sum_max AND count(Process_active, over=snapshot) > 0
    expression: sum(Process_p * energy_limit_weight, over=snapshot) <= Process_e_sum_max
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
    description: "`Process-ext-p_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
    dims: [scenario, process]
    where: Process_p_nom_extendable AND Process_active_asset AND Process_p_nom_max
    expression: Process_p_nom_ext <= Process_p_nom_max
  Process_p_nom_set:
    description: "`Process-p_nom_set` — the chosen build pinned, wherever a value is given"
    dims: [process]
    where: Process_p_nom_extendable AND Process_active_asset AND Process_p_nom_set
    expression: Process_p_nom_ext == Process_p_nom_set
  Process_p_nom_modularity:
    description: "`Process-p_nom_modularity` — the chosen build is a whole number of modules"
    dims: [process]
    where: Process_p_nom_extendable AND Process_p_nom_mod > 0 AND Process_active_asset
    expression: Process_p_nom_ext == Process_p_nom_mod * Process_n_mod
  Process_p_set:
    description: "`Process-p_set` — internal power pinned to the given schedule, wherever one is given"
    dims: [scenario, snapshot, process]
    where: Process_p_set AND Process_active
    expression: Process_p == Process_p_set

assumptions:
  Process_output_delay_under_uniform_weighting:
    holds: "snapshot_weightings_generators == shift(snapshot_weightings_generators, along=snapshot, offset=1, edge='wrap')"
    where: "Process_output_delay > 0"
    description: >-
      the same for a delayed process port (#299)
  Process_marginal_cost_quadratic_without_risk_preference:
    holds: "Process_marginal_cost_quadratic == 0"
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
| $`\mathrm{com}^{z}`$ | `Process_committable` over $`\mathcal{J}`$, data another file declares |
| $`\gamma^{z}`$ | `Process_maintenance_pu` over $`\mathcal{J} \times \Xi`$, data another file declares |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$, data another file declares |
| $`\pi`$ | `scenario_weight` over $`\Xi`$, data another file declares |
| $`\mathrm{w}^{\mathrm{gen}}`$ | `snapshot_weightings_generators` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$, data another file declares |
| $`\mu^{z}`$ | `Process_maintenance` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`\mu^{z,\mathrm{nom}}`$ | `Process_maintenance_capacity` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, an expression this file adds `Process_injection` to |
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{I} \times \mathcal{Y}`$, an expression this file adds `Process_additions` to |
| $`\mathit{w}^{E}`$ | `energy_limit_weight` over $`\mathcal{T}`$, an expression another file defines |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Process_opex` to |
| $`\mathit{tech\_capacity\_expansion}`$ | `tech_capacity_expansion` over $`\mathcal{G}`$, an expression this file adds `Process_tech_capacity_expansion` to |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `Process_capex` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{bus}: \mathcal{R} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` with $`\mathrm{carrier}: \mathcal{J} \to \mathcal{I}`$ — energy carriers, what a growth limit is set per |
| $`\mathcal{G}`$ | index $`g`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods. It is PyPSA's `investment_periods` |
| $`\mathcal{J}`$ | index $`j`$ — `process` with $`\mathrm{carrier}: \mathcal{J} \to \mathcal{I},\ \mathrm{process}: \mathcal{R} \to \mathcal{J}`$ — generalised multi-port converters, each with an internal power that every port draws or delivers at its own rate |
| $`\mathcal{R}`$ | index $`r`$ — `process_output` with $`\mathrm{bus}: \mathcal{R} \to \mathcal{N},\ \mathrm{process}: \mathcal{R} \to \mathcal{J}`$ — a process's ports, one label per port a process declares. The labels are PyPSA's `bus0`, `bus1`, …, each with a signed `rate`, data prep. A process of any number of ports is then one term in the balance |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z}`$ | `Process_active` over $`\mathcal{J} \times \mathcal{T}`$ — whether a process is active in a snapshot's period. It is PyPSA's `active`, data prep |
| $`\mathrm{act}^{z}`$ | `Process_active_asset` over $`\mathcal{J}`$ — whether a process is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{c}^{\mathrm{cap},z}`$ | `Process_capital_cost` over $`\mathcal{J} \times \Xi`$ — cost of one unit of nominal power for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1157-1178`, `costs.py:102-203`) |
| $`\mathrm{W}^{z}`$ | `Process_capital_weight` over $`\mathcal{J}`$ — the sum of period weights a process is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\overline{\mathrm{E}}^{z}`$ | `Process_e_sum_max` over $`\mathcal{J} \times \Xi`$ — most energy of its internal power over the horizon. It is infinity where no cap is meant |
| $`\underline{\mathrm{E}}^{z}`$ | `Process_e_sum_min` over $`\mathcal{J} \times \Xi`$ — least energy of its internal power over the horizon. It is minus infinity where no floor is meant |
| $`\mathrm{new}^{z}`$ | `Process_first_active` over $`\mathcal{Y} \times \mathcal{J}`$ — one in the first period a process is active in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`) |
| $`\mathrm{c}^{z}`$ | `Process_marginal_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one unit of internal power |
| $`\mathrm{c}^{z,(2)}`$ | `Process_marginal_cost_quadratic` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of the square of one unit of internal power |
| $`\mathrm{N}^{z,\mathrm{fix}}`$ | `Process_modules_installed` over $`\mathcal{J} \times \Xi`$ — how many whole modules a committable build has in place, data prep. It is `Process_p_nom / Process_p_nom_mod` where a fixed build is modular, and one where it is not. PyPSA refuses a fixed modular build whose nominal power is not a whole number of modules |
| $`\mathrm{cyc}^{z}`$ | `Process_output_cyclic_delay` over $`\mathcal{R}`$ — whether a delayed port's transfer wraps from the end of its investment period (PyPSA's `cyclic_delay0`, `cyclic_delay1`, …). Where it does not, the energy still in transit at each period's first snapshots is lost. The flag is the same in every scenario, as the delay is |
| $`\mathrm{d}^{z}`$ | `Process_output_delay` over $`\mathcal{R}`$ — snapshots a port's transfer lags its process's internal power (PyPSA's `delay0`, `delay1`, … read long). In data prep you divide it by the `snapshot_weightings.generators` value and round it up. It is zero for a port that transfers at once. A port has the same delay in every scenario, as a link's port has |
| $`\overline{\mathrm{z}}`$ | `Process_p_max_pu` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — most internal power, per unit of nominal power |
| $`\underline{\mathrm{z}}`$ | `Process_p_min_pu` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — least internal power, per unit of nominal power: negative for a process that runs both ways |
| $`\mathrm{nonneg}^{z}`$ | `Process_p_min_pu_nonneg` over $`\mathcal{J}`$ — true where none of the process's own minimums-per-unit is negative. It is PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep |
| $`\mathrm{z}^{\mathrm{nom}}`$ | `Process_p_nom` over $`\mathcal{J} \times \Xi`$ — nominal internal power |
| $`\mathrm{ext}^{z}`$ | `Process_p_nom_extendable` over $`\mathcal{J}`$ — whether the nominal internal power is a decision |
| $`\overline{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_max` over $`\mathcal{J} \times \Xi`$ — most nominal power an extendable process may be built at |
| $`\underline{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_min` over $`\mathcal{J} \times \Xi`$ — least nominal power an extendable process may be built at |
| $`\mathrm{z}^{\mathrm{mod}}`$ | `Process_p_nom_mod` over $`\mathcal{J}`$, `absent` where the data has no row — the module size a build comes in whole numbers of. No value means the build is continuous |
| $`\mathrm{z}^{\mathrm{nom,set}}`$ | `Process_p_nom_set` over $`\mathcal{J}`$, `absent` where the data has no row — a given nominal power for an extendable process. One without a value has no row here |
| $`\mathrm{z}^{\mathrm{set}}`$ | `Process_p_set` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — a given internal power schedule. A process without one has no row here |
| $`\alpha`$ | `Process_rate` over $`\mathcal{R} \times \Xi \times \mathcal{T}`$ — the energy a port draws or delivers per unit of internal power (PyPSA's `rate0`, `rate1`, … read long). It is negative where the port withdraws and positive where it injects. A link is a process whose `bus0` rate is minus one and whose output rates are its efficiencies. The rate at the snapshot the transfer arrives applies, so a delayed port transfers at its arrival snapshot's rate (`constraints.py:1575`) |
| $`\mathrm{m}^{z}`$ | `Process_tech_capacity_weight` over $`\mathcal{G} \times \mathcal{J}`$, `absent` where the data has no row — one where the process is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z,\mathrm{com}}`$ | `Process_committed` over $`\mathcal{J} \times \mathcal{T}`$ — a committable process that is active in the snapshot's period: every unit-commitment row's set |

#### Variables

| Symbol | Meaning |
|---|---|
| $`N^{z}`$ | `Process_n_mod` over $`\mathcal{J}`$ — `Process-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`z`$ | `Process_p` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-p` — PyPSA's internal power `p`. A positive value drives every port at its own rate, withdrawing where the rate is negative and injecting where it is positive |
| $`Z`$ | `Process_p_nom_ext` over $`\mathcal{J}`$ — `Process-p_nom` — nominal internal power where it is a decision, for a process that is active. A fixed build is the parameter of the same PyPSA name |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Process\_additions}`$ | `Process_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Process\_capex}`$ | `Process_capex` (scalar) |
| $`\mathit{Process\_injection}`$ | `Process_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathrm{M}^{z}`$ | `Process_modules` over $`\mathcal{J} \times \Xi`$ — how many modules a committed process's status counts: the chosen number where the build is extendable and modular, and the modules installed otherwise (`constraints.py:656-661`) |
| $`\mathit{Process\_opex}`$ | `Process_opex` over $`\Xi`$ |
| $`\overrightarrow{z}`$ | `Process_output_arrival` over $`\mathcal{R} \times \Xi \times \mathcal{T}`$ — what a process transfers at a port at a snapshot. It is its internal power delayed by the port's `delay` within its investment period. It is multiplied by the port's rate at the snapshot the transfer arrives. Where the port is `cyclic_delay`, the delayed transfer wraps from the period's end. Where it is not, the energy still in transit at the period's first snapshots is lost. A port that does not delay (`delay` zero) transfers at once, cyclic or not |
| $`\widehat{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_committed` over $`\mathcal{J} \times \Xi`$ — the build a committed process's ramp rows are taken against: one module where the build is modular, since its status counts modules, and the given build otherwise (`constraints.py:1131-1134`) |
| $`\widetilde{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_effective` over $`\mathcal{J} \times \Xi`$ — the build a process's limits are taken against: the chosen one where it is extendable, the given one otherwise |
| $`\mathit{Process\_tech\_capacity\_expansion}`$ | `Process_tech_capacity_expansion` over $`\mathcal{G}`$ |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`t \ominus^{\mathrm{map}(t)} k`$ | `within=subject[map]` — $`t-k`$ inside the group of $`t`$ |

#### Conditions

**`Process_committed`**

```math
\mathrm{on}^{z,\mathrm{com}}_{j,t} \iff \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t} \qquad \forall\, j \in \mathcal{J},\ t \in \mathcal{T}
```

#### Variable domains

**`Process_n_mod`**

```math
N^{z}_{j} \ge 0, N^{z}_{j} \in \mathbb{Z} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \wedge \mathrm{act}^{z}_{j}
```

**`Process_p`**

```math
z_{j,\xi,t} \in \mathbb{R} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z}_{j,t}
```

**`Process_p_nom_ext`**

```math
Z_{j} \in \mathbb{R} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j}
```

#### Definitions

**`Process_additions`**

```math
\mathit{Process\_additions}_{i,y} = \sum_{j \in \mathcal{J} \,:\, \mathrm{carrier}(j) = i} Z_{j} \cdot \mathrm{new}^{z}_{y,j} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

**`Process_capex`**

```math
\mathit{Process\_capex} = \sum_{j \in \mathcal{J},\ \xi \in \Xi} \pi_{\xi} \cdot Z_{j} \cdot \mathrm{c}^{\mathrm{cap},z}_{j,\xi} \cdot \mathrm{W}^{z}_{j}
```

**`Process_injection`**

```math
\mathit{Process\_injection}_{n,\xi,t} = \sum_{r \in \mathcal{R} \,:\, \mathrm{bus}(r) = n} \overrightarrow{z}_{r,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_modules`**

```math
\mathrm{M}^{z}_{j,\xi} = \begin{cases} N^{z}_{j} & \text{if } \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \\ \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

**`Process_opex`**

```math
\mathit{Process\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} z_{j,\xi,t} \cdot \mathrm{c}^{z}_{j,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{period}(t)} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} z_{j,\xi,t} \cdot z_{j,\xi,t} \cdot \mathrm{c}^{z,(2)}_{j,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{period}(t)} \qquad \forall\, \xi \in \Xi
```

**`Process_output_arrival`**

```math
\overrightarrow{z}_{r,\xi,t} = \begin{cases} z_{\mathrm{process}(r),\xi,t \ominus^{\mathrm{period}(t)} \mathrm{d}^{z}} \cdot \alpha_{r,\xi,t} & \text{if } \mathrm{cyc}^{z}_{r} \\ z_{\mathrm{process}(r),\xi,t \boxminus_{0}^{\mathrm{period}(t)} \mathrm{d}^{z}} \cdot \alpha_{r,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, r \in \mathcal{R},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_p_nom_committed`**

```math
\widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} = \begin{cases} \mathrm{z}^{\mathrm{mod}}_{j} & \text{if } \mathrm{z}^{\mathrm{mod}}_{j} > 0 \\ \mathrm{z}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

**`Process_p_nom_effective`**

```math
\widetilde{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} = \begin{cases} Z_{j} & \text{if } \mathrm{ext}^{z}_{j} \\ \mathrm{z}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

**`Process_tech_capacity_expansion`**

```math
\mathit{Process\_tech\_capacity\_expansion}_{g} = \sum_{j \in \mathcal{J}} Z_{j} \cdot \mathrm{m}^{z}_{g,j} \qquad \forall\, g \in \mathcal{G}
```

#### Subject to

**`Process_e_sum_max`**

```math
\sum_{t \in \mathcal{T}} z_{j,\xi,t} \cdot \mathit{w}^{E}_{t} \le \overline{\mathrm{E}}^{z}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \overline{\mathrm{E}}^{z}_{j,\xi} \text{ is defined} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{z}_{j,t} \} \rvert > 0
```

**`Process_e_sum_min`**

```math
\sum_{t \in \mathcal{T}} z_{j,\xi,t} \cdot \mathit{w}^{E}_{t} \ge \underline{\mathrm{E}}^{z}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \underline{\mathrm{E}}^{z}_{j,\xi} \text{ is defined} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{z}_{j,t} \} \rvert > 0
```

**`Process_ext_p_lower`**

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_ext_p_nom_lower`**

```math
Z_{j} \ge \underline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j}
```

**`Process_ext_p_nom_upper`**

```math
Z_{j} \le \overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j} \wedge \overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \text{ is defined}
```

**`Process_ext_p_upper`**

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_fix_p_lower`**

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( 1 - \gamma^{z}_{j,\xi} \cdot \mu^{z}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_fix_p_upper`**

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( 1 - \gamma^{z}_{j,\xi} \cdot \mu^{z}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_p_nom_modularity`**

```math
Z_{j} = \mathrm{z}^{\mathrm{mod}}_{j} \cdot N^{z}_{j} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \wedge \mathrm{act}^{z}_{j}
```

**`Process_p_nom_set`**

```math
Z_{j} = \mathrm{z}^{\mathrm{nom,set}}_{j} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j} \wedge \mathrm{z}^{\mathrm{nom,set}}_{j} \text{ is defined}
```

**`Process_p_set`**

```math
z_{j,\xi,t} = \mathrm{z}^{\mathrm{set}}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{z}^{\mathrm{set}}_{j,\xi,t} \text{ is defined} \wedge \mathrm{on}^{z}_{j,t}
```

#### Assumptions

**`Process_marginal_cost_quadratic_without_risk_preference`**

```math
\mathrm{c}^{z,(2)}_{j,\xi,t} = 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \omega \text{ is defined}
```

**`Process_output_delay_under_uniform_weighting`**

```math
\mathrm{w}^{\mathrm{gen}}_{t} = \mathrm{w}^{\mathrm{gen}}_{t \ominus 1} \qquad \forall\, r \in \mathcal{R},\ t \in \mathcal{T} \,:\, \mathrm{d}^{z}_{r} > 0
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
