<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Parameters, variables, constraints and the objective

You declare the data, the decisions, the rules and the goal of a spec in four
blocks. A fifth block, `given:`, names what the file reads from another file.
Each block takes an optional `description:`, free text that the
[typeset](../typeset.md#descriptions) legend prints.

## `parameters`

A parameter declares the dimensions of a data column, and the numbers arrive
with the data, matched by name.

```yaml
dimensions:
  snapshot: { dtype: int }
parameters:
  load:
    dims: [snapshot]
  discount_rate:
    dims: [] # a scalar
```

| Field         |                                                                |                   |
| ------------- | -------------------------------------------------------------- | ----------------- |
| `dims`        | required. The dimensions it is indexed by. `[]` means a scalar |                   |
| `dtype`       | `float`, `int`, `bool`, `str`                                  | default `float`   |
| `missing`     | what a missing row means ([a missing row](#a-missing-row))     | default `refused` |
| `description` | free text                                                      | default `null`    |

The column has to match the `dtype`:

| declared | the column                        |                                               |
| -------- | --------------------------------- | --------------------------------------------- |
| `float`  | a float column, or an integer one |                                               |
| `int`    | an integer column                 |                                               |
| `bool`   | a boolean column                  | `1` and `0` are not booleans. Cast the column |
| `str`    | a string column                   |                                               |

A null or NaN value is **refused** when the data is attached, so a coordinate
with no value has no row. `inf` and `-inf` are values.

Only `float` and `int` are values. A `str` parameter is a label and a `bool`
parameter is a mask, and each selects rows in a
[`where`](expressions.md#where-strings). Writing either as a coefficient, a
term or a divisor is a load error, so declare a `0` or `1` that you multiply by
as `dtype: int`.

### A missing row

`missing:` says what it means when the data has no row at a coordinate of the
`dims`. A table that lost a row in preparation looks the same as a table that
never had the row, so the file says which one you mean.

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  cost: { dims: [generator] } # refused: every generator has a cost
  start_up_cost: { dims: [generator], missing: neutral } # no row means no cost
  p_set: { dims: [generator], missing: absent } # no row, no fixing row
  efficiency: { dims: [generator], missing: 1 }
  p_nom_max: { dims: [generator], missing: .inf }
  active: { dims: [generator], dtype: bool, missing: true }
```

| `missing:`            | A missing row                                                                                         |
| --------------------- | ----------------------------------------------------------------------------------------------------- |
| `refused`, by default | is refused when the data is attached, and the refusal names the coordinate                            |
| `absent`              | is [absence](absence.md): it takes the row of a term that reads it, and is one summand fewer in a sum |
| `neutral`             | reads as the value that contributes nothing: `0` as a coefficient, and `false` in a `where`           |
| a value               | reads as that value, wherever a value is read                                                         |

A consumer does not build the model from data with a refused row, and each
consumer decides how it reports this: it may raise at the first gap, or list
every missing coordinate.

A bare numeric name in a `where` asks whether the data has a row, whatever the
`missing:`, so `where: p_nom_max` selects the rows the data gives. Under
`refused` every coordinate has a row, so a bare `float` name asks only "is it
finite?", and a bare `int` or `str` name is a load error. A comparison reads the
value, so `where: efficiency <= 1` is true at a missing row of `efficiency`
above, which reads `1` there. Under `absent` and `neutral`, a comparison at a
missing row is false. A bare `bool` name reads its value, so `where: active`
reads `true` at a missing row.

A value has the parameter's dtype:

| `dtype` | a value                                                  |
| ------- | -------------------------------------------------------- |
| `float` | a number. `.inf`, `inf`, `-.inf` and `-inf` are numbers  |
| `int`   | an integer. An integer column cannot hold `inf`          |
| `bool`  | `true` or `false`                                        |
| `str`   | none. A label has no value to fill, and no `neutral` one |

A NaN, a quoted number and `missing: null` are refused. A `given:` parameter
has no `missing:`, because the file that declares the parameter owns it. A
parameter that a [`piecewise:`](piecewise.md#missing-breakpoints) block reads
takes `missing:` too, and a values parameter of a curve with `points:` declares
a `missing:` other than `refused`.

The typeset legend prints what a missing row means beside the parameter, such
as `` `neutral` where the data has no row ``, and prints nothing for `refused`.

## `variables`

A variable is what the solver decides, with one column per coordinate of
`dims`.

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
variables:
  dispatch:
    dims: [snapshot, generator]
    where: "capacity > 0"
    bounds:
      lower: 0
      upper: capacity
```

| Field                           |                                                                                                                   |                      |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------- |
| `dims`                          | required. The dimensions it is indexed by                                                                         |                      |
| `where`                         | which coordinates exist ([absence](absence.md))                                                                   | default `null`       |
| `bounds.lower` / `bounds.upper` | a finite number, or the name of a `float` or `int` parameter. `null` leaves that side open                        | default `null`       |
| `domain`                        | `continuous`, `integer` or `binary`. `binary` carries fixed 0/1 bounds                                            | default `continuous` |
| `missing`                       | `absent` or `neutral`: what a masked-out coordinate means ([absence](absence.md#what-a-missing-coordinate-means)) | default `absent`     |
| `description`                   | free text                                                                                                         | default `null`       |

An open side is `null`, because a bound is never infinite: `.inf` and `-.inf`
are refused, with `null` named as the rewrite.

A bound is a name or a number, so `upper: capacity` is accepted and
`upper: -rating` is refused. Supply the negated column as data.

Equal bounds pin a variable ([fix a quantity](../../howto/pin-a-variable.md)),
and a pinned variable is still a variable.

## `given`

`given:` holds what this file reads and does not build: data under
`parameters:`, columns under `variables:`, named expressions under
`expressions:`, masks under `masks:`, and row families under `constraints:`. It
takes those five keys and no other, and a file with a `given:` block loads and
prints on its own.

### `given: parameters`

A given parameter is data this file reads and another file declares.

```yaml
given:
  parameters:
    gen_cost: { dims: [generator], description: what one unit of output costs }
    gen_on: { dims: [generator], dtype: bool }
  variables:
    gen_p: { dims: [snapshot, generator] }
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
constraints:
  off_units_idle:
    dims: [snapshot, generator]
    where: not gen_on
    expression: gen_p <= 0
objective:
  sense: minimize
  expression: sum(gen_p * gen_cost)
```

| Field         |                                                      |                 |
| ------------- | ---------------------------------------------------- | --------------- |
| `dims`        | required. The dimensions the parameter is indexed by |                 |
| `dtype`       | `float`, `int`, `bool` or `str`                      | default `float` |
| `description` | free text                                            | default `null`  |

A given parameter is read wherever a parameter is: in an expression, a `where`
and a bound. A name declared under both `parameters:` and
`given: parameters:` is refused. The typeset legend lists a given parameter
under _Given_.

### `given: variables`

A given variable is a column this file reads and another file introduces.

```yaml
given:
  variables:
    flow:
      dims: [snapshot, port]
      description: what a port puts into its bus
dimensions:
  snapshot: { dtype: int }
  port: { dtype: str }
  generator: { dtype: str }
relations:
  gen_port: { key: generator, values: port }
variables:
  gen_p: { dims: [snapshot, generator], bounds: { lower: 0 } }
constraints:
  gen_injects:
    dims: [snapshot, generator]
    expression: at(flow, by=gen_port[port]) == gen_p
```

| Field         |                                                   |                      |
| ------------- | ------------------------------------------------- | -------------------- |
| `dims`        | required. The dimensions the column is indexed by |                      |
| `domain`      | `continuous`, `integer` or `binary`               | default `continuous` |
| `description` | free text                                         | default `null`       |

There is no `bounds` and no `where`, because the file that introduces the
column owns both.

An expression reads a given variable as it reads any other. A name declared
under both `variables:` and `given: variables:` is refused. The typeset legend
lists a given variable under _Given_, and prints no domain line for it.

[`merge`](../../howto/compose.md#a-library-of-components) folds a given
declaration into the declaration of another fragment that introduces the name,
so a composed library carries none of them. The merged spec keeps the
declaration of the file that introduces the name, and the `given:` entry has to
state the same, or less.

Where nothing in this language introduces the column, the program carries the
declaration until a host model provides it
([what a program does not build](../reading.md#what-a-program-does-not-build)).

### `given: constraints`

A given constraint is a row family that another model builds and whose dual
this file reads.

```yaml
given:
  constraints:
    balance:
      dims: [snapshot, bus]
      description: the host model clears each bus
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
expressions:
  price:
    expression: dual(balance)
```

| Field         |                                                   |                |
| ------------- | ------------------------------------------------- | -------------- |
| `dims`        | required. The dimensions the row family runs over |                |
| `description` | free text                                         | default `null` |

There is no `expression` and no `sense`, because a file may name a given row
family only inside `dual(name)`. The reported expression takes its dimensions
from the `dims` of the given entry. A name declared under both
`constraints:` and `given: constraints:` is refused.

### `given: expressions`

A given expression is a named expression this file reads and another file
defines.

```yaml
given:
  expressions:
    injection:
      dims: [snapshot, bus]
      description: what the components put into a bus
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
constraints:
  balance:
    dims: [snapshot, bus]
    expression: injection == 0
```

| Field         |                                                   |                |
| ------------- | ------------------------------------------------- | -------------- |
| `dims`        | required. The dimensions the expression runs over |                |
| `description` | free text                                         | default `null` |

There is no body, but a [term](#terms) of this file may add to the name. This
file reads the name as it reads a given variable: a quantity over its `dims`,
of degree one. A `where` does not read it, because a mask is built before any
variable exists, so read a predicate that another file defines as a
[given mask](#given-masks) instead. A name declared under both `expressions:` and
`given: expressions:` is refused. The typeset legend lists a given expression
under _Given_.

[`merge`](../../howto/compose.md#a-library-of-components) folds a given
expression into the definition of another fragment. The `dims` are an upper
bound, so a body that carries a dimension they do not name is refused. A body
over fewer dimensions is folded, and then the merged spec refuses a row that
would repeat across the missing dimension, but accepts a row where another term
carries that dimension. The merged spec holds the body to the rules of every
place this file reads it, so a square of a given expression is refused once the
folded body is quadratic.

#### Terms

`adds_to:` adds this expression as a **term** to the sum it names, which is a
given expression of the same file. The `given:` entry reads the sum, and
`adds_to:` writes to it. The term is an ordinary named expression, so it takes
`cases:`, a description and every other field a named expression takes. The
file reads the name as the whole sum, both alone and after a merge, and the
term is the part of the sum that this file adds.

```yaml
# fleet.yaml adds a term
given:
  expressions:
    injection: { dims: [snapshot, bus] }
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
  generator: { dtype: str }
relations:
  gen_bus: { key: generator, values: bus }
variables:
  gen_p: { dims: [snapshot, generator], bounds: { lower: 0 } }
expressions:
  generation:
    description: what the fleet puts into a bus
    expression: sum(gen_p, over=generator, by=gen_bus[bus])
    adds_to: injection
```

```yaml
# balance.yaml reads the sum, and adds nothing to it
given:
  expressions:
    injection:
      dims: [snapshot, bus]
      description: what the components put into a bus
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
constraints:
  balance:
    dims: [snapshot, bus]
    expression: injection == 0
```

Each file loads alone, and the loader checks each term:

- `adds_to:` names a `given: expressions:` entry of the same file. A name the
  file does not read there is refused, and the message names the nearest one. A
  name the file defines is refused too: write the term into that body instead.
- A term does not read the sum it adds to, directly or through another name.
- A term carries no dimension the given entry does not state.
- A term is held to degree two, the same as every expression that reads the
  sum.

The typeset legend lists the entry under _Given_ and names the term, and the
math prints the term under _Definitions_ as its own line.

[`merge`](../../howto/compose.md#a-library-of-components) adds every term by
its name, in the order the files are given in. Each term stays a named
expression of the merged spec, without its `adds_to:`, and a cased term is
added like any other.

- One file may define the sum with one `expression:`, and the merged body is
  that body followed by the terms. A file that defines `injection` as `slack`
  gives `slack + generation` once it is merged with `fleet.yaml`. The body
  keeps its `dims:` and its description, and a second file that defines the
  sum collides with the first.
- A merged spec takes further terms: a merge defines every sum it has
  terms for, and a later merge adds to that body. So the first merge that holds
  the terms of a sum also holds a file that reads it.
- Where no file defines the sum, the terms are its body. The sum runs over
  the frame its readers state, every reader writes the dims in the same
  order, and the sum takes the first description a reader wrote.
- Where no file defines the sum, some file reads it for more than adding to it.
  That file reads the sum and adds nothing, or uses it in its math. Terms that
  only their own files read are refused, and the message names the nearest name,
  because a misspelt `given:` entry looks exactly like this. A sum that one file alone
  reads is refused too, because that file can misspell the entry, the `adds_to:`
  and its own use of the name alike.
- A definition written as `cases:` takes no term, so name the cased body as
  its own expression, and define the sum as that name.
- A name that a file declares as a variable, a parameter or a constraint takes
  no term.
- A term does not read its own sum through another file. The merge refuses
  it and names both files:

  ```text
  fragment '#2' adds 't' to 'injection', and 't' reads 'injection' back through 'x' of '#1', so the sum would define itself. Write 't' from something else, or define 'x' without 'injection'.
  ```

### `given: masks`

A given mask is a [mask](named.md#masks) this file reads and another file
defines.

```yaml
given:
  variables:
    p: { dims: [period, generator] }
  masks:
    stands:
      dims: [period, generator]
      description: the generator stands in this period
dimensions:
  period: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  ramp: { dims: [generator] }
constraints:
  ramp_up:
    dims: [period, generator]
    where: stands AND shift(stands, along=period, offset=1)
    expression: p - shift(p, along=period, offset=1) <= ramp
```

| Field         |                                                        |                |
| ------------- | ------------------------------------------------------ | -------------- |
| `dims`        | required. The dimensions the definer's predicate reads |                |
| `description` | free text                                              | default `null` |

There is no predicate, because the file that defines the mask owns it. A
`where` reads the name as data over its `dims`, true or false at each
coordinate. A `where` may read a given mask but not a given expression, because
a mask reads nothing that a solve decides. The name is refused in arithmetic,
the same as a mask. The typeset legend lists a given mask under _Given_.

[`merge`](../../howto/compose.md#a-library-of-components) folds a given mask
into the mask that another fragment defines. The `dims` name exactly the
dimensions that the predicate of the defining file reads, and a `given:` entry
that names a different set is refused, with both sets of dimensions in the
message.

## `constraints`

Each block under `constraints:` declares one constraint, named by its key.

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  load: { dims: [snapshot] }
variables:
  dispatch: { dims: [snapshot, generator] }
constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load
```

| Field         |                                                     |                |
| ------------- | --------------------------------------------------- | -------------- |
| `dims`        | required. The rows this rule builds                 |                |
| `expression`  | required. It uses exactly one of `<=`, `>=` or `==` |                |
| `where`       | which rows are built ([absence](absence.md))        | default `null` |
| `description` | free text                                           | default `null` |

The dimensions of the expression must **equal** its `dims`
([how dimensions combine](expressions.md#how-dimensions-combine)).

At least one side of the comparator carries a variable, so a comparison between
numbers and parameters alone is refused at load.

`dims: []` gives one scalar row. A scalar variable may not carry a `where`, so
put the condition on the constraints that use it.

Write a rule that differs by regime as two blocks, each under its own `where:`
([state a rule that differs by regime](../../howto/regimes.md)).

## `objective`

The objective is a single block with no name.

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  cost: { dims: [generator] }
variables:
  dispatch: { dims: [generator] }
objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

| Field         |                                          |                    |
| ------------- | ---------------------------------------- | ------------------ |
| `expression`  | required. Arithmetic, with no comparator |                    |
| `sense`       | `minimize` or `maximize`                 | default `minimize` |
| `description` | free text                                | default `null`     |

The expression must be **scalar**. The loader adds no sum for you:
`sum(x * a) + sum(y * b)` and `sum(x * a + y * b)` are both allowed, and they
state different objectives.

There is one objective block, so to pursue several goals, weight them into one
expression.

A spec composed from several files also has one objective, which one file sets,
and [`merge`](../../howto/compose.md) refuses a second one. Each other file
adds its part to a sum that the objective reads, with [`adds_to:`](#terms).
