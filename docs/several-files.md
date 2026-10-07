<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A spec in several files

Build a dispatch spec from files that each hold one part of it, merge them into
one spec, and then add a component without changing the other files. Do
[your first spec](first-spec.md) first.

## The network

Make a file `network.yaml`, which balances every bus. It reads the injection at
a bus under [`given:`](reference/language/declarations.md#given), because each
component file adds its own share as a
[term](reference/language/declarations.md#terms). A term is a named expression
that adds to a sum another file reads. The file also sets the objective, which
reads the total cost in the same way: each component adds its cost as a term.

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
expression 'injection' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this declaration with the one another file declares, or builds it from the terms other files add.
expression 'total_cost' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this declaration with the one another file declares, or builds it from the terms other files add.
```

## The generators

Make a file `generators.yaml`. Its named expression `generation` is what the
fleet puts into a bus. The file reads the injection too, and
[`adds_to:`](reference/language/declarations.md#terms) on `generation` makes
`generation` a term of the injection. In the same way, `generation_cost` is a
term of the total cost. The file restates the two dimensions it shares with the
network as a dtype only, because a missing description does not conflict with
the network, and `merge` keeps the description from `network.yaml`.

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
expression 'injection' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
expression 'total_cost' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
```

Print the math of the file on its own:

```python
import mathspec as ms

print(ms.to_markdown('generators.yaml', legend=False))
```

Each term prints as its own definition, and the legend, left out here, says
what each term adds to. The file sets no objective, so on its own it is a
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
expression 'injection' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
```

## Merge the files

Merge the three files in Python, and give them as a list:

```python
spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml'])
print(spec.expressions['injection'].expression)
print(spec.dimensions['snapshot'].description)
```

`merge` writes the injection as the sum of the two terms by name, in the order
of the list. Each term stays a named expression of the merged spec. The
dimension keeps the one description written for it, which is the network's:

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

The injection has a third term at the end, and the total cost a second one,
although `network.yaml` did not change:

```text
generation + consumption + purchase
generation_cost + import_cost
```

Only `network.yaml` sets the objective. `merge` refuses a second file that
sets one, because it does not join two objectives. Add a part of the cost as a
term of `total_cost` instead.

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
variable 'dispatch' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this declaration with the one another file declares.
```

Merge all five files:

```python
spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml', 'imports.yaml', 'emissions.yaml'])
print(sorted(spec.constraints))
print(bool(spec.program.given))
```

The cap reads `dispatch` from `generators.yaml`. Because `spec.program.given`
is empty, nothing outside the five files has to provide a name:

```text
['balance', 'emission_limit']
False
```

## Leave the network out

Merge the generators and the loads without the network:

```python
ms.merge(['generators.yaml', 'loads.yaml'])
```

`merge` refuses it. A term adds to a sum that the rest of the spec reads, but
without the network, only the two files that add to `injection` read it:

```text
fragments 'generators.yaml' and 'loads.yaml' add a term to 'injection', and no other fragment reads it. Add the fragment that reads 'injection', or fix the spelling under 'given:'.
```

## Where to next

- [Compose a spec from several files](howto/compose.md) covers `merge` and
  `override`, which lays a patch over a spec.
- [`given`](reference/language/declarations.md#given) gives the rules for a
  file that reads what another file declares.
- [A component library](examples/library/index.md) shows larger fragments
  beside the math they print.
