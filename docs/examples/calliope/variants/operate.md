<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Operate mode

A patch of [Calliope in fragments](../index.md). Calliope's `operate.yaml`: every capacity is data, not a decision. The patch turns each capacity variable into a parameter of the same name, removes the rows and the costs that only a capacity decision has, and leaves the operating cost. Calliope's rolling horizon is a loop of solves, and is not in the math. A patch is not a spec, so it prints as the declarations it writes, in the spec it lands on.

<!-- gallery:begin -->
```python
ms.override(
    ms.merge(base),
    ['variants/operate.yaml'],
)
```

```yaml title="variants/operate.yaml"
parameters:
  flow_cap:
    description: "`flow_cap` — the flow capacity, fixed in operate mode. Calliope's default is `.inf`"
    dims: [nodes, techs, carriers]
  area_use:
    description: "`area_use` — the area used, fixed in operate mode. Calliope's default is `.inf`"
    dims: [nodes, techs]
  source_cap:
    description: "`source_cap` — the source capacity, fixed in operate mode. Calliope's default is `.inf`"
    dims: [nodes, techs]
  storage_cap:
    description: "`storage_cap` — the storage capacity, fixed in operate mode. Calliope's default is `.inf`"
    dims: [nodes, techs]

variables:
  flow_cap: null
  area_use: null
  source_cap: null
  storage_cap: null

constraints:
  flow_capacity_per_storage_capacity_min: null
  flow_capacity_per_storage_capacity_max: null
  source_capacity_equals_flow_capacity: null
  force_zero_area_use: null
  area_use_per_flow_capacity: null
  area_use_capacity_per_loc: null
  flow_capacity_systemwide_max: null
  flow_capacity_systemwide_min: null
  symmetric_transmission: null

expressions:
  cost_investment: null
  cost_investment_annualised: null
  cost_investment_flow_cap: null
  cost_investment_storage_cap: null
  cost_investment_source_cap: null
  cost_investment_area_use: null
  cost_operation_fixed: null
  cost_flow_cap_sum: null
  depreciation_rate: null
  flows_cost_investment: null
  flows_cost_operation_fixed: null
  flow_cap_from: null
  flow_cap_to: null
  cost:
    description: "`cost` — the operating cost of a technology, over every time step"
    expression: sum(cost_operation_variable, over=timesteps)

assumptions:
  operate_mode_cyclic_storage:
    description: Calliope's `operate_mode_cyclic_storage` — a store in operate mode is not cyclic
    holds: NOT (cyclic_storage AND (base_tech == 'storage' OR include_storage))
```

**`cost`**

```math
\mathit{cost}_{n,i,k} = \sum_{t \in \mathcal{T}} \mathit{cost}^{\mathrm{operation,variable}}_{n,i,k,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ k \in \mathcal{K}
```

**`operate_mode_cyclic_storage`**

```math
\neg \left( \mathrm{cyclic\_storage}_{n,i} \wedge \left( \mathrm{base\_tech}_{i} = \text{'}\mathrm{storage}\text{'} \vee \mathrm{include\_storage}_{n,i} \right) \right) \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I}
```

Removed: `flow_cap`, `area_use`, `source_cap`, `storage_cap`, `cost_investment`, `cost_investment_annualised`, `cost_investment_flow_cap`, `cost_investment_storage_cap`, `cost_investment_source_cap`, `cost_investment_area_use`, `cost_operation_fixed`, `cost_flow_cap_sum`, `depreciation_rate`, `flows_cost_investment`, `flows_cost_operation_fixed`, `flow_cap_from`, `flow_cap_to`, `flow_capacity_per_storage_capacity_min`, `flow_capacity_per_storage_capacity_max`, `source_capacity_equals_flow_capacity`, `force_zero_area_use`, `area_use_per_flow_capacity`, `area_use_capacity_per_loc`, `flow_capacity_systemwide_max`, `flow_capacity_systemwide_min`, `symmetric_transmission`.
<!-- gallery:end -->
