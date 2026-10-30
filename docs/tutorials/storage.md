<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A storage unit over time

In this tutorial you build a specification of an optimisation model
(a [spec](../reference/glossary.md#spec)) for a battery. The battery buys power
when it is cheap and sells it when it is expensive. On the way you declare a set of labels
(a [dimension](../reference/language/dimensions.md)) in a fixed order. You then link each hour to the hour before it. You also leave out every
battery that has no capacity. This tutorial takes about 20 minutes.

Do [your first spec](first-spec.md) first.

## Dimensions

The spec has two dimensions: the hours
of a day, and the batteries. Make a file `storage.yaml`:

```yaml title="storage.yaml"
description: A battery that buys power when it is cheap and sells it when it is expensive.

dimensions:
  snapshot: { dtype: int, description: hours of the day }
  store: { description: batteries }
```

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check storage.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    for note in ms.advice('storage.yaml'):
        print(note)
    ```

```text
dimension 'snapshot' is never used: nothing is indexed by it, nothing sums into it, and no relation has a column over it. Remove it, or keep it if the entries that use it are still to be written.
dimension 'store' is never used: nothing is indexed by it, nothing sums into it, and no relation has a column over it. Remove it, or keep it if the entries that use it are still to be written.
```

mathspec accepts the file. `check` prints one remark that is not a refusal (a line of
[advice](../reference/glossary.md#advice)) for
each dimension. No named parameter, variable or constraint
(an [entry](../reference/glossary.md#entry)) uses either dimension yet.

Keep this Python session open. Later steps use `ms`.

## Parameters, variables and the objective

Each battery has an energy capacity and a power rate, and the price of power
changes from hour to hour. These three quantities are data the spec requires
([parameters](../reference/language/parameters-variables-constraints.md#parameters)). A battery also has three solver decisions
([variables](../reference/language/parameters-variables-constraints.md#variables)). They are the power it takes in, the power it gives out, and the energy it holds after each hour (its state of charge).

The quantity the solver optimises
(the [objective](../reference/language/parameters-variables-constraints.md#objective)) is what the batteries pay for power less what they earn
from it. Add the parameters, the variables and the objective:

```yaml
parameters:
  capacity: { dims: [store], description: energy a battery holds when full }
  rate: { dims: [store], description: most power a battery takes in or gives out }
  price: { dims: [snapshot], description: price of power }

variables:
  charge:
    description: power a battery takes in
    dims: [snapshot, store]
    bounds: { lower: 0, upper: rate }
  discharge:
    description: power a battery gives out
    dims: [snapshot, store]
    bounds: { lower: 0, upper: rate }
  soc:
    description: energy a battery holds at the end of an hour
    dims: [snapshot, store]
    bounds: { lower: 0, upper: capacity }

objective:
  sense: minimize
  expression: sum((charge - discharge) * price)
```

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check storage.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('storage.yaml'):
        print(note)
    ```

`check` prints nothing. No rule links the variables
yet, so with data attached, a solver could let a battery sell more power than the
battery bought.

## The state of charge

The energy balance links each hour of a battery to the hour before. A battery
ends each hour with the energy it had an hour before, plus what it
took in, less what it gave out.
[`shift`](../reference/language/operators.md#shift) takes the value of an
expression at another position along a dimension. So
`shift(soc, along=snapshot, offset=1)` is `soc` one hour earlier. Add the energy balance as a rule the decisions must satisfy
(a [constraint](../reference/language/parameters-variables-constraints.md#constraints)):

```yaml
constraints:
  energy_balance:
    dims: [snapshot, store]
    expression: soc == shift(soc, along=snapshot, offset=1) + charge - discharge
```

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check storage.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('storage.yaml'):
        print(note)
    ```

```text
Constraint 'energy_balance': shift(along=snapshot) reads the order of 'snapshot', which is not declared ordered, so the order would come from the row order of the data. Declare 'snapshot: {ordered: true}' under dimensions:.
```

When mathspec first reads the file
(at [load](../reference/glossary.md#load)), it refuses the file. The command exits with status 1, and [`advice`](../reference/api.md#mathspec.advice) raises [`SchemaError`](../reference/api.md#mathspec.errors.SchemaError). `shift` counts positions
along `snapshot`, and the file does not declare `snapshot` as ordered.

## Declaring the order

An [ordered dimension](../reference/language/dimensions.md#ordered) is one whose
order `shift` may use. Add `ordered: true` to `snapshot`:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true, description: hours of the day }
  store: { description: batteries }
```

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check storage.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('storage.yaml'):
        print(note)
    ```

`check` prints nothing. With data attached, the first
hour has no hour before it, so the row of `energy_balance` there does
not exist (it is [absent](../reference/language/absence.md)).

## Closing the day on itself

The `edge=` argument of `shift` sets the value of `shift` at the first hour.
With `edge='wrap'`, at the first hour the shift takes `soc` at the last
hour. Each battery then ends the day with the energy it started with. Change the constraint:

```yaml
constraints:
  energy_balance:
    dims: [snapshot, store]
    expression: soc == shift(soc, along=snapshot, offset=1, edge='wrap') + charge - discharge
```

Print the math, without the tables of symbols:

=== "Command line"

    ```bash
    python -m mathspec markdown --no-legend storage.yaml
    ```

=== "Python"

    ```python
    print(ms.to_markdown('storage.yaml', legend=False))
    ```

!!! example "Rendered output"

    A battery that buys power when it is cheap and sells it when it is expensive.

    #### Variable domains

    **`charge`**

    ```math
    0 \le \mathit{charge}_{t,s} \le \mathrm{rate}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

    **`discharge`**

    ```math
    0 \le \mathit{discharge}_{t,s} \le \mathrm{rate}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

    **`soc`**

    ```math
    0 \le \mathit{soc}_{t,s} \le \mathrm{capacity}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

    #### Objective

    ```math
    \min \sum_{t \in \mathcal{T},\ s \in \mathcal{S}} \left( \mathit{charge}_{t,s} - \mathit{discharge}_{t,s} \right) \cdot \mathrm{price}_{t}
    ```

    #### Subject to

    **`energy_balance`**

    ```math
    \mathit{soc}_{t,s} = \mathit{soc}_{t \ominus 1,s} + \mathit{charge}_{t,s} - \mathit{discharge}_{t,s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

The constraint contains $\mathit{soc}_{t \ominus 1,s}$, the state of charge at
the hour before $t$, counted around the day. With data attached, every hour now has a row.

## Leaving out a battery with no capacity

Where its condition is false, a [`where:`](../reference/language/absence.md#where) line leaves out the rows of an entry. Add `where: "capacity > 0"` to each variable:

```yaml
variables:
  charge:
    description: power a battery takes in
    dims: [snapshot, store]
    where: "capacity > 0"
    bounds: { lower: 0, upper: rate }
  discharge:
    description: power a battery gives out
    dims: [snapshot, store]
    where: "capacity > 0"
    bounds: { lower: 0, upper: rate }
  soc:
    description: energy a battery holds at the end of an hour
    dims: [snapshot, store]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }
```

Check the file:

=== "Command line"

    ```bash
    python -m mathspec check storage.yaml
    ```

=== "Python"

    ```python
    for note in ms.advice('storage.yaml'):
        print(note)
    ```

`check` prints nothing. With data attached, a
battery with no capacity has no `charge`, `discharge` or `soc`.

## The math

The whole file is now:

```yaml title="storage.yaml"
description: A battery that buys power when it is cheap and sells it when it is expensive.

dimensions:
  snapshot: { dtype: int, ordered: true, description: hours of the day }
  store: { description: batteries }

parameters:
  capacity: { dims: [store], description: energy a battery holds when full }
  rate: { dims: [store], description: most power a battery takes in or gives out }
  price: { dims: [snapshot], description: price of power }

variables:
  charge:
    description: power a battery takes in
    dims: [snapshot, store]
    where: "capacity > 0"
    bounds: { lower: 0, upper: rate }
  discharge:
    description: power a battery gives out
    dims: [snapshot, store]
    where: "capacity > 0"
    bounds: { lower: 0, upper: rate }
  soc:
    description: energy a battery holds at the end of an hour
    dims: [snapshot, store]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }

constraints:
  energy_balance:
    dims: [snapshot, store]
    expression: soc == shift(soc, along=snapshot, offset=1, edge='wrap') + charge - discharge

objective:
  sense: minimize
  expression: sum((charge - discharge) * price)
```

Print the whole spec:

=== "Command line"

    ```bash
    python -m mathspec markdown storage.yaml
    ```

=== "Python"

    ```python
    print(ms.to_markdown('storage.yaml'))
    ```

!!! example "Rendered output"

    A battery that buys power when it is cheap and sells it when it is expensive.

    #### Sets

    | Symbol | Meaning |
    |---|---|
    | $`\mathcal{T}`$ | index $`t`$ — `snapshot` — hours of the day |
    | $`\mathcal{S}`$ | index $`s`$ — `store` — batteries |

    #### Parameters

    | Symbol | Meaning |
    |---|---|
    | $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{S}`$ — energy a battery holds when full |
    | $`\mathrm{rate}`$ | `rate` over $`\mathcal{S}`$ — most power a battery takes in or gives out |
    | $`\mathrm{price}`$ | `price` over $`\mathcal{T}`$ — price of power |

    #### Variables

    | Symbol | Meaning |
    |---|---|
    | $`\mathit{charge}`$ | `charge` over $`\mathcal{T} \times \mathcal{S}`$ — power a battery takes in |
    | $`\mathit{discharge}`$ | `discharge` over $`\mathcal{T} \times \mathcal{S}`$ — power a battery gives out |
    | $`\mathit{soc}`$ | `soc` over $`\mathcal{T} \times \mathcal{S}`$ — energy a battery holds at the end of an hour |

    #### Notation

    | Symbol | Meaning |
    |---|---|
    | $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |

    #### Variable domains

    **`charge`**

    ```math
    0 \le \mathit{charge}_{t,s} \le \mathrm{rate}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{capacity}_{s} > 0
    ```

    **`discharge`**

    ```math
    0 \le \mathit{discharge}_{t,s} \le \mathrm{rate}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{capacity}_{s} > 0
    ```

    **`soc`**

    ```math
    0 \le \mathit{soc}_{t,s} \le \mathrm{capacity}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{capacity}_{s} > 0
    ```

    #### Objective

    ```math
    \min \sum_{t \in \mathcal{T},\ s \in \mathcal{S}} \left( \mathit{charge}_{t,s} - \mathit{discharge}_{t,s} \right) \cdot \mathrm{price}_{t}
    ```

    #### Subject to

    **`energy_balance`**

    ```math
    \mathit{soc}_{t,s} = \mathit{soc}_{t \ominus 1,s} + \mathit{charge}_{t,s} - \mathit{discharge}_{t,s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

The notation table lists the meaning of $t \ominus k$.

mathspec prints the condition on each variable's `where:` line, $\mathrm{capacity}_{s} > 0$, at the end of the variable's bounds. `energy_balance` has no condition of its own, so
mathspec prints none for it. With data attached, the rows of `energy_balance`
are absent wherever its variables are.

## What you built

You have built the spec of a battery that trades against an hourly price. The
spec's hours are in a fixed order, and `energy_balance` uses `shift` to link the state of charge to the hour before. The first hour takes the state of charge of the last. With data attached, a battery with no
capacity has no variables and no rows.

## Where to next

- In [A spec in several files](several-files.md) you split a spec into files
  that each contain one part of it.

!!! info "See also"

    - The [`shift` reference](../reference/language/operators.md#shift), for the other values
      of `edge=`, an offset read from a parameter, and a shift within groups
    - [Absence and where](../reference/language/absence.md), for every way a row
      becomes absent, and how absence spreads
    - [Unit commitment](../examples/commitment.md), for start-up and ramping limits
      written with `shift`
