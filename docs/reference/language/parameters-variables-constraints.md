<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Given, parameters, variables, objective and constraints

A spec declares its data under `parameters:` and its decisions under
`variables:`, and states its goal under `objective:` and its rules under
`constraints:`. It lists under `given:` what another file declares. This page
lists the keys of those five sections, in the order of the
[top-level keys](file.md#top-level-keys). Every entry in these sections
also takes `description:`, free text that the
[typeset](../typeset.md#descriptions) legend lists beside the entry.

## `given`

`given:` lists what this file uses and another file declares. It takes five keys: data under `parameters:`, named conditions under
`conditions:`, variables under `variables:`, named expressions under
`expressions:`, and families of rows under `constraints:`. A file with a
`given:` section loads and prints on its own, and
[`python -m mathspec check`](../cli.md#check) prints one line of
[advice](../glossary.md#advice) for each given entry.

[`merge`](../composition.md#merge) replaces each
[given entry](../composition.md#given-entries) with the entry that another file
of the composed spec ([a fragment](../glossary.md#fragment)) declares under the
same name.

mathspec refuses a name that a file declares both in a section and under the
same key of `given:`. For a parameter `cost`, the message is:

```text
Given parameter 'cost' collides with the parameter of the same name. Rename one of them.
```

For a variable, an expression or a condition, mathspec prints the same
message with the kind of entry changed. For a constraint `c`, mathspec prints a
different message, with one rewrite:

```text
Given constraint 'c' is also declared under 'constraints:'. Delete one of the two.
```

The typeset legend lists every given entry under _Given_.

### `given: parameters`

A given parameter is data that this file uses and another file declares.

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

`python -m mathspec check` loads the file and prints one line of advice for
each of the three given entries:

```text
parameter 'gen_cost' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this entry with the one another file declares.
parameter 'gen_on' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this entry with the one another file declares.
variable 'gen_p' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this entry with the one another file declares.
```

Each line states that the entry must come from another file, over the same
dimensions.

| Key     | What it sets                                           | Default |
| ------- | ------------------------------------------------------ | ------- |
| `dims`  | required. The dimensions the parameter is indexed over |         |
| `dtype` | `float`, `int`, `bool` or `str`                        | `float` |

A given parameter may appear wherever a parameter may: in an expression, a
`where:` and a bound.

### `given: conditions`

A given condition is a [named condition](named.md#conditions) that this file
uses and another file defines.

```yaml
given:
  variables:
    p: { dims: [period, generator] }
  conditions:
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

`ramp_up` has a row only where the generator stands in this period and in the
period before.

| Key    | What it sets                                                          | Default |
| ------ | --------------------------------------------------------------------- | ------- |
| `dims` | required. The dimensions that the condition of the defining file uses |         |

A given condition has no body, because the file that defines it sets the
body. A condition in this file uses the name as data over its `dims`, true or
false at each coordinate. As for a named condition,
mathspec refuses the name in arithmetic. `merge`
[refuses](../composition.md#given-entries) a given condition whose `dims`
differ from the dimensions of the defining condition.

### `given: variables`

A given variable is a variable that this file uses and another file
declares.

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

`gen_injects` states that the flow at the port of each generator equals the
output of that generator.

| Key      | What it sets                                          | Default      |
| -------- | ----------------------------------------------------- | ------------ |
| `dims`   | required. The dimensions the variable is indexed over |              |
| `domain` | `continuous`, `integer` or `binary`                   | `continuous` |

A given variable takes no `bounds` and no `where`, because the file that
declares the variable sets both. mathspec prints no domain line for it.

`merge` [keeps](../composition.md#given-entries) the entry of the file that
declares the variable. Where no file of the composed spec declares the
variable, the given entry stays in the compiled form of the spec (its
[program](../glossary.md#program)). With data attached,
[the model that the spec is layered onto](../reading.md#what-a-program-does-not-build)
provides the variable.

### `given: expressions`

A given expression is a named expression that this file uses and another
file defines.

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

`balance` states that what the components put into each bus adds up to zero.

| Key    | What it sets                                            | Default |
| ------ | ------------------------------------------------------- | ------- |
| `dims` | required. The dimensions the expression is indexed over |         |

A given expression has no body, but a named expression of this file may
[add a term](named.md#adds_to) to it. mathspec reads the name as it
reads a given variable: a quantity over its `dims`, of degree one.

mathspec refuses a comparison on a given expression in a condition, because a
condition is read before any variable exists. For `where: "injection > 0"` on
a variable `x`, the message is:

```text
Variable 'x': where references the given expression 'injection'. A given expression may hold a variable, and a condition is read before variables exist — it may test parameters and dimension coordinates only.
```

The bare name, `where: injection`, loads. `check` prints only the advice for
the given entry, and mathspec ends the typeset domain of `x` with the
condition "injection exists".

`merge` replaces a given expression with the definition of another fragment,
and [checks](../composition.md#given-entries) that body against the `dims` of
this file. `merge` accepts a body
over fewer dimensions. It refuses a row that would repeat the body across a
missing dimension where no other term is over that dimension. `merge` also holds the body to the rules of every place where this file uses it. So mathspec refuses a square of a given expression once the body is quadratic.

### `given: constraints`

A given constraint is a family of rows that another file declares, and whose
marginal value per row ([dual](named.md#dual)) this file uses.

```yaml
given:
  constraints:
    balance:
      dims: [snapshot, bus]
      description: another file clears each bus
dimensions:
  snapshot: { dtype: int }
  bus: { dtype: str }
expressions:
  price:
    expression: dual(balance)
```

`price` is the dual of each `balance` row: the marginal price at each bus and
snapshot.

| Key    | What it sets                                                | Default |
| ------ | ----------------------------------------------------------- | ------- |
| `dims` | required. The dimensions the family of rows is indexed over |         |

A given constraint takes no `expression`, because a file may use it only
inside [`dual(name)`](named.md#dual). `price`, a named expression computed
after the solver runs (a [reported expression](named.md#reported-expressions)),
takes its dimensions from the `dims` of the given entry.

## `parameters`

A **parameter** is a column of data that the spec uses, such as the load at
each snapshot or the cost of each generator. The entry declares the dimensions
of the column, and the numbers arrive with the data, which a tool matches to the
parameter by name.

```yaml
dimensions:
  snapshot: { dtype: int }
parameters:
  load:
    dims: [snapshot]
  discount_rate:
    dims: [] # a scalar
variables:
  p: { dims: [snapshot] }
constraints:
  meet:
    dims: [snapshot]
    expression: p * (1 + discount_rate) >= load
```

`load` has one value per snapshot, and `discount_rate` has one value only,
because `dims: []` declares a scalar.

| Key       | What it sets                                                     | Default   |
| --------- | ---------------------------------------------------------------- | --------- |
| `dims`    | required. The dimensions it is indexed over. `[]` means a scalar |           |
| `dtype`   | `float`, `int`, `bool` or `str`                                  | `float`   |
| `missing` | what a missing row of the data means ([`missing`](#missing))     | `refused` |

With data attached, a tool requires the column to match the `dtype`:

| `dtype` | The column                        | Note                                            |
| ------- | --------------------------------- | ----------------------------------------------- |
| `float` | a float column, or an integer one |                                                 |
| `int`   | an integer column                 |                                                 |
| `bool`  | a boolean column                  | a column of `1` and `0` is not a boolean column |
| `str`   | a string column                   |                                                 |

When the data is attached, a tool **refuses** a null value or a not-a-number
value (NaN), so a coordinate with no value has no row. `inf` and `-inf` are
values.

Only a `float` or an `int` parameter is a number. A `str` parameter is a label
and a `bool` parameter is a condition, and each one selects rows in a
[`where:`](expressions.md#conditions). mathspec refuses either one at load as a
coefficient, a term or a divisor. For a `bool` parameter `flag` in
`p * flag >= 0`, the message is:

```text
Constraint 'c': 'flag' is declared dtype: bool, and an expression reads only float and int. Name it in a condition ("flag", "NOT flag"), or declare it dtype: int to multiply by 0 and 1.
```

mathspec suggests both rewrites.

A `str` parameter takes any label. A dimension with
[`one_of`](dimensions.md#one_of) has a fixed list of labels.

### `missing`

`missing:` sets the meaning of a coordinate of the `dims` at which the data has
no row. It takes one of four values: `refused`, the default, `absent`,
`neutral`, or a value of the `dtype` of the parameter.

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
variables:
  p: { dims: [generator], where: active, bounds: { lower: 0, upper: p_nom_max } }
  start: { dims: [generator], domain: binary }
constraints:
  fix:
    dims: [generator]
    expression: p == p_set
  eff:
    dims: [generator]
    where: efficiency <= 1
    expression: p * efficiency >= 0
objective:
  expression: sum(p * cost) + sum(start * start_up_cost)
```

`cost` takes the default, `refused`. `start_up_cost` takes `neutral` and
`p_set` takes `absent`, and `efficiency`, `p_nom_max` and `active` each take a
value.

A condition treats a missing row in one of three ways:

- Whatever the `missing:`, a bare numeric name is true where the data has a
  row. A bare `float` name is true only where its value is also
  finite. So
  `where: p_nom_max` selects the rows that the data contains. mathspec refuses a bare `int` or `str` name under `refused` at load, because
  the condition would be true everywhere.
- A comparison uses the value. So `where: efficiency <= 1` is true at a
  missing row of `efficiency` above, which is `1` there. Under `absent` and
  `neutral`, a comparison at a missing row is false.
- A bare `bool` name is its value. So `where: active` is true at a missing row
  of `active` above.

A value has the `dtype` of the parameter:

| `dtype` | A value                                                  |
| ------- | -------------------------------------------------------- |
| `float` | a number. `.inf`, `inf`, `-.inf` and `-inf` are numbers  |
| `int`   | an integer. An integer column has no `inf`               |
| `bool`  | `true` or `false`                                        |
| `str`   | none. A label has no value to fill, and no `neutral` one |

mathspec refuses a NaN, a quoted number and `missing: null` at load, and in
each message mathspec suggests what to write. For `missing: null` it prints:

```text
parameters.v.missing: missing: null on a parameter names no reading. Write absent for a row that is not there, or leave the key out for refused.
```

mathspec suggests two rewrites, `absent` and `refused`.

A `given:` parameter has no `missing:`, because the file that declares the
parameter sets it.

A values parameter of a curve with `points:` must declare a
[`missing:` other than `refused`](piecewise.md#missing-breakpoints).

The typeset legend lists what a missing row means beside the parameter, such
as `` `neutral` where the data has no row ``. It lists nothing for `refused`.

## `variables`

A **variable** is a quantity that the solver decides, with one value per
coordinate of its `dims`.

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
variables:
  dispatch:
    dims: [generator]
    where: "capacity > 0"
    bounds:
      lower: 0
      upper: capacity
```

A [`where:`](absence.md#where) leaves `dispatch` only at the generators whose
capacity is above zero. The solver keeps each value between `0` and the
capacity of its generator.

| Key                             | What it sets                                                                                                      | Default      |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------ |
| `dims`                          | required. The dimensions it is indexed over                                                                       |              |
| `where`                         | which coordinates exist ([absence](absence.md))                                                                   | `null`       |
| `bounds.lower` / `bounds.upper` | a finite number, or the name of a `float` or `int` parameter. `null` leaves that side open                        | `null`       |
| `domain`                        | `continuous`, `integer` or `binary`. `binary` has fixed bounds of 0 and 1                                         | `continuous` |
| `missing`                       | `absent` or `neutral`: what a coordinate outside the `where:` means ([absence](absence.md#missing-on-a-variable)) | `absent`     |

A bound is never infinite, so an open side is `null`. mathspec refuses `.inf`
and `-.inf` at load, and gives `null` as the rewrite:

```text
variables.p.bounds.upper: bounds.upper is inf. For an open side, write upper: null or leave it out.
```

A bound is a name or a number, and not an expression. So `upper: capacity` is
accepted, and `lower: -rating` is refused:

```text
Variable 'p' bounds.lower: bounds take a parameter name or a number, not an expression (got '-rating'). Precompute it as a parameter.
```

mathspec suggests the rewrite: a parameter whose value is `-rating`.

Equal
bounds pin a variable to one value
([fix a quantity](../../howto/pin-a-variable.md)), and a pinned variable is
still a variable.

## `objective`

The **objective** is the one number that the solver minimises or maximises.
It is a single entry with no name.

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

The solver minimises the total cost of dispatch over every generator.

| Key          | What it sets                             | Default    |
| ------------ | ---------------------------------------- | ---------- |
| `expression` | required. Arithmetic, with no comparison |            |
| `sense`      | `minimize` or `maximize`                 | `minimize` |

The expression must be **scalar**, and mathspec adds no sum for you. Without
the `sum`, the expression above is over `generator`:

```text
The objective: the expression carries dims ['generator'], and an objective is one number. Wrap each additive term in its own sum(): `sum(p * cost) + sum(p_nom * capex)`.
```

mathspec suggests the rewrite, with one sum per term.

`sum(x * a) + sum(y * b)` and `sum(x * a + y * b)` are both accepted, and they
state different objectives where `x` or `y` is
[absent](absence.md#how-absence-travels).

A spec has one objective entry, and that entry has one expression, so several
goals are weighted into that expression. A spec composed from several files
also has one objective, which one file sets, and
[`merge`](../composition.md#merge) refuses a second one. With
[`adds_to:`](named.md#adds_to), each other file adds its part to a sum that the
objective uses.

A file with no `objective` states a **feasibility problem**. The solver then
looks for any decisions that meet every constraint, and minimises nothing.

## `constraints`

A **constraint** is a rule that the decisions obey, with one row per
coordinate of its `dims`. Each key under `constraints:` declares one
constraint, named by the key.

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

`power_balance` has one row per snapshot, and each row states that the
generators together meet the load.

| Key          | What it sets                                                  | Default |
| ------------ | ------------------------------------------------------------- | ------- |
| `dims`       | required. The dimensions of its rows                          |         |
| `expression` | required. A comparison with exactly one of `<=`, `>=` or `==` |         |
| `where`      | which rows exist ([absence](absence.md))                      | `null`  |

The dimensions of the expression
([how dimensions combine](expressions.md#how-dimensions-combine)) must
**equal** the `dims` of the constraint. With
`dispatch == load` as the expression above, `dispatch` is over `generator`,
which the `dims` do not list:

```text
Constraint 'power_balance': the expression carries dims ['generator'] that are not in its dims: ['snapshot']. Add them to dims:, or sum them out.
```

mathspec lists the extra dimension and the `dims`, and suggests two
rewrites.

At least one side of the comparison must have a variable, so at load mathspec refuses a comparison between numbers and parameters alone:

```text
Constraint 'enough': neither side of the comparison carries a variable, so the row decides nothing.
Got: 'load <= cap'
Name the variable it bounds, or state the fact under `assumptions:`.
```

mathspec repeats the refused comparison and suggests two rewrites.

`dims: []` declares one scalar row, for a rule such as a budget for the whole
system.

A [rule that differs by case](../../howto/cases.md) is two entries, each under
its own `where:`.

!!! info "See also"

    - [named expressions, conditions and macros](named.md) for `expressions:`,
      `conditions:` and `adds_to:`
    - [absence and `where`](absence.md) for the rows that a `where:` or a missing
      row removes
    - [composing specs](../composition.md) for what `merge` builds from given
      entries
    - [`missing` on a parameter](absence.md#missing-on-a-parameter) for the result
      of each value of `missing:`
