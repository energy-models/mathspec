<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Power flow

This file states Kirchhoff's voltage law around each cycle. It is one of the 25 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It lists the sum `Cycle_angle_sum` under [`given`](../../reference/language/parameters-variables-constraints.md#given) and adds nothing to it. The lines and the transformers add their terms to it.

<!-- gallery:begin -->
```yaml
given:
  expressions:
    Cycle_angle_sum:
      dims: [cycle, scenario, snapshot]
      description: >-
        the voltage angle differences around a cycle: every branch flow times
        its cycle weight, and every transformer phase shift

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight
  snapshot:
    description: dispatch periods
    dtype: datetime
    ordered: true
  cycle:
    description: >-
      independent cycles of the passive network graph, the cycle basis, data
      prep. Each period has its own basis, of the branches that are active in it. A
      label is a position in that period's basis, so one label is a different
      cycle in another period
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
  Cycle_in_basis:
    description: >-
      whether a period's cycle basis reaches the cycle label, data prep. A
      label beyond the basis of the period has no Kirchhoff voltage law row
    dims: [period, cycle]
    dtype: bool

constraints:
  Kirchhoff_Voltage_Law:
    description: >-
      `Kirchhoff-Voltage-Law` — around every independent cycle the
      impedance-weighted flows sum to nothing. This makes the linear power
      flow physical rather than transport. A transformer's flow weighs its
      effective reactance, and its phase shift enters the cycle sum too. The
      shift is a constant where it is fixed. Where a phase-shifting
      transformer chooses its shift, it is the shift decision times its cycle
      weight. A snapshot uses the cycles of its own period, of the branches
      that are active in it (`constraints.py:1710-1729`). A cycle label that
      period's basis does not reach has no row
    dims: [scenario, snapshot, cycle]
    where: at(Cycle_in_basis, by=snapshot_period[period])
    expression: Cycle_angle_sum == 0
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Cycle\_angle\_sum}`$ | `Cycle_angle_sum` over $`\mathcal{C} \times \Xi \times \mathcal{T}`$, an expression another file defines — the voltage angle differences around a cycle: every branch flow times its cycle weight, and every transformer phase shift |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{C}`$ | index $`c`$ — `cycle` — independent cycles of the passive network graph, the cycle basis, data prep. Each period has its own basis, of the branches that are active in it. A label is a position in that period's basis, so one label is a different cycle in another period |
| $`\mathcal{Y}`$ | index $`y`$ — `period` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — investment periods. It is PyPSA's `investment_periods` |
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` with $`\mathrm{snapshot\_period}: \mathcal{T} \to \mathcal{Y}`$ — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{Cycle\_in\_basis}`$ | `Cycle_in_basis` over $`\mathcal{C} \times \mathcal{Y}`$ — whether a period's cycle basis reaches the cycle label, data prep. A label beyond the basis of the period has no Kirchhoff voltage law row |

#### Subject to

**`Kirchhoff_Voltage_Law`**

```math
\mathit{Cycle\_angle\_sum}_{c,\xi,t} = 0 \qquad \forall\, c \in \mathcal{C},\ \xi \in \Xi,\ t \in \mathcal{T} \,:\, \mathrm{Cycle\_in\_basis}_{c,\mathrm{snapshot\_period}(t)}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 25 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
