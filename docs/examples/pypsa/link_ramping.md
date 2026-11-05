<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Link ramping

This file states the ramping rows of PyPSA's `Link`. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. `Link_previous_p` is the output carried into each snapshot, from `p_init` at the first where the unit came in running. `Link_ramp_up_allowance` adds the start-up ramp in the snapshot the unit turns on.

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Link_p_nom_extendable: { dims: [link], dtype: bool }
    Link_committable: { dims: [link], dtype: bool }
    Link_status_initial: { dims: [scenario, link], dtype: int }
    Link_p_nom_mod: { dims: [link] }
    Link_modules_installed: { dims: [scenario, link] }
    Link_big_m: { dims: [scenario, link] }
    Link_active: { dims: [snapshot, link], dtype: bool }
  variables:
    Link_p: { dims: [scenario, snapshot, link] }
    Link_status: { dims: [scenario, snapshot, link], domain: integer }
    Link_start_up: { dims: [scenario, snapshot, link], domain: integer }
    Link_shut_down: { dims: [scenario, snapshot, link], domain: integer }
    Link_p_nom_ext: { dims: [link] }
  expressions:
    Link_p_nom_effective: { dims: [link, scenario] }
    Link_previous_status: { dims: [link, scenario, snapshot] }
    Link_p_nom_committed: { dims: [link, scenario] }
  conditions:
    Link_com_ext: { dims: [link, snapshot] }

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
  Link_ramp_limit_up:
    description: most a link may raise its flow between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time
    dims: [scenario, snapshot, link]
    missing: absent
  Link_ramp_limit_down:
    description: most a link may lower its flow between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time
    dims: [scenario, snapshot, link]
    missing: absent
  Link_ramp_limit_start_up:
    description: most flow in the snapshot a link starts, per unit of nominal power. No value means no limit
    dims: [scenario, link]
    missing: absent
  Link_ramp_limit_shut_down:
    description: most flow in the snapshot before a link stops, per unit of nominal power. No value means no limit
    dims: [scenario, link]
    missing: absent
  Link_p_init:
    description: >-
      the flow a link brought into the horizon (PyPSA's `p_init`), read only
      where the link came in running. No value means it is unknown, and the
      link then has no ramp row at the first snapshot
    dims: [scenario, link]
    missing: 0

expressions:
  Link_previous_p:
    description: >-
      the output a link carries into a snapshot. It is nothing at the first
      snapshot it is active in past the first of the horizon: PyPSA fills an
      output it did not build with zero (`constraints.py:679`). It is the
      output carried over otherwise
    dims: [scenario, snapshot, link]
    cases:
      opening_late: { when: "position(snapshot) > 0 AND NOT shift(Link_active, along=snapshot, offset=1)", expression: 0 }
    otherwise: Link_p_carried_over
  Link_p_carried_over:
    description: >-
      the output a link carries over into a snapshot. At the first, it is the
      `p_init` it brought in where it came in running, and nothing where it
      came in off. After that, it is the previous snapshot's
    dims: [scenario, snapshot, link]
    cases:
      opening: { when: "position(snapshot) == 0", expression: Link_status_initial * Link_p_init }
    otherwise: shift(Link_p, along=snapshot, offset=1)
  Link_ramp_up_rate:
    description: >-
      the ramp limit in a link's up row, PyPSA's `ramp_limit_up`. It is the
      full build where PyPSA has none, since a start-up ramp alone builds the
      row
    dims: [scenario, snapshot, link]
    cases:
      given: { when: Link_ramp_limit_up, expression: Link_ramp_limit_up }
    otherwise: 1
  Link_ramp_down_rate:
    description: >-
      the ramp limit in a link's down row, PyPSA's `ramp_limit_down`. It is
      the full build where PyPSA has none, since a shut-down ramp alone builds
      the row
    dims: [scenario, snapshot, link]
    cases:
      given: { when: Link_ramp_limit_down, expression: Link_ramp_limit_down }
    otherwise: 1
  Link_start_up_rate:
    description: >-
      the start-up ramp in a link's up row (PyPSA's `ramp_limit_start_up`), or
      the full build where it has none
    dims: [scenario, link]
    cases:
      given: { when: Link_ramp_limit_start_up, expression: Link_ramp_limit_start_up }
    otherwise: 1
  Link_shut_down_rate:
    description: >-
      the shut-down ramp in a link's down row (PyPSA's
      `ramp_limit_shut_down`), or the full build where it has none
    dims: [scenario, link]
    cases:
      given: { when: Link_ramp_limit_shut_down, expression: Link_ramp_limit_shut_down }
    otherwise: 1
  Link_ramp_previous_status:
    description: >-
      the status a committed link's ramp rows carry into a snapshot. At the
      first snapshot, a fixed modular link that came in running has every
      module on, since the state it brought in is on or off
      (`constraints.py:1092-1097`). It is the state carried in otherwise
    dims: [scenario, snapshot, link]
    cases:
      opening_modules:
        when: "position(snapshot) == 0 AND NOT Link_p_nom_extendable AND Link_p_nom_mod > 0"
        expression: Link_status_initial * Link_modules_installed
    otherwise: Link_previous_status
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

conditions:
  Link_ramps_from_previous:
    description: >-
      a snapshot whose ramp uses a previous output. It is any snapshot but its
      period's first, and the horizon's first where the link comes in off or
      carries an initial output
    condition: >-
      position(snapshot, within=snapshot_period[period]) > 0 OR (position(snapshot) == 0 AND
      (Link_status_initial == 0 OR Link_p_init))

constraints:
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

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f}`$ | `Link_active` over $`\mathcal{L} \times \mathcal{T}`$, data another file declares |
| $`\mathrm{M}^{f}`$ | `Link_big_m` over $`\mathcal{L} \times \Xi`$, data another file declares |
| $`\mathrm{com}^{f}`$ | `Link_committable` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{N}^{f,\mathrm{fix}}`$ | `Link_modules_installed` over $`\mathcal{L} \times \Xi`$, data another file declares |
| $`\mathrm{ext}^{f}`$ | `Link_p_nom_extendable` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{f}^{\mathrm{mod}}`$ | `Link_p_nom_mod` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{u}^{f,0}`$ | `Link_status_initial` over $`\mathcal{L} \times \Xi`$, data another file declares |
| $`f`$ | `Link_p` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`F`$ | `Link_p_nom_ext` over $`\mathcal{L}`$ |
| $`\mathit{dn}^{f}`$ | `Link_shut_down` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`\mathit{up}^{f}`$ | `Link_start_up` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`u^{f}`$ | `Link_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ |
| $`\widehat{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_committed` over $`\mathcal{L} \times \Xi`$, an expression another file defines |
| $`\widetilde{\mathrm{f}}^{\mathrm{nom}}`$ | `Link_p_nom_effective` over $`\mathcal{L} \times \Xi`$, an expression another file defines |
| $`\overleftarrow{u}^{f}`$ | `Link_previous_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, an expression another file defines |
| $`\mathrm{on}^{f,\mathrm{com,ext}}`$ | `Link_com_ext` over $`\mathcal{L} \times \mathcal{T}`$, a condition another file defines |

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
| $`\mathrm{f}^{0}`$ | `Link_p_init` over $`\mathcal{L} \times \Xi`$, $`0`$ where the data has no row — the flow a link brought into the horizon (PyPSA's `p_init`), read only where the link came in running. No value means it is unknown, and the link then has no ramp row at the first snapshot |
| $`\mathrm{rd}^{f}`$ | `Link_ramp_limit_down` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a link may lower its flow between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |
| $`\mathrm{rd}^{f,\mathrm{dn}}`$ | `Link_ramp_limit_shut_down` over $`\mathcal{L} \times \Xi`$, `absent` where the data has no row — most flow in the snapshot before a link stops, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{f,\mathrm{up}}`$ | `Link_ramp_limit_start_up` over $`\mathcal{L} \times \Xi`$, `absent` where the data has no row — most flow in the snapshot a link starts, per unit of nominal power. No value means no limit |
| $`\mathrm{ru}^{f}`$ | `Link_ramp_limit_up` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$, `absent` where the data has no row — most a link may raise its flow between snapshots, per unit of nominal power. No value means no limit. The value at the later of the two snapshots applies, so the limit may change over time |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{prev}^{f}`$ | `Link_ramps_from_previous` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — a snapshot whose ramp uses a previous output. It is any snapshot but its period's first, and the horizon's first where the link comes in off or carries an initial output |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\overleftarrow{f}^{\circ}`$ | `Link_p_carried_over` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the output a link carries over into a snapshot. At the first, it is the `p_init` it brought in where it came in running, and nothing where it came in off. After that, it is the previous snapshot's |
| $`\overleftarrow{f}`$ | `Link_previous_p` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the output a link carries into a snapshot. It is nothing at the first snapshot it is active in past the first of the horizon: PyPSA fills an output it did not build with zero (`constraints.py:679`). It is the output carried over otherwise |
| $`\Delta^{f,-}`$ | `Link_ramp_down_allowance` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — how far a link may lower flow between two snapshots. It is its ramp limit of the build while it stays on, plus its shut-down ramp in the snapshot it turns off |
| $`\widetilde{\mathrm{rd}}^{f}`$ | `Link_ramp_down_rate` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the ramp limit in a link's down row, PyPSA's `ramp_limit_down`. It is the full build where PyPSA has none, since a shut-down ramp alone builds the row |
| $`\overleftarrow{\bar u}^{f}`$ | `Link_ramp_previous_status` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the status a committed link's ramp rows carry into a snapshot. At the first snapshot, a fixed modular link that came in running has every module on, since the state it brought in is on or off (`constraints.py:1092-1097`). It is the state carried in otherwise |
| $`\Delta^{f,+}`$ | `Link_ramp_up_allowance` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — how far a link may raise flow between two snapshots. It is its ramp limit of the build while it stays on, plus its start-up ramp in the snapshot it turns on |
| $`\widetilde{\mathrm{ru}}^{f}`$ | `Link_ramp_up_rate` over $`\mathcal{L} \times \Xi \times \mathcal{T}`$ — the ramp limit in a link's up row, PyPSA's `ramp_limit_up`. It is the full build where PyPSA has none, since a start-up ramp alone builds the row |
| $`\widetilde{\mathrm{rd}}^{f,\mathrm{dn}}`$ | `Link_shut_down_rate` over $`\mathcal{L} \times \Xi`$ — the shut-down ramp in a link's down row (PyPSA's `ramp_limit_shut_down`), or the full build where it has none |
| $`\widetilde{\mathrm{ru}}^{f,\mathrm{up}}`$ | `Link_start_up_rate` over $`\mathcal{L} \times \Xi`$ — the start-up ramp in a link's up row (PyPSA's `ramp_limit_start_up`), or the full build where it has none |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |

#### Conditions

**`Link_ramps_from_previous`**

```math
\mathrm{prev}^{f}_{l,\xi,t} \iff \mathrm{pos}_{\mathrm{snapshot\_period}(t)}(t) > 0 \vee \mathrm{pos}(t) = 0 \wedge \left( \mathrm{u}^{f,0}_{l,\xi} = 0 \vee \mathrm{f}^{0}_{l,\xi} \text{ is defined} \right) \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

#### Definitions

**`Link_p_carried_over`**

```math
\overleftarrow{f}^{\circ}_{l,\xi,t} = \begin{cases} \mathrm{u}^{f,0}_{l,\xi} \cdot \mathrm{f}^{0}_{l,\xi} & \text{if } \mathrm{pos}(t) = 0 \\ f_{l,\xi,t - 1} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_previous_p`**

```math
\overleftarrow{f}_{l,\xi,t} = \begin{cases} 0 & \text{if } \mathrm{pos}(t) > 0 \wedge \neg \mathrm{on}^{f}_{l,t - 1} \\ \overleftarrow{f}^{\circ}_{l,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_ramp_down_allowance`**

```math
\Delta^{f,-}_{l,\xi,t} = \begin{cases} \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot u^{f}_{l,\xi,t} + \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \left( \overleftarrow{\bar u}^{f}_{l,\xi,t} - u^{f}_{l,\xi,t} \right) & \text{if } \mathrm{com}^{f}_{l} \\ \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot \widetilde{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_ramp_down_rate`**

```math
\widetilde{\mathrm{rd}}^{f}_{l,\xi,t} = \begin{cases} \mathrm{rd}^{f}_{l,\xi,t} & \text{if } \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_ramp_previous_status`**

```math
\overleftarrow{\bar u}^{f}_{l,\xi,t} = \begin{cases} \mathrm{u}^{f,0}_{l,\xi} \cdot \mathrm{N}^{f,\mathrm{fix}}_{l,\xi} & \text{if } \mathrm{pos}(t) = 0 \wedge \neg \mathrm{ext}^{f}_{l} \wedge \mathrm{f}^{\mathrm{mod}}_{l} > 0 \\ \overleftarrow{u}^{f}_{l,\xi,t} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_ramp_up_allowance`**

```math
\Delta^{f,+}_{l,\xi,t} = \begin{cases} \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \overleftarrow{\bar u}^{f}_{l,\xi,t} + \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} \cdot \widehat{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} \cdot \left( u^{f}_{l,\xi,t} - \overleftarrow{\bar u}^{f}_{l,\xi,t} \right) & \text{if } \mathrm{com}^{f}_{l} \\ \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot \widetilde{\mathrm{f}}^{\mathrm{nom}}_{l,\xi} & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_ramp_up_rate`**

```math
\widetilde{\mathrm{ru}}^{f}_{l,\xi,t} = \begin{cases} \mathrm{ru}^{f}_{l,\xi,t} & \text{if } \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T}
```

**`Link_shut_down_rate`**

```math
\widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} = \begin{cases} \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} & \text{if } \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

**`Link_start_up_rate`**

```math
\widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} = \begin{cases} \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} & \text{if } \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \\ 1 & \text{otherwise} \end{cases} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi
```

#### Subject to

**`Link_p_ramp_limit_down`**

```math
\overleftarrow{f}_{l,\xi,t} - f_{l,\xi,t} \le \Delta^{f,-}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{f}_{l} \wedge \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \right) \wedge \mathrm{prev}^{f}_{l,\xi,t} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_p_ramp_limit_down_run_big_m`**

```math
\overleftarrow{f}_{l,\xi,t} - f_{l,\xi,t} \le \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot u^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```

**`Link_p_ramp_limit_down_shut_big_m`**

```math
\overleftarrow{f}_{l,\xi,t} - f_{l,\xi,t} \le \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot \mathit{dn}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{rd}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{rd}^{f,\mathrm{dn}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```

**`Link_p_ramp_limit_up`**

```math
f_{l,\xi,t} - \overleftarrow{f}_{l,\xi,t} \le \Delta^{f,+}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \left( \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \right) \wedge \neg \left( \mathrm{com}^{f}_{l} \wedge \mathrm{ext}^{f}_{l} \wedge \neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \right) \wedge \mathrm{prev}^{f}_{l,\xi,t} \wedge \mathrm{on}^{f}_{l,t}
```

**`Link_p_ramp_limit_up_run_big_m`**

```math
f_{l,\xi,t} - \overleftarrow{f}_{l,\xi,t} \le \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot \overleftarrow{u}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```

**`Link_p_ramp_limit_up_start_big_m`**

```math
f_{l,\xi,t} - \overleftarrow{f}_{l,\xi,t} \le \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} \cdot F_{l} + \mathrm{M}^{f}_{l,\xi} - \mathrm{M}^{f}_{l,\xi} \cdot \mathit{up}^{f}_{l,\xi,t} \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com,ext}}_{l,t} \wedge \left( \mathrm{ru}^{f}_{l,\xi,t} \text{ is defined} \vee \mathrm{ru}^{f,\mathrm{up}}_{l,\xi} \text{ is defined} \right) \wedge \mathrm{prev}^{f}_{l,\xi,t}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
