<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Operators

This page describes the four operators of the expression grammar, `sum`, `at`,
`shift` and `sum_back`, and what mathspec refuses in each call.

An operator is a construct built into the language, such as `sum`
([operator](../glossary.md#operator)). The four operators below act on
arithmetic expressions, and `count`, `position` and the comparisons act in a
[condition](expressions.md#conditions).

A [reported expression](named.md#reported-expressions) may also call
[`dual`](named.md#dual), which reads the dual of a constraint after the solver
runs.

A file cannot add an operator, and only
[a change to mathspec](../../about/limits.md) adds one. A
[macro](named.md#macros) can combine the operators that exist.

| Operator                                                   | Result                                                                                                                                                        |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sum(array)`                                               | `sum` removes every [dimension](dimensions.md) of `array`. The result is a scalar                                                                              |
| `sum(array, over=dim)`                                     | `sum` removes `dim`                                                                                                                                           |
| `sum(array, over=[a, …])`                                  | `sum` removes each dimension in the list                                                                                                                      |
| `sum(array, over=dim, by=relation[c])`                     | `sum` removes `dim`, and groups the result by the column `c` of the [relation](relations.md). The call joins on the other key columns, so `array` and the result are indexed over them |
| `sum(array, over=[dim, …], by=relation[c, …])`             | The call does the same with several dimensions and several columns of one relation, joins on them together, and groups by their product                            |
| `at(array, by=relation[c])`                                | The result is `array` read at the value of the relation's column `c`, once per key of the relation. The result gains the key                                                |
| `shift(array, along=dim, offset=n)`                        | The result is the value `n` positions earlier along `dim`, and the vacated edge is [absent](absence.md)                                                                         |
| `shift(array, along=dim, offset=n, edge='wrap')`           | The result is the value `n` positions earlier, counted cyclically, so nothing is vacated                                                                                    |
| `shift(array, along=dim, offset=n, edge=v)`                | The result is the value `n` positions earlier, with the number `v` at the vacated edge                                                                                      |
| `shift(array, along=dim, offset=p, edge=…)`                | The result is the value `p` positions earlier, with `p` an integer parameter read per entity                                                                                |
| `shift(array, along=dim, offset=n, within=relation[c])`    | The result is the value `n` positions earlier inside each group that the relation's column `c` makes. Neighbours, edges and a wrap all belong to that group                 |
| `sum_back(array, along=dim, window=n)`                     | The result is the sum of the last `n` positions along `dim`, ending at the position being written                                                                           |
| `sum_back(array, along=dim, window=p)`                     | The result is the sum of the last `p` positions, with `p` an integer parameter read per entity                                                                              |
| `sum_back(array, along=dim, window=p, edge='wrap')`        | Instead of stopping short at its start, the window reaches around the dimension                                                                               |
| `sum_back(array, along=dim, window=n, within=relation[c])` | The window stays inside each group that the relation's column `c` makes                                                                                       |

`array` is any expression with the right dimensions, such as a parameter or a
variable. [Every operator as math](#every-operator-as-math) lists the typeset
form of each row of the table.

## `sum`

`sum` adds the values of an expression along one or more dimensions, and
removes those dimensions from the result. Each row of the result is the sum of
the values that share its coordinates, and no value moves between rows.
`array` must be indexed over each dimension in `over=`, and a list contains
each dimension once. `sum(x, over=[a, b])` is the same as
`sum(sum(x, over=a), over=b)`, and the [typesetter](../typeset.md) prints it as
one sum over both sets.

With `by=`, the sum adds up
each group that a column of a [relation](relations.md) makes, and the result is
indexed over that column. The balance at each bus (a nodal balance) is one
`sum(by=)` per kind of component:

```yaml
dimensions:
  bus: { dtype: str }
  generator: { dtype: str }
  line: { dtype: str }
relations:
  gen_bus: { key: generator, values: bus }
  line_from: { key: line, values: bus }
  line_to: { key: line, values: bus }
parameters:
  load: { dims: [bus] }
  cost: { dims: [generator] }
variables:
  p: { dims: [generator], bounds: { lower: 0 } }
  f: { dims: [line] }
constraints:
  nodal_balance:
    dims: [bus]
    expression: >-
      sum(p, over=generator, by=gen_bus[bus])
      + sum(f, over=line, by=line_to[bus])
      - sum(f, over=line, by=line_from[bus])
      == load
objective: { sense: minimize, expression: "sum(p * cost, over=generator)" }
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} p_{g} + \sum_{l \in \mathcal{L} \,:\, \mathrm{line\_to}(l) = b} f_{l} - \left( \sum_{l \in \mathcal{L} \,:\, \mathrm{line\_from}(l) = b} f_{l} \right) = \mathrm{load}_{b} \qquad \forall\, b \in \mathcal{B}
```

At load, mathspec refuses `sum(x)` over an expression that has no dimension. With a
parameter `total: { dims: [] }` added to the spec above, and the constraint
`r: { dims: [], expression: "sum(p) <= sum(total)" }`, mathspec prints:

```text
Constraint 'r': sum() has no over= or by=, and its operand has no dimensions to sum over. Remove the sum.
```

The scalar `total` has nothing to add up, so mathspec suggests the rewrite: no
sum.

!!! info "See also"

    - [How a relation is used](relations.md#how-a-relation-is-used), for
      the dimensions that a call through a relation joins on, and those its result
      has.

## `at`

`at` takes, for each key label of a relation, the value of an expression at
the label that the relation maps it to. `at` adds nothing up (a
[lookup](relations.md#lookups)), and takes one row for each key label. Here
`at` takes,
for every line, the build decision of its bus:

```yaml
dimensions:
  bus: { dtype: str }
  line: { dtype: str }
relations:
  line_bus: { key: line, values: bus }
parameters:
  cap: { dims: [line] }
variables:
  build: { dims: [bus], domain: binary }
  f: { dims: [line] }
constraints:
  flow_needs_build:
    dims: [line]
    expression: f <= cap * at(build, by=line_bus[bus])
objective: { sense: minimize, expression: "sum(build, over=bus)" }
```

```math
f_{l} \le \mathrm{cap}_{l} \cdot \mathit{build}_{\mathrm{line\_bus}(l)} \qquad \forall\, l \in \mathcal{L}
```

`at` removes the column in `by=`, `bus`, and adds the key, `line`, so `build`
is read once per line.

## `shift`

`shift` takes the value of an expression a number of positions earlier along
an [ordered](dimensions.md#ordered) dimension. `shift` counts positions in the
order of the dimension, not labels. Only the values move, and the result has
the [coordinates](../glossary.md#coordinate) of the expression. `edge=` sets
the value at a coordinate where nothing moved in. Here `edge='wrap'` makes a store cyclic, so the first
snapshot takes the value of the last:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  storage: { dtype: str }
parameters:
  eta: { dims: [storage] }
variables:
  soc: { dims: [snapshot, storage], bounds: { lower: 0 } }
  charge: { dims: [snapshot, storage], bounds: { lower: 0 } }
  discharge: { dims: [snapshot, storage], bounds: { lower: 0 } }
constraints:
  storage_balance:
    dims: [snapshot, storage]
    expression: soc == shift(soc, along=snapshot, offset=1, edge='wrap') + charge * eta - discharge
objective: { sense: minimize, expression: sum(charge) }
```

```math
\mathit{soc}_{t,s} = \mathit{soc}_{t \ominus 1,s} + \mathit{charge}_{t,s} \cdot \mathrm{eta}_{s} - \mathit{discharge}_{t,s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
```

With three snapshots of data, snapshot 0 of the storage `battery` takes the value of the last snapshot. Each later snapshot takes the value of the one before it. The legend of the typeset
document defines $`t \ominus k`$ as $`t-k`$, counted cyclically.

Without `edge=`, the vacated coordinate is absent, so a row that uses it is
also [absent](absence.md#how-absence-travels).

Over a variable, the only numeric edge of a `shift` is `0`. With the
constraint `r: soc >= shift(soc, along=snapshot, offset=1, edge=5)` over
`[snapshot, storage]` in the spec above, mathspec prints:

```text
Constraint 'r': shift(edge=5) reads a variable, and over a variable only edge=0 is allowed. Write edge=0, and add the constant to the expression.
```

mathspec suggests the rewrite: `edge=0`, with the constant `5` in the
expression.

At load, mathspec refuses a `shift` with no `edge=` over an expression with no
variable. With a parameter `inflow` over `[snapshot, storage]` added to the spec
above, and `r: soc >= shift(inflow, along=snapshot, offset=1)`, mathspec prints
three rewrites:

```text
Constraint 'r': shift() over an expression with no variable leaves the vacated positions with no value. Write which you mean:
  shift(x, along=d, offset=n, edge='wrap')   the dimension really is cyclic
  shift(x, along=d, offset=n, edge=0)        the vacated positions contribute zero
  ...and a where: excluding them        the vacated rows should not exist at all
A where: alone does not remove this refusal, and edge=0 alone keeps a row whose bound is that zero.
```

Each rewrite is one meaning of the vacated positions: a cyclic dimension, a
zero, or no row.

!!! info "See also"

    - [Absence and where](absence.md) for how an absent edge travels through the
      rest of an expression.
    - [State a rule that differs by case](../../howto/cases.md) for an initial
      condition written as an entry of its own.

### `within=`

`within=` takes a [partition](relations.md#partitions), such as one into
seasons, and the neighbour of a coordinate is then the one before it in its own
group:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  season: { dtype: str }
relations:
  season_of: { key: snapshot, values: season }
parameters:
  inflow: { dims: [snapshot] }
variables:
  soc: { dims: [snapshot], bounds: { lower: 0 } }
constraints:
  season_balance:
    dims: [snapshot]
    expression: soc == shift(soc, along=snapshot, offset=1, edge='wrap', within=season_of[season]) + inflow
objective: { sense: minimize, expression: sum(soc) }
```

```math
\mathit{soc}_{t} = \mathit{soc}_{t \ominus^{\mathrm{season\_of}(t)} 1} + \mathrm{inflow}_{t} \qquad \forall\, t \in \mathcal{T}
```

The first snapshot of each season takes the value of the last snapshot of the
same season. Every `edge=` setting applies one group at a time, and a
coordinate in no group is absent under every `edge=`.

### `offset=` from a parameter

A parameter as offset states a construction lead time, a transit time, or any
other delay that is a column of the data:

```yaml
dimensions:
  technology: { dtype: str }
  month: { dtype: int, ordered: true }
parameters:
  lead: { dims: [technology], dtype: int }
  demand: { dims: [technology, month] }
variables:
  order:
    dims: [technology, month]
    bounds: { lower: 0 }
constraints:
  arrives_after_its_lead:
    dims: [technology, month]
    expression: shift(order, along=month, offset=lead, edge=0) >= demand
objective: { sense: minimize, expression: sum(order) }
```

```math
\mathit{order}_{t,m \boxminus_{0} \mathrm{lead}} \ge \mathrm{demand}_{t,m} \qquad \forall\, t \in \mathcal{T},\ m \in \mathcal{M}
```

For each technology, the shift takes `order` `lead` months back, and
$`m \boxminus_{0} k`$ is $`m-k`$ with `0` past the edge.

mathspec refuses the
file at load for any of four faults of the parameter. With `lead` declared
`dtype: float`, mathspec prints:

```text
Constraint 'arrives_after_its_lead': shift(offset=lead) counts positions, but 'lead' is declared dtype: float. Declare it dtype: int.
```

An offset is a count of positions, so `lead` must be `dtype: int`.

The offset may not vary along the dimension that the shift moves along. With `lead`
declared over `[technology, month]`, mathspec prints:

```text
Constraint 'arrives_after_its_lead': shift(offset=lead) steps along 'month', and 'lead' is declared over ['month', 'technology']. Declare 'lead' over dims without 'month'.
```

`lead` then varies along `month`, the dimension that the shift moves along.

mathspec reads the offset over the dimensions of the shifted expression, and
over the dimension that a [`within=`](#within) column groups into. At load, mathspec refuses an offset over any other dimension. With a dimension `period`, a relation
`period_of: { key: month, values: period }`, and `lead` declared over
`[period]`, the spec loads under `within=period_of[period]`, with one offset
per period. Without the `within=` on the shift, mathspec refuses the file and
prints:

```text
Constraint 'arrives_after_its_lead': shift(offset=lead): 'lead' varies over ['period'], which the expression does not carry (dims ['month', 'technology']). Declare 'lead' over dims the expression carries, or group by a relation into one of ['period'].
```

`period` is neither a dimension of `order` nor a group of a `within=`.

An offset may not negate the parameter, and with `offset=-lead` mathspec
prints:

```text
Constraint 'arrives_after_its_lead': shift(offset=-lead) negates a named offset. Negate the values of the parameter instead.
```

mathspec suggests the rewrite: the values of `lead`, negated in the data.

## `sum_back`

`sum_back` sums the last `window` positions along an
[ordered](dimensions.md#ordered) dimension, ending at the position being
written. `sum_back` states the hours a started unit stays on (a minimum up
time), a rolling budget or a delivery horizon. The dimension **stays** in the
result, and with a window of `1` the result is `array`.

```yaml
dimensions:
  unit: { dtype: str }
  hour: { dtype: int, ordered: true }
parameters:
  min_up: { dims: [unit], dtype: int }
variables:
  started: { dims: [unit, hour], domain: binary }
  on: { dims: [unit, hour], domain: binary }
constraints:
  stays_up_its_own_time:
    dims: [unit, hour]
    expression: sum_back(started, along=hour, window=min_up) <= on
objective: { sense: minimize, expression: sum(on) }
```

```math
\sum_{h' \in \mathcal{H} \,:\, 0 \le h - h' < \mathrm{min\_up}} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}
```

A unit that started in any of the last `min_up` hours must be on, and each unit
has its own window length.

A window given as a parameter is `dtype: int`, and does not vary along the
dimension being summed. With `min_up` declared over `[unit, hour]`, mathspec
prints:

```text
Constraint 'stays_up_its_own_time': sum_back(window=min_up) steps along 'hour', and 'min_up' is declared over ['hour', 'unit']. Declare 'min_up' over dims without 'hour'.
```

`min_up` then varies along `hour`, the dimension that the window runs along.

Without `edge=`, a window that reaches past the start of the dimension is
**short**, and no row is lost. `edge=` takes `'wrap'` or nothing, and `'wrap'` makes the window reach
around to the end. With `edge=0`, mathspec prints:

```text
Constraint 'stays_up_its_own_time': sum_back(edge=...) takes 'wrap' or nothing. To add a constant, write it in the expression.
```

mathspec suggests the rewrite: the constant, written in the expression.

As for [`shift`](#within), `within=` takes a
[partition](relations.md#partitions), and the window then stays inside each
group.

## Every operator as math

The typesetter prints each form from the smallest spec that uses it.

<!-- Generated by tools/spec_math.py from examples/operators/. Regenerate with `pixi run python -m tools.spec_math`. -->

<!-- operator-math:begin -->
| Operator | Renders as |
|---|---|
| `sum(array)` | $`\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \le \mathrm{budget}`$ |
| `sum(array, over=dim)` | $`\sum_{g \in \mathcal{G}} p_{t,g} \le \mathrm{limit}_{t} \qquad \forall\, t \in \mathcal{T}`$ |
| `sum(array, over=[a, …])` | $`\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g,c} \le \mathrm{limit}_{c} \qquad \forall\, c \in \mathcal{C}`$ |
| `sum(array, over=dim, by=relation[c])` | $`\sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} p_{t,g} \le \mathrm{limit}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}`$ |
| `sum(array, over=dim, by=relation[c]), joining on the rest of the key` | $`\sum_{g \in \mathcal{G} \,:\, \mathrm{zone\_of}(g,\ e) = z} p_{g,e} \ge \mathrm{demand}_{z,e} \qquad \forall\, z \in \mathcal{Z},\ e \in \mathcal{E}`$ |
| `sum(array, over=[dim, …], by=relation[c, …])` | $`\sum_{g \in \mathcal{G},\ e \in \mathcal{E} \,:\, \mathrm{slot\_of.bus}(g,\ e) = b \wedge \mathrm{slot\_of.technology}(g,\ e) = t} p_{g,e} \le \mathrm{cap}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}`$ |
| `at(array, by=relation[c])` | $`p_{t} \le \mathrm{cap}_{\mathrm{period\_of}(t)} \qquad \forall\, t \in \mathcal{T}`$ |
| `at(array, by=relation[c]), two columns over one dimension` | $`f_{l} \le \mathrm{cap}_{\mathrm{ends.bus0}(l)} \qquad \forall\, l \in \mathcal{L}`$ |
| `shift(array, along=dim, offset=n)` | $`p_{t} \le p_{t - 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `shift(array, along=dim, offset=n, edge='wrap')` | $`p_{t} \le p_{t \ominus 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `shift(array, along=dim, offset=n, edge=v)` | $`p_{t} \le p_{t \boxminus_{0} 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `shift(array, along=dim, offset=p, edge=…)` | $`\mathit{order}_{t,m \boxminus_{0} \mathrm{lead}} \ge \mathrm{demand}_{t,m} \qquad \forall\, t \in \mathcal{T},\ m \in \mathcal{M}`$ |
| `shift(array, along=dim, offset=n, within=relation[c])` | $`p_{t} \le p_{t \ominus^{\mathrm{season\_of}(t)} 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `sum_back(array, along=dim, window=n)` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h - h' < 3} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `sum_back(array, along=dim, window=p)` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h - h' < \mathrm{min\_up}} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `sum_back(array, along=dim, window=p, edge='wrap')` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h \ominus h' < \mathrm{min\_up}} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `sum_back(array, along=dim, window=n, within=relation[c])` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h -^{\mathrm{day\_of}(h)} h' < 3} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `dual(constraint)` | $`\mathit{price}_{t} = \lambda_{\mathrm{balance},t} \qquad \forall\, t \in \mathcal{T}`$ |
<!-- operator-math:end -->

!!! info "See also"

    - [Absence and where](absence.md) for what each operator does with an absent
      input.
    - [Relations](relations.md#how-a-relation-is-used) for the relation that `by=`
      and `within=` take.
    - [Macros](named.md#macros) for a composition of operators under one name.
    - [One construct per spec](../../examples/operators.md) for the smallest spec
      that uses each form.
    - [Typeset output](../typeset.md) for how the typesetter prints a spec.
