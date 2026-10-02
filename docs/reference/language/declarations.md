<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Parameters, variables, constraints and the objective

These four blocks carry the math, and `given:` names what the math reads from
another file. Each takes an optional `description:`, free text that the
[typeset](../typeset.md#descriptions) legend prints.

## `parameters`

A parameter declares a shape. The numbers arrive by name with the data.

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

**A null or NaN value is refused** when the data is attached. A coordinate
with no value has no row. `inf` and `-inf` are values.

Only `float` and `int` are values. A `str` parameter is a label and a `bool`
parameter is a mask: each selects rows in a
[`where`](expressions.md#where-strings), and writing either as a coefficient,
a term or a divisor is a load error. A `0` or `1` that is meant to be
multiplied by is declared `dtype: int`.

### A missing row

`missing:` says what a coordinate the `dims` reach with no row means. A table
that lost a row in preparation and a table that never had one look the same in
the data, so the file says which was meant.

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  cost: { dims: [generator] } # refused: every generator has a cost
  ramp_limit: { dims: [generator], missing: neutral } # no row means no limit
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

A consumer does not build the model from data with a refused row. How it says
so is its own: it may raise at the first gap, or list every missing coordinate.

A bare numeric name in a `where` asks whether the data has a row under every
reading, so `where: p_nom_max` selects the rows the data gives. A comparison
reads the value: `where: efficiency < 1` is true at a missing row of the
parameter above. Under `absent` and `neutral`, a comparison at a missing row is
false. A bare `bool` name reads its value, so `where: active` reads `true`
there.

A value has the parameter's dtype:

| `dtype` | a value                                                 |
| ------- | ------------------------------------------------------- |
| `float` | a number. `.inf`, `inf`, `-.inf` and `-inf` are numbers |
| `int`   | an integer. An integer column cannot hold `inf`         |
| `bool`  | `true` or `false`                                       |
| `str`   | none. A label has no value to fill                      |

A NaN, a quoted number and `missing: null` are refused. A `given:` parameter
has no `missing:`. The file that declares the parameter owns it. A parameter a
[`piecewise:`](piecewise.md) block reads takes no `missing:` either: the block
owns the shape of its curve. Such a parameter is `neutral` where only curves
with `points:` read it, and `refused` otherwise, in the curve and outside it. The typeset legend prints a value beside the
parameter.

## `variables`

A variable is what the solver decides. There is one column per coordinate of
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

An open side is `null`. A bound is never infinite: `.inf` and `-.inf` are
refused, with `null` named as the rewrite.

A bound is a name or a number: `upper: capacity` is accepted,
and `upper: -rating` is refused. Ship the negated column as data.

Equal bounds pin a variable ([fix a quantity](../../howto/pin-a-variable.md)).
A pinned variable is still a variable.

## `given`

`given:` holds what this file reads and does not build: data under
`parameters:`, columns under `variables:`, named expressions under
`expressions:`, and row families under `constraints:`. It takes those four keys
and no other. A file with a `given:` block loads and prints on its own.

### `given: parameters`

A given parameter is data this file reads and another file declares.

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
given:
  parameters:
    gen_cost: { dims: [generator], description: what one unit of output costs }
    gen_on: { dims: [generator], dtype: bool }
  variables:
    gen_p: { dims: [snapshot, generator] }
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
dimensions:
  snapshot: { dtype: int }
  port: { dtype: str }
  generator: { dtype: str }
relations:
  gen_port: { key: generator, values: port }
variables:
  gen_p: { dims: [snapshot, generator], bounds: { lower: 0 } }
given:
  variables:
    flow:
      dims: [snapshot, port]
      description: what a port puts into its bus
constraints:
  gen_injects:
    dims: [snapshot, generator]
    expression: at(flow, by=gen_port, over=port, into=generator) == gen_p
```

| Field         |                                                   |                      |
| ------------- | ------------------------------------------------- | -------------------- |
| `dims`        | required. The dimensions the column is indexed by |                      |
| `domain`      | `continuous`, `integer` or `binary`               | default `continuous` |
| `description` | free text                                         | default `null`       |

There is no `bounds` and no `where`. The file that introduces the column owns
both.

An expression reads a given variable as it reads any other. A name declared
under both `variables:` and `given: variables:` is refused. The typeset legend
lists a given variable under _Given_, and prints no domain line for it.

[`merge`](../../howto/compose.md#a-library-of-components) folds a given
declaration into the declaration of another fragment that introduces the name,
so a composed library carries none of them. The folded declaration is the
introducer's, and what the reader states has to say the same or less.

Where nothing in this language introduces the column, the program carries the
declaration until a host model provides it
([what a program does not build](../reading.md#what-a-program-does-not-build)).

### `given: constraints`

A given constraint is a row family that another model builds. This file reads
its dual.

```yaml
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
given:
  constraints:
    balance:
      dims: [snapshot, bus]
      description: the host model clears each bus
expressions:
  price:
    expression: dual(balance)
```

| Field         |                                                   |                |
| ------------- | ------------------------------------------------- | -------------- |
| `dims`        | required. The dimensions the row family runs over |                |
| `description` | free text                                         | default `null` |

There is no `expression` and no `sense`.
`dual(name)` is the only place a given row family may be named, and the frame
gives the reported expression its dimensions. A name declared under both
`constraints:` and `given: constraints:` is refused.

### `given: expressions`

A given expression is a named expression this file reads and another file
defines.

```yaml
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
given:
  expressions:
    injection:
      dims: [snapshot, bus]
      description: what the components put into a bus
constraints:
  balance:
    dims: [snapshot, bus]
    expression: injection == 0
```

| Field         |                                                   |                |
| ------------- | ------------------------------------------------- | -------------- |
| `dims`        | required. The dimensions the expression runs over |                |
| `description` | free text                                         | default `null` |

There is no body. A [term](#terms) of this file may add to the name. This
file reads the name as it reads a given variable: a quantity over the frame, of
degree one. A `where` does not read it, because a mask is built before any
variable exists. A name declared under both `expressions:` and
`given: expressions:` is refused. The typeset legend lists a given expression
under _Given_.

[`merge`](../../howto/compose.md#a-library-of-components) folds a given
expression into the definition of another fragment. The `dims` are an upper
bound: a body that carries a dimension they do not name is refused. A body over
fewer dimensions is folded, and the composed spec decides: it refuses a row
that would repeat across the missing dimension, and accepts one where another
term carries it. The composed spec holds the body to the rules of every place
this file reads it: a square of a given expression that is quadratic is
refused once folded.

#### Terms

`adds_to:` adds this expression as a **term** to the sum it names. The sum is
a given expression of the same file: the given entry is the read, and
`adds_to:` is the write. The term is an ordinary named expression, so it takes
`cases:`, a description and every other field a named expression takes. The
file reads the name as the whole sum, alone and composed, and the term is its
part of it.

```yaml
# fleet.yaml adds a term
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
  generator: { dtype: str }
relations:
  gen_bus: { key: generator, values: bus }
variables:
  gen_p: { dims: [snapshot, generator], bounds: { lower: 0 } }
given:
  expressions:
    injection: { dims: [snapshot, bus] }
expressions:
  generation:
    description: what the fleet puts into a bus
    expression: sum(gen_p, by=gen_bus, over=generator, into=bus)
    adds_to: injection
```

```yaml
# balance.yaml reads the sum, and adds nothing to it
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
given:
  expressions:
    injection:
      dims: [snapshot, bus]
      description: what the components put into a bus
constraints:
  balance:
    dims: [snapshot, bus]
    expression: injection == 0
```

Each file loads alone, and the loader checks each term:

- **`adds_to:` names a `given: expressions:` entry of the same file.** A name
  the file does not read there is refused, with the near miss. A name the file
  defines is refused too: write the term into that body instead.
- **A term does not read the sum it adds to**, directly or through another
  name.
- **A term carries no dimension the given entry does not state.**
- **A term is held to degree two**, as what reads the sum is.

The typeset legend lists the entry under _Given_ and names the term. The math
prints the term under _Definitions_ as its own line.

[`merge`](../../howto/compose.md#a-library-of-components) adds every term by
its name, in the order the files are given in. Each term stays a named
expression of the merged spec, without its `adds_to:`. A cased term is added
like any other.

- **One file may define the sum with one `expression:`.** The merged body is
  that body followed by the terms. A file that defines `injection` as `slack`
  gives `slack + generation` once it is merged with `fleet.yaml`. The body
  keeps its `dims:` and its description. A second file that defines the sum
  collides with the first.
- **A merged spec takes further terms.** A merge defines every sum it has
  terms for, and a later merge adds to that body. So the first merge that holds
  the terms of a sum also holds a file that reads it.
- **Where no file defines the sum, the terms are its body.** The sum runs over
  the frame its readers state, and every reader writes the dims in the same
  order. The sum takes the first description a reader wrote.
- **Where no file defines the sum, some file reads it for more than adding to
  it.** That file reads the sum and adds nothing, or uses it in its math.
  Terms that only their own files read are refused, with the near miss, since
  that is what a misspelt `given:` entry looks like. A sum that one file alone
  reads is refused too, because that file can misspell the entry, the
  `adds_to:` and its own use of the name alike.
- **A definition written as `cases:` takes no term.** Name the cased body as
  its own expression, and define the sum as that name.
- **A name that a file declares as a variable, a parameter or a constraint
  takes no term.**
- **A term does not read its own sum through another file.** The merge refuses
  it and names both files:

  ```text
  fragment '#2' adds 't' to 'injection', and 't' reads 'injection' back through 'x' of '#1', so the sum would define itself. A term may not read what reads its sum: write 't' from something else, or define 'x' without 'injection'.
  ```

## `constraints`

One block is one rule. The name of the block is the name of the constraint.

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

At least one side of the comparator carries a variable. A comparison between
numbers and parameters alone is refused at load.

`dims: []` gives one scalar row. A scalar variable may not carry a `where`; put the condition on the constraints
that use it.

Two regimes of one rule are two blocks, each under its own `where:`
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

The expression must be **scalar**. Nothing is summed for you:
`sum(x * a) + sum(y * b)` and `sum(x * a + y * b)` are both allowed, and they
state different objectives.

There is one objective block. To pursue several goals, weight them into one
expression.

A spec composed from several files also has one objective, and one file sets
it. [`merge`](../../howto/compose.md) refuses a second one. Each other file adds its part
to a sum that the objective reads, with [`adds_to:`](#terms).
