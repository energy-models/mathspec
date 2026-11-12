<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Process ramping

This file states the ramping rows of PyPSA's `Process`. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. `Process_previous_p` is the output carried into each snapshot, from `p_init` at the first where the unit came in running. `Process_ramp_up_allowance` adds the start-up ramp in the snapshot the unit turns on.

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Process_p_nom_extendable: { dims: [process], dtype: bool }
    Process_committable: { dims: [process], dtype: bool }
    Process_status_initial: { dims: [scenario, process] }
    Process_p_nom_mod: { dims: [process] }
    Process_modules_installed: { dims: [scenario, process] }
    Process_big_m: { dims: [scenario, process] }
    Process_active: { dims: [snapshot, process], dtype: bool }
  variables:
    Process_p: { dims: [scenario, snapshot, process] }
    Process_status: { dims: [scenario, snapshot, process], domain: integer }
    Process_start_up: { dims: [scenario, snapshot, process], domain: integer }
    Process_shut_down: { dims: [scenario, snapshot, process], domain: integer }
    Process_p_nom_ext: { dims: [process] }
  expressions:
    Process_p_nom_effective: { dims: [process, scenario] }
    Process_previous_status: { dims: [process, scenario, snapshot] }
    Process_p_nom_committed: { dims: [process, scenario] }
  conditions:
    Process_com_ext: { dims: [process, snapshot] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  process:
    description: generalised multi-port converters, each with an internal power that every port draws or delivers at its own rate
  period:
    description: investment periods. It is PyPSA's `investment_periods`
    dtype: int
    ordered: true

maps:
  snapshot:
    period:
      description: the investment period a snapshot falls in
      refers_to: period

parameters:
  Process_ramp_limit_up:
    description: most a process may raise its internal power between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time
    dims: [scenario, snapshot, process]
    missing: absent
  Process_ramp_limit_down:
    description: most a process may lower its internal power between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time
    dims: [scenario, snapshot, process]
    missing: absent
  Process_ramp_limit_start_up:
    description: most internal power in the snapshot a process starts, per unit of nominal power. No value means no limit
    dims: [scenario, process]
    missing: absent
  Process_ramp_limit_shut_down:
    description: most internal power in the snapshot before a process stops, per unit of nominal power. No value means no limit
    dims: [scenario, process]
    missing: absent
  Process_p_init:
    description: >-
      the internal power a process brought into the horizon, data prep. It is
      PyPSA's `p_init` where the process came in running, and zero where it
      came in off. Under a rolling horizon, it is the internal power the
      previous window solved. No value means it is unknown, and the process
      then has no ramp row at the first snapshot
    dims: [scenario, process]
    missing: 0

expressions:
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
  Process_p_carried_over:
    description: >-
      the output a process carries over into a snapshot. At the first, it is
      the `p_init` it brought in, which is zero where it came in off. After
      that, it is the previous snapshot's
    dims: [scenario, snapshot, process]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Process_p_init }
    otherwise: shift(Process_p, along=snapshot, offset=1)
  Process_ramp_up_rate:
    description: >-
      the ramp limit in a process's up row, PyPSA's `ramp_limit_up`. It is the
      full build where PyPSA has none, since a start-up ramp alone builds the
      row
    dims: [scenario, snapshot, process]
    cases:
      given: { when: Process_ramp_limit_up, expression: Process_ramp_limit_up }
    otherwise: 1
  Process_ramp_down_rate:
    description: >-
      the ramp limit in a process's down row, PyPSA's `ramp_limit_down`. It is
      the full build where PyPSA has none, since a shut-down ramp alone builds
      the row
    dims: [scenario, snapshot, process]
    cases:
      given: { when: Process_ramp_limit_down, expression: Process_ramp_limit_down }
    otherwise: 1
  Process_start_up_rate:
    description: >-
      the start-up ramp in a process's up row (PyPSA's `ramp_limit_start_up`),
      or the full build where it has none
    dims: [scenario, process]
    cases:
      given: { when: Process_ramp_limit_start_up, expression: Process_ramp_limit_start_up }
    otherwise: 1
  Process_shut_down_rate:
    description: >-
      the shut-down ramp in a process's down row (PyPSA's
      `ramp_limit_shut_down`), or the full build where it has none
    dims: [scenario, process]
    cases:
      given: { when: Process_ramp_limit_shut_down, expression: Process_ramp_limit_shut_down }
    otherwise: 1
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

conditions:
  Process_ramps_from_previous:
    description: >-
      a snapshot whose ramp uses a previous output. It is any snapshot but its
      period's first, and the horizon's first where the process comes in off
      or carries an initial output
    condition: >-
      position(snapshot, within=snapshot[period]) > 0 OR (position(snapshot) == 0 AND
      (Process_status_initial == 0 OR Process_p_init))

constraints:
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
      Process_p - Process_previous_p >=
      -Process_ramp_down_rate * Process_p_nom_ext
      - Process_big_m + Process_big_m * Process_status
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

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z}`$ | `Process_active` over $`\mathcal{J} \times \mathcal{T}`$, data another file declares |
| $`\mathrm{M}^{z}`$ | `Process_big_m` over $`\mathcal{J} \times \Xi`$, data another file declares |
| $`\mathrm{com}^{z}`$ | `Process_committable` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{N}^{z,\mathrm{fix}}`$ | `Process_modules_installed` over $`\mathcal{J} \times \Xi`$, data another file declares |
| $`\mathrm{ext}^{z}`$ | `Process_p_nom_extendable` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{z}^{\mathrm{mod}}`$ | `Process_p_nom_mod` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{u}^{z,0}`$ | `Process_status_initial` over $`\mathcal{J} \times \Xi`$, data another file declares |
| $`z`$ | `Process_p` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`Z`$ | `Process_p_nom_ext` over $`\mathcal{J}`$ |
| $`\mathit{dn}^{z}`$ | `Process_shut_down` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{up}^{z}`$ | `Process_start_up` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`u^{z}`$ | `Process_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`\widehat{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_committed` over $`\mathcal{J} \times \Xi`$, an expression another file defines |
| $`\widetilde{\mathrm{z}}^{\mathrm{nom}}`$ | `Process_p_nom_effective` over $`\mathcal{J} \times \Xi`$, an expression another file defines |
| $`\overleftarrow{u}^{z}`$ | `Process_previous_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, an expression another file defines |
| $`\mathrm{on}^{z,\mathrm{com,ext}}`$ | `Process_com_ext` over $`\mathcal{J} \times \mathcal{T}`$, a condition another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods. It is PyPSA's `investment_periods` |
| $`\mathcal{J}`$ | index $`j`$ — `process` — generalised multi-port converters, each with an internal power that every port draws or delivers at its own rate |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{z}^{0}`$ | `Process_p_init` over $`\mathcal{J} \times \Xi`$, $`0`$ where the data has no row — the internal power a process brought into the horizon, data prep. It is PyPSA's `p_init` where the process came in running, and zero where it came in off. Under a rolling horizon, it is the internal power the previous window solved. No value means it is unknown, and the process then has no ramp row at the first snapshot |
| $`\mathrm{rd}^{z}`$ | `Process_ramp_limit_down` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a process may lower its internal power between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{rd}^{z,\mathrm{dn}}`$ | `Process_ramp_limit_shut_down` over $`\mathcal{J} \times \Xi`$, `absent` where the data has no row — most internal power in the snapshot before a process stops, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{z,\mathrm{up}}`$ | `Process_ramp_limit_start_up` over $`\mathcal{J} \times \Xi`$, `absent` where the data has no row — most internal power in the snapshot a process starts, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{z}`$ | `Process_ramp_limit_up` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a process may raise its internal power between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{prev}^{z}`$ | `Process_ramps_from_previous` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — a snapshot whose ramp uses a previous output. It is any snapshot but its period's first, and the horizon's first where the process comes in off or carries an initial output |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{z}^{\circ}`$ | `Process_p_carried_over` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the output a process carries over into a snapshot. At the first, it is the `p_init` it brought in, which is zero where it came in off. After that, it is the previous snapshot's |
| $`\overleftarrow{z}`$ | `Process_previous_p` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the output a process carries into a snapshot. It is nothing at the first snapshot it is active in past the first of the horizon: PyPSA fills an output it did not build with zero (`constraints.py:716`). It is the output carried over otherwise |
| $`\Delta^{z,-}`$ | `Process_ramp_down_allowance` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — how far a process may lower internal power between two snapshots. It is its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\widetilde{\mathrm{rd}}^{z}`$ | `Process_ramp_down_rate` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the ramp limit in a process's down row, PyPSA's `ramp_limit_down`. It is the full build where PyPSA has none, since a shut-down ramp alone builds the row |
| $`\overleftarrow{\bar u}^{z}`$ | `Process_ramp_previous_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the status a committed process's ramp rows carry into a snapshot. At the first snapshot, a fixed modular process that came in running has every module on, since the state it brought in is on or off (`constraints.py:1152-1157`). The transition and down-time rows count it as one module (PyPSA/PyPSA\#2114). It is the state carried in otherwise |
| $`\Delta^{z,+}`$ | `Process_ramp_up_allowance` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — how far a process may raise internal power between two snapshots. It is its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\widetilde{\mathrm{ru}}^{z}`$ | `Process_ramp_up_rate` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the ramp limit in a process's up row, PyPSA's `ramp_limit_up`. It is the full build where PyPSA has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}^{z,\mathrm{dn}}`$ | `Process_shut_down_rate` over $`\mathcal{J} \times \Xi`$ — the shut-down ramp in a process's down row (PyPSA's `ramp_limit_shut_down`), or the full build where it has none |
| $`\widetilde{\mathrm{ru}}^{z,\mathrm{up}}`$ | `Process_start_up_rate` over $`\mathcal{J} \times \Xi`$ — the start-up ramp in a process's up row (PyPSA's `ramp_limit_start_up`), or the full build where it has none |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{map}(t)}(t)`$ | `position(within=subject[map])` — the position of $`t`$ inside its group |

#### Conditions

**`Process_ramps_from_previous`**

```math
\mathrm{prev}^{z}_{j,\xi,t} \iff \mathrm{pos}_{\mathrm{period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{z,0}_{j,\xi} = 0 \vee \mathrm{z}^{0}_{j,\xi} \text{ is defined} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

#### Definitions

**`Process_p_carried_over`**

```math
\overleftarrow{z}^{\circ}_{j,\xi,t} = \begin{cases} \mathrm{z}^{0}_{j,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ z_{j,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_previous_p`**

```math
\overleftarrow{z}_{j,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{z}_{j,t - 1} \\ \overleftarrow{z}^{\circ}_{j,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_ramp_down_allowance`**

```math
\Delta^{z,-}_{j,\xi,t} = \begin{cases} \widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot u^{z}_{j,\xi,t} + \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \left( \overleftarrow{\bar u}^{z}_{j,\xi,t} - u^{z}_{j,\xi,t} \right) & \text{if } \mathrm{com}^{z}_{j} \\ \widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot \widetilde{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_ramp_down_rate`**

```math
\widetilde{\mathrm{rd}}^{z}_{j,\xi,t} = \begin{cases} \mathrm{rd}^{z}_{j,\xi,t} & \text{if } \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_ramp_previous_status`**

```math
\overleftarrow{\bar u}^{z}_{j,\xi,t} = \begin{cases} \mathrm{u}^{z,0}_{j,\xi} \cdot \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \\ \overleftarrow{u}^{z}_{j,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_ramp_up_allowance`**

```math
\Delta^{z,+}_{j,\xi,t} = \begin{cases} \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \overleftarrow{\bar u}^{z}_{j,\xi,t} + \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} \cdot \widehat{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} \cdot \left( u^{z}_{j,\xi,t} - \overleftarrow{\bar u}^{z}_{j,\xi,t} \right) & \text{if } \mathrm{com}^{z}_{j} \\ \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot \widetilde{\mathrm{z}}^{\mathrm{nom}}_{j,\xi} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_ramp_up_rate`**

```math
\widetilde{\mathrm{ru}}^{z}_{j,\xi,t} = \begin{cases} \mathrm{ru}^{z}_{j,\xi,t} & \text{if } \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_shut_down_rate`**

```math
\widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} = \begin{cases} \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} & \text{if } \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

**`Process_start_up_rate`**

```math
\widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} = \begin{cases} \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} & \text{if } \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi
```

#### Subject to

**`Process_p_ramp_limit_down`**

```math
\overleftarrow{z}_{j,\xi,t} - z_{j,\xi,t} \le \Delta^{z,-}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right) \wedge \mathrm{prev}^{z}_{j,\xi,t} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_p_ramp_limit_down_run_big_m`**

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} \ge -\widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot Z_{j} - \mathrm{M}^{z}_{j,\xi} + \mathrm{M}^{z}_{j,\xi} \cdot u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```

**`Process_p_ramp_limit_down_shut_big_m`**

```math
\overleftarrow{z}_{j,\xi,t} - z_{j,\xi,t} \le \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot Z_{j} + \mathrm{M}^{z}_{j,\xi} - \mathrm{M}^{z}_{j,\xi} \cdot \mathit{dn}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{rd}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{rd}^{z,\mathrm{dn}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```

**`Process_p_ramp_limit_up`**

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} \le \Delta^{z,+}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \right) \wedge \mathrm{prev}^{z}_{j,\xi,t} \wedge \mathrm{on}^{z}_{j,t}
```

**`Process_p_ramp_limit_up_run_big_m`**

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} \le \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot Z_{j} + \mathrm{M}^{z}_{j,\xi} - \mathrm{M}^{z}_{j,\xi} \cdot \overleftarrow{u}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```

**`Process_p_ramp_limit_up_start_big_m`**

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} \le \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} \cdot Z_{j} + \mathrm{M}^{z}_{j,\xi} - \mathrm{M}^{z}_{j,\xi} \cdot \mathit{up}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \left( \mathrm{ru}^{z}_{j,\xi,t} \text{ is defined} \vee \mathrm{ru}^{z,\mathrm{up}}_{j,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{z}_{j,\xi,t}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
