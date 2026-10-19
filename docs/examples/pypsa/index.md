<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA in 14 files

You can read the PyPSA spec here one component at a time.
[PyPSA in one file](../pypsa.md) states it as `examples/pypsa.yaml`, one spec
of about four thousand lines. The same spec is split into 14 **fragments**,
one file per topic under `examples/pypsa/`. `merge` joins the 14 files back
into the one file, and the two have the same
[canonical form](../../howto/compare.md).

Each fragment loads and prints on its own, and
[`advice`](../../reference/api.md#advice) runs on each fragment alone. A
fragment lists each name that it reads but does not declare under
[`given`](../../reference/language/parameters-variables-constraints.md#given). Some sums take a
share from every component, such as the bus balance or the operating cost. A
component names its share of such a sum as an expression of its own, a
[term](../../reference/language/parameters-variables-constraints.md#terms), whose `adds_to:` key
names the sum. The surface reads each sum and adds nothing to it, so the terms
always have a reader. To add a component, you add one file, and the surface
does not change.

`tools/pypsa_split.py` writes the 14 files from the one file, and a check
compares them to it, so the two always agree. The split is a proof of concept,
and which of the two is the source is not decided yet.

## What each file says

The fragments are of three kinds:

- **The surface holds what every model shares.** It holds the weightings, the
  risk preference and the flags that every topic reads, and the balance at
  each bus. It reads every sum with its description and sets the objective,
  which reads `total_cost`.
- **A component file owns one PyPSA class.** It holds the dimension, the data,
  the variables, the rows and the share of each sum of the class of that name.
  `Generator`, `Link` and `Process` also carry their unit commitment, their
  ramp limits and their maintenance. These three files read alike, because
  PyPSA builds the same rows for each class.
- **A system file holds a part of the system that a model may leave out.**
  These are the operating cost at risk, the carriers, the global constraints,
  security and power flow. Power flow reads `Cycle_angle_sum`, the sum that
  only the lines and the transformers add to, and holds Kirchhoff's row.

<!-- gallery:begin -->
### The sums

| Sum | Over | Read in | The terms, by the fragment that adds each |
| --- | --- | --- | --- |
| `total_cost` | scalar | [surface](surface.md) | [`risk_weighted_opex`](cost.md), [`Generator_capex`](generator.md), [`Line_capex`](line.md), [`Link_capex`](link.md), [`Process_capex`](process.md), [`StorageUnit_capex`](storage_unit.md), [`Store_capex`](store.md), [`Transformer_capex`](transformer.md) |
| `scenario_opex` | `scenario` | [surface](surface.md) | [`Generator_commitment_opex`](generator.md), [`Generator_opex`](generator.md), [`Link_commitment_opex`](link.md), [`Link_opex`](link.md), [`Process_commitment_opex`](process.md), [`Process_opex`](process.md), [`StorageUnit_opex`](storage_unit.md), [`Store_opex`](store.md) |
| `Bus_injection` | `scenario, snapshot, bus` | [surface](surface.md) | [`Generator_injection`](generator.md), [`Line_injection`](line.md), [`Link_injection`](link.md), [`Load_injection`](load.md), [`Process_injection`](process.md), [`StorageUnit_injection`](storage_unit.md), [`Store_injection`](store.md), [`Transformer_injection`](transformer.md) |
| `tech_capacity_expansion` | `global_constraint` | [surface](surface.md) | [`Generator_tech_capacity_expansion`](generator.md), [`Line_tech_capacity_expansion`](line.md), [`Link_tech_capacity_expansion`](link.md), [`Process_tech_capacity_expansion`](process.md), [`StorageUnit_tech_capacity_expansion`](storage_unit.md), [`Store_tech_capacity_expansion`](store.md) |
| `Carrier_additions` | `period, carrier` | [surface](surface.md) | [`Generator_additions`](generator.md), [`Line_additions`](line.md), [`Link_additions`](link.md), [`Process_additions`](process.md), [`StorageUnit_additions`](storage_unit.md), [`Store_additions`](store.md) |
| `primary_energy` | `scenario, global_constraint` | [surface](surface.md) | [`Generator_primary_energy`](generator.md), [`StorageUnit_primary_energy`](storage_unit.md), [`Store_primary_energy`](store.md) |
| `operational_limit` | `scenario, global_constraint` | [surface](surface.md) | [`Generator_operational_limit`](generator.md), [`StorageUnit_operational_limit`](storage_unit.md), [`Store_operational_limit`](store.md) |
| `transmission_volume_expansion` | `scenario, global_constraint` | [surface](surface.md) | [`Line_transmission_volume_expansion`](line.md), [`Link_transmission_volume_expansion`](link.md) |
| `transmission_expansion_cost` | `scenario, global_constraint` | [surface](surface.md) | [`Line_transmission_expansion_cost`](line.md), [`Link_transmission_expansion_cost`](link.md) |
| `Cycle_angle_sum` | `scenario, snapshot, cycle` | [power_flow](power_flow.md) | [`Line_angle_sum`](line.md), [`Transformer_angle_sum`](transformer.md) |

### The fragments

| Fragment | Parameters | Variables | Constraints | Reads | Adds to |
| --- | --- | --- | --- | --- | --- |
| [carrier](carrier.md) | 2 | 0 | 1 | 1 |  |
| [cost](cost.md) | 1 | 3 | 2 | 4 | `total_cost` |
| [generator](generator.md) | 44 | 10 | 50 | 13 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [global_constraints](global_constraints.md) | 3 | 0 | 15 | 6 |  |
| [line](line.md) | 22 | 4 | 14 | 9 | `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `total_cost`, `Carrier_additions`, `Bus_injection`, `Cycle_angle_sum` |
| [link](link.md) | 44 | 10 | 48 | 12 | `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [load](load.md) | 3 | 0 | 0 | 1 | `Bus_injection` |
| [power_flow](power_flow.md) | 0 | 0 | 1 | 1 |  |
| [process](process.md) | 42 | 10 | 48 | 10 | `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [security](security.md) | 2 | 0 | 8 | 10 |  |
| [storage_unit](storage_unit.md) | 36 | 6 | 21 | 14 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [store](store.md) | 29 | 4 | 11 | 14 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [surface](surface.md) | 9 | 0 | 1 | 9 |  |
| [transformer](transformer.md) | 24 | 5 | 16 | 5 | `total_cost`, `Bus_injection`, `Cycle_angle_sum` |
<!-- gallery:end -->

## Leaving a file out

You may leave out a component, the cost, the carriers, the global constraints
or security. You may leave out power flow together with the lines, the
transformers and security. What is left is a whole spec, with nothing left
under `given:`. You may not leave out the surface, because the terms of the
components would then add to a sum that no fragment reads, and `merge` refuses
the files. For the same reason, you may not leave out power flow while a line
or a transformer is in.
