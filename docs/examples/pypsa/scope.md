<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA: scope and refusals

You can check here whether the file
[`examples/pypsa.yaml`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa.yaml)
states the model that your call of `n.optimize()` builds. Where PyPSA refuses
the data, [Refusals](#refusals) lists what the file states for each case.

The file states the spec of the model that a plain `n.optimize()` builds in
the power system modelling framework PyPSA. It also states two classes of
model beyond a plain `n.optimize()`. The two-stage stochastic class spans a
`scenario` dimension, and `n.set_scenarios(...)` switches it on (rung 14). The
multi-period investment class spans a `period` dimension, and the keyword
`multi_investment_periods` switches it on (rung 15).

The file grows one step of the PyPSA ladder
([a rung](../../reference/glossary.md#rung)) at a time, and each rung states
one `n.optimize()` keyword or feature in full. The
[rung tables](https://github.com/energy-models/mathspec/blob/main/examples/references/pypsa/README.md)
list the rows that PyPSA builds, with the status of each in the file. The rows
and the line numbers on this page are those of PyPSA `master` at commit
`72a12418`, under `pypsa/optimization/`.

The work that turns a PyPSA network into the data the file declares
([data prep](../../reference/glossary.md#data-preparation)) is outside the
file. [Data prep](#data-prep) lists the parameters whose values come from it.

Three rules apply throughout the file:

- Each bound is an explicit row, as PyPSA writes it, so its dual is the dual of
  a row.
- Each case of a PyPSA rule is a
  [`where:`](../../reference/language/absence.md#where) condition on a column
  of data.
- The names are those of PyPSA, spelled `Component_attribute`. The typesetter
  prints them in the usual symbols, from the symbol table
  `examples/symbols/pypsa.yaml`.

## Refusals

PyPSA raises on the data in the table below, warns on it, or handles it outside
its general rows. None of these refusals is a [limit](../../about/limits.md) of the
language. For eight rows of the table, the file states
[assumptions](../../reference/language/assumptions.md), which a tool runs when it
attaches the data.

| PyPSA raises                                                                       | on                                                                                                                                                                                                                                                                                     | here                                                                                                                                                                                                                                           |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ValueError`, `optimize.py:506-513`                                                | a nonzero `marginal_cost_quadratic` on any Generator, Link, Process, StorageUnit or Store under a risk preference, `omega = 0` included                                                                                                                                                | Where `CVaR_omega` has a row, the file states an assumption: `Generator_marginal_cost_quadratic_without_risk_preference`, and the `Link`, `Process`, `StorageUnit` and `Store` ones.                                                           |
| `ValueError`, `constraints.py:1953`                                                | fixed modular `p_nom` not a multiple of `p_nom_mod`                                                                                                                                                                                                                                    | The file states a fractional module cap.                                                                                                                                                                                                       |
| `ValueError`, `constraints.py:1605`                                                | load on a bus with nothing attached                                                                                                                                                                                                                                                    | The file states no row for the bus, so its load goes unserved.                                                                                                                                                                                 |
| `ValueError`, `optimize.py:472`                                                    | no component has a cost                                                                                                                                                                                                                                                                | The file states a feasibility problem.                                                                                                                                                                                                         |
| `NotImplementedError`, `global_constraints.py:473`, `:525`, `:679`, `:727`         | storage that keeps its level across periods in a `primary_energy` or `operational_limit` row, with period `years` `!= 1`                                                                                                                                                               | The file states an assumption: `StorageUnit_primary_energy_carried_over_has_unit_years`, `StorageUnit_operational_limit_carried_over_has_unit_years`, and the `Store` ones.                                                                    |
| `KeyError`, `global_constraints.py:490`, `:542`, `:696`, `:741` (PyPSA/PyPSA#2113) | a `primary_energy` or `operational_limit` row over storage that reopens per period, on a network with scenarios                                                                                                                                                                        | Where there is more than one scenario, the file states an assumption: `StorageUnit_primary_energy_per_period_without_scenarios`, `StorageUnit_operational_limit_per_period_without_scenarios`, and the `Store` ones.                           |
| `ValueError`, `global_constraints.py:380-385`, `:619-624`                          | a `primary_energy` or `operational_limit` row that specifies an `investment_period` without `multi_investment_periods`                                                                                                                                                                 | You compute `GlobalConstraint_counts_snapshot` in data prep.                                                                                                                                                                                   |
| `ValueError`, `constraints.py:2513`, `:2691`                                       | an extendable lossy branch with `s_nom_max = inf`, either mode                                                                                                                                                                                                                         | You compute `Line_loss_max` and `Transformer_loss_max` in data prep.                                                                                                                                                                           |
| `RuntimeError`, `constraints.py:2739`                                              | the secant loop passing `max_segments`                                                                                                                                                                                                                                                 | You compute the `segment` axis in data prep.                                                                                                                                                                                                   |
| `ValueError`, `abstract.py:634-643`                                                | an outage named in `branch_outages` that is active in no period of the run                                                                                                                                                                                                             | `Line_BODF` and `Transformer_BODF` have no value for the outage, so the file states no copy.                                                                                                                                                   |
| `ConsistencyError`, `consistency.py:1250`                                          | a bus port, `*_nom_set`, `delay`, `cyclic_delay`, `v_nom`, `x_pu_eff` or `r_pu_eff` that differs by scenario (`constants.py:26-58`)                                                                                                                                                    | The file states no such difference, because the ports, `Generator_p_nom_set` and the others, and `Link_output_delay` and the others span no `scenario`. `Line_cycle_weight`, `Line_BODF` and the `Transformer` ones span no `scenario` either. |
| `NotImplementedError`, `global_constraints.py:68-70`                               | a `tech_capacity_expansion_limit` row on a network with scenarios                                                                                                                                                                                                                      | Where there is more than one scenario, the file states an assumption: `GlobalConstraint_tech_capacity_expansion_limit_without_scenarios`. One scenario and none look alike in the file, and PyPSA refuses one scenario too.                    |
| `ConsistencyError`, `consistency.py:1531-1585`                                     | a maintainable component whose `maintenance_duration` or `maintenance_events` is not positive, whose events do not fit the weighted horizon, or that is extendable with `p_nom_max = inf`                                                                                              | The file states an assumption: `Generator_maintenance_events_positive`, `-duration_positive`, `-duration_fits_the_horizon`, `-events_fit_the_horizon`, `-build_cap_is_finite`, and the `Link` and `Process` ones.                              |
| `ValueError`, `piecewise.py:277-297`                                               | a piecewise `marginal_cost` curve on an extendable generator, or on one whose `p_nom` is zero, missing or infinite                                                                                                                                                                     | The file states an assumption: `Generator_marginal_cost_curve_on_a_fixed_build`.                                                                                                                                                               |
| `KeyError`, `constraints.py:1916`                                                  | a `*_nom_set` on a unit that is not extendable, or that has `active = False`                                                                                                                                                                                                           | The file states no row: `Generator-p_nom_set` and the others exist only where the build is extendable, and an inactive unit is fixed ([Data prep](#data-prep)).                                                                                |
| `KeyError`, `constraints.py:2943`                                                  | `e_sum_min` or `e_sum_max` on a Generator, Link, Process or Store with `active = False`                                                                                                                                                                                                | The file states the row with no variable: `Generator-e_sum_min` and its siblings are `0 >= e_sum_min`, which fails where the floor is positive.                                                                                                |
| `ValueError`, `constraints.py:1606-1611`                                           | a loaded bus where every unit and branch has retired in some snapshot                                                                                                                                                                                                                  | The file states the row with no variable: `Bus-nodal_balance` requires the load alone to be zero, and no solution meets it.                                                                                                                    |
| `ValueError`, `components/descriptors.py:141-144`                                  | a `transmission_volume_expansion_limit`, `transmission_expansion_cost_limit` or `tech_capacity_expansion_limit` row that specifies an `investment_period` outside `n.investment_periods`                                                                                               | You compute `Line_volume_weight`, `Line_expansion_cost_weight`, `Line_tech_capacity_weight` and the other components' ones in data prep.                                                                                                       |
| `ValueError`, `flow_based.py:109-114`                                              | a `flow_based` row whose sense is not `<=`                                                                                                                                                                                                                                             | The file states an assumption: `GlobalConstraint_flow_based_sense_is_le`.                                                                                                                                                                      |
| `ValueError`, `flow_based.py:71-93`, `:116-166`, `:196-200`                        | a flow-based domain where a line, transformer or link that is no corridor joins two zones, a zone has nothing attached, a `ptdf_<name>` names no bus or link, a corridor is inactive or touches no zone, a zone is in two domains, only some rows name a domain, or a row has no `ram` | You compute `GlobalConstraint_zonal_ptdf`, `GlobalConstraint_link_ptdf`, `Bus_flow_based_zone` and `Bus_flow_based_domain` in data prep.                                                                                                       |
| a warning, or `ConsistencyError` under `strict`, `consistency.py:235-287`          | a transformer with `phase_shift_min > phase_shift_max`, or a decided phase shift with an infinite bound                                                                                                                                                                                | The file states the rows as PyPSA builds them. In the first case the transformer keeps its fixed `phase_shift`, and in the second `Transformer-phase_shift` is unbounded on that side.                                                         |
| nothing, and PyPSA lags by elapsed time, `multiports.py:100-133`                   | a Link or Process port with `delay > 0` under a `generators` weighting that is not one value over the horizon                                                                                                                                                                          | The file states an assumption: `Link_output_delay_under_uniform_weighting`, and the `Process` one. The file states the delay as a shift by whole snapshots, the same number in every period (#299).                                            |
| nothing, and PyPSA takes `0 * inf` as `0`, `constraints.py:129-134`                | a fixed build of `inf` where its least or most per-unit output is zero                                                                                                                                                                                                                 | The file states no assumption. `Generator-fix-p-lower` and the other fixed bounds contain the product as written, so the row is `0 * inf`, which has no value.                                                                                 |

## Data prep

These parameters take their values from the PyPSA network, as PyPSA sets them
before it builds a row.

- Every parameter computed from `r`, `x` or `s_nom` takes the values after
  PyPSA applies the line and transformer types
  (`network/power_flow.py:448-571`). A line with a `type` has `r` and `x` from
  the type, its `length` and `num_parallel`. A transformer with a `type` also
  has `s_nom`, `phase_shift` and `tap_ratio` from it.
- The carrier of a Line, a Link or a Store with a blank `carrier` is the
  carrier of its bus. PyPSA (`network/power_flow.py:810-812`, `:861-867`) fills
  a Line's or a Link's from `bus0`, and a Store's from `bus`. Growth limits and
  global constraints use the filled carrier.
- `Line_cycle_weight` is `x_pu_eff` on an AC sub-network and `r_pu_eff` on a DC
  one (`networks.py:1434-1439`). PyPSA weighs each branch in
  `Kirchhoff-Voltage-Law` by the carrier of its
  sub-network.
- In a `tech_capacity_expansion_limit` row with a bus,
  `Line_tech_capacity_weight` and the other components' ones count a branch, a
  Link and a Process at its `bus0` (`global_constraints.py:95`). They count a
  one-port component at its `bus`.
- On a plain run, `period_weight_objective` and `period_weight_years` are one.
  PyPSA (`optimize.py:231-233`, `:293-297`) reads
  `investment_period_weightings` only under `multi_investment_periods`.
- `StorageUnit_primary_energy_weight` and `Store_primary_energy_weight` have a
  value only for storage that is not cyclic. PyPSA (`global_constraints.py:452`,
  `:506`) reads `cyclic_state_of_charge` and `e_cyclic` alone, so a unit that
  cycles per period with `cyclic_state_of_charge = False` still counts. An
  `operational_limit` row also skips storage with `active = False` (`:657`,
  `:708`).
- `Generator_p_nom_extendable` and the others are false for a unit with
  `active = False`. PyPSA (`variables.py:360-368`) builds `{c}-p_nom` only for
  extendable units that are active, so an inactive unit has no capacity
  variable in PyPSA or in the file.
- `Line_BODF` and `Transformer_BODF` are the outage factors of the
  sub-networks of each period's active branches (`abstract.py:652-664`,
  rung 68). As in PyPSA, a branch not active in a period has no value there.
- `Link_output_delay` and `Process_output_delay` are numbers of snapshots: the
  PyPSA `delay` divided by the one value of the `generators` weighting, rounded
  up. The PyPSA `delay` is elapsed time in that weighting, and PyPSA
  (`multiports.py:100-133`) rounds the source down to a snapshot start.
- `Store_max_hours` and `Store_cycles_max` have a value only where PyPSA's
  `max_hours` or `cycles_max` is finite. `Store_split_dispatch` is PyPSA's
  `split_dispatch()` (`stores.py:88-116`), true where an efficiency differs
  from one, `marginal_cost_dispatch` or `marginal_cost_store` is nonzero, or
  `cycles_max` is finite, in any snapshot.
- `GlobalConstraint_zonal_ptdf` and `GlobalConstraint_link_ptdf` are the
  `ptdf_<name>` columns of the `flow_based` rows, read long by bus or link.
  `Bus_flow_based_zone` is true for a bus that names a column.
  `flow_based_domain` has one label per `domain` the rows name, or one label
  where they name none, and `Bus_flow_based_domain` maps each zone to the
  domain whose rows name it (`flow_based.py:65-93`).
- `Generator_marginal_cost_curve_p` is a curve's `p_pu` times `p_nom`, and
  `Generator_marginal_cost_curve_cost` is zero at the first breakpoint and
  adds each segment's width times the `marginal_cost` at its upper end
  (`piecewise.py:298-305`). A generator with no curve has no rows. The
  `marginal_cost` at the first breakpoint prices nothing.
- `global_constraint` has no label for a global constraint with nothing to
  count. PyPSA (`global_constraints.py:100-101`, `:554-555`, `:753-754`,
  `:839-840`) skips a row whose set is empty. In the file, that row would be
  `0` against its constant, which fails where the constant is on the wrong
  side of zero.

!!! info "See also"

    - [PyPSA](index.md), for the fragments that the file splits into
    - [The relaxed commitment](../pypsa_linearized_uc.md), for the patch that
      relaxes the commitment rows
    - [Assumptions](../../reference/language/assumptions.md), for the checks a
      tool runs when it attaches data
