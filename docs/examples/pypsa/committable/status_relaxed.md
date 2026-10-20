<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Committable classes, the relaxed status

This file states the status, the starts and the stops of a committable `Generator`, `Link` and `Process` as shares in [0, 1], as `n.optimize(linearized_unit_commitment=True)` builds them, with the four rows that tighten the relaxation. It is written once and each class takes it under its own names, as [the commitment](commitment.md) says. Each of those is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. The math below prints the generator's. Its assumption refuses a modular committable unit, as PyPSA does. It reads the ramp rates, so a model that takes it also takes [the ramping](ramping.md). [PyPSA, the relaxed commitment](../../pypsa_linearized_uc.md) is the model it gives. It reads `Unit_active`, `Unit_committable`, `Unit_committed`, `Unit_p`, `Unit_p_max_pu`, `Unit_p_min_pu` and 9 more names that other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Unit_active: { dims: [snapshot, unit], dtype: bool }
    Unit_committable: { dims: [unit], dtype: bool }
    Unit_p_max_pu: { dims: [scenario, snapshot, unit] }
    Unit_p_min_pu: { dims: [scenario, snapshot, unit] }
    Unit_p_nom: { dims: [scenario, unit] }
    Unit_p_nom_extendable: { dims: [unit], dtype: bool }
    Unit_p_nom_mod: { dims: [unit] }
    Unit_shut_down_cost: { dims: [scenario, snapshot, unit] }
    Unit_start_up_cost: { dims: [scenario, snapshot, unit] }
  variables:
    Unit_p: { dims: [scenario, snapshot, unit] }
  expressions:
    Unit_ramp_down_rate: { dims: [scenario, snapshot, unit] }
    Unit_ramp_up_rate: { dims: [scenario, snapshot, unit] }
    Unit_shut_down_rate: { dims: [scenario, unit] }
    Unit_start_up_rate: { dims: [scenario, unit] }
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

variables:
  Unit_status:
    description: >-
      `-status` — how much of a committable unit is on, a share in [0, 1]
      rather than an integer: the relaxation the keyword solves
      (`variables.py:86-87`)
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    bounds:
      lower: 0
      upper: 1
  Unit_start_up:
    description: "`-start_up` — how much of a committable unit turns on this snapshot, a share in [0, 1] (`variables.py:137-138`)"
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    bounds:
      lower: 0
      upper: 1
  Unit_shut_down:
    description: "`-shut_down` — how much of a committable unit turns off this snapshot, a share in [0, 1] (`variables.py:188-189`)"
    dims: [scenario, snapshot, unit]
    where: Unit_committed
    bounds:
      lower: 0
      upper: 1

constraints:
  Unit_com_p_before:
    description: >-
      `-com-p-before` — the output a unit had entering this snapshot fits
      the share of it still on, less the share it is shutting down at the
      shut-down ramp (`constraints.py:635-649`). The translated terms vacate
      the first snapshot, as PyPSA's `sns[1:]` does
    dims: [scenario, snapshot, unit]
    where: Unit_committable AND NOT Unit_p_nom_extendable AND count(count(Unit_start_up_cost != Unit_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Unit_active
    expression: >-
      shift(Unit_p, along=snapshot, offset=1)
      - Unit_shut_down_rate * Unit_p_nom * shift(Unit_status, along=snapshot, offset=1)
      - (Unit_p_max_pu * Unit_p_nom - Unit_shut_down_rate * Unit_p_nom)
      * (Unit_status - Unit_start_up) <= 0
  Unit_com_p_current:
    description: >-
      `-com-p-current` — output fits the share on, and the share starting
      up only up to the start-up ramp (`constraints.py:652-665`)
    dims: [scenario, snapshot, unit]
    where: Unit_committable AND NOT Unit_p_nom_extendable AND count(count(Unit_start_up_cost != Unit_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND position(snapshot) > 0 AND Unit_active
    expression: >-
      Unit_p - Unit_p_max_pu * Unit_p_nom * Unit_status
      + (Unit_p_max_pu * Unit_p_nom - Unit_start_up_rate * Unit_p_nom) * Unit_start_up <= 0
  Unit_com_partly_start_up:
    description: >-
      `-com-partly-start-up` — raising output while a share is starting up
      is bounded by the ramp of the share on and the start-up ramp of the
      share coming on (`constraints.py:667-682`)
    dims: [scenario, snapshot, unit]
    where: Unit_committable AND NOT Unit_p_nom_extendable AND count(count(Unit_start_up_cost != Unit_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Unit_active
    expression: >-
      Unit_p - shift(Unit_p, along=snapshot, offset=1)
      - (Unit_p_min_pu * Unit_p_nom + Unit_ramp_up_rate * Unit_p_nom) * Unit_status
      + Unit_p_min_pu * Unit_p_nom * shift(Unit_status, along=snapshot, offset=1)
      + (Unit_p_min_pu * Unit_p_nom + Unit_ramp_up_rate * Unit_p_nom - Unit_start_up_rate * Unit_p_nom)
      * Unit_start_up <= 0
  Unit_com_partly_shut_down:
    description: >-
      `-com-partly-shut-down` — lowering output while a share is shutting
      down is bounded likewise, by the shut-down ramp (`constraints.py:684-699`)
    dims: [scenario, snapshot, unit]
    where: Unit_committable AND NOT Unit_p_nom_extendable AND count(count(Unit_start_up_cost != Unit_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Unit_active
    expression: >-
      shift(Unit_p, along=snapshot, offset=1) - Unit_p
      - Unit_shut_down_rate * Unit_p_nom * shift(Unit_status, along=snapshot, offset=1)
      + (Unit_shut_down_rate * Unit_p_nom - Unit_ramp_down_rate * Unit_p_nom) * Unit_status
      - (Unit_p_min_pu * Unit_p_nom + Unit_ramp_down_rate * Unit_p_nom - Unit_shut_down_rate * Unit_p_nom)
      * Unit_start_up <= 0

assumptions:
  Unit_committable_is_not_modular:
    holds: "NOT (Unit_p_nom_mod > 0)"
    where: "Unit_committable AND count(Unit_active, over=snapshot) > 0"
    description: >-
      a modular committable unit counts its status in modules, which the
      relaxation cannot share out — PyPSA refuses it under the keyword
      (`optimize.py:783-784`, `consistency.py:1540-1581`)
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{on}`$ | `Generator_active` over $`\mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`\mathrm{com}`$ | `Generator_committable` over $`\mathcal{G}`$, data another file declares |
| $`\overline{\mathrm{p}}`$ | `Generator_p_max_pu` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`\underline{\mathrm{p}}`$ | `Generator_p_min_pu` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\Xi \times \mathcal{G}`$, data another file declares |
| $`\mathrm{ext}`$ | `Generator_p_nom_extendable` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{p}^{\mathrm{mod}}`$ | `Generator_p_nom_mod` over $`\mathcal{G}`$, data another file declares |
| $`\mathrm{c}^{\mathrm{dn}}`$ | `Generator_shut_down_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`\mathrm{c}^{\mathrm{up}}`$ | `Generator_start_up_cost` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, data another file declares |
| $`p`$ | `Generator_p` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ |
| $`\widetilde{\mathrm{rd}}`$ | `Generator_ramp_down_rate` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, an expression another file defines |
| $`\widetilde{\mathrm{ru}}`$ | `Generator_ramp_up_rate` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$, an expression another file defines |
| $`\widetilde{\mathrm{rd}}^{\mathrm{dn}}`$ | `Generator_shut_down_rate` over $`\Xi \times \mathcal{G}`$, an expression another file defines |
| $`\widetilde{\mathrm{ru}}^{\mathrm{up}}`$ | `Generator_start_up_rate` over $`\Xi \times \mathcal{G}`$, an expression another file defines |
| $`\mathrm{on}^{\mathrm{com}}`$ | `Generator_committed` over $`\mathcal{T} \times \mathcal{G}`$, a mask another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — the units of the class this layer is renamed for |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `-status` — how much of a committable unit is on, a share in \[0, 1\] rather than an integer: the relaxation the keyword solves (`variables.py:86-87`) |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `-start_up` — how much of a committable unit turns on this snapshot, a share in \[0, 1\] (`variables.py:137-138`) |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `-shut_down` — how much of a committable unit turns off this snapshot, a share in \[0, 1\] (`variables.py:188-189`) |

#### Notation

| Symbol | Meaning |
|---|---|
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |

#### Variable domains

**`Generator_status`**

```math
0 \le u_{\xi,t,g} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_start_up`**

```math
0 \le \mathit{up}_{\xi,t,g} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

**`Generator_shut_down`**

```math
0 \le \mathit{dn}_{\xi,t,g} \le 1 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{on}^{\mathrm{com}}_{t,g}
```

#### Subject to

**`Generator_com_p_before`**

```math
p_{\xi,t - 1,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t - 1,g} - \left( \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \left( u_{\xi,t,g} - \mathit{up}_{\xi,t,g} \right) \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi',t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi',t',g} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}_{t,g}
```

**`Generator_com_p_current`**

```math
p_{\xi,t,g} - \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t,g} + \left( \overline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \mathit{up}_{\xi,t,g} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi',t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi',t',g} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{pos}(t) > 0 \wedge \mathrm{on}_{t,g}
```

**`Generator_com_partly_start_up`**

```math
p_{\xi,t,g} - p_{\xi,t - 1,g} - \left( \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} + \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot u_{\xi,t,g} + \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t - 1,g} + \left( \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} + \widetilde{\mathrm{ru}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{ru}}^{\mathrm{up}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \mathit{up}_{\xi,t,g} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi',t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi',t',g} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}_{t,g}
```

**`Generator_com_partly_shut_down`**

```math
p_{\xi,t - 1,g} - p_{\xi,t,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \cdot u_{\xi,t - 1,g} + \left( \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot u_{\xi,t,g} - \left( \underline{\mathrm{p}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} + \widetilde{\mathrm{rd}}_{\xi,t,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} - \widetilde{\mathrm{rd}}^{\mathrm{dn}}_{\xi,g} \cdot \mathrm{p}^{\mathrm{nom}}_{\xi,g} \right) \cdot \mathit{up}_{\xi,t,g} \le 0 \qquad \forall\, \xi \in \Xi,\ t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \neg \mathrm{ext}_{g} \wedge \lvert \{ \xi' \in \Xi \,:\, \lvert \{ t' \in \mathcal{T} \,:\, \mathrm{c}^{\mathrm{up}}_{\xi',t',g} \neq \mathrm{c}^{\mathrm{dn}}_{\xi',t',g} \} \rvert > 0 \} \rvert = 0 \wedge \mathrm{on}_{t,g}
```

#### Assumptions

**`Generator_committable_is_not_modular`**

```math
\neg \left( \mathrm{p}^{\mathrm{mod}}_{g} > 0 \right) \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{com}_{g} \wedge \lvert \{ t \in \mathcal{T} \,:\, \mathrm{on}_{t,g} \} \rvert > 0
```
<!-- gallery:end -->
