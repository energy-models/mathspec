<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Generator ramping

This file states the ramping rows of PyPSA's `Generator`. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. `Generator_previous_p` is the output carried into each snapshot, from `p_init` at the first where the unit came in running. `Generator_ramp_up_allowance` adds the start-up ramp in the snapshot the unit turns on.

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Generator_p_nom_extendable: { dims: [generator], dtype: bool }
    Generator_committable: { dims: [generator], dtype: bool }
    Generator_status_initial: { dims: [scenario, generator] }
    Generator_p_nom_mod: { dims: [generator] }
    Generator_modules_installed: { dims: [scenario, generator] }
    Generator_big_m: { dims: [scenario, generator] }
    Generator_active: { dims: [snapshot, generator], dtype: bool }
  variables:
    Generator_p: { dims: [scenario, snapshot, generator] }
    Generator_status: { dims: [scenario, snapshot, generator], domain: integer }
    Generator_start_up: { dims: [scenario, snapshot, generator], domain: integer }
    Generator_shut_down: { dims: [scenario, snapshot, generator], domain: integer }
    Generator_p_nom_ext: { dims: [generator] }
  expressions:
    Generator_previous_status: { dims: [generator, scenario, snapshot] }
    Generator_p_nom_effective: { dims: [generator, scenario] }
    Generator_p_nom_committed: { dims: [generator, scenario] }
  conditions:
    Generator_com_ext: { dims: [generator, snapshot] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  generator:
    description: generating units, each on one bus
  period:
    description: investment periods. It is PyPSA's `investment_periods`
    dtype: int
    ordered: true

relations:
  snapshot_period:
    description: the investment period a snapshot falls in
    key: snapshot
    values: period

parameters:
  Generator_ramp_limit_up:
    description: most a generator may raise its output between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time
    dims: [scenario, snapshot, generator]
    missing: absent
  Generator_ramp_limit_down:
    description: most a generator may lower its output between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time
    dims: [scenario, snapshot, generator]
    missing: absent
  Generator_ramp_limit_start_up:
    description: most output in the snapshot a unit starts, per unit of nominal power. No value means no limit
    dims: [scenario, generator]
    missing: absent
  Generator_ramp_limit_shut_down:
    description: most output in the snapshot before a unit stops, per unit of nominal power. No value means no limit
    dims: [scenario, generator]
    missing: absent
  Generator_p_init:
    description: >-
      the output a unit brought into the horizon, data prep. It is PyPSA's
      `p_init` where the unit came in running, and zero where it came in off.
      Under a rolling horizon, it is the output the previous window solved. No
      value means it is unknown, and the unit then has no ramp row at the
      first snapshot
    dims: [scenario, generator]
    missing: 0

expressions:
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
  Generator_p_carried_over:
    description: >-
      the output a generator carries over into a snapshot. At the first, it is
      the `p_init` it brought in, which is zero where it came in off. After
      that, it is the previous snapshot's
    dims: [scenario, snapshot, generator]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Generator_p_init }
    otherwise: shift(Generator_p, along=snapshot, offset=1)
  Generator_ramp_up_rate:
    description: >-
      the ramp limit in a unit's up row, PyPSA's `ramp_limit_up`. It is the
      full build where PyPSA has none, since a start-up ramp alone builds the
      row
    dims: [scenario, snapshot, generator]
    cases:
      given: { when: Generator_ramp_limit_up, expression: Generator_ramp_limit_up }
    otherwise: 1
  Generator_ramp_down_rate:
    description: >-
      the ramp limit in a unit's down row, PyPSA's `ramp_limit_down`. It is
      the full build where PyPSA has none, since a shut-down ramp alone builds
      the row
    dims: [scenario, snapshot, generator]
    cases:
      given: { when: Generator_ramp_limit_down, expression: Generator_ramp_limit_down }
    otherwise: 1
  Generator_start_up_rate:
    description: >-
      the start-up ramp in a unit's up row (PyPSA's `ramp_limit_start_up`), or
      the full build where it has none
    dims: [scenario, generator]
    cases:
      given: { when: Generator_ramp_limit_start_up, expression: Generator_ramp_limit_start_up }
    otherwise: 1
  Generator_shut_down_rate:
    description: >-
      the shut-down ramp in a unit's down row (PyPSA's
      `ramp_limit_shut_down`), or the full build where it has none
    dims: [scenario, generator]
    cases:
      given: { when: Generator_ramp_limit_shut_down, expression: Generator_ramp_limit_shut_down }
    otherwise: 1
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

conditions:
  Generator_ramps_from_previous:
    description: >-
      a snapshot whose ramp uses a previous output. It is any snapshot but its
      period's first, and the horizon's first where the generator comes in off
      or carries an initial output
    condition: >-
      position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
      (Generator_status_initial == 0 OR Generator_p_init))

constraints:
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
      Generator_p - Generator_previous_p >=
      -Generator_ramp_down_rate * Generator_p_nom_ext
      - Generator_big_m + Generator_big_m * Generator_status
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

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}`$ | `Generator_active` over $`\mathcal{G} \times \mathcal{T}`$, data another file declares |
| $`\mathrm{M}`$ | `Generator_big_m` over $`\mathcal{G} \times \Xi`$, data another file declares |
| $`\mathrm{com}`$ | `Generator_committable` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{N}^{\mathrm{fix}}`$ | `Generator_modules_installed` over $`\mathcal{G} \times \Xi`$, data another file declares |
| $`\mathrm{ext}`$ | `Generator_p_nom_extendable` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{p}^{\mathrm{mod}}`$ | `Generator_p_nom_mod` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{u}^{0}`$ | `Generator_status_initial` over $`\mathcal{G} \times \Xi`$, data another file declares |
| $`p`$ | `Generator_p` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ |
| $`P`$ | `Generator_p_nom_ext` over $`\mathcal{G}`$ |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{up}`$ | `Generator_start_up` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ |
| $`u`$ | `Generator_status` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ |
| $`\widehat{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_committed` over $`\mathcal{G} \times \Xi`$, an expression another file defines |
| $`\widetilde{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_effective` over $`\mathcal{G} \times \Xi`$, an expression another file defines |
| $`\overleftarrow{u}`$ | `Generator_previous_status` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, an expression another file defines |
| $`\mathrm{on}^{\mathrm{com,ext}}`$ | `Generator_com_ext` over $`\mathcal{G} \times \mathcal{T}`$, a condition another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units, each on one bus |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods. It is PyPSA's `investment_periods` |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{p}^{0}`$ | `Generator_p_init` over $`\mathcal{G} \times \Xi`$, $`0`$ where the data has no row — the output a unit brought into the horizon, data prep. It is PyPSA's `p_init` where the unit came in running, and zero where it came in off. Under a rolling horizon, it is the output the previous window solved. No value means it is unknown, and the unit then has no ramp row at the first snapshot |
| $`\mathrm{rd}`$ | `Generator_ramp_limit_down` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a generator may lower its output between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{rd}^{\mathrm{dn}}`$ | `Generator_ramp_limit_shut_down` over $`\mathcal{G} \times \Xi`$, `absent` where the data has no row — most output in the snapshot before a unit stops, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{\mathrm{up}}`$ | `Generator_ramp_limit_start_up` over $`\mathcal{G} \times \Xi`$, `absent` where the data has no row — most output in the snapshot a unit starts, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}`$ | `Generator_ramp_limit_up` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a generator may raise its output between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{prev}`$ | `Generator_ramps_from_previous` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — a snapshot whose ramp uses a previous output. It is any snapshot but its period's first, and the horizon's first where the generator comes in off or carries an initial output |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{p}^{\circ}`$ | `Generator_p_carried_over` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the output a generator carries over into a snapshot. At the first, it is the `p_init` it brought in, which is zero where it came in off. After that, it is the previous snapshot's |
| $`\overleftarrow{p}`$ | `Generator_previous_p` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the output a generator carries into a snapshot. It is nothing at the first snapshot it is active in past the first of the horizon: PyPSA fills an output it did not build with zero (`constraints.py:716`). It is the output carried over otherwise |
| $`\Delta^{-}`$ | `Generator_ramp_down_allowance` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — how far a generator may lower output between two snapshots. It is its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\widetilde{\mathrm{rd}}`$ | `Generator_ramp_down_rate` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the ramp limit in a unit's down row, PyPSA's `ramp_limit_down`. It is the full build where PyPSA has none, since a shut-down ramp alone builds the row |
| $`\overleftarrow{\bar u}`$ | `Generator_ramp_previous_status` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the status a committed unit's ramp rows carry into a snapshot. At the first snapshot, a fixed modular unit that came in running has every module on, since the state it brought in is on or off (`constraints.py:1152-1157`). The transition and down-time rows count it as one module (PyPSA/PyPSA\#2114). It is the state carried in otherwise |
| $`\Delta^{+}`$ | `Generator_ramp_up_allowance` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — how far a generator may raise output between two snapshots. It is its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\widetilde{\mathrm{ru}}`$ | `Generator_ramp_up_rate` over $`\mathcal{G} \times \Xi \times \mathcal{T}`$ — the ramp limit in a unit's up row, PyPSA's `ramp_limit_up`. It is the full build where PyPSA has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}^{\mathrm{dn}}`$ | `Generator_shut_down_rate` over $`\mathcal{G} \times \Xi`$ — the shut-down ramp in a unit's down row (PyPSA's `ramp_limit_shut_down`), or the full build where it has none |
| $`\widetilde{\mathrm{ru}}^{\mathrm{up}}`$ | `Generator_start_up_rate` over $`\mathcal{G} \times \Xi`$ — the start-up ramp in a unit's up row (PyPSA's `ramp_limit_start_up`), or the full build where it has none |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |

#### Conditions

**`Generator_ramps_from_previous`**

```math
\mathrm{prev}_{g,\xi,t} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{0}_{g,\xi} = 0 \vee \mathrm{p}^{0}_{g,\xi} \text{ is defined} \right) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

#### Definitions

**`Generator_p_carried_over`**

```math
\overleftarrow{p}^{\circ}_{g,\xi,t} = \begin{cases} \mathrm{p}^{0}_{g,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ p_{g,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Generator_previous_p`**

```math
\overleftarrow{p}_{g,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}_{g,t - 1} \\ \overleftarrow{p}^{\circ}_{g,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Generator_ramp_down_allowance`**

```math
\Delta^{-}_{g,\xi,t} = \begin{cases} \widetilde{\mathrm{rd}}_{g,\xi,t} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot u_{g,\xi,t} + \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \left( \overleftarrow{\bar u}_{g,\xi,t} - u_{g,\xi,t} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{rd}}_{g,\xi,t} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Generator_ramp_down_rate`**

```math
\widetilde{\mathrm{rd}}_{g,\xi,t} = \begin{cases} \mathrm{rd}_{g,\xi,t} & \text{if } \mathrm{rd}_{g,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Generator_ramp_previous_status`**

```math
\overleftarrow{\bar u}_{g,\xi,t} = \begin{cases} \mathrm{u}^{0}_{g,\xi} \cdot \mathrm{N}^{\mathrm{fix}}_{g,\xi} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \\ \overleftarrow{u}_{g,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Generator_ramp_up_allowance`**

```math
\Delta^{+}_{g,\xi,t} = \begin{cases} \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \overleftarrow{\bar u}_{g,\xi,t} + \widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} \cdot \left( u_{g,\xi,t} - \overleftarrow{\bar u}_{g,\xi,t} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{g,\xi} & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Generator_ramp_up_rate`**

```math
\widetilde{\mathrm{ru}}_{g,\xi,t} = \begin{cases} \mathrm{ru}_{g,\xi,t} & \text{if } \mathrm{ru}_{g,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Generator_shut_down_rate`**

```math
\widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} = \begin{cases} \mathrm{rd}^{\mathrm{dn}}_{g,\xi} & \text{if } \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

**`Generator_start_up_rate`**

```math
\widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} = \begin{cases} \mathrm{ru}^{\mathrm{up}}_{g,\xi} & \text{if } \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi
```

#### Subject to

**`Generator_p_ramp_limit_down`**

```math
\overleftarrow{p}_{g,\xi,t} - p_{g,\xi,t} \le \Delta^{-}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{rd}_{g,\xi,t} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{g,\xi,t} \wedge \mathrm{on}_{g,t}
```

**`Generator_p_ramp_limit_down_run_big_m`**

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} \ge -\widetilde{\mathrm{rd}}_{g,\xi,t} \cdot P_{g} - \mathrm{M}_{g,\xi} + \mathrm{M}_{g,\xi} \cdot u_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{rd}_{g,\xi,t} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```

**`Generator_p_ramp_limit_down_shut_big_m`**

```math
\overleftarrow{p}_{g,\xi,t} - p_{g,\xi,t} \le \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot P_{g} + \mathrm{M}_{g,\xi} - \mathrm{M}_{g,\xi} \cdot \mathit{dn}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{rd}_{g,\xi,t} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```

**`Generator_p_ramp_limit_up`**

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} \le \Delta^{+}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{ru}_{g,\xi,t} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{g,\xi,t} \wedge \mathrm{on}_{g,t}
```

**`Generator_p_ramp_limit_up_run_big_m`**

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} \le \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot P_{g} + \mathrm{M}_{g,\xi} - \mathrm{M}_{g,\xi} \cdot \overleftarrow{u}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{ru}_{g,\xi,t} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```

**`Generator_p_ramp_limit_up_start_big_m`**

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} \le \widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} \cdot P_{g} + \mathrm{M}_{g,\xi} - \mathrm{M}_{g,\xi} \cdot \mathit{up}_{g,\xi,t} \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{g,t} \wedge \left( \mathrm{ru}_{g,\xi,t} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{g,\xi} \text{ is defined} \right) \wedge \mathrm{prev}_{g,\xi,t}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
