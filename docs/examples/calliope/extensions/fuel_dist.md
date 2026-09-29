<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# Fuel distribution

An extension of [Calliope in fragments](../index.md). Calliope's example `fuel_dist.yaml`: carriers that move between nodes with no network. Calliope restates `system_balance` and the objective whole to add the distributor; here it is a term of each sum, and no base file changes.

<!-- gallery:begin -->
```yaml
dimensions:
  nodes:
    description: Calliope's `nodes` — the places technologies stand at
  carriers:
    description: Calliope's `carriers` — energy and commodity carriers
  costs:
    description: Calliope's `costs` — cost classes, such as monetary and CO2
  timesteps:
    description: Calliope's `timesteps` — time steps, in order
    dtype: datetime

parameters:
  allow_fuel_distribution:
    description: "`allow_fuel_distribution` — whether a node takes part in distributing a carrier"
    dims: [nodes, carriers]
    dtype: bool
  fuel_import_max:
    description: "`fuel_import_max` — the most of a carrier a node imports in a time step; given only where set"
    dims: [nodes, carriers]
  fuel_export_max:
    description: "`fuel_export_max` — the most of a carrier a node exports in a time step; given only where set"
    dims: [nodes, carriers]
  cost_fuel_distribution:
    description: "`cost_fuel_distribution` — the cost of importing one unit of a carrier, and the revenue of exporting it"
    dims: [nodes, carriers, costs]

variables:
  fuel_distributor:
    description: >-
      `fuel_distributor` — what a node imports of a carrier, with no network
      behind it; an export is negative
    dims: [nodes, carriers, timesteps]
    where: allow_fuel_distribution
    absence: zero

expressions:
  fuel_dist_carrier_flow:
    description: "`+ fuel_distributor` — the term Calliope writes into `system_balance`, by restating it whole"
    expression: fuel_distributor
  cost_var_fuel_distribution:
    description: "`cost_var_fuel_distribution` — the cost of importing, and the revenue of exporting, a carrier"
    expression: timestep_weights * fuel_distributor * cost_fuel_distribution
  fuel_dist_system_cost:
    description: >-
      `sum(cost_var_fuel_distribution, …) * objective_cost_weights` — the term
      Calliope writes into the objective, by restating it whole
    expression: sum(cost_var_fuel_distribution * objective_cost_weights)

given:
  parameters:
    timestep_weights: { dims: [timesteps] }
    objective_cost_weights: { dims: [costs] }
  expressions:
    carrier_flow: { dims: [nodes, carriers, timesteps], term: fuel_dist_carrier_flow }
    system_cost: { dims: [], term: fuel_dist_system_cost }

constraints:
  restrict_total_imports_and_exports:
    description: >-
      `restrict_total_imports_and_exports` — what the nodes import of a
      carrier is what they export. Calliope's `where: fuel_distributor` over
      a carrier reads as any node distributing it
    dims: [carriers, timesteps]
    where: count(fuel_distributor, over=nodes) >= 1
    expression: sum(fuel_distributor, over=nodes) == 0
  restrict_nodal_imports:
    description: "`restrict_nodal_imports` — a node imports at most its limit"
    dims: [nodes, carriers, timesteps]
    where: fuel_distributor AND fuel_import_max
    expression: fuel_distributor <= fuel_import_max
  restrict_nodal_exports:
    description: "`restrict_nodal_exports` — a node exports at most its limit"
    dims: [nodes, carriers, timesteps]
    where: fuel_distributor AND fuel_export_max
    expression: -1 * fuel_distributor <= fuel_export_max
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{N}`$ | index $`n`$ — `nodes` — Calliope's `nodes` — the places technologies stand at |
| $`\mathcal{C}`$ | index $`c`$ — `carriers` — Calliope's `carriers` — energy and commodity carriers |
| $`\mathcal{K}`$ | index $`k`$ — `costs` — Calliope's `costs` — cost classes, such as monetary and CO2 |
| $`\mathcal{T}`$ | index $`t`$ — `timesteps` — Calliope's `timesteps` — time steps, in order |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{allow\_fuel\_distribution}`$ | `allow_fuel_distribution` over $`\mathcal{N} \times \mathcal{C}`$ — `allow_fuel_distribution` — whether a node takes part in distributing a carrier |
| $`\mathrm{fuel\_import\_max}`$ | `fuel_import_max` over $`\mathcal{N} \times \mathcal{C}`$ — `fuel_import_max` — the most of a carrier a node imports in a time step; given only where set |
| $`\mathrm{fuel\_export\_max}`$ | `fuel_export_max` over $`\mathcal{N} \times \mathcal{C}`$ — `fuel_export_max` — the most of a carrier a node exports in a time step; given only where set |
| $`\mathrm{cost\_fuel\_distribution}`$ | `cost_fuel_distribution` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{K}`$ — `cost_fuel_distribution` — the cost of importing one unit of a carrier, and the revenue of exporting it |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{fuel\_distributor}`$ | `fuel_distributor` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ — `fuel_distributor` — what a node imports of a carrier, with no network behind it; an export is negative |

#### Given

| Symbol | Meaning |
|---|---|
| $`\mathrm{timestep\_weights}`$ | `timestep_weights` over $`\mathcal{T}`$, data another file declares |
| $`\mathrm{objective\_cost\_weights}`$ | `objective_cost_weights` over $`\mathcal{K}`$, data another file declares |
| $`\mathit{carrier\_flow}`$ | `carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$, an expression this file adds `fuel_dist_carrier_flow` to |
| $`\mathit{system\_cost}`$ | `system_cost` (scalar), an expression this file adds `fuel_dist_system_cost` to |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{fuel\_dist\_carrier\_flow}`$ | `fuel_dist_carrier_flow` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{T}`$ — `+ fuel_distributor` — the term Calliope writes into `system_balance`, by restating it whole |
| $`\mathit{cost\_var\_fuel\_distribution}`$ | `cost_var_fuel_distribution` over $`\mathcal{N} \times \mathcal{C} \times \mathcal{K} \times \mathcal{T}`$ — `cost_var_fuel_distribution` — the cost of importing, and the revenue of exporting, a carrier |
| $`\mathit{fuel\_dist\_system\_cost}`$ | `fuel_dist_system_cost` (scalar) — `sum(cost_var_fuel_distribution, …) * objective_cost_weights` — the term Calliope writes into the objective, by restating it whole |

Upright is what the data supplies — a parameter such as $`\mathrm{allow\_fuel\_distribution}`$, a coordinate map, a label — and italic is what the solver chooses, such as $`\mathit{fuel\_distributor}`$. An index is italic too, being what a quantifier chooses, and a set is script.

#### Subject to

**`restrict_total_imports_and_exports`**

```math
\sum_{n \in \mathcal{N}} \mathit{fuel\_distributor}_{n,c,t} = 0 \qquad \forall\, c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \lvert \{ n \in \mathcal{N} \,:\, \mathit{fuel\_distributor}_{n,c,t} \text{ exists} \} \rvert \ge 1
```

**`restrict_nodal_imports`**

```math
\mathit{fuel\_distributor}_{n,c,t} \le \mathrm{fuel\_import\_max}_{n,c} \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{fuel\_distributor}_{n,c,t} \text{ exists} \wedge \mathrm{fuel\_import\_max}_{n,c} \text{ is defined}
```

**`restrict_nodal_exports`**

```math
-1 \cdot \mathit{fuel\_distributor}_{n,c,t} \le \mathrm{fuel\_export\_max}_{n,c} \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathit{fuel\_distributor}_{n,c,t} \text{ exists} \wedge \mathrm{fuel\_export\_max}_{n,c} \text{ is defined}
```

#### Definitions

**`fuel_dist_carrier_flow`**

```math
\mathit{fuel\_dist\_carrier\_flow}_{n,c,t} = \mathit{fuel\_distributor}_{n,c,t} \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T}
```

**`cost_var_fuel_distribution`**

```math
\mathit{cost\_var\_fuel\_distribution}_{n,c,k,t} = \mathrm{timestep\_weights}_{t} \cdot \mathit{fuel\_distributor}_{n,c,t} \cdot \mathrm{cost\_fuel\_distribution}_{n,c,k} \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ k \in \mathcal{K},\ t \in \mathcal{T}
```

**`fuel_dist_system_cost`**

```math
\mathit{fuel\_dist\_system\_cost} = \sum_{n \in \mathcal{N},\ c \in \mathcal{C},\ k \in \mathcal{K},\ t \in \mathcal{T}} \mathit{cost\_var\_fuel\_distribution}_{n,c,k,t} \cdot \mathrm{objective\_cost\_weights}_{k}
```

#### Variable domains

**`fuel_distributor`**

```math
\mathit{fuel\_distributor}_{n,c,t} \in \mathbb{R} \qquad \forall\, n \in \mathcal{N},\ c \in \mathcal{C},\ t \in \mathcal{T} \,:\, \mathrm{allow\_fuel\_distribution}_{n,c}
```
<!-- gallery:end -->
