<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Your first spec

In this tutorial you build the specification of an optimisation model
(a [spec](../reference/glossary.md#spec)) for least-cost dispatch. In this
model a fleet of generators meets an hourly load at the lowest cost. You build
the file one section at a time, check it after each step, and print it as math at the
end. This tutorial takes about 15 minutes. Before you start,
[install mathspec](../howto/installation.md).

One YAML file states the spec. The file contains
no data and needs no solver, so you run every step on the file alone.

## Dimensions

A [dimension](../reference/language/dimensions.md) is a set the spec is indexed over, such as the hours of a year or the generators of a fleet. Make a file
`dispatch.yaml` with a description and two dimensions:

```yaml title="dispatch.yaml"
description: Least-cost dispatch of a generator fleet against an hourly load.

dimensions:
  snapshot: { dtype: int, description: dispatch periods }
  generator: { description: generating units }
```

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check dispatch.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    for note in ms.advice('dispatch.yaml'):
        print(note)
    ```

```text
dimension 'snapshot' is never used: nothing is indexed by it, nothing sums into it, and no relation has a column over it. Remove it, or keep it if the entries that use it are still to be written.
dimension 'generator' is never used: nothing is indexed by it, nothing sums into it, and no relation has a column over it. Remove it, or keep it if the entries that use it are still to be written.
```

mathspec accepts the file. `check` prints one remark that is not a refusal (a line of
[advice](../reference/glossary.md#advice)) for
each dimension. No named parameter, variable or constraint
(an [entry](../reference/glossary.md#entry)) in the file uses either dimension yet.

Keep this Python session open. Later steps use `ms`.

## Parameters and a variable

A [parameter](../reference/language/parameters-variables-constraints.md#parameters)
is data the spec requires, and a
[variable](../reference/language/parameters-variables-constraints.md#variables)
is a decision the solver makes. Add three parameters and one variable to the
file:

```yaml
parameters:
  capacity: { dims: [generator], description: installed capacity }
  load: { dims: [snapshot], description: demand to be met }
  cost: { dims: [generator], description: marginal cost }

variables:
  dispatch:
    description: output of a generator in a snapshot
    dims: [snapshot, generator]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }
```

The `dims:` key lists the dimensions an entry is indexed over. With data
attached, `capacity` has one value for each generator, and `dispatch` has one
for each dispatch period (snapshot) and generator.

The [`where:`](../reference/language/absence.md#where) line is a condition.
With data attached, a generator with no capacity has no `dispatch` (it is
[absent](../reference/language/absence.md)).

Print the math with `markdown` or [`to_markdown`](../reference/typeset.md). The `--no-legend` flag and `legend=False` leave out the tables of symbols:

=== "Command line"

    ```bash
    python -m mathspec markdown --no-legend dispatch.yaml
    ```

=== "Python"

    ```python
    print(ms.to_markdown('dispatch.yaml', legend=False))
    ```

!!! example "Rendered output"

    Least-cost dispatch of a generator fleet against an hourly load.

    #### Variable domains

    **`dispatch`**

    ```math
    0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{capacity}_{g} > 0
    ```

In the equation, `dispatch` lies between zero and the capacity for every snapshot $t$ and every generator $g$ whose capacity is more than zero.

## A constraint and the objective

A [constraint](../reference/language/parameters-variables-constraints.md#constraints)
is a rule the decisions obey, and the
[objective](../reference/language/parameters-variables-constraints.md#objective)
is the quantity the solver makes as small or as large as it can. Add a
constraint that meets the load in every snapshot, and an objective that
minimises the cost:

```yaml
constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

The sum adds the dispatch of every generator, so with data attached,
`power_balance` has one row for each snapshot. Check the file again:

=== "Command line"

    ```bash
    python -m mathspec check dispatch.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('dispatch.yaml'):
        print(note)
    ```

`check` prints nothing, because every dimension is now used.

## An undeclared name

When mathspec first reads a file (at
[load](../reference/glossary.md#load)), it refuses the file if an expression uses a name the file does not [declare](../reference/language/expressions.md#name-resolution). Change `cost` to `costs` in the objective:

```yaml
objective:
  sense: minimize
  expression: sum(dispatch * costs)
```

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check dispatch.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('dispatch.yaml'):
        print(note)
    ```

```text
The objective: 'costs' not found.
  Variables: ['dispatch']
  Parameters: ['capacity', 'cost', 'load']
Check the spelling, or declare 'costs'.
```

mathspec refuses the file. The command exits with status 1, and [`advice`](../reference/api.md#mathspec.advice) raises [`SchemaError`](../reference/api.md#mathspec.errors.SchemaError).
mathspec names the entry with the
unknown name, lists the names the file declares, and suggests what to write instead.

Change `costs` back to `cost`:

```yaml
objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

Check the file again:

=== "Command line"

    ```bash
    python -m mathspec check dispatch.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('dispatch.yaml'):
        print(note)
    ```

`check` prints nothing again.

## The math

The whole file is now:

```yaml title="dispatch.yaml"
description: Least-cost dispatch of a generator fleet against an hourly load.

dimensions:
  snapshot: { dtype: int, description: dispatch periods }
  generator: { description: generating units }

parameters:
  capacity: { dims: [generator], description: installed capacity }
  load: { dims: [snapshot], description: demand to be met }
  cost: { dims: [generator], description: marginal cost }

variables:
  dispatch:
    description: output of a generator in a snapshot
    dims: [snapshot, generator]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }

constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

The file contains every entry the steps above added. Print the whole spec:

=== "Command line"

    ```bash
    python -m mathspec markdown dispatch.yaml
    ```

=== "Python"

    ```python
    print(ms.to_markdown('dispatch.yaml'))
    ```

!!! example "Rendered output"

    Least-cost dispatch of a generator fleet against an hourly load.

    #### Sets

    | Symbol | Meaning |
    |---|---|
    | $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
    | $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units |

    #### Parameters

    | Symbol | Meaning |
    |---|---|
    | $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{G}`$ — installed capacity |
    | $`\mathrm{load}`$ | `load` over $`\mathcal{T}`$ — demand to be met |
    | $`\mathrm{cost}`$ | `cost` over $`\mathcal{G}`$ — marginal cost |

    #### Variables

    | Symbol | Meaning |
    |---|---|
    | $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{T} \times \mathcal{G}`$ — output of a generator in a snapshot |

    #### Variable domains

    **`dispatch`**

    ```math
    0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{capacity}_{g} > 0
    ```

    #### Objective

    ```math
    \min \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
    ```

    #### Subject to

    **`power_balance`**

    ```math
    \sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
    ```

The tables at the top list the symbol and description of each set, parameter
and variable. Below them, the bounds of `dispatch`, the objective and
`power_balance` each appear as one equation.

## What you built

You have built a least-cost dispatch spec in one file. It declares two
dimensions, three parameters, a variable with bounds, a constraint and an
objective. `check` accepts it, and `markdown` prints it as math.

## Where to next

- In [A storage unit over time](storage.md) you add a dimension in a fixed
  order, and link each hour to the hour before it.
- In [A spec in several files](several-files.md) you split a spec into files
  that each contain one part of it.
- [Print a spec as math](../howto/print.md) lists the steps to print a spec in two
  typesetting languages (LaTeX and Typst).

!!! info "See also"

    - [The language](../reference/language/index.md), for every rule a file must
      follow
    - [Examples](../examples/index.md), for larger specs beside their math
