<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA

You can read the spec of the model that `n.optimize()` builds in the power
system modelling framework PyPSA here, one topic at a time. The spec is one
file,
[`examples/pypsa.yaml`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa.yaml),
of about 5,200 lines, split into 25 whole specs of one topic each
([fragments](../../reference/glossary.md#fragment)) under `examples/pypsa/`.
[`merge`](../../reference/composition.md#merge) composes the 25 files into one
spec with the same
[canonical form](../../reference/reading.md#comparing-two-specs) as the one
file. [A sample page](generator_commitment.md) has one fragment in full beside
its math, and [PyPSA: scope and refusals](scope.md) lists the `n.optimize()`
keywords that the file states and the data that PyPSA refuses. [The relaxed commitment](../pypsa_linearized_uc.md) is a patch
over the file that relaxes the commitment decisions to shares in [0, 1].

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

`tools/pypsa_split.py` writes the 25 files from the one file, and a test
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

| Sum | Over | Listed in | The terms, by the fragment that adds each |
| --- | --- | --- | --- |
| `Bus_injection` | `bus, scenario, snapshot` | [network](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/network.yaml) | [`FlowBased_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/flow_based.yaml), [`Generator_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml), [`Line_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml), [`Link_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml), [`Load_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/load.yaml), [`Process_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process.yaml), [`StorageUnit_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml), [`Store_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml), [`Transformer_injection`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/transformer.yaml) |
| `total_cost` | scalar | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`risk_weighted_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/cost.yaml), [`Generator_capex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml), [`Line_capex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml), [`Link_capex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml), [`Process_capex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process.yaml), [`StorageUnit_capex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml), [`Store_capex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml), [`Transformer_capex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/transformer.yaml) |
| `scenario_opex` | `scenario` | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`Generator_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml), [`Generator_commitment_opex`](generator_commitment.md), [`Link_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml), [`Link_commitment_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link_commitment.yaml), [`Process_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process.yaml), [`Process_commitment_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process_commitment.yaml), [`StorageUnit_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml), [`Store_opex`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml) |
| `Carrier_additions` | `carrier, period` | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`Generator_additions`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml), [`Line_additions`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml), [`Link_additions`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml), [`Process_additions`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process.yaml), [`StorageUnit_additions`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml), [`Store_additions`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml) |
| `tech_capacity_expansion` | `global_constraint` | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`Generator_tech_capacity_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml), [`Line_tech_capacity_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml), [`Link_tech_capacity_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml), [`Process_tech_capacity_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process.yaml), [`StorageUnit_tech_capacity_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml), [`Store_tech_capacity_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml) |
| `operational_limit` | `global_constraint, scenario` | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`Generator_operational_limit`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml), [`StorageUnit_operational_limit`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml), [`Store_operational_limit`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml) |
| `primary_energy` | `global_constraint, scenario` | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`Generator_primary_energy`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml), [`StorageUnit_primary_energy`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml), [`Store_primary_energy`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml) |
| `Cycle_angle_sum` | `cycle, scenario, snapshot` | [power_flow](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/power_flow.yaml) | [`Line_angle_sum`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml), [`Transformer_angle_sum`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/transformer.yaml) |
| `transmission_expansion_cost` | `global_constraint, scenario` | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`Line_transmission_expansion_cost`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml), [`Link_transmission_expansion_cost`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml) |
| `transmission_volume_expansion` | `global_constraint, scenario` | [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | [`Line_transmission_volume_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml), [`Link_transmission_volume_expansion`](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml) |

### The fragments

| Fragment | Purpose | Given | Adds to |
| --- | --- | --- | --- |
| [carrier](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/carrier.yaml) | The growth limits of each carrier | 1 |  |
| [cost](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/cost.yaml) | The expected operating cost and its tail, weighted by scenario | 4 | `total_cost` |
| [flow_based](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/flow_based.yaml) | Flow-based market coupling | 5 | `Bus_injection` |
| [generator](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator.yaml) | PyPSA's `Generator` | 19 | `Carrier_additions`, `total_cost`, `Bus_injection`, `operational_limit`, `scenario_opex`, `primary_energy`, `tech_capacity_expansion` |
| [generator_commitment](generator_commitment.md) | The commitment rows of PyPSA's `Generator` | 19 | `scenario_opex` |
| [generator_maintenance](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator_maintenance.yaml) | The maintenance rows of PyPSA's `Generator` | 10 |  |
| [generator_ramping](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/generator_ramping.yaml) | The ramping rows of PyPSA's `Generator` | 15 |  |
| [global_constraints](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/global_constraints.yaml) | The five system totals that PyPSA caps | 6 |  |
| [line](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/line.yaml) | PyPSA's `Line` | 9 | `Carrier_additions`, `Cycle_angle_sum`, `total_cost`, `Bus_injection`, `tech_capacity_expansion`, `transmission_expansion_cost`, `transmission_volume_expansion` |
| [link](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link.yaml) | PyPSA's `Link` | 17 | `Carrier_additions`, `total_cost`, `Bus_injection`, `scenario_opex`, `tech_capacity_expansion`, `transmission_expansion_cost`, `transmission_volume_expansion` |
| [link_commitment](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link_commitment.yaml) | The commitment rows of PyPSA's `Link` | 18 | `scenario_opex` |
| [link_maintenance](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link_maintenance.yaml) | The maintenance rows of PyPSA's `Link` | 10 |  |
| [link_ramping](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/link_ramping.yaml) | The ramping rows of PyPSA's `Link` | 15 |  |
| [load](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/load.yaml) | PyPSA's `Load` | 1 | `Bus_injection` |
| [network](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/network.yaml) | The buses and the balance at each bus | 1 |  |
| [power_flow](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/power_flow.yaml) | Kirchhoff's voltage law around each cycle | 1 |  |
| [process](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process.yaml) | PyPSA's `Process` | 15 | `Carrier_additions`, `total_cost`, `Bus_injection`, `scenario_opex`, `tech_capacity_expansion` |
| [process_commitment](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process_commitment.yaml) | The commitment rows of PyPSA's `Process` | 18 | `scenario_opex` |
| [process_maintenance](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process_maintenance.yaml) | The maintenance rows of PyPSA's `Process` | 10 |  |
| [process_ramping](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/process_ramping.yaml) | The ramping rows of PyPSA's `Process` | 15 |  |
| [security](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/security.yaml) | The security-constrained flows over the outages | 10 |  |
| [settings](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/settings.yaml) | The weightings, the risk preference and the flags that the other fragments use | 8 |  |
| [storage_unit](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/storage_unit.yaml) | PyPSA's `StorageUnit` | 14 | `Carrier_additions`, `total_cost`, `Bus_injection`, `operational_limit`, `scenario_opex`, `primary_energy`, `tech_capacity_expansion` |
| [store](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/store.yaml) | PyPSA's `Store` | 15 | `Carrier_additions`, `total_cost`, `Bus_injection`, `operational_limit`, `scenario_opex`, `primary_energy`, `tech_capacity_expansion` |
| [transformer](https://github.com/energy-models/mathspec/blob/main/examples/pypsa/transformer.yaml) | PyPSA's `Transformer` | 5 | `Cycle_angle_sum`, `total_cost`, `Bus_injection` |
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
    - [PyPSA: scope and refusals](scope.md), for the `n.optimize()` keywords that
      the one file states and the data that PyPSA refuses
    - [`given`](../../reference/language/parameters-variables-constraints.md#given),
      for the names a fragment uses but does not declare
