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
| `alias`       | [the dimension whose labels this one has](#alias)                           | `null`   |
| `description` | free text, which the typeset legend lists                                   | `null`   |

The file does not list the labels themselves. They arrive with the data, in
the order that the data table lists them. With data attached, a piece of
software that reads a spec ([a tool](../glossary.md#tool)) matches every entry
indexed over the dimension to the labels.

mathspec loads a dimension that no entry uses, and for that dimension
`python -m mathspec check` prints a message that does not refuse the file
([advice](../glossary.md#advice)).

The label of another dimension that each label has, such as the carrier of
each generator, is a [map](relations.md#maps), not a dimension.

## `one_of`

`one_of` lists every label that a `str` dimension allows. With `one_of`
declared, mathspec checks at load the spelling of each label that a condition
compares against.

```yaml
dimensions:
  carrier: { dtype: str, one_of: [ccgt, ocgt, wind] }
  generator: { dtype: str }
maps:
  generator: { carrier: { dim: carrier } }
variables:
  p: { dims: [generator], where: "generator[carrier] == 'wind'" }
```

`p` exists only at the generators whose carrier is `wind`. The map
`generator[carrier]` gives each generator one carrier, and `one_of` makes `wind`
one of three allowed labels.

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
compares the dimension, or a map into it, against a label that is not in the
list. With `generator[carrier] == 'gnrtr'` in place of `generator[carrier] == 'wind'` above, mathspec prints:

```text
Variable 'p': 'gnrtr' is not a label of 'carrier', which allows only ['ccgt', 'ocgt', 'wind']. Write one of them, or add 'gnrtr' to the one_of of 'carrier'.
```

mathspec lists the allowed labels and suggests two rewrites.

With data attached, a tool refuses a label
outside the list: in the table of the dimension, in every column of a relation
over it, and in the column of every map into it.

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
maps:
  connection:
    bus: { dim: bus }
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
    expression: sum(flow, over=connection, by=connection[bus]) == load
```

`flow` has one column per listed connection and snapshot, and none for a unit
and a port that the data does not list together. `limit` reads the capacity of
the unit of each connection, and `balance` adds each flow to the bus of its
connection. The legend prints the dimension as
$`\mathcal{C} \subseteq \mathcal{P} \times \mathcal{U}`$, and `limit` prints as:

```math
\mathit{flow}_{c,t} \le \mathrm{capacity}_{\mathrm{unit}(c)} \qquad \forall\, c \in \mathcal{C},\ t \in \mathcal{T}
```

`over` takes a list of dimensions, each once. Where a tuple holds two labels of
one dimension, such as the two regions of a trade link, one member is an
[alias](#alias) of that dimension:

```yaml
dimensions:
  region: { dtype: str }
  from_region: { alias: region }
  trade: { over: [from_region, region] }
```

A member has the name of its dimension. The order of the
members changes nothing, because mathspec sorts them by name at load.

### The maps of the dimension

Each member is also a [map](relations.md#maps) of the dimension, named after
the member, with `dim:` the dimension of the member and `missing: refused`. So
`connection` above has the maps `unit` and `port` beside the map `bus` that
the file declares, and a call reads a member as it reads any map:

| Written                                           | Result                                                      |
| ------------------------------------------------- | ----------------------------------------------------------- |
| `at(capacity, by=connection[unit])`               | the capacity of the unit of each connection                 |
| `at(rating, by=connection[unit, port])`           | `rating`, a parameter over `unit` and `port`, at each tuple |
| `sum(flow, over=connection, by=connection[port])` | the flows of each port, added over its connections          |
| `where: "connection[unit] == 'u1'"`               | the connections of the unit `u1`                            |
| `where: "at(active, by=connection[unit])"`        | the connections whose unit is in the condition `active`     |

A fact about a tuple that is not a member, such as the bus of a connection,
is a map that the file declares under `maps: connection:`, as `bus` is above.
mathspec refuses a declared map with the name of a member. With
`maps: { connection: { unit: { dim: unit } } }`, mathspec prints:

```text
maps: 'connection': map 'unit' has the name of a member of 'connection', which already gives each tuple its label of 'unit'. Read the member as connection[unit], or rename the map.
```

### One dimension in every operator

A dimension with members is one dimension wherever a `dims:` list or an
operator names it. mathspec does not align an entry over a member with an
entry over the dimension. With `flow <= capacity` in `limit` above, mathspec
prints:

```text
Constraint 'limit': an operand over ['unit'] meets one over 'connection'. 'unit' is a member of 'connection', which is one dimension here. Read the operand at each tuple: at(capacity, by=connection[unit]), or sum flow to the member: sum(flow, over=connection, by=connection[unit]).
```

mathspec suggests the lookup through the map of the member, or the sum
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

A `dims:` list is the domain of an entry, so a tool refuses a data row at a
tuple that the dimension does not list. A
[`where:`](absence.md#where) condition then removes rows of that domain.

At load, mathspec also refuses each of these, and prints the rewrite:

| Refused                                                                                  | What you write instead                                                    |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| a member that has members of its own                                                     | the members themselves, in one list                                       |
| a dimension twice, as in `over: [region, region]`                                        | an [alias](#alias) of the dimension as one of the members                 |
| `ordered: true`, `dtype:` or `one_of:` beside `over:`                                    | the key on a member                                                       |
| `shift`, `sum_back`, `position`, `piecewise:` or `sos:` of `type: 2` along the dimension | an entry over the members, with `where:` a relation that lists the tuples |
| a comparison of the dimension with a label, as in `connection == 'a'`                    | a comparison of a member, as in `connection[unit] == 'u1'`                |
| a call through a member on an operand over both the dimension and that member            | the member summed out of the operand first                                |

A set of tuples with an ordered member, such as the periods in which each unit
is active, therefore stays a [bare relation](relations.md) over `unit` and
`period`. An entry over `unit` and `period` uses it as `where: active`, and an
entry over `connection` and `period` reads it as
`where: "at(active, by=connection[unit])"`.

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
The [maps of the members](#the-maps-of-the-dimension) take their labels from
these fields, so a tool reads no column of the table of the dimension for
them. A tool requires three things of the column:

- Each tuple appears once.
- Every field is a label of its dimension.
- Under `missing: refused`, every combination of member labels appears.

mathspec declares no type for the tuple, so a tool may store the label in any
form that keeps the fields.

## `alias`

An entry is over each dimension once. An alias is the same labels under a
second name, so an entry can be over them twice, such as an efficiency for
each pair of regions that trade:

```yaml
dimensions:
  region: { dtype: str }
  from_region: { alias: region }
relations:
  trade: { dims: [from_region, region], missing: absent }
parameters:
  ire_flo: { dims: [from_region, region], where: trade }
variables:
  exp: { dims: [region] }
  imp: { dims: [region] }
constraints:
  eq_ire:
    dims: [region]
    expression: imp == sum(ire_flo * at(exp, by=from_region[region]), over=from_region)
```

`from_region` has the labels, the `dtype` and the order of `region`, so it
takes no `dtype:`, `one_of:` or `ordered:` of its own. The data of `ire_flo`
has the columns `from_region`, `region` and `value`, and the data has no table
for `from_region`. An alias has the map `from_region[region]`, which sends
each label to itself, so `at(exp, by=from_region[region])` reads `exp` at the
region a row comes from. The typesetter prints the alias as the index of
`region`, primed, over the same set:

```math
\mathit{imp}_{r} = \sum_{r' \in \mathcal{R}} \mathrm{ire\_flo}_{r',r} \cdot \mathit{exp}_{r'} \qquad \forall\, r \in \mathcal{R}
```

An alias names a declared dimension that is no alias itself. A second alias of
`region` prints with two primes.

!!! info "See also"

    - [Relations and maps](relations.md#maps), for the calls that read a member.

    - [choose between a dimension, a relation, a map and a parameter](../../howto/declare-a-column.md)
      for a column of data.
