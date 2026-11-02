<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Carriers

This file states the growth limits of each carrier. It is one of the 24 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. Its limits contain the sum `Carrier_additions`, which it lists under [`given`](../../reference/language/parameters-variables-constraints.md#given). `Carrier_growth_limit` compares the additions of each period with those of the period before through [`shift`](../../reference/language/operators.md#shift). Its `edge=0` leaves the first period its bare allowance.

<!-- gallery:begin -->
```yaml
given:
  expressions:
    Carrier_additions: { dims: [period, carrier] }

dimensions:
  period:
    description: investment periods. It is PyPSA's `investment_periods`
    dtype: int
    ordered: true
  carrier:
    description: energy carriers, what a growth limit is set per

parameters:
  Carrier_max_growth:
    description: >-
      most capacity of a carrier that may be added in a period. No value means
      no limit. It is the least over the scenarios, as PyPSA takes it
      (`global_constraints.py:227-231`), data prep. PyPSA reads it only under
      `multi_investment_periods` (`global_constraints.py:220-221`). Otherwise
      you feed no value in data prep
    dims: [carrier]
    missing: neutral
  Carrier_max_relative_growth:
    description: >-
      share of the previous period's additions that may be added on top: the
      least over the scenarios, as PyPSA takes it, data prep
    dims: [carrier]

expressions:
  Carrier_relative_growth:
    description: >-
      the share of the previous period's additions in a carrier's growth
      limit, PyPSA's `max_relative_growth` clipped at zero. A negative share
      thus adds nothing and never tightens the limit
    dims: [carrier]
    cases:
      positive: { when: Carrier_max_relative_growth > 0, expression: Carrier_max_relative_growth }
    otherwise: 0

constraints:
  Carrier_growth_limit:
    description: >-
      `Carrier-growth_limit` — what a carrier adds in a period is at most its
      allowance plus a share of what it added the period before. It counts
      what its extendable components add, each build in the first period it
      is active in. The first period has no predecessor, so `edge=0` leaves it
      the bare allowance
    dims: [carrier, period]
    where: Carrier_max_growth
    expression: >-
      Carrier_additions
      - shift(Carrier_additions, along=period, offset=1, edge=0) * Carrier_relative_growth
      <= Carrier_max_growth
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathit{Carrier\_additions}`$ | `Carrier_additions` over $`\mathcal{Y} \times \mathcal{I}`$, an expression another file defines |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{Y}`$ | index $`y`$ — `period` — investment periods. It is PyPSA's `investment_periods` |
| $`\mathcal{I}`$ | index $`i`$ — `carrier` — energy carriers, what a growth limit is set per |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\overline{\Delta}`$ | `Carrier_max_growth` over $`\mathcal{I}`$, `neutral` where the data has no row — most capacity of a carrier that may be added in a period. No value means no limit. It is the least over the scenarios, as PyPSA takes it (`global_constraints.py:227-231`), data prep. PyPSA reads it only under `multi_investment_periods` (`global_constraints.py:220-221`). Otherwise you feed no value in data prep |
| $`\mathrm{r}`$ | `Carrier_max_relative_growth` over $`\mathcal{I}`$ — share of the previous period's additions that may be added on top: the least over the scenarios, as PyPSA takes it, data prep |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathrm{r}^{+}`$ | `Carrier_relative_growth` over $`\mathcal{I}`$ — the share of the previous period's additions in a carrier's growth limit, PyPSA's `max_relative_growth` clipped at zero. A negative share thus adds nothing and never tightens the limit |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |

#### Definitions

**`Carrier_relative_growth`**

```math
\mathrm{r}^{+}_{i} = \begin{cases} \mathrm{r}_{i} & \text{if } \mathrm{r}_{i} > 0 \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, i \in \mathcal{I}
```

#### Subject to

**`Carrier_growth_limit`**

```math
\mathit{Carrier\_additions}_{y,i} - \mathit{Carrier\_additions}_{y \boxminus_{0} 1,i} \cdot \mathrm{r}^{+}_{i} \le \overline{\Delta}_{i} \qquad \forall\, i \in \mathcal{I},\ y \in \mathcal{Y} \,:\, \overline{\Delta}_{i} \text{ is defined}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 24 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
