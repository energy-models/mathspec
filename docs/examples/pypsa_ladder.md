<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA in one file

One spec file, `examples/pypsa.yaml`, states the spec of the model that a
plain `n.optimize()` builds in the power system modelling framework PyPSA. The
file grows one step of the PyPSA ladder
([a rung](../reference/glossary.md#rung)) at a time. Each rung states one
`n.optimize()` keyword or feature in full.

The file also states two classes of model beyond a plain `n.optimize()`. The
two-stage stochastic class spans a `scenario` dimension, and
`n.set_scenarios(...)` switches it on (rung 14). The multi-period investment
class spans a `period` dimension, and the keyword `multi_investment_periods`
switches it on (rung 15).

Each rung table lists the rows PyPSA builds, linked to their entries in the
file. The rows and the line numbers are those of PyPSA `master` at commit
`72a12418`, under `pypsa/optimization/`. The banner of each rung states the
objective that PyPSA solved its reference network to.

The work that turns a PyPSA network into the data the file declares
([data prep](../reference/glossary.md#data-preparation)) is outside the file.
[Data prep](#data-prep) lists the parameters whose values come from it.

Three rules apply throughout the file:

- Each bound is an explicit row, as PyPSA writes it, so its dual is the dual of
  a row.
- Each case of a PyPSA rule is a
  [`where:`](../reference/language/absence.md#where) condition on a column of
  data.
- The names are those of PyPSA, spelled `Component_attribute`. The typesetter
  prints them in the usual symbols, from the symbol table
  `examples/symbols/pypsa.yaml`.

## Statuses

A row has one of four statuses:

- A row is **done** where the file states it as the one entry that PyPSA builds.
- A row is **split** where the file states the same feasible region and optimum
  in a different form, such as several `where:` entries.
- A row is **out** where the file leaves it out, because PyPSA builds it only
  under the keyword, scope or version in the note.
- A row is **refused** where PyPSA refuses the data, and
  [Refusals](#refusals) lists what the file states for it.

A rung with no table adds no row. A name with `{k}`, `{s}`, `{c}` or `{n}` is a
family of rows that PyPSA numbers per segment, scenario, outaged component or
sub-network.

## The rungs

<!-- reference:spine:begin -->
> Every rung's network is `spine.build()` plus the rung's own `n.add` calls, data inline; a keyword not passed is PyPSA's default. A banner states what PyPSA solved the rung to; how an engine attaches the network to the file, and what it makes of it, is that engine's own record.

<details markdown="1">
<summary>The shared spine, <code>spine.py</code></summary>

`spine.py`

```python
"""The spine every rung starts from: two buses, a coal and a gas unit, one link, two loads.

Four hourly snapshots with three different weighting columns, none of them constant
and none 1.0, so a factor a formula drops or swaps cannot pass as identity.
"""

from __future__ import annotations

from datetime import datetime

#: Four hourly stamps — snapshots are timestamps, as PyPSA's are in practice and as the file declares them.
SNAPSHOTS = [datetime(2015, 1, 1, hour) for hour in range(4)]
WEIGHTINGS = {'objective': [2.0, 1.5, 2.5, 3.0], 'stores': [0.5, 2.0, 1.5, 2.5], 'generators': [1.5, 0.5, 3.0, 2.0]}


def build():
    """The spine as a fresh ``pypsa.Network``; each rung adds to what this returns."""
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(SNAPSHOTS)
    for column, values in WEIGHTINGS.items():
        n.snapshot_weightings[column] = values
    n.add('Bus', 'north')
    n.add('Bus', 'south')
    n.add('Generator', 'coal', bus='north', p_nom=100, marginal_cost=10)
    n.add('Generator', 'gas', bus='south', p_nom=100, marginal_cost=30)
    n.add('Link', 'wire', bus0='north', bus1='south', p_nom=40, p_min_pu=-1, efficiency=0.9)
    n.add('Load', 'north_load', bus='north', p_set=30)
    n.add('Load', 'south_load', bus='south', p_set=40)
    return n
```

</details>
<!-- reference:spine:end -->

### Rung 1 — transport

| PyPSA                                             | status | note                                                                                                                                                                                                       |
| ------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`Generator-p`, `Link-p`](#variable-domains)      | done   |                                                                                                                                                                                                            |
| [`Generator-fix-p-lower`](#generator-fix-p-lower) | done   |                                                                                                                                                                                                            |
| [`Generator-fix-p-upper`](#generator-fix-p-upper) | done   |                                                                                                                                                                                                            |
| [`Link-fix-p-lower`](#link-fix-p-lower)           | done   |                                                                                                                                                                                                            |
| [`Link-fix-p-upper`](#link-fix-p-upper)           | done   |                                                                                                                                                                                                            |
| [`Bus-nodal_balance`](#bus-nodal_balance)         | done   | a loaded bus with nothing attached in [Refusals](#refusals)                                                                                                                                                |
| `Bus-meshed-*-nodal_balance`                      | out    | the rows and duals of `Bus-nodal_balance`, split by component columns per bus into containers of the model-building library linopy, under the keyword `meshed_thresholds`, default `[30, 100, 400]` (#123) |
| [`marginal_cost`](#objective)                     | done   |                                                                                                                                                                                                            |
| `objective_constant`                              | split  | an objective shift, which a test compares net of `n._objective_constant`, nonzero in rungs 11 (`21915277.52`) and 13 (`160.0`)                                                                             |

Rungs 43, 50 and 60 extend the `Bus-nodal_balance` row.

<!-- reference:rung_01_transport:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7182.222222222223`, 45 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_01_transport.py`

```python
"""Rung 1: transport — two buses, two generators, one controllable link."""

from __future__ import annotations

from math import nan

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.links_t.p_set['wire'] = [10, nan, nan, nan]
    n.add('Generator', 'must_run', bus='south', p_nom=10, marginal_cost=0, p_set=[5, 5, 5, 5])
    return n
```

</details>
<!-- reference:rung_01_transport:end -->

### Rung 2 — storage

| PyPSA                                                                                               | status | note                                                                                                                                                                                   |
| --------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`StorageUnit-p_dispatch`, `-p_store`, `-state_of_charge`, `Store-e`, `Store-p`](#variable-domains) | done   |                                                                                                                                                                                        |
| [`StorageUnit-spill`](#variable-domains)                                                            | done   | `where: inflow > 0`, [`missing: 0`](../reference/language/absence.md#missing), with bounds on the variable, as PyPSA's                                                                 |
| [`StorageUnit-fix-*`](#storageunit-fix-p_dispatch-lower), [`Store-fix-e-*`](#store-fix-e-lower)     | done   |                                                                                                                                                                                        |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance)                                         | done   | the charge carried into a snapshot as a quantity stated with [`cases:`](../reference/language/named.md#cases) (cyclic, opening, carried), and `(1-loss)**eh` from data prep            |
| [`Store-energy_balance`](#store-energy_balance)                                                     | done   | as `StorageUnit-energy_balance`                                                                                                                                                        |
| [`StorageUnit-p_set`](#storageunit-p_set), [`{c}-{attr}_set`](#generator-p_set)                     | done   | `Generator-p_set`, `Link-p_set`, `StorageUnit-state_of_charge_set`, `Store-e_set` and `Line-s_set` here, and `Store-p_set`, `StorageUnit-p_dispatch_set` and `-p_store_set` in rung 37 |
| [`marginal_cost_storage`, `spill_cost`](#objective)                                                 | done   |                                                                                                                                                                                        |

Rung 60 extends the `StorageUnit-energy_balance` row. Rung 76 extends the
`Store-energy_balance` row and adds the bounds of `Store-p` and `Store-p_store`.

<!-- reference:rung_02_storage:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `4456.659315422356`, 111 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_02_storage.py`

```python
"""Rung 2: storage — a cyclic battery, an inflow reservoir with a set state of charge, and a store."""

from __future__ import annotations

from math import nan

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.generators_t.marginal_cost['gas'] = [15, 15, 60, 60]
    n.add(
        'StorageUnit',
        'battery',
        bus='south',
        p_nom=20,
        max_hours=4,
        efficiency_store=0.95,
        efficiency_dispatch=0.9,
        standing_loss=0.01,
        cyclic_state_of_charge=True,
        marginal_cost=0.5,
        p_set=[0, nan, nan, nan],
    )
    n.add(
        'StorageUnit',
        'reservoir',
        bus='south',
        p_nom=10,
        max_hours=2,
        spill_cost=2,
        state_of_charge_initial=5,
        marginal_cost_storage=0.1,
        inflow=[12, 12, 12, 12],
        state_of_charge_set=[nan, nan, nan, 10],
    )
    n.add(
        'Store',
        'cavern',
        bus='south',
        e_nom=40,
        e_initial=25,
        standing_loss=0.005,
        marginal_cost=0.2,
        e_set=[nan, nan, nan, 20],
    )
    return n
```

</details>
<!-- reference:rung_02_storage:end -->

### Rung 3 — expansion

| PyPSA                                                     | status | note                                                                                                  |
| --------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| [`{c}-p_nom`, `-s_nom`, `-e_nom`](#variable-domains)      | done   | `{c}_p_nom_ext` for an extendable build, the parameter for a fixed build                              |
| [`{c}-ext-{attr}-lower/upper`](#generator-ext-p-lower)    | done   |                                                                                                       |
| [`{c}-ext-p_nom-lower/upper`](#generator-ext-p_nom-lower) | done   |                                                                                                       |
| [`{c}-p_nom_set`](#generator-p_nom_set)                   | done   |                                                                                                       |
| [`Generator-e_sum_min/max`](#generator-e_sum_min)         | done   |                                                                                                       |
| [capital cost](#objective)                                | done   | `periodized_cost` from data prep: `capital_cost`, or the annuity of `overnight_cost`, plus `fom_cost` |

<!-- reference:rung_03_expansion:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7633.908502024292`, 200 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_03_expansion.py`

```python
"""Rung 3: expansion — extendable capacity, energy-sum bounds, fixed and set nominal capacities."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'island')
    n.add('Carrier', 'onwind')
    n.add('Carrier', 'solarpv')
    n.add('Carrier', 'dc')
    n.add('Carrier', 'phs')
    n.add('Carrier', 'h2')
    n.add(
        'Generator',
        'wind',
        bus='north',
        carrier='onwind',
        p_nom_extendable=True,
        capital_cost=50,
        p_nom_min=5,
        p_nom_max=80,
        marginal_cost=0,
        e_sum_min=40,
        ramp_limit_up=0.4,
        ramp_limit_down=0.4,
        p_max_pu=[0.3, 0.8, 0.5, 0.9],
    )
    n.add(
        'Generator',
        'solar',
        bus='north',
        carrier='solarpv',
        p_nom_extendable=True,
        capital_cost=60,
        p_nom_max=40,
        marginal_cost=0,
        p_nom_set=15,
        p_max_pu=[0.5, 0.6, 0.4, 0.2],
    )
    n.add('Generator', 'diesel', bus='island', marginal_cost=40, p_nom=60, e_sum_max=70)
    n.add(
        'Link',
        'cable',
        bus0='north',
        bus1='island',
        carrier='dc',
        length=120,
        p_nom_extendable=True,
        capital_cost=20,
        p_nom_max=30,
        efficiency=0.95,
        p_nom_set=25,
        ramp_limit_up=0.3,
        ramp_limit_down=0.3,
    )
    n.add('Load', 'island_load', bus='island', p_set=10)
    n.add(
        'StorageUnit',
        'pump',
        bus='north',
        carrier='phs',
        p_nom_extendable=True,
        capital_cost=15,
        p_nom_max=30,
        max_hours=4,
        efficiency_store=0.9,
        efficiency_dispatch=0.9,
        cyclic_state_of_charge=True,
        p_nom_set=20,
    )
    n.add('StorageUnit', 'ice', bus='island', max_hours=2, p_nom=8, state_of_charge_initial=6)
    n.add(
        'Store',
        'tank',
        bus='north',
        carrier='h2',
        e_nom_extendable=True,
        capital_cost=2,
        e_nom_max=80,
        e_cyclic=True,
        e_nom_set=50,
    )
    n.add('Store', 'keg', bus='island', e_nom=15, e_initial=5)
    n.add(
        'GlobalConstraint',
        'tech_wind',
        type='tech_capacity_expansion_limit',
        carrier_attribute='onwind',
        sense='==',
        constant=50,
    )
    n.add(
        'GlobalConstraint',
        'tech_solar',
        type='tech_capacity_expansion_limit',
        carrier_attribute='solarpv',
        sense='>=',
        constant=10,
    )
    n.add(
        'GlobalConstraint',
        'tech_dc',
        type='tech_capacity_expansion_limit',
        carrier_attribute='dc',
        sense='<=',
        constant=28,
    )
    n.add(
        'GlobalConstraint',
        'tech_phs',
        type='tech_capacity_expansion_limit',
        carrier_attribute='phs',
        sense='<=',
        constant=25,
    )
    n.add(
        'GlobalConstraint',
        'tech_h2',
        type='tech_capacity_expansion_limit',
        carrier_attribute='h2',
        sense='>=',
        constant=30,
    )
    n.add(
        'GlobalConstraint',
        'vol_dc',
        type='transmission_volume_expansion_limit',
        carrier_attribute='dc',
        sense='<=',
        constant=3500,
    )
    n.add(
        'GlobalConstraint',
        'cost_dc',
        type='transmission_expansion_cost_limit',
        carrier_attribute='dc',
        sense='>=',
        constant=400,
    )
    n.add(
        'GlobalConstraint',
        'cost_dc_exact',
        type='transmission_expansion_cost_limit',
        carrier_attribute='dc',
        sense='==',
        constant=500,
    )
    return n
```

</details>
<!-- reference:rung_03_expansion:end -->

### Rung 4 — ramps

The build, the allowance and the output carried into a snapshot are each a
quantity stated with `cases:`. A fixed, an extendable and a committed unit
therefore share one entry. A missing limit is the full build. Rung 8 adds the rows of an
extendable committed unit, which use a large constant bound (big-M).

| PyPSA                                                    | status | note                                         |
| -------------------------------------------------------- | ------ | -------------------------------------------- |
| [`{c}-p-ramp_limit_up/down`](#generator-p-ramp_limit_up) | done   | a lone start-up or shut-down ramp in rung 28 |

Rungs 45 and 46 extend these rows.

<!-- reference:rung_04_ramps:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `8785.0`, 64 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_04_ramps.py`

```python
"""Rung 4: ramps — ramp limits on fixed and extendable generators and links."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'east')
    n.add('Generator', 'coal_slow', bus='north', p_nom=80, marginal_cost=8, ramp_limit_up=0.2, ramp_limit_down=0.2)
    n.add('Link', 'tie', bus0='north', bus1='east', p_nom=50, efficiency=1, ramp_limit_up=0.4, ramp_limit_down=0.4)
    n.add('Load', 'east_load', bus='east', p_set=[5, 20, 25, 10])
    n.add('Load', 'swing', bus='north', p_set=[0, 25, 45, 0])
    return n
```

</details>
<!-- reference:rung_04_ramps:end -->

### Rung 5 — global constraints

PyPSA names every global constraint row `GlobalConstraint-{name}`. The type and
the comparator are data. A sense from data is a
[limit](../about/limits.md) of the language (#70). The file states each type as
three entries, one per sense.

| PyPSA type                                                                    | status | note                                                                                                       |
| ----------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy)                                           | split  | an entry per sense, with carrier weights from data prep, one period in rung 35 and per scenario in rung 40 |
| [`operational_limit`](#operational_limit)                                     | split  | an entry per sense, one period in rung 35, per scenario in rung 40                                         |
| [`transmission_volume_expansion_limit`](#transmission_volume_expansion_limit) | split  | an entry per sense, membership from PyPSA's carrier string in data prep, per scenario in rung 40           |
| [`transmission_expansion_cost_limit`](#transmission_expansion_cost_limit)     | split  | an entry per sense, with the cost as the `capital_cost` property, without `fom_cost`                       |
| [`tech_capacity_expansion_limit`](#tech_capacity_expansion_limit)             | split  | an entry per sense                                                                                         |
| `Bus-nom_min/max_{carrier}`                                                   | out    | deprecated in PyPSA                                                                                        |

Rung 60 extends the `primary_energy` row. Rung 15 states the
`Carrier-growth_limit` row, and rung 21 extends it to every extendable
component.

<!-- reference:rung_05_global_constraints:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `10282.833333333334`, 110 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_05_global_constraints.py`

```python
"""Rung 5: global constraints — one row per limit type and sense."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Carrier', 'coalc', co2_emissions=0.9)
    n.add('Carrier', 'gasc', co2_emissions=0.4)
    n.add('Carrier', 'windc')
    n.add('Generator', 'coal5', bus='north', carrier='coalc', p_nom=60, marginal_cost=9, efficiency=0.35)
    n.add('Generator', 'gas5', bus='north', carrier='gasc', p_nom=60, marginal_cost=25, efficiency=0.5)
    n.add('Generator', 'wind5', bus='north', carrier='windc', p_nom=60, marginal_cost=40)
    n.add('Load', 'extra5', bus='north', p_set=50)
    n.add('StorageUnit', 'res5', bus='north', carrier='gasc', p_nom=20, max_hours=4, state_of_charge_initial=30)
    n.add('Store', 'tank5', bus='north', carrier='coalc', e_nom=40, e_initial=25)
    n.add(
        'GlobalConstraint',
        'co2_cap',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='<=',
        constant=150,
    )
    n.add(
        'GlobalConstraint',
        'co2_floor',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='>=',
        constant=20,
    )
    n.add(
        'GlobalConstraint',
        'co2_exact',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='==',
        constant=120,
    )
    n.add('GlobalConstraint', 'op_wind', type='operational_limit', carrier_attribute='windc', sense='==', constant=30)
    n.add('GlobalConstraint', 'op_coal', type='operational_limit', carrier_attribute='coalc', sense='<=', constant=200)
    n.add('GlobalConstraint', 'op_gas', type='operational_limit', carrier_attribute='gasc', sense='>=', constant=10)
    return n
```

</details>
<!-- reference:rung_05_global_constraints:end -->

### Rung 6 — KVL

A line's flow obeys the Kirchhoff voltage law (KVL). Around every independent
cycle of the network, the flows times their series impedance sum to zero. The
set of independent cycles (the cycle basis) is data, which you compute in data
prep.

| PyPSA                                                              | status | note                                  |
| ------------------------------------------------------------------ | ------ | ------------------------------------- |
| [`Line-s`](#variable-domains), [`Line-fix-s-*`](#line-fix-s-lower) | done   | the ext and nominal rows as in rung 3 |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law)                  | done   | the cycle basis from data prep        |

Rungs 60 and 66 extend the `Kirchhoff-Voltage-Law` row.

<!-- reference:rung_06_kvl:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `23962.0`, 123 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_06_kvl.py`

```python
"""Rung 6: KVL — passive lines under Kirchhoff's voltage law."""

from __future__ import annotations

from math import nan

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'a')
    n.add('Bus', 'b')
    n.add('Bus', 'c')
    n.add('Generator', 'hydro', bus='a', p_nom=80, marginal_cost=10)
    n.add('Generator', 'diesel6', bus='b', p_nom=80, marginal_cost=50)
    n.add('Load', 'town', bus='c', p_set=45)
    n.add('Line', 'ab', bus0='a', bus1='b', carrier='AC', length=30, x=0.1, r=0.01, s_nom=60)
    n.add('Line', 'bc', bus0='b', bus1='c', carrier='AC', length=40, x=0.2, r=0.01, s_nom=60, s_set=[16, nan, nan, nan])
    n.add('Line', 'ca', bus0='c', bus1='a', carrier='AC', length=35, x=0.1, r=0.01, s_nom=60)
    n.add(
        'Line',
        'ca2',
        bus0='c',
        bus1='a',
        carrier='AC',
        length=50,
        x=0.15,
        r=0.01,
        s_nom_extendable=True,
        capital_cost=10,
        s_nom_max=40,
        s_nom_set=30,
    )
    n.add(
        'Line',
        'ca3',
        bus0='c',
        bus1='a',
        carrier='AC',
        length=80,
        x=0.12,
        r=0.01,
        s_nom_extendable=True,
        capital_cost=8,
        s_nom_max=40,
    )
    n.add(
        'GlobalConstraint',
        'vol_ac',
        type='transmission_volume_expansion_limit',
        carrier_attribute='AC',
        sense='==',
        constant=2300,
    )
    n.add(
        'GlobalConstraint',
        'vol_ac_floor',
        type='transmission_volume_expansion_limit',
        carrier_attribute='AC',
        sense='>=',
        constant=1000,
    )
    n.add(
        'GlobalConstraint',
        'cost_ac',
        type='transmission_expansion_cost_limit',
        carrier_attribute='AC',
        sense='<=',
        constant=500,
    )
    n.add(
        'GlobalConstraint',
        'cost_ac_floor',
        type='transmission_expansion_cost_limit',
        carrier_attribute='AC',
        sense='>=',
        constant=100,
    )
    n.add(
        'GlobalConstraint',
        'tech_ac',
        type='tech_capacity_expansion_limit',
        carrier_attribute='AC',
        sense='<=',
        constant=60,
    )
    return n
```

</details>
<!-- reference:rung_06_kvl:end -->

### Rung 7 — commitment

| PyPSA                                                                                           | status | note                                                                                                                                                                          |
| ----------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-status`, `-start_up`, `-shut_down`](#variable-domains)                                    | done   | Generator, with Link in rung 25 and Process in rung 26                                                                                                                        |
| [`{c}-com-p-lower/upper`](#generator-com-p-lower)                                               | done   | not for a modular build, which takes `com-mod-p-*` (PyPSA/PyPSA#1901)                                                                                                         |
| [`{c}-*-p-fixed-upper`](#generator-status-p-fixed-upper)                                        | done   | status, start and stop each at most one, as explicit rows                                                                                                                     |
| [`{c}-com-transition-start-up/shut-down`](#generator-com-transition-start-up)                   | done   | the carried-in state stated with `cases:`, no entry for the first snapshot, and zero carried in for a unit built in a later period (rung 64)                                  |
| [`{c}-com-up-time`, `-down-time`](#generator-com-up-time)                                       | done   | [`sum_back`](../reference/language/operators.md#sum_back)`(window=min_up_time)` from the first snapshot. The up or down time brought in counts as a start or a stop before it, from data prep (rung 24). A modular unit's down time counts modules |
| [`stand_by_cost`, `start_up_cost`, `shut_down_cost`](#objective)                                | done   | the period weight and no snapshot weight on a start or a stop (rung 48), and a cost that may change per snapshot (rung 62)                                                                |
| [`{c}-com-p-before/-current/-partly-*`](pypsa_linearized_uc.md)                                 | done   | under `linearized_unit_commitment`, in a file laid over this one ([a patch](../reference/glossary.md#patch)): rungs 12, 44, 47 and 74 for Generator, rung 67 for Link and Process |

<!-- reference:rung_07_commitment:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7775.0`, 118 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_07_commitment.py`

```python
"""Rung 7: commitment — committable units with up and down times and ramp limits at the transitions."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add(
        'Generator',
        'uc',
        bus='north',
        committable=True,
        p_nom=50,
        marginal_cost=5,
        p_min_pu=0.4,
        min_up_time=3,
        min_down_time=2,
        up_time_before=1,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        ramp_limit_start_up=0.6,
        ramp_limit_shut_down=0.6,
        start_up_cost=100,
        shut_down_cost=50,
        stand_by_cost=5,
    )
    n.add(
        'Generator',
        'cold',
        bus='south',
        committable=True,
        p_nom=30,
        marginal_cost=60,
        p_min_pu=0.3,
        min_up_time=2,
        min_down_time=1,
        up_time_before=0,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        start_up_cost=80,
    )
    n.add('Load', 'swing7', bus='north', p_set=[25, 45, 45, 10])
    return n
```

</details>
<!-- reference:rung_07_commitment:end -->

### Rung 8 — modular and big-M

| PyPSA                                                                  | status | note                                                                                                                                                                  |
| ---------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-n_mod`, `{c}-p_nom_modularity`](#generator-p_nom_modularity)     | done   | Generator, Link and Process, and none for a build that is active in no snapshot (rung 63)                                                                             |
| [`{c}-*-p_nom-variable-upper`](#generator-status-p_nom-variable-upper) | done   | a modular unit is on only where a module is built                                                                                                                     |
| [`{c}-*-p-fixed-upper`, modular](#generator-status-p-fixed-upper)      | done   | the cap as the whole count of modules, `p_nom / p_nom_mod` from data prep, also for a fixed build such as `array` (#123), a fractional count in [Refusals](#refusals) |
| [`{c}-com-mod-p-lower/upper`](#generator-com-mod-p-lower)              | done   | one module's share times the status, for a fixed build too, in place of the `com-p-*` rows (PyPSA/PyPSA#1901)                                                         |
| [`{c}-com-ext-p-*` (big-M)](#generator-com-ext-p-upper-cap)            | done   | a cap row beside a big-M row, with `M` from data prep, PyPSA's rule for an infinite build cap included (rung 64)                                                      |
| [`{c}-com-ext-p-lower-nonneg`](#generator-com-ext-p-lower-nonneg)      | done   | `(p_min_pu >= 0).all()` from data prep                                                                                                                                |
| [`{c}-p-ramp_limit_*-bigM`](#generator-p-ramp_limit_up-run-bigm)       | done   | run and start rows up, run and shut rows down, each over the carried-in output stated with `cases:`, and the ordinary rows for a modular build (rung 27)              |

<!-- reference:rung_08_modular_big_m:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `15915.0`, 183 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_08_modular_big_m.py`

```python
"""Rung 8: modular and big-M — capacity in whole modules, built or already standing, and a committable unit whose capacity is also built."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'mill')
    n.add(
        'Generator',
        'block',
        bus='mill',
        p_nom_extendable=True,
        committable=True,
        p_nom_mod=25,
        p_nom_max=100,
        capital_cost=30,
        marginal_cost=20,
        p_min_pu=0.2,
        up_time_before=0,
    )
    n.add(
        'Generator',
        'flex',
        bus='mill',
        p_nom_extendable=True,
        committable=True,
        p_nom_max=80,
        capital_cost=50,
        marginal_cost=10,
        p_min_pu=0.3,
        up_time_before=0,
        ramp_limit_up=0.25,
        ramp_limit_down=0.25,
    )
    n.add(
        'Generator',
        'sink',
        bus='mill',
        p_nom_extendable=True,
        committable=True,
        p_nom_max=30,
        capital_cost=40,
        marginal_cost=15,
        p_min_pu=-0.2,
        up_time_before=0,
    )
    n.add(
        'Generator',
        'array',
        bus='mill',
        committable=True,
        p_nom=90,
        p_nom_mod=30,
        marginal_cost=12,
        p_min_pu=0.2,
        up_time_before=0,
    )
    n.add('Load', 'mill_load', bus='mill', p_set=[40, 80, 120, 60])
    return n
```

</details>
<!-- reference:rung_08_modular_big_m:end -->

### Rung 9 — multi-link

| PyPSA                                           | status | note                                                                                               |
| ----------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| [nodal balance, ports 1..n](#bus-nodal_balance) | done   | one term over `link_output`, so a link of any number of output ports needs no further entry (#124) |

<!-- reference:rung_09_multilink:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `11714.4`, 92 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_09_multilink.py`

```python
"""Rung 9: a multi-link with four output ports — power and heat sold, waste heat vented, and a station service the link draws back."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'gasb')
    n.add('Bus', 'power')
    n.add('Bus', 'heat')
    n.add('Bus', 'flue')
    n.add('Bus', 'aux')
    n.add('Generator', 'well', bus='gasb', p_nom=100, marginal_cost=5)
    n.add('Generator', 'grid_import', bus='power', p_nom=50, marginal_cost=60)
    n.add('Generator', 'vent', bus='flue', p_nom=100, p_min_pu=-1, p_max_pu=0)
    n.add('Generator', 'aux_supply', bus='aux', p_nom=10, marginal_cost=2)
    n.add(
        'Link',
        'chp',
        bus0='gasb',
        bus1='power',
        bus2='heat',
        bus3='flue',
        bus4='aux',
        efficiency=0.4,
        efficiency2=0.45,
        efficiency3=0.1,
        efficiency4=-0.02,
        p_nom=60,
        marginal_cost=1,
    )
    n.add('Load', 'homes', bus='power', p_set=20)
    n.add('Load', 'district', bus='heat', p_set=18)
    return n
```

</details>
<!-- reference:rung_09_multilink:end -->

### Rung 10 — quadratic costs

The PyPSA `marginal_cost_quadratic` is a marginal cost that is quadratic in
output. It adds one squared cost per component to the objective, and weights
each snapshot by the hours the snapshot weighs. Here a generator and a link
have it, and rung 36 puts it on a process, a storage unit and a store. On a
plain run, it is zero, so the squared cost is zero and the objective stays
linear.

| PyPSA                                   | status | note                                             |
| --------------------------------------- | ------ | ------------------------------------------------ |
| [`marginal_cost_quadratic`](#objective) | done   | degree 2 in the objective, on Generator and Link |

<!-- reference:rung_10_quadratic_costs:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `12587.437500000098`, 60 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_10_quadratic_costs.py`

```python
"""Rung 10: quadratic costs — a marginal cost quadratic in output."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'village')
    n.add('Generator', 'steam', bus='north', p_nom=80, marginal_cost=5, marginal_cost_quadratic=0.08)
    n.add('Generator', 'engine', bus='north', p_nom=80, marginal_cost=20, marginal_cost_quadratic=0.01)
    n.add(
        'Link',
        'wire2',
        bus0='north',
        bus1='village',
        p_nom=40,
        p_min_pu=-1,
        efficiency=0.9,
        marginal_cost=1,
        marginal_cost_quadratic=0.02,
    )
    n.add('Load', 'village_load', bus='village', p_set=15)
    n.add('Load', 'extra10', bus='north', p_set=[30, 50, 40, 60])
    return n
```

</details>
<!-- reference:rung_10_quadratic_costs:end -->

### Rung 11 — ac-dc-meshed

This rung is the whole `ac_dc_meshed` example of PyPSA. It has meshed
alternating-current (AC) and direct-current (DC) networks, extendable lines,
links and generators, carriers and a CO2 budget. It has the rows of rungs 1, 3,
5 and 6 together, and it is the first rung with an objective constant.

<!-- reference:rung_11_ac_dc_meshed:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `-3474256.0405499237`, 468 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_11_ac_dc_meshed.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 11: PyPSA's own `ac_dc_meshed` example, whole — meshed AC and DC, extendable lines, links and generators, carriers, a CO2 budget."""

from __future__ import annotations

from datetime import datetime

#: Ten hourly stamps, the example's own. Every weighting column there is 1.0, which is
#: also the default, so no row below sets one.
SNAPSHOTS = [datetime(2015, 1, 1, hour) for hour in range(10)]

#: Wind availability per snapshot, for the three generators that carry a profile.
P_MAX_PU = {
    'Manchester Wind': [0.930019875, 0.4857475804, 0.2336917351, 0.2576042221, 0.6269055694, 0.6035984088, 0.6789075462, 0.3613026112, 0.6216040549, 0.5215183715],
    'Norway Wind': [0.9745832033, 0.4812903778, 0.4072258018, 0.5999649628, 0.524468219, 0.0096927054, 0.2204533621, 0.8239185004, 0.5562297265, 0.4394160378],
    'Frankfurt Wind': [0.5590784039, 0.7529103711, 0.1234650887, 0.9666766524, 0.8590078044, 0.5261537924, 0.077893008, 0.0590234716, 0.2485544952, 0.1080601728],
}  # fmt: skip

#: Demand per snapshot, for each of the six loads.
P_SET = {
    'London': [35.7962441027, 976.8245614698, 250.5873120464, 130.7531445827, 151.1001686, 931.857051942, 289.8482871447, 864.3433217147, 689.5772637703, 627.8789859434],
    'Frankfurt': [398.0478469638, 432.4361062425, 379.8039282662, 868.3617642835, 548.7707546221, 828.6652426012, 449.2907519075, 699.1637663734, 915.8667802518, 414.8876464034],
    'Norway': [820.035835936, 854.8340468618, 42.550744351, 647.5482327851, 884.0738733306, 509.0624485516, 595.6079648147, 291.6424496984, 2.1534925491, 760.7401765038],
    'Norwich': [415.4625642653, 262.6061464526, 418.4763531902, 552.9595393098, 218.159858091, 791.9762655836, 531.8706808219, 23.5134667186, 970.0590684572, 0.9248336907],
    'Bremen': [640.0863775411, 703.554333706, 440.8361303183, 612.5763056818, 803.4367808051, 605.4006873582, 641.0905902397, 408.0085411725, 912.2477761646, 898.0530916423],
    'Manchester': [857.5514402011, 750.5996237166, 156.5648760141, 527.8708221189, 83.8977589634, 676.6233193474, 731.1371004827, 553.3448891847, 298.338082262, 768.2905859888],
}  # fmt: skip


def build():
    """The example network, stated as the calls that build it.

    A rung states its data inline, so that the PyPSA model under review is the
    script — ``reference.py`` says so and ``test_pypsa_references.py`` checks
    it. The numbers here are PyPSA's own ``ac_dc_meshed``, which is where this
    rung's published objective comes from; ``reference.py`` pins the version
    they were read at.
    """
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(SNAPSHOTS)
    # Bus
    n.add('Bus', 'London', v_nom=380.0, x=-0.13, y=51.5)
    n.add('Bus', 'Norwich', v_nom=380.0, x=1.3, y=52.6)
    n.add('Bus', 'Norwich DC', v_nom=200.0, x=1.3, y=52.5, carrier='DC')
    n.add('Bus', 'Manchester', v_nom=380.0, x=-2.2, y=53.47)
    n.add('Bus', 'Bremen', v_nom=380.0, x=8.8, y=53.08)
    n.add('Bus', 'Bremen DC', v_nom=200.0, x=8.8, y=52.98, carrier='DC')
    n.add('Bus', 'Frankfurt', v_nom=380.0, x=8.7, y=50.12)
    n.add('Bus', 'Norway', v_nom=380.0, x=10.75, y=60.0)
    n.add('Bus', 'Norway DC', v_nom=200.0, x=10.75, y=60.0, carrier='DC')
    # Carrier
    n.add('Carrier', 'gas', co2_emissions=0.24, color='red')
    n.add('Carrier', 'wind', color='blue')
    n.add('Carrier', 'battery', color='green')
    n.add('Carrier', 'load', color='black')
    n.add('Carrier', 'AC', color='orange')
    n.add('Carrier', 'DC', color='purple')
    # Generator
    n.add(
        'Generator',
        'Manchester Wind',
        bus='Manchester',
        p_nom=80.0,
        p_nom_extendable=True,
        p_nom_min=100.0,
        p_max_pu=P_MAX_PU['Manchester Wind'],
        carrier='wind',
        marginal_cost=0.11,
        capital_cost=2793.6516029328,
    )
    n.add(
        'Generator',
        'Manchester Gas',
        bus='Manchester',
        p_nom=50000.0,
        p_nom_extendable=True,
        carrier='gas',
        marginal_cost=4.5323676307,
        capital_cost=196.6151679691,
        efficiency=0.3500264336,
    )
    n.add(
        'Generator',
        'Norway Wind',
        bus='Norway',
        p_nom=100.0,
        p_nom_extendable=True,
        p_nom_min=100.0,
        p_max_pu=P_MAX_PU['Norway Wind'],
        carrier='wind',
        marginal_cost=0.09,
        capital_cost=2184.3747960912,
    )
    n.add(
        'Generator',
        'Norway Gas',
        bus='Norway',
        p_nom=20000.0,
        p_nom_extendable=True,
        carrier='gas',
        marginal_cost=5.8928445406,
        capital_cost=158.2512497168,
        efficiency=0.3568363832,
    )
    n.add(
        'Generator',
        'Frankfurt Wind',
        bus='Frankfurt',
        p_nom=110.0,
        p_nom_extendable=True,
        p_nom_min=100.0,
        p_max_pu=P_MAX_PU['Frankfurt Wind'],
        carrier='wind',
        marginal_cost=0.1,
        capital_cost=2129.4561224763,
    )
    n.add(
        'Generator',
        'Frankfurt Gas',
        bus='Frankfurt',
        p_nom=80000.0,
        p_nom_extendable=True,
        carrier='gas',
        marginal_cost=4.0863219899,
        capital_cost=102.6769530076,
        efficiency=0.3516658529,
    )
    # Line
    n.add(
        'Line',
        '0',
        bus0='London',
        bus1='Manchester',
        x=0.7968782824,
        s_nom=40000.0,
        s_nom_extendable=True,
        capital_cost=0.1367157553,
        carrier='AC',
    )
    n.add(
        'Line',
        '1',
        bus0='Manchester',
        bus1='Norwich',
        x=0.3915599178,
        s_nom=40000.0,
        s_nom_extendable=True,
        capital_cost=0.1334916779,
        carrier='AC',
    )
    n.add(
        'Line',
        '2',
        bus0='Bremen DC',
        bus1='Norwich DC',
        r=0.2126041927,
        s_nom=40000.0,
        s_nom_extendable=True,
        capital_cost=0.0086734246,
        carrier='AC',
    )
    n.add(
        'Line',
        '3',
        bus0='Norwich DC',
        bus1='Norway DC',
        r=0.4861637504,
        s_nom=40000.0,
        s_nom_extendable=True,
        capital_cost=0.1291260515,
        carrier='AC',
    )
    n.add(
        'Line',
        '4',
        bus0='Norway DC',
        bus1='Bremen DC',
        r=0.4287266497,
        s_nom=40000.0,
        s_nom_extendable=True,
        capital_cost=0.0624298729,
        carrier='AC',
    )
    n.add(
        'Line',
        '5',
        bus0='Norwich',
        bus1='London',
        x=0.2388003463,
        s_nom=40000.0,
        s_nom_extendable=True,
        capital_cost=0.0218524519,
        carrier='AC',
    )
    n.add(
        'Line',
        '6',
        bus0='Bremen',
        bus1='Frankfurt',
        x=0.4,
        s_nom=40000.0,
        s_nom_extendable=True,
        capital_cost=0.2,
        carrier='AC',
    )
    # Link
    n.add(
        'Link',
        'Norwich Converter',
        bus0='Norwich',
        bus1='Norwich DC',
        carrier='DC',
        p_nom=1000.0,
        p_nom_extendable=True,
        p_min_pu=-0.9,
        p_max_pu=0.9,
        capital_cost=0.21,
    )
    n.add(
        'Link',
        'Norway Converter',
        bus0='Norway',
        bus1='Norway DC',
        carrier='DC',
        p_nom=1000.0,
        p_nom_extendable=True,
        p_min_pu=-0.9,
        p_max_pu=0.9,
        capital_cost=0.2,
    )
    n.add(
        'Link',
        'Bremen Converter',
        bus0='Bremen',
        bus1='Bremen DC',
        carrier='DC',
        p_nom=1000.0,
        p_nom_extendable=True,
        p_min_pu=-0.9,
        p_max_pu=0.9,
        capital_cost=0.19,
    )
    n.add(
        'Link',
        'DC link',
        bus0='London',
        bus1='Bremen',
        carrier='DC',
        p_nom=1000.0,
        p_nom_extendable=True,
        p_min_pu=-0.9,
        p_max_pu=0.9,
        capital_cost=0.8765342,
    )
    # Load
    n.add('Load', 'London', bus='London', carrier='load', p_set=P_SET['London'])
    n.add('Load', 'Frankfurt', bus='Frankfurt', carrier='load', p_set=P_SET['Frankfurt'])
    n.add('Load', 'Norway', bus='Norway', carrier='load', p_set=P_SET['Norway'])
    n.add('Load', 'Norwich', bus='Norwich', carrier='load', p_set=P_SET['Norwich'])
    n.add('Load', 'Bremen', bus='Bremen', carrier='load', p_set=P_SET['Bremen'])
    n.add('Load', 'Manchester', bus='Manchester', carrier='load', p_set=P_SET['Manchester'])
    # GlobalConstraint
    n.add('GlobalConstraint', 'co2_limit', sense='<=', constant=1000.0)
    return n
```

</details>
<!-- reference:rung_11_ac_dc_meshed:end -->

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

| PyPSA                                                                                                                                                                         | status | note                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| [`Line-loss`, `Transformer-loss`](#variable-domains)                                                                                                                          | done   | absent, and zero in the balance, where lossless                                                                      |
| [`Line-fix-s-*`, `Line-ext-s-*`](#line-fix-s-lower), [`Transformer-fix-s-*`, `Transformer-ext-s-*`](#transformer-fix-s-lower)                                                 | done   | the loss counted against the rating                                                                                  |
| [`Bus-nodal_balance`](#bus-nodal_balance)                                                                                                                                     | done   | half of each incident line's and transformer's loss at either end                                                    |
| [`Line-loss_upper`](#line-loss_upper), [`Transformer-loss_upper`](#transformer-loss_upper)                                                                                    | done   | `loss_max` from data prep, and its refusals in [Refusals](#refusals)                                                 |
| [`Line-loss_tangents-{k}-1`](#line-loss_tangents-k-1), [`Transformer-loss_tangents-{k}-1`](#transformer-loss_tangents-k-1)                                                    | split  | a row per segment in PyPSA, one entry over `segment` in the file                                                     |
| [`Line-loss_tangents-{k}--1`](#line-loss_tangents-k--1), [`Transformer-loss_tangents-{k}--1`](#transformer-loss_tangents-k--1)                                                | split  |                                                                                                                      |
| [`Line-loss_secants-pos`, `Line-loss_secants-neg`](#line-loss_tangents-k-1), [`Transformer-loss_secants-pos`, `Transformer-loss_secants-neg`](#transformer-loss_tangents-k-1) | done   | the same two entries in the secant mode, with slope, offset and the breakpoint loop from data prep (rungs 19 and 23) |

<!-- reference:rung_13_losses:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `10645.295879552297`, 150 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_13_losses.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 13: transmission losses in tangent form — a loss per line."""

from __future__ import annotations

import spine

OPTIMIZE = {'transmission_losses': {'mode': 'tangents', 'segments': 2}}


def build():
    """The spine plus a 110 kV triangle of lines, one of them extendable — ohms a real line has, so the loss stays a few percent of the flow."""
    n = spine.build()
    n.add('Bus', ['a', 'b', 'c'], v_nom=110)
    n.add('Generator', 'hydro13', bus='a', p_nom=80, marginal_cost=10)
    n.add('Generator', 'diesel13', bus='b', p_nom=80, marginal_cost=50)
    n.add('Line', 'ab13', bus0='a', bus1='b', carrier='AC', x=30, r=6, s_nom=60)
    n.add('Line', 'bc13', bus0='b', bus1='c', carrier='AC', x=60, r=9.7, s_nom=60)
    n.add(
        'Line',
        'ca13',
        bus0='c',
        bus1='a',
        carrier='AC',
        x=45,
        r=6,
        s_nom=40,
        s_nom_extendable=True,
        s_nom_max=90,
        capital_cost=4,
    )
    n.add('Load', 'town13', bus='c', p_set=[35, 55, 15, 45])
    return n
```

</details>
<!-- reference:rung_13_losses:end -->

### Rung 19 — transmission losses in secant form

Rung 19 is rung 13's network in the secant mode. It has the same loss rows, but
PyPSA's tolerance loop places the cuts, not one cut per segment.

<!-- reference:rung_19_losses_secants:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `10840.926895402912`, 150 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_19_losses_secants.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 19: transmission losses in secant form — the same loss per line, its cuts placed by PyPSA's tolerance loop."""

from __future__ import annotations

import spine

OPTIMIZE = {'transmission_losses': {'mode': 'secants', 'atol': 1, 'rtol': 0.1, 'max_segments': 20}}


def build():
    """Rung 13's 110 kV triangle, unchanged, so the two modes differ only in the cuts."""
    n = spine.build()
    n.add('Bus', ['a', 'b', 'c'], v_nom=110)
    n.add('Generator', 'hydro19', bus='a', p_nom=80, marginal_cost=10)
    n.add('Generator', 'diesel19', bus='b', p_nom=80, marginal_cost=50)
    n.add('Line', 'ab19', bus0='a', bus1='b', carrier='AC', x=30, r=6, s_nom=60)
    n.add('Line', 'bc19', bus0='b', bus1='c', carrier='AC', x=60, r=9.7, s_nom=60)
    n.add(
        'Line',
        'ca19',
        bus0='c',
        bus1='a',
        carrier='AC',
        x=45,
        r=6,
        s_nom=40,
        s_nom_extendable=True,
        s_nom_max=90,
        capital_cost=4,
    )
    n.add('Load', 'town19', bus='c', p_set=[35, 55, 15, 45])
    return n
```

</details>
<!-- reference:rung_19_losses_secants:end -->

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

| PyPSA                                                                                          | status | note                                                                                                                                        |
| ---------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| [`Generator-p`, `Link-p`](#variable-domains)                                                   | done   | over `scenario`, except `Generator-p_nom`, which is chosen once                                                                             |
| [`Generator-fix-p-*`, `-ext-p-*`, `Link-fix-p-*`, `Bus-nodal_balance`](#generator-fix-p-lower) | done   | rungs 1 and 3, over `scenario`                                                                                                              |
| [`CVaR-a`, `CVaR-theta`, `CVaR`](#variable-domains)                                            | done   |                                                                                                                                             |
| [`CVaR-excess-{s}`](#cvar-excess-s)                                                            | split  | a row per scenario in PyPSA, one entry over `scenario` in the file, none without a risk preference                                          |
| [`CVaR-def`](#cvar-def)                                                                        | done   | `1 / (1 - alpha)` from data prep, none without a risk preference                                                                            |
| [objective](#objective)                                                                        | done   | capacity once, at its capital cost in expectation over the scenarios, and operation at `(1 - omega)` in expectation and `omega` at the tail |
| [`Generator-fix-p-*`](#generator-fix-p-lower) and the other rows over component data           | done   | data per scenario, such as `p_max_pu`, with operating data in rung 41, first-stage bounds and capital cost in rung 42                       |

<!-- reference:rung_14_stochastic:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `9267.386666666665`, 87 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_14_stochastic.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 14: two futures and a risk preference — capacity chosen once, dispatch per scenario."""

from __future__ import annotations

import spine


def build():
    """The spine plus an extendable wind unit whose availability and the south's load differ between a calm and a stormy future."""
    n = spine.build()
    n.add('Generator', 'wind14', bus='south', p_nom_extendable=True, p_nom_max=100, marginal_cost=1, capital_cost=20)
    n.add('Load', 'port14', bus='south')
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    n.c.loads.dynamic.p_set[('calm', 'port14')] = [10, 20, 15, 10]
    n.c.loads.dynamic.p_set[('stormy', 'port14')] = [40, 60, 50, 30]
    n.c.generators.dynamic.p_max_pu[('calm', 'wind14')] = [0.9, 0.7, 0.8, 0.6]
    n.c.generators.dynamic.p_max_pu[('stormy', 'wind14')] = [0.3, 0.2, 0.4, 0.1]
    n.set_risk_preference(alpha=0.5, omega=0.3)
    return n
```

</details>
<!-- reference:rung_14_stochastic:end -->

### Rung 15 — investment periods

This rung runs `n.optimize(multi_investment_periods=True)`, where each snapshot
belongs to an investment period. An asset is active in the periods that its
build year and lifetime span. Its capacity is paid once per period that it is
active in. Each period has a weight, and a carrier may grow only so much per
period. The snapshots an asset is active in are the parameter `{c}_active`,
from data prep.

| PyPSA                                                                     | status | note                                                                                                                           |
| ------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| [`Generator-p`](#variable-domains)                                        | done   | where the generator is active in the snapshot's period, by `active` from data prep                                             |
| [`Generator-fix-p-*`, `-ext-p-*`, `-ext-p_nom-*`](#generator-fix-p-lower) | done   | rungs 1 and 3, where `active` is true                                                                                          |
| [`Carrier-growth_limit`](#carrier-growth_limit)                           | done   | every extendable component of the carrier, counted in the first period a build is active in, with `edge=0` at the first period |
| [objective](#objective)                                                   | done   | period weight on operation, capacity once per period it is active in                                                           |

Rungs 29, 32, 35, 38, 39, 49 and 66 extend these rows.

<!-- reference:rung_15_multi_period:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `12747.19109626398`, 80 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_15_multi_period.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 15: two investment periods — build years, lifetimes, period weights and a carrier's growth limit."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods, a unit that retires, two wind builds capped by growth."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0, 2.0, 1.5, 2.5, 2.0]
    n.add('Bus', ['north', 'south'])
    n.add('Carrier', 'wind', max_growth=50, max_relative_growth=0.5)
    n.add('Carrier', 'gas')
    n.add('Generator', 'old_gas', bus='north', carrier='gas', p_nom=40, marginal_cost=30, build_year=2010, lifetime=15)
    n.add(
        'Generator',
        'wind20',
        bus='north',
        carrier='wind',
        p_nom_extendable=True,
        p_nom_max=200,
        marginal_cost=1,
        capital_cost=100,
        build_year=2020,
        lifetime=30,
        p_max_pu=[0.8, 0.6, 0.7, 0.5, 0.8, 0.6, 0.7, 0.5],
    )
    n.add(
        'Generator',
        'wind30',
        bus='south',
        carrier='wind',
        p_nom_extendable=True,
        p_nom_max=200,
        marginal_cost=1,
        capital_cost=80,
        build_year=2030,
        lifetime=30,
        p_max_pu=[0.9, 0.7, 0.6, 0.8, 0.9, 0.7, 0.6, 0.8],
    )
    n.add(
        'Generator',
        'gas30',
        bus='south',
        carrier='gas',
        p_nom_extendable=True,
        p_nom_max=200,
        marginal_cost=40,
        capital_cost=50,
        build_year=2030,
        lifetime=30,
    )
    n.add('Link', 'wire15', bus0='north', bus1='south', p_nom=60, p_min_pu=-1, efficiency=0.95)
    n.add('Load', 'town15', bus='north', p_set=[20, 30, 25, 20, 35, 45, 40, 30])
    n.add('Load', 'port15', bus='south', p_set=[10, 20, 15, 10, 30, 40, 35, 25])
    return n
```

</details>
<!-- reference:rung_15_multi_period:end -->

### Rung 16 — link delay

A source feeds two sinks over links whose energy arrives late. With the PyPSA
`delay`, a port delivers a number of snapshots late. `cyclic_delay` sets what
happens to flow still in transit at the end of the horizon: it wraps to the
start, or it is lost. The delay is a number per link and the wrap a kind per
link. The balance states them with `cases:` over a
[`shift`](../reference/language/operators.md#shift) by
`offset=Link_output_delay`. One case wraps (`edge='wrap'`),
and the other vacates (`edge=0`).

This is the only rung with a uniform `generators` weighting, and PyPSA measures
`delay` in units of that weighting. With a uniform weighting, a delay of `n` is
a shift of exactly `n` snapshot positions, which a positional `shift` gives.
With a weighting that is not uniform, PyPSA resamples by elapsed time, not by
position. A `shift` that varies along the snapshot axis is a
[limit](../about/limits.md) of the language (#299). The file states an
[assumption](../reference/language/assumptions.md),
[`Link_output_delay_under_uniform_weighting`](#link_output_delay_under_uniform_weighting),
and a tool refuses such a delay when data is attached.

| PyPSA                                              | status | note                                                                                       |
| -------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------ |
| [link `delay`, `cyclic_delay`](#bus-nodal_balance) | done   | a `cases:` on `cyclic_delay` over `shift(offset=delay)`, at uniform `generators` weighting |

<!-- reference:rung_16_link_delay:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `5262.5`, 52 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_16_link_delay.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 16: link delay — a source feeding two sinks over links whose energy arrives late, one wrapping cyclically and one losing what is still in transit at the horizon's edge."""

from __future__ import annotations

from datetime import datetime

#: Four hourly stamps. The `generators` weighting is uniform here, and only here
#: on the ladder, because PyPSA measures `delay` in those units: a uniform column
#: makes a delay of `n` a shift of exactly `n` snapshot positions, which is what a
#: positional `shift(offset=n)` reproduces. The `objective` and `stores` columns
#: stay non-uniform, so no cost or storage factor passes as identity.
SNAPSHOTS = [datetime(2015, 1, 1, hour) for hour in range(4)]
WEIGHTINGS = {'objective': [2.0, 1.5, 2.5, 3.0], 'stores': [0.5, 2.0, 1.5, 2.5], 'generators': [1.0, 1.0, 1.0, 1.0]}

#: Each sink carries the same demand, so the only thing that separates their cost
#: is how each link treats the horizon's edge.
DEMAND = [20.0, 15.0, 25.0, 10.0]


def build():
    """A source, two delayed links, and two sinks, stated as the calls that build it.

    ``pipe_wrap`` delays by two snapshots and wraps cyclically, so every unit the
    cheap source sends reaches its sink and the expensive backup stays dark.
    ``pipe_lose`` delays by one and does not wrap, so the flow that would arrive
    in the first snapshot is lost and that snapshot's demand falls to the backup.
    The two links differ in both a per-link number (`delay`) and a per-link kind
    (`cyclic_delay`), which is what the spec's ``cases:`` turns on.
    """
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(SNAPSHOTS)
    for column, values in WEIGHTINGS.items():
        n.snapshot_weightings[column] = values
    n.add('Bus', 'source')
    n.add('Bus', 'sink_wrap')
    n.add('Bus', 'sink_lose')
    n.add('Generator', 'spring', bus='source', p_nom=200, marginal_cost=5)
    n.add('Generator', 'backup_wrap', bus='sink_wrap', p_nom=200, marginal_cost=100)
    n.add('Generator', 'backup_lose', bus='sink_lose', p_nom=200, marginal_cost=100)
    n.add('Link', 'pipe_wrap', bus0='source', bus1='sink_wrap', p_nom=100, delay=2, cyclic_delay=True)
    n.add('Link', 'pipe_lose', bus0='source', bus1='sink_lose', p_nom=100, delay=1, cyclic_delay=False)
    n.add('Load', 'load_wrap', bus='sink_wrap', p_set=DEMAND)
    n.add('Load', 'load_lose', bus='sink_lose', p_set=DEMAND)
    return n
```

</details>
<!-- reference:rung_16_link_delay:end -->

### Rung 17 — process

A process is a generalised converter that moves an internal power from `bus0`
to the buses it feeds. Each port draws or delivers at its own `rate`. A
non-extendable process has a fixed capacity, and an extendable one chooses its
capacity between `p_nom_min` and `p_nom_max`. A ramp limit caps the change in
internal power between snapshots. A `p_set` fixes an internal power schedule,
and a `p_nom_set` fixes the built capacity of an extendable process. The rows
are those of the generator and the link, applied to a converter.

| PyPSA                                                                 | status | note                                                             |
| --------------------------------------------------------------------- | ------ | ---------------------------------------------------------------- |
| [`Process-p`, `Process-p_nom`](#variable-domains)                     | done   | internal power and capacity, as a link                           |
| [`Process-fix-p-*`, `-ext-p-*`, `-ext-p_nom-*`](#process-fix-p-lower) | done   | rungs 1 and 3, over a converter                                  |
| [`Process-p-ramp_limit_*`](#process-p-ramp_limit_up)                  | done   | rung 4, on a non-committable converter, and committed in rung 26 |
| [`Process-p_set`](#process-p_set)                                     | done   | a fixed internal power schedule                                  |
| [`Process-p_nom_set`](#process-p_nom_set)                             | done   | a fixed built capacity                                           |
| [`Bus-nodal_balance`](#bus-nodal_balance)                             | done   | each port enters at its `rate`                                   |
| [objective](#objective)                                               | done   | marginal cost on internal power, and capital cost on capacity    |

<!-- reference:rung_17_process:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `9730.0`, 70 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_17_process.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 17: process — generalized converters, one fixed and ramping, one extendable, one on a set schedule, all feeding a hub."""

from __future__ import annotations

from math import nan

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'hub')
    n.add(
        'Process',
        'conv_fix',
        bus0='north',
        bus1='hub',
        p_nom=50,
        marginal_cost=2,
        ramp_limit_up=0.3,
        ramp_limit_down=0.3,
    )
    n.add(
        'Process',
        'conv_ext',
        bus0='south',
        bus1='hub',
        p_nom_extendable=True,
        capital_cost=20,
        p_nom_min=5,
        p_nom_max=40,
        marginal_cost=1,
        p_nom_set=25,
    )
    n.add('Process', 'conv_set', bus0='north', bus1='hub', p_nom=20, marginal_cost=3, p_set=[10, nan, nan, nan])
    n.add('Load', 'hub_load', bus='hub', p_set=[15, 20, 25, 10])
    return n
```

</details>
<!-- reference:rung_17_process:end -->

### Rung 18 — transformer

A transformer is a passive branch between two buses, as a line is. Its flow
follows its effective series reactance and a phase shift, which is fixed or
optimised. It obeys KVL around every independent cycle, and a transformer in no
cycle has no KVL row. A non-extendable transformer has a fixed nominal apparent
power, and an extendable one chooses it between `s_nom_min` and `s_nom_max`. An
`s_set` fixes a flow schedule, and an `s_nom_set` fixes the built capacity of
an extendable transformer.

| PyPSA                                                                         | status | note                                      |
| ----------------------------------------------------------------------------- | ------ | ----------------------------------------- |
| [`Transformer-s`, `Transformer-s_nom`](#variable-domains)                     | done   | flow and capacity, as a line              |
| [`Transformer-fix-s-*`, `-ext-s-*`, `-ext-s_nom-*`](#transformer-fix-s-lower) | done   | rungs 1 and 3, over a transformer         |
| [`Transformer-s_set`](#transformer-s_set)                                     | done   | a fixed flow schedule                     |
| [`Transformer-s_nom_set`](#transformer-s_nom_set)                             | done   | a fixed built capacity                    |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law)                             | done   | rung 6, over `x_pu_eff` and a phase shift |
| [`Transformer-phase_shift`](#variable-domains)                                | done   | rung 20, an optimised phase shift         |
| [objective](#objective)                                                       | done   | capital on capacity                       |

<!-- reference:rung_18_transformer:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `12274.401472395122`, 106 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_18_transformer.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 18: transformer — passive branches under KVL in a meshed triangle, one fixed and on a set flow, two extendable in parallel."""

from __future__ import annotations

from math import nan

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'a')
    n.add('Bus', 'b')
    n.add('Bus', 'c')
    n.add('Generator', 'hydro18', bus='a', p_nom=80, marginal_cost=10)
    n.add('Generator', 'diesel18', bus='b', p_nom=80, marginal_cost=50)
    n.add('Load', 'town18', bus='c', p_set=45)
    n.add('Line', 'ab', bus0='a', bus1='b', carrier='AC', length=30, x=0.1, r=0.01, s_nom=60)
    n.add(
        'Transformer',
        'bc',
        bus0='b',
        bus1='c',
        x=0.1,
        r=0.01,
        s_nom=60,
        phase_shift=10,
        s_set=[16, nan, nan, nan],
    )
    n.add(
        'Transformer',
        'ca',
        bus0='c',
        bus1='a',
        x=0.15,
        r=0.01,
        s_nom=60,
        s_nom_extendable=True,
        capital_cost=10,
        s_nom_min=5,
        s_nom_max=40,
        s_nom_set=30,
        tap_ratio=1.05,
    )
    n.add(
        'Transformer',
        'ca2',
        bus0='c',
        bus1='a',
        x=0.12,
        r=0.01,
        s_nom=60,
        s_nom_extendable=True,
        capital_cost=8,
        s_nom_min=5,
        s_nom_max=40,
    )
    return n
```

</details>
<!-- reference:rung_18_transformer:end -->

### Rung 20 — phase shifter

Where the `phase_shift_min` of a phase-shifting transformer is below its
`phase_shift_max`, its voltage angle shift is a decision per snapshot. The shift
lies between the two bounds, in degrees. It enters the same KVL cycle sum as a
fixed one, so it redistributes the flows around a cycle without moving active
power. In this rung, with the shift, the transformer runs at its rating while
the upstream unit serves the whole load as the load varies. The decided shift replaces
the fixed `phase_shift`.

<!-- reference:rung_20_phase_shifter:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `16455.0`, 88 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_20_phase_shifter.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 20: phase shifter — a transformer whose per-snapshot phase shift is optimised, holding it at its rating and rerouting the surplus around the cycle.

The parallel lines carry low reactance, so a few degrees of shift move tens of
megawatts: the phase-shifting transformer keeps its flow at its ``s_nom`` while
the upstream hydro serves the whole varying load, and the costly local unit
stays off. A fixed shift could not follow the load, so the shift is a decision.
"""

from __future__ import annotations

import spine


def build():
    """The spine plus a triangle where a phase-shifting transformer reroutes cheap power around a binding leg, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', ['a', 'b', 'c'])
    n.add('Generator', 'hydro20', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel20', bus='c', p_nom=300, marginal_cost=200)
    n.add('Load', 'town20', bus='c', p_set=[90, 75, 120, 105])
    n.add('Line', 'ab20', bus0='a', bus1='b', carrier='AC', x=0.002, r=0.0002, s_nom=120)
    n.add('Line', 'bc20', bus0='b', bus1='c', carrier='AC', x=0.002, r=0.0002, s_nom=120)
    n.add(
        'Transformer',
        'ca20',
        bus0='c',
        bus1='a',
        x=0.002,
        r=0.0002,
        s_nom=40,
        phase_shift_min=-30,
        phase_shift_max=30,
    )
    return n
```

</details>
<!-- reference:rung_20_phase_shifter:end -->

### Rung 21 — carrier growth

The `max_growth` of a carrier caps what the carrier adds in an investment
period. The cap covers every extendable component of that carrier, not only
the generators. Here a battery carrier caps a storage unit and a store built in
the first period, and the two builds fill the cap together. A store built in the
later period adds its allowance plus half of what the carrier added before.
PyPSA counts only the components that have a carrier attribute, and the file
states the same sum, so a transformer counts in no carrier.

<!-- reference:rung_21_carrier_growth:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `8452.5`, 86 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_21_carrier_growth.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 21: a carrier's growth limit binds its non-generator builds — a storage unit and two stores over two periods."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: cheap solar only at the first snapshot of each period, so battery capacity pays off but its growth is capped."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0]
    n.add('Bus', 'grid')
    n.add('Carrier', 'solar')
    n.add('Carrier', 'gas')
    n.add('Carrier', 'battery', max_growth=20, max_relative_growth=0.5)
    n.add('Generator', 'solar', bus='grid', carrier='solar', p_nom=100, marginal_cost=1, p_max_pu=[1, 0, 1, 0])
    n.add('Generator', 'backup', bus='grid', carrier='gas', p_nom=200, marginal_cost=80)
    n.add(
        'StorageUnit',
        'bat20',
        bus='grid',
        carrier='battery',
        p_nom_extendable=True,
        p_nom_max=100,
        max_hours=4,
        capital_cost=50,
        build_year=2020,
        lifetime=30,
    )
    n.add(
        'Store',
        'tank20',
        bus='grid',
        carrier='battery',
        e_nom_extendable=True,
        e_nom_max=10,
        capital_cost=10,
        build_year=2020,
        lifetime=30,
    )
    n.add(
        'Store',
        'tank30',
        bus='grid',
        carrier='battery',
        e_nom_extendable=True,
        e_nom_max=100,
        capital_cost=8,
        build_year=2030,
        lifetime=30,
    )
    n.add('Load', 'town', bus='grid', p_set=[40, 60, 40, 80])
    return n
```

</details>
<!-- reference:rung_21_carrier_growth:end -->

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

<!-- reference:rung_22_transformer_losses:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `10643.477135410736`, 174 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_22_transformer_losses.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 22: transformer losses in tangent form — a loss per transformer, as per line."""

from __future__ import annotations

import spine

OPTIMIZE = {'transmission_losses': {'mode': 'tangents', 'segments': 3}}


def build():
    """The spine plus a triangle of one 110 kV line and two transformers, one extendable and off-nominal tap, per-unit resistances a real transformer has, so its loss stays a few percent of the flow."""
    n = spine.build()
    n.add('Bus', ['a', 'b', 'c'], v_nom=110)
    n.add('Generator', 'hydro22', bus='a', p_nom=80, marginal_cost=10)
    n.add('Generator', 'diesel22', bus='b', p_nom=80, marginal_cost=50)
    n.add('Line', 'ab22', bus0='a', bus1='b', carrier='AC', x=30, r=6, s_nom=60)
    n.add('Transformer', 'bc22', bus0='b', bus1='c', x=0.1, r=0.03, s_nom=60)
    n.add(
        'Transformer',
        'ca22',
        bus0='c',
        bus1='a',
        x=0.12,
        r=0.02,
        s_nom=40,
        s_nom_extendable=True,
        s_nom_max=90,
        capital_cost=4,
        tap_ratio=1.05,
    )
    n.add('Load', 'town22', bus='c', p_set=[35, 55, 15, 45])
    return n
```

</details>
<!-- reference:rung_22_transformer_losses:end -->

### Rung 23 — transformer losses in secant form

Rung 23 is rung 22's network in the secant mode. It has the same loss rows, but
PyPSA's tolerance loop places the cuts.

<!-- reference:rung_23_transformer_losses_secants:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `10821.999155213578`, 142 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_23_transformer_losses_secants.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 23: transformer losses in secant form — the same loss per transformer, its cuts placed by PyPSA's tolerance loop."""

from __future__ import annotations

import spine

OPTIMIZE = {'transmission_losses': {'mode': 'secants', 'atol': 1, 'rtol': 0.1, 'max_segments': 20}}


def build():
    """Rung 22's triangle, unchanged, so the two modes differ only in the cuts."""
    n = spine.build()
    n.add('Bus', ['a', 'b', 'c'], v_nom=110)
    n.add('Generator', 'hydro23', bus='a', p_nom=80, marginal_cost=10)
    n.add('Generator', 'diesel23', bus='b', p_nom=80, marginal_cost=50)
    n.add('Line', 'ab23', bus0='a', bus1='b', carrier='AC', x=30, r=6, s_nom=60)
    n.add('Transformer', 'bc23', bus0='b', bus1='c', x=0.1, r=0.03, s_nom=60)
    n.add(
        'Transformer',
        'ca23',
        bus0='c',
        bus1='a',
        x=0.12,
        r=0.02,
        s_nom=40,
        s_nom_extendable=True,
        s_nom_max=90,
        capital_cost=4,
        tap_ratio=1.05,
    )
    n.add('Load', 'town23', bus='c', p_set=[35, 55, 15, 45])
    return n
```

</details>
<!-- reference:rung_23_transformer_losses_secants:end -->

### Rung 24 — must stay down

A committable unit that stopped `down_time_before` snapshots before the horizon
stays off until its `min_down_time` has passed. PyPSA counts that stop in the
down-time row of the first `min_down_time - down_time_before` snapshots, which
holds the status at zero there. Here the cheapest
unit in the network brought one snapshot of a three-snapshot down time into the
horizon. It stays off for two snapshots, and the dearer coal unit serves the
load.

<!-- reference:rung_24_must_stay_down:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `9007.5`, 64 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_24_must_stay_down.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 24: must stay down — a committable unit still serving the down time it brought in stays off."""

from __future__ import annotations

import spine


def build():
    """The spine plus a cheap committable unit that stopped one snapshot before the horizon and must stay off for three."""
    n = spine.build()
    n.add(
        'Generator',
        'warm',
        bus='north',
        committable=True,
        p_nom=50,
        marginal_cost=5,
        p_min_pu=0.2,
        min_down_time=3,
        up_time_before=0,
        down_time_before=1,
        start_up_cost=20,
    )
    n.add('Load', 'swing24', bus='north', p_set=[25, 45, 45, 10])
    return n
```

</details>
<!-- reference:rung_24_must_stay_down:end -->

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

| PyPSA                                                                                                                  | status | note                                                                                |
| ---------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------- |
| [`Link-status`, `-start_up`, `-shut_down`, `-n_mod`](#variable-domains)                                                | done   | as the generator's, rungs 7 and 8                                                   |
| [`Link-com-p-*`, `-com-mod-p-*`, `-com-ext-p-*`](#link-com-p-lower)                                                    | done   | no `Link-fix-p-*` or `Link-ext-p-*` rows for a committable link, as for a generator |
| [`Link-*-p-fixed-upper`, `-*-p_nom-variable-upper`](#link-status-p-fixed-upper)                                        | done   |                                                                                     |
| [`Link-com-transition-*`, `-com-up-time`, `-com-down-time`](#link-com-transition-start-up)                             | done   |                                                                                     |
| [`Link-p-ramp_limit_*`, `-*-bigM`](#link-p-ramp_limit_up)                                                              | done   | the generator's allowance stated with `cases:`, and its big-M rows, over flow       |
| [`Link-p_nom_modularity`](#link-p_nom_modularity)                                                                      | done   |                                                                                     |
| [`stand_by_cost`, `start_up_cost`, `shut_down_cost`](#objective)                                                       | done   |                                                                                     |

<!-- reference:rung_25_committable_link:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `13982.0`, 227 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_25_committable_link.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 25: committable links — a link held on by the up time it brought in, one held off by its down time, one kept on by its own up time, and committable builds that are extendable, modular or both."""

from __future__ import annotations

import spine


def build():
    """The spine plus an east bus that only committable links serve."""
    n = spine.build()
    n.add('Bus', 'east')
    n.add(
        'Link',
        'hvdc',
        bus0='north',
        bus1='east',
        committable=True,
        p_nom=60,
        p_min_pu=0.3,
        marginal_cost=8,
        min_up_time=3,
        min_down_time=2,
        up_time_before=1,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        ramp_limit_start_up=0.6,
        ramp_limit_shut_down=0.6,
        start_up_cost=100,
        shut_down_cost=50,
        stand_by_cost=5,
    )
    n.add(
        'Link',
        'cold_tie',
        bus0='north',
        bus1='east',
        committable=True,
        p_nom=40,
        p_min_pu=0.2,
        min_up_time=2,
        min_down_time=3,
        up_time_before=0,
        down_time_before=1,
        start_up_cost=20,
    )
    n.add(
        'Link',
        'ext_tie',
        bus0='north',
        bus1='east',
        committable=True,
        p_nom_extendable=True,
        p_nom_max=30,
        capital_cost=5,
        p_min_pu=0.2,
        marginal_cost=2,
        up_time_before=0,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
    )
    n.add(
        'Link',
        'mod_tie',
        bus0='south',
        bus1='east',
        committable=True,
        p_nom_extendable=True,
        p_nom_mod=10,
        p_nom_max=40,
        capital_cost=3,
        p_min_pu=0.5,
    )
    n.add(
        'Link',
        'mod_fix',
        bus0='north',
        bus1='east',
        committable=True,
        p_nom=20,
        p_nom_mod=10,
        p_min_pu=0.5,
        marginal_cost=1,
    )
    n.add('Load', 'east_load', bus='east', p_set=[20, 70, 60, 5])
    return n
```

</details>
<!-- reference:rung_25_committable_link:end -->

### Rung 26 — committable processes

A committable process has the same unit commitment over its internal power
`p`. The status gates `p`, not a port, so every port follows the status at its
own `rate`. This rung states the links of rung 25 again as processes. Each
draws a quarter more from the north than it delivers to the east. The same
up and down time rules hold.

| PyPSA                                                                                                                        | status | note                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------- |
| [`Process-status`, `-start_up`, `-shut_down`, `-n_mod`](#variable-domains)                                                   | done   | as the link's, rung 25                                                                  |
| [`Process-com-p-*`, `-com-mod-p-*`, `-com-ext-p-*`](#process-com-p-lower)                                                    | done   | no `Process-fix-p-*` or `Process-ext-p-*` rows for a committable process                |
| [`Process-*-p-fixed-upper`, `-*-p_nom-variable-upper`](#process-status-p-fixed-upper)                                        | done   |                                                                                         |
| [`Process-com-transition-*`, `-com-up-time`, `-com-down-time`](#process-com-transition-start-up)                             | done   |                                                                                         |
| [`Process-p-ramp_limit_*`, `-*-bigM`](#process-p-ramp_limit_up)                                                              | done   | the generator's allowance stated with `cases:`, and its big-M rows, over internal power |
| [`Process-p_nom_modularity`](#process-p_nom_modularity)                                                                      | done   |                                                                                         |
| [`stand_by_cost`, `start_up_cost`, `shut_down_cost`](#objective)                                                             | done   |                                                                                         |

<!-- reference:rung_26_committable_process:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `15865.124999999998`, 227 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_26_committable_process.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 26: committable processes — rung 25's committable links restated as processes that draw a quarter more than they deliver."""

from __future__ import annotations

import spine


def build():
    """The spine plus an east bus that only committable processes serve."""
    n = spine.build()
    n.add('Bus', 'east')
    n.add(
        'Process',
        'warm_conv',
        bus0='north',
        bus1='east',
        rate0=-1.25,
        committable=True,
        p_nom=60,
        p_min_pu=0.3,
        marginal_cost=8,
        min_up_time=3,
        min_down_time=2,
        up_time_before=1,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        ramp_limit_start_up=0.6,
        ramp_limit_shut_down=0.6,
        start_up_cost=100,
        shut_down_cost=50,
        stand_by_cost=5,
    )
    n.add(
        'Process',
        'cold_conv',
        bus0='north',
        bus1='east',
        rate0=-1.25,
        committable=True,
        p_nom=40,
        p_min_pu=0.2,
        min_up_time=2,
        min_down_time=3,
        up_time_before=0,
        down_time_before=1,
        start_up_cost=20,
    )
    n.add(
        'Process',
        'ext_conv',
        bus0='north',
        bus1='east',
        rate0=-1.25,
        committable=True,
        p_nom_extendable=True,
        p_nom_max=30,
        capital_cost=5,
        p_min_pu=0.2,
        marginal_cost=2,
        up_time_before=0,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
    )
    n.add(
        'Process',
        'mod_conv',
        bus0='south',
        bus1='east',
        rate0=-1.25,
        committable=True,
        p_nom_extendable=True,
        p_nom_mod=10,
        p_nom_max=40,
        capital_cost=3,
        p_min_pu=0.5,
    )
    n.add(
        'Process',
        'mod_fix',
        bus0='north',
        bus1='east',
        rate0=-1.25,
        committable=True,
        p_nom=20,
        p_nom_mod=10,
        p_min_pu=0.5,
        marginal_cost=1,
    )
    n.add('Load', 'east_load', bus='east', p_set=[20, 70, 60, 5])
    return n
```

</details>
<!-- reference:rung_26_committable_process:end -->

### Rung 27 — modular ramps

A committable, extendable and modular unit gets no big-M ramp rows. PyPSA gives
it the ordinary `{c}-p-ramp_limit_*` rows of a committed unit, with one module
`p_nom_mod` in place of `p_nom`. The status counts the modules that are on, so
the allowance grows with each module. This rung has one such generator, link
and process on a peak bus. Each has a start-up and shut-down ramp of 0.6 and a
ramp limit of one half. The ramp rows are tight at the optimum at the rise and
at the fall of the load.

| PyPSA                                                                     | status | note                                                                                                                             |
| ------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-p-ramp_limit_up/down`, modular](#generator-p-ramp_limit_up)         | done   | the committed allowance over `p_nom_committed`, which is one module where the build is extendable and modular, `p_nom` otherwise |
| [`{c}-p-ramp_limit_*-bigM`, modular](#generator-p-ramp_limit_up-run-bigm) | done   | none for a modular build                                                                                                         |

<!-- reference:rung_27_modular_ramp:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `45469.49999999998`, 161 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_27_modular_ramp.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 27: modular ramps — a committable extendable modular unit ramps against one module through the ordinary ramp rows, not the big-M ones."""

from __future__ import annotations

import spine


def build():
    """The spine plus a peak bus served by a committable modular generator, link and process, each ramp-limited, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'peak')
    common = {
        'committable': True,
        'p_nom_extendable': True,
        'p_nom_mod': 20,
        'p_nom_max': 60,
        'capital_cost': 2,
        'p_min_pu': 0.2,
        'up_time_before': 0,
        'ramp_limit_up': 0.5,
        'ramp_limit_down': 0.5,
        'ramp_limit_start_up': 0.6,
        'ramp_limit_shut_down': 0.6,
    }
    n.add('Generator', 'mod_gen', bus='peak', marginal_cost=3, **common)
    n.add('Link', 'mod_link', bus0='north', bus1='peak', marginal_cost=4, **common)
    n.add('Process', 'mod_proc', bus0='south', bus1='peak', rate0=-1.25, marginal_cost=5, **common)
    n.add('Generator', 'peak_backup', bus='peak', p_nom=200, marginal_cost=500)
    n.add('Load', 'peak_load', bus='peak', p_set=[10, 90, 150, 20])
    return n
```

</details>
<!-- reference:rung_27_modular_ramp:end -->

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

| PyPSA                                                                                      | status | note                                                                                           |
| ------------------------------------------------------------------------------------------ | ------ | ---------------------------------------------------------------------------------------------- |
| [`{c}-p-ramp_limit_up/down`, start-up or shut-down ramp alone](#generator-p-ramp_limit_up) | done   | a `where:` on either limit, with a missing one as `1` in `ramp_up_rate` and its three siblings |

<!-- reference:rung_28_start_up_ramp:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `83282.99999999983`, 152 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_28_start_up_ramp.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 28: a start-up ramp alone — a committable unit with only a start-up and a shut-down ramp still gets ramp rows, at the full build between them."""

from __future__ import annotations

import spine


def build():
    """The spine plus a pulse bus served by committable generator, link and process that carry only start-up and shut-down ramps, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'pulse')
    common = {
        'committable': True,
        'p_nom': 40,
        'p_min_pu': 0.1,
        'up_time_before': 0,
        'ramp_limit_start_up': 0.4,
        'ramp_limit_shut_down': 0.5,
    }
    n.add('Generator', 'pulse_gen', bus='pulse', marginal_cost=3, **common)
    n.add('Link', 'pulse_link', bus0='north', bus1='pulse', marginal_cost=4, **common)
    n.add('Process', 'pulse_proc', bus0='south', bus1='pulse', rate0=-1.25, marginal_cost=5, **common)
    n.add('Generator', 'pulse_backup', bus='pulse', p_nom=200, marginal_cost=500)
    n.add('Load', 'pulse_load', bus='pulse', p_set=[0, 60, 110, 0])
    return n
```

</details>
<!-- reference:rung_28_start_up_ramp:end -->

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

| PyPSA                                                                                                                    | status | note                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance), [`Store-energy_balance`](#store-energy_balance), per period | done   | two more cases in the charge carried in: a `shift(…, edge='wrap', within=snapshot_period[period])` and the initial level where [`position()`](../reference/language/expressions.md#position) within `snapshot_period[period]` is `0` |
| [`{c}-p-ramp_limit_*`, `-bigM`, at a period start](#generator-p-ramp_limit_up)                                           | done   | a `where:` that is false at every period start but the horizon's first                                                                                                                                                               |

<!-- reference:rung_29_storage_per_period:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7438.461538461539`, 244 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_29_storage_per_period.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 29: storage per investment period — a storage unit and a store that cycle within each period, two that reopen on their initial level, and a ramp that restarts at a period start."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods, four storages that each close or reopen per period, a ramp-limited coal unit."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0, 2.0, 1.5, 2.5, 2.0]
    n.snapshot_weightings['stores'] = [0.5, 2.0, 1.5, 2.5, 0.5, 2.0, 1.5, 2.5]
    n.add('Bus', 'hub')
    n.add('Generator', 'coal29', bus='hub', p_nom=100, marginal_cost=10, ramp_limit_up=0.1, ramp_limit_down=0.1)
    n.add('Generator', 'peak29', bus='hub', p_nom=200, marginal_cost=[80, 20, 90, 30, 80, 20, 90, 30])
    n.add('StorageUnit', 'su_cycle', bus='hub', p_nom=15, max_hours=4, cyclic_state_of_charge_per_period=True)
    n.add(
        'StorageUnit',
        'su_reset',
        bus='hub',
        p_nom=15,
        max_hours=4,
        state_of_charge_initial=20,
        state_of_charge_initial_per_period=True,
    )
    n.add('Store', 'e_cycle', bus='hub', e_nom=30, e_cyclic_per_period=True)
    n.add('Store', 'e_reset', bus='hub', e_nom=30, e_initial=10, e_initial_per_period=True)
    n.add('Load', 'hub_load', bus='hub', p_set=[40, 60, 70, 40, 90, 110, 120, 90])
    return n
```

</details>
<!-- reference:rung_29_storage_per_period:end -->

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

| PyPSA                                                                                                                                                                                                        | status | note                                                                                                                           |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| [`Line-fix-s-*-security-for-{c}-outage-in-sub-network-{n}`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n), [`Line-ext-s-*-security-…`](#line-ext-s-lower-security-for-c-outage-in-sub-network-n) | split  | a row per outaged component and sub-network in PyPSA, one entry over the `outage` axis in the file                             |
| [`Transformer-fix-s-*-security-…`](#transformer-fix-s-lower-security-for-c-outage-in-sub-network-n), [`Transformer-ext-s-*-security-…`](#transformer-ext-s-lower-security-for-c-outage-in-sub-network-n)     | split  | the same for a transformer                                                                                                     |
| [`Line-fix-s-*-security-…`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n), [`Transformer-fix-s-*-security-…`](#transformer-fix-s-lower-security-for-c-outage-in-sub-network-n)                   | done   | none for a branch not active in a period, which has no factor there (rung 66)                                                  |
| [`Line-fix-s-*-security-…`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n), [`Transformer-fix-s-*-security-…`](#transformer-fix-s-lower-security-for-c-outage-in-sub-network-n)                   | done   | in each period, the factors of that period's own active branches (rung 68)                                                     |
| [`Line-fix-s-*-security-…`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n), [`Transformer-fix-s-*-security-…`](#transformer-fix-s-lower-security-for-c-outage-in-sub-network-n)                   | done   | over scenarios, the first scenario's factors, so `Line_BODF` spans no `scenario` (rung 56)                                     |
| `…-period-{p}` copies                                                                                                                                                                                        | split  | under `multi_investment_periods`, one entry over `snapshot`, each snapshot in one period                                       |
| [`Line-loss`, `Transformer-loss`](#variable-domains) and the relaxed commitment rows                                                                                                                         | done   | none in a security-constrained run, which has no `transmission_losses` or `linearized_unit_commitment`, and no rung of its own |

<!-- reference:rung_30_security_constrained:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `22113.333333333332`, 240 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_30_security_constrained.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 30: security-constrained — a meshed triangle of lines and two transformers, one extendable, that must carry their flow within their rating after any one of three outages."""

from __future__ import annotations

import pandas as pd
import spine

BRANCH_OUTAGES = pd.MultiIndex.from_tuples([('Line', 'ab'), ('Line', 'ca'), ('Transformer', 'ca_t')])


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'a')
    n.add('Bus', 'b')
    n.add('Bus', 'c')
    n.add('Generator', 'hydro30', bus='a', p_nom=100, marginal_cost=10)
    n.add('Generator', 'diesel30', bus='b', p_nom=100, marginal_cost=50)
    n.add('Generator', 'peak30', bus='c', p_nom=100, marginal_cost=200)
    n.add('Load', 'town30', bus='c', p_set=[40, 60, 80, 50])
    n.add('Line', 'ab', bus0='a', bus1='b', x=0.1, s_nom=60)
    n.add('Line', 'bc', bus0='b', bus1='c', x=0.1, s_nom=60, s_max_pu=0.9)
    n.add('Line', 'ca', bus0='c', bus1='a', x=0.1, s_nom_extendable=True, capital_cost=5, s_nom_max=200)
    n.add('Transformer', 'ca_t', bus0='c', bus1='a', x=0.2, s_nom=30)
    n.add('Transformer', 'bc_t', bus0='b', bus1='c', x=0.3, s_nom_extendable=True, capital_cost=3, s_nom_max=50)
    return n
```

</details>
<!-- reference:rung_30_security_constrained:end -->

### Rung 32 — storage that stands in one period only

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
[`StorageUnit_stands_in_one_run`](#storageunit_stands_in_one_run),
[`-opens_late_only_where_it_opens`](#storageunit_opens_late_only_where_it_opens)
and [`-opens_late_where_it_opens`](#storageunit_opens_late_where_it_opens) for
the storage unit. No assumption ties `{c}_inactive_snapshots` to the count of
inactive snapshots. A [`count`](../reference/language/expressions.md#count)
compared against a parameter is a
[limit](../about/limits.md#meaning-that-needs-data-or-code) of the language.

This rung's network has a cyclic store that retires after the 2020 period. A
cyclic storage unit and a store with an initial level of 5 open in the 2030
period. Without the opening rows, the level before 2030 would be absent, and
each storage would open on any level it chose. With them, the objective rises
to `7230.49`.

| PyPSA                                                                                                                                                      | status | note                                                                                                                                                                                  |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance), [`Store-energy_balance`](#store-energy_balance), at the first snapshot a storage is active in | done   | the `cyclic` and `opening` cases true at `position(snapshot) == 0` or at `{c}_opens_late`, the cyclic one shifting one snapshot and then `{c}_inactive_snapshots` more, `edge='wrap'` |

<!-- reference:rung_32_storage_later_period:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7230.4866975671375`, 108 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_32_storage_later_period.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 32: storage that stands in one period only — two built in the later period open at its first snapshot, and a cyclic one that retires closes on its own last snapshot."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods, two storages built in 2030, one cyclic store that retires after 2020."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0, 2.0, 1.5, 2.5, 2.0]
    n.snapshot_weightings['stores'] = [0.5, 2.0, 1.5, 2.5, 0.5, 2.0, 1.5, 2.5]
    n.add('Bus', 'hub')
    n.add('Generator', 'base32', bus='hub', p_nom=100, marginal_cost=10)
    n.add('Generator', 'peak32', bus='hub', p_nom=200, marginal_cost=[80, 20, 90, 30, 80, 20, 90, 30])
    n.add(
        'StorageUnit',
        'su_late',
        bus='hub',
        p_nom=15,
        max_hours=4,
        standing_loss=0.02,
        cyclic_state_of_charge=True,
        build_year=2030,
        lifetime=30,
    )
    n.add('Store', 'e_late', bus='hub', e_nom=30, e_initial=5, build_year=2030, lifetime=30)
    n.add('Store', 'e_retire', bus='hub', e_nom=30, standing_loss=0.01, e_cyclic=True, build_year=2020, lifetime=10)
    n.add('Load', 'hub_load', bus='hub', p_set=[40, 60, 70, 40, 90, 110, 120, 90])
    return n
```

</details>
<!-- reference:rung_32_storage_later_period:end -->

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
([a relation](../reference/language/relations.md)), `*_maintenance_cover`,
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

| PyPSA                                                                                                                                                                                                  | status | note                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | --------------------------------------------------- |
| [`Generator-maintenance`, `-maintenance_start`, `-maintenance_capacity`](#variable-domains), and the `Link` and `Process` ones                                                                         | done   | zero where the component is not maintainable        |
| [`Generator-maint-event-count`](#generator-maint-event-count), [`-maint-window`](#generator-maint-window), [`-maint-start-horizon`](#generator-maint-start-horizon), and the `Link` and `Process` ones | done   | the window and the blocked starts from data prep    |
| [`Generator-maintcap_*`](#generator-maintcap_upper), and the `Link` and `Process` ones                                                                                                                 | done   | `-maintcap_lower_nommin` only where `p_nom_min > 0` |
| [`Generator-fix-p-*`](#generator-fix-p-lower), [`-ext-p-*`](#generator-ext-p-lower), and the `Link` and `Process` ones, in maintenance                                                                 | done   | the bound less `maintenance_pu` of the build        |

<!-- reference:rung_33_maintenance:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7367.560185185185`, 179 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_33_maintenance.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 33: maintenance — a fixed and an extendable generator, link and process, each taken off for events that the generator weightings time."""

from __future__ import annotations

import spine


def build():
    """The spine plus an east bus and six maintainable components, fixed and extendable, with a dear peaker to cover them."""
    n = spine.build()
    n.add('Bus', 'east')
    n.add('Generator', 'hydro', bus='north', p_nom=50, marginal_cost=2, maintainable=True, maintenance_duration=3)
    n.add(
        'Generator',
        'wind_ext',
        bus='south',
        p_nom_extendable=True,
        p_nom_min=10,
        p_nom_max=60,
        capital_cost=20,
        marginal_cost=1,
        p_max_pu=[0.9, 0.6, 0.8, 0.7],
        maintainable=True,
        maintenance_duration=2,
        maintenance_pu=0.5,
    )
    n.add(
        'Link',
        'tie_fix',
        bus0='north',
        bus1='east',
        p_nom=30,
        efficiency=0.95,
        maintainable=True,
        maintenance_duration=1,
        maintenance_events=2,
    )
    n.add(
        'Link',
        'tie_ext',
        bus0='south',
        bus1='east',
        p_nom_extendable=True,
        p_nom_min=5,
        p_nom_max=40,
        capital_cost=4,
        efficiency=0.9,
        p_min_pu=-1,
        maintainable=True,
        maintenance_duration=3,
    )
    n.add(
        'Process',
        'conv_fix',
        bus0='north',
        bus1='east',
        rate0=-1.25,
        p_nom=25,
        maintainable=True,
        maintenance_duration=3,
        maintenance_pu=0.6,
    )
    n.add(
        'Process',
        'conv_ext',
        bus0='south',
        bus1='east',
        rate0=-1.25,
        p_nom_extendable=True,
        p_nom_min=5,
        p_nom_max=30,
        capital_cost=3,
        maintainable=True,
        maintenance_duration=1,
    )
    n.add('Generator', 'east_peak', bus='east', p_nom=100, marginal_cost=60)
    n.add('Load', 'east_load', bus='east', p_set=[50, 60, 40, 55])
    return n
```

</details>
<!-- reference:rung_33_maintenance:end -->

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

| PyPSA                                                                                                                                                                                                                                                      | status | note                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------- |
| [`Generator-maintenance_status`](#variable-domains), and the `Link` and `Process` ones                                                                                                                                                                     | done   |                                                                                                                              |
| [`Generator-maint-status-*`](#generator-maint-status-le-status), [`-maint-modstatus-*`](#generator-maint-modstatus-le-status), and the `Link` and `Process` ones                                                                                           | done   | `maint-status` for a fixed build that is not modular, `maint-modstatus` for a modular build, fixed or not (PyPSA/PyPSA#1901) |
| [`Generator-com-p-*`](#generator-com-p-lower), [`-com-mod-p-*`](#generator-com-mod-p-lower), [`-com-ext-p-lower`](#generator-com-ext-p-lower), [`-com-ext-p-upper-cap`](#generator-com-ext-p-upper-cap), and the `Link` and `Process` ones, in maintenance | done   |                                                                                                                              |

<!-- reference:rung_34_committable_maintenance:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `6420.048611111111`, 503 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_34_committable_maintenance.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 34: maintenance of committable units — a fixed, an extendable and a modular committable generator, link and process, each taken off for one event."""

from __future__ import annotations

import spine


def build():
    """The spine plus an east bus and nine maintainable committable components, with a dear peaker to cover them."""
    n = spine.build()
    n.add('Bus', 'east')
    committable = {'committable': True, 'maintainable': True}
    n.add(
        'Generator',
        'unit',
        bus='north',
        p_nom=60,
        p_min_pu=0.3,
        marginal_cost=5,
        start_up_cost=10,
        maintenance_duration=2,
        **committable,
    )
    n.add(
        'Generator',
        'unit_ext',
        bus='south',
        p_nom_extendable=True,
        p_nom_min=5,
        p_nom_max=50,
        capital_cost=10,
        p_min_pu=0.2,
        marginal_cost=4,
        maintenance_duration=3,
        maintenance_pu=0.5,
        **committable,
    )
    n.add(
        'Generator',
        'unit_mod',
        bus='south',
        p_nom_extendable=True,
        p_nom_mod=10,
        p_nom_max=30,
        capital_cost=8,
        p_min_pu=0.5,
        marginal_cost=3,
        maintenance_duration=1,
        **committable,
    )
    for component, ports in (('Link', {}), ('Process', {'rate0': -1.25})):
        n.add(
            component,
            f'{component.lower()}_unit',
            bus0='north',
            bus1='east',
            p_nom=40,
            p_min_pu=0.2,
            marginal_cost=1,
            maintenance_duration=2,
            **ports,
            **committable,
        )
        n.add(
            component,
            f'{component.lower()}_ext',
            bus0='south',
            bus1='east',
            p_nom_extendable=True,
            p_nom_min=5,
            p_nom_max=30,
            capital_cost=5,
            p_min_pu=0.2,
            maintenance_duration=3,
            maintenance_pu=0.5,
            **ports,
            **committable,
        )
        n.add(
            component,
            f'{component.lower()}_mod',
            bus0='north',
            bus1='east',
            p_nom_extendable=True,
            p_nom_mod=10,
            p_nom_max=20,
            capital_cost=3,
            p_min_pu=0.5,
            maintenance_duration=1,
            **ports,
            **committable,
        )
    n.add('Generator', 'east_peak', bus='east', p_nom=100, marginal_cost=60)
    n.add('Load', 'east_load', bus='east', p_set=[50, 60, 40, 55])
    return n
```

</details>
<!-- reference:rung_34_committable_maintenance:end -->

### Rung 35 — a global constraint for one investment period

This rung runs `n.optimize(multi_investment_periods=True)` with
`primary_energy` and `operational_limit` rows that name an `investment_period`.
PyPSA (`global_constraints.py:378-390`, `597-609`) sums such a row over the
snapshots of that period only, and over the whole horizon where the row names
none. Each snapshot (`:333`, `:636`) counts with its generator weighting times the
`years` weighting of its period. Storage closes in such a row as
follows:

- A storage unit or store that reopens per period closes at the last snapshot
  of each counted period, weighted by that period's years (`:488-491`,
  `:694-697`).
- One that carries its level across periods closes once, at the last counted
  snapshot that it is active in (`:474-477`, `:680-683`, rung 69).

The file states the counted snapshots as `GlobalConstraint_counts_snapshot`,
from data prep, and the years as `period_weight_years`. On a plain run, the
counted snapshots are all true and the years are one, so the rows collapse to
the standard ones.

This rung's network caps CO2 in 2030 alone and again over the horizon. It
limits a hydro carrier with a per-period storage unit and store in the 2020
period. The two periods weigh 5 and 10 years. With the same network and no
`investment_period`, PyPSA solves to `10675.0`.

| PyPSA                                                                                                     | status  | note                                                                                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit) over one investment period | done    | `GlobalConstraint_energy_weight`, zero outside the counted snapshots, with the years weighing each snapshot                                                                                                                  |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit) over one investment period | done    | the closing level of storage as `StorageUnit_closing_weight` and `Store_closing_weight`, at each counted period's last snapshot where the storage reopens per period, at the last counted snapshot it is active in otherwise |
| [`primary_energy`](#primary_energy) | refused | over storage that reopens per period, on a network with scenarios, in [Refusals](#refusals) |

<!-- reference:rung_35_period_global_constraints:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `4886.764705882353`, 171 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_35_period_global_constraints.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 35: a global constraint for one investment period — a CO2 cap on 2030 alone, one over the horizon, and a 2020 limit on a carrier with storage that reopens per period."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods of unequal years, two emitting units, a hydro carrier with a unit and storage."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [5.0, 10.0]
    n.snapshot_weightings['generators'] = [1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0]
    n.add('Carrier', 'coal35', co2_emissions=1.0)
    n.add('Carrier', 'gas35', co2_emissions=0.4)
    n.add('Carrier', 'hydro35')
    n.add('Bus', 'hub')
    n.add('Generator', 'coal35', bus='hub', carrier='coal35', p_nom=100, marginal_cost=10, efficiency=0.4)
    n.add('Generator', 'gas35', bus='hub', carrier='gas35', p_nom=100, marginal_cost=30, efficiency=0.5)
    n.add('Generator', 'clean35', bus='hub', p_nom=200, marginal_cost=60)
    n.add('Generator', 'river35', bus='hub', carrier='hydro35', p_nom=30, marginal_cost=5)
    n.add(
        'StorageUnit',
        'dam35',
        bus='hub',
        carrier='hydro35',
        p_nom=15,
        max_hours=4,
        state_of_charge_initial=20,
        state_of_charge_initial_per_period=True,
    )
    n.add('Store', 'pond35', bus='hub', carrier='hydro35', e_nom=30, e_initial=10, e_initial_per_period=True)
    n.add('Load', 'town35', bus='hub', p_set=[60, 80, 70, 50, 90, 110, 100, 80])
    n.add(
        'GlobalConstraint',
        'co2_2030',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='<=',
        constant=3500,
        investment_period=2030,
    )
    n.add(
        'GlobalConstraint',
        'co2_all',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='<=',
        constant=6000,
    )
    n.add(
        'GlobalConstraint',
        'hydro_2020',
        type='operational_limit',
        carrier_attribute='hydro35',
        sense='<=',
        constant=600,
        investment_period=2020,
    )
    return n
```

</details>
<!-- reference:rung_35_period_global_constraints:end -->

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

| PyPSA                                                                     | status  | note                                                   |
| ------------------------------------------------------------------------- | ------- | ------------------------------------------------------ |
| [`marginal_cost_quadratic`](#objective) on Process, StorageUnit and Store | done    | degree 2 in the objective, with no charge on `p_store` |
| [`marginal_cost_quadratic`](#objective)                                   | refused | under a risk preference, in [Refusals](#refusals)      |

<!-- reference:rung_36_quadratic_storage_process:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `19185.241281403858`, 92 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_36_quadratic_storage_process.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 36: quadratic costs on a process, a storage unit and a store — the storage unit pays on dispatch only, the store on its net power both ways."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Bus', 'hub')
    n.add('Process', 'conv36', bus0='north', bus1='hub', p_nom=60, marginal_cost=1, marginal_cost_quadratic=0.05)
    n.add(
        'StorageUnit',
        'battery36',
        bus='south',
        p_nom=20,
        max_hours=4,
        state_of_charge_initial=40,
        marginal_cost=0.5,
        marginal_cost_quadratic=[0.2, 0.1, 0.3, 0.1],
    )
    n.add('Store', 'tank36', bus='hub', e_nom=60, e_initial=20, marginal_cost_quadratic=0.4)
    n.add('Load', 'hub_load', bus='hub', p_set=[20, 45, 30, 50])
    n.add('Load', 'peak36', bus='south', p_set=[10, 40, 20, 60])
    return n
```

</details>
<!-- reference:rung_36_quadratic_storage_process:end -->

### Rung 37 — storage dispatch pinned to a schedule

PyPSA pins a store's power delivered to `p_set`. It pins a storage unit's
dispatch to `p_dispatch_set` and its charging to `p_store_set`, each on its
own. PyPSA builds a row only where a value is given and the storage is active.
On a plain run, the data has no value, so PyPSA builds no row.

The rung pins a store to deliver 10 in the first snapshot and to take 5 in the
last. It pins the dispatch of a storage unit in the first snapshot, and its
charging in the second. With the same network and no pins, PyPSA solves to
`5811.111111111111`.

| PyPSA                                                                                                                                             | status | note                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| [`Store-p_set`](#store-p_set), [`StorageUnit-p_dispatch_set`](#storageunit-p_dispatch_set), [`StorageUnit-p_store_set`](#storageunit-p_store_set) | done   | `where:` a value is given and the storage is active, as in PyPSA (`optimize.py:917`, `:922`, `constraints.py:2156-2220`) |

<!-- reference:rung_37_fixed_storage_dispatch:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `6395.833333333333`, 84 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_37_fixed_storage_dispatch.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 37: storage dispatch pinned — a store's power delivered, and a storage unit's dispatch and charging, each on its own schedule."""

from __future__ import annotations

from math import nan

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.generators_t.marginal_cost['gas'] = [15, 60, 15, 60]
    n.add('Store', 'tank37', bus='south', e_nom=40, e_initial=20, p_set=[10, nan, nan, -5])
    n.add(
        'StorageUnit',
        'battery37',
        bus='south',
        p_nom=20,
        max_hours=2,
        state_of_charge_initial=10,
        p_dispatch_set=[6, nan, nan, nan],
        p_store_set=[nan, 4, nan, nan],
    )
    return n
```

</details>
<!-- reference:rung_37_fixed_storage_dispatch:end -->

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
[`Link_output_delay_under_uniform_weighting`](#link_output_delay_under_uniform_weighting).
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

| PyPSA                                                                                | status | note                                                                                                                                              |
| ------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| [link and process `delay`, `cyclic_delay`](#bus-nodal_balance) per investment period | done   | `shift(offset=delay, within=snapshot_period[period])`, with `edge='wrap'` closing each period and `edge=0` vacating each period's first snapshots |

<!-- reference:rung_38_delay_per_period:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `12918.75`, 104 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_38_delay_per_period.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 38: delays per investment period — a link that wraps its delayed flow within each period, and a process that loses what is still in transit at each period's start."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}

#: The `generators` weighting is uniform, as on rung 16, so a delay of `n` is a
#: shift of exactly `n` positions. The `objective` column stays non-uniform.
WEIGHTINGS = {'objective': [2.0, 1.5, 2.5, 3.0, 2.0, 1.5, 2.5, 3.0], 'generators': [1.0] * 8}

#: Demand differs from snapshot to snapshot, so which snapshot a delayed flow is
#: read from changes what it costs.
DEMAND = [20.0, 15.0, 25.0, 10.0, 30.0, 35.0, 5.0, 40.0]


def build():
    """A whole network, not the spine: eight snapshots over two periods, a source, a delayed link and a delayed process.

    ``pipe_wrap`` delays by two snapshots and wraps cyclically, so the first two
    snapshots of each period read the last two of that same period, never the
    other period. ``conv_lose`` delays by one and does not wrap, so the first
    snapshot of each period, 2030 included, receives nothing and its demand falls
    to the backup. The source is capped, so where each delayed flow is read from
    decides how much of the backup runs.
    """
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    for column, values in WEIGHTINGS.items():
        n.snapshot_weightings[column] = values
    n.add('Bus', ['source', 'sink_wrap', 'sink_lose'])
    n.add('Generator', 'spring38', bus='source', p_nom=60, marginal_cost=5)
    n.add('Generator', 'backup_wrap38', bus='sink_wrap', p_nom=200, marginal_cost=100)
    n.add('Generator', 'backup_lose38', bus='sink_lose', p_nom=200, marginal_cost=100)
    n.add('Link', 'pipe_wrap', bus0='source', bus1='sink_wrap', p_nom=30, delay=2, cyclic_delay=True)
    n.add('Process', 'conv_lose', bus0='source', bus1='sink_lose', p_nom=30, delay1=1, cyclic_delay1=False)
    n.add('Load', 'load_wrap', bus='sink_wrap', p_set=DEMAND)
    n.add('Load', 'load_lose', bus='sink_lose', p_set=DEMAND)
    return n
```

</details>
<!-- reference:rung_38_delay_per_period:end -->

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

| PyPSA                                                                              | status | note                                                                                           |
| ---------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------- |
| [`Carrier-growth_limit`](#carrier-growth_limit), `max_relative_growth.clip(min=0)` | done   | `Carrier_relative_growth` is `Carrier_max_relative_growth` where it is positive, `0` otherwise |

<!-- reference:rung_39_negative_relative_growth:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `8600.0`, 56 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_39_negative_relative_growth.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 39: a negative relative growth adds nothing to a carrier's growth limit — PyPSA clips it at zero."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: a battery carrier with `max_relative_growth=-0.5` builds in both periods."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0]
    n.add('Bus', 'grid')
    n.add('Carrier', 'solar')
    n.add('Carrier', 'gas')
    n.add('Carrier', 'battery', max_growth=20, max_relative_growth=-0.5)
    n.add('Generator', 'solar', bus='grid', carrier='solar', p_nom=100, marginal_cost=1, p_max_pu=[1, 0, 1, 0])
    n.add('Generator', 'backup', bus='grid', carrier='gas', p_nom=200, marginal_cost=80)
    n.add(
        'Store',
        'tank20',
        bus='grid',
        carrier='battery',
        e_nom_extendable=True,
        e_nom_max=100,
        capital_cost=10,
        build_year=2020,
        lifetime=30,
    )
    n.add(
        'Store',
        'tank30',
        bus='grid',
        carrier='battery',
        e_nom_extendable=True,
        e_nom_max=100,
        capital_cost=8,
        build_year=2030,
        lifetime=30,
    )
    n.add('Load', 'town', bus='grid', p_set=[40, 60, 40, 80])
    return n
```

</details>
<!-- reference:rung_39_negative_relative_growth:end -->

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

| PyPSA                                                                                                                                                                                                | status | note                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit), [`transmission_volume_expansion_limit`](#transmission_volume_expansion_limit) with a constant and sense per scenario | done   | The file states `GlobalConstraint_constant` and `GlobalConstraint_sense` over `scenario`.                                                                                                    |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit), [`transmission_volume_expansion_limit`](#transmission_volume_expansion_limit)                                        | done   | PyPSA reads a `carrier_attribute` or `investment_period` per scenario (`global_constraints.py:815-822`). The file states the weights and `GlobalConstraint_counts_snapshot` over `scenario`. |

Rungs 52 and 53 extend these rows.

<!-- reference:rung_40_scenario_global_constraints:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `15106.666666666666`, 86 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_40_scenario_global_constraints.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 40: a global constraint takes its own constant and sense in each scenario."""

from __future__ import annotations

import spine

#: each scenario's own constant and sense, per row
PER_SCENARIO = {
    ('calm', 'volume40'): {'constant': 60},
    ('stormy', 'volume40'): {'constant': 20},
    ('calm', 'co2_40'): {'constant': 250, 'sense': '<='},
    ('stormy', 'co2_40'): {'constant': 200, 'sense': '=='},
}


def build():
    """The spine over two futures, with an extendable line under a volume limit and a CO2 row that differ by scenario."""
    n = spine.build()
    n.add('Carrier', 'AC')
    n.add('Carrier', 'coalc', co2_emissions=0.5)
    n.c.generators.static.loc['coal', 'carrier'] = 'coalc'
    n.add(
        'Line',
        'tie40',
        bus0='north',
        bus1='south',
        x=0.1,
        carrier='AC',
        length=2,
        s_nom_extendable=True,
        capital_cost=1,
    )
    n.add('Load', 'port40', bus='south', p_set=30)
    n.add(
        'GlobalConstraint',
        'volume40',
        type='transmission_volume_expansion_limit',
        carrier_attribute='AC',
        sense='<=',
        constant=60,
    )
    n.add(
        'GlobalConstraint', 'co2_40', type='primary_energy', carrier_attribute='co2_emissions', sense='<=', constant=250
    )
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    for row, values in PER_SCENARIO.items():
        for column, value in values.items():
            n.c.global_constraints.static.loc[row, column] = value
    return n
```

</details>
<!-- reference:rung_40_scenario_global_constraints:end -->

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

| PyPSA                                                                                                         | status  | note                                                                             |
| ------------------------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------------------- |
| [objective](#objective), [`Bus-nodal_balance`](#bus-nodal_balance) with a cost and an efficiency per scenario | done    | `Generator_marginal_cost` and `Link_efficiency` over `scenario`                  |
| [`Bus-nodal_balance`](#bus-nodal_balance)                                                                     | refused | a link `delay` or `cyclic_delay` that differs by scenario, [Refusals](#refusals) |

Rungs 55, 57 and 58 extend these rows.

<!-- reference:rung_41_scenario_operational_data:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `17964.0`, 96 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_41_scenario_operational_data.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 41: a unit's cost and a link's efficiency differ by scenario."""

from __future__ import annotations

import spine

#: each scenario's own value, per component and attribute
PER_SCENARIO = {
    ('calm', 'gas41'): {'marginal_cost': 20},
    ('stormy', 'gas41'): {'marginal_cost': 80},
    ('calm', 'wire41'): {'efficiency': 0.9},
    ('stormy', 'wire41'): {'efficiency': 0.6},
}


def build():
    """The spine over two futures, with a gas unit that costs more and a link that delivers less in the stormy one."""
    n = spine.build()
    n.add('Generator', 'gas41', bus='south', p_nom=100, marginal_cost=20)
    n.add('Link', 'wire41', bus0='north', bus1='south', p_nom=40, efficiency=0.9)
    n.add('Load', 'port41', bus='south', p_set=60)
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    for (scenario, name), values in PER_SCENARIO.items():
        component = n.c.generators if name == 'gas41' else n.c.links
        for column, value in values.items():
            component.static.loc[(scenario, name), column] = value
    return n
```

</details>
<!-- reference:rung_41_scenario_operational_data:end -->

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

| PyPSA                                                                               | status | note                                                                   |
| ----------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------- |
| [`{c}-ext-p_nom-lower/upper`](#generator-ext-p_nom-lower) with a bound per scenario | done   | one row per scenario, over `scenario`, the tightest bounding the build |
| [capital cost](#objective) per scenario                                             | done   | `scenario_weight` times each scenario's capital cost                   |

<!-- reference:rung_42_scenario_first_stage:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `5049.999999999999`, 84 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_42_scenario_first_stage.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 42: an extendable unit's capital cost and build cap differ by scenario."""

from __future__ import annotations

import spine

#: each scenario's own value, per attribute of the extendable unit
PER_SCENARIO = {
    'calm': {'capital_cost': 20, 'p_nom_max': 100},
    'stormy': {'capital_cost': 60, 'p_nom_max': 30},
}


def build():
    """The spine over two futures, with an extendable wind unit that costs more and may be built less in the stormy one."""
    n = spine.build()
    n.add('Generator', 'wind42', bus='south', p_nom_extendable=True, p_nom_max=100, marginal_cost=1, capital_cost=20)
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    for scenario, values in PER_SCENARIO.items():
        for column, value in values.items():
            n.c.generators.static.loc[(scenario, 'wind42'), column] = value
    return n
```

</details>
<!-- reference:rung_42_scenario_first_stage:end -->

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

| PyPSA                                                             | status | note                                                                                                               |
| ----------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| [`Bus-nodal_balance`](#bus-nodal_balance) with a component `sign` | done   | `Generator_sign`, `StorageUnit_sign` and `Store_sign` times each variable, and `Load_sign` times the load, negated |

<!-- reference:rung_43_sign:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `2125.0`, 88 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_43_sign.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 43: a component's `sign` turns its term in the bus balance around."""

from __future__ import annotations

import spine

#: the sign each component enters the bus balance with, against PyPSA's default
SIGNS = {'generators': ('flex43', -1), 'loads': ('feed43', 1), 'storage_units': ('su43', -1), 'stores': ('e43', -1)}


def build():
    """The spine with a unit that draws power, a load that feeds it, and a storage unit and a store drawn the other way round."""
    n = spine.build()
    n.add('Generator', 'flex43', bus='south', p_nom=20, marginal_cost=-50, sign=-1)
    n.add('Load', 'feed43', bus='north', p_set=10, sign=1)
    n.add('StorageUnit', 'su43', bus='south', p_nom=10, max_hours=2, state_of_charge_initial=20, sign=-1)
    n.add('Store', 'e43', bus='north', e_nom=30, e_initial=30, sign=-1)
    return n
```

</details>
<!-- reference:rung_43_sign:end -->

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

| PyPSA                                                                              | status | note                                                                                                                                                                         |
| ---------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-p-ramp_limit_up/down`](#generator-p-ramp_limit_up) with a limit per snapshot | done   | `{c}_ramp_limit_up`, `{c}_ramp_limit_down` and their rates over `snapshot`, with no row at a snapshot without a value, unless the row has a start-up or shut-down ramp there |

<!-- reference:rung_45_ramp_per_snapshot:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `10996.0`, 83 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_45_ramp_per_snapshot.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 45: ramp limits per snapshot — a generator, a link and a process whose ramp limits change over time, and lift at one snapshot."""

from __future__ import annotations

import math

import spine


def build():
    """The spine plus a steep bus served by a generator, a link and a process with ramp limits per snapshot, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'steep')
    up = [0.1, 0.1, 0.5, 0.1]
    down = [0.1, 0.1, 0.1, math.nan]
    n.add('Generator', 'steep_gen', bus='steep', p_nom=60, marginal_cost=3, ramp_limit_up=up, ramp_limit_down=down)
    n.add(
        'Link',
        'steep_link',
        bus0='north',
        bus1='steep',
        p_nom=40,
        marginal_cost=4,
        ramp_limit_up=up,
        ramp_limit_down=down,
    )
    n.add(
        'Process',
        'steep_proc',
        bus0='south',
        bus1='steep',
        rate0=-1.25,
        p_nom=40,
        marginal_cost=5,
        ramp_limit_up=up,
        ramp_limit_down=down,
    )
    n.add('Generator', 'steep_backup', bus='steep', p_nom=200, marginal_cost=500)
    n.add('Load', 'steep_load', bus='steep', p_set=[10, 20, 90, 10])
    return n
```

</details>
<!-- reference:rung_45_ramp_per_snapshot:end -->

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

| PyPSA                                                                                                                     | status | note                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------- |
| [`{c}-p-ramp_limit_*`](#generator-p-ramp_limit_up), [`-bigM`](#generator-p-ramp_limit_up-run-bigm), at the first snapshot | done   | `{c}_previous_p` opens on `{c}_status_initial * {c}_p_init`, and the row exists where `{c}_status_initial == 0 OR {c}_p_init` |

<!-- reference:rung_46_initial_output:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `101294.125`, 200 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_46_initial_output.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 46: the output brought in — units that came in running with a given `p_init` ramp from it into the first snapshot."""

from __future__ import annotations

import spine


def build():
    """The spine plus a warm bus served by fixed, extendable and committable units that each carry a `p_init`, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'warm')
    ramps = {'ramp_limit_up': 0.25, 'ramp_limit_down': 0.25}
    n.add('Generator', 'warm_gen', bus='warm', p_nom=60, marginal_cost=3, p_init=10, **ramps)
    n.add('Link', 'warm_link', bus0='north', bus1='warm', p_nom=40, marginal_cost=4, p_init=0, **ramps)
    n.add(
        'Process', 'warm_proc', bus0='south', bus1='warm', rate0=-1.25, p_nom=40, marginal_cost=600, p_init=40, **ramps
    )
    n.add(
        'Generator',
        'warm_ext',
        bus='warm',
        p_nom_extendable=True,
        p_nom_max=40,
        capital_cost=5,
        marginal_cost=2,
        p_init=5,
        **ramps,
    )
    n.add(
        'Generator',
        'warm_com',
        bus='warm',
        committable=True,
        p_nom=50,
        p_min_pu=0.2,
        marginal_cost=2.5,
        p_init=30,
        ramp_limit_start_up=0.4,
        ramp_limit_shut_down=0.4,
        **ramps,
    )
    n.add(
        'Generator',
        'warm_com_ext',
        bus='warm',
        committable=True,
        p_nom_extendable=True,
        p_nom_max=40,
        capital_cost=5,
        marginal_cost=2.2,
        p_init=5,
        **ramps,
    )
    n.add('Generator', 'warm_backup', bus='warm', p_nom=300, marginal_cost=500)
    n.add('Load', 'warm_load', bus='warm', p_set=[150, 150, 60, 60])
    return n
```

</details>
<!-- reference:rung_46_initial_output:end -->

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

| PyPSA                                                                                                 | status | note                                                              |
| ----------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------- |
| [`start_up_cost`, `shut_down_cost`](#objective) under `multi_investment_periods` and snapshot weights | done   | the period weight and the scenario weight, no snapshot weight |

<!-- reference:rung_48_start_up_period_weight:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7125.0`, 72 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_48_start_up_period_weight.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 48: a start and a stop take their period's weight and no snapshot weight, over two weighted periods."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: a committable peaker that starts and stops once in each period."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(3)] + [(2030, datetime(2030, 1, 1, t)) for t in range(3)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0, 1.5, 2.5]
    n.add('Bus', 'grid')
    n.add('Generator', 'base48', bus='grid', p_nom=60, marginal_cost=10)
    n.add('Generator', 'dear48', bus='grid', p_nom=100, marginal_cost=90)
    n.add(
        'Generator',
        'peak48',
        bus='grid',
        p_nom=50,
        marginal_cost=20,
        committable=True,
        p_min_pu=0.4,
        start_up_cost=300,
        shut_down_cost=100,
        up_time_before=0,
    )
    n.add('Load', 'town48', bus='grid', p_set=[50, 100, 50, 50, 100, 50])
    return n
```

</details>
<!-- reference:rung_48_start_up_period_weight:end -->

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

| PyPSA                                                                              | status | note                                                                                 |
| ---------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| [`Carrier-growth_limit`](#carrier-growth_limit) without `multi_investment_periods` | done   | The file states no row, as `Carrier_max_growth` has no value on a single-period run. |

<!-- reference:rung_49_single_period_growth:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `335.0`, 42 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_49_single_period_growth.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 49: a carrier's growth limit without `multi_investment_periods` — PyPSA builds no row, so the build passes the cap."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Carrier', 'wind', max_growth=10)
    n.add('Generator', 'wind49', bus='south', carrier='wind', p_nom_extendable=True, p_nom_max=100, capital_cost=5)
    return n
```

</details>
<!-- reference:rung_49_single_period_growth:end -->

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

| PyPSA                                                                      | status | note                                               |
| -------------------------------------------------------------------------- | ------ | -------------------------------------------------- |
| [`Bus-nodal_balance`](#bus-nodal_balance) with a load that is not `active` | done   | `Load_demand` is zero where `Load_active` is false |

<!-- reference:rung_50_inactive_load:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7380.0`, 32 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_50_inactive_load.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 50: a load that is not `active` — PyPSA drops it from its bus's balance."""

from __future__ import annotations

import spine


def build():
    """The spine plus this rung's additions, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Load', 'idle50', bus='south', p_set=[30, 10, 20, 40], active=False)
    return n
```

</details>
<!-- reference:rung_50_inactive_load:end -->

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

| PyPSA                                                                      | status | note                                                                    |
| -------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------- |
| [`Carrier-growth_limit`](#carrier-growth_limit) with an asset that retires | done   | `{c}_first_active` is zero after the first period an asset is active in |

<!-- reference:rung_51_growth_retired_asset:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `3432.5`, 26 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_51_growth_retired_asset.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 51: a carrier's growth limit counts an asset in the first period it stands in only, not again after it retires.

The old unit retires before the new one is built, so each builds to the
limit in its own period.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def network(carriers: dict[str, str]):
    """Two periods, a solar unit that stands in 2020 only and one built in 2030, each under the carrier named for it."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0]
    n.add('Bus', 'grid')
    n.add('Carrier', 'gas')
    for carrier in sorted(set(carriers.values())):
        n.add('Carrier', carrier, max_growth=10)
    for name, build_year in (('solar_old', 2020), ('solar_new', 2030)):
        n.add(
            'Generator',
            name,
            bus='grid',
            carrier=carriers[name],
            p_nom_extendable=True,
            p_nom_max=50,
            marginal_cost=1,
            capital_cost=5,
            build_year=build_year,
            lifetime=10,
        )
    n.add('Generator', 'backup', bus='grid', carrier='gas', p_nom=100, marginal_cost=80)
    n.add('Load', 'town', bus='grid', p_set=[15, 20, 15, 20])
    return n


def build():
    """Both solar units under one carrier with `max_growth = 10`; the old one retires after 2020."""
    return network({'solar_old': 'solar', 'solar_new': 'solar'})
```

</details>
<!-- reference:rung_51_growth_retired_asset:end -->

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

| PyPSA                                                                                                 | status | note                 |
| ----------------------------------------------------------------------------------------------------- | ------ | -------------------- |
| [`transmission_expansion_cost_limit`](#transmission_expansion_cost_limit) on a network with scenarios | done   | the row per scenario |

<!-- reference:rung_52_scenario_cost_limit:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `15630.0`, 86 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_52_scenario_cost_limit.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 52: a `transmission_expansion_cost_limit` row holds in every scenario.

The two futures are identical, so the expected cost is the cost of the same
network without scenarios.
"""

from __future__ import annotations

import spine


def network():
    """The spine plus an extendable DC link whose build a cost limit of 150 caps."""
    n = spine.build()
    n.add('Carrier', 'DC')
    n.add(
        'Link',
        'hvdc52',
        bus0='north',
        bus1='south',
        carrier='DC',
        p_nom_extendable=True,
        p_nom_max=100,
        capital_cost=10,
    )
    n.add('Load', 'port52', bus='south', p_set=40)
    n.add(
        'GlobalConstraint',
        'cost52',
        type='transmission_expansion_cost_limit',
        carrier_attribute='DC',
        sense='<=',
        constant=150,
    )
    return n


def build():
    """The same network over two identical futures."""
    n = network()
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    return n
```

</details>
<!-- reference:rung_52_scenario_cost_limit:end -->

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

| PyPSA                                                                                                                                    | status | note                 |
| ---------------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------- |
| [`transmission_volume_expansion_limit`](#transmission_volume_expansion_limit) on a network with scenarios and `multi_investment_periods` | done   | the row per scenario |

<!-- reference:rung_53_scenario_period_volume_limit:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `15005.0`, 70 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_53_scenario_period_volume_limit.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 53: a `transmission_volume_expansion_limit` row holds in every scenario under `multi_investment_periods`.

The two futures are identical, so the expected cost is the cost of the same
network without scenarios.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def network():
    """Two periods, a cheap unit behind an extendable line whose volume a limit of 60 caps."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0]
    n.add('Bus', ['hill', 'town'])
    n.add('Carrier', 'AC')
    n.add('Generator', 'hydro53', bus='hill', p_nom=100, marginal_cost=5)
    n.add('Generator', 'diesel53', bus='town', p_nom=100, marginal_cost=90)
    n.add(
        'Line',
        'tie53',
        bus0='hill',
        bus1='town',
        x=0.1,
        carrier='AC',
        length=3,
        s_nom_extendable=True,
        s_nom_max=100,
        capital_cost=1,
        build_year=2020,
        lifetime=30,
    )
    n.add('Load', 'town_load', bus='town', p_set=[40, 50, 60, 45])
    n.add(
        'GlobalConstraint',
        'volume53',
        type='transmission_volume_expansion_limit',
        carrier_attribute='AC',
        sense='<=',
        constant=60,
    )
    return n


def build():
    """The same network over two identical futures."""
    n = network()
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    return n
```

</details>
<!-- reference:rung_53_scenario_period_volume_limit:end -->

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

| PyPSA                                                                                            | status | note                                                                 |
| ------------------------------------------------------------------------------------------------ | ------ | -------------------------------------------------------------------- |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law) with a transformer on a network with scenarios | done   | the row per scenario, with one phase shift for every scenario (#783) |

<!-- reference:rung_55_scenario_transformer_cycle:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `13105.0`, 152 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_55_scenario_transformer_cycle.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 55: a cycle of two transformers takes its Kirchhoff voltage row in every scenario.

The two futures are identical, so the expected cost is the cost of the same
network without scenarios.
"""

from __future__ import annotations

import spine


def network():
    """The spine plus two parallel transformers of unequal reactance, so the one that takes more flow caps the pair."""
    n = spine.build()
    n.add('Bus', ['a', 'b'])
    n.add('Generator', 'hydro55', bus='a', p_nom=100, marginal_cost=10)
    n.add('Generator', 'diesel55', bus='b', p_nom=100, marginal_cost=50)
    n.add('Load', 'town55', bus='b', p_set=[50, 40, 55, 45])
    n.add('Transformer', 't55', bus0='a', bus1='b', x=0.1, s_nom=30)
    n.add('Transformer', 't55_2', bus0='a', bus1='b', x=0.2, s_nom=30)
    return n


def build():
    """The same network over two identical futures."""
    n = network()
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    return n
```

</details>
<!-- reference:rung_55_scenario_transformer_cycle:end -->

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

| PyPSA                                                                                                                                             | status | note                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------- |
| [`Line-fix-s-*-security-for-{c}-outage-in-sub-network-{n}`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n) on a network with scenarios | done   | the copies per scenario |

<!-- reference:rung_56_scenario_security_constrained:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `18205.0`, 216 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_56_scenario_security_constrained.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 56: a security-constrained run over scenarios copies its rows into every scenario.

The two futures are identical, so the expected cost is the cost of the same
network without scenarios.
"""

from __future__ import annotations

import spine

BRANCH_OUTAGES = ['l56', 'l56_2']


def network():
    """The spine plus two parallel lines, so each must carry the whole import alone when the other is out."""
    n = spine.build()
    n.add('Bus', ['a', 'b'])
    n.add('Generator', 'hydro56', bus='a', p_nom=100, marginal_cost=10)
    n.add('Generator', 'diesel56', bus='b', p_nom=100, marginal_cost=50)
    n.add('Load', 'town56', bus='b', p_set=[50, 40, 55, 45])
    n.add('Line', 'l56', bus0='a', bus1='b', x=0.1, s_nom=30)
    n.add('Line', 'l56_2', bus0='a', bus1='b', x=0.1, s_nom=35)
    return n


def build():
    """The same network over two identical futures."""
    n = network()
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    return n
```

</details>
<!-- reference:rung_56_scenario_security_constrained:end -->

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

| PyPSA                                                               | status | note                                                       |
| ------------------------------------------------------------------- | ------ | ---------------------------------------------------------- |
| [`{c}-p_nom_set`](#generator-p_nom_set) on a network with scenarios | done   | one row, the same feasible set as PyPSA's row per scenario |

<!-- reference:rung_57_scenario_nom_set:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `4800.000000000001`, 86 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_57_scenario_nom_set.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 57: `p_nom_set` pins an extendable build on a network with scenarios.

The two futures are identical, so the expected cost is the cost of the same
network without scenarios.
"""

from __future__ import annotations

import spine


def network():
    """The spine plus a cheap extendable wind unit whose build is pinned below what it would choose."""
    n = spine.build()
    n.add(
        'Generator',
        'wind57',
        bus='south',
        p_nom_extendable=True,
        p_nom_max=100,
        capital_cost=5,
        p_nom_set=20,
    )
    return n


def build():
    """The same network over two identical futures."""
    n = network()
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    return n
```

</details>
<!-- reference:rung_57_scenario_nom_set:end -->

### Rung 58 — a committable unit per scenario

The reference script calls `n.set_scenarios(...)` with a committable unit. The file
states the status rows in every scenario, and PyPSA builds them in every
scenario too.

The rung adds a cheap committable unit to the spine that cannot run below `40`
% of its build, with a start-up cost of `100`. The two futures are identical,
and PyPSA solves to `7430.0`, the objective of the network without scenarios.
With the same unit not committable, PyPSA solves to `7330.0`.

| PyPSA                                                             | status | note                  |
| ----------------------------------------------------------------- | ------ | --------------------- |
| [`{c}-com-*`](#generator-com-p-lower) on a network with scenarios | done   | the rows per scenario |

<!-- reference:rung_58_scenario_committable:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7430.0`, 128 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_58_scenario_committable.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 58: a committable unit takes its status rows in every scenario.

The two futures are identical, so the expected cost is the cost of the same
network without scenarios.
"""

from __future__ import annotations

import spine


def network():
    """The spine plus a cheap committable unit that cannot run below 40 % of its build."""
    n = spine.build()
    n.add(
        'Generator',
        'uc58',
        bus='north',
        committable=True,
        p_nom=50,
        marginal_cost=5,
        p_min_pu=0.4,
        min_up_time=2,
        up_time_before=0,
        start_up_cost=100,
    )
    n.add('Load', 'swing58', bus='north', p_set=[5, 45, 45, 10])
    return n


def build():
    """The same network over two identical futures."""
    n = network()
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    return n
```

</details>
<!-- reference:rung_58_scenario_committable:end -->

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

| PyPSA                                                                                      | status | note                                                                                               |
| ------------------------------------------------------------------------------------------ | ------ | -------------------------------------------------------------------------------------------------- |
| [`Bus-nodal_balance`](#bus-nodal_balance) with an efficiency or a rate per snapshot        | done   | `Link_efficiency` and `Process_rate` span `snapshot`, taken at the snapshot a delayed flow arrives |
| [`StorageUnit-energy_balance`](#storageunit-energy_balance) with efficiencies per snapshot | done   | `StorageUnit_efficiency_store` and `StorageUnit_efficiency_dispatch` span `snapshot`               |
| [`primary_energy`](#primary_energy) with a generator efficiency per snapshot               | done   | `Generator_primary_energy_weight` spans `snapshot`                                                 |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law) with a fixed phase shift per snapshot    | done   | `Transformer_phase_shift_weight` spans `snapshot`                                                  |

<!-- reference:rung_60_efficiency_per_snapshot:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `130562.09418409193`, 133 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_60_efficiency_per_snapshot.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 60: efficiencies per snapshot — a link, a process, a storage unit, a fuel unit under a primary-energy cap and a transformer with a fixed phase shift, each reading its coefficient per snapshot."""

from __future__ import annotations

from datetime import datetime

#: Four hourly stamps. The `generators` weighting is uniform, as rung 16's, so a
#: `delay` of one is a shift of one snapshot position. The `objective` and
#: `stores` columns stay non-uniform, so no cost or storage factor passes as identity.
SNAPSHOTS = [datetime(2015, 1, 1, hour) for hour in range(4)]
WEIGHTINGS = {'objective': [2.0, 1.5, 2.5, 3.0], 'stores': [0.5, 2.0, 1.5, 2.5], 'generators': [1.0, 1.0, 1.0, 1.0]}

LINK_EFFICIENCY = [2.0, 3.5, 2.5, 3.0]
PROCESS_RATE = [0.9, 0.5, 0.8, 0.6]
EFFICIENCY_STORE = [0.9, 0.5, 0.9, 0.5]
EFFICIENCY_DISPATCH = [0.6, 0.9, 0.7, 0.95]
FUEL_EFFICIENCY = [0.3, 0.6, 0.4, 0.5]
PHASE_SHIFT = [0.0, 0.5, -0.3, 1.0]


def build():
    """A source feeding a sink over a delayed link and a delayed process, a storage unit and a capped fuel unit at the sink, and a triangle with a fixed phase shift per snapshot."""
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(SNAPSHOTS)
    for column, values in WEIGHTINGS.items():
        n.snapshot_weightings[column] = values
    n.add('Carrier', 'fuel60', co2_emissions=1.0)
    n.add('Bus', ['source', 'sink'])
    n.add('Generator', 'spring60', bus='source', p_nom=200, marginal_cost=5)
    n.add('Generator', 'backup60', bus='sink', p_nom=200, marginal_cost=100)
    n.add(
        'Generator', 'fuel_unit60', bus='sink', carrier='fuel60', p_nom=40, marginal_cost=20, efficiency=FUEL_EFFICIENCY
    )
    n.add('Link', 'heat_pump60', bus0='source', bus1='sink', p_nom=10, efficiency=LINK_EFFICIENCY, delay=1)
    n.add('Process', 'boiler60', bus0='source', bus1='sink', p_nom=20, rate1=PROCESS_RATE, delay1=1)
    n.add(
        'StorageUnit',
        'battery60',
        bus='sink',
        p_nom=20,
        max_hours=2,
        cyclic_state_of_charge=True,
        efficiency_store=EFFICIENCY_STORE,
        efficiency_dispatch=EFFICIENCY_DISPATCH,
    )
    n.add('Load', 'sink_load60', bus='sink', p_set=[60.0, 90.0, 50.0, 100.0])
    n.add(
        'GlobalConstraint',
        'fuel_cap60',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='<=',
        constant=150,
    )
    n.add('Bus', ['a', 'b', 'c'])
    n.add('Generator', 'hydro60', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel60', bus='c', p_nom=300, marginal_cost=200)
    n.add('Load', 'town60', bus='c', p_set=[90.0, 75.0, 120.0, 105.0])
    n.add('Line', 'ab60', bus0='a', bus1='b', carrier='AC', x=0.002, r=0.0002, s_nom=120)
    n.add('Line', 'bc60', bus0='b', bus1='c', carrier='AC', x=0.002, r=0.0002, s_nom=120)
    n.add('Transformer', 'ca60', bus0='c', bus1='a', x=0.002, r=0.0002, s_nom=40, phase_shift=PHASE_SHIFT)
    return n
```

</details>
<!-- reference:rung_60_efficiency_per_snapshot:end -->

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

| PyPSA                                                                                                                        | status | note                                                                               |
| ---------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------- |
| [`Line-v_ang-lower`](#line-v_ang-lower), [`Line-v_ang-upper`](#line-v_ang-upper)                                             | done   | `Line_carrier == 'AC'` in the `where`, and no row for an infinite `Line_v_ang_max` |
| [`Transformer-v_ang-lower`](#transformer-v_ang-lower), [`Transformer-v_ang-upper`](#transformer-v_ang-upper)                 | done   | the fixed shift is `Transformer_phase_shift_fixed`, per snapshot                   |
| [`Transformer-v_ang-var-lower`](#transformer-v_ang-var-lower), [`Transformer-v_ang-var-upper`](#transformer-v_ang-var-upper) | done   | the decided shift is the `Transformer_phase_shift` variable, in degrees            |
| [`{c}-v_ang-*`](#line-v_ang-lower) on a network with scenarios                                                               | done   | the rows per scenario, with one phase shift for every scenario (#783)              |

<!-- reference:rung_61_voltage_angle_limits:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `121834.62083205313`, 176 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_61_voltage_angle_limits.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 61: voltage angle limits — a line, a transformer with a fixed phase shift and one with a decided shift, each holding the angle difference across it within its `v_ang_max`.

A line beside the spine's link may carry only the flow that keeps the angle
across it within one degree, so the lossy link carries the rest. Two triangles
carry cheap upstream power to a town past a costly local unit. In the first a
transformer has a fixed shift, in the second the shift is a decision; the
angle cap on each transformer binds before its thermal rating does, so the
local unit runs. In one cycle the angle caps of all branches couple, so each
triangle carries one cap only. No scenario: with scenarios PyPSA builds no
angle row.
"""

from __future__ import annotations

import spine


def build():
    """The spine plus a line beside its link and two triangles, each with one voltage angle limit that binds, as a ``pypsa.Network``."""
    n = spine.build()
    n.add('Line', 'north_south61', bus0='north', bus1='south', carrier='AC', x=0.002, s_nom=100, v_ang_max=1)
    n.add('Bus', ['a', 'b', 'c'])
    n.add('Generator', 'hydro61', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel61', bus='c', p_nom=300, marginal_cost=200)
    n.add('Load', 'town61', bus='c', p_set=[90, 75, 120, 105])
    n.add('Line', 'ab61', bus0='a', bus1='b', carrier='AC', x=0.002, s_nom=200)
    n.add('Line', 'bc61', bus0='b', bus1='c', carrier='AC', x=0.002, s_nom=200)
    n.add('Transformer', 'ca61', bus0='c', bus1='a', x=0.4, s_nom=200, phase_shift=2, v_ang_max=2.5)
    n.add('Bus', ['d', 'e', 'f'])
    n.add('Generator', 'hydro61_shift', bus='d', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel61_shift', bus='f', p_nom=300, marginal_cost=200)
    n.add('Load', 'town61_shift', bus='f', p_set=[90, 75, 120, 105])
    n.add('Line', 'de61', bus0='d', bus1='e', carrier='AC', x=0.002, s_nom=200)
    n.add('Line', 'ef61', bus0='e', bus1='f', carrier='AC', x=0.002, s_nom=200)
    n.add(
        'Transformer',
        'fd61',
        bus0='f',
        bus1='d',
        x=0.4,
        s_nom=80,
        phase_shift_min=-30,
        phase_shift_max=30,
        v_ang_max=5,
    )
    return n
```

</details>
<!-- reference:rung_61_voltage_angle_limits:end -->

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

| PyPSA                                                        | status | note                                                                                            |
| ------------------------------------------------------------ | ------ | ----------------------------------------------------------------------------------------------- |
| [`start_up_cost`, `shut_down_cost`](#objective) per snapshot | done   | Generator, Link and Process over `[scenario, snapshot, …]`, with no snapshot weight, as rung 48 |

<!-- reference:rung_62_startup_cost_per_snapshot:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `6850.0`, 60 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_62_startup_cost_per_snapshot.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 62: a start-up cost per snapshot — a committable unit starts in the snapshot where a start costs least, with no snapshot weight on that cost."""

from __future__ import annotations

from datetime import datetime

SNAPSHOTS = [datetime(2015, 1, 1, hour) for hour in range(5)]
WEIGHTINGS = [2.0, 1.5, 1.0, 2.0, 1.0]
START_UP_COST = [400.0, 100.0, 900.0, 900.0, 900.0]
SHUT_DOWN_COST = [300.0, 300.0, 300.0, 300.0, 0.0]


def build():
    """A whole network, not the spine: a committable peaker the load needs in the third and fourth snapshots, cheap to start one snapshot early and free to stop in the last."""
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(SNAPSHOTS)
    n.snapshot_weightings['objective'] = WEIGHTINGS
    n.add('Bus', 'grid')
    n.add('Generator', 'base62', bus='grid', p_nom=60, marginal_cost=10)
    n.add('Generator', 'dear62', bus='grid', p_nom=100, marginal_cost=90)
    n.add(
        'Generator',
        'peak62',
        bus='grid',
        p_nom=50,
        marginal_cost=20,
        committable=True,
        p_min_pu=0.4,
        up_time_before=0,
    )
    n.generators_t.start_up_cost['peak62'] = START_UP_COST
    n.generators_t.shut_down_cost['peak62'] = SHUT_DOWN_COST
    n.add('Load', 'town62', bus='grid', p_set=[50, 50, 100, 100, 50])
    return n
```

</details>
<!-- reference:rung_62_startup_cost_per_snapshot:end -->

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

| PyPSA                                                                                             | status | note                                                                    |
| ------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------- |
| [`Line-n_mod`, `Line-s_nom_modularity`](#line-s_nom_modularity)                                   | done   |                                                                         |
| [`Transformer-n_mod`, `Transformer-s_nom_modularity`](#transformer-s_nom_modularity)              | done   |                                                                         |
| [`StorageUnit-n_mod`, `StorageUnit-p_nom_modularity`](#storageunit-p_nom_modularity)              | done   |                                                                         |
| [`Store-n_mod`, `Store-e_nom_modularity`](#store-e_nom_modularity)                                | done   |                                                                         |
| [`{c}-n_mod`, `{c}-{attr}_modularity`](#generator-p_nom_modularity) for a unit that is not active | done   | no column and no row where `count({c}_active, over=snapshot) > 0` fails |

<!-- reference:rung_63_modular_branches_and_storage:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `13927.0`, 116 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_63_modular_branches_and_storage.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 63: modular branches and storage — a line, a transformer, a storage unit and a store each built in whole modules, beside a modular generator, link and process that are not active."""

from __future__ import annotations

import spine


def build():
    """The spine plus an east bus fed over a modular line and a modular transformer, with a modular storage unit and store, and three inactive modular builds."""
    n = spine.build()
    n.add('Bus', 'east')
    n.add(
        'Line', 'ne63', bus0='north', bus1='east', x=0.01, r=0.001, s_nom_extendable=True, s_nom_mod=25, capital_cost=3
    )
    n.add('Transformer', 'se63', bus0='south', bus1='east', x=0.01, s_nom_extendable=True, s_nom_mod=15, capital_cost=2)
    n.add(
        'StorageUnit',
        'battery63',
        bus='east',
        p_nom_extendable=True,
        p_nom_mod=15,
        max_hours=2,
        capital_cost=5,
        cyclic_state_of_charge=True,
    )
    n.add('Store', 'tank63', bus='east', e_nom_extendable=True, e_nom_mod=40, capital_cost=2, e_cyclic=True)
    n.add('Generator', 'east_backup63', bus='east', p_nom=200, marginal_cost=200)
    n.add('Load', 'east_load63', bus='east', p_set=[20, 70, 110, 40])
    idle = {'p_nom_extendable': True, 'p_nom_mod': 20, 'capital_cost': 1, 'marginal_cost': 1, 'active': False}
    n.add('Generator', 'idle_gen63', bus='east', **idle)
    n.add('Link', 'idle_link63', bus0='north', bus1='east', **idle)
    n.add('Process', 'idle_proc63', bus0='south', bus1='east', rate0=-1.25, **idle)
    return n
```

</details>
<!-- reference:rung_63_modular_branches_and_storage:end -->

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

| PyPSA                                                                                                  | status | note                                                                                                        |
| ------------------------------------------------------------------------------------------------------ | ------ | ----------------------------------------------------------------------------------------------------------- |
| [`{c}-com-transition-start-up`](#generator-com-transition-start-up) for a unit built in a later period | done   | `Generator_previous_status` is zero at the first snapshot a unit is active in past the first of the horizon |
| [`{c}-com-ext-p-*` (big-M)](#generator-com-ext-p-upper-bigm) with `p_nom_max = inf`                    | done   | `Generator_big_m` is M by PyPSA's rule                                                                      |

<!-- reference:rung_64_commitment_edges:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `9140.0`, 205 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_64_commitment_edges.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 64: commitment edges — a committable generator, link and process built in the later period start up when they open, and a committable unit without a build cap is released by an inferred big M."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods, three committable units built in 2030, an uncapped committable build, and a dear peaker."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 2.0, 2.0, 1.5, 2.5, 2.0]
    n.add('Bus', ['hub', 'fuel'])
    n.add('Generator', 'well64', bus='fuel', p_nom=200, marginal_cost=1)
    n.add('Generator', 'peak64', bus='hub', p_nom=300, marginal_cost=50)
    late = {'committable': True, 'p_nom': 30, 'p_min_pu': 0.25, 'build_year': 2030, 'lifetime': 30}
    n.add('Generator', 'late_gen64', bus='hub', marginal_cost=2, start_up_cost=100, **late)
    n.add('Link', 'late_link64', bus0='fuel', bus1='hub', marginal_cost=1, start_up_cost=70, **late)
    n.add('Process', 'late_proc64', bus0='fuel', bus1='hub', rate0=-1.25, start_up_cost=40, **late)
    n.add(
        'Generator',
        'uncapped64',
        bus='hub',
        committable=True,
        p_nom_extendable=True,
        capital_cost=20,
        marginal_cost=10,
        p_min_pu=0.2,
        up_time_before=0,
        start_up_cost=30,
    )
    n.add('Load', 'hub_load64', bus='hub', p_set=[40, 60, 70, 50, 120, 140, 150, 130])
    return n
```

</details>
<!-- reference:rung_64_commitment_edges:end -->

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

| PyPSA                                                                                                                     | status | note                                                            |
| ------------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------- |
| [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law) per investment period                                                   | done   | the cycle weights span `period`, read at each snapshot's period |
| [`Line-fix-s-*-security-…`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n) for a branch not active in a period | done   | no factor and no copy                                           |

<!-- reference:rung_66_cycles_per_period:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `16000.0`, 62 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_66_cycles_per_period.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 66: cycles per period — a line that comes in with the second period closes a triangle, under a security-constrained run that outages it."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}
BRANCH_OUTAGES = ['ca66']


def build():
    """A whole network, not the spine: a path from `a` to `c` in 2020, and a triangle in 2030 once `ca66` stands."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [10.0, 10.0]
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 3.0]
    n.add('Bus', ['a', 'b', 'c'])
    n.add('Generator', 'hydro66', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel66', bus='c', p_nom=300, marginal_cost=100)
    n.add('Load', 'town66', bus='c', p_set=[80, 100, 90, 110])
    n.add('Line', 'ab66', bus0='a', bus1='b', x=0.1, s_nom=150)
    n.add('Line', 'bc66', bus0='b', bus1='c', x=0.1, s_nom=150)
    n.add('Line', 'ca66', bus0='c', bus1='a', x=0.1, s_nom=40, build_year=2030, lifetime=50)
    return n
```

</details>
<!-- reference:rung_66_cycles_per_period:end -->

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

| PyPSA                                                                                                                                         | status | note                                             |
| --------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------ |
| [`Line-fix-s-*-security-…`](#line-fix-s-lower-security-for-c-outage-in-sub-network-n) for an outage of a branch not active in the last period | done   | `Line_BODF` and `Transformer_BODF` span `period` |

<!-- reference:rung_68_outage_factors_per_period:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `13000.0`, 46 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_68_outage_factors_per_period.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 68: outage factors per period — a security-constrained run outages a line that retires before the last period.

Each period takes the outage factors of the branches active in it, so the
outage of the retired line binds in 2020 and builds no rows in 2030.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}
BRANCH_OUTAGES = ['ab_old68']
PERIODS = {2020: (1.0, [2.0, 1.5], [80, 70]), 2030: (0.5, [2.5, 3.0], [90, 60])}


def network(periods: list[int]):
    """Cheap hydro at `a`, a town with diesel at `b`, and two parallel lines; `ab_old68` retires in 2025."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples([(p, datetime(p, 1, 1, t)) for p in periods for t in range(2)])
    n.investment_periods = periods
    n.investment_period_weightings['objective'] = [PERIODS[p][0] for p in periods]
    n.investment_period_weightings['years'] = 10.0
    n.snapshot_weightings['objective'] = [w for p in periods for w in PERIODS[p][1]]
    n.add('Bus', ['a', 'b'])
    n.add('Generator', 'hydro68', bus='a', p_nom=300, marginal_cost=10)
    n.add('Generator', 'diesel68', bus='b', p_nom=300, marginal_cost=100)
    n.add('Load', 'town68', bus='b', p_set=[load for p in periods for load in PERIODS[p][2]])
    n.add('Line', 'ab68', bus0='a', bus1='b', x=0.1, s_nom=60)
    n.add('Line', 'ab_old68', bus0='a', bus1='b', x=0.1, s_nom=60, build_year=2000, lifetime=25)
    return n


def build():
    """Both periods: after the outage of `ab_old68`, `ab68` carries the whole import of 2020 alone."""
    return network(list(PERIODS))
```

</details>
<!-- reference:rung_68_outage_factors_per_period:end -->

### Rung 69 — storage that retires before the close

This rung runs `n.optimize(multi_investment_periods=True)` with a
`primary_energy` row over storage that carries its level across periods and
retires before the last counted snapshot. PyPSA fills the level forward over
the counted snapshots and takes the last value
(`global_constraints.py:476-479`, `:528-531`, and `:682-685`, `:730-733` for
`operational_limit`). The level exists only where the storage is active.
PyPSA's row therefore contains the level at the last counted snapshot where the
storage is active.

The file states that snapshot as
[`StorageUnit_last_counted_active`](#storageunit_last_counted_active) and
[`Store_last_counted_active`](#store_last_counted_active). The counted
snapshots are the whole horizon or one period, and a storage is active in one
continuous stretch of periods. So the snapshot is the last one where the two
overlap.

The rung adds a store and a storage unit of an emitting carrier. Each has an
initial level of 20 and retires after 2020. A CO2 cap of `5` applies over the
horizon. The row bounds the two levels at the last snapshot of 2020 to at least
`35`. A row at the last snapshot of 2030, where neither storage is active,
would have no variable and would be `0 <= -35`.

| PyPSA                                                                          | status | note                                                                                                                                                                                |
| ------------------------------------------------------------------------------ | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy), [`operational_limit`](#operational_limit) | done   | for storage that retires before the last counted snapshot, `StorageUnit_last_counted_active` and `Store_last_counted_active`, the last counted snapshot where the storage is active |

<!-- reference:rung_69_storage_retires_before_close:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `350.0`, 37 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_69_storage_retires_before_close.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 69: storage that retires before the last counted snapshot closes a `primary_energy` row at the last level it holds."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: four snapshots over two periods, a store and a storage unit of an emitting carrier that retire after 2020, and a CO2 cap over the horizon."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(2)] + [(2030, datetime(2030, 1, 1, t)) for t in range(2)]
    )
    n.investment_periods = [2020, 2030]
    n.add('Carrier', 'gas', co2_emissions=1.0)
    n.add('Bus', 'hub')
    n.add('Generator', 'base69', bus='hub', p_nom=100, marginal_cost=10)
    n.add('Load', 'hub_load', bus='hub', p_set=10)
    n.add('Store', 'e_retire', bus='hub', carrier='gas', e_nom=30, e_initial=20, build_year=2020, lifetime=10)
    n.add(
        'StorageUnit',
        'su_retire',
        bus='hub',
        carrier='gas',
        p_nom=10,
        max_hours=3,
        state_of_charge_initial=20,
        build_year=2020,
        lifetime=10,
    )
    n.add(
        'GlobalConstraint', 'co2_cap', type='primary_energy', carrier_attribute='co2_emissions', sense='<=', constant=5
    )
    return n
```

</details>
<!-- reference:rung_69_storage_retires_before_close:end -->

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

| PyPSA                                                                       | status  | note                                    |
| --------------------------------------------------------------------------- | ------- | --------------------------------------- |
| [`CVaR-a`, `CVaR-theta`, `CVaR`](#variable-domains) at `omega = 0`          | done    | where `CVaR_omega` has a value          |
| [`CVaR-excess-{s}`](#cvar-excess-s), [`CVaR-def`](#cvar-def) at `omega = 0` | done    | where `CVaR_omega` has a value          |
| [objective](#objective) at `omega = 0`                                      | refused | a quadratic cost, [Refusals](#refusals) |

<!-- reference:rung_70_risk_preference_zero:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `7946.733333333334`, 87 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_70_risk_preference_zero.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 70: rung 14 with a risk preference of weight zero — PyPSA builds the CVaR columns and rows all the same."""

from __future__ import annotations

import spine


def build():
    """Rung 14's calm and stormy futures, with `omega = 0`: the optimum is the risk-neutral one."""
    n = spine.build()
    n.add('Generator', 'wind70', bus='south', p_nom_extendable=True, p_nom_max=100, marginal_cost=1, capital_cost=20)
    n.add('Load', 'port70', bus='south')
    n.set_scenarios({'calm': 0.6, 'stormy': 0.4})
    n.c.loads.dynamic.p_set[('calm', 'port70')] = [10, 20, 15, 10]
    n.c.loads.dynamic.p_set[('stormy', 'port70')] = [40, 60, 50, 30]
    n.c.generators.dynamic.p_max_pu[('calm', 'wind70')] = [0.9, 0.7, 0.8, 0.6]
    n.c.generators.dynamic.p_max_pu[('stormy', 'wind70')] = [0.3, 0.2, 0.4, 0.1]
    n.set_risk_preference(alpha=0.5, omega=0.0)
    return n
```

</details>
<!-- reference:rung_70_risk_preference_zero:end -->

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

| PyPSA                                                                                                           | status | note                                                         |
| --------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------ |
| [`Generator-p-ramp_limit_up`](#generator-p-ramp_limit_up) at the first snapshot, for a unit that is not committable | done   | `Generator_status_initial` is one, whatever `up_time_before` |

<!-- reference:rung_71_running_unless_committable:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `4836.111111111111`, 72 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_71_running_unless_committable.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 71: a unit that is not committable comes in running — its first-snapshot ramp starts from its `p_init`, whatever its `up_time_before` and whether another unit is committable."""

from __future__ import annotations

import spine


def build():
    """The spine plus a cheap ramp-limited unit that is not committable, with `up_time_before=0` and a `p_init`, beside a committable one."""
    n = spine.build()
    n.add(
        'Generator',
        'flex71',
        bus='south',
        p_nom=40,
        marginal_cost=5,
        ramp_limit_up=0.25,
        ramp_limit_start_up=0.5,
        up_time_before=0,
        p_init=10,
    )
    n.add('Generator', 'unit71', bus='south', committable=True, p_nom=20, p_min_pu=0.5, marginal_cost=20)
    return n
```

</details>
<!-- reference:rung_71_running_unless_committable:end -->

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

| PyPSA                                                                 | status | note                                       |
| --------------------------------------------------------------------- | ------ | ------------------------------------------ |
| [`Generator-com-down-time`](#generator-com-down-time), modular        | done   | bound by `Generator_modules`, not by one   |

<!-- reference:rung_72_modular_down_time:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `17190.0`, 111 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_72_modular_down_time.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 72: modular down time — a committable modular unit that stops some modules keeps the others running, because its down-time row is bound by its module count, not by one."""

from __future__ import annotations

import spine


def build():
    """The spine plus a dip bus served by a fixed and an extendable committable modular unit, each with a minimum down time, and a dear backup."""
    n = spine.build()
    n.add('Bus', 'dip')
    common = {
        'committable': True,
        'p_nom_mod': 10,
        'p_min_pu': 0.8,
        'min_down_time': 2,
        'up_time_before': 0,
        'start_up_cost': 5,
    }
    n.add('Generator', 'fixed72', bus='dip', p_nom=40, marginal_cost=2, **common)
    n.add(
        'Generator',
        'ext72',
        bus='dip',
        p_nom_extendable=True,
        p_nom_max=30,
        capital_cost=1,
        marginal_cost=3,
        **common,
    )
    n.add('Generator', 'dip_backup', bus='dip', p_nom=200, marginal_cost=100)
    n.add('Load', 'dip_load', bus='dip', p_set=[60, 15, 60, 70])
    return n
```

</details>
<!-- reference:rung_72_modular_down_time:end -->

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

| PyPSA                                                                                        | status | note                                                                                 |
| -------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| [`Generator-p-ramp_limit_up`](#generator-p-ramp_limit_up), `-down`, fixed modular committable | done   | per module, and every installed module on at the first snapshot after a running start |

<!-- reference:rung_73_fixed_modular_ramp:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `12300.0`, 80 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_73_fixed_modular_ramp.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 73: the ramp of a fixed modular committable unit — each running module ramps by its own share, and a unit that came in running counts all its modules on at the first snapshot."""

from __future__ import annotations

import spine


def build():
    """The spine plus a step bus served by a fixed committable modular unit that came in running at a `p_init`, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'step')
    n.add(
        'Generator',
        'modramp73',
        bus='step',
        committable=True,
        p_nom=60,
        p_nom_mod=20,
        p_min_pu=0.2,
        marginal_cost=2,
        ramp_limit_up=0.5,
        ramp_limit_down=0.5,
        ramp_limit_start_up=0.5,
        ramp_limit_shut_down=0.5,
        p_init=15,
    )
    n.add('Generator', 'step_backup', bus='step', p_nom=200, marginal_cost=100)
    n.add('Load', 'step_load', bus='step', p_set=[60, 20, 55, 30])
    return n
```

</details>
<!-- reference:rung_73_fixed_modular_ramp:end -->

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
[Refusals](#refusals).

The cap of `600` binds, and the row counts `10` years of each storage's
opening level against it. PyPSA solves to `12900.0`. Without the cap, it solves
to `9000.0`, and with the cap over the horizon, to `16500.0`. With the storage
on a carrier that emits nothing, it solves to `11400.0` (#977).

| PyPSA                                                                                                   | status | note                                                                         |
| ------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------- |
| [`primary_energy`](#primary_energy) for one period over storage that reopens per period, no scenarios   | done   | `StorageUnit_closing_weight` and `Store_closing_weight` in the stated period |

<!-- reference:rung_75_period_primary_energy_storage:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `12900.0`, 137 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_75_period_primary_energy_storage.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 75: a primary-energy cap for one period over storage that reopens per period — the cap counts the storage change of its own period alone."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods of unequal years, a gas unit, and a gas storage unit and store that each reopen per period."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [5.0, 10.0]
    n.add('Carrier', 'gas75', co2_emissions=0.5)
    n.add('Bus', 'hub')
    n.add('Generator', 'gas75', bus='hub', carrier='gas75', p_nom=100, marginal_cost=30)
    n.add('Generator', 'clean75', bus='hub', p_nom=200, marginal_cost=60)
    n.add(
        'StorageUnit',
        'tank75',
        bus='hub',
        carrier='gas75',
        p_nom=20,
        max_hours=4,
        state_of_charge_initial=60,
        state_of_charge_initial_per_period=True,
    )
    n.add('Store', 'pile75', bus='hub', carrier='gas75', e_nom=60, e_initial=40, e_initial_per_period=True)
    n.add('Load', 'town75', bus='hub', p_set=[60, 80, 70, 50, 90, 110, 100, 80])
    n.add(
        'GlobalConstraint',
        'co2_2030',
        type='primary_energy',
        carrier_attribute='co2_emissions',
        sense='<=',
        constant=600,
        investment_period=2030,
    )
    return n
```

</details>
<!-- reference:rung_75_period_primary_energy_storage:end -->

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

| network | objective |
| --- | --- |
| the battery without `max_hours` | `11343.8333` |
| the battery's efficiencies at `1` | `11174.2333` |
| the battery's discharge cost at `0` | `11317.3444` |
| the reservoir without inflow | `12523.7796` |
| the reservoir's spill cost at `0` | `11329.1944` |
| the reservoir without `max_hours` | `8538.7333` |
| the lossy store's charging cost at `0` | `11332.0833` |
| the lossy store's efficiency at `1` | `11043.0167` |

| PyPSA | status | note |
| --- | --- | --- |
| [`Store-p_store`](#variable-domains) | done | every store, held at zero where it does not split its dispatch |
| [`Store-spill`](#variable-domains) | done | `where: inflow > 0`, [`missing: 0`](../reference/language/absence.md#missing), with bounds on the variable, as `StorageUnit-spill` |
| [`Store-fix-p-*`](#store-fix-p-lower), [`Store-ext-p-*`](#store-ext-p-lower) | done | on `p + p_store`, where `max_hours` has a value, and the floor of zero for a store that splits |
| [`Store-fix-p_store-*`](#store-fix-p_store-lower), [`Store-ext-p_store-*`](#store-ext-p_store-lower) | done | the cap of zero for a store that does not split |
| [`Store-energy_balance`](#store-energy_balance) | done | both efficiencies, inflow and spill |
| [`marginal_cost_dispatch`, `marginal_cost_store`, `spill_cost` of a Store](#objective) | done | in `Store_opex` |

<!-- reference:rung_76_store_power:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `11362.944444444443`, 139 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_76_store_power.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 76: stores that cover a storage unit — a power rating through `max_hours`, an efficiency each way, inflow and spill, and a cost each way."""

from __future__ import annotations

import spine


def build():
    """The spine plus four stores: a rated battery with two efficiencies, a reservoir with inflow, an extendable lossy store and an unrated extendable one, under a swinging load."""
    n = spine.build()
    n.add(
        'Store',
        'battery76',
        bus='south',
        e_nom=40,
        max_hours=2,
        efficiency_store=0.9,
        efficiency_dispatch=0.95,
        marginal_cost_dispatch=1,
        e_cyclic=True,
    )
    n.add(
        'Store',
        'reservoir76',
        bus='south',
        e_nom=60,
        max_hours=4,
        p_min_pu=0,
        inflow=[20, 20, 20, 20],
        spill_cost=2,
        e_initial=50,
    )
    n.add(
        'Store',
        'ext76',
        bus='south',
        e_nom_extendable=True,
        e_nom_max=80,
        capital_cost=1,
        max_hours=4,
        efficiency_store=0.8,
        marginal_cost_store=0.5,
        e_cyclic=True,
    )
    n.add('Store', 'plain76', bus='north', e_nom_extendable=True, capital_cost=3, e_cyclic=True)
    n.add('Load', 'swing76', bus='south', p_set=[0, 60, 0, 70])
    return n
```

</details>
<!-- reference:rung_76_store_power:end -->

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

| PyPSA                                                                                                                              | status | note                                       |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------ |
| [`Generator-e_sum_min/max`](#generator-e_sum_min) under `multi_investment_periods`                                                 | done   | each snapshot weighs its period's `years`  |
| [`Link-e_sum_min/max`](#link-e_sum_min), [`Process-e_sum_min/max`](#process-e_sum_min), [`Store-e_sum_min/max`](#store-e_sum_min) | done   | the same row over each component's `p`     |

<!-- reference:rung_77_energy_limits:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `11618.75`, 143 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_77_energy_limits.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 77: energy limits on every dispatching component — `e_sum_min` and `e_sum_max` on a generator, link, process and store, with each period weighted by its years."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

OPTIMIZE = {'multi_investment_periods': True}


def build():
    """A whole network, not the spine: eight snapshots over two periods of unequal years, a cheap supply on a fuel bus, and four units under energy limits feeding a hub."""
    import pypsa

    n = pypsa.Network()
    n.snapshots = pd.MultiIndex.from_tuples(
        [(2020, datetime(2020, 1, 1, t)) for t in range(4)] + [(2030, datetime(2030, 1, 1, t)) for t in range(4)]
    )
    n.investment_periods = [2020, 2030]
    n.investment_period_weightings['objective'] = [1.0, 0.5]
    n.investment_period_weightings['years'] = [5.0, 10.0]
    n.snapshot_weightings['generators'] = [1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0]
    n.add('Bus', ['fuel', 'hub'])
    n.add('Generator', 'well77', bus='fuel', p_nom=200, marginal_cost=1)
    n.add('Generator', 'cheap77', bus='hub', p_nom=50, marginal_cost=5, e_sum_max=2500)
    n.add('Generator', 'dear77', bus='hub', p_nom=200, marginal_cost=80)
    n.add('Link', 'pipe77', bus0='fuel', bus1='hub', p_nom=40, marginal_cost=90, e_sum_min=400, e_sum_max=5000)
    n.add(
        'Process',
        'plant77',
        bus0='fuel',
        bus1='hub',
        rate0=-1.25,
        p_nom=40,
        marginal_cost=6,
        e_sum_min=100,
        e_sum_max=1800,
    )
    n.add('Store', 'pile77', bus='hub', e_nom=200, e_initial=200, marginal_cost=3, e_sum_min=-50, e_sum_max=150)
    n.add('Load', 'hub_load77', bus='hub', p_set=[90, 110, 100, 80, 100, 120, 110, 90])
    return n
```

</details>
<!-- reference:rung_77_energy_limits:end -->

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

| PyPSA                                         | status | note                                     |
| --------------------------------------------- | ------ | ---------------------------------------- |
| [`Store-cycles_max`](#store-cycles_max)       | done   | over `Store_e_nom_effective`             |

<!-- reference:rung_78_store_cycles:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `15004.0`, 75 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_78_store_cycles.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 78: a cycle limit on a store — the discharge over the horizon is at most `cycles_max` times the build, fixed or chosen."""

from __future__ import annotations

import spine


def build():
    """The spine plus a fixed and an extendable store on the south bus, each with a cycle limit, under a swinging load."""
    n = spine.build()
    n.add('Store', 'cell78', bus='south', e_nom=30, e_cyclic=True, cycles_max=0.5)
    n.add('Store', 'pack78', bus='south', e_nom_extendable=True, capital_cost=1, e_cyclic=True, cycles_max=0.5)
    n.add('Load', 'swing78', bus='south', p_set=[0, 60, 0, 70])
    return n
```

</details>
<!-- reference:rung_78_store_cycles:end -->

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

| PyPSA                                                                                           | status  | note                                                                         |
| ----------------------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------- |
| [`FlowBased-net_position`](#variable-domains)                                                   | done    | where `Bus_flow_based_zone`, and in `Bus_injection` as `FlowBased_injection` |
| [`GlobalConstraint-ram`](#flow_based)                                                           | done    | per CNEC and snapshot, where `GlobalConstraint_ram` has a value              |
| [`FlowBased-balance`](#flowbased-balance)                                                       | done    | per domain, through `Bus_flow_based_domain`                                  |
| [`flow_based`](#flow_based) with a sense other than `<=`, and the domain checks PyPSA raises on | refused | [Refusals](#refusals)                                                        |

<!-- reference:rung_79_flow_based:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `17005.31914893617`, 55 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_79_flow_based.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 79: flow-based market coupling — three zones trade through their net positions under two critical network elements, one of them with a corridor link."""

from __future__ import annotations

import math

import pandas as pd


def build():
    """A whole network, not the spine: three zone buses with their own supply and load, a corridor link from one to another, and a two-row flow-based domain."""
    import pypsa

    n = pypsa.Network()
    n.set_snapshots(pd.date_range('2015-01-01', periods=4, freq='h'))
    n.snapshot_weightings['objective'] = [2.0, 1.5, 2.5, 3.0]
    n.add('Bus', ['north79', 'centre79', 'south79'])
    n.add('Generator', 'hydro79', bus='north79', p_nom=200, marginal_cost=5)
    n.add('Generator', 'coal79', bus='centre79', p_nom=200, marginal_cost=30)
    n.add('Generator', 'gas79', bus='south79', p_nom=200, marginal_cost=60)
    n.add('Load', 'north_load79', bus='north79', p_set=20)
    n.add('Load', 'centre_load79', bus='centre79', p_set=[40, 50, 60, 50])
    n.add('Load', 'south_load79', bus='south79', p_set=[80, 90, 100, 70])
    n.add('Link', 'hvdc79', bus0='north79', bus1='south79', p_nom=30, p_min_pu=-1)
    ptdf = pd.DataFrame(
        {'north79': [0.6, 0.2], 'centre79': [0.1, 0.5], 'south79': [-0.3, -0.2], 'hvdc79': [-0.4, 0.0]},
        index=['ns79', 'cs79'],
    )
    ram = pd.DataFrame({'ns79': [40.0, 40.0, 40.0, 40.0], 'cs79': [30.0, math.nan, 25.0, 30.0]}, index=n.snapshots)
    n.c.global_constraints.add_flow_based(ptdf, ram=ram, domain='core79')
    return n
```

</details>
<!-- reference:rung_79_flow_based:end -->

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

| PyPSA                                                                                                                   | status | note                                                    |
| ----------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------- |
| [`Generator-maint-modstatus-*`](#generator-maint-modstatus-le-status), fixed modular, and the `Link` and `Process` ones | done   | bound by `Generator_maintenance_modules`, `p_nom` based |

<!-- reference:rung_80_fixed_modular_maintenance:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `16026.25`, 179 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_80_fixed_modular_maintenance.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 80: maintenance of fixed modular committable units — a generator, a link and a process of four modules each take all their modules off for one event."""

from __future__ import annotations

import spine


def build():
    """The spine plus a shop bus served by a fixed modular committable generator, link and process, each maintainable, with a dear backup."""
    n = spine.build()
    n.add('Bus', 'shop')
    unit = {
        'p_nom': 40,
        'p_nom_mod': 10,
        'committable': True,
        'maintainable': True,
        'maintenance_duration': 1,
    }
    n.add('Generator', 'gen80', bus='shop', marginal_cost=5, **unit)
    n.add('Link', 'link80', bus0='north', bus1='shop', marginal_cost=1, **unit)
    n.add('Process', 'process80', bus0='north', bus1='shop', rate0=-1.25, marginal_cost=1, **unit)
    n.add('Generator', 'shop_backup', bus='shop', p_nom=200, marginal_cost=60)
    n.add('Load', 'shop_load', bus='shop', p_set=[70, 90, 60, 80])
    return n
```

</details>
<!-- reference:rung_80_fixed_modular_maintenance:end -->

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

| PyPSA                                                                 | status | note                                                                                                       |
| --------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------- |
| `Generator-marginal_cost_piecewise_chord`, `_domain_lo`, `_domain_hi` | split  | [`Generator_marginal_cost_lp`](#generator_marginal_cost_lp), where `Generator_marginal_cost_as_lp` is true |

<!-- reference:rung_81_piecewise_marginal_cost:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `30890.0`, 60 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_81_piecewise_marginal_cost.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 81: a piecewise `marginal_cost` curve — a generator that is not committable pays a convex cost curve, which PyPSA states as the line of each segment."""

from __future__ import annotations

import spine


def build():
    """The spine plus a generator on the south bus whose marginal cost climbs from 12 to 20 to 45 over three segments, and a south load that walks it up every segment."""
    n = spine.build()
    n.add('Generator', 'curve81', bus='south', p_nom=80, marginal_cost={0.0: 0.0, 0.25: 12.0, 0.5: 20.0, 1.0: 45.0})
    n.add('Load', 'south_peak81', bus='south', p_set=[20, 60, 100, 170])
    return n
```

</details>
<!-- reference:rung_81_piecewise_marginal_cost:end -->

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
[special ordered set](../reference/glossary.md#special-ordered-set-sos) of type
2 (SOS2). The file keeps the increments there, which reach the same
optimum. Under `linearized_unit_commitment`, the status is a share between 0
and 1, and a curve gate is binary or integer. So
[the patch](pypsa_linearized_uc.md) assumes that no generator with a curve is
committable.

The curve of `block82` is not convex: its first 20 MW cost 40 per MWh and the
rest 15. It stays off in the first two snapshots, where its status holds its
curve at zero. In the third snapshot it runs at 84 MW: it pays for its dear
first 20 MW to reach the cheap rest. `curve82` drops to 20 MW there. In the last
snapshot it runs at 100 MW. PyPSA solves to `26135.0`.

| PyPSA                                                                                                                               | status | note                                                                                                                                                     |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Generator-marginal_cost_piecewise_delta`, `_order_binary`, `_delta_bound`, `_fill_order`, `_binary_order`, `_link`, `_output_link` | split  | [`Generator_marginal_cost_incremental`](#generator_marginal_cost_incremental), where `Generator_marginal_cost_as_lp` is false, and in place of SOS2 rows |
| `Generator-marginal_cost_piecewise_active_bound`                                                                                    | split  | where `Generator_status` exists, and no row at gate 1                                                                                                    |

<!-- reference:rung_82_piecewise_marginal_cost_committable:begin -->
> ✔ `pypsa 1.4.0.post1.dev54+g72a124187` solves this rung's network at objective `26135.0`, 164 rows.

<details markdown="1">
<summary>The network, as PyPSA code</summary>

`rung_82_piecewise_marginal_cost_committable.py`

```python
# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Rung 82: a piecewise `marginal_cost` curve on a committable generator — its status gates the curve, and PyPSA states every curve of the call by increments filled in order."""

from __future__ import annotations

import spine


def build():
    """Rung 81's network plus a committable generator on the south bus whose curve is not convex: its first 20 MW cost 40 and the rest 15, and every snapshot on costs 50."""
    n = spine.build()
    n.add('Generator', 'curve82', bus='south', p_nom=80, marginal_cost={0.0: 0.0, 0.25: 12.0, 0.5: 20.0, 1.0: 45.0})
    n.add(
        'Generator',
        'block82',
        bus='south',
        p_nom=100,
        committable=True,
        stand_by_cost=50,
        marginal_cost={0.0: 0.0, 0.2: 40.0, 1.0: 15.0},
    )
    n.add('Load', 'south_peak82', bus='south', p_set=[20, 60, 100, 180])
    return n
```

</details>
<!-- reference:rung_82_piecewise_marginal_cost_committable:end -->

## Refusals

PyPSA raises on the data in the table below, warns on it, or handles it outside
its general rows. None of these refusals is a [limit](../about/limits.md) of the
language. The file states eight of the checks as
[assumptions](../reference/language/assumptions.md), which a tool runs when it
attaches the data.

| PyPSA raises                                                                                         | on                                                                                                                                                                                        | here                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ValueError`, `optimize.py:506-513`                                                                  | a nonzero `marginal_cost_quadratic` on any Generator, Link, Process, StorageUnit or Store under a risk preference, `omega = 0` included                                                   | Where `CVaR_omega` has a row, the file states an assumption: [`Generator_marginal_cost_quadratic_without_risk_preference`](#generator_marginal_cost_quadratic_without_risk_preference), and the `Link`, `Process`, `StorageUnit` and `Store` ones.                                                                                                                                                                                                                                                    |
| `ValueError`, `constraints.py:1953`                                                                  | fixed modular `p_nom` not a multiple of `p_nom_mod`                                                                                                                                       | The file states a fractional module cap.                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `ValueError`, `constraints.py:1605`                                                                  | load on a bus with nothing attached                                                                                                                                                       | The file states no row for the bus, so its load goes unserved.                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `ValueError`, `optimize.py:472`                                                                      | no component carries a cost                                                                                                                                                               | The file states a feasibility problem.                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `NotImplementedError`, `global_constraints.py:473`, `:525`, `:679`, `:727`                           | storage that carries its level across periods in a `primary_energy` or `operational_limit` row, with period `years` `!= 1`                                                                | The file states an assumption: [`StorageUnit_primary_energy_carried_over_has_unit_years`](#storageunit_primary_energy_carried_over_has_unit_years), [`StorageUnit_operational_limit_carried_over_has_unit_years`](#storageunit_operational_limit_carried_over_has_unit_years), and the `Store` ones.                                                                                                                                                                                                  |
| `KeyError`, `global_constraints.py:490`, `:542`, `:696`, `:741` (PyPSA/PyPSA#2113) | a `primary_energy` or `operational_limit` row over storage that reopens per period, on a network with scenarios | Where there is more than one scenario, the file states an assumption: [`StorageUnit_primary_energy_per_period_without_scenarios`](#storageunit_primary_energy_per_period_without_scenarios), [`StorageUnit_operational_limit_per_period_without_scenarios`](#storageunit_operational_limit_per_period_without_scenarios), and the `Store` ones. |
| `ValueError`, `global_constraints.py:380-385`, `:619-624`                                            | a `primary_energy` or `operational_limit` row that names an `investment_period` without `multi_investment_periods`                                                                        | You compute `GlobalConstraint_counts_snapshot` in data prep.                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `ValueError`, `constraints.py:2513`, `:2691`                                                         | an extendable lossy branch with `s_nom_max = inf`, either mode                                                                                                                            | You compute `Line_loss_max` and `Transformer_loss_max` in data prep.                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `RuntimeError`, `constraints.py:2739`                                                                | the secant loop passing `max_segments`                                                                                                                                                    | You compute the `segment` axis in data prep.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `ValueError`, `abstract.py:634-643`                                                                  | an outage named in `branch_outages` that is active in no period of the run                                                                                                                | `Line_BODF` and `Transformer_BODF` have no value for the outage, so the file states no copy.                                                                                                                                                                                                                                                                                                                                                                                                          |
| `ConsistencyError`, `consistency.py:1250` | a bus port, `*_nom_set`, `delay`, `cyclic_delay`, `v_nom`, `x_pu_eff` or `r_pu_eff` that differs by scenario (`constants.py:26-58`) | The file states no such difference, because the ports, `Generator_p_nom_set` and the others, and `Link_output_delay` and the others span no `scenario`. `Line_cycle_weight`, `Line_BODF` and the `Transformer` ones span no `scenario` either. |
| `NotImplementedError`, `global_constraints.py:68-70`                                                 | a `tech_capacity_expansion_limit` row on a network with scenarios                                                                                                                         | Where there is more than one scenario, the file states an assumption: [`GlobalConstraint_tech_capacity_expansion_limit_without_scenarios`](#globalconstraint_tech_capacity_expansion_limit_without_scenarios). One scenario and none look alike in the file, and PyPSA refuses one scenario too.                                                                                                                                                                                                      |
| `ConsistencyError`, `consistency.py:1531-1585`                                                       | a maintainable component whose `maintenance_duration` or `maintenance_events` is not positive, whose events do not fit the weighted horizon, or that is extendable with `p_nom_max = inf` | The file states an assumption: [`Generator_maintenance_events_positive`](#generator_maintenance_events_positive), [`-duration_positive`](#generator_maintenance_duration_positive), [`-duration_fits_the_horizon`](#generator_maintenance_duration_fits_the_horizon), [`-events_fit_the_horizon`](#generator_maintenance_events_fit_the_horizon), [`-build_cap_is_finite`](#generator_maintenance_build_cap_is_finite), and the `Link` and `Process` ones.                                            |
| `ValueError`, `piecewise.py:277-297` | a piecewise `marginal_cost` curve on an extendable generator, or on one whose `p_nom` is zero, missing or infinite | The file states an assumption: [`Generator_marginal_cost_curve_on_a_fixed_build`](#generator_marginal_cost_curve_on_a_fixed_build). |
| `KeyError`, `constraints.py:1916`                                                                    | a `*_nom_set` on a unit that is not extendable, or that has `active = False`                                                                                                              | The file states no row: [`Generator-p_nom_set`](#generator-p_nom_set) and the others exist only where the build is extendable, and an inactive unit is fixed ([Data prep](#data-prep)).                                                                                                                                                                                                                                                                                                               |
| `KeyError`, `constraints.py:2943` | `e_sum_min` or `e_sum_max` on a Generator, Link, Process or Store with `active = False` | The file states the row with no variable: [`Generator-e_sum_min`](#generator-e_sum_min) and its siblings are `0 >= e_sum_min`, which fails where the floor is positive. |
| `ValueError`, `constraints.py:1606-1611`                                                             | a loaded bus where every unit and branch has retired in some snapshot                                                                                                                     | The file states the row with no variable: [`Bus-nodal_balance`](#bus-nodal_balance) requires the load alone to be zero, and no solution meets it.                                                                                                                                                                                                                                                                                                                                                     |
| `ValueError`, `components/descriptors.py:141-144`                                                    | a `transmission_volume_expansion_limit`, `transmission_expansion_cost_limit` or `tech_capacity_expansion_limit` row that names an `investment_period` outside `n.investment_periods`      | You compute `Line_volume_weight`, `Line_expansion_cost_weight`, `Line_tech_capacity_weight` and the other components' ones in data prep.                                                                                                                                                                                                                                                                                                                                                              |
| `ValueError`, `flow_based.py:109-114` | a `flow_based` row whose sense is not `<=` | The file states an assumption: [`GlobalConstraint_flow_based_sense_is_le`](#globalconstraint_flow_based_sense_is_le). |
| `ValueError`, `flow_based.py:71-93`, `:116-166`, `:196-200` | a flow-based domain where a line, transformer or link that is no corridor joins two zones, a zone has nothing attached, a `ptdf_<name>` names no bus or link, a corridor is inactive or touches no zone, a zone is in two domains, only some rows name a domain, or a row has no `ram` | You compute `GlobalConstraint_zonal_ptdf`, `GlobalConstraint_link_ptdf`, `Bus_flow_based_zone` and `Bus_flow_based_domain` in data prep. |
| a warning, or `ConsistencyError` under `strict`, `consistency.py:235-287`                            | a transformer with `phase_shift_min > phase_shift_max`, or a decided phase shift with an infinite bound                                                                                   | The file states the rows as PyPSA builds them. In the first case the transformer keeps its fixed `phase_shift`, and in the second [`Transformer-phase_shift`](#variable-domains) is unbounded on that side.                                                                                                                                                                                                                                                                                           |
| nothing, and PyPSA lags by elapsed time, `multiports.py:100-133`                                     | a Link or Process port with `delay > 0` under a `generators` weighting that is not one value over the horizon                                                                             | The file states an assumption: [`Link_output_delay_under_uniform_weighting`](#link_output_delay_under_uniform_weighting), and the `Process` one. The file states the delay as a shift by whole snapshots, the same number in every period (#299).                                                                                                                                                                                                                                                     |
| nothing, and PyPSA takes `0 * inf` as `0`, `constraints.py:129-134`                                  | a fixed build of `inf` where its least or most per-unit output is zero                                                                                                                    | The file states no assumption. [`Generator-fix-p-lower`](#generator-fix-p-lower) and the other fixed bounds contain the product as written, so the row is `0 * inf`, which has no value.                                                                                                                                                                                                                                                                                                              |

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
  [`Kirchhoff-Voltage-Law`](#kirchhoff-voltage-law) by the carrier of its
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

## The file

<!-- gallery:begin -->
The file states a plain `n.optimize()`, its multi-period class under the `multi_investment_periods` keyword, and its stochastic class, which `n.set_scenarios(...)` sets. Every quantity chosen once the future is known (second-stage) spans the futures dispatch is chosen in (`scenario`). Capacity is chosen once, before the future is known, and paid at its expected cost in each investment `period` its build year and lifetime span. Operation is the expectation over the scenarios' weights, with a share priced at the worst-outcome mean cost (CVaR) only where a risk preference is set. A plain run's data has one scenario, one period, unit weights, no outage and every `active` flag true, so the problem is the standard one. On a security-constrained run, PyPSA copies each branch flow limit once per `outage`, and the outage factors, `active` flags and scenario weights come from data prep.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{B}`$ | index $`b`$ — `breakpoint` — the corners of a piecewise-linear curve, in order. A curve runs over the breakpoints its data has rows for, so curves may differ in length |
| $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Bus\_flow\_based\_domain}: \mathcal{N} \to \mathcal{L},\ \mathrm{Generator\_bus}: \mathcal{G} \to \mathcal{N},\ \mathrm{Line\_bus0}: \mathcal{K} \to \mathcal{N},\ \mathrm{Line\_bus1}: \mathcal{K} \to \mathcal{N},\ \mathrm{Link\_bus0}: \mathcal{L} \to \mathcal{N},\ \mathrm{Link\_output\_bus}: \mathcal{O} \to \mathcal{N},\ \mathrm{Load\_bus}: \mathcal{D} \to \mathcal{N},\ \mathrm{Process\_output\_bus}: \mathcal{R} \to \mathcal{N},\ \mathrm{StorageUnit\_bus}: \mathcal{S} \to \mathcal{N},\ \mathrm{Store\_bus}: \mathcal{V} \to \mathcal{N},\ \mathrm{Transformer\_bus0}: \mathcal{M} \to \mathcal{N},\ \mathrm{Transformer\_bus1}: \mathcal{M} \to \mathcal{N}`$, `Bus_flow_based_domain` is `absent` where the data has no row — network nodes |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` with $`\mathrm{Generator\_carrier}: \mathcal{G} \to \mathcal{I},\ \mathrm{Line\_carrier}: \mathcal{K} \to \mathcal{I},\ \mathrm{Link\_carrier}: \mathcal{L} \to \mathcal{I},\ \mathrm{Process\_carrier}: \mathcal{J} \to \mathcal{I},\ \mathrm{StorageUnit\_carrier}: \mathcal{S} \to \mathcal{I},\ \mathrm{Store\_carrier}: \mathcal{V} \to \mathcal{I}`$ — energy carriers, what a growth limit is set per |
| $`\mathcal{C}`$ | index $`c`$ — `cycle` — independent cycles of the passive network graph, the cycle basis, data prep. Each period has its own basis, of the branches that are active in it. A label is a position in that period's basis, so one label is a different cycle in another period |
| $`\mathcal{L}`$ | index $`l`$ — `flow_based_domain` with $`\mathrm{Bus\_flow\_based\_domain}: \mathcal{N} \to \mathcal{L}`$, `Bus_flow_based_domain` is `absent` where the data has no row — the flow-based domains, each with its own zero-sum balance of net positions (PyPSA's `domain` of a `flow_based` row), data prep. A run whose flow-based rows name no domain has one. A run without them has none |
| $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_bus}: \mathcal{G} \to \mathcal{N},\ \mathrm{Generator\_carrier}: \mathcal{G} \to \mathcal{I},\ \mathrm{Generator\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{G} \times \Xi \times \mathcal{T}`$, `Generator_maintenance_cover` is `absent` where the data has no row — generating units, each on one bus |
| $`\mathcal{O}`$ | index $`o`$ — `global_constraint` — PyPSA's `GlobalConstraint` rows, one label per declared limit |
| $`\mathcal{K}`$ | index $`k`$ — `line` with $`\mathrm{Line\_bus0}: \mathcal{K} \to \mathcal{N},\ \mathrm{Line\_bus1}: \mathcal{K} \to \mathcal{N},\ \mathrm{Line\_carrier}: \mathcal{K} \to \mathcal{I},\ \mathrm{Outage\_line}: \mathcal{K}^{\mathrm{out}} \to \mathcal{K}`$, `Outage_line` is `absent` where the data has no row — passive branches, each between two buses, their flow set by impedance |
| $`\mathcal{L}`$ | index $`l`$ — `link` with $`\mathrm{Link\_bus0}: \mathcal{L} \to \mathcal{N},\ \mathrm{Link\_carrier}: \mathcal{L} \to \mathcal{I},\ \mathrm{Link\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{L} \times \Xi \times \mathcal{T},\ \mathrm{Link\_output\_link}: \mathcal{O} \to \mathcal{L}`$, `Link_maintenance_cover` is `absent` where the data has no row — controllable connections, each from one bus to the buses it delivers to |
| $`\mathcal{O}`$ | index $`o`$ — `link_output` with $`\mathrm{Link\_output\_bus}: \mathcal{O} \to \mathcal{N},\ \mathrm{Link\_output\_link}: \mathcal{O} \to \mathcal{L}`$ — a link's output ports, one label per port a link declares. The labels are PyPSA's `bus1`, `bus2`, … columns read long, data prep. A link of any number of output ports is then one term in the balance |
| $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{Load\_bus}: \mathcal{D} \to \mathcal{N}`$ — demands, each on one bus |
| $`\mathcal{K}^{\mathrm{out}}`$ | index $`\kappa`$ — `outage` with $`\mathrm{Outage\_line}: \mathcal{K}^{\mathrm{out}} \to \mathcal{K},\ \mathrm{Outage\_transformer}: \mathcal{K}^{\mathrm{out}} \to \mathcal{M}`$, `Outage_line` is `absent` where the data has no row, `Outage_transformer` is `absent` where the data has no row — the passive branches a security-constrained run takes out one at a time (PyPSA's `branch_outages`), each a line or a transformer. A plain run has none |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods. It is PyPSA's `investment_periods` |
| $`\mathcal{J}`$ | index $`j`$ — `process` with $`\mathrm{Process\_carrier}: \mathcal{J} \to \mathcal{I},\ \mathrm{Process\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{J} \times \Xi \times \mathcal{T},\ \mathrm{Process\_output\_process}: \mathcal{R} \to \mathcal{J}`$, `Process_maintenance_cover` is `absent` where the data has no row — generalised multi-port converters, each with an internal power that every port draws or delivers at its own rate |
| $`\mathcal{R}`$ | index $`r`$ — `process_output` with $`\mathrm{Process\_output\_bus}: \mathcal{R} \to \mathcal{N},\ \mathrm{Process\_output\_process}: \mathcal{R} \to \mathcal{J}`$ — a process's ports, one label per port a process declares. The labels are PyPSA's `bus0`, `bus1`, …, each with a signed `rate`, data prep. A process of any number of ports is then one term in the balance |
| $`\Xi`$ | index $`\xi`$ — `scenario` with $`\mathrm{Generator\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{G} \times \Xi \times \mathcal{T},\ \mathrm{Link\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{L} \times \Xi \times \mathcal{T},\ \mathrm{Process\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{J} \times \Xi \times \mathcal{T}`$, `Generator_maintenance_cover` is `absent` where the data has no row, `Link_maintenance_cover` is `absent` where the data has no row, `Process_maintenance_cover` is `absent` where the data has no row — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{M}`$ | index $`m`$ — `segment` — the cuts a passive branch's loss curve is held above. They are PyPSA's tangents, as many as its `segments` count, or its secants, as many as its tolerance loop places. A lossless run has none |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{Generator\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{G} \times \Xi \times \mathcal{T},\ \mathrm{Link\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{L} \times \Xi \times \mathcal{T},\ \mathrm{Process\_maintenance\_cover} \subseteq \mathcal{T} \times \mathcal{J} \times \Xi \times \mathcal{T},\ \mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$, `Generator_maintenance_cover` is `absent` where the data has no row, `Link_maintenance_cover` is `absent` where the data has no row, `Process_maintenance_cover` is `absent` where the data has no row — dispatch periods |
| $`\mathcal{S}`$ | index $`s`$ — `storage_unit` with $`\mathrm{StorageUnit\_bus}: \mathcal{S} \to \mathcal{N},\ \mathrm{StorageUnit\_carrier}: \mathcal{S} \to \mathcal{I}`$ — storage units, dispatch and store behind one bus connection |
| $`\mathcal{V}`$ | index $`v`$ — `store` with $`\mathrm{Store\_bus}: \mathcal{V} \to \mathcal{N},\ \mathrm{Store\_carrier}: \mathcal{V} \to \mathcal{I}`$ — pure energy stores, each on one bus |
| $`\mathcal{M}`$ | index $`m`$ — `transformer` with $`\mathrm{Outage\_transformer}: \mathcal{K}^{\mathrm{out}} \to \mathcal{M},\ \mathrm{Transformer\_bus0}: \mathcal{M} \to \mathcal{N},\ \mathrm{Transformer\_bus1}: \mathcal{M} \to \mathcal{N}`$, `Outage_transformer` is `absent` where the data has no row — passive branches between two buses, their flow set by impedance and tap ratio, with a phase shift fixed or optimised |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{zone}`$ | `Bus_flow_based_zone` over $`\mathcal{N}`$ — whether a bus is a zone of a flow-based domain: some `flow_based` row has its `ptdf_<bus>` column, data prep |
| $`\alpha`$ | `CVaR_alpha` (scalar), `absent` where the data has no row — PyPSA's `risk_preference['alpha']` — the confidence level. The tail is the other `1 - alpha` of the probability. `CVaR_alpha` has a value exactly where `CVaR_omega` has one |
| $`\omega`$ | `CVaR_omega` (scalar), $`0`$ where the data has no row — PyPSA's `risk_preference['omega']` — the share of operating cost priced at the tail rather than in expectation. `CVaR_omega` has a value only where a risk preference is set. Without a risk preference, the file has no CVaR variables or rows. With `omega = 0`, PyPSA builds them, and the optimum is the risk-neutral one |
| $`\overline{\Delta}`$ | `Carrier_max_growth` over $`\mathcal{I}`$, `absent` where the data has no row — most capacity of a carrier that may be added in a period. No value means no limit. It is the least over the scenarios, as PyPSA takes it (`global_constraints.py:239-243`), data prep. PyPSA reads it only under `multi_investment_periods` (`global_constraints.py:232-233`). Otherwise you feed no value in data prep |
| $`\mathrm{r}`$ | `Carrier_max_relative_growth` over $`\mathcal{I}`$ — share of the previous period's additions that may be added on top: the least over the scenarios, as PyPSA takes it, data prep |
| $`\mathrm{on}`$ | `Generator_active` over $`\mathcal{G} \times \mathcal{T}`$ — whether a generator is active in a snapshot's period. It is PyPSA's `active`, from build year and lifetime, data prep |
| $`\mathrm{act}`$ | `Generator_active_asset` over $`\mathcal{G}`$ — whether a generator is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{M}`$ | `Generator_big_m` over $`\mathcal{G} \times \Xi`$, `absent` where the data has no row — the bound a committed extendable generator's big-M rows release it by, data prep. It is the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu` (`components.py:1100-1171`). Without that keyword, it is ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`. Where there is none of them, it is 1e6. Below the output a solve wants, it caps that output |
| $`\mathrm{c}^{\mathrm{cap}}`$ | `Generator_capital_cost` over $`\mathcal{G} \times \Xi`$ — cost of one unit of nominal power for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1176-1197`, `costs.py:102-203`) |
| $`\mathrm{W}`$ | `Generator_capital_weight` over $`\mathcal{G}`$ — the sum of period weights a generator is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{com}`$ | `Generator_committable` over $`\mathcal{G}`$ — whether output is gated by an on/off status decision |
| $`\mathrm{rest}`$ | `Generator_down_time_brought_in` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — one while the down time a unit brought into the horizon is still running, zero after. It is PyPSA's stop `down_time_before` snapshots before the first, counted while `min_down_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep |
| $`\overline{\mathrm{E}}`$ | `Generator_e_sum_max` over $`\mathcal{G} \times \Xi`$ — most energy over the horizon: a fuel or emission budget in energy terms. It is infinity where no cap is meant |
| $`\underline{\mathrm{E}}`$ | `Generator_e_sum_min` over $`\mathcal{G} \times \Xi`$ — least energy over the horizon. It is minus infinity where no floor is meant |
| $`\mathrm{new}`$ | `Generator_first_active` over $`\mathcal{G} \times \mathcal{Y}`$ — one in the first period a generator is active in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`) |
| $`\mathrm{mnt}`$ | `Generator_maintainable` over $`\mathcal{G}`$ — whether a generator must be taken off for maintenance within the horizon: in any scenario, as PyPSA takes the union over them (`components.py:1018-1021`) |
| $`\tau^{\mathrm{mnt}}`$ | `Generator_maintenance_duration` over $`\mathcal{G} \times \Xi`$, `absent` where the data has no row — the hours of generator weightings one maintenance event covers, PyPSA's `maintenance_duration`. It has no value where the generator is not maintainable. No row contains it. In data prep you turn it into `Generator_maintenance_cover` and `Generator_maintenance_start_blocked`. The assumptions state that it fits the horizon |
| $`\mathrm{n}^{\mathrm{mnt}}`$ | `Generator_maintenance_events` over $`\mathcal{G} \times \Xi`$ — how many maintenance events occur within the horizon |
| $`\gamma`$ | `Generator_maintenance_pu` over $`\mathcal{G} \times \Xi`$ — the share of the build a maintenance event takes off |
| $`\mathrm{blk}`$ | `Generator_maintenance_start_blocked` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — true where no maintenance event may start, data prep. The snapshots it would cover there run past the end of the horizon or into one the generator is not active in. It is PyPSA's `active & ~valid`, from `maintenance_duration` and the generator weightings |
| $`\mathrm{c}`$ | `Generator_marginal_cost` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — cost of one unit of output |
| $`\mathrm{C}^{\mathrm{curve}}`$ | `Generator_marginal_cost_curve_cost` over $`\mathcal{B} \times \mathcal{G}`$, `absent` where the data has no row — the running cost at each breakpoint of a generator's piecewise `marginal_cost` curve: zero at the first, then each segment's width in output times the `marginal_cost` at its upper breakpoint, summed, data prep. It is linopy's `Slopes(...).to_breakpoints` (`piecewise.py:303-305`) |
| $`\mathrm{p}^{\mathrm{curve}}`$ | `Generator_marginal_cost_curve_p` over $`\mathcal{B} \times \mathcal{G}`$, `absent` where the data has no row — the output at each breakpoint of a generator's piecewise `marginal_cost` curve: PyPSA's `p_pu` breakpoints times `p_nom`, data prep. A generator with no curve has no rows |
| $`\mathrm{c}^{(2)}`$ | `Generator_marginal_cost_quadratic` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — cost of the square of one unit of output |
| $`\mathrm{DT}`$ | `Generator_min_down_time` over $`\mathcal{G} \times \Xi`$ — least snapshots a unit stays off once stopped |
| $`\mathrm{UT}`$ | `Generator_min_up_time` over $`\mathcal{G} \times \Xi`$ — least snapshots a unit stays on once started |
| $`\mathrm{N}^{\mathrm{fix}}`$ | `Generator_modules_installed` over $`\mathcal{G} \times \Xi`$ — how many whole modules a committable build has in place, data prep. It is `Generator_p_nom / Generator_p_nom_mod` where a fixed build is modular, and one where it is not. PyPSA refuses a fixed modular build whose nominal power is not a whole number of modules |
| $`\mathrm{b}`$ | `Generator_operational_limit_weight` over $`\mathcal{G} \times \mathcal{O} \times \Xi`$, `absent` where the data has no row — one where the generator is in the row's set, data prep. One outside it has no row |
| $`\mathrm{p}^{0}`$ | `Generator_p_init` over $`\mathcal{G} \times \Xi`$, $`0`$ where the data has no row — the output a unit brought into the horizon (PyPSA's `p_init`), read only where the unit came in running. No value means it is unknown, and the unit then has no ramp row at the first snapshot |
| $`\overline{\mathrm{p}}`$ | `Generator_p_max_pu` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — most output, per unit of nominal power: an availability profile |
| $`\underline{\mathrm{p}}`$ | `Generator_p_min_pu` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — least output, per unit of nominal power |
| $`\mathrm{nonneg}`$ | `Generator_p_min_pu_nonneg` over $`\mathcal{G}`$ — true where none of the generator's own minimums-per-unit is negative. It is PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep |
| $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\mathcal{G} \times \Xi`$ — nominal power |
| $`\mathrm{ext}`$ | `Generator_p_nom_extendable` over $`\mathcal{G}`$ — whether the nominal power is a decision |
| $`\overline{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_max` over $`\mathcal{G} \times \Xi`$ — most nominal power an extendable generator may be built at |
| $`\underline{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_min` over $`\mathcal{G} \times \Xi`$ — least nominal power an extendable generator may be built at |
| $`\mathrm{p}^{\mathrm{mod}}`$ | `Generator_p_nom_mod` over $`\mathcal{G}`$, `absent` where the data has no row — the module size a build comes in whole numbers of. No value means the build is continuous |
| $`\mathrm{p}^{\mathrm{nom,set}}`$ | `Generator_p_nom_set` over $`\mathcal{G}`$, `absent` where the data has no row — a given nominal power for an extendable generator. One without a value has no row here |
| $`\mathrm{p}^{\mathrm{set}}`$ | `Generator_p_set` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — a given output schedule. A generator without one has no row here |
| $`\mathrm{a}`$ | `Generator_primary_energy_weight` over $`\mathcal{G} \times \mathcal{O} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — the constrained attribute per unit of energy at the bus: the carrier's `co2_emissions` over the generator's efficiency at the snapshot, data prep. A generator of an unweighted carrier has no row |
| $`\mathrm{rd}`$ | `Generator_ramp_limit_down` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a generator may lower its output between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{rd}^{\mathrm{dn}}`$ | `Generator_ramp_limit_shut_down` over $`\mathcal{G} \times \Xi`$, `absent` where the data has no row — most output in the snapshot before a unit stops, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{\mathrm{up}}`$ | `Generator_ramp_limit_start_up` over $`\mathcal{G} \times \Xi`$, `absent` where the data has no row — most output in the snapshot a unit starts, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}`$ | `Generator_ramp_limit_up` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a generator may raise its output between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{c}^{\mathrm{dn}}`$ | `Generator_shut_down_cost` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — cost of one stop in this snapshot |
| $`\mathrm{sgn}`$ | `Generator_sign` over $`\mathcal{G}`$ — the sign output enters its bus's balance with. It is PyPSA's `sign`, `1` unless given, `-1` for a unit that draws power. PyPSA refuses one that differs by scenario (`constants.py:46`) |
| $`\mathrm{c}^{\mathrm{on}}`$ | `Generator_stand_by_cost` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — cost of one snapshot spent on |
| $`\mathrm{c}^{\mathrm{up}}`$ | `Generator_start_up_cost` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — cost of one start in this snapshot |
| $`\mathrm{u}^{0}`$ | `Generator_status_initial` over $`\mathcal{G} \times \Xi`$ — one where the unit was on before the first snapshot, zero where off. It is PyPSA's `up_time_before > 0` for a committable unit, and one for a unit that is not, whose ramp rows PyPSA starts from on (`constraints.py:323`), data prep |
| $`\mathrm{m}`$ | `Generator_tech_capacity_weight` over $`\mathcal{G} \times \mathcal{O}`$, `absent` where the data has no row — one where the generator is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |
| $`\mathrm{hold}`$ | `Generator_up_time_brought_in` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — one while the up time a unit brought into the horizon is still running, zero after. It is PyPSA's start `up_time_before` snapshots before the first, counted while `min_up_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep |
| $`\mathrm{K}`$ | `GlobalConstraint_constant` over $`\mathcal{O} \times \Xi`$ — the constant the total is held against. What a variable cannot represent is folded in here in data prep. That is an initial charge, times its period's years for each counted period where the storage reopens per period, or a non-extendable build. PyPSA reads it per scenario (`global_constraints.py:573`, `:772`, `:851-856`) |
| $`\mathrm{in}`$ | `GlobalConstraint_counts_snapshot` over $`\mathcal{O} \times \Xi \times \mathcal{T}`$, `false` where the data has no row — whether a row counts a snapshot in a scenario (PyPSA's `investment_period`), data prep. It is every snapshot where the row states no period, and only that period's where it states one. A row that states a period the run does not model has no label here, as PyPSA skips it (`global_constraints.py:388`). PyPSA reads the column only under `multi_investment_periods`. It fails on a row that states a period without it (`global_constraints.py:380-385`) |
| $`\mathrm{PTDF}^{f}`$ | `GlobalConstraint_link_ptdf` over $`\mathcal{O} \times \mathcal{L} \times \Xi \times \mathcal{T}`$, $`0`$ where the data has no row — the factor of a `flow_based` row for a corridor link, whose flow enters the row: PyPSA's `ptdf_<link>` column read long, data prep. No value is zero |
| $`\mathrm{RAM}`$ | `GlobalConstraint_ram` over $`\mathcal{O} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — the remaining available margin of a `flow_based` row, one critical network element (CNEC). It may differ by snapshot. No value drops the row in that snapshot (`flow_based.py:201`) |
| $`\mathrm{sense}`$ | `GlobalConstraint_sense` over $`\mathcal{O} \times \Xi`$ — the row's sense in each scenario: `<=`, `>=` or `==`. PyPSA reads a row's sense per scenario (`global_constraints.py:572`, `:771`, `:851-856`) |
| $`\mathrm{type}`$ | `GlobalConstraint_type` over $`\mathcal{O}`$ — which formula the row takes: `primary_energy`, `operational_limit`, `transmission_volume_expansion_limit`, `transmission_expansion_cost_limit`, `tech_capacity_expansion_limit` or `flow_based` |
| $`\mathrm{PTDF}^{z}`$ | `GlobalConstraint_zonal_ptdf` over $`\mathcal{N} \times \mathcal{O} \times \Xi \times \mathcal{T}`$, $`0`$ where the data has no row — the zonal power transfer distribution factor of a `flow_based` row for a zone bus: PyPSA's `ptdf_<bus>` column read long, data prep. It may differ by snapshot. No value is zero, as PyPSA fills it |
| $`\beta`$ | `Line_BODF` over $`\mathcal{K} \times \mathcal{K}^{\mathrm{out}} \times \mathcal{Y}`$, `absent` where the data has no row — the share of an outaged branch's flow a line takes on when that branch goes out (PyPSA's `BODF`), data prep. It comes from the PTDF of the sub-network the period's active branches form. A row exists only where the line and the outage are active in the period and share a sub-network. It is -1 at the outaged line itself. PyPSA takes the factors of the first scenario (`abstract.py:652`), and refuses impedances that differ by scenario (`constants.py:33-35`). So the factors are the same in every scenario |
| $`\mathrm{on}^{s}`$ | `Line_active` over $`\mathcal{K} \times \mathcal{T}`$ — whether a line is active in a snapshot's period. It is PyPSA's `active`, data prep |
| $`\mathrm{act}^{s}`$ | `Line_active_asset` over $`\mathcal{K}`$ — whether a line is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{c}^{\mathrm{cap},s}`$ | `Line_capital_cost` over $`\mathcal{K} \times \Xi`$ — cost of one unit of nominal apparent power for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1176-1197`, `costs.py:102-203`) |
| $`\mathrm{W}^{s}`$ | `Line_capital_weight` over $`\mathcal{K}`$ — the sum of period weights a line is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{x}`$ | `Line_cycle_weight` over $`\mathcal{C} \times \mathcal{K} \times \mathcal{Y}`$, `absent` where the data has no row — the line's series impedance, signed by its orientation in the cycle: the cycle basis, data prep. A line in no cycle has no row. PyPSA builds the cycle basis from the first scenario (`networks.py:1430-1437`), and refuses a `v_nom`, `x_pu_eff` or `r_pu_eff` that differs by scenario (`constants.py:33-35`). So the weight is the same in every scenario |
| $`\mathrm{cc}`$ | `Line_expansion_cost_weight` over $`\mathcal{O} \times \mathcal{K} \times \Xi`$, `absent` where the data has no row — the line's capital cost where its carrier is in the row's set, data prep. Where the row states no `investment_period` under `multi_investment_periods`, it is times the objective weights of the periods the line is active in. A line outside the set, or one that is not active in the row's period, has no row. The capital cost is PyPSA's `capital_cost` property, which is `Line_capital_cost` without `fom_cost` (`components.py:1201-1219`, `global_constraints.py:897-906`) |
| $`\mathrm{new}^{s}`$ | `Line_first_active` over $`\mathcal{K} \times \mathcal{Y}`$ — one in the first period a line is active in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`) |
| $`\overline{\ell}`$ | `Line_loss_max` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — the loss at a line's rating. It is PyPSA's `r_pu_eff * (s_max_pu * s_nom_max)**2`, data prep |
| $`\mathrm{b}`$ | `Line_loss_offset` over $`\mathcal{K} \times \Xi \times \mathcal{M} \times \mathcal{T}`$ — where that cut meets the loss axis: a tangent's `loss_k - slope_k * p_k`, a secant's `-r_pu_eff * p_k * p_k+1`, negative, data prep |
| $`\mathrm{a}`$ | `Line_loss_slope` over $`\mathcal{K} \times \Xi \times \mathcal{M} \times \mathcal{T}`$ — the slope of a cut to the loss curve, data prep. It is a tangent's `2 * r_pu_eff * p_k` at its segment's flow, or a secant's `r_pu_eff * (p_k + p_k+1)` between consecutive breakpoints |
| $`\overline{\mathrm{s}}`$ | `Line_s_max_pu` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — most flow either way, per unit of nominal apparent power |
| $`\mathrm{s}^{\mathrm{nom}}`$ | `Line_s_nom` over $`\mathcal{K} \times \Xi`$ — nominal apparent power |
| $`\mathrm{ext}^{s}`$ | `Line_s_nom_extendable` over $`\mathcal{K}`$ — whether the nominal apparent power is a decision |
| $`\overline{\mathrm{s}}^{\mathrm{nom}}`$ | `Line_s_nom_max` over $`\mathcal{K} \times \Xi`$ — most nominal apparent power an extendable line may be built at |
| $`\underline{\mathrm{s}}^{\mathrm{nom}}`$ | `Line_s_nom_min` over $`\mathcal{K} \times \Xi`$ — least nominal apparent power an extendable line may be built at |
| $`\mathrm{s}^{\mathrm{mod}}`$ | `Line_s_nom_mod` over $`\mathcal{K}`$, `absent` where the data has no row — the module size a build comes in whole numbers of. No value means the build is continuous |
| $`\mathrm{s}^{\mathrm{nom,set}}`$ | `Line_s_nom_set` over $`\mathcal{K}`$, `absent` where the data has no row — a given nominal apparent power for an extendable line. One without a value has no row here |
| $`\mathrm{s}^{\mathrm{set}}`$ | `Line_s_set` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — a given flow schedule. A line without one has no row here |
| $`\mathrm{m}^{l}`$ | `Line_tech_capacity_weight` over $`\mathcal{O} \times \mathcal{K}`$, `absent` where the data has no row — one where the line is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |
| $`\overline{\delta}`$ | `Line_v_ang_max` over $`\mathcal{K} \times \Xi`$, `absent` where the data has no row — the most the voltage angle difference across a line may be either way, in degrees. It is PyPSA's `v_ang_max`. Infinite, and so no row, by default. A line whose carrier is not AC has no row either. The deprecated `v_ang_min` is ignored, as PyPSA ignores it with a `DeprecationWarning` (`constraints.py:1797-1804`) |
| $`\mathrm{len}`$ | `Line_volume_weight` over $`\mathcal{O} \times \mathcal{K} \times \Xi`$, `absent` where the data has no row — the line's length in each scenario where its carrier is in the row's set (`global_constraints.py:874-875`), data prep. A line outside it, or one that is not active in the row's `investment_period`, has no row |
| $`\mathrm{x}^{\mathrm{eff}}`$ | `Line_x_pu_eff` over $`\mathcal{K} \times \Xi`$ — the line's effective series reactance. It is PyPSA's `x_pu_eff`, `x` over the square of its bus's nominal voltage, data prep |
| $`\mathrm{on}^{f}`$ | `Link_active` over $`\mathcal{L} \times \mathcal{T}`$ — whether a link is active in a snapshot's period. It is PyPSA's `active`, data prep |
| $`\mathrm{act}^{f}`$ | `Link_active_asset` over $`\mathcal{L}`$ — whether a link is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{M}^{f}`$ | `Link_big_m` over $`\mathcal{L} \times \Xi`$, `absent` where the data has no row — the bound a committed extendable link's big-M rows release it by, data prep. It is the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu` (`components.py:1100-1171`). Without that keyword, it is ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`. Where there is none of them, it is 1e6. Below the flow a solve wants, it caps that flow |
| $`\mathrm{c}^{\mathrm{cap},f}`$ | `Link_capital_cost` over $`\mathcal{L} \times \Xi`$ — cost of one unit of nominal power for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1176-1197`, `costs.py:102-203`) |
| $`\mathrm{W}^{f}`$ | `Link_capital_weight` over $`\mathcal{L}`$ — the sum of period weights a link is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{com}^{f}`$ | `Link_committable` over $`\mathcal{L}`$ — whether flow is gated by an on/off status decision |
| $`\mathrm{rest}^{f}`$ | `Link_down_time_brought_in` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — one while the down time a link brought into the horizon is still running, zero after. It is PyPSA's stop `down_time_before` snapshots before the first, counted while `min_down_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep |
| $`\overline{\mathrm{E}}^{f}`$ | `Link_e_sum_max` over $`\mathcal{L} \times \Xi`$ — most energy of its flow at `bus0`, the withdrawal there, over the horizon. It is infinity where no cap is meant |
| $`\underline{\mathrm{E}}^{f}`$ | `Link_e_sum_min` over $`\mathcal{L} \times \Xi`$ — least energy of its flow at `bus0`, the withdrawal there, over the horizon. It is minus infinity where no floor is meant |
| $`\eta`$ | `Link_efficiency` over $`\mathcal{O} \times \Xi \times \mathcal{T}`$ — share of the flow that arrives at an output port, PyPSA's `efficiency`, `efficiency2`, … read long: negative where that port consumes rather than delivers. Read at the snapshot the flow arrives, so a delayed port delivers at its arrival snapshot's efficiency (`constraints.py:1575`) |
| $`\mathrm{cc}^{f}`$ | `Link_expansion_cost_weight` over $`\mathcal{O} \times \mathcal{L} \times \Xi`$, `absent` where the data has no row — the link's capital cost where its carrier is in the row's set, data prep. Where the row states no `investment_period` under `multi_investment_periods`, it is times the objective weights of the periods the link is active in. A link outside the set, or one that is not active in the row's period, has no row. The capital cost is PyPSA's `capital_cost` property, which is `Link_capital_cost` without `fom_cost` (`components.py:1201-1219`, `global_constraints.py:897-906`) |
| $`\mathrm{new}^{f}`$ | `Link_first_active` over $`\mathcal{L} \times \mathcal{Y}`$ — one in the first period a link is active in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`) |
| $`\mathrm{mnt}^{f}`$ | `Link_maintainable` over $`\mathcal{L}`$ — whether a link must be taken off for maintenance within the horizon: in any scenario, as PyPSA takes the union over them (`components.py:1018-1021`) |
| $`\tau^{f,\mathrm{mnt}}`$ | `Link_maintenance_duration` over $`\mathcal{L} \times \Xi`$, `absent` where the data has no row — the hours of generator weightings one maintenance event covers, PyPSA's `maintenance_duration`. It has no value where the link is not maintainable. No row contains it. In data prep you turn it into `Link_maintenance_cover` and `Link_maintenance_start_blocked`. The assumptions state that it fits the horizon |
| $`\mathrm{n}^{f,\mathrm{mnt}}`$ | `Link_maintenance_events` over $`\mathcal{L} \times \Xi`$ — how many maintenance events occur within the horizon |
| $`\gamma^{f}`$ | `Link_maintenance_pu` over $`\mathcal{L} \times \Xi`$ — the share of the build a maintenance event takes off |
| $`\mathrm{blk}^{f}`$ | `Link_maintenance_start_blocked` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — true where no maintenance event may start, data prep. The snapshots it would cover there run past the end of the horizon or into one the link is not active in. It is PyPSA's `active & ~valid`, from `maintenance_duration` and the generator weightings |
| $`\mathrm{c}^{f}`$ | `Link_marginal_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one unit of flow |
| $`\mathrm{c}^{f,(2)}`$ | `Link_marginal_cost_quadratic` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of the square of one unit of flow |
| $`\mathrm{DT}^{f}`$ | `Link_min_down_time` over $`\mathcal{L} \times \Xi`$ — least snapshots a link stays off once stopped |
| $`\mathrm{UT}^{f}`$ | `Link_min_up_time` over $`\mathcal{L} \times \Xi`$ — least snapshots a link stays on once started |
| $`\mathrm{N}^{f,\mathrm{fix}}`$ | `Link_modules_installed` over $`\mathcal{L} \times \Xi`$ — how many whole modules a committable build has in place, data prep. It is `Link_p_nom / Link_p_nom_mod` where a fixed build is modular, and one where it is not. PyPSA refuses a fixed modular build whose nominal power is not a whole number of modules |
| $`\mathrm{cyc}^{f}`$ | `Link_output_cyclic_delay` over $`\mathcal{O}`$ — whether a delayed port's flow wraps from the end of its investment period (PyPSA's `cyclic_delay`, `cyclic_delay2`, …). Where it does not, the flow still in transit at each period's first snapshots is lost. The flag is the same in every scenario, as the delay is |
| $`\mathrm{d}^{f}`$ | `Link_output_delay` over $`\mathcal{O}`$ — snapshots a port's delivery lags its link's flow (PyPSA's `delay`, `delay2`, … read long). In data prep you divide it by the `snapshot_weightings.generators` value and round it up. It is zero for a port that delivers at once. A port has the same delay in every scenario, because PyPSA refuses a delay that differs by scenario (`constants.py:55`) |
| $`\mathrm{f}^{0}`$ | `Link_p_init` over $`\mathcal{L} \times \Xi`$, $`0`$ where the data has no row — the flow a link brought into the horizon (PyPSA's `p_init`), read only where the link came in running. No value means it is unknown, and the link then has no ramp row at the first snapshot |
| $`\overline{\mathrm{f}}`$ | `Link_p_max_pu` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — most flow, per unit of nominal power |
| $`\underline{\mathrm{f}}`$ | `Link_p_min_pu` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — least flow, per unit of nominal power: negative for a link that carries both ways |
| $`\mathrm{nonneg}^{f}`$ | `Link_p_min_pu_nonneg` over $`\mathcal{L}`$ — true where none of the link's own minimums-per-unit is negative. It is PyPSA's per-unit `(p_min_pu >= 0).all()` over every snapshot and scenario, data prep |
| $`\mathrm{f}^{\mathrm{nom}}`$ | `Link_p_nom` over $`\mathcal{L} \times \Xi`$ — nominal power |
| $`\mathrm{ext}^{f}`$ | `Link_p_nom_extendable` over $`\mathcal{L}`$ — whether the nominal power is a decision |
| $`\overline{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_max` over $`\mathcal{L} \times \Xi`$ — most nominal power an extendable link may be built at |
| $`\underline{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_min` over $`\mathcal{L} \times \Xi`$ — least nominal power an extendable link may be built at |
| $`\mathrm{f}^{\mathrm{mod}}`$ | `Link_p_nom_mod` over $`\mathcal{L}`$, `absent` where the data has no row — the module size a build comes in whole numbers of. No value means the build is continuous |
| $`\mathrm{f}^{\mathrm{nom,set}}`$ | `Link_p_nom_set` over $`\mathcal{L}`$, `absent` where the data has no row — a given nominal power for an extendable link. One without a value has no row here |
| $`\mathrm{f}^{\mathrm{set}}`$ | `Link_p_set` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — a given flow schedule. A link without one has no row here |
| $`\mathrm{rd}^{f}`$ | `Link_ramp_limit_down` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a link may lower its flow between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{rd}^{f,\mathrm{dn}}`$ | `Link_ramp_limit_shut_down` over $`\mathcal{L} \times \Xi`$, `absent` where the data has no row — most flow in the snapshot before a link stops, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{f,\mathrm{up}}`$ | `Link_ramp_limit_start_up` over $`\mathcal{L} \times \Xi`$, `absent` where the data has no row — most flow in the snapshot a link starts, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{f}`$ | `Link_ramp_limit_up` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a link may raise its flow between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{c}^{f,\mathrm{dn}}`$ | `Link_shut_down_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one stop in this snapshot |
| $`\mathrm{c}^{f,\mathrm{on}}`$ | `Link_stand_by_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one snapshot spent on |
| $`\mathrm{c}^{f,\mathrm{up}}`$ | `Link_start_up_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one start in this snapshot |
| $`\mathrm{u}^{f,0}`$ | `Link_status_initial` over $`\mathcal{L} \times \Xi`$ — one where the link was on before the first snapshot, zero where off. It is PyPSA's `up_time_before > 0` for a committable link, and one for a link that is not, whose ramp rows PyPSA starts from on (`constraints.py:323`), data prep |
| $`\mathrm{m}^{f}`$ | `Link_tech_capacity_weight` over $`\mathcal{O} \times \mathcal{L}`$, `absent` where the data has no row — one where the link is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |
| $`\mathrm{hold}^{f}`$ | `Link_up_time_brought_in` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — one while the up time a link brought into the horizon is still running, zero after. It is PyPSA's start `up_time_before` snapshots before the first, counted while `min_up_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep |
| $`\mathrm{len}^{f}`$ | `Link_volume_weight` over $`\mathcal{O} \times \mathcal{L} \times \Xi`$, `absent` where the data has no row — the link's length in each scenario where its carrier is in the row's set (`global_constraints.py:874-875`), data prep. A link outside it, or one that is not active in the row's `investment_period`, has no row |
| $`\mathrm{on}^{\mathrm{load}}`$ | `Load_active` over $`\mathcal{D}`$ — whether a load is active in the network, PyPSA's `active`. A load has no build year and no lifetime, so the flag is the same in every snapshot. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{D} \times \Xi \times \mathcal{T}`$ — demand |
| $`\mathrm{sgn}^{\mathrm{load}}`$ | `Load_sign` over $`\mathcal{D}`$ — the sign a load's demand enters its bus's balance with. It is PyPSA's `sign`, `-1` unless given, `1` for a load that feeds its bus. PyPSA refuses one that differs by scenario (`constants.py:46`) |
| $`\mathrm{on}^{z}`$ | `Process_active` over $`\mathcal{J} \times \mathcal{T}`$ — whether a process is active in a snapshot's period. It is PyPSA's `active`, data prep |
| $`\mathrm{act}^{z}`$ | `Process_active_asset` over $`\mathcal{J}`$ — whether a process is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{M}^{z}`$ | `Process_big_m` over $`\mathcal{J} \times \Xi`$, `absent` where the data has no row — the bound a committed extendable process's big-M rows release it by, data prep. It is the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu` (`components.py:1100-1171`). Without that keyword, it is ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`. Where there is none of them, it is 1e6. Below the internal power a solve wants, it caps that internal power |
| $`\mathrm{c}^{\mathrm{cap},z}`$ | `Process_capital_cost` over $`\mathcal{J} \times \Xi`$ — cost of one unit of nominal power for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1176-1197`, `costs.py:102-203`) |
| $`\mathrm{W}^{z}`$ | `Process_capital_weight` over $`\mathcal{J}`$ — the sum of period weights a process is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{com}^{z}`$ | `Process_committable` over $`\mathcal{J}`$ — whether internal power is gated by an on/off status decision |
| $`\mathrm{rest}^{z}`$ | `Process_down_time_brought_in` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — one while the down time a process brought into the horizon is still running, zero after. It is PyPSA's stop `down_time_before` snapshots before the first, counted while `min_down_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep |
| $`\overline{\mathrm{E}}^{z}`$ | `Process_e_sum_max` over $`\mathcal{J} \times \Xi`$ — most energy of its internal power over the horizon. It is infinity where no cap is meant |
| $`\underline{\mathrm{E}}^{z}`$ | `Process_e_sum_min` over $`\mathcal{J} \times \Xi`$ — least energy of its internal power over the horizon. It is minus infinity where no floor is meant |
| $`\mathrm{new}^{z}`$ | `Process_first_active` over $`\mathcal{Y} \times \mathcal{J}`$ — one in the first period a process is active in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`) |
| $`\mathrm{mnt}^{z}`$ | `Process_maintainable` over $`\mathcal{J}`$ — whether a process must be taken off for maintenance within the horizon: in any scenario, as PyPSA takes the union over them (`components.py:1018-1021`) |
| $`\tau^{z,\mathrm{mnt}}`$ | `Process_maintenance_duration` over $`\mathcal{J} \times \Xi`$, `absent` where the data has no row — the hours of generator weightings one maintenance event covers, PyPSA's `maintenance_duration`. It has no value where the process is not maintainable. No row contains it. In data prep you turn it into `Process_maintenance_cover` and `Process_maintenance_start_blocked`. The assumptions state that it fits the horizon |
| $`\mathrm{n}^{z,\mathrm{mnt}}`$ | `Process_maintenance_events` over $`\mathcal{J} \times \Xi`$ — how many maintenance events occur within the horizon |
| $`\gamma^{z}`$ | `Process_maintenance_pu` over $`\mathcal{J} \times \Xi`$ — the share of the build a maintenance event takes off |
| $`\mathrm{blk}^{z}`$ | `Process_maintenance_start_blocked` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — true where no maintenance event may start, data prep. The snapshots it would cover there run past the end of the horizon or into one the process is not active in. It is PyPSA's `active & ~valid`, from `maintenance_duration` and the generator weightings |
| $`\mathrm{c}^{z}`$ | `Process_marginal_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one unit of internal power |
| $`\mathrm{c}^{z,(2)}`$ | `Process_marginal_cost_quadratic` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of the square of one unit of internal power |
| $`\mathrm{DT}^{z}`$ | `Process_min_down_time` over $`\mathcal{J} \times \Xi`$ — least snapshots a process stays off once stopped |
| $`\mathrm{UT}^{z}`$ | `Process_min_up_time` over $`\mathcal{J} \times \Xi`$ — least snapshots a process stays on once started |
| $`\mathrm{N}^{z,\mathrm{fix}}`$ | `Process_modules_installed` over $`\mathcal{J} \times \Xi`$ — how many whole modules a committable build has in place, data prep. It is `Process_p_nom / Process_p_nom_mod` where a fixed build is modular, and one where it is not. PyPSA refuses a fixed modular build whose nominal power is not a whole number of modules |
| $`\mathrm{cyc}^{z}`$ | `Process_output_cyclic_delay` over $`\mathcal{R}`$ — whether a delayed port's transfer wraps from the end of its investment period (PyPSA's `cyclic_delay0`, `cyclic_delay1`, …). Where it does not, the energy still in transit at each period's first snapshots is lost. The flag is the same in every scenario, as the delay is |
| $`\mathrm{d}^{z}`$ | `Process_output_delay` over $`\mathcal{R}`$ — snapshots a port's transfer lags its process's internal power (PyPSA's `delay0`, `delay1`, … read long). In data prep you divide it by the `snapshot_weightings.generators` value and round it up. It is zero for a port that transfers at once. A port has the same delay in every scenario, as a link's port has |
| $`\mathrm{z}^{0}`$ | `Process_p_init` over $`\mathcal{J} \times \Xi`$, $`0`$ where the data has no row — the internal power a process brought into the horizon (PyPSA's `p_init`), read only where the process came in running. No value means it is unknown, and the process then has no ramp row at the first snapshot |
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
| $`\mathrm{rd}^{z}`$ | `Process_ramp_limit_down` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a process may lower its internal power between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{rd}^{z,\mathrm{dn}}`$ | `Process_ramp_limit_shut_down` over $`\mathcal{J} \times \Xi`$, `absent` where the data has no row — most internal power in the snapshot before a process stops, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{z,\mathrm{up}}`$ | `Process_ramp_limit_start_up` over $`\mathcal{J} \times \Xi`$, `absent` where the data has no row — most internal power in the snapshot a process starts, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{z}`$ | `Process_ramp_limit_up` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a process may raise its internal power between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\alpha`$ | `Process_rate` over $`\mathcal{R} \times \Xi \times \mathcal{T}`$ — the energy a port draws or delivers per unit of internal power (PyPSA's `rate0`, `rate1`, … read long). It is negative where the port withdraws and positive where it injects. A link is a process whose `bus0` rate is minus one and whose output rates are its efficiencies. The rate at the snapshot the transfer arrives applies, so a delayed port transfers at its arrival snapshot's rate (`constraints.py:1575`) |
| $`\mathrm{c}^{z,\mathrm{dn}}`$ | `Process_shut_down_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one stop in this snapshot |
| $`\mathrm{c}^{z,\mathrm{on}}`$ | `Process_stand_by_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one snapshot spent on |
| $`\mathrm{c}^{z,\mathrm{up}}`$ | `Process_start_up_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one start in this snapshot |
| $`\mathrm{u}^{z,0}`$ | `Process_status_initial` over $`\mathcal{J} \times \Xi`$ — one where the process was on before the first snapshot, zero where off. It is PyPSA's `up_time_before > 0` for a committable process, and one for a process that is not, whose ramp rows PyPSA starts from on (`constraints.py:323`), data prep |
| $`\mathrm{m}^{z}`$ | `Process_tech_capacity_weight` over $`\mathcal{O} \times \mathcal{J}`$, `absent` where the data has no row — one where the process is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |
| $`\mathrm{hold}^{z}`$ | `Process_up_time_brought_in` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — one while the up time a process brought into the horizon is still running, zero after. It is PyPSA's start `up_time_before` snapshots before the first, counted while `min_up_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep |
| $`\mathrm{on}^{h}`$ | `StorageUnit_active` over $`\mathcal{T} \times \mathcal{S}`$ — whether a storage unit is active in a snapshot's period. It is PyPSA's `active`, data prep |
| $`\mathrm{act}^{h}`$ | `StorageUnit_active_asset` over $`\mathcal{S}`$ — whether a storage unit is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{c}^{\mathrm{cap},h}`$ | `StorageUnit_capital_cost` over $`\Xi \times \mathcal{S}`$ — cost of one unit of nominal power for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1176-1197`, `costs.py:102-203`) |
| $`\mathrm{W}^{h}`$ | `StorageUnit_capital_weight` over $`\mathcal{S}`$ — the sum of period weights a storage unit is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{cyc}`$ | `StorageUnit_cyclic_state_of_charge` over $`\Xi \times \mathcal{S}`$ — whether the horizon closes on itself instead of opening on the initial charge |
| $`\mathrm{cyc}^{y}`$ | `StorageUnit_cyclic_state_of_charge_per_period` over $`\Xi \times \mathcal{S}`$ — whether each investment period closes on itself instead of carrying its charge on to the next. It overrides `cyclic_state_of_charge` and `state_of_charge_initial_per_period`. PyPSA reads it only under `multi_investment_periods`. Otherwise you feed false in data prep |
| $`\eta^{+}`$ | `StorageUnit_efficiency_dispatch` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — share of the charge drawn down that reaches the bus |
| $`\eta^{-}`$ | `StorageUnit_efficiency_store` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — share of the power drawn from the bus that becomes charge |
| $`\mathrm{new}^{h}`$ | `StorageUnit_first_active` over $`\mathcal{Y} \times \mathcal{S}`$ — one in the first period a storage unit is active in, zero elsewhere, data prep. PyPSA takes `active & (active.cumsum() == 1)` (`global_constraints.py:278`) |
| $`\mathrm{idle}`$ | `StorageUnit_inactive_snapshots` over $`\mathcal{S}`$ — how many snapshots a storage unit is not active in. It is PyPSA's `(~active).sum()`, data prep. A cyclic unit reaches back this many snapshots further, so it closes on the last snapshot it is active in |
| $`\mathrm{inflow}`$ | `StorageUnit_inflow` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — energy arriving per hour, a river into a reservoir |
| $`\mathrm{c}^{h}`$ | `StorageUnit_marginal_cost` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — cost of one unit of dispatch |
| $`\mathrm{c}^{h,(2)}`$ | `StorageUnit_marginal_cost_quadratic` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — cost of the square of one unit of dispatch. Storing is not charged |
| $`\mathrm{c}^{\mathrm{soc}}`$ | `StorageUnit_marginal_cost_storage` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — cost of one unit of charge held over one snapshot |
| $`\mathrm{T}^{h}`$ | `StorageUnit_max_hours` over $`\Xi \times \mathcal{S}`$ — energy capacity, as hours of dispatch at nominal power |
| $`\mathrm{open}`$ | `StorageUnit_opens_late` over $`\mathcal{T} \times \mathcal{S}`$ — whether a snapshot is the first a storage unit is active in, where that is not the first of the horizon, data prep. It is PyPSA's `active.cumsum() == 1` over the snapshots it is active in, past the first snapshot. It is false in a run where every unit is active throughout |
| $`\mathrm{b}^{h}`$ | `StorageUnit_operational_limit_weight` over $`\mathcal{O} \times \Xi \times \mathcal{S}`$, `absent` where the data has no row — one where the storage unit is in the row's set, data prep. One outside it has no row |
| $`\mathrm{h}^{+,\mathrm{set}}`$ | `StorageUnit_p_dispatch_set` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$, `absent` where the data has no row — a given dispatch schedule. A unit without one has no row here |
| $`\overline{\mathrm{h}}`$ | `StorageUnit_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — most dispatch, per unit of nominal power |
| $`\underline{\mathrm{h}}`$ | `StorageUnit_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — most storing, per unit of nominal power and negated |
| $`\mathrm{h}^{\mathrm{nom}}`$ | `StorageUnit_p_nom` over $`\Xi \times \mathcal{S}`$ — nominal power |
| $`\mathrm{ext}^{h}`$ | `StorageUnit_p_nom_extendable` over $`\mathcal{S}`$ — whether the nominal power is a decision |
| $`\overline{\mathrm{h}}^{\mathrm{nom}}`$ | `StorageUnit_p_nom_max` over $`\Xi \times \mathcal{S}`$ — most nominal power an extendable storage unit may be built at |
| $`\underline{\mathrm{h}}^{\mathrm{nom}}`$ | `StorageUnit_p_nom_min` over $`\Xi \times \mathcal{S}`$ — least nominal power an extendable storage unit may be built at |
| $`\mathrm{h}^{\mathrm{mod}}`$ | `StorageUnit_p_nom_mod` over $`\mathcal{S}`$, `absent` where the data has no row — the module size a build comes in whole numbers of. No value means the build is continuous |
| $`\mathrm{h}^{\mathrm{nom,set}}`$ | `StorageUnit_p_nom_set` over $`\mathcal{S}`$, `absent` where the data has no row — a given nominal power for an extendable storage unit. One without a value has no row here |
| $`\mathrm{h}^{\mathrm{set}}`$ | `StorageUnit_p_set` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$, `absent` where the data has no row — a given net dispatch schedule. A unit without one has no row here |
| $`\mathrm{h}^{-,\mathrm{set}}`$ | `StorageUnit_p_store_set` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$, `absent` where the data has no row — a given charging schedule. A unit without one has no row here |
| $`\mathrm{a}^{h}`$ | `StorageUnit_primary_energy_weight` over $`\mathcal{O} \times \Xi \times \mathcal{S}`$, `absent` where the data has no row — the constrained attribute per unit of charge depleted, data prep. An unweighted unit has no row |
| $`\rho`$ | `StorageUnit_retention` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — share of charge kept over a snapshot. It is PyPSA's `(1 - standing_loss) ** elapsed hours`, data prep |
| $`\mathrm{sgn}^{h}`$ | `StorageUnit_sign` over $`\mathcal{S}`$ — the sign net dispatch enters its bus's balance with. It is PyPSA's `sign`, `1` unless given. PyPSA refuses one that differs by scenario (`constants.py:46`) |
| $`\mathrm{c}^{\mathrm{spill}}`$ | `StorageUnit_spill_cost` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — cost of one unit of inflow passed on unused |
| $`\mathrm{soc}^{0}`$ | `StorageUnit_state_of_charge_initial` over $`\Xi \times \mathcal{S}`$ — charge held before the first snapshot |
| $`\mathrm{reset}`$ | `StorageUnit_state_of_charge_initial_per_period` over $`\Xi \times \mathcal{S}`$ — whether each investment period opens on the initial charge instead of carrying the previous period's. PyPSA reads it only under `multi_investment_periods`. Otherwise you feed false in data prep |
| $`\mathrm{soc}^{\mathrm{set}}`$ | `StorageUnit_state_of_charge_set` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$, `absent` where the data has no row — a given charge schedule. A unit without one has no row here |
| $`\mathrm{m}^{h}`$ | `StorageUnit_tech_capacity_weight` over $`\mathcal{O} \times \mathcal{S}`$, `absent` where the data has no row — one where the storage unit is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |
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
| $`\mathrm{c}^{q,+}`$ | `Store_marginal_cost_dispatch` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of discharge, `p + p_store` |
| $`\mathrm{c}^{q,(2)}`$ | `Store_marginal_cost_quadratic` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of the square of the net power delivered, so charging costs as much as delivering |
| $`\mathrm{c}^{e}`$ | `Store_marginal_cost_storage` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of energy held over one snapshot |
| $`\mathrm{c}^{q,-}`$ | `Store_marginal_cost_store` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of charging, `p_store` |
| $`\mathrm{T}^{e}`$ | `Store_max_hours` over $`\Xi \times \mathcal{V}`$, `absent` where the data has no row — energy capacity, as hours of discharge at the power rating. The rating is `e_nom / max_hours`. No value means PyPSA's default of infinity, and the store's power is then unbounded |
| $`\mathrm{open}^{e}`$ | `Store_opens_late` over $`\mathcal{T} \times \mathcal{V}`$ — whether a snapshot is the first a store is active in, where that is not the first of the horizon, data prep. It is PyPSA's `active.cumsum() == 1` over the snapshots it is active in, past the first snapshot. It is false in a run where every store is active throughout |
| $`\mathrm{b}^{e}`$ | `Store_operational_limit_weight` over $`\mathcal{O} \times \Xi \times \mathcal{V}`$, `absent` where the data has no row — one where the store is in the row's set, data prep. One outside it has no row |
| $`\overline{\mathrm{q}}`$ | `Store_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — most discharge, per unit of the power rating. It is PyPSA's `p_max_pu`, `1` unless given, read only where `max_hours` has a value |
| $`\underline{\mathrm{q}}`$ | `Store_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — most charging, per unit of the power rating, negated. It is PyPSA's `p_min_pu`, `-1` unless given, read only where `max_hours` has a value |
| $`\mathrm{q}^{\mathrm{set}}`$ | `Store_p_set` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$, `absent` where the data has no row — a given schedule of power delivered. A store without one has no row here |
| $`\mathrm{a}^{e}`$ | `Store_primary_energy_weight` over $`\mathcal{O} \times \Xi \times \mathcal{V}`$, `absent` where the data has no row — the constrained attribute per unit of energy depleted, data prep. An unweighted store has no row |
| $`\rho^{e}`$ | `Store_retention` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — share of energy kept over a snapshot. It is PyPSA's `(1 - standing_loss) ** elapsed hours`, data prep |
| $`\mathrm{sgn}^{q}`$ | `Store_sign` over $`\mathcal{V}`$ — the sign the power a store delivers enters its bus's balance with. It is PyPSA's `sign`, `1` unless given. PyPSA refuses one that differs by scenario (`constants.py:46`) |
| $`\mathrm{c}^{\mathrm{spill},e}`$ | `Store_spill_cost` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — cost of one unit of inflow passed on unused |
| $`\mathrm{split}^{e}`$ | `Store_split_dispatch` over $`\Xi \times \mathcal{V}`$ — whether a store charges through `p_store` apart from its net dispatch `p`. It is PyPSA's `split_dispatch()`: true where an efficiency differs from one, a cost applies to one direction only, or `cycles_max` is finite, in any snapshot (`stores.py:88-116`), data prep. Where it is false, `p_store` is held at zero and the charging bound applies to `p` |
| $`\mathrm{m}^{e}`$ | `Store_tech_capacity_weight` over $`\mathcal{O} \times \mathcal{V}`$, `absent` where the data has no row — one where the store is in the row's carrier-and-bus set, data prep. One outside it, or one that is not active in the row's `investment_period`, has no row |
| $`\beta^{\sigma}`$ | `Transformer_BODF` over $`\mathcal{K}^{\mathrm{out}} \times \mathcal{Y} \times \mathcal{M}`$, `absent` where the data has no row — the share of an outaged branch's flow a transformer takes on when that branch goes out, as a line's. A row only where the transformer and the outage are active in the period and share a sub-network. It is the same in every scenario, as a line's |
| $`\mathrm{on}^{\sigma}`$ | `Transformer_active` over $`\mathcal{T} \times \mathcal{M}`$ — whether a transformer is active in a snapshot's period. It is PyPSA's `active`, data prep |
| $`\mathrm{act}^{\sigma}`$ | `Transformer_active_asset` over $`\mathcal{M}`$ — whether a transformer is one of PyPSA's `active_assets`, by its `active` flag alone, without build year and lifetime. A unit that is active in no snapshot of the horizon still counts. PyPSA refuses one that differs by scenario (`constants.py:54`) |
| $`\mathrm{c}^{\mathrm{cap},\sigma}`$ | `Transformer_capital_cost` over $`\Xi \times \mathcal{M}`$ — cost of one unit of nominal apparent power for the modelled horizon (PyPSA's `periodized_cost`), data prep. It is `overnight_cost` as an annuity over `lifetime` at `discount_rate`, times `nyears`, where `overnight_cost` is given, and `capital_cost` where it is not. Both add `fom_cost` (`components.py:1176-1197`, `costs.py:102-203`) |
| $`\mathrm{W}^{\sigma}`$ | `Transformer_capital_weight` over $`\mathcal{M}`$ — the sum of period weights a transformer is active in. It is PyPSA's `active * period_weighting`, summed, data prep |
| $`\mathrm{x}^{\sigma}`$ | `Transformer_cycle_weight` over $`\mathcal{C} \times \mathcal{Y} \times \mathcal{M}`$, `absent` where the data has no row — the transformer's effective series reactance, `x` times its tap ratio, signed by its orientation in the cycle. It is PyPSA's `x_pu_eff`, the cycle basis, data prep. A transformer in no cycle has no row. It is the same in every scenario, as a line's |
| $`\overline{\ell}^{\sigma}`$ | `Transformer_loss_max` over $`\Xi \times \mathcal{T} \times \mathcal{M}`$ — the loss at a transformer's rating (PyPSA's `r_pu_eff * (s_max_pu * s_nom_max)**2`), data prep. Its `r_pu_eff` is the resistance over the given `s_nom` times the tap ratio |
| $`\mathrm{b}^{\sigma}`$ | `Transformer_loss_offset` over $`\Xi \times \mathcal{M} \times \mathcal{T} \times \mathcal{M}`$ — where that cut meets the loss axis: a tangent's `loss_k - slope_k * p_k`, a secant's `-r_pu_eff * p_k * p_k+1`, negative, data prep |
| $`\mathrm{a}^{\sigma}`$ | `Transformer_loss_slope` over $`\Xi \times \mathcal{M} \times \mathcal{T} \times \mathcal{M}`$ — the slope of a cut to a transformer's loss curve, data prep. It is a tangent's `2 * r_pu_eff * p_k` or a secant's `r_pu_eff * (p_k + p_k+1)`, as a line's. It uses the transformer's own `r_pu_eff` and rating |
| $`\mathrm{Transformer\_phase\_shift\_cycle\_weight}`$ | `Transformer_phase_shift_cycle_weight` over $`\mathcal{C} \times \mathcal{Y} \times \mathcal{M}`$ — the cycle sign for a varying transformer's phase shift, times π/180 so a shift in degrees enters the cycle sum in radians, data prep. It is zero for a fixed transformer or one in no cycle |
| $`\varphi^{\sigma}`$ | `Transformer_phase_shift_fixed` over $`\mathcal{T} \times \mathcal{M}`$ — a fixed transformer's phase shift at each snapshot, in degrees. It is PyPSA's `phase_shift`, zero by default. A varying transformer's shift is a decision instead |
| $`\mathrm{Transformer\_phase\_shift\_max}`$ | `Transformer_phase_shift_max` over $`\mathcal{M}`$ — the most a varying transformer's phase shift may take, in degrees. It is PyPSA's `phase_shift_max`. Equal to `phase_shift_min` for a fixed transformer |
| $`\mathrm{Transformer\_phase\_shift\_min}`$ | `Transformer_phase_shift_min` over $`\mathcal{M}`$ — the least a varying transformer's phase shift may take, in degrees. It is PyPSA's `phase_shift_min`. Where it is below `phase_shift_max` the shift is a decision, otherwise the transformer keeps its fixed `phase_shift` |
| $`\mathrm{Transformer\_phase\_shift\_varying}`$ | `Transformer_phase_shift_varying` over $`\mathcal{M}`$ — whether a transformer's phase shift is a decision (PyPSA's `phase_shift_min < phase_shift_max`, read as a flag in data prep). False is a fixed shift, set by `phase_shift`. The shift parameters have no scenario, but PyPSA reads them per scenario (`variables.py:446-456`, `constraints.py:1744`, `:1835`). The spec and PyPSA differ here (\#783) |
| $`\vartheta`$ | `Transformer_phase_shift_weight` over $`\mathcal{C} \times \mathcal{T} \times \mathcal{M}`$, `absent` where the data has no row — a fixed transformer's phase shift in radians at each snapshot, signed by its orientation in the cycle, data prep. It is a constant added to the cycle sum. It is zero for a varying transformer, whose shift is a decision instead. The constant and the variable term thus never both count a shift. A transformer with no shift or in no cycle of its snapshot's period has no row |
| $`\overline{\sigma}`$ | `Transformer_s_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{M}`$ — most flow either way, per unit of nominal apparent power |
| $`\sigma^{\mathrm{nom}}`$ | `Transformer_s_nom` over $`\Xi \times \mathcal{M}`$ — nominal apparent power |
| $`\mathrm{ext}^{\sigma}`$ | `Transformer_s_nom_extendable` over $`\mathcal{M}`$ — whether the nominal apparent power is a decision |
| $`\overline{\sigma}^{\mathrm{nom}}`$ | `Transformer_s_nom_max` over $`\Xi \times \mathcal{M}`$ — most nominal apparent power an extendable transformer may be built at |
| $`\underline{\sigma}^{\mathrm{nom}}`$ | `Transformer_s_nom_min` over $`\Xi \times \mathcal{M}`$ — least nominal apparent power an extendable transformer may be built at |
| $`\sigma^{\mathrm{mod}}`$ | `Transformer_s_nom_mod` over $`\mathcal{M}`$, `absent` where the data has no row — the module size a build comes in whole numbers of. No value means the build is continuous |
| $`\sigma^{\mathrm{nom,set}}`$ | `Transformer_s_nom_set` over $`\mathcal{M}`$, `absent` where the data has no row — a given nominal apparent power for an extendable transformer. One without a value has no row here |
| $`\sigma^{\mathrm{set}}`$ | `Transformer_s_set` over $`\Xi \times \mathcal{T} \times \mathcal{M}`$, `absent` where the data has no row — a given flow schedule. A transformer without one has no row here |
| $`\overline{\delta}^{\sigma}`$ | `Transformer_v_ang_max` over $`\Xi \times \mathcal{M}`$, `absent` where the data has no row — the most the voltage angle difference across a transformer, its phase shift included, may be either way, in degrees. It is PyPSA's `v_ang_max`. Infinite, and so no row, by default. The deprecated `v_ang_min` is ignored, as a line's |
| $`\mathrm{x}^{\mathrm{eff},\sigma}`$ | `Transformer_x_pu_eff` over $`\Xi \times \mathcal{M}`$ — the transformer's effective series reactance. It is PyPSA's `x_pu_eff`, `x` over its `s_nom` times its tap ratio, data prep |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$ — PyPSA's `investment_period_weightings.objective` — what a period's cost weighs. PyPSA reads it only under `multi_investment_periods`. Otherwise you feed one in data prep, whatever the column contains (`optimize.py:231-233`, `:293-297`) |
| $`\mathrm{w}^{\mathrm{yr}}`$ | `period_weight_years` over $`\mathcal{Y}`$ — PyPSA's `investment_period_weightings.years` — what a period's energy weighs in a `primary_energy`, `operational_limit` or `e_sum` row. PyPSA reads it only under `multi_investment_periods`. Otherwise you feed one in data prep |
| $`\pi`$ | `scenario_weight` over $`\Xi`$ — PyPSA's `scenario_weightings.weight` — the probability of a future |
| $`\mathrm{w}^{\mathrm{gen}}`$ | `snapshot_weightings_generators` over $`\mathcal{T}`$ — PyPSA's `snapshot_weightings.generators` — hours a snapshot weighs in an energy total |
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$ — PyPSA's `snapshot_weightings.objective` — hours a snapshot weighs in the cost |
| $`\mathrm{w}^{\mathrm{sto}}`$ | `snapshot_weightings_stores` over $`\mathcal{T}`$ — PyPSA's `snapshot_weightings.stores` — hours a snapshot weighs in a storage balance |
| $`\mathrm{lossy}`$ | `transmission_losses` (scalar) — whether the network dissipates transmission losses (PyPSA's `transmission_losses` read as a flag). Its mode, tangents or secants, only decides how you fill the `segment` axis in data prep. The rows are the same. False with no segments is a lossless run. A security-constrained run over a network with passive branches builds no loss. PyPSA hands the keyword not to `create_model` (`abstract.py:645-650`) but to the solver (`:549`), so you feed false there in data prep |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{\mathrm{com,ext}}`$ | `Generator_com_ext` over $`\mathcal{G} \times \mathcal{T}`$ — a committable generator with an extendable, non-modular build that is active in the snapshot's period. These are PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |
| $`\mathrm{on}^{\mathrm{com}}`$ | `Generator_committed` over $`\mathcal{G} \times \mathcal{T}`$ — a committable generator that is active in the snapshot's period: every unit-commitment row's set |
| $`\mathrm{on}^{\mathrm{mnt,ext}}`$ | `Generator_maint_ext` over $`\mathcal{G} \times \mathcal{T}`$ — a maintainable generator with an extendable build that is active in the snapshot's period, unless it is committable and modular. These are the maintenance rows against the chosen build |
| $`\mathrm{lp}`$ | `Generator_marginal_cost_as_lp` (scalar) — linopy's choice of method for all generator cost curves at once (`method="auto"`): the segment lines where every curve is convex and no generator with a curve is committable, the incremental rows otherwise. PyPSA gates the curves by `Generator-status` where one is committable, and linopy states no segment lines under a gate (`optimize.py:314-318`, `piecewise.py:193-217`) |
| $`\mathrm{curve}`$ | `Generator_marginal_cost_curve` over $`\mathcal{G}`$ — a generator that pays along a piecewise `marginal_cost` curve: one of PyPSA's `active_assets` with curve data (`optimize.py:307`, `piecewise.py:223-250`) |
| $`\mathrm{bend}`$ | `Generator_marginal_cost_curve_bends_down` over $`\mathcal{B} \times \mathcal{G}`$ — a breakpoint where a generator's cost curve gets less steep: the segment after it rises less per unit of output than the one before |
| $`\mathrm{prev}`$ | `Generator_ramps_from_previous` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — a snapshot whose ramp uses a previous output. It is any snapshot but its period's first, and the horizon's first where the generator comes in off or carries an initial output |
| $`\mathrm{on}^{s,\mathrm{lossy}}`$ | `Line_lossy` over $`\mathcal{K} \times \mathcal{T}`$ — a line that is active in the snapshot's period, where the run models transmission losses |
| $`\mathrm{on}^{f,\mathrm{com,ext}}`$ | `Link_com_ext` over $`\mathcal{L} \times \mathcal{T}`$ — a committable link with an extendable, non-modular build that is active in the snapshot's period. These are PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |
| $`\mathrm{on}^{f,\mathrm{com}}`$ | `Link_committed` over $`\mathcal{L} \times \mathcal{T}`$ — a committable link that is active in the snapshot's period: every unit-commitment row's set |
| $`\mathrm{on}^{f,\mathrm{mnt,ext}}`$ | `Link_maint_ext` over $`\mathcal{L} \times \mathcal{T}`$ — a maintainable link with an extendable build that is active in the snapshot's period, unless it is committable and modular. These are the maintenance rows against the chosen build |
| $`\mathrm{prev}^{f}`$ | `Link_ramps_from_previous` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — a snapshot whose ramp uses a previous output. It is any snapshot but its period's first, and the horizon's first where the link comes in off or carries an initial output |
| $`\mathrm{on}^{z,\mathrm{com,ext}}`$ | `Process_com_ext` over $`\mathcal{J} \times \mathcal{T}`$ — a committable process with an extendable, non-modular build that is active in the snapshot's period. These are PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |
| $`\mathrm{on}^{z,\mathrm{com}}`$ | `Process_committed` over $`\mathcal{J} \times \mathcal{T}`$ — a committable process that is active in the snapshot's period: every unit-commitment row's set |
| $`\mathrm{on}^{z,\mathrm{mnt,ext}}`$ | `Process_maint_ext` over $`\mathcal{J} \times \mathcal{T}`$ — a maintainable process with an extendable build that is active in the snapshot's period, unless it is committable and modular. These are the maintenance rows against the chosen build |
| $`\mathrm{prev}^{z}`$ | `Process_ramps_from_previous` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — a snapshot whose ramp uses a previous output. It is any snapshot but its period's first, and the horizon's first where the process comes in off or carries an initial output |
| $`\mathrm{on}^{h,\mathrm{ext}}`$ | `StorageUnit_ext` over $`\mathcal{T} \times \mathcal{S}`$ — a storage unit with an extendable build that is active in the snapshot's period. It is PyPSA's `ext` rows |
| $`\mathrm{on}^{h,\mathrm{fix}}`$ | `StorageUnit_fix` over $`\mathcal{T} \times \mathcal{S}`$ — a storage unit with a fixed build that is active in the snapshot's period. It is PyPSA's `fix` rows |
| $`\mathrm{on}^{\sigma,\mathrm{lossy}}`$ | `Transformer_lossy` over $`\mathcal{T} \times \mathcal{M}`$ — a transformer that is active in the snapshot's period, where the run models transmission losses |

#### Variables

| Symbol | Meaning |
|---|---|
| $`CVaR`$ | `CVaR` (scalar), $`0`$ where the mask leaves it out — `CVaR` — the tail's average cost, what the objective prices at `omega` |
| $`a`$ | `CVaR_a` over $`\Xi`$, $`0`$ where the mask leaves it out — `CVaR-a` — how far a scenario's operating cost exceeds the tail's start. It is nothing where it does not |
| $`\theta`$ | `CVaR_theta` (scalar), $`0`$ where the mask leaves it out — `CVaR-theta` — where the tail starts, the value at risk |
| $`\mathit{NP}`$ | `FlowBased_net_position` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `FlowBased-net_position` — what a zone bus exports to the flow-based domain, unbounded. It leaves the zone's nodal balance (`flow_based.py:207-234`). A bus that is no zone has none |
| $`\mu`$ | `Generator_maintenance` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Generator-maintenance` — whether a maintainable generator is in maintenance: continuous, and one exactly where an event covers the snapshot |
| $`\mu^{\mathrm{nom}}`$ | `Generator_maintenance_capacity` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Generator-maintenance_capacity` — the chosen build while in maintenance, zero otherwise: the product the `maintcap` rows linearise |
| $`\mu^{\mathrm{up}}`$ | `Generator_maintenance_start` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Generator-maintenance_start` — whether a maintenance event starts in this snapshot |
| $`\mu^{u}`$ | `Generator_maintenance_status` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Generator-maintenance_status` — the status while in maintenance, zero otherwise: the product the `maint-status` rows linearise, so a unit in maintenance may also be off |
| $`C^{\mathrm{curve}}`$ | `Generator_marginal_cost_piecewise` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — `Generator-marginal_cost_piecewise` — the running cost of a generator that pays along a curve, held above the curve |
| $`N`$ | `Generator_n_mod` over $`\mathcal{G}`$ — `Generator-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`p`$ | `Generator_p` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — `Generator-p` — output of a generator in a snapshot |
| $`P`$ | `Generator_p_nom_ext` over $`\mathcal{G}`$ — `Generator-p_nom` — nominal power where it is a decision, for a generator that is active. A fixed build is the parameter of the same PyPSA name |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — `Generator-shut_down` — how much of a committable unit turns off this snapshot, capped as the status is |
| $`\mathit{up}`$ | `Generator_start_up` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — `Generator-start_up` — how much of a committable unit turns on this snapshot, capped as the status is |
| $`u`$ | `Generator_status` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — `Generator-status` — how much of a committable unit is on. It is an integer the rows below cap at one, or at the module count where the build is modular |
| $`\ell`$ | `Line_loss` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Line-loss` — what a line dissipates carrying its flow, pushed down by the cost and held up by the cuts. Absent, and zero in the balance, where the network is lossless |
| $`N^{s}`$ | `Line_n_mod` over $`\mathcal{K}`$ — `Line-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`s`$ | `Line_s` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — `Line-s` — PyPSA's `p0`, the flow measured at the `Line_bus0` end: a positive value withdraws there and injects at `Line_bus1`, lossless |
| $`S`$ | `Line_s_nom_ext` over $`\mathcal{K}`$ — `Line-s_nom` — nominal apparent power where it is a decision, for a line that is active. A fixed build is the parameter of the same PyPSA name |
| $`\mu^{f}`$ | `Link_maintenance` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Link-maintenance` — whether a maintainable link is in maintenance: continuous, and one exactly where an event covers the snapshot |
| $`\mu^{f,\mathrm{nom}}`$ | `Link_maintenance_capacity` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Link-maintenance_capacity` — the chosen build while in maintenance, zero otherwise: the product the `maintcap` rows linearise |
| $`\mu^{f,\mathrm{up}}`$ | `Link_maintenance_start` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Link-maintenance_start` — whether a maintenance event starts in this snapshot |
| $`\mu^{f,u}`$ | `Link_maintenance_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Link-maintenance_status` — the status while in maintenance, zero otherwise: the product the `maint-status` rows linearise, so a unit in maintenance may also be off |
| $`N^{f}`$ | `Link_n_mod` over $`\mathcal{L}`$ — `Link-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`f`$ | `Link_p` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-p` — PyPSA's `p0`, the flow measured at the `Link_bus0` end. A positive value withdraws there and injects at every bus the link's output ports deliver to |
| $`F`$ | `Link_p_nom_ext` over $`\mathcal{L}`$ — `Link-p_nom` — nominal power where it is a decision, for a link that is active. A fixed build is the parameter of the same PyPSA name |
| $`\mathit{dn}^{f}`$ | `Link_shut_down` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-shut_down` — how much of a committable link turns off this snapshot, capped as the status is |
| $`\mathit{up}^{f}`$ | `Link_start_up` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-start_up` — how much of a committable link turns on this snapshot, capped as the status is |
| $`u^{f}`$ | `Link_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-status` — how much of a committable link is on. It is an integer the rows below cap at one, or at the module count where the build is modular |
| $`\mu^{z}`$ | `Process_maintenance` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Process-maintenance` — whether a maintainable process is in maintenance: continuous, and one exactly where an event covers the snapshot |
| $`\mu^{z,\mathrm{nom}}`$ | `Process_maintenance_capacity` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Process-maintenance_capacity` — the chosen build while in maintenance, zero otherwise: the product the `maintcap` rows linearise |
| $`\mu^{z,\mathrm{up}}`$ | `Process_maintenance_start` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Process-maintenance_start` — whether a maintenance event starts in this snapshot |
| $`\mu^{z,u}`$ | `Process_maintenance_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, $`0`$ where the mask leaves it out — `Process-maintenance_status` — the status while in maintenance, zero otherwise: the product the `maint-status` rows linearise, so a unit in maintenance may also be off |
| $`N^{z}`$ | `Process_n_mod` over $`\mathcal{J}`$ — `Process-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`z`$ | `Process_p` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-p` — PyPSA's internal power `p`. A positive value drives every port at its own rate, withdrawing where the rate is negative and injecting where it is positive |
| $`Z`$ | `Process_p_nom_ext` over $`\mathcal{J}`$ — `Process-p_nom` — nominal internal power where it is a decision, for a process that is active. A fixed build is the parameter of the same PyPSA name |
| $`\mathit{dn}^{z}`$ | `Process_shut_down` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-shut_down` — how much of a committable process turns off this snapshot, capped as the status is |
| $`\mathit{up}^{z}`$ | `Process_start_up` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-start_up` — how much of a committable process turns on this snapshot, capped as the status is |
| $`u^{z}`$ | `Process_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-status` — how much of a committable process is on. It is an integer the rows below cap at one, or at the module count where the build is modular |
| $`N^{h}`$ | `StorageUnit_n_mod` over $`\mathcal{S}`$ — `StorageUnit-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`h^{+}`$ | `StorageUnit_p_dispatch` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — `StorageUnit-p_dispatch` — power delivered to the bus |
| $`H`$ | `StorageUnit_p_nom_ext` over $`\mathcal{S}`$ — `StorageUnit-p_nom` — nominal power where it is a decision, for a storage unit that is active. A fixed build is the parameter of the same PyPSA name |
| $`h^{-}`$ | `StorageUnit_p_store` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — `StorageUnit-p_store` — power drawn from the bus into charge |
| $`\mathit{spill}`$ | `StorageUnit_spill` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$, $`0`$ where the mask leaves it out — `StorageUnit-spill` — inflow passed on unused. It is zero where there is no inflow, so the balance keeps its row there. The bounds are PyPSA's, on the variable rather than as rows |
| $`\mathit{soc}`$ | `StorageUnit_state_of_charge` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — `StorageUnit-state_of_charge` — energy held at the end of a snapshot |
| $`e`$ | `Store_e` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — `Store-e` — energy held at the end of a snapshot |
| $`E`$ | `Store_e_nom_ext` over $`\mathcal{V}`$ — `Store-e_nom` — nominal capacity where it is a decision, for a store that is active. A fixed build is the parameter of the same PyPSA name |
| $`N^{e}`$ | `Store_n_mod` over $`\mathcal{V}`$ — `Store-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`q`$ | `Store_p` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — `Store-p` — net power delivered to the bus. Charging is negative |
| $`q^{-}`$ | `Store_p_store` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — `Store-p_store` — power drawn from the bus to charge, so that `p + p_store` is the discharge. It is held at zero by its rows where the store does not split its dispatch |
| $`\mathit{spill}^{e}`$ | `Store_spill` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$, $`0`$ where the mask leaves it out — `Store-spill` — inflow passed on unused. It is zero where there is no inflow, so the balance keeps its row there. The bounds are PyPSA's, on the variable rather than as rows |
| $`\ell^{\sigma}`$ | `Transformer_loss` over $`\Xi \times \mathcal{T} \times \mathcal{M}`$, $`0`$ where the mask leaves it out — `Transformer-loss` — what a transformer dissipates carrying its flow, as a line does. Absent, and zero in the balance, where the network is lossless |
| $`N^{\sigma}`$ | `Transformer_n_mod` over $`\mathcal{M}`$ — `Transformer-n_mod` — how many modules of an extendable modular build. A unit that is not active has none |
| $`\mathit{Transformer\_phase\_shift}`$ | `Transformer_phase_shift` over $`\Xi \times \mathcal{T} \times \mathcal{M}`$, $`0`$ where the mask leaves it out — `Transformer-phase_shift` — a phase-shifting transformer's voltage angle shift in degrees, chosen per snapshot to redistribute the flows around its cycles without moving active power. Absent, and zero in the cycle sum, where the shift is fixed |
| $`\sigma`$ | `Transformer_s` over $`\Xi \times \mathcal{T} \times \mathcal{M}`$ — `Transformer-s` — PyPSA's `p0`, the flow measured at the `Transformer_bus0` end: a positive value withdraws there and injects at `Transformer_bus1`, lossless |
| $`\Sigma`$ | `Transformer_s_nom_ext` over $`\mathcal{M}`$ — `Transformer-s_nom` — nominal apparent power where it is a decision, for a transformer that is active. A fixed build is the parameter of the same PyPSA name |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Bus\_injection}`$ | `Bus_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ — what every component puts into a bus, less what it takes out of it. PyPSA writes each term into the balance, and a load on its right-hand side |
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{I} \times \mathcal{Y}`$ — what a carrier adds in a period: every extendable component of that carrier, counting each build in the first period it is active in. Like PyPSA, it sums only the components that carry a carrier attribute, so a transformer, which has none, counts in no carrier |
| $`\mathrm{r}^{+}`$ | `Carrier_relative_growth` over $`\mathcal{I}`$ — the share of the previous period's additions in a carrier's growth limit, PyPSA's `max_relative_growth` clipped at zero. A negative share thus adds nothing and never tightens the limit |
| $`\mathit{Cycle\_angle\_sum}`$ | `Cycle_angle_sum` over $`\mathcal{C} \times \Xi \times \mathcal{T}`$ — the voltage angle differences around a cycle: every branch flow times its cycle weight, and every transformer phase shift |
| $`\mathit{NP}^{\mathrm{inj}}`$ | `FlowBased_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ — what a zone bus exports to its flow-based domain leaves the bus (`constraints.py:1578`) |
| $`\mathit{Generator\_additions}`$ | `Generator_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Generator\_capex}`$ | `Generator_capex` (scalar) |
| $`\mathit{Generator\_commitment\_opex}`$ | `Generator_commitment_opex` over $`\Xi`$ |
| $`\mathit{Generator\_injection}`$ | `Generator_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathrm{Generator\_maintenance\_modules}`$ | `Generator_maintenance_modules` over $`\mathcal{G} \times \Xi`$ — how many modules of a modular committable generator can be on in maintenance: its build cap in modules where the build is extendable, and the modules installed where it is fixed (`constraints.py:588-594`) |
| $`\mathrm{M}`$ | `Generator_modules` over $`\mathcal{G} \times \Xi`$ — how many modules a committed unit's status counts: the chosen number where the build is extendable and modular, and the modules installed otherwise (`constraints.py:656-661`) |
| $`\mathit{Generator\_operational\_limit}`$ | `Generator_operational_limit` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{Generator\_opex}`$ | `Generator_opex` over $`\Xi`$ |
| $`\overleftarrow{p}^{\circ}`$ | `Generator_p_carried_over` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the output a generator carries over into a snapshot. At the first, it is the `p_init` it brought in where it came in running, and nothing where it came in off. After that, it is the previous snapshot's |
| $`\widehat{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_committed` over $`\mathcal{G} \times \Xi`$ — the build a committed unit's ramp rows are taken against: one module where the build is modular, since its status counts modules, and the given build otherwise (`constraints.py:1131-1134`) |
| $`\widetilde{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_effective` over $`\mathcal{G} \times \Xi`$ — the build a generator's limits are taken against: the chosen one where it is extendable, the given one otherwise |
| $`\overleftarrow{p}`$ | `Generator_previous_p` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the output a generator carries into a snapshot. It is nothing at the first snapshot it is active in past the first of the horizon: PyPSA fills an output it did not build with zero (`constraints.py:716`). It is the output carried over otherwise |
| $`\overleftarrow{u}`$ | `Generator_previous_status` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the commitment state a generator carries into a snapshot. It is off at the first snapshot it is active in past the first of the horizon. PyPSA reads a status it did not build as off there (`constraints.py:391`). It is the state carried over otherwise |
| $`\mathit{Generator\_primary\_energy}`$ | `Generator_primary_energy` over $`\mathcal{O} \times \Xi`$ |
| $`\Delta^{-}`$ | `Generator_ramp_down_allowance` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — how far a generator may lower output between two snapshots. It is its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\widetilde{\mathrm{rd}}`$ | `Generator_ramp_down_rate` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the ramp limit in a unit's down row, PyPSA's `ramp_limit_down`. It is the full build where PyPSA has none, since a shut-down ramp alone builds the row |
| $`\overleftarrow{\bar u}`$ | `Generator_ramp_previous_status` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the status a committed unit's ramp rows carry into a snapshot. At the first snapshot, a fixed modular unit that came in running has every module on, since the state it brought in is on or off (`constraints.py:1152-1157`). The transition and down-time rows count it as one module (PyPSA/PyPSA\#2114). It is the state carried in otherwise |
| $`\Delta^{+}`$ | `Generator_ramp_up_allowance` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — how far a generator may raise output between two snapshots. It is its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\widetilde{\mathrm{ru}}`$ | `Generator_ramp_up_rate` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the ramp limit in a unit's up row, PyPSA's `ramp_limit_up`. It is the full build where PyPSA has none, since a start-up ramp alone builds the row |
| $`C^{\mathrm{run}}`$ | `Generator_running_cost` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — what a generator's output costs in a snapshot: the value read off its piecewise curve where it has one, and its linear `marginal_cost` otherwise. A curve replaces the linear cost, as PyPSA drops the unit from that term (`optimize.py:333-348`) |
| $`\widetilde{\mathrm{rd}}^{\mathrm{dn}}`$ | `Generator_shut_down_rate` over $`\mathcal{G} \times \Xi`$ — the shut-down ramp in a unit's down row (PyPSA's `ramp_limit_shut_down`), or the full build where it has none |
| $`\widetilde{\mathrm{ru}}^{\mathrm{up}}`$ | `Generator_start_up_rate` over $`\mathcal{G} \times \Xi`$ — the start-up ramp in a unit's up row (PyPSA's `ramp_limit_start_up`), or the full build where it has none |
| $`\overleftarrow{u}^{\circ}`$ | `Generator_status_carried_over` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the state a generator carries over into a snapshot: the state it brought into the horizon at the first, the previous snapshot's after that |
| $`\mathit{Generator\_tech\_capacity\_expansion}`$ | `Generator_tech_capacity_expansion` over $`\mathcal{O}`$ |
| $`\mathit{w}^{\mathrm{gc}}`$ | `GlobalConstraint_energy_weight` over $`\mathcal{O} \times \Xi \times \mathcal{T}`$ — what one unit of power at a snapshot counts for in a row. Where the row counts the snapshot, it is the generator weighting times the years of the snapshot's period. Where it does not, it is nothing |
| $`\mathit{Line\_additions}`$ | `Line_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Line\_angle\_sum}`$ | `Line_angle_sum` over $`\mathcal{C} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{Line\_capex}`$ | `Line_capex` (scalar) |
| $`\mathit{Line\_injection}`$ | `Line_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\check{s}`$ | `Line_s_monitored` over $`\mathcal{K} \times \Xi \times \mathcal{T}`$ — the flow in a line's post-contingency rows. It is its flow where it is active, and nothing where it does not. PyPSA builds those rows for every branch of the sub-network in every snapshot |
| $`\mathit{Line\_tech\_capacity\_expansion}`$ | `Line_tech_capacity_expansion` over $`\mathcal{O}`$ |
| $`\mathit{Line\_transmission\_expansion\_cost}`$ | `Line_transmission_expansion_cost` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{Line\_transmission\_volume\_expansion}`$ | `Line_transmission_volume_expansion` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{Link\_additions}`$ | `Link_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Link\_capex}`$ | `Link_capex` (scalar) |
| $`\mathit{Link\_commitment\_opex}`$ | `Link_commitment_opex` over $`\Xi`$ |
| $`\mathit{Link\_injection}`$ | `Link_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathrm{Link\_maintenance\_modules}`$ | `Link_maintenance_modules` over $`\mathcal{L} \times \Xi`$ — how many modules of a modular committable link can be on in maintenance: its build cap in modules where the build is extendable, and the modules installed where it is fixed (`constraints.py:588-594`) |
| $`\mathrm{M}^{f}`$ | `Link_modules` over $`\mathcal{L} \times \Xi`$ — how many modules a committed link's status counts: the chosen number where the build is extendable and modular, and the modules installed otherwise (`constraints.py:656-661`) |
| $`\mathit{Link\_opex}`$ | `Link_opex` over $`\Xi`$ |
| $`\overrightarrow{f}`$ | `Link_output_arrival` over $`\mathcal{O} \times \Xi \times \mathcal{T}`$ — what a link delivers to an output port at a snapshot. It is its flow delayed by the port's `delay` within its investment period. It is multiplied by the port's efficiency at the snapshot the flow arrives. Where the port is `cyclic_delay`, the delayed flow wraps from the period's end. Where it is not, the flow still in transit at the period's first snapshots is lost. A port that does not delay (`delay` zero) delivers its flow unshifted, cyclic or not |
| $`\overleftarrow{f}^{\circ}`$ | `Link_p_carried_over` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the output a link carries over into a snapshot. At the first, it is the `p_init` it brought in where it came in running, and nothing where it came in off. After that, it is the previous snapshot's |
| $`\widehat{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_committed` over $`\mathcal{L} \times \Xi`$ — the build a committed link's ramp rows are taken against: one module where the build is modular, since its status counts modules, and the given build otherwise (`constraints.py:1131-1134`) |
| $`\widetilde{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_effective` over $`\mathcal{L} \times \Xi`$ — the build a link's limits are taken against: the chosen one where it is extendable, the given one otherwise |
| $`\overleftarrow{f}`$ | `Link_previous_p` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the output a link carries into a snapshot. It is nothing at the first snapshot it is active in past the first of the horizon: PyPSA fills an output it did not build with zero (`constraints.py:716`). It is the output carried over otherwise |
| $`\overleftarrow{u}^{f}`$ | `Link_previous_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the commitment state a link carries into a snapshot. It is off at the first snapshot it is active in past the first of the horizon. PyPSA reads a status it did not build as off there (`constraints.py:391`). It is the state carried over otherwise |
| $`\Delta^{f,-}`$ | `Link_ramp_down_allowance` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — how far a link may lower flow between two snapshots. It is its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\widetilde{\mathrm{rd}}^{f}`$ | `Link_ramp_down_rate` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the ramp limit in a link's down row, PyPSA's `ramp_limit_down`. It is the full build where PyPSA has none, since a shut-down ramp alone builds the row |
| $`\overleftarrow{\bar u}^{f}`$ | `Link_ramp_previous_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the status a committed link's ramp rows carry into a snapshot. At the first snapshot, a fixed modular link that came in running has every module on, since the state it brought in is on or off (`constraints.py:1152-1157`). The transition and down-time rows count it as one module (PyPSA/PyPSA\#2114). It is the state carried in otherwise |
| $`\Delta^{f,+}`$ | `Link_ramp_up_allowance` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — how far a link may raise flow between two snapshots. It is its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\widetilde{\mathrm{ru}}^{f}`$ | `Link_ramp_up_rate` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the ramp limit in a link's up row, PyPSA's `ramp_limit_up`. It is the full build where PyPSA has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}^{f,\mathrm{dn}}`$ | `Link_shut_down_rate` over $`\mathcal{L} \times \Xi`$ — the shut-down ramp in a link's down row (PyPSA's `ramp_limit_shut_down`), or the full build where it has none |
| $`\widetilde{\mathrm{ru}}^{f,\mathrm{up}}`$ | `Link_start_up_rate` over $`\mathcal{L} \times \Xi`$ — the start-up ramp in a link's up row (PyPSA's `ramp_limit_start_up`), or the full build where it has none |
| $`\overleftarrow{u}^{\circ f}`$ | `Link_status_carried_over` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the state a link carries over into a snapshot: the state it brought into the horizon at the first, the previous snapshot's after that |
| $`\mathit{Link\_tech\_capacity\_expansion}`$ | `Link_tech_capacity_expansion` over $`\mathcal{O}`$ |
| $`\mathit{Link\_transmission\_expansion\_cost}`$ | `Link_transmission_expansion_cost` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{Link\_transmission\_volume\_expansion}`$ | `Link_transmission_volume_expansion` over $`\mathcal{O} \times \Xi`$ |
| $`\check{\mathrm{load}}`$ | `Load_demand` over $`\mathcal{D} \times \Xi \times \mathcal{T}`$ — what a load draws from its bus's balance. It is its demand times its sign where it is active, and nothing where it is not. PyPSA drops an inactive load from the balance (`constraints.py:1591-1592`) |
| $`\mathrm{Load\_injection}`$ | `Load_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\hat{s}`$ | `Outage_s` over $`\mathcal{K}^{\mathrm{out}} \times \Xi \times \mathcal{T}`$ — the flow an outage takes off its branch: the outaged line's or transformer's flow before it goes out |
| $`\mathit{Process\_additions}`$ | `Process_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Process\_capex}`$ | `Process_capex` (scalar) |
| $`\mathit{Process\_commitment\_opex}`$ | `Process_commitment_opex` over $`\Xi`$ |
| $`\mathit{Process\_injection}`$ | `Process_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathrm{Process\_maintenance\_modules}`$ | `Process_maintenance_modules` over $`\mathcal{J} \times \Xi`$ — how many modules of a modular committable process can be on in maintenance: its build cap in modules where the build is extendable, and the modules installed where it is fixed (`constraints.py:588-594`) |
| $`\mathrm{M}^{z}`$ | `Process_modules` over $`\mathcal{J} \times \Xi`$ — how many modules a committed process's status counts: the chosen number where the build is extendable and modular, and the modules installed otherwise (`constraints.py:656-661`) |
| $`\mathit{Process\_opex}`$ | `Process_opex` over $`\Xi`$ |
| $`\overrightarrow{z}`$ | `Process_output_arrival` over $`\mathcal{R} \times \Xi \times \mathcal{T}`$ — what a process transfers at a port at a snapshot. It is its internal power delayed by the port's `delay` within its investment period. It is multiplied by the port's rate at the snapshot the transfer arrives. Where the port is `cyclic_delay`, the delayed transfer wraps from the period's end. Where it is not, the energy still in transit at the period's first snapshots is lost. A port that does not delay (`delay` zero) transfers at once, cyclic or not |
| $`\overleftarrow{z}^{\circ}`$ | `Process_p_carried_over` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the output a process carries over into a snapshot. At the first, it is the `p_init` it brought in where it came in running, and nothing where it came in off. After that, it is the previous snapshot's |
| $`\widehat{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_committed` over $`\mathcal{J} \times \Xi`$ — the build a committed process's ramp rows are taken against: one module where the build is modular, since its status counts modules, and the given build otherwise (`constraints.py:1131-1134`) |
| $`\widetilde{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_effective` over $`\mathcal{J} \times \Xi`$ — the build a process's limits are taken against: the chosen one where it is extendable, the given one otherwise |
| $`\overleftarrow{z}`$ | `Process_previous_p` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the output a process carries into a snapshot. It is nothing at the first snapshot it is active in past the first of the horizon: PyPSA fills an output it did not build with zero (`constraints.py:716`). It is the output carried over otherwise |
| $`\overleftarrow{u}^{z}`$ | `Process_previous_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the commitment state a process carries into a snapshot. It is off at the first snapshot it is active in past the first of the horizon. PyPSA reads a status it did not build as off there (`constraints.py:391`). It is the state carried over otherwise |
| $`\Delta^{z,-}`$ | `Process_ramp_down_allowance` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — how far a process may lower internal power between two snapshots. It is its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\widetilde{\mathrm{rd}}^{z}`$ | `Process_ramp_down_rate` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the ramp limit in a process's down row, PyPSA's `ramp_limit_down`. It is the full build where PyPSA has none, since a shut-down ramp alone builds the row |
| $`\overleftarrow{\bar u}^{z}`$ | `Process_ramp_previous_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the status a committed process's ramp rows carry into a snapshot. At the first snapshot, a fixed modular process that came in running has every module on, since the state it brought in is on or off (`constraints.py:1152-1157`). The transition and down-time rows count it as one module (PyPSA/PyPSA\#2114). It is the state carried in otherwise |
| $`\Delta^{z,+}`$ | `Process_ramp_up_allowance` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — how far a process may raise internal power between two snapshots. It is its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\widetilde{\mathrm{ru}}^{z}`$ | `Process_ramp_up_rate` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the ramp limit in a process's up row, PyPSA's `ramp_limit_up`. It is the full build where PyPSA has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}^{z,\mathrm{dn}}`$ | `Process_shut_down_rate` over $`\mathcal{J} \times \Xi`$ — the shut-down ramp in a process's down row (PyPSA's `ramp_limit_shut_down`), or the full build where it has none |
| $`\widetilde{\mathrm{ru}}^{z,\mathrm{up}}`$ | `Process_start_up_rate` over $`\mathcal{J} \times \Xi`$ — the start-up ramp in a process's up row (PyPSA's `ramp_limit_start_up`), or the full build where it has none |
| $`\overleftarrow{u}^{\circ z}`$ | `Process_status_carried_over` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the state a process carries over into a snapshot: the state it brought into the horizon at the first, the previous snapshot's after that |
| $`\mathit{Process\_tech\_capacity\_expansion}`$ | `Process_tech_capacity_expansion` over $`\mathcal{O}`$ |
| $`\mathit{StorageUnit\_additions}`$ | `StorageUnit_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{StorageUnit\_capex}`$ | `StorageUnit_capex` (scalar) |
| $`\overleftarrow{\mathit{soc}}`$ | `StorageUnit_charge_carried_in` over $`\Xi \times \mathcal{T} \times \mathcal{S}`$ — the charge a unit opens a snapshot with. At the first snapshot it is active in, it is its last such snapshot's less standing loss where it is cyclic. Where it is not, it is the given initial charge, which no standing loss has touched yet. Otherwise it is the previous snapshot's less standing loss. A unit built in a later period opens in that period, and a cyclic one that retires closes on its own last snapshot. Per period, the same holds with each investment period as the horizon |
| $`\mathit{w}^{h}`$ | `StorageUnit_closing_weight` over $`\mathcal{O} \times \Xi \times \mathcal{T} \times \mathcal{S}`$ — what the charge a unit holds at a snapshot counts for in a row as its closing level. Where the unit reopens per period, it is the years of the period at the last snapshot of each counted period. Where it does not, it is one at the last counted snapshot it is active in. It is nothing elsewhere |
| $`\mathit{StorageUnit\_injection}`$ | `StorageUnit_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{last}^{h}`$ | `StorageUnit_last_counted_active` over $`\mathcal{O} \times \Xi \times \mathcal{T} \times \mathcal{S}`$ — one at the last snapshot a row counts where a unit is active, and zero elsewhere. A unit that retires before the last counted snapshot closes on its last active level. PyPSA forward-fills the level over the counted snapshots (`global_constraints.py:476-479`) |
| $`\mathit{StorageUnit\_operational\_limit}`$ | `StorageUnit_operational_limit` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{StorageUnit\_opex}`$ | `StorageUnit_opex` over $`\Xi`$ |
| $`\mathit{StorageUnit\_primary\_energy}`$ | `StorageUnit_primary_energy` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{StorageUnit\_tech\_capacity\_expansion}`$ | `StorageUnit_tech_capacity_expansion` over $`\mathcal{O}`$ |
| $`\mathit{Store\_additions}`$ | `Store_additions` over $`\mathcal{I} \times \mathcal{Y}`$ |
| $`\mathit{Store\_capex}`$ | `Store_capex` (scalar) |
| $`\overline{\mathrm{q}}^{-}`$ | `Store_charge_cap_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — the most charging through `p_store`, per unit of `e_nom`. It is `-p_min_pu / max_hours` for a store that splits its dispatch, and zero otherwise (`stores.py:79-86`) |
| $`\mathit{w}^{e}`$ | `Store_closing_weight` over $`\mathcal{O} \times \Xi \times \mathcal{T} \times \mathcal{V}`$ — what the energy a store holds at a snapshot counts for in a row as its closing level. Where the store reopens per period, it is the years of the period at the last snapshot of each counted period. Where it does not, it is one at the last counted snapshot it is active in. It is nothing elsewhere |
| $`\underline{\mathrm{q}}^{+}`$ | `Store_discharge_floor_pu` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — the least discharge, per unit of `e_nom`. It is zero for a store that splits its dispatch, so `p_store` carries the charge. Otherwise it is the most charging as a negative discharge, `p_min_pu / max_hours` (`stores.py:79-86`) |
| $`\widetilde{\mathrm{e}}^{\mathrm{nom}}`$ | `Store_e_nom_effective` over $`\Xi \times \mathcal{V}`$ — the build a store's limits are taken against: the chosen one where it is extendable, the given one otherwise |
| $`\overleftarrow{e}`$ | `Store_energy_carried_in` over $`\Xi \times \mathcal{T} \times \mathcal{V}`$ — the energy a store opens a snapshot with. At the first snapshot it is active in, it is its last such snapshot's less standing loss where it is cyclic. Where it is not, it is the given initial energy, which no standing loss has touched yet. Otherwise it is the previous snapshot's less standing loss. A store built in a later period opens in that period, and a cyclic one that retires closes on its own last snapshot. Per period, the same holds with each investment period as the horizon |
| $`\mathit{Store\_injection}`$ | `Store_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{last}^{e}`$ | `Store_last_counted_active` over $`\mathcal{O} \times \Xi \times \mathcal{T} \times \mathcal{V}`$ — one at the last snapshot a row counts where a store is active, and zero elsewhere. A store that retires before the last counted snapshot closes on its last active level. PyPSA forward-fills the level over the counted snapshots (`global_constraints.py:528-531`) |
| $`\mathit{Store\_operational\_limit}`$ | `Store_operational_limit` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{Store\_opex}`$ | `Store_opex` over $`\Xi`$ |
| $`\mathit{Store\_primary\_energy}`$ | `Store_primary_energy` over $`\mathcal{O} \times \Xi`$ |
| $`\mathit{Store\_tech\_capacity\_expansion}`$ | `Store_tech_capacity_expansion` over $`\mathcal{O}`$ |
| $`\mathit{Transformer\_angle\_sum}`$ | `Transformer_angle_sum` over $`\mathcal{C} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{Transformer\_capex}`$ | `Transformer_capex` (scalar) |
| $`\mathit{Transformer\_injection}`$ | `Transformer_injection` over $`\mathcal{N} \times \Xi \times \mathcal{T}`$ |
| $`\check{\sigma}`$ | `Transformer_s_monitored` over $`\Xi \times \mathcal{T} \times \mathcal{M}`$ — the flow a transformer's post-contingency rows read, as a line's |
| $`\mathit{w}^{E}`$ | `energy_limit_weight` over $`\mathcal{T}`$ — what one unit of power at a snapshot counts for in an `e_sum` row: the generator weighting times the years of the snapshot's period, as in an `operational_limit` row (`constraints.py:2935-2937`) |
| $`\mathit{operational\_limit}`$ | `operational_limit` over $`\mathcal{O} \times \Xi`$ — what an `operational_limit` row totals: the weighted energy its generators deliver over the snapshots it counts, plus what its non-cyclic storage draws down. The initial charge it draws from is folded into the row's constant |
| $`\mathit{primary\_energy}`$ | `primary_energy` over $`\mathcal{O} \times \Xi`$ — what a `primary_energy` row totals: weighted generator energy over the snapshots it counts, less the charge left in weighted storage at the close. The initial charge it is compared against is folded into the row's constant |
| $`\mathit{risk\_weighted\_opex}`$ | `risk_weighted_opex` (scalar) |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$ — what a future costs to run: every operating term, weighted by the snapshot's hours and its period, before the scenario's own weight. A start and a stop cost what they cost, unweighted, as PyPSA adds them (`optimize.py:448-468`) |
| $`\mathit{tech\_capacity\_expansion}`$ | `tech_capacity_expansion` over $`\mathcal{O}`$ — what a `tech_capacity_expansion_limit` row totals: the chosen build of the row's carrier-and-bus set |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar) — what the system costs. Capacity counts once per active period at its expected cost over the scenarios. Operation counts in expectation over the scenarios, and a share of it at the tail |
| $`\mathit{transmission\_expansion\_cost}`$ | `transmission_expansion_cost` over $`\mathcal{O} \times \Xi`$ — what a `transmission_expansion_cost_limit` row totals: capital cost times the chosen build of the row's branches |
| $`\mathit{transmission\_volume\_expansion}`$ | `transmission_volume_expansion` over $`\mathcal{O} \times \Xi`$ — what a `transmission_volume_expansion_limit` row totals: length times the chosen build of the row's branches |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`t \ominus^{\mathrm{relation}(t)} k`$ | `within=relation[...]` — $`t-k`$ inside the group of $`t`$ |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |
| $`\lvert \mathcal{T} \rvert`$ | the size of $`\mathcal{T}`$; $`\lvert \mathcal{T} \rvert - 1`$ is the last position |

### `Generator_com_ext`

```yaml
Generator_com_ext:
  description: >-
    a committable generator with an extendable, non-modular build that
    is active in the snapshot's period. These are PyPSA's `com-ext` rows, whose
    status is relaxed against the chosen build
  condition: >-
    Generator_committable
    AND Generator_p_nom_extendable
    AND NOT (Generator_p_nom_mod > 0)
    AND Generator_active
```

```math
\mathrm{on}^{\mathrm{com,ext}}_{g,t} \iff \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \wedge \mathrm{on}_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

### `Generator_committed`

```yaml
Generator_committed:
  description: >-
    a committable generator that is active in the snapshot's period: every
    unit-commitment row's set
  condition: Generator_committable AND Generator_active
```

```math
\mathrm{on}^{\mathrm{com}}_{g,t} \iff \mathrm{com}_{g} \wedge \mathrm{on}_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

### `Generator_maint_ext`

```yaml
Generator_maint_ext:
  description: >-
    a maintainable generator with an extendable build that is active in the
    snapshot's period, unless it is committable and modular. These are the
    maintenance rows against the chosen build
  condition: >-
    Generator_maintainable
    AND Generator_p_nom_extendable
    AND NOT (Generator_committable AND Generator_p_nom_mod > 0)
    AND Generator_active
```

```math
\mathrm{on}^{\mathrm{mnt,ext}}_{g,t} \iff \mathrm{mnt}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \wedge \mathrm{on}_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

### `Generator_marginal_cost_as_lp`

```yaml
Generator_marginal_cost_as_lp:
  description: >-
    linopy's choice of method for all generator cost curves at once
    (`method="auto"`): the segment lines where every curve is convex and no
    generator with a curve is committable, the incremental rows otherwise.
    PyPSA gates the curves by `Generator-status` where one is committable,
    and linopy states no segment lines under a gate (`optimize.py:314-318`,
    `piecewise.py:193-217`)
  condition: >-
    count(Generator_marginal_cost_curve AND count(Generator_marginal_cost_curve_bends_down, over=breakpoint) > 0, over=generator) == 0
    AND count(Generator_marginal_cost_curve AND Generator_committable, over=generator) == 0
```

```math
\mathrm{lp} \iff \lvert \{ g \in \mathcal{G} \,:\, \mathrm{curve}_{g} \wedge \lvert \{ b \in \mathcal{B} \,:\, \mathrm{bend}_{b,g} \} \rvert > 0 \} \rvert = 0 \wedge \lvert \{ g \in \mathcal{G} \,:\, \mathrm{curve}_{g} \wedge \mathrm{com}_{g} \} \rvert = 0
```

### `Generator_marginal_cost_curve`

```yaml
Generator_marginal_cost_curve:
  description: >-
    a generator that pays along a piecewise `marginal_cost` curve: one of
    PyPSA's `active_assets` with curve data (`optimize.py:307`,
    `piecewise.py:223-250`)
  condition: count(Generator_marginal_cost_curve_p, over=breakpoint) > 0 AND Generator_active_asset
```

```math
\mathrm{curve}_{g} \iff \lvert \{ b \in \mathcal{B} \,:\, \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined} \} \rvert > 0 \wedge \mathrm{act}_{g} \qquad \forall\, g \in \mathcal{G}
```

### `Generator_marginal_cost_curve_bends_down`

```yaml
Generator_marginal_cost_curve_bends_down:
  description: >-
    a breakpoint where a generator's cost curve gets less steep: the
    segment after it rises less per unit of output than the one before
  condition: >-
    Generator_marginal_cost_curve_p
    AND shift(Generator_marginal_cost_curve_p, along=breakpoint, offset=1)
    AND shift(Generator_marginal_cost_curve_p, along=breakpoint, offset=-1)
    AND (Generator_marginal_cost_curve_cost - shift(Generator_marginal_cost_curve_cost, along=breakpoint, offset=1, edge=0))
    * (shift(Generator_marginal_cost_curve_p, along=breakpoint, offset=-1, edge=0) - Generator_marginal_cost_curve_p)
    > (shift(Generator_marginal_cost_curve_cost, along=breakpoint, offset=-1, edge=0) - Generator_marginal_cost_curve_cost)
    * (Generator_marginal_cost_curve_p - shift(Generator_marginal_cost_curve_p, along=breakpoint, offset=1, edge=0))
```

```math
\mathrm{bend}_{b,g} \iff \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined} \wedge \mathrm{p}^{\mathrm{curve}}_{b - 1,g} \text{ is defined} \wedge \mathrm{p}^{\mathrm{curve}}_{b + 1,g} \text{ is defined} \wedge \left( \mathrm{C}^{\mathrm{curve}}_{b,g} - \mathrm{C}^{\mathrm{curve}}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{p}^{\mathrm{curve}}_{b \boxplus_{0} 1,g} - \mathrm{p}^{\mathrm{curve}}_{b,g} \right) > \left( \mathrm{C}^{\mathrm{curve}}_{b \boxplus_{0} 1,g} - \mathrm{C}^{\mathrm{curve}}_{b,g} \right) \cdot \left( \mathrm{p}^{\mathrm{curve}}_{b,g} - \mathrm{p}^{\mathrm{curve}}_{b \boxminus_{0} 1,g} \right) \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G}
```

### `Generator_ramps_from_previous`

```yaml
Generator_ramps_from_previous:
  description: >-
    a snapshot whose ramp uses a previous output. It is any snapshot but its
    period's first, and the horizon's first where the generator comes in off
    or carries an initial output
  condition: >-
    position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
    (Generator_status_initial == 0 OR Generator_p_init))
```

```math
\mathrm{prev}_{g,\xi,t} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{0}_{g,\xi} = 0 \vee \mathrm{p}^{0}_{g,\xi} \text{ is defined} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Line_lossy`

```yaml
Line_lossy:
  description: >-
    a line that is active in the snapshot's period, where the run models
    transmission losses
  condition: transmission_losses AND Line_active
```

```math
\mathrm{on}^{s,\mathrm{lossy}}_{k,t} \iff \mathrm{lossy} \wedge \mathrm{on}^{s}_{k,t} \qquad \forall\, k \in \mathcal{K},\ t \in \mathcal{T}
```

### `Link_com_ext`

```yaml
Link_com_ext:
  description: >-
    a committable link with an extendable, non-modular build that is active in
    the snapshot's period. These are PyPSA's `com-ext` rows, whose status is
    relaxed against the chosen build
  condition: >-
    Link_committable
    AND Link_p_nom_extendable
    AND NOT (Link_p_nom_mod > 0)
    AND Link_active
```

```math
\mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \iff \mathrm{com}^{f}_{l} \wedge \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \wedge \mathrm{on}^{f}_{l,t} \qquad \forall\, l \in \mathcal{L},\ t \in \mathcal{T}
```

### `Link_committed`

```yaml
Link_committed:
  description: >-
    a committable link that is active in the snapshot's period: every
    unit-commitment row's set
  condition: Link_committable AND Link_active
```

```math
\mathrm{on}^{f,\mathrm{com}}_{l,t} \iff \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t} \qquad \forall\, l \in \mathcal{L},\ t \in \mathcal{T}
```

### `Link_maint_ext`

```yaml
Link_maint_ext:
  description: >-
    a maintainable link with an extendable build that is active in the
    snapshot's period, unless it is committable and modular. These are the
    maintenance rows against the chosen build
  condition: >-
    Link_maintainable
    AND Link_p_nom_extendable
    AND NOT (Link_committable AND Link_p_nom_mod > 0)
    AND Link_active
```

```math
\mathrm{on}^{f,\mathrm{mnt,ext}}_{l,t} \iff \mathrm{mnt}^{f}_{l} \wedge \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{com}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \wedge \mathrm{on}^{f}_{l,t} \qquad \forall\, l \in \mathcal{L},\ t \in \mathcal{T}
```

### `Link_ramps_from_previous`

```yaml
Link_ramps_from_previous:
  description: >-
    a snapshot whose ramp uses a previous output. It is any snapshot but its
    period's first, and the horizon's first where the link comes in off or
    carries an initial output
  condition: >-
    position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
    (Link_status_initial == 0 OR Link_p_init))
```

```math
\mathrm{prev}^{f}_{l,\xi,t} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{f,0}_{l,\xi} = 0 \vee \mathrm{f}^{0}_{l,\xi} \text{ is defined} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_com_ext`

```yaml
Process_com_ext:
  description: >-
    a committable process with an extendable, non-modular build that is active
    in the snapshot's period. These are PyPSA's `com-ext` rows, whose status
    is relaxed against the chosen build
  condition: >-
    Process_committable
    AND Process_p_nom_extendable
    AND NOT (Process_p_nom_mod > 0)
    AND Process_active
```

```math
\mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \iff \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \wedge \mathrm{on}^{z}_{j,t} \qquad \forall\, j \in \mathcal{J},\ t \in \mathcal{T}
```

### `Process_committed`

```yaml
Process_committed:
  description: >-
    a committable process that is active in the snapshot's period: every
    unit-commitment row's set
  condition: Process_committable AND Process_active
```

```math
\mathrm{on}^{z,\mathrm{com}}_{j,t} \iff \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t} \qquad \forall\, j \in \mathcal{J},\ t \in \mathcal{T}
```

### `Process_maint_ext`

```yaml
Process_maint_ext:
  description: >-
    a maintainable process with an extendable build that is active in the
    snapshot's period, unless it is committable and modular. These are the
    maintenance rows against the chosen build
  condition: >-
    Process_maintainable
    AND Process_p_nom_extendable
    AND NOT (Process_committable AND Process_p_nom_mod > 0)
    AND Process_active
```

```math
\mathrm{on}^{z,\mathrm{mnt,ext}}_{j,t} \iff \mathrm{mnt}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \wedge \mathrm{on}^{z}_{j,t} \qquad \forall\, j \in \mathcal{J},\ t \in \mathcal{T}
```

### `Process_ramps_from_previous`

```yaml
Process_ramps_from_previous:
  description: >-
    a snapshot whose ramp uses a previous output. It is any snapshot but its
    period's first, and the horizon's first where the process comes in off
    or carries an initial output
  condition: >-
    position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
    (Process_status_initial == 0 OR Process_p_init))
```

```math
\mathrm{prev}^{z}_{j,\xi,t} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{z,0}_{j,\xi} = 0 \vee \mathrm{z}^{0}_{j,\xi} \text{ is defined} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `StorageUnit_ext`

```yaml
StorageUnit_ext:
  description: >-
    a storage unit with an extendable build that is active in the snapshot's
    period. It is PyPSA's `ext` rows
  condition: StorageUnit_p_nom_extendable AND StorageUnit_active
```

```math
\mathrm{on}^{h,\mathrm{ext}}_{t,s} \iff \mathrm{ext}^{h}_{s} \wedge \mathrm{on}^{h}_{t,s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
```

### `StorageUnit_fix`

```yaml
StorageUnit_fix:
  description: >-
    a storage unit with a fixed build that is active in the snapshot's period.
    It is PyPSA's `fix` rows
  condition: NOT StorageUnit_p_nom_extendable AND StorageUnit_active
```

```math
\mathrm{on}^{h,\mathrm{fix}}_{t,s} \iff \neg \mathrm{ext}^{h}_{s} \wedge \mathrm{on}^{h}_{t,s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
```

### `Transformer_lossy`

```yaml
Transformer_lossy:
  description: >-
    a transformer that is active in the snapshot's period, where the run models
    transmission losses
  condition: transmission_losses AND Transformer_active
```

```math
\mathrm{on}^{\sigma,\mathrm{lossy}}_{t,m} \iff \mathrm{lossy} \wedge \mathrm{on}^{\sigma}_{t,m} \qquad \forall\, t \in \mathcal{T},\ m \in \mathcal{M}
```

#### Variable domains

**`CVaR`**

```math
CVaR \in \mathbb{R} \qquad \text{where } \omega \text{ is defined}
```

**`CVaR_a`**

```math
a_{\xi} \ge 0 \qquad \forall\, \xi \in \Xi \,:\, \omega \text{ is defined}
```

**`CVaR_theta`**

```math
\theta \in \mathbb{R} \qquad \text{where } \omega \text{ is defined}
```

**`FlowBased_net_position`**

```math
\mathit{NP}_{n,\xi,t} \in \mathbb{R} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{zone}_{n}
```

**`Generator_maintenance`**

```math
0 \le \mu_{g,\xi,t} \le 1 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{g,t}
```

**`Generator_maintenance_capacity`**

```math
\mu^{\mathrm{nom}}_{g,\xi,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{g,t}
```

**`Generator_maintenance_start`**

```math
\mu^{\mathrm{up}}_{g,\xi,t} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{g,t}
```

**`Generator_maintenance_status`**

```math
\mu^{u}_{g,\xi,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \left( \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right)
```

**`Generator_marginal_cost_piecewise`**

```math
C^{\mathrm{curve}}_{g,\xi,t} \in \mathbb{R} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t}
```

**`Generator_n_mod`**

```math
N_{g} \ge 0, N_{g} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \wedge \mathrm{act}_{g}
```

**`Generator_p`**

```math
p_{g,\xi,t} \in \mathbb{R} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}_{g,t}
```

**`Generator_p_nom_ext`**

```math
P_{g} \in \mathbb{R} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g}
```

**`Generator_shut_down`**

```math
\mathit{dn}_{g,\xi,t} \ge 0, \mathit{dn}_{g,\xi,t} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

**`Generator_start_up`**

```math
\mathit{up}_{g,\xi,t} \ge 0, \mathit{up}_{g,\xi,t} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

**`Generator_status`**

```math
u_{g,\xi,t} \ge 0, u_{g,\xi,t} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

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

**`Link_maintenance`**

```math
0 \le \mu^{f}_{l,\xi,t} \le 1 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_maintenance_capacity`**

```math
\mu^{f,\mathrm{nom}}_{l,\xi,t} \ge 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{mnt,ext}}_{l,t}
```

**`Link_maintenance_start`**

```math
\mu^{f,\mathrm{up}}_{l,\xi,t} \in \{0, 1\} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_maintenance_status`**

```math
\mu^{f,u}_{l,\xi,t} \ge 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \left( \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \right)
```

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

**`Link_shut_down`**

```math
\mathit{dn}^{f}_{l,\xi,t} \ge 0, \mathit{dn}^{f}_{l,\xi,t} \in \mathbb{Z} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

**`Link_start_up`**

```math
\mathit{up}^{f}_{l,\xi,t} \ge 0, \mathit{up}^{f}_{l,\xi,t} \in \mathbb{Z} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

**`Link_status`**

```math
u^{f}_{l,\xi,t} \ge 0, u^{f}_{l,\xi,t} \in \mathbb{Z} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

**`Process_maintenance`**

```math
0 \le \mu^{z}_{j,\xi,t} \le 1 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_maintenance_capacity`**

```math
\mu^{z,\mathrm{nom}}_{j,\xi,t} \ge 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{j,t}
```

**`Process_maintenance_start`**

```math
\mu^{z,\mathrm{up}}_{j,\xi,t} \in \{0, 1\} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_maintenance_status`**

```math
\mu^{z,u}_{j,\xi,t} \ge 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right)
```

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

**`Process_shut_down`**

```math
\mathit{dn}^{z}_{j,\xi,t} \ge 0, \mathit{dn}^{z}_{j,\xi,t} \in \mathbb{Z} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

**`Process_start_up`**

```math
\mathit{up}^{z}_{j,\xi,t} \ge 0, \mathit{up}^{z}_{j,\xi,t} \in \mathbb{Z} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

**`Process_status`**

```math
u^{z}_{j,\xi,t} \ge 0, u^{z}_{j,\xi,t} \in \mathbb{Z} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

**`StorageUnit_n_mod`**

```math
N^{h}_{s} \ge 0, N^{h}_{s} \in \mathbb{Z} \qquad \forall\, s \in \mathcal{S} \,:\, \mathrm{ext}^{h}_{s} \wedge \mathrm{h}^{\mathrm{mod}}_{s} > 0 \wedge \mathrm{act}^{h}_{s}
```

**`StorageUnit_p_dispatch`**

```math
h^{+}_{\xi,t,s} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h}_{t,s}
```

**`StorageUnit_p_nom_ext`**

```math
H_{s} \in \mathbb{R} \qquad \forall\, s \in \mathcal{S} \,:\, \mathrm{ext}^{h}_{s} \wedge \mathrm{act}^{h}_{s}
```

**`StorageUnit_p_store`**

```math
h^{-}_{\xi,t,s} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h}_{t,s}
```

**`StorageUnit_spill`**

```math
0 \le \mathit{spill}_{\xi,t,s} \le \mathrm{inflow}_{\xi,t,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{inflow}_{\xi,t,s} > 0 \wedge \mathrm{on}^{h}_{t,s}
```

**`StorageUnit_state_of_charge`**

```math
\mathit{soc}_{\xi,t,s} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h}_{t,s}
```

**`Store_e`**

```math
e_{\xi,t,v} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v}
```

**`Store_e_nom_ext`**

```math
E_{v} \in \mathbb{R} \qquad \forall\, v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v}
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

**`Transformer_loss`**

```math
\ell^{\sigma}_{\xi,t,m} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{on}^{\sigma,\mathrm{lossy}}_{t,m}
```

**`Transformer_n_mod`**

```math
N^{\sigma}_{m} \ge 0, N^{\sigma}_{m} \in \mathbb{Z} \qquad \forall\, m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \sigma^{\mathrm{mod}}_{m} > 0 \wedge \mathrm{act}^{\sigma}_{m}
```

**`Transformer_phase_shift`**

```math
\mathrm{Transformer\_phase\_shift\_min}_{m} \le \mathit{Transformer\_phase\_shift}_{\xi,t,m} \le \mathrm{Transformer\_phase\_shift\_max}_{m} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{Transformer\_phase\_shift\_varying}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

**`Transformer_s`**

```math
\sigma_{\xi,t,m} \in \mathbb{R} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{on}^{\sigma}_{t,m}
```

**`Transformer_s_nom_ext`**

```math
\Sigma_{m} \in \mathbb{R} \qquad \forall\, m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{act}^{\sigma}_{m}
```

### `Bus_injection`

```yaml
Bus_injection:
  dims: [scenario, snapshot, bus]
  expression: >-
    FlowBased_injection
    + Generator_injection
    + Line_injection
    + Link_injection
    + Load_injection
    + Process_injection
    + StorageUnit_injection
    + Store_injection
    + Transformer_injection
  description: >-
    what every component puts into a bus, less what it takes out of it.
    PyPSA writes each term into the balance, and a load on its right-hand
    side
```

```math
\mathit{Bus\_injection}_{n,\xi,t} = \mathit{NP}^{\mathrm{inj}}_{n,\xi,t} + \mathit{Generator\_injection}_{n,\xi,t} + \mathit{Line\_injection}_{n,\xi,t} + \mathit{Link\_injection}_{n,\xi,t} + \mathrm{Load\_injection}_{n,\xi,t} + \mathit{Process\_injection}_{n,\xi,t} + \mathit{StorageUnit\_injection}_{n,\xi,t} + \mathit{Store\_injection}_{n,\xi,t} + \mathit{Transformer\_injection}_{n,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Carrier_additions`

```yaml
Carrier_additions:
  dims: [period, carrier]
  expression: >-
    Generator_additions
    + Line_additions
    + Link_additions
    + Process_additions
    + StorageUnit_additions
    + Store_additions
  description: >-
    what a carrier adds in a period: every extendable component of that
    carrier, counting each build in the first period it is active in. Like
    PyPSA, it sums only the components that carry a carrier attribute, so a
    transformer, which has none, counts in no carrier
```

```math
\mathit{Carrier\_additions}_{i,y} = \mathit{Generator\_additions}_{i,y} + \mathit{Line\_additions}_{i,y} + \mathit{Link\_additions}_{i,y} + \mathit{Process\_additions}_{i,y} + \mathit{StorageUnit\_additions}_{i,y} + \mathit{Store\_additions}_{i,y} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

### `Carrier_relative_growth`

```yaml
Carrier_relative_growth:
  description: >-
    the share of the previous period's additions in a carrier's growth
    limit, PyPSA's `max_relative_growth` clipped at zero. A negative share
    thus adds nothing and never tightens the limit
  dims: [carrier]
  cases:
    positive: { when: Carrier_max_relative_growth > 0, expression: Carrier_max_relative_growth }
  otherwise: 0
```

```math
\mathrm{r}^{+}_{i} = \begin{cases} \mathrm{r}_{i} & \text{if } \mathrm{r}_{i} > 0 \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, i \in \mathcal{I}
```

### `Cycle_angle_sum`

```yaml
Cycle_angle_sum:
  dims: [scenario, snapshot, cycle]
  expression: Line_angle_sum + Transformer_angle_sum
  description: >-
    the voltage angle differences around a cycle: every branch flow times
    its cycle weight, and every transformer phase shift
```

```math
\mathit{Cycle\_angle\_sum}_{c,\xi,t} = \mathit{Line\_angle\_sum}_{c,\xi,t} + \mathit{Transformer\_angle\_sum}_{c,\xi,t} \qquad \forall\, c \in \mathcal{C},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `FlowBased_injection`

```yaml
FlowBased_injection:
  description: what a zone bus exports to its flow-based domain leaves the bus (`constraints.py:1578`)
  dims: [scenario, snapshot, bus]
  expression: -FlowBased_net_position
```

```math
\mathit{NP}^{\mathrm{inj}}_{n,\xi,t} = -\mathit{NP}_{n,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_additions`

```yaml
Generator_additions:
  expression: >-
    sum(Generator_p_nom_ext * Generator_first_active, over=generator, by=Generator_carrier[carrier])
```

```math
\mathit{Generator\_additions}_{i,y} = \sum_{g \in \mathcal{G} \,:\, \mathrm{Generator\_carrier}(g) = i} P_{g} \cdot \mathrm{new}_{g,y} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

### `Generator_capex`

```yaml
Generator_capex:
  expression: sum(scenario_weight * Generator_p_nom_ext * Generator_capital_cost * Generator_capital_weight)
```

```math
\mathit{Generator\_capex} = \sum_{g \in \mathcal{G},\ \xi \in \Xi} \pi_{\xi} \cdot P_{g} \cdot \mathrm{c}^{\mathrm{cap}}_{g,\xi} \cdot \mathrm{W}_{g}
```

### `Generator_commitment_opex`

```yaml
Generator_commitment_opex:
  expression: >-
    sum(sum(((Generator_status * Generator_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
    + sum(sum((Generator_start_up * Generator_start_up_cost) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
    + sum(sum((Generator_shut_down * Generator_shut_down_cost) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
```

```math
\mathit{Generator\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} u_{g,\xi,t} \cdot \mathrm{c}^{\mathrm{on}}_{g,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} \mathit{up}_{g,\xi,t} \cdot \mathrm{c}^{\mathrm{up}}_{g,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} \mathit{dn}_{g,\xi,t} \cdot \mathrm{c}^{\mathrm{dn}}_{g,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `Generator_injection`

```yaml
Generator_injection:
  expression: sum(Generator_sign * Generator_p, over=generator, by=Generator_bus[bus])
```

```math
\mathit{Generator\_injection}_{n,\xi,t} = \sum_{g \in \mathcal{G} \,:\, \mathrm{Generator\_bus}(g) = n} \mathrm{sgn}_{g} \cdot p_{g,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_maintenance_modules`

```yaml
Generator_maintenance_modules:
  description: >-
    how many modules of a modular committable generator can be on in
    maintenance: its build cap in modules where the build is extendable,
    and the modules installed where it is fixed (`constraints.py:588-594`)
  dims: [scenario, generator]
  cases:
    extendable: { when: Generator_p_nom_extendable, expression: Generator_p_nom_max / Generator_p_nom_mod }
  otherwise: Generator_modules_installed
```

```math
\mathrm{Generator\_maintenance\_modules}_{g,\xi} = \begin{cases} \frac{\overline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi}}{\mathrm{p}^{\mathrm{mod}}_{g}} & \text{if } \mathrm{ext}_{g} \\ \mathrm{N}^{\mathrm{fix}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

### `Generator_modules`

```yaml
Generator_modules:
  description: >-
    how many modules a committed unit's status counts: the chosen number
    where the build is extendable and modular, and the modules installed
    otherwise (`constraints.py:656-661`)
  dims: [scenario, generator]
  cases:
    chosen: { when: Generator_p_nom_extendable AND Generator_p_nom_mod > 0, expression: Generator_n_mod }
  otherwise: Generator_modules_installed
```

```math
\mathrm{M}_{g,\xi} = \begin{cases} N_{g} & \text{if } \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \\ \mathrm{N}^{\mathrm{fix}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

### `Generator_operational_limit`

```yaml
Generator_operational_limit:
  expression: >-
    sum(sum((Generator_p * GlobalConstraint_energy_weight) * Generator_operational_limit_weight, over=snapshot), over=generator)
```

```math
\mathit{Generator\_operational\_limit}_{o,\xi} = \sum_{g \in \mathcal{G}} \sum_{t \in \mathcal{T}} p_{g,\xi,t} \cdot \mathit{w}^{\mathrm{gc}}_{o,\xi,t} \cdot \mathrm{b}_{g,o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Generator_opex`

```yaml
Generator_opex:
  expression: >-
    sum(sum((Generator_running_cost * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
    + sum(sum((((Generator_p * Generator_p) * Generator_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=generator), over=snapshot)
```

```math
\mathit{Generator\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} C^{\mathrm{run}}_{g,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} p_{g,\xi,t} \cdot p_{g,\xi,t} \cdot \mathrm{c}^{(2)}_{g,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `Generator_p_carried_over`

```yaml
Generator_p_carried_over:
  description: >-
    the output a generator carries over into a snapshot. At the first, it is
    the `p_init` it brought in where it came in running, and nothing where
    it came in off. After that, it is the previous snapshot's
  dims: [scenario, snapshot, generator]
  cases:
    opening: { when: "position(snapshot) == 0", expression: Generator_status_initial * Generator_p_init }
  otherwise: shift(Generator_p, along=snapshot, offset=1)
```

```math
\overleftarrow{p}^{\circ}_{g,\xi,t} = \begin{cases} \mathrm{u}^{0}_{g,\xi} \cdot \mathrm{p}^{0}_{g,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ p_{g,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_p_nom_committed`

```yaml
Generator_p_nom_committed:
  description: >-
    the build a committed unit's ramp rows are taken against: one module
    where the build is modular, since its status counts modules, and the
    given build otherwise (`constraints.py:1131-1134`)
  dims: [scenario, generator]
  cases:
    modular_build: { when: "Generator_p_nom_mod > 0", expression: Generator_p_nom_mod }
  otherwise: Generator_p_nom
```

```math
\widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} = \begin{cases} \mathrm{p}^{\mathrm{mod}}_{g} & \text{if } \mathrm{p}^{\mathrm{mod}}_{g} > 0 \\ \mathrm{p}^{\mathrm{nom}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

### `Generator_p_nom_effective`

```yaml
Generator_p_nom_effective:
  description: "the build a generator's limits are taken against: the chosen one where it is extendable, the given one otherwise"
  dims: [scenario, generator]
  cases:
    extendable: { when: Generator_p_nom_extendable, expression: Generator_p_nom_ext }
  otherwise: Generator_p_nom
```

```math
\widetilde{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} = \begin{cases} P_{g} & \text{if } \mathrm{ext}_{g} \\ \mathrm{p}^{\mathrm{nom}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

### `Generator_previous_p`

```yaml
Generator_previous_p:
  description: >-
    the output a generator carries into a snapshot. It is nothing at the
    first snapshot it is active in past the first of the horizon: PyPSA
    fills an output it did not build with zero (`constraints.py:716`).
    It is the output carried over otherwise
  dims: [scenario, snapshot, generator]
  cases:
    opening_late: { when: "position(snapshot) > 0 AND NOT shift(Generator_active, along=snapshot, offset=1)", expression: 0 }
  otherwise: Generator_p_carried_over
```

```math
\overleftarrow{p}_{g,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}_{g,t - 1} \\ \overleftarrow{p}^{\circ}_{g,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_previous_status`

```yaml
Generator_previous_status:
  description: >-
    the commitment state a generator carries into a snapshot. It is off at
    the first snapshot it is active in past the first of the horizon. PyPSA
    reads a status it did not build as off there (`constraints.py:391`). It
    is the state carried over otherwise
  dims: [scenario, snapshot, generator]
  cases:
    opening_late: { when: "position(snapshot) > 0 AND NOT shift(Generator_active, along=snapshot, offset=1)", expression: 0 }
  otherwise: Generator_status_carried_over
```

```math
\overleftarrow{u}_{g,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}_{g,t - 1} \\ \overleftarrow{u}^{\circ}_{g,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_primary_energy`

```yaml
Generator_primary_energy:
  expression: >-
    sum(sum((Generator_p * GlobalConstraint_energy_weight) * Generator_primary_energy_weight, over=snapshot), over=generator)
```

```math
\mathit{Generator\_primary\_energy}_{o,\xi} = \sum_{g \in \mathcal{G}} \sum_{t \in \mathcal{T}} p_{g,\xi,t} \cdot \mathit{w}^{\mathrm{gc}}_{o,\xi,t} \cdot \mathrm{a}_{g,o,\xi,t} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Generator_ramp_down_allowance`

```yaml
Generator_ramp_down_allowance:
  description: >-
    how far a generator may lower output between two snapshots. It is its
    ramp limit of the build while it stays on, plus its shut-down ramp in
    the snapshot it turns off
  dims: [scenario, snapshot, generator]
  cases:
    committed:
      when: Generator_committable
      expression: >-
        Generator_ramp_down_rate * Generator_p_nom_committed * Generator_status
        + Generator_shut_down_rate * Generator_p_nom_committed
        * (Generator_ramp_previous_status - Generator_status)
  otherwise: Generator_ramp_down_rate * Generator_p_nom_effective
```

```math
\Delta^{-}_{g,\xi,t} = \begin{cases} \widetilde{\mathrm{rd}}_{g,\xi,t} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot u_{g,\xi,t} + \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \left( \overleftarrow{\bar u}_{g,\xi,t} - u_{g,\xi,t} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{rd}}_{g,\xi,t} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_ramp_down_rate`

```yaml
Generator_ramp_down_rate:
  description: >-
    the ramp limit in a unit's down row, PyPSA's `ramp_limit_down`. It is
    the full build where PyPSA has none, since a shut-down ramp alone builds
    the row
  dims: [scenario, snapshot, generator]
  cases:
    given: { when: Generator_ramp_limit_down, expression: Generator_ramp_limit_down }
  otherwise: 1
```

```math
\widetilde{\mathrm{rd}}_{g,\xi,t} = \begin{cases} \mathrm{rd}_{g,\xi,t} & \text{if } \mathrm{rd}_{g,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_ramp_previous_status`

```yaml
Generator_ramp_previous_status:
  description: >-
    the status a committed unit's ramp rows carry into a snapshot. At the
    first snapshot, a fixed modular unit that came in running has every
    module on, since the state it brought in is on or off
    (`constraints.py:1152-1157`). The transition and down-time rows count it as one module
    (PyPSA/PyPSA#2114). It is the state carried in otherwise
  dims: [scenario, snapshot, generator]
  cases:
    opening_modules:
      when: "position(snapshot) == 0 AND NOT Generator_p_nom_extendable AND Generator_p_nom_mod > 0"
      expression: Generator_status_initial * Generator_modules_installed
  otherwise: Generator_previous_status
```

```math
\overleftarrow{\bar u}_{g,\xi,t} = \begin{cases} \mathrm{u}^{0}_{g,\xi} \cdot \mathrm{N}^{\mathrm{fix}}_{g,\xi} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \\ \overleftarrow{u}_{g,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_ramp_up_allowance`

```yaml
Generator_ramp_up_allowance:
  description: >-
    how far a generator may raise output between two snapshots. It is its
    ramp limit of the build while it stays on, plus its start-up ramp in the
    snapshot it turns on
  dims: [scenario, snapshot, generator]
  cases:
    committed:
      when: Generator_committable
      expression: >-
        Generator_ramp_up_rate * Generator_p_nom_committed * Generator_ramp_previous_status
        + Generator_start_up_rate * Generator_p_nom_committed
        * (Generator_status - Generator_ramp_previous_status)
  otherwise: Generator_ramp_up_rate * Generator_p_nom_effective
```

```math
\Delta^{+}_{g,\xi,t} = \begin{cases} \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \overleftarrow{\bar u}_{g,\xi,t} + \widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \left( u_{g,\xi,t} - \overleftarrow{\bar u}_{g,\xi,t} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_ramp_up_rate`

```yaml
Generator_ramp_up_rate:
  description: >-
    the ramp limit in a unit's up row, PyPSA's `ramp_limit_up`. It is the
    full build where PyPSA has none, since a start-up ramp alone builds the
    row
  dims: [scenario, snapshot, generator]
  cases:
    given: { when: Generator_ramp_limit_up, expression: Generator_ramp_limit_up }
  otherwise: 1
```

```math
\widetilde{\mathrm{ru}}_{g,\xi,t} = \begin{cases} \mathrm{ru}_{g,\xi,t} & \text{if } \mathrm{ru}_{g,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_running_cost`

```yaml
Generator_running_cost:
  description: >-
    what a generator's output costs in a snapshot: the value read off its
    piecewise curve where it has one, and its linear `marginal_cost`
    otherwise. A curve replaces the linear cost, as PyPSA drops the unit
    from that term (`optimize.py:333-348`)
  dims: [scenario, snapshot, generator]
  cases:
    curve: { when: Generator_marginal_cost_curve, expression: Generator_marginal_cost_piecewise }
  otherwise: Generator_p * Generator_marginal_cost
```

```math
C^{\mathrm{run}}_{g,\xi,t} = \begin{cases} C^{\mathrm{curve}}_{g,\xi,t} & \text{if } \mathrm{curve}_{g} \\ p_{g,\xi,t} \cdot \mathrm{c}_{g,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_shut_down_rate`

```yaml
Generator_shut_down_rate:
  description: >-
    the shut-down ramp in a unit's down row (PyPSA's
    `ramp_limit_shut_down`), or the full build where it has none
  dims: [scenario, generator]
  cases:
    given: { when: Generator_ramp_limit_shut_down, expression: Generator_ramp_limit_shut_down }
  otherwise: 1
```

```math
\widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} = \begin{cases} \mathrm{rd}^{\mathrm{dn}}_{g,\xi} & \text{if } \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

### `Generator_start_up_rate`

```yaml
Generator_start_up_rate:
  description: >-
    the start-up ramp in a unit's up row (PyPSA's `ramp_limit_start_up`), or
    the full build where it has none
  dims: [scenario, generator]
  cases:
    given: { when: Generator_ramp_limit_start_up, expression: Generator_ramp_limit_start_up }
  otherwise: 1
```

```math
\widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} = \begin{cases} \mathrm{ru}^{\mathrm{up}}_{g,\xi} & \text{if } \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

### `Generator_status_carried_over`

```yaml
Generator_status_carried_over:
  description: >-
    the state a generator carries over into a snapshot: the state it brought
    into the horizon at the first, the previous snapshot's after that
  dims: [scenario, snapshot, generator]
  cases:
    opening: { when: "position(snapshot) == 0", expression: Generator_status_initial }
  otherwise: shift(Generator_status, along=snapshot, offset=1)
```

```math
\overleftarrow{u}^{\circ}_{g,\xi,t} = \begin{cases} \mathrm{u}^{0}_{g,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ u_{g,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_tech_capacity_expansion`

```yaml
Generator_tech_capacity_expansion:
  expression: sum(Generator_p_nom_ext * Generator_tech_capacity_weight, over=generator)
```

```math
\mathit{Generator\_tech\_capacity\_expansion}_{o} = \sum_{g \in \mathcal{G}} P_{g} \cdot \mathrm{m}_{g,o} \qquad \forall\, o \in \mathcal{O}
```

### `GlobalConstraint_energy_weight`

```yaml
GlobalConstraint_energy_weight:
  description: >-
    what one unit of power at a snapshot counts for in a row. Where the row
    counts the snapshot, it is the generator weighting times the years of
    the snapshot's period. Where it does not, it is nothing
  dims: [scenario, global_constraint, snapshot]
  cases:
    counted:
      when: GlobalConstraint_counts_snapshot
      expression: snapshot_weightings_generators * at(period_weight_years, by=snapshot_period[period])
  otherwise: 0
```

```math
\mathit{w}^{\mathrm{gc}}_{o,\xi,t} = \begin{cases} \mathrm{w}^{\mathrm{gen}}_{t} \cdot \mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} & \text{if } \mathrm{in}_{o,\xi,t} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Line_additions`

```yaml
Line_additions:
  expression: >-
    sum(Line_s_nom_ext * Line_first_active, over=line, by=Line_carrier[carrier])
```

```math
\mathit{Line\_additions}_{i,y} = \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_carrier}(k) = i} S_{k} \cdot \mathrm{new}^{s}_{k,y} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

### `Line_angle_sum`

```yaml
Line_angle_sum: sum(Line_s * at(Line_cycle_weight, by=snapshot_period[period]), over=line)
```

```math
\mathit{Line\_angle\_sum}_{c,\xi,t} = \sum_{k \in \mathcal{K}} s_{k,\xi,t} \cdot \mathrm{x}_{c,k,\mathrm{snapshot\_period}(t)} \qquad \forall\, c \in \mathcal{C},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Line_capex`

```yaml
Line_capex:
  expression: sum(scenario_weight * Line_s_nom_ext * Line_capital_cost * Line_capital_weight)
```

```math
\mathit{Line\_capex} = \sum_{k \in \mathcal{K},\ \xi \in \Xi} \pi_{\xi} \cdot S_{k} \cdot \mathrm{c}^{\mathrm{cap},s}_{k,\xi} \cdot \mathrm{W}^{s}_{k}
```

### `Line_injection`

```yaml
Line_injection:
  expression: >-
    -sum(Line_s, over=line, by=Line_bus0[bus])
    + sum(Line_s, over=line, by=Line_bus1[bus])
    - (0.5 * sum(Line_loss, over=line, by=Line_bus0[bus]))
    - (0.5 * sum(Line_loss, over=line, by=Line_bus1[bus]))
```

```math
\mathit{Line\_injection}_{n,\xi,t} = -\left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus0}(k) = n} s_{k,\xi,t} \right) + \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus1}(k) = n} s_{k,\xi,t} - 0.5 \cdot \left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus0}(k) = n} \ell_{k,\xi,t} \right) - 0.5 \cdot \left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus1}(k) = n} \ell_{k,\xi,t} \right) \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Line_s_monitored`

```yaml
Line_s_monitored:
  description: >-
    the flow in a line's post-contingency rows. It is its flow where it
    is active, and nothing where it does not. PyPSA builds those rows for every
    branch of the sub-network in every snapshot
  dims: [scenario, snapshot, line]
  cases:
    standing: { when: Line_active, expression: Line_s }
  otherwise: 0
```

```math
\check{s}_{k,\xi,t} = \begin{cases} s_{k,\xi,t} & \text{if } \mathrm{on}^{s}_{k,t} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Line_tech_capacity_expansion`

```yaml
Line_tech_capacity_expansion:
  expression: sum(Line_s_nom_ext * Line_tech_capacity_weight, over=line)
```

```math
\mathit{Line\_tech\_capacity\_expansion}_{o} = \sum_{k \in \mathcal{K}} S_{k} \cdot \mathrm{m}^{l}_{o,k} \qquad \forall\, o \in \mathcal{O}
```

### `Line_transmission_expansion_cost`

```yaml
Line_transmission_expansion_cost:
  expression: sum(Line_s_nom_ext * Line_expansion_cost_weight, over=line)
```

```math
\mathit{Line\_transmission\_expansion\_cost}_{o,\xi} = \sum_{k \in \mathcal{K}} S_{k} \cdot \mathrm{cc}_{o,k,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Line_transmission_volume_expansion`

```yaml
Line_transmission_volume_expansion:
  expression: sum(Line_s_nom_ext * Line_volume_weight, over=line)
```

```math
\mathit{Line\_transmission\_volume\_expansion}_{o,\xi} = \sum_{k \in \mathcal{K}} S_{k} \cdot \mathrm{len}_{o,k,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Link_additions`

```yaml
Link_additions:
  expression: >-
    sum(Link_p_nom_ext * Link_first_active, over=link, by=Link_carrier[carrier])
```

```math
\mathit{Link\_additions}_{i,y} = \sum_{l \in \mathcal{L} \,:\, \mathrm{Link\_carrier}(l) = i} F_{l} \cdot \mathrm{new}^{f}_{l,y} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

### `Link_capex`

```yaml
Link_capex:
  expression: sum(scenario_weight * Link_p_nom_ext * Link_capital_cost * Link_capital_weight)
```

```math
\mathit{Link\_capex} = \sum_{l \in \mathcal{L},\ \xi \in \Xi} \pi_{\xi} \cdot F_{l} \cdot \mathrm{c}^{\mathrm{cap},f}_{l,\xi} \cdot \mathrm{W}^{f}_{l}
```

### `Link_commitment_opex`

```yaml
Link_commitment_opex:
  expression: >-
    sum(sum(((Link_status * Link_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
    + sum(sum((Link_start_up * Link_start_up_cost) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
    + sum(sum((Link_shut_down * Link_shut_down_cost) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
```

```math
\mathit{Link\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} u^{f}_{l,\xi,t} \cdot \mathrm{c}^{f,\mathrm{on}}_{l,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} \mathit{up}^{f}_{l,\xi,t} \cdot \mathrm{c}^{f,\mathrm{up}}_{l,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} \mathit{dn}^{f}_{l,\xi,t} \cdot \mathrm{c}^{f,\mathrm{dn}}_{l,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `Link_injection`

```yaml
Link_injection:
  expression: >-
    -sum(Link_p, over=link, by=Link_bus0[bus])
    + sum(Link_output_arrival, over=link_output, by=Link_output_bus[bus])
```

```math
\mathit{Link\_injection}_{n,\xi,t} = -\left( \sum_{l \in \mathcal{L} \,:\, \mathrm{Link\_bus0}(l) = n} f_{l,\xi,t} \right) + \sum_{o \in \mathcal{O} \,:\, \mathrm{Link\_output\_bus}(o) = n} \overrightarrow{f}_{o,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_maintenance_modules`

```yaml
Link_maintenance_modules:
  description: >-
    how many modules of a modular committable link can be on in
    maintenance: its build cap in modules where the build is extendable,
    and the modules installed where it is fixed (`constraints.py:588-594`)
  dims: [scenario, link]
  cases:
    extendable: { when: Link_p_nom_extendable, expression: Link_p_nom_max / Link_p_nom_mod }
  otherwise: Link_modules_installed
```

```math
\mathrm{Link\_maintenance\_modules}_{l,\xi} = \begin{cases} \frac{\overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi}}{\mathrm{f}^{\mathrm{mod}}_{l}} & \text{if } \mathrm{ext}^{f}_{l} \\ \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

### `Link_modules`

```yaml
Link_modules:
  description: >-
    how many modules a committed link's status counts: the chosen number
    where the build is extendable and modular, and the modules installed
    otherwise (`constraints.py:656-661`)
  dims: [scenario, link]
  cases:
    chosen: { when: Link_p_nom_extendable AND Link_p_nom_mod > 0, expression: Link_n_mod }
  otherwise: Link_modules_installed
```

```math
\mathrm{M}^{f}_{l,\xi} = \begin{cases} N^{f}_{l} & \text{if } \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \\ \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

### `Link_opex`

```yaml
Link_opex:
  expression: >-
    sum(sum(((Link_p * Link_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
    + sum(sum((((Link_p * Link_p) * Link_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
```

```math
\mathit{Link\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} f_{l,\xi,t} \cdot \mathrm{c}^{f}_{l,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} f_{l,\xi,t} \cdot f_{l,\xi,t} \cdot \mathrm{c}^{f,(2)}_{l,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `Link_output_arrival`

```yaml
Link_output_arrival:
  description: >-
    what a link delivers to an output port at a snapshot. It is its flow
    delayed by the port's `delay` within its investment period. It is
    multiplied by the port's efficiency at the snapshot the flow arrives.
    Where the port is `cyclic_delay`, the delayed flow wraps from the
    period's end. Where it is not, the flow still in transit at the period's
    first snapshots is lost. A port that does not delay (`delay` zero)
    delivers its flow unshifted, cyclic or not
  dims: [scenario, snapshot, link_output]
  cases:
    wrapping:
      when: Link_output_cyclic_delay
      expression: shift(at(Link_p, by=Link_output_link[link]), along=snapshot, offset=Link_output_delay, edge='wrap', within=snapshot_period[period]) * Link_efficiency
  otherwise: shift(at(Link_p, by=Link_output_link[link]), along=snapshot, offset=Link_output_delay, edge=0, within=snapshot_period[period]) * Link_efficiency
```

```math
\overrightarrow{f}_{o,\xi,t} = \begin{cases} f_{\mathrm{Link\_output\_link}(o),\xi,t \ominus^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{f}} \cdot \eta_{o,\xi,t} & \text{if } \mathrm{cyc}^{f}_{o} \\ f_{\mathrm{Link\_output\_link}(o),\xi,t \boxminus_{0}^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{f}} \cdot \eta_{o,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_p_carried_over`

```yaml
Link_p_carried_over:
  description: >-
    the output a link carries over into a snapshot. At the first, it is the
    `p_init` it brought in where it came in running, and nothing where it
    came in off. After that, it is the previous snapshot's
  dims: [scenario, snapshot, link]
  cases:
    opening: { when: "position(snapshot) == 0", expression: Link_status_initial * Link_p_init }
  otherwise: shift(Link_p, along=snapshot, offset=1)
```

```math
\overleftarrow{f}^{\circ}_{l,\xi,t} = \begin{cases} \mathrm{u}^{f,0}_{l,\xi} \cdot \mathrm{f}^{0}_{l,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ f_{l,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_p_nom_committed`

```yaml
Link_p_nom_committed:
  description: >-
    the build a committed link's ramp rows are taken against: one module
    where the build is modular, since its status counts modules, and the
    given build otherwise (`constraints.py:1131-1134`)
  dims: [scenario, link]
  cases:
    modular_build: { when: "Link_p_nom_mod > 0", expression: Link_p_nom_mod }
  otherwise: Link_p_nom
```

```math
\widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} = \begin{cases} \mathrm{f}^{\mathrm{mod}}_{l} & \text{if } \mathrm{f}^{\mathrm{mod}}_{l} > 0 \\ \mathrm{f}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

### `Link_p_nom_effective`

```yaml
Link_p_nom_effective:
  description: "the build a link's limits are taken against: the chosen one where it is extendable, the given one otherwise"
  dims: [scenario, link]
  cases:
    extendable: { when: Link_p_nom_extendable, expression: Link_p_nom_ext }
  otherwise: Link_p_nom
```

```math
\widetilde{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} = \begin{cases} F_{l} & \text{if } \mathrm{ext}^{f}_{l} \\ \mathrm{f}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

### `Link_previous_p`

```yaml
Link_previous_p:
  description: >-
    the output a link carries into a snapshot. It is nothing at the first
    snapshot it is active in past the first of the horizon: PyPSA fills an
    output it did not build with zero (`constraints.py:716`). It is the
    output carried over otherwise
  dims: [scenario, snapshot, link]
  cases:
    opening_late: { when: "position(snapshot) > 0 AND NOT shift(Link_active, along=snapshot, offset=1)", expression: 0 }
  otherwise: Link_p_carried_over
```

```math
\overleftarrow{f}_{l,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{f}_{l,t - 1} \\ \overleftarrow{f}^{\circ}_{l,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_previous_status`

```yaml
Link_previous_status:
  description: >-
    the commitment state a link carries into a snapshot. It is off at the
    first snapshot it is active in past the first of the horizon. PyPSA reads a
    status it did not build as off there (`constraints.py:391`). It is the
    state carried over otherwise
  dims: [scenario, snapshot, link]
  cases:
    opening_late: { when: "position(snapshot) > 0 AND NOT shift(Link_active, along=snapshot, offset=1)", expression: 0 }
  otherwise: Link_status_carried_over
```

```math
\overleftarrow{u}^{f}_{l,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{f}_{l,t - 1} \\ \overleftarrow{u}^{\circ f}_{l,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_ramp_down_allowance`

```yaml
Link_ramp_down_allowance:
  description: >-
    how far a link may lower flow between two snapshots. It is its ramp
    limit of the build while it stays on, plus its shut-down ramp in the
    snapshot it turns off
  dims: [scenario, snapshot, link]
  cases:
    committed:
      when: Link_committable
      expression: >-
        Link_ramp_down_rate * Link_p_nom_committed * Link_status
        + Link_shut_down_rate * Link_p_nom_committed
        * (Link_ramp_previous_status - Link_status)
  otherwise: Link_ramp_down_rate * Link_p_nom_effective
```

```math
\Delta^{f,-}_{l,\xi,t} = \begin{cases} \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot u^{f}_{l,\xi,t} + \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \left( \overleftarrow{\bar u}^{f}_{l,\xi,t} - u^{f}_{l,\xi,t} \right) & \text{if } \mathrm{com}^{f}_{l} \\ \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot \widetilde{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_ramp_down_rate`

```yaml
Link_ramp_down_rate:
  description: >-
    the ramp limit in a link's down row, PyPSA's `ramp_limit_down`. It is
    the full build where PyPSA has none, since a shut-down ramp alone builds
    the row
  dims: [scenario, snapshot, link]
  cases:
    given: { when: Link_ramp_limit_down, expression: Link_ramp_limit_down }
  otherwise: 1
```

```math
\widetilde{\mathrm{rd}}^{f}_{l,\xi,t} = \begin{cases} \mathrm{rd}^{f}_{l,\xi,t} & \text{if } \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_ramp_previous_status`

```yaml
Link_ramp_previous_status:
  description: >-
    the status a committed link's ramp rows carry into a snapshot. At the
    first snapshot, a fixed modular link that came in running has every
    module on, since the state it brought in is on or off
    (`constraints.py:1152-1157`). The transition and down-time rows count it as one module
    (PyPSA/PyPSA#2114). It is the state carried in otherwise
  dims: [scenario, snapshot, link]
  cases:
    opening_modules:
      when: "position(snapshot) == 0 AND NOT Link_p_nom_extendable AND Link_p_nom_mod > 0"
      expression: Link_status_initial * Link_modules_installed
  otherwise: Link_previous_status
```

```math
\overleftarrow{\bar u}^{f}_{l,\xi,t} = \begin{cases} \mathrm{u}^{f,0}_{l,\xi} \cdot \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \\ \overleftarrow{u}^{f}_{l,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_ramp_up_allowance`

```yaml
Link_ramp_up_allowance:
  description: >-
    how far a link may raise flow between two snapshots. It is its ramp
    limit of the build while it stays on, plus its start-up ramp in the
    snapshot it turns on
  dims: [scenario, snapshot, link]
  cases:
    committed:
      when: Link_committable
      expression: >-
        Link_ramp_up_rate * Link_p_nom_committed * Link_ramp_previous_status
        + Link_start_up_rate * Link_p_nom_committed
        * (Link_status - Link_ramp_previous_status)
  otherwise: Link_ramp_up_rate * Link_p_nom_effective
```

```math
\Delta^{f,+}_{l,\xi,t} = \begin{cases} \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \overleftarrow{\bar u}^{f}_{l,\xi,t} + \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \left( u^{f}_{l,\xi,t} - \overleftarrow{\bar u}^{f}_{l,\xi,t} \right) & \text{if } \mathrm{com}^{f}_{l} \\ \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot \widetilde{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_ramp_up_rate`

```yaml
Link_ramp_up_rate:
  description: >-
    the ramp limit in a link's up row, PyPSA's `ramp_limit_up`. It is the
    full build where PyPSA has none, since a start-up ramp alone builds the
    row
  dims: [scenario, snapshot, link]
  cases:
    given: { when: Link_ramp_limit_up, expression: Link_ramp_limit_up }
  otherwise: 1
```

```math
\widetilde{\mathrm{ru}}^{f}_{l,\xi,t} = \begin{cases} \mathrm{ru}^{f}_{l,\xi,t} & \text{if } \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_shut_down_rate`

```yaml
Link_shut_down_rate:
  description: >-
    the shut-down ramp in a link's down row (PyPSA's
    `ramp_limit_shut_down`), or the full build where it has none
  dims: [scenario, link]
  cases:
    given: { when: Link_ramp_limit_shut_down, expression: Link_ramp_limit_shut_down }
  otherwise: 1
```

```math
\widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} = \begin{cases} \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} & \text{if } \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

### `Link_start_up_rate`

```yaml
Link_start_up_rate:
  description: >-
    the start-up ramp in a link's up row (PyPSA's `ramp_limit_start_up`), or
    the full build where it has none
  dims: [scenario, link]
  cases:
    given: { when: Link_ramp_limit_start_up, expression: Link_ramp_limit_start_up }
  otherwise: 1
```

```math
\widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} = \begin{cases} \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} & \text{if } \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

### `Link_status_carried_over`

```yaml
Link_status_carried_over:
  description: >-
    the state a link carries over into a snapshot: the state it brought into
    the horizon at the first, the previous snapshot's after that
  dims: [scenario, snapshot, link]
  cases:
    opening: { when: "position(snapshot) == 0", expression: Link_status_initial }
  otherwise: shift(Link_status, along=snapshot, offset=1)
```

```math
\overleftarrow{u}^{\circ f}_{l,\xi,t} = \begin{cases} \mathrm{u}^{f,0}_{l,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ u^{f}_{l,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Link_tech_capacity_expansion`

```yaml
Link_tech_capacity_expansion:
  expression: sum(Link_p_nom_ext * Link_tech_capacity_weight, over=link)
```

```math
\mathit{Link\_tech\_capacity\_expansion}_{o} = \sum_{l \in \mathcal{L}} F_{l} \cdot \mathrm{m}^{f}_{o,l} \qquad \forall\, o \in \mathcal{O}
```

### `Link_transmission_expansion_cost`

```yaml
Link_transmission_expansion_cost:
  expression: sum(Link_p_nom_ext * Link_expansion_cost_weight, over=link)
```

```math
\mathit{Link\_transmission\_expansion\_cost}_{o,\xi} = \sum_{l \in \mathcal{L}} F_{l} \cdot \mathrm{cc}^{f}_{o,l,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Link_transmission_volume_expansion`

```yaml
Link_transmission_volume_expansion:
  expression: sum(Link_p_nom_ext * Link_volume_weight, over=link)
```

```math
\mathit{Link\_transmission\_volume\_expansion}_{o,\xi} = \sum_{l \in \mathcal{L}} F_{l} \cdot \mathrm{len}^{f}_{o,l,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Load_demand`

```yaml
Load_demand:
  description: >-
    what a load draws from its bus's balance. It is its demand times its
    sign where it is active, and nothing where it is not. PyPSA drops an
    inactive load from the balance (`constraints.py:1591-1592`)
  dims: [scenario, snapshot, load]
  cases:
    active: { when: Load_active, expression: Load_sign * Load_p_set }
  otherwise: 0
```

```math
\check{\mathrm{load}}_{d,\xi,t} = \begin{cases} \mathrm{sgn}^{\mathrm{load}}_{d} \cdot \mathrm{load}_{d,\xi,t} & \text{if } \mathrm{on}^{\mathrm{load}}_{d} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, d \in \mathcal{D},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Load_injection`

```yaml
Load_injection: sum(Load_demand, over=load, by=Load_bus[bus])
```

```math
\mathrm{Load\_injection}_{n,\xi,t} = \sum_{d \in \mathcal{D} \,:\, \mathrm{Load\_bus}(d) = n} \check{\mathrm{load}}_{d,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Outage_s`

```yaml
Outage_s:
  description: >-
    the flow an outage takes off its branch: the outaged line's or
    transformer's flow before it goes out
  dims: [scenario, snapshot, outage]
  cases:
    line: { when: Outage_line, expression: "at(Line_s_monitored, by=Outage_line[line])" }
  otherwise: at(Transformer_s_monitored, by=Outage_transformer[transformer])
```

```math
\hat{s}_{\kappa,\xi,t} = \begin{cases} \check{s}_{\mathrm{Outage\_line}(\kappa),\xi,t} & \text{if } \mathrm{Outage\_line}(\kappa) \text{ is defined} \\ \check{\sigma}_{\xi,t,\mathrm{Outage\_transformer}(\kappa)} & \text{otherwise} \end{cases} \qquad \forall\, \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_additions`

```yaml
Process_additions:
  expression: >-
    sum(Process_p_nom_ext * Process_first_active, over=process, by=Process_carrier[carrier])
```

```math
\mathit{Process\_additions}_{i,y} = \sum_{j \in \mathcal{J} \,:\, \mathrm{Process\_carrier}(j) = i} Z_{j} \cdot \mathrm{new}^{z}_{y,j} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

### `Process_capex`

```yaml
Process_capex:
  expression: sum(scenario_weight * Process_p_nom_ext * Process_capital_cost * Process_capital_weight)
```

```math
\mathit{Process\_capex} = \sum_{j \in \mathcal{J},\ \xi \in \Xi} \pi_{\xi} \cdot Z_{j} \cdot \mathrm{c}^{\mathrm{cap},z}_{j,\xi} \cdot \mathrm{W}^{z}_{j}
```

### `Process_commitment_opex`

```yaml
Process_commitment_opex:
  expression: >-
    sum(sum(((Process_status * Process_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
    + sum(sum((Process_start_up * Process_start_up_cost) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
    + sum(sum((Process_shut_down * Process_shut_down_cost) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
```

```math
\mathit{Process\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} u^{z}_{j,\xi,t} \cdot \mathrm{c}^{z,\mathrm{on}}_{j,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} \mathit{up}^{z}_{j,\xi,t} \cdot \mathrm{c}^{z,\mathrm{up}}_{j,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} \mathit{dn}^{z}_{j,\xi,t} \cdot \mathrm{c}^{z,\mathrm{dn}}_{j,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `Process_injection`

```yaml
Process_injection:
  expression: >-
    sum(Process_output_arrival, over=process_output, by=Process_output_bus[bus])
```

```math
\mathit{Process\_injection}_{n,\xi,t} = \sum_{r \in \mathcal{R} \,:\, \mathrm{Process\_output\_bus}(r) = n} \overrightarrow{z}_{r,\xi,t} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_maintenance_modules`

```yaml
Process_maintenance_modules:
  description: >-
    how many modules of a modular committable process can be on in
    maintenance: its build cap in modules where the build is extendable,
    and the modules installed where it is fixed (`constraints.py:588-594`)
  dims: [scenario, process]
  cases:
    extendable: { when: Process_p_nom_extendable, expression: Process_p_nom_max / Process_p_nom_mod }
  otherwise: Process_modules_installed
```

```math
\mathrm{Process\_maintenance\_modules}_{j,\xi} = \begin{cases} \frac{\overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi}}{\mathrm{z}^{\mathrm{mod}}_{j}} & \text{if } \mathrm{ext}^{z}_{j} \\ \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

### `Process_modules`

```yaml
Process_modules:
  description: >-
    how many modules a committed process's status counts: the chosen number
    where the build is extendable and modular, and the modules installed
    otherwise (`constraints.py:656-661`)
  dims: [scenario, process]
  cases:
    chosen: { when: Process_p_nom_extendable AND Process_p_nom_mod > 0, expression: Process_n_mod }
  otherwise: Process_modules_installed
```

```math
\mathrm{M}^{z}_{j,\xi} = \begin{cases} N^{z}_{j} & \text{if } \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \\ \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

### `Process_opex`

```yaml
Process_opex:
  expression: >-
    sum(sum(((Process_p * Process_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
    + sum(sum((((Process_p * Process_p) * Process_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
```

```math
\mathit{Process\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} z_{j,\xi,t} \cdot \mathrm{c}^{z}_{j,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} z_{j,\xi,t} \cdot z_{j,\xi,t} \cdot \mathrm{c}^{z,(2)}_{j,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `Process_output_arrival`

```yaml
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
      expression: shift(at(Process_p, by=Process_output_process[process]), along=snapshot, offset=Process_output_delay, edge='wrap', within=snapshot_period[period]) * Process_rate
  otherwise: shift(at(Process_p, by=Process_output_process[process]), along=snapshot, offset=Process_output_delay, edge=0, within=snapshot_period[period]) * Process_rate
```

```math
\overrightarrow{z}_{r,\xi,t} = \begin{cases} z_{\mathrm{Process\_output\_process}(r),\xi,t \ominus^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{z}} \cdot \alpha_{r,\xi,t} & \text{if } \mathrm{cyc}^{z}_{r} \\ z_{\mathrm{Process\_output\_process}(r),\xi,t \boxminus_{0}^{\mathrm{snapshot\_period}(t)} \mathrm{d}^{z}} \cdot \alpha_{r,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, r \in \mathcal{R},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_p_carried_over`

```yaml
Process_p_carried_over:
  description: >-
    the output a process carries over into a snapshot. At the first, it is
    the `p_init` it brought in where it came in running, and nothing where
    it came in off. After that, it is the previous snapshot's
  dims: [scenario, snapshot, process]
  cases:
    opening: { when: "position(snapshot) == 0", expression: Process_status_initial * Process_p_init }
  otherwise: shift(Process_p, along=snapshot, offset=1)
```

```math
\overleftarrow{z}^{\circ}_{j,\xi,t} = \begin{cases} \mathrm{u}^{z,0}_{j,\xi} \cdot \mathrm{z}^{0}_{j,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ z_{j,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_p_nom_committed`

```yaml
Process_p_nom_committed:
  description: >-
    the build a committed process's ramp rows are taken against: one module
    where the build is modular, since its status counts modules, and the
    given build otherwise (`constraints.py:1131-1134`)
  dims: [scenario, process]
  cases:
    modular_build: { when: "Process_p_nom_mod > 0", expression: Process_p_nom_mod }
  otherwise: Process_p_nom
```

```math
\widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} = \begin{cases} \mathrm{z}^{\mathrm{mod}}_{j} & \text{if } \mathrm{z}^{\mathrm{mod}}_{j} > 0 \\ \mathrm{z}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

### `Process_p_nom_effective`

```yaml
Process_p_nom_effective:
  description: "the build a process's limits are taken against: the chosen one where it is extendable, the given one otherwise"
  dims: [scenario, process]
  cases:
    extendable: { when: Process_p_nom_extendable, expression: Process_p_nom_ext }
  otherwise: Process_p_nom
```

```math
\widetilde{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} = \begin{cases} Z_{j} & \text{if } \mathrm{ext}^{z}_{j} \\ \mathrm{z}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

### `Process_previous_p`

```yaml
Process_previous_p:
  description: >-
    the output a process carries into a snapshot. It is nothing at the first
    snapshot it is active in past the first of the horizon: PyPSA fills an
    output it did not build with zero (`constraints.py:716`). It is the
    output carried over otherwise
  dims: [scenario, snapshot, process]
  cases:
    opening_late: { when: "position(snapshot) > 0 AND NOT shift(Process_active, along=snapshot, offset=1)", expression: 0 }
  otherwise: Process_p_carried_over
```

```math
\overleftarrow{z}_{j,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{z}_{j,t - 1} \\ \overleftarrow{z}^{\circ}_{j,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_previous_status`

```yaml
Process_previous_status:
  description: >-
    the commitment state a process carries into a snapshot. It is off at the
    first snapshot it is active in past the first of the horizon. PyPSA reads a
    status it did not build as off there (`constraints.py:391`). It is the
    state carried over otherwise
  dims: [scenario, snapshot, process]
  cases:
    opening_late: { when: "position(snapshot) > 0 AND NOT shift(Process_active, along=snapshot, offset=1)", expression: 0 }
  otherwise: Process_status_carried_over
```

```math
\overleftarrow{u}^{z}_{j,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{z}_{j,t - 1} \\ \overleftarrow{u}^{\circ z}_{j,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_ramp_down_allowance`

```yaml
Process_ramp_down_allowance:
  description: >-
    how far a process may lower internal power between two snapshots. It is
    its ramp limit of the build while it stays on, plus its shut-down ramp
    in the snapshot it turns off
  dims: [scenario, snapshot, process]
  cases:
    committed:
      when: Process_committable
      expression: >-
        Process_ramp_down_rate * Process_p_nom_committed * Process_status
        + Process_shut_down_rate * Process_p_nom_committed
        * (Process_ramp_previous_status - Process_status)
  otherwise: Process_ramp_down_rate * Process_p_nom_effective
```

```math
\Delta^{z,-}_{j,\xi,t} = \begin{cases} \widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot u^{z}_{j,\xi,t} + \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \left( \overleftarrow{\bar u}^{z}_{j,\xi,t} - u^{z}_{j,\xi,t} \right) & \text{if } \mathrm{com}^{z}_{j} \\ \widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot \widetilde{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_ramp_down_rate`

```yaml
Process_ramp_down_rate:
  description: >-
    the ramp limit in a process's down row, PyPSA's `ramp_limit_down`. It is
    the full build where PyPSA has none, since a shut-down ramp alone builds
    the row
  dims: [scenario, snapshot, process]
  cases:
    given: { when: Process_ramp_limit_down, expression: Process_ramp_limit_down }
  otherwise: 1
```

```math
\widetilde{\mathrm{rd}}^{z}_{j,\xi,t} = \begin{cases} \mathrm{rd}^{z}_{j,\xi,t} & \text{if } \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_ramp_previous_status`

```yaml
Process_ramp_previous_status:
  description: >-
    the status a committed process's ramp rows carry into a snapshot. At the
    first snapshot, a fixed modular process that came in running has every
    module on, since the state it brought in is on or off
    (`constraints.py:1152-1157`). The transition and down-time rows count it as one module
    (PyPSA/PyPSA#2114). It is the state carried in otherwise
  dims: [scenario, snapshot, process]
  cases:
    opening_modules:
      when: "position(snapshot) == 0 AND NOT Process_p_nom_extendable AND Process_p_nom_mod > 0"
      expression: Process_status_initial * Process_modules_installed
  otherwise: Process_previous_status
```

```math
\overleftarrow{\bar u}^{z}_{j,\xi,t} = \begin{cases} \mathrm{u}^{z,0}_{j,\xi} \cdot \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \\ \overleftarrow{u}^{z}_{j,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_ramp_up_allowance`

```yaml
Process_ramp_up_allowance:
  description: >-
    how far a process may raise internal power between two snapshots. It is
    its ramp limit of the build while it stays on, plus its start-up ramp in
    the snapshot it turns on
  dims: [scenario, snapshot, process]
  cases:
    committed:
      when: Process_committable
      expression: >-
        Process_ramp_up_rate * Process_p_nom_committed * Process_ramp_previous_status
        + Process_start_up_rate * Process_p_nom_committed
        * (Process_status - Process_ramp_previous_status)
  otherwise: Process_ramp_up_rate * Process_p_nom_effective
```

```math
\Delta^{z,+}_{j,\xi,t} = \begin{cases} \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \overleftarrow{\bar u}^{z}_{j,\xi,t} + \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \left( u^{z}_{j,\xi,t} - \overleftarrow{\bar u}^{z}_{j,\xi,t} \right) & \text{if } \mathrm{com}^{z}_{j} \\ \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot \widetilde{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_ramp_up_rate`

```yaml
Process_ramp_up_rate:
  description: >-
    the ramp limit in a process's up row, PyPSA's `ramp_limit_up`. It is the
    full build where PyPSA has none, since a start-up ramp alone builds the
    row
  dims: [scenario, snapshot, process]
  cases:
    given: { when: Process_ramp_limit_up, expression: Process_ramp_limit_up }
  otherwise: 1
```

```math
\widetilde{\mathrm{ru}}^{z}_{j,\xi,t} = \begin{cases} \mathrm{ru}^{z}_{j,\xi,t} & \text{if } \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_shut_down_rate`

```yaml
Process_shut_down_rate:
  description: >-
    the shut-down ramp in a process's down row (PyPSA's
    `ramp_limit_shut_down`), or the full build where it has none
  dims: [scenario, process]
  cases:
    given: { when: Process_ramp_limit_shut_down, expression: Process_ramp_limit_shut_down }
  otherwise: 1
```

```math
\widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} = \begin{cases} \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} & \text{if } \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

### `Process_start_up_rate`

```yaml
Process_start_up_rate:
  description: >-
    the start-up ramp in a process's up row (PyPSA's `ramp_limit_start_up`),
    or the full build where it has none
  dims: [scenario, process]
  cases:
    given: { when: Process_ramp_limit_start_up, expression: Process_ramp_limit_start_up }
  otherwise: 1
```

```math
\widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} = \begin{cases} \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} & \text{if } \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

### `Process_status_carried_over`

```yaml
Process_status_carried_over:
  description: >-
    the state a process carries over into a snapshot: the state it brought
    into the horizon at the first, the previous snapshot's after that
  dims: [scenario, snapshot, process]
  cases:
    opening: { when: "position(snapshot) == 0", expression: Process_status_initial }
  otherwise: shift(Process_status, along=snapshot, offset=1)
```

```math
\overleftarrow{u}^{\circ z}_{j,\xi,t} = \begin{cases} \mathrm{u}^{z,0}_{j,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ u^{z}_{j,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Process_tech_capacity_expansion`

```yaml
Process_tech_capacity_expansion:
  expression: sum(Process_p_nom_ext * Process_tech_capacity_weight, over=process)
```

```math
\mathit{Process\_tech\_capacity\_expansion}_{o} = \sum_{j \in \mathcal{J}} Z_{j} \cdot \mathrm{m}^{z}_{o,j} \qquad \forall\, o \in \mathcal{O}
```

### `StorageUnit_additions`

```yaml
StorageUnit_additions:
  expression: >-
    sum(StorageUnit_p_nom_ext * StorageUnit_first_active, over=storage_unit, by=StorageUnit_carrier[carrier])
```

```math
\mathit{StorageUnit\_additions}_{i,y} = \sum_{s \in \mathcal{S} \,:\, \mathrm{StorageUnit\_carrier}(s) = i} H_{s} \cdot \mathrm{new}^{h}_{y,s} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

### `StorageUnit_capex`

```yaml
StorageUnit_capex:
  expression: sum(scenario_weight * StorageUnit_p_nom_ext * StorageUnit_capital_cost * StorageUnit_capital_weight)
```

```math
\mathit{StorageUnit\_capex} = \sum_{\xi \in \Xi,\ s \in \mathcal{S}} \pi_{\xi} \cdot H_{s} \cdot \mathrm{c}^{\mathrm{cap},h}_{\xi,s} \cdot \mathrm{W}^{h}_{s}
```

### `StorageUnit_charge_carried_in`

```yaml
StorageUnit_charge_carried_in:
  description: >-
    the charge a unit opens a snapshot with. At the first snapshot it is active
    in, it is its last such snapshot's less standing loss where it is
    cyclic. Where it is not, it is the given initial charge, which no
    standing loss has touched yet. Otherwise it is the previous snapshot's
    less standing loss. A unit built in a later period opens in that period,
    and a cyclic one that retires closes on its own last snapshot. Per
    period, the same holds with each investment period as the horizon
  dims: [scenario, snapshot, storage_unit]
  cases:
    cyclic:
      when: >-
        StorageUnit_cyclic_state_of_charge AND NOT StorageUnit_cyclic_state_of_charge_per_period
        AND NOT StorageUnit_state_of_charge_initial_per_period
        AND (position(snapshot) == 0 OR StorageUnit_opens_late)
      expression: >-
        StorageUnit_retention
        * shift(shift(StorageUnit_state_of_charge, along=snapshot, offset=1, edge='wrap'), along=snapshot, offset=StorageUnit_inactive_snapshots, edge='wrap')
    opening:
      when: >-
        NOT StorageUnit_cyclic_state_of_charge AND NOT StorageUnit_cyclic_state_of_charge_per_period
        AND NOT StorageUnit_state_of_charge_initial_per_period
        AND (position(snapshot) == 0 OR StorageUnit_opens_late)
      expression: StorageUnit_state_of_charge_initial
    period_cyclic:
      when: StorageUnit_cyclic_state_of_charge_per_period
      expression: >-
        StorageUnit_retention
        * shift(StorageUnit_state_of_charge, along=snapshot, offset=1, edge='wrap', within=snapshot_period[period])
    period_opening:
      when: >-
        StorageUnit_state_of_charge_initial_per_period AND NOT StorageUnit_cyclic_state_of_charge_per_period
        AND position(snapshot, within=snapshot_period[period]) == 0
      expression: StorageUnit_state_of_charge_initial
  otherwise: StorageUnit_retention * shift(StorageUnit_state_of_charge, along=snapshot, offset=1)
```

```math
\overleftarrow{\mathit{soc}}_{\xi,t,s} = \begin{cases} \rho_{\xi,t,s} \cdot \mathit{soc}_{\xi,\left( t \ominus \mathrm{idle} \right) \ominus 1,s} & \text{if } \mathrm{cyc}_{\xi,s} \wedge \neg \mathrm{cyc}^{y}_{\xi,s} \wedge \neg \mathrm{reset}_{\xi,s} \wedge \left( \mathrm{pos}(t) = 0 \vee \mathrm{open}_{t,s} \right) \\ \mathrm{soc}^{0}_{\xi,s} & \text{if } \neg \mathrm{cyc}_{\xi,s} \wedge \neg \mathrm{cyc}^{y}_{\xi,s} \wedge \neg \mathrm{reset}_{\xi,s} \wedge \left( \mathrm{pos}(t) = 0 \vee \mathrm{open}_{t,s} \right) \\ \rho_{\xi,t,s} \cdot \mathit{soc}_{\xi,t \ominus^{\mathrm{snapshot\_period}(t)} 1,s} & \text{if } \mathrm{cyc}^{y}_{\xi,s} \\ \mathrm{soc}^{0}_{\xi,s} & \text{if } \mathrm{reset}_{\xi,s} \wedge \neg \mathrm{cyc}^{y}_{\xi,s} \wedge \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) = 0 \\ \rho_{\xi,t,s} \cdot \mathit{soc}_{\xi,t - 1,s} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S}
```

### `StorageUnit_closing_weight`

```yaml
StorageUnit_closing_weight:
  description: >-
    what the charge a unit holds at a snapshot counts for in a row as its
    closing level. Where the unit reopens per period, it is the years of the
    period at the last snapshot of each counted period. Where it does not,
    it is one at the last counted snapshot it is active in. It is nothing
    elsewhere
  dims: [scenario, global_constraint, snapshot, storage_unit]
  cases:
    per_period:
      when: StorageUnit_state_of_charge_initial_per_period AND GlobalConstraint_counts_snapshot AND position(snapshot, within=snapshot_period[period]) == -1
      expression: at(period_weight_years, by=snapshot_period[period])
    carried_over:
      when: NOT StorageUnit_state_of_charge_initial_per_period
      expression: StorageUnit_last_counted_active
  otherwise: 0
```

```math
\mathit{w}^{h}_{o,\xi,t,s} = \begin{cases} \mathit{last}^{h}_{o,\xi,t,s} & \text{if } \neg \mathrm{reset}_{\xi,s} \\ \mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} & \text{if } \mathrm{reset}_{\xi,s} \wedge \mathrm{in}_{o,\xi,t} \wedge \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) = \lvert \mathcal{T}_{\mathrm{snapshot\_period}(t)} \rvert - 1 \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S}
```

### `StorageUnit_injection`

```yaml
StorageUnit_injection:
  expression: >-
    sum(StorageUnit_sign * (StorageUnit_p_dispatch - StorageUnit_p_store), over=storage_unit, by=StorageUnit_bus[bus])
```

```math
\mathit{StorageUnit\_injection}_{n,\xi,t} = \sum_{s \in \mathcal{S} \,:\, \mathrm{StorageUnit\_bus}(s) = n} \mathrm{sgn}^{h}_{s} \cdot \left( h^{+}_{\xi,t,s} - h^{-}_{\xi,t,s} \right) \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `StorageUnit_last_counted_active`

```yaml
StorageUnit_last_counted_active:
  description: >-
    one at the last snapshot a row counts where a unit is active, and zero
    elsewhere. A unit that retires before the last counted snapshot closes
    on its last active level. PyPSA forward-fills the level over the counted
    snapshots (`global_constraints.py:476-479`)
  dims: [scenario, global_constraint, snapshot, storage_unit]
  cases:
    last:
      when: >-
        GlobalConstraint_counts_snapshot AND StorageUnit_active
        AND NOT shift(GlobalConstraint_counts_snapshot AND StorageUnit_active, along=snapshot, offset=-1)
      expression: 1
  otherwise: 0
```

```math
\mathit{last}^{h}_{o,\xi,t,s} = \begin{cases} 1 & \text{if } \mathrm{in}_{o,\xi,t} \wedge \mathrm{on}^{h}_{t,s} \wedge \neg \left( \mathrm{in}_{o,\xi,t + 1} \wedge \mathrm{on}^{h}_{t + 1,s} \right) \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S}
```

### `StorageUnit_operational_limit`

```yaml
StorageUnit_operational_limit:
  expression: >-
    -sum(sum((StorageUnit_state_of_charge * StorageUnit_closing_weight) * StorageUnit_operational_limit_weight, over=snapshot), over=storage_unit)
```

```math
\mathit{StorageUnit\_operational\_limit}_{o,\xi} = -\left( \sum_{s \in \mathcal{S}} \sum_{t \in \mathcal{T}} \mathit{soc}_{\xi,t,s} \cdot \mathit{w}^{h}_{o,\xi,t,s} \cdot \mathrm{b}^{h}_{o,\xi,s} \right) \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `StorageUnit_opex`

```yaml
StorageUnit_opex:
  expression: >-
    sum(sum(((StorageUnit_p_dispatch * StorageUnit_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=storage_unit), over=snapshot)
    + sum(sum((((StorageUnit_p_dispatch * StorageUnit_p_dispatch) * StorageUnit_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=storage_unit), over=snapshot)
    + sum(sum(((StorageUnit_state_of_charge * StorageUnit_marginal_cost_storage) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=storage_unit), over=snapshot)
    + sum(sum(((StorageUnit_spill * StorageUnit_spill_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=storage_unit), over=snapshot)
```

```math
\mathit{StorageUnit\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{s \in \mathcal{S}} h^{+}_{\xi,t,s} \cdot \mathrm{c}^{h}_{\xi,t,s} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{s \in \mathcal{S}} h^{+}_{\xi,t,s} \cdot h^{+}_{\xi,t,s} \cdot \mathrm{c}^{h,(2)}_{\xi,t,s} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{s \in \mathcal{S}} \mathit{soc}_{\xi,t,s} \cdot \mathrm{c}^{\mathrm{soc}}_{\xi,t,s} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{s \in \mathcal{S}} \mathit{spill}_{\xi,t,s} \cdot \mathrm{c}^{\mathrm{spill}}_{\xi,t,s} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `StorageUnit_primary_energy`

```yaml
StorageUnit_primary_energy:
  expression: >-
    -sum(sum((StorageUnit_state_of_charge * StorageUnit_closing_weight) * StorageUnit_primary_energy_weight, over=snapshot), over=storage_unit)
```

```math
\mathit{StorageUnit\_primary\_energy}_{o,\xi} = -\left( \sum_{s \in \mathcal{S}} \sum_{t \in \mathcal{T}} \mathit{soc}_{\xi,t,s} \cdot \mathit{w}^{h}_{o,\xi,t,s} \cdot \mathrm{a}^{h}_{o,\xi,s} \right) \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `StorageUnit_tech_capacity_expansion`

```yaml
StorageUnit_tech_capacity_expansion:
  expression: sum(StorageUnit_p_nom_ext * StorageUnit_tech_capacity_weight, over=storage_unit)
```

```math
\mathit{StorageUnit\_tech\_capacity\_expansion}_{o} = \sum_{s \in \mathcal{S}} H_{s} \cdot \mathrm{m}^{h}_{o,s} \qquad \forall\, o \in \mathcal{O}
```

### `Store_additions`

```yaml
Store_additions:
  expression: >-
    sum(Store_e_nom_ext * Store_first_active, over=store, by=Store_carrier[carrier])
```

```math
\mathit{Store\_additions}_{i,y} = \sum_{v \in \mathcal{V} \,:\, \mathrm{Store\_carrier}(v) = i} E_{v} \cdot \mathrm{new}^{e}_{y,v} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y}
```

### `Store_capex`

```yaml
Store_capex:
  expression: sum(scenario_weight * Store_e_nom_ext * Store_capital_cost * Store_capital_weight)
```

```math
\mathit{Store\_capex} = \sum_{\xi \in \Xi,\ v \in \mathcal{V}} \pi_{\xi} \cdot E_{v} \cdot \mathrm{c}^{\mathrm{cap},e}_{\xi,v} \cdot \mathrm{W}^{e}_{v}
```

### `Store_charge_cap_pu`

```yaml
Store_charge_cap_pu:
  description: >-
    the most charging through `p_store`, per unit of `e_nom`. It is
    `-p_min_pu / max_hours` for a store that splits its dispatch, and zero
    otherwise (`stores.py:79-86`)
  dims: [scenario, snapshot, store]
  cases:
    split: { when: Store_split_dispatch, expression: -Store_p_min_pu / Store_max_hours }
  otherwise: 0
```

```math
\overline{\mathrm{q}}^{-}_{\xi,t,v} = \begin{cases} \frac{-\underline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} & \text{if } \mathrm{split}^{e}_{\xi,v} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

### `Store_closing_weight`

```yaml
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
```

```math
\mathit{w}^{e}_{o,\xi,t,v} = \begin{cases} \mathit{last}^{e}_{o,\xi,t,v} & \text{if } \neg \mathrm{reset}^{e}_{\xi,v} \\ \mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} & \text{if } \mathrm{reset}^{e}_{\xi,v} \wedge \mathrm{in}_{o,\xi,t} \wedge \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) = \lvert \mathcal{T}_{\mathrm{snapshot\_period}(t)} \rvert - 1 \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

### `Store_discharge_floor_pu`

```yaml
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
```

```math
\underline{\mathrm{q}}^{+}_{\xi,t,v} = \begin{cases} 0 & \text{if } \mathrm{split}^{e}_{\xi,v} \\ \frac{\underline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

### `Store_e_nom_effective`

```yaml
Store_e_nom_effective:
  description: "the build a store's limits are taken against: the chosen one where it is extendable, the given one otherwise"
  dims: [scenario, store]
  cases:
    extendable: { when: Store_e_nom_extendable, expression: Store_e_nom_ext }
  otherwise: Store_e_nom
```

```math
\widetilde{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} = \begin{cases} E_{v} & \text{if } \mathrm{ext}^{e}_{v} \\ \mathrm{e}^{\mathrm{nom}}_{\xi,v} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V}
```

### `Store_energy_carried_in`

```yaml
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
```

```math
\overleftarrow{e}_{\xi,t,v} = \begin{cases} \rho^{e}_{\xi,t,v} \cdot e_{\xi,\left( t \ominus \mathrm{idle}^{e} \right) \ominus 1,v} & \text{if } \mathrm{cyc}^{e}_{\xi,v} \wedge \neg \mathrm{cyc}^{e,y}_{\xi,v} \wedge \neg \mathrm{reset}^{e}_{\xi,v} \wedge \left( \mathrm{pos}(t) = 0 \vee \mathrm{open}^{e}_{t,v} \right) \\ \mathrm{e}^{0}_{\xi,v} & \text{if } \neg \mathrm{cyc}^{e}_{\xi,v} \wedge \neg \mathrm{cyc}^{e,y}_{\xi,v} \wedge \neg \mathrm{reset}^{e}_{\xi,v} \wedge \left( \mathrm{pos}(t) = 0 \vee \mathrm{open}^{e}_{t,v} \right) \\ \rho^{e}_{\xi,t,v} \cdot e_{\xi,t \ominus^{\mathrm{snapshot\_period}(t)} 1,v} & \text{if } \mathrm{cyc}^{e,y}_{\xi,v} \\ \mathrm{e}^{0}_{\xi,v} & \text{if } \mathrm{reset}^{e}_{\xi,v} \wedge \neg \mathrm{cyc}^{e,y}_{\xi,v} \wedge \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) = 0 \\ \rho^{e}_{\xi,t,v} \cdot e_{\xi,t - 1,v} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

### `Store_injection`

```yaml
Store_injection: sum(Store_sign * Store_p, over=store, by=Store_bus[bus])
```

```math
\mathit{Store\_injection}_{n,\xi,t} = \sum_{v \in \mathcal{V} \,:\, \mathrm{Store\_bus}(v) = n} \mathrm{sgn}^{q}_{v} \cdot q_{\xi,t,v} \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Store_last_counted_active`

```yaml
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
```

```math
\mathit{last}^{e}_{o,\xi,t,v} = \begin{cases} 1 & \text{if } \mathrm{in}_{o,\xi,t} \wedge \mathrm{on}^{e}_{t,v} \wedge \neg \left( \mathrm{in}_{o,\xi,t + 1} \wedge \mathrm{on}^{e}_{t + 1,v} \right) \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V}
```

### `Store_operational_limit`

```yaml
Store_operational_limit:
  expression: >-
    -sum(sum((Store_e * Store_closing_weight) * Store_operational_limit_weight, over=snapshot), over=store)
```

```math
\mathit{Store\_operational\_limit}_{o,\xi} = -\left( \sum_{v \in \mathcal{V}} \sum_{t \in \mathcal{T}} e_{\xi,t,v} \cdot \mathit{w}^{e}_{o,\xi,t,v} \cdot \mathrm{b}^{e}_{o,\xi,v} \right) \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Store_opex`

```yaml
Store_opex:
  expression: >-
    sum(sum(((Store_p * Store_marginal_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
    + sum(sum((((Store_p * Store_p) * Store_marginal_cost_quadratic) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
    + sum(sum(((Store_e * Store_marginal_cost_storage) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
    + sum(sum((((Store_p + Store_p_store) * Store_marginal_cost_dispatch) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
    + sum(sum(((Store_p_store * Store_marginal_cost_store) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
    + sum(sum(((Store_spill * Store_spill_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=store), over=snapshot)
```

```math
\mathit{Store\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} q_{\xi,t,v} \cdot \mathrm{c}^{q}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} q_{\xi,t,v} \cdot q_{\xi,t,v} \cdot \mathrm{c}^{q,(2)}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} e_{\xi,t,v} \cdot \mathrm{c}^{e}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} \left( q_{\xi,t,v} + q^{-}_{\xi,t,v} \right) \cdot \mathrm{c}^{q,+}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} q^{-}_{\xi,t,v} \cdot \mathrm{c}^{q,-}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{v \in \mathcal{V}} \mathit{spill}^{e}_{\xi,t,v} \cdot \mathrm{c}^{\mathrm{spill},e}_{\xi,t,v} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

### `Store_primary_energy`

```yaml
Store_primary_energy:
  expression: >-
    -sum(sum((Store_e * Store_closing_weight) * Store_primary_energy_weight, over=snapshot), over=store)
```

```math
\mathit{Store\_primary\_energy}_{o,\xi} = -\left( \sum_{v \in \mathcal{V}} \sum_{t \in \mathcal{T}} e_{\xi,t,v} \cdot \mathit{w}^{e}_{o,\xi,t,v} \cdot \mathrm{a}^{e}_{o,\xi,v} \right) \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `Store_tech_capacity_expansion`

```yaml
Store_tech_capacity_expansion:
  expression: sum(Store_e_nom_ext * Store_tech_capacity_weight, over=store)
```

```math
\mathit{Store\_tech\_capacity\_expansion}_{o} = \sum_{v \in \mathcal{V}} E_{v} \cdot \mathrm{m}^{e}_{o,v} \qquad \forall\, o \in \mathcal{O}
```

### `Transformer_angle_sum`

```yaml
Transformer_angle_sum:
  expression: >-
    sum(Transformer_s * at(Transformer_cycle_weight, by=snapshot_period[period]), over=transformer)
    + sum(Transformer_phase_shift_weight, over=transformer)
    + sum(Transformer_phase_shift * at(Transformer_phase_shift_cycle_weight, by=snapshot_period[period]), over=transformer)
```

```math
\mathit{Transformer\_angle\_sum}_{c,\xi,t} = \sum_{m \in \mathcal{M}} \sigma_{\xi,t,m} \cdot \mathrm{x}^{\sigma}_{c,\mathrm{snapshot\_period}(t),m} + \sum_{m \in \mathcal{M}} \vartheta_{c,t,m} + \sum_{m \in \mathcal{M}} \mathit{Transformer\_phase\_shift}_{\xi,t,m} \cdot \mathrm{Transformer\_phase\_shift\_cycle\_weight}_{c,\mathrm{snapshot\_period}(t),m} \qquad \forall\, c \in \mathcal{C},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Transformer_capex`

```yaml
Transformer_capex:
  expression: sum(scenario_weight * Transformer_s_nom_ext * Transformer_capital_cost * Transformer_capital_weight)
```

```math
\mathit{Transformer\_capex} = \sum_{\xi \in \Xi,\ m \in \mathcal{M}} \pi_{\xi} \cdot \Sigma_{m} \cdot \mathrm{c}^{\mathrm{cap},\sigma}_{\xi,m} \cdot \mathrm{W}^{\sigma}_{m}
```

### `Transformer_injection`

```yaml
Transformer_injection:
  expression: >-
    -sum(Transformer_s, over=transformer, by=Transformer_bus0[bus])
    + sum(Transformer_s, over=transformer, by=Transformer_bus1[bus])
    - (0.5 * sum(Transformer_loss, over=transformer, by=Transformer_bus0[bus]))
    - (0.5 * sum(Transformer_loss, over=transformer, by=Transformer_bus1[bus]))
```

```math
\mathit{Transformer\_injection}_{n,\xi,t} = -\left( \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus0}(m) = n} \sigma_{\xi,t,m} \right) + \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus1}(m) = n} \sigma_{\xi,t,m} - 0.5 \cdot \left( \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus0}(m) = n} \ell^{\sigma}_{\xi,t,m} \right) - 0.5 \cdot \left( \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus1}(m) = n} \ell^{\sigma}_{\xi,t,m} \right) \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Transformer_s_monitored`

```yaml
Transformer_s_monitored:
  description: the flow a transformer's post-contingency rows read, as a line's
  dims: [scenario, snapshot, transformer]
  cases:
    standing: { when: Transformer_active, expression: Transformer_s }
  otherwise: 0
```

```math
\check{\sigma}_{\xi,t,m} = \begin{cases} \sigma_{\xi,t,m} & \text{if } \mathrm{on}^{\sigma}_{t,m} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M}
```

### `energy_limit_weight`

```yaml
energy_limit_weight:
  description: >-
    what one unit of power at a snapshot counts for in an `e_sum` row: the
    generator weighting times the years of the snapshot's period, as in an
    `operational_limit` row (`constraints.py:2935-2937`)
  dims: [snapshot]
  expression: snapshot_weightings_generators * at(period_weight_years, by=snapshot_period[period])
```

```math
\mathit{w}^{E}_{t} = \mathrm{w}^{\mathrm{gen}}_{t} \cdot \mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, t \in \mathcal{T}
```

### `operational_limit`

```yaml
operational_limit:
  dims: [scenario, global_constraint]
  expression: >-
    Generator_operational_limit
    + StorageUnit_operational_limit
    + Store_operational_limit
  description: >-
    what an `operational_limit` row totals: the weighted energy its
    generators deliver over the snapshots it counts, plus what its
    non-cyclic storage draws down. The initial charge it draws from is
    folded into the row's constant
```

```math
\mathit{operational\_limit}_{o,\xi} = \mathit{Generator\_operational\_limit}_{o,\xi} + \mathit{StorageUnit\_operational\_limit}_{o,\xi} + \mathit{Store\_operational\_limit}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `primary_energy`

```yaml
primary_energy:
  dims: [scenario, global_constraint]
  expression: Generator_primary_energy + StorageUnit_primary_energy + Store_primary_energy
  description: >-
    what a `primary_energy` row totals: weighted generator energy over the
    snapshots it counts, less the charge left in weighted storage at the
    close. The initial charge it is compared against is folded into the
    row's constant
```

```math
\mathit{primary\_energy}_{o,\xi} = \mathit{Generator\_primary\_energy}_{o,\xi} + \mathit{StorageUnit\_primary\_energy}_{o,\xi} + \mathit{Store\_primary\_energy}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `risk_weighted_opex`

```yaml
risk_weighted_opex:
  expression: (1 - CVaR_omega) * sum(scenario_weight * scenario_opex, over=scenario) + CVaR_omega * CVaR
```

```math
\mathit{risk\_weighted\_opex} = \left( 1 - \omega \right) \cdot \left( \sum_{\xi \in \Xi} \pi_{\xi} \cdot \mathit{scenario\_opex}_{\xi} \right) + \omega \cdot CVaR
```

### `scenario_opex`

```yaml
scenario_opex:
  dims: [scenario]
  expression: >-
    Generator_opex
    + Generator_commitment_opex
    + Link_opex
    + Link_commitment_opex
    + Process_opex
    + Process_commitment_opex
    + StorageUnit_opex
    + Store_opex
  description: >-
    what a future costs to run: every operating term, weighted by the
    snapshot's hours and its period, before the scenario's own weight. A
    start and a stop cost what they cost, unweighted, as PyPSA adds them
    (`optimize.py:448-468`)
```

```math
\mathit{scenario\_opex}_{\xi} = \mathit{Generator\_opex}_{\xi} + \mathit{Generator\_commitment\_opex}_{\xi} + \mathit{Link\_opex}_{\xi} + \mathit{Link\_commitment\_opex}_{\xi} + \mathit{Process\_opex}_{\xi} + \mathit{Process\_commitment\_opex}_{\xi} + \mathit{StorageUnit\_opex}_{\xi} + \mathit{Store\_opex}_{\xi} \qquad \forall\, \xi \in \Xi
```

### `tech_capacity_expansion`

```yaml
tech_capacity_expansion:
  dims: [global_constraint]
  expression: >-
    Generator_tech_capacity_expansion
    + Line_tech_capacity_expansion
    + Link_tech_capacity_expansion
    + Process_tech_capacity_expansion
    + StorageUnit_tech_capacity_expansion
    + Store_tech_capacity_expansion
  description: >-
    what a `tech_capacity_expansion_limit` row totals: the chosen build of
    the row's carrier-and-bus set
```

```math
\mathit{tech\_capacity\_expansion}_{o} = \mathit{Generator\_tech\_capacity\_expansion}_{o} + \mathit{Line\_tech\_capacity\_expansion}_{o} + \mathit{Link\_tech\_capacity\_expansion}_{o} + \mathit{Process\_tech\_capacity\_expansion}_{o} + \mathit{StorageUnit\_tech\_capacity\_expansion}_{o} + \mathit{Store\_tech\_capacity\_expansion}_{o} \qquad \forall\, o \in \mathcal{O}
```

### `total_cost`

```yaml
total_cost:
  dims: []
  expression: >-
    Generator_capex
    + Link_capex
    + StorageUnit_capex
    + Store_capex
    + Line_capex
    + Process_capex
    + Transformer_capex
    + risk_weighted_opex
  description: >-
    what the system costs. Capacity counts once per active period at its
    expected cost over the scenarios. Operation counts in expectation over
    the scenarios, and a share of it at the tail
```

```math
\mathit{total\_cost} = \mathit{Generator\_capex} + \mathit{Link\_capex} + \mathit{StorageUnit\_capex} + \mathit{Store\_capex} + \mathit{Line\_capex} + \mathit{Process\_capex} + \mathit{Transformer\_capex} + \mathit{risk\_weighted\_opex}
```

### `transmission_expansion_cost`

```yaml
transmission_expansion_cost:
  dims: [scenario, global_constraint]
  expression: Line_transmission_expansion_cost + Link_transmission_expansion_cost
  description: >-
    what a `transmission_expansion_cost_limit` row totals: capital cost
    times the chosen build of the row's branches
```

```math
\mathit{transmission\_expansion\_cost}_{o,\xi} = \mathit{Line\_transmission\_expansion\_cost}_{o,\xi} + \mathit{Link\_transmission\_expansion\_cost}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### `transmission_volume_expansion`

```yaml
transmission_volume_expansion:
  dims: [scenario, global_constraint]
  expression: Line_transmission_volume_expansion + Link_transmission_volume_expansion
  description: >-
    what a `transmission_volume_expansion_limit` row totals: length times
    the chosen build of the row's branches
```

```math
\mathit{transmission\_volume\_expansion}_{o,\xi} = \mathit{Line\_transmission\_volume\_expansion}_{o,\xi} + \mathit{Link\_transmission\_volume\_expansion}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi
```

### Objective

```yaml
objective:
  sense: minimize
  expression: total_cost
```

```math
\min \mathit{total\_cost}
```

### `Bus-nodal_balance`

`Bus_nodal_balance`

```yaml
Bus_nodal_balance:
  description: >-
    `Bus-nodal_balance` — what is generated at a bus meets the load there,
    less half of every incident line's and transformer's loss. What is
    generated includes storage dispatch and stores. It is net of what the
    links take away, plus what arrives over them after losses and any delay
    at every port they deliver to. Each process port draws or delivers at
    its own rate, and each passive branch carries its flow. PyPSA dissipates
    a branch's loss half at either end. Each generator, storage unit, store
    and load term enters with its component's `sign`
    (`constraints.py:1480-1481`, `:1592`), and an inactive load not at all.
    A bus nothing is attached to has no row. PyPSA refuses one that carries
    load. The file states no assumption for it.
  dims: [scenario, snapshot, bus]
  expression: Bus_injection == 0
```

```math
-\mathit{NP}_{n,\xi,t} + \sum_{g \in \mathcal{G} \,:\, \mathrm{Generator\_bus}(g) = n} \mathrm{sgn}_{g} \cdot p_{g,\xi,t} - \left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus0}(k) = n} s_{k,\xi,t} \right) + \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus1}(k) = n} s_{k,\xi,t} - 0.5 \cdot \left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus0}(k) = n} \ell_{k,\xi,t} \right) - 0.5 \cdot \left( \sum_{k \in \mathcal{K} \,:\, \mathrm{Line\_bus1}(k) = n} \ell_{k,\xi,t} \right) - \left( \sum_{l \in \mathcal{L} \,:\, \mathrm{Link\_bus0}(l) = n} f_{l,\xi,t} \right) + \sum_{o \in \mathcal{O} \,:\, \mathrm{Link\_output\_bus}(o) = n} \overrightarrow{f}_{o,\xi,t} + \sum_{d \in \mathcal{D} \,:\, \mathrm{Load\_bus}(d) = n} \check{\mathrm{load}}_{d,\xi,t} + \sum_{r \in \mathcal{R} \,:\, \mathrm{Process\_output\_bus}(r) = n} \overrightarrow{z}_{r,\xi,t} + \sum_{s \in \mathcal{S} \,:\, \mathrm{StorageUnit\_bus}(s) = n} \mathrm{sgn}^{h}_{s} \cdot \left( h^{+}_{\xi,t,s} - h^{-}_{\xi,t,s} \right) + \sum_{v \in \mathcal{V} \,:\, \mathrm{Store\_bus}(v) = n} \mathrm{sgn}^{q}_{v} \cdot q_{\xi,t,v} - \left( \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus0}(m) = n} \sigma_{\xi,t,m} \right) + \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus1}(m) = n} \sigma_{\xi,t,m} - 0.5 \cdot \left( \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus0}(m) = n} \ell^{\sigma}_{\xi,t,m} \right) - 0.5 \cdot \left( \sum_{m \in \mathcal{M} \,:\, \mathrm{Transformer\_bus1}(m) = n} \ell^{\sigma}_{\xi,t,m} \right) = 0 \qquad \forall\, n \in \mathcal{N},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `CVaR-def`

`CVaR_def`

```yaml
CVaR_def:
  description: "`CVaR-def` — the tail's average is at least where it starts plus the expected excess over the tail's probability"
  dims: []
  where: CVaR_omega
  expression: CVaR_theta + 1 / (1 - CVaR_alpha) * sum(scenario_weight * CVaR_a, over=scenario) <= CVaR
```

```math
\theta + \frac{1}{1 - \alpha} \cdot \left( \sum_{\xi \in \Xi} \pi_{\xi} \cdot a_{\xi} \right) \le CVaR \qquad \text{where } \omega \text{ is defined}
```

### `CVaR-excess-{s}`

`CVaR_excess`

```yaml
CVaR_excess:
  description: "`CVaR-excess-{s}` — a scenario's operating cost beyond the tail's start is its excess. PyPSA names one row per scenario"
  dims: [scenario]
  where: CVaR_omega
  expression: CVaR_a - scenario_opex + CVaR_theta >= 0
```

```math
a_{\xi} - \mathit{scenario\_opex}_{\xi} + \theta \ge 0 \qquad \forall\, \xi \in \Xi \,:\, \omega \text{ is defined}
```

### `Carrier-growth_limit`

`Carrier_growth_limit`

```yaml
Carrier_growth_limit:
  description: >-
    `Carrier-growth_limit` — what a carrier adds in a period is at most its
    allowance plus a share of what it added the period before. It counts
    what its extendable components add, each build in the first period it
    is active in. The first period has no predecessor, so `edge=0` leaves it
    the bare allowance
  dims: [carrier, period]
  where: Carrier_max_growth
  expression: >-
    Carrier_additions
    - shift(Carrier_additions, along=period, offset=1, edge=0) * Carrier_relative_growth
    <= Carrier_max_growth
```

```math
\mathit{Carrier\_additions}_{i,y} - \mathit{Carrier\_additions}_{i,y \boxminus_{0} 1} \cdot \mathrm{r}^{+}_{i} \le \overline{\Delta}_{i} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y} \,:\, \overline{\Delta}_{i} \text{ is defined}
```

### `FlowBased-balance`

`FlowBased_balance`

```yaml
FlowBased_balance:
  description: "`FlowBased-balance` — the net positions of each domain's zones sum to zero"
  dims: [scenario, snapshot, flow_based_domain]
  expression: sum(FlowBased_net_position, over=bus, by=Bus_flow_based_domain[flow_based_domain]) == 0
```

```math
\sum_{n \in \mathcal{N} \,:\, \mathrm{Bus\_flow\_based\_domain}(n) = l} \mathit{NP}_{n,\xi,t} = 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator-com-down-time`

`Generator_com_down_time`

```yaml
Generator_com_down_time:
  description: >-
    `Generator-com-down-time` — a unit stopped within its own minimum down time
    is still off, and so are the modules of a modular unit that stopped.
    The down time it brought into the horizon counts as one stop before the
    first snapshot, also where the unit is modular and all its modules
    stopped (`constraints.py:656-683`, PyPSA/PyPSA#2114)
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND Generator_min_down_time > 0
  expression: >-
    sum_back(Generator_shut_down, along=snapshot, window=Generator_min_down_time)
    + Generator_down_time_brought_in <= Generator_modules - Generator_status
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}} \mathit{dn}_{g,\xi,t'} + \mathrm{rest}_{g,\xi,t} \le \mathrm{M}_{g,\xi} - u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{DT}_{g,\xi} > 0
```

### `Generator-com-ext-p-lower`

`Generator_com_ext_p_lower`

```yaml
Generator_com_ext_p_lower:
  description: >-
    `Generator-com-ext-p-lower` — a committed extendable unit outputs at
    least its minimum of the chosen build. Off, the big M releases the row
  dims: [scenario, snapshot, generator]
  where: Generator_com_ext
  expression: >-
    Generator_p >=
    Generator_p_min_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
    + Generator_big_m * Generator_status - Generator_big_m
```

```math
p_{g,\xi,t} \ge \underline{\mathrm{p}}_{g,\xi,t} \cdot \left( P_{g} - \gamma_{g,\xi} \cdot \mu^{\mathrm{nom}}_{g,\xi,t} \right) + \mathrm{M}_{g,\xi} \cdot u_{g,\xi,t} - \mathrm{M}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t}
```

### `Generator-com-ext-p-lower-nonneg`

`Generator_com_ext_p_lower_nonneg`

```yaml
Generator_com_ext_p_lower_nonneg:
  description: >-
    `Generator-com-ext-p-lower-nonneg` — where no minimum-per-unit is
    negative, output is also plainly non-negative, a row the big-M lower
    cannot assert while the unit is off
  dims: [scenario, snapshot, generator]
  where: Generator_com_ext AND Generator_p_min_pu_nonneg
  expression: Generator_p >= 0
```

```math
p_{g,\xi,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \mathrm{nonneg}_{g}
```

### `Generator-com-ext-p-upper-bigM`

`Generator_com_ext_p_upper_big_m`

```yaml
Generator_com_ext_p_upper_big_m:
  description: "`Generator-com-ext-p-upper-bigM` — off, a unit outputs nothing. On, the big M is no bound"
  dims: [scenario, snapshot, generator]
  where: Generator_com_ext
  expression: Generator_p <= Generator_big_m * Generator_status
```

```math
p_{g,\xi,t} \le \mathrm{M}_{g,\xi} \cdot u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t}
```

### `Generator-com-ext-p-upper-cap`

`Generator_com_ext_p_upper_cap`

```yaml
Generator_com_ext_p_upper_cap:
  description: >-
    `Generator-com-ext-p-upper-cap` — a committed extendable unit outputs
    at most what is available of the chosen build, whatever its status
  dims: [scenario, snapshot, generator]
  where: Generator_com_ext
  expression: Generator_p <= Generator_p_max_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
```

```math
p_{g,\xi,t} \le \overline{\mathrm{p}}_{g,\xi,t} \cdot \left( P_{g} - \gamma_{g,\xi} \cdot \mu^{\mathrm{nom}}_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t}
```

### `Generator-com-mod-p-lower`

`Generator_com_mod_p_lower`

```yaml
Generator_com_mod_p_lower:
  description: >-
    `Generator-com-mod-p-lower` — a committed modular unit outputs at least
    its minimum of one module, whether the build is fixed or a decision
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND Generator_p_nom_mod > 0
  expression: Generator_p >= Generator_p_min_pu * Generator_p_nom_mod * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
```

```math
p_{g,\xi,t} \ge \underline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{mod}}_{g} \cdot \left( u_{g,\xi,t} - \gamma_{g,\xi} \cdot \mu^{u}_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `Generator-com-mod-p-upper`

`Generator_com_mod_p_upper`

```yaml
Generator_com_mod_p_upper:
  description: >-
    `Generator-com-mod-p-upper` — a committed modular unit outputs at most
    one module's share, whether the build is fixed or a decision
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND Generator_p_nom_mod > 0
  expression: Generator_p <= Generator_p_max_pu * Generator_p_nom_mod * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
```

```math
p_{g,\xi,t} \le \overline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{mod}}_{g} \cdot \left( u_{g,\xi,t} - \gamma_{g,\xi} \cdot \mu^{u}_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `Generator-com-p-lower`

`Generator_com_p_lower`

```yaml
Generator_com_p_lower:
  description: "`Generator-com-p-lower` — a committed unit outputs at least its minimum. Off, it outputs at least nothing"
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
  expression: Generator_p >= Generator_p_min_pu * Generator_p_nom * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
```

```math
p_{g,\xi,t} \ge \underline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot \left( u_{g,\xi,t} - \gamma_{g,\xi} \cdot \mu^{u}_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-com-p-upper`

`Generator_com_p_upper`

```yaml
Generator_com_p_upper:
  description: "`Generator-com-p-upper` — a committed unit outputs at most what is available. Off, it outputs at most nothing"
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
  expression: Generator_p <= Generator_p_max_pu * Generator_p_nom * (Generator_status - Generator_maintenance_pu * Generator_maintenance_status)
```

```math
p_{g,\xi,t} \le \overline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot \left( u_{g,\xi,t} - \gamma_{g,\xi} \cdot \mu^{u}_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-com-transition-shut-down`

`Generator_com_transition_shut_down`

```yaml
Generator_com_transition_shut_down:
  description: "`Generator-com-transition-shut-down` — turning off is a stop, counted against the state the unit carried into the snapshot"
  dims: [scenario, snapshot, generator]
  where: Generator_committed
  expression: Generator_shut_down >= Generator_previous_status - Generator_status
```

```math
\mathit{dn}_{g,\xi,t} \ge \overleftarrow{u}_{g,\xi,t} - u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

### `Generator-com-transition-start-up`

`Generator_com_transition_start_up`

```yaml
Generator_com_transition_start_up:
  description: "`Generator-com-transition-start-up` — turning on is a start, counted against the state the unit carried into the snapshot"
  dims: [scenario, snapshot, generator]
  where: Generator_committed
  expression: Generator_start_up >= Generator_status - Generator_previous_status
```

```math
\mathit{up}_{g,\xi,t} \ge u_{g,\xi,t} - \overleftarrow{u}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

### `Generator-com-up-time`

`Generator_com_up_time`

```yaml
Generator_com_up_time:
  description: >-
    `Generator-com-up-time` — a unit started within its own minimum up time is
    still on. The up time it brought into the horizon counts as a start
    before the first snapshot
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND Generator_min_up_time > 0
  expression: >-
    sum_back(Generator_start_up, along=snapshot, window=Generator_min_up_time)
    + Generator_up_time_brought_in <= Generator_status
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}} \mathit{up}_{g,\xi,t'} + \mathrm{hold}_{g,\xi,t} \le u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{UT}_{g,\xi} > 0
```

### `Generator-e_sum_max`

`Generator_e_sum_max`

```yaml
Generator_e_sum_max:
  description: "`Generator-e_sum_max` — energy over the horizon, each period weighted by its years, is at most its budget. A budget of infinity is no row"
  dims: [scenario, generator]
  where: Generator_e_sum_max
  expression: sum(Generator_p * energy_limit_weight, over=snapshot) <= Generator_e_sum_max
```

```math
\sum_{t \in \mathcal{T}} p_{g,\xi,t} \cdot \mathit{w}^{E}_{t} \le \overline{\mathrm{E}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \overline{\mathrm{E}}_{g,\xi} \text{ is defined}
```

### `Generator-e_sum_min`

`Generator_e_sum_min`

```yaml
Generator_e_sum_min:
  description: "`Generator-e_sum_min` — energy over the horizon, each period weighted by its years, is at least its floor. A floor of minus infinity is no row"
  dims: [scenario, generator]
  where: Generator_e_sum_min
  expression: sum(Generator_p * energy_limit_weight, over=snapshot) >= Generator_e_sum_min
```

```math
\sum_{t \in \mathcal{T}} p_{g,\xi,t} \cdot \mathit{w}^{E}_{t} \ge \underline{\mathrm{E}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \underline{\mathrm{E}}_{g,\xi} \text{ is defined}
```

### `Generator-ext-p-lower`

`Generator_ext_p_lower`

```yaml
Generator_ext_p_lower:
  description: "`Generator-ext-p-lower` — an extendable generator outputs at least its minimum of the chosen build"
  dims: [scenario, snapshot, generator]
  where: Generator_p_nom_extendable AND not Generator_committable AND Generator_active
  expression: Generator_p >= Generator_p_min_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
```

```math
p_{g,\xi,t} \ge \underline{\mathrm{p}}_{g,\xi,t} \cdot \left( P_{g} - \gamma_{g,\xi} \cdot \mu^{\mathrm{nom}}_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{g,t}
```

### `Generator-ext-p_nom-lower`

`Generator_ext_p_nom_lower`

```yaml
Generator_ext_p_nom_lower:
  description: "`Generator-ext-p_nom-lower` — the chosen build is at least its floor in every scenario"
  dims: [scenario, generator]
  where: Generator_p_nom_extendable AND Generator_active_asset
  expression: Generator_p_nom_ext >= Generator_p_nom_min
```

```math
P_{g} \ge \underline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g}
```

### `Generator-ext-p_nom-upper`

`Generator_ext_p_nom_upper`

```yaml
Generator_ext_p_nom_upper:
  description: "`Generator-ext-p_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
  dims: [scenario, generator]
  where: Generator_p_nom_extendable AND Generator_active_asset AND Generator_p_nom_max
  expression: Generator_p_nom_ext <= Generator_p_nom_max
```

```math
P_{g} \le \overline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g} \wedge \overline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \text{ is defined}
```

### `Generator-ext-p-upper`

`Generator_ext_p_upper`

```yaml
Generator_ext_p_upper:
  description: "`Generator-ext-p-upper` — an extendable generator outputs at most what is available of the chosen build"
  dims: [scenario, snapshot, generator]
  where: Generator_p_nom_extendable AND not Generator_committable AND Generator_active
  expression: Generator_p <= Generator_p_max_pu * (Generator_p_nom_ext - Generator_maintenance_pu * Generator_maintenance_capacity)
```

```math
p_{g,\xi,t} \le \overline{\mathrm{p}}_{g,\xi,t} \cdot \left( P_{g} - \gamma_{g,\xi} \cdot \mu^{\mathrm{nom}}_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{g,t}
```

### `Generator-fix-p-lower`

`Generator_fix_p_lower`

```yaml
Generator_fix_p_lower:
  description: "`Generator-fix-p-lower` — a fixed generator outputs at least its minimum"
  dims: [scenario, snapshot, generator]
  where: not Generator_p_nom_extendable AND not Generator_committable AND Generator_active
  expression: Generator_p >= Generator_p_min_pu * Generator_p_nom * (1 - Generator_maintenance_pu * Generator_maintenance)
```

```math
p_{g,\xi,t} \ge \underline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot \left( 1 - \gamma_{g,\xi} \cdot \mu_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{g,t}
```

### `Generator-fix-p-upper`

`Generator_fix_p_upper`

```yaml
Generator_fix_p_upper:
  description: "`Generator-fix-p-upper` — a fixed generator outputs at most what is available"
  dims: [scenario, snapshot, generator]
  where: not Generator_p_nom_extendable AND not Generator_committable AND Generator_active
  expression: Generator_p <= Generator_p_max_pu * Generator_p_nom * (1 - Generator_maintenance_pu * Generator_maintenance)
```

```math
p_{g,\xi,t} \le \overline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot \left( 1 - \gamma_{g,\xi} \cdot \mu_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}_{g} \wedge \neg \mathrm{com}_{g} \wedge \mathrm{on}_{g,t}
```

### `Generator-maint-event-count`

`Generator_maint_event_count`

```yaml
Generator_maint_event_count:
  description: "`Generator-maint-event-count` — a maintainable generator holds its number of maintenance events over the horizon"
  dims: [scenario, generator]
  where: Generator_maintainable
  expression: sum(Generator_maintenance_start, over=snapshot) == Generator_maintenance_events
```

```math
\sum_{t \in \mathcal{T}} \mu^{\mathrm{up}}_{g,\xi,t} = \mathrm{n}^{\mathrm{mnt}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{mnt}_{g}
```

### `Generator-maint-modstatus-lb`

`Generator_maint_modstatus_lb`

```yaml
Generator_maint_modstatus_lb:
  description: "`Generator-maint-modstatus-lb` — in maintenance, every module on is on in maintenance"
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_committed AND Generator_p_nom_mod > 0
  expression: Generator_maintenance_status >= Generator_status - Generator_maintenance_modules * (1 - Generator_maintenance)
```

```math
\mu^{u}_{g,\xi,t} \ge u_{g,\xi,t} - \mathrm{Generator\_maintenance\_modules}_{g,\xi} \cdot \left( 1 - \mu_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `Generator-maint-modstatus-le-maint`

`Generator_maint_modstatus_le_maint`

```yaml
Generator_maint_modstatus_le_maint:
  description: >-
    `Generator-maint-modstatus-le-maint` — out of maintenance, no module is
    on in maintenance. In it, at most its modules in maintenance
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_committed AND Generator_p_nom_mod > 0
  expression: Generator_maintenance_status <= Generator_maintenance_modules * Generator_maintenance
```

```math
\mu^{u}_{g,\xi,t} \le \mathrm{Generator\_maintenance\_modules}_{g,\xi} \cdot \mu_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `Generator-maint-modstatus-le-status`

`Generator_maint_modstatus_le_status`

```yaml
Generator_maint_modstatus_le_status:
  description: "`Generator-maint-modstatus-le-status` — the modules on in maintenance are at most the modules on"
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_committed AND Generator_p_nom_mod > 0
  expression: Generator_maintenance_status <= Generator_status
```

```math
\mu^{u}_{g,\xi,t} \le u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `Generator-maint-start-horizon`

`Generator_maint_start_horizon`

```yaml
Generator_maint_start_horizon:
  description: "`Generator-maint-start-horizon` — no event starts where it could not run its whole duration"
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_active AND Generator_maintenance_start_blocked
  expression: Generator_maintenance_start == 0
```

```math
\mu^{\mathrm{up}}_{g,\xi,t} = 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{blk}_{g,\xi,t}
```

### `Generator-maint-status-lb`

`Generator_maint_status_lb`

```yaml
Generator_maint_status_lb:
  description: "`Generator-maint-status-lb` — on and in maintenance, the status in maintenance is one"
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
  expression: Generator_maintenance_status >= Generator_status + Generator_maintenance - 1
```

```math
\mu^{u}_{g,\xi,t} \ge u_{g,\xi,t} + \mu_{g,\xi,t} - 1 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-maint-status-le-maint`

`Generator_maint_status_le_maint`

```yaml
Generator_maint_status_le_maint:
  description: "`Generator-maint-status-le-maint` — out of maintenance, the status in maintenance is zero"
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
  expression: Generator_maintenance_status <= Generator_maintenance
```

```math
\mu^{u}_{g,\xi,t} \le \mu_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-maint-status-le-status`

`Generator_maint_status_le_status`

```yaml
Generator_maint_status_le_status:
  description: "`Generator-maint-status-le-status` — the status in maintenance is at most the status"
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_committed AND NOT Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0)
  expression: Generator_maintenance_status <= Generator_status
```

```math
\mu^{u}_{g,\xi,t} \le u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-maint-window`

`Generator_maint_window`

```yaml
Generator_maint_window:
  description: >-
    `Generator-maint-window` — a generator is in maintenance exactly where
    an event it started covers the snapshot. Two events do not overlap,
    since the maintenance status is at most one
  dims: [scenario, snapshot, generator]
  where: Generator_maintainable AND Generator_active
  expression: Generator_maintenance == sum(Generator_maintenance_start, over=start, by=Generator_maintenance_cover[covered])
```

```math
\mu_{g,\xi,t} = \sum_{t' \in \mathcal{T} \,:\, \left( t,\ g,\ \xi,\ t' \right) \in \mathrm{Generator\_maintenance\_cover}} \mu^{\mathrm{up}}_{g,\xi,t'} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}_{g} \wedge \mathrm{on}_{g,t}
```

### `Generator-maintcap_lower_nommax`

`Generator_maintcap_lower_nommax`

```yaml
Generator_maintcap_lower_nommax:
  description: "`Generator-maintcap_lower_nommax` — in maintenance, the whole chosen build is taken off"
  dims: [scenario, snapshot, generator]
  where: Generator_maint_ext
  expression: Generator_maintenance_capacity >= Generator_p_nom_ext - Generator_p_nom_max * (1 - Generator_maintenance)
```

```math
\mu^{\mathrm{nom}}_{g,\xi,t} \ge P_{g} - \overline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \left( 1 - \mu_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{g,t}
```

### `Generator-maintcap_lower_nommin`

`Generator_maintcap_lower_nommin`

```yaml
Generator_maintcap_lower_nommin:
  description: "`Generator-maintcap_lower_nommin` — in maintenance, at least the floor of the build is taken off"
  dims: [scenario, snapshot, generator]
  where: Generator_maint_ext AND Generator_p_nom_min > 0
  expression: Generator_maintenance_capacity >= Generator_p_nom_min * Generator_maintenance
```

```math
\mu^{\mathrm{nom}}_{g,\xi,t} \ge \underline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \mu_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{g,t} \wedge \underline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} > 0
```

### `Generator-maintcap_upper`

`Generator_maintcap_upper`

```yaml
Generator_maintcap_upper:
  description: >-
    `Generator-maintcap_upper` — the build taken off is at most the chosen build in
    maintenance, and at most the build less its floor out of it
  dims: [scenario, snapshot, generator]
  where: Generator_maint_ext
  expression: Generator_maintenance_capacity <= Generator_p_nom_ext - Generator_p_nom_min * (1 - Generator_maintenance)
```

```math
\mu^{\mathrm{nom}}_{g,\xi,t} \le P_{g} - \underline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \left( 1 - \mu_{g,\xi,t} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{g,t}
```

### `Generator-maintcap_upper_nommax`

`Generator_maintcap_upper_nommax`

```yaml
Generator_maintcap_upper_nommax:
  description: "`Generator-maintcap_upper_nommax` — out of maintenance, no build is taken off"
  dims: [scenario, snapshot, generator]
  where: Generator_maint_ext
  expression: Generator_maintenance_capacity <= Generator_p_nom_max * Generator_maintenance
```

```math
\mu^{\mathrm{nom}}_{g,\xi,t} \le \overline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \mu_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{mnt,ext}}_{g,t}
```

### `Generator-p_nom_modularity`

`Generator_p_nom_modularity`

```yaml
Generator_p_nom_modularity:
  description: "`Generator-p_nom_modularity` — the chosen build is a whole number of modules"
  dims: [generator]
  where: Generator_p_nom_extendable AND Generator_p_nom_mod > 0 AND Generator_active_asset
  expression: Generator_p_nom_ext == Generator_p_nom_mod * Generator_n_mod
```

```math
P_{g} = \mathrm{p}^{\mathrm{mod}}_{g} \cdot N_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \wedge \mathrm{act}_{g}
```

### `Generator-p_nom_set`

`Generator_p_nom_set`

```yaml
Generator_p_nom_set:
  description: "`Generator-p_nom_set` — the chosen build pinned, wherever a value is given"
  dims: [generator]
  where: Generator_p_nom_extendable AND Generator_active_asset AND Generator_p_nom_set
  expression: Generator_p_nom_ext == Generator_p_nom_set
```

```math
P_{g} = \mathrm{p}^{\mathrm{nom,set}}_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{ext}_{g} \wedge \mathrm{act}_{g} \wedge \mathrm{p}^{\mathrm{nom,set}}_{g} \text{ is defined}
```

### `Generator-p-ramp_limit_down`

`Generator_p_ramp_limit_down`

```yaml
Generator_p_ramp_limit_down:
  description: >-
    `Generator-p-ramp_limit_down` — a generator lowers output no faster than
    its ramp limit of the build. A committed one lowers it no further than
    its shut-down ramp in the snapshot it turns off. A unit that came into
    the horizon running has a row at the first snapshot only where its
    `p_init` gives the output it brought in. No unit has one at the start of
    a later investment period, nor does any unit a big M releases instead
  dims: [scenario, snapshot, generator]
  where: >-
    (Generator_ramp_limit_down OR Generator_ramp_limit_shut_down)
    AND NOT (Generator_committable AND Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0))
    AND Generator_ramps_from_previous
    AND Generator_active
  expression: Generator_previous_p - Generator_p <= Generator_ramp_down_allowance
```

```math
\overleftarrow{p}_{g,\xi,t} - p_{g,\xi,t} \le \Delta^{-}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{rd}_{g,\xi,t} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{g,\xi,t} \wedge \mathrm{on}_{g,t}
```

### `Generator-p-ramp_limit_down-run-bigM`

`Generator_p_ramp_limit_down_run_big_m`

```yaml
Generator_p_ramp_limit_down_run_big_m:
  description: >-
    `Generator-p-ramp_limit_down-run-bigM` — a committed extendable unit
    lowers output no faster than its limit of the chosen build. The big M
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
```

```math
\overleftarrow{p}_{g,\xi,t} - p_{g,\xi,t} \le \widetilde{\mathrm{rd}}_{g,\xi,t} \cdot P_{g} + \mathrm{M}_{g,\xi} - \mathrm{M}_{g,\xi} \cdot u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{rd}_{g,\xi,t} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```

### `Generator-p-ramp_limit_down-shut-bigM`

`Generator_p_ramp_limit_down_shut_big_m`

```yaml
Generator_p_ramp_limit_down_shut_big_m:
  description: >-
    `Generator-p-ramp_limit_down-shut-bigM` — in the snapshot it turns off,
    a committed extendable unit ramps no further than its shut-down ramp of
    the chosen build. The big M releases the row everywhere else
  dims: [scenario, snapshot, generator]
  where: >-
    Generator_com_ext
    AND (Generator_ramp_limit_down OR Generator_ramp_limit_shut_down)
    AND Generator_ramps_from_previous
  expression: >-
    Generator_previous_p - Generator_p <=
    Generator_shut_down_rate * Generator_p_nom_ext
    + Generator_big_m - Generator_big_m * Generator_shut_down
```

```math
\overleftarrow{p}_{g,\xi,t} - p_{g,\xi,t} \le \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot P_{g} + \mathrm{M}_{g,\xi} - \mathrm{M}_{g,\xi} \cdot \mathit{dn}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{rd}_{g,\xi,t} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```

### `Generator-p-ramp_limit_up`

`Generator_p_ramp_limit_up`

```yaml
Generator_p_ramp_limit_up:
  description: >-
    `Generator-p-ramp_limit_up` — a generator raises output no faster than
    its ramp limit of the build. A committed one raises it no further than
    its start-up ramp in the snapshot it turns on. A unit that came into the
    horizon running has a row at the first snapshot only where its `p_init`
    gives the output it brought in. No unit has one at the start of a later
    investment period, nor does any unit a big M releases instead
  dims: [scenario, snapshot, generator]
  where: >-
    (Generator_ramp_limit_up OR Generator_ramp_limit_start_up)
    AND NOT (Generator_committable AND Generator_p_nom_extendable AND NOT (Generator_p_nom_mod > 0))
    AND Generator_ramps_from_previous
    AND Generator_active
  expression: Generator_p - Generator_previous_p <= Generator_ramp_up_allowance
```

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} \le \Delta^{+}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{ru}_{g,\xi,t} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{g,\xi,t} \wedge \mathrm{on}_{g,t}
```

### `Generator-p-ramp_limit_up-run-bigM`

`Generator_p_ramp_limit_up_run_big_m`

```yaml
Generator_p_ramp_limit_up_run_big_m:
  description: >-
    `Generator-p-ramp_limit_up-run-bigM` — a committed extendable unit
    raises output no faster than its limit of the chosen build. The big M
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
```

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} \le \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot P_{g} + \mathrm{M}_{g,\xi} - \mathrm{M}_{g,\xi} \cdot \overleftarrow{u}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{ru}_{g,\xi,t} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```

### `Generator-p-ramp_limit_up-start-bigM`

`Generator_p_ramp_limit_up_start_big_m`

```yaml
Generator_p_ramp_limit_up_start_big_m:
  description: >-
    `Generator-p-ramp_limit_up-start-bigM` — in the snapshot it turns on, a
    committed extendable unit ramps no further than its start-up ramp of the
    chosen build. The big M releases the row everywhere else
  dims: [scenario, snapshot, generator]
  where: >-
    Generator_com_ext
    AND (Generator_ramp_limit_up OR Generator_ramp_limit_start_up)
    AND Generator_ramps_from_previous
  expression: >-
    Generator_p - Generator_previous_p <=
    Generator_start_up_rate * Generator_p_nom_ext
    + Generator_big_m - Generator_big_m * Generator_start_up
```

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} \le \widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} \cdot P_{g} + \mathrm{M}_{g,\xi} - \mathrm{M}_{g,\xi} \cdot \mathit{up}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{ru}_{g,\xi,t} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```

### `Generator-p_set`

`Generator_p_set`

```yaml
Generator_p_set:
  description: "`Generator-p_set` — output pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, generator]
  where: Generator_p_set AND Generator_active
  expression: Generator_p == Generator_p_set
```

```math
p_{g,\xi,t} = \mathrm{p}^{\mathrm{set}}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{p}^{\mathrm{set}}_{g,\xi,t} \text{ is defined} \wedge \mathrm{on}_{g,t}
```

### `Generator-shut_down-p-fixed-upper`

`Generator_shut_down_p_fixed_upper`

```yaml
Generator_shut_down_p_fixed_upper:
  description: >-
    `Generator-shut_down-p-fixed-upper` — a stop is at most the modules in
    place, an explicit row as PyPSA writes it. The bound is one where the
    build is not modular, and the fixed build's whole count of modules where
    it is
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND NOT (Generator_p_nom_extendable AND Generator_p_nom_mod > 0)
  expression: Generator_shut_down <= Generator_modules_installed
```

```math
\mathit{dn}_{g,\xi,t} \le \mathrm{N}^{\mathrm{fix}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-shut_down-p_nom-variable-upper`

`Generator_shut_down_p_nom_variable_upper`

```yaml
Generator_shut_down_p_nom_variable_upper:
  description: "`Generator-shut_down-p_nom-variable-upper` — a modular unit stops only where a module is built"
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND Generator_p_nom_extendable AND Generator_p_nom_mod > 0
  expression: Generator_shut_down <= Generator_n_mod
```

```math
\mathit{dn}_{g,\xi,t} \le N_{g} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `Generator-start_up-p-fixed-upper`

`Generator_start_up_p_fixed_upper`

```yaml
Generator_start_up_p_fixed_upper:
  description: >-
    `Generator-start_up-p-fixed-upper` — a start is at most the modules in
    place, an explicit row as PyPSA writes it. The bound is one where the
    build is not modular, and the fixed build's whole count of modules where
    it is
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND NOT (Generator_p_nom_extendable AND Generator_p_nom_mod > 0)
  expression: Generator_start_up <= Generator_modules_installed
```

```math
\mathit{up}_{g,\xi,t} \le \mathrm{N}^{\mathrm{fix}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-start_up-p_nom-variable-upper`

`Generator_start_up_p_nom_variable_upper`

```yaml
Generator_start_up_p_nom_variable_upper:
  description: "`Generator-start_up-p_nom-variable-upper` — a modular unit starts only where a module is built"
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND Generator_p_nom_extendable AND Generator_p_nom_mod > 0
  expression: Generator_start_up <= Generator_n_mod
```

```math
\mathit{up}_{g,\xi,t} \le N_{g} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `Generator-status-p-fixed-upper`

`Generator_status_p_fixed_upper`

```yaml
Generator_status_p_fixed_upper:
  description: >-
    `Generator-status-p-fixed-upper` — a status is at most the modules in
    place, an explicit row as PyPSA writes it. The bound is one where the
    build is not modular, and the fixed build's whole count of modules where
    it is
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND NOT (Generator_p_nom_extendable AND Generator_p_nom_mod > 0)
  expression: Generator_status <= Generator_modules_installed
```

```math
u_{g,\xi,t} \le \mathrm{N}^{\mathrm{fix}}_{g,\xi} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

### `Generator-status-p_nom-variable-upper`

`Generator_status_p_nom_variable_upper`

```yaml
Generator_status_p_nom_variable_upper:
  description: "`Generator-status-p_nom-variable-upper` — a modular unit is on only where a module is built"
  dims: [scenario, snapshot, generator]
  where: Generator_committed AND Generator_p_nom_extendable AND Generator_p_nom_mod > 0
  expression: Generator_status <= Generator_n_mod
```

```math
u_{g,\xi,t} \le N_{g} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

### `flow_based`

`GlobalConstraint_flow_based_ub`

```yaml
GlobalConstraint_flow_based_ub:
  description: >-
    `flow_based` — a CNEC's flow, the zones' net positions and the corridor
    links' flows each times its factor, is at most its remaining available
    margin. PyPSA names the rows `GlobalConstraint-ram`, one per CNEC and
    snapshot, and reads no `constant` (`flow_based.py:262-293`)
  dims: [scenario, snapshot, global_constraint]
  where: >-
    GlobalConstraint_type == 'flow_based' AND GlobalConstraint_sense == '<='
    AND GlobalConstraint_ram AND GlobalConstraint_counts_snapshot
  expression: >-
    sum(GlobalConstraint_zonal_ptdf * FlowBased_net_position, over=bus)
    + sum(GlobalConstraint_link_ptdf * Link_p, over=link)
    <= GlobalConstraint_ram
```

```math
\sum_{n \in \mathcal{N}} \mathrm{PTDF}^{z}_{n,o,\xi,t} \cdot \mathit{NP}_{n,\xi,t} + \sum_{l \in \mathcal{L}} \mathrm{PTDF}^{f}_{o,l,\xi,t} \cdot f_{l,\xi,t} \le \mathrm{RAM}_{o,\xi,t} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{type}_{o} = \text{'}\mathrm{flow\_based}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{<=}\text{'} \wedge \mathrm{RAM}_{o,\xi,t} \text{ is defined} \wedge \mathrm{in}_{o,\xi,t}
```

### `operational_limit`

`GlobalConstraint_operational_limit_eq`

```yaml
GlobalConstraint_operational_limit_eq:
  description: "`operational_limit` — its total, at its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'operational_limit' AND GlobalConstraint_sense == '=='
  expression: operational_limit == GlobalConstraint_constant
```

```math
\mathit{operational\_limit}_{o,\xi} = \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{operational\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{==}\text{'}
```

### `operational_limit`

`GlobalConstraint_operational_limit_lb`

```yaml
GlobalConstraint_operational_limit_lb:
  description: "`operational_limit` — its total, at least its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'operational_limit' AND GlobalConstraint_sense == '>='
  expression: operational_limit >= GlobalConstraint_constant
```

```math
\mathit{operational\_limit}_{o,\xi} \ge \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{operational\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{>=}\text{'}
```

### `operational_limit`

`GlobalConstraint_operational_limit_ub`

```yaml
GlobalConstraint_operational_limit_ub:
  description: "`operational_limit` — its total, at most its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'operational_limit' AND GlobalConstraint_sense == '<='
  expression: operational_limit <= GlobalConstraint_constant
```

```math
\mathit{operational\_limit}_{o,\xi} \le \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{operational\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{<=}\text{'}
```

### `primary_energy`

`GlobalConstraint_primary_energy_eq`

```yaml
GlobalConstraint_primary_energy_eq:
  description: "`primary_energy` — its total, at its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'primary_energy' AND GlobalConstraint_sense == '=='
  expression: primary_energy == GlobalConstraint_constant
```

```math
\mathit{primary\_energy}_{o,\xi} = \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{primary\_energy}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{==}\text{'}
```

### `primary_energy`

`GlobalConstraint_primary_energy_lb`

```yaml
GlobalConstraint_primary_energy_lb:
  description: "`primary_energy` — its total, at least its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'primary_energy' AND GlobalConstraint_sense == '>='
  expression: primary_energy >= GlobalConstraint_constant
```

```math
\mathit{primary\_energy}_{o,\xi} \ge \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{primary\_energy}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{>=}\text{'}
```

### `primary_energy`

`GlobalConstraint_primary_energy_ub`

```yaml
GlobalConstraint_primary_energy_ub:
  description: "`primary_energy` — its total, at most its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'primary_energy' AND GlobalConstraint_sense == '<='
  expression: primary_energy <= GlobalConstraint_constant
```

```math
\mathit{primary\_energy}_{o,\xi} \le \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{primary\_energy}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{<=}\text{'}
```

### `tech_capacity_expansion_limit`

`GlobalConstraint_tech_capacity_expansion_limit_eq`

```yaml
GlobalConstraint_tech_capacity_expansion_limit_eq:
  description: "`tech_capacity_expansion_limit` — its total, at its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'tech_capacity_expansion_limit' AND GlobalConstraint_sense == '=='
  expression: tech_capacity_expansion == GlobalConstraint_constant
```

```math
\mathit{tech\_capacity\_expansion}_{o} = \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{tech\_capacity\_expansion\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{==}\text{'}
```

### `tech_capacity_expansion_limit`

`GlobalConstraint_tech_capacity_expansion_limit_lb`

```yaml
GlobalConstraint_tech_capacity_expansion_limit_lb:
  description: "`tech_capacity_expansion_limit` — its total, at least its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'tech_capacity_expansion_limit' AND GlobalConstraint_sense == '>='
  expression: tech_capacity_expansion >= GlobalConstraint_constant
```

```math
\mathit{tech\_capacity\_expansion}_{o} \ge \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{tech\_capacity\_expansion\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{>=}\text{'}
```

### `tech_capacity_expansion_limit`

`GlobalConstraint_tech_capacity_expansion_limit_ub`

```yaml
GlobalConstraint_tech_capacity_expansion_limit_ub:
  description: "`tech_capacity_expansion_limit` — its total, at most its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'tech_capacity_expansion_limit' AND GlobalConstraint_sense == '<='
  expression: tech_capacity_expansion <= GlobalConstraint_constant
```

```math
\mathit{tech\_capacity\_expansion}_{o} \le \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{tech\_capacity\_expansion\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{<=}\text{'}
```

### `transmission_expansion_cost_limit`

`GlobalConstraint_transmission_expansion_cost_limit_eq`

```yaml
GlobalConstraint_transmission_expansion_cost_limit_eq:
  description: "`transmission_expansion_cost_limit` — its total, at its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'transmission_expansion_cost_limit' AND GlobalConstraint_sense == '=='
  expression: transmission_expansion_cost == GlobalConstraint_constant
```

```math
\mathit{transmission\_expansion\_cost}_{o,\xi} = \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{transmission\_expansion\_cost\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{==}\text{'}
```

### `transmission_expansion_cost_limit`

`GlobalConstraint_transmission_expansion_cost_limit_lb`

```yaml
GlobalConstraint_transmission_expansion_cost_limit_lb:
  description: "`transmission_expansion_cost_limit` — its total, at least its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'transmission_expansion_cost_limit' AND GlobalConstraint_sense == '>='
  expression: transmission_expansion_cost >= GlobalConstraint_constant
```

```math
\mathit{transmission\_expansion\_cost}_{o,\xi} \ge \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{transmission\_expansion\_cost\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{>=}\text{'}
```

### `transmission_expansion_cost_limit`

`GlobalConstraint_transmission_expansion_cost_limit_ub`

```yaml
GlobalConstraint_transmission_expansion_cost_limit_ub:
  description: "`transmission_expansion_cost_limit` — its total, at most its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'transmission_expansion_cost_limit' AND GlobalConstraint_sense == '<='
  expression: transmission_expansion_cost <= GlobalConstraint_constant
```

```math
\mathit{transmission\_expansion\_cost}_{o,\xi} \le \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{transmission\_expansion\_cost\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{<=}\text{'}
```

### `transmission_volume_expansion_limit`

`GlobalConstraint_transmission_volume_expansion_limit_eq`

```yaml
GlobalConstraint_transmission_volume_expansion_limit_eq:
  description: "`transmission_volume_expansion_limit` — its total, at its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'transmission_volume_expansion_limit' AND GlobalConstraint_sense == '=='
  expression: transmission_volume_expansion == GlobalConstraint_constant
```

```math
\mathit{transmission\_volume\_expansion}_{o,\xi} = \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{transmission\_volume\_expansion\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{==}\text{'}
```

### `transmission_volume_expansion_limit`

`GlobalConstraint_transmission_volume_expansion_limit_lb`

```yaml
GlobalConstraint_transmission_volume_expansion_limit_lb:
  description: "`transmission_volume_expansion_limit` — its total, at least its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'transmission_volume_expansion_limit' AND GlobalConstraint_sense == '>='
  expression: transmission_volume_expansion >= GlobalConstraint_constant
```

```math
\mathit{transmission\_volume\_expansion}_{o,\xi} \ge \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{transmission\_volume\_expansion\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{>=}\text{'}
```

### `transmission_volume_expansion_limit`

`GlobalConstraint_transmission_volume_expansion_limit_ub`

```yaml
GlobalConstraint_transmission_volume_expansion_limit_ub:
  description: "`transmission_volume_expansion_limit` — its total, at most its constant"
  dims: [scenario, global_constraint]
  where: GlobalConstraint_type == 'transmission_volume_expansion_limit' AND GlobalConstraint_sense == '<='
  expression: transmission_volume_expansion <= GlobalConstraint_constant
```

```math
\mathit{transmission\_volume\_expansion}_{o,\xi} \le \mathrm{K}_{o,\xi} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{transmission\_volume\_expansion\_limit}\text{'} \wedge \mathrm{sense}_{o,\xi} = \text{'}\mathrm{<=}\text{'}
```

### `Kirchhoff-Voltage-Law`

`Kirchhoff_Voltage_Law`

```yaml
Kirchhoff_Voltage_Law:
  description: >-
    `Kirchhoff-Voltage-Law` — around every independent cycle the
    impedance-weighted flows sum to nothing. This makes the linear power
    flow physical rather than transport. A transformer's flow weighs its
    effective reactance, and its phase shift enters the cycle sum too. The
    shift is a constant where it is fixed. Where a phase-shifting
    transformer chooses its shift, it is the shift decision times its cycle
    weight. A snapshot uses the cycles of its own period, of the branches
    that are active in it (`constraints.py:1710-1729`). A cycle label that
    period's basis does not reach has no row
  dims: [scenario, snapshot, cycle]
  expression: Cycle_angle_sum == 0
```

```math
\sum_{k \in \mathcal{K}} s_{k,\xi,t} \cdot \mathrm{x}_{c,k,\mathrm{snapshot\_period}(t)} + \sum_{m \in \mathcal{M}} \sigma_{\xi,t,m} \cdot \mathrm{x}^{\sigma}_{c,\mathrm{snapshot\_period}(t),m} + \sum_{m \in \mathcal{M}} \vartheta_{c,t,m} + \sum_{m \in \mathcal{M}} \mathit{Transformer\_phase\_shift}_{\xi,t,m} \cdot \mathrm{Transformer\_phase\_shift\_cycle\_weight}_{c,\mathrm{snapshot\_period}(t),m} = 0 \qquad \forall\, c \in \mathcal{C},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Line-ext-s-lower`

`Line_ext_s_lower`

```yaml
Line_ext_s_lower:
  description: "`Line-ext-s-lower` — an extendable line carries at least the negative of its rating of the chosen build, the loss counted against it"
  dims: [scenario, snapshot, line]
  where: Line_s_nom_extendable AND Line_active
  expression: Line_s - Line_loss >= -Line_s_max_pu * Line_s_nom_ext
```

```math
s_{k,\xi,t} - \ell_{k,\xi,t} \ge -\overline{\mathrm{s}}_{k,\xi,t} \cdot S_{k} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

### `Line-ext-s-lower-security-for-{c}-outage-in-sub-network-{n}`

`Line_ext_s_lower_security`

```yaml
Line_ext_s_lower_security:
  description: >-
    `Line-ext-s-lower-security-for-{c}-outage-in-sub-network-{n}` — after
    any one outage, an extendable line carries at least the negative of its
    rating of the chosen build. Its flow takes on its share of the outaged
    branch's flow. PyPSA names one row per outaged component `c` and
    sub-network `n`. Under `multi_investment_periods` it appends
    `-period-{p}` for each period `p`. This entry states them all over the
    outage dimension
  dims: [scenario, snapshot, line, outage]
  where: Line_s_nom_extendable AND at(Line_BODF, by=snapshot_period[period])
  expression: Line_s_monitored + at(Line_BODF, by=snapshot_period[period]) * Outage_s >= -Line_s_max_pu * Line_s_nom_ext
```

```math
\check{s}_{k,\xi,t} + \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \cdot \hat{s}_{\kappa,\xi,t} \ge -\overline{\mathrm{s}}_{k,\xi,t} \cdot S_{k} \qquad \forall\, k \in \mathcal{K},\ \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{s}_{k} \wedge \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \text{ is defined}
```

### `Line-ext-s_nom-lower`

`Line_ext_s_nom_lower`

```yaml
Line_ext_s_nom_lower:
  description: "`Line-ext-s_nom-lower` — the chosen build is at least its floor in every scenario"
  dims: [scenario, line]
  where: Line_s_nom_extendable AND Line_active_asset
  expression: Line_s_nom_ext >= Line_s_nom_min
```

```math
S_{k} \ge \underline{\mathrm{s}}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{act}^{s}_{k}
```

### `Line-ext-s_nom-upper`

`Line_ext_s_nom_upper`

```yaml
Line_ext_s_nom_upper:
  description: "`Line-ext-s_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
  dims: [scenario, line]
  where: Line_s_nom_extendable AND Line_active_asset AND Line_s_nom_max
  expression: Line_s_nom_ext <= Line_s_nom_max
```

```math
S_{k} \le \overline{\mathrm{s}}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{act}^{s}_{k} \wedge \overline{\mathrm{s}}^{\mathrm{nom}}_{k,\xi} \text{ is defined}
```

### `Line-ext-s-upper`

`Line_ext_s_upper`

```yaml
Line_ext_s_upper:
  description: "`Line-ext-s-upper` — an extendable line carries at most its rating of the chosen build, the loss included"
  dims: [scenario, snapshot, line]
  where: Line_s_nom_extendable AND Line_active
  expression: Line_s + Line_loss <= Line_s_max_pu * Line_s_nom_ext
```

```math
s_{k,\xi,t} + \ell_{k,\xi,t} \le \overline{\mathrm{s}}_{k,\xi,t} \cdot S_{k} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

### `Line-ext-s-upper-security-for-{c}-outage-in-sub-network-{n}`

`Line_ext_s_upper_security`

```yaml
Line_ext_s_upper_security:
  description: >-
    `Line-ext-s-upper-security-for-{c}-outage-in-sub-network-{n}` — after
    any one outage, an extendable line carries at most its rating of the
    chosen build. Its flow takes on its share of the outaged branch's flow.
    PyPSA names one row per outaged component `c` and sub-network `n`. Under
    `multi_investment_periods` it appends `-period-{p}` for each period `p`.
    This entry states them all over the outage dimension
  dims: [scenario, snapshot, line, outage]
  where: Line_s_nom_extendable AND at(Line_BODF, by=snapshot_period[period])
  expression: Line_s_monitored + at(Line_BODF, by=snapshot_period[period]) * Outage_s <= Line_s_max_pu * Line_s_nom_ext
```

```math
\check{s}_{k,\xi,t} + \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \cdot \hat{s}_{\kappa,\xi,t} \le \overline{\mathrm{s}}_{k,\xi,t} \cdot S_{k} \qquad \forall\, k \in \mathcal{K},\ \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{s}_{k} \wedge \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \text{ is defined}
```

### `Line-fix-s-lower`

`Line_fix_s_lower`

```yaml
Line_fix_s_lower:
  description: "`Line-fix-s-lower` — a fixed line carries at least the negative of its rating, the loss counted against it"
  dims: [scenario, snapshot, line]
  where: not Line_s_nom_extendable AND Line_active
  expression: Line_s - Line_loss >= -Line_s_max_pu * Line_s_nom
```

```math
s_{k,\xi,t} - \ell_{k,\xi,t} \ge -\overline{\mathrm{s}}_{k,\xi,t} \cdot \mathrm{s}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

### `Line-fix-s-lower-security-for-{c}-outage-in-sub-network-{n}`

`Line_fix_s_lower_security`

```yaml
Line_fix_s_lower_security:
  description: >-
    `Line-fix-s-lower-security-for-{c}-outage-in-sub-network-{n}` — after
    any one outage, a fixed line carries at least the negative of its
    rating. Its flow takes on its share of the outaged branch's flow. PyPSA
    names one row per outaged component `c` and sub-network `n`. Under
    `multi_investment_periods` it appends `-period-{p}` for each period `p`.
    This entry states them all over the outage dimension
  dims: [scenario, snapshot, line, outage]
  where: not Line_s_nom_extendable AND at(Line_BODF, by=snapshot_period[period])
  expression: Line_s_monitored + at(Line_BODF, by=snapshot_period[period]) * Outage_s >= -Line_s_max_pu * Line_s_nom
```

```math
\check{s}_{k,\xi,t} + \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \cdot \hat{s}_{\kappa,\xi,t} \ge -\overline{\mathrm{s}}_{k,\xi,t} \cdot \mathrm{s}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{s}_{k} \wedge \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \text{ is defined}
```

### `Line-fix-s-upper`

`Line_fix_s_upper`

```yaml
Line_fix_s_upper:
  description: "`Line-fix-s-upper` — a fixed line carries at most its rating, the loss included"
  dims: [scenario, snapshot, line]
  where: not Line_s_nom_extendable AND Line_active
  expression: Line_s + Line_loss <= Line_s_max_pu * Line_s_nom
```

```math
s_{k,\xi,t} + \ell_{k,\xi,t} \le \overline{\mathrm{s}}_{k,\xi,t} \cdot \mathrm{s}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{s}_{k} \wedge \mathrm{on}^{s}_{k,t}
```

### `Line-fix-s-upper-security-for-{c}-outage-in-sub-network-{n}`

`Line_fix_s_upper_security`

```yaml
Line_fix_s_upper_security:
  description: >-
    `Line-fix-s-upper-security-for-{c}-outage-in-sub-network-{n}` — after
    any one outage, a fixed line carries at most its rating. Its flow takes
    on its share of the outaged branch's flow. PyPSA names one row per
    outaged component `c` and sub-network `n`. Under
    `multi_investment_periods` it appends `-period-{p}` for each period `p`.
    This entry states them all over the outage dimension
  dims: [scenario, snapshot, line, outage]
  where: not Line_s_nom_extendable AND at(Line_BODF, by=snapshot_period[period])
  expression: Line_s_monitored + at(Line_BODF, by=snapshot_period[period]) * Outage_s <= Line_s_max_pu * Line_s_nom
```

```math
\check{s}_{k,\xi,t} + \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \cdot \hat{s}_{\kappa,\xi,t} \le \overline{\mathrm{s}}_{k,\xi,t} \cdot \mathrm{s}^{\mathrm{nom}}_{k,\xi} \qquad \forall\, k \in \mathcal{K},\ \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{s}_{k} \wedge \beta_{k,\kappa,\mathrm{snapshot\_period}(t)} \text{ is defined}
```

### `Line-loss_tangents-{k}-1`

`Line_loss_tangents_forward`

```yaml
Line_loss_tangents_forward:
  description: >-
    `Line-loss_tangents-{k}-1`, `Line-loss_secants-pos` — the loss sits
    above every cut to its curve for flow one way. PyPSA names one row per
    tangent `k`, or one row stacked over its `secant` axis, and this entry
    states them all over the segment dimension
  dims: [scenario, snapshot, line, segment]
  where: Line_lossy
  expression: Line_loss + Line_loss_slope * Line_s >= Line_loss_offset
```

```math
\ell_{k,\xi,t} + \mathrm{a}_{k,\xi,m,t} \cdot s_{k,\xi,t} \ge \mathrm{b}_{k,\xi,m,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ m \in \mathcal{M},\ t \in \mathcal{T} \,:\, \mathrm{on}^{s,\mathrm{lossy}}_{k,t}
```

### `Line-loss_tangents-{k}--1`

`Line_loss_tangents_reverse`

```yaml
Line_loss_tangents_reverse:
  description: >-
    `Line-loss_tangents-{k}--1`, `Line-loss_secants-neg` — the same fan
    mirrored, the loss depending on the flow's magnitude
  dims: [scenario, snapshot, line, segment]
  where: Line_lossy
  expression: Line_loss - Line_loss_slope * Line_s >= Line_loss_offset
```

```math
\ell_{k,\xi,t} - \mathrm{a}_{k,\xi,m,t} \cdot s_{k,\xi,t} \ge \mathrm{b}_{k,\xi,m,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ m \in \mathcal{M},\ t \in \mathcal{T} \,:\, \mathrm{on}^{s,\mathrm{lossy}}_{k,t}
```

### `Line-loss_upper`

`Line_loss_upper`

```yaml
Line_loss_upper:
  description: "`Line-loss_upper` — a line dissipates at most the loss at its rating"
  dims: [scenario, snapshot, line]
  where: Line_lossy
  expression: Line_loss <= Line_loss_max
```

```math
\ell_{k,\xi,t} \le \overline{\ell}_{k,\xi,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{s,\mathrm{lossy}}_{k,t}
```

### `Line-s_nom_modularity`

`Line_s_nom_modularity`

```yaml
Line_s_nom_modularity:
  description: "`Line-s_nom_modularity` — the chosen build is a whole number of modules"
  dims: [line]
  where: Line_s_nom_extendable AND Line_s_nom_mod > 0 AND Line_active_asset
  expression: Line_s_nom_ext == Line_s_nom_mod * Line_n_mod
```

```math
S_{k} = \mathrm{s}^{\mathrm{mod}}_{k} \cdot N^{s}_{k} \qquad \forall\, k \in \mathcal{K} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{s}^{\mathrm{mod}}_{k} > 0 \wedge \mathrm{act}^{s}_{k}
```

### `Line-s_nom_set`

`Line_s_nom_set`

```yaml
Line_s_nom_set:
  description: "`Line-s_nom_set` — the chosen build pinned, wherever a value is given"
  dims: [line]
  where: Line_s_nom_extendable AND Line_active_asset AND Line_s_nom_set
  expression: Line_s_nom_ext == Line_s_nom_set
```

```math
S_{k} = \mathrm{s}^{\mathrm{nom,set}}_{k} \qquad \forall\, k \in \mathcal{K} \,:\, \mathrm{ext}^{s}_{k} \wedge \mathrm{act}^{s}_{k} \wedge \mathrm{s}^{\mathrm{nom,set}}_{k} \text{ is defined}
```

### `Line-s_set`

`Line_s_set`

```yaml
Line_s_set:
  description: "`Line-s_set` — flow pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, line]
  where: Line_s_set AND Line_active
  expression: Line_s == Line_s_set
```

```math
s_{k,\xi,t} = \mathrm{s}^{\mathrm{set}}_{k,\xi,t} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{s}^{\mathrm{set}}_{k,\xi,t} \text{ is defined} \wedge \mathrm{on}^{s}_{k,t}
```

### `Line-v_ang-lower`

`Line_v_ang_lower`

```yaml
Line_v_ang_lower:
  description: >-
    `Line-v_ang-lower` — an AC line carries at least the flow at which the
    voltage angle difference across it is the negative of its limit. That
    difference is `x_pu_eff` times the flow in radians
  dims: [scenario, snapshot, line]
  where: Line_v_ang_max AND Line_carrier == 'AC' AND Line_active
  expression: Line_s >= -Line_v_ang_max * (3.141592653589793 / 180) / Line_x_pu_eff
```

```math
s_{k,\xi,t} \ge \frac{-\overline{\delta}_{k,\xi} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff}}_{k,\xi}} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \overline{\delta}_{k,\xi} \text{ is defined} \wedge \mathrm{Line\_carrier}(k) = \text{'}\mathrm{AC}\text{'} \wedge \mathrm{on}^{s}_{k,t}
```

### `Line-v_ang-upper`

`Line_v_ang_upper`

```yaml
Line_v_ang_upper:
  description: >-
    `Line-v_ang-upper` — an AC line carries at most the flow at which the
    voltage angle difference across it reaches its limit
  dims: [scenario, snapshot, line]
  where: Line_v_ang_max AND Line_carrier == 'AC' AND Line_active
  expression: Line_s <= Line_v_ang_max * (3.141592653589793 / 180) / Line_x_pu_eff
```

```math
s_{k,\xi,t} \le \frac{\overline{\delta}_{k,\xi} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff}}_{k,\xi}} \qquad \forall\, k \in \mathcal{K},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \overline{\delta}_{k,\xi} \text{ is defined} \wedge \mathrm{Line\_carrier}(k) = \text{'}\mathrm{AC}\text{'} \wedge \mathrm{on}^{s}_{k,t}
```

### `Link-com-down-time`

`Link_com_down_time`

```yaml
Link_com_down_time:
  description: >-
    `Link-com-down-time` — a link stopped within its own minimum down time
    is still off, and so are the modules of a modular link that stopped.
    The down time it brought into the horizon counts as one stop before the
    first snapshot, also where the link is modular and all its modules
    stopped (`constraints.py:656-683`, PyPSA/PyPSA#2114)
  dims: [scenario, snapshot, link]
  where: Link_committed AND Link_min_down_time > 0
  expression: >-
    sum_back(Link_shut_down, along=snapshot, window=Link_min_down_time)
    + Link_down_time_brought_in <= Link_modules - Link_status
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}^{f}} \mathit{dn}^{f}_{l,\xi,t'} + \mathrm{rest}^{f}_{l,\xi,t} \le \mathrm{M}^{f}_{l,\xi} - u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{DT}^{f}_{l,\xi} > 0
```

### `Link-com-ext-p-lower`

`Link_com_ext_p_lower`

```yaml
Link_com_ext_p_lower:
  description: >-
    `Link-com-ext-p-lower` — a committed extendable link flows at least its
    minimum of the chosen build. Off, the big M releases the row
  dims: [scenario, snapshot, link]
  where: Link_com_ext
  expression: >-
    Link_p >=
    Link_p_min_pu * (Link_p_nom_ext - Link_maintenance_pu * Link_maintenance_capacity)
    + Link_big_m * Link_status - Link_big_m
```

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) + \mathrm{M}^{f}_{l,\xi} \cdot u^{f}_{l,\xi,t} - \mathrm{M}^{f}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```

### `Link-com-ext-p-lower-nonneg`

`Link_com_ext_p_lower_nonneg`

```yaml
Link_com_ext_p_lower_nonneg:
  description: >-
    `Link-com-ext-p-lower-nonneg` — where no minimum-per-unit is
    negative, flow is also plainly non-negative, a row the big-M lower
    cannot assert while the link is off
  dims: [scenario, snapshot, link]
  where: Link_com_ext AND Link_p_min_pu_nonneg
  expression: Link_p >= 0
```

```math
f_{l,\xi,t} \ge 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \mathrm{nonneg}^{f}_{l}
```

### `Link-com-ext-p-upper-bigM`

`Link_com_ext_p_upper_big_m`

```yaml
Link_com_ext_p_upper_big_m:
  description: "`Link-com-ext-p-upper-bigM` — off, a link flows nothing. On, the big M is no bound"
  dims: [scenario, snapshot, link]
  where: Link_com_ext
  expression: Link_p <= Link_big_m * Link_status
```

```math
f_{l,\xi,t} \le \mathrm{M}^{f}_{l,\xi} \cdot u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```

### `Link-com-ext-p-upper-cap`

`Link_com_ext_p_upper_cap`

```yaml
Link_com_ext_p_upper_cap:
  description: >-
    `Link-com-ext-p-upper-cap` — a committed extendable link flows
    at most what is available of the chosen build, whatever its status
  dims: [scenario, snapshot, link]
  where: Link_com_ext
  expression: Link_p <= Link_p_max_pu * (Link_p_nom_ext - Link_maintenance_pu * Link_maintenance_capacity)
```

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```

### `Link-com-mod-p-lower`

`Link_com_mod_p_lower`

```yaml
Link_com_mod_p_lower:
  description: >-
    `Link-com-mod-p-lower` — a committed modular link flows at least
    its minimum of one module, whether the build is fixed or a decision
  dims: [scenario, snapshot, link]
  where: Link_committed AND Link_p_nom_mod > 0
  expression: Link_p >= Link_p_min_pu * Link_p_nom_mod * (Link_status - Link_maintenance_pu * Link_maintenance_status)
```

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{mod}}_{l} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Link-com-mod-p-upper`

`Link_com_mod_p_upper`

```yaml
Link_com_mod_p_upper:
  description: >-
    `Link-com-mod-p-upper` — a committed modular link flows at most
    one module's share, whether the build is fixed or a decision
  dims: [scenario, snapshot, link]
  where: Link_committed AND Link_p_nom_mod > 0
  expression: Link_p <= Link_p_max_pu * Link_p_nom_mod * (Link_status - Link_maintenance_pu * Link_maintenance_status)
```

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{mod}}_{l} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Link-com-p-lower`

`Link_com_p_lower`

```yaml
Link_com_p_lower:
  description: "`Link-com-p-lower` — a committed link flows at least its minimum. Off, it flows at least nothing"
  dims: [scenario, snapshot, link]
  where: Link_committed AND NOT Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0)
  expression: Link_p >= Link_p_min_pu * Link_p_nom * (Link_status - Link_maintenance_pu * Link_maintenance_status)
```

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-com-p-upper`

`Link_com_p_upper`

```yaml
Link_com_p_upper:
  description: "`Link-com-p-upper` — a committed link flows at most what is available. Off, it flows at most nothing"
  dims: [scenario, snapshot, link]
  where: Link_committed AND NOT Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0)
  expression: Link_p <= Link_p_max_pu * Link_p_nom * (Link_status - Link_maintenance_pu * Link_maintenance_status)
```

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-com-transition-shut-down`

`Link_com_transition_shut_down`

```yaml
Link_com_transition_shut_down:
  description: "`Link-com-transition-shut-down` — turning off is a stop, counted against the state the link carried into the snapshot"
  dims: [scenario, snapshot, link]
  where: Link_committed
  expression: Link_shut_down >= Link_previous_status - Link_status
```

```math
\mathit{dn}^{f}_{l,\xi,t} \ge \overleftarrow{u}^{f}_{l,\xi,t} - u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

### `Link-com-transition-start-up`

`Link_com_transition_start_up`

```yaml
Link_com_transition_start_up:
  description: "`Link-com-transition-start-up` — turning on is a start, counted against the state the link carried into the snapshot"
  dims: [scenario, snapshot, link]
  where: Link_committed
  expression: Link_start_up >= Link_status - Link_previous_status
```

```math
\mathit{up}^{f}_{l,\xi,t} \ge u^{f}_{l,\xi,t} - \overleftarrow{u}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

### `Link-com-up-time`

`Link_com_up_time`

```yaml
Link_com_up_time:
  description: >-
    `Link-com-up-time` — a link started within its own minimum up time is
    still on. The up time it brought into the horizon counts as a start
    before the first snapshot
  dims: [scenario, snapshot, link]
  where: Link_committed AND Link_min_up_time > 0
  expression: >-
    sum_back(Link_start_up, along=snapshot, window=Link_min_up_time)
    + Link_up_time_brought_in <= Link_status
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}^{f}} \mathit{up}^{f}_{l,\xi,t'} + \mathrm{hold}^{f}_{l,\xi,t} \le u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{UT}^{f}_{l,\xi} > 0
```

### `Link-e_sum_max`

`Link_e_sum_max`

```yaml
Link_e_sum_max:
  description: "`Link-e_sum_max` — energy withdrawn at `bus0` over the horizon, each period weighted by its years, is at most its budget. A budget of infinity is no row"
  dims: [scenario, link]
  where: Link_e_sum_max
  expression: sum(Link_p * energy_limit_weight, over=snapshot) <= Link_e_sum_max
```

```math
\sum_{t \in \mathcal{T}} f_{l,\xi,t} \cdot \mathit{w}^{E}_{t} \le \overline{\mathrm{E}}^{f}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \overline{\mathrm{E}}^{f}_{l,\xi} \text{ is defined}
```

### `Link-e_sum_min`

`Link_e_sum_min`

```yaml
Link_e_sum_min:
  description: "`Link-e_sum_min` — energy withdrawn at `bus0` over the horizon, each period weighted by its years, is at least its floor. A floor of minus infinity is no row"
  dims: [scenario, link]
  where: Link_e_sum_min
  expression: sum(Link_p * energy_limit_weight, over=snapshot) >= Link_e_sum_min
```

```math
\sum_{t \in \mathcal{T}} f_{l,\xi,t} \cdot \mathit{w}^{E}_{t} \ge \underline{\mathrm{E}}^{f}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \underline{\mathrm{E}}^{f}_{l,\xi} \text{ is defined}
```

### `Link-ext-p-lower`

`Link_ext_p_lower`

```yaml
Link_ext_p_lower:
  description: "`Link-ext-p-lower` — an extendable link carries at least its minimum of the chosen build, negative for the other way"
  dims: [scenario, snapshot, link]
  where: Link_p_nom_extendable AND not Link_committable AND Link_active
  expression: Link_p >= Link_p_min_pu * (Link_p_nom_ext - Link_maintenance_pu * Link_maintenance_capacity)
```

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-ext-p_nom-lower`

`Link_ext_p_nom_lower`

```yaml
Link_ext_p_nom_lower:
  description: "`Link-ext-p_nom-lower` — the chosen build is at least its floor in every scenario"
  dims: [scenario, link]
  where: Link_p_nom_extendable AND Link_active_asset
  expression: Link_p_nom_ext >= Link_p_nom_min
```

```math
F_{l} \ge \underline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{act}^{f}_{l}
```

### `Link-ext-p_nom-upper`

`Link_ext_p_nom_upper`

```yaml
Link_ext_p_nom_upper:
  description: "`Link-ext-p_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
  dims: [scenario, link]
  where: Link_p_nom_extendable AND Link_active_asset AND Link_p_nom_max
  expression: Link_p_nom_ext <= Link_p_nom_max
```

```math
F_{l} \le \overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{act}^{f}_{l} \wedge \overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \text{ is defined}
```

### `Link-ext-p-upper`

`Link_ext_p_upper`

```yaml
Link_ext_p_upper:
  description: "`Link-ext-p-upper` — an extendable link carries at most the chosen build"
  dims: [scenario, snapshot, link]
  where: Link_p_nom_extendable AND not Link_committable AND Link_active
  expression: Link_p <= Link_p_max_pu * (Link_p_nom_ext - Link_maintenance_pu * Link_maintenance_capacity)
```

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-fix-p-lower`

`Link_fix_p_lower`

```yaml
Link_fix_p_lower:
  description: "`Link-fix-p-lower` — a fixed link carries at least its minimum, negative for the other way"
  dims: [scenario, snapshot, link]
  where: not Link_p_nom_extendable AND not Link_committable AND Link_active
  expression: Link_p >= Link_p_min_pu * Link_p_nom * (1 - Link_maintenance_pu * Link_maintenance)
```

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( 1 - \gamma^{f}_{l,\xi} \cdot \mu^{f}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-fix-p-upper`

`Link_fix_p_upper`

```yaml
Link_fix_p_upper:
  description: "`Link-fix-p-upper` — a fixed link carries at most its nominal power"
  dims: [scenario, snapshot, link]
  where: not Link_p_nom_extendable AND not Link_committable AND Link_active
  expression: Link_p <= Link_p_max_pu * Link_p_nom * (1 - Link_maintenance_pu * Link_maintenance)
```

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( 1 - \gamma^{f}_{l,\xi} \cdot \mu^{f}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{f}_{l} \wedge \neg \mathrm{com}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-maint-event-count`

`Link_maint_event_count`

```yaml
Link_maint_event_count:
  description: "`Link-maint-event-count` — a maintainable link holds its number of maintenance events over the horizon"
  dims: [scenario, link]
  where: Link_maintainable
  expression: sum(Link_maintenance_start, over=snapshot) == Link_maintenance_events
```

```math
\sum_{t \in \mathcal{T}} \mu^{f,\mathrm{up}}_{l,\xi,t} = \mathrm{n}^{f,\mathrm{mnt}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{mnt}^{f}_{l}
```

### `Link-maint-modstatus-lb`

`Link_maint_modstatus_lb`

```yaml
Link_maint_modstatus_lb:
  description: "`Link-maint-modstatus-lb` — in maintenance, every module on is on in maintenance"
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_committed AND Link_p_nom_mod > 0
  expression: Link_maintenance_status >= Link_status - Link_maintenance_modules * (1 - Link_maintenance)
```

```math
\mu^{f,u}_{l,\xi,t} \ge u^{f}_{l,\xi,t} - \mathrm{Link\_maintenance\_modules}_{l,\xi} \cdot \left( 1 - \mu^{f}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Link-maint-modstatus-le-maint`

`Link_maint_modstatus_le_maint`

```yaml
Link_maint_modstatus_le_maint:
  description: >-
    `Link-maint-modstatus-le-maint` — out of maintenance, no module is on in
    maintenance. In it, at most its modules in maintenance
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_committed AND Link_p_nom_mod > 0
  expression: Link_maintenance_status <= Link_maintenance_modules * Link_maintenance
```

```math
\mu^{f,u}_{l,\xi,t} \le \mathrm{Link\_maintenance\_modules}_{l,\xi} \cdot \mu^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Link-maint-modstatus-le-status`

`Link_maint_modstatus_le_status`

```yaml
Link_maint_modstatus_le_status:
  description: "`Link-maint-modstatus-le-status` — the modules on in maintenance are at most the modules on"
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_committed AND Link_p_nom_mod > 0
  expression: Link_maintenance_status <= Link_status
```

```math
\mu^{f,u}_{l,\xi,t} \le u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Link-maint-start-horizon`

`Link_maint_start_horizon`

```yaml
Link_maint_start_horizon:
  description: "`Link-maint-start-horizon` — no event starts where it could not run its whole duration"
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_active AND Link_maintenance_start_blocked
  expression: Link_maintenance_start == 0
```

```math
\mu^{f,\mathrm{up}}_{l,\xi,t} = 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t} \wedge \mathrm{blk}^{f}_{l,\xi,t}
```

### `Link-maint-status-lb`

`Link_maint_status_lb`

```yaml
Link_maint_status_lb:
  description: "`Link-maint-status-lb` — on and in maintenance, the status in maintenance is one"
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_committed AND NOT Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0)
  expression: Link_maintenance_status >= Link_status + Link_maintenance - 1
```

```math
\mu^{f,u}_{l,\xi,t} \ge u^{f}_{l,\xi,t} + \mu^{f}_{l,\xi,t} - 1 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-maint-status-le-maint`

`Link_maint_status_le_maint`

```yaml
Link_maint_status_le_maint:
  description: "`Link-maint-status-le-maint` — out of maintenance, the status in maintenance is zero"
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_committed AND NOT Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0)
  expression: Link_maintenance_status <= Link_maintenance
```

```math
\mu^{f,u}_{l,\xi,t} \le \mu^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-maint-status-le-status`

`Link_maint_status_le_status`

```yaml
Link_maint_status_le_status:
  description: "`Link-maint-status-le-status` — the status in maintenance is at most the status"
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_committed AND NOT Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0)
  expression: Link_maintenance_status <= Link_status
```

```math
\mu^{f,u}_{l,\xi,t} \le u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-maint-window`

`Link_maint_window`

```yaml
Link_maint_window:
  description: >-
    `Link-maint-window` — a link is in maintenance exactly where an event it
    started covers the snapshot. Two events do not overlap, since the
    maintenance status is at most one
  dims: [scenario, snapshot, link]
  where: Link_maintainable AND Link_active
  expression: Link_maintenance == sum(Link_maintenance_start, over=start, by=Link_maintenance_cover[covered])
```

```math
\mu^{f}_{l,\xi,t} = \sum_{t' \in \mathcal{T} \,:\, \left( t,\ l,\ \xi,\ t' \right) \in \mathrm{Link\_maintenance\_cover}} \mu^{f,\mathrm{up}}_{l,\xi,t'} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-maintcap_lower_nommax`

`Link_maintcap_lower_nommax`

```yaml
Link_maintcap_lower_nommax:
  description: "`Link-maintcap_lower_nommax` — in maintenance, the whole chosen build is taken off"
  dims: [scenario, snapshot, link]
  where: Link_maint_ext
  expression: Link_maintenance_capacity >= Link_p_nom_ext - Link_p_nom_max * (1 - Link_maintenance)
```

```math
\mu^{f,\mathrm{nom}}_{l,\xi,t} \ge F_{l} - \overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \left( 1 - \mu^{f}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{mnt,ext}}_{l,t}
```

### `Link-maintcap_lower_nommin`

`Link_maintcap_lower_nommin`

```yaml
Link_maintcap_lower_nommin:
  description: "`Link-maintcap_lower_nommin` — in maintenance, at least the floor of the build is taken off"
  dims: [scenario, snapshot, link]
  where: Link_maint_ext AND Link_p_nom_min > 0
  expression: Link_maintenance_capacity >= Link_p_nom_min * Link_maintenance
```

```math
\mu^{f,\mathrm{nom}}_{l,\xi,t} \ge \underline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \mu^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{mnt,ext}}_{l,t} \wedge \underline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} > 0
```

### `Link-maintcap_upper`

`Link_maintcap_upper`

```yaml
Link_maintcap_upper:
  description: >-
    `Link-maintcap_upper` — the build taken off is at most the chosen build in
    maintenance, and at most the build less its floor out of it
  dims: [scenario, snapshot, link]
  where: Link_maint_ext
  expression: Link_maintenance_capacity <= Link_p_nom_ext - Link_p_nom_min * (1 - Link_maintenance)
```

```math
\mu^{f,\mathrm{nom}}_{l,\xi,t} \le F_{l} - \underline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \left( 1 - \mu^{f}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{mnt,ext}}_{l,t}
```

### `Link-maintcap_upper_nommax`

`Link_maintcap_upper_nommax`

```yaml
Link_maintcap_upper_nommax:
  description: "`Link-maintcap_upper_nommax` — out of maintenance, no build is taken off"
  dims: [scenario, snapshot, link]
  where: Link_maint_ext
  expression: Link_maintenance_capacity <= Link_p_nom_max * Link_maintenance
```

```math
\mu^{f,\mathrm{nom}}_{l,\xi,t} \le \overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \mu^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{mnt,ext}}_{l,t}
```

### `Link-p_nom_modularity`

`Link_p_nom_modularity`

```yaml
Link_p_nom_modularity:
  description: "`Link-p_nom_modularity` — the chosen build is a whole number of modules"
  dims: [link]
  where: Link_p_nom_extendable AND Link_p_nom_mod > 0 AND Link_active_asset
  expression: Link_p_nom_ext == Link_p_nom_mod * Link_n_mod
```

```math
F_{l} = \mathrm{f}^{\mathrm{mod}}_{l} \cdot N^{f}_{l} \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \wedge \mathrm{act}^{f}_{l}
```

### `Link-p_nom_set`

`Link_p_nom_set`

```yaml
Link_p_nom_set:
  description: "`Link-p_nom_set` — the chosen build pinned, wherever a value is given"
  dims: [link]
  where: Link_p_nom_extendable AND Link_active_asset AND Link_p_nom_set
  expression: Link_p_nom_ext == Link_p_nom_set
```

```math
F_{l} = \mathrm{f}^{\mathrm{nom,set}}_{l} \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{ext}^{f}_{l} \wedge \mathrm{act}^{f}_{l} \wedge \mathrm{f}^{\mathrm{nom,set}}_{l} \text{ is defined}
```

### `Link-p-ramp_limit_down`

`Link_p_ramp_limit_down`

```yaml
Link_p_ramp_limit_down:
  description: >-
    `Link-p-ramp_limit_down` — a link lowers flow no faster than its ramp
    limit of the build. A committed one lowers it no further than its
    shut-down ramp in the snapshot it turns off. A link that came into the
    horizon running has a row at the first snapshot only where its `p_init`
    gives the flow it brought in. No link has one at the start of a later
    investment period, nor does any link a big M releases instead
  dims: [scenario, snapshot, link]
  where: >-
    (Link_ramp_limit_down OR Link_ramp_limit_shut_down)
    AND NOT (Link_committable AND Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0))
    AND Link_ramps_from_previous
    AND Link_active
  expression: Link_previous_p - Link_p <= Link_ramp_down_allowance
```

```math
\overleftarrow{f}_{l,\xi,t} - f_{l,\xi,t} \le \Delta^{f,-}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{f}_{l} \wedge \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \right) \wedge \mathrm{prev}^{f}_{l,\xi,t} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-p-ramp_limit_down-run-bigM`

`Link_p_ramp_limit_down_run_big_m`

```yaml
Link_p_ramp_limit_down_run_big_m:
  description: >-
    `Link-p-ramp_limit_down-run-bigM` — a committed extendable link lowers
    flow no faster than its limit of the chosen build. The big M releases
    the row in the snapshot it turns off
  dims: [scenario, snapshot, link]
  where: Link_com_ext AND (Link_ramp_limit_down OR Link_ramp_limit_shut_down) AND Link_ramps_from_previous
  expression: >-
    Link_previous_p - Link_p <=
    Link_ramp_down_rate * Link_p_nom_ext
    + Link_big_m - Link_big_m * Link_status
```

```math
\overleftarrow{f}_{l,\xi,t} - f_{l,\xi,t} \le \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```

### `Link-p-ramp_limit_down-shut-bigM`

`Link_p_ramp_limit_down_shut_big_m`

```yaml
Link_p_ramp_limit_down_shut_big_m:
  description: >-
    `Link-p-ramp_limit_down-shut-bigM` — in the snapshot it turns off, a
    committed extendable link ramps no further than its shut-down ramp of
    the chosen build. The big M releases the row everywhere else
  dims: [scenario, snapshot, link]
  where: Link_com_ext AND (Link_ramp_limit_down OR Link_ramp_limit_shut_down) AND Link_ramps_from_previous
  expression: >-
    Link_previous_p - Link_p <=
    Link_shut_down_rate * Link_p_nom_ext
    + Link_big_m - Link_big_m * Link_shut_down
```

```math
\overleftarrow{f}_{l,\xi,t} - f_{l,\xi,t} \le \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot \mathit{dn}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```

### `Link-p-ramp_limit_up`

`Link_p_ramp_limit_up`

```yaml
Link_p_ramp_limit_up:
  description: >-
    `Link-p-ramp_limit_up` — a link raises flow no faster than its ramp
    limit of the build. A committed one raises it no further than its
    start-up ramp in the snapshot it turns on. A link that came into the
    horizon running has a row at the first snapshot only where its `p_init`
    gives the flow it brought in. No link has one at the start of a later
    investment period, nor does any link a big M releases instead
  dims: [scenario, snapshot, link]
  where: >-
    (Link_ramp_limit_up OR Link_ramp_limit_start_up)
    AND NOT (Link_committable AND Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0))
    AND Link_ramps_from_previous
    AND Link_active
  expression: Link_p - Link_previous_p <= Link_ramp_up_allowance
```

```math
f_{l,\xi,t} - \overleftarrow{f}_{l,\xi,t} \le \Delta^{f,+}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{f}_{l} \wedge \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \right) \wedge \mathrm{prev}^{f}_{l,\xi,t} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-p-ramp_limit_up-run-bigM`

`Link_p_ramp_limit_up_run_big_m`

```yaml
Link_p_ramp_limit_up_run_big_m:
  description: >-
    `Link-p-ramp_limit_up-run-bigM` — a committed extendable link raises
    flow no faster than its limit of the chosen build. The big M releases
    the row in the snapshot it turns on
  dims: [scenario, snapshot, link]
  where: Link_com_ext AND (Link_ramp_limit_up OR Link_ramp_limit_start_up) AND Link_ramps_from_previous
  expression: >-
    Link_p - Link_previous_p <=
    Link_ramp_up_rate * Link_p_nom_ext
    + Link_big_m - Link_big_m * Link_previous_status
```

```math
f_{l,\xi,t} - \overleftarrow{f}_{l,\xi,t} \le \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot \overleftarrow{u}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```

### `Link-p-ramp_limit_up-start-bigM`

`Link_p_ramp_limit_up_start_big_m`

```yaml
Link_p_ramp_limit_up_start_big_m:
  description: >-
    `Link-p-ramp_limit_up-start-bigM` — in the snapshot it turns on, a
    committed extendable link ramps no further than its start-up ramp of the
    chosen build. The big M releases the row everywhere else
  dims: [scenario, snapshot, link]
  where: Link_com_ext AND (Link_ramp_limit_up OR Link_ramp_limit_start_up) AND Link_ramps_from_previous
  expression: >-
    Link_p - Link_previous_p <=
    Link_start_up_rate * Link_p_nom_ext
    + Link_big_m - Link_big_m * Link_start_up
```

```math
f_{l,\xi,t} - \overleftarrow{f}_{l,\xi,t} \le \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot \mathit{up}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```

### `Link-p_set`

`Link_p_set`

```yaml
Link_p_set:
  description: "`Link-p_set` — flow pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, link]
  where: Link_p_set AND Link_active
  expression: Link_p == Link_p_set
```

```math
f_{l,\xi,t} = \mathrm{f}^{\mathrm{set}}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{f}^{\mathrm{set}}_{l,\xi,t} \text{ is defined} \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-shut_down-p-fixed-upper`

`Link_shut_down_p_fixed_upper`

```yaml
Link_shut_down_p_fixed_upper:
  description: >-
    `Link-shut_down-p-fixed-upper` — a stop is at most the modules in place,
    an explicit row as PyPSA writes it. The bound is one where the build is
    not modular, and the fixed build's whole count of modules where it is
  dims: [scenario, snapshot, link]
  where: Link_committed AND NOT (Link_p_nom_extendable AND Link_p_nom_mod > 0)
  expression: Link_shut_down <= Link_modules_installed
```

```math
\mathit{dn}^{f}_{l,\xi,t} \le \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \left( \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-shut_down-p_nom-variable-upper`

`Link_shut_down_p_nom_variable_upper`

```yaml
Link_shut_down_p_nom_variable_upper:
  description: "`Link-shut_down-p_nom-variable-upper` — a modular link stops only where a module is built"
  dims: [scenario, snapshot, link]
  where: Link_committed AND Link_p_nom_extendable AND Link_p_nom_mod > 0
  expression: Link_shut_down <= Link_n_mod
```

```math
\mathit{dn}^{f}_{l,\xi,t} \le N^{f}_{l} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Link-start_up-p-fixed-upper`

`Link_start_up_p_fixed_upper`

```yaml
Link_start_up_p_fixed_upper:
  description: >-
    `Link-start_up-p-fixed-upper` — a start is at most the modules in place,
    an explicit row as PyPSA writes it. The bound is one where the build is
    not modular, and the fixed build's whole count of modules where it is
  dims: [scenario, snapshot, link]
  where: Link_committed AND NOT (Link_p_nom_extendable AND Link_p_nom_mod > 0)
  expression: Link_start_up <= Link_modules_installed
```

```math
\mathit{up}^{f}_{l,\xi,t} \le \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \left( \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-start_up-p_nom-variable-upper`

`Link_start_up_p_nom_variable_upper`

```yaml
Link_start_up_p_nom_variable_upper:
  description: "`Link-start_up-p_nom-variable-upper` — a modular link starts only where a module is built"
  dims: [scenario, snapshot, link]
  where: Link_committed AND Link_p_nom_extendable AND Link_p_nom_mod > 0
  expression: Link_start_up <= Link_n_mod
```

```math
\mathit{up}^{f}_{l,\xi,t} \le N^{f}_{l} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Link-status-p-fixed-upper`

`Link_status_p_fixed_upper`

```yaml
Link_status_p_fixed_upper:
  description: >-
    `Link-status-p-fixed-upper` — a status is at most the modules in place,
    an explicit row as PyPSA writes it. The bound is one where the build is
    not modular, and the fixed build's whole count of modules where it is
  dims: [scenario, snapshot, link]
  where: Link_committed AND NOT (Link_p_nom_extendable AND Link_p_nom_mod > 0)
  expression: Link_status <= Link_modules_installed
```

```math
u^{f}_{l,\xi,t} \le \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \left( \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

### `Link-status-p_nom-variable-upper`

`Link_status_p_nom_variable_upper`

```yaml
Link_status_p_nom_variable_upper:
  description: "`Link-status-p_nom-variable-upper` — a modular link is on only where a module is built"
  dims: [scenario, snapshot, link]
  where: Link_committed AND Link_p_nom_extendable AND Link_p_nom_mod > 0
  expression: Link_status <= Link_n_mod
```

```math
u^{f}_{l,\xi,t} \le N^{f}_{l} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

### `Process-com-down-time`

`Process_com_down_time`

```yaml
Process_com_down_time:
  description: >-
    `Process-com-down-time` — a process stopped within its own minimum down time
    is still off, and so are the modules of a modular process that stopped.
    The down time it brought into the horizon counts as one stop before the
    first snapshot, also where the process is modular and all its modules
    stopped (`constraints.py:656-683`, PyPSA/PyPSA#2114)
  dims: [scenario, snapshot, process]
  where: Process_committed AND Process_min_down_time > 0
  expression: >-
    sum_back(Process_shut_down, along=snapshot, window=Process_min_down_time)
    + Process_down_time_brought_in <= Process_modules - Process_status
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}^{z}} \mathit{dn}^{z}_{j,\xi,t'} + \mathrm{rest}^{z}_{j,\xi,t} \le \mathrm{M}^{z}_{j,\xi} - u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{DT}^{z}_{j,\xi} > 0
```

### `Process-com-ext-p-lower`

`Process_com_ext_p_lower`

```yaml
Process_com_ext_p_lower:
  description: >-
    `Process-com-ext-p-lower` — a committed extendable process runs at least
    its minimum of the chosen build. Off, the big M releases the row
  dims: [scenario, snapshot, process]
  where: Process_com_ext
  expression: >-
    Process_p >=
    Process_p_min_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
    + Process_big_m * Process_status - Process_big_m
```

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) + \mathrm{M}^{z}_{j,\xi} \cdot u^{z}_{j,\xi,t} - \mathrm{M}^{z}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t}
```

### `Process-com-ext-p-lower-nonneg`

`Process_com_ext_p_lower_nonneg`

```yaml
Process_com_ext_p_lower_nonneg:
  description: >-
    `Process-com-ext-p-lower-nonneg` — where no minimum-per-unit is
    negative, internal power is also plainly non-negative, a row the big-M lower
    cannot assert while the process is off
  dims: [scenario, snapshot, process]
  where: Process_com_ext AND Process_p_min_pu_nonneg
  expression: Process_p >= 0
```

```math
z_{j,\xi,t} \ge 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \mathrm{nonneg}^{z}_{j}
```

### `Process-com-ext-p-upper-bigM`

`Process_com_ext_p_upper_big_m`

```yaml
Process_com_ext_p_upper_big_m:
  description: "`Process-com-ext-p-upper-bigM` — off, a process does not run. On, the big M is no bound"
  dims: [scenario, snapshot, process]
  where: Process_com_ext
  expression: Process_p <= Process_big_m * Process_status
```

```math
z_{j,\xi,t} \le \mathrm{M}^{z}_{j,\xi} \cdot u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t}
```

### `Process-com-ext-p-upper-cap`

`Process_com_ext_p_upper_cap`

```yaml
Process_com_ext_p_upper_cap:
  description: >-
    `Process-com-ext-p-upper-cap` — a committed extendable process runs
    at most what is available of the chosen build, whatever its status
  dims: [scenario, snapshot, process]
  where: Process_com_ext
  expression: Process_p <= Process_p_max_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
```

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t}
```

### `Process-com-mod-p-lower`

`Process_com_mod_p_lower`

```yaml
Process_com_mod_p_lower:
  description: >-
    `Process-com-mod-p-lower` — a committed modular process runs at least
    its minimum of one module, whether the build is fixed or a decision
  dims: [scenario, snapshot, process]
  where: Process_committed AND Process_p_nom_mod > 0
  expression: Process_p >= Process_p_min_pu * Process_p_nom_mod * (Process_status - Process_maintenance_pu * Process_maintenance_status)
```

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{mod}}_{j} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `Process-com-mod-p-upper`

`Process_com_mod_p_upper`

```yaml
Process_com_mod_p_upper:
  description: >-
    `Process-com-mod-p-upper` — a committed modular process runs at most
    one module's share, whether the build is fixed or a decision
  dims: [scenario, snapshot, process]
  where: Process_committed AND Process_p_nom_mod > 0
  expression: Process_p <= Process_p_max_pu * Process_p_nom_mod * (Process_status - Process_maintenance_pu * Process_maintenance_status)
```

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{mod}}_{j} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `Process-com-p-lower`

`Process_com_p_lower`

```yaml
Process_com_p_lower:
  description: "`Process-com-p-lower` — a committed process runs at least its minimum. Off, it runs at least nothing"
  dims: [scenario, snapshot, process]
  where: Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
  expression: Process_p >= Process_p_min_pu * Process_p_nom * (Process_status - Process_maintenance_pu * Process_maintenance_status)
```

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-com-p-upper`

`Process_com_p_upper`

```yaml
Process_com_p_upper:
  description: "`Process-com-p-upper` — a committed process runs at most what is available. Off, it runs at most nothing"
  dims: [scenario, snapshot, process]
  where: Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
  expression: Process_p <= Process_p_max_pu * Process_p_nom * (Process_status - Process_maintenance_pu * Process_maintenance_status)
```

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-com-transition-shut-down`

`Process_com_transition_shut_down`

```yaml
Process_com_transition_shut_down:
  description: "`Process-com-transition-shut-down` — turning off is a stop, counted against the state the process carried into the snapshot"
  dims: [scenario, snapshot, process]
  where: Process_committed
  expression: Process_shut_down >= Process_previous_status - Process_status
```

```math
\mathit{dn}^{z}_{j,\xi,t} \ge \overleftarrow{u}^{z}_{j,\xi,t} - u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

### `Process-com-transition-start-up`

`Process_com_transition_start_up`

```yaml
Process_com_transition_start_up:
  description: "`Process-com-transition-start-up` — turning on is a start, counted against the state the process carried into the snapshot"
  dims: [scenario, snapshot, process]
  where: Process_committed
  expression: Process_start_up >= Process_status - Process_previous_status
```

```math
\mathit{up}^{z}_{j,\xi,t} \ge u^{z}_{j,\xi,t} - \overleftarrow{u}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

### `Process-com-up-time`

`Process_com_up_time`

```yaml
Process_com_up_time:
  description: >-
    `Process-com-up-time` — a process started within its own minimum up time is
    still on. The up time it brought into the horizon counts as a start
    before the first snapshot
  dims: [scenario, snapshot, process]
  where: Process_committed AND Process_min_up_time > 0
  expression: >-
    sum_back(Process_start_up, along=snapshot, window=Process_min_up_time)
    + Process_up_time_brought_in <= Process_status
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}^{z}} \mathit{up}^{z}_{j,\xi,t'} + \mathrm{hold}^{z}_{j,\xi,t} \le u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{UT}^{z}_{j,\xi} > 0
```

### `Process-e_sum_max`

`Process_e_sum_max`

```yaml
Process_e_sum_max:
  description: "`Process-e_sum_max` — energy of the internal power over the horizon, each period weighted by its years, is at most its budget. A budget of infinity is no row"
  dims: [scenario, process]
  where: Process_e_sum_max
  expression: sum(Process_p * energy_limit_weight, over=snapshot) <= Process_e_sum_max
```

```math
\sum_{t \in \mathcal{T}} z_{j,\xi,t} \cdot \mathit{w}^{E}_{t} \le \overline{\mathrm{E}}^{z}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \overline{\mathrm{E}}^{z}_{j,\xi} \text{ is defined}
```

### `Process-e_sum_min`

`Process_e_sum_min`

```yaml
Process_e_sum_min:
  description: "`Process-e_sum_min` — energy of the internal power over the horizon, each period weighted by its years, is at least its floor. A floor of minus infinity is no row"
  dims: [scenario, process]
  where: Process_e_sum_min
  expression: sum(Process_p * energy_limit_weight, over=snapshot) >= Process_e_sum_min
```

```math
\sum_{t \in \mathcal{T}} z_{j,\xi,t} \cdot \mathit{w}^{E}_{t} \ge \underline{\mathrm{E}}^{z}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \underline{\mathrm{E}}^{z}_{j,\xi} \text{ is defined}
```

### `Process-ext-p-lower`

`Process_ext_p_lower`

```yaml
Process_ext_p_lower:
  description: "`Process-ext-p-lower` — an extendable process runs at least its minimum of the chosen build, negative for the other way"
  dims: [scenario, snapshot, process]
  where: Process_p_nom_extendable AND not Process_committable AND Process_active
  expression: Process_p >= Process_p_min_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
```

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-ext-p_nom-lower`

`Process_ext_p_nom_lower`

```yaml
Process_ext_p_nom_lower:
  description: "`Process-ext-p_nom-lower` — the chosen build is at least its floor in every scenario"
  dims: [scenario, process]
  where: Process_p_nom_extendable AND Process_active_asset
  expression: Process_p_nom_ext >= Process_p_nom_min
```

```math
Z_{j} \ge \underline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j}
```

### `Process-ext-p_nom-upper`

`Process_ext_p_nom_upper`

```yaml
Process_ext_p_nom_upper:
  description: "`Process-ext-p_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
  dims: [scenario, process]
  where: Process_p_nom_extendable AND Process_active_asset AND Process_p_nom_max
  expression: Process_p_nom_ext <= Process_p_nom_max
```

```math
Z_{j} \le \overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j} \wedge \overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \text{ is defined}
```

### `Process-ext-p-upper`

`Process_ext_p_upper`

```yaml
Process_ext_p_upper:
  description: "`Process-ext-p-upper` — an extendable process runs at most the chosen build"
  dims: [scenario, snapshot, process]
  where: Process_p_nom_extendable AND not Process_committable AND Process_active
  expression: Process_p <= Process_p_max_pu * (Process_p_nom_ext - Process_maintenance_pu * Process_maintenance_capacity)
```

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-fix-p-lower`

`Process_fix_p_lower`

```yaml
Process_fix_p_lower:
  description: "`Process-fix-p-lower` — a fixed process runs at least its minimum, negative for the other way"
  dims: [scenario, snapshot, process]
  where: not Process_p_nom_extendable AND not Process_committable AND Process_active
  expression: Process_p >= Process_p_min_pu * Process_p_nom * (1 - Process_maintenance_pu * Process_maintenance)
```

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( 1 - \gamma^{z}_{j,\xi} \cdot \mu^{z}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-fix-p-upper`

`Process_fix_p_upper`

```yaml
Process_fix_p_upper:
  description: "`Process-fix-p-upper` — a fixed process runs at most its nominal power"
  dims: [scenario, snapshot, process]
  where: not Process_p_nom_extendable AND not Process_committable AND Process_active
  expression: Process_p <= Process_p_max_pu * Process_p_nom * (1 - Process_maintenance_pu * Process_maintenance)
```

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( 1 - \gamma^{z}_{j,\xi} \cdot \mu^{z}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \neg \mathrm{ext}^{z}_{j} \wedge \neg \mathrm{com}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-maint-event-count`

`Process_maint_event_count`

```yaml
Process_maint_event_count:
  description: "`Process-maint-event-count` — a maintainable process holds its number of maintenance events over the horizon"
  dims: [scenario, process]
  where: Process_maintainable
  expression: sum(Process_maintenance_start, over=snapshot) == Process_maintenance_events
```

```math
\sum_{t \in \mathcal{T}} \mu^{z,\mathrm{up}}_{j,\xi,t} = \mathrm{n}^{z,\mathrm{mnt}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{mnt}^{z}_{j}
```

### `Process-maint-modstatus-lb`

`Process_maint_modstatus_lb`

```yaml
Process_maint_modstatus_lb:
  description: "`Process-maint-modstatus-lb` — in maintenance, every module on is on in maintenance"
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_committed AND Process_p_nom_mod > 0
  expression: Process_maintenance_status >= Process_status - Process_maintenance_modules * (1 - Process_maintenance)
```

```math
\mu^{z,u}_{j,\xi,t} \ge u^{z}_{j,\xi,t} - \mathrm{Process\_maintenance\_modules}_{j,\xi} \cdot \left( 1 - \mu^{z}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `Process-maint-modstatus-le-maint`

`Process_maint_modstatus_le_maint`

```yaml
Process_maint_modstatus_le_maint:
  description: >-
    `Process-maint-modstatus-le-maint` — out of maintenance, no module is on
    in maintenance. In it, at most its modules in maintenance
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_committed AND Process_p_nom_mod > 0
  expression: Process_maintenance_status <= Process_maintenance_modules * Process_maintenance
```

```math
\mu^{z,u}_{j,\xi,t} \le \mathrm{Process\_maintenance\_modules}_{j,\xi} \cdot \mu^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `Process-maint-modstatus-le-status`

`Process_maint_modstatus_le_status`

```yaml
Process_maint_modstatus_le_status:
  description: "`Process-maint-modstatus-le-status` — the modules on in maintenance are at most the modules on"
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_committed AND Process_p_nom_mod > 0
  expression: Process_maintenance_status <= Process_status
```

```math
\mu^{z,u}_{j,\xi,t} \le u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `Process-maint-start-horizon`

`Process_maint_start_horizon`

```yaml
Process_maint_start_horizon:
  description: "`Process-maint-start-horizon` — no event starts where it could not run its whole duration"
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_active AND Process_maintenance_start_blocked
  expression: Process_maintenance_start == 0
```

```math
\mu^{z,\mathrm{up}}_{j,\xi,t} = 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t} \wedge \mathrm{blk}^{z}_{j,\xi,t}
```

### `Process-maint-status-lb`

`Process_maint_status_lb`

```yaml
Process_maint_status_lb:
  description: "`Process-maint-status-lb` — on and in maintenance, the status in maintenance is one"
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
  expression: Process_maintenance_status >= Process_status + Process_maintenance - 1
```

```math
\mu^{z,u}_{j,\xi,t} \ge u^{z}_{j,\xi,t} + \mu^{z}_{j,\xi,t} - 1 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-maint-status-le-maint`

`Process_maint_status_le_maint`

```yaml
Process_maint_status_le_maint:
  description: "`Process-maint-status-le-maint` — out of maintenance, the status in maintenance is zero"
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
  expression: Process_maintenance_status <= Process_maintenance
```

```math
\mu^{z,u}_{j,\xi,t} \le \mu^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-maint-status-le-status`

`Process_maint_status_le_status`

```yaml
Process_maint_status_le_status:
  description: "`Process-maint-status-le-status` — the status in maintenance is at most the status"
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_committed AND NOT Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0)
  expression: Process_maintenance_status <= Process_status
```

```math
\mu^{z,u}_{j,\xi,t} \le u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-maint-window`

`Process_maint_window`

```yaml
Process_maint_window:
  description: >-
    `Process-maint-window` — a process is in maintenance exactly where an
    event it started covers the snapshot. Two events do not overlap, since
    the maintenance status is at most one
  dims: [scenario, snapshot, process]
  where: Process_maintainable AND Process_active
  expression: Process_maintenance == sum(Process_maintenance_start, over=start, by=Process_maintenance_cover[covered])
```

```math
\mu^{z}_{j,\xi,t} = \sum_{t' \in \mathcal{T} \,:\, \left( t,\ j,\ \xi,\ t' \right) \in \mathrm{Process\_maintenance\_cover}} \mu^{z,\mathrm{up}}_{j,\xi,t'} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-maintcap_lower_nommax`

`Process_maintcap_lower_nommax`

```yaml
Process_maintcap_lower_nommax:
  description: "`Process-maintcap_lower_nommax` — in maintenance, the whole chosen build is taken off"
  dims: [scenario, snapshot, process]
  where: Process_maint_ext
  expression: Process_maintenance_capacity >= Process_p_nom_ext - Process_p_nom_max * (1 - Process_maintenance)
```

```math
\mu^{z,\mathrm{nom}}_{j,\xi,t} \ge Z_{j} - \overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \left( 1 - \mu^{z}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{j,t}
```

### `Process-maintcap_lower_nommin`

`Process_maintcap_lower_nommin`

```yaml
Process_maintcap_lower_nommin:
  description: "`Process-maintcap_lower_nommin` — in maintenance, at least the floor of the build is taken off"
  dims: [scenario, snapshot, process]
  where: Process_maint_ext AND Process_p_nom_min > 0
  expression: Process_maintenance_capacity >= Process_p_nom_min * Process_maintenance
```

```math
\mu^{z,\mathrm{nom}}_{j,\xi,t} \ge \underline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \mu^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{j,t} \wedge \underline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} > 0
```

### `Process-maintcap_upper`

`Process_maintcap_upper`

```yaml
Process_maintcap_upper:
  description: >-
    `Process-maintcap_upper` — the build taken off is at most the chosen build in
    maintenance, and at most the build less its floor out of it
  dims: [scenario, snapshot, process]
  where: Process_maint_ext
  expression: Process_maintenance_capacity <= Process_p_nom_ext - Process_p_nom_min * (1 - Process_maintenance)
```

```math
\mu^{z,\mathrm{nom}}_{j,\xi,t} \le Z_{j} - \underline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \left( 1 - \mu^{z}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{j,t}
```

### `Process-maintcap_upper_nommax`

`Process_maintcap_upper_nommax`

```yaml
Process_maintcap_upper_nommax:
  description: "`Process-maintcap_upper_nommax` — out of maintenance, no build is taken off"
  dims: [scenario, snapshot, process]
  where: Process_maint_ext
  expression: Process_maintenance_capacity <= Process_p_nom_max * Process_maintenance
```

```math
\mu^{z,\mathrm{nom}}_{j,\xi,t} \le \overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \mu^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{mnt,ext}}_{j,t}
```

### `Process-p_nom_modularity`

`Process_p_nom_modularity`

```yaml
Process_p_nom_modularity:
  description: "`Process-p_nom_modularity` — the chosen build is a whole number of modules"
  dims: [process]
  where: Process_p_nom_extendable AND Process_p_nom_mod > 0 AND Process_active_asset
  expression: Process_p_nom_ext == Process_p_nom_mod * Process_n_mod
```

```math
Z_{j} = \mathrm{z}^{\mathrm{mod}}_{j} \cdot N^{z}_{j} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \wedge \mathrm{act}^{z}_{j}
```

### `Process-p_nom_set`

`Process_p_nom_set`

```yaml
Process_p_nom_set:
  description: "`Process-p_nom_set` — the chosen build pinned, wherever a value is given"
  dims: [process]
  where: Process_p_nom_extendable AND Process_active_asset AND Process_p_nom_set
  expression: Process_p_nom_ext == Process_p_nom_set
```

```math
Z_{j} = \mathrm{z}^{\mathrm{nom,set}}_{j} \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{ext}^{z}_{j} \wedge \mathrm{act}^{z}_{j} \wedge \mathrm{z}^{\mathrm{nom,set}}_{j} \text{ is defined}
```

### `Process-p-ramp_limit_down`

`Process_p_ramp_limit_down`

```yaml
Process_p_ramp_limit_down:
  description: >-
    `Process-p-ramp_limit_down` — a process lowers internal power no faster
    than its ramp limit of the build. A committed one lowers it no further
    than its shut-down ramp in the snapshot it turns off. A process that
    came into the horizon running has a row at the first snapshot only where
    `p_init` gives the internal power it brought in. No process has one at
    the start of a later investment period, nor does any process a big M
    releases instead
  dims: [scenario, snapshot, process]
  where: >-
    (Process_ramp_limit_down OR Process_ramp_limit_shut_down)
    AND NOT (Process_committable AND Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0))
    AND Process_ramps_from_previous
    AND Process_active
  expression: Process_previous_p - Process_p <= Process_ramp_down_allowance
```

```math
\overleftarrow{z}_{j,\xi,t} - z_{j,\xi,t} \le \Delta^{z,-}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right) \wedge \mathrm{prev}^{z}_{j,\xi,t} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-p-ramp_limit_down-run-bigM`

`Process_p_ramp_limit_down_run_big_m`

```yaml
Process_p_ramp_limit_down_run_big_m:
  description: >-
    `Process-p-ramp_limit_down-run-bigM` — a committed extendable process
    lowers internal power no faster than its limit of the chosen build. The
    big M releases the row in the snapshot it turns off
  dims: [scenario, snapshot, process]
  where: >-
    Process_com_ext
    AND (Process_ramp_limit_down OR Process_ramp_limit_shut_down)
    AND Process_ramps_from_previous
  expression: >-
    Process_previous_p - Process_p <=
    Process_ramp_down_rate * Process_p_nom_ext
    + Process_big_m - Process_big_m * Process_status
```

```math
\overleftarrow{z}_{j,\xi,t} - z_{j,\xi,t} \le \widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot Z_{j} + \mathrm{M}^{z}_{j,\xi} - \mathrm{M}^{z}_{j,\xi} \cdot u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```

### `Process-p-ramp_limit_down-shut-bigM`

`Process_p_ramp_limit_down_shut_big_m`

```yaml
Process_p_ramp_limit_down_shut_big_m:
  description: >-
    `Process-p-ramp_limit_down-shut-bigM` — in the snapshot it turns off, a
    committed extendable process ramps no further than its shut-down ramp of
    the chosen build. The big M releases the row everywhere else
  dims: [scenario, snapshot, process]
  where: >-
    Process_com_ext
    AND (Process_ramp_limit_down OR Process_ramp_limit_shut_down)
    AND Process_ramps_from_previous
  expression: >-
    Process_previous_p - Process_p <=
    Process_shut_down_rate * Process_p_nom_ext
    + Process_big_m - Process_big_m * Process_shut_down
```

```math
\overleftarrow{z}_{j,\xi,t} - z_{j,\xi,t} \le \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot Z_{j} + \mathrm{M}^{z}_{j,\xi} - \mathrm{M}^{z}_{j,\xi} \cdot \mathit{dn}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```

### `Process-p-ramp_limit_up`

`Process_p_ramp_limit_up`

```yaml
Process_p_ramp_limit_up:
  description: >-
    `Process-p-ramp_limit_up` — a process raises internal power no faster
    than its ramp limit of the build. A committed one raises it no further
    than its start-up ramp in the snapshot it turns on. A process that came
    into the horizon running has a row at the first snapshot only where
    `p_init` gives the internal power it brought in. No process has one at
    the start of a later investment period, nor does any process a big M
    releases instead
  dims: [scenario, snapshot, process]
  where: >-
    (Process_ramp_limit_up OR Process_ramp_limit_start_up)
    AND NOT (Process_committable AND Process_p_nom_extendable AND NOT (Process_p_nom_mod > 0))
    AND Process_ramps_from_previous
    AND Process_active
  expression: Process_p - Process_previous_p <= Process_ramp_up_allowance
```

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} \le \Delta^{z,+}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right) \wedge \mathrm{prev}^{z}_{j,\xi,t} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-p-ramp_limit_up-run-bigM`

`Process_p_ramp_limit_up_run_big_m`

```yaml
Process_p_ramp_limit_up_run_big_m:
  description: >-
    `Process-p-ramp_limit_up-run-bigM` — a committed extendable process
    raises internal power no faster than its limit of the chosen build. The
    big M releases the row in the snapshot it turns on
  dims: [scenario, snapshot, process]
  where: Process_com_ext AND (Process_ramp_limit_up OR Process_ramp_limit_start_up) AND Process_ramps_from_previous
  expression: >-
    Process_p - Process_previous_p <=
    Process_ramp_up_rate * Process_p_nom_ext
    + Process_big_m - Process_big_m * Process_previous_status
```

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} \le \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot Z_{j} + \mathrm{M}^{z}_{j,\xi} - \mathrm{M}^{z}_{j,\xi} \cdot \overleftarrow{u}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```

### `Process-p-ramp_limit_up-start-bigM`

`Process_p_ramp_limit_up_start_big_m`

```yaml
Process_p_ramp_limit_up_start_big_m:
  description: >-
    `Process-p-ramp_limit_up-start-bigM` — in the snapshot it turns on, a
    committed extendable process ramps no further than its start-up ramp of
    the chosen build. The big M releases the row everywhere else
  dims: [scenario, snapshot, process]
  where: Process_com_ext AND (Process_ramp_limit_up OR Process_ramp_limit_start_up) AND Process_ramps_from_previous
  expression: >-
    Process_p - Process_previous_p <=
    Process_start_up_rate * Process_p_nom_ext
    + Process_big_m - Process_big_m * Process_start_up
```

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} \le \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} \cdot Z_{j} + \mathrm{M}^{z}_{j,\xi} - \mathrm{M}^{z}_{j,\xi} \cdot \mathit{up}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```

### `Process-p_set`

`Process_p_set`

```yaml
Process_p_set:
  description: "`Process-p_set` — internal power pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, process]
  where: Process_p_set AND Process_active
  expression: Process_p == Process_p_set
```

```math
z_{j,\xi,t} = \mathrm{z}^{\mathrm{set}}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{z}^{\mathrm{set}}_{j,\xi,t} \text{ is defined} \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-shut_down-p-fixed-upper`

`Process_shut_down_p_fixed_upper`

```yaml
Process_shut_down_p_fixed_upper:
  description: >-
    `Process-shut_down-p-fixed-upper` — a stop is at most the modules in
    place, an explicit row as PyPSA writes it. The bound is one where the
    build is not modular, and the fixed build's whole count of modules where
    it is
  dims: [scenario, snapshot, process]
  where: Process_committed AND NOT (Process_p_nom_extendable AND Process_p_nom_mod > 0)
  expression: Process_shut_down <= Process_modules_installed
```

```math
\mathit{dn}^{z}_{j,\xi,t} \le \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-shut_down-p_nom-variable-upper`

`Process_shut_down_p_nom_variable_upper`

```yaml
Process_shut_down_p_nom_variable_upper:
  description: "`Process-shut_down-p_nom-variable-upper` — a modular process stops only where a module is built"
  dims: [scenario, snapshot, process]
  where: Process_committed AND Process_p_nom_extendable AND Process_p_nom_mod > 0
  expression: Process_shut_down <= Process_n_mod
```

```math
\mathit{dn}^{z}_{j,\xi,t} \le N^{z}_{j} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `Process-start_up-p-fixed-upper`

`Process_start_up_p_fixed_upper`

```yaml
Process_start_up_p_fixed_upper:
  description: >-
    `Process-start_up-p-fixed-upper` — a start is at most the modules in
    place, an explicit row as PyPSA writes it. The bound is one where the
    build is not modular, and the fixed build's whole count of modules where
    it is
  dims: [scenario, snapshot, process]
  where: Process_committed AND NOT (Process_p_nom_extendable AND Process_p_nom_mod > 0)
  expression: Process_start_up <= Process_modules_installed
```

```math
\mathit{up}^{z}_{j,\xi,t} \le \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-start_up-p_nom-variable-upper`

`Process_start_up_p_nom_variable_upper`

```yaml
Process_start_up_p_nom_variable_upper:
  description: "`Process-start_up-p_nom-variable-upper` — a modular process starts only where a module is built"
  dims: [scenario, snapshot, process]
  where: Process_committed AND Process_p_nom_extendable AND Process_p_nom_mod > 0
  expression: Process_start_up <= Process_n_mod
```

```math
\mathit{up}^{z}_{j,\xi,t} \le N^{z}_{j} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `Process-status-p-fixed-upper`

`Process_status_p_fixed_upper`

```yaml
Process_status_p_fixed_upper:
  description: >-
    `Process-status-p-fixed-upper` — a status is at most the modules in
    place, an explicit row as PyPSA writes it. The bound is one where the
    build is not modular, and the fixed build's whole count of modules where
    it is
  dims: [scenario, snapshot, process]
  where: Process_committed AND NOT (Process_p_nom_extendable AND Process_p_nom_mod > 0)
  expression: Process_status <= Process_modules_installed
```

```math
u^{z}_{j,\xi,t} \le \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

### `Process-status-p_nom-variable-upper`

`Process_status_p_nom_variable_upper`

```yaml
Process_status_p_nom_variable_upper:
  description: "`Process-status-p_nom-variable-upper` — a modular process is on only where a module is built"
  dims: [scenario, snapshot, process]
  where: Process_committed AND Process_p_nom_extendable AND Process_p_nom_mod > 0
  expression: Process_status <= Process_n_mod
```

```math
u^{z}_{j,\xi,t} \le N^{z}_{j} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

### `StorageUnit-energy_balance`

`StorageUnit_energy_balance`

```yaml
StorageUnit_energy_balance:
  description: >-
    `StorageUnit-energy_balance` — the charge carried in, plus what is
    stored after its efficiency, less what dispatch draws down before its
    own, plus inflow not spilled
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_active
  expression: >-
    StorageUnit_state_of_charge ==
    StorageUnit_charge_carried_in
    + StorageUnit_efficiency_store * StorageUnit_p_store * snapshot_weightings_stores
    - StorageUnit_p_dispatch * snapshot_weightings_stores / StorageUnit_efficiency_dispatch
    + (StorageUnit_inflow - StorageUnit_spill) * snapshot_weightings_stores
```

```math
\mathit{soc}_{\xi,t,s} = \overleftarrow{\mathit{soc}}_{\xi,t,s} + \eta^{-}_{\xi,t,s} \cdot h^{-}_{\xi,t,s} \cdot \mathrm{w}^{\mathrm{sto}}_{t} - \frac{h^{+}_{\xi,t,s} \cdot \mathrm{w}^{\mathrm{sto}}_{t}}{\eta^{+}_{\xi,t,s}} + \left( \mathrm{inflow}_{\xi,t,s} - \mathit{spill}_{\xi,t,s} \right) \cdot \mathrm{w}^{\mathrm{sto}}_{t} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h}_{t,s}
```

### `StorageUnit-ext-p_dispatch-lower`

`StorageUnit_ext_p_dispatch_lower`

```yaml
StorageUnit_ext_p_dispatch_lower:
  description: "`StorageUnit-ext-p_dispatch-lower` — dispatch is non-negative"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_ext
  expression: StorageUnit_p_dispatch >= 0
```

```math
h^{+}_{\xi,t,s} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{ext}}_{t,s}
```

### `StorageUnit-ext-p_dispatch-upper`

`StorageUnit_ext_p_dispatch_upper`

```yaml
StorageUnit_ext_p_dispatch_upper:
  description: "`StorageUnit-ext-p_dispatch-upper` — an extendable unit dispatches at most the chosen build"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_ext
  expression: StorageUnit_p_dispatch <= StorageUnit_p_max_pu * StorageUnit_p_nom_ext
```

```math
h^{+}_{\xi,t,s} \le \overline{\mathrm{h}}_{\xi,t,s} \cdot H_{s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{ext}}_{t,s}
```

### `StorageUnit-ext-p_nom-lower`

`StorageUnit_ext_p_nom_lower`

```yaml
StorageUnit_ext_p_nom_lower:
  description: "`StorageUnit-ext-p_nom-lower` — the chosen build is at least its floor in every scenario"
  dims: [scenario, storage_unit]
  where: StorageUnit_p_nom_extendable AND StorageUnit_active_asset
  expression: StorageUnit_p_nom_ext >= StorageUnit_p_nom_min
```

```math
H_{s} \ge \underline{\mathrm{h}}^{\mathrm{nom}}_{\xi,s} \qquad \forall\, \xi \in \Xi,\ s \in \mathcal{S} \,:\, \mathrm{ext}^{h}_{s} \wedge \mathrm{act}^{h}_{s}
```

### `StorageUnit-ext-p_nom-upper`

`StorageUnit_ext_p_nom_upper`

```yaml
StorageUnit_ext_p_nom_upper:
  description: "`StorageUnit-ext-p_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
  dims: [scenario, storage_unit]
  where: StorageUnit_p_nom_extendable AND StorageUnit_active_asset AND StorageUnit_p_nom_max
  expression: StorageUnit_p_nom_ext <= StorageUnit_p_nom_max
```

```math
H_{s} \le \overline{\mathrm{h}}^{\mathrm{nom}}_{\xi,s} \qquad \forall\, \xi \in \Xi,\ s \in \mathcal{S} \,:\, \mathrm{ext}^{h}_{s} \wedge \mathrm{act}^{h}_{s} \wedge \overline{\mathrm{h}}^{\mathrm{nom}}_{\xi,s} \text{ is defined}
```

### `StorageUnit-ext-p_store-lower`

`StorageUnit_ext_p_store_lower`

```yaml
StorageUnit_ext_p_store_lower:
  description: "`StorageUnit-ext-p_store-lower` — storing is non-negative"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_ext
  expression: StorageUnit_p_store >= 0
```

```math
h^{-}_{\xi,t,s} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{ext}}_{t,s}
```

### `StorageUnit-ext-p_store-upper`

`StorageUnit_ext_p_store_upper`

```yaml
StorageUnit_ext_p_store_upper:
  description: >-
    `StorageUnit-ext-p_store-upper` — an extendable unit stores at most the
    chosen build, the minimum-per-unit column carrying that cap negated
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_ext
  expression: StorageUnit_p_store <= -StorageUnit_p_min_pu * StorageUnit_p_nom_ext
```

```math
h^{-}_{\xi,t,s} \le -\underline{\mathrm{h}}_{\xi,t,s} \cdot H_{s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{ext}}_{t,s}
```

### `StorageUnit-ext-state_of_charge-lower`

`StorageUnit_ext_state_of_charge_lower`

```yaml
StorageUnit_ext_state_of_charge_lower:
  description: "`StorageUnit-ext-state_of_charge-lower` — charge is non-negative"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_ext
  expression: StorageUnit_state_of_charge >= 0
```

```math
\mathit{soc}_{\xi,t,s} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{ext}}_{t,s}
```

### `StorageUnit-ext-state_of_charge-upper`

`StorageUnit_ext_state_of_charge_upper`

```yaml
StorageUnit_ext_state_of_charge_upper:
  description: "`StorageUnit-ext-state_of_charge-upper` — an extendable unit holds at most its hours at the chosen build"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_ext
  expression: StorageUnit_state_of_charge <= StorageUnit_max_hours * StorageUnit_p_nom_ext
```

```math
\mathit{soc}_{\xi,t,s} \le \mathrm{T}^{h}_{\xi,s} \cdot H_{s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{ext}}_{t,s}
```

### `StorageUnit-fix-p_dispatch-lower`

`StorageUnit_fix_p_dispatch_lower`

```yaml
StorageUnit_fix_p_dispatch_lower:
  description: "`StorageUnit-fix-p_dispatch-lower` — dispatch is non-negative"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_fix
  expression: StorageUnit_p_dispatch >= 0
```

```math
h^{+}_{\xi,t,s} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{fix}}_{t,s}
```

### `StorageUnit-fix-p_dispatch-upper`

`StorageUnit_fix_p_dispatch_upper`

```yaml
StorageUnit_fix_p_dispatch_upper:
  description: "`StorageUnit-fix-p_dispatch-upper` — a fixed unit dispatches at most its nominal power"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_fix
  expression: StorageUnit_p_dispatch <= StorageUnit_p_max_pu * StorageUnit_p_nom
```

```math
h^{+}_{\xi,t,s} \le \overline{\mathrm{h}}_{\xi,t,s} \cdot \mathrm{h}^{\mathrm{nom}}_{\xi,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{fix}}_{t,s}
```

### `StorageUnit-fix-p_store-lower`

`StorageUnit_fix_p_store_lower`

```yaml
StorageUnit_fix_p_store_lower:
  description: "`StorageUnit-fix-p_store-lower` — storing is non-negative"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_fix
  expression: StorageUnit_p_store >= 0
```

```math
h^{-}_{\xi,t,s} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{fix}}_{t,s}
```

### `StorageUnit-fix-p_store-upper`

`StorageUnit_fix_p_store_upper`

```yaml
StorageUnit_fix_p_store_upper:
  description: >-
    `StorageUnit-fix-p_store-upper` — a fixed unit stores at most its
    nominal power, the minimum-per-unit column carrying that cap negated
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_fix
  expression: StorageUnit_p_store <= -StorageUnit_p_min_pu * StorageUnit_p_nom
```

```math
h^{-}_{\xi,t,s} \le -\underline{\mathrm{h}}_{\xi,t,s} \cdot \mathrm{h}^{\mathrm{nom}}_{\xi,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{fix}}_{t,s}
```

### `StorageUnit-fix-state_of_charge-lower`

`StorageUnit_fix_state_of_charge_lower`

```yaml
StorageUnit_fix_state_of_charge_lower:
  description: "`StorageUnit-fix-state_of_charge-lower` — charge is non-negative"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_fix
  expression: StorageUnit_state_of_charge >= 0
```

```math
\mathit{soc}_{\xi,t,s} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{fix}}_{t,s}
```

### `StorageUnit-fix-state_of_charge-upper`

`StorageUnit_fix_state_of_charge_upper`

```yaml
StorageUnit_fix_state_of_charge_upper:
  description: "`StorageUnit-fix-state_of_charge-upper` — a fixed unit holds at most its hours at nominal power"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_fix
  expression: StorageUnit_state_of_charge <= StorageUnit_max_hours * StorageUnit_p_nom
```

```math
\mathit{soc}_{\xi,t,s} \le \mathrm{T}^{h}_{\xi,s} \cdot \mathrm{h}^{\mathrm{nom}}_{\xi,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h,\mathrm{fix}}_{t,s}
```

### `StorageUnit-p_dispatch_set`

`StorageUnit_p_dispatch_set`

```yaml
StorageUnit_p_dispatch_set:
  description: "`StorageUnit-p_dispatch_set` — dispatch pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_p_dispatch_set AND StorageUnit_active
  expression: StorageUnit_p_dispatch == StorageUnit_p_dispatch_set
```

```math
h^{+}_{\xi,t,s} = \mathrm{h}^{+,\mathrm{set}}_{\xi,t,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{h}^{+,\mathrm{set}}_{\xi,t,s} \text{ is defined} \wedge \mathrm{on}^{h}_{t,s}
```

### `StorageUnit-p_nom_modularity`

`StorageUnit_p_nom_modularity`

```yaml
StorageUnit_p_nom_modularity:
  description: "`StorageUnit-p_nom_modularity` — the chosen build is a whole number of modules"
  dims: [storage_unit]
  where: StorageUnit_p_nom_extendable AND StorageUnit_p_nom_mod > 0 AND StorageUnit_active_asset
  expression: StorageUnit_p_nom_ext == StorageUnit_p_nom_mod * StorageUnit_n_mod
```

```math
H_{s} = \mathrm{h}^{\mathrm{mod}}_{s} \cdot N^{h}_{s} \qquad \forall\, s \in \mathcal{S} \,:\, \mathrm{ext}^{h}_{s} \wedge \mathrm{h}^{\mathrm{mod}}_{s} > 0 \wedge \mathrm{act}^{h}_{s}
```

### `StorageUnit-p_nom_set`

`StorageUnit_p_nom_set`

```yaml
StorageUnit_p_nom_set:
  description: "`StorageUnit-p_nom_set` — the chosen build pinned, wherever a value is given"
  dims: [storage_unit]
  where: StorageUnit_p_nom_extendable AND StorageUnit_active_asset AND StorageUnit_p_nom_set
  expression: StorageUnit_p_nom_ext == StorageUnit_p_nom_set
```

```math
H_{s} = \mathrm{h}^{\mathrm{nom,set}}_{s} \qquad \forall\, s \in \mathcal{S} \,:\, \mathrm{ext}^{h}_{s} \wedge \mathrm{act}^{h}_{s} \wedge \mathrm{h}^{\mathrm{nom,set}}_{s} \text{ is defined}
```

### `StorageUnit-p_set`

`StorageUnit_p_set`

```yaml
StorageUnit_p_set:
  description: "`StorageUnit-p_set` — net dispatch pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_p_set AND StorageUnit_active
  expression: StorageUnit_p_dispatch - StorageUnit_p_store == StorageUnit_p_set
```

```math
h^{+}_{\xi,t,s} - h^{-}_{\xi,t,s} = \mathrm{h}^{\mathrm{set}}_{\xi,t,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{h}^{\mathrm{set}}_{\xi,t,s} \text{ is defined} \wedge \mathrm{on}^{h}_{t,s}
```

### `StorageUnit-p_store_set`

`StorageUnit_p_store_set`

```yaml
StorageUnit_p_store_set:
  description: "`StorageUnit-p_store_set` — charging pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_p_store_set AND StorageUnit_active
  expression: StorageUnit_p_store == StorageUnit_p_store_set
```

```math
h^{-}_{\xi,t,s} = \mathrm{h}^{-,\mathrm{set}}_{\xi,t,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{h}^{-,\mathrm{set}}_{\xi,t,s} \text{ is defined} \wedge \mathrm{on}^{h}_{t,s}
```

### `StorageUnit-state_of_charge_set`

`StorageUnit_state_of_charge_set`

```yaml
StorageUnit_state_of_charge_set:
  description: "`StorageUnit-state_of_charge_set` — charge pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, storage_unit]
  where: StorageUnit_state_of_charge_set AND StorageUnit_active
  expression: StorageUnit_state_of_charge == StorageUnit_state_of_charge_set
```

```math
\mathit{soc}_{\xi,t,s} = \mathrm{soc}^{\mathrm{set}}_{\xi,t,s} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{soc}^{\mathrm{set}}_{\xi,t,s} \text{ is defined} \wedge \mathrm{on}^{h}_{t,s}
```

### `Store-cycles_max`

`Store_cycles_max`

```yaml
Store_cycles_max:
  description: >-
    `Store-cycles_max` — the discharge over the horizon, `p + p_store`
    weighted by the stores weighting, is at most `cycles_max` times the
    build. A store without `cycles_max` has no row
    (`constraints.py:2607-2633`)
  dims: [scenario, store]
  where: Store_cycles_max AND Store_active_asset
  expression: sum((Store_p + Store_p_store) * snapshot_weightings_stores, over=snapshot) <= Store_cycles_max * Store_e_nom_effective
```

```math
\sum_{t \in \mathcal{T}} \left( q_{\xi,t,v} + q^{-}_{\xi,t,v} \right) \cdot \mathrm{w}^{\mathrm{sto}}_{t} \le \mathrm{cyc}^{\max}_{\xi,v} \cdot \widetilde{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{cyc}^{\max}_{\xi,v} \text{ is defined} \wedge \mathrm{act}^{e}_{v}
```

### `Store-e_nom_modularity`

`Store_e_nom_modularity`

```yaml
Store_e_nom_modularity:
  description: "`Store-e_nom_modularity` — the chosen build is a whole number of modules"
  dims: [store]
  where: Store_e_nom_extendable AND Store_e_nom_mod > 0 AND Store_active_asset
  expression: Store_e_nom_ext == Store_e_nom_mod * Store_n_mod
```

```math
E_{v} = \mathrm{e}^{\mathrm{mod}}_{v} \cdot N^{e}_{v} \qquad \forall\, v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{e}^{\mathrm{mod}}_{v} > 0 \wedge \mathrm{act}^{e}_{v}
```

### `Store-e_nom_set`

`Store_e_nom_set`

```yaml
Store_e_nom_set:
  description: "`Store-e_nom_set` — the chosen build pinned, wherever a value is given"
  dims: [store]
  where: Store_e_nom_extendable AND Store_active_asset AND Store_e_nom_set
  expression: Store_e_nom_ext == Store_e_nom_set
```

```math
E_{v} = \mathrm{e}^{\mathrm{nom,set}}_{v} \qquad \forall\, v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v} \wedge \mathrm{e}^{\mathrm{nom,set}}_{v} \text{ is defined}
```

### `Store-e_set`

`Store_e_set`

```yaml
Store_e_set:
  description: "`Store-e_set` — energy pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, store]
  where: Store_e_set AND Store_active
  expression: Store_e == Store_e_set
```

```math
e_{\xi,t,v} = \mathrm{e}^{\mathrm{set}}_{\xi,t,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{e}^{\mathrm{set}}_{\xi,t,v} \text{ is defined} \wedge \mathrm{on}^{e}_{t,v}
```

### `Store-e_sum_max`

`Store_e_sum_max`

```yaml
Store_e_sum_max:
  description: "`Store-e_sum_max` — net energy delivered over the horizon, each period weighted by its years, is at most its budget. A budget of infinity is no row"
  dims: [scenario, store]
  where: Store_e_sum_max
  expression: sum(Store_p * energy_limit_weight, over=snapshot) <= Store_e_sum_max
```

```math
\sum_{t \in \mathcal{T}} q_{\xi,t,v} \cdot \mathit{w}^{E}_{t} \le \overline{\mathrm{E}}^{q}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \overline{\mathrm{E}}^{q}_{\xi,v} \text{ is defined}
```

### `Store-e_sum_min`

`Store_e_sum_min`

```yaml
Store_e_sum_min:
  description: "`Store-e_sum_min` — net energy delivered over the horizon, each period weighted by its years, is at least its floor. A floor of minus infinity is no row"
  dims: [scenario, store]
  where: Store_e_sum_min
  expression: sum(Store_p * energy_limit_weight, over=snapshot) >= Store_e_sum_min
```

```math
\sum_{t \in \mathcal{T}} q_{\xi,t,v} \cdot \mathit{w}^{E}_{t} \ge \underline{\mathrm{E}}^{q}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \underline{\mathrm{E}}^{q}_{\xi,v} \text{ is defined}
```

### `Store-energy_balance`

`Store_energy_balance`

```yaml
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
```

```math
e_{\xi,t,v} = \overleftarrow{e}_{\xi,t,v} - \frac{q_{\xi,t,v} \cdot \mathrm{w}^{\mathrm{sto}}_{t}}{\eta^{e,+}_{\xi,t,v}} + \left( \eta^{e,-}_{\xi,t,v} - \frac{1}{\eta^{e,+}_{\xi,t,v}} \right) \cdot q^{-}_{\xi,t,v} \cdot \mathrm{w}^{\mathrm{sto}}_{t} + \left( \mathrm{inflow}^{e}_{\xi,t,v} - \mathit{spill}^{e}_{\xi,t,v} \right) \cdot \mathrm{w}^{\mathrm{sto}}_{t} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v}
```

### `Store-ext-e-lower`

`Store_ext_e_lower`

```yaml
Store_ext_e_lower:
  description: "`Store-ext-e-lower` — an extendable store holds at least its floor of the chosen build"
  dims: [scenario, snapshot, store]
  where: Store_e_nom_extendable AND Store_active
  expression: Store_e >= Store_e_min_pu * Store_e_nom_ext
```

```math
e_{\xi,t,v} \ge \underline{\mathrm{e}}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

### `Store-ext-e_nom-lower`

`Store_ext_e_nom_lower`

```yaml
Store_ext_e_nom_lower:
  description: "`Store-ext-e_nom-lower` — the chosen build is at least its floor in every scenario"
  dims: [scenario, store]
  where: Store_e_nom_extendable AND Store_active_asset
  expression: Store_e_nom_ext >= Store_e_nom_min
```

```math
E_{v} \ge \underline{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v}
```

### `Store-ext-e_nom-upper`

`Store_ext_e_nom_upper`

```yaml
Store_ext_e_nom_upper:
  description: "`Store-ext-e_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
  dims: [scenario, store]
  where: Store_e_nom_extendable AND Store_active_asset AND Store_e_nom_max
  expression: Store_e_nom_ext <= Store_e_nom_max
```

```math
E_{v} \le \overline{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{act}^{e}_{v} \wedge \overline{\mathrm{e}}^{\mathrm{nom}}_{\xi,v} \text{ is defined}
```

### `Store-ext-e-upper`

`Store_ext_e_upper`

```yaml
Store_ext_e_upper:
  description: "`Store-ext-e-upper` — an extendable store holds at most the chosen build"
  dims: [scenario, snapshot, store]
  where: Store_e_nom_extendable AND Store_active
  expression: Store_e <= Store_e_max_pu * Store_e_nom_ext
```

```math
e_{\xi,t,v} \le \overline{\mathrm{e}}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

### `Store-ext-p-lower`

`Store_ext_p_lower`

```yaml
Store_ext_p_lower:
  description: >-
    `Store-ext-p-lower` — an extendable store discharges at least its floor, which is
    zero where it splits its dispatch and its most charging otherwise. A
    store that does not split and has no `max_hours` has no row
  dims: [scenario, snapshot, store]
  where: Store_e_nom_extendable AND Store_active AND (Store_split_dispatch OR Store_max_hours)
  expression: Store_p + Store_p_store >= Store_discharge_floor_pu * Store_e_nom_ext
```

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \ge \underline{\mathrm{q}}^{+}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

### `Store-ext-p_store-lower`

`Store_ext_p_store_lower`

```yaml
Store_ext_p_store_lower:
  description: "`Store-ext-p_store-lower` — charging is non-negative"
  dims: [scenario, snapshot, store]
  where: Store_e_nom_extendable AND Store_active
  expression: Store_p_store >= 0
```

```math
q^{-}_{\xi,t,v} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

### `Store-ext-p_store-upper`

`Store_ext_p_store_upper`

```yaml
Store_ext_p_store_upper:
  description: >-
    `Store-ext-p_store-upper` — an extendable store charges at most the power rating of the chosen build where it
    splits its dispatch, and not at all where it does not. A store that splits
    and has no `max_hours` has no row
  dims: [scenario, snapshot, store]
  where: Store_e_nom_extendable AND Store_active AND (NOT Store_split_dispatch OR Store_max_hours)
  expression: Store_p_store <= Store_charge_cap_pu * Store_e_nom_ext
```

```math
q^{-}_{\xi,t,v} \le \overline{\mathrm{q}}^{-}_{\xi,t,v} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \neg \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

### `Store-ext-p-upper`

`Store_ext_p_upper`

```yaml
Store_ext_p_upper:
  description: "`Store-ext-p-upper` — an extendable store discharges at most the power rating of the chosen build. A store without `max_hours` has no row"
  dims: [scenario, snapshot, store]
  where: Store_e_nom_extendable AND Store_active AND Store_max_hours
  expression: Store_p + Store_p_store <= Store_p_max_pu / Store_max_hours * Store_e_nom_ext
```

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \le \frac{\overline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} \cdot E_{v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{T}^{e}_{\xi,v} \text{ is defined}
```

### `Store-fix-e-lower`

`Store_fix_e_lower`

```yaml
Store_fix_e_lower:
  description: "`Store-fix-e-lower` — a fixed store holds at least its floor"
  dims: [scenario, snapshot, store]
  where: not Store_e_nom_extendable AND Store_active
  expression: Store_e >= Store_e_min_pu * Store_e_nom
```

```math
e_{\xi,t,v} \ge \underline{\mathrm{e}}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

### `Store-fix-e-upper`

`Store_fix_e_upper`

```yaml
Store_fix_e_upper:
  description: "`Store-fix-e-upper` — a fixed store holds at most its nominal capacity"
  dims: [scenario, snapshot, store]
  where: not Store_e_nom_extendable AND Store_active
  expression: Store_e <= Store_e_max_pu * Store_e_nom
```

```math
e_{\xi,t,v} \le \overline{\mathrm{e}}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

### `Store-fix-p-lower`

`Store_fix_p_lower`

```yaml
Store_fix_p_lower:
  description: >-
    `Store-fix-p-lower` — a fixed store discharges at least its floor, which is
    zero where it splits its dispatch and its most charging otherwise. A
    store that does not split and has no `max_hours` has no row
  dims: [scenario, snapshot, store]
  where: NOT Store_e_nom_extendable AND Store_active AND (Store_split_dispatch OR Store_max_hours)
  expression: Store_p + Store_p_store >= Store_discharge_floor_pu * Store_e_nom
```

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \ge \underline{\mathrm{q}}^{+}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

### `Store-fix-p_store-lower`

`Store_fix_p_store_lower`

```yaml
Store_fix_p_store_lower:
  description: "`Store-fix-p_store-lower` — charging is non-negative"
  dims: [scenario, snapshot, store]
  where: NOT Store_e_nom_extendable AND Store_active
  expression: Store_p_store >= 0
```

```math
q^{-}_{\xi,t,v} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v}
```

### `Store-fix-p_store-upper`

`Store_fix_p_store_upper`

```yaml
Store_fix_p_store_upper:
  description: >-
    `Store-fix-p_store-upper` — a fixed store charges at most its power rating where it
    splits its dispatch, and not at all where it does not. A store that splits
    and has no `max_hours` has no row
  dims: [scenario, snapshot, store]
  where: NOT Store_e_nom_extendable AND Store_active AND (NOT Store_split_dispatch OR Store_max_hours)
  expression: Store_p_store <= Store_charge_cap_pu * Store_e_nom
```

```math
q^{-}_{\xi,t,v} \le \overline{\mathrm{q}}^{-}_{\xi,t,v} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \left( \neg \mathrm{split}^{e}_{\xi,v} \vee \mathrm{T}^{e}_{\xi,v} \text{ is defined} \right)
```

### `Store-fix-p-upper`

`Store_fix_p_upper`

```yaml
Store_fix_p_upper:
  description: "`Store-fix-p-upper` — a fixed store discharges at most its power rating. A store without `max_hours` has no row"
  dims: [scenario, snapshot, store]
  where: NOT Store_e_nom_extendable AND Store_active AND Store_max_hours
  expression: Store_p + Store_p_store <= Store_p_max_pu / Store_max_hours * Store_e_nom
```

```math
q_{\xi,t,v} + q^{-}_{\xi,t,v} \le \frac{\overline{\mathrm{q}}_{\xi,t,v}}{\mathrm{T}^{e}_{\xi,v}} \cdot \mathrm{e}^{\mathrm{nom}}_{\xi,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \neg \mathrm{ext}^{e}_{v} \wedge \mathrm{on}^{e}_{t,v} \wedge \mathrm{T}^{e}_{\xi,v} \text{ is defined}
```

### `Store-p_set`

`Store_p_set`

```yaml
Store_p_set:
  description: "`Store-p_set` — power delivered pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, store]
  where: Store_p_set AND Store_active
  expression: Store_p == Store_p_set
```

```math
q_{\xi,t,v} = \mathrm{q}^{\mathrm{set}}_{\xi,t,v} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{q}^{\mathrm{set}}_{\xi,t,v} \text{ is defined} \wedge \mathrm{on}^{e}_{t,v}
```

### `Transformer-ext-s-lower`

`Transformer_ext_s_lower`

```yaml
Transformer_ext_s_lower:
  description: "`Transformer-ext-s-lower` — an extendable transformer carries at least the negative of its rating of the chosen build, the loss counted against it"
  dims: [scenario, snapshot, transformer]
  where: Transformer_s_nom_extendable AND Transformer_active
  expression: Transformer_s - Transformer_loss >= -Transformer_s_max_pu * Transformer_s_nom_ext
```

```math
\sigma_{\xi,t,m} - \ell^{\sigma}_{\xi,t,m} \ge -\overline{\sigma}_{\xi,t,m} \cdot \Sigma_{m} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-ext-s-lower-security-for-{c}-outage-in-sub-network-{n}`

`Transformer_ext_s_lower_security`

```yaml
Transformer_ext_s_lower_security:
  description: >-
    `Transformer-ext-s-lower-security-for-{c}-outage-in-sub-network-{n}` —
    after any one outage, an extendable transformer carries at least the
    negative of its rating of the chosen build. Its flow takes on its share
    of the outaged branch's flow. PyPSA names one row per outaged component
    `c` and sub-network `n`. Under `multi_investment_periods` it appends
    `-period-{p}` for each period `p`. This entry states them all over the
    outage dimension
  dims: [scenario, snapshot, transformer, outage]
  where: Transformer_s_nom_extendable AND at(Transformer_BODF, by=snapshot_period[period])
  expression: Transformer_s_monitored + at(Transformer_BODF, by=snapshot_period[period]) * Outage_s >= -Transformer_s_max_pu * Transformer_s_nom_ext
```

```math
\check{\sigma}_{\xi,t,m} + \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \cdot \hat{s}_{\kappa,\xi,t} \ge -\overline{\sigma}_{\xi,t,m} \cdot \Sigma_{m} \qquad \forall\, \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \text{ is defined}
```

### `Transformer-ext-s_nom-lower`

`Transformer_ext_s_nom_lower`

```yaml
Transformer_ext_s_nom_lower:
  description: "`Transformer-ext-s_nom-lower` — the chosen build is at least its floor in every scenario"
  dims: [scenario, transformer]
  where: Transformer_s_nom_extendable AND Transformer_active_asset
  expression: Transformer_s_nom_ext >= Transformer_s_nom_min
```

```math
\Sigma_{m} \ge \underline{\sigma}^{\mathrm{nom}}_{\xi,m} \qquad \forall\, \xi \in \Xi,\ m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{act}^{\sigma}_{m}
```

### `Transformer-ext-s_nom-upper`

`Transformer_ext_s_nom_upper`

```yaml
Transformer_ext_s_nom_upper:
  description: "`Transformer-ext-s_nom-upper` — the chosen build is at most its cap in every scenario. A cap of infinity is no row"
  dims: [scenario, transformer]
  where: Transformer_s_nom_extendable AND Transformer_active_asset AND Transformer_s_nom_max
  expression: Transformer_s_nom_ext <= Transformer_s_nom_max
```

```math
\Sigma_{m} \le \overline{\sigma}^{\mathrm{nom}}_{\xi,m} \qquad \forall\, \xi \in \Xi,\ m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{act}^{\sigma}_{m} \wedge \overline{\sigma}^{\mathrm{nom}}_{\xi,m} \text{ is defined}
```

### `Transformer-ext-s-upper`

`Transformer_ext_s_upper`

```yaml
Transformer_ext_s_upper:
  description: "`Transformer-ext-s-upper` — an extendable transformer carries at most its rating of the chosen build, the loss included"
  dims: [scenario, snapshot, transformer]
  where: Transformer_s_nom_extendable AND Transformer_active
  expression: Transformer_s + Transformer_loss <= Transformer_s_max_pu * Transformer_s_nom_ext
```

```math
\sigma_{\xi,t,m} + \ell^{\sigma}_{\xi,t,m} \le \overline{\sigma}_{\xi,t,m} \cdot \Sigma_{m} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-ext-s-upper-security-for-{c}-outage-in-sub-network-{n}`

`Transformer_ext_s_upper_security`

```yaml
Transformer_ext_s_upper_security:
  description: >-
    `Transformer-ext-s-upper-security-for-{c}-outage-in-sub-network-{n}` —
    after any one outage, an extendable transformer carries at most its
    rating of the chosen build. Its flow takes on its share of the outaged
    branch's flow. PyPSA names one row per outaged component `c` and
    sub-network `n`. Under `multi_investment_periods` it appends
    `-period-{p}` for each period `p`. This entry states them all over the
    outage dimension
  dims: [scenario, snapshot, transformer, outage]
  where: Transformer_s_nom_extendable AND at(Transformer_BODF, by=snapshot_period[period])
  expression: Transformer_s_monitored + at(Transformer_BODF, by=snapshot_period[period]) * Outage_s <= Transformer_s_max_pu * Transformer_s_nom_ext
```

```math
\check{\sigma}_{\xi,t,m} + \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \cdot \hat{s}_{\kappa,\xi,t} \le \overline{\sigma}_{\xi,t,m} \cdot \Sigma_{m} \qquad \forall\, \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \text{ is defined}
```

### `Transformer-fix-s-lower`

`Transformer_fix_s_lower`

```yaml
Transformer_fix_s_lower:
  description: "`Transformer-fix-s-lower` — a fixed transformer carries at least the negative of its rating, the loss counted against it"
  dims: [scenario, snapshot, transformer]
  where: not Transformer_s_nom_extendable AND Transformer_active
  expression: Transformer_s - Transformer_loss >= -Transformer_s_max_pu * Transformer_s_nom
```

```math
\sigma_{\xi,t,m} - \ell^{\sigma}_{\xi,t,m} \ge -\overline{\sigma}_{\xi,t,m} \cdot \sigma^{\mathrm{nom}}_{\xi,m} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \neg \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-fix-s-lower-security-for-{c}-outage-in-sub-network-{n}`

`Transformer_fix_s_lower_security`

```yaml
Transformer_fix_s_lower_security:
  description: >-
    `Transformer-fix-s-lower-security-for-{c}-outage-in-sub-network-{n}` —
    after any one outage, a fixed transformer carries at least the negative
    of its rating. Its flow takes on its share of the outaged branch's flow.
    PyPSA names one row per outaged component `c` and sub-network `n`. Under
    `multi_investment_periods` it appends `-period-{p}` for each period `p`.
    This entry states them all over the outage dimension
  dims: [scenario, snapshot, transformer, outage]
  where: not Transformer_s_nom_extendable AND at(Transformer_BODF, by=snapshot_period[period])
  expression: Transformer_s_monitored + at(Transformer_BODF, by=snapshot_period[period]) * Outage_s >= -Transformer_s_max_pu * Transformer_s_nom
```

```math
\check{\sigma}_{\xi,t,m} + \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \cdot \hat{s}_{\kappa,\xi,t} \ge -\overline{\sigma}_{\xi,t,m} \cdot \sigma^{\mathrm{nom}}_{\xi,m} \qquad \forall\, \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \neg \mathrm{ext}^{\sigma}_{m} \wedge \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \text{ is defined}
```

### `Transformer-fix-s-upper`

`Transformer_fix_s_upper`

```yaml
Transformer_fix_s_upper:
  description: "`Transformer-fix-s-upper` — a fixed transformer carries at most its rating, the loss included"
  dims: [scenario, snapshot, transformer]
  where: not Transformer_s_nom_extendable AND Transformer_active
  expression: Transformer_s + Transformer_loss <= Transformer_s_max_pu * Transformer_s_nom
```

```math
\sigma_{\xi,t,m} + \ell^{\sigma}_{\xi,t,m} \le \overline{\sigma}_{\xi,t,m} \cdot \sigma^{\mathrm{nom}}_{\xi,m} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \neg \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-fix-s-upper-security-for-{c}-outage-in-sub-network-{n}`

`Transformer_fix_s_upper_security`

```yaml
Transformer_fix_s_upper_security:
  description: >-
    `Transformer-fix-s-upper-security-for-{c}-outage-in-sub-network-{n}` —
    after any one outage, a fixed transformer carries at most its rating.
    Its flow takes on its share of the outaged branch's flow. PyPSA names
    one row per outaged component `c` and sub-network `n`. Under
    `multi_investment_periods` it appends `-period-{p}` for each period `p`.
    This entry states them all over the outage dimension
  dims: [scenario, snapshot, transformer, outage]
  where: not Transformer_s_nom_extendable AND at(Transformer_BODF, by=snapshot_period[period])
  expression: Transformer_s_monitored + at(Transformer_BODF, by=snapshot_period[period]) * Outage_s <= Transformer_s_max_pu * Transformer_s_nom
```

```math
\check{\sigma}_{\xi,t,m} + \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \cdot \hat{s}_{\kappa,\xi,t} \le \overline{\sigma}_{\xi,t,m} \cdot \sigma^{\mathrm{nom}}_{\xi,m} \qquad \forall\, \kappa \in \mathcal{K}^{\mathrm{out}},\ \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \neg \mathrm{ext}^{\sigma}_{m} \wedge \beta^{\sigma}_{\kappa,\mathrm{snapshot\_period}(t),m} \text{ is defined}
```

### `Transformer-loss_tangents-{k}-1`

`Transformer_loss_tangents_forward`

```yaml
Transformer_loss_tangents_forward:
  description: >-
    `Transformer-loss_tangents-{k}-1`, `Transformer-loss_secants-pos` — the
    loss sits above every cut to its curve for flow one way, as a line's
    does, over the segment dimension
  dims: [scenario, snapshot, transformer, segment]
  where: Transformer_lossy
  expression: Transformer_loss + Transformer_loss_slope * Transformer_s >= Transformer_loss_offset
```

```math
\ell^{\sigma}_{\xi,t,m} + \mathrm{a}^{\sigma}_{\xi,m,t,m} \cdot \sigma_{\xi,t,m} \ge \mathrm{b}^{\sigma}_{\xi,m,t,m} \qquad \forall\, \xi \in \Xi,\ m \in \mathcal{M},\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{on}^{\sigma,\mathrm{lossy}}_{t,m}
```

### `Transformer-loss_tangents-{k}--1`

`Transformer_loss_tangents_reverse`

```yaml
Transformer_loss_tangents_reverse:
  description: >-
    `Transformer-loss_tangents-{k}--1`, `Transformer-loss_secants-neg` — the
    same fan mirrored, the loss depending on the flow's magnitude
  dims: [scenario, snapshot, transformer, segment]
  where: Transformer_lossy
  expression: Transformer_loss - Transformer_loss_slope * Transformer_s >= Transformer_loss_offset
```

```math
\ell^{\sigma}_{\xi,t,m} - \mathrm{a}^{\sigma}_{\xi,m,t,m} \cdot \sigma_{\xi,t,m} \ge \mathrm{b}^{\sigma}_{\xi,m,t,m} \qquad \forall\, \xi \in \Xi,\ m \in \mathcal{M},\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{on}^{\sigma,\mathrm{lossy}}_{t,m}
```

### `Transformer-loss_upper`

`Transformer_loss_upper`

```yaml
Transformer_loss_upper:
  description: "`Transformer-loss_upper` — a transformer dissipates at most the loss at its rating"
  dims: [scenario, snapshot, transformer]
  where: Transformer_lossy
  expression: Transformer_loss <= Transformer_loss_max
```

```math
\ell^{\sigma}_{\xi,t,m} \le \overline{\ell}^{\sigma}_{\xi,t,m} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \mathrm{on}^{\sigma,\mathrm{lossy}}_{t,m}
```

### `Transformer-s_nom_modularity`

`Transformer_s_nom_modularity`

```yaml
Transformer_s_nom_modularity:
  description: "`Transformer-s_nom_modularity` — the chosen build is a whole number of modules"
  dims: [transformer]
  where: Transformer_s_nom_extendable AND Transformer_s_nom_mod > 0 AND Transformer_active_asset
  expression: Transformer_s_nom_ext == Transformer_s_nom_mod * Transformer_n_mod
```

```math
\Sigma_{m} = \sigma^{\mathrm{mod}}_{m} \cdot N^{\sigma}_{m} \qquad \forall\, m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \sigma^{\mathrm{mod}}_{m} > 0 \wedge \mathrm{act}^{\sigma}_{m}
```

### `Transformer-s_nom_set`

`Transformer_s_nom_set`

```yaml
Transformer_s_nom_set:
  description: "`Transformer-s_nom_set` — the chosen build pinned, wherever a value is given"
  dims: [transformer]
  where: Transformer_s_nom_extendable AND Transformer_active_asset AND Transformer_s_nom_set
  expression: Transformer_s_nom_ext == Transformer_s_nom_set
```

```math
\Sigma_{m} = \sigma^{\mathrm{nom,set}}_{m} \qquad \forall\, m \in \mathcal{M} \,:\, \mathrm{ext}^{\sigma}_{m} \wedge \mathrm{act}^{\sigma}_{m} \wedge \sigma^{\mathrm{nom,set}}_{m} \text{ is defined}
```

### `Transformer-s_set`

`Transformer_s_set`

```yaml
Transformer_s_set:
  description: "`Transformer-s_set` — flow pinned to the given schedule, wherever one is given"
  dims: [scenario, snapshot, transformer]
  where: Transformer_s_set AND Transformer_active
  expression: Transformer_s == Transformer_s_set
```

```math
\sigma_{\xi,t,m} = \sigma^{\mathrm{set}}_{\xi,t,m} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \sigma^{\mathrm{set}}_{\xi,t,m} \text{ is defined} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-v_ang-lower`

`Transformer_v_ang_lower`

```yaml
Transformer_v_ang_lower:
  description: >-
    `Transformer-v_ang-lower` — a transformer with a fixed shift carries at
    least the flow at which the voltage angle difference across it is minus
    its limit. That difference is `x_pu_eff` times the flow plus the shift
  dims: [scenario, snapshot, transformer]
  where: Transformer_v_ang_max AND NOT Transformer_phase_shift_varying AND Transformer_active
  expression: Transformer_s >= -(Transformer_v_ang_max + Transformer_phase_shift_fixed) * (3.141592653589793 / 180) / Transformer_x_pu_eff
```

```math
\sigma_{\xi,t,m} \ge \frac{-\left( \overline{\delta}^{\sigma}_{\xi,m} + \varphi^{\sigma}_{t,m} \right) \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff},\sigma}_{\xi,m}} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \overline{\delta}^{\sigma}_{\xi,m} \text{ is defined} \wedge \neg \mathrm{Transformer\_phase\_shift\_varying}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-v_ang-upper`

`Transformer_v_ang_upper`

```yaml
Transformer_v_ang_upper:
  description: >-
    `Transformer-v_ang-upper` — a transformer with a fixed shift carries at
    most the flow at which the voltage angle difference across it reaches
    its limit. That difference includes the shift
  dims: [scenario, snapshot, transformer]
  where: Transformer_v_ang_max AND NOT Transformer_phase_shift_varying AND Transformer_active
  expression: Transformer_s <= (Transformer_v_ang_max - Transformer_phase_shift_fixed) * (3.141592653589793 / 180) / Transformer_x_pu_eff
```

```math
\sigma_{\xi,t,m} \le \frac{\left( \overline{\delta}^{\sigma}_{\xi,m} - \varphi^{\sigma}_{t,m} \right) \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff},\sigma}_{\xi,m}} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \overline{\delta}^{\sigma}_{\xi,m} \text{ is defined} \wedge \neg \mathrm{Transformer\_phase\_shift\_varying}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-v_ang-var-lower`

`Transformer_v_ang_var_lower`

```yaml
Transformer_v_ang_var_lower:
  description: >-
    `Transformer-v_ang-var-lower` — for a transformer whose shift is a
    decision, the flow plus the shift over `x_pu_eff` is at least minus the
    limit over `x_pu_eff`
  dims: [scenario, snapshot, transformer]
  where: Transformer_v_ang_max AND Transformer_phase_shift_varying AND Transformer_active
  expression: Transformer_s + Transformer_phase_shift * (3.141592653589793 / 180) / Transformer_x_pu_eff >= -Transformer_v_ang_max * (3.141592653589793 / 180) / Transformer_x_pu_eff
```

```math
\sigma_{\xi,t,m} + \frac{\mathit{Transformer\_phase\_shift}_{\xi,t,m} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff},\sigma}_{\xi,m}} \ge \frac{-\overline{\delta}^{\sigma}_{\xi,m} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff},\sigma}_{\xi,m}} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \overline{\delta}^{\sigma}_{\xi,m} \text{ is defined} \wedge \mathrm{Transformer\_phase\_shift\_varying}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Transformer-v_ang-var-upper`

`Transformer_v_ang_var_upper`

```yaml
Transformer_v_ang_var_upper:
  description: >-
    `Transformer-v_ang-var-upper` — for a transformer whose shift is a
    decision, the flow plus the shift over `x_pu_eff` is at most the limit
    over `x_pu_eff`
  dims: [scenario, snapshot, transformer]
  where: Transformer_v_ang_max AND Transformer_phase_shift_varying AND Transformer_active
  expression: Transformer_s + Transformer_phase_shift * (3.141592653589793 / 180) / Transformer_x_pu_eff <= Transformer_v_ang_max * (3.141592653589793 / 180) / Transformer_x_pu_eff
```

```math
\sigma_{\xi,t,m} + \frac{\mathit{Transformer\_phase\_shift}_{\xi,t,m} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff},\sigma}_{\xi,m}} \le \frac{\overline{\delta}^{\sigma}_{\xi,m} \cdot \frac{3.141592653589793}{180}}{\mathrm{x}^{\mathrm{eff},\sigma}_{\xi,m}} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ m \in \mathcal{M} \,:\, \overline{\delta}^{\sigma}_{\xi,m} \text{ is defined} \wedge \mathrm{Transformer\_phase\_shift\_varying}_{m} \wedge \mathrm{on}^{\sigma}_{t,m}
```

### `Generator_marginal_cost_incremental`

```yaml
Generator_marginal_cost_incremental:
  description: >-
    `Generator-marginal_cost_piecewise` — the running cost of a generator
    with a curve is at least the curve at its output, stated by segments
    filled in order and switched by the status of a committable generator,
    where linopy chooses the incremental rows
  along: breakpoint
  dims: [scenario, snapshot, generator]
  where: NOT Generator_marginal_cost_as_lp AND Generator_marginal_cost_curve AND Generator_active AND Generator_marginal_cost_curve_p
  method: incremental
  activity: Generator_status
  links:
    p: [Generator_p, Generator_marginal_cost_curve_p]
    cost: [Generator_marginal_cost_piecewise, Generator_marginal_cost_curve_cost, ">="]
```

```math
C^{\mathrm{curve}}_{g,\xi,t} \ge \left( \begin{cases} u_{g,\xi,t} & \text{if } \mathrm{on}^{\mathrm{com}}_{g,t} \\ 1 & \text{otherwise} \end{cases} \cdot \left( \mathrm{p}^{\mathrm{curve}}_{\min \{ b \in \mathcal{B} \,:\, \neg \mathrm{lp} \wedge \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined} \},g},\ \mathrm{C}^{\mathrm{curve}}_{\min \{ b \in \mathcal{B} \,:\, \neg \mathrm{lp} \wedge \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined} \},g} \right) + \min(\begin{cases} u_{g,\xi,t} & \text{if } \mathrm{on}^{\mathrm{com}}_{g,t} \\ 1 & \text{otherwise} \end{cases},\ 1) \cdot \left( \mathrm{pwl}_{b \in \mathcal{B} \,:\, \neg \mathrm{lp} \wedge \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined}}(\mathrm{p}^{\mathrm{curve}}_{b,g},\ \mathrm{C}^{\mathrm{curve}}_{b,g}) - \left( \mathrm{p}^{\mathrm{curve}}_{\min \{ b \in \mathcal{B} \,:\, \neg \mathrm{lp} \wedge \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined} \},g},\ \mathrm{C}^{\mathrm{curve}}_{\min \{ b \in \mathcal{B} \,:\, \neg \mathrm{lp} \wedge \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined} \},g} \right) \right) \right)(p_{g,\xi,t}) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_marginal_cost_lp`

```yaml
Generator_marginal_cost_lp:
  description: >-
    `Generator-marginal_cost_piecewise` — the running cost of a generator
    with a curve is at least the curve at its output, stated as the line of
    each segment, where linopy chooses the segment lines
  along: breakpoint
  dims: [scenario, snapshot, generator]
  where: Generator_marginal_cost_as_lp AND Generator_marginal_cost_curve AND Generator_active AND Generator_marginal_cost_curve_p
  method: lp
  links:
    p: [Generator_p, Generator_marginal_cost_curve_p]
    cost: [Generator_marginal_cost_piecewise, Generator_marginal_cost_curve_cost, ">="]
```

```math
C^{\mathrm{curve}}_{g,\xi,t} \ge \mathrm{pwl}_{b \in \mathcal{B} \,:\, \mathrm{lp} \wedge \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined}}(\mathrm{p}^{\mathrm{curve}}_{b,g},\ \mathrm{C}^{\mathrm{curve}}_{b,g})(p_{g,\xi,t}) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_big_m_where_committed_and_extendable`

```yaml
Generator_big_m_where_committed_and_extendable:
  holds: "Generator_big_m"
  where: "Generator_com_ext"
  description: >-
    a committable generator with an extendable, non-modular build has
    the big-M its rows release it by — PyPSA computes one for each
    (`get_committable_big_m_values`)
```

```math
\mathrm{M}_{g,\xi} \text{ is defined} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t}
```

### `Generator_maintenance_build_cap_is_finite`

```yaml
Generator_maintenance_build_cap_is_finite:
  holds: "Generator_p_nom_max < inf"
  where: "Generator_maintainable AND Generator_p_nom_extendable"
  description: >-
    the `maintcap` rows bound the chosen build in maintenance by
    `p_nom_max`, so an infinite cap is an infinite coefficient. PyPSA
    refuses it (`consistency.py:1576`)
```

```math
\overline{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} < \infty \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{mnt}_{g} \wedge \mathrm{ext}_{g}
```

### `Generator_maintenance_duration_fits_the_horizon`

```yaml
Generator_maintenance_duration_fits_the_horizon:
  holds: "Generator_maintenance_duration <= sum(snapshot_weightings_generators, over=snapshot)"
  where: "Generator_maintainable"
  description: >-
    one event longer than the horizon, in generator weightings, blocks every
    start and makes the event count infeasible. PyPSA refuses it
    (`consistency.py:1552`)
```

```math
\tau^{\mathrm{mnt}}_{g,\xi} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{mnt}_{g}
```

### `Generator_maintenance_duration_positive`

```yaml
Generator_maintenance_duration_positive:
  holds: "Generator_maintenance_duration > 0"
  where: "Generator_maintainable"
  description: >-
    an event that covers no hours is no maintenance window. PyPSA refuses it
    (`consistency.py:1531`)
```

```math
\tau^{\mathrm{mnt}}_{g,\xi} > 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{mnt}_{g}
```

### `Generator_maintenance_events_fit_the_horizon`

```yaml
Generator_maintenance_events_fit_the_horizon:
  holds: "Generator_maintenance_duration * Generator_maintenance_events <= sum(snapshot_weightings_generators, over=snapshot)"
  where: "Generator_maintainable"
  description: >-
    the events together longer than the horizon, in generator weightings,
    cannot all be scheduled. PyPSA refuses it (`consistency.py:1564`)
```

```math
\tau^{\mathrm{mnt}}_{g,\xi} \cdot \mathrm{n}^{\mathrm{mnt}}_{g,\xi} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{mnt}_{g}
```

### `Generator_maintenance_events_positive`

```yaml
Generator_maintenance_events_positive:
  holds: "Generator_maintenance_events > 0"
  where: "Generator_maintainable"
  description: >-
    a maintainable generator with no event schedules no maintenance. PyPSA
    refuses it (`consistency.py:1541`)
```

```math
\mathrm{n}^{\mathrm{mnt}}_{g,\xi} > 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{mnt}_{g}
```

### `Generator_marginal_cost_curve_on_a_fixed_build`

```yaml
Generator_marginal_cost_curve_on_a_fixed_build:
  holds: "NOT Generator_p_nom_extendable AND Generator_p_nom > 0 AND Generator_p_nom < inf"
  where: "Generator_marginal_cost_curve"
  description: >-
    a generator's cost curve is given per unit of a fixed, positive, finite
    `p_nom`, which scales it to output. PyPSA refuses an extendable unit and
    a zero, missing or infinite `p_nom` (`piecewise.py:277-297`), and takes
    a negative one, which the file does not state
```

```math
\neg \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{nom}}_{g,\xi} > 0 \wedge \mathrm{p}^{\mathrm{nom}}_{g,\xi} < \infty \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi \,:\, \mathrm{curve}_{g}
```

### `Generator_marginal_cost_quadratic_without_risk_preference`

```yaml
Generator_marginal_cost_quadratic_without_risk_preference:
  holds: "Generator_marginal_cost_quadratic == 0"
  where: "CVaR_omega"
  description: >-
    a quadratic cost puts a square into every `CVaR-excess` row. PyPSA
    refuses quadratic costs under any risk preference, `omega = 0` included
    (`optimize.py:506-513`). In data prep you write a `CVaR_omega` row only
    where a risk preference is set
```

```math
\mathrm{c}^{(2)}_{g,\xi,t} = 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \omega \text{ is defined}
```

### `GlobalConstraint_flow_based_sense_is_le`

```yaml
GlobalConstraint_flow_based_sense_is_le:
  holds: "GlobalConstraint_sense == '<='"
  where: "GlobalConstraint_type == 'flow_based'"
  description: >-
    PyPSA refuses a `flow_based` row whose sense is not `<=`
    (`flow_based.py:109-114`)
```

```math
\mathrm{sense}_{o,\xi} = \text{'}\mathrm{<=}\text{'} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi \,:\, \mathrm{type}_{o} = \text{'}\mathrm{flow\_based}\text{'}
```

### `GlobalConstraint_tech_capacity_expansion_limit_without_scenarios`

```yaml
GlobalConstraint_tech_capacity_expansion_limit_without_scenarios:
  holds: "GlobalConstraint_type != 'tech_capacity_expansion_limit'"
  where: "count(scenario_weight, over=scenario) > 1"
  description: >-
    PyPSA does not build a `tech_capacity_expansion_limit` row on a network
    with scenarios and refuses it (`global_constraints.py:68-70`). The spec
    cannot tell a network with one scenario from one with none. A tool thus
    refuses the row only where there is more than one scenario
```

```math
\mathrm{type}_{o} \neq \text{'}\mathrm{tech\_capacity\_expansion\_limit}\text{'} \qquad \forall\, o \in \mathcal{O} \,:\, \lvert \{ \xi \in \Xi \,:\, \pi_{\xi} \text{ is defined} \} \rvert > 1
```

### `Link_big_m_where_committed_and_extendable`

```yaml
Link_big_m_where_committed_and_extendable:
  holds: "Link_big_m"
  where: "Link_com_ext"
  description: >-
    a committable link with an extendable, non-modular build has
    the big-M its rows release it by — PyPSA computes one for each
    (`get_committable_big_m_values`)
```

```math
\mathrm{M}^{f}_{l,\xi} \text{ is defined} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```

### `Link_maintenance_build_cap_is_finite`

```yaml
Link_maintenance_build_cap_is_finite:
  holds: "Link_p_nom_max < inf"
  where: "Link_maintainable AND Link_p_nom_extendable"
  description: >-
    the `maintcap` rows bound the chosen build in maintenance by
    `p_nom_max`, so an infinite cap is an infinite coefficient. PyPSA
    refuses it (`consistency.py:1576`)
```

```math
\overline{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} < \infty \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{mnt}^{f}_{l} \wedge \mathrm{ext}^{f}_{l}
```

### `Link_maintenance_duration_fits_the_horizon`

```yaml
Link_maintenance_duration_fits_the_horizon:
  holds: "Link_maintenance_duration <= sum(snapshot_weightings_generators, over=snapshot)"
  where: "Link_maintainable"
  description: >-
    one event longer than the horizon, in generator weightings, blocks every
    start and makes the event count infeasible. PyPSA refuses it
    (`consistency.py:1552`)
```

```math
\tau^{f,\mathrm{mnt}}_{l,\xi} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{mnt}^{f}_{l}
```

### `Link_maintenance_duration_positive`

```yaml
Link_maintenance_duration_positive:
  holds: "Link_maintenance_duration > 0"
  where: "Link_maintainable"
  description: >-
    an event that covers no hours is no maintenance window. PyPSA refuses it
    (`consistency.py:1531`)
```

```math
\tau^{f,\mathrm{mnt}}_{l,\xi} > 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{mnt}^{f}_{l}
```

### `Link_maintenance_events_fit_the_horizon`

```yaml
Link_maintenance_events_fit_the_horizon:
  holds: "Link_maintenance_duration * Link_maintenance_events <= sum(snapshot_weightings_generators, over=snapshot)"
  where: "Link_maintainable"
  description: >-
    the events together longer than the horizon, in generator weightings,
    cannot all be scheduled. PyPSA refuses it (`consistency.py:1564`)
```

```math
\tau^{f,\mathrm{mnt}}_{l,\xi} \cdot \mathrm{n}^{f,\mathrm{mnt}}_{l,\xi} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{mnt}^{f}_{l}
```

### `Link_maintenance_events_positive`

```yaml
Link_maintenance_events_positive:
  holds: "Link_maintenance_events > 0"
  where: "Link_maintainable"
  description: >-
    a maintainable link with no event schedules no maintenance. PyPSA
    refuses it (`consistency.py:1541`)
```

```math
\mathrm{n}^{f,\mathrm{mnt}}_{l,\xi} > 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi \,:\, \mathrm{mnt}^{f}_{l}
```

### `Link_marginal_cost_quadratic_without_risk_preference`

```yaml
Link_marginal_cost_quadratic_without_risk_preference:
  holds: "Link_marginal_cost_quadratic == 0"
  where: "CVaR_omega"
  description: >-
    a quadratic cost puts a square into every `CVaR-excess` row. PyPSA
    refuses quadratic costs under any risk preference, `omega = 0` included
    (`optimize.py:506-513`). In data prep you write a `CVaR_omega` row only
    where a risk preference is set
```

```math
\mathrm{c}^{f,(2)}_{l,\xi,t} = 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \omega \text{ is defined}
```

### `Link_output_delay_under_uniform_weighting`

```yaml
Link_output_delay_under_uniform_weighting:
  holds: "snapshot_weightings_generators == shift(snapshot_weightings_generators, along=snapshot, offset=1, edge='wrap')"
  where: "Link_output_delay > 0"
  description: >-
    a delayed port lags by the same whole number of snapshots in every
    period. PyPSA lags by elapsed time in `generators` weighting and rounds
    the source down to a snapshot start (`multiports.py:100-133`). The two
    agree only where that weighting is one value over the horizon. PyPSA
    does not refuse an uneven weighting, so a tool refuses it through this
    assumption when data is attached (#299)
```

```math
\mathrm{w}^{\mathrm{gen}}_{t} = \mathrm{w}^{\mathrm{gen}}_{t \ominus 1} \qquad \forall\, o \in \mathcal{O},\ t \in \mathcal{T} \,:\, \mathrm{d}^{f}_{o} > 0
```

### `Process_big_m_where_committed_and_extendable`

```yaml
Process_big_m_where_committed_and_extendable:
  holds: "Process_big_m"
  where: "Process_com_ext"
  description: >-
    a committable process with an extendable, non-modular build has
    the big-M its rows release it by — PyPSA computes one for each
    (`get_committable_big_m_values`)
```

```math
\mathrm{M}^{z}_{j,\xi} \text{ is defined} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t}
```

### `Process_maintenance_build_cap_is_finite`

```yaml
Process_maintenance_build_cap_is_finite:
  holds: "Process_p_nom_max < inf"
  where: "Process_maintainable AND Process_p_nom_extendable"
  description: >-
    the `maintcap` rows bound the chosen build in maintenance by
    `p_nom_max`, so an infinite cap is an infinite coefficient. PyPSA
    refuses it (`consistency.py:1576`)
```

```math
\overline{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} < \infty \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{mnt}^{z}_{j} \wedge \mathrm{ext}^{z}_{j}
```

### `Process_maintenance_duration_fits_the_horizon`

```yaml
Process_maintenance_duration_fits_the_horizon:
  holds: "Process_maintenance_duration <= sum(snapshot_weightings_generators, over=snapshot)"
  where: "Process_maintainable"
  description: >-
    one event longer than the horizon, in generator weightings, blocks every
    start and makes the event count infeasible. PyPSA refuses it
    (`consistency.py:1552`)
```

```math
\tau^{z,\mathrm{mnt}}_{j,\xi} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{mnt}^{z}_{j}
```

### `Process_maintenance_duration_positive`

```yaml
Process_maintenance_duration_positive:
  holds: "Process_maintenance_duration > 0"
  where: "Process_maintainable"
  description: >-
    an event that covers no hours is no maintenance window. PyPSA refuses it
    (`consistency.py:1531`)
```

```math
\tau^{z,\mathrm{mnt}}_{j,\xi} > 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{mnt}^{z}_{j}
```

### `Process_maintenance_events_fit_the_horizon`

```yaml
Process_maintenance_events_fit_the_horizon:
  holds: "Process_maintenance_duration * Process_maintenance_events <= sum(snapshot_weightings_generators, over=snapshot)"
  where: "Process_maintainable"
  description: >-
    the events together longer than the horizon, in generator weightings,
    cannot all be scheduled. PyPSA refuses it (`consistency.py:1564`)
```

```math
\tau^{z,\mathrm{mnt}}_{j,\xi} \cdot \mathrm{n}^{z,\mathrm{mnt}}_{j,\xi} \le \sum_{t \in \mathcal{T}} \mathrm{w}^{\mathrm{gen}}_{t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{mnt}^{z}_{j}
```

### `Process_maintenance_events_positive`

```yaml
Process_maintenance_events_positive:
  holds: "Process_maintenance_events > 0"
  where: "Process_maintainable"
  description: >-
    a maintainable process with no event schedules no maintenance. PyPSA
    refuses it (`consistency.py:1541`)
```

```math
\mathrm{n}^{z,\mathrm{mnt}}_{j,\xi} > 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi \,:\, \mathrm{mnt}^{z}_{j}
```

### `Process_marginal_cost_quadratic_without_risk_preference`

```yaml
Process_marginal_cost_quadratic_without_risk_preference:
  holds: "Process_marginal_cost_quadratic == 0"
  where: "CVaR_omega"
  description: >-
    a quadratic cost puts a square into every `CVaR-excess` row. PyPSA
    refuses quadratic costs under any risk preference, `omega = 0` included
    (`optimize.py:506-513`). In data prep you write a `CVaR_omega` row only
    where a risk preference is set
```

```math
\mathrm{c}^{z,(2)}_{j,\xi,t} = 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \omega \text{ is defined}
```

### `Process_output_delay_under_uniform_weighting`

```yaml
Process_output_delay_under_uniform_weighting:
  holds: "snapshot_weightings_generators == shift(snapshot_weightings_generators, along=snapshot, offset=1, edge='wrap')"
  where: "Process_output_delay > 0"
  description: >-
    the same for a delayed process port (#299)
```

```math
\mathrm{w}^{\mathrm{gen}}_{t} = \mathrm{w}^{\mathrm{gen}}_{t \ominus 1} \qquad \forall\, r \in \mathcal{R},\ t \in \mathcal{T} \,:\, \mathrm{d}^{z}_{r} > 0
```

### `StorageUnit_marginal_cost_quadratic_without_risk_preference`

```yaml
StorageUnit_marginal_cost_quadratic_without_risk_preference:
  holds: "StorageUnit_marginal_cost_quadratic == 0"
  where: "CVaR_omega"
  description: >-
    a quadratic cost puts a square into every `CVaR-excess` row. PyPSA
    refuses quadratic costs under any risk preference, `omega = 0` included
    (`optimize.py:506-513`). In data prep you write a `CVaR_omega` row only
    where a risk preference is set
```

```math
\mathrm{c}^{h,(2)}_{\xi,t,s} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \omega \text{ is defined}
```

### `StorageUnit_opens_late_only_where_it_opens`

```yaml
StorageUnit_opens_late_only_where_it_opens:
  holds: "StorageUnit_active AND NOT shift(StorageUnit_active, along=snapshot, offset=1) AND position(snapshot) > 0"
  where: "StorageUnit_opens_late"
  description: >-
    `StorageUnit_opens_late` marks the first snapshot the storage unit is active in, past
    the first of the horizon, and no other
```

```math
\mathrm{on}^{h}_{t,s} \wedge \neg \mathrm{on}^{h}_{t - 1,s} \wedge \mathrm{pos}(t) > 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{open}_{t,s}
```

### `StorageUnit_opens_late_where_it_opens`

```yaml
StorageUnit_opens_late_where_it_opens:
  holds: "StorageUnit_opens_late"
  where: "StorageUnit_active AND NOT shift(StorageUnit_active, along=snapshot, offset=1) AND position(snapshot) > 0"
  description: >-
    a storage unit that opens past the first snapshot of the horizon opens
    on its initial level, or its last level where it is cyclic. This holds
    only where `StorageUnit_opens_late` is true at the snapshot
```

```math
\mathrm{open}_{t,s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{on}^{h}_{t,s} \wedge \neg \mathrm{on}^{h}_{t - 1,s} \wedge \mathrm{pos}(t) > 0
```

### `StorageUnit_operational_limit_carried_over_has_unit_years`

```yaml
StorageUnit_operational_limit_carried_over_has_unit_years:
  holds: "at(period_weight_years == 1, by=snapshot_period[period])"
  where: "StorageUnit_operational_limit_weight AND NOT StorageUnit_state_of_charge_initial_per_period AND GlobalConstraint_counts_snapshot"
  description: >-
    the same for an `operational_limit` row, over the periods it counts.
    PyPSA refuses it (`global_constraints.py:670`)
```

```math
\mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} = 1 \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{b}^{h}_{o,\xi,s} \text{ is defined} \wedge \neg \mathrm{reset}_{\xi,s} \wedge \mathrm{in}_{o,\xi,t}
```

### `StorageUnit_operational_limit_per_period_without_scenarios`

```yaml
StorageUnit_operational_limit_per_period_without_scenarios:
  holds: "NOT StorageUnit_state_of_charge_initial_per_period"
  where: "StorageUnit_operational_limit_weight AND count(scenario_weight, over=scenario) > 1"
  description: >-
    the same for an `operational_limit` row, which fails the same way
    (`global_constraints.py:696`, PyPSA/PyPSA#2113)
```

```math
\neg \mathrm{reset}_{\xi,s} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ s \in \mathcal{S} \,:\, \mathrm{b}^{h}_{o,\xi,s} \text{ is defined} \wedge \lvert \{ \xi' \in \Xi \,:\, \pi_{\xi'} \text{ is defined} \} \rvert > 1
```

### `StorageUnit_primary_energy_carried_over_has_unit_years`

```yaml
StorageUnit_primary_energy_carried_over_has_unit_years:
  holds: "period_weight_years == 1"
  where: "StorageUnit_primary_energy_weight AND NOT StorageUnit_state_of_charge_initial_per_period"
  description: >-
    a unit that carries its charge from one period to the next closes once,
    at the last counted snapshot. No period's years weighs that level. PyPSA
    refuses it where any period's years is not one
    (`global_constraints.py:464`)
```

```math
\mathrm{w}^{\mathrm{yr}}_{y} = 1 \qquad \forall\, o \in \mathcal{O},\ y \in \mathcal{Y},\ \xi \in \Xi,\ s \in \mathcal{S} \,:\, \mathrm{a}^{h}_{o,\xi,s} \text{ is defined} \wedge \neg \mathrm{reset}_{\xi,s}
```

### `StorageUnit_primary_energy_per_period_without_scenarios`

```yaml
StorageUnit_primary_energy_per_period_without_scenarios:
  holds: "NOT StorageUnit_state_of_charge_initial_per_period"
  where: "StorageUnit_primary_energy_weight AND count(scenario_weight, over=scenario) > 1"
  description: >-
    PyPSA reads the closing charge of a unit that reopens per period by
    snapshot alone, and fails on a network with scenarios
    (`global_constraints.py:490`, PyPSA/PyPSA#2113). It fails with or without
    an `investment_period`. A tool refuses the unit only where there is
    more than one scenario, since the spec cannot tell one scenario from
    none
```

```math
\neg \mathrm{reset}_{\xi,s} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ s \in \mathcal{S} \,:\, \mathrm{a}^{h}_{o,\xi,s} \text{ is defined} \wedge \lvert \{ \xi' \in \Xi \,:\, \pi_{\xi'} \text{ is defined} \} \rvert > 1
```

### `StorageUnit_stands_in_one_run`

```yaml
StorageUnit_stands_in_one_run:
  holds: "count(StorageUnit_active AND NOT shift(StorageUnit_active, along=snapshot, offset=1), over=snapshot) <= 1"
  description: >-
    the snapshots a storage unit is active in are one unbroken run, as a build
    year and a lifetime make them. The opening row holds at the first
    of them only, and a cyclic storage unit reaches back
    `StorageUnit_inactive_snapshots` further to the last of them
```

```math
\lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{h}_{t,s} \wedge \neg \mathrm{on}^{h}_{t - 1,s} \} \rvert \le 1 \qquad \forall\, s \in \mathcal{S}
```

### `Store_marginal_cost_quadratic_without_risk_preference`

```yaml
Store_marginal_cost_quadratic_without_risk_preference:
  holds: "Store_marginal_cost_quadratic == 0"
  where: "CVaR_omega"
  description: >-
    a quadratic cost puts a square into every `CVaR-excess` row. PyPSA
    refuses quadratic costs under any risk preference, `omega = 0` included
    (`optimize.py:506-513`). In data prep you write a `CVaR_omega` row only
    where a risk preference is set
```

```math
\mathrm{c}^{q,(2)}_{\xi,t,v} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \omega \text{ is defined}
```

### `Store_opens_late_only_where_it_opens`

```yaml
Store_opens_late_only_where_it_opens:
  holds: "Store_active AND NOT shift(Store_active, along=snapshot, offset=1) AND position(snapshot) > 0"
  where: "Store_opens_late"
  description: >-
    `Store_opens_late` marks the first snapshot the store is active in, past
    the first of the horizon, and no other
```

```math
\mathrm{on}^{e}_{t,v} \wedge \neg \mathrm{on}^{e}_{t - 1,v} \wedge \mathrm{pos}(t) > 0 \qquad \forall\, t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{open}^{e}_{t,v}
```

### `Store_opens_late_where_it_opens`

```yaml
Store_opens_late_where_it_opens:
  holds: "Store_opens_late"
  where: "Store_active AND NOT shift(Store_active, along=snapshot, offset=1) AND position(snapshot) > 0"
  description: >-
    a store that opens past the first snapshot of the horizon opens on its
    initial level, or its last level where it is cyclic. This holds only
    where `Store_opens_late` is true at the snapshot
```

```math
\mathrm{open}^{e}_{t,v} \qquad \forall\, t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{on}^{e}_{t,v} \wedge \neg \mathrm{on}^{e}_{t - 1,v} \wedge \mathrm{pos}(t) > 0
```

### `Store_operational_limit_carried_over_has_unit_years`

```yaml
Store_operational_limit_carried_over_has_unit_years:
  holds: "at(period_weight_years == 1, by=snapshot_period[period])"
  where: "Store_operational_limit_weight AND NOT Store_e_initial_per_period AND GlobalConstraint_counts_snapshot"
  description: >-
    the same for an `operational_limit` row, over the periods it counts.
    PyPSA refuses it (`global_constraints.py:718`)
```

```math
\mathrm{w}^{\mathrm{yr}}_{\mathrm{snapshot\_period}(t)} = 1 \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ t \in \mathcal{T},\ v \in \mathcal{V} \,:\, \mathrm{b}^{e}_{o,\xi,v} \text{ is defined} \wedge \neg \mathrm{reset}^{e}_{\xi,v} \wedge \mathrm{in}_{o,\xi,t}
```

### `Store_operational_limit_per_period_without_scenarios`

```yaml
Store_operational_limit_per_period_without_scenarios:
  holds: "NOT Store_e_initial_per_period"
  where: "Store_operational_limit_weight AND count(scenario_weight, over=scenario) > 1"
  description: >-
    the same for an `operational_limit` row, which fails the same way
    (`global_constraints.py:741`, PyPSA/PyPSA#2113)
```

```math
\neg \mathrm{reset}^{e}_{\xi,v} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{b}^{e}_{o,\xi,v} \text{ is defined} \wedge \lvert \{ \xi' \in \Xi \,:\, \pi_{\xi'} \text{ is defined} \} \rvert > 1
```

### `Store_primary_energy_carried_over_has_unit_years`

```yaml
Store_primary_energy_carried_over_has_unit_years:
  holds: "period_weight_years == 1"
  where: "Store_primary_energy_weight AND NOT Store_e_initial_per_period"
  description: >-
    a store that carries its energy from one period to the next closes once,
    at the last counted snapshot. No period's years weighs that level. PyPSA
    refuses it where any period's years is not one
    (`global_constraints.py:516`)
```

```math
\mathrm{w}^{\mathrm{yr}}_{y} = 1 \qquad \forall\, o \in \mathcal{O},\ y \in \mathcal{Y},\ \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{a}^{e}_{o,\xi,v} \text{ is defined} \wedge \neg \mathrm{reset}^{e}_{\xi,v}
```

### `Store_primary_energy_per_period_without_scenarios`

```yaml
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
```

```math
\neg \mathrm{reset}^{e}_{\xi,v} \qquad \forall\, o \in \mathcal{O},\ \xi \in \Xi,\ v \in \mathcal{V} \,:\, \mathrm{a}^{e}_{o,\xi,v} \text{ is defined} \wedge \lvert \{ \xi' \in \Xi \,:\, \pi_{\xi'} \text{ is defined} \} \rvert > 1
```

### `Store_stands_in_one_run`

```yaml
Store_stands_in_one_run:
  holds: "count(Store_active AND NOT shift(Store_active, along=snapshot, offset=1), over=snapshot) <= 1"
  description: >-
    the snapshots a store is active in are one unbroken run, as a build
    year and a lifetime make them. The opening row holds at the first
    of them only, and a cyclic store reaches back
    `Store_inactive_snapshots` further to the last of them
```

```math
\lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{e}_{t,v} \wedge \neg \mathrm{on}^{e}_{t - 1,v} \} \rvert \le 1 \qquad \forall\, v \in \mathcal{V}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](pypsa/index.md), for the same spec split into one file
      per component
    - [PyPSA, the relaxed commitment](pypsa_linearized_uc.md), for the patch that
      relaxes the commitment rows
    - [Composition](../reference/composition.md), for the `merge` and `override`
      calls that combine files
    - [Assumptions](../reference/language/assumptions.md), for the checks a tool
      runs when it attaches data
