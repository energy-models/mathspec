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

| `missing:`            | A missing row                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------------- |
| `refused`, by default | is refused where the model reads it ([where a parameter is read](#where-a-parameter-is-read)) |
| `absent`              | is absence, by the rules on this page                                                         |
| a value               | reads as that value, wherever the model reads the parameter                                   |

A value is the same number at every position, so the file says what a missing
row is: `missing: 0` for a cost that is zero, `missing: 1` for an efficiency
that is one, and `missing: false` for a flag that is off. The table below says
what a missing row does at each position:

| Position                                                    | `refused`  | `absent`                              | a value                                 |
| ----------------------------------------------------------- | ---------- | ------------------------------------- | --------------------------------------- |
| a coefficient, or a constant on either side of a comparison | is refused | removes the row                       | reads the value                         |
| a factor of a summand in a `sum`                            | is refused | removes the summand, not the row      | reads the value                         |
| a divisor                                                   | is refused | removes the row                       | reads the value. `0` is refused at load |
| a `bounds:` entry                                           | is refused | leaves that side of the variable open | reads the value                         |
| the amount of an `offset=` or a `window=`                   | is refused | makes the operator absent there       | reads the value                         |
| a comparison in a `where`                                   | is false   | is false                              | compares the value                      |
| a bare `bool` name in a `where`                             | is refused | is false                              | reads the value                         |
| a bare number or label in a `where`                         | is false   | is false                              | is false                                |

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

## Where a parameter is read

A `refused` parameter needs a row at each coordinate where the model reads its
value, and at no other coordinate. A tool builds the masks first, because the
masks decide which variables and rows exist. Then the tool refuses a missing
row at a coordinate the model reads, and names the parameter and the
coordinate.

```yaml
dimensions:
  g: { dtype: str }
parameters:
  capacity: { dims: [g] }
  p_max: { dims: [g] } # refused, by default
variables:
  dispatch:
    dims: [g]
    where: "capacity > 0"
    bounds: { lower: 0, upper: p_max }
```

With `capacity = {wind: 10, gas: 5, old: 0}`, the model has no `dispatch[old]`.
So the model never reads `p_max[old]`, and a `p_max` table with rows for `wind`
and `gas` only is accepted. A `p_max` table with no row for `gas` is refused,
because the model reads the upper bound of `dispatch[gas]`.

The model reads a parameter where its value goes into the model it builds:

| The parameter stands as                                          | The model reads it at                                                    |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------ |
| a coefficient, a divisor or a constant in a constraint           | each row that the model builds                                           |
| a factor of a summand in `sum` or `sum_back`                     | each summand that exists, so not where the summand has an absent factor  |
| a `bounds:` entry                                                | each coordinate where the variable exists                                |
| the amount of an `offset=` or a `window=`                        | each coordinate where a row that the model builds evaluates the operator |
| a term of the objective                                          | each term that exists                                                    |
| a term of a [reported expression](named.md#reported-expressions) | each coordinate where the expression is reported                         |
| a values parameter of a [`piecewise:`](piecewise.md) entry       | each breakpoint that the curve runs through                              |
| a bare `bool` name in a `where`                                  | each coordinate where the model evaluates that `where`                   |

A row that an absent term removes is not built, so the model reads no
parameter in that row. A tool does not have to build the model to apply this
rule: [`program.reads`](../reading.md#where-the-model-reads-each-parameter)
gives the mask of each `refused` parameter, which the tool evaluates when it
attaches the data.

A `where` reads one kind of parameter: a bare `bool` name, such as
`where: committable`, reads the value of the flag. The model evaluates the
`where` of a variable or a constraint at every coordinate of its dims, and the
`when` of a case wherever it evaluates the expression that holds the case. A
flag under `count`, `shift` or `at` in a `where` is read at each position that
the operator looks at, and a flag in a [mask](named.md#masks) wherever the
mask is evaluated. Both sides of `AND` and `OR` are evaluated.

Every other part of a `where` reads no parameter. A bare number or label asks
whether the table has a row. A comparison at a missing row is false, unless the
`missing:` of the parameter names a value. So `where: "capacity > 0"` above is
false at a generator with no `capacity` row, and that generator has no
`dispatch`. Because a comparison reads nothing, `where: "cost AND cost > 0"`
selects the rows of a sparse `refused` table `cost` without refusing it.

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
divisor parameter with a missing row where the quotient is read is refused,
unless the parameter is `missing: absent` or names a value other than `0`. A deleted row has
[no dual](named.md#reading-a-constraints-dual).
