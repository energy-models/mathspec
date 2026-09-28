<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Calliope in fragments

[Calliope](https://github.com/calliope-project/calliope) states its math in
YAML: a base, modes laid over it, and examples of math a modeller adds. This
is all of it, from Calliope `v0.7.0` (`src/calliope/math/` and
`docs/user_defined_math/examples/`), as files under `examples/calliope/`.
[The port record](port.md) lists every Calliope block with how it is stated
here, and what mathspec is missing where the port is not one block for one.

Calliope composes its math by overriding: a mode or an example restates a
base block whole to change it. Here, three kinds of file do that work, and
[the PyPSA split](../pypsa/index.md) uses the first two.

- **A base fragment** is one topic of Calliope's base math. `merge` composes
  the fragments into one spec.
- **An extension** adds to the base: new rows, new decisions, and a term to a
  sum the base declares. `merge` composes it with the base. Where Calliope
  restates `system_balance`, `cost_investment`, `cost_operation_fixed` or the
  objective to add one term, the extension adds the term and no base file
  changes.
- **A variant** changes what the base states: a mode, or an example that
  rewrites a base row. `override` lays it over the composition. A variant is
  a patch, not a spec, and it prints as the declarations it writes.

## Compose a model

```python
from pathlib import Path

import mathspec as ms

here = Path('examples/calliope')
base = sorted(here.glob('*.yaml'))

plan = ms.merge(base)
milp = ms.override(ms.merge([*base, here / 'extensions/milp.yaml']), [here / 'variants/milp.yaml'])
operate = ms.override(plan, [here / 'variants/operate.yaml'])
spores = ms.override(plan, [here / 'variants/spores.yaml'])
clustered = ms.override(plan, [here / 'variants/storage_inter_cluster.yaml'])
```

A mode and an extension compose as Calliope's do: the MILP fragment and its
patch, then operate mode and its MILP half, then an example.

```python
fuel = ms.merge([*base, here / 'extensions/fuel_dist.yaml'])
chp = ms.override(ms.merge([*base, here / 'extensions/chp_htp.yaml']), [here / 'variants/chp_htp.yaml'])
```

## What a file needs beside it

A fragment reads what it does not declare under
[`given`](../../reference/language/declarations.md#given), and loads and
prints alone. A model needs the file that declares each name a fragment
reads, and `merge` keeps what no file declares under `given:`.

- `settings`, `balance`, `flows` and `cost` are the core. They read one
  another, and the four compose with nothing left under `given:`.
- `conversion` and `transmission` read `flows` alone. `storage`, `export`,
  `feasibility` and `reporting` read the core, and `reporting` reads `export`.
- `area`, `demand` and `supply` read one another. A source or a sink per unit
  of area reads `area_use`, and `area_use` is built where a source or a sink
  is per unit of area. Compose the three together. Without `demand` and
  `supply`, `area` keeps `sink_unit` and `source_unit` under `given:`.
- `supply_storage` couples `supply` and `storage`, and needs both.
- `extensions/milp.yaml` reads the capacities of `storage`, `area` and
  `supply`. `piecewise_linear_costs`, `piecewise_linear_efficiency` and
  `uptime_downtime_limits` read the units it builds, so they need it.
- `piecewise_linear_costs` and `sos2_piecewise_linear_costs` both declare
  `piecewise_cost_investment`, so `merge` refuses the two together. The CHP
  variants both rewrite `balance_conversion`. Calliope's examples are
  alternatives in the same way.

## Conventions

- **Names are Calliope's.** A declaration Calliope names is spelled as
  Calliope spells it, and its description opens with that name. A sub-expression
  Calliope writes as `$name` is a named expression. A name Calliope has no word
  for, such as a term of a sum, carries the name of the file that adds it.
- **A parameter's default is data preparation.** Calliope reads a missing
  value as the parameter's `default:` in arithmetic, and as not given in a
  `where:`. Here a missing row reads as `0` and as false. Where a default is
  not zero and the math reads the value, data prep fills it, and the
  description says so. A bound has a row wherever its variable has one, so
  data prep fills its default too. Where the math reads the parameter only
  behind a `where:` that tests it, the description says "given only where set".
- **A variable with a mask is zero outside it.** Calliope's `default: 0` is
  `absence: zero`, so a sum of costs keeps its terms where one of them is
  masked.
- **A parameter carries the dimensions Calliope's examples give it.** The
  timesteps are added where Calliope resamples the parameter.

<!-- gallery:begin -->
### The sums

| Sum | Over | Declared in | The terms, by the fragment that adds each |
| --- | --- | --- | --- |
| `cost_investment` | `nodes, techs, costs` | [cost](cost.md) | [`cost_investment_area_use`](area.md), [`flows_cost_investment`](flows.md), [`cost_investment_purchase`](extensions/milp.md), [`piecewise_cost_investment_term`](extensions/piecewise_linear_costs.md), [`cost_investment_piecewise`](extensions/sos2_piecewise_linear_costs.md), [`cost_investment_storage_cap`](storage.md), [`cost_investment_source_cap`](supply.md) |
| `carrier_flow` | `nodes, carriers, timesteps` | [balance](balance.md) | [`export_carrier_flow`](export.md), [`feasibility_carrier_flow`](feasibility.md), [`flows_carrier_flow`](flows.md), [`fuel_dist_carrier_flow`](extensions/fuel_dist.md) |
| `cost_operation_variable` | `nodes, techs, costs, timesteps` | [cost](cost.md) | [`export_cost_operation_variable`](export.md), [`flows_cost_operation_variable`](flows.md), [`supply_cost_operation_variable`](supply.md) |
| `system_cost` | nothing: one number | [settings](settings.md) | [`cost_of_techs`](cost.md), [`fuel_dist_system_cost`](extensions/fuel_dist.md) |
| `cost_operation_fixed` | `nodes, techs, costs` | [cost](cost.md) | [`flows_cost_operation_fixed`](flows.md), [`cost_month_peak_charge`](extensions/monthly_peak_flow_charge.md) |
| `penalty` | nothing: one number | [settings](settings.md) | [`unmet_demand_penalty`](feasibility.md) |

### The fragments

| Fragment | Parameters | Variables | Constraints | Reads | Adds to |
| --- | --- | --- | --- | --- | --- |
| [area](area.md) | 5 | 1 | 3 | 5 | `cost_investment` |
| [balance](balance.md) | 0 | 0 | 1 | 2 |  |
| [conversion](conversion.md) | 0 | 0 | 1 | 4 |  |
| [cost](cost.md) | 5 | 0 | 0 | 4 | `system_cost` |
| [demand](demand.md) | 4 | 0 | 3 | 5 |  |
| [export](export.md) | 4 | 1 | 1 | 5 | `carrier_flow`, `cost_operation_variable` |
| [feasibility](feasibility.md) | 0 | 2 | 0 | 6 | `carrier_flow`, `penalty` |
| [flows](flows.md) | 22 | 3 | 7 | 7 | `carrier_flow`, `cost_investment`, `cost_operation_variable`, `cost_operation_fixed` |
| [reporting](reporting.md) | 0 | 0 | 0 | 6 |  |
| [settings](settings.md) | 4 | 0 | 0 | 0 |  |
| [storage](storage.md) | 10 | 2 | 6 | 7 | `cost_investment` |
| [supply](supply.md) | 10 | 2 | 6 | 10 | `cost_investment`, `cost_operation_variable` |
| [supply_storage](supply_storage.md) | 0 | 0 | 1 | 7 |  |
| [transmission](transmission.md) | 0 | 0 | 2 | 5 |  |
| [annual_energy_balance](extensions/annual_energy_balance.md) | 5 | 0 | 5 | 4 |  |
| [chp_htp](extensions/chp_htp.md) | 4 | 0 | 6 | 6 |  |
| [demand_share_per_timestep_decision](extensions/demand_share_per_timestep_decision.md) | 2 | 1 | 3 | 2 |  |
| [fuel_dist](extensions/fuel_dist.md) | 4 | 1 | 3 | 4 | `carrier_flow`, `system_cost` |
| [max_time_varying](extensions/max_time_varying.md) | 1 | 0 | 1 | 3 |  |
| [milp](extensions/milp.md) | 11 | 4 | 26 | 22 | `cost_investment` |
| [monthly_peak_flow_charge](extensions/monthly_peak_flow_charge.md) | 2 | 1 | 1 | 4 | `cost_operation_fixed` |
| [net_import_share](extensions/net_import_share.md) | 1 | 0 | 3 | 4 |  |
| [piecewise_linear_costs](extensions/piecewise_linear_costs.md) | 2 | 1 | 1 | 3 | `cost_investment` |
| [piecewise_linear_efficiency](extensions/piecewise_linear_efficiency.md) | 2 | 0 | 1 | 3 |  |
| [share_all_timesteps](extensions/share_all_timesteps.md) | 2 | 0 | 2 | 2 |  |
| [share_per_timestep](extensions/share_per_timestep.md) | 2 | 0 | 2 | 2 |  |
| [sos2_piecewise_linear_costs](extensions/sos2_piecewise_linear_costs.md) | 2 | 2 | 1 | 2 | `cost_investment` |
| [uptime_downtime_limits](extensions/uptime_downtime_limits.md) | 4 | 0 | 4 | 6 |  |
| [urban_scale_chp](extensions/urban_scale_chp.md) | 1 | 0 | 2 | 5 |  |
<!-- gallery:end -->
