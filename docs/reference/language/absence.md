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
parameter takes one of four values:

| `missing:`            | Result                                                                                                                                        |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `refused`, by default | a tool refuses the parameter if any row of its data is missing, and names the coordinate                                                      |
| `absent`              | a missing row is absent: a term that uses the row is absent, and a sum leaves the term out                                                    |
| `neutral`             | a missing row takes the value that adds nothing to the expression or condition that uses it: `0` as a coefficient, and `false` in a condition |
| a value               | a missing row takes that value                                                                                                                |

<figure class="diagram">
--8<-- "docs/static/absence-missing-parameter.svg"
</figure>

At `old`, where `rel_max` has no row, a tool refuses the data, or `rel_max` is
absent, `0` or `1`.

Three positions have no neutral value: a divisor, a `bounds:` entry, and the
whole constant side of a comparison. With data attached, a missing row of a
`neutral` parameter in one of them is refused. Under `absent`, a missing
divisor or constant side is absent, and the row is absent with it.

Three declarations set a bound only where the data has one: `missing: absent`,
`missing: .inf` or `-.inf` on the parameter, or a `where:` on the variable.
Elsewhere, that side of the variable is open.

A curve requires a row at each breakpoint within its `points:`, and [missing breakpoints](piecewise.md#missing-breakpoints) describes a missing row in its table.

### `missing` on a variable

The `missing:` key of a variable sets whether a coordinate that its `where:`
excludes is absent (`absent`, the default) or zero (`neutral`). Under
`absent`, a row that needs that coordinate is absent. Some quantities are zero
outside their condition, and declare `missing: neutral`:

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
    missing: neutral # outside the condition spill is 0, and the row exists
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

`missing: neutral` requires a `where:`, because a variable with no condition
exists at every coordinate, and at load mathspec refuses the variable without one:

```text
variables.p: missing: neutral needs a `where:`. A variable with no mask exists at every coordinate of its dims, so nothing is missing. Add a `where:`, or delete `missing:`.
```

`p` has no `where:`, so no coordinate of `p` is missing.

Inside a sum, `missing: neutral` has no effect, because an absent term
already adds nothing there.

In the legend, beside the variable, the [typesetter](../typeset.md) prints
`` `neutral` where the mask leaves it out ``.

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
  rel_max: { dims: [generator], missing: neutral }
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

With data attached, a `neutral` coefficient can leave a constraint row with no
variable in it. In a constraint `rel_max * y <= capacity`, the row where
`rel_max` has no row is `0 <= capacity`. Before any data is attached,
mathspec [refuses](parameters-variables-constraints.md#constraints) only a
constraint whose expression has no variable. So that
constraint loads, because its expression has the variable `y`, and the row
`0 <= capacity` exists only once the data is attached.

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

A missing row of a parameter that divides follows the rule for a divisor. Under
`neutral` a tool refuses the data, and under `absent` the quotient is absent.

!!! info "See also"

    - [`dual`](named.md#dual) for the dual of an absent constraint row.
    - [Operators](operators.md) and [conditions](expressions.md#conditions) for the operators and the `where:` grammar that this page uses.
