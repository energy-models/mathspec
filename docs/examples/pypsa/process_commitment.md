<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Processes, the commitment

This file states the commitment rows of PyPSA's `Process`. It is one of the [24 fragments](index.md) that merge back into `examples/pypsa.yaml`. It adds a term to the sum `scenario_opex`. It reads `Process_active`, `Process_maintenance_capacity`, `Process_maintenance_pu`, `Process_maintenance_status`, `Process_modules_installed`, `Process_n_mod` and 10 more names that other fragments declare, and lists them under [`given`](../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    snapshot_weightings_objective: { dims: [snapshot] }
    Process_p_nom: { dims: [scenario, process] }
    Process_p_nom_extendable: { dims: [process], dtype: bool }
    Process_p_min_pu: { dims: [scenario, snapshot, process] }
    Process_p_max_pu: { dims: [scenario, snapshot, process] }
    Process_p_nom_mod: { dims: [process] }
    Process_modules_installed: { dims: [scenario, process] }
    Process_p_min_pu_nonneg: { dims: [process], dtype: bool }
    Process_maintenance_pu: { dims: [scenario, process] }
    period_weight_objective: { dims: [period] }
    Process_active: { dims: [snapshot, process], dtype: bool }
  variables:
    Process_p: { dims: [scenario, snapshot, process] }
    Process_n_mod: { dims: [process], domain: integer }
    Process_maintenance_capacity: { dims: [scenario, snapshot, process] }
    Process_maintenance_status: { dims: [scenario, snapshot, process] }
    Process_p_nom_ext: { dims: [process] }
  expressions:
    scenario_opex: { dims: [scenario] }
  conditions:
    Process_committed: { dims: [process, snapshot] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  process:
    description: generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate
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
  Process_committable:
    description: whether internal power is gated by an on/off status decision
    dims: [process]
    dtype: bool
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

variables:
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

expressions:
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
  Process_commitment_opex:
    expression: >-
      sum(sum(((Process_status * Process_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=process), over=snapshot)
      + sum(sum(Process_start_up * Process_start_up_cost, over=process), over=snapshot)
      + sum(sum(Process_shut_down * Process_shut_down_cost, over=process), over=snapshot)
    adds_to: scenario_opex

conditions:
  Process_com_ext:
    description: >-
      a committable process with an extendable, non-modular build that stands
      in the snapshot's period — PyPSA's `com-ext` rows, whose status is
      relaxed against the chosen build
    condition: >-
      Process_committable
      AND Process_p_nom_extendable
      AND NOT (Process_p_nom_mod > 0)
      AND Process_active

constraints:
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
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z}`$ | `Process_active` over $`\mathcal{J} \times \mathcal{T}`$, data another file declares |
| $`\gamma^{z}`$ | `Process_maintenance_pu` over $`\mathcal{J} \times \Xi`$, data another file declares |
| $`\mathrm{N}^{z,\mathrm{fix}}`$ | `Process_modules_installed` over $`\mathcal{J} \times \Xi`$, data another file declares |
| $`\overline{\mathrm{z}}`$ | `Process_p_max_pu` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, data another file declares |
| $`\underline{\mathrm{z}}`$ | `Process_p_min_pu` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$, data another file declares |
| $`\mathrm{nonneg}^{z}`$ | `Process_p_min_pu_nonneg` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{z}^{\mathrm{nom}}`$ | `Process_p_nom` over $`\mathcal{J} \times \Xi`$, data another file declares |
| $`\mathrm{ext}^{z}`$ | `Process_p_nom_extendable` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{z}^{\mathrm{mod}}`$ | `Process_p_nom_mod` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$, data another file declares |
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$, data another file declares |
| $`\mu^{z,\mathrm{nom}}`$ | `Process_maintenance_capacity` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`\mu^{z,u}`$ | `Process_maintenance_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`N^{z}`$ | `Process_n_mod` over $`\mathcal{J}`$ |
| $`z`$ | `Process_p` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ |
| $`Z`$ | `Process_p_nom_ext` over $`\mathcal{J}`$ |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Process_commitment_opex` to |
| $`\mathrm{on}^{z,\mathrm{com}}`$ | `Process_committed` over $`\mathcal{J} \times \mathcal{T}`$, a condition another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods — PyPSA's `investment_periods` |
| $`\mathcal{J}`$ | index $`j`$ — `process` — generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{M}^{z}`$ | `Process_big_m` over $`\mathcal{J} \times \Xi`$, `neutral` where the data has no row — the bound a committed extendable process's big-M rows release it by — the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu`, and where that keyword is not given, ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`, or 1e6 where there is none of them (`components.py:1050-1121`). Below the internal power a solve wants, it caps that internal power; data prep |
| $`\mathrm{com}^{z}`$ | `Process_committable` over $`\mathcal{J}`$ — whether internal power is gated by an on/off status decision |
| $`\mathrm{DT}^{z}`$ | `Process_min_down_time` over $`\mathcal{J} \times \Xi`$ — least snapshots a process stays off once stopped |
| $`\mathrm{UT}^{z}`$ | `Process_min_up_time` over $`\mathcal{J} \times \Xi`$ — least snapshots a process stays on once started |
| $`\mathrm{rest}^{z}`$ | `Process_must_stay_down` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — true while the down time a process brought into the horizon still binds — PyPSA's `min_down_time - down_time_before` snapshots, where `down_time_before > 0`, data prep for the same reason |
| $`\mathrm{hold}^{z}`$ | `Process_must_stay_up` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — true while the up time a process brought into the horizon still binds — data prep, since `position()` compares against a literal rather than a parameter |
| $`\mathrm{c}^{z,\mathrm{dn}}`$ | `Process_shut_down_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one stop in this snapshot |
| $`\mathrm{c}^{z,\mathrm{on}}`$ | `Process_stand_by_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one snapshot spent on |
| $`\mathrm{c}^{z,\mathrm{up}}`$ | `Process_start_up_cost` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — cost of one start in this snapshot |
| $`\mathrm{u}^{z,0}`$ | `Process_status_initial` over $`\mathcal{J} \times \Xi`$ — one where the process was on before the first snapshot, zero where off — PyPSA's `up_time_before > 0`, data prep |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z,\mathrm{com,ext}}`$ | `Process_com_ext` over $`\mathcal{J} \times \mathcal{T}`$ — a committable process with an extendable, non-modular build that stands in the snapshot's period — PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dn}^{z}`$ | `Process_shut_down` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-shut_down` — how much of a committable process turns off this snapshot, capped as the status is |
| $`\mathit{up}^{z}`$ | `Process_start_up` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-start_up` — how much of a committable process turns on this snapshot, capped as the status is |
| $`u^{z}`$ | `Process_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — `Process-status` — how much of a committable process is on: an integer the rows below cap at one, or at the module count where the build is modular |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Process\_commitment\_opex}`$ | `Process_commitment_opex` over $`\Xi`$ |
| $`\overleftarrow{u}^{z}`$ | `Process_previous_status` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the commitment state a process carries into a snapshot — off at the first snapshot it stands in past the first of the horizon, as PyPSA reads a status it did not build (`constraints.py:298`), and the state carried over otherwise |
| $`\overleftarrow{u}^{\circ z}`$ | `Process_status_carried_over` over $`\mathcal{J} \times \Xi \times \mathcal{T}`$ — the state a process carries over into a snapshot — the state it brought into the horizon at the first, the previous snapshot's after that |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |

#### Conditions

**`Process_com_ext`**

```math
\mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \iff \mathrm{com}^{z}_{j} \wedge \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \wedge \mathrm{on}^{z}_{j,t} \qquad \forall\, j \in \mathcal{J},\ t \in \mathcal{T}
```

#### Variable domains

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

#### Definitions

**`Process_commitment_opex`**

```math
\mathit{Process\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} u^{z}_{j,\xi,t} \cdot \mathrm{c}^{z,\mathrm{on}}_{j,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} \mathit{up}^{z}_{j,\xi,t} \cdot \mathrm{c}^{z,\mathrm{up}}_{j,\xi,t} + \sum_{t \in \mathcal{T}} \sum_{j \in \mathcal{J}} \mathit{dn}^{z}_{j,\xi,t} \cdot \mathrm{c}^{z,\mathrm{dn}}_{j,\xi,t} \qquad \forall\, \xi \in \Xi
```

**`Process_previous_status`**

```math
\overleftarrow{u}^{z}_{j,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{z}_{j,t - 1} \\ \overleftarrow{u}^{\circ z}_{j,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Process_status_carried_over`**

```math
\overleftarrow{u}^{\circ z}_{j,\xi,t} = \begin{cases} \mathrm{u}^{z,0}_{j,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ u^{z}_{j,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T}
```

#### Subject to

**`Process_com_down_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}^{z}} \mathit{dn}^{z}_{j,\xi,t'} \le 1 - u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{DT}^{z}_{j,\xi} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Process_com_ext_p_lower`**

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) + \mathrm{M}^{z}_{j,\xi} \cdot u^{z}_{j,\xi,t} - \mathrm{M}^{z}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t}
```

**`Process_com_ext_p_lower_nonneg`**

```math
z_{j,\xi,t} \ge 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t} \wedge \mathrm{nonneg}^{z}_{j}
```

**`Process_com_ext_p_upper_big_m`**

```math
z_{j,\xi,t} \le \mathrm{M}^{z}_{j,\xi} \cdot u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t}
```

**`Process_com_ext_p_upper_cap`**

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \left( Z_{j} - \gamma^{z}_{j,\xi} \cdot \mu^{z,\mathrm{nom}}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com,ext}}_{j,t}
```

**`Process_com_mod_p_lower`**

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{mod}}_{j} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_com_mod_p_upper`**

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{mod}}_{j} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_com_p_lower`**

```math
z_{j,\xi,t} \ge \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_com_p_upper`**

```math
z_{j,\xi,t} \le \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \left( u^{z}_{j,\xi,t} - \gamma^{z}_{j,\xi} \cdot \mu^{z,u}_{j,\xi,t} \right) \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_com_status_must_stay_down`**

```math
u^{z}_{j,\xi,t} = 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{rest}^{z}_{j,\xi,t}
```

**`Process_com_status_must_stay_up`**

```math
u^{z}_{j,\xi,t} = 1 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{hold}^{z}_{j,\xi,t}
```

**`Process_com_transition_shut_down`**

```math
\mathit{dn}^{z}_{j,\xi,t} \ge \overleftarrow{u}^{z}_{j,\xi,t} - u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

**`Process_com_transition_start_up`**

```math
\mathit{up}^{z}_{j,\xi,t} \ge u^{z}_{j,\xi,t} - \overleftarrow{u}^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

**`Process_com_up_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}^{z}} \mathit{up}^{z}_{j,\xi,t'} \le u^{z}_{j,\xi,t} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{UT}^{z}_{j,\xi} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Process_shut_down_p_fixed_upper`**

```math
\mathit{dn}^{z}_{j,\xi,t} \le \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_shut_down_p_nom_variable_upper`**

```math
\mathit{dn}^{z}_{j,\xi,t} \le N^{z}_{j} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_start_up_p_fixed_upper`**

```math
\mathit{up}^{z}_{j,\xi,t} \le \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_start_up_p_nom_variable_upper`**

```math
\mathit{up}^{z}_{j,\xi,t} \le N^{z}_{j} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```

**`Process_status_p_fixed_upper`**

```math
u^{z}_{j,\xi,t} \le \mathrm{N}^{z,\mathrm{fix}}_{j,\xi} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \neg \left( \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right)
```

**`Process_status_p_nom_variable_upper`**

```math
u^{z}_{j,\xi,t} \le N^{z}_{j} \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t} \wedge \mathrm{ext}^{z}_{j} \wedge \mathrm{z}^{\mathrm{mod}}_{j} > 0
```
<!-- gallery:end -->
