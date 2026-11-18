<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Dimensions

A **dimension** is a set of labels that entries are indexed over, such as the
hours in `snapshot` or the units in `generator`.
This page lists the keys a dimension accepts, the closed label lists of
`one_of`, the rule for the order of a dimension, and the members that a
dimension lists under `over`.

## `dimensions`

Each key under `dimensions:` declares one dimension, and every dimension that
the file uses anywhere is declared here.

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
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

`snapshot` has integer labels in a fixed order, and `generator` has string
labels in no order. `sum(dispatch, over=generator)` removes `generator`, so
`power_balance` has one row per snapshot.

The order of the keys under `dimensions:`, and the order of a `dims:` list,
change nothing. mathspec sorts both by name at load, and an entry is indexed
over its dimensions in that order. So `dispatch` above prints as
$`\mathit{dispatch}_{g,t}`$, and the legend lists `generator` first.

| Key           | What it sets                                                                | Default  |
| ------------- | --------------------------------------------------------------------------- | -------- |
| `dtype`       | the type of a label: `float`, `int`, `str` or `datetime`                    | `str`    |
| `one_of`      | [the labels a `str` dimension allows](#one_of)                              | `null`   |
| `ordered`     | whether the order of the labels is part of the spec ([`ordered`](#ordered)) | `false`  |
| `over`        | [the dimensions whose labels a label combines](#over)                       | `null`   |
| `missing`     | [whether every combination of the members needs a label](#missing)          | `absent` |
| `description` | free text, which the typeset legend lists                                   | `null`   |

The file does not list the labels themselves. They arrive with the data, in
the order that the data table lists them. With data attached, a piece of
software that reads a spec ([a tool](../glossary.md#tool)) matches every entry
indexed over the dimension to the labels.

mathspec loads a dimension that no entry uses, and for that dimension
`python -m mathspec check` prints a message that does not refuse the file
([advice](../glossary.md#advice)).

A map from one dimension onto another is a [relation](relations.md), not a
dimension.

## `one_of`

`one_of` lists every label that a `str` dimension allows. With `one_of`
declared, mathspec checks at load the spelling of each label that a condition
compares against.

```yaml
dimensions:
  carrier: { dtype: str, one_of: [ccgt, ocgt, wind] }
  generator: { dtype: str }
relations:
  carrier_of: { key: generator, values: carrier }
variables:
  p: { dims: [generator], where: "carrier_of == 'wind'" }
```

`p` exists only at the generators whose carrier is `wind`. The relation
`carrier_of` maps each generator to one carrier, and `one_of` makes `wind` one of
three allowed labels.

A `one_of` list meets four rules:

- Each label is a string, so mathspec refuses a number such as `2030` and
  accepts the string `'2030'`.
- The list has at least one label, and each label once.
- The `dtype` is `str` by default, so `carrier: { one_of: [ccgt, ocgt, wind] }`
  declares the same dimension. mathspec refuses a `one_of` with any other
  `dtype`.
- In every other rule, the dimension is an ordinary `str` dimension.

The order of the list changes nothing. mathspec sorts it by name at load, so
`one_of: [wind, ccgt, ocgt]` declares the same dimension.

At load, mathspec refuses a [condition](expressions.md#conditions) that
compares the dimension, or a relation column over it, against a label that is
not in the list. With `carrier_of == 'gnrtr'` in place of `'wind'` above, mathspec prints:

```text
Variable 'p': 'gnrtr' is not a label of 'carrier', which allows only ['ccgt', 'ocgt', 'wind']. Write one of them, or add 'gnrtr' to the one_of of 'carrier'.
```

mathspec lists the allowed labels and suggests two rewrites.

With data attached, a tool refuses a label
outside the list, in the table of the dimension and in every relation column
over it.

Only a dimension takes `one_of`, and a `one_of` key on a parameter is refused
as an unknown key.

## `ordered`

`ordered: true` makes the order of the labels part of the spec. Five
constructs use the order of a dimension, and each one requires `ordered: true`:

| Construct                                                                            | What it uses                     |
| ------------------------------------------------------------------------------------ | -------------------------------- |
| [`shift(x, along=d, offset=n)`](operators.md#shift), in an expression or a condition | the label `n` positions back     |
| [`sum_back(x, along=d, window=n)`](operators.md#sum_back)                            | the last `n` labels              |
| [`position(d)`](expressions.md#position)                                             | where a label sits along `d`     |
| [`piecewise:`](piecewise.md) with `over: d`                                          | which breakpoints are neighbours |
| a [special ordered set (`sos:`)](piecewise.md#sos) with `type: 2` and `along: d`     | which labels are consecutive     |

The ramp constraint below steps back one snapshot, and `snapshot` is not
declared ordered:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  ramp_limit: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator] }
constraints:
  ramp:
    dims: [snapshot, generator]
    expression: p - shift(p, along=snapshot, offset=1) <= ramp_limit
```

```text
Constraint 'ramp': shift(along=snapshot) reads the order of 'snapshot', which is not declared ordered, so the order would come from the row order of the data. Declare 'snapshot: {ordered: true}' under dimensions:.
```

<figure class="diagram">
--8<-- "docs/static/dimensions-ordered.svg"
</figure>

The file loads once `snapshot` is declared `{ dtype: int, ordered: true }`.
With snapshots `1`, `2` and `3` attached, `shift` has a row at snapshots `2`
and `3` and none at `1`.

An `int` dimension is not ordered unless it declares `ordered: true`.

An `sos` entry of `type: 1` uses no order, so it needs no `ordered: true`.

A dimension with [`over:`](#over) has no order, so mathspec refuses
`ordered: true` on it.

[`edge='wrap'`](operators.md#shift) makes one `shift` cyclic, so that the first
label steps back to the last. `edge='wrap'` does not change the dimension, and
the dimension still needs `ordered: true`.

## `over`

`over` lists the dimensions (the **members**) whose labels a label of the
dimension combines. A label is then one tuple of member labels, such as the
unit `u1` with the port `out`.

```yaml
dimensions:
  unit: { dtype: str }
  port: { dtype: str }
  bus: { dtype: str }
  snapshot: { dtype: int, ordered: true }
  connection: { over: [unit, port] }
relations:
  connection_bus: { key: connection, values: bus }
parameters:
  capacity: { dims: [unit] }
  load: { dims: [bus, snapshot] }
variables:
  flow: { dims: [connection, snapshot], bounds: { lower: 0 } }
constraints:
  limit:
    dims: [connection, snapshot]
    expression: flow <= at(capacity, by=connection[unit])
  balance:
    dims: [bus, snapshot]
    expression: sum(flow, over=connection, by=connection_bus[bus]) == load
```

`flow` has one column per listed connection and snapshot, and none for a unit
and a port that the data does not list together. `limit` reads the capacity of
the unit of each connection, and `balance` adds each flow to the bus of its
connection. The legend prints the dimension as
$`\mathcal{C} \subseteq \mathcal{P} \times \mathcal{U}`$, and `limit` prints as:

```math
\mathit{flow}_{c,t} \le \mathrm{capacity}_{\mathrm{connection.unit}(c)} \qquad \forall\, c \in \mathcal{C},\ t \in \mathcal{T}
```

`over` takes a list of dimensions, or a mapping of name to dimension where two
members are over one dimension:

```yaml
dimensions:
  region: { dtype: str }
  trade: { over: { source: region, target: region } }
```

A member in the list form has the name of its dimension. The order of the
members changes nothing, because mathspec sorts them by name at load.

### The relation of the dimension

A dimension with members also declares a [relation](relations.md) of the same
name. Its key is the dimension, its values are the members, and it has a row
for every label. So `connection` above is also the relation
`{ key: connection, values: [unit, port] }`, and a call reads a member as it
reads any relation column:

| Written                                           | Result                                                      |
| ------------------------------------------------- | ----------------------------------------------------------- |
| `at(capacity, by=connection[unit])`               | the capacity of the unit of each connection                 |
| `at(rating, by=connection[unit, port])`           | `rating`, a parameter over `unit` and `port`, at each tuple |
| `at(flow, by=connection[unit, port])`             | `flow` at each unit and port that the dimension lists       |
| `sum(flow, over=connection, by=connection[port])` | the flows of each port, added over its connections          |
| `where: "connection[unit] == 'u1'"`               | the connections of the unit `u1`                            |
| `where: "at(active, by=connection[unit])"`        | the connections whose unit is in the condition `active`     |

The last `at` is on an operand over `connection`, so the dimension goes and
its members arrive
([`at` by the members of a dimension](operators.md#at-by-the-members-of-a-dimension)).

mathspec refuses a relation under `relations:` with the name of a dimension,
so the file does not declare this relation a second time. A fact about a tuple
that is not a member, such as the bus of a connection, is a relation keyed by
the dimension, as `connection_bus` is above.

### One dimension in every operator

A dimension with members is one dimension wherever a `dims:` list or an
operator names it. mathspec does not align an entry over a member with an
entry over the dimension. With `flow <= capacity` in `limit` above, mathspec
prints:

```text
Constraint 'limit': an operand over ['unit'] meets one over 'connection'. 'unit' is a member of 'connection', which is one dimension here. Read the operand at each tuple: at(capacity, by=connection[unit]), or sum flow to the member: sum(flow, over=connection, by=connection[unit]).
```

mathspec suggests the lookup through the relation of the dimension, or the sum
of `flow` to the member. The same refusal applies wherever the two operands
meet: in a product, in a sum, and in the objective, as in
`sum(flow * capacity)`. An entry over both, such as a variable over
`[connection, unit]`, loads.

mathspec refuses the meeting unless the `dims:` of the entry lists both the
dimension and the member. Then the two operands meet as their cross product,
at every pair of a connection and a unit. With
`dims: [connection, unit, snapshot]`, `flow <= capacity` loads, with one row
for each connection, unit and snapshot. Inside a `sum`, a dimension that the
`sum` adds up is not in the `dims:` of the entry, so
`sum(flow * capacity, over=unit)` is refused in that entry too. The objective
and an [assumption](assumptions.md) have no `dims:`, so mathspec refuses
the meeting in each of them. It also refuses the meeting in the `where:` of a
`piecewise:` entry, because mathspec repeats that condition in assumptions.

A sum over a member is refused the same way. With `sum(flow, over=unit)`,
mathspec prints:

```text
Constraint 'balance': sum(over=unit) but the expression has only the dims ['connection', 'snapshot']. 'unit' is a member of 'connection', which is one dimension here. Write sum(..., over=connection, by=connection[port]).
```

mathspec suggests the sum over the dimension, grouped by the other member.

An entry whose `dims:` lists the dimension beside its own member loads, but
it often means each connection at its own unit only. For such an entry,
`python -m mathspec check` prints [advice](errors.md#what-advice-warns-about).
For `limit` with `dims: [connection, unit, snapshot]`, mathspec prints:

```text
Constraint 'limit': dims: lists 'connection' beside its member 'unit', so the entry is their cross product: each connection meets every unit, not only its own. For its own unit, drop 'unit' from dims: and read the operand at each tuple: at(capacity, by=connection[unit]). To go by unit instead, drop 'connection' from dims: and sum to the member: sum(flow, over=connection, by=connection[unit]).
```

A `dims:` list is the domain of an entry, so a tool refuses a data row at a
tuple that the dimension does not list. A
[`where:`](absence.md#where) condition then removes rows of that domain.

At load, mathspec also refuses each of these, and prints the rewrite:

| Refused                                                                                         | What you write instead                                               |
| ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| a member that has members of its own                                                            | the members themselves, in one list                                  |
| a dimension twice in the list form, as in `over: [region, region]`                              | the mapping form, with a name for each member                        |
| a member named after a dimension that it is not over                                            | another name for the member                                          |
| `ordered: true`, `dtype:` or `one_of:` beside `over:`                                           | the key on a member                                                  |
| `shift`, `sum_back`, `position`, `piecewise:` or `sos:` of `type: 2` along the dimension        | the construct along an ordered member, as described below this table |
| a comparison of the dimension with a label, as in `connection == 'a'`                           | a comparison of a member, as in `connection[unit] == 'u1'`           |
| a call through the relation of the dimension on an operand over both the dimension and a member | the member summed out of the operand first                           |

A tuple has no order, and a member can declare one. `shift` and `sum_back`
step along an ordered member of an operand that
[`at` has moved to the members](operators.md#at-by-the-members-of-a-dimension).
A second `at` reads the result back at each tuple. Here `assignment` lists the
periods in which each unit is active, and `carry` reads the level of the same
unit one period earlier:

```yaml
dimensions:
  unit: { dtype: str }
  period: { dtype: int, ordered: true }
  assignment: { over: [unit, period] }
variables:
  level: { dims: [assignment], bounds: { lower: 0 } }
  charge: { dims: [assignment], bounds: { lower: 0 } }
constraints:
  carry:
    dims: [assignment]
    expression: level == at(shift(at(level, by=assignment[unit, period]), along=period, offset=1), by=assignment[unit, period]) + charge
```

```math
\mathit{level}_{a} = \mathit{level}_{\left( \mathrm{assignment.period}(a) - 1,\ \mathrm{assignment.unit}(a) \right)} + \mathit{charge}_{a} \qquad \forall\, a \in \mathcal{A}
```

`carry` has no row for an assignment whose unit has no assignment one period
earlier, because the shifted level is
[absent](absence.md#how-absence-travels) there.

`position`, `piecewise:` and `sos:` take no operand that `at` can move. An
entry that uses one of them along a member is over the members, and the set
of tuples is a [bare relation](relations.md) over `unit` and `period`. Such an
entry uses the relation as `where: active`, and an entry over `connection` and
`period` reads it as `where: "at(active, by=connection[unit])"`.

### Two dimensions that share a member

Two dimensions with members can share one, as `connection` and `assignment`
share `unit` below. An entry over both is their cross product, with one row
for each pair of a connection and an assignment. A `where:` that compares the
shared member keeps the pairs of one unit, which is the inner join of the two:

```yaml
dimensions:
  unit: { dtype: str }
  port: { dtype: str }
  period: { dtype: int, ordered: true }
  connection: { over: [unit, port] }
  assignment: { over: [unit, period] }
variables:
  sent: { dims: [connection] }
  busy: { dims: [assignment] }
constraints:
  exclusive:
    dims: [connection, assignment]
    where: connection[unit] == assignment[unit]
    expression: sent + busy <= 1
```

mathspec reads each side through the relation of its own dimension, and the
`dims:` of the entry lists both, so the comparison loads ([conditions](expressions.md#conditions)).
`exclusive` prints as:

```math
\mathit{sent}_{c} + \mathit{busy}_{a} \le 1 \qquad \forall\, a \in \mathcal{A},\ c \in \mathcal{C} \,:\, \mathrm{connection.unit}(c) = \mathrm{assignment.unit}(a)
```

Without the `where:`, `exclusive` loads as the cross product, and
`python -m mathspec check` prints advice that suggests the filter:

```text
Constraint 'exclusive': dims: lists 'assignment' and 'connection', which share the member 'unit', so the entry is their cross product: each assignment meets every connection, of its own unit or another. For the pairs that agree on unit (the inner join), add assignment[unit] == connection[unit] to where:.
```

A named expression has no `where:`, so mathspec gives this advice for the
entry that reads it.

The left join also keeps a connection whose unit has no assignment. It is an
entry over `connection` and `period` that reads `busy` in two steps. The
inner `at` moves `busy` from `assignment` to its members, and the outer `at`
reads the result at the unit of each connection:

```yaml
dimensions:
  unit: { dtype: str }
  port: { dtype: str }
  period: { dtype: int, ordered: true }
  connection: { over: [unit, port] }
  assignment: { over: [unit, period] }
variables:
  sent: { dims: [connection, period] }
  busy: { dims: [assignment] }
constraints:
  only_when_busy:
    dims: [connection, period]
    expression: sent <= at(at(busy, by=assignment[unit, period]), by=connection[unit])
```

```math
\mathit{sent}_{c,p} \le \mathit{busy}_{\left( p,\ \mathrm{connection.unit}(c) \right)} \qquad \forall\, c \in \mathcal{C},\ p \in \mathcal{P}
```

`sent` has a column for every connection and period. `only_when_busy` has a
row only where the unit of the connection has an assignment in that period,
because `busy` is [absent](absence.md#how-absence-travels) elsewhere.

The language has no outer join, which would keep the tuples of either
dimension. Write such an entry over the members, as
`dims: [unit, port, period]`, with the two sets of tuples as the bare
relations `plugged` over `[unit, port]` and `active` over `[unit, period]`.
Then `where: "plugged OR active"` keeps the rows of either.

### `missing`

`missing:` on a dimension with members sets whether every combination of
member labels needs a label.

| `missing:`           | Result                                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------ |
| `absent`, by default | the data lists the tuples that exist, and a combination that it leaves out is not in the dimension     |
| `refused`            | a tool refuses data that leaves a combination out, so the dimension is the full product of its members |

With `missing: refused`, the legend prints the dimension with $`=`$ in place of
$`\subseteq`$. mathspec refuses `missing:` on a dimension without `over:`.

### The data contract

With data attached, the labels of `connection` are one column whose values
have one field per member, named after the member: `{unit: u1, port: out}`.
The [relation of the dimension](#the-relation-of-the-dimension) takes its rows
from this column, so a tool reads no table of its own for it.
A tool requires three things of the column:

- Each tuple appears once.
- Every field is a label of its dimension.
- Under `missing: refused`, every combination of member labels appears.

mathspec declares no type for the tuple, so a tool may store the label in any
form that keeps the fields.

!!! info "See also"

    - [Relations](relations.md), for the calls that read a member.

    - [choose between a dimension, a relation and a parameter](../../howto/declare-a-column.md)
      for a column of data.
