<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Absence and `where`

A `where:` does not set a variable to zero. It leaves the variable **unbuilt**
at the masked coordinates: no column, and no value.

```yaml
dimensions:
  g: { dtype: str }
parameters:
  capacity: { dims: [g] }
variables:
  dispatch:
    dims: [g]
    where: "capacity > 0"
```

With `capacity = {wind: 10, gas: 5, old: 0}`, the model has `dispatch[wind]` and
`dispatch[gas]`. There is no `dispatch[old]`.

The [grammar](expressions.md#where-strings) says what a `where:` may hold.

## What creates absence

| Construct                                         | What is absent                                                              |
| ------------------------------------------------- | --------------------------------------------------------------------------- |
| `where:` on a variable                            | the variable, at the masked coordinates                                     |
| `where:` on a constraint                          | the row                                                                     |
| `shift(x, along=d, offset=n)` without `edge=`     | the vacated edge coordinate ([shift](operators.md#shift))                   |
| a label a `missing: absent` relation does not map | that label's group membership ([relations](relations.md#the-data-contract)) |
| a missing row of a `missing: absent` parameter    | the parameter, at that coordinate                                           |

Nothing else creates absence. A missing row is the only gap a parameter has: a
null or NaN value is [refused](declarations.md#parameters) when the data is
attached. **The parameter's [`missing:`](declarations.md#a-missing-row) says
what a missing row is:**

| `missing:`            | A missing row                                                                               |
| --------------------- | ------------------------------------------------------------------------------------------- |
| `refused`, by default | is refused when the data is attached                                                        |
| `absent`              | is absence, by the rules on this page                                                       |
| `neutral`             | reads as the value that contributes nothing: `0` as a coefficient, and `false` in a `where` |
| a value               | reads as that value                                                                         |

`neutral` has no value in three positions: a divisor, a `bounds:` entry, and
the whole constant side of a comparison. A missing row there is refused when
the data is attached. A [`piecewise:`](piecewise.md) block owns the parameters
it reads, so they take no `missing:`, and a curve needs a row at each breakpoint
its `points:` admits. Under
`absent`, a missing divisor or constant side is absence and takes the row, and a
missing bound leaves that side of the variable open. For a bound only where the
data has one, declare the parameter `missing: absent` or `missing: .inf`, or mask
the variable.

## How absence travels

Through arithmetic, absence spreads and takes the row with it. Out of a summing
operator, it does not.

```yaml
variables:
  x: { dims: [g] }
  y: { dims: [g], where: "capacity > 0" } # no y[old]
constraints:
  each:
    dims: [g]
    expression: x + y >= 1 # rows at wind and gas; no row at old
  total:
    dims: []
    expression: sum(x + y, over=g) >= 1 # x[wind] + y[wind] + x[gas] + y[gas] >= 1
  split:
    dims: []
    expression: sum(x, over=g) + sum(y, over=g) >= 1 # x[old] is back in
```

`total` sums the summand wherever the summand exists. `split` sums each
operand over its own domain. The two are different constraints.

Beside a parameter, the rule reads the other way:

```yaml
constraints:
  cap:
    dims: [g]
    expression: x - rel_max * y <= 0
```

Where the variable `y` is masked, the row is gone. Where a `missing: neutral`
parameter `rel_max` has no row, it reads as `0`, and the row stands as
`x <= 0`. To drop the row there instead, declare `rel_max` `missing: absent`, or
write `where: rel_max` on the constraint.

| Operator                              | An output slot reads            | An absent input                      |
| ------------------------------------- | ------------------------------- | ------------------------------------ |
| `sum(x, over=d)`                      | every position along `d`        | is one summand fewer; the row stands |
| `sum(x, by=relation, over=a, into=b)` | every member of the group       | is one summand fewer; the row stands |
| `sum_back(x, along=d, window=w)`      | the positions the window covers | is one summand fewer; the row stands |
| `shift(x, along=d, offset=n)`         | one position, `n` back          | _is_ the output, so it spreads       |
| `at(x, by=relation, over=a, into=b)`  | one position, through the map   | _is_ the output, so it spreads       |

## What a missing coordinate means

By default a masked coordinate has **no value**, and a row that needs it is not
built. Some quantities are **zero** outside their mask, and the variable says
which reading applies:

```yaml
variables:
  spill:
    dims: [storage]
    where: has_inflow
    missing: neutral # outside the mask spill is 0 and the row stands
  soc:
    dims: [storage]
    where: has_store # the default, missing: absent — no row
constraints:
  balance:
    dims: [storage]
    expression: inflow - spill - soc == 0
```

At a storage with a store and no inflow, `balance` reads `inflow - soc == 0`. At
a storage with inflow and no store, there is no row.

`missing: neutral` needs a `where:`. It changes nothing inside a summing operator.

## Rows with no variable terms

A `neutral` parameter row can leave a row with nothing to decide, such as
`0 == load` at a bus with no generator. Such a row is not built. An expression that names no variable _in the file_ is refused at
load.

## Reported values

A [reported expression](named.md#reported-expressions) inherits the absence of
the solved numbers it reads, by the rules above. A quotient is absent where its
divisor is absent, and where its divisor is exactly zero, whether a solve or the
data gave that zero. A solved value is read as the engine reads it back, and an
engine may read a value within its solver's tolerance of zero as zero.
A divisor parameter with a missing row where the quotient is read is refused,
unless the parameter is `missing: absent` or names a value. A deleted row has
[no dual](named.md#reading-a-constraints-dual).
