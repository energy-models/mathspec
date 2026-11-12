<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Link commitment

This file states the commitment rows of PyPSA's `Link`. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It adds a [term](../../reference/language/named.md#adds_to) to the sum `scenario_opex`. `Link_status_carried_over` is the state at the start of each snapshot, from the state the unit brought into the horizon at the first. `Link_com_ext_p_upper_big_m` bounds an extendable committed unit by a large constant (big-M).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    snapshot_weightings_objective: { dims: [snapshot] }
    Link_p_nom: { dims: [scenario, link] }
    Link_p_nom_extendable: { dims: [link], dtype: bool }
    Link_p_min_pu: { dims: [scenario, snapshot, link] }
    Link_p_max_pu: { dims: [scenario, snapshot, link] }
    Link_p_nom_mod: { dims: [link] }
    Link_modules_installed: { dims: [scenario, link] }
    Link_p_min_pu_nonneg: { dims: [link], dtype: bool }
    Link_maintenance_pu: { dims: [scenario, link] }
    period_weight_objective: { dims: [period] }
    Link_active: { dims: [snapshot, link], dtype: bool }
  variables:
    Link_p: { dims: [scenario, snapshot, link] }
    Link_n_mod: { dims: [link], domain: integer }
    Link_maintenance_capacity: { dims: [scenario, snapshot, link] }
    Link_maintenance_status: { dims: [scenario, snapshot, link] }
    Link_p_nom_ext: { dims: [link] }
  expressions:
    Link_modules: { dims: [link, scenario] }
    scenario_opex: { dims: [scenario] }
  conditions:
    Link_committed: { dims: [link, snapshot] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  link:
    description: controllable connections, each from one bus to the buses it delivers to
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
  Link_committable:
    description: whether flow is gated by an on/off status decision
    dims: [link]
    dtype: bool
  Link_min_up_time:
    description: least snapshots a link stays on once started
    dims: [scenario, link]
    dtype: int
  Link_min_down_time:
    description: least snapshots a link stays off once stopped
    dims: [scenario, link]
    dtype: int
  Link_status_initial:
    description: >-
      one where the link was on before the first snapshot, zero where off.
      It is PyPSA's `up_time_before > 0` for a committable link, and one for
      a link that is not, whose ramp rows PyPSA starts from on
      (`constraints.py:323`), data prep. Under a rolling horizon, it is the
      status the previous window solved, a fraction where unit commitment is
      linearised
    dims: [scenario, link]
  Link_up_time_brought_in:
    description: >-
      one while the up time a link brought into the horizon is still
      running, zero after. It is PyPSA's start `up_time_before` snapshots
      before the first, counted while `min_up_time` has not passed since
      (`constraints.py:302-323`, `:677-678`), data prep. Under a rolling
      horizon with linearised unit commitment, it is the fraction of the
      start the previous window solved
    dims: [scenario, snapshot, link]
  Link_down_time_brought_in:
    description: >-
      one while the down time a link brought into the horizon is still
      running, zero after. It is PyPSA's stop `down_time_before` snapshots
      before the first, counted while `min_down_time` has not passed since
      (`constraints.py:302-323`, `:677-678`), data prep. Under a rolling
      horizon with linearised unit commitment, it is the fraction of the
      stop the previous window solved
    dims: [scenario, snapshot, link]
  Link_start_up_cost:
    description: cost of one start in this snapshot
    dims: [scenario, snapshot, link]
  Link_shut_down_cost:
    description: cost of one stop in this snapshot
    dims: [scenario, snapshot, link]
  Link_stand_by_cost:
    description: cost of one snapshot spent on
    dims: [scenario, snapshot, link]
  Link_big_m:
    description: >-
      the bound a committed extendable link's big-M rows release it by, data
      prep. It is the build cap `p_nom_max` times the highest `p_max_pu`,
      where the cap is finite and positive. Elsewhere it is
      `committable_big_m` times the highest `p_max_pu`
      (`components.py:1082-1152`). Without that keyword, it is ten times the
      largest of the peak total load and the component's largest finite
      `p_nom` and `p_nom_max`. Where there is none of them, it is 1e6. Below
      the flow a solve wants, it caps that flow
    dims: [scenario, link]
    missing: absent

variables:
  Link_status:
    description: >-
      `Link-status` — how much of a committable link is on. It is an integer
      the rows below cap at one, or at the module count where the build is
      modular
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0
  Link_start_up:
    description: "`Link-start_up` — how much of a committable link turns on this snapshot, capped as the status is"
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0
  Link_shut_down:
    description: "`Link-shut_down` — how much of a committable link turns off this snapshot, capped as the status is"
    dims: [scenario, snapshot, link]
    where: Link_committed
    domain: integer
    bounds:
      lower: 0

expressions:
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
  Link_status_carried_over:
    description: >-
      the state a link carries over into a snapshot: the state it brought into
      the horizon at the first, the previous snapshot's after that
    dims: [scenario, snapshot, link]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Link_status_initial }
    otherwise: shift(Link_status, along=snapshot, offset=1)
  Link_commitment_opex:
    expression: >-
      sum(sum(((Link_status * Link_stand_by_cost) * snapshot_weightings_objective) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
      + sum(sum((Link_start_up * Link_start_up_cost) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
      + sum(sum((Link_shut_down * Link_shut_down_cost) * at(period_weight_objective, by=snapshot_period[period]), over=link), over=snapshot)
    adds_to: scenario_opex

conditions:
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

constraints:
  Link_com_p_lower:
    description: "`Link-com-p-lower` — a committed link flows at least its minimum. Off, it flows at least nothing"
    dims: [scenario, snapshot, link]
    where: Link_committed AND NOT Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0)
    expression: Link_p >= Link_p_min_pu * Link_p_nom * (Link_status - Link_maintenance_pu * Link_maintenance_status)
  Link_com_p_upper:
    description: "`Link-com-p-upper` — a committed link flows at most what is available. Off, it flows at most nothing"
    dims: [scenario, snapshot, link]
    where: Link_committed AND NOT Link_p_nom_extendable AND NOT (Link_p_nom_mod > 0)
    expression: Link_p <= Link_p_max_pu * Link_p_nom * (Link_status - Link_maintenance_pu * Link_maintenance_status)
  Link_com_transition_start_up:
    description: "`Link-com-transition-start-up` — turning on is a start, counted against the state the link carried into the snapshot"
    dims: [scenario, snapshot, link]
    where: Link_committed
    expression: Link_start_up >= Link_status - Link_previous_status
  Link_com_transition_shut_down:
    description: "`Link-com-transition-shut-down` — turning off is a stop, counted against the state the link carried into the snapshot"
    dims: [scenario, snapshot, link]
    where: Link_committed
    expression: Link_shut_down >= Link_previous_status - Link_status
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
  Link_com_ext_p_upper_cap:
    description: >-
      `Link-com-ext-p-upper-cap` — a committed extendable link flows
      at most what is available of the chosen build, whatever its status
    dims: [scenario, snapshot, link]
    where: Link_com_ext
    expression: Link_p <= Link_p_max_pu * (Link_p_nom_ext - Link_maintenance_pu * Link_maintenance_capacity)
  Link_com_ext_p_upper_big_m:
    description: "`Link-com-ext-p-upper-bigM` — off, a link flows nothing. On, the big M is no bound"
    dims: [scenario, snapshot, link]
    where: Link_com_ext
    expression: Link_p <= Link_big_m * Link_status
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
  Link_com_ext_p_lower_nonneg:
    description: >-
      `Link-com-ext-p-lower-nonneg` — where no minimum-per-unit is
      negative, flow is also plainly non-negative, a row the big-M lower
      cannot assert while the link is off
    dims: [scenario, snapshot, link]
    where: Link_com_ext AND Link_p_min_pu_nonneg
    expression: Link_p >= 0
  Link_com_mod_p_lower:
    description: >-
      `Link-com-mod-p-lower` — a committed modular link flows at least
      its minimum of one module, whether the build is fixed or a decision
    dims: [scenario, snapshot, link]
    where: Link_committed AND Link_p_nom_mod > 0
    expression: Link_p >= Link_p_min_pu * Link_p_nom_mod * (Link_status - Link_maintenance_pu * Link_maintenance_status)
  Link_com_mod_p_upper:
    description: >-
      `Link-com-mod-p-upper` — a committed modular link flows at most
      one module's share, whether the build is fixed or a decision
    dims: [scenario, snapshot, link]
    where: Link_committed AND Link_p_nom_mod > 0
    expression: Link_p <= Link_p_max_pu * Link_p_nom_mod * (Link_status - Link_maintenance_pu * Link_maintenance_status)
  Link_status_p_fixed_upper:
    description: >-
      `Link-status-p-fixed-upper` — a status is at most the modules in place,
      an explicit row as PyPSA writes it. The bound is one where the build is
      not modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, link]
    where: Link_committed AND NOT (Link_p_nom_extendable AND Link_p_nom_mod > 0)
    expression: Link_status <= Link_modules_installed
  Link_start_up_p_fixed_upper:
    description: >-
      `Link-start_up-p-fixed-upper` — a start is at most the modules in place,
      an explicit row as PyPSA writes it. The bound is one where the build is
      not modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, link]
    where: Link_committed AND NOT (Link_p_nom_extendable AND Link_p_nom_mod > 0)
    expression: Link_start_up <= Link_modules_installed
  Link_shut_down_p_fixed_upper:
    description: >-
      `Link-shut_down-p-fixed-upper` — a stop is at most the modules in place,
      an explicit row as PyPSA writes it. The bound is one where the build is
      not modular, and the fixed build's whole count of modules where it is
    dims: [scenario, snapshot, link]
    where: Link_committed AND NOT (Link_p_nom_extendable AND Link_p_nom_mod > 0)
    expression: Link_shut_down <= Link_modules_installed
  Link_status_p_nom_variable_upper:
    description: "`Link-status-p_nom-variable-upper` — a modular link is on only where a module is built"
    dims: [scenario, snapshot, link]
    where: Link_committed AND Link_p_nom_extendable AND Link_p_nom_mod > 0
    expression: Link_status <= Link_n_mod
  Link_start_up_p_nom_variable_upper:
    description: "`Link-start_up-p_nom-variable-upper` — a modular link starts only where a module is built"
    dims: [scenario, snapshot, link]
    where: Link_committed AND Link_p_nom_extendable AND Link_p_nom_mod > 0
    expression: Link_start_up <= Link_n_mod
  Link_shut_down_p_nom_variable_upper:
    description: "`Link-shut_down-p_nom-variable-upper` — a modular link stops only where a module is built"
    dims: [scenario, snapshot, link]
    where: Link_committed AND Link_p_nom_extendable AND Link_p_nom_mod > 0
    expression: Link_shut_down <= Link_n_mod

assumptions:
  Link_big_m_where_committed_and_extendable:
    holds: "Link_big_m"
    where: "Link_com_ext"
    description: >-
      a committable link with an extendable, non-modular build has
      the big-M its rows release it by — PyPSA computes one for each
      (`get_committable_big_m_values`)
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f}`$ | `Link_active` over $`\mathcal{L} \times \mathcal{T}`$, data another file declares |
| $`\gamma^{f}`$ | `Link_maintenance_pu` over $`\mathcal{L} \times \Xi`$, data another file declares |
| $`\mathrm{N}^{f,\mathrm{fix}}`$ | `Link_modules_installed` over $`\mathcal{L} \times \Xi`$, data another file declares |
| $`\overline{\mathrm{f}}`$ | `Link_p_max_pu` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, data another file declares |
| $`\underline{\mathrm{f}}`$ | `Link_p_min_pu` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, data another file declares |
| $`\mathrm{nonneg}^{f}`$ | `Link_p_min_pu_nonneg` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{f}^{\mathrm{nom}}`$ | `Link_p_nom` over $`\mathcal{L} \times \Xi`$, data another file declares |
| $`\mathrm{ext}^{f}`$ | `Link_p_nom_extendable` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{f}^{\mathrm{mod}}`$ | `Link_p_nom_mod` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{w}^{y}`$ | `period_weight_objective` over $`\mathcal{Y}`$, data another file declares |
| $`\mathrm{w}`$ | `snapshot_weightings_objective` over $`\mathcal{T}`$, data another file declares |
| $`\mu^{f,\mathrm{nom}}`$ | `Link_maintenance_capacity` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`\mu^{f,u}`$ | `Link_maintenance_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`N^{f}`$ | `Link_n_mod` over $`\mathcal{L}`$ |
| $`f`$ | `Link_p` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`F`$ | `Link_p_nom_ext` over $`\mathcal{L}`$ |
| $`\mathrm{M}^{f}`$ | `Link_modules` over $`\mathcal{L} \times \Xi`$, an expression another file defines |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression this file adds `Link_commitment_opex` to |
| $`\mathrm{on}^{f,\mathrm{com}}`$ | `Link_committed` over $`\mathcal{L} \times \mathcal{T}`$, a condition another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{L}`$ | index $`l`$ — `link` — controllable connections, each from one bus to the buses it delivers to |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods. It is PyPSA's `investment_periods` |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{M}^{f}`$ | `Link_big_m` over $`\mathcal{L} \times \Xi`$, `absent` where the data has no row — the bound a committed extendable link's big-M rows release it by, data prep. It is the build cap `p_nom_max` times the highest `p_max_pu`, where the cap is finite and positive. Elsewhere it is `committable_big_m` times the highest `p_max_pu` (`components.py:1082-1152`). Without that keyword, it is ten times the largest of the peak total load and the component's largest finite `p_nom` and `p_nom_max`. Where there is none of them, it is 1e6. Below the flow a solve wants, it caps that flow |
| $`\mathrm{com}^{f}`$ | `Link_committable` over $`\mathcal{L}`$ — whether flow is gated by an on/off status decision |
| $`\mathrm{rest}^{f}`$ | `Link_down_time_brought_in` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — one while the down time a link brought into the horizon is still running, zero after. It is PyPSA's stop `down_time_before` snapshots before the first, counted while `min_down_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep. Under a rolling horizon with linearised unit commitment, it is the fraction of the stop the previous window solved |
| $`\mathrm{DT}^{f}`$ | `Link_min_down_time` over $`\mathcal{L} \times \Xi`$ — least snapshots a link stays off once stopped |
| $`\mathrm{UT}^{f}`$ | `Link_min_up_time` over $`\mathcal{L} \times \Xi`$ — least snapshots a link stays on once started |
| $`\mathrm{c}^{f,\mathrm{dn}}`$ | `Link_shut_down_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one stop in this snapshot |
| $`\mathrm{c}^{f,\mathrm{on}}`$ | `Link_stand_by_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one snapshot spent on |
| $`\mathrm{c}^{f,\mathrm{up}}`$ | `Link_start_up_cost` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — cost of one start in this snapshot |
| $`\mathrm{u}^{f,0}`$ | `Link_status_initial` over $`\mathcal{L} \times \Xi`$ — one where the link was on before the first snapshot, zero where off. It is PyPSA's `up_time_before > 0` for a committable link, and one for a link that is not, whose ramp rows PyPSA starts from on (`constraints.py:323`), data prep. Under a rolling horizon, it is the status the previous window solved, a fraction where unit commitment is linearised |
| $`\mathrm{hold}^{f}`$ | `Link_up_time_brought_in` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — one while the up time a link brought into the horizon is still running, zero after. It is PyPSA's start `up_time_before` snapshots before the first, counted while `min_up_time` has not passed since (`constraints.py:302-323`, `:677-678`), data prep. Under a rolling horizon with linearised unit commitment, it is the fraction of the start the previous window solved |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f,\mathrm{com,ext}}`$ | `Link_com_ext` over $`\mathcal{L} \times \mathcal{T}`$ — a committable link with an extendable, non-modular build that is active in the snapshot's period. These are PyPSA's `com-ext` rows, whose status is relaxed against the chosen build |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dn}^{f}`$ | `Link_shut_down` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-shut_down` — how much of a committable link turns off this snapshot, capped as the status is |
| $`\mathit{up}^{f}`$ | `Link_start_up` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-start_up` — how much of a committable link turns on this snapshot, capped as the status is |
| $`u^{f}`$ | `Link_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — `Link-status` — how much of a committable link is on. It is an integer the rows below cap at one, or at the module count where the build is modular |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{Link\_commitment\_opex}`$ | `Link_commitment_opex` over $`\Xi`$ |
| $`\overleftarrow{u}^{f}`$ | `Link_previous_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the commitment state a link carries into a snapshot. It is off at the first snapshot it is active in past the first of the horizon. PyPSA reads a status it did not build as off there (`constraints.py:391`). It is the state carried over otherwise |
| $`\overleftarrow{u}^{\circ f}`$ | `Link_status_carried_over` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the state a link carries over into a snapshot: the state it brought into the horizon at the first, the previous snapshot's after that |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |

#### Conditions

**`Link_com_ext`**

```math
\mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \iff \mathrm{com}^{f}_{l} \wedge \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \wedge \mathrm{on}^{f}_{l,t} \qquad \forall\, l \in \mathcal{L},\ t \in \mathcal{T}
```

#### Variable domains

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

#### Definitions

**`Link_commitment_opex`**

```math
\mathit{Link\_commitment\_opex}_{\xi} = \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} u^{f}_{l,\xi,t} \cdot \mathrm{c}^{f,\mathrm{on}}_{l,\xi,t} \cdot \mathrm{w}_{t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} \mathit{up}^{f}_{l,\xi,t} \cdot \mathrm{c}^{f,\mathrm{up}}_{l,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} + \sum_{t \in \mathcal{T}} \sum_{l \in \mathcal{L}} \mathit{dn}^{f}_{l,\xi,t} \cdot \mathrm{c}^{f,\mathrm{dn}}_{l,\xi,t} \cdot \mathrm{w}^{y}_{\mathrm{snapshot\_period}(t)} \qquad \forall\, \xi \in \Xi
```

**`Link_previous_status`**

```math
\overleftarrow{u}^{f}_{l,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{f}_{l,t - 1} \\ \overleftarrow{u}^{\circ f}_{l,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_status_carried_over`**

```math
\overleftarrow{u}^{\circ f}_{l,\xi,t} = \begin{cases} \mathrm{u}^{f,0}_{l,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ u^{f}_{l,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

#### Subject to

**`Link_com_down_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{DT}^{f}} \mathit{dn}^{f}_{l,\xi,t'} + \mathrm{rest}^{f}_{l,\xi,t} \le \mathrm{M}^{f}_{l,\xi} - u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{DT}^{f}_{l,\xi} > 0
```

**`Link_com_ext_p_lower`**

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) + \mathrm{M}^{f}_{l,\xi} \cdot u^{f}_{l,\xi,t} - \mathrm{M}^{f}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```

**`Link_com_ext_p_lower_nonneg`**

```math
f_{l,\xi,t} \ge 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \mathrm{nonneg}^{f}_{l}
```

**`Link_com_ext_p_upper_big_m`**

```math
f_{l,\xi,t} \le \mathrm{M}^{f}_{l,\xi} \cdot u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```

**`Link_com_ext_p_upper_cap`**

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \left( F_{l} - \gamma^{f}_{l,\xi} \cdot \mu^{f,\mathrm{nom}}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```

**`Link_com_mod_p_lower`**

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{mod}}_{l} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

**`Link_com_mod_p_upper`**

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{mod}}_{l} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

**`Link_com_p_lower`**

```math
f_{l,\xi,t} \ge \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

**`Link_com_p_upper`**

```math
f_{l,\xi,t} \le \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \left( u^{f}_{l,\xi,t} - \gamma^{f}_{l,\xi} \cdot \mu^{f,u}_{l,\xi,t} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

**`Link_com_transition_shut_down`**

```math
\mathit{dn}^{f}_{l,\xi,t} \ge \overleftarrow{u}^{f}_{l,\xi,t} - u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

**`Link_com_transition_start_up`**

```math
\mathit{up}^{f}_{l,\xi,t} \ge u^{f}_{l,\xi,t} - \overleftarrow{u}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

**`Link_com_up_time`**

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < \mathrm{UT}^{f}} \mathit{up}^{f}_{l,\xi,t'} + \mathrm{hold}^{f}_{l,\xi,t} \le u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{UT}^{f}_{l,\xi} > 0
```

**`Link_shut_down_p_fixed_upper`**

```math
\mathit{dn}^{f}_{l,\xi,t} \le \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \left( \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

**`Link_shut_down_p_nom_variable_upper`**

```math
\mathit{dn}^{f}_{l,\xi,t} \le N^{f}_{l} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

**`Link_start_up_p_fixed_upper`**

```math
\mathit{up}^{f}_{l,\xi,t} \le \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \left( \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

**`Link_start_up_p_nom_variable_upper`**

```math
\mathit{up}^{f}_{l,\xi,t} \le N^{f}_{l} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

**`Link_status_p_fixed_upper`**

```math
u^{f}_{l,\xi,t} \le \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \neg \left( \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right)
```

**`Link_status_p_nom_variable_upper`**

```math
u^{f}_{l,\xi,t} \le N^{f}_{l} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t} \wedge \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0
```

#### Assumptions

**`Link_big_m_where_committed_and_extendable`**

```math
\mathrm{M}^{f}_{l,\xi} \text{ is defined} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
