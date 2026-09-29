<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# SPORES

A patch of [Calliope in fragments](../index.md). Calliope's `spores.yaml`: the objective is the SPORES score of the capacity built, and the least-cost objective becomes a row capped at the least cost plus a slack. The row reads the sums the objective read, so a file that adds a cost is capped too. The iteration that updates the scores is a loop of solves, and is not in the math. A patch is not a spec, so it prints as the declarations it writes, in the spec it lands on.

<!-- gallery:begin -->
```python
ms.override(
    ms.merge(base),
    ['variants/spores.yaml'],
)
```

```yaml title="variants/spores.yaml"
parameters:
  spores_baseline_cost:
    description: >-
      `spores_baseline_cost` — the least cost of the system, which a SPORES
      iteration may exceed by its slack. Calliope's default is `.inf`
    dims: []
  spores_slack:
    description: "`spores_slack` — the share by which a SPORES iteration may exceed the least cost"
    dims: []
  spores_score:
    description: "`spores_score` — the score a technology at a node carries from the SPORES iterations before"
    dims: [nodes, techs, carriers]

constraints:
  total_system_cost_max:
    description: >-
      `total_system_cost_max` — the cost the least-cost objective reads is at
      most the least cost plus the slack. It reads the same sums the
      objective did, so a file that adds a cost adds it here too
    dims: []
    expression: system_cost + penalty <= spores_baseline_cost * (1 + spores_slack)

expressions:
  spores_score_cumulative:
    description: "`spores_score_cumulative` — the SPORES score, reported with the results"
    expression: spores_score
  spores_baseline_cost_tracked:
    description: "`spores_baseline_cost_tracked` — the SPORES baseline cost, reported with the results"
    expression: spores_baseline_cost

objective:
  description: >-
    `min_spores` — the SPORES score of the flow capacity built, plus the
    penalty on unmet demand
  expression: sum(flow_cap * spores_score) + penalty
```

**`spores_score_cumulative`**

```math
\mathrm{spores\_score\_cumulative}_{n,i,c} = \mathrm{spores\_score}_{n,i,c} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C}
```

**`spores_baseline_cost_tracked`**

```math
\mathrm{spores\_baseline\_cost\_tracked} = \mathrm{spores\_baseline\_cost}
```

**`total_system_cost_max`**

```math
\mathit{system\_cost} + \mathit{penalty} \le \mathrm{spores\_baseline\_cost} \cdot \left( 1 + \mathrm{spores\_slack} \right)
```

**The objective**

```math
\min \sum_{n \in \mathcal{N},\ i \in \mathcal{I},\ c \in \mathcal{C}} \mathit{flow\_cap}_{n,i,c} \cdot \mathrm{spores\_score}_{n,i,c} + \mathit{penalty}
```
<!-- gallery:end -->
