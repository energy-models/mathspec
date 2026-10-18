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
`dispatch[gas]`, but no `dispatch[old]`.

The [`where` grammar](expressions.md#where-strings) says what a `where:` may
hold.

## What creates absence

| Construct                                                     | What is absent                                                                     |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `where:` on a variable                                        | the variable, at the masked coordinates                                            |
| `where:` on a constraint                                      | the row                                                                            |
| `shift(x, along=d, offset=n)` without `edge=`                 | the vacated edge coordinate ([shift](operators.md#shift))                          |
| a key combination a `missing: absent` relation has no row for | that combination's place in the relation ([relations](relations.md#a-missing-row)) |
| a missing row of a `missing: absent` parameter                | the parameter, at that coordinate                                                  |

Nothing else creates absence. A missing row is the only gap a parameter can
have, because a null or NaN value is [refused](parameters-variables-constraints.md#parameters) when
the data is attached. The parameter's [`missing:`](parameters-variables-constraints.md#a-missing-row)
key says what a missing row is:

| `missing:`            | A missing row                                               |
| --------------------- | ----------------------------------------------------------- |
| `refused`, by default | is refused when the data is attached                        |
| `absent`              | is absence, by the rules on this page                       |
| a value               | reads as that value, wherever the model reads the parameter |

Under `refused`, the table has a row at every combination of the labels of its
dimensions, so no position ever reads a missing row. A value is the same
number at every position, so the file says what a missing row is: `missing: 0`
for a cost that is zero, `missing: 1` for an efficiency that is one, and
`missing: false` for a flag that is off. The table below says what a missing
row of an `absent` parameter, or of a parameter with a value, does at each
position:

| Position                                                    | `absent`                              | a value                                 |
| ----------------------------------------------------------- | ------------------------------------- | --------------------------------------- |
| a coefficient, or a constant on either side of a comparison | removes the row                       | reads the value                         |
| a factor of a summand in a `sum`                            | removes the summand, not the row      | reads the value                         |
| a divisor                                                   | removes the row                       | reads the value. `0` is refused at load |
| a `bounds:` entry                                           | leaves that side of the variable open | reads the value                         |
| the amount of an `offset=` or a `window=`                   | makes the operator absent there       | reads the value                         |
| a comparison in a `where`                                   | is false                              | compares the value                      |
| a bare `bool` name in a `where`                             | is false                              | reads the value                         |
| a bare number or label in a `where`                         | is false                              | is false                                |

A value of `0` as an amount reads `shift(x, along=t, offset=0)` as `x` itself,
and sums nothing under `sum_back(x, along=t, window=0)`. A curve needs a row at
each breakpoint its `points:` admits, and
[missing breakpoints](piecewise.md#missing-breakpoints) says what a missing row
of a table that a curve reads means. For a bound only where the data has one,
mask the variable, or declare the parameter `missing: absent` or
`missing: .inf`.

## How absence travels

An absent term in arithmetic removes the whole row. An absent term inside a
summing operator is only one summand fewer, so the row stays.

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

`total` sums the summand wherever the summand exists, but `split` sums each
operand over its own domain, so the two are different constraints.

A parameter with a missing row works the other way:

```yaml
constraints:
  cap:
    dims: [g]
    expression: x - rel_max * y <= 0
```

Where the variable `y` is masked, the row is gone. Where a `missing: 0`
parameter `rel_max` has no row, it reads as `0`, and the row stands as
`x <= 0`. To drop the row there instead, declare `rel_max` `missing: absent`, or
write `where: rel_max` on the constraint.

| Operator                         | An output slot reads            | An absent input                      |
| -------------------------------- | ------------------------------- | ------------------------------------ |
| `sum(x, over=d)`                 | every position along `d`        | is one summand fewer; the row stands |
| `sum(x, over=d, by=relation[c])` | every member of the group       | is one summand fewer; the row stands |
| `sum_back(x, along=d, window=w)` | the positions the window covers | is one summand fewer; the row stands |
| `shift(x, along=d, offset=n)`    | one position, `n` back          | _is_ the output, so it spreads       |
| `at(x, by=relation[c])`          | one position, through the map   | _is_ the output, so it spreads       |

## A table with gaps on purpose

A table that has rows only where the model needs them is declared
`missing: absent`. An [assumption](assumptions.md) then says where the table
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
assumptions:
  p_max_where_dispatch_exists:
    holds: "p_max"
    where: "capacity > 0"
```

With `capacity = {wind: 10, gas: 5, old: 0}`, the model has no `dispatch[old]`,
so a `p_max` table with rows for `wind` and `gas` only is accepted. A table with
no row for `gas` fails the assumption, because `capacity > 0` holds at `gas`.
Without the assumption, a missing `p_max[gas]` leaves the upper bound of
`dispatch[gas]` open.

## What a missing coordinate means

By default a masked coordinate has **no value**, and a row that needs it is not
built. Some quantities have a known number outside their mask, such as **zero**,
and the `missing:` key of the variable names it:

```yaml
variables:
  spill:
    dims: [storage]
    where: has_inflow
    missing: 0 # outside the mask spill is 0 and the row stands
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

A variable takes `missing: absent` or a finite number, because a variable has
no data to refuse. A number needs a `where:`. It must lie in the `domain:` of
the variable, so a `binary` variable takes `0` or `1`, and inside its literal
`bounds:`. `to_spec` refuses the file otherwise. Inside a summing operator,
`missing: 0` changes nothing, and another number adds itself once for each
coordinate that the mask leaves out. The typeset legend prints the number
where the mask leaves it out beside the variable.

## Rows with no variable terms

A missing row that reads as `0` can leave a row with nothing to decide, such as
`0 == load` at a bus with no generator, and such a row is not built. `to_spec`
refuses an expression that names no variable _in the file_.

## Reported values

A [reported expression](named.md#reported-expressions) inherits the absence of
the solved numbers it reads, by the rules above. A quotient is absent where its
divisor is absent, and where its divisor is exactly zero, whether a solve or the
data gave that zero. A solved value is read as the engine reads it back, so
an engine may read a value within its solver's tolerance of zero as zero. A
missing row of an `absent` divisor parameter makes the quotient absent, and
`to_spec` refuses a divisor that a `missing: 0` parameter can make zero. A
deleted row has [no dual](named.md#reading-a-constraints-dual).
