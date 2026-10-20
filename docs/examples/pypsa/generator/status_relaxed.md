<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Generators, the relaxed status

This file states the status, the starts and the stops of a committable `Generator` as shares in [0, 1], as `n.optimize(linearized_unit_commitment=True)` builds them, with the four rows that tighten the relaxation. It is one of the [fragments](../index.md) that merge into `examples/pypsa.yaml` and its variants. Its assumption refuses a modular committable unit, as PyPSA does. It reads the ramp rates, so a model that takes it also takes [the ramping](ramping.md). [PyPSA, the relaxed commitment](../../pypsa_linearized_uc.md) is the model it gives. It reads `Generator_active`, `Generator_committable`, `Generator_committed`, `Generator_p`, `Generator_p_max_pu`, `Generator_p_min_pu` and 9 more names that other fragments declare, and lists them under [`given`](../../../reference/language/parameters-variables-constraints.md#given).

<!-- gallery:begin -->
```yaml
given:
  parameters:
    Generator_active: { dims: [snapshot, generator], dtype: bool }
    Generator_committable: { dims: [generator], dtype: bool }
    Generator_p_max_pu: { dims: [scenario, snapshot, generator] }
    Generator_p_min_pu: { dims: [scenario, snapshot, generator] }
    Generator_p_nom: { dims: [scenario, generator] }
    Generator_p_nom_extendable: { dims: [generator], dtype: bool }
    Generator_p_nom_mod: { dims: [generator] }
    Generator_shut_down_cost: { dims: [scenario, snapshot, generator] }
    Generator_start_up_cost: { dims: [scenario, snapshot, generator] }
  variables:
    Generator_p: { dims: [scenario, snapshot, generator] }
  expressions:
    Generator_ramp_down_rate: { dims: [scenario, snapshot, generator] }
    Generator_ramp_up_rate: { dims: [scenario, snapshot, generator] }
    Generator_shut_down_rate: { dims: [scenario, generator] }
    Generator_start_up_rate: { dims: [scenario, generator] }
  masks:
    Generator_committed: { dims: [snapshot, generator] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  generator:
    description: generating units, each on one bus

variables:
  Generator_status:
    description: >-
      `Generator-status` — how much of a committable unit is on, a share in [0, 1]
      rather than an integer: the relaxation the keyword solves
      (`variables.py:86-87`)
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    bounds:
      lower: 0
      upper: 1
  Generator_start_up:
    description: "`Generator-start_up` — how much of a committable unit turns on this snapshot, a share in [0, 1] (`variables.py:137-138`)"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    bounds:
      lower: 0
      upper: 1
  Generator_shut_down:
    description: "`Generator-shut_down` — how much of a committable unit turns off this snapshot, a share in [0, 1] (`variables.py:188-189`)"
    dims: [scenario, snapshot, generator]
    where: Generator_committed
    bounds:
      lower: 0
      upper: 1

constraints:
  Generator_com_p_before:
    description: >-
      `Generator-com-p-before` — the output a unit had entering this snapshot fits
      the share of it still on, less the share it is shutting down at the
      shut-down ramp (`constraints.py:635-649`). The translated terms vacate
      the first snapshot, as PyPSA's `sns[1:]` does
    dims: [scenario, snapshot, generator]
    where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Generator_active
    expression: >-
      shift(Generator_p, along=snapshot, offset=1)
      - Generator_shut_down_rate * Generator_p_nom * shift(Generator_status, along=snapshot, offset=1)
      - (Generator_p_max_pu * Generator_p_nom - Generator_shut_down_rate * Generator_p_nom)
      * (Generator_status - Generator_start_up) <= 0
  Generator_com_p_current:
    description: >-
      `Generator-com-p-current` — output fits the share on, and the share starting
      up only up to the start-up ramp (`constraints.py:652-665`)
    dims: [scenario, snapshot, generator]
    where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND position(snapshot) > 0 AND Generator_active
    expression: >-
      Generator_p - Generator_p_max_pu * Generator_p_nom * Generator_status
      + (Generator_p_max_pu * Generator_p_nom - Generator_start_up_rate * Generator_p_nom) * Generator_start_up <= 0
  Generator_com_partly_start_up:
    description: >-
      `Generator-com-partly-start-up` — raising output while a share is starting up
      is bounded by the ramp of the share on and the start-up ramp of the
      share coming on (`constraints.py:667-682`)
    dims: [scenario, snapshot, generator]
    where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Generator_active
    expression: >-
      Generator_p - shift(Generator_p, along=snapshot, offset=1)
      - (Generator_p_min_pu * Generator_p_nom + Generator_ramp_up_rate * Generator_p_nom) * Generator_status
      + Generator_p_min_pu * Generator_p_nom * shift(Generator_status, along=snapshot, offset=1)
      + (Generator_p_min_pu * Generator_p_nom + Generator_ramp_up_rate * Generator_p_nom - Generator_start_up_rate * Generator_p_nom)
      * Generator_start_up <= 0
  Generator_com_partly_shut_down:
    description: >-
      `Generator-com-partly-shut-down` — lowering output while a share is shutting
      down is bounded likewise, by the shut-down ramp (`constraints.py:684-699`)
    dims: [scenario, snapshot, generator]
    where: Generator_committable AND NOT Generator_p_nom_extendable AND count(count(Generator_start_up_cost != Generator_shut_down_cost, over=snapshot) > 0, over=scenario) == 0 AND Generator_active
    expression: >-
      shift(Generator_p, along=snapshot, offset=1) - Generator_p
      - Generator_shut_down_rate * Generator_p_nom * shift(Generator_status, along=snapshot, offset=1)
      + (Generator_shut_down_rate * Generator_p_nom - Generator_ramp_down_rate * Generator_p_nom) * Generator_status
      - (Generator_p_min_pu * Generator_p_nom + Generator_ramp_down_rate * Generator_p_nom - Generator_shut_down_rate * Generator_p_nom)
      * Generator_start_up <= 0

assumptions:
  Generator_committable_is_not_modular:
    holds: "NOT (Generator_p_nom_mod > 0)"
    where: "Generator_committable AND count(Generator_active, over=snapshot) > 0"
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
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units, each on one bus |

#### Variables

| Symbol | Meaning |
|---|---|
| $`u`$ | `Generator_status` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-status` — how much of a committable unit is on, a share in \[0, 1\] rather than an integer: the relaxation the keyword solves (`variables.py:86-87`) |
| $`\mathit{up}`$ | `Generator_start_up` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-start_up` — how much of a committable unit turns on this snapshot, a share in \[0, 1\] (`variables.py:137-138`) |
| $`\mathit{dn}`$ | `Generator_shut_down` over $`\Xi \times \mathcal{T} \times \mathcal{G}`$ — `Generator-shut_down` — how much of a committable unit turns off this snapshot, a share in \[0, 1\] (`variables.py:188-189`) |

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
