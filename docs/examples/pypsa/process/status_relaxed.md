<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Processes, the relaxed status

This file states the status, the starts and the stops of a committable `Process` as shares in [0, 1], as `n.optimize(linearized_unit_commitment=True)` builds them, with the four rows that tighten the relaxation. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. Its assumption refuses a modular committable unit, as PyPSA does. It reads the ramp rates, so a model that takes it also takes [the ramping](ramping.md). [PyPSA, the relaxed commitment](../../pypsa_linearized_uc.md) is the model it gives. It reads `Process_active`, `Process_committable`, `Process_committed`, `Process_p`, `Process_p_max_pu`, `Process_p_min_pu` and 9 more names that other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Process_active: { dims: [snapshot, process], dtype: bool }
    Process_committable: { dims: [process], dtype: bool }
    Process_p_max_pu: { dims: [scenario, snapshot, process] }
    Process_p_min_pu: { dims: [scenario, snapshot, process] }
    Process_p_nom: { dims: [scenario, process] }
    Process_p_nom_extendable: { dims: [process], dtype: bool }
    Process_p_nom_mod: { dims: [process] }
    Process_shut_down_cost: { dims: [scenario, snapshot, process] }
    Process_start_up_cost: { dims: [scenario, snapshot, process] }
  variables:
    Process_p: { dims: [scenario, snapshot, process] }
  expressions:
    Process_ramp_down_rate: { dims: [scenario, snapshot, process] }
    Process_ramp_up_rate: { dims: [scenario, snapshot, process] }
    Process_shut_down_rate: { dims: [scenario, process] }
    Process_start_up_rate: { dims: [scenario, process] }
  masks:
    Process_committed: { dims: [snapshot, process] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  process:
    description: generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate

variables:
  Process_status:
    description: >-
      `Process-status` — how much of a committable process is on, a share in [0, 1]
      rather than an integer: the relaxation the keyword solves
      (`variables.py:86-87`)
    dims: [scenario, snapshot, process]
    where: Process_committed
    bounds:
      lower: 0
      upper: 1
  Process_start_up:
    description: "`Process-start_up` — how much of a committable process turns on this snapshot, a share in [0, 1] (`variables.py:137-138`)"
    dims: [scenario, snapshot, process]
    where: Process_committed
    bounds:
      lower: 0
      upper: 1
  Process_shut_down:
    description: "`Process-shut_down` — how much of a committable process turns off this snapshot, a share in [0, 1] (`variables.py:188-189`)"
    dims: [scenario, snapshot, process]
    where: Process_committed
    bounds:
      lower: 0
      upper: 1

constraints:
  Process_com_p_before:
    description: >-
      `Process-com-p-before` — the output a process had entering this snapshot fits
      the share of it still on, less the share it is shutting down at the
      shut-down ramp (`constraints.py:635-649`). The translated terms vacate
      the first snapshot, as PyPSA's `sns[1:]` does
    dims: [scenario, snapshot, process]
    where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Process_active
    expression: >-
      shift(Process_p, along=snapshot, offset=1)
      - Process_shut_down_rate * Process_p_nom * shift(Process_status, along=snapshot, offset=1)
      - (Process_p_max_pu * Process_p_nom - Process_shut_down_rate * Process_p_nom)
      * (Process_status - Process_start_up) <= 0
  Process_com_p_current:
    description: >-
      `Process-com-p-current` — output fits the share on, and the share starting
      up only up to the start-up ramp (`constraints.py:652-665`)
    dims: [scenario, snapshot, process]
    where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND position(snapshot) > 0 AND Process_active
    expression: >-
      Process_p - Process_p_max_pu * Process_p_nom * Process_status
      + (Process_p_max_pu * Process_p_nom - Process_start_up_rate * Process_p_nom) * Process_start_up <= 0
  Process_com_partly_start_up:
    description: >-
      `Process-com-partly-start-up` — raising output while a share is starting up
      is bounded by the ramp of the share on and the start-up ramp of the
      share coming on (`constraints.py:667-682`)
    dims: [scenario, snapshot, process]
    where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Process_active
    expression: >-
      Process_p - shift(Process_p, along=snapshot, offset=1)
      - (Process_p_min_pu * Process_p_nom + Process_ramp_up_rate * Process_p_nom) * Process_status
      + Process_p_min_pu * Process_p_nom * shift(Process_status, along=snapshot, offset=1)
      + (Process_p_min_pu * Process_p_nom + Process_ramp_up_rate * Process_p_nom - Process_start_up_rate * Process_p_nom)
      * Process_start_up <= 0
  Process_com_partly_shut_down:
    description: >-
      `Process-com-partly-shut-down` — lowering output while a share is shutting
      down is bounded likewise, by the shut-down ramp (`constraints.py:684-699`)
    dims: [scenario, snapshot, process]
    where: Process_committable AND NOT Process_p_nom_extendable AND count(count(Process_start_up_cost != Process_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Process_active
    expression: >-
      shift(Process_p, along=snapshot, offset=1) - Process_p
      - Process_shut_down_rate * Process_p_nom * shift(Process_status, along=snapshot, offset=1)
      + (Process_shut_down_rate * Process_p_nom - Process_ramp_down_rate * Process_p_nom) * Process_status
      - (Process_p_min_pu * Process_p_nom + Process_ramp_down_rate * Process_p_nom - Process_shut_down_rate * Process_p_nom)
      * Process_start_up <= 0

assumptions:
  Process_committable_is_not_modular:
    holds: "NOT (Process_p_nom_mod > 0)"
    where: "Process_committable AND count(Process_active, over=snapshot) > 0"
    description: >-
      a modular committable unit counts its status in modules, which the
      relaxation cannot share out — PyPSA refuses it under the keyword
      (`optimize.py:783-784`, `consistency.py:1540-1581`)
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{z}`$ | `Process_active` over $`\mathcal{T} \times \mathcal{J}`$, data another file declares |
| $`\mathrm{com}^{z}`$ | `Process_committable` over $`\mathcal{J}`$, data another file declares |
| $`\overline{\mathrm{z}}`$ | `Process_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, data another file declares |
| $`\underline{\mathrm{z}}`$ | `Process_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, data another file declares |
| $`\mathrm{z}^{\mathrm{nom}}`$ | `Process_p_nom` over $`\Xi \times \mathcal{J}`$, data another file declares |
| $`\mathrm{ext}^{z}`$ | `Process_p_nom_extendable` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{z}^{\mathrm{mod}}`$ | `Process_p_nom_mod` over $`\mathcal{J}`$, data another file declares |
| $`\mathrm{c}^{z,\mathrm{dn}}`$ | `Process_shut_down_cost` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, data another file declares |
| $`\mathrm{c}^{z,\mathrm{up}}`$ | `Process_start_up_cost` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, data another file declares |
| $`z`$ | `Process_p` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ |
| $`\widetilde{\mathrm{rd}}^{z}`$ | `Process_ramp_down_rate` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, an expression another file defines |
| $`\widetilde{\mathrm{ru}}^{z}`$ | `Process_ramp_up_rate` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$, an expression another file defines |
| $`\widetilde{\mathrm{rd}}^{z,\mathrm{dn}}`$ | `Process_shut_down_rate` over $`\Xi \times \mathcal{J}`$, an expression another file defines |
| $`\widetilde{\mathrm{ru}}^{z,\mathrm{up}}`$ | `Process_start_up_rate` over $`\Xi \times \mathcal{J}`$, an expression another file defines |
| $`\mathrm{on}^{z,\mathrm{com}}`$ | `Process_committed` over $`\mathcal{T} \times \mathcal{J}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{J}`$ | index $`j`$ — `process` — generalized multi-port converters, each with an internal power that every port draws or delivers at its own rate |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u^{z}`$ | `Process_status` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-status` — how much of a committable process is on, a share in \[0, 1\] rather than an integer: the relaxation the keyword solves (`variables.py:86-87`) |
| $`\mathit{up}^{z}`$ | `Process_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-start_up` — how much of a committable process turns on this snapshot, a share in \[0, 1\] (`variables.py:137-138`) |
| $`\mathit{dn}^{z}`$ | `Process_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{J}`$ — `Process-shut_down` — how much of a committable process turns off this snapshot, a share in \[0, 1\] (`variables.py:188-189`) |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |

#### Variable domains

**`Process_status`**

```math
0 \le u^{z}_{\xi,t,j} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_start_up`**

```math
0 \le \mathit{up}^{z}_{\xi,t,j} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

**`Process_shut_down`**

```math
0 \le \mathit{dn}^{z}_{\xi,t,j} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{on}^{z,\mathrm{com}}_{t,j}
```

#### Subject to

**`Process_com_p_before`**

```math
z_{\xi,t - 1,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t - 1,j} - \left( \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \left( u^{z}_{\xi,t,j} - \mathit{up}^{z}_{\xi,t,j} \right) \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi',t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi',t',j} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_com_p_current`**

```math
z_{\xi,t,j} - \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t,j} + \left( \overline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \mathit{up}^{z}_{\xi,t,j} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi',t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi',t',j} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{pos}(t) > 0 \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_com_partly_start_up`**

```math
z_{\xi,t,j} - z_{\xi,t - 1,j} - \left( \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} + \widetilde{\mathrm{ru}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot u^{z}_{\xi,t,j} + \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t - 1,j} + \left( \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} + \widetilde{\mathrm{ru}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{ru}}^{z,\mathrm{up}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \mathit{up}^{z}_{\xi,t,j} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi',t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi',t',j} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{z}_{t,j}
```

**`Process_com_partly_shut_down`**

```math
z_{\xi,t - 1,j} - z_{\xi,t,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \cdot u^{z}_{\xi,t - 1,j} + \left( \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{rd}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot u^{z}_{\xi,t,j} - \left( \underline{\mathrm{z}}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} + \widetilde{\mathrm{rd}}^{z}_{\xi,t,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} - \widetilde{\mathrm{rd}}^{z,\mathrm{dn}}_{\xi,j} \cdot \mathrm{z}^{\mathrm{nom}}_{\xi,j} \right) \cdot \mathit{up}^{z}_{\xi,t,j} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \neg \mathrm{ext}^{z}_{j} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{z,\mathrm{up}}_{\xi',t',j} \neq \mathrm{c}^{z,\mathrm{dn}}_{\xi',t',j} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{z}_{t,j}
```

#### Assumptions

**`Process_committable_is_not_modular`**

```math
\neg \left( \mathrm{z}^{\mathrm{mod}}_{j} > 0 \right) \qquad \forall\, j \in \mathcal{J} \,:\, \mathrm{com}^{z}_{j} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{z}_{t,j} \} \rvert > 0
```
<!-- gallery:end -->
