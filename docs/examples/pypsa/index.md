<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA in 24 files

This section states the PyPSA spec one topic at a time.
[PyPSA in one file](../pypsa_ladder.md) states it as `examples/pypsa.yaml`, one spec of
about 4,700 lines. Here the same spec is split into 24 whole specs of one topic
each ([fragments](../../reference/glossary.md#fragment)), under
`examples/pypsa/`. [`merge`](../../reference/composition.md#merge) composes the
24 files into one spec, which has the same
[canonical form](../../reference/reading.md#comparing-two-specs) as the one
file.

Each fragment loads and prints on its own, and
[`advice`](../../reference/api.md#advice) runs on each fragment alone. A
fragment lists each name that it uses but does not declare under
[`given`](../../reference/language/parameters-variables-constraints.md#given).

Some sums take a share from every component, such as the bus balance or the
operating cost. A component states its share of such a sum as an expression of
its own, a [term](../../reference/language/named.md#adds_to), whose `adds_to:`
key is the sum. For each sum, one fragment lists it under `given:` and adds
nothing to it, so every term adds to a sum that some fragment lists. A
component is one file, and adding it leaves the network file unchanged.

`tools/pypsa_split.py` writes the 24 files from the one file, and a test
compares them with it, so the two always agree.

## The four kinds of fragment

- A **component** file states the PyPSA class of that name: its dimension, its
  data, its variables, its rows and its share of each sum. The committable
  classes are `Generator`, `Link` and `Process`. Each of them is split by
  feature into four files: the class, its commitment, its ramping and its
  maintenance. The three sets of four files are alike, because PyPSA builds
  the same rows for each class.
- A file that describes a sum lists it under `given:` with its description,
  and states the row that contains it. The network and power flow files are
  of this kind.
- A file of one feature states rows that span several classes. The cost,
  carrier, global constraints and security files state the risk-weighted
  operating cost, the growth limits, the five caps and the outage rows.
- The **settings** file states the weightings and the flags that the other
  fragments use. It also lists the totals that the cost, carrier and global
  constraints files list, because a spec may leave those files out. Its
  objective minimises `total_cost`. Each component adds its capital cost to
  `total_cost`, and the cost file adds the risk-weighted operating cost.

## Sums and fragments

<!-- gallery:begin -->
### The sums

| Sum | Over | Read in | The terms, by the fragment that adds each |
| --- | --- | --- | --- |
| `total_cost` | scalar | [settings](settings.md) | [`risk_weighted_opex`](cost.md), [`Generator_capex`](generator.md), [`Line_capex`](line.md), [`Link_capex`](link.md), [`Process_capex`](process.md), [`StorageUnit_capex`](storage_unit.md), [`Store_capex`](store.md), [`Transformer_capex`](transformer.md) |
| `scenario_opex` | `scenario` | [settings](settings.md) | [`Generator_opex`](generator.md), [`Generator_commitment_opex`](generator_commitment.md), [`Link_opex`](link.md), [`Link_commitment_opex`](link_commitment.md), [`Process_opex`](process.md), [`Process_commitment_opex`](process_commitment.md), [`StorageUnit_opex`](storage_unit.md), [`Store_opex`](store.md) |
| `Bus_injection` | `scenario, snapshot, bus` | [network](network.md) | [`Generator_injection`](generator.md), [`Line_injection`](line.md), [`Link_injection`](link.md), [`Load_injection`](load.md), [`Process_injection`](process.md), [`StorageUnit_injection`](storage_unit.md), [`Store_injection`](store.md), [`Transformer_injection`](transformer.md) |
| `tech_capacity_expansion` | `global_constraint` | [settings](settings.md) | [`Generator_tech_capacity_expansion`](generator.md), [`Line_tech_capacity_expansion`](line.md), [`Link_tech_capacity_expansion`](link.md), [`Process_tech_capacity_expansion`](process.md), [`StorageUnit_tech_capacity_expansion`](storage_unit.md), [`Store_tech_capacity_expansion`](store.md) |
| `Carrier_additions` | `period, carrier` | [settings](settings.md) | [`Generator_additions`](generator.md), [`Line_additions`](line.md), [`Link_additions`](link.md), [`Process_additions`](process.md), [`StorageUnit_additions`](storage_unit.md), [`Store_additions`](store.md) |
| `primary_energy` | `scenario, global_constraint` | [settings](settings.md) | [`Generator_primary_energy`](generator.md), [`StorageUnit_primary_energy`](storage_unit.md), [`Store_primary_energy`](store.md) |
| `operational_limit` | `scenario, global_constraint` | [settings](settings.md) | [`Generator_operational_limit`](generator.md), [`StorageUnit_operational_limit`](storage_unit.md), [`Store_operational_limit`](store.md) |
| `transmission_volume_expansion` | `scenario, global_constraint` | [settings](settings.md) | [`Line_transmission_volume_expansion`](line.md), [`Link_transmission_volume_expansion`](link.md) |
| `transmission_expansion_cost` | `scenario, global_constraint` | [settings](settings.md) | [`Line_transmission_expansion_cost`](line.md), [`Link_transmission_expansion_cost`](link.md) |
| `Cycle_angle_sum` | `scenario, snapshot, cycle` | [power_flow](power_flow.md) | [`Line_angle_sum`](line.md), [`Transformer_angle_sum`](transformer.md) |

### The fragments

| Fragment | Parameters | Variables | Constraints | Reads | Adds to |
| --- | --- | --- | --- | --- | --- |
| [carrier](carrier.md) | 2 | 0 | 1 | 1 |  |
| [cost](cost.md) | 1 | 3 | 2 | 4 | `total_cost` |
| [generator](generator.md) | 24 | 3 | 11 | 17 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [generator_commitment](generator_commitment.md) | 10 | 3 | 20 | 17 | `scenario_opex` |
| [generator_maintenance](generator_maintenance.md) | 5 | 4 | 13 | 9 |  |
| [generator_ramping](generator_ramping.md) | 5 | 0 | 6 | 14 |  |
| [global_constraints](global_constraints.md) | 3 | 0 | 15 | 6 |  |
| [line](line.md) | 22 | 4 | 14 | 9 | `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `total_cost`, `Carrier_additions`, `Bus_injection`, `Cycle_angle_sum` |
| [link](link.md) | 24 | 3 | 9 | 16 | `transmission_volume_expansion`, `transmission_expansion_cost`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [link_commitment](link_commitment.md) | 10 | 3 | 20 | 17 | `scenario_opex` |
| [link_maintenance](link_maintenance.md) | 5 | 4 | 13 | 9 |  |
| [link_ramping](link_ramping.md) | 5 | 0 | 6 | 14 |  |
| [load](load.md) | 3 | 0 | 0 | 1 | `Bus_injection` |
| [network](network.md) | 0 | 0 | 1 | 1 |  |
| [power_flow](power_flow.md) | 0 | 0 | 1 | 1 |  |
| [process](process.md) | 22 | 3 | 9 | 14 | `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [process_commitment](process_commitment.md) | 10 | 3 | 20 | 17 | `scenario_opex` |
| [process_maintenance](process_maintenance.md) | 5 | 4 | 13 | 9 |  |
| [process_ramping](process_ramping.md) | 5 | 0 | 6 | 14 |  |
| [security](security.md) | 2 | 0 | 8 | 10 |  |
| [settings](settings.md) | 9 | 0 | 0 | 8 |  |
| [storage_unit](storage_unit.md) | 36 | 6 | 21 | 14 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [store](store.md) | 29 | 4 | 11 | 14 | `primary_energy`, `operational_limit`, `tech_capacity_expansion`, `scenario_opex`, `total_cost`, `Carrier_additions`, `Bus_injection` |
| [transformer](transformer.md) | 24 | 5 | 16 | 5 | `total_cost`, `Bus_injection`, `Cycle_angle_sum` |
<!-- gallery:end -->

## Leaving a file out

A spec may leave out a component family, the cost, the carriers, the global
constraints or security. What remains is a whole spec, with nothing left
under `given:`. Lines and transformers leave only together with security,
because security lists `Line_s_nom` and four more line names, and the same for
transformers, under `given:`. While a component is in, a spec may not leave
out the network, power flow or settings. The terms of the component would then
add to a sum that no fragment lists, and `merge` refuses the files.

!!! info "See also"

    - [Composition](../../reference/composition.md), for what `merge` refuses
    - [PyPSA in one file](../pypsa_ladder.md), for the same spec as one file, rung by
      rung
    - [`given`](../../reference/language/parameters-variables-constraints.md#given),
      for the names a fragment uses but does not declare
