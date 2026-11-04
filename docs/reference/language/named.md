<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Named expressions, conditions and macros

This page describes the three sections that declare a named part of a spec,
`conditions:`, `expressions:` and `macros:`, and what mathspec refuses in each.

## `conditions`

A named condition is a [condition](expressions.md#conditions) with a name, and
a [`where:`](absence.md#where), a [`when:`](#cases) or a
[`holds:`](assumptions.md#assumptions) uses it by that name. Under a `where:` the condition narrows the entry, and under a `holds:` it is only checked against the data:

```yaml
dimensions:
  period: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  build_year: { dims: [generator] }
  lifetime: { dims: [generator] }
  period_year: { dims: [period] }
  p_nom: { dims: [generator] }
conditions:
  stands:
    condition: build_year <= period_year AND period_year < build_year + lifetime
    description: the generator stands in this period
variables:
  p:
    dims: [period, generator]
    where: stands
    bounds: { lower: 0, upper: p_nom }
constraints:
  ramp_up:
    dims: [period, generator]
    where: stands AND shift(stands, along=period, offset=1)
    expression: p - shift(p, along=period, offset=1) <= 0.5 * p_nom
objective: { sense: maximize, expression: sum(p) }
```

The [typesetter](../typeset.md) prints the condition once, under _Conditions_, with ⟺ where a
named expression has =. Where a `where:` uses the condition, its symbol, like the
symbol of data, is upright:

```math
\mathrm{stands}_{g,e} \iff \mathrm{build\_year}_{g} \le \mathrm{period\_year}_{e} \wedge \mathrm{period\_year}_{e} < \mathrm{build\_year}_{g} + \mathrm{lifetime}_{g} \qquad \forall\, g \in \mathcal{G},\ e \in \mathcal{E}
```

```math
p_{e,g} - p_{e - 1,g} \le 0.5 \cdot \mathrm{p}^{\mathrm{nom}}_{g} \qquad \forall\, e \in \mathcal{E},\ g \in \mathcal{G} \,:\, \mathrm{stands}_{g,e} \wedge \mathrm{stands}_{g,e - 1}
```

<figure class="diagram">
--8<-- "docs/static/named-conditions.svg"
</figure>

With data in which generator `b` exists only from 2040, `p` has no row at 2030
and `b`. The constraint `ramp_up` has a row only where the generator stands in
this period and in the period before it.

| Key           | Required | Default | What it sets                                                         |
| ------------- | -------- | ------- | -------------------------------------------------------------------- |
| `condition`   | yes      |         | the condition, in the [condition grammar](expressions.md#conditions) |
| `description` | no       | `null`  | free text                                                            |

An entry with no `description:` may be the bare condition, as in
`stands: p_nom > 0`.

The bare name of a named condition selects the same rows as its condition
written out. The same rows are selected in a `where:`, a `when:` and a
`holds:`, under `NOT`, and inside [`count`](expressions.md#count),
[`shift`](expressions.md#shift-in-a-condition) and
[`at`](expressions.md#at-in-a-condition).

A named condition declares no `dims:`. It is indexed over the dimensions that its condition uses, sorted by name, so the typesetter prints `stands` with the indices `g,e` above. Where an entry over more dimensions uses the condition, mathspec repeats it
along the others. `shift` moves it only along a dimension over which the
condition is indexed.

A named condition may use another named condition, and a named expression
that uses only data. mathspec refuses a cycle, and lists its chain in the
message:

```text
Condition 'again': circular condition reference: again -> again. Remove one reference.
```

The chain `again -> again` is a condition that uses its own name.

A named condition is never a number, so mathspec refuses it in arithmetic and
in a comparison. With `e: sum(p * stands, over=generator)` under
`expressions:`, mathspec prints:

```text
Named expression 'e': 'stands' is a named condition, which is true or false where it is read, and not a number. Write it bare — stands, or NOT stands — rather than comparing it or computing with it.
```

mathspec suggests the two forms in which it accepts a named condition.

mathspec refuses a condition that is always true or always false (that folds
to `True` or `False`), because it admits every row or none. For the condition `always: p_nom > 0 OR True`,
mathspec prints:

```text
Condition 'always': the condition 'p_nom > 0 OR True' folds to true, so it admits every row and names nothing a `where:` needs. Delete it, or write the condition over the data.
```

`p_nom > 0 OR True` is true whatever the data is, so `always` admits every
row.

The `where:` of a variable may not test, through a named condition, whether
that variable exists. With `built: p` under `conditions:` and
`where: built` on the variable `p`, mathspec prints:

```text
Variable 'p': variable 'p' asks whether it exists in its own `where:`, through a named condition, which nothing can answer — its `where:` is what decides where it exists. Test a parameter, or another variable declared before it.
```

mathspec suggests two things that `p` may test instead: a parameter, or a
variable declared before `p`.

!!! info "See also"

    - [`given: conditions`](parameters-variables-constraints.md#given-conditions)
      for a named condition that another file declares.

## `expressions`

A named expression is a quantity with a name, such as the total generation of
a fleet. A constraint or the objective may use it by that name. The entry is a bare string, or a mapping with the keys
in the table below:

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  rate: { dims: [generator] }
  cap: { dims: [] }
variables:
  p: { dims: [generator], bounds: { lower: 0 } }
expressions:
  total_generation: sum(p, over=generator)
  emissions:
    expression: sum(p * rate, over=generator)
    description: CO2 released, the quantity a cap would bound
constraints:
  emission_cap: { dims: [], expression: emissions <= cap }
objective: { sense: maximize, expression: total_generation }
```

The [typesetter](../typeset.md) prints each named expression once, under
_Definitions_, and prints its symbol where the math uses it:

```math
\mathit{total\_generation} = \sum_{g \in \mathcal{G}} p_{g}
```

```math
\mathit{emissions} = \sum_{g \in \mathcal{G}} p_{g} \cdot \mathrm{rate}_{g}
```

```math
\mathit{emissions} \le \mathrm{cap}
```

The constraint `emission_cap` uses `emissions` by name, and the objective uses
`total_generation`, so the body of each entry is written once.

| Key           | Required         | Default | What it sets                                                                                             |
| ------------- | ---------------- | ------- | -------------------------------------------------------------------------------------------------------- |
| `expression`  | without `cases:` |         | the quantity, in the [expression grammar](expressions.md), which `cases:` replaces                       |
| `dims`        | with `cases:`    | `null`  | the dimensions over which the quantity is indexed, in the order of its indices ([`dims`](#dims))         |
| `description` | no               | `null`  | free text                                                                                                |
| `cases`       | no               | `null`  | a map of named cases, each with a `when:` condition and an `expression:` ([`cases`](#cases))             |
| `otherwise`   | with `cases:`    | `null`  | the value at every combination of labels (a [coordinate](../glossary.md#coordinate)) that no case claims |
| `adds_to`     | no               | `null`  | the name of a sum that this entry adds a term to ([`adds_to`](#adds_to))                                 |

### `dims`

Without `dims:`, mathspec takes the dimensions of the entry from the
expression, sorted by name. With `dims:`, you set the order of the indices,
and mathspec holds the expression to the list in both directions:

```yaml
dimensions:
  generator: { dtype: str }
  snapshot: { dtype: int, ordered: true }
parameters:
  p_max: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator], bounds: { lower: 0, upper: p_max } }
expressions:
  headroom:
    dims: [generator, snapshot]
    expression: p_max - p
    description: the capacity a generator leaves unused in a snapshot
objective: { sense: minimize, expression: sum(headroom) }
```

`headroom` is indexed over `[generator, snapshot]`, in that order.

At load, mathspec refuses the file with `dims: [generator]` in place of
`dims: [generator, snapshot]`:

```text
Named expression 'headroom': the body carries dims ['snapshot'] outside the dims: ['generator']. Add them to dims:, or take them out of the body.
```

The body `p_max - p` uses `p`, which is indexed over `snapshot`, so `snapshot`
has to be in `dims:`. mathspec also refuses a `dims:` that lists a dimension
the expression is not indexed over.

An expression that uses the entry repeats
the value of the entry along each dimension that the entry is not indexed over.

### `cases`

A cased expression has a different value in each case, so that the rule which
uses it is written once. In the spec below, `previous_status` is whether a
unit is on (its commitment state) at the start of a snapshot. For a unit that is never switched off, the state is `1`. At the
first snapshot it is an initial value, and everywhere else it is the status of
the previous snapshot:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  committable: { dims: [generator], dtype: bool }
  status_initial: { dims: [generator] }
  ramp_limit: { dims: [generator] }
  start_up_limit: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator], bounds: { lower: 0 } }
  status: { dims: [snapshot, generator], domain: binary }
expressions:
  previous_status:
    description: the commitment state a unit carries into a snapshot
    dims: [snapshot, generator]
    cases:
      always_on:
        when: "not committable"
        expression: 1
      boundary:
        when: "committable and position(snapshot) == 0"
        expression: status_initial
    otherwise: shift(status, along=snapshot, offset=1)
constraints:
  ramp_up:
    dims: [snapshot, generator]
    expression: >-
      p - shift(p, along=snapshot, offset=1, edge=0)
      <= ramp_limit * previous_status + start_up_limit * (1 - previous_status)
objective: { sense: minimize, expression: sum(p) }
```

The typesetter prints each case as one row of the definition, and
`otherwise:` as the last row:

```math
\mathit{previous\_status}_{t,g} = \begin{cases} 1 & \text{if } \neg \mathrm{committable}_{g} \\ \mathrm{status}^{\mathrm{initial}}_{g} & \text{if } \mathrm{committable}_{g} \wedge \mathrm{pos}(t) = 0 \\ \mathit{status}_{t - 1,g} & \text{otherwise} \end{cases} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

<figure class="diagram">
--8<-- "docs/static/named-cases.svg"
</figure>

The constraint `ramp_up` refers to `previous_status` by name, and at each
snapshot each unit takes the value of its case.

With data attached, a coordinate that a case claims can still have no value.
In the example above, `otherwise:` uses `shift(status, …)`, which has no value
at the first snapshot. There the cases `always_on` and `boundary` claim every
unit, so no row is lost.

#### Refused cases

The cases have no order, so mathspec checks at load that no coordinate falls
under two of them.

The first four messages below are the first line of the output. After each,
mathspec prints this line once for each place where `ramp_up` uses
`previous_status`:

```text
Constraint 'ramp_up': named expression 'previous_status' does not load. Fix the error listed for 'previous_status' first.
```

`ramp_up` uses `previous_status` twice, so mathspec prints this line twice.

No two cases may claim one coordinate. Here the case `boundary` has
`when: "position(snapshot) == 0"`, a test on
[`position`](expressions.md#position) without `committable and`, so it overlaps
`always_on` at the first snapshot:

```text
Named expression 'previous_status': cases 'always_on' and 'boundary' both claim the value where committable is false, the position of snapshot is 0. Narrow one of the two `when:` strings by the negation of the other, or drop the wider one and let `otherwise:` cover that region.
```

mathspec lists the coordinates that the two cases share: where
`committable` is false and the position of `snapshot` is 0.

A `when:` must be a condition on the data. mathspec refuses `True`, `False`,
and a condition that folds to one of them. With
`when: "committable OR True"` on the case `always_on`, mathspec prints:

```text
Named expression 'previous_status', case 'always_on': the mask admits every row, so no other arm can hold anywhere and `otherwise:` covers nothing. Write the expression without `cases:`, or narrow the `when`.
```

`always_on` then claims every row, so `boundary` and `otherwise:` claim
none.

mathspec refuses a pair of cases that it cannot tell apart without data. The
conditions `position(snapshot) == -1` on `always_on` and
`position(snapshot) == 0` on `boundary` pick the same row of a dimension
with one member:

```text
Named expression 'previous_status': cases 'always_on' and 'boundary' cannot be told apart before the data arrives: snapshot is split at positions counted from both ends (-1, 0), which name the same row when it has one member. Count from one end only.
```

With one snapshot, the position `0` and the position `-1` are the same
snapshot, so both cases would claim it.

Where `cases:` has two or more cases, a `when:` may not compare expressions. Whether two such cases overlap is known only when the data is attached. With `when: "ramp_limit > 2 * start_up_limit"` on
`always_on`, mathspec prints:

```text
Named expression 'previous_status': cases 'always_on' and 'boundary' cannot be told apart before the data arrives: it compares expressions, whose values only the data decides. Compare one parameter against a literal, or precompute the test as a boolean parameter and test that.
```

mathspec suggests two conditions that it accepts instead: a parameter
compared with a literal, or a boolean parameter. A `cases:` with one case
may compare expressions, because its `otherwise:` claims only what the
case leaves.

Each `when:` and each value is indexed only over dimensions that `dims:`
lists. A value indexed over fewer of them is repeated along the others, as a
parameter with fewer dimensions is. Each dimension in `dims:` must index
some value or some `when:`. With an extra dimension `extra` in `dims:`,
mathspec prints this message alone:

```text
Named expression 'previous_status': dims: gives ['extra'], but no case value and no `when:` is indexed over ['extra']. A named expression stands for its expression, so dims: gives only the dimensions it is indexed over. Take ['extra'] out of dims:; an expression that reads 'previous_status' still repeats it along its own other dims.
```

No case of `previous_status` is indexed over `extra`, so mathspec refuses
`extra` in `dims:`.

!!! info "See also"

    - [State a rule that differs by case](../../howto/cases.md) for the task, and
      for a claimed coordinate that is left with no value.
    - [Conditions](expressions.md#conditions) for the grammar of a `when:` string.
    - [Absence and where](absence.md) for what an entry uses where a value is
      absent.

### `adds_to`

`adds_to:` adds a named expression as a **term** to a sum that the file lists
under [`given: expressions:`](parameters-variables-constraints.md#given-expressions).
A term is an ordinary named expression, so it takes `cases:`, `description:`
and every other key of a named expression. Both alone and after
[`merge`](../composition.md#merge) composes the files, mathspec reads the name
of the sum as the whole sum. The term is the part that this
file adds.

```yaml title="fleet.yaml"
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

```yaml title="balance.yaml"
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

`fleet.yaml` adds `generation` to `injection`, and `balance.yaml` uses the sum
and adds nothing to it. Each file loads alone, and mathspec checks each term
at load:

- `adds_to:` must list a `given: expressions:` entry of the same file.
  mathspec refuses a name that the file does not list there, and suggests the
  nearest name, such as `Did you mean 'injection'?`.
- A term does not use the sum that it adds to, directly or through another
  name.
- A term is indexed only over dimensions that the given entry lists.
- Like every expression that uses the sum, a term contains a product of at
  most [two variables](expressions.md#where-a-product-of-two-variables-is-allowed).

mathspec also refuses a name that the file defines, because the term belongs
in the body:

```text
Named expression 'gen': it adds to 'injection', which this file defines. Write the term into the body of 'injection', or read 'injection' under 'given: expressions:' and add its body as a term.
```

mathspec suggests both rewrites: the term written into the body, or the sum
declared under `given: expressions:`.

The typeset legend lists the given entry, together with the term, under
_Given_. The term is printed under _Definitions_ as its own line.

[`merge`](../composition.md#merge) adds every term to its sum by name, and
[terms and sums](../composition.md#terms-and-sums) describes the merged body.
Each term stays a named expression of the merged spec, without its `adds_to:`.

Where no file defines the sum, the terms are its body. `merge` holds a sum to
these rules:

- Every file that lists the sum under `given:` lists its `dims` in the same
  order.
- Where no file defines the sum, the sum is indexed over each listed
  dimension that a term is indexed over. It takes the first description that
  such a file states.
- An entry may not use the sum over a dimension that no term is indexed over.
- Where no file defines the sum, at least two files list it. One of them adds
  no term, or uses the sum in its math. Otherwise `merge` refuses the terms,
  and suggests the nearest name.
- A defined sum written with `cases:` takes no term.
- A name that a file declares as a variable, a parameter or a constraint takes
  no term.

A term does not use its own sum through another file. `merge` refuses such a
term, and names both files:

```text
fragment '#2' adds 't' to 'injection', and 't' reads 'injection' back through 'x' of '#1', so the sum would define itself. Write 't' from something else, or define 'x' without 'injection'.
```

Here `t` in the second file adds to `injection` and uses `x` of the first
file, and `x` uses `injection`.

### Reported expressions

A named expression is either **in the math** or **reported**. An entry is in
the math when the objective, a constraint or a `piecewise:` link uses it,
directly or through another entry or a macro. A bound and a `where:` do not
count as a use. Every other entry is reported, and a tool may report its
value after the solver runs. Here the objective uses `system_cost`, and nothing uses `delivered` or
`lcoe`:

```yaml
dimensions:
  generator: { dtype: str }
  snapshot: { dtype: int }
parameters:
  marginal_cost: { dims: [generator] }
  load: { dims: [snapshot] }
variables:
  p: { dims: [snapshot, generator], bounds: { lower: 0 } }
expressions:
  system_cost: sum(sum(p * marginal_cost, over=generator), over=snapshot)
  delivered: sum(sum(p, over=generator), over=snapshot)
  lcoe: system_cost / delivered
constraints:
  balance: { dims: [snapshot], expression: "sum(p, over=generator) == load" }
objective: { sense: minimize, expression: system_cost }
```

```math
\mathit{lcoe} = \frac{\mathit{system\_cost}}{\mathit{delivered}}
```

`system_cost` is in the math, and `delivered` and `lcoe` are reported.

Where the math uses an entry, mathspec substitutes the body there, and the
[degree limit](expressions.md#where-a-product-of-two-variables-is-allowed)
applies where the body is used. A reported entry may not contain a comparison.
It has **no** degree limit, so it may divide by a variable, raise one to a
power, and multiply two sums.

When a constraint uses a reported entry, the entry is in the math, and
mathspec refuses the file under the name of the constraint. With
`cheap: { dims: [], expression: lcoe <= 50 }` added under `constraints:`,
mathspec prints:

```text
Constraint 'cheap': the divisor contains variables, which is not affine. Divide by a parameter, or precompute the reciprocal as one.
```

`lcoe` divides by `delivered`, which contains the variable `p`.

#### `dual`

`dual(c)` is the marginal value of each row of the constraint `c` (its
shadow price). It is indexed over the `dims` of `c`, and only a reported entry may call `dual`:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  load: { dims: [snapshot] }
  cost: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator], bounds: { lower: 0 } }
expressions:
  price: dual(balance)
constraints:
  balance: { dims: [snapshot], expression: "sum(p, over=generator) == load" }
objective: { sense: minimize, expression: sum(p * cost) }
```

`price` is indexed over `snapshot`, as `balance` is. mathspec refuses `dual`
in a constraint, the objective, a `piecewise:` link, and any entry that one of
those uses. With a constraint `d` that uses `2 * dual(balance)`, mathspec
prints:

```text
Constraint 'd': a dual exists only after a solve, so it cannot stand here. Keep the entry that reads it out of constraints, the objective, bounds and where.
```

Through the rules for bounds and for conditions, mathspec also refuses `dual`
in a bound and in a `where:`.

With `c` written as `lhs <= rhs + d`, the dual is the rate of change
of the optimal objective in `d` at `d = 0`. The rule is the same for `<=`,
`>=` and `==`, and under `minimize` and `maximize`, so an equality also has a
dual with a sign. The side on which a term is written sets the sign, because
`p <= cap` and `-p >= -cap` state one row with opposite duals. A row met with equality (a tight row) has
a dual of the sign below.

| Under `minimize`, a tight row    | Its dual                                       |
| -------------------------------- | ---------------------------------------------- |
| `p <= cap`                       | at most 0                                      |
| `p >= load`                      | at least 0                                     |
| `sum(p, over=generator) == load` | any sign: the price of one more unit of `load` |

A row that the `where:` of `c` leaves absent has no dual.

!!! info "See also"

    - [reported values](absence.md#reported-values), for where a reported
      entry is absent.

## `macros`

A macro is a template that takes arguments. mathspec substitutes each call
into its expression before any software that reads the spec
([a tool](../glossary.md#tool)) sees the expression. So the tool that builds the model
(an engine) never sees the macro:

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  cost: { dims: [generator] }
  p_nom: { dims: [generator] }
variables:
  p: { dims: [generator], bounds: { lower: 0, upper: p_nom } }
macros:
  weighted_sum:
    args: [array, weights]
    kwargs: [over]
    template: sum(array * weights, over=over)
objective:
  sense: minimize
  expression: weighted_sum(p, cost, over=generator)
```

```math
\min \sum_{g \in \mathcal{G}} p_{g} \cdot \mathrm{cost}_{g}
```

The objective is printed with the template written in, so the name of the
macro does not appear in the math.

A template takes its arguments by the names under `args` and `kwargs` (its
formals):

| Key           | Required | Default | What it sets                           |
| ------------- | -------- | ------- | -------------------------------------- |
| `template`    | yes      |         | the expression, with the formals in it |
| `args`        | no       | `[]`    | the positional formals, in call order  |
| `kwargs`      | no       | `[]`    | the keyword formals                    |
| `description` | no       | `null`  | free text                              |

A template contains arithmetic, and no comparison and no `cases:` entry. An
argument may itself use macros and named expressions.

Inside a template, a formal hides a name that the spec declares. A formal
may not have the name of a declared dimension:

```text
Macro 'weighted_sum': formal 'generator' collides with declared dimension 'generator'. Rename the formal.
```

The formal `generator` would hide the dimension `generator` inside the
template.

At each call site, mathspec checks the number of arguments. The call
`weighted_sum(p, over=generator)` passes one positional argument, and
mathspec prints:

```text
The objective: macro 'weighted_sum' expects 2 positional argument(s), and the call passes 1. Call it as weighted_sum(array, weights, over=...).
```

mathspec writes out the call with every formal that `weighted_sum` takes.

mathspec refuses a cycle of macros, and for two macros `a` and `b` that call each other it prints one line for each:

```text
Macro 'a': macro 'b' calls itself through b -> a -> b. Remove one of the calls in that chain.
Macro 'b': macro 'a' calls itself through a -> b -> a. Remove one of the calls in that chain.
```

In each line, mathspec lists the chain of calls that starts at the other
macro.

[`to_spec`](../api.md#mathspec.to_spec) checks every template against every rule that applies at a call
site, whether or not anything calls the macro. A formal is left for the
call site to fill. A macro `wrong` with the template
`sum(x, over=snapshot)`, in a file that declares no `snapshot`, is refused
although nothing calls it:

```text
Macro 'wrong': sum(over=snapshot) does not name a declared dimension or a formal argument of this macro. Dimensions: generator.
Declare 'snapshot' under 'dimensions:', or correct the spelling.
```

`snapshot` is neither a dimension of the file nor a formal of `wrong`.

A list may contain a formal, as in `sum(x, over=[d, snapshot])`. There the
call fills it with a name, or with a list of names that is spliced in.

!!! info "See also"

    - [Operators](operators.md) for the operators that a template can combine.
    - [The limits of the language](../../about/limits.md) for what the language
      does not express, and how a new construct enters mathspec.
