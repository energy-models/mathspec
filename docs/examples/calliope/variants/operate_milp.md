<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Operate mode, with MILP

A patch of [Calliope in fragments](../index.md). The half of Calliope's `operate.yaml` that lands on the MILP fragment: the units bought are data too. It is laid after the MILP patch and operate mode. A patch is not a spec, so it prints as the declarations it writes, in the spec it lands on.

<!-- gallery:begin -->
```python
ms.override(
    ms.merge(base + ['extensions/milp.yaml']),
    ['variants/milp.yaml', 'variants/operate.yaml', 'variants/operate_milp.yaml'],
)
```

```yaml title="variants/operate_milp.yaml"
parameters:
  purchased_units:
    description: "`purchased_units` — the units bought, fixed in operate mode. Calliope's default is `.inf`"
    dims: [nodes, techs]

variables:
  purchased_units: null

constraints:
  storage_capacity_units_milp: null
  flow_capacity_units_milp: null
  unit_capacity_max_systemwide_milp: null
  unit_capacity_min_systemwide_milp: null
  flow_capacity_max_purchase_milp: null
  flow_capacity_max_purchase_milp_big_m: null
  storage_capacity_max_purchase_milp: null
  flow_capacity_minimum: null
  flow_capacity_minimum_purchased: null
  storage_capacity_minimum: null
  storage_capacity_minimum_purchased: null
  area_use_minimum: null
  area_use_minimum_purchased: null
  source_capacity_minimum: null
  source_capacity_minimum_purchased: null
  flow_capacity_systemwide_min_purchased: null

expressions:
  cost_investment_purchase: null
```

Removed: `purchased_units`, `cost_investment_purchase`, `storage_capacity_units_milp`, `flow_capacity_units_milp`, `unit_capacity_max_systemwide_milp`, `unit_capacity_min_systemwide_milp`, `flow_capacity_max_purchase_milp`, `flow_capacity_max_purchase_milp_big_m`, `storage_capacity_max_purchase_milp`, `flow_capacity_minimum`, `flow_capacity_minimum_purchased`, `storage_capacity_minimum`, `storage_capacity_minimum_purchased`, `area_use_minimum`, `area_use_minimum_purchased`, `source_capacity_minimum`, `source_capacity_minimum_purchased`, `flow_capacity_systemwide_min_purchased`.
<!-- gallery:end -->
