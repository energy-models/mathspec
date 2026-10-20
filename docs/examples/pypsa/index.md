<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA in fragments

You can read the PyPSA spec here one component at a time. The spec is written
as **fragments**, one file per topic under `examples/pypsa/`. `merge`
joins them into one spec, and `tools/pypsa_compose.py` writes that spec out as
`examples/pypsa.yaml`, which [PyPSA in one file](../pypsa.md) indexes. Edit
the fragments; a check fails when the written file no longer matches them.

Each fragment loads and prints on its own, and
[`advice`](../../reference/api.md#advice) runs on each fragment alone. A
fragment lists each name that it reads but does not declare under
[`given`](../../reference/language/parameters-variables-constraints.md#given). Some sums take a
share from every component, such as the bus balance or the operating cost. A
component names its share of such a sum as an expression of its own, a
[term](../../reference/language/parameters-variables-constraints.md#terms), whose `adds_to:` key
names the sum. The surface reads each sum of the system and adds nothing to it, so the terms
always have a reader. To add a component, you add one file, and the surface
does not change.

## What each file says

The fragments are of four kinds:

- **The surface holds what every model shares.** It holds the weightings and
  the flags that every topic reads, and the balance at each bus. It defines
  `total_cost` as the operating cost in expectation, reads every other sum
  with its description, and sets the objective, which reads `total_cost`.
- **A component file owns one PyPSA class.** It holds the dimension, the data,
  the variables, the rows and the share of each sum of the class of that name.
- **A layer adds one feature to a committable class.** `Generator`, `Link` and
  `Process` each have a folder with the class. Their commitment, ramping and
  maintenance are written once, under `committable/`, over the dimension
  `unit` and names that start with `Unit_`. Each class takes each layer under
  its own names with
  [`rename`](../../howto/compose.md#one-fragment-for-several-classes), because
  PyPSA builds the same rows for each class. A layer reads only the layers
  below it.
- **A system file holds a part of the system that a model may leave out.**
  These are the carriers, the global constraints, security and power flow.
  The risk preference is a choice of two files: `risk.yaml` prices a share of
  operation at the tail of the scenarios, and `risk_neutral.yaml` refuses data
  that sets a risk preference. Power flow reads `Cycle_angle_sum`, the sum that
  only the lines and the transformers add to, and holds Kirchhoff's row.

<!-- gallery:begin -->
### The sums

| Sum | Over | Read in | The terms, by the fragment that adds each |
| --- | --- | --- | --- |
| `scenario_opex` | `scenario` | [surface](surface.md) | [`Generator_opex`](generator/class.md), [`Generator_commitment_opex`](committable/commitment.md), [`Link_opex`](link/class.md), [`Link_commitment_opex`](committable/commitment.md), [`Process_opex`](process/class.md), [`Process_commitment_opex`](committable/commitment.md), [`StorageUnit_opex`](storage_unit.md), [`Store_opex`](store.md) |
| `total_cost` | scalar | [surface](surface.md) | [`Generator_capex`](generator/class.md), [`Line_capex`](line.md), [`Link_capex`](link/class.md), [`Process_capex`](process/class.md), [`CVaR_tail_premium`](risk.md), [`StorageUnit_capex`](storage_unit.md), [`Store_capex`](store.md), [`Transformer_capex`](transformer.md) |
| `Bus_injection` | `scenario, snapshot, bus` | [surface](surface.md) | [`Generator_injection`](generator/class.md), [`Line_injection`](line.md), [`Link_injection`](link/class.md), [`Load_injection`](load.md), [`Process_injection`](process/class.md), [`StorageUnit_injection`](storage_unit.md), [`Store_injection`](store.md), [`Transformer_injection`](transformer.md) |
| `tech_capacity_expansion` | `global_constraint` | [surface](surface.md) | [`Generator_tech_capacity_expansion`](generator/class.md), [`Line_tech_capacity_expansion`](line.md), [`Link_tech_capacity_expansion`](link/class.md), [`Process_tech_capacity_expansion`](process/class.md), [`StorageUnit_tech_capacity_expansion`](storage_unit.md), [`Store_tech_capacity_expansion`](store.md) |
| `Carrier_additions` | `period, carrier` | [surface](surface.md) | [`Generator_additions`](generator/class.md), [`Line_additions`](line.md), [`Link_additions`](link/class.md), [`Process_additions`](process/class.md), [`StorageUnit_additions`](storage_unit.md), [`Store_additions`](store.md) |
| `primary_energy` | `scenario, global_constraint` | [surface](surface.md) | [`Generator_primary_energy`](generator/class.md), [`StorageUnit_primary_energy`](storage_unit.md), [`Store_primary_energy`](store.md) |
| `operational_limit` | `scenario, global_constraint` | [surface](surface.md) | [`Generator_operational_limit`](generator/class.md), [`StorageUnit_operational_limit`](storage_unit.md), [`Store_operational_limit`](store.md) |
| `transmission_volume_expansion` | `scenario, global_constraint` | [surface](surface.md) | [`Line_transmission_volume_expansion`](line.md), [`Link_transmission_volume_expansion`](link/class.md) |
| `transmission_expansion_cost` | `scenario, global_constraint` | [surface](surface.md) | [`Line_transmission_expansion_cost`](line.md), [`Link_transmission_expansion_cost`](link/class.md) |
| `Cycle_angle_sum` | `scenario, snapshot, cycle` | [power_flow](power_flow.md) | [`Line_angle_sum`](line.md), [`Transformer_angle_sum`](transformer.md) |
| `Generator_p_nom_available` | `scenario, snapshot, generator` | [generator/class](generator/class.md) | [`Generator_maintenance_outage`](committable/maintenance.md) |
| `Generator_status_available` | `scenario, snapshot, generator` | [generator/commitment](committable/commitment.md) | [`Generator_maintenance_status_outage`](committable/maintenance.md) |
| `Link_p_nom_available` | `scenario, snapshot, link` | [link/class](link/class.md) | [`Link_maintenance_outage`](committable/maintenance.md) |
| `Link_status_available` | `scenario, snapshot, link` | [link/commitment](committable/commitment.md) | [`Link_maintenance_status_outage`](committable/maintenance.md) |
| `Process_p_nom_available` | `scenario, snapshot, process` | [process/class](process/class.md) | [`Process_maintenance_outage`](committable/maintenance.md) |
| `Process_status_available` | `scenario, snapshot, process` | [process/commitment](committable/commitment.md) | [`Process_maintenance_status_outage`](committable/maintenance.md) |

### The fragments

| Fragment | Parameters | Variables | Constraints | Reads | Adds to |
| --- | --- | --- | --- | --- | --- |
| [carrier](carrier.md) | 2 | 0 | 1 | 1 |  |
| [generator/class](generator/class.md) | 24 | 3 | 11 | 14 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [generator/commitment](committable/commitment.md) | 10 | 0 | 20 | 18 | `scenario_opex` |
| [generator/commitment_none](committable/commitment_none.md) | 3 | 3 | 0 | 1 |  |
| [generator/maintenance](committable/maintenance.md) | 5 | 4 | 13 | 12 | `Generator_p_nom_available`, `Generator_status_available` |
| [generator/ramping](committable/ramping.md) | 5 | 0 | 6 | 14 |  |
| [generator/status_integer](committable/status_integer.md) | 0 | 3 | 0 | 0 |  |
| [generator/status_relaxed](committable/status_relaxed.md) | 0 | 3 | 4 | 14 |  |
| [global_constraints](global_constraints.md) | 3 | 0 | 15 | 6 |  |
| [line](line.md) | 22 | 4 | 14 | 9 | `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `total_cost`, `Carrier_additions`, `Bus_injection`, `Cycle_angle_sum` |
| [link/class](link/class.md) | 24 | 3 | 9 | 13 | `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [link/commitment](committable/commitment.md) | 10 | 0 | 20 | 18 | `scenario_opex` |
| [link/commitment_none](committable/commitment_none.md) | 3 | 3 | 0 | 1 |  |
| [link/maintenance](committable/maintenance.md) | 5 | 4 | 13 | 12 | `Link_p_nom_available`, `Link_status_available` |
| [link/ramping](committable/ramping.md) | 5 | 0 | 6 | 14 |  |
| [link/status_integer](committable/status_integer.md) | 0 | 3 | 0 | 0 |  |
| [link/status_relaxed](committable/status_relaxed.md) | 0 | 3 | 4 | 14 |  |
| [load](load.md) | 3 | 0 | 0 | 1 | `Bus_injection` |
| [power_flow](power_flow.md) | 0 | 0 | 1 | 1 |  |
| [process/class](process/class.md) | 22 | 3 | 9 | 11 | `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [process/commitment](committable/commitment.md) | 10 | 0 | 20 | 18 | `scenario_opex` |
| [process/commitment_none](committable/commitment_none.md) | 3 | 3 | 0 | 1 |  |
| [process/maintenance](committable/maintenance.md) | 5 | 4 | 13 | 12 | `Process_p_nom_available`, `Process_status_available` |
| [process/ramping](committable/ramping.md) | 5 | 0 | 6 | 14 |  |
| [process/status_integer](committable/status_integer.md) | 0 | 3 | 0 | 0 |  |
| [process/status_relaxed](committable/status_relaxed.md) | 0 | 3 | 4 | 14 |  |
| [risk](risk.md) | 2 | 3 | 2 | 3 | `total_cost` |
| [risk_neutral](risk_neutral.md) | 1 | 0 | 0 | 0 |  |
| [security](security.md) | 2 | 0 | 8 | 10 |  |
| [storage_unit](storage_unit.md) | 36 | 6 | 21 | 14 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [store](store.md) | 29 | 4 | 11 | 14 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [surface](surface.md) | 8 | 0 | 1 | 8 |  |
| [transformer](transformer.md) | 24 | 5 | 16 | 5 | `total_cost`, `Bus_injection`, `Cycle_angle_sum` |
<!-- gallery:end -->

## Leaving a file out

You may leave out a component, the carriers, the global constraints or
security, and you may take `risk_neutral.yaml` in place of `risk.yaml`. You may leave out power flow together with the lines, the
transformers and security. What is left is a whole spec, with nothing left
under `given:`. You may not leave out the surface, because the terms of the
components would then add to a sum that no fragment reads, and `merge` refuses
the files. For the same reason, you may not leave out power flow while a line
or a transformer is in.

## Choosing the layers of a class

A committable class takes its class file, then one of two files for its
commitment, then any of its ramping and its maintenance. The commitment also
takes one of two files for its status:

| Layer | What it adds | Without it |
| --- | --- | --- |
| `commitment.yaml` | the rows of a committed unit, which read the status | take `commitment_none.yaml` |
| `commitment_none.yaml` | the names the ramping and the maintenance read, each masked empty | take `commitment.yaml` |
| `status_integer.yaml` | the status, its starts and stops as integers | take `status_relaxed.yaml` |
| `status_relaxed.yaml` | the status as a share in [0, 1], the rows that tighten it, and its refusal of a modular unit; it reads the ramp rates | take `status_integer.yaml` |
| `ramping.yaml` | the ramp limits | no unit is held to a ramp limit |
| `maintenance.yaml` | the maintenance events, and what they take out of the build and the status | no unit is maintained |

`examples/pypsa.yaml` takes every layer with the integer status, and
`examples/pypsa_linearized_uc.yaml` takes the relaxed status in its place.

The class reads `Generator_committable` under `given:`, and only the two
commitment files declare it. A class with neither file leaves the name under
`given:`, and an engine refuses the spec. A class with both is refused by
`merge`, because two files declare the name. The commitment reads the status
the same way, from one of the two status files. `commitment_none.yaml`
declares the status itself, so it takes no status file.
`commitment_none.yaml` also declares an assumption that no unit is
committable, so data that holds a committable unit is refused when it is
attached, rather than leaving that unit without output limits.

The maintenance adds to two sums that the lower layers define:
`Generator_p_nom_available` in the class, the build the output limits are
taken against, and `Generator_status_available` in either commitment file.
Without the maintenance layer, each sum is its body. The maintenance data is
then declared by no file, so an engine refuses it when it is attached.
