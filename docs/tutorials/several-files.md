<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A spec in several files

In this tutorial you build the specification of an optimisation model
(a [spec](../reference/glossary.md#spec)) for dispatch from files that each contain one
part of the spec. You merge them into one spec, and then add a component without changing
the files you already have. This tutorial takes about 30 minutes. Do
[your first spec](first-spec.md) first.

Each file here is one part that
[`merge`](../reference/composition.md#merge) composes (a [fragment](../reference/composition.md)).

## The network

Make a file `network.yaml`, with a constraint that balances every bus and an
objective that minimises the total cost. The file lists the injection and the total
cost as names used but not declared here
(under [`given:`](../reference/language/parameters-variables-constraints.md#given)). Each file you make next adds a part of a sum ([a term](../reference/language/named.md#adds_to)) to the injection and to the total cost.

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

=== "Command line"

    ```bash
    python -m mathspec check network.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    for note in ms.advice('network.yaml'):
        print(note)
    ```

```text
expression 'injection' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this entry with the one another file declares, or builds it from the terms other files add.
expression 'total_cost' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this entry with the one another file declares, or builds it from the terms other files add.
```

mathspec accepts the file. `check` prints one remark that is not a refusal (a line of
[advice](../reference/glossary.md#advice)) for
each name the file lists under `given:`.

Keep this Python session open. Later steps use `ms`.

## The generators

Make a file `generators.yaml`. The file declares the [shared dimensions](../reference/composition.md#each-kind-of-entry) again, with only the type of their labels (a [`dtype`](../reference/language/dimensions.md#dimensions)). The
[`adds_to:`](../reference/language/named.md#adds_to)
keys of the file make `generation` a term of the injection and `generation_cost` a term of
the total cost. `gen_bus` is a table of label pairs
(a [relation](../reference/language/relations.md)) from each generator to its bus. `generation` uses `gen_bus` to sum the dispatch by bus.

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

=== "Command line"

    ```bash
    python -m mathspec check generators.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('generators.yaml'):
        print(note)
    ```

```text
expression 'injection' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
expression 'total_cost' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
```

mathspec accepts the file, and prints one line of advice for each sum that the
file adds a term to.

Use `markdown` or [`to_markdown`](../reference/typeset.md) to print the math of `generators.yaml` on its own:

=== "Command line"

    ```bash
    python -m mathspec markdown --no-legend generators.yaml
    ```

=== "Python"

    ```python
    print(ms.to_markdown('generators.yaml', legend=False))
    ```

!!! example "Rendered output"

    A generator fleet, each unit on one bus.

    #### Variable domains

    **`dispatch`**

    ```math
    0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    #### Definitions

    **`generation`**

    ```math
    \mathit{generation}_{b,t} = \sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} \mathit{dispatch}_{t,g} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
    ```

    **`generation_cost`**

    ```math
    \mathit{generation}^{\mathrm{cost}} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
    ```

Each term appears as its own definition. The sum in `generation` covers the generators on bus $b$, the $g$ where $\mathrm{gen\_bus}(g) = b$. mathspec prints
no objective,
because the file sets none.

## The loads

Make a file `loads.yaml`. Its term, `consumption`, takes the demand out of
each bus:

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

=== "Command line"

    ```bash
    python -m mathspec check loads.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('loads.yaml'):
        print(note)
    ```

```text
expression 'injection' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
```

mathspec accepts the file, with one line of advice, for the injection.

## Merging the files

`merge` has no command, so you merge the files in Python. If you used the
command line so far, start Python in the folder that contains the files. Merge the three files, and give them as a list:

```python
import mathspec as ms

spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml'])
print(spec.expressions['injection'].expression)
print(spec.dimensions['snapshot'].description)
```

```text
generation + consumption
dispatch periods
```

`merge` writes the injection as the sum of the two terms by name, in the order of the list. In the merged spec, each term stays a reusable expression with a name (a [named expression](../reference/language/named.md#expressions)). `snapshot`
has the one description written for it, which is the description
in `network.yaml`.

Print the math of the merged spec:

```python
print(ms.to_markdown(spec, legend=False))
```

!!! example "Rendered output"

    #### Variable domains

    **`dispatch`**

    ```math
    0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    #### Definitions

    **`generation`**

    ```math
    \mathit{generation}_{b,t} = \sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} \mathit{dispatch}_{t,g} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
    ```

    **`generation_cost`**

    ```math
    \mathit{generation}^{\mathrm{cost}} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
    ```

    **`consumption`**

    ```math
    \mathrm{consumption}_{b,t} = -\mathrm{demand}_{t,b} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
    ```

    **`injection`**

    ```math
    \mathit{injection}_{t,b} = \mathit{generation}_{b,t} + \mathrm{consumption}_{b,t} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    **`total_cost`**

    ```math
    \mathit{total\_cost} = \mathit{generation}^{\mathrm{cost}}
    ```

    #### Objective

    ```math
    \min \mathit{total\_cost}
    ```

    #### Subject to

    **`balance`**

    ```math
    \mathit{injection}_{t,b} = 0 \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

The merged spec defines `injection` and `total_cost` from their terms, and the
objective and the `balance` constraint of the network use these two sums.

## The imports

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

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check imports.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('imports.yaml'):
        print(note)
    ```

```text
expression 'injection' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
expression 'total_cost' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
```

mathspec accepts the file, with the same advice as for the generators.

In Python, merge the four files:

```python
spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml', 'imports.yaml'])
print(spec.expressions['injection'].expression)
print(spec.expressions['total_cost'].expression)
```

```text
generation + consumption + purchase
generation_cost + import_cost
```

The injection has a third term at the end, and the total cost has a second
term, although `network.yaml` is unchanged. The cost of the imports is a
term, because
[`merge` takes the objective from one file only](../reference/composition.md#each-kind-of-entry).

## The emission cap

Make a file `emissions.yaml`. Its constraint caps what the fleet emits, and
the file lists `dispatch` under `given:` instead of declaring it:

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

=== "Command line"

    ```bash
    python -m mathspec check emissions.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('emissions.yaml'):
        print(note)
    ```

```text
variable 'dispatch' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this entry with the one another file declares.
```

mathspec accepts the file, and advises that another file must declare
`dispatch`.

In Python, merge all five files:

```python
spec = ms.merge(['network.yaml', 'generators.yaml', 'loads.yaml', 'imports.yaml', 'emissions.yaml'])
print(sorted(spec.constraints))
print(bool(spec.program.given))
```

```text
['balance', 'emission_limit']
False
```

The merged spec has both constraints. The cap now uses the `dispatch` that `generators.yaml` declares.
`spec.program` is the merged spec, every name resolved
(its [program](../reference/reading.md#spec-and-program)). `spec.program.given` is empty, so no
name is left for a file outside these five files to provide.

## Leaving the network out

Merge the generators and the loads without the network:

```python
ms.merge(['generators.yaml', 'loads.yaml'])
```

```text
fragments 'generators.yaml' and 'loads.yaml' add a term to 'injection', and no other fragment reads it. Add the fragment that reads 'injection', or fix the spelling under 'given:'.
```

`merge` refuses the list, because
[a term needs a file that lists its sum under `given:`](../reference/language/named.md#adds_to).

## What you built

You have built a dispatch spec from five files. The network uses two sums,
three component files add terms to those sums, and one file uses a variable that
another declares. You added the imports and the emission cap without changing `network.yaml`.

## Where to next

- [Compose a spec from several files](../howto/compose.md) lists the steps for
  `merge` and for [`override`](../reference/composition.md#override), which lays a
  file of changes (a [patch](../reference/glossary.md#patch)) over a spec.

!!! info "See also"

    - [Composing specs](../reference/composition.md), for every rule of `merge`
      and `override`, and what each of them refuses
    - The [`given` reference](../reference/language/parameters-variables-constraints.md#given),
      for the rules for a file that uses what another file declares
    - [A component library](../examples/library/index.md), for larger fragments
      beside their math
