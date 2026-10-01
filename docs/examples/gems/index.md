<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# GEMS in ten files

This is the `basic_models_library` 1.0.0 of
[GEMS v0.4.0](https://github.com/AntaresSimulatorTeam/GEMS/releases/tag/v0.4.0),
RTE's component modelling language, written as ten files under
`examples/ports/gems/`. Each GEMS model is one
[fragment](../../howto/compose.md#a-library-of-components), named after the
model, and `system.yaml` holds what a GEMS interpreter supplies: the time and
scenario axes, and the objective.

A GEMS port maps to a sum. The model that receives through a port reads a
[given](../../reference/language/declarations.md#given) expression, such as
`Bus_balance_port_flow`, and names no model that connects to it. Each model
that sends through the port adds a
[term](../../reference/language/declarations.md#terms) to that sum with
`adds_to:`, through a relation that holds its connections. `merge` of the
files you use is the system, and [the composed spec](composed.md) shows it.
[mathspec and GEMS](../../about/gems.md) compares the two languages.

<!-- gallery:begin -->
### The sums

| Sum | Over | Read in | The terms, by the fragment that adds each |
| --- | --- | --- | --- |
| `Bus_balance_port_flow` | `time, scenario, bus` | [bus](bus.md) | [`Generator_balance_port_flow`](generator.md), [`Link_in_port_flow`](link.md), [`Link_out_port_flow`](link.md), [`Load_balance_port_flow`](load.md), [`Renewable_balance_port_flow`](renewable.md), [`Storage_injection_port_flow`](storage.md) |
| `total_cost` | `scenario` | [system](system.md) | [`Bus_objective`](bus.md), [`Energy_limit_soft_objective`](energy_limitation_soft_constraint_max.md), [`Generator_objective`](generator.md) |
| `Emission_port_co2` | `scenario, emission_limit` | [emission_constraint](emission_constraint.md) | [`Generator_emission_port_co2`](generator.md) |
| `Energy_limit_hard_port_energy` | `scenario, energy_limit_hard` | [energy_limitation_hard_constraint_max](energy_limitation_hard_constraint_max.md) | [`Generator_cumulative_energy_hard`](generator.md) |
| `Energy_limit_soft_port_energy` | `scenario, energy_limit_soft` | [energy_limitation_soft_constraint_max](energy_limitation_soft_constraint_max.md) | [`Generator_cumulative_energy_soft`](generator.md) |

### The fragments

| Fragment | Parameters | Variables | Constraints | Reads | Adds to |
| --- | --- | --- | --- | --- | --- |
| [system](system.md) | 1 | 0 | 0 | 1 |  |
| [bus](bus.md) | 2 | 2 | 1 | 2 | `total_cost` |
| [load](load.md) | 1 | 0 | 0 | 1 | `Bus_balance_port_flow` |
| [link](link.md) | 2 | 3 | 2 | 1 | `Bus_balance_port_flow` |
| [renewable](renewable.md) | 1 | 0 | 0 | 1 | `Bus_balance_port_flow` |
| [generator](generator.md) | 4 | 1 | 0 | 5 | `Bus_balance_port_flow`, `Emission_port_co2`, `Energy_limit_hard_port_energy`, `Energy_limit_soft_port_energy`, `total_cost` |
| [storage](storage.md) | 6 | 3 | 2 | 1 | `Bus_balance_port_flow` |
| [emission_constraint](emission_constraint.md) | 1 | 0 | 1 | 1 |  |
| [energy_limitation_hard_constraint_max](energy_limitation_hard_constraint_max.md) | 1 | 0 | 1 | 1 |  |
| [energy_limitation_soft_constraint_max](energy_limitation_soft_constraint_max.md) | 2 | 1 | 1 | 2 | `total_cost` |
<!-- gallery:end -->
