<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA reference networks

The rung tables below list each row and column that PyPSA builds, with its
status in [`examples/pypsa.yaml`](../../pypsa.yaml). A rung is one step of the
PyPSA ladder, which is one `n.optimize()` keyword or feature stated in full.
Each rung has a script in this folder, `rung_*.py`, that builds its network
with the data inline. Most scripts start from the shared two-bus network in
[`spine.py`](spine.py) and add the rung's own `n.add` calls. The other scripts,
such as those over investment periods, build a network of their own. A keyword
that a script does not pass has PyPSA's default.

[`reference.py`](reference.py) solves each network with the PyPSA version that
it pins, and writes the rows, the columns and the objective to
[`references.json`](references.json). `tests/test_pypsa_references.py` compares
that record with the entries of the file, without an engine.

Each name in the PyPSA column of a table is a row or a column that PyPSA
builds. The entry of `examples/pypsa.yaml` that states it opens its description
with the same name. The rows and the line numbers are those of PyPSA `master`
at commit `72a12418`, under `pypsa/optimization/`.
[PyPSA: scope and refusals](../../../docs/examples/pypsa/scope.md) lists the
networks that PyPSA refuses and what you compute in data prep.

## Statuses

A row has one of four statuses:

- A row is **done** where the file states it as the one entry that PyPSA builds.
- A row is **split** where the file states the same feasible region and optimum
  in a different form, such as several `where:` entries.
- A row is **out** where the file leaves it out, because PyPSA builds it only
  under the keyword, scope or version in the note.
- A row is **refused** where PyPSA refuses the data, and
  [Refusals](../../../docs/examples/pypsa/scope.md#refusals) lists what the file states for it.

A rung with no table adds no row. A name with `{k}`, `{s}`, `{c}` or `{n}` is a
family of rows that PyPSA numbers per segment, scenario, outaged component or
sub-network.

## The rungs

### Rung 1 — transport

| PyPSA                        | status | note                                                                                                                                                                                                       |
| ---------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Generator-p`, `Link-p`      | done   |                                                                                                                                                                                                            |
| `Generator-fix-p-lower`      | done   |                                                                                                                                                                                                            |
| `Generator-fix-p-upper`      | done   |                                                                                                                                                                                                            |
| `Link-fix-p-lower`           | done   |                                                                                                                                                                                                            |
| `Link-fix-p-upper`           | done   |                                                                                                                                                                                                            |
| `Bus-nodal_balance`          | done   | a loaded bus with nothing attached in [Refusals](../../../docs/examples/pypsa/scope.md#refusals)                                                                                                           |
| `Bus-meshed-*-nodal_balance` | out    | the rows and duals of `Bus-nodal_balance`, split by component columns per bus into containers of the model-building library linopy, under the keyword `meshed_thresholds`, default `[30, 100, 400]` (#123) |
| `marginal_cost`              | done   |                                                                                                                                                                                                            |
| `objective_constant`         | split  | an objective shift, which a test compares net of `n._objective_constant`, nonzero in rungs 11 (`21915277.52`) and 13 (`160.0`)                                                                             |

Rungs 43, 50 and 60 extend the `Bus-nodal_balance` row.

The network: [`rung_01_transport.py`](rung_01_transport.py).

### Rung 2 — storage

| PyPSA                                                                          | status | note                                                                                                                                                                                   |
| ------------------------------------------------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `StorageUnit-p_dispatch`, `-p_store`, `-state_of_charge`, `Store-e`, `Store-p` | done   |                                                                                                                                                                                        |
| `StorageUnit-spill`                                                            | done   | `where: inflow > 0`, [`missing: 0`](../../../docs/reference/language/absence.md#missing), with bounds on the variable, as PyPSA's                                                      |
| `StorageUnit-fix-*`, `Store-fix-e-*`                                           | done   |                                                                                                                                                                                        |
| `StorageUnit-energy_balance`                                                   | done   | the charge carried into a snapshot as a quantity stated with [`cases:`](../../../docs/reference/language/named.md#cases) (cyclic, opening, carried), and `(1-loss)**eh` from data prep |
| `Store-energy_balance`                                                         | done   | as `StorageUnit-energy_balance`                                                                                                                                                        |
| `StorageUnit-p_set`, `{c}-{attr}_set`                                          | done   | `Generator-p_set`, `Link-p_set`, `StorageUnit-state_of_charge_set`, `Store-e_set` and `Line-s_set` here, and `Store-p_set`, `StorageUnit-p_dispatch_set` and `-p_store_set` in rung 37 |
| `marginal_cost_storage`, `spill_cost`                                          | done   |                                                                                                                                                                                        |

Rung 60 extends the `StorageUnit-energy_balance` row. Rung 76 extends the
`Store-energy_balance` row and adds the bounds of `Store-p` and `Store-p_store`.

The network: [`rung_02_storage.py`](rung_02_storage.py).

### Rung 3 — expansion

| PyPSA                           | status | note                                                                                                  |
| ------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `{c}-p_nom`, `-s_nom`, `-e_nom` | done   | `{c}_p_nom_ext` for an extendable build, the parameter for a fixed build                              |
| `{c}-ext-{attr}-lower/upper`    | done   |                                                                                                       |
| `{c}-ext-p_nom-lower/upper`     | done   |                                                                                                       |
| `{c}-p_nom_set`                 | done   |                                                                                                       |
| `Generator-e_sum_min/max`       | done   |                                                                                                       |
| capital cost                    | done   | `periodized_cost` from data prep: `capital_cost`, or the annuity of `overnight_cost`, plus `fom_cost` |

The network: [`rung_03_expansion.py`](rung_03_expansion.py).

### Rung 4 — ramps

The build, the allowance and the output carried into a snapshot are each a
quantity stated with `cases:`. A fixed, an extendable and a committed unit
therefore share one entry. A missing limit is the full build. Rung 8 adds the rows of an
extendable committed unit, which use a large constant bound (big-M).

| PyPSA                      | status | note                                         |
| -------------------------- | ------ | -------------------------------------------- |
| `{c}-p-ramp_limit_up/down` | done   | a lone start-up or shut-down ramp in rung 28 |

Rungs 45 and 46 extend these rows.

The network: [`rung_04_ramps.py`](rung_04_ramps.py).

### Rung 5 — global constraints

PyPSA names every global constraint row `GlobalConstraint-{name}`. The type and
the comparator are data. A sense from data is a
[limit](../../../docs/about/limits.md) of the language (#70). The file states each type as
three entries, one per sense.

| PyPSA type                            | status | note                                                                                                       |
| ------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------- |
| `primary_energy`                      | split  | an entry per sense, with carrier weights from data prep, one period in rung 35 and per scenario in rung 40 |
| `operational_limit`                   | split  | an entry per sense, one period in rung 35, per scenario in rung 40                                         |
| `transmission_volume_expansion_limit` | split  | an entry per sense, membership from PyPSA's carrier string in data prep, per scenario in rung 40           |
| `transmission_expansion_cost_limit`   | split  | an entry per sense, with the cost as the `capital_cost` property, without `fom_cost`                       |
| `tech_capacity_expansion_limit`       | split  | an entry per sense                                                                                         |
| `Bus-nom_min/max_{carrier}`           | out    | deprecated in PyPSA                                                                                        |

Rung 60 extends the `primary_energy` row. Rung 15 states the
`Carrier-growth_limit` row, and rung 21 extends it to every extendable
component.

The network: [`rung_05_global_constraints.py`](rung_05_global_constraints.py).

### Rung 6 — KVL

A line's flow obeys the Kirchhoff voltage law (KVL). Around every independent
cycle of the network, the flows times their series impedance sum to zero. The
set of independent cycles (the cycle basis) is data, which you compute in data
prep.

| PyPSA                    | status | note                                  |
| ------------------------ | ------ | ------------------------------------- |
| `Line-s`, `Line-fix-s-*` | done   | the ext and nominal rows as in rung 3 |
| `Kirchhoff-Voltage-Law`  | done   | the cycle basis from data prep        |

Rungs 60 and 66 extend the `Kirchhoff-Voltage-Law` row.

The network: [`rung_06_kvl.py`](rung_06_kvl.py).

### Rung 7 — commitment

| PyPSA                                                            | status | note                                                                                                                                                                                                                                                          |
| ---------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `{c}-status`, `-start_up`, `-shut_down`                          | done   | Generator, with Link in rung 25 and Process in rung 26                                                                                                                                                                                                        |
| `{c}-com-p-lower/upper`                                          | done   | not for a modular build, which takes `com-mod-p-*` (PyPSA/PyPSA#1901)                                                                                                                                                                                         |
| `{c}-*-p-fixed-upper`                                            | done   | status, start and stop each at most one, as explicit rows                                                                                                                                                                                                     |
| `{c}-com-transition-start-up/shut-down`                          | done   | the carried-in state stated with `cases:`, no entry for the first snapshot, and zero carried in for a unit built in a later period (rung 64)                                                                                                                  |
| `{c}-com-up-time`, `-down-time`                                  | done   | [`sum_back`](../../../docs/reference/language/operators.md#sum_back)`(window=min_up_time)` from the first snapshot. The up or down time brought in counts as a start or a stop before it, from data prep (rung 24). A modular unit's down time counts modules |
| `stand_by_cost`, `start_up_cost`, `shut_down_cost`               | done   | the period weight and no snapshot weight on a start or a stop (rung 48), and a cost that may change per snapshot (rung 62)                                                                                                                                    |
| [`{c}-com-p-before/-current/-partly-*`](#the-relaxed-commitment) | done   | under `linearized_unit_commitment`, in a file laid over this one ([a patch](../../../docs/reference/glossary.md#patch)): rungs 12, 44, 47 and 74 for Generator, rung 67 for Link and Process                                                                  |

The network: [`rung_07_commitment.py`](rung_07_commitment.py).

### Rung 8 — modular and big-M

| PyPSA                               | status | note                                                                                                                                                                                                       |
| ----------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `{c}-n_mod`, `{c}-p_nom_modularity` | done   | Generator, Link and Process, and none for a build that is active in no snapshot (rung 63)                                                                                                                  |
| `{c}-*-p_nom-variable-upper`        | done   | a modular unit is on only where a module is built                                                                                                                                                          |
| `{c}-*-p-fixed-upper`, modular      | done   | the cap as the whole count of modules, `p_nom / p_nom_mod` from data prep, also for a fixed build such as `array` (#123), a fractional count in [Refusals](../../../docs/examples/pypsa/scope.md#refusals) |
| `{c}-com-mod-p-lower/upper`         | done   | one module's share times the status, for a fixed build too, in place of the `com-p-*` rows (PyPSA/PyPSA#1901)                                                                                              |
| `{c}-com-ext-p-*` (big-M)           | done   | a cap row beside a big-M row, with `M` from data prep, PyPSA's rule for an infinite build cap included (rung 64)                                                                                           |
| `{c}-com-ext-p-lower-nonneg`        | done   | `(p_min_pu >= 0).all()` from data prep                                                                                                                                                                     |
| `{c}-p-ramp_limit_*-bigM`           | done   | run and start rows up, run and shut rows down, each over the carried-in output stated with `cases:`, and the ordinary rows for a modular build (rung 27)                                                   |

The network: [`rung_08_modular_big_m.py`](rung_08_modular_big_m.py).

### Rung 9 — multi-link

| PyPSA                     | status | note                                                                                               |
| ------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| nodal balance, ports 1..n | done   | one term over `link_output`, so a link of any number of output ports needs no further entry (#124) |

The network: [`rung_09_multilink.py`](rung_09_multilink.py).

### Rung 10 — quadratic costs

The PyPSA `marginal_cost_quadratic` is a marginal cost that is quadratic in
output. It adds one squared cost per component to the objective, and weights
each snapshot by the hours the snapshot weighs. Here a generator and a link
have it, and rung 36 puts it on a process, a storage unit and a store. On a
plain run, it is zero, so the squared cost is zero and the objective stays
linear.

| PyPSA                     | status | note                                             |
| ------------------------- | ------ | ------------------------------------------------ |
| `marginal_cost_quadratic` | done   | degree 2 in the objective, on Generator and Link |

The network: [`rung_10_quadratic_costs.py`](rung_10_quadratic_costs.py).

### Rung 11 — ac-dc-meshed

This rung is the whole `ac_dc_meshed` example of PyPSA. It has meshed
alternating-current (AC) and direct-current (DC) networks, extendable lines,
links and generators, carriers and a CO2 budget. It has the rows of rungs 1, 3,
5 and 6 together, and it is the first rung with an objective constant.

The network: [`rung_11_ac_dc_meshed.py`](rung_11_ac_dc_meshed.py).

### Rung 13 — transmission losses

This rung runs `n.optimize(transmission_losses=...)`, under which a line
dissipates a loss that its flow causes. The loss stays above a fan of cuts to
the quadratic loss curve `r_pu_eff * p**2`. Half of it is charged at either end
of the line.

PyPSA has two modes (`constraints.py:2722`). Both build the same rows
`loss + slope * flow >= offset` and `loss - slope * flow >= offset`, one pair
per cut:

- `{'mode': 'tangents', 'segments': K}` takes `K` tangents at `p_k = k / K` of
  the rating, with slope `2 r p_k`.
- `True`, or `{'mode': 'secants', 'atol': 1, 'rtol': 0.1, 'max_segments': 20}`,
  takes the secants between consecutive breakpoints `p_k, p_k+1`. Each has
  slope `r (p_k + p_k+1)` and offset `-r p_k p_k+1`. The breakpoints start at
  `p_0 = 0` and step by `max(k / (k - 1), 1 + 2 (rtol + sqrt(rtol + rtol**2)))`
  until they cover the rating.

The mode sets only the values of `Line_loss_slope` and `Line_loss_offset` over
the `segment` axis. You compute them, and the breakpoint loop, in data prep.
The loss variable, its cap and the cut rows exist only where
`transmission_losses` is on. On a plain run, the flag is off and the data has
no segments. The loss is then absent and zero in the balance, and the rows
collapse to the lossless ones.

| PyPSA                                                                                                            | status | note                                                                                                                 |
| ---------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| `Line-loss`, `Transformer-loss`                                                                                  | done   | absent, and zero in the balance, where lossless                                                                      |
| `Line-fix-s-*`, `Line-ext-s-*`, `Transformer-fix-s-*`, `Transformer-ext-s-*`                                     | done   | the loss counted against the rating                                                                                  |
| `Bus-nodal_balance`                                                                                              | done   | half of each incident line's and transformer's loss at either end                                                    |
| `Line-loss_upper`, `Transformer-loss_upper`                                                                      | done   | `loss_max` from data prep, and its refusals in [Refusals](../../../docs/examples/pypsa/scope.md#refusals)            |
| `Line-loss_tangents-{k}-1`, `Transformer-loss_tangents-{k}-1`                                                    | split  | a row per segment in PyPSA, one entry over `segment` in the file                                                     |
| `Line-loss_tangents-{k}--1`, `Transformer-loss_tangents-{k}--1`                                                  | split  |                                                                                                                      |
| `Line-loss_secants-pos`, `Line-loss_secants-neg`, `Transformer-loss_secants-pos`, `Transformer-loss_secants-neg` | done   | the same two entries in the secant mode, with slope, offset and the breakpoint loop from data prep (rungs 19 and 23) |

The network: [`rung_13_losses.py`](rung_13_losses.py).

### Rung 19 — transmission losses in secant form

Rung 19 is rung 13's network in the secant mode. It has the same loss rows, but
PyPSA's tolerance loop places the cuts, not one cut per segment.

The network: [`rung_19_losses_secants.py`](rung_19_losses_secants.py).

### Rung 14 — two-stage stochastic

This rung has two futures and a risk preference, set by `n.set_scenarios(...)`
and `n.set_risk_preference(alpha, omega)`. Everything over a snapshot spans a
scenario as well. Capacity does not, because it is chosen once before the
future is known. The operating cost is the expectation over the scenarios'
weights.

A risk preference adds the conditional value at risk (CVaR) rows: an excess per
scenario and the tail's average, blended into the objective at `omega`. PyPSA
(`optimize.py:497`) builds the CVaR columns and rows under any risk preference,
and none without one. The file states them only where `CVaR_omega` has a
value, and `CVaR_omega` has a value only under a risk preference. Rung 70 sets
`omega = 0`. On a plain run, there is no risk preference and no CVaR row.

A parameter spans `scenario` exactly when PyPSA reads it per scenario. PyPSA
reads component data through `c.da`, one value per scenario
(`components/array.py:347-406`), so almost every parameter spans one. This
rung's wind `p_max_pu` differs by scenario, and the file states it over
`scenario`.

Some parameters span no `scenario`. PyPSA (`constants.py:26-58`,
`consistency.py:1250`) refuses a difference by scenario in the attributes that
fix the network's shape, such as `bus`, `carrier`, `lifetime`, `active`,
`committable` or `p_nom_extendable`. It refuses one in `*_nom_set`, `delay` and
`cyclic_delay` too. These parameters, and the values you derive from them in
data prep, span no `scenario`. PyPSA (`components.py:1018-1021`,
`constraints.py:477-482`, `global_constraints.py:239-243`) also reduces three
quantities over the scenarios, so they span none:

- `maintainable`, to a union over the scenarios
- `(p_min_pu >= 0).all()`, over every scenario
- a carrier's growth limits, to their least value

PyPSA builds the cycle basis (`networks.py:1428-1435`) and the outage factors
(`abstract.py:652`) from the first scenario. It refuses a `v_nom`, `x_pu_eff`
or `r_pu_eff` that differs by scenario (`constants.py:33-35`,
PyPSA/PyPSA#2104), so the first scenario's impedances are those of every
scenario. The cycle weights and the branch outage distribution factors (BODF)
of a branch therefore span no `scenario`.

In the file, a transformer's phase shift spans no `scenario` (#783). PyPSA
(`variables.py:446-456`, `constraints.py:1744`) reads it per scenario.

| PyPSA                                                                | status | note                                                                                                                                        |
| -------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `Generator-p`, `Link-p`                                              | done   | over `scenario`, except `Generator-p_nom`, which is chosen once                                                                             |
| `Generator-fix-p-*`, `-ext-p-*`, `Link-fix-p-*`, `Bus-nodal_balance` | done   | rungs 1 and 3, over `scenario`                                                                                                              |
| `CVaR-a`, `CVaR-theta`, `CVaR`                                       | done   |                                                                                                                                             |
| `CVaR-excess-{s}`                                                    | split  | a row per scenario in PyPSA, one entry over `scenario` in the file, none without a risk preference                                          |
| `CVaR-def`                                                           | done   | `1 / (1 - alpha)` from data prep, none without a risk preference                                                                            |
| objective                                                            | done   | capacity once, at its capital cost in expectation over the scenarios, and operation at `(1 - omega)` in expectation and `omega` at the tail |
| `Generator-fix-p-*` and the other rows over component data           | done   | data per scenario, such as `p_max_pu`, with operating data in rung 41, first-stage bounds and capital cost in rung 42                       |

The network: [`rung_14_stochastic.py`](rung_14_stochastic.py).

### Rung 15 — investment periods

This rung runs `n.optimize(multi_investment_periods=True)`, where each snapshot
belongs to an investment period. An asset is active in the periods that its
build year and lifetime span. Its capacity is paid once per period that it is
active in. Each period has a weight, and a carrier may grow only so much per
period. The snapshots an asset is active in are the parameter `{c}_active`,
from data prep.

| PyPSA                                           | status | note                                                                                                                           |
| ----------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `Generator-p`                                   | done   | where the generator is active in the snapshot's period, by `active` from data prep                                             |
| `Generator-fix-p-*`, `-ext-p-*`, `-ext-p_nom-*` | done   | rungs 1 and 3, where `active` is true                                                                                          |
| `Carrier-growth_limit`                          | done   | every extendable component of the carrier, counted in the first period a build is active in, with `edge=0` at the first period |
| objective                                       | done   | period weight on operation, capacity once per period it is active in                                                           |

Rungs 29, 32, 35, 38, 39, 49 and 66 extend these rows.

The network: [`rung_15_multi_period.py`](rung_15_multi_period.py).

### Rung 16 — link delay

A source feeds two sinks over links whose energy arrives late. With the PyPSA
`delay`, a port delivers a number of snapshots late. `cyclic_delay` sets what
happens to flow still in transit at the end of the horizon: it wraps to the
start, or it is lost. The delay is a number per link and the wrap a kind per
link. The balance states them with `cases:` over a
[`shift`](../../../docs/reference/language/operators.md#shift) by
`offset=Link_output_delay`. One case wraps (`edge='wrap'`),
and the other vacates (`edge=0`).

This is the only rung with a uniform `generators` weighting, and PyPSA measures
`delay` in units of that weighting. With a uniform weighting, a delay of `n` is
a shift of exactly `n` snapshot positions, which a positional `shift` gives.
With a weighting that is not uniform, PyPSA resamples by elapsed time, not by
position. A `shift` that varies along the snapshot axis is a
[limit](../../../docs/about/limits.md) of the language (#299). The file states an
[assumption](../../../docs/reference/language/assumptions.md),
`Link_output_delay_under_uniform_weighting`,
and a tool refuses such a delay when data is attached.

| PyPSA                        | status | note                                                                                       |
| ---------------------------- | ------ | ------------------------------------------------------------------------------------------ |
| link `delay`, `cyclic_delay` | done   | a `cases:` on `cyclic_delay` over `shift(offset=delay)`, at uniform `generators` weighting |

The network: [`rung_16_link_delay.py`](rung_16_link_delay.py).

### Rung 17 — process

A process is a generalised converter that moves an internal power from `bus0`
to the buses it feeds. Each port draws or delivers at its own `rate`. A
non-extendable process has a fixed capacity, and an extendable one chooses its
capacity between `p_nom_min` and `p_nom_max`. A ramp limit caps the change in
internal power between snapshots. A `p_set` fixes an internal power schedule,
and a `p_nom_set` fixes the built capacity of an extendable process. The rows
are those of the generator and the link, applied to a converter.

| PyPSA                                         | status | note                                                             |
| --------------------------------------------- | ------ | ---------------------------------------------------------------- |
| `Process-p`, `Process-p_nom`                  | done   | internal power and capacity, as a link                           |
| `Process-fix-p-*`, `-ext-p-*`, `-ext-p_nom-*` | done   | rungs 1 and 3, over a converter                                  |
| `Process-p-ramp_limit_*`                      | done   | rung 4, on a non-committable converter, and committed in rung 26 |
| `Process-p_set`                               | done   | a fixed internal power schedule                                  |
| `Process-p_nom_set`                           | done   | a fixed built capacity                                           |
| `Bus-nodal_balance`                           | done   | each port enters at its `rate`                                   |
| objective                                     | done   | marginal cost on internal power, and capital cost on capacity    |

The network: [`rung_17_process.py`](rung_17_process.py).

### Rung 18 — transformer

A transformer is a passive branch between two buses, as a line is. Its flow
follows its effective series reactance and a phase shift, which is fixed or
optimised. It obeys KVL around every independent cycle, and a transformer in no
cycle has no KVL row. A non-extendable transformer has a fixed nominal apparent
power, and an extendable one chooses it between `s_nom_min` and `s_nom_max`. An
`s_set` fixes a flow schedule, and an `s_nom_set` fixes the built capacity of
an extendable transformer.

| PyPSA                                             | status | note                                      |
| ------------------------------------------------- | ------ | ----------------------------------------- |
| `Transformer-s`, `Transformer-s_nom`              | done   | flow and capacity, as a line              |
| `Transformer-fix-s-*`, `-ext-s-*`, `-ext-s_nom-*` | done   | rungs 1 and 3, over a transformer         |
| `Transformer-s_set`                               | done   | a fixed flow schedule                     |
| `Transformer-s_nom_set`                           | done   | a fixed built capacity                    |
| `Kirchhoff-Voltage-Law`                           | done   | rung 6, over `x_pu_eff` and a phase shift |
| `Transformer-phase_shift`                         | done   | rung 20, an optimised phase shift         |
| objective                                         | done   | capital on capacity                       |

The network: [`rung_18_transformer.py`](rung_18_transformer.py).

### Rung 20 — phase shifter

Where the `phase_shift_min` of a phase-shifting transformer is below its
`phase_shift_max`, its voltage angle shift is a decision per snapshot. The shift
lies between the two bounds, in degrees. It enters the same KVL cycle sum as a
fixed one, so it redistributes the flows around a cycle without moving active
power. In this rung, with the shift, the transformer runs at its rating while
the upstream unit serves the whole load as the load varies. The decided shift replaces
the fixed `phase_shift`.

The network: [`rung_20_phase_shifter.py`](rung_20_phase_shifter.py).

### Rung 21 — carrier growth

The `max_growth` of a carrier caps what the carrier adds in an investment
period. The cap covers every extendable component of that carrier, not only
the generators. Here a battery carrier caps a storage unit and a store built in
the first period, and the two builds fill the cap together. A store built in the
later period adds its allowance plus half of what the carrier added before.
PyPSA counts only the components that have a carrier attribute, and the file
states the same sum, so a transformer counts in no carrier.

The network: [`rung_21_carrier_growth.py`](rung_21_carrier_growth.py).

### Rung 22 — transformer losses

PyPSA applies the loss of rung 13 to every passive branch, so a transformer
dissipates a loss as a line does. A transformer has:

- its own loss variable
- the loss counted against its rating
- its cap and its fan of cuts
- half of the loss at either end in the balance

The loss curve is rung 13's. A transformer's `r_pu_eff`
(`power_flow.py:845`) is its resistance over its given `s_nom`, times its tap
ratio. The given `s_nom` sets it also for an extendable transformer, whose
build does not move the curve. Here the loss of the extendable transformer
counts against its rating, so its build exceeds the flow it carries.

The network: [`rung_22_transformer_losses.py`](rung_22_transformer_losses.py).

### Rung 23 — transformer losses in secant form

Rung 23 is rung 22's network in the secant mode. It has the same loss rows, but
PyPSA's tolerance loop places the cuts.

The network: [`rung_23_transformer_losses_secants.py`](rung_23_transformer_losses_secants.py).

### Rung 24 — must stay down

A committable unit that stopped `down_time_before` snapshots before the horizon
stays off until its `min_down_time` has passed. PyPSA counts that stop in the
down-time row of the first `min_down_time - down_time_before` snapshots, which
holds the status at zero there. Here the cheapest
unit in the network brought one snapshot of a three-snapshot down time into the
horizon. It stays off for two snapshots, and the dearer coal unit serves the
load.

The network: [`rung_24_must_stay_down.py`](rung_24_must_stay_down.py).

### Rung 25 — committable links

A committable link has the whole on-off scheduling of a generator (unit
commitment), over its flow.
PyPSA builds the same status, transition, up time, down time, big-M,
modular and ramp rows for a `Link` as for a `Generator`. It prices the
starts, stops and stand-by snapshots of a link the same way.

Here only committable links serve an east bus. `hvdc` brought one snapshot of a
three-snapshot up time into the horizon. It stays on for two snapshots,
although a cheaper link could carry the load. `cold_tie` brought one snapshot
of a three-snapshot down time, so it stays off for two snapshots. Started then,
it would have to stay on into the last snapshot, for its two-snapshot up time.
The load there is below its minimum, so it does not start at all.

The other links are committable builds that are extendable, modular, or both.

| PyPSA                                                     | status | note                                                                                |
| --------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------- |
| `Link-status`, `-start_up`, `-shut_down`, `-n_mod`        | done   | as the generator's, rungs 7 and 8                                                   |
| `Link-com-p-*`, `-com-mod-p-*`, `-com-ext-p-*`            | done   | no `Link-fix-p-*` or `Link-ext-p-*` rows for a committable link, as for a generator |
| `Link-*-p-fixed-upper`, `-*-p_nom-variable-upper`         | done   |                                                                                     |
| `Link-com-transition-*`, `-com-up-time`, `-com-down-time` | done   |                                                                                     |
| `Link-p-ramp_limit_*`, `-*-bigM`                          | done   | the generator's allowance stated with `cases:`, and its big-M rows, over flow       |
| `Link-p_nom_modularity`                                   | done   |                                                                                     |
| `stand_by_cost`, `start_up_cost`, `shut_down_cost`        | done   |                                                                                     |

The network: [`rung_25_committable_link.py`](rung_25_committable_link.py).

### Rung 26 — committable processes

A committable process has the same unit commitment over its internal power
`p`. The status gates `p`, not a port, so every port follows the status at its
own `rate`. This rung states the links of rung 25 again as processes. Each
draws a quarter more from the north than it delivers to the east. The same
up and down time rules hold.

| PyPSA                                                        | status | note                                                                                    |
| ------------------------------------------------------------ | ------ | --------------------------------------------------------------------------------------- |
| `Process-status`, `-start_up`, `-shut_down`, `-n_mod`        | done   | as the link's, rung 25                                                                  |
| `Process-com-p-*`, `-com-mod-p-*`, `-com-ext-p-*`            | done   | no `Process-fix-p-*` or `Process-ext-p-*` rows for a committable process                |
| `Process-*-p-fixed-upper`, `-*-p_nom-variable-upper`         | done   |                                                                                         |
| `Process-com-transition-*`, `-com-up-time`, `-com-down-time` | done   |                                                                                         |
| `Process-p-ramp_limit_*`, `-*-bigM`                          | done   | the generator's allowance stated with `cases:`, and its big-M rows, over internal power |
| `Process-p_nom_modularity`                                   | done   |                                                                                         |
| `stand_by_cost`, `start_up_cost`, `shut_down_cost`           | done   |                                                                                         |

The network: [`rung_26_committable_process.py`](rung_26_committable_process.py).

### Rung 27 — modular ramps

A committable, extendable and modular unit gets no big-M ramp rows. PyPSA gives
it the ordinary `{c}-p-ramp_limit_*` rows of a committed unit, with one module
`p_nom_mod` in place of `p_nom`. The status counts the modules that are on, so
the allowance grows with each module. This rung has one such generator, link
and process on a peak bus. Each has a start-up and shut-down ramp of 0.6 and a
ramp limit of one half. The ramp rows are tight at the optimum at the rise and
at the fall of the load.

| PyPSA                               | status | note                                                                                                                             |
| ----------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------- |
| `{c}-p-ramp_limit_up/down`, modular | done   | the committed allowance over `p_nom_committed`, which is one module where the build is extendable and modular, `p_nom` otherwise |
| `{c}-p-ramp_limit_*-bigM`, modular  | done   | none for a modular build                                                                                                         |

The network: [`rung_27_modular_ramp.py`](rung_27_modular_ramp.py).

### Rung 28 — a start-up ramp alone

PyPSA builds a ramp row where either the ramp limit or the start-up ramp is
given. It takes the missing one as `1.0`, the full build. The down row is the
same with the shut-down ramp. This rung has a committable generator, link and
process with only two ramps, for start-up (0.4) and for shut-down (0.5). The
start-up ramp caps the snapshot each unit turns on, and the shut-down ramp caps
the snapshot before it turns off. PyPSA (`constraints.py:1116-1117`) also
builds the row at the first snapshot for either ramp alone.

A unit that is not committable starts the horizon on, whatever its
`up_time_before` (`constraints.py:323`). Data prep writes `{c}_status_initial`
as one for it (PyPSA/PyPSA#1943).

| PyPSA                                                        | status | note                                                                                           |
| ------------------------------------------------------------ | ------ | ---------------------------------------------------------------------------------------------- |
| `{c}-p-ramp_limit_up/down`, start-up or shut-down ramp alone | done   | a `where:` on either limit, with a missing one as `1` in `ramp_up_rate` and its three siblings |

The network: [`rung_28_start_up_ramp.py`](rung_28_start_up_ramp.py).

### Rung 29 — storage per investment period

This rung runs `n.optimize(multi_investment_periods=True)` with storage that
treats each investment period as a horizon of its own. A storage unit with
`cyclic_state_of_charge_per_period` and a store with `e_cyclic_per_period` close
each period on itself. The first snapshot of a period then takes the level of
the last snapshot of that period. A storage unit with
`state_of_charge_initial_per_period` and a store with `e_initial_per_period`
open each period on their initial level. The per-period cyclic flag overrides
the global one and the per-period initial flag. PyPSA reads the four flags only
under `multi_investment_periods`, so on a plain run they are false.

PyPSA also builds no ramp row at the first snapshot of a later period, with or
without these flags. The ramp-limited coal unit in this rung raises its output
from 59.2 to 90 across the period boundary, above its limit of 10 per snapshot.
Inside each period, its ramp rows are tight at the optimum.

| PyPSA                                                            | status | note                                                                                                                                                                                                                                            |
| ---------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `StorageUnit-energy_balance`, `Store-energy_balance`, per period | done   | two more cases in the charge carried in: a `shift(…, edge='wrap', within=snapshot_period[period])` and the initial level where [`position()`](../../../docs/reference/language/expressions.md#position) within `snapshot_period[period]` is `0` |
| `{c}-p-ramp_limit_*`, `-bigM`, at a period start                 | done   | a `where:` that is false at every period start but the horizon's first                                                                                                                                                                          |

The network: [`rung_29_storage_per_period.py`](rung_29_storage_per_period.py).

### Rung 30 — security-constrained

This rung runs `n.optimize.optimize_security_constrained(branch_outages=...)`.
After any one outage of a listed passive branch, every branch of the same
sub-network stays within its rating. PyPSA (`abstract.py:130-198`,
`:544-556`) computes the sub-network's BODF and copies each flow limit row.
Each copy adds the outaged branch's flow, times its factor, to the left-hand
side. The copy has the same sense, right-hand side and extendable rating as
the row.
The outaged branch is monitored too, at the factor `-1`.

A copy has no loss. PyPSA (`abstract.py:645-650`) builds the model without
`transmission_losses` and `linearized_unit_commitment`, and hands any other
keyword to the solver (`abstract.py:666`). A security run is therefore lossless
and integer, and `transmission_losses` is false there. A network with no
passive branch is the exception. There PyPSA (`abstract.py:625-632`) runs a
plain `n.optimize()` with every keyword, and no outage exists.

An outage is a line or a transformer. A `branch_outages` of bare names lists
only lines. The file states the copies over an `outage` axis, with the factors `Line_BODF` and
`Transformer_BODF` from data prep. You compute the factors from the branches
active in each period, so they span `period`. A branch not active in a period
has no factor there, so it has no copy there. On a plain run, the data has no
outage, so no copy exists and the rows collapse to the standard ones.

In this rung, PyPSA outages two lines and a transformer of a meshed triangle,
and monitors the third line only. PyPSA solves the same network at
objective `17380.0` with a plain `n.optimize()`, and the outages raise it to
`22113.33` (#620). The cheap unit at `a` falls to 32 in every snapshot. The
unit at `b` covers the rest. The build of the extendable line `ca` is 20.7
instead of 2 in the plain run. Six of the 120 copied rows are tight at the optimum:
`Transformer-fix-s-lower` against a line outage, and `Line-ext-s-lower` against
a transformer outage.

| PyPSA                                                                                | status | note                                                                                                                           |
| ------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `Line-fix-s-*-security-for-{c}-outage-in-sub-network-{n}`, `Line-ext-s-*-security-…` | split  | a row per outaged component and sub-network in PyPSA, one entry over the `outage` axis in the file                             |
| `Transformer-fix-s-*-security-…`, `Transformer-ext-s-*-security-…`                   | split  | the same for a transformer                                                                                                     |
| `Line-fix-s-*-security-…`, `Transformer-fix-s-*-security-…`                          | done   | none for a branch not active in a period, which has no factor there (rung 66)                                                  |
| `Line-fix-s-*-security-…`, `Transformer-fix-s-*-security-…`                          | done   | in each period, the factors of that period's own active branches (rung 68)                                                     |
| `Line-fix-s-*-security-…`, `Transformer-fix-s-*-security-…`                          | done   | over scenarios, the first scenario's factors, so `Line_BODF` spans no `scenario` (rung 56)                                     |
| `…-period-{p}` copies                                                                | split  | under `multi_investment_periods`, one entry over `snapshot`, each snapshot in one period                                       |
| `Line-loss`, `Transformer-loss` and the relaxed commitment rows                      | done   | none in a security-constrained run, which has no `transmission_losses` or `linearized_unit_commitment`, and no rung of its own |

The network: [`rung_30_security_constrained.py`](rung_30_security_constrained.py).

### Rung 32 — storage active in one period only

This rung runs `n.optimize(multi_investment_periods=True)` with storage that is
not per period and is not active in every period. PyPSA
(`constraints.py:2181-2183`, `2251-2254`) opens such a storage at the first
snapshot it is active in. A storage that is not cyclic opens on its initial
level. A cyclic one opens on the level of the last snapshot it is active in.
PyPSA reads the previous level through a forward fill over the snapshots the
storage is not active in.

A build year and a lifetime make those snapshots one stretch at each end of the
horizon. The file states the same rows with two parameters from data prep.
`{c}_opens_late` is the opening snapshot past the horizon's first.
`{c}_inactive_snapshots` is the number of snapshots the storage is not active
in, and a cyclic storage reaches back that many snapshots further. On a plain
run, the two are false and zero, so the rows collapse to the standard ones.

Three assumptions per class state the stretch and the opening snapshot:
`StorageUnit_stands_in_one_run`,
`-opens_late_only_where_it_opens`
and `-opens_late_where_it_opens` for
the storage unit. No assumption ties `{c}_inactive_snapshots` to the count of
inactive snapshots. A [`count`](../../../docs/reference/language/expressions.md#count)
compared against a parameter is a
[limit](../../../docs/about/limits.md#meaning-that-needs-data-or-code) of the language.

This rung's network has a cyclic store that retires after the 2020 period. A
cyclic storage unit and a store with an initial level of 5 open in the 2030
period. Without the opening rows, the level before 2030 would be absent, and
each storage would open on any level it chose. With them, the objective rises
to `7230.49`.

| PyPSA                                                                                              | status | note                                                                                                                                                                                  |
| -------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `StorageUnit-energy_balance`, `Store-energy_balance`, at the first snapshot a storage is active in | done   | the `cyclic` and `opening` cases true at `position(snapshot) == 0` or at `{c}_opens_late`, the cyclic one shifting one snapshot and then `{c}_inactive_snapshots` more, `edge='wrap'` |

The network: [`rung_32_storage_later_period.py`](rung_32_storage_later_period.py).

### Rung 33 — maintenance

A `Generator`, `Link` or `Process` with `maintainable=True` is taken off for
`maintenance_events` events (default 1) within the horizon. Each event
(`constraints.py:826-859`) covers the snapshot it starts in and the snapshots
after it, until their `generators` weightings reach `maintenance_duration`
hours. While in maintenance, the component (`constraints.py:150-160`, `236-249`)
loses the share `maintenance_pu` (default 1) of its build from both of its
bounds. The status `maintenance` (`variables.py:207-264`) is continuous in
[0, 1], and the binary starts make it 0 or 1.

An extendable build multiplies a variable by a variable. PyPSA
(`constraints.py:869-908`) writes that product as `maintenance_capacity`, and
bounds it with four linear rows on a product (McCormick rows). The rows are
against `p_nom_min` and `p_nom_max`, so PyPSA refuses an extendable
maintainable build with an infinite `p_nom_max`.

The window of an event depends on the weightings, so its width varies along
`snapshot`. `sum_back` takes a width that does not vary along the dimension it
sums, so the file states the windows as data. A table that pairs labels
([a relation](../../../docs/reference/language/relations.md)), `*_maintenance_cover`,
pairs each start with the snapshots it covers. The condition
`*_maintenance_start_blocked` marks a start whose window runs past the
horizon's end, or into a snapshot the component is not active in. You
compute both in data prep from `maintenance_duration`, the weightings and
`active`, and with them each row is the one PyPSA builds.

Across investment periods, an event may cross a period boundary, and the count
is over the whole horizon, as in PyPSA. Over scenarios, every maintenance
variable is second stage, with one schedule per scenario.

Here every maintainable component is new, and a peaker at 60 covers the east
bus. With the same network and no `maintainable`, PyPSA solves to
`5388.833333333333`.

| PyPSA                                                                                                     | status | note                                                |
| --------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------- |
| `Generator-maintenance`, `-maintenance_start`, `-maintenance_capacity`, and the `Link` and `Process` ones | done   | zero where the component is not maintainable        |
| `Generator-maint-event-count`, `-maint-window`, `-maint-start-horizon`, and the `Link` and `Process` ones | done   | the window and the blocked starts from data prep    |
| `Generator-maintcap_*`, and the `Link` and `Process` ones                                                 | done   | `-maintcap_lower_nommin` only where `p_nom_min > 0` |
| `Generator-fix-p-*`, `-ext-p-*`, and the `Link` and `Process` ones, in maintenance                        | done   | the bound less `maintenance_pu` of the build        |

The network: [`rung_33_maintenance.py`](rung_33_maintenance.py).

### Rung 34 — maintenance of committable units

A committable build scales its bounds by the status, so maintenance takes its
share off the status. PyPSA (`variables.py:307-344`, `constraints.py:507-540`)
writes the product of the status and `maintenance` as `maintenance_status`,
with three McCormick rows. A unit in maintenance can then also be off. A
modular committable build (`constraints.py:583-621`) uses the same product,
bounded by its module count in maintenance, `Generator_maintenance_modules`:
`p_nom_max / p_nom_mod` for an extendable build and `p_nom / p_nom_mod` for a
fixed one (rung 80). An extendable committable
build that is not modular (`constraints.py:440-450`) uses
`maintenance_capacity` in its big-M rows instead.

`-com-ext-p-upper-bigM` does not change. Ramps, the up and down times and the
storage rows do not contain maintenance. With the same network and no
`maintainable`, PyPSA solves to `5370.0`.

| PyPSA                                                                                                                              | status | note                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `Generator-maintenance_status`, and the `Link` and `Process` ones                                                                  | done   |                                                                                                                              |
| `Generator-maint-status-*`, `-maint-modstatus-*`, and the `Link` and `Process` ones                                                | done   | `maint-status` for a fixed build that is not modular, `maint-modstatus` for a modular build, fixed or not (PyPSA/PyPSA#1901) |
| `Generator-com-p-*`, `-com-mod-p-*`, `-com-ext-p-lower`, `-com-ext-p-upper-cap`, and the `Link` and `Process` ones, in maintenance | done   |                                                                                                                              |

The network: [`rung_34_committable_maintenance.py`](rung_34_committable_maintenance.py).

### Rung 35 — a global constraint for one investment period

This rung runs `n.optimize(multi_investment_periods=True)` with
`primary_energy` and `operational_limit` rows that name an `investment_period`.
PyPSA (`global_constraints.py:378-390`, `597-609`) sums such a row over the
snapshots of that period only, and over the whole horizon where the row specifies
none. Each snapshot (`:333`, `:636`) counts with its generator weighting times the
`years` weighting of its period. Storage closes in such a row as
follows:

- A storage unit or store that reopens per period closes at the last snapshot
  of each counted period, weighted by that period's years (`:488-491`,
  `:694-697`).
- One that keeps its level across periods closes once, at the last counted
  snapshot that it is active in (`:474-477`, `:680-683`, rung 69).

The file states the counted snapshots as `GlobalConstraint_counts_snapshot`,
from data prep, and the years as `period_weight_years`. On a plain run, the
counted snapshots are all true and the years are one, so the rows collapse to
the standard ones.

This rung's network caps CO2 in 2030 alone and again over the horizon. It
limits a hydro carrier with a per-period storage unit and store in the 2020
period. The two periods weigh 5 and 10 years. With the same network and no
`investment_period`, PyPSA solves to `10675.0`.

| PyPSA                                                            | status  | note                                                                                                                                                                                                                         |
| ---------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `primary_energy`, `operational_limit` over one investment period | done    | `GlobalConstraint_energy_weight`, zero outside the counted snapshots, with the years weighing each snapshot                                                                                                                  |
| `primary_energy`, `operational_limit` over one investment period | done    | the closing level of storage as `StorageUnit_closing_weight` and `Store_closing_weight`, at each counted period's last snapshot where the storage reopens per period, at the last counted snapshot it is active in otherwise |
| `primary_energy`                                                 | refused | over storage that reopens per period, on a network with scenarios, in [Refusals](../../../docs/examples/pypsa/scope.md#refusals)                                                                                             |

The network: [`rung_35_period_global_constraints.py`](rung_35_period_global_constraints.py).

### Rung 36 — quadratic costs on a process and on storage

PyPSA (`variables.csv:22`, `:30`, `:33`) declares `marginal_cost_quadratic` on
three other components, and this rung puts it on all three. A process pays on
its internal power `p`, and a storage unit on `p_dispatch` only. A store pays on
its net `p`, so charging costs as much as delivering. Each quadratic cost
(`optimize.py:349-366`) is the square times `marginal_cost_quadratic`, weighted
as the linear cost is. On a plain run, `marginal_cost_quadratic` is zero, so
the quadratic costs are zero.

The cost of this rung's storage unit changes per snapshot. With the same network
and no quadratic cost, PyPSA solves to `17641.666666666668`.

| PyPSA                                                       | status  | note                                                                                   |
| ----------------------------------------------------------- | ------- | -------------------------------------------------------------------------------------- |
| `marginal_cost_quadratic` on Process, StorageUnit and Store | done    | degree 2 in the objective, with no charge on `p_store`                                 |
| `marginal_cost_quadratic`                                   | refused | under a risk preference, in [Refusals](../../../docs/examples/pypsa/scope.md#refusals) |

The network: [`rung_36_quadratic_storage_process.py`](rung_36_quadratic_storage_process.py).

### Rung 37 — storage dispatch pinned to a schedule

PyPSA pins a store's power delivered to `p_set`. It pins a storage unit's
dispatch to `p_dispatch_set` and its charging to `p_store_set`, each on its
own. PyPSA builds a row only where a value is given and the storage is active.
On a plain run, the data has no value, so PyPSA builds no row.

The rung pins a store to deliver 10 in the first snapshot and to take 5 in the
last. It pins the dispatch of a storage unit in the first snapshot, and its
charging in the second. With the same network and no pins, PyPSA solves to
`5811.111111111111`.

| PyPSA                                                                  | status | note                                                                                                                     |
| ---------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| `Store-p_set`, `StorageUnit-p_dispatch_set`, `StorageUnit-p_store_set` | done   | `where:` a value is given and the storage is active, as in PyPSA (`optimize.py:917`, `:922`, `constraints.py:2156-2220`) |

The network: [`rung_37_fixed_storage_dispatch.py`](rung_37_fixed_storage_dispatch.py).

### Rung 38 — delays per investment period

This rung runs `n.optimize(multi_investment_periods=True)` with delayed ports.
PyPSA applies a link's or a process's `delay` in each investment period on its
own (`constraints.py:1370-1378`, `multiports.py:212-219`). A `cyclic_delay`
port wraps from the end of its own period. A port that is not cyclic loses the
flow still in transit at the first snapshots of every period. PyPSA measures
the delay in `generators` weighting per period and rounds it down to a snapshot
start (`multiports.py:106-123`). Scenarios do not change the source snapshot.

The file states a shift by the same whole number of snapshots in every period.
It states an assumption for it,
`Link_output_delay_under_uniform_weighting`.
When data is attached, a tool refuses a delayed port whose `generators`
weighting has more than one value over the horizon (#299).
`Link_output_arrival` and `Process_output_arrival` shift with
`within=snapshot_period[period]`. On a plain run, the data has one period, so
the shift is the flat one.

The rung adds a link that delays by two and wraps, and a process that delays
by one and does not wrap. Both run on two periods of four snapshots. A shift
over the flat horizon would let 2030 receive the flow that 2020 sent. With that
flat shift patched into PyPSA's source index, PyPSA solves the network to
`10543.75` (#620).

| PyPSA                                                          | status | note                                                                                                                                              |
| -------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| link and process `delay`, `cyclic_delay` per investment period | done   | `shift(offset=delay, within=snapshot_period[period])`, with `edge='wrap'` closing each period and `edge=0` vacating each period's first snapshots |

The network: [`rung_38_delay_per_period.py`](rung_38_delay_per_period.py).

### Rung 39 — a negative relative growth

This rung runs `n.optimize(multi_investment_periods=True)` with a carrier whose
`max_relative_growth` is negative. PyPSA clips the share at zero before it
builds `Carrier-growth_limit` (`global_constraints.py:250`), so a negative
share adds nothing and does not tighten the limit. `Carrier_relative_growth`
states the clip as a case: the given share where it is positive, zero
otherwise. On a plain run, the data has one period, and PyPSA builds no
growth row.

The rung adds a battery carrier with `max_growth=20` and
`max_relative_growth=-0.5`, and two stores, built in 2020 and 2030
respectively. Taking the share as given would add half of the 2020 build to the
left side of the 2030 row. With that row patched into PyPSA through
`extra_functionality`, PyPSA solves the network to `9347.5` (#620).

| PyPSA                                                     | status | note                                                                                           |
| --------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------- |
| `Carrier-growth_limit`, `max_relative_growth.clip(min=0)` | done   | `Carrier_relative_growth` is `Carrier_max_relative_growth` where it is positive, `0` otherwise |

The network: [`rung_39_negative_relative_growth.py`](rung_39_negative_relative_growth.py).

### Rung 40 — a global constraint per scenario

The reference script calls `n.set_scenarios(...)` with `GlobalConstraint` rows whose
`constant` and `sense` differ between the scenarios. PyPSA builds one
`GlobalConstraint-{name}` row per scenario for `primary_energy`,
`operational_limit` and `transmission_volume_expansion_limit`. It reads each
scenario's own sense and constant (`global_constraints.py:366-376`,
`:572-573`, `:771-772`, `:806-814`, `:846-856`). The file states
`GlobalConstraint_constant` and `GlobalConstraint_sense` over `scenario` as
well, so each row takes its own value in each future. A row with no scenario
axis in its total, such as the transmission volume, repeats the same capacity
sum under each scenario's constant. On a plain run, the data has one scenario,
and the rows collapse to the standard ones.

The rung puts an extendable line under a volume limit of `60` in the calm
future and `20` in the stormy one. It adds a CO2 row that is at most `250` in
the calm future and exactly `200` in the stormy one. All three are tight at
the optimum. With the same network and the calm values in both futures, PyPSA
solves to `12943.333333333334`.

| PyPSA                                                                                                               | status | note                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `primary_energy`, `operational_limit`, `transmission_volume_expansion_limit` with a constant and sense per scenario | done   | The file states `GlobalConstraint_constant` and `GlobalConstraint_sense` over `scenario`.                                                                                                    |
| `primary_energy`, `operational_limit`, `transmission_volume_expansion_limit`                                        | done   | PyPSA reads a `carrier_attribute` or `investment_period` per scenario (`global_constraints.py:815-822`). The file states the weights and `GlobalConstraint_counts_snapshot` over `scenario`. |

Rungs 52 and 53 extend these rows.

The network: [`rung_40_scenario_global_constraints.py`](rung_40_scenario_global_constraints.py).

### Rung 41 — operating data per scenario

The reference script calls `n.set_scenarios(...)` with a gas unit's `marginal_cost` and a
link's `efficiency` set per scenario. PyPSA reads both through `c.da`, one
value per scenario, into the objective and into `Bus-nodal_balance`
(`components/array.py:347-406`). The file states `Generator_marginal_cost` and
`Link_efficiency` over `scenario`. On a plain run, the data has one scenario,
and the rows collapse to the standard ones.

The rung adds a gas unit that costs `20` in the calm future and `80` in the
stormy one. A second link delivers `0.9` and `0.6` of its flow. Each value
changes the objective. With the calm value in both futures, PyPSA solves to
these objectives.

| calm value in both futures | objective |
| -------------------------- | --------- |
| gas unit `marginal_cost`   | `16308.0` |
| link `efficiency`          | `16992.0` |
| both                       | `15660.0` |

| PyPSA                                                                     | status  | note                                                                                                                  |
| ------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------- |
| objective, `Bus-nodal_balance` with a cost and an efficiency per scenario | done    | `Generator_marginal_cost` and `Link_efficiency` over `scenario`                                                       |
| `Bus-nodal_balance`                                                       | refused | a link `delay` or `cyclic_delay` that differs by scenario, [Refusals](../../../docs/examples/pypsa/scope.md#refusals) |

Rungs 55, 57 and 58 extend these rows.

The network: [`rung_41_scenario_operational_data.py`](rung_41_scenario_operational_data.py).

### Rung 42 — first-stage data per scenario

The reference script calls `n.set_scenarios(...)` with an extendable unit whose
`capital_cost` and `p_nom_max` differ between the scenarios. The build is
chosen once, but PyPSA reads its bounds per scenario. It writes
`Generator-ext-p_nom-lower` and `-upper` once per scenario
(`constraints.py:949-962`), so the tightest cap bounds the build. PyPSA prices
the build at each scenario's capital cost and weights the costs by the scenario
weights (`optimize.py:438-445`, `:484-490`). The build pays its capital cost in
expectation.

The file states `Generator_p_nom_max`, `Generator_capital_cost` and the bound
rows over `scenario`. It states the capital costs in the objective under
`scenario_weight`. On a plain run, the data has one scenario of weight one, and
the rows and the objective collapse to the standard ones.

The rung's wind unit costs `20` in the calm future and `60` in the stormy one,
weighted `0.6` and `0.4`. It may be built to `100` and `30`. PyPSA builds `30`
at the expected cost of `36`. With a cost of `36` and a cap of `30` in both
futures, PyPSA solves the same network to the same objective. With the calm
values in both futures, PyPSA solves to `1943.0`.

| PyPSA                                                 | status | note                                                                   |
| ----------------------------------------------------- | ------ | ---------------------------------------------------------------------- |
| `{c}-ext-p_nom-lower/upper` with a bound per scenario | done   | one row per scenario, over `scenario`, the tightest bounding the build |
| capital cost per scenario                             | done   | `scenario_weight` times each scenario's capital cost                   |

The network: [`rung_42_scenario_first_stage.py`](rung_42_scenario_first_stage.py).

### Rung 43 — a component's sign

This rung runs `n.optimize()` with a generator, a load, a storage unit and a
store whose `sign` is not PyPSA's default. PyPSA multiplies each of these in
`Bus-nodal_balance` by that `sign`:

- a generator's `p`
- a storage unit's `p_dispatch` and `p_store`
- a store's `p` (`constraints.py:1474-1475`)
- a load's `p_set`, on the constant side (`constraints.py:1586`)

PyPSA reads `sign` nowhere else in the model it builds. The default is `1` for
a generator, a storage unit and a store, and `-1` for a load. PyPSA refuses a
`sign` that differs by scenario (`constants.py:46`). The file states
`Generator_sign`, `Load_sign`, `StorageUnit_sign` and `Store_sign` without
`scenario`. On a plain run, the data has PyPSA's defaults, and the row
collapses to the standard one.

The rung adds a unit that draws `20` from its bus at a cost of `-50`. It adds
a storage unit that opens full and a full store. These three have a `sign` of
`-1`. The rung also adds a load of `10` with a `sign` of `1`, which feeds its
bus. Each sign changes the objective. With the default sign restored, PyPSA solves to these
objectives.

| default sign restored on | objective  |
| ------------------------ | ---------- |
| the unit                 | `-5652.78` |
| the load                 | `3925.0`   |
| the storage unit         | `1187.5`   |
| the store                | `925.0`    |
| all four                 | `-5255.56` |

| PyPSA                                       | status | note                                                                                                               |
| ------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| `Bus-nodal_balance` with a component `sign` | done   | `Generator_sign`, `StorageUnit_sign` and `Store_sign` times each variable, and `Load_sign` times the load, negated |

The network: [`rung_43_sign.py`](rung_43_sign.py).

### Rung 45 — ramp limits per snapshot

This rung runs `n.optimize()` with a generator, a link and a process whose
`ramp_limit_up` and `ramp_limit_down` change over time. PyPSA declares both as
a constant or a time series (`static or series`) for all three components. It
declares `ramp_limit_start_up` and `ramp_limit_shut_down` static. The row
between two snapshots takes the limit at the later snapshot
(`constraints.py:1104-1105`, `1089-1090`, `1119-1120`). PyPSA makes the "no
limit" test per snapshot (`constraints.py:1110-1111`), and takes a missing
value as the full build there (`constraints.py:1116-1119`).

The file states `{c}_ramp_limit_up` and `{c}_ramp_limit_down` over `snapshot`,
and `{c}_ramp_up_rate` and `{c}_ramp_down_rate` with them. A snapshot without a
value has no ramp row, unless the row has a start-up or shut-down ramp there.
On a plain run, the data has the same value at each snapshot, and the rows
collapse to the standard ones.

The rung adds a steep bus with a load of `90` at the third snapshot. Each unit
may raise its output by `0.1` of its build, and by `0.5` into the third
snapshot. It may lower its output by `0.1`, and without a limit into the last
snapshot. With the constant limit `0.1` in each direction, the backup covers
the peak, and PyPSA solves to `90871.0` (#620).

| PyPSA                                                | status | note                                                                                                                                                                         |
| ---------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `{c}-p-ramp_limit_up/down` with a limit per snapshot | done   | `{c}_ramp_limit_up`, `{c}_ramp_limit_down` and their rates over `snapshot`, with no row at a snapshot without a value, unless the row has a start-up or shut-down ramp there |

The network: [`rung_45_ramp_per_snapshot.py`](rung_45_ramp_per_snapshot.py).

### Rung 46 — the output brought in

This rung runs `n.optimize()` with units that have `p_init`, the output they
brought into the horizon. PyPSA reads `p_init` only where a unit came in
running (`up_time_before > 0`, or not committable), and zero where it came in
off (`constraints.py:338`). It builds the ramp rows at the first snapshot where
that value exists (`constraints.py:1151`). A unit that came in running
without `p_init` has no ramp row there. PyPSA carries the value into the first
snapshot's rows with the status the unit came in with
(`constraints.py:1158-1163`).

PyPSA builds these rows the same way for a Generator, a Link and a Process. It
does so for a fixed, an extendable and a committable build, and for the big-M
rows of a committable extendable build (`constraints.py:1004-1007`). PyPSA reads
`p_init` per scenario. Under `multi_investment_periods`, it reads `p_init` only
at the horizon's first snapshot, as PyPSA builds no ramp row at a later period
start (`constraints.py:1159-1162`).

The file states `{c}_p_init`, and the output carried in at the first snapshot
is `{c}_status_initial * {c}_p_init`. The first-snapshot `where:` is
`{c}_status_initial == 0 OR {c}_p_init`. On a plain run, the data has no
`p_init`, and the rows collapse to the standard ones.

PyPSA warns where a committable generator came in off and has a `p_init`, and
ignores the value (`consistency.py:669-680`). The product with
`{c}_status_initial` is zero there too. A unit that is not committable comes in
running, whatever its `up_time_before` (rung 71).

PyPSA sets the first-snapshot condition without the `active` condition. A unit
that is not active at the first snapshot still gets a row there, with no
variable in it. The file does not state that row.

The rung adds a warm bus with a load of `150`, then `60`, served by six
ramp-limited units:

- a fixed generator
- a link from `p_init = 0`
- a dear process that came in at full output
- an extendable generator
- a committable generator
- a committable extendable generator

Each `p_init` is tight at the optimum. Without any of them, PyPSA solves to
`9921.0` (#620).

| PyPSA                                                | status | note                                                                                                                          |
| ---------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `{c}-p-ramp_limit_*`, `-bigM`, at the first snapshot | done   | `{c}_previous_p` opens on `{c}_status_initial * {c}_p_init`, and the row exists where `{c}_status_initial == 0 OR {c}_p_init` |

The network: [`rung_46_initial_output.py`](rung_46_initial_output.py).

### Rung 48 — a start and a stop, weighted by the period

This rung runs `n.optimize(multi_investment_periods=True)` with a committable
unit that starts and stops. PyPSA adds `start_up_cost * start_up` and
`shut_down_cost * shut_down` to the objective with the objective weight of the
period, and without the weight of the snapshot (`optimize.py:294-297`,
`:464-465`). It weights every other operating cost by both. PyPSA/PyPSA#2011
added the period weight, which fixed PyPSA/PyPSA#1986. Over
scenarios, it weights the start and stop costs by the scenario weight, as every
operating cost. The file states the two costs in `scenario_opex` with the
period weight, and the scenario weight applies on top.

The rung adds a committable peaker that starts once and stops once in each of
two periods. The period weights are `1.0` and `0.5`, and the snapshot weights
are not `1.0`. PyPSA solves to `7125.0`, and to `6525.0` without the start and
stop costs. The difference is `600.0`, the four events weighted by their period.
Without the period weight, the difference is `800.0` (#620).

| PyPSA                                                                                   | status | note                                                          |
| --------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------- |
| `start_up_cost`, `shut_down_cost` under `multi_investment_periods` and snapshot weights | done   | the period weight and the scenario weight, no snapshot weight |

The network: [`rung_48_start_up_period_weight.py`](rung_48_start_up_period_weight.py).

### Rung 49 — a growth limit in one period

This rung runs `n.optimize()` with a carrier that has `max_growth`. PyPSA
builds `Carrier-growth_limit` only under `multi_investment_periods`, and
returns before it reads the carrier otherwise
(`global_constraints.py:232-233`). A single-period run has no growth limit.
The file states the row where `Carrier_max_growth` has a value.
`Carrier_max_growth` has no value on a single-period run, so no row is built.

The rung adds a cheap extendable wind unit with `max_growth = 10` to the shared
network most rungs start from (the spine). PyPSA builds it to `67` and solves
to `335.0`, the same as without the limit. With the same network as one
investment period under `multi_investment_periods`, PyPSA caps the build at
`10` and solves to `2583.33` (#620).

| PyPSA                                                     | status | note                                                                                 |
| --------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| `Carrier-growth_limit` without `multi_investment_periods` | done   | The file states no row, as `Carrier_max_growth` has no value on a single-period run. |

The network: [`rung_49_single_period_growth.py`](rung_49_single_period_growth.py).

### Rung 50 — a load that is not active

This rung runs `n.optimize()` with a load whose `active` is false. PyPSA
conditions the load side of `Bus-nodal_balance` on `active`
(`constraints.py:1585-1586`), so an inactive load draws nothing. A load has no
build year and no lifetime. Its `active` is the static flag alone, in every
snapshot and every period (`descriptors.py:135-136`). PyPSA refuses an
`active` that differs by scenario (`constants.py:54`).

The file states `Load_active` over the load, and `Load_demand`, the load's
signed demand where it is active and zero where it is not. The balance
contains `Load_demand`. On a plain run, every load is active in the data, and
the row collapses to the standard one.

The rung adds an inactive load to the spine's south bus. PyPSA solves to
`7380.0`, the same as without the load. With the load active, PyPSA solves to
`14730.0` (#620).

| PyPSA                                                | status | note                                               |
| ---------------------------------------------------- | ------ | -------------------------------------------------- |
| `Bus-nodal_balance` with a load that is not `active` | done   | `Load_demand` is zero where `Load_active` is false |

The network: [`rung_50_inactive_load.py`](rung_50_inactive_load.py).

### Rung 51 — a growth limit after an asset retires

This rung runs `n.optimize(multi_investment_periods=True)` with a carrier that
has `max_growth`, and an extendable asset of that carrier that retires before
the last period. In the file, a build counts only in the first period it is
active in: `{c}_first_active` is one there and zero elsewhere. PyPSA takes
`active & (active.cumsum() == 1)`, which is false after the asset retires
(`global_constraints.py:278`).

The rung adds two solar units under one carrier with `max_growth = 10`. The
old one is active in 2020 only, the new one in 2030 only. Both build to `10`,
and PyPSA solves to `3432.5`. A limit that counts the old unit again in 2030
caps the new one at `10` minus the old one's build. PyPSA then solves to
`5185.0`. Without `max_growth`, PyPSA solves to `248.75`.

| PyPSA                                             | status | note                                                                    |
| ------------------------------------------------- | ------ | ----------------------------------------------------------------------- |
| `Carrier-growth_limit` with an asset that retires | done   | `{c}_first_active` is zero after the first period an asset is active in |

The network: [`rung_51_growth_retired_asset.py`](rung_51_growth_retired_asset.py).

### Rung 52 — a transmission cost limit per scenario

The reference script calls `n.set_scenarios(...)` with a
`transmission_expansion_cost_limit` row. The file states the row in every
scenario, as it states every global constraint. PyPSA builds one row per
scenario too, with that scenario's capital cost
(`global_constraints.py:806-856`, `:900`).

The rung adds an extendable DC link to the spine under a cost limit of `150`,
so the link builds `15`. The two futures are identical, and PyPSA solves to
`15630.0`, the objective of the network without scenarios. Without the row,
PyPSA solves to `11890.0`.

| PyPSA                                                           | status | note                 |
| --------------------------------------------------------------- | ------ | -------------------- |
| `transmission_expansion_cost_limit` on a network with scenarios | done   | the row per scenario |

The network: [`rung_52_scenario_cost_limit.py`](rung_52_scenario_cost_limit.py).

### Rung 53 — a transmission volume limit per scenario and period

The reference script calls `n.set_scenarios(...)` and runs
`n.optimize(multi_investment_periods=True)` with a
`transmission_volume_expansion_limit` row. The file states the row in every
scenario. PyPSA builds one row per scenario too, over the lines active in the
row's periods, with that scenario's length (`global_constraints.py:828`,
`:874-875`).

The rung is two periods with an extendable line of length `3` under a volume
limit of `60`, so the line builds `20`. The two futures are identical, and
PyPSA solves to `15005.0`, the objective of the network without scenarios.
Without the row, PyPSA solves to `1465.0`.

| PyPSA                                                                                            | status | note                 |
| ------------------------------------------------------------------------------------------------ | ------ | -------------------- |
| `transmission_volume_expansion_limit` on a network with scenarios and `multi_investment_periods` | done   | the row per scenario |

The network: [`rung_53_scenario_period_volume_limit.py`](rung_53_scenario_period_volume_limit.py).

### Rung 55 — a transformer cycle per scenario

The reference script calls `n.set_scenarios(...)` with two transformers in parallel, a
cycle. The file states the Kirchhoff voltage row in every scenario, and PyPSA
builds it in every scenario too (`constraints.py:1738-1750`). PyPSA takes a
phase shift per scenario, and the file states one for every scenario (#783).

The rung adds two transformers of reactance `0.1` and `0.2`, each rated `30`,
to the spine. The row splits the flow two to one, so the first caps the pair at
`45`. The two futures are identical, and PyPSA solves to `13105.0`, the
objective of the network without scenarios. With one transformer rated `60`,
PyPSA solves to `11705.0`.

| PyPSA                                                                  | status | note                                                                 |
| ---------------------------------------------------------------------- | ------ | -------------------------------------------------------------------- |
| `Kirchhoff-Voltage-Law` with a transformer on a network with scenarios | done   | the row per scenario, with one phase shift for every scenario (#783) |

The network: [`rung_55_scenario_transformer_cycle.py`](rung_55_scenario_transformer_cycle.py).

### Rung 56 — a security-constrained run per scenario

This rung runs `n.optimize.optimize_security_constrained(...)` on a network
with scenarios. The file states the outage copies in every scenario. PyPSA
builds them in every scenario too, with the outage factors of the first
scenario (`abstract.py:610-619`, `:652-664`).

The rung adds two parallel lines rated `30` and `35` to the spine, and outages
each. Each line must carry the whole import alone, so the import falls to `30`.
The two futures are identical, and PyPSA solves to `18205.0`, the objective of
the network without scenarios. With a plain `n.optimize()`, PyPSA solves to
`11705.0`.

| PyPSA                                                                                 | status | note                    |
| ------------------------------------------------------------------------------------- | ------ | ----------------------- |
| `Line-fix-s-*-security-for-{c}-outage-in-sub-network-{n}` on a network with scenarios | done   | the copies per scenario |

The network: [`rung_56_scenario_security_constrained.py`](rung_56_scenario_security_constrained.py).

### Rung 57 — a fixed build per scenario

The reference script calls `n.set_scenarios(...)` with `p_nom_set` on an
extendable unit.
The file states `Generator-p_nom_set` once, and PyPSA builds it once per
scenario (`constraints.py:1915-1924`). PyPSA refuses a `p_nom_set` that
differs by scenario (`constants.py:42-44`), so the rows are equal. The file
states `Generator_p_nom_set` and every other `*_nom_set` without `scenario`.

The rung adds a cheap extendable wind unit to the spine, pinned to `20`. The
two futures are identical, and PyPSA solves to `4800.0`, the objective of the
network without scenarios. Without `p_nom_set`, PyPSA builds the unit to `67`
and solves to `335.0`.

| PyPSA                                       | status | note                                                       |
| ------------------------------------------- | ------ | ---------------------------------------------------------- |
| `{c}-p_nom_set` on a network with scenarios | done   | one row, the same feasible set as PyPSA's row per scenario |

The network: [`rung_57_scenario_nom_set.py`](rung_57_scenario_nom_set.py).

### Rung 58 — a committable unit per scenario

The reference script calls `n.set_scenarios(...)` with a committable unit. The file
states the status rows in every scenario, and PyPSA builds them in every
scenario too.

The rung adds a cheap committable unit to the spine that cannot run below `40`
% of its build, with a start-up cost of `100`. The two futures are identical,
and PyPSA solves to `7430.0`, the objective of the network without scenarios.
With the same unit not committable, PyPSA solves to `7330.0`.

| PyPSA                                   | status | note                  |
| --------------------------------------- | ------ | --------------------- |
| `{c}-com-*` on a network with scenarios | done   | the rows per scenario |

The network: [`rung_58_scenario_committable.py`](rung_58_scenario_committable.py).

### Rung 60 — efficiencies per snapshot

This rung runs `n.optimize()` with a link, a process, a storage unit, a fuel
unit and a transformer whose coefficients change over time. PyPSA declares
these coefficients `static or series` and reads each per snapshot:

- a link's `efficiency`, `efficiency2`, …
- a process's `rate0`, `rate1`, …
- a storage unit's `efficiency_store` and `efficiency_dispatch`
- a generator's `efficiency`
- a transformer's `phase_shift`

PyPSA's balance takes a port's coefficient at the snapshot the flow arrives.
It shifts the flow first and multiplies it by the coefficient after
(`constraints.py:1565-1569`). The energy balance of a storage unit takes both
efficiencies per snapshot (`constraints.py:2167-2168`). A `primary_energy` row
divides a generator's output by its efficiency at the same snapshot
(`global_constraints.py:434-439`). A fixed phase shift enters the cycle sum per
snapshot (`constraints.py:1738-1744`).

The file states `Link_efficiency`, `Process_rate`,
`StorageUnit_efficiency_store`, `StorageUnit_efficiency_dispatch`,
`Generator_primary_energy_weight` and `Transformer_phase_shift_weight` over
`snapshot`. `Link_output_arrival` and `Process_output_arrival` contain the
shifted flow times the coefficient. The file states a standing loss per
snapshot in `StorageUnit_retention` and `Store_retention`. On a plain run, the
data has the same value at each snapshot, and the rows are the standard ones.

The rung adds a sink fed from a source over a link and a process that both
deliver one snapshot late. Beside them are a storage unit and a fuel unit under a
`primary_energy` cap. A separate triangle has a transformer with a fixed phase
shift per snapshot. The `generators` weighting is uniform, as in rung 16.
PyPSA solves to `130562.09`, and each coefficient changes the objective. With
the coefficient held at its mean at each snapshot, PyPSA solves to these
objectives (#620).

| coefficient held at its mean       | objective   |
| ---------------------------------- | ----------- |
| link `efficiency`                  | `130774.59` |
| process `rate1`                    | `130622.09` |
| storage unit `efficiency_store`    | `129770.09` |
| storage unit `efficiency_dispatch` | `129966.86` |
| generator `efficiency`             | `131280.86` |
| transformer `phase_shift`          | `130313.38` |

The snapshot at which a delayed port takes the coefficient also changes the
result. With each series moved one snapshot later, the port takes it at the
snapshot the flow departs. PyPSA then solves to `130676.26` for the link and to
`130742.09` for the process.

| PyPSA                                                         | status | note                                                                                               |
| ------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| `Bus-nodal_balance` with an efficiency or a rate per snapshot | done   | `Link_efficiency` and `Process_rate` span `snapshot`, taken at the snapshot a delayed flow arrives |
| `StorageUnit-energy_balance` with efficiencies per snapshot   | done   | `StorageUnit_efficiency_store` and `StorageUnit_efficiency_dispatch` span `snapshot`               |
| `primary_energy` with a generator efficiency per snapshot     | done   | `Generator_primary_energy_weight` spans `snapshot`                                                 |
| `Kirchhoff-Voltage-Law` with a fixed phase shift per snapshot | done   | `Transformer_phase_shift_weight` spans `snapshot`                                                  |

The network: [`rung_60_efficiency_per_snapshot.py`](rung_60_efficiency_per_snapshot.py).

### Rung 61 — voltage angle limits

This rung runs `n.optimize()` with a cap on the voltage angle difference across
a line or a transformer. PyPSA master adds `v_ang_max`, in degrees, on Line and
Transformer (PyPSA#1910). PyPSA builds two rows for each active AC line and
transformer with a finite `v_ang_max` (`constraints.py:1764-1881`, called at
`optimize.py:951`). The rows bound the angle difference by the cap either
way.

The angle difference is `x_pu_eff` times the flow, plus the shift in radians
for a transformer. PyPSA divides through by `x_pu_eff`, so the flow takes
coefficient one. A fixed shift moves the bounds: `Transformer-v_ang-lower` and
`Transformer-v_ang-upper`. A decided shift is a variable of the row:
`Transformer-v_ang-var-lower` and `Transformer-v_ang-var-upper`. PyPSA ignores
`v_ang_min` and warns that it is deprecated, so the file has no parameter for
it.

This rung has no scenarios, and no rung states the angle rows on a network
with scenarios. PyPSA takes the phase shift per scenario, and the file states
one for every scenario (#783).

The rung adds a line with a cap of one degree beside the link of the spine. The
lossy link carries the rest of the flow south. Two triangles each carry
cheap upstream power to a town past a costly local unit. In the first, the
transformer has a fixed shift of two degrees. In the second, the shift is a
decision. In one cycle, the angle caps of all branches couple, so each triangle
has one cap.

PyPSA solves to `121834.62`, and each cap is tight at the optimum. With a cap
removed, PyPSA solves to these objectives (#620).

| cap removed                       | objective   |
| --------------------------------- | ----------- |
| line `north_south61`              | `121161.89` |
| transformer `ca61`, fixed shift   | `35214.37`  |
| transformer `fd61`, decided shift | `111382.98` |
| all three                         | `24090.0`   |

| PyPSA                                                        | status | note                                                                               |
| ------------------------------------------------------------ | ------ | ---------------------------------------------------------------------------------- |
| `Line-v_ang-lower`, `Line-v_ang-upper`                       | done   | `Line_carrier == 'AC'` in the `where`, and no row for an infinite `Line_v_ang_max` |
| `Transformer-v_ang-lower`, `Transformer-v_ang-upper`         | done   | the fixed shift is `Transformer_phase_shift_fixed`, per snapshot                   |
| `Transformer-v_ang-var-lower`, `Transformer-v_ang-var-upper` | done   | the decided shift is the `Transformer_phase_shift` variable, in degrees            |
| `{c}-v_ang-*` on a network with scenarios                    | done   | the rows per scenario, with one phase shift for every scenario (#783)              |

The network: [`rung_61_voltage_angle_limits.py`](rung_61_voltage_angle_limits.py).

### Rung 62 — a start-up cost per snapshot

This rung runs `n.optimize()` with a committable unit whose start-up and
shut-down costs change over time. PyPSA declares the `start_up_cost` and
`shut_down_cost` of a Generator, a Link and a Process as `static or series`
(PyPSA/PyPSA#1909). It takes the cost of a start or a stop at its snapshot
(`optimize.py:457-468`). It still adds the cost without the weight of the
snapshot and without the weight of the period, as rung 48 states.

The file states the same, with `Generator_start_up_cost`,
`Generator_shut_down_cost` and the Link and Process pairs over `snapshot`. A
static cost is the same value at each snapshot.

The rung adds a committable peaker that the load needs in the third and
fourth snapshots. A start costs `100` in the second snapshot and `900` in the
third, and a stop is free only in the last snapshot. PyPSA solves to `6850.0`:
the unit starts one snapshot early at minimum output and stops in the last
snapshot. Each series changes the objective (#807).

| cost changed                             | objective |
| ---------------------------------------- | --------- |
| start-up cost held at its mean, `640.0`  | `7090.0`  |
| shut-down cost held at its mean, `240.0` | `7050.0`  |
| start-up cost times the snapshot weight  | `6900.0`  |

| PyPSA                                          | status | note                                                                                            |
| ---------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------- |
| `start_up_cost`, `shut_down_cost` per snapshot | done   | Generator, Link and Process over `[scenario, snapshot, …]`, with no snapshot weight, as rung 48 |

The network: [`rung_62_startup_cost_per_snapshot.py`](rung_62_startup_cost_per_snapshot.py).

### Rung 63 — modular branches and storage

PyPSA builds `{c}-n_mod` and the `{c}-{attr}_modularity` row for every
component with a nominal build (`variables.py:371-392`,
`constraints.py:1927-1987`, called at `optimize.py:871-874` and `:901-905`):

- Generator, Link and Process on `p_nom`
- Line and Transformer on `s_nom`
- StorageUnit on `p_nom`
- Store on `e_nom`

PyPSA builds each only for a unit that is extendable, modular and among
`c.active_assets` (`variables.py:387`, `constraints.py:1967`). These are the
units whose static `active` flag is true
(`components/descriptors.py:151-187`). The file states the pairs of Line,
Transformer, StorageUnit and Store. In the file, a unit is among
`active_assets` where it is active in at least one snapshot.

PyPSA reads the static `active` flag, so it also builds both for a unit whose
build year and lifetime miss every period. No other PyPSA row contains
`{c}-n_mod`. PyPSA builds no `{c}-{attr}` column for a unit that is not active
either. The file declares `{c}_{attr}_ext` there, priced at zero by
`{c}_capital_weight`.

The rung feeds an east bus over a modular line and a modular transformer, with
a modular storage unit and store on it. Beside them are a modular extendable
generator, link and process with `active = False`, for which PyPSA builds no
`n_mod`. PyPSA solves to `13927.0`, and each module size changes the
objective. With the module size of that component set to zero, PyPSA solves to
these objectives (#815).

| module size set to zero  | objective |
| ------------------------ | --------- |
| line `s_nom_mod`         | `13882.0` |
| transformer `s_nom_mod`  | `13921.0` |
| storage unit `p_nom_mod` | `13877.0` |
| store `e_nom_mod`        | `13873.0` |

| PyPSA                                                              | status | note                                                                    |
| ------------------------------------------------------------------ | ------ | ----------------------------------------------------------------------- |
| `Line-n_mod`, `Line-s_nom_modularity`                              | done   |                                                                         |
| `Transformer-n_mod`, `Transformer-s_nom_modularity`                | done   |                                                                         |
| `StorageUnit-n_mod`, `StorageUnit-p_nom_modularity`                | done   |                                                                         |
| `Store-n_mod`, `Store-e_nom_modularity`                            | done   |                                                                         |
| `{c}-n_mod`, `{c}-{attr}_modularity` for a unit that is not active | done   | no column and no row where `count({c}_active, over=snapshot) > 0` fails |

The network: [`rung_63_modular_branches_and_storage.py`](rung_63_modular_branches_and_storage.py).

### Rung 64 — commitment edges

This rung runs `n.optimize(multi_investment_periods=True)` with a committable
generator, link and process built in the later period, and a committable unit
with no build cap. PyPSA counts a start against the previous snapshot's status
and reads a status it did not build as zero (`constraints.py:391`). So a unit
that opens in a later period starts from off at its first snapshot, and pays
its start-up cost there. The file states this zero status in
`Generator_previous_status` and its `Link` and `Process` siblings. Without the
zero, the previous status at that first snapshot is absent. The start-up row is
then not built, and the unit starts for free.

A committed extendable unit has a big-M bound in its `com-ext-p-*` rows. Where
`p_nom_max` is finite and positive, M is that cap times the highest
`p_max_pu`. Where the cap is infinite, PyPSA takes the `committable_big_m`
keyword (`components.py:1100-1171`). Without the keyword, M is ten times the
largest of the peak total load and the component's largest finite `p_nom` and
`p_nom_max`. `Generator_big_m` is M by the same rule. An M below the output the
solver chooses caps that output.

PyPSA solves to `9140.0`. The three units start once each, at the first
snapshot of the 2030 period, and their start-up costs take that period's weight
of `0.5`. With their start-up rows dropped there, PyPSA solves to `9035.0`, the
three weighted start-up costs less. The uncapped unit builds `70`, below its M
of `3000`. With `committable_big_m=50`, PyPSA solves to `11640.0`, and the unit
builds `50` (#817, #975).

| PyPSA                                                            | status | note                                                                                                        |
| ---------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| `{c}-com-transition-start-up` for a unit built in a later period | done   | `Generator_previous_status` is zero at the first snapshot a unit is active in past the first of the horizon |
| `{c}-com-ext-p-*` (big-M) with `p_nom_max = inf`                 | done   | `Generator_big_m` is M by PyPSA's rule                                                                      |

The network: [`rung_64_commitment_edges.py`](rung_64_commitment_edges.py).

### Rung 66 — cycles per period

This rung runs
`n.optimize.optimize_security_constrained(multi_investment_periods=True)` over
a network whose meshes change between periods. PyPSA builds the cycle basis of
each period from the branches that are active in it. It writes the cycle rows of
each period over that period's snapshots only (`constraints.py:1710-1729`). A
cycle label is a position in its period's basis, so label `0` may name a
different cycle in each period.

The file states the cycle weights `Line_cycle_weight`,
`Transformer_cycle_weight` and `Transformer_phase_shift_cycle_weight` over
`period`. `Kirchhoff_Voltage_Law` contains, at each snapshot, the weights of
that snapshot's period. A cycle label that the basis of a period does not reach
has no weight there, and its row is not built. On a plain run, the data has
one period, and the rows are the standard ones.

The rung joins `a` and `c` over `ab66` and `bc66`, which form a path in the
2020 period. The line `ca66` comes in with 2030 and closes a triangle, so 2030
has one cycle and 2020 has none. PyPSA builds 2 cycle rows and solves to
`16000.0`. A single basis over all branches would apply the triangle's row to
the 2020 snapshots, with `ca66` absent. That row and the balance at `b` force
the flow on `ab66` and `bc66` to zero. Without those two lines in 2020, PyPSA
solves to `43900.0` (#814).

The run outages `ca66`, which is active in 2030 only. In 2020 `ca66` is not
active, so the file states no copy in 2020 and PyPSA builds none
(`abstract.py:653-664`). PyPSA builds the 6 copies of 2030 for the lower and
the upper limit, and the file states the same 6.

| PyPSA                                                         | status | note                                                            |
| ------------------------------------------------------------- | ------ | --------------------------------------------------------------- |
| `Kirchhoff-Voltage-Law` per investment period                 | done   | the cycle weights span `period`, read at each snapshot's period |
| `Line-fix-s-*-security-…` for a branch not active in a period | done   | no factor and no copy                                           |

The network: [`rung_66_cycles_per_period.py`](rung_66_cycles_per_period.py).

### Rung 68 — outage factors per period

This rung runs
`n.optimize.optimize_security_constrained(multi_investment_periods=True)` with
an outage of a line that retires before the last period. `Line_BODF` and
`Transformer_BODF` are the outage factors of each period, from the branches
active in it. The file states the copies of a period over its snapshots only.
PyPSA does the same. It finds the sub-networks of each period's active
branches and names the copies of the period `…-period-{p}`
(`abstract.py:653-664`). It refuses an outage named in `branch_outages` that
is active in no period (`abstract.py:634-643`).

The rung joins `a` and `b` over two lines rated `60`. `ab_old68` is active in
2020 and retires in 2025, and `ab68` is active in both periods. The run outages
`ab_old68`. In 2020 its factor on `ab68` is `1`, so `ab68` carries the whole
import alone after the outage, and the import is at most `60`. In 2030
`ab_old68` is not active and has no copy.

PyPSA solves to `13000.0`. Without the 2020 copies, the import is up to `120`
in 2020, and PyPSA solves to `8050.0`.

| PyPSA                                                                             | status | note                                             |
| --------------------------------------------------------------------------------- | ------ | ------------------------------------------------ |
| `Line-fix-s-*-security-…` for an outage of a branch not active in the last period | done   | `Line_BODF` and `Transformer_BODF` span `period` |

The network: [`rung_68_outage_factors_per_period.py`](rung_68_outage_factors_per_period.py).

### Rung 69 — storage that retires before the close

This rung runs `n.optimize(multi_investment_periods=True)` with a
`primary_energy` row over storage that keeps its level across periods and
retires before the last counted snapshot. PyPSA fills the level forward over
the counted snapshots and takes the last value
(`global_constraints.py:476-479`, `:528-531`, and `:682-685`, `:730-733` for
`operational_limit`). The level exists only where the storage is active.
PyPSA's row therefore contains the level at the last counted snapshot where the
storage is active.

The file states that snapshot as
`StorageUnit_last_counted_active` and
`Store_last_counted_active`. The counted
snapshots are the whole horizon or one period, and a storage is active in one
continuous stretch of periods. So the snapshot is the last one where the two
overlap.

The rung adds a store and a storage unit of an emitting carrier. Each has an
initial level of 20 and retires after 2020. A CO2 cap of `5` applies over the
horizon. The row bounds the two levels at the last snapshot of 2020 to at least
`35`. A row at the last snapshot of 2030, where neither storage is active,
would have no variable and would be `0 <= -35`.

| PyPSA                                 | status | note                                                                                                                                                                                |
| ------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `primary_energy`, `operational_limit` | done   | for storage that retires before the last counted snapshot, `StorageUnit_last_counted_active` and `Store_last_counted_active`, the last counted snapshot where the storage is active |

The network: [`rung_69_storage_retires_before_close.py`](rung_69_storage_retires_before_close.py).

### Rung 70 — a risk preference of weight zero

This rung is rung 14 with `n.set_risk_preference(alpha=0.5, omega=0.0)`.
Under any risk preference, PyPSA builds `CVaR-a`, `CVaR-theta`, `CVaR`,
`CVaR-excess-{s}` and `CVaR-def` (`optimize.py:497`, `variables.py:508`), and
refuses a quadratic cost (`optimize.py:506-513`). Without a risk preference,
it builds none of them. With and without the risk preference, PyPSA solves to
`7946.733333333334`, and the risk preference adds 3 rows (#849).

In the file, the columns, the rows and the assumption against a quadratic cost
exist where `CVaR_omega` has a value. A value of `0.0` counts. `CVaR_omega`
has a value only where a risk preference is set. The columns take
`missing: 0`, so the objective's cost `CVaR_omega * CVaR` exists without them.

| PyPSA                                         | status  | note                                                                         |
| --------------------------------------------- | ------- | ---------------------------------------------------------------------------- |
| `CVaR-a`, `CVaR-theta`, `CVaR` at `omega = 0` | done    | where `CVaR_omega` has a value                                               |
| `CVaR-excess-{s}`, `CVaR-def` at `omega = 0`  | done    | where `CVaR_omega` has a value                                               |
| objective at `omega = 0`                      | refused | a quadratic cost, [Refusals](../../../docs/examples/pypsa/scope.md#refusals) |

The network: [`rung_70_risk_preference_zero.py`](rung_70_risk_preference_zero.py).

### Rung 71 — a unit that is not committable comes in running

This rung runs `n.optimize()` with a unit that is not committable and has
`up_time_before = 0`, a `p_init` and a ramp limit, beside a committable unit.
PyPSA reads the status brought in as one for every unit that is not
committable (`constraints.py:323`). The unit ramps from its `p_init` into the
first snapshot, and its ramp row gets no start-up term
(`constraints.py:1141-1147`). Before PyPSA/PyPSA#1973, the same unit came in
off, and its first-snapshot ramp depended on whether another unit was
committable (PyPSA/PyPSA#1943).

The file states `Generator_status_initial` as one for a unit that is not
committable, so `Generator_previous_p` opens on its `p_init`.

The cheap unit ramps from `10` by `10` a snapshot, and its ramp row is tight at
the optimum. PyPSA solves to `4836.1111`. With `up_time_before = 1`, or without
the committable unit, it solves to the same objective. Without the `p_init`,
it solves to `4500.0` (#977).

| PyPSA                                                                                 | status | note                                                         |
| ------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------ |
| `Generator-p-ramp_limit_up` at the first snapshot, for a unit that is not committable | done   | `Generator_status_initial` is one, whatever `up_time_before` |

The network: [`rung_71_running_unless_committable.py`](rung_71_running_unless_committable.py).

### Rung 72 — modular down time

This rung runs `n.optimize()` with a fixed and an extendable committable
modular generator, each with a minimum down time. The status of a modular unit
counts the modules that are on. PyPSA bounds its down-time row by the module
count: `p_nom / p_nom_mod` for a fixed build, and `n_mod` for an extendable one
(`constraints.py:656-683`). Before PyPSA/PyPSA#2051, the bound was one, so a
modular unit with a minimum down time ran one module at most.

The file states the bound as `Generator_modules`, which is `Generator_n_mod`
for an extendable modular build and `Generator_modules_installed` otherwise.

Both units come in off, and the load dips below what one module can run at its
minimum part load. A fixed modular unit that came in running is the open case
PyPSA/PyPSA#2114: the start-up transition and this row count the status it
brought in as one module. Modules that stop at the dip stay off for two snapshots.
PyPSA solves to `17190.0`. Without the minimum down times, it solves to
`9390.0`. At `51986084`, before PyPSA/PyPSA#2051, it solved to `43495.0`
(#977).

| PyPSA                              | status | note                                     |
| ---------------------------------- | ------ | ---------------------------------------- |
| `Generator-com-down-time`, modular | done   | bound by `Generator_modules`, not by one |

The network: [`rung_72_modular_down_time.py`](rung_72_modular_down_time.py).

### Rung 73 — the ramp of a fixed modular unit

This rung runs `n.optimize()` with a fixed committable modular generator that
has ramp limits and came in running at a `p_init`. Each module that is on
ramps by its own share, `ramp_limit_up * p_nom_mod`
(`constraints.py:1131-1134`). At the first snapshot, PyPSA counts every
installed module as on, since the status brought in is on or off
(`constraints.py:1152-1157`). The start-up transition and the down-time row
count the same status as one module (PyPSA/PyPSA#2114). This rung has no
start-up cost and no minimum down time, so neither of them binds. Before PyPSA/PyPSA#2055, the share was
`ramp_limit_up * p_nom`, so a fixed modular unit ramped as many times faster
as it had modules (PyPSA/PyPSA#1985).

The file states the share against `Generator_p_nom_committed`, one module for
any modular build. `Generator_ramp_previous_status` counts every installed
module at the first snapshot.

The unit has three modules of `20` and ramps by `10` per module that is on.
Its first-snapshot ramp from `15` to `45` and the ramps that follow are tight
at the optimum. PyPSA solves to `12300.0`. Without the `p_init`, it solves to
`11320.0`, and without the ramp limits, to `8135.0`. At `51986084`, before
PyPSA/PyPSA#2055, it solved to `8135.0` (#977).

| PyPSA                                                           | status | note                                                                                  |
| --------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------- |
| `Generator-p-ramp_limit_up`, `-down`, fixed modular committable | done   | per module, and every installed module on at the first snapshot after a running start |

The network: [`rung_73_fixed_modular_ramp.py`](rung_73_fixed_modular_ramp.py).

### Rung 75 — a primary-energy cap for one period over storage that reopens per period

This rung runs `n.optimize(multi_investment_periods=True)` with a
`primary_energy` row for 2030 alone, over a gas storage unit and a gas store
that each reopen per period. PyPSA counts the storage change of the stated
period only: its opening level less its closing level at the period's last
snapshot, weighted by that period's years (`global_constraints.py:390-394`,
`:489-493`, `:541-545`). Before PyPSA/PyPSA#2099, PyPSA took the last snapshot
of every period and raised `KeyError` (PyPSA/PyPSA#2093).

The file states the closing level as `StorageUnit_closing_weight` and
`Store_closing_weight`, which are the period's years at the last snapshot of
each counted period. On a network with scenarios, PyPSA still raises: see
[Refusals](../../../docs/examples/pypsa/scope.md#refusals).

The cap of `600` binds, and the row counts `10` years of each storage's
opening level against it. PyPSA solves to `12900.0`. Without the cap, it solves
to `9000.0`, and with the cap over the horizon, to `16500.0`. With the storage
on a carrier that emits nothing, it solves to `11400.0` (#977).

| PyPSA                                                                              | status | note                                                                         |
| ---------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------- |
| `primary_energy` for one period over storage that reopens per period, no scenarios | done   | `StorageUnit_closing_weight` and `Store_closing_weight` in the stated period |

The network: [`rung_75_period_primary_energy_storage.py`](rung_75_period_primary_energy_storage.py).

### Rung 76 — a store that covers a storage unit

This rung runs `n.optimize()` with four stores that use what PyPSA/PyPSA#1934
gave the Store. PyPSA deprecates the StorageUnit in favour of the Store, and
still builds every StorageUnit row.

- A store has a charging variable `Store-p_store` beside its net dispatch
  `Store-p`, so `p + p_store` is the discharge. Every store has the variable.
  Where a store does not split its dispatch, PyPSA holds `p_store` at zero by
  its bound rows, and the charging bound applies to `p` (`stores.py:79-116`).
  A store splits where an efficiency differs from one, a cost applies to one
  direction only, or `cycles_max` is finite.
- A finite `max_hours` gives the store a power rating `e_nom / max_hours`.
  PyPSA bounds the discharge by `p_max_pu` and the charge by `-p_min_pu` times
  that rating (`constraints.py:142-144`, `:239-241`). The bound rows are
  `Store-fix-p-*`, `Store-fix-p_store-*` and their `ext` siblings. Without
  `max_hours`, the rating is infinite and PyPSA builds no row on that side.
- The energy balance draws the discharge down before `efficiency_dispatch`,
  adds the charge after `efficiency_store`, and adds `inflow` less `spill`
  (`constraints.py:2472-2476`, `:2560-2567`).
- `marginal_cost_dispatch` prices the discharge, `marginal_cost_store` the
  charge, and `spill_cost` the spill. `marginal_cost` keeps pricing the net
  dispatch (`optimize.py:108-120`).

The file states the bounds per unit of `e_nom` as `Store_discharge_floor_pu`
and `Store_charge_cap_pu`, and whether a store splits as
`Store_split_dispatch`, from data prep. With every new attribute at its
default, the new rows hold `p_store` at zero and the balance is the old one.

The rung adds to the south bus a rated battery with an efficiency each way and
a discharge cost, a reservoir with inflow that spills at its rating, and an
extendable lossy store with a charging cost. An unrated extendable store sits
on the north bus. PyPSA solves to `11362.9444`. The variants solve to these
objectives (#977):

| network                                | objective    |
| -------------------------------------- | ------------ |
| the battery without `max_hours`        | `11343.8333` |
| the battery's efficiencies at `1`      | `11174.2333` |
| the battery's discharge cost at `0`    | `11317.3444` |
| the reservoir without inflow           | `12523.7796` |
| the reservoir's spill cost at `0`      | `11329.1944` |
| the reservoir without `max_hours`      | `8538.7333`  |
| the lossy store's charging cost at `0` | `11332.0833` |
| the lossy store's efficiency at `1`    | `11043.0167` |

| PyPSA                                                                    | status | note                                                                                                                                          |
| ------------------------------------------------------------------------ | ------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `Store-p_store`                                                          | done   | every store, held at zero where it does not split its dispatch                                                                                |
| `Store-spill`                                                            | done   | `where: inflow > 0`, [`missing: 0`](../../../docs/reference/language/absence.md#missing), with bounds on the variable, as `StorageUnit-spill` |
| `Store-fix-p-*`, `Store-ext-p-*`                                         | done   | on `p + p_store`, where `max_hours` has a value, and the floor of zero for a store that splits                                                |
| `Store-fix-p_store-*`, `Store-ext-p_store-*`                             | done   | the cap of zero for a store that does not split                                                                                               |
| `Store-energy_balance`                                                   | done   | both efficiencies, inflow and spill                                                                                                           |
| `marginal_cost_dispatch`, `marginal_cost_store`, `spill_cost` of a Store | done   | in `Store_opex`                                                                                                                               |

The network: [`rung_76_store_power.py`](rung_76_store_power.py).

### Rung 77 — energy limits on every dispatching component

This rung runs `n.optimize(multi_investment_periods=True)` with `e_sum_min` or
`e_sum_max` on a Generator, a Link, a Process and a Store. Since
PyPSA/PyPSA#1987, PyPSA builds `{c}-e_sum_min` and `{c}-e_sum_max` for each of
them (`constraints.py:2938-2954`). The energy is the sum of `p` weighted by
the generator weighting. For a Link, `p` is the withdrawal at `bus0`, and for
a Store, the net dispatch. Under `multi_investment_periods`, each snapshot also
weighs its period's `years`, as in an `operational_limit` row
(`constraints.py:2935-2937`).

The file states the four pairs of rows over `energy_limit_weight`, the
generator weighting times `period_weight_years`. On a plain run the years are
one, so the rows collapse to the standard ones.

The generator's, the process's and the store's caps and the link's floor are
tight at the optimum. The three other limits are not. PyPSA solves to
`11618.75`.
With the years at `1`, it solves to `16428.125`. Without the generator's
cap, it solves to `7900.625`. Without the link's floor, it solves to
`11508.75`, without the process's cap to `8677.5`, and without the store's
cap to `6225.0` (#977).

| PyPSA                                                                | status | note                                      |
| -------------------------------------------------------------------- | ------ | ----------------------------------------- |
| `Generator-e_sum_min/max` under `multi_investment_periods`           | done   | each snapshot weighs its period's `years` |
| `Link-e_sum_min/max`, `Process-e_sum_min/max`, `Store-e_sum_min/max` | done   | the same row over each component's `p`    |

The network: [`rung_77_energy_limits.py`](rung_77_energy_limits.py).

### Rung 78 — a cycle limit on a store

This rung runs `n.optimize()` with two stores that have `cycles_max`, the most
equivalent full cycles over the horizon (PyPSA/PyPSA#2006). PyPSA builds one
`Store-cycles_max` row per store: the discharge `p + p_store`, weighted by the
stores weighting and summed over the horizon, is at most `cycles_max` times
`e_nom`, or the chosen `e_nom` of an extendable store
(`constraints.py:2607-2633`). A finite `cycles_max` makes the store split its
dispatch, so `p_store` carries the charge and the discharge is at least zero
(rung 76).

The file states the row over `Store_e_nom_effective`, the chosen build where
the store is extendable and the given one otherwise.

Both rows are tight at the optimum. PyPSA solves to `15004.0`, and the
extendable store builds `114`. Without the fixed store's limit, PyPSA solves
to `14974.0`, and without the extendable store's limit, to `14947.0` (#977).

| PyPSA              | status | note                         |
| ------------------ | ------ | ---------------------------- |
| `Store-cycles_max` | done   | over `Store_e_nom_effective` |

The network: [`rung_78_store_cycles.py`](rung_78_store_cycles.py).

### Rung 79 — flow-based market coupling

This rung runs `n.optimize()` with a flow-based domain (PyPSA/PyPSA#2069).
A `GlobalConstraint` of type `flow_based` is one critical network element with
contingency (CNEC). It lists its zonal power transfer distribution factors
(PTDF) as `ptdf_<name>` attributes. A name is a zone bus, or a corridor link
whose flow enters the row. PyPSA builds:

- `FlowBased-net_position`, an unbounded variable per zone bus and snapshot,
  which leaves the zone's nodal balance (`flow_based.py:207-234`,
  `constraints.py:1578`)
- `GlobalConstraint-ram`, a row per CNEC and snapshot: the net positions and
  corridor flows, each times its factor, are at most the CNEC's remaining
  available margin `ram`. A `ram` of NaN drops the row in that snapshot, and
  an `investment_period` limits the row to that period. PyPSA reads no
  `constant` (`flow_based.py:262-288`)
- `FlowBased-balance`, the net positions of each named `domain` summing to
  zero per snapshot (`flow_based.py:289-293`)

The file reads the PTDF columns long, as `GlobalConstraint_zonal_ptdf` and
`GlobalConstraint_link_ptdf`, and the domains as the relation
`Bus_flow_based_domain`, from data prep. `FlowBased_injection` is the zone's
term in `Bus_injection`. On a run without flow-based rows, no bus is a zone and
the balance is the standard one.

The rung has three zone buses that trade only through their net positions,
and a corridor link from the north to the south zone. The north-south CNEC is
tight in every snapshot, and the centre-south one where it has a `ram`.
PyPSA solves to `17005.3191`. With the corridor link's factor at `0`, it
solves to `22596.8085`. With the centre-south `ram` at `30` in every
snapshot, it solves to `16872.3404`. Without the domain, the zones cannot
trade and PyPSA solves to `45000.0` (#977).

| PyPSA                                                                            | status  | note                                                                         |
| -------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------- |
| `FlowBased-net_position`                                                         | done    | where `Bus_flow_based_zone`, and in `Bus_injection` as `FlowBased_injection` |
| `GlobalConstraint-ram`                                                           | done    | per CNEC and snapshot, where `GlobalConstraint_ram` has a value              |
| `FlowBased-balance`                                                              | done    | per domain, through `Bus_flow_based_domain`                                  |
| `flow_based` with a sense other than `<=`, and the domain checks PyPSA raises on | refused | [Refusals](../../../docs/examples/pypsa/scope.md#refusals)                   |

The network: [`rung_79_flow_based.py`](rung_79_flow_based.py).

### Rung 80 — maintenance of fixed modular committable units

This rung runs `n.optimize()` with a fixed modular committable generator, link
and process, each of four modules and maintainable. In maintenance, PyPSA
bounds the modules on by `p_nom / p_nom_mod` for a fixed build and by
`p_nom_max / p_nom_mod` for an extendable one (`constraints.py:588-594`). Before
PyPSA/PyPSA#2100, a fixed build took `p_nom_max` too, which is infinite by
default, and `n.optimize()` returned `('ok', 'unknown')` without a solution
(PyPSA/PyPSA#2094).

The file states the bound as `Generator_maintenance_modules`, and the `Link`
and `Process` ones. They are `Generator_modules_installed` for a fixed build.

Each unit takes all four modules off for one snapshot, and a dear backup
covers the gap. PyPSA solves to `16026.25`. Without maintenance, it solves to
`13656.25`. At `061974e3`, PyPSA returns `('ok', 'unknown')`.

| PyPSA                                                                           | status | note                                                    |
| ------------------------------------------------------------------------------- | ------ | ------------------------------------------------------- |
| `Generator-maint-modstatus-*`, fixed modular, and the `Link` and `Process` ones | done   | bound by `Generator_maintenance_modules`, `p_nom` based |

The network: [`rung_80_fixed_modular_maintenance.py`](rung_80_fixed_modular_maintenance.py).

### Rung 81 — a piecewise marginal cost curve

This rung runs `n.optimize()` with a generator whose `marginal_cost` is a
curve. The curve is a dictionary from `p_pu` to the marginal cost of the
segment that ends there. PyPSA builds the column `Generator-marginal_cost_piecewise`, holds it
above the curve at `Generator-p`, and puts it in the objective in place of
`p` times `marginal_cost` (`optimize.py:308-348`). The curve runs over
`p_pu` times `p_nom`, and its cost sums each segment's width times its
marginal cost (`piecewise.py:298-305`). The model-building library linopy
chooses how to state the curve. Where every curve is convex and no generator
with a curve is committable, it states each segment's line (`_chord`) and the
curve's ends (`_domain_lo`, `_domain_hi`).

The file states the curve as `piecewise:` entries along the `breakpoint`
dimension, and you compute the breakpoints in data prep.
`Generator_marginal_cost_lp` states the segment lines where
`Generator_marginal_cost_as_lp`, linopy's choice for the whole call, is true.

The curve of `curve81` costs 12, then 20, then 45 per MWh. A south load walks
it from 24 MW in the first snapshot to the end of the second segment, 40 MW, in
the next two. In the last, gas is at its limit, so `curve81` runs at 74 MW,
34 MW into its dear third segment. Its output costs 13.33, 16, 16 and 29.32 per MWh on average,
where a linear `marginal_cost` is one number. PyPSA solves to `30890.0`.

| PyPSA                                                                 | status | note                                                                        |
| --------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------- |
| `Generator-marginal_cost_piecewise_chord`, `_domain_lo`, `_domain_hi` | split  | `Generator_marginal_cost_lp`, where `Generator_marginal_cost_as_lp` is true |

The network: [`rung_81_piecewise_marginal_cost.py`](rung_81_piecewise_marginal_cost.py).

### Rung 82 — a piecewise marginal cost curve on a committable generator

This rung adds a committable generator with a curve to the network of rung 81.
PyPSA then gates every curve of the call: by `Generator-status` for a
committable generator, and by 1 for any other (`optimize.py:314-318`,
`piecewise.py:193-203`). linopy states no segment lines under a gate. It
states each curve by increments instead: a share of each segment
(`_delta`), filled in order (`_order_binary`, `_delta_bound`, `_fill_order`,
`_binary_order`), at most the gate (`_active_bound`). Two rows tie the output
(`_link`) and the cost (`_output_link`) to the shares.

The file states the increments as `Generator_marginal_cost_incremental`, with
`activity: Generator_status`, where `Generator_marginal_cost_as_lp` is false.
A generator that is not committable has no status, so its curve is ungated,
which is a gate of 1. Where a curve's output or cost is not strictly
increasing, linopy states the curve by weights on its breakpoints instead, a
[special ordered set](../../../docs/reference/glossary.md#special-ordered-set-sos) of type
2 (SOS2). The file keeps the increments there, which reach the same
optimum. Under `linearized_unit_commitment`, the status is a share between 0
and 1, and a curve gate is binary or integer. So
[the patch](#the-relaxed-commitment) assumes that no generator with a curve is
committable.

The curve of `block82` is not convex: its first 20 MW cost 40 per MWh and the
rest 15. It stays off in the first two snapshots, where its status holds its
curve at zero. In the third snapshot it runs at 84 MW: it pays for its dear
first 20 MW to reach the cheap rest. `curve82` drops to 20 MW there. In the last
snapshot it runs at 100 MW. PyPSA solves to `26135.0`.

| PyPSA                                                                                                                               | status | note                                                                                                             |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| `Generator-marginal_cost_piecewise_delta`, `_order_binary`, `_delta_bound`, `_fill_order`, `_binary_order`, `_link`, `_output_link` | split  | `Generator_marginal_cost_incremental`, where `Generator_marginal_cost_as_lp` is false, and in place of SOS2 rows |
| `Generator-marginal_cost_piecewise_active_bound`                                                                                    | split  | where `Generator_status` exists, and no row at gate 1                                                            |

The network: [`rung_82_piecewise_marginal_cost_committable.py`](rung_82_piecewise_marginal_cost_committable.py).

## The relaxed commitment

Five rungs run under `n.optimize(linearized_unit_commitment=True)`, with the
patch `examples/variants/pypsa_linearized_uc.yaml` laid over the file
([the relaxed commitment](../../../docs/examples/pypsa_linearized_uc.md)).

### Rung 12 — linearised unit commitment

| PyPSA                                         | status | note                                                                                                                  |
| --------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------- |
| `Generator-status`, `-start_up`, `-shut_down` | done   | shares in [0, 1]                                                                                                      |
| `Generator-com-p-before`                      | done   | where start and stop cost the same in every snapshot and scenario, by a `count` over `snapshot`, then over `scenario` |
| `Generator-com-p-current`                     | done   |                                                                                                                       |
| `Generator-com-partly-start-up`               | done   |                                                                                                                       |
| `Generator-com-partly-shut-down`              | done   |                                                                                                                       |

The network: [`rung_12_linearized_uc.py`](rung_12_linearized_uc.py).

### Rung 44 — relaxed integer commitment rows

Under the keyword, PyPSA builds the commitment rows of the integer run and adds
the four tightening rows (`constraints.py:684-792`). The keyword relaxes only the
status, start and stop to shares in [0, 1] (`variables.py:91-92`). The patch
leaves each of these rows to [`examples/pypsa.yaml`](../../pypsa.yaml), and the rung's
network contains them under the keyword:

- A unit still serving the down time it brought in stays off, through its
  down-time row (`constraints.py:663-683`).
- PyPSA builds a ramp row where a unit has a ramp limit, or only a start-up or
  shut-down ramp (`constraints.py:1116-1125`). A missing limit is the full
  build.
- A maintainable unit is off for its events. The maintenance start stays a
  binary under the keyword (`variables.py:239-264`). The product of status and
  maintenance enters the commitment rows through the `maint-status` rows
  (`constraints.py:510-543`). A maintainable unit that is not committable loses
  the same share of its fixed rows (`constraints.py:153-163`).

The rung adds five cheap units under a load that swings. A start costs more
than a stop, so PyPSA builds no tightening rows for them, and each row is
tight at the optimum. PyPSA solves the rung and its variants to these objectives
(#977):

| network                                         | objective |
| ----------------------------------------------- | --------- |
| the rung as built                               | `7400.0`  |
| without the down time brought in                | `6540.0`  |
| without the start-up ramp                       | `7164.0`  |
| the missing start-up and shut-down ramps as `0` | `8060.0`  |
| the committable unit not maintainable           | `7310.0`  |
| the fixed unit not maintainable                 | `7100.0`  |

| PyPSA                                                                                            | status | note                                                                                  |
| ------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------- |
| `Generator-com-down-time` with the down time brought in                                          | done   |                                                                                       |
| `Generator-p-ramp_limit_up`, `-down` for a start-up or shut-down ramp alone, and a missing limit | done   | `Generator_ramp_up_rate` and the other three rates are `1` where the limit is missing |
| `Generator-maint-*`, `Generator-maint-status-*`                                                  | done   | fixed units                                                                           |
| `Generator-com-p-lower`, `-upper`, `Generator-fix-p-lower`, `-upper` in maintenance              | done   |                                                                                       |

The network: [`rung_44_linearized_commitment.py`](rung_44_linearized_commitment.py).

### Rung 47 — ramps and signs under the keyword

Under the keyword, the rung's network contains five kinds of row, each on fixed
builds. The patch states the first kind, the four tightening rows.
[`examples/pypsa.yaml`](../../pypsa.yaml) states the other four:

- In the four tightening rows, a missing ramp limit is the full build
  (`constraints.py:410-415`). The rows contain `Generator_ramp_up_rate` and the
  other three rates.
- A ramp limit has a value per snapshot, and the ramp row uses its value at the
  later of the two snapshots (`constraints.py:1110-1111`). A row is absent at a
  snapshot where neither the limit nor the start-up or shut-down ramp has a
  value (`constraints.py:1116-1117`, `1122`, `1140`).
- A unit that came in running with a `p_init` ramps from it into the first
  snapshot (`constraints.py:1149-1151`, `1105-1109`). Where `p_init` has no
  value, the unit has no ramp row at the first snapshot.
- A unit that is not committable has ramp rows with its status fixed at `1`
  (`constraints.py:1141-1147`), and comes in running whatever its
  `up_time_before` (`constraints.py:323`).
- Each generator's and load's part enters the bus balance with its component's
  `sign` (`constraints.py:1480-1481`, `:1592`).

The rung adds a relax bus with a tightened unit that has only start-up and
shut-down ramps. One committable unit has a ramp limit that lifts at the third snapshot, and
a dear committable unit came in running at `p_init=40`. A fixed unit with ramp limits, a unit of sign `-1`, a load of sign
`1` and a dear backup complete the bus. The row of each unit is tight at
the optimum, and PyPSA solves the rung and its variants to these objectives
(#977):

| network                                          | objective   |
| ------------------------------------------------ | ----------- |
| the rung as built                                | `12862.5`   |
| the missing limits as `0` in the two partly rows | `36126.875` |
| the ramp limit at `0.25` in every snapshot       | `14554.75`  |
| without the `p_init`                             | `8437.5`    |
| without the fixed unit's ramp limits             | `12800.0`   |
| the unit's sign at `1`                           | `12592.5`   |
| the load's sign at `-1`                          | `13887.5`   |

| PyPSA                                                                                                   | status | note                                                                          |
| ------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------- |
| `Generator-com-p-before`, `-current`, `-partly-start-up`, `-partly-shut-down` with a missing ramp limit | done   | the four rates are `1` where the limit is missing                             |
| `Generator-p-ramp_limit_up`, `-down` per snapshot                                                       | done   | `Generator_ramp_limit_up` and `-down` over `[scenario, snapshot, generator]`  |
| `Generator-p-ramp_limit_up`, `-down` at the first snapshot from `p_init`                                | done   | `Generator_previous_p` opens at `Generator_status_initial * Generator_p_init` |
| `Generator-p-ramp_limit_up`, `-down` for a unit that is not committable                                 | done   | `Generator_ramp_up_allowance` and `-down` have the status fixed at `1`        |
| `Bus-nodal_balance` with `sign`                                                                         | done   | `Generator_sign` and `Load_sign`                                              |

The network: [`rung_47_linearized_ramps.py`](rung_47_linearized_ramps.py).

### Rung 67 — relaxed link and process commitment

The keyword relaxes Link and Process as it relaxes Generator
(`optimize.py:876-880`), and PyPSA builds the four tightening rows for each
(`constraints.py:684-792`). The rung adds an east bus that three committable
units serve from the north. They are a link and a process, each with a fixed
build and the same start and stop cost, and an extendable link. PyPSA does not
tighten the extendable link, because the tightening rows contain the build as
data (`constraints.py:702-704`). A dear backup on the east bus balances the
bus.

Each tightening row is tight at the optimum, and PyPSA solves to `47777.33`.
When the stop of the link costs `1e-7` more than its start, PyPSA does not
tighten the link, and it solves to `46554.0`. When the process is left
untightened in the same way, PyPSA solves to `47465.70`. Without the keyword,
it solves to `54013.13`.

| PyPSA                                                                       | status | note                                  |
| --------------------------------------------------------------------------- | ------ | ------------------------------------- |
| `Link-status`, `-start_up`, `-shut_down`                                    | done   | shares in [0, 1]                      |
| `Process-status`, `-start_up`, `-shut_down`                                 | done   | shares in [0, 1]                      |
| `Link-com-p-before`, `-current`, `-partly-start-up`, `-partly-shut-down`    | done   | a fixed build only                    |
| `Process-com-p-before`, `-current`, `-partly-start-up`, `-partly-shut-down` | done   | a fixed build only                    |
| `Link-com-ext-p-*` under the keyword                                        | done   | no tightening for an extendable build |

The network: [`rung_67_linearized_link_process.py`](rung_67_linearized_link_process.py).

### Rung 74 — a relaxed unit that opens in a later period

Under the keyword and `multi_investment_periods`, a committable unit built in
the later period has no output or status before its first snapshot. PyPSA
fills both with zero there (`constraints.py:716`), so the four tightening rows
open on a unit that was off. The patch reads `Generator_previous_p`, which is
zero at the first snapshot a unit is active in past the first of the horizon.

The rung's unit has equal start and stop costs, so PyPSA tightens it. It opens
in 2030 and its start-up ramp of `30` is tight at the period's first snapshot.
PyPSA solves to `24825.2778`. With the unit built in 2020, PyPSA solves to
`3462.5`. With a start that costs more than a stop, PyPSA does not tighten
the unit, and it solves to `23226.3333` (#977).

| PyPSA                                                                                                                 | status | note                                                                  |
| --------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------- |
| `Generator-com-p-before`, `-partly-start-up`, `-partly-shut-down` at a unit's first snapshot past the horizon's first | done   | `Generator_previous_p` and `Generator_previous_status` are zero there |

The network: [`rung_74_linearized_late_opening.py`](rung_74_linearized_late_opening.py).
