<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Absence and `where`

This page lists the constructs that remove a row from an entry, and how
absence travels through an expression. Every entry is a table with at most one
row for each combination of labels of its dimensions (a
[coordinate](../glossary.md#coordinate)). An entry is **absent** at a
coordinate when it has no row there. For a variable, absent means that the
solver never sees it at that coordinate, and for a constraint, nothing is
required there. Absent is different from zero, because zero is a value in a
row.

## `where`

Where its condition is false, a `where:` on a variable leaves the variable absent, not zero.

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
variables:
  dispatch:
    dims: [generator]
    where: "capacity > 0"
```

<figure class="diagram">
--8<-- "docs/static/absence-where-variable.svg"
</figure>

With `capacity = {wind: 10, gas: 5, old: 0}`, the model has `dispatch[wind]`
and `dispatch[gas]`, and no `dispatch[old]`.

Where its condition is false, a `where:` on a constraint removes the row, so
the constraint requires nothing there:

<figure class="diagram">
--8<-- "docs/static/absence-where-constraint.svg"
</figure>

With the same capacities, `min_out` has rows at `wind` and `gas`, and none at
`old`.

The [condition grammar](expressions.md#conditions) defines what a `where:` may
contain.

## What creates absence

Seven constructs make a coordinate absent:

| Construct                                         | What is absent                                                              |
| ------------------------------------------------- | --------------------------------------------------------------------------- |
| `where:` on a variable                            | the variable, at the coordinates the condition excludes ([`where`](#where)) |
| `where:` on a constraint                          | the row ([`where`](#where))                                                 |
| `shift(x, along=d, offset=n)` without `edge=`     | the expression, at the edge coordinate ([shift](operators.md#shift))        |
| a key with no row in a `missing: absent` relation | the relation, at that key ([relations](relations.md#missing))               |
| a missing row of a `missing: absent` parameter    | the parameter, at that coordinate ([`missing`](#missing))                   |
| `within=` at a coordinate in no group             | the expression, at that coordinate ([`within=`](operators.md#within))       |
| a quotient whose divisor is zero                  | the quotient, at that coordinate ([reported values](#reported-values))      |

No value shifts in at the edge, so a `shift` without `edge=` has no row there:

<figure class="diagram">
--8<-- "docs/static/absence-shift.svg"
</figure>

`shift(x, along=snapshot, offset=1)` has no row at snapshot 1, so the expression is absent there.

A relation with `missing: absent` is absent at a key that has no row in the
data:

<figure class="diagram">
--8<-- "docs/static/absence-relation-missing.svg"
</figure>

`line_to` has no row for `l3`, so the relation is absent at `l3`.

## `missing`

On a parameter and on a variable, the `missing:` key sets what a coordinate
with no row means.

### `missing` on a parameter

The [`missing:`](parameters-variables-constraints.md#missing) key of a
parameter takes one of three values:

| `missing:`            | Result                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------ |
| `refused`, by default | a tool refuses the parameter if any row of its data is missing, and names the coordinate   |
| `absent`              | a missing row is absent: a term that uses the row is absent, and a sum leaves the term out |
| a value               | a missing row takes that value, wherever the model uses the parameter                      |

<figure class="diagram">
--8<-- "docs/static/absence-missing-parameter.svg"
</figure>

At `old`, where `rel_max` has no row, a tool refuses the data, or `rel_max` is
absent, `0` or `1`.

Under `refused`, the data has a row at every coordinate of the parameter, so
no expression uses a missing row. A value is the same number wherever the
parameter is used, so the file sets the number: `missing: 0` for a cost that is
zero, `missing: 1` for an efficiency of one, and `missing: false` for a flag
that is off.

Where an expression uses a missing row, the result depends on the position:

| Position                                                    | Under `absent`                                 | Under a value                                                                 |
| ----------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------- |
| a coefficient, or a constant on either side of a comparison | the row is absent                              | the value is used                                                             |
| a factor of a term of a sum                                 | the sum leaves the term out, and the row stays | the value is used                                                             |
| a divisor                                                   | the row is absent                              | the value is used. mathspec refuses `0` at load, unless a guard leaves it out |
| a `bounds:` entry                                           | that side of the variable is open              | the value is the bound                                                        |
| the amount of an `offset=` or a `window=`                   | the operator is absent at that coordinate      | the value is the amount                                                       |
| a comparison in a `where:`                                  | the comparison is false                        | the comparison uses the value                                                 |
| a bare `bool` name in a `where:`                            | the condition is false                         | the condition is the value                                                    |
| a bare number or label in a `where:`                        | the condition is false                         | the condition is false                                                        |

An amount of `0` makes `shift(x, along=t, offset=0)` equal to `x`, and
`sum_back(x, along=t, window=0)` a sum of no terms.

Three declarations set a bound only where the data has one: `missing: absent`,
`missing: .inf` or `-.inf` on the parameter, or a `where:` on the variable.
Elsewhere, that side of the variable is open.

A curve requires a row at each breakpoint within its `points:`, and [missing breakpoints](piecewise.md#missing-breakpoints) describes a missing row in its table.

### A guarded divisor

At load, mathspec refuses a divisor that a missing row of a `missing: 0`
parameter can make `0`, unless a guard leaves every missing row out where the
quotient is used. A guard is a condition that is false at a missing row, such
as `c > 0`, `c != 0` or the bare name `c`. A guard covers the quotient when it
is one of the conditions joined by `AND` in one of these places:

- the `where:` of the constraint
- the `when:` of the case that contains the quotient
- the `where:` of a `missing: absent` variable that multiplies the quotient,
  because the product is absent where that variable is absent

```yaml
dimensions:
  g: { dtype: str }
parameters:
  c: { dims: [g], missing: 0 }
  d: { dims: [g] }
variables:
  y: { dims: [g] }
constraints:
  per_unit:
    dims: [g]
    where: "c > 0"
    expression: y <= d / c
```

At a missing row of `c`, the guard `c > 0` is false, so `per_unit` has no row
there and `d / c` divides by nothing.

A variable with a `missing:` number takes that number outside its `where:`, so
its `where:` guards nothing. A guard applies only at the coordinate where it
is evaluated. A `sum`, a window, a `shift` and an `at` use other coordinates,
so a guard outside one of them does not cover a divisor inside it. A named
expression is evaluated over its own dimensions, so the guard for its divisor
goes in its own `cases:`.

### Zero divisors in the data

With data attached, an engine must refuse a divisor that is `0` in a row it
builds, or in a term of a sum it adds, and name the divisor. At load, mathspec
checks only the form of a divisor, so each of these loads, and an engine
refuses it where the data makes the divisor `0`:

- `x / (1 - c)` with `c: { missing: 1 }`, at a missing row of `c`
- `x / ((c + 1) - 1)` with `c: { missing: 0 }`, at a missing row of `c`
- a case that contains `1 - 1`, where its `when:` holds
- `x / c`, at a row of `c` whose value is `0`

An absent row or term divides by nothing, so an engine does not refuse a
divisor where a `where:`, a case or an absent variable leaves the row out. A
[reported expression](#reported-values) is not refused, because its quotient
is absent where its divisor is `0`.

### `missing` on a variable

The `missing:` key of a variable sets whether a coordinate that its `where:`
excludes is absent (`absent`, the default) or takes a number, such as `0`.
Under `absent`, a row that needs that coordinate is absent. Some quantities are
zero outside their condition, and declare `missing: 0`:

```yaml
dimensions:
  storage: { dtype: str }
parameters:
  inflow: { dims: [storage] }
  has_inflow: { dims: [storage], dtype: bool }
  has_store: { dims: [storage], dtype: bool }
variables:
  spill:
    dims: [storage]
    where: has_inflow
    missing: 0 # outside the condition spill is 0, and the row exists
  soc:
    dims: [storage]
    where: has_store # the default, missing: absent, so no row
constraints:
  balance:
    dims: [storage]
    expression: inflow - spill - soc == 0
```

<figure class="diagram">
--8<-- "docs/static/absence-missing-variable.svg"
</figure>

At a storage with a store and no inflow, `balance` is `inflow - soc == 0`, and at a storage with inflow and no store `balance` has no row.

A variable takes `missing: absent` or a finite number, because a variable has
no data for a tool to refuse. A number requires a `where:`, because a variable
with no condition exists at every coordinate, and at load mathspec refuses the
variable without one:

```text
variables.p: missing: 0 needs a `where:`. A variable with no mask exists at every coordinate of its dims, so nothing is missing. Add a `where:`, or delete `missing:`.
```

`p` has no `where:`, so no coordinate of `p` is missing.

The number must lie in the `domain:` of the variable, so a `binary` variable
takes `0` or `1`, and an `integer` variable takes an integer. The `bounds:`
apply only where the `where:` holds, so the number may lie outside them. A
unit with `lower: 1` where it is built can have `missing: 0` where it is not.

Inside a sum, `missing: 0` has no effect, because an absent term already adds
nothing there. Any other number adds itself once for each coordinate that the
`where:` excludes.

In the legend, beside the variable, the [typesetter](../typeset.md) prints the
number, such as `` `0` where the mask leaves it out ``.

## How absence travels

In arithmetic, an absent term makes the whole row absent, but inside a sum, an absent term is left out and the row stays.

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
variables:
  x: { dims: [generator] }
  y: { dims: [generator], where: "capacity > 0" } # no y[old]
constraints:
  each:
    dims: [generator]
    expression: x + y >= 1 # rows at wind and gas, no row at old
  total:
    dims: []
    expression: sum(x + y, over=generator) >= 1 # x[wind] + y[wind] + x[gas] + y[gas] >= 1
  split:
    dims: []
    expression: sum(x, over=generator) + sum(y, over=generator) >= 1 # x[old] is back in
```

<figure class="diagram">
--8<-- "docs/static/absence-travels.svg"
</figure>

With the capacities above, `y[old]` is absent, and because `x + y` is arithmetic, `each` has no row at `old`. In `total`, the term `x + y` is
absent at `old`, so the sum leaves out both `x[old]` and `y[old]`. In `split`, each sum runs over the coordinates of its own operand, so `x[old]` is in the first sum, and `total` and `split` differ.

A parameter with a missing row and an absent variable have different effects:

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
  rel_max: { dims: [generator], missing: 0 }
variables:
  x: { dims: [generator] }
  y: { dims: [generator], where: "capacity > 0" }
constraints:
  cap:
    dims: [generator]
    expression: x - rel_max * y <= 0
```

<figure class="diagram">
--8<-- "docs/static/absence-cap.svg"
</figure>

With data attached, `y` is absent at `old`, so `cap` has no row there. At `gas`,
where `rel_max` has no row, the row is `x[gas] <= 0`. With `missing: absent` on
`rel_max`, or with `where: rel_max` on the constraint, `cap` has no row there
either.

An operator has one of two results for an absent input:

| Operator                         | Inputs to one output          | At an absent input                               |
| -------------------------------- | ----------------------------- | ------------------------------------------------ |
| `sum(x, over=d)`                 | every position along `d`      | the sum leaves it out, and the row stays         |
| `sum(x, over=d, by=relation[c])` | every member of the group     | the sum leaves it out, and the row stays         |
| `sum_back(x, along=d, window=w)` | the positions in the window   | the sum leaves it out, and the row stays         |
| `shift(x, along=d, offset=n)`    | one position, `n` back        | that input is the only one, so the row is absent |
| `at(x, by=relation[c])`          | one position, through the map | that input is the only one, so the row is absent |

With data attached, a missing row that takes the value `0` can leave a
constraint row with no variable in it. In a constraint `rel_max * y <= capacity`, the row where
`rel_max` has no row is `0 <= capacity`. Before any data is attached,
mathspec [refuses](parameters-variables-constraints.md#constraints) only a
constraint whose expression has no variable. So that
constraint loads, because its expression has the variable `y`, and the row
`0 <= capacity` exists only once the data is attached.

## A table with gaps on purpose

A parameter whose data has rows only where the model needs them is declared
`missing: absent`. An [assumption](assumptions.md) then states where the data
must have a row, and the tool that attaches the data checks it:

```yaml
dimensions:
  g: { dtype: str }
parameters:
  capacity: { dims: [g] }
  p_max: { dims: [g], missing: absent }
variables:
  dispatch:
    dims: [g]
    where: "capacity > 0"
    bounds: { lower: 0, upper: p_max }
objective:
  sense: maximize
  expression: sum(dispatch, over=g)
assumptions:
  p_max_where_dispatch_exists:
    holds: "p_max"
    where: "capacity > 0"
```

With `capacity = {wind: 10, gas: 5, old: 0}`, the model has no `dispatch[old]`,
so the tool accepts `p_max` data with rows for `wind` and `gas` only. Data with
no row for `gas` fails the assumption, because `capacity > 0` holds at `gas`.
Without the assumption, a missing `p_max[gas]` leaves the upper bound of
`dispatch[gas]` open.

## Reported values

A [reported expression](named.md#reported-expressions) is computed from solved values, and is absent wherever a value that it uses is absent.

A quotient is also absent where its divisor is zero, and the zero may come
from the data or from a solved value. Here `lcoe` is a reported expression
over `generator`:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  marginal_cost: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator], bounds: { lower: 0 } }
expressions:
  cost: sum(p * marginal_cost, over=snapshot)
  delivered: sum(p, over=snapshot)
  lcoe: cost / delivered
objective:
  sense: minimize
  expression: sum(cost)
```

<figure class="diagram">
--8<-- "docs/static/absence-quotient.svg"
</figure>

With `delivered` zero at `old`, `lcoe` has rows at `wind` and `gas`, and none
at `old`.

A missing row of an `absent` parameter that divides makes the quotient absent.
At load, mathspec refuses a divisor that a `missing: 0` parameter can make
zero, unless a [guard](#a-guarded-divisor) leaves the missing row out.

!!! info "See also"

    - [`dual`](named.md#dual) for the dual of an absent constraint row.
    - [Operators](operators.md) and [conditions](expressions.md#conditions) for the operators and the `where:` grammar that this page uses.
