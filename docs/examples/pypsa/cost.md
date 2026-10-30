<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The cost

This file states the expected operating cost and its tail, weighted by scenario. It is one of the 24 whole specs of one topic each ([fragments](../../reference/glossary.md#fragment)) that [`merge`](../../reference/composition.md#merge) composes into the spec of `examples/pypsa.yaml`. It adds a [term](../../reference/language/named.md#adds_to) to the sum `total_cost`. `CVaR_excess` and `CVaR_def` state the conditional value at risk (CVaR) of the operating cost over the scenarios.

<!-- gallery:begin -->
```yaml
given:
  parameters:
    scenario_weight: { dims: [scenario] }
    CVaR_omega: { dims: [] }
  expressions:
    scenario_opex: { dims: [scenario] }
    total_cost: { dims: [] }

dimensions:
  scenario:
    description: the futures dispatch is chosen in, each with a weight

parameters:
  CVaR_alpha:
    description: PyPSA's `risk_preference['alpha']` — the confidence level. The tail is the other `1 - alpha` of the probability. `CVaR_alpha` has a value exactly where `CVaR_omega` has one
    dims: []
    missing: neutral

variables:
  CVaR_a:
    description: "`CVaR-a` — how far a scenario's operating cost exceeds the tail's start. It is nothing where it does not"
    dims: [scenario]
    where: CVaR_omega
    missing: neutral
    bounds:
      lower: 0
  CVaR_theta:
    description: "`CVaR-theta` — where the tail starts, the value at risk"
    dims: []
    where: CVaR_omega
    missing: neutral
  CVaR:
    description: "`CVaR` — the tail's average cost, what the objective prices at `omega`"
    dims: []
    where: CVaR_omega
    missing: neutral

expressions:
  risk_weighted_opex:
    expression: (1 - CVaR_omega) * sum(scenario_weight * scenario_opex, over=scenario) + CVaR_omega * CVaR
    adds_to: total_cost

constraints:
  CVaR_excess:
    description: "`CVaR-excess-{s}` — a scenario's operating cost beyond the tail's start is its excess. PyPSA names one row per scenario"
    dims: [scenario]
    where: CVaR_omega
    expression: CVaR_a - scenario_opex + CVaR_theta >= 0
  CVaR_def:
    description: "`CVaR-def` — the tail's average is at least where it starts plus the expected excess over the tail's probability"
    dims: []
    where: CVaR_omega
    expression: CVaR_theta + 1 / (1 - CVaR_alpha) * sum(scenario_weight * CVaR_a, over=scenario) <= CVaR
```

#### Given

| Symbol | Meaning |
|---|---|
| $`\pi`$ | `scenario_weight` over $`\Xi`$, data another file declares |
| $`\omega`$ | `CVaR_omega` (scalar), data another file declares |
| $`\mathit{scenario\_opex}`$ | `scenario_opex` over $`\Xi`$, an expression another file defines |
| $`\mathit{total\_cost}`$ | `total_cost` (scalar), an expression this file adds `risk_weighted_opex` to |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\Xi`$ | index $`\xi`$ — `scenario` — the futures dispatch is chosen in, each with a weight |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\alpha`$ | `CVaR_alpha` (scalar), `neutral` where the data has no row — PyPSA's `risk_preference['alpha']` — the confidence level. The tail is the other `1 - alpha` of the probability. `CVaR_alpha` has a value exactly where `CVaR_omega` has one |

#### Variables

| Symbol | Meaning |
|---|---|
| $`a`$ | `CVaR_a` over $`\Xi`$, `neutral` where the mask leaves it out — `CVaR-a` — how far a scenario's operating cost exceeds the tail's start. It is nothing where it does not |
| $`\theta`$ | `CVaR_theta` (scalar), `neutral` where the mask leaves it out — `CVaR-theta` — where the tail starts, the value at risk |
| $`CVaR`$ | `CVaR` (scalar), `neutral` where the mask leaves it out — `CVaR` — the tail's average cost, what the objective prices at `omega` |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{risk\_weighted\_opex}`$ | `risk_weighted_opex` (scalar) |

#### Variable domains

**`CVaR_a`**

```math
a_{\xi} \ge 0 \qquad \forall\, \xi \in \Xi \,:\, \omega \text{ is defined}
```

**`CVaR_theta`**

```math
\theta \in \mathbb{R} \qquad \text{where } \omega \text{ is defined}
```

**`CVaR`**

```math
CVaR \in \mathbb{R} \qquad \text{where } \omega \text{ is defined}
```

#### Definitions

**`risk_weighted_opex`**

```math
\mathit{risk\_weighted\_opex} = \left( 1 - \omega \right) \cdot \left( \sum_{\xi \in \Xi} \pi_{\xi} \cdot \mathit{scenario\_opex}_{\xi} \right) + \omega \cdot CVaR
```

#### Subject to

**`CVaR_excess`**

```math
a_{\xi} - \mathit{scenario\_opex}_{\xi} + \theta \ge 0 \qquad \forall\, \xi \in \Xi \,:\, \omega \text{ is defined}
```

**`CVaR_def`**

```math
\theta + \frac{1}{1 - \alpha} \cdot \left( \sum_{\xi \in \Xi} \pi_{\xi} \cdot a_{\xi} \right) \le CVaR \qquad \text{where } \omega \text{ is defined}
```
<!-- gallery:end -->

!!! info "See also"

    - [PyPSA in 24 files](index.md), for how the fragments compose
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by rung
