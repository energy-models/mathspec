<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# No risk preference

This file states that a model prices operation in expectation only. It is one of the [fragments](index.md) that merge into `examples/pypsa.yaml` and its variants. It declares `CVaR_omega`, which the components read, and an assumption that refuses data in which a risk preference is set, because this model would ignore it. A model takes this file or [the risk preference](risk.md), never both.

<!-- gallery:begin -->
```yaml
parameters:
  CVaR_omega:
    description: >-
      PyPSA's `risk_preference['omega']` — this model prices operation in
      expectation only, so no risk preference is set
    dims: []
    missing: neutral

assumptions:
  CVaR_omega_unset:
    holds: "NOT CVaR_omega"
    description: >-
      this model leaves the risk preference out, so a preference in the data
      would be ignored; take `risk.yaml` in place of `risk_neutral.yaml`
```

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\omega`$ | `CVaR_omega` (scalar), `neutral` where the data has no row — PyPSA's `risk_preference['omega']` — this model prices operation in expectation only, so no risk preference is set |

#### Assumptions

**`CVaR_omega_unset`**

```math
\neg \left( \omega \text{ is defined} \right)
```
<!-- gallery:end -->
