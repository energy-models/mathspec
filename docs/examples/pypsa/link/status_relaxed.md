<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Links, the relaxed status

This file states the status, the starts and the stops of a committable `Link` as shares in [0, 1], as `n.optimize(linearized_unit_commitment=True)` builds them, with the four rows that tighten the relaxation. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. Its assumption refuses a modular committable unit, as PyPSA does. It reads the ramp rates, so a model that takes it also takes [the ramping](ramping.md). [PyPSA, the relaxed commitment](../../pypsa_linearized_uc.md) is the model it gives. It reads `Link_active`, `Link_committable`, `Link_committed`, `Link_p`, `Link_p_max_pu`, `Link_p_min_pu` and 9 more names that other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Link_active: { dims: [snapshot, link], dtype: bool }
    Link_committable: { dims: [link], dtype: bool }
    Link_p_max_pu: { dims: [scenario, snapshot, link] }
    Link_p_min_pu: { dims: [scenario, snapshot, link] }
    Link_p_nom: { dims: [scenario, link] }
    Link_p_nom_extendable: { dims: [link], dtype: bool }
    Link_p_nom_mod: { dims: [link] }
    Link_shut_down_cost: { dims: [scenario, snapshot, link] }
    Link_start_up_cost: { dims: [scenario, snapshot, link] }
  variables:
    Link_p: { dims: [scenario, snapshot, link] }
  expressions:
    Link_ramp_down_rate: { dims: [scenario, snapshot, link] }
    Link_ramp_up_rate: { dims: [scenario, snapshot, link] }
    Link_shut_down_rate: { dims: [scenario, link] }
    Link_start_up_rate: { dims: [scenario, link] }
  masks:
    Link_committed: { dims: [snapshot, link] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  link:
    description: controllable connections, each from one bus to the buses it delivers to

variables:
  Link_status:
    description: >-
      `Link-status` — how much of a committable link is on, a share in [0, 1]
      rather than an integer: the relaxation the keyword solves
      (`variables.py:86-87`)
    dims: [scenario, snapshot, link]
    where: Link_committed
    bounds:
      lower: 0
      upper: 1
  Link_start_up:
    description: "`Link-start_up` — how much of a committable link turns on this snapshot, a share in [0, 1] (`variables.py:137-138`)"
    dims: [scenario, snapshot, link]
    where: Link_committed
    bounds:
      lower: 0
      upper: 1
  Link_shut_down:
    description: "`Link-shut_down` — how much of a committable link turns off this snapshot, a share in [0, 1] (`variables.py:188-189`)"
    dims: [scenario, snapshot, link]
    where: Link_committed
    bounds:
      lower: 0
      upper: 1

constraints:
  Link_com_p_before:
    description: >-
      `Link-com-p-before` — the output a link had entering this snapshot fits
      the share of it still on, less the share it is shutting down at the
      shut-down ramp (`constraints.py:635-649`). The translated terms vacate
      the first snapshot, as PyPSA's `sns[1:]` does
    dims: [scenario, snapshot, link]
    where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Link_active
    expression: >-
      shift(Link_p, along=snapshot, offset=1)
      - Link_shut_down_rate * Link_p_nom * shift(Link_status, along=snapshot, offset=1)
      - (Link_p_max_pu * Link_p_nom - Link_shut_down_rate * Link_p_nom)
      * (Link_status - Link_start_up) <= 0
  Link_com_p_current:
    description: >-
      `Link-com-p-current` — output fits the share on, and the share starting
      up only up to the start-up ramp (`constraints.py:652-665`)
    dims: [scenario, snapshot, link]
    where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND position(snapshot) > 0 AND Link_active
    expression: >-
      Link_p - Link_p_max_pu * Link_p_nom * Link_status
      + (Link_p_max_pu * Link_p_nom - Link_start_up_rate * Link_p_nom) * Link_start_up <= 0
  Link_com_partly_start_up:
    description: >-
      `Link-com-partly-start-up` — raising output while a share is starting up
      is bounded by the ramp of the share on and the start-up ramp of the
      share coming on (`constraints.py:667-682`)
    dims: [scenario, snapshot, link]
    where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Link_active
    expression: >-
      Link_p - shift(Link_p, along=snapshot, offset=1)
      - (Link_p_min_pu * Link_p_nom + Link_ramp_up_rate * Link_p_nom) * Link_status
      + Link_p_min_pu * Link_p_nom * shift(Link_status, along=snapshot, offset=1)
      + (Link_p_min_pu * Link_p_nom + Link_ramp_up_rate * Link_p_nom - Link_start_up_rate * Link_p_nom)
      * Link_start_up <= 0
  Link_com_partly_shut_down:
    description: >-
      `Link-com-partly-shut-down` — lowering output while a share is shutting
      down is bounded likewise, by the shut-down ramp (`constraints.py:684-699`)
    dims: [scenario, snapshot, link]
    where: Link_committable AND NOT Link_p_nom_extendable AND count(count(Link_start_up_cost != Link_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Link_active
    expression: >-
      shift(Link_p, along=snapshot, offset=1) - Link_p
      - Link_shut_down_rate * Link_p_nom * shift(Link_status, along=snapshot, offset=1)
      + (Link_shut_down_rate * Link_p_nom - Link_ramp_down_rate * Link_p_nom) * Link_status
      - (Link_p_min_pu * Link_p_nom + Link_ramp_down_rate * Link_p_nom - Link_shut_down_rate * Link_p_nom)
      * Link_start_up <= 0

assumptions:
  Link_committable_is_not_modular:
    holds: "NOT (Link_p_nom_mod > 0)"
    where: "Link_committable AND count(Link_active, over=snapshot) > 0"
    description: >-
      a modular committable unit counts its status in modules, which the
      relaxation cannot share out — PyPSA refuses it under the keyword
      (`optimize.py:783-784`, `consistency.py:1540-1581`)
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}^{f}`$ | `Link_active` over $`\mathcal{T} \times \mathcal{L}`$, data another file declares |
| $`\mathrm{com}^{f}`$ | `Link_committable` over $`\mathcal{L}`$, data another file declares |
| $`\overline{\mathrm{f}}`$ | `Link_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$, data another file declares |
| $`\underline{\mathrm{f}}`$ | `Link_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$, data another file declares |
| $`\mathrm{f}^{\mathrm{nom}}`$ | `Link_p_nom` over $`\Xi \times \mathcal{L}`$, data another file declares |
| $`\mathrm{ext}^{f}`$ | `Link_p_nom_extendable` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{f}^{\mathrm{mod}}`$ | `Link_p_nom_mod` over $`\mathcal{L}`$, data another file declares |
| $`\mathrm{c}^{f,\mathrm{dn}}`$ | `Link_shut_down_cost` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$, data another file declares |
| $`\mathrm{c}^{f,\mathrm{up}}`$ | `Link_start_up_cost` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$, data another file declares |
| $`f`$ | `Link_p` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ |
| $`\widetilde{\mathrm{rd}}^{f}`$ | `Link_ramp_down_rate` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$, an expression another file defines |
| $`\widetilde{\mathrm{ru}}^{f}`$ | `Link_ramp_up_rate` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$, an expression another file defines |
| $`\widetilde{\mathrm{rd}}^{f,\mathrm{dn}}`$ | `Link_shut_down_rate` over $`\Xi \times \mathcal{L}`$, an expression another file defines |
| $`\widetilde{\mathrm{ru}}^{f,\mathrm{up}}`$ | `Link_start_up_rate` over $`\Xi \times \mathcal{L}`$, an expression another file defines |
| $`\mathrm{on}^{f,\mathrm{com}}`$ | `Link_committed` over $`\mathcal{T} \times \mathcal{L}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{L}`$ | index $`l`$ — `link` — controllable connections, each from one bus to the buses it delivers to |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u^{f}`$ | `Link_status` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — `Link-status` — how much of a committable link is on, a share in \[0, 1\] rather than an integer: the relaxation the keyword solves (`variables.py:86-87`) |
| $`\mathit{up}^{f}`$ | `Link_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — `Link-start_up` — how much of a committable link turns on this snapshot, a share in \[0, 1\] (`variables.py:137-138`) |
| $`\mathit{dn}^{f}`$ | `Link_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{L}`$ — `Link-shut_down` — how much of a committable link turns off this snapshot, a share in \[0, 1\] (`variables.py:188-189`) |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |

#### Variable domains

**`Link_status`**

```math
0 \le u^{f}_{\xi,t,l} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

**`Link_start_up`**

```math
0 \le \mathit{up}^{f}_{\xi,t,l} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

**`Link_shut_down`**

```math
0 \le \mathit{dn}^{f}_{\xi,t,l} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{on}^{f,\mathrm{com}}_{t,l}
```

#### Subject to

**`Link_com_p_before`**

```math
f_{\xi,t - 1,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t - 1,l} - \left( \overline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \left( u^{f}_{\xi,t,l} - \mathit{up}^{f}_{\xi,t,l} \right) \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi',t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi',t',l} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{f}_{t,l}
```

**`Link_com_p_current`**

```math
f_{\xi,t,l} - \overline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t,l} + \left( \overline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \mathit{up}^{f}_{\xi,t,l} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi',t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi',t',l} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{pos}(t) > 0 \wedge \mathrm{on}^{f}_{t,l}
```

**`Link_com_partly_start_up`**

```math
f_{\xi,t,l} - f_{\xi,t - 1,l} - \left( \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} + \widetilde{\mathrm{ru}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot u^{f}_{\xi,t,l} + \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t - 1,l} + \left( \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} + \widetilde{\mathrm{ru}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{ru}}^{f,\mathrm{up}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \mathit{up}^{f}_{\xi,t,l} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi',t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi',t',l} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{f}_{t,l}
```

**`Link_com_partly_shut_down`**

```math
f_{\xi,t - 1,l} - f_{\xi,t,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \cdot u^{f}_{\xi,t - 1,l} + \left( \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{rd}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot u^{f}_{\xi,t,l} - \left( \underline{\mathrm{f}}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} + \widetilde{\mathrm{rd}}^{f}_{\xi,t,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} - \widetilde{\mathrm{rd}}^{f,\mathrm{dn}}_{\xi,l} \cdot \mathrm{f}^{\mathrm{nom}}_{\xi,l} \right) \cdot \mathit{up}^{f}_{\xi,t,l} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \neg \mathrm{ext}^{f}_{l} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{f,\mathrm{up}}_{\xi',t',l} \neq \mathrm{c}^{f,\mathrm{dn}}_{\xi',t',l} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}^{f}_{t,l}
```

#### Assumptions

**`Link_committable_is_not_modular`**

```math
\neg \left( \mathrm{f}^{\mathrm{mod}}_{l} > 0 \right) \qquad \forall\, l \in \mathcal{L} \,:\, \mathrm{com}^{f}_{l} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}^{f}_{t,l} \} \rvert > 0
```
<!-- gallery:end -->
