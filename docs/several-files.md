<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A spec in several files

In this lesson you build a dispatch spec out of files that each hold one part
of it, merge them into one spec, and then add a component without changing the
other files. Do [your first spec](first-spec.md) first.

## The network

Make a file `network.yaml`. It balances every bus, and it reads the injection
at a bus under [`given:`](reference/language/declarations.md#given): what the
components put in is theirs to say, in
[a term](reference/language/declarations.md#terms) each. It also sets the
objective, and the objective reads the total cost the same way: what each
component costs is a term of its own.

```yaml title="network.yaml"
description: Every bus is balanced in every snapshot.

given:
  expressions:
    injection:
      dims: [snapshot, bus]
      description: what the components put into a bus, less what they take out
    total_cost:
      dims: []
      description: what running the system costs

dimensions:
  snapshot: { dtype: int, description: dispatch periods }
  bus: { description: network nodes }

constraints:
  balance:
    dims: [snapshot, bus]
    expression: injection == 0

objective:
  sense: minimize
  expression: total_cost
```

Check the file:

```bash
python -m mathspec check network.yaml
```

The check accepts it, and notes each name it reads and does not define:

```text
expression 'injection' is read here and declared elsewhere: the model this one is layered onto provides it. A consumer checks that it does, on the same frame, and refuses the program where it does not. A fragment is composed instead: merge() folds this declaration into the one a sibling introduces, or writes it from the terms siblings add.
expression 'total_cost' is read here and declared elsewhere: the model this one is layered onto provides it. A consumer checks that it does, on the same frame, and refuses the program where it does not. A fragment is composed instead: merge() folds this declaration into the one a sibling introduces, or writes it from the terms siblings add.
```

## The generators

Make a file `generators.yaml`. It says what the fleet puts into a bus as a
named expression, `generation`. It reads the injection too, and
[`adds_to:`](reference/language/declarations.md#terms) on `generation` names
the injection as what the expression adds to. What the fleet costs is a term
of the total cost in the same way, `generation_cost`. The two dimensions it shares
with the network it restates as a dtype and nothing else: a description is not
a claim, and `merge` carries the network's.

```yaml title="generators.yaml"
description: A generator fleet, each unit on one bus.

given:
  expressions:
    injection: { dims: [snapshot, bus] }
    total_cost: { dims: [] }

dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
  generator: { description: generating units }

relations:
  gen_bus: { key: generator, values: bus, description: the bus a generator sits on }

parameters:
  capacity: { dims: [generator], description: installed capacity }
  cost: { dims: [generator], description: marginal cost }

variables:
  dispatch:
    description: output of a generator in a snapshot
    dims: [snapshot, generator]
    bounds: { lower: 0, upper: capacity }

expressions:
  generation:
    description: what the fleet puts into a bus
    expression: sum(dispatch, over=generator, by=gen_bus[bus])
    adds_to: injection
  generation_cost:
    description: what running the fleet costs
    expression: sum(dispatch * cost)
    adds_to: total_cost
```

Check the file:

```bash
python -m mathspec check generators.yaml
```

The check accepts it, and notes each term:

```text
expression 'injection' is read here, and this file adds a term to it: merge() sums the term with what the other files write under the name. Until then, the program reads it and does not build it.
expression 'total_cost' is read here, and this file adds a term to it: merge() sums the term with what the other files write under the name. Until then, the program reads it and does not build it.
```

Print the math of the file on its own:

```python
import mathspec as ms

print(ms.to_markdown('generators.yaml', legend=False))
```

Each term prints as its own definition, and the legend, left out here, says
what it adds to. The file sets no objective, so on its own it is a
feasibility problem:

!!! example "Rendered output"

    A generator fleet, each unit on one bus.

    #### Definitions

    **`generation`**

    ```math
    \mathit{generation}_{t,b} = \sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} \mathit{dispatch}_{t,g} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    **`generation_cost`**

    ```math
    \mathit{generation}^{\mathrm{cost}} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
    ```

    #### Variable domains

    **`dispatch`**

    ```math
    0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

## The loads

Make a file `loads.yaml`. Its term, `consumption`, takes the demand out of the
bus:

```yaml title="loads.yaml"
description: The demand at every bus.

given:
  expressions:
    injection: { dims: [snapshot, bus] }

dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }

parameters:
  demand: { dims: [snapshot, bus], description: demand to be met }

expressions:
  consumption:
    description: what the loads take out of a bus
    expression: -demand
    adds_to: injection
```

Check the file:

```bash
python -m mathspec check loads.yaml
```

The check accepts it, with the same note:

```text
expression 'injection' is read here, and this file adds a term to it: merge() sums the term with what the other files write under the name. Until then, the program reads it and does not build it.
```

## Merge the files

Merge the three files in Python. Give them as a list:

```python
spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml'])
print(spec.expressions['injection'].expression)
print(spec.dimensions['snapshot'].description)
```

The injection is the sum of the two terms by name, in the order of the list.
Each term stays a named expression of the merged spec. The dimension
carries the one description written for it, the network's:

```text
generation + consumption
dispatch periods
```

Print the math of the merged spec:

```python
print(ms.to_markdown(spec, legend=False))
```

!!! example "Rendered output"

    #### Objective

    ```math
    \min \mathit{total\_cost}
    ```

    #### Subject to

    **`balance`**

    ```math
    \mathit{injection}_{t,b} = 0 \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    #### Definitions

    **`generation`**

    ```math
    \mathit{generation}_{t,b} = \sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} \mathit{dispatch}_{t,g} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    **`generation_cost`**

    ```math
    \mathit{generation}^{\mathrm{cost}} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
    ```

    **`consumption`**

    ```math
    \mathrm{consumption}_{t,b} = -\mathrm{demand}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    **`injection`**

    ```math
    \mathit{injection}_{t,b} = \mathit{generation}_{t,b} + \mathrm{consumption}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    **`total_cost`**

    ```math
    \mathit{total\_cost} = \mathit{generation}^{\mathrm{cost}}
    ```

    #### Variable domains

    **`dispatch`**

    ```math
    0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

## Add a component

Make a file `imports.yaml`. It adds a term, `purchase`, to the injection and a
term, `import_cost`, to the total cost:

```yaml title="imports.yaml"
description: Power bought from outside the network, at a price.

given:
  expressions:
    injection: { dims: [snapshot, bus] }
    total_cost: { dims: [] }

dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }

parameters:
  import_limit: { dims: [bus], description: most a bus can import }
  import_price: { dims: [snapshot], description: price of imported power }

variables:
  imported:
    description: power a bus imports in a snapshot
    dims: [snapshot, bus]
    bounds: { lower: 0, upper: import_limit }

expressions:
  purchase:
    description: what the imports put into a bus
    expression: imported
    adds_to: injection
  import_cost:
    description: what the imports cost
    expression: sum(imported * import_price)
    adds_to: total_cost
```

Merge the four files:

```python
spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml', 'imports.yaml'])
print(spec.expressions['injection'].expression)
print(spec.expressions['total_cost'].expression)
```

The injection has a third term at the end, and the total cost a second one.
`network.yaml` did not change:

```text
generation + consumption + purchase
generation_cost + import_cost
```

Only `network.yaml` sets the objective. A second file that sets one is
refused: `merge` does not join two objectives, and a part of the cost is a
term of `total_cost`.

## Read what another file declares

Make a file `emissions.yaml`. It caps what the fleet emits, and it reads
`dispatch` under `given:` rather than declaring it:

```yaml title="emissions.yaml"
description: A cap on what the fleet emits over the horizon.

given:
  variables:
    dispatch: { dims: [snapshot, generator] }

dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }

parameters:
  emission_rate: { dims: [generator], description: emissions per unit of output }
  emission_cap: { dims: [], description: most the fleet may emit }

constraints:
  emission_limit:
    dims: []
    expression: sum(dispatch * emission_rate) <= emission_cap
```

Check the file:

```bash
python -m mathspec check emissions.yaml
```

The check accepts it, and notes the variable it reads:

```text
variable 'dispatch' is read here and declared elsewhere: the model this one is layered onto provides it. A consumer checks that it does, on the same frame, and refuses the program where it does not. A fragment is composed instead: merge() folds this declaration into the one a sibling introduces.
```

Merge all five files:

```python
spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml', 'imports.yaml', 'emissions.yaml'])
print(sorted(spec.constraints))
print(bool(spec.program.given))
```

The cap reads the generators' `dispatch`, and nothing is left for anything
outside the files to provide:

```text
['balance', 'emission_limit']
False
```

## Leave the network out

Merge the generators and the loads without the network:

```python
ms.merge(['generators.yaml', 'loads.yaml'])
```

`merge` refuses it. A term adds to a sum that the rest of the spec reads, and
without the network no file reads `injection` other than the two files that
add to it:

```text
fragments 'generators.yaml' and 'loads.yaml' add a term to 'injection', and no other fragment reads it: none reads it without adding to it, or uses it in its math. A term writes into a sum the rest of the spec reads: add the fragment that reads it, or fix the spelling under 'given:'.
```

## Where to next

- [Compose a spec from several files](howto/compose.md) covers `merge` and
  `override`, which lays a patch over a spec.
- [`given`](reference/language/declarations.md#given) gives every rule a file
  that reads another file obeys.
- [A component library](examples/library/index.md) shows larger fragments
  beside the math they print.
