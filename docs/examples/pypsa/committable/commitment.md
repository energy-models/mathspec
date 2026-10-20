<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Committable classes, the commitment

This file states the unit commitment of PyPSA's `Generator`, `Link` and `Process`. It is written once, over the dimension `unit` and names that start with `Unit_`, and each class takes it under its own names with [`rename`](../../../howto/compose.md#one-fragment-for-several-classes). The fragment `link/commitment` is this file with `unit` renamed `link`, `Unit_p` renamed `Link_p`, and so on for each name. Each of those is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. The math below prints the generator's. It declares `Unit_committable`, and a model takes this file or [no commitment](commitment_none.md), never both. It reads its status from [the integer status](status_integer.md) or [the relaxed status](status_relaxed.md), and its output limits read `Unit_status_available`, which [the maintenance](maintenance.md) adds to. It adds a term to the sum `scenario_opex`. It reads `Unit_active`, `Unit_committed`, `Unit_modules_installed`, `Unit_n_mod`, `Unit_p`, `Unit_p_max_pu` and 12 more names that other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    snapshot_weightings_objective: { dims: [snapshot] }
    Unit_p_nom: { dims: [scenario, unit] }
    Unit_p_nom_extendable: { dims: [unit], dtype: bool }
    Unit_p_min_pu: { dims: [scenario, snapshot, unit] }
    Unit_p_max_pu: { dims: [scenario, snapshot, unit] }
    Unit_p_nom_mod: { dims: [unit] }
    Unit_modules_installed: { dims: [scenario, unit] }
    Unit_p_min_pu_nonneg: { dims: [unit], dtype: bool }
    period_weight_objective: { dims: [period] }
    Unit_active: { dims: [snapshot, unit], dtype: bool }
  variables:
    Unit_status: { dims: [scenario, snapshot, unit] }
    Unit_start_up: { dims: [scenario, snapshot, unit] }
    Unit_shut_down: { dims: [scenario, snapshot, unit] }
    Unit_p: { dims: [scenario, snapshot, unit] }
    Unit_n_mod: { dims: [unit], domain: integer }
    Unit_p_nom_ext: { dims: [unit] }
  expressions:
    Unit_p_nom_available: { dims: [scenario, snapshot, unit] }
    scenario_opex: { dims: [scenario] }
  masks:
    Unit_committed: { dims: [snapshot, unit] }

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
  Unit_committable:
    description: whether output is gated by an on/off status decision
    dims: [unit]
    dtype: bool
  Unit_min_up_time:
    description: least snapshots a unit stays on once started
    dims: [scenario, unit]
    dtype: int
  Unit_min_down_time:
    description: least snapshots a unit stays off once stopped
    dims: [scenario, unit]
    dtype: int
  Unit_status_initial:
    description: one where the unit was on before the first snapshot, zero where off — PyPSA's `up_time_before > 0`, data prep
    dims: [scenario, unit]
    dtype: int
  Unit_must_stay_up:
    description: >-
      true while the up time a unit brought into the horizon still binds —
      data prep, since `position()` compares against a literal rather than a
      parameter
    dims: [scenario, snapshot, unit]
    dtype: bool
  Unit_must_stay_down:
    description: >-
      true while the down time a unit brought into the horizon still binds —
      PyPSA's `min_down_time - down_time_before` snapshots, where
      `down_time_before > 0`, data prep for the same reason
    dims: [scenario, snapshot, unit]
    dtype: bool
  Unit_start_up_cost:
    description: cost of one start in this snapshot
    dims: [scenario, snapshot, unit]
  Unit_shut_down_cost:
    description: cost of one stop in this snapshot
    dims: [scenario, snapshot, unit]
  Unit_stand_by_cost:
    description: cost of one snapshot spent on
    dims: [scenario, snapshot, unit]
  Unit_big_m:
    description: >-
      the bound a committed extendable unit's big-M rows release it by — the
      build cap `p_nom_max` times the highest `p_max_pu`, where the cap is
      finite and positive. Elsewhere it is `committable_big_m` times the
      highest `p_max_pu`, and where that keyword is not given, ten times the
      largest of the peak total load and the component's largest finite
      `p_nom` and `p_nom_max`, or 1e6 where there is none of them
      (`components.py:1050-1121`). Below the output a solve wants, it caps that
      output; data prep
    dims: [scenario, unit]
    missing: neutral

expressions:
  Unit_status_available:
    description: >-
      how much of a committed unit is on and can run — its status, less what
      maintenance takes out of it, where a maintenance file adds that
    dims: [scenario, snapshot, unit]
    expression: Unit_status
  Unit_previous_status:
    description: >-
      the commitment state a unit carries into a snapshot — off at the
      first snapshot it stands in past the first of the horizon, as PyPSA
      reads a status it did not build (`constraints.py:298`), and the state
      carried over otherwise
    dims: [scenario, snapshot, unit]
    cases:
      opening_late: { when: "position(snapshot) > 0 AND NOT shift(Unit_active, along=snapshot, offset=1)", expression: 0 }
    otherwise: Unit_status_carried_over
  Unit_status_carried_over:
    description: >-
      the state a unit carries over into a snapshot — the state it brought
      into the horizon at the first, the previous snapshot's after that
    dims: [scenario, snapshot, unit]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Unit_status_initial }
    otherwise: shift(Unit_status, along=snapshot, offset=1)
  Unit_commitment_opex:
    expression: >-
      sum(sum(((Unit_status * Unit_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=unit), over=snapshot)
      + sum(sum(Unit_start_up * Unit_start_up_cost, over=unit), over=snapshot)
      + sum(sum(Unit_shut_down * Unit_shut_down_cost, over=unit), over=snapshot)
    adds_to: scenario_opex

masks:
  Unit_com_ext:
    description: >-
      a committable unit with an extendable, non-modular build that
      stands in the snapshot's period — PyPSA's `com-ext` rows, whose status
      is relaxed against the chosen build
    where: >-
      Unit_committable
      AND Unit_p_nom_extendable
      AND NOT (Unit_p_nom_mod > 0)
      AND Unit_active

constraints:
  Unit_com_p_lower:
    description: "`-com-p-lower` — a committed unit outputs at least its minimum; off, at least nothing"
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND NOT Unit_p_nom_extendable AND NOT (Unit_p_nom_mod > 0)
    expression: Unit_p >= Unit_p_min_pu * Unit_p_nom * Unit_status_available
  Unit_com_p_upper:
    description: "`-com-p-upper` — a committed unit outputs at most what is available; off, at most nothing"
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND NOT Unit_p_nom_extendable AND NOT (Unit_p_nom_mod > 0)
    expression: Unit_p <= Unit_p_max_pu * Unit_p_nom * Unit_status_available
  Unit_com_transition_start_up:
    description: "`-com-transition-start-up` — turning on is a start, counted against the state the unit carried into the snapshot"
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    expression: Unit_start_up >= Unit_status - Unit_previous_status
  Unit_com_transition_shut_down:
    description: "`-com-transition-shut-down` — turning off is a stop, counted against the state the unit carried into the snapshot"
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    expression: Unit_shut_down >= Unit_previous_status - Unit_status
  Unit_com_up_time:
    description: >-
      `-com-up-time` — a unit started within its own minimum up time
      is still on. The first snapshot's share of the window is the brought-in
      up time's, which the must-stay-up mask carries
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_min_up_time > 0 AND position(snapshot) > 0
    expression: sum_back(Unit_start_up, along=snapshot, window=Unit_min_up_time) <= Unit_status
  Unit_com_down_time:
    description: >-
      `-com-down-time` — a unit stopped within its own minimum down
      time is still off. The first snapshot's share of the window is the
      brought-in down time's, which the must-stay-down mask carries
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_min_down_time > 0 AND position(snapshot) > 0
    expression: sum_back(Unit_shut_down, along=snapshot, window=Unit_min_down_time) <= 1 - Unit_status
  Unit_com_status_must_stay_up:
    description: "`-com-status-min_up_time_must_stay_up` — a unit still serving the up time it brought in stays on"
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_must_stay_up
    expression: Unit_status == 1
  Unit_com_status_must_stay_down:
    description: >-
      `-com-status-min_down_time_must_stay_up` — a unit still serving
      the down time it brought in stays off; PyPSA names the row `_must_stay_up`
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_must_stay_down
    expression: Unit_status == 0
  Unit_com_ext_p_upper_cap:
    description: >-
      `-com-ext-p-upper-cap` — a committed extendable unit outputs
      at most what is available of the chosen build, whatever its status
    dims: [scenario, snapshot, unit]
    where: Unit_com_ext
    expression: Unit_p <= Unit_p_max_pu * Unit_p_nom_available
  Unit_com_ext_p_upper_big_m:
    description: "`-com-ext-p-upper-bigM` — off, a unit outputs nothing; on, the big M is no bound"
    dims: [scenario, snapshot, unit]
    where: Unit_com_ext
    expression: Unit_p <= Unit_big_m * Unit_status
  Unit_com_ext_p_lower:
    description: >-
      `-com-ext-p-lower` — a committed extendable unit outputs at
      least its minimum of the chosen build; off, the big M releases the row
    dims: [scenario, snapshot, unit]
    where: Unit_com_ext
    expression: >-
      Unit_p >=
      Unit_p_min_pu * Unit_p_nom_available
      + Unit_big_m * Unit_status - Unit_big_m
  Unit_com_ext_p_lower_nonneg:
    description: >-
      `-com-ext-p-lower-nonneg` — where no minimum-per-unit is
      negative, output is also plainly non-negative, a row the big-M lower
      cannot assert while the unit is off
    dims: [scenario, snapshot, unit]
    where: Unit_com_ext AND Unit_p_min_pu_nonneg
    expression: Unit_p >= 0
  Unit_com_mod_p_lower:
    description: >-
      `-com-mod-p-lower` — a committed modular unit outputs at least
      its minimum of one module, whether the build is fixed or a decision
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_p_nom_mod > 0
    expression: Unit_p >= Unit_p_min_pu * Unit_p_nom_mod * Unit_status_available
  Unit_com_mod_p_upper:
    description: >-
      `-com-mod-p-upper` — a committed modular unit outputs at most
      one module's share, whether the build is fixed or a decision
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_p_nom_mod > 0
    expression: Unit_p <= Unit_p_max_pu * Unit_p_nom_mod * Unit_status_available
  Unit_status_p_fixed_upper:
    description: >-
      `-status-p-fixed-upper` — a status is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND NOT (Unit_p_nom_extendable AND Unit_p_nom_mod > 0)
    expression: Unit_status <= Unit_modules_installed
  Unit_start_up_p_fixed_upper:
    description: >-
      `-start_up-p-fixed-upper` — a start is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND NOT (Unit_p_nom_extendable AND Unit_p_nom_mod > 0)
    expression: Unit_start_up <= Unit_modules_installed
  Unit_shut_down_p_fixed_upper:
    description: >-
      `-shut_down-p-fixed-upper` — a stop is at most the modules in
      place, an explicit row as PyPSA writes it: one where the build is not
      modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND NOT (Unit_p_nom_extendable AND Unit_p_nom_mod > 0)
    expression: Unit_shut_down <= Unit_modules_installed
  Unit_status_p_nom_variable_upper:
    description: "`-status-p_nom-variable-upper` — a modular unit is on only where a module is built"
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_p_nom_extendable AND Unit_p_nom_mod > 0
    expression: Unit_status <= Unit_n_mod
  Unit_start_up_p_nom_variable_upper:
    description: "`-start_up-p_nom-variable-upper` — a modular unit starts only where a module is built"
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_p_nom_extendable AND Unit_p_nom_mod > 0
    expression: Unit_start_up <= Unit_n_mod
  Unit_shut_down_p_nom_variable_upper:
    description: "`-shut_down-p_nom-variable-upper` — a modular unit stops only where a module is built"
    dims: [scenario, snapshot, unit]
    where: Unit_committed AND Unit_p_nom_extendable AND Unit_p_nom_mod > 0
    expression: Unit_shut_down <= Unit_n_mod
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\Xi \times \mathcal{G}`$, data another file declares |
| $`\mathrm{ext}`$ | `Generator_p_nom_extendable` over $`\mathcal{G}`$, data another file declares |
| $`\underline{\mathrm{p}}`$ | `Generator_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`\overline{\mathrm{p}}`$ | `Generator_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`\mathrm{p}^{\mathrm{mod}}`$ | `Generator_p_nom_mod` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{N}^{\mathrm{fix}}`$ | `Generator_modules_installed` over $`\Xi \times \mathcal{G}`$, data another file declares |
| $`\mathrm{nonneg}`$ | `Generator_p_min_pu_nonneg` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$, data another file declares |
| $`\mathrm{on}`$ | `Generator_active` over $`\mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`p`$ | `Generator_p` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`N`$ | `Generator_n_mod` over $`\mathcal{G}`$ |
| $`P`$ | `Generator_p_nom_ext` over $`\mathcal{G}`$ |
| $`\mathrm{p}^{\mathrm{av}}`$ | `Generator_p_nom_available` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, an expression another file defines |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Generator_commitment_opex` to |
| $`\mathrm{on}^{\mathrm{com}}`$ | `Generator_committed` over $`\mathcal{T} \times \mathcal{G}`$, a mask another file defines |

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
| $`\mathrm{com}`$ | `Generator_committable` over $`\mathcal{G}`$ — whether output is gated by an on/off status decision |
| $`\mathrm{UT}`$ | `Generator_min_up_time` over $`\Xi \times \mathcal{G}`$ — least snapshots a unit stays on once started |
| $`\mathrm{DT}`$ | `Generator_min_down_time` over $`\Xi \times \mathcal{G}`$ — least snapshots a unit stays off once stopped |
| $`\mathrm{u}^{0}`$ | `Generator_status_initial` over $`\Xi \times \mathcal{G}`$ — one where the unit was on before the first snapshot, zero where off — PyPSA's `up_time_before > 0`, data prep |
| $`\mathrm{hold}`$ | `Generator_must_stay_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — true while the up time a unit brought into the horizon still binds — data prep, since `position()` compares against a literal rather than a parameter |
| $`\mathrm{rest}`$ | `Generator_must_stay_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — true while the down time a unit brought into the horizon still binds — PyPSA's `min_down_time - down_time_before` snapshots, where `down_time_before > 0`, data prep for the same reason |
| $`\mathrm{c}^{\mathrm{up}}`$ | `Generator_start_up_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of one start in this snapshot |
| $`\mathrm{c}^{\mathrm{dn}}`$ | `Generator_shut_down_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of one stop in this snapshot |
| $`\mathrm{c}^{\mathrm{on}}`$ | `Generator_stand_by_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — cost of one snapshot spent on |
| $`\mathrm{M}`$ | `Generator_big_m` over $`\Xi \times \mathcal{G}`$, `neutral` where the data has no row — the bound a committed extendable unit's big-M rows release it by — the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu`, and where that keyword is not given, ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`, or 1e6 where there is none of them (`components.py:1050-1121`). Below the output a solve wants, it caps that output; data prep |

#### Masks

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{\mathrm{com,ext}}`$ | `Generator_com_ext` over $`\mathcal{T} \times \mathcal{G}`$ — a committable unit with an extendable, non-modular build that stands in the snapshot's period — PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`u^{\mathrm{av}}`$ | `Generator_status_available` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — how much of a committed unit is on and can run — its status, less what maintenance takes out of it, where a maintenance file adds that |
| $`\overleftarrow{u}`$ | `Generator_previous_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the commitment state a unit carries into a snapshot — off at the first snapshot it stands in past the first of the horizon, as PyPSA reads a status it did not build (`constraints.py:298`), and the state carried over otherwise |
| $`\overleftarrow{u}^{\circ}`$ | `Generator_status_carried_over` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — the state a unit carries over into a snapshot — the state it brought into the horizon at the first, the previous snapshot's after that |
| $`\mathit{Generator\_commitment\_opex}`$ | `Generator_commitment_opex` over $`\Xi`$ |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |

#### Masks

**`Generator_com_ext`**

```math
\mathrm{on}^{\mathrm{com,ext}}_{t,g} \iff \mathrm{com}_{g} \wedge \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \wedge \mathrm{on}_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Definitions

**`Generator_status_available`**

```math
u^{\mathrm{av}}_{\xi,t,g} = u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_previous_status`**

```math
\overleftarrow{u}_{\xi,t,g} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}_{t - 1,g} \\ \overleftarrow{u}^{\circ}_{\xi,t,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_status_carried_over`**

```math
\overleftarrow{u}^{\circ}_{\xi,t,g} = \begin{cases} \mathrm{u}^{0}_{\xi,g} & \text{if } \mathrm{pos}(t) = 0 \\ u_{\xi,t - 1,g} & \text{otherwise} \end{cases} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G}
```

**`Generator_commitment_opex`**

```math
\mathit{Generator\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} u_{\xi,t,g} \cdot \mathrm{c}^{\mathrm{on}}_{\xi,t,g} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} \mathit{up}_{\xi,t,g} \cdot \mathrm{c}^{\mathrm{up}}_{\xi,t,g} + \sum_{t \in \mathcal{T}} \sum_{g \in \mathcal{G}} \mathit{dn}_{\xi,t,g} \cdot \mathrm{c}^{\mathrm{dn}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi
```

#### Subject to

**`Generator_com_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u^{\mathrm{av}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_com_p_upper`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u^{\mathrm{av}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \mathrm{ext}_{g} \wedge \neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_com_transition_start_up`**

```math
\mathit{up}_{\xi,t,g} \ge u_{\xi,t,g} - \overleftarrow{u}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_com_transition_shut_down`**

```math
\mathit{dn}_{\xi,t,g} \ge \overleftarrow{u}_{\xi,t,g} - u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_com_up_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}} \mathit{up}_{\xi,t',g} \le u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{UT}_{\xi,g} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Generator_com_down_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}} \mathit{dn}_{\xi,t',g} \le 1 - u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{DT}_{\xi,g} > 0 \wedge \mathrm{pos}(t) > 0
```

**`Generator_com_status_must_stay_up`**

```math
u_{\xi,t,g} = 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{hold}_{\xi,t,g}
```

**`Generator_com_status_must_stay_down`**

```math
u_{\xi,t,g} = 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{rest}_{\xi,t,g}
```

**`Generator_com_ext_p_upper_cap`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{av}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g}
```

**`Generator_com_ext_p_upper_big_m`**

```math
p_{\xi,t,g} \le \mathrm{M}_{\xi,g} \cdot u_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g}
```

**`Generator_com_ext_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{av}}_{\xi,t,g} + \mathrm{M}_{\xi,g} \cdot u_{\xi,t,g} - \mathrm{M}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g}
```

**`Generator_com_ext_p_lower_nonneg`**

```math
p_{\xi,t,g} \ge 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com,ext}}_{t,g} \wedge \mathrm{nonneg}_{g}
```

**`Generator_com_mod_p_lower`**

```math
p_{\xi,t,g} \ge \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{mod}}_{g} \cdot u^{\mathrm{av}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_com_mod_p_upper`**

```math
p_{\xi,t,g} \le \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{mod}}_{g} \cdot u^{\mathrm{av}}_{\xi,t,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_status_p_fixed_upper`**

```math
u_{\xi,t,g} \le \mathrm{N}^{\mathrm{fix}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_start_up_p_fixed_upper`**

```math
\mathit{up}_{\xi,t,g} \le \mathrm{N}^{\mathrm{fix}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_shut_down_p_fixed_upper`**

```math
\mathit{dn}_{\xi,t,g} \le \mathrm{N}^{\mathrm{fix}}_{\xi,g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \neg \left( \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right)
```

**`Generator_status_p_nom_variable_upper`**

```math
u_{\xi,t,g} \le N_{g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_start_up_p_nom_variable_upper`**

```math
\mathit{up}_{\xi,t,g} \le N_{g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```

**`Generator_shut_down_p_nom_variable_upper`**

```math
\mathit{dn}_{\xi,t,g} \le N_{g} \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g} \wedge \mathrm{ext}_{g} \wedge \mathrm{p}^{\mathrm{mod}}_{g} > 0
```
<!-- gallery:end -->
