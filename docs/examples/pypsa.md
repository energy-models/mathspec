<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA in one file

The model a plain `n.optimize()` builds, stated as one file and grown a rung
at a time. The file also carries the two classes PyPSA switches on with a
keyword: the two-stage stochastic class over a `scenario` axis (rung 14), and
the multi-period investment class over a `period` axis (rung 15). A plain run
feeds one scenario and one all-active period, so every extra axis collapses and
the standard model returns. The index below lists every row PyPSA emits (PyPSA
`1.3.0`, `pypsa/optimization/`) and links each to its block in the file.

Three rules shape the file. Bounds are the explicit rows PyPSA writes, so
their duals are row duals. Regimes are data columns and `where:` masks. Names
are PyPSA's, `Component_attribute`, with a symbol table
(`examples/symbols/pypsa.yaml`) making the math read as math.

## Index

A row is **done** once the file states it as the one block PyPSA builds.
**split** means the same feasible region and optimum under a different
statement, such as several `where:` blocks. **open** means not stated yet.
**out** means never stated, deliberately: emitted only under the keyword,
scope or version the note names. **diverges** means the file states the
intended math where PyPSA `1.3.0` has a bug; the note names the issue, and the
rung records the intended objective and what PyPSA gives until the fix ships. A name carrying `{k}`, `{s}`, `{c}` or `{n}` stands
for the family PyPSA numbers per segment, scenario, outaged component or
sub-network.

Each rung's banner states what PyPSA solved its reference network to. A
rung that records a PyPSA bug, marked ✘, states what PyPSA gives beside the
intended objective.

<!-- gallery: examples/references/pypsa/spine.py -->

### Rung 1 — transport

| PyPSA                                                                               | status | note                                                                                                                                                                                                                                                                                          |
| ----------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`Generator-p`, `Link-p`](#variable-domains)                                        | done   |                                                                                                                                                                                                                                                                                               |
| [`Generator-fix-p-lower`](#generator-fix-p-lower)                                   | done   |                                                                                                                                                                                                                                                                                               |
| [`Generator-fix-p-upper`](#generator-fix-p-upper)                                   | done   |                                                                                                                                                                                                                                                                                               |
| [`Link-fix-p-lower`](#link-fix-p-lower)                                             | done   |                                                                                                                                                                                                                                                                                               |
| [`Link-fix-p-upper`](#link-fix-p-upper)                                             | done   |                                                                                                                                                                                                                                                                                               |
| [`Bus-nodal_balance`](#bus-nodal_balance)                                           | done   | a loaded bus with nothing attached: PyPSA refuses, see X2                                                                                                                                                                                                                                     |
| [`Bus-nodal_balance`](#bus-nodal_balance) with a component `sign`                   | done   | rung 43                                                                                                                                                                                                                                                                                       |
| [`Bus-nodal_balance`](#bus-nodal_balance) with a load that is not `active`          | done   | rung 50; `Load_demand` is zero where `Load_active` is false                                                                                                                                                                                                                                   |
| [`Bus-nodal_balance`](#bus-nodal_balance) with an efficiency or a rate per snapshot | done   | rung 60                                                                                                                                                                                                                                                                                       |
| `Bus-meshed-*-nodal_balance`                                                        | out    | the same balance rows, dealt into linopy containers by how many component columns name a bus — `meshed_thresholds`, an `n.optimize()` keyword defaulting to `[30, 100, 400]`. Same rows, same duals, another name; a modeler whose engine wants the split states it, the file does not (#123) |
| [`marginal_cost`](#objective)                                                       | done   |                                                                                                                                                                                                                                                                                               |
| [`marginal_cost_quadratic`](#objective)                                             | done   | rungs 10 and 36, below; Generator and Link `p`, Process `p`, StorageUnit `p_dispatch` only, and Store net `p`                                                                                                                                                                                 |
| `objective_constant`                                                                | split  | an objective shift, compared net of `n._objective_constant` — rungs 11 and 13 carry a nonzero one, `21915277.52` and `160.0`, so the netting is under test                                                                                                                                    |

<!-- gallery: examples/references/pypsa/rung_01_transport.py -->

### Rung 2 — storage

| PyPSA                                                                                               | status | note                                                                                                                                                                    |
| --------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`StorageUnit-p_dispatch`, `-p_store`, `-state_of_charge`, `Store-e`, `Store-p`](#variable-domains) | done   |                                                                                                                                                                         |
| [`StorageUnit-spill`](#variable-domains)                                                            | done   | `where: inflow > 0`, `absence: zero`; bounds on the variable, as PyPSA's                                                                                                |
| [`StorageUnit-fix-*`](#storageunit-fix-p_dispatch-lower), [`Store-fix-e-*`](#store-fix-e-lower)     | done   |                                                                                                                                                                         |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance)                                         | done   | the charge carried into a snapshot is a cased quantity — cyclic, opening, carried; `(1-loss)**eh` is prep                                                               |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance) with efficiencies per snapshot          | done   | rung 60                                                                                                                                                                 |
| [`Store-energy_balance`](#store-energy_balance)                                                     | done   | same                                                                                                                                                                    |
| [`StorageUnit-p_set`](#storageunit-p_set), [`{c}-{attr}_set`](#generator-p_set)                     | done   | `Generator-p_set`, `Link-p_set`, `StorageUnit-state_of_charge_set`, `Store-e_set`, `Line-s_set`; `Store-p_set`, `StorageUnit-p_dispatch_set`, `-p_store_set` in rung 37 |
| [`marginal_cost_storage`, `spill_cost`](#objective)                                                 | done   |                                                                                                                                                                         |

<!-- gallery: examples/references/pypsa/rung_02_storage.py -->

### Rung 3 — expansion

| PyPSA                                                     | status | note                                                        |
| --------------------------------------------------------- | ------ | ----------------------------------------------------------- |
| [`{c}-p_nom`, `-s_nom`, `-e_nom`](#variable-domains)      | done   | `{c}_p_nom_ext` here — the fixed regime keeps the parameter |
| [`{c}-ext-{attr}-lower/upper`](#generator-ext-p-lower)    | done   |                                                             |
| [`{c}-ext-p_nom-lower/upper`](#generator-ext-p_nom-lower) | done   |                                                             |
| [`{c}-p_nom_set`](#generator-p_nom_set)                   | done   |                                                             |
| [`Generator-e_sum_min/max`](#generator-e_sum_min)         | done   |                                                             |
| [capital cost](#objective)                                | done   | `periodized_cost` is an annuity, data prep                  |

<!-- gallery: examples/references/pypsa/rung_03_expansion.py -->

### Rung 4 — ramps

| PyPSA                                                                                            | status | note                                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------ | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-p-ramp_limit_up/down`](#generator-p-ramp_limit_up)                                         | done   | the build, the allowance and the output carried in are cased quantities, so fixed, extendable and committed are one block; big-M is rung 8's. A missing limit reads as the full build, and a start-up or shut-down ramp alone builds the row, rung 28 |
| [`{c}-p-ramp_limit_up/down`](#generator-p-ramp_limit_up) with a limit per snapshot               | done   | rung 45                                                                                                                                                                                                                                               |
| [`{c}-p-ramp_limit_*`](#generator-p-ramp_limit_up), `-bigM`, at the first snapshot from `p_init` | done   | rung 46                                                                                                                                                                                                                                               |

<!-- gallery: examples/references/pypsa/rung_04_ramps.py -->

### Rung 5 — global constraints

`GlobalConstraint-{name}` for all; the type and the comparator are data, so
each type is three blocks by sense.

| PyPSA type                                                                    | status | note                                                                                                                      |
| ----------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy)                                           | split  | a block per sense — sense as data is beyond #70; carrier weights are prep; one period in rung 35; per scenario in rung 40 |
| [`primary_energy`](#primary_energy) with a generator efficiency per snapshot  | done   | rung 60                                                                                                                   |
| [`operational_limit`](#operational_limit)                                     | split  | a block per sense; one period in rung 35; per scenario in rung 40                                                         |
| [`transmission_volume_expansion_limit`](#transmission_volume_expansion_limit) | split  | a block per sense; membership from PyPSA's carrier string is prep; per scenario in rung 40                                |
| [`transmission_expansion_cost_limit`](#transmission_expansion_cost_limit)     | split  | a block per sense                                                                                                         |
| [`tech_capacity_expansion_limit`](#tech_capacity_expansion_limit)             | split  | a block per sense                                                                                                         |
| `Bus-nom_min/max_{carrier}`                                                   | out    | deprecated in PyPSA                                                                                                       |
| [`Carrier-growth_limit`](#carrier-growth_limit)                               | done   | generators in rung 15, every extendable component in rung 21, below                                                       |

<!-- gallery: examples/references/pypsa/rung_05_global_constraints.py -->

### Rung 6 — KVL

| PyPSA                                                                                   | status | note                                                |
| --------------------------------------------------------------------------------------- | ------ | --------------------------------------------------- |
| [`Line-s`](#variable-domains), [`Line-fix-s-*`](#line-fix-s-lower)                      | done   | the ext and nominal rows sit under rung 3's pattern |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law)                                       | done   | the cycle basis is data prep                        |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law) with a fixed phase shift per snapshot | done   | rung 60                                             |

<!-- gallery: examples/references/pypsa/rung_06_kvl.py -->

### Rung 7 — commitment

| PyPSA                                                                                           | status | note                                                                                                                 |
| ----------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| [`{c}-status`, `-start_up`, `-shut_down`](#variable-domains)                                    | done   | Generator; Link in rung 25, Process in rung 26                                                                       |
| [`{c}-com-p-lower/upper`](#generator-com-p-lower)                                               | done   |                                                                                                                      |
| [`{c}-*-p-fixed-upper`](#generator-status-p-fixed-upper)                                        | done   | status, start and stop each at most one, as explicit rows                                                            |
| [`{c}-com-transition-start-up/shut-down`](#generator-com-transition-start-up)                   | done   | the state carried into a snapshot is a cased quantity, so the first snapshot needs no block of its own               |
| [`{c}-com-up-time`, `-down-time`](#generator-com-up-time)                                       | done   | `sum_back(window=min_up_time)`                                                                                       |
| [`{c}-com-status-min_up_time_must_stay_up`](#generator-com-status-min_up_time_must_stay_up)     | done   | the window is a prep mask — `position()` takes a literal                                                             |
| [`{c}-com-status-min_down_time_must_stay_up`](#generator-com-status-min_down_time_must_stay_up) | done   | the same prep mask over the down time brought in, status zero; PyPSA's name says `_must_stay_up`; rung 24 records it |
| [`stand_by_cost`, `start_up_cost`, `shut_down_cost`](#objective)                                | done   | a start and a stop carry no snapshot or period weight, rung 48                                                       |
| [`{c}-com-p-before/-current/-partly-*`](pypsa_linearized_uc.md)                                 | done   | rungs 12, 44 and 47, a file of its own: Generator commitment on fixed builds                                         |

<!-- gallery: examples/references/pypsa/rung_07_commitment.py -->

### Rung 8 — modular and big-M

| PyPSA                                                                  | status | note                                                                                                                                                                                        |
| ---------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-n_mod`, `{c}-p_nom_modularity`](#generator-p_nom_modularity)     | done   |                                                                                                                                                                                             |
| [`{c}-*-p_nom-variable-upper`](#generator-status-p_nom-variable-upper) | done   | a modular unit is on only where a module is built                                                                                                                                           |
| [`{c}-*-p-fixed-upper`, modular](#generator-status-p-fixed-upper)      | done   | the cap is the build's whole count of modules, `p_nom / p_nom_mod` in data prep, see X1; rung 8's `array` fixes one (#123)                                                                  |
| [`{c}-com-mod-p-lower/upper`](#generator-com-mod-p-lower)              | done   | one module's share, times the status — a fixed build too, beside its ordinary `com-p-*` rows                                                                                                |
| [`{c}-com-ext-p-*` (big-M)](#generator-com-ext-p-upper-cap)            | done   | a cap row beside a big-M row; `M` is the build cap at full availability, data prep                                                                                                          |
| [`{c}-com-ext-p-lower-nonneg`](#generator-com-ext-p-lower-nonneg)      | done   | `(p_min_pu >= 0).all()` is prep                                                                                                                                                             |
| [`{c}-p-ramp_limit_*-bigM`](#generator-p-ramp_limit_up-run-bigm)       | done   | run and start rows up, run and shut rows down; the output carried in is a cased quantity, so each is one block. A modular build takes the ordinary rows against one module instead, rung 27 |

<!-- gallery: examples/references/pypsa/rung_08_modular_big_m.py -->

### Rung 9 — multi-link

| PyPSA                                           | status | note                                                                                                     |
| ----------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| [nodal balance, ports 1..n](#bus-nodal_balance) | done   | one term over `link_output`, so a link of any number of output ports needs no further declaration (#124) |

<!-- gallery: examples/references/pypsa/rung_09_multilink.py -->

### Rung 10 — quadratic costs

A marginal cost quadratic in output: PyPSA's `marginal_cost_quadratic`, one
squared term per component in the objective, each snapshot weighted by the hours
it stands for. Generator and Link carry it here; rung 36 puts it on a process,
a storage unit and a store. A plain run feeds zero, so the term vanishes and
the objective stays linear.

| PyPSA                                   | status | note                                               |
| --------------------------------------- | ------ | -------------------------------------------------- |
| [`marginal_cost_quadratic`](#objective) | done   | degree 2 in the objective; Generator and Link here |

<!-- gallery: examples/references/pypsa/rung_10_quadratic_costs.py -->

### Rung 11 — ac-dc-meshed

PyPSA's `ac_dc_meshed` example, whole: meshed AC and DC, extendable lines,
links and generators, carriers, a CO2 budget. Every statement above,
composed; the first rung with an objective constant.

<!-- gallery: examples/references/pypsa/rung_11_ac_dc_meshed.py -->

### Rung 13 — transmission losses

`n.optimize(transmission_losses=...)`: a line dissipates a loss its flow buys,
held above a fan of cuts to the quadratic loss curve `r_pu_eff * p**2`, half
charged at either end of the line. PyPSA has two modes, and both build the same
rows `loss + slope * flow >= offset` and `loss - slope * flow >= offset`, one
pair per cut: `{'mode': 'tangents', 'segments': K}` takes `K` tangents at
`p_k = k / K` of the rating, slope `2 r p_k`; `True`, or
`{'mode': 'secants', 'atol': 1, 'rtol': 0.1, 'max_segments': 20}`, takes the
secants between consecutive breakpoints `p_k, p_k+1`, slope `r (p_k + p_k+1)`
and offset `-r p_k p_k+1`, the breakpoints placed from `p_0 = 0` by a step
`max(k / (k - 1), 1 + 2 (rtol + sqrt(rtol + rtol**2)))` until the rating is
covered (`constraints.py:2545`). The mode therefore only decides how data prep
fills `Line_loss_slope` and `Line_loss_offset` over the `segment` axis, and the
breakpoint loop is data prep with them. The loss variable, its cap and the cut
rows exist only where `transmission_losses` is on. A plain run leaves the flag
off and supplies no segments, so the loss is absent and reads as zero in the
balance, and the model collapses to the lossless one.

| PyPSA                                                                                                                                                                         | status | note                                                                                                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------- |
| [`Line-loss`, `Transformer-loss`](#variable-domains)                                                                                                                          | done   | absent, and zero in the balance, where lossless                                                                        |
| [`Line-fix-s-*`, `Line-ext-s-*`](#line-fix-s-lower), [`Transformer-fix-s-*`, `Transformer-ext-s-*`](#transformer-fix-s-lower)                                                 | done   | the loss counted against the rating                                                                                    |
| [`Bus-nodal_balance`](#bus-nodal_balance)                                                                                                                                     | done   | half of each incident line's and transformer's loss at either end                                                      |
| [`Line-loss_upper`](#line-loss_upper), [`Transformer-loss_upper`](#transformer-loss_upper)                                                                                    | done   | `loss_max` is data prep, see X4                                                                                        |
| [`Line-loss_tangents-{k}-1`](#line-loss_tangents-k-1), [`Transformer-loss_tangents-{k}-1`](#transformer-loss_tangents-k-1)                                                    | split  | PyPSA names a row per segment; one block over the dimension                                                            |
| [`Line-loss_tangents-{k}--1`](#line-loss_tangents-k--1), [`Transformer-loss_tangents-{k}--1`](#transformer-loss_tangents-k--1)                                                | split  |                                                                                                                        |
| [`Line-loss_secants-pos`, `Line-loss_secants-neg`](#line-loss_tangents-k-1), [`Transformer-loss_secants-pos`, `Transformer-loss_secants-neg`](#transformer-loss_tangents-k-1) | done   | the same two blocks in the secant mode; slope, offset and the breakpoint loop are data prep; rungs 19 and 23 record it |

<!-- gallery: examples/references/pypsa/rung_13_losses.py -->

The same triangle solved in the secant mode records the identical loss rows,
its cuts placed by PyPSA's tolerance loop rather than fixed per segment.

<!-- gallery: examples/references/pypsa/rung_19_losses_secants.py -->

### Rung 14 — two-stage stochastic

Two futures and a risk preference: `n.set_scenarios(...)` with
`n.set_risk_preference(alpha, omega)`. Everything over a snapshot spans a
scenario as well. Capacity does not, because it is chosen once before the
future is known. The operating cost is the expectation over the scenarios'
weights. A risk preference adds the CVaR (conditional value at risk) rows: an
excess per scenario and the tail's average, blended into the objective at
`omega`. PyPSA builds neither row without a risk preference
(`optimize.py:458`). The file builds them only where `omega` is positive, so a
plain run, and a risk preference with `omega = 0`, has none.

A parameter spans `scenario` exactly when PyPSA reads it per scenario. PyPSA
reads component data through `c.da`, one value per scenario
(`components/array.py:332-395`), so almost every parameter spans one. It
refuses a difference in the attributes that fix the network's shape, such as
`bus`, `carrier`, `lifetime`, `active`, `committable` or `p_nom_extendable`
(`consistency.py:1174-1195`), and these parameters and what data prep derives
from them span none. Some other parameters span none either. PyPSA reduces
`maintainable` to a union over the scenarios, `(p_min_pu >= 0).all()` over
them, and a carrier's growth limits to their least value
(`components.py:1016-1019`, `constraints.py:397-401`,
`global_constraints.py:226-230`). It builds the cycle basis from the first
scenario (`networks.py:1354-1361`). A link's delay and a transformer's phase
shift span none, because PyPSA `1.3.0` mishandles them over scenarios (rung
41). A branch's `BODF` spans none, because PyPSA refuses a
security-constrained run over scenarios. This rung's wind `p_max_pu` differs by scenario, and the file states it over
`scenario`. Rungs 41 and 42 make operating data and first-stage data differ.

| PyPSA                                                                                          | status | note                                                                                                                                 |
| ---------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| [`Generator-p`, `Link-p`](#variable-domains)                                                   | done   | over `scenario`; `Generator-p_nom` is not — chosen once                                                                              |
| [`Generator-fix-p-*`, `-ext-p-*`, `Link-fix-p-*`, `Bus-nodal_balance`](#generator-fix-p-lower) | done   | rungs 1 and 3, over `scenario`                                                                                                       |
| [`CVaR-a`, `CVaR-theta`, `CVaR`](#variable-domains)                                            | done   |                                                                                                                                      |
| [`CVaR-excess-{s}`](#cvar-excess-s)                                                            | split  | PyPSA names a row per scenario; one block over the dimension; none where `omega` is zero                                             |
| [`CVaR-def`](#cvar-def)                                                                        | done   | `1 / (1 - alpha)` is data prep; none where `omega` is zero                                                                           |
| [objective](#objective)                                                                        | done   | capacity once, at its capital cost in expectation over the scenarios; operation `(1 - omega)` in expectation, `omega` at the tail    |
| `Generator-p_max_pu` and other component data per scenario                                     | done   | every parameter PyPSA reads per scenario spans `scenario`; operating data in rung 41, first-stage bounds and capital cost in rung 42 |

<!-- gallery: examples/references/pypsa/rung_14_stochastic.py -->

### Rung 15 — investment periods

`n.optimize(multi_investment_periods=True)`. A snapshot belongs to an
investment period. An asset stands in the periods its build year and lifetime
span. Capacity is paid once per period the asset stands in, and each period
carries a weight. A carrier may grow only so much per period. Which snapshots
an asset is active in is data prep, because a `where` reaches only the frame's
own dimensions.

| PyPSA                                                                                                                                                             | status | note                                                                                                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------- |
| [`Generator-p`](#variable-domains)                                                                                                                                | done   | where the generator stands in the snapshot's period — `active`, data prep                                              |
| [`Generator-fix-p-*`, `-ext-p-*`, `-ext-p_nom-*`](#generator-fix-p-lower)                                                                                         | done   | rungs 1 and 3, masked by `active`                                                                                      |
| [`Carrier-growth_limit`](#carrier-growth_limit)                                                                                                                   | done   | every extendable component of the carrier, counted in the first period a build stands in; `edge=0` at the first period |
| [`Carrier-growth_limit`](#carrier-growth_limit) with a negative `max_relative_growth`                                                                             | done   | rung 39                                                                                                                |
| [`Carrier-growth_limit`](#carrier-growth_limit) without `multi_investment_periods`                                                                                | done   | rung 49; not built, so data prep feeds no `max_growth`                                                                 |
| [objective](#objective)                                                                                                                                           | done   | period weight on operation; capacity once per period it stands in                                                      |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance), [`Store-energy_balance`](#store-energy_balance) per period, ramps at period starts                   | done   | rung 29                                                                                                                |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance), [`Store-energy_balance`](#store-energy_balance) for storage built in a later period or retired early | done   | rung 32                                                                                                                |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit) for one investment period, weighted by period years                                | done   | rung 35                                                                                                                |
| [link and process `delay`, `cyclic_delay`](#bus-nodal_balance) per investment period                                                                              | done   | rung 38                                                                                                                |

<!-- gallery: examples/references/pypsa/rung_15_multi_period.py -->

### Rung 16 — link delay

A source feeding two sinks over links whose energy arrives late. PyPSA's
`delay` lags a port's delivery by a number of snapshots, and `cyclic_delay`
says whether the flow still in transit at the horizon's edge wraps to the start
or is lost. The two are a per-link number and a per-link kind, so the balance
turns them on with a `cases:` block over `shift(…, offset=Link_output_delay,
edge=…)` — one arm wrapping (`edge='wrap'`), the other vacating (`edge=0`).

This is the one rung whose `generators` weighting is uniform. PyPSA measures
`delay` in those units, so a uniform column makes a delay of `n` a shift of
exactly `n` snapshot positions, which a positional `shift` reproduces. Under a
non-uniform column PyPSA resamples by elapsed time rather than by position — a
shift that varies along the snapshot axis, above what `shift` states (#299).

| PyPSA                                              | status | note                                                                                                       |
| -------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------- |
| [link `delay`, `cyclic_delay`](#bus-nodal_balance) | done   | a `cases:` on `cyclic_delay` over `shift(offset=delay)`, at uniform `generators` weighting; supersedes #75 |

<!-- gallery: examples/references/pypsa/rung_16_link_delay.py -->

### Rung 17 — process

A process is a generalized converter. It moves an internal power from `bus0` to
the buses it feeds, and each port draws or delivers at its own `rate`. A
non-extendable process carries a fixed capacity. An extendable one chooses its
capacity between `p_nom_min` and `p_nom_max`. A ramp limit caps the change in
internal power between snapshots. A `p_set` fixes an internal power schedule. A
`p_nom_set` fixes an extendable process's built capacity. The machinery is the
generator's and the link's, read over a converter.

| PyPSA                                                                 | status | note                                                         |
| --------------------------------------------------------------------- | ------ | ------------------------------------------------------------ |
| [`Process-p`, `Process-p_nom`](#variable-domains)                     | done   | internal power and capacity, as a link                       |
| [`Process-fix-p-*`, `-ext-p-*`, `-ext-p_nom-*`](#process-fix-p-lower) | done   | rungs 1 and 3, over a converter                              |
| [`Process-p-ramp_limit_*`](#process-p-ramp_limit_up)                  | done   | rung 4, on a non-committable converter; committed in rung 26 |
| [`Process-p_set`](#process-p_set)                                     | done   | a fixed internal power schedule                              |
| [`Process-p_nom_set`](#process-p_nom_set)                             | done   | a fixed built capacity                                       |
| [`Bus-nodal_balance`](#bus-nodal_balance)                             | done   | each port enters at its `rate`                               |
| [objective](#objective)                                               | done   | marginal cost on internal power; capital on capacity         |

<!-- gallery: examples/references/pypsa/rung_17_process.py -->

### Rung 18 — transformer

A transformer is a passive branch between two buses, as a line is, but its flow
follows its effective series reactance and a phase shift, fixed or optimised. It
obeys the Kirchhoff voltage law (KVL) around every independent cycle, so it
builds no flow outside a mesh. A non-extendable transformer carries a fixed
nominal apparent power. An extendable one chooses it between `s_nom_min` and
`s_nom_max`. An `s_set` fixes a flow schedule. An `s_nom_set` fixes an extendable
transformer's built capacity.

| PyPSA                                                                         | status | note                                      |
| ----------------------------------------------------------------------------- | ------ | ----------------------------------------- |
| [`Transformer-s`, `Transformer-s_nom`](#variable-domains)                     | done   | flow and capacity, as a line              |
| [`Transformer-fix-s-*`, `-ext-s-*`, `-ext-s_nom-*`](#transformer-fix-s-lower) | done   | rungs 1 and 3, over a transformer         |
| [`Transformer-s_set`](#transformer-s_set)                                     | done   | a fixed flow schedule                     |
| [`Transformer-s_nom_set`](#transformer-s_nom_set)                             | done   | a fixed built capacity                    |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law)                             | done   | rung 6, over `x_pu_eff` and a phase shift |
| [`Transformer-phase_shift`](#variable-domains)                                | done   | rung 20, an optimised phase shift         |
| [objective](#objective)                                                       | done   | capital on capacity                       |

<!-- gallery: examples/references/pypsa/rung_18_transformer.py -->

### Rung 20 — phase shifter

A phase-shifting transformer's voltage angle shift is a per-snapshot decision
where its `phase_shift_min` sits below its `phase_shift_max`, bounded between the
two in degrees. The shift enters the same KVL cycle sum as a fixed one, so it
redistributes the flows around a cycle without moving active power. Here the
shift holds the transformer at its rating while the upstream unit serves the
whole varying load, and the fixed `phase_shift` gives way to it.

<!-- gallery: examples/references/pypsa/rung_20_phase_shifter.py -->

### Rung 21 — carrier growth

A carrier's `max_growth` caps what it adds in an investment period, across every
extendable component of that carrier, not the generators alone. Here a battery
carrier caps a storage unit and a store built in the first period, and the two
builds fill the cap together. A store built in the later period adds its
allowance plus half of what the carrier added before. PyPSA counts the
components that carry a carrier attribute, and so does the spec, so a
transformer counts in no carrier.

<!-- gallery: examples/references/pypsa/rung_21_carrier_growth.py -->

### Rung 22 — transformer losses

PyPSA applies the loss of rung 13 to every passive branch, so a transformer
dissipates a loss as a line does: its own loss variable, the loss counted
against its rating, its cap and its fan of cuts, and half of it at either end
in the balance. The loss curve is `r_pu_eff * p**2`, where a transformer's
`r_pu_eff` is its resistance over its given `s_nom`, times its tap ratio
(`power_flow.py:815`). The given `s_nom` sets it also for an extendable
transformer, whose build does not move the curve. Here the loss of the
extendable transformer is counted against its rating, so it builds more than
the flow it carries.

<!-- gallery: examples/references/pypsa/rung_22_transformer_losses.py -->

The same triangle solved in the secant mode records the identical loss rows,
its cuts placed by PyPSA's tolerance loop.

<!-- gallery: examples/references/pypsa/rung_23_transformer_losses_secants.py -->

### Rung 24 — must stay down

A committable unit that stopped `down_time_before` snapshots before the horizon
stays off until its `min_down_time` has passed. PyPSA fixes its status to zero
in the first `min_down_time - down_time_before` snapshots. Here the cheapest
unit in the network brought one snapshot of a three-snapshot down time into
the horizon, so it stays off for two snapshots and the dearer coal unit serves
the load.

<!-- gallery: examples/references/pypsa/rung_24_must_stay_down.py -->

### Rung 25 — committable links

A committable link carries the generator's whole unit commitment over its flow.
PyPSA builds the same status, transition, up time, down time, must-stay,
big-M, modular and ramp rows for a `Link` as for a `Generator`, and prices its
starts, stops and stand-by snapshots the same way. Here an east bus is served
only by committable links. `hvdc` brought one snapshot of a three-snapshot up
time into the horizon, so it stays on for two snapshots although a cheaper link
could carry the load. `cold_tie` brought one snapshot of a three-snapshot down
time, so it stays off for two snapshots. Its own two-snapshot up time would
then hold it on into the last snapshot, where the load is below its minimum, so
it does not start at all. The other links are committable builds that are
extendable, modular, or both.

| PyPSA                                                                                                                  | status | note                                                                                      |
| ---------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------- |
| [`Link-status`, `-start_up`, `-shut_down`, `-n_mod`](#variable-domains)                                                | done   | as the generator's, rung 7 and 8                                                          |
| [`Link-com-p-*`, `-com-mod-p-*`, `-com-ext-p-*`](#link-com-p-lower)                                                    | done   | a committable link leaves the `Link-fix-p-*` and `Link-ext-p-*` rows, as a generator does |
| [`Link-*-p-fixed-upper`, `-*-p_nom-variable-upper`](#link-status-p-fixed-upper)                                        | done   |                                                                                           |
| [`Link-com-transition-*`, `-com-up-time`, `-com-down-time`](#link-com-transition-start-up)                             | done   |                                                                                           |
| [`Link-com-status-min_up_time_must_stay_up`, `-min_down_time_must_stay_up`](#link-com-status-min_up_time_must_stay_up) | done   | prep masks, as the generator's                                                            |
| [`Link-p-ramp_limit_*`, `-*-bigM`](#link-p-ramp_limit_up)                                                              | done   | the generator's cased allowance and big-M rows over flow                                  |
| [`Link-p_nom_modularity`](#link-p_nom_modularity)                                                                      | done   |                                                                                           |
| [`stand_by_cost`, `start_up_cost`, `shut_down_cost`](#objective)                                                       | done   |                                                                                           |

<!-- gallery: examples/references/pypsa/rung_25_committable_link.py -->

### Rung 26 — committable processes

A committable process carries the same unit commitment over its internal power
`p`. The status gates `p`, not a port, so every port follows the status at its
own `rate`. This rung restates rung 25's links as processes that draw a quarter
more from the north than they deliver to the east. The same must-stay and up
time rules bind.

| PyPSA                                                                                                                        | status | note                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------- |
| [`Process-status`, `-start_up`, `-shut_down`, `-n_mod`](#variable-domains)                                                   | done   | as the link's, rung 25                                                        |
| [`Process-com-p-*`, `-com-mod-p-*`, `-com-ext-p-*`](#process-com-p-lower)                                                    | done   | a committable process leaves the `Process-fix-p-*` and `Process-ext-p-*` rows |
| [`Process-*-p-fixed-upper`, `-*-p_nom-variable-upper`](#process-status-p-fixed-upper)                                        | done   |                                                                               |
| [`Process-com-transition-*`, `-com-up-time`, `-com-down-time`](#process-com-transition-start-up)                             | done   |                                                                               |
| [`Process-com-status-min_up_time_must_stay_up`, `-min_down_time_must_stay_up`](#process-com-status-min_up_time_must_stay_up) | done   | prep masks, as the generator's                                                |
| [`Process-p-ramp_limit_*`, `-*-bigM`](#process-p-ramp_limit_up)                                                              | done   | the generator's cased allowance and big-M rows over internal power            |
| [`Process-p_nom_modularity`](#process-p_nom_modularity)                                                                      | done   |                                                                               |
| [`stand_by_cost`, `start_up_cost`, `shut_down_cost`](#objective)                                                             | done   |                                                                               |

<!-- gallery: examples/references/pypsa/rung_26_committable_process.py -->

### Rung 27 — modular ramps

A committable, extendable and modular unit gets no big-M ramp rows. PyPSA gives
it the ordinary `{c}-p-ramp_limit_*` rows of a committed unit, with one module
`p_nom_mod` in place of `p_nom`. The status counts the modules that are on, so
the allowance grows with each module. This rung has one such generator, link
and process on a peak bus, each with a ramp limit of one half and a start-up
and shut-down ramp of 0.6. The ramp rows bind at the rise and at the fall of
the load.

| PyPSA                                                                     | status | note                                                                                                                     |
| ------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| [`{c}-p-ramp_limit_up/down`, modular](#generator-p-ramp_limit_up)         | done   | the committed allowance reads `p_nom_committed`: one module where the build is extendable and modular, `p_nom` otherwise |
| [`{c}-p-ramp_limit_*-bigM`, modular](#generator-p-ramp_limit_up-run-bigm) | done   | not built for a modular build                                                                                            |

<!-- gallery: examples/references/pypsa/rung_27_modular_ramp.py -->

### Rung 28 — a start-up ramp alone

PyPSA builds a ramp row where either the ramp limit or the start-up ramp is
given, and reads the missing one as `1.0`, the full build. The down row is the
same with the shut-down ramp. This rung has a committable generator, link and
process that carry only a start-up ramp of 0.4 and a shut-down ramp of 0.5. The
start-up ramp caps the snapshot each unit turns on, and the shut-down ramp caps
the snapshot before it turns off.

| PyPSA                                                                                      | status | note                                                                                             |
| ------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------ |
| [`{c}-p-ramp_limit_up/down`, start-up or shut-down ramp alone](#generator-p-ramp_limit_up) | done   | the `where:` reads either limit; `ramp_up_rate` and its three siblings read a missing one as `1` |

<!-- gallery: examples/references/pypsa/rung_28_start_up_ramp.py -->

### Rung 29 — storage per investment period

`n.optimize(multi_investment_periods=True)` with storage that treats each
investment period as a horizon of its own. A storage unit with
`cyclic_state_of_charge_per_period` and a store with `e_cyclic_per_period`
close each period on itself: the first snapshot of a period carries in the
level of that period's last snapshot. A storage unit with
`state_of_charge_initial_per_period` and a store with `e_initial_per_period`
open each period on their initial level. The per-period cyclic flag overrides
the global one and the per-period initial flag. PyPSA reads the four flags only
under `multi_investment_periods`, so data prep feeds false on a plain run.

PyPSA also builds no ramp row at the first snapshot of a later period, with or
without these flags. The ramp-limited coal unit in this rung raises its output
from 59.2 to 90 across the period boundary, above its limit of 10 per
snapshot, while its ramp rows bind inside each period.

| PyPSA                                                                                                                    | status | note                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance), [`Store-energy_balance`](#store-energy_balance), per period | done   | two more cases in the charge carried in: a `shift(…, edge='wrap', by=snapshot_period, within=period)` and the initial level at `position(snapshot, by=snapshot_period, within=period) == 0` |
| [`{c}-p-ramp_limit_*`, `-bigM`, at a period start](#generator-p-ramp_limit_up)                                           | done   | the `where:` drops every period start but the horizon's first                                                                                                                               |

<!-- gallery: examples/references/pypsa/rung_29_storage_per_period.py -->

### Rung 30 — security-constrained

`n.optimize.optimize_security_constrained(branch_outages=...)`: after any one
outage of a listed passive branch, every branch of the same sub-network carries
its flow within its rating. PyPSA computes the sub-network's branch outage
distribution factors (BODF) and copies each flow limit row with the outaged
branch's flow, times its factor, added to the left-hand side
(`abstract.py:443-489`). The copy keeps the row's sense, right-hand side and
extendable rating. It carries no loss term: PyPSA builds the model without
`transmission_losses` and `linearized_unit_commitment` (`abstract.py:437-441`)
and hands any other keyword to the solver (`abstract.py:491`), so a security
run is lossless and integer. Data prep feeds `transmission_losses` false there.
A network with no passive branch is the exception: PyPSA runs a plain
`n.optimize()` with every keyword (`abstract.py:429-435`), and no outage
exists. An outage is a line or a transformer, and
a plain list names lines. The outaged branch is monitored too, at the factor
`-1`. The file states the copies over an `outage` axis, with the factors as
data prep, `Line_BODF` and `Transformer_BODF`. A plain run supplies no outage,
so no copy is built and the model collapses to the standard one.

The rung outages two lines and a transformer of a meshed triangle and leaves
the third line monitored only. A plain `n.optimize()` solves the same network
at objective `17380.0`; the outages raise it to `22113.33` (#620). The cheap
unit at `a` falls to 32 in every snapshot, the unit at `b` covers the rest, and
the extendable line `ca` builds 20.7 instead of 2. Six of the 120 copied rows
bind, in `Transformer-fix-s-lower` against a line outage and in
`Line-ext-s-lower` against a transformer outage.

| PyPSA                                                                                                                                                                                                        | status   | note                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`Line-fix-s-*-security-for-{c}-outage-in-sub-network-{n}`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n), [`Line-ext-s-*-security-…`](#line-ext-s-lower-security-for-c-outage-in-sub-network-n) | split    | PyPSA names a row per outaged component and sub-network; one block over the `outage` axis                                                                                                  |
| [`Transformer-fix-s-*-security-…`](#transformer-fix-s-lower-security-for-c-outage-in-sub-network-n), [`Transformer-ext-s-*-security-…`](#transformer-ext-s-lower-security-for-c-outage-in-sub-network-n)     | split    | the same for a transformer                                                                                                                                                                 |
| a branch not active in a period                                                                                                                                                                              | done     | PyPSA keeps the copy with that branch's flow dropped, so the file reads its flow as zero there; a copy left with no variable is not built here, where linopy counts it; no rung records it |
| a security-constrained run over scenarios                                                                                                                                                                    | diverges | rung 56, [PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942)                                                                                                                    |
| `transmission_losses`, `linearized_unit_commitment` in a security-constrained run                                                                                                                            | done     | PyPSA builds neither, so the copies carry no loss term and data prep feeds `transmission_losses` false; no rung, since rung 30 is lossless                                                 |

<!-- gallery: examples/references/pypsa/rung_30_security_constrained.py -->

### Rung 32 — storage that stands in one period only

`n.optimize(multi_investment_periods=True)` with storage that is not per period
and does not stand in every period. PyPSA opens such a storage at the first
snapshot it stands in: on its initial level where it is not cyclic, and on the
level of the last snapshot it stands in where it is cyclic
(`constraints.py:2095-2097`, `2270-2273`). It reads the previous level through
a forward fill over the snapshots the storage does not stand in. Because a
build year and a lifetime make those snapshots one run at each end of the
horizon, the file states the same rows with two data-prep parameters. The
opening snapshot past the horizon's first is `{c}_opens_late`. The number of
snapshots the storage does not stand in is `{c}_inactive_snapshots`, and a
cyclic storage reaches back that many snapshots further. A plain run feeds
false and zero, so the rows collapse to the standard ones. The assumptions
[`StorageUnit_stands_in_one_run`](#storageunit_stands_in_one_run),
[`-opens_late_only_where_it_opens`](#storageunit_opens_late_only_where_it_opens)
and [`-opens_late_where_it_opens`](#storageunit_opens_late_where_it_opens), and
the `Store` ones, state the run and the opening snapshot. No
assumption ties `{c}_inactive_snapshots` to the count of inactive snapshots,
because a `count` compares against a whole number and not against a
parameter.

The rung builds a cyclic storage unit and a store with an initial level of 5 in
2030, and a cyclic store that retires after 2020. The earlier file read the
level before 2030 as absent and dropped the opening row, so each storage
opened on any level it chose. With the same rows, the objective falls to
`5620.61` (#620).

| PyPSA                                                                                                                                                   | status | note                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance), [`Store-energy_balance`](#store-energy_balance), at the first snapshot a storage stands in | done   | the `cyclic` and `opening` cases hold at `position(snapshot) == 0` or at `{c}_opens_late`; the cyclic one shifts one snapshot and then `{c}_inactive_snapshots` more, `edge='wrap'` |

<!-- gallery: examples/references/pypsa/rung_32_storage_later_period.py -->

### Rung 33 — maintenance

A `Generator`, `Link` or `Process` with `maintainable=True` is taken off for
`maintenance_events` events (default 1) within the horizon. Each event covers
the snapshot it starts in and the snapshots after it, until their
`generators` weightings reach `maintenance_duration` hours
(`constraints.py:767-800`). While it is in maintenance, the component loses the
share `maintenance_pu` (default 1) of its build from both of its bounds
(`constraints.py:135-145`, `221-234`). The status `maintenance` is continuous in
[0, 1], and the binary starts make it whole (`variables.py:202-259`). An
extendable build multiplies a variable by a variable. PyPSA writes that product
as `maintenance_capacity` and holds it with four McCormick rows against
`p_nom_min` and `p_nom_max` (`constraints.py:810-845`), so PyPSA refuses an
extendable maintainable build with an infinite `p_nom_max`.

The window of an event depends on the weightings, so its width varies along
`snapshot`. `sum_back` takes a width that does not vary along the dimension it
sums. So the file reads the windows as data: the relation
`*_maintenance_cover` pairs each start with the snapshots it covers. The mask
`*_maintenance_start_blocked` marks the starts whose window runs past the end
of the horizon or into a snapshot the component does not stand in. Both come
from `maintenance_duration`, the weightings and `active`. With them, each row
is the one PyPSA builds. Across investment periods an event may cross a period
boundary, and the count is over the whole horizon, as in PyPSA. Over scenarios
every maintenance variable is second stage, one schedule per scenario.

Here every maintainable component is new, and a peaker at 60 covers the east
bus. With the same network and no `maintainable`, PyPSA solves to
`5388.833333333333`.

| PyPSA                                                                                                                                                                                                  | status | note                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | --------------------------------------------------- |
| [`Generator-maintenance`, `-maintenance_start`, `-maintenance_capacity`](#variable-domains), and the `Link` and `Process` ones                                                                         | done   | zero where the component is not maintainable        |
| [`Generator-maint-event-count`](#generator-maint-event-count), [`-maint-window`](#generator-maint-window), [`-maint-start-horizon`](#generator-maint-start-horizon), and the `Link` and `Process` ones | done   | the window and the blocked starts are data prep     |
| [`Generator-maintcap_*`](#generator-maintcap_upper), and the `Link` and `Process` ones                                                                                                                 | done   | `-maintcap_lower_nommin` only where `p_nom_min > 0` |
| [`Generator-fix-p-*`](#generator-fix-p-lower), [`-ext-p-*`](#generator-ext-p-lower), and the `Link` and `Process` ones, in maintenance                                                                 | done   | the bound less `maintenance_pu` of the build        |

<!-- gallery: examples/references/pypsa/rung_33_maintenance.py -->

### Rung 34 — maintenance of committable units

A committable build scales its bounds by the status, so maintenance takes its
share off the status. PyPSA writes the product of the status and `maintenance`
as `maintenance_status`, with three McCormick rows, so a unit in maintenance
can also be off (`variables.py:301-338`, `constraints.py:425-458`). A modular
committable build uses the same product, bounded by the module count
`p_nom_max / p_nom_mod` (`constraints.py:498-533`). An extendable committable
build that is not modular uses `maintenance_capacity` in its big-M rows
instead (`constraints.py:363-373`). `-com-ext-p-upper-bigM` does not change.
Ramps, the up and down times and the storage rows do not read maintenance.

With the same network and no `maintainable`, PyPSA solves to `5370.0`.

| PyPSA                                                                                                                                                                                                                                                      | status | note                                                       |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------- |
| [`Generator-maintenance_status`](#variable-domains), and the `Link` and `Process` ones                                                                                                                                                                     | done   |                                                            |
| [`Generator-maint-status-*`](#generator-maint-status-le-status), [`-maint-modstatus-*`](#generator-maint-modstatus-le-status), and the `Link` and `Process` ones                                                                                           | done   | a fixed build's status, and a modular build's module count |
| [`Generator-com-p-*`](#generator-com-p-lower), [`-com-mod-p-*`](#generator-com-mod-p-lower), [`-com-ext-p-lower`](#generator-com-ext-p-lower), [`-com-ext-p-upper-cap`](#generator-com-ext-p-upper-cap), and the `Link` and `Process` ones, in maintenance | done   |                                                            |

<!-- gallery: examples/references/pypsa/rung_34_committable_maintenance.py -->

### Rung 35 — a global constraint for one investment period

`n.optimize(multi_investment_periods=True)` with `primary_energy` and
`operational_limit` rows that name an `investment_period`. PyPSA sums such a
row over the snapshots of that period only, and over the whole horizon where
the row names none (`global_constraints.py:373-378`, `600-606`). Each snapshot
counts with its generator weighting times the `years` weighting of its period
(`:326`, `:615`). A storage unit or store that reopens per period closes at the
last snapshot of each counted period, weighted by that period's years
(`:474-477`, `:673-676`). One that carries its level across periods closes
once, at the last counted snapshot (`:459-470`, `:658-668`). The file states
the counted snapshots as `GlobalConstraint_counts_snapshot`, data prep, and
the years as `period_weight_years`. A plain run feeds all true and one, so the
rows collapse to the standard ones.

The rung caps CO2 in 2030 alone, caps it again over the horizon, and limits a
hydro carrier with a per-period storage unit and store in 2020. The years
weightings are 5 and 10. With the same network and no `investment_period`,
PyPSA solves to `10675.0`.

| PyPSA                                                                                                     | status            | note                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit) over one investment period | done              | `GlobalConstraint_energy_weight` is zero outside the counted snapshots, and the years weigh each snapshot                                                           |
| the closing level of storage in those rows                                                                | done              | `StorageUnit_closing_weight`, `Store_closing_weight`: each counted period's last snapshot where the storage reopens per period, the last counted snapshot otherwise |
| a `primary_energy` row for one period over storage that reopens per period                                | refused, as PyPSA | assumed: [`StorageUnit_primary_energy_per_period_closes_over_the_horizon`](#storageunit_primary_energy_per_period_closes_over_the_horizon), and the `Store` one     |

<!-- gallery: examples/references/pypsa/rung_35_period_global_constraints.py -->

### Rung 36 — quadratic costs on a process and on storage

PyPSA's `marginal_cost_quadratic` on the three other components that carry it
(`variables.csv:22`, `:30`, `:33`): a process pays on its internal power `p`, a
storage unit on `p_dispatch` only, and a store on its net `p`, so charging
costs as much as delivering. Each term is the square times the cost, weighted
as the linear term is (`optimize.py:317-334`). A plain run feeds zero, so the
terms vanish.

The rung puts a quadratic cost on a process, a storage unit, with a cost that
changes per snapshot, and a store. With the same network and no quadratic
cost, PyPSA solves to `17641.666666666668`.

| PyPSA                                                                     | status            | note                                                                                                                                                                                          |
| ------------------------------------------------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`marginal_cost_quadratic`](#objective) on Process, StorageUnit and Store | done              | degree 2 in the objective; `p_store` is not charged                                                                                                                                           |
| a quadratic cost under a risk preference                                  | refused, as PyPSA | assumed: [`Generator_marginal_cost_quadratic_without_risk_preference`](#generator_marginal_cost_quadratic_without_risk_preference), and the `Link`, `Process`, `StorageUnit` and `Store` ones |

<!-- gallery: examples/references/pypsa/rung_36_quadratic_storage_process.py -->

### Rung 37 — storage dispatch pinned to a schedule

PyPSA pins a store's power delivered to `p_set`, and a storage unit's dispatch
and charging to `p_dispatch_set` and `p_store_set`, each on its own
(`optimize.py:846`, `:851`; `constraints.py:1961-2019`). A row stands only
where a value is given and the storage is active. A plain run gives no value,
so no row stands.

The rung pins a store to deliver 10 in the first snapshot and to take 5 in the
last, and pins a storage unit's dispatch in the first snapshot and its
charging in the second. With the same network and no pins, PyPSA solves to
`5811.111111111111`.

| PyPSA                                                                                                                                             | status | note                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------- |
| [`Store-p_set`](#store-p_set), [`StorageUnit-p_dispatch_set`](#storageunit-p_dispatch_set), [`StorageUnit-p_store_set`](#storageunit-p_store_set) | done   | `where:` a value is given and the storage is active |

<!-- gallery: examples/references/pypsa/rung_37_fixed_storage_dispatch.py -->

### Rung 38 — delays per investment period

`n.optimize(multi_investment_periods=True)` with delayed ports. PyPSA applies
a link's or a process's `delay` in each investment period on its own
(`constraints.py:1324-1332`; `multiports.py:212-219`). A `cyclic_delay` port
wraps from the end of its own period. A port that is not cyclic loses the flow
still in transit at the first snapshots of every period. PyPSA measures the
delay in `generators` weighting per period and rounds it down to a snapshot
start (`multiports.py:106-123`). Scenarios do not change the source snapshot.
`Link_output_arrival` and `Process_output_arrival` therefore shift with
`by=snapshot_period, within=period`. A plain run has one period, so the shift
is the flat one.

The rung builds a link that delays by two and wraps, and a process that
delays by one and does not wrap, on two periods of four snapshots. The earlier
file shifted over the flat horizon, so 2030 read the flow sent in 2020. With
that flat shift patched into PyPSA's source index, the network solves to
`10543.75` (#620).

| PyPSA                                                                                | status | note                                                                                                                                       |
| ------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [link and process `delay`, `cyclic_delay`](#bus-nodal_balance) per investment period | done   | `shift(offset=delay, by=snapshot_period, within=period)`; `edge='wrap'` closes each period, `edge=0` vacates each period's first snapshots |

<!-- gallery: examples/references/pypsa/rung_38_delay_per_period.py -->

### Rung 39 — a negative relative growth

`n.optimize(multi_investment_periods=True)` with a carrier whose
`max_relative_growth` is negative. PyPSA clips the share at zero before it
builds `Carrier-growth_limit` (`global_constraints.py:237`), so a negative
share adds nothing and does not tighten the limit. `Carrier_relative_growth`
states the clip as a case: the given share where it is positive, zero
otherwise. A plain run has one period and builds no growth row.

The rung builds a battery carrier with `max_growth=20` and
`max_relative_growth=-0.5`, and two stores built in 2020 and 2030. The earlier
file read the share as given, so the 2030 row added half of the 2020 build to
the left side. With that row patched into PyPSA through `extra_functionality`,
the network solves to `9347.5` (#620).

| PyPSA                                                                              | status | note                                                                                           |
| ---------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------- |
| [`Carrier-growth_limit`](#carrier-growth_limit), `max_relative_growth.clip(min=0)` | done   | `Carrier_relative_growth` is `Carrier_max_relative_growth` where it is positive, `0` otherwise |

<!-- gallery: examples/references/pypsa/rung_39_negative_relative_growth.py -->

### Rung 40 — a global constraint per scenario

`n.set_scenarios(...)` with `GlobalConstraint` rows whose `constant` and
`sense` differ between the scenarios. PyPSA builds one `GlobalConstraint-{name}`
row per scenario for `primary_energy`, `operational_limit` and
`transmission_volume_expansion_limit`, and reads each scenario's own sense and
constant (`global_constraints.py:361-371`, `:556-557`, `:748-749`,
`:786-795`, `:860-861`). The file states `GlobalConstraint_constant` and
`GlobalConstraint_sense` over `scenario` as well, so each row takes its own
value in each future. A row with no scenario axis in its total, such as the
transmission volume, repeats the same capacity sum under each scenario's
constant. A plain run feeds one scenario, and the rows collapse to the standard
ones.

The rung puts an extendable line under a volume limit of `60` in the calm
future and `20` in the stormy one, and a CO2 row that is at most `250` in the
calm future and exactly `200` in the stormy one. All three bind. With the same
network and the calm values in both futures, PyPSA solves to
`12943.333333333334`.

| PyPSA                                                                                                                                                                                                | status   | note                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit), [`transmission_volume_expansion_limit`](#transmission_volume_expansion_limit) with a constant and sense per scenario | done     | `GlobalConstraint_constant` and `GlobalConstraint_sense` over `scenario`                                                            |
| `transmission_expansion_cost_limit` on a network with scenarios                                                                                                                                      | diverges | rung 52, [PyPSA/PyPSA#1939](https://github.com/PyPSA/PyPSA/issues/1939)                                                             |
| `transmission_volume_expansion_limit` on a network with scenarios and `multi_investment_periods`                                                                                                     | diverges | rung 53, [PyPSA/PyPSA#1939](https://github.com/PyPSA/PyPSA/issues/1939)                                                             |
| a `carrier_attribute` or `investment_period` per scenario                                                                                                                                            | done     | PyPSA reads both per scenario (`global_constraints.py:797-802`); the weights and `GlobalConstraint_counts_snapshot` span `scenario` |

<!-- gallery: examples/references/pypsa/rung_40_scenario_global_constraints.py -->

### Rung 41 — operating data per scenario

`n.set_scenarios(...)` with a gas unit's `marginal_cost` and a link's
`efficiency` set per scenario. PyPSA reads both through `c.da`, one value per
scenario, into the objective and into `Bus-nodal_balance`
(`components/array.py:332-395`). The file states `Generator_marginal_cost` and
`Link_efficiency` over `scenario`, as it states every parameter PyPSA reads per
scenario. A plain run feeds one scenario, and the rows collapse to the standard
ones.

The rung adds a gas unit that costs `20` in the calm future and `80` in the
stormy one, and a second link that delivers `0.9` and `0.6` of its flow. Each
binds. With the calm cost in both futures, PyPSA solves to `16308.0`; with the
calm efficiency in both, to `16992.0`; with both calm values in both, to
`15660.0`.

| PyPSA                                                                                                         | status   | note                                                                    |
| ------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------- |
| [objective](#objective), [`Bus-nodal_balance`](#bus-nodal_balance) with a cost and an efficiency per scenario | done     | `Generator_marginal_cost` and `Link_efficiency` over `scenario`         |
| a link `delay` or `cyclic_delay` that differs by scenario                                                     | diverges | rung 54, [PyPSA/PyPSA#1941](https://github.com/PyPSA/PyPSA/issues/1941) |
| a transformer in a cycle on a network with scenarios                                                          | diverges | rung 55, [PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942) |
| a committable component on a network with scenarios                                                           | diverges | rung 58, [PyPSA/PyPSA#1913](https://github.com/PyPSA/PyPSA/issues/1913) |
| [`{c}-p_nom_set`](#generator-p_nom_set) on a network with scenarios                                           | diverges | rung 57, [PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942) |

<!-- gallery: examples/references/pypsa/rung_41_scenario_operational_data.py -->

### Rung 42 — first-stage data per scenario

`n.set_scenarios(...)` with an extendable unit whose `capital_cost` and
`p_nom_max` differ between the scenarios. The build is chosen once, but PyPSA
reads its bounds per scenario and writes `Generator-ext-p_nom-lower` and
`-upper` once per scenario, so the tightest cap binds
(`constraints.py:885-895`). It prices the build at each scenario's capital
cost and weights the terms by the scenario weights (`optimize.py:405-412`,
`:448-454`), so the build pays its capital cost in expectation. The file states
`Generator_p_nom_max` and `Generator_capital_cost` over `scenario`, the bound
rows over `scenario`, and the capital terms of the objective under
`scenario_weight`. A plain run feeds one scenario of weight one, and the rows
and the objective collapse to the standard ones.

The rung's wind unit costs `20` in the calm future and `60` in the stormy one,
weighted `0.6` and `0.4`, and may be built to `100` and `30`. PyPSA builds `30`
at the expected cost of `36`: the same network with a cost of `36` and a cap of
`30` in both futures solves to the same objective. With the calm values in both
futures, PyPSA solves to `1943.0`.

| PyPSA                                                                               | status | note                                                      |
| ----------------------------------------------------------------------------------- | ------ | --------------------------------------------------------- |
| [`{c}-ext-p_nom-lower/upper`](#generator-ext-p_nom-lower) with a bound per scenario | done   | one row per scenario, over `scenario`; the tightest binds |
| [capital cost](#objective) per scenario                                             | done   | `scenario_weight` times each scenario's capital cost      |

<!-- gallery: examples/references/pypsa/rung_42_scenario_first_stage.py -->

### Rung 43 — a component's sign

`n.optimize()` with a generator, a load, a storage unit and a store whose
`sign` is not PyPSA's default. PyPSA multiplies each of their terms in
`Bus-nodal_balance` by that `sign`: a generator's `p`, a storage unit's
`p_dispatch` and `p_store`, a store's `p` (`constraints.py:1428-1429`), and a
load's `p_set` on the constant side (`constraints.py:1538`). It reads `sign`
nowhere else in the model. The default is `1` for a generator, a storage unit
and a store, and `-1` for a load. PyPSA refuses a `sign` that differs by
scenario (`consistency.py:1187`), so the file states `Generator_sign`,
`Load_sign`, `StorageUnit_sign` and `Store_sign` without `scenario`. A plain run
feeds PyPSA's defaults, and the row collapses to the standard one.

The rung adds a unit that draws `20` from its bus at a cost of `-50`, a storage
unit that opens full and a full store, each with a `sign` of `-1`, and a load of
`10` with a `sign` of `1`, which feeds its bus. Each sign binds. With the default sign on the
unit, PyPSA solves to `-5652.78`; on the load, to `3925.0`; on the storage unit,
to `1187.5`; on the store, to `925.0`; on all four, to `-5255.56`.

| PyPSA                                                             | status | note                                                                                                           |
| ----------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------- |
| [`Bus-nodal_balance`](#bus-nodal_balance) with a component `sign` | done   | `Generator_sign`, `StorageUnit_sign` and `Store_sign` times each term, and `Load_sign` times the load, negated |

<!-- gallery: examples/references/pypsa/rung_43_sign.py -->

### Rung 45 — ramp limits per snapshot

`n.optimize()` with a generator, a link and a process whose `ramp_limit_up`
and `ramp_limit_down` change over time. PyPSA declares both `static or series`
for all three components, and `ramp_limit_start_up` and `ramp_limit_shut_down`
static. The row between two snapshots reads the limit at the later snapshot
(`constraints.py:1040-1041`, `1109-1110`, `1139-1140`). The "no limit" test is
made per snapshot (`constraints.py:1046-1047`), and a missing value reads as
the full build there (`constraints.py:1052-1055`). So the file states
`{c}_ramp_limit_up` and `{c}_ramp_limit_down` over `snapshot`, and
`{c}_ramp_up_rate` and `{c}_ramp_down_rate` with them. A snapshot without a
value has no row in the table, so the `where:` drops the row there unless a
start-up or shut-down ramp builds it. A plain run feeds the same value at each
snapshot, and the rows collapse to the standard ones.

The rung adds a steep bus with a load of `90` at the third snapshot. Each unit
may raise its output by `0.1` of its build, and by `0.5` into the third
snapshot. It may lower its output by `0.1`, and without a limit into the last
snapshot. With the constant limit `0.1` in each direction, the backup covers
the peak, and PyPSA solves to `90871.0` (#620).

| PyPSA                                                                              | status | note                                                                                                                                                               |
| ---------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`{c}-p-ramp_limit_up/down`](#generator-p-ramp_limit_up) with a limit per snapshot | done   | `{c}_ramp_limit_up`, `{c}_ramp_limit_down` and their rates span `snapshot`; a snapshot without a value drops the row unless a start-up or shut-down ramp builds it |

<!-- gallery: examples/references/pypsa/rung_45_ramp_per_snapshot.py -->

### Rung 46 — the output brought in

`n.optimize()` with units that carry `p_init`, the output they brought into the
horizon. PyPSA reads `p_init` only where a unit came in running
(`up_time_before > 0`), and reads zero where it came in off
(`constraints.py:1091-1092`). It builds the ramp rows at the first snapshot
where that value exists (`constraints.py:1094`), so a unit that came in running
without `p_init` has none there, as before. It carries the value into the first
snapshot's rows with the status the unit came in with (`constraints.py:1101-1106`).
This is the same for a Generator, a Link and a Process. It holds for a fixed,
an extendable and a committable build, and for the big-M rows of a committable
extendable build (`constraints.py:937-946`). PyPSA reads `p_init` per scenario.
Under `multi_investment_periods` it reads it only at the horizon's first
snapshot, because no ramp row stands at a later period start
(`constraints.py:1097-1099`). The file states `{c}_p_init`, and the output
carried in at the first snapshot is `{c}_status_initial * {c}_p_init`. The
first-snapshot `where:` reads `{c}_status_initial == 0 OR {c}_p_init`. A
plain run feeds no `p_init`, and the rows collapse to the standard ones.

PyPSA warns where a committable generator came in off and has a `p_init`, and
ignores the value (`consistency.py:669-680`). The product with
`{c}_status_initial` ignores it too. A unit that is not committable and came in
off is refused: see [Refusals](#refusals). PyPSA sets the first-snapshot mask
without its `active` mask, so a unit that does not stand at the first snapshot
still gets a row there, with no variable in it. The file does not state that
row.

The rung adds a warm bus with a load of `150`, then `60`, served by six
ramp-limited units: a fixed generator, a link from `p_init = 0`, a dear process
that came in at full output, an extendable generator, a committable generator
and a committable extendable generator. Each `p_init` binds. Without any of
them, PyPSA solves to `9921.0` (#620).

| PyPSA                                                                                                                     | status | note                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-p-ramp_limit_*`](#generator-p-ramp_limit_up), [`-bigM`](#generator-p-ramp_limit_up-run-bigm), at the first snapshot | done   | `{c}_previous_p` opens on `{c}_status_initial * {c}_p_init`; the row stands where `{c}_status_initial == 0 OR {c}_p_init` |

<!-- gallery: examples/references/pypsa/rung_46_initial_output.py -->

### Rung 48 — a start and a stop, unweighted

`n.optimize(multi_investment_periods=True)` with a committable unit that starts
and stops. PyPSA adds `start_up_cost * start_up` and
`shut_down_cost * shut_down` to the objective without the snapshot's objective
weight and without the period's weight (`optimize.py:414-429`). It weights every
other operating term by both (`optimize.py:262-264`). Over scenarios, it weights
the start and stop costs by the scenario's weight, as every operating term
(`optimize.py:448-452`). The file states the two terms in `scenario_opex`
without a weight, so the scenario weight is the only one they carry.

The rung builds a committable peaker that starts once and stops once in each of
two periods, with period weights `1.0` and `0.5` and snapshot weights that are
not `1.0`. PyPSA solves to `7325.0`, and to `6525.0` without the start and stop
costs. The difference is `800.0`, the four events at their unweighted cost. The
earlier file weighted them by the period, which reads `600.0` (#620).

| PyPSA                                                                                                 | status | note                                                              |
| ----------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------- |
| [`start_up_cost`, `shut_down_cost`](#objective) under `multi_investment_periods` and snapshot weights | done   | no snapshot weight and no period weight; the scenario weight only |

<!-- gallery: examples/references/pypsa/rung_48_unweighted_start_up.py -->

### Rung 49 — a growth limit in one period

`n.optimize()` with a carrier that carries `max_growth`. PyPSA builds
`Carrier-growth_limit` only under `multi_investment_periods`, and returns
before it reads the carrier otherwise (`global_constraints.py:219-220`). A
single-period run has no growth limit. The file states the row where
`Carrier_max_growth` has a value, so data prep feeds no value on a
single-period run, and no row is built.

The rung adds a cheap extendable wind unit with `max_growth = 10` to the spine.
PyPSA builds it to `67` and solves to `335.0`, the same as without the limit.
The same network as one investment period under `multi_investment_periods`
caps the build at `10` and solves to `2583.33` (#620).

| PyPSA                                                                              | status | note                                               |
| ---------------------------------------------------------------------------------- | ------ | -------------------------------------------------- |
| [`Carrier-growth_limit`](#carrier-growth_limit) without `multi_investment_periods` | done   | not built; data prep feeds no `Carrier_max_growth` |

<!-- gallery: examples/references/pypsa/rung_49_single_period_growth.py -->

### Rung 50 — a load that is not active

`n.optimize()` with a load whose `active` is false. PyPSA masks the load side
of `Bus-nodal_balance` by `active` (`constraints.py:1537-1538`), so an inactive
load draws nothing. A load has no build year and no lifetime, so its `active` is
the static flag alone, in every snapshot and every period
(`descriptors.py:135-136`). PyPSA refuses an `active` that differs by scenario
(`consistency.py:1195`). The file states `Load_active` over the load and
`Load_demand`, the load's signed demand where it is active and zero where it
is not. The balance reads `Load_demand`. A plain run feeds every load active,
and the row collapses to the standard one.

The rung adds an inactive load to the spine's south bus. PyPSA solves to
`7380.0`, the same as without the load. With the load active, it solves to
`14730.0` (#620).

| PyPSA                                                                      | status | note                                               |
| -------------------------------------------------------------------------- | ------ | -------------------------------------------------- |
| [`Bus-nodal_balance`](#bus-nodal_balance) with a load that is not `active` | done   | `Load_demand` is zero where `Load_active` is false |

<!-- gallery: examples/references/pypsa/rung_50_inactive_load.py -->

### Rung 51 — a growth limit after an asset retires

`n.optimize(multi_investment_periods=True)` with a carrier that carries
`max_growth`, and an extendable asset of that carrier that retires before the
last period. The file counts a build in the first period it stands in only:
`{c}_first_active` is one there and zero elsewhere. PyPSA `1.3.0` takes
`active.cumsum() == 1`, which stays true after the asset retires, so it counts
the asset again in every later period (`global_constraints.py:276`,
[PyPSA/PyPSA#1938](https://github.com/PyPSA/PyPSA/issues/1938)).

The rung builds two solar units under one carrier with `max_growth = 10`. The
old one stands in 2020 only, the new one in 2030 only. Both build to `10` in
the file. PyPSA holds the new one at `10` minus the old one's build, so it
builds nothing in 2030 and solves to `5185.0`. The oracle is the same network
with a carrier per unit, each with the same limit: each carrier has one asset,
and the repeated row PyPSA builds for the old one repeats its own bound. It
solves to `3432.5`. Without `max_growth`, the network solves to `248.75`.

| PyPSA                                                                      | status   | note                                                                                                                                 |
| -------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| [`Carrier-growth_limit`](#carrier-growth_limit) with an asset that retires | diverges | [PyPSA/PyPSA#1938](https://github.com/PyPSA/PyPSA/issues/1938); `{c}_first_active` is zero after the first period an asset stands in |

<!-- gallery: examples/references/pypsa/rung_51_growth_retired_asset.py -->

### Rung 52 — a transmission cost limit per scenario

`n.set_scenarios(...)` with a `transmission_expansion_cost_limit` row. The
file builds the row in every scenario, as it builds every global constraint.
PyPSA `1.3.0` builds no row: it matches the extendable names against a table
indexed by scenario and name, and finds none (`global_constraints.py:916`,
[PyPSA/PyPSA#1939](https://github.com/PyPSA/PyPSA/issues/1939)).

The rung adds an extendable DC link to the spine under a cost limit of `150`,
so the link builds `15`. The two futures are identical. The oracle is the same
network without scenarios, which PyPSA solves with the row to `15630.0`. With
scenarios, PyPSA solves to `11890.0`, the objective of the network without the
row.

| PyPSA                                                                                                 | status   | note                                                                                 |
| ----------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------ |
| [`transmission_expansion_cost_limit`](#transmission_expansion_cost_limit) on a network with scenarios | diverges | [PyPSA/PyPSA#1939](https://github.com/PyPSA/PyPSA/issues/1939); the row per scenario |

<!-- gallery: examples/references/pypsa/rung_52_scenario_cost_limit.py -->

### Rung 53 — a transmission volume limit per scenario and period

`n.set_scenarios(...)` and `n.optimize(multi_investment_periods=True)` with a
`transmission_volume_expansion_limit` row. The file builds the row in every
scenario. PyPSA `1.3.0` builds no row: the active-asset filter reindexes a table
indexed by scenario and name by the names alone, and keeps none
(`global_constraints.py:828`, `descriptors.py:263`,
[PyPSA/PyPSA#1939](https://github.com/PyPSA/PyPSA/issues/1939)). Without
periods, PyPSA builds the row (rung 40).

The rung is two periods with an extendable line of length `3` under a volume
limit of `60`, so the line builds `20`. The two futures are identical. The
oracle is the same network without scenarios, which PyPSA solves with the row to
`15005.0`. With scenarios, PyPSA solves to `1465.0`, the objective of the
network without the row.

| PyPSA                                                                                                                                    | status   | note                                                                                 |
| ---------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------ |
| [`transmission_volume_expansion_limit`](#transmission_volume_expansion_limit) on a network with scenarios and `multi_investment_periods` | diverges | [PyPSA/PyPSA#1939](https://github.com/PyPSA/PyPSA/issues/1939); the row per scenario |

<!-- gallery: examples/references/pypsa/rung_53_scenario_period_volume_limit.py -->

### Rung 54 — a delay per scenario

`n.set_scenarios(...)` with a link `delay` and a process `delay1` that differ
by scenario. The file states `Link_output_delay`, `Link_output_cyclic_delay`,
`Process_output_delay` and `Process_output_cyclic_delay` over `scenario`, so
each future shifts a port's flow by its own delay. The shifted flow already
spans `scenario`, so the offset may too. PyPSA `1.3.0` groups the ports by
delay over all scenarios and shifts each group in every scenario, so a port
whose delay differs by scenario delivers its flow once per group
(`constraints.py:1269-1276`,
[PyPSA/PyPSA#1941](https://github.com/PyPSA/PyPSA/issues/1941)). A plain run
feeds one scenario, and the rows collapse to the standard ones.

The rung is a capped source feeding two sinks, one through a link and one
through a process. The calm future delivers at once. The stormy one delivers a
snapshot late, cyclically on the link and with the first snapshot lost on the
process. Nothing is extendable, so the futures do not interact. The oracle is
each future solved alone, `7650.0` calm and `11500.0` stormy, weighted `0.6`
and `0.4`: `9190.0`. PyPSA solves to `9300.0`.

| PyPSA                                                                                                                                                        | status   | note                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------ |
| [`Link_output_arrival`](#link_output_arrival), [`Process_output_arrival`](#process_output_arrival) with a `delay` or `cyclic_delay` that differs by scenario | diverges | [PyPSA/PyPSA#1941](https://github.com/PyPSA/PyPSA/issues/1941); the delays span `scenario` |

<!-- gallery: examples/references/pypsa/rung_54_scenario_delay.py -->

### Rung 55 — a transformer cycle per scenario

`n.set_scenarios(...)` with two transformers in parallel, a cycle. The file
builds the Kirchhoff voltage row in every scenario. PyPSA `1.3.0` raises
`KeyError`: it selects the transformers of a cycle by name from a table indexed
by scenario and name (`constraints.py:1654`,
[PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942)).

The rung adds two transformers of reactance `0.1` and `0.2`, each rated `30`,
to the spine. The row splits the flow two to one, so the first caps the pair at
`45`. The two futures are identical. The oracle is the same network without
scenarios, which PyPSA solves to `13105.0`. One transformer rated `60` solves to
`11705.0`.

| PyPSA                                                                                            | status   | note                                                                                                                                    |
| ------------------------------------------------------------------------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law) with a transformer on a network with scenarios | diverges | [PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942); the row per scenario. The file holds one phase shift for every scenario |

<!-- gallery: examples/references/pypsa/rung_55_scenario_transformer_cycle.py -->

### Rung 56 — a security-constrained run per scenario

`n.optimize.optimize_security_constrained(...)` on a network with scenarios.
The file builds the outage copies in every scenario. PyPSA `1.3.0` raises
`ValueError`. With outages named as a list, it finds none of them in the
network (`abstract.py:427`). With no outages named, it fails to intersect the
branches (`abstract.py:445`,
[PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942)). With outages
named as `(component, name)` pairs, it builds no copy and solves without them.

The rung adds two parallel lines rated `30` and `35` to the spine, and outages
each. Each line must carry the whole import alone, so the import falls to `30`.
The two futures are identical. The oracle is the same network without
scenarios, which PyPSA solves to `18205.0`. A plain `n.optimize()` solves to
`11705.0`.

| PyPSA                                                                                                                                             | status   | note                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------- |
| [`Line-fix-s-*-security-for-{c}-outage-in-sub-network-{n}`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n) on a network with scenarios | diverges | [PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942); the copies per scenario |

<!-- gallery: examples/references/pypsa/rung_56_scenario_security_constrained.py -->

### Rung 57 — a fixed build per scenario

`n.set_scenarios(...)` with `p_nom_set` on an extendable unit. The file builds
`Generator-p_nom_set` in every scenario. PyPSA `1.3.0` raises `TypeError`: it
renames the scenario-and-name index of the set build with one name
(`constraints.py:1708`,
[PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942)). The same holds
for every `*_nom_set`.

The rung adds a cheap extendable wind unit to the spine, pinned to `20`. The
two futures are identical. The oracle is the same network without scenarios,
which PyPSA solves to `4800.0`. Without `p_nom_set`, the unit builds `67` and
the network solves to `335.0`.

| PyPSA                                                               | status   | note                                                                                 |
| ------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------ |
| [`{c}-p_nom_set`](#generator-p_nom_set) on a network with scenarios | diverges | [PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942); the row per scenario |

<!-- gallery: examples/references/pypsa/rung_57_scenario_nom_set.py -->

### Rung 58 — a committable unit per scenario

`n.set_scenarios(...)` with a committable unit. The file builds the status
rows in every scenario. PyPSA `1.3.0` raises `KeyError`: it selects the status
by snapshot and name where the first dimension is the scenario
(`constraints.py:1872`,
[PyPSA/PyPSA#1913](https://github.com/PyPSA/PyPSA/issues/1913)).

The rung adds a cheap committable unit to the spine that cannot run below `40`
% of its build, with a start-up cost of `100`. The two futures are identical.
The oracle is the same network without scenarios, which PyPSA solves to
`7430.0`. The same unit, not committable, solves to `7330.0`.

| PyPSA                                               | status   | note                                                                                  |
| --------------------------------------------------- | -------- | ------------------------------------------------------------------------------------- |
| a committable component on a network with scenarios | diverges | [PyPSA/PyPSA#1913](https://github.com/PyPSA/PyPSA/issues/1913); the rows per scenario |

<!-- gallery: examples/references/pypsa/rung_58_scenario_committable.py -->

### Rung 60 — efficiencies per snapshot

`n.optimize()` with a link, a process, a storage unit, a fuel unit and a
transformer whose coefficients change over time. PyPSA declares a link's
`efficiency`, `efficiency2`, …, a process's `rate0`, `rate1`, …, a storage
unit's `efficiency_store` and `efficiency_dispatch`, a generator's
`efficiency` and a transformer's `phase_shift` all `static or series`, and
reads each per snapshot. The balance reads a port's coefficient at the
snapshot the flow arrives: it shifts the flow first and multiplies it by the
coefficient after (`constraints.py:1518-1522`). The energy balance of a storage
unit reads both efficiencies per snapshot (`constraints.py:2081-2082`). A
`primary_energy` row divides a generator's output by its efficiency at the
same snapshot (`global_constraints.py:418-423`). A fixed phase shift enters the
cycle sum per snapshot (`constraints.py:1657-1663`). So the file states
`Link_efficiency`, `Process_rate`, `StorageUnit_efficiency_store`,
`StorageUnit_efficiency_dispatch`, `Generator_primary_energy_weight` and
`Transformer_phase_shift_weight` over `snapshot`. `Link_output_arrival` and
`Process_output_arrival` multiply the shifted flow by the coefficient. A
standing loss was already stated per snapshot, in `StorageUnit_retention` and
`Store_retention`. A plain run feeds the same value at each snapshot, and the
rows collapse to the standard ones.

The rung feeds a sink from a source over a link and a process that both
deliver one snapshot late, beside a storage unit and a fuel unit under a
`primary_energy` cap. A separate triangle carries a transformer with a fixed
phase shift per snapshot. The `generators` weighting is uniform, as in rung 16.
PyPSA solves to `130562.09`. Each coefficient binds: with its mean at each
snapshot, PyPSA solves to these objectives (#620).

| coefficient held at its mean       | objective   |
| ---------------------------------- | ----------- |
| link `efficiency`                  | `130774.59` |
| process `rate1`                    | `130622.09` |
| storage unit `efficiency_store`    | `129770.09` |
| storage unit `efficiency_dispatch` | `129966.86` |
| generator `efficiency`             | `131280.86` |
| transformer `phase_shift`          | `130313.38` |

Where a delayed port reads the coefficient matters too. With each series
moved one snapshot later, which reads it at the snapshot the flow departs,
PyPSA solves to `130676.26` for the link and to `130742.09` for the process.

| PyPSA                                                                                      | status | note                                                                                              |
| ------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------- |
| [`Bus-nodal_balance`](#bus-nodal_balance) with an efficiency or a rate per snapshot        | done   | `Link_efficiency` and `Process_rate` span `snapshot`, read at the snapshot a delayed flow arrives |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance) with efficiencies per snapshot | done   | `StorageUnit_efficiency_store` and `StorageUnit_efficiency_dispatch` span `snapshot`              |
| [`primary_energy`](#primary_energy) with a generator efficiency per snapshot               | done   | `Generator_primary_energy_weight` spans `snapshot`                                                |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law) with a fixed phase shift per snapshot    | done   | `Transformer_phase_shift_weight` spans `snapshot`                                                 |

<!-- gallery: examples/references/pypsa/rung_60_efficiency_per_snapshot.py -->

## Refusals

Where PyPSA refuses to build, parity means refusing too. None is a language
gap. The maintenance checks are assumptions of the file, which the consumer
that binds the data runs. Each other one is a data check not made yet, and
where it should live — language, data prep, or harness — is one open question. Line numbers are pinned pypsa
1.3.0, the version the records above are from.

| PyPSA raises                                                               | on                                                                                                                                                                                        | here                                                                                                                                                                                                                                                                                                                                                                                                                                | note |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| `ValueError`, `optimize.py:467-474`                                        | a nonzero `marginal_cost_quadratic` on any Generator, Link, Process, StorageUnit or Store under a risk preference                                                                         | assumed where `omega > 0`: [`Generator_marginal_cost_quadratic_without_risk_preference`](#generator_marginal_cost_quadratic_without_risk_preference), and the `Link`, `Process`, `StorageUnit` and `Store` ones. The file cannot tell no risk preference from `omega = 0`, which PyPSA also refuses                                                                                                                                 |      |
| `ValueError`, `constraints.py:1850`                                        | fixed modular `p_nom` not a multiple of `p_nom_mod`                                                                                                                                       | a fractional module cap                                                                                                                                                                                                                                                                                                                                                                                                             | X1   |
| `ValueError`, `constraints.py:1557`                                        | load on a bus with nothing attached                                                                                                                                                       | row not built, unserved                                                                                                                                                                                                                                                                                                                                                                                                             | X2   |
| `ValueError`, `optimize.py:436`                                            | no component carries a cost                                                                                                                                                               | feasibility problem                                                                                                                                                                                                                                                                                                                                                                                                                 | X3   |
| `NotImplementedError`, `global_constraints.py:457`, `:509`, `:656`, `:704` | storage that carries its level across periods in a `primary_energy` or `operational_limit` row, with period `years` `!= 1`                                                                | assumed: [`StorageUnit_primary_energy_carried_over_has_unit_years`](#storageunit_primary_energy_carried_over_has_unit_years), [`StorageUnit_operational_limit_carried_over_has_unit_years`](#storageunit_operational_limit_carried_over_has_unit_years), and the `Store` ones                                                                                                                                                       |      |
| `KeyError`, `global_constraints.py:474`, `:526`                            | a `primary_energy` row for one period over storage that reopens per period                                                                                                                | assumed: [`StorageUnit_primary_energy_per_period_closes_over_the_horizon`](#storageunit_primary_energy_per_period_closes_over_the_horizon), and the `Store` one                                                                                                                                                                                                                                                                     |      |
| `UnboundLocalError`, `global_constraints.py:375`, `:602`                   | a `primary_energy` or `operational_limit` row that names an `investment_period` without `multi_investment_periods`                                                                        | data prep, at `GlobalConstraint_counts_snapshot`                                                                                                                                                                                                                                                                                                                                                                                    |      |
| `ValueError`, `constraints.py:2411`, `:2518`                               | an extendable lossy branch with `s_nom_max = inf`, either mode                                                                                                                            | data prep, at `Line_loss_max` and `Transformer_loss_max`                                                                                                                                                                                                                                                                                                                                                                            | X4   |
| `RuntimeError`, `constraints.py:2561`                                      | the secant loop passing `max_segments`                                                                                                                                                    | data prep, at the `segment` axis                                                                                                                                                                                                                                                                                                                                                                                                    | X4   |
| `ValueError`, `abstract.py:427`, `:445`                                    | a security-constrained run over scenarios                                                                                                                                                 | rows per scenario, not refused: a PyPSA bug, [PyPSA/PyPSA#1942](https://github.com/PyPSA/PyPSA/issues/1942), rung 56                                                                                                                                                                                                                                                                                                                |      |
| `NotImplementedError`, `global_constraints.py:66-68`                       | a `tech_capacity_expansion_limit` row on a network with scenarios                                                                                                                         | assumed where there is more than one scenario: [`GlobalConstraint_tech_capacity_expansion_limit_without_scenarios`](#globalconstraint_tech_capacity_expansion_limit_without_scenarios). The file cannot tell one scenario from none, which PyPSA also refuses                                                                                                                                                                       |      |
| `ConsistencyError`, `consistency.py:1506-1560`                             | a maintainable component whose `maintenance_duration` or `maintenance_events` is not positive, whose events do not fit the weighted horizon, or that is extendable with `p_nom_max = inf` | assumed: [`Generator_maintenance_events_positive`](#generator_maintenance_events_positive), [`-duration_positive`](#generator_maintenance_duration_positive), [`-duration_fits_the_horizon`](#generator_maintenance_duration_fits_the_horizon), [`-events_fit_the_horizon`](#generator_maintenance_events_fit_the_horizon), [`-build_cap_is_finite`](#generator_maintenance_build_cap_is_finite), and the `Link` and `Process` ones |      |
| nothing; HiGHS refuses the model, `constraints.py:500-503`                 | a fixed modular committable maintainable build, whose module count `p_nom_max / p_nom_mod` is infinite                                                                                    | assumed: [`Generator_maintenance_module_count_is_finite`](#generator_maintenance_module_count_is_finite), and the `Link` and `Process` ones                                                                                                                                                                                                                                                                                         |      |
| nothing; PyPSA builds the row, `constraints.py:1091-1094`, `1110-1112`     | a ramp-limited Generator, Link or Process that is not committable, with `up_time_before = 0`                                                                                              | assumed: [`Generator_came_in_running_unless_committable`](#generator_came_in_running_unless_committable), and the `Link` and `Process` ones. PyPSA caps the unit at zero in the first snapshot, or at its start-up ramp where another unit of the component is committable with a fixed build, and documents `up_time_before` as read only for a committable unit                                                                   |      |

Duals and solutions are read back by the harness on the specsolve side:
`marginal_price` is the balance dual over `w_objective`, `mu_upper` the
concatenation of the regime blocks, `p0`/`p1` derived from `Link-p`.

## The file

<!-- gallery: examples/pypsa.yaml -->
