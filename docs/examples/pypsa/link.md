<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Links

This file states PyPSA's `Link`. It is one of the [24 fragments](index.md) that merge back into `examples/pypsa.yaml`. It adds a term to each of these sums: `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions` and `Bus_injection`. It reads `CVaR_omega`, `Link_committable`, `Link_maintenance`, `Link_maintenance_capacity`, `Link_maintenance_pu`, `period_weight_objective` and 2 more names that other fragments declare, and lists them under [`given`](../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    snapshot_weightings_objective: { dims: [snapshot] }
    Link_committable: { dims: [link], dtype: bool }
    Link_maintenance_pu: { dims: [scenario, link] }
    scenario_weight: { dims: [scenario] }
    CVaR_omega: { dims: [] }
    period_weight_objective: { dims: [period] }
    snapshot_weightings_generators: { dims: [snapshot] }
  variables:
    Link_maintenance: { dims: [scenario, snapshot, link] }
    Link_maintenance_capacity: { dims: [scenario, snapshot, link] }
  expressions:
    transmission_volume_expansion: { dims: [global_constraint, scenario] }
    transmission_expansion_cost: { dims: [global_constraint, scenario] }
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
  link:
    description: controllable connections, each from one bus to the buses it delivers to
  link_output:
    description: >-
      a link's output ports, one label per port a link declares — PyPSA's
      `bus1`, `bus2`, … columns read long, so a link of any number of output
      ports is one term in the balance, data prep
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
  Link_carrier:
    description: the carrier a link converts from
    key: link
    values: carrier
  Link_bus0:
    description: the bus a link leaves
    key: link
    values: bus
  Link_output_link:
    description: the link an output port belongs to
    key: link_output
    values: link
  Link_output_bus:
    description: >-
      the bus an output port delivers to — PyPSA's `bus1`, `bus2`, … columns.
      A link of three output ports is three labels here rather than a third
      relation, so the file states any number of them
    key: link_output
    values: bus

parameters:
  Link_p_nom:
    description: nominal power
    dims: [scenario, link]
  Link_p_nom_extendable:
    description: whether the nominal power is a decision
    dims: [link]
    dtype: bool
  Link_p_min_pu:
    description: least flow, per unit of nominal power — negative for a link that carries both ways
    dims: [scenario, snapshot, link]
  Link_p_max_pu:
    description: most flow, per unit of nominal power
    dims: [scenario, snapshot, link]
  Link_efficiency:
    description: >-
      share of the flow that arrives at an output port, PyPSA's `efficiency`,
      `efficiency2`, … read long — negative where that port consumes rather
      than delivers. Read at the snapshot the flow arrives, so a delayed port
      delivers at its arrival snapshot's efficiency (`constraints.py:1498`)
    dims: [scenario, snapshot, link_output]
  Link_output_delay:
    description: >-
      snapshots a port's delivery lags its link's flow — PyPSA's `delay`,
      `delay2`, … read long, divided by the `snapshot_weightings.generators`
      value and rounded up in data prep; zero for a port that delivers at once.
      A port has the same delay in every scenario, because PyPSA refuses
      a delay that differs by scenario (`constants.py:52`)
    dims: [link_output]
    dtype: int
  Link_output_cyclic_delay:
    description: >-
      whether a delayed port's flow wraps from the end of its investment
      period — PyPSA's `cyclic_delay`, `cyclic_delay2`, …; where it does not,
      the flow still in transit at each period's first snapshots is lost.
      The flag is the same in every scenario, as the delay is
    dims: [link_output]
    dtype: bool
  Link_marginal_cost:
    description: cost of one unit of flow
    dims: [scenario, snapshot, link]
  Link_marginal_cost_quadratic:
    description: cost of the square of one unit of flow
    dims: [scenario, snapshot, link]
  Link_p_nom_mod:
    description: the module size a build comes in whole numbers of; no value means the build is continuous
    dims: [link]
    missing: neutral
  Link_modules_installed:
    description: >-
      how many whole modules a committable build has in place: `Link_p_nom
      / Link_p_nom_mod` where a fixed build is modular, one where it is
      not, data prep. PyPSA refuses a fixed modular build whose nominal power
      is not a whole number of modules
    dims: [scenario, link]
  Link_p_min_pu_nonneg:
    description: >-
      true where none of the link's own minimums-per-unit is negative —
      PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep
    dims: [link]
    dtype: bool
  Link_active:
    description: whether a link stands in a snapshot's period — PyPSA's `active`, data prep
    dims: [snapshot, link]
    dtype: bool
  Link_active_asset:
    description: >-
      whether a link is one of PyPSA's `active_assets` — its `active` flag
      alone, without build year and lifetime, so a unit that stands in no
      snapshot of the horizon still counts. PyPSA refuses one that differs
      by scenario (`constants.py:51`)
    dims: [link]
    dtype: bool
  Link_capital_weight:
    description: the sum of period weights a link stands in — PyPSA's `active * period_weighting`, summed, data prep
    dims: [link]
  Link_first_active:
    description: >-
      one in the first period a link stands in, zero elsewhere, data prep.
      PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`)
    dims: [period, link]
  Link_p_set:
    description: a given flow schedule; a link without one has no row here
    dims: [scenario, snapshot, link]
    missing: neutral
  Link_p_nom_min:
    description: least nominal power an extendable link may be built at
    dims: [scenario, link]
  Link_p_nom_max:
    description: most nominal power an extendable link may be built at
    dims: [scenario, link]
  Link_capital_cost:
    description: >-
      cost of one unit of nominal power for the modelled horizon —
      PyPSA's `periodized_cost`: `overnight_cost` as an annuity over
      `lifetime` at `discount_rate`, times `nyears`, where it is given, and
      `capital_cost` where it is not, plus `fom_cost`
      (`components.py:1126-1147`, `costs.py:102-203`), data prep
    dims: [scenario, link]
  Link_p_nom_set:
    description: a given nominal power for an extendable link; one without a value has no row here
    dims: [link]
    missing: neutral
  Link_volume_weight:
    description: >-
      the link's length in each scenario where its carrier is in the row's
      set (`global_constraints.py:847-848`) — data prep; a
      link outside it, or one that does not stand in the row's
      `investment_period`, has no row
    dims: [scenario, global_constraint, link]
    missing: neutral
  Link_expansion_cost_weight:
    description: >-
      the link's capital cost where its carrier is in the row's set, times
      the objective weights of the periods it stands in where the row names
      no `investment_period` under `multi_investment_periods` — data prep; a
      link outside the set, or one that does not stand in the row's period,
      has no row. The capital cost is PyPSA's `capital_cost` property, which is
      `Link_capital_cost` without `fom_cost` (`components.py:1151-1169`,
      `global_constraints.py:870-879`)
    dims: [scenario, global_constraint, link]
    missing: neutral
  Link_tech_capacity_weight:
    description: >-
      one where the link is in the row's carrier-and-bus set — data prep; one
      outside it, or one that does not stand in the row's `investment_period`,
      has no row
    dims: [global_constraint, link]
    missing: neutral

variables:
  Link_p:
    description: >-
      `Link-p` — PyPSA's `p0`, the flow measured at the `Link_bus0` end: a
      positive value withdraws there and injects at every bus the link's
      output ports deliver to
    dims: [scenario, snapshot, link]
    where: Link_active
  Link_n_mod:
    description: "`Link-n_mod` — how many modules of an extendable modular build; none for a unit that is not active"
    dims: [link]
    where: Link_p_nom_extendable AND Link_p_nom_mod > 0 AND Link_active_asset
    domain: integer
    bounds:
      lower: 0
  Link_p_nom_ext:
    description: >-
      `Link-p_nom` — nominal power where it is a decision, for a link that is
      active; the parameter of the same PyPSA name carries the fixed regime
    dims: [link]
    where: Link_p_nom_extendable AND Link_active_asset

expressions:
  Link_p_nom_effective:
    description: the build a link's limits are taken against — the chosen one where it is extendable, the given one otherwise
    dims: [scenario, link]
    cases:
      extendable: { when: Link_p_nom_extendable, expression: Link_p_nom_ext }
    otherwise: Link_p_nom
  Link_p_nom_committed:
    description: >-
      the build a committed link's ramp rows are taken against — one module
      where the build is extendable and modular, the given build otherwise
    dims: [scenario, link]
    cases:
      modular_build: { when: Link_p_nom_extendable AND Link_p_nom_mod > 0, expression: Link_p_nom_mod }
    otherwise: Link_p_nom
  Link_output_arrival:
    description: >-
      what a link delivers to an output port at a snapshot — its flow delayed
      by the port's `delay` within its investment period, times the port's
      efficiency at the snapshot the flow arrives; where the port is
      `cyclic_delay` the delayed flow wraps from the period's end, and where it
      is not the flow still in transit at the period's first snapshots is
      lost. A port that does not delay (`delay`
      zero) delivers its flow unshifted, cyclic or not
    dims: [scenario, snapshot, link_output]
    cases:
      wrapping:
        when: Link_output_cyclic_delay
        expression: shift(at(Link_p, by=Link_output_link[link]), along=snapshot, offset=Link_output_delay, edge='wrap', within=snapshot_period[period]) * Link_efficiency
    otherwise: shift(at(Link_p, by=Link_output_link[link]), along=snapshot, offset=Link_output_delay, edge=0, within=snapshot_period[period]) * Link_efficiency
  Link_transmission_volume_expansion:
    expression: sum(Link_p_nom_ext * Link_volume_weight, over=link)
    adds_to: transmission_volume_expansion
  Link_transmission_expansion_cost:
    expression: sum(Link_p_nom_ext * Link_expansion_cost_weight, over=link)
    adds_to: transmission_expansion_cost
  Link_tech_capacity_expansion:
    expression: sum(Link_p_nom_ext * Link_tech_capacity_weight, over=link)
    adds_to: tech_capacity_expansion
  Link_opex:
    expression: >-
      sum(sum(((Link_p * Link_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
      + sum(sum((((Link_p * Link_p) * Link_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
    adds_to: scenario_opex
  Link_capex:
    expression: sum(scenario_weight * Link_p_nom_ext * Link_capital_cost * Link_capital_weight)
    adds_to: total_cost
  Link_additions:
    expression: >-
      sum(Link_p_nom_ext * Link_first_active, over=link, by=Link_carrier[carrier])
    adds_to: Carrier_additions
  Link_injection:
    expression: >-
      -sum(Link_p, over=link, by=Link_bus0[bus])
      + sum(Link_output_arrival, over=link_output, by=Link_output_bus[bus])
    adds_to: Bus_injection

conditions:
  Link_committed:
    description: >-
      a committable link that stands in the snapshot's period — every
      unit-commitment row's set
    condition: Link_committable AND Link_active

constraints:
  Link_fix_p_lower:
    description: "`Link-fix-p-lower` — a fixed link carries at least its minimum, negative for the other way"
    dims: [scenario, snapshot, link]
    where: not Link_p_nom_extendable AND not Link_committable AND Link_active
    expression: Link_p >= Link_p_min_pu * Link_p_nom * (1 - Link_maintenance_pu * Link_maintenance)
  Link_fix_p_upper:
    description: "`Link-fix-p-upper` — a fixed link carries at most its nominal power"
    dims: [scenario, snapshot, link]
    where: not Link_p_nom_extendable AND not Link_committable AND Link_active
    expression: Link_p <= Link_p_max_pu * Link_p_nom * (1 - Link_maintenance_pu * Link_maintenance)
  Link_ext_p_lower:
    description: "`Link-ext-p-lower` — an extendable link carries at least its minimum of the chosen build, negative for the other way"
    dims: [scenario, snapshot, link]
    where: Link_p_nom_extendable AND not Link_committable AND Link_active
    expression: Link_p >= Link_p_min_pu * (Link_p_nom_ext - Link_maintenance_pu * Link_maintenance_capacity)
  Link_ext_p_upper:
    description: "`Link-ext-p-upper` — an extendable link carries at most the chosen build"
    dims: [scenario, snapshot, link]
    where: Link_p_nom_extendable AND not Link_committable AND Link_active
    expression: Link_p <= Link_p_max_pu * (Link_p_nom_ext - Link_maintenance_pu * Link_maintenance_capacity)
  Link_ext_p_nom_lower:
    description: "`Link-ext-p_nom-lower` — the chosen build is at least its floor in every scenario"
    dims: [scenario, link]
    where: Link_p_nom_extendable AND Link_active_asset
    expression: Link_p_nom_ext >= Link_p_nom_min
  Link_ext_p_nom_upper:
    description: "`Link-ext-p_nom-upper` — the chosen build is at most its cap in every scenario; a cap of infinity is no row"
    dims: [scenario, link]
    where: Link_p_nom_extendable AND Link_active_asset AND Link_p_nom_max
    expression: Link_p_nom_ext <= Link_p_nom_max
  Link_p_nom_set:
    description: "`Link-p_nom_set` — the chosen build pinned, wherever a value is given"
    dims: [link]
    where: Link_p_nom_extendable AND Link_active_asset AND Link_p_nom_set
    expression: Link_p_nom_ext == Link_p_nom_set
  Link_p_nom_modularity:
    description: "`Link-p_nom_modularity` — the chosen build is a whole number of modules"
    dims: [link]
    where: Link_p_nom_extendable AND Link_p_nom_mod > 0 AND Link_active_asset
    expression: Link_p_nom_ext == Link_p_nom_mod * Link_n_mod
  Link_p_set:
    description: "`Link-p_set` — flow pinned to the given schedule, wherever one is given"
    dims: [scenario, snapshot, link]
    where: Link_p_set AND Link_active
    expression: Link_p == Link_p_set

assumptions:
  Link_output_delay_under_uniform_weighting:
    holds: "snapshot_weightings_generators == shift(snapshot_weightings_generators, along=snapshot, offset=1, edge='wrap')"
    where: "Link_output_delay > 0"
    description: >-
      a delayed port lags by the same whole number of snapshots in every
      period. PyPSA lags by elapsed time in `generators` weighting and
      rounds the source down to a snapshot start (`multiports.py:100-133`),
      so the two agree only where that weighting is one value over the
      horizon. PyPSA does not refuse an uneven weighting, so the file does
      (#299)
  Link_marginal_cost_quadratic_without_risk_preference:
    holds: "Link_marginal_cost_quadratic == 0"
    where: "CVaR_omega"
    description: >-
      a quadratic cost puts a square into every `CVaR-excess` row, and PyPSA
      refuses quadratic costs under any risk preference
      (`optimize.py:470-477`), `omega = 0` included. Data prep writes a
      `CVaR_omega` row only where a risk preference is set
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\omega`$ | `CVaR_omega` (scalar), data another file declares |
| $`\mathrm{com}^{f}`$ | `Link_committable` over $`\mathcal{L}`$, data another file declares |
| $`\gamma^{f}`$ | `Link_maintenance_pu` over $`\mathcal{L} \times \Xi`$, data another file declares |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$, data another file declares |
| $`\pi`$ | `scenario_weight` over $`\Xi`$, data another file declares |
| $`\mathrm{w}^{\mathrm{gen}}`$ | `snapshot_weightings_generators` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$, data another file declares |
| $`\mu^{f}`$ | `Link_maintenance` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`\mu^{f,\mathrm{nom}}`$ | `Link_maintenance_capacity` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, an expression this file adds `Link_injection` to |
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{I} \times \mathcal{Y}`$, an expression this file adds `Link_additions` to |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Link_opex` to |
| $`\mathit{tech\_capacity\_expansion}`$ | `tech_capacity_expansion` over $`\mathcal{G}`$, an expression this file adds `Link_tech_capacity_expansion` to |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `Link_capex` to |
| $`\mathit{transmission\_expansion\_cost}`$ | `transmission_expansion_cost` over $`\mathcal{G} \times \Xi`$, an expression this file adds `Link_transmission_expansion_cost` to |
| $`\mathit{transmission\_volume\_expansion}`$ | `transmission_volume_expansion` over $`\mathcal{G} \times \Xi`$, an expression this file adds `Link_transmission_volume_expansion` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Link\_bus0}: \mathcal{L} \to \mathcal{N},\ \mathrm{Link\_output\_bus}: \mathcal{O} \to \mathcal{N}`$ — network nodes |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` with $`\mathrm{Link\_carrier}: \mathcal{L} \to \mathcal{I}`$ — energy carriers, what a growth limit is set per |
| $`\mathcal{G}`$ | index $`g`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{L}`$ | index $`l`$ — `link` with $`\mathrm{Link\_bus0}: \mathcal{L} \to \mathcal{N},\ \mathrm{Link\_carrier}: \mathcal{L} \to \mathcal{I},\ \mathrm{Link\_output\_link}: \mathcal{O} \to \mathcal{L}`$ — controllable connections, each from one bus to the buses it delivers to |
| $`\mathcal{O}`$ | index $`o`$ — `link_output` with $`\mathrm{Link\_output\_bus}: \mathcal{O} \to \mathcal{N},\ \mathrm{Link\_output\_link}: \mathcal{O} \to \mathcal{L}`$ — a link's output ports, one label per port a link declares — PyPSA's `bus1`, `bus2`, … columns read long, so a link of any number of output ports is one term in the balance, data prep |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods — PyPSA's `investment_periods` |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f}`$ | `Link_active` over $`\mathcal{L} \times \mathcal{T}`$ — whether a link stands in a snapshot's period — PyPSA's `active`, data prep |
| $`\mathrm{act}^{f}`$ | `Link_active_asset` over $`\mathcal{L}`$ — whether a link is one of PyPSA's `active_assets` — its `active` flag alone, without build year and lifetime, so a unit that stands in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:51`) |
| $`\mathrm{c}^{\mathrm{cap},f}`$ | `Link_capital_cost` over $`\mathcal{L} \times \Xi`$ — cost of one unit of nominal power for the modelled horizon — PyPSA's `periodized_cost`: `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where it is given, and `capital_cost` where it is not, plus `fom_cost` (`components.py:1126-1147`, `costs.py:102-203`), data prep |
| $`\mathrm{W}^{f}`$ | `Link_capital_weight` over $`\mathcal{L}`$ — the sum of period weights a link stands in — PyPSA's `active * period_weighting`, summed, data prep |
| $`\eta`$ | `Link_efficiency` over $`\mathcal{O} \times \Xi \times \mathcal{T}`$ — share of the flow that arrives at an output port, PyPSA's `efficiency`, `efficiency2`, … read long — negative where that port consumes rather than delivers. Read at the snapshot the flow arrives, so a delayed port delivers at its arrival snapshot's efficiency (`constraints.py:1498`) |
| $`\mathrm{cc}^{f}`$ | `Link_expansion_cost_weight` over $`\mathcal{G} \times \mathcal{L} \times \Xi`$, `neutral` where the data has no row — the link's capital cost where its carrier is in the row's set, times the objective weights of the periods it stands in where the row names no `investment_period` under `multi_investment_periods` — data prep; a link outside the set, or one that does not stand in the row's period, has no row. The capital cost is PyPSA's `capital_cost` property, which is `Link_capital_cost` without `fom_cost` (`components.py:1151-1169`, `global_constraints.py:870-879`) |
| $`\mathrm{new}^{f}`$ | `Link_first_active` over $`\mathcal{L} \times \mathcal{Y}`$ — one in the first period a link stands in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:265`) |
| $`\mathrm{c}^{f}`$ | `Link_marginal_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one unit of flow |
| $`\mathrm{c}^{f,(2)}`$ | `Link_marginal_cost_quadratic` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of the square of one unit of flow |
| $`\mathrm{N}^{f,\mathrm{fix}}`$ | `Link_modules_installed` over $`\mathcal{L} \times \Xi`$ — how many whole modules a committable build has in place: `Link_p_nom / Link_p_nom_mod` where a fixed build is modular, one where it is not, data prep. PyPSA refuses a fixed modular build whose nominal power is not a whole number of modules |
| $`\mathrm{cyc}^{f}`$ | `Link_output_cyclic_delay` over $`\mathcal{O}`$ — whether a delayed port's flow wraps from the end of its investment period — PyPSA's `cyclic_delay`, `cyclic_delay2`, …; where it does not, the flow still in transit at each period's first snapshots is lost. The flag is the same in every scenario, as the delay is |
| $`\mathrm{d}^{f}`$ | `Link_output_delay` over $`\mathcal{O}`$ — snapshots a port's delivery lags its link's flow — PyPSA's `delay`, `delay2`, … read long, divided by the `snapshot_weightings.generators` value and rounded up in data prep; zero for a port that delivers at once. A port has the same delay in every scenario, because PyPSA refuses a delay that differs by scenario (`constants.py:52`) |
| $`\overline{\mathrm{f}}`$ | `Link_p_max_pu` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — most flow, per unit of nominal power |
| $`\underline{\mathrm{f}}`$ | `Link_p_min_pu` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — least flow, per unit of nominal power — negative for a link that carries both ways |
| $`\mathrm{nonneg}^{f}`$ | `Link_p_min_pu_nonneg` over $`\mathcal{L}`$ — true where none of the link's own minimums-per-unit is negative — PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep |
| $`\mathrm{f}^{\mathrm{nom}}`$ | `Link_p_nom` over $`\mathcal{L} \times \Xi`$ — nominal power |
| $`\mathrm{ext}^{f}`$ | `Link_p_nom_extendable` over $`\mathcal{L}`$ — whether the nominal power is a decision |
| $`\overline{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_max` over $`\mathcal{L} \times \Xi`$ — most nominal power an extendable link may be built at |
| $`\underline{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_min` over $`\mathcal{L} \times \Xi`$ — least nominal power an extendable link may be built at |
| $`\mathrm{f}^{\mathrm{mod}}`$ | `Link_p_nom_mod` over $`\mathcal{L}`$, `neutral` where the data has no row — the module size a build comes in whole numbers of; no value means the build is continuous |
| $`\mathrm{f}^{\mathrm{nom,set}}`$ | `Link_p_nom_set` over $`\mathcal{L}`$, `neutral` where the data has no row — a given nominal power for an extendable link; one without a value has no row here |
| $`\mathrm{f}^{\mathrm{set}}`$ | `Link_p_set` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, `neutral` where the data has no row — a given flow schedule; a link without one has no row here |
| $`\mathrm{m}^{f}`$ | `Link_tech_capacity_weight` over $`\mathcal{G} \times \mathcal{L}`$, `neutral` where the data has no row — one where the link is in the row's carrier-and-bus set — data prep; one outside it, or one that does not stand in the row's `investment_period`, has no row |
| $`\mathrm{len}^{f}`$ | `Link_volume_weight` over $`\mathcal{G} \times \mathcal{L} \times \Xi`$, `neutral` where the data has no row — the link's length in each scenario where its carrier is in the row's set (`global_constraints.py:847-848`) — data prep; a link outside it, or one that does not stand in the row's `investment_period`, has no row |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f,\mathrm{com}}`$ | `Link_committed` over $`\mathcal{L} \times \mathcal{T}`$ — a committable link that stands in the snapshot's period — every unit-commitment row's set |

#### Variables

| Symbol | Meaning |
|---|---|
| $`N^{f}`$ | `Link_n_mod` over $`\mathcal{L}`$ — `Link-n_mod` — how many modules of an extendable modular build; none for a unit that is not active |
| $`f`$ | `Link_p` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-p` — PyPSA's `p0`, the flow measured at the `Link_bus0` end: a positive value withdraws there and injects at every bus the link's output ports deliver to |
| $`F`$ | `Link_p_nom_ext` over $`\mathcal{L}`$ — `Link-p_nom` — nominal power where it is a decision, for a link that is active; the parameter of the same PyPSA name carries the fixed regime |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Link\_additions}`$ | `Link_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Link\_capex}`$ | `Link_capex` (scalar) |
| $`\mathit{Link\_injection}`$ | `Link_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{Link\_opex}`$ | `Link_opex` over $`\Xi`$ |
| $`\overrightarrow{f}`$ | `Link_output_arrival` over $`\mathcal{O} \times \Xi \times \mathcal{T}`$ — what a link delivers to an output port at a snapshot — its flow delayed by the port's `delay` within its investment period, times the port's efficiency at the snapshot the flow arrives; where the port is `cyclic_delay` the delayed flow wraps from the period's end, and where it is not the flow still in transit at the period's first snapshots is lost. A port that does not delay (`delay` zero) delivers its flow unshifted, cyclic or not |
| $`\widehat{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_committed` over $`\mathcal{L} \times \Xi`$ — the build a committed link's ramp rows are taken against — one module where the build is extendable and modular, the given build otherwise |
| $`\widetilde{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_effective` over $`\mathcal{L} \times \Xi`$ — the build a link's limits are taken against — the chosen one where it is extendable, the given one otherwise |
| $`\mathit{Link\_tech\_capacity\_expansion}`$ | `Link_tech_capacity_expansion` over $`\mathcal{G}`$ |
| $`\mathit{Link\_transmission\_expansion\_cost}`$ | `Link_transmission_expansion_cost` over $`\mathcal{G} \times \Xi`$ |
| $`\mathit{Link\_transmission\_volume\_expansion}`$ | `Link_transmission_volume_expansion` over $`\mathcal{G} \times \Xi`$ |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`t \ominus^{\mathrm{relation}(t)} k`$ | `within=relation[...]` — $`t-k`$ inside the group of $`t`$ |

#### Conditions

**`Link_committed`**

```math
\mathrm{on}^{f,\mathrm{com}}_{l,t} \iff \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t} \qquad \forall\, l \in \mathcal{L},\ t \in \mathcal{T}
```

#### Variable domains

**`Link_n_mod`**

```math
N^{f}_{l} \ge 0, N^{f}_{l} \in \mathbb{Z} \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \wedge \mathrm{act}^{f}_{l}
```

**`Link_p`**

```math
f_{l,\xi,t} \in \mathbb{R} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f}_{l,t}
```

**`Link_p_nom_ext`**

```math
F_{l} \in \mathbb{R} \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{act}^{f}_{l}
```

#### Definitions

**`Link_additions`**

```math
\mathit{Link\_additions}_{i,y} = \sum_{l \in \mathcal{L} \,:\, \mathrm{Link\_carrier}(l) = i} F_{l} \cdot \mathrm{new}^{f}_{l,y} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

**`Link_capex`**

```math
\mathit{Link\_capex} = \sum_{l \in \mathcal{L},\ \xi \in \Xi} \pi_{\xi} \cdot F_{l} \cdot \mathrm{c}^{\mathrm{cap},f}_{l,\xi} \cdot \mathrm{W}^{f}_{l}
```

**`Link_injection`**

```math
\mathit{Link\_injection}_{n,\xi,t} = -\left( \sum_{l \in \mathcal{L} \,:\, \mathrm{Link\_bus0}(l) = n} f_{l,\xi,t} \right) + \sum_{o \in \mathcal{O} \,:\, \mathrm{Link\_output\_bus}(o) = n} \overrightarrow{f}_{o,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_opex`**

```math
\mathit{Link\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} f_{l,\xi,t} \cdot \mathrm{c}^{f}_{l,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} f_{l,\xi,t} \cdot f_{l,\xi,t} \cdot \mathrm{c}^{f,(2)}_{l,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

**`Link_output_arrival`**

```math
\overrightarrow{f}_{o,\xi,t} = \begin{cases} f_{\mathrm{Link\_output\_link}(o),\xi,t \ominus^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{f}} \cdot \eta_{o,\xi,t} & \text{if } \mathrm{cyc}^{f}_{o} \\ f_{\mathrm{Link\_output\_link}(o),\xi,t \boxminus_{0}^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{f}} \cdot \eta_{o,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_p_nom_committed`**

```math
\widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} = \begin{cases} \mathrm{f}^{\mathrm{mod}}_{l} & \text{if } \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \\ \mathrm{f}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

**`Link_p_nom_effective`**

```math
\widetilde{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} = \begin{cases} F_{l} & \text{if } \mathrm{ext}^{f}_{l} \\ \mathrm{f}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

**`Link_tech_capacity_expansion`**

```math
\mathit{Link\_tech\_capacity\_expansion}_{g} = \sum_{l \in \mathcal{L}} F_{l} \cdot \mathrm{m}^{f}_{g,l} \qquad \forall\, g \in \mathcal{G}
```

**`Link_transmission_expansion_cost`**

```math
\mathit{Link\_transmission\_expansion\_cost}_{g,\xi} = \sum_{l \in \mathcal{L}} F_{l} \cdot \mathrm{cc}^{f}_{g,l,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

**`Link_transmission_volume_expansion`**

```math
\mathit{Link\_transmission\_volume\_expansion}_{g,\xi} = \sum_{l \in \mathcal{L}} F_{l} \cdot \mathrm{len}^{f}_{g,l,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

#### Subject to

**`Link_ext_p_lower`**

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_ext_p_nom_lower`**

```math
F_{l} \ge \underline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{act}^{f}_{l}
```

**`Link_ext_p_nom_upper`**

```math
F_{l} \le \overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{act}^{f}_{l} \wedge \overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \text{ is defined}
```

**`Link_ext_p_upper`**

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_fix_p_lower`**

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( 1 - \gamma^{f}_{l,\xi} \cdot \mu^{f}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_fix_p_upper`**

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( 1 - \gamma^{f}_{l,\xi} \cdot \mu^{f}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_p_nom_modularity`**

```math
F_{l} = \mathrm{f}^{\mathrm{mod}}_{l} \cdot N^{f}_{l} \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \wedge \mathrm{act}^{f}_{l}
```

**`Link_p_nom_set`**

```math
F_{l} = \mathrm{f}^{\mathrm{nom,set}}_{l} \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{act}^{f}_{l} \wedge \mathrm{f}^{\mathrm{nom,set}}_{l} \text{ is defined}
```

**`Link_p_set`**

```math
f_{l,\xi,t} = \mathrm{f}^{\mathrm{set}}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{f}^{\mathrm{set}}_{l,\xi,t} \text{ is defined} \wedge \mathrm{on}^{f}_{l,t}
```

#### Assumptions

**`Link_marginal_cost_quadratic_without_risk_preference`**

```math
\mathrm{c}^{f,(2)}_{l,\xi,t} = 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \omega \text{ is defined}
```

**`Link_output_delay_under_uniform_weighting`**

```math
\mathrm{w}^{\mathrm{gen}}_{t} = \mathrm{w}^{\mathrm{gen}}_{t \ominus 1} \qquad \forall\, o \in \mathcal{O},\ t \in \mathcal{T} \,:\, \mathrm{d}^{f}_{o} > 0
```
<!-- gallery:end -->
