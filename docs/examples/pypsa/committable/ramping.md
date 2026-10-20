<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Committable classes, the ramping

This file states the ramp limits of PyPSA's `Generator`, `Link` and `Process`. It is written once and each class takes it under its own names, as [the commitment](commitment.md) says. Each of those is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. The math below prints the generator's. It reads the status from [the commitment](commitment.md) or from [no commitment](commitment_none.md). It reads `Unit_active`, `Unit_big_m`, `Unit_com_ext`, `Unit_committable`, `Unit_p`, `Unit_p_nom_committed` and 9 more names that other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Unit_p_nom_extendable: { dims: [unit], dtype: bool }
    Unit_committable: { dims: [unit], dtype: bool }
    Unit_status_initial: { dims: [scenario, unit], dtype: int }
    Unit_p_nom_mod: { dims: [unit] }
    Unit_big_m: { dims: [scenario, unit] }
    Unit_active: { dims: [snapshot, unit], dtype: bool }
  variables:
    Unit_p: { dims: [scenario, snapshot, unit] }
    Unit_status: { dims: [scenario, snapshot, unit] }
    Unit_start_up: { dims: [scenario, snapshot, unit] }
    Unit_shut_down: { dims: [scenario, snapshot, unit] }
    Unit_p_nom_ext: { dims: [unit] }
  expressions:
    Unit_previous_status: { dims: [scenario, snapshot, unit] }
    Unit_p_nom_effective: { dims: [scenario, unit] }
    Unit_p_nom_committed: { dims: [scenario, unit] }
  masks:
    Unit_com_ext: { dims: [snapshot, unit] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  unit:
    description: the units of the class this layer is renamed for
  period:
    description: investment periods — PyPSA's `investment_periods`
    dtype: int
    ordered: true

relations:
  snapshot_period:
    description: the investment period a snapshot falls in
    key: snapshot
    values: period

parameters:
  Unit_ramp_limit_up:
    description: most a unit may raise its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time
    dims: [scenario, snapshot, unit]
    missing: neutral
  Unit_ramp_limit_down:
    description: most a unit may lower its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time
    dims: [scenario, snapshot, unit]
    missing: neutral
  Unit_ramp_limit_start_up:
    description: most output in the snapshot a unit starts, per unit of nominal power; no value means no limit
    dims: [scenario, unit]
    missing: neutral
  Unit_ramp_limit_shut_down:
    description: most output in the snapshot before a unit stops, per unit of nominal power; no value means no limit
    dims: [scenario, unit]
    missing: neutral
  Unit_p_init:
    description: >-
      the output a unit brought into the horizon — PyPSA's `p_init`, read
      only where the unit came in running; no value means it is unknown, so
      the unit carries no ramp row at the first snapshot
    dims: [scenario, unit]
    missing: neutral

expressions:
  Unit_previous_p:
    description: >-
      the output a unit carries into a snapshot — at the first, the
      `p_init` it brought in where it came in running and nothing where it
      came in off; the previous snapshot's after that
    dims: [scenario, snapshot, unit]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Unit_status_initial * Unit_p_init }
    otherwise: shift(Unit_p, along=snapshot, offset=1)
  Unit_ramp_up_rate:
    description: >-
      the ramp limit a unit's up row reads — PyPSA's `ramp_limit_up`, or the
      full build where it has none, since a start-up ramp alone builds the row
    dims: [scenario, snapshot, unit]
    cases:
      given: { when: Unit_ramp_limit_up, expression: Unit_ramp_limit_up }
    otherwise: 1
  Unit_ramp_down_rate:
    description: >-
      the ramp limit a unit's down row reads — PyPSA's `ramp_limit_down`, or
      the full build where it has none, since a shut-down ramp alone builds the row
    dims: [scenario, snapshot, unit]
    cases:
      given: { when: Unit_ramp_limit_down, expression: Unit_ramp_limit_down }
    otherwise: 1
  Unit_start_up_rate:
    description: >-
      the start-up ramp a unit's up row reads — PyPSA's `ramp_limit_start_up`,
      or the full build where it has none
    dims: [scenario, unit]
    cases:
      given: { when: Unit_ramp_limit_start_up, expression: Unit_ramp_limit_start_up }
    otherwise: 1
  Unit_shut_down_rate:
    description: >-
      the shut-down ramp a unit's down row reads — PyPSA's
      `ramp_limit_shut_down`, or the full build where it has none
    dims: [scenario, unit]
    cases:
      given: { when: Unit_ramp_limit_shut_down, expression: Unit_ramp_limit_shut_down }
    otherwise: 1
  Unit_ramp_up_allowance:
    description: >-
      how far a unit may raise output between two snapshots — its ramp
      limit of the build while it stays on, plus its start-up ramp in the
      snapshot it turns on
    dims: [scenario, snapshot, unit]
    cases:
      committed:
        when: Unit_committable
        expression: >-
          Unit_ramp_up_rate * Unit_p_nom_committed * Unit_previous_status
          + Unit_start_up_rate * Unit_p_nom_committed
          * (Unit_status - Unit_previous_status)
    otherwise: Unit_ramp_up_rate * Unit_p_nom_effective
  Unit_ramp_down_allowance:
    description: >-
      how far a unit may lower output between two snapshots — its ramp
      limit of the build while it stays on, plus its shut-down ramp in the
      snapshot it turns off
    dims: [scenario, snapshot, unit]
    cases:
      committed:
        when: Unit_committable
        expression: >-
          Unit_ramp_down_rate * Unit_p_nom_committed * Unit_status
          + Unit_shut_down_rate * Unit_p_nom_committed
          * (Unit_previous_status - Unit_status)
    otherwise: Unit_ramp_down_rate * Unit_p_nom_effective

masks:
  Unit_ramps_from_previous:
    description: >-
      a snapshot whose ramp reads a previous output — any snapshot but its
      period's first, and the horizon's first where the unit comes in off
      or carries an initial output
    where: >-
      position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
      (Unit_status_initial == 0 OR Unit_p_init))

constraints:
  Unit_p_ramp_limit_up_run_big_m:
    description: >-
      `-p-ramp_limit_up-run-bigM` — a committed extendable unit
      raises output no faster than its limit of the chosen build; the big M
      releases the row in the snapshot it turns on
    dims: [scenario, snapshot, unit]
    where: >-
      Unit_com_ext
      AND (Unit_ramp_limit_up OR Unit_ramp_limit_start_up)
      AND Unit_ramps_from_previous
    expression: >-
      Unit_p - Unit_previous_p <=
      Unit_ramp_up_rate * Unit_p_nom_ext
      + Unit_big_m - Unit_big_m * Unit_previous_status
  Unit_p_ramp_limit_up_start_big_m:
    description: >-
      `-p-ramp_limit_up-start-bigM` — in the snapshot it turns on, a
      committed extendable unit ramps no further than its start-up ramp of
      the chosen build; the big M releases the row everywhere else
    dims: [scenario, snapshot, unit]
    where: >-
      Unit_com_ext
      AND (Unit_ramp_limit_up OR Unit_ramp_limit_start_up)
      AND Unit_ramps_from_previous
    expression: >-
      Unit_p - Unit_previous_p <=
      Unit_start_up_rate * Unit_p_nom_ext
      + Unit_big_m - Unit_big_m * Unit_start_up
  Unit_p_ramp_limit_down_run_big_m:
    description: >-
      `-p-ramp_limit_down-run-bigM` — a committed extendable unit
      lowers output no faster than its limit of the chosen build; the big M
      releases the row in the snapshot it turns off
    dims: [scenario, snapshot, unit]
    where: >-
      Unit_com_ext
      AND (Unit_ramp_limit_down OR Unit_ramp_limit_shut_down)
      AND Unit_ramps_from_previous
    expression: >-
      Unit_previous_p - Unit_p <=
      Unit_ramp_down_rate * Unit_p_nom_ext
      + Unit_big_m - Unit_big_m * Unit_status
  Unit_p_ramp_limit_down_shut_big_m:
    description: >-
      `-p-ramp_limit_down-shut-bigM` — in the snapshot it turns off,
      a committed extendable unit ramps no further than its shut-down ramp of
      the chosen build; the big M releases the row everywhere else
    dims: [scenario, snapshot, unit]
    where: >-
      Unit_com_ext
      AND (Unit_ramp_limit_down OR Unit_ramp_limit_shut_down)
      AND Unit_ramps_from_previous
    expression: >-
      Unit_previous_p - Unit_p <=
      Unit_shut_down_rate * Unit_p_nom_ext
      + Unit_big_m - Unit_big_m * Unit_shut_down
  Unit_p_ramp_limit_up:
    description: >-
      `-p-ramp_limit_up` — a unit raises output no faster than
      its ramp limit of the build, and a committed one no further than its
      start-up ramp in the snapshot it turns on. A unit that came into the
      horizon running carries a row at the first snapshot only where its
      `p_init` gives the output it brought in, and no unit carries one at
      the start of a later investment period — nor does any unit a big M releases instead
    dims: [scenario, snapshot, unit]
    where: >-
      (Unit_ramp_limit_up OR Unit_ramp_limit_start_up)
      AND NOT (Unit_committable AND Unit_p_nom_extendable AND NOT (Unit_p_nom_mod > 0))
      AND Unit_ramps_from_previous
      AND Unit_active
    expression: Unit_p - Unit_previous_p <= Unit_ramp_up_allowance
  Unit_p_ramp_limit_down:
    description: >-
      `-p-ramp_limit_down` — a unit lowers output no faster than
      its ramp limit of the build, and a committed one no further than its
      shut-down ramp in the snapshot it turns off. A unit that came into the
      horizon running carries a row at the first snapshot only where its
      `p_init` gives the output it brought in, and no unit carries one at
      the start of a later investment period — nor does any unit a big M releases instead
    dims: [scenario, snapshot, unit]
    where: >-
      (Unit_ramp_limit_down OR Unit_ramp_limit_shut_down)
      AND NOT (Unit_committable AND Unit_p_nom_extendable AND NOT (Unit_p_nom_mod > 0))
      AND Unit_ramps_from_previous
      AND Unit_active
    expression: Unit_previous_p - Unit_p <= Unit_ramp_down_allowance

assumptions:
  Unit_came_in_running_unless_committable:
    holds: "Unit_status_initial == 1"
    where: "NOT Unit_committable AND (Unit_ramp_limit_up OR Unit_ramp_limit_down OR Unit_ramp_limit_start_up OR Unit_ramp_limit_shut_down)"
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
| $`\mathrm{ext}`$ | `Generator_p_nom_extendable` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{com}`$ | `Generator_committable` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{u}^{0}`$ | `Generator_status_initial` over $`\Xi \times \mathcal{G}`$, data another file declares |
| $`\mathrm{p}^{\mathrm{mod}}`$ | `Generator_p_nom_mod` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{M}`$ | `Generator_big_m` over $`\Xi \times \mathcal{G}`$, data another file declares |
| $`\mathrm{on}`$ | `Generator_active` over $`\mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`p`$ | `Generator_p` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`P`$ | `Generator_p_nom_ext` over $`\mathcal{G}`$ |
| $`\overleftarrow{u}`$ | `Generator_previous_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, an expression another file defines |
| $`\widetilde{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_effective` over $`\Xi \times \mathcal{G}`$, an expression another file defines |
| $`\widehat{\mathrm{p}}^{\mathrm{nom}}`$ | `Generator_p_nom_committed` over $`\Xi \times \mathcal{G}`$, an expression another file defines |
| $`\mathrm{on}^{\mathrm{com,ext}}`$ | `Generator_com_ext` over $`\mathcal{T} \times \mathcal{G}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — the units of the class this layer is renamed for |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods — PyPSA's `investment_periods` |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{ru}`$ | `Generator_ramp_limit_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the data has no row — most a unit may raise its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time |
| $`\mathrm{rd}`$ | `Generator_ramp_limit_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, `neutral` where the data has no row — most a unit may lower its output between snapshots, per unit of nominal power; no value means no limit — read at the later of the two snapshots, so the limit may change over time |
| $`\mathrm{ru}^{\mathrm{up}}`$ | `Generator_ramp_limit_start_up` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — most output in the snapshot a unit starts, per unit of nominal power; no value means no limit |
| $`\mathrm{rd}^{\mathrm{dn}}`$ | `Generator_ramp_limit_shut_down` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — most output in the snapshot before a unit stops, per unit of nominal power; no value means no limit |
| $`\mathrm{p}^{0}`$ | `Generator_p_init` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — the output a unit brought into the horizon — PyPSA's `p_init`, read only where the unit came in running; no value means it is unknown, so the unit carries no ramp row at the first snapshot |

#### Masks

| Symbol | Meaning |
|---|---|
| $`\mathrm{prev}`$ | `Generator_ramps_from_previous` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — a snapshot whose ramp reads a previous output — any snapshot but its period's first, and the horizon's first where the unit comes in off or carries an initial output |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{p}`$ | `Generator_previous_p` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the output a unit carries into a snapshot — at the first, the `p_init` it brought in where it came in running and nothing where it came in off; the previous snapshot's after that |
| $`\widetilde{\mathrm{ru}}`$ | `Generator_ramp_up_rate` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the ramp limit a unit's up row reads — PyPSA's `ramp_limit_up`, or the full build where it has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}`$ | `Generator_ramp_down_rate` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the ramp limit a unit's down row reads — PyPSA's `ramp_limit_down`, or the full build where it has none, since a shut-down ramp alone builds the row |
| $`\widetilde{\mathrm{ru}}^{\mathrm{up}}`$ | `Generator_start_up_rate` over $`\Xi \times \mathcal{G}`$ — the start-up ramp a unit's up row reads — PyPSA's `ramp_limit_start_up`, or the full build where it has none |
| $`\widetilde{\mathrm{rd}}^{\mathrm{dn}}`$ | `Generator_shut_down_rate` over $`\Xi \times \mathcal{G}`$ — the shut-down ramp a unit's down row reads — PyPSA's `ramp_limit_shut_down`, or the full build where it has none |
| $`\Delta^{+}`$ | `Generator_ramp_up_allowance` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how far a unit may raise output between two snapshots — its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\Delta^{-}`$ | `Generator_ramp_down_allowance` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how far a unit may lower output between two snapshots — its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |

#### Masks

**`Generator_ramps_from_previous`**

```math
\mathrm{prev}_{\xi,t,g} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{0}_{\xi,g} = 0 \vee \mathrm{p}^{0}_{\xi,g} \text{ is defined} \right) \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Definitions

**`Generator_previous_p`**

```math
\overleftarrow{p}_{\xi,t,g} = \begin{cases} \mathrm{u}^{0}_{\xi,g} \cdot \mathrm{p}^{0}_{\xi,g} & \text{if } \mathrm{pos}(t) = 0 \\ p_{\xi,t - 1,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
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

**`Generator_ramp_up_allowance`**

```math
\Delta^{+}_{\xi,t,g} = \begin{cases} \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \overleftarrow{u}_{\xi,t,g} + \widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \left( u_{\xi,t,g} - \overleftarrow{u}_{\xi,t,g} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_ramp_down_allowance`**

```math
\Delta^{-}_{\xi,t,g} = \begin{cases} \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t,g} + \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \widehat{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} \cdot \left( \overleftarrow{u}_{\xi,t,g} - u_{\xi,t,g} \right) & \text{if } \mathrm{com}_{g} \\ \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \widetilde{\mathrm{p}}^{\mathrm{nom}}_{\xi,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Subject to

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

**`Generator_p_ramp_limit_up`**

```math
p_{\xi,t,g} - \overleftarrow{p}_{\xi,t,g} \le \Delta^{+}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \left( \mathrm{ru}_{\xi,t,g} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{\xi,g} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{\xi,t,g} \wedge \mathrm{on}_{t,g}
```

**`Generator_p_ramp_limit_down`**

```math
\overleftarrow{p}_{\xi,t,g} - p_{\xi,t,g} \le \Delta^{-}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \left( \mathrm{rd}_{\xi,t,g} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{\xi,g} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \right) \wedge \mathrm{prev}_{\xi,t,g} \wedge \mathrm{on}_{t,g}
```

#### Assumptions

**`Generator_came_in_running_unless_committable`**

```math
\mathrm{u}^{0}_{\xi,g} = 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \neg \mathrm{com}_{g} \wedge \left( \mathrm{ru}_{\xi,t,g} \text{ is defined} \vee \mathrm{rd}_{\xi,t,g} \text{ is defined} \vee \mathrm{ru}^{\mathrm{up}}_{\xi,g} \text{ is defined} \vee \mathrm{rd}^{\mathrm{dn}}_{\xi,g} \text{ is defined} \right)
```
<!-- gallery:end -->
