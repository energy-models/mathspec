<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Linearised unit commitment in PyPSA

This page states the spec of the model that
`n.optimize(linearized_unit_commitment=True)` builds in PyPSA. The file
`examples/variants/pypsa_linearized_uc.yaml` states only the change to a base
spec (a [patch](../reference/glossary.md#patch)), and its base is the file
of [the PyPSA example](pypsa/index.md), `examples/pypsa.yaml`.
[`override`](../reference/composition.md#override) lays the patch over the
base:

```python
import mathspec as ms

spec = ms.override('examples/pypsa.yaml', ['examples/variants/pypsa_linearized_uc.yaml'])
```

`spec` is the base with the patch laid over it.

The patch relaxes the status (`variables.py:91-92`), the start (`:142-143`)
and the stop (`:193-194`) of each committable unit. PyPSA refuses a modular
committable unit under the keyword (`optimize.py:841-842`). The other rows of
the integer run have their scenarios, periods and `active` conditions.

Five steps of the PyPSA ladder ([rungs](../reference/glossary.md#rung)),
numbered 12, 44, 47, 67 and 74, run under the keyword. Their
[rung tables](https://github.com/energy-models/mathspec/blob/main/examples/references/pypsa/README.md#the-relaxed-commitment)
list the rows that PyPSA builds for each, with the status of each row in the
patched spec.

## The file

<!-- gallery:begin -->
A committable generator, link or process has a status, starts and stops that are shares in [0, 1]. The patch states `n.optimize(linearized_unit_commitment=True)` over `examples/pypsa.yaml`, and the shares relax that file's integers (`variables.py:91-92`). Four rows PyPSA adds only under the keyword tighten the relaxation (`constraints.py:684-792`). PyPSA builds them only for a unit with a fixed build whose start and stop cost the same in every snapshot and every scenario. The patch states an assumption of no modular committable unit, which PyPSA refuses under the keyword and a tool refuses when data is attached. Every other row is the integer run's.

### `Generator-status`

`Generator_status`

```yaml
Generator_status:
  description: >-
    `Generator-status` — how much of a committable unit is on, a share in [0, 1]
    rather than an integer: the relaxation the keyword solves
    (`variables.py:91-92`)
  domain: null
  bounds:
    upper: 1
```

```math
0 \le u_{g,\xi,t} \le 1 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

### `Generator-start_up`

`Generator_start_up`

```yaml
Generator_start_up:
  description: "`Generator-start_up` — how much of a committable unit turns on this snapshot, a share in [0, 1] (`variables.py:142-143`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{up}_{g,\xi,t} \le 1 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

### `Generator-shut_down`

`Generator_shut_down`

```yaml
Generator_shut_down:
  description: "`Generator-shut_down` — how much of a committable unit turns off this snapshot, a share in [0, 1] (`variables.py:193-194`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{dn}_{g,\xi,t} \le 1 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{\mathrm{com}}_{g,t}
```

### `Link-status`

`Link_status`

```yaml
Link_status:
  description: >-
    `Link-status` — how much of a committable link is on, a share in [0, 1]
    rather than an integer: the relaxation the keyword solves
    (`variables.py:91-92`)
  domain: null
  bounds:
    upper: 1
```

```math
0 \le u^{f}_{l,\xi,t} \le 1 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

### `Link-start_up`

`Link_start_up`

```yaml
Link_start_up:
  description: "`Link-start_up` — how much of a committable link turns on this snapshot, a share in [0, 1] (`variables.py:142-143`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{up}^{f}_{l,\xi,t} \le 1 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

### `Link-shut_down`

`Link_shut_down`

```yaml
Link_shut_down:
  description: "`Link-shut_down` — how much of a committable link turns off this snapshot, a share in [0, 1] (`variables.py:193-194`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{dn}^{f}_{l,\xi,t} \le 1 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{f,\mathrm{com}}_{l,t}
```

### `Process-status`

`Process_status`

```yaml
Process_status:
  description: >-
    `Process-status` — how much of a committable process is on, a share in [0, 1]
    rather than an integer: the relaxation the keyword solves
    (`variables.py:91-92`)
  domain: null
  bounds:
    upper: 1
```

```math
0 \le u^{z}_{j,\xi,t} \le 1 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

### `Process-start_up`

`Process_start_up`

```yaml
Process_start_up:
  description: "`Process-start_up` — how much of a committable process turns on this snapshot, a share in [0, 1] (`variables.py:142-143`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{up}^{z}_{j,\xi,t} \le 1 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

### `Process-shut_down`

`Process_shut_down`

```yaml
Process_shut_down:
  description: "`Process-shut_down` — how much of a committable process turns off this snapshot, a share in [0, 1] (`variables.py:193-194`)"
  domain: null
  bounds:
    upper: 1
```

```math
0 \le \mathit{dn}^{z}_{j,\xi,t} \le 1 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{on}^{z,\mathrm{com}}_{j,t}
```

### `Generator-com-p-before`

`Generator_com_p_before`

```yaml
Generator_com_p_before:
  description: >-
    `Generator-com-p-before` — the output a unit had entering this snapshot
    fits the share of it still on (`constraints.py:729-742`). The share it
    is shutting down counts only at the shut-down ramp. At the first snapshot,
    the unit carries in the state and output it brought into the horizon,
    and has no row where it came in running without an initial output
    (`constraints.py:712-719`)
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Generator_active AND (position(snapshot) > 0 OR Generator_status_initial == 0 OR Generator_p_init)
  expression: >-
    Generator_previous_p
    - Generator_shut_down_rate * Generator_p_nom * Generator_previous_status
    - (Generator_p_max_pu * Generator_p_nom - Generator_shut_down_rate * Generator_p_nom)
    * (Generator_status - Generator_start_up) <= 0
```

```math
\overleftarrow{p}_{g,\xi,t} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot \overleftarrow{u}_{g,\xi,t} - \left( \overline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \right) \cdot \left( u_{g,\xi,t} - \mathit{up}_{g,\xi,t} \right) \le 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{g,\xi',t'} \neq \mathrm{c}^{\mathrm{dn}}_{g,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}_{g,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{0}_{g,\xi} = 0 \vee \mathrm{p}^{0}_{g,\xi} \text{ is defined} \right)
```

### `Generator-com-p-current`

`Generator_com_p_current`

```yaml
Generator_com_p_current:
  description: >-
    `Generator-com-p-current` — output fits the share on, and the share starting
    up only up to the start-up ramp (`constraints.py:744-757`)
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Generator_active
  expression: >-
    Generator_p - Generator_p_max_pu * Generator_p_nom * Generator_status
    + (Generator_p_max_pu * Generator_p_nom - Generator_start_up_rate * Generator_p_nom) * Generator_start_up <= 0
```

```math
p_{g,\xi,t} - \overline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot u_{g,\xi,t} + \left( \overline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} - \widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \right) \cdot \mathit{up}_{g,\xi,t} \le 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{g,\xi',t'} \neq \mathrm{c}^{\mathrm{dn}}_{g,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}_{g,t}
```

### `Generator-com-partly-start-up`

`Generator_com_partly_start_up`

```yaml
Generator_com_partly_start_up:
  description: >-
    `Generator-com-partly-start-up` — raising output while a share is
    starting up is bounded by two ramps (`constraints.py:759-774`). They are
    the ramp of the share on and the start-up ramp of the share coming on
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Generator_active AND (position(snapshot) > 0 OR Generator_status_initial == 0 OR Generator_p_init)
  expression: >-
    Generator_p - Generator_previous_p
    - (Generator_p_min_pu * Generator_p_nom + Generator_ramp_up_rate * Generator_p_nom) * Generator_status
    + Generator_p_min_pu * Generator_p_nom * Generator_previous_status
    + (Generator_p_min_pu * Generator_p_nom + Generator_ramp_up_rate * Generator_p_nom - Generator_start_up_rate * Generator_p_nom)
    * Generator_start_up <= 0
```

```math
p_{g,\xi,t} - \overleftarrow{p}_{g,\xi,t} - \left( \underline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} + \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \right) \cdot u_{g,\xi,t} + \underline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot \overleftarrow{u}_{g,\xi,t} + \left( \underline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} + \widetilde{\mathrm{ru}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} - \widetilde{\mathrm{ru}}^{\mathrm{up}}_{g,\xi} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \right) \cdot \mathit{up}_{g,\xi,t} \le 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{g,\xi',t'} \neq \mathrm{c}^{\mathrm{dn}}_{g,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}_{g,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{0}_{g,\xi} = 0 \vee \mathrm{p}^{0}_{g,\xi} \text{ is defined} \right)
```

### `Generator-com-partly-shut-down`

`Generator_com_partly_shut_down`

```yaml
Generator_com_partly_shut_down:
  description: >-
    `Generator-com-partly-shut-down` — lowering output while a share is shutting
    down is bounded likewise, by the shut-down ramp (`constraints.py:776-791`)
  dims: [scenario, snapshot, generator]
  where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Generator_active AND (position(snapshot) > 0 OR Generator_status_initial == 0 OR Generator_p_init)
  expression: >-
    Generator_previous_p - Generator_p
    - Generator_shut_down_rate * Generator_p_nom * Generator_previous_status
    + (Generator_shut_down_rate * Generator_p_nom - Generator_ramp_down_rate * Generator_p_nom) * Generator_status
    - (Generator_p_min_pu * Generator_p_nom + Generator_ramp_down_rate * Generator_p_nom - Generator_shut_down_rate * Generator_p_nom)
    * Generator_start_up <= 0
```

```math
\overleftarrow{p}_{g,\xi,t} - p_{g,\xi,t} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \cdot \overleftarrow{u}_{g,\xi,t} + \left( \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} - \widetilde{\mathrm{rd}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \right) \cdot u_{g,\xi,t} - \left( \underline{\mathrm{p}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} + \widetilde{\mathrm{rd}}_{g,\xi,t} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{g,\xi} \cdot \mathrm{p}^{\mathrm{nom}}_{g,\xi} \right) \cdot \mathit{up}_{g,\xi,t} \le 0 \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{g,\xi',t'} \neq \mathrm{c}^{\mathrm{dn}}_{g,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}_{g,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{0}_{g,\xi} = 0 \vee \mathrm{p}^{0}_{g,\xi} \text{ is defined} \right)
```

### `Link-com-p-before`

`Link_com_p_before`

```yaml
Link_com_p_before:
  description: >-
    `Link-com-p-before` — the output a link had entering this snapshot fits
    the share of it still on (`constraints.py:729-742`). The share it is
    shutting down counts only at the shut-down ramp. At the first snapshot,
    the link carries in the state and output it brought into the horizon,
    and has no row where it came in running without an initial output
    (`constraints.py:712-719`)
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Link_active AND (position(snapshot) > 0 OR Link_status_initial == 0 OR Link_p_init)
  expression: >-
    Link_previous_p
    - Link_shut_down_rate * Link_p_nom * Link_previous_status
    - (Link_p_max_pu * Link_p_nom - Link_shut_down_rate * Link_p_nom)
    * (Link_status - Link_start_up) <= 0
```

```math
\overleftarrow{f}_{l,\xi,t} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \overleftarrow{u}^{f}_{l,\xi,t} - \left( \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \right) \cdot \left( u^{f}_{l,\xi,t} - \mathit{up}^{f}_{l,\xi,t} \right) \le 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{l,\xi',t'} \neq \mathrm{c}^{f,\mathrm{dn}}_{l,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{f}_{l,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{f,0}_{l,\xi} = 0 \vee \mathrm{f}^{0}_{l,\xi} \text{ is defined} \right)
```

### `Link-com-p-current`

`Link_com_p_current`

```yaml
Link_com_p_current:
  description: >-
    `Link-com-p-current` — output fits the share on, and the share starting
    up only up to the start-up ramp (`constraints.py:744-757`)
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Link_active
  expression: >-
    Link_p - Link_p_max_pu * Link_p_nom * Link_status
    + (Link_p_max_pu * Link_p_nom - Link_start_up_rate * Link_p_nom) * Link_start_up <= 0
```

```math
f_{l,\xi,t} - \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot u^{f}_{l,\xi,t} + \left( \overline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} - \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \right) \cdot \mathit{up}^{f}_{l,\xi,t} \le 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{l,\xi',t'} \neq \mathrm{c}^{f,\mathrm{dn}}_{l,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{f}_{l,t}
```

### `Link-com-partly-start-up`

`Link_com_partly_start_up`

```yaml
Link_com_partly_start_up:
  description: >-
    `Link-com-partly-start-up` — raising output while a share is starting up
    is bounded by two ramps (`constraints.py:759-774`). They are the ramp of
    the share on and the start-up ramp of the share coming on
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Link_active AND (position(snapshot) > 0 OR Link_status_initial == 0 OR Link_p_init)
  expression: >-
    Link_p - Link_previous_p
    - (Link_p_min_pu * Link_p_nom + Link_ramp_up_rate * Link_p_nom) * Link_status
    + Link_p_min_pu * Link_p_nom * Link_previous_status
    + (Link_p_min_pu * Link_p_nom + Link_ramp_up_rate * Link_p_nom - Link_start_up_rate * Link_p_nom)
    * Link_start_up <= 0
```

```math
f_{l,\xi,t} - \overleftarrow{f}_{l,\xi,t} - \left( \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} + \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \right) \cdot u^{f}_{l,\xi,t} + \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \overleftarrow{u}^{f}_{l,\xi,t} + \left( \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} + \widetilde{\mathrm{ru}}^{f}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} - \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{l,\xi} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \right) \cdot \mathit{up}^{f}_{l,\xi,t} \le 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{l,\xi',t'} \neq \mathrm{c}^{f,\mathrm{dn}}_{l,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{f}_{l,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{f,0}_{l,\xi} = 0 \vee \mathrm{f}^{0}_{l,\xi} \text{ is defined} \right)
```

### `Link-com-partly-shut-down`

`Link_com_partly_shut_down`

```yaml
Link_com_partly_shut_down:
  description: >-
    `Link-com-partly-shut-down` — lowering output while a share is shutting
    down is bounded likewise, by the shut-down ramp (`constraints.py:776-791`)
  dims: [scenario, snapshot, link]
  where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Link_active AND (position(snapshot) > 0 OR Link_status_initial == 0 OR Link_p_init)
  expression: >-
    Link_previous_p - Link_p
    - Link_shut_down_rate * Link_p_nom * Link_previous_status
    + (Link_shut_down_rate * Link_p_nom - Link_ramp_down_rate * Link_p_nom) * Link_status
    - (Link_p_min_pu * Link_p_nom + Link_ramp_down_rate * Link_p_nom - Link_shut_down_rate * Link_p_nom)
    * Link_start_up <= 0
```

```math
\overleftarrow{f}_{l,\xi,t} - f_{l,\xi,t} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \cdot \overleftarrow{u}^{f}_{l,\xi,t} + \left( \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} - \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \right) \cdot u^{f}_{l,\xi,t} - \left( \underline{\mathrm{f}}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} + \widetilde{\mathrm{rd}}^{f}_{l,\xi,t} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{l,\xi} \cdot \mathrm{f}^{\mathrm{nom}}_{l,\xi} \right) \cdot \mathit{up}^{f}_{l,\xi,t} \le 0 \qquad \forall\, l \in \mathcal{L},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{l,\xi',t'} \neq \mathrm{c}^{f,\mathrm{dn}}_{l,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{f}_{l,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{f,0}_{l,\xi} = 0 \vee \mathrm{f}^{0}_{l,\xi} \text{ is defined} \right)
```

### `Process-com-p-before`

`Process_com_p_before`

```yaml
Process_com_p_before:
  description: >-
    `Process-com-p-before` — the output a process had entering this snapshot
    fits the share of it still on (`constraints.py:729-742`). The share it
    is shutting down counts only at the shut-down ramp. At the first snapshot,
    the process carries in the state and output it brought into the horizon,
    and has no row where it came in running without an initial output
    (`constraints.py:712-719`)
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Process_active AND (position(snapshot) > 0 OR Process_status_initial == 0 OR Process_p_init)
  expression: >-
    Process_previous_p
    - Process_shut_down_rate * Process_p_nom * Process_previous_status
    - (Process_p_max_pu * Process_p_nom - Process_shut_down_rate * Process_p_nom)
    * (Process_status - Process_start_up) <= 0
```

```math
\overleftarrow{z}_{j,\xi,t} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \overleftarrow{u}^{z}_{j,\xi,t} - \left( \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \right) \cdot \left( u^{z}_{j,\xi,t} - \mathit{up}^{z}_{j,\xi,t} \right) \le 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{j,\xi',t'} \neq \mathrm{c}^{z,\mathrm{dn}}_{j,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{z}_{j,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{z,0}_{j,\xi} = 0 \vee \mathrm{z}^{0}_{j,\xi} \text{ is defined} \right)
```

### `Process-com-p-current`

`Process_com_p_current`

```yaml
Process_com_p_current:
  description: >-
    `Process-com-p-current` — output fits the share on, and the share starting
    up only up to the start-up ramp (`constraints.py:744-757`)
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Process_active
  expression: >-
    Process_p - Process_p_max_pu * Process_p_nom * Process_status
    + (Process_p_max_pu * Process_p_nom - Process_start_up_rate * Process_p_nom) * Process_start_up <= 0
```

```math
z_{j,\xi,t} - \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot u^{z}_{j,\xi,t} + \left( \overline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} - \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \right) \cdot \mathit{up}^{z}_{j,\xi,t} \le 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{j,\xi',t'} \neq \mathrm{c}^{z,\mathrm{dn}}_{j,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{z}_{j,t}
```

### `Process-com-partly-start-up`

`Process_com_partly_start_up`

```yaml
Process_com_partly_start_up:
  description: >-
    `Process-com-partly-start-up` — raising output while a share is starting
    up is bounded by two ramps (`constraints.py:759-774`). They are the ramp
    of the share on and the start-up ramp of the share coming on
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Process_active AND (position(snapshot) > 0 OR Process_status_initial == 0 OR Process_p_init)
  expression: >-
    Process_p - Process_previous_p
    - (Process_p_min_pu * Process_p_nom + Process_ramp_up_rate * Process_p_nom) * Process_status
    + Process_p_min_pu * Process_p_nom * Process_previous_status
    + (Process_p_min_pu * Process_p_nom + Process_ramp_up_rate * Process_p_nom - Process_start_up_rate * Process_p_nom)
    * Process_start_up <= 0
```

```math
z_{j,\xi,t} - \overleftarrow{z}_{j,\xi,t} - \left( \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} + \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \right) \cdot u^{z}_{j,\xi,t} + \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \overleftarrow{u}^{z}_{j,\xi,t} + \left( \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} + \widetilde{\mathrm{ru}}^{z}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} - \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{j,\xi} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \right) \cdot \mathit{up}^{z}_{j,\xi,t} \le 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{j,\xi',t'} \neq \mathrm{c}^{z,\mathrm{dn}}_{j,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{z}_{j,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{z,0}_{j,\xi} = 0 \vee \mathrm{z}^{0}_{j,\xi} \text{ is defined} \right)
```

### `Process-com-partly-shut-down`

`Process_com_partly_shut_down`

```yaml
Process_com_partly_shut_down:
  description: >-
    `Process-com-partly-shut-down` — lowering output while a share is shutting
    down is bounded likewise, by the shut-down ramp (`constraints.py:776-791`)
  dims: [scenario, snapshot, process]
  where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Process_active AND (position(snapshot) > 0 OR Process_status_initial == 0 OR Process_p_init)
  expression: >-
    Process_previous_p - Process_p
    - Process_shut_down_rate * Process_p_nom * Process_previous_status
    + (Process_shut_down_rate * Process_p_nom - Process_ramp_down_rate * Process_p_nom) * Process_status
    - (Process_p_min_pu * Process_p_nom + Process_ramp_down_rate * Process_p_nom - Process_shut_down_rate * Process_p_nom)
    * Process_start_up <= 0
```

```math
\overleftarrow{z}_{j,\xi,t} - z_{j,\xi,t} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \cdot \overleftarrow{u}^{z}_{j,\xi,t} + \left( \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} - \widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \right) \cdot u^{z}_{j,\xi,t} - \left( \underline{\mathrm{z}}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} + \widetilde{\mathrm{rd}}^{z}_{j,\xi,t} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{j,\xi} \cdot \mathrm{z}^{\mathrm{nom}}_{j,\xi} \right) \cdot \mathit{up}^{z}_{j,\xi,t} \le 0 \qquad \forall\, j \in \mathcal{J},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{j,\xi',t'} \neq \mathrm{c}^{z,\mathrm{dn}}_{j,\xi',t'} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{z}_{j,t} \wedge \left( \mathrm{pos}(t) > 0 \vee \mathrm{u}^{z,0}_{j,\xi} = 0 \vee \mathrm{z}^{0}_{j,\xi} \text{ is defined} \right)
```

### `Generator_marginal_cost_incremental`

`Generator_marginal_cost_incremental`

```yaml
Generator_marginal_cost_incremental:
  description: >-
    `Generator-marginal_cost_piecewise` — the running cost of a generator
    with a curve is at least the curve at its output, stated by segments
    filled in order, where linopy chooses the incremental rows. No status
    gates it, because no generator with a curve is committable under the
    keyword
  activity: null
```

```math
C^{\mathrm{curve}}_{g,\xi,t} \ge \mathrm{pwl}_{b \in \mathcal{B} \,:\, \neg \mathrm{lp} \wedge \mathrm{curve}_{g} \wedge \mathrm{on}_{g,t} \wedge \mathrm{p}^{\mathrm{curve}}_{b,g} \text{ is defined}}(\mathrm{p}^{\mathrm{curve}}_{b,g},\ \mathrm{C}^{\mathrm{curve}}_{b,g})(p_{g,\xi,t}) \qquad \forall\, g \in \mathcal{G},\ \xi \in \Xi,\ t \in \mathcal{T}
```

### `Generator_marginal_cost_curve_is_not_committable`

`Generator_marginal_cost_curve_is_not_committable`

```yaml
Generator_marginal_cost_curve_is_not_committable:
  holds: "NOT Generator_committable"
  where: "Generator_marginal_cost_curve"
  description: >-
    a generator with a piecewise `marginal_cost` curve is not committable.
    PyPSA gates such a curve by the status share (`optimize.py:314-318`,
    `piecewise.py:193-203`), and a curve gate is binary or integer
```

```math
\neg \mathrm{com}_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{curve}_{g}
```

### `Generator_committable_is_not_modular`

`Generator_committable_is_not_modular`

```yaml
Generator_committable_is_not_modular:
  holds: "NOT (Generator_p_nom_mod > 0)"
  where: "Generator_committable AND count(Generator_active, over=snapshot) > 0"
  description: >-
    a modular committable unit counts its status in modules, which the
    relaxation cannot share out. PyPSA refuses it under the keyword
    (`optimize.py:841-842`, `consistency.py:1588-1629`)
```

```math
\neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}_{g,t} \} \rvert > 0
```

### `Link_committable_is_not_modular`

`Link_committable_is_not_modular`

```yaml
Link_committable_is_not_modular:
  holds: "NOT (Link_p_nom_mod > 0)"
  where: "Link_committable AND count(Link_active, over=snapshot) > 0"
  description: >-
    a modular committable unit counts its status in modules, which the
    relaxation cannot share out. PyPSA refuses it under the keyword
    (`optimize.py:841-842`, `consistency.py:1588-1629`)
```

```math
\neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{f}_{l,t} \} \rvert > 0
```

### `Process_committable_is_not_modular`

`Process_committable_is_not_modular`

```yaml
Process_committable_is_not_modular:
  holds: "NOT (Process_p_nom_mod > 0)"
  where: "Process_committable AND count(Process_active, over=snapshot) > 0"
  description: >-
    a modular committable unit counts its status in modules, which the
    relaxation cannot share out. PyPSA refuses it under the keyword
    (`optimize.py:841-842`, `consistency.py:1588-1629`)
```

```math
\neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{z}_{j,t} \} \rvert > 0
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA](pypsa/index.md), for the base spec and its fragments
    - [PyPSA: scope and refusals](pypsa/scope.md), for the `n.optimize()` keywords that the
      base spec states and the data that PyPSA refuses
    - [`override`](../reference/composition.md#override), for how a patch is laid
      over its base
    - [Patch](../reference/glossary.md#patch), for the term
