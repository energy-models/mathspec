<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Relations and maps

A **relation** is a set of combinations of labels of
[dimensions](dimensions.md), such as the buses that each generator may connect
to. A **map** gives each row of a dimension or a relation one label of a
dimension, such as the bus of each generator. The file declares both, and the
rows come with the data. This page lists the keys of `relations:` and `maps:`,
the data they expect, and how each operator uses them.

## `relations`

Each key under `relations:` declares one relation.

```yaml
dimensions:
  bus: { dtype: str }
  generator: { dtype: str }
  snapshot: { dtype: int }
relations:
  connection: { dims: [generator, bus], missing: absent } # the pairs that are wired
  neighbour: { dims: { from: snapshot, to: snapshot }, missing: absent }
```

Each row of `connection` is one pair of a generator and a bus, and a pair with
no row is not in the relation.

| Key           | What it sets                                                             | Default   |
| ------------- | ------------------------------------------------------------------------ | --------- |
| `dims`        | required. The columns of the relation, at least two                      |           |
| `missing`     | [`refused` or `absent`](#missing): whether every combination needs a row | `refused` |
| `description` | free text                                                                | `null`    |

A column is named after its dimension, or after no dimension. Where two
columns share a dimension, each column has its own name in the mapping form,
as in `{from: snapshot, to: snapshot}`. A column named after a dimension that
it is not over is refused, because mathspec reads the name of a column as its
dimension. With `zp: { dims: { period: zone, generator: generator } }`,
mathspec prints:

```text
Relation 'zp' names column 'period' after dimension 'period', but the column is over 'zone'. Rename the column after what it holds.
```

A relation with one column is refused, because one column holds labels of one
dimension, and a map or a condition states that. With
`r: { dims: [generator] }`, mathspec prints:

```text
Relation 'r' has one column under 'dims:', and a relation needs at least two. To give each generator a label, declare a map under maps: generator:. To mark some of them, declare a bool parameter or a condition.
```

A relation is not a dimension, so its name does not go in `dims:`, `over=` or
`along=`. With `flow: { dims: [connection] }`, mathspec prints:

```text
Variable 'flow' names the relation 'connection', and a relation is not a dimension. Name its dimensions, ['bus', 'generator'], under dims:, and confine the entry with in: [connection].
```

The order of the columns under `dims:` changes nothing. The typesetter sorts
the columns by name, so `connection` above prints as
$`\mathrm{connection} \subseteq \mathcal{B} \times \mathcal{G}`$.

## `maps`

Each key under `maps:` names a **subject**, which is a dimension or a relation.
Each key under the subject declares one map, which gives every row of the
subject one label of the dimension that `refers:` names.

```yaml
dimensions:
  bus: { dtype: str }
  generator: { dtype: str }
  line: { dtype: str }
maps:
  generator:
    bus: bus # each generator is on one bus
  line:
    bus0: bus
    bus1: { refers: bus, missing: absent } # a line may have an open end
```

`bus: bus` is the short form of `bus: { refers: bus }`, and mathspec writes a
map back in the short form when `refers:` is its only key. A condition or an
operator reads a map as `subject[map]`, so `generator[bus]` is the bus of a
generator.

| Key           | What it sets                                                                      | Default   |
| ------------- | --------------------------------------------------------------------------------- | --------- |
| `refers`      | required. The dimension whose labels the map gives                                |           |
| `missing`     | [`refused` or `absent`](#missing): whether every row of the subject needs a label | `refused` |
| `description` | free text                                                                         | `null`    |

A map is named after the dimension it refers to, or after no dimension. The
typesetter prints a map as a function from its subject into that dimension, so
`generator[bus]` prints as $`\mathrm{bus}: \mathcal{G} \to \mathcal{B}`$.
mathspec refuses a map at load in four cases:

- The subject is neither a dimension nor a relation.
- `refers:` names a relation, or names no dimension.
- The map is named after a dimension that it does not refer to.
- The map has the name of a column of its subject.

With `generator: { period: zone }`, mathspec prints:

```text
maps: 'generator': map 'period' is named after dimension 'period', but refers to 'zone'. Rename the map after what it holds.
```

A relation with two columns over one dimension takes no maps, because a map
gives one label per combination of the dimensions of its subject.

### Cardinalities

How many labels a row may have (the cardinality) decides whether a fact is a
map or a relation:

| What the file states                         | Written                                                                                         | Cardinality                 |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------- |
| each generator has one bus                   | `maps: { generator: { bus: bus } }`                                                             | many-to-one                 |
| a generator may connect to several buses     | `relations: { connection: { dims: [generator, bus], missing: absent } }`                        | many-to-many                |
| a generator has one zone in each period      | `relations: { zone_of: { dims: [generator, period] } }` and `maps: { zone_of: { zone: zone } }` | many-to-one, from a pair    |
| a snapshot has a month, a week and a weekday | `maps: { snapshot: { month: month, week: week, weekday: weekday } }`                            | three maps of one subject   |
| a line has two ends, both buses              | `maps: { line: { bus0: bus, bus1: bus } }`                                                      | two maps into one dimension |
| a snapshot has a representative snapshot     | `maps: { snapshot: { rep: snapshot } }`                                                         | many-to-one, onto itself    |
| a snapshot has neighbours                    | `relations: { neighbour: { dims: { from: snapshot, to: snapshot }, missing: absent } }`         | many-to-many, onto itself   |

## `missing`

`missing:` sets whether the data may leave something out. On a relation, it
sets whether every combination of the dimensions under `dims:` needs a row. On
a map, it sets whether every row of the subject needs a label.

```yaml
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  line: { dtype: str }
relations:
  connection: { dims: [generator, bus], missing: absent } # most pairs are not wired
maps:
  generator:
    bus: bus # refused: every generator is on a bus
  line:
    bus0: bus
    bus1: { refers: bus, missing: absent } # an open end is meant
```

<figure class="diagram">
--8<-- "docs/static/relations-missing.svg"
</figure>

At `l3`, the data gives `line[bus1]` no label, so `line[bus1]` is absent there.

| `missing:`            | Result                                                                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `refused`, by default | a tool refuses the data when it is attached, and names the combination or the row                                        |
| `absent`              | a combination with no row is not in the relation, and a row with no label maps to nothing, which is [absent](absence.md) |

No number can replace a missing label, so at load mathspec refuses a value
such as `missing: 0`:

```text
maps.generator.bus.missing: missing: 0 on a map, which takes refused or absent. A row with nothing there is refused, or is not in the data.
```

Under the default `refused`, a relation needs a row for every combination, so
`connection` would need every generator wired to every bus. Most relations are
sparse, so they declare `missing: absent`.

The typeset legend lists `` `connection` is `absent` where the data has no row ``
and `` `line[bus1]` is `absent` where the data gives no label `` beside each
dimension they are over, and nothing for `refused`.

## The data contract

With data attached, each relation and each subject with maps has one table,
named after it. The table of a relation has one column per column under
`dims:`. The table of a subject also has one column per map, named after the
map. So the data for the maps of `line` is a table `line` with the columns
`line`, `bus0` and `bus1`. A piece of software that reads a spec
([a tool](../glossary.md#tool)) requires five things of a table:

- The table has one row per combination of the columns of its subject, so a
  generator with two rows, on two buses, is refused.
- Every label in the column of a map is a label of the dimension it refers to,
  and a label that matches none is refused.
- The table has a row for every combination of its dimensions, unless the
  relation declares `missing: absent`. The table of a dimension has a row for
  every label of the dimension.
- A null is refused, except in the column of a map that declares
  `missing: absent`.
- The order of the rows has no meaning, because the order comes from the
  [dimension](dimensions.md#ordered).

A relation and a map have no `where:`, so their rows and labels come from the
data alone. A tool therefore knows them before it evaluates any condition,
such as the [`where:` of a parameter](parameters-variables-constraints.md#where).

The rows of a relation can also be the coordinates of a parameter or a
variable, its [index set](../glossary.md#index-set). An entry with
`in: [connection]` has coordinates only at the pairs that `connection` lists,
and a tool refuses a row of the data of a parameter at any other pair
([`in`](parameters-variables-constraints.md#in)). A map is not an index set,
because it adds no row to its subject.

An [assumption](assumptions.md) can require rows of a relation or labels of a
map. For `line[bus1]` [above](#missing), `{holds: "line[bus1]", where: "closed"}`
requires an end for every closed line, where `closed` is a `bool` parameter
over `line`.

## How relations and maps are used

A relation fixes no direction, so the same table can map generators to buses
or buses to generators. A call **joins** the expression it acts on (its
operand) to the table on their shared columns, and then **groups** the rows it
has joined. In a call, `s[c]` names the subject `s` and its column `c`, and
`s[c, …]` names several columns of one table. A column is a map of `s`, or one
of the columns of a relation under `dims:`. The subject appears once, so one
call uses one table.

| Kind              | What it does                                                                  | Written as                                         |
| ----------------- | ----------------------------------------------------------------------------- | -------------------------------------------------- |
| join and group by | rows of the operand match rows of the table, and each group is added up       | `sum(x, over=d, by=s[c])`                          |
| join              | each row of the operand matches one row of the table, and takes its label     | `at(x, by=s[m])`                                   |
| partition         | the dimensions stay, and the rows are grouped                                 | `shift`, `sum_back`, `position` with `within=s[m]` |
| test              | a coordinate stays where the relation has a row, or where the map has a label | `r` or `s[m]` in a condition                       |

Four rules apply to every call:

1. A call lists every column it uses.
2. A map that the call does not list is not used.
3. The key of a subject cannot change in a call.
4. A dimension that no column of the table is over passes through to the
   result.

Under the first rule, mathspec refuses `at(x, by=generator)`, and the message
lists the maps of the subject:

```text
Constraint 'c': at(by=generator) names the subject and none of its maps. Write by=generator[<map>], with a map of 'generator': ['bus'].
```

### Sums

`sum(x, over=d, by=s[c])` sums `x` over the columns in `over=`, grouped by
the columns in `by=`. As in `sum(x, over=d)`, `over=` lists what the result
loses and `by=` lists what it gains, and either one may be a list. A sum
through a table adds each row of `x` only to the groups that the table lists
for it. A row that the table does not list is left out.

<figure class="diagram">
--8<-- "docs/static/relations-sum-by.svg"
</figure>

`north` adds up `wind` and `gas`, and `south` is `solar` alone.

Each column of the table is either **joined on** or not, and either
**grouped by** or not, and the call sets both:

| Column of the table                 | Joined on | Grouped by | In the result |
| ----------------------------------- | --------- | ---------- | ------------- |
| a column in `over=`                 | yes       | no         | removed       |
| a column in `by=`                   | no        | yes        | added         |
| a key column the call does not list | yes       | yes        | kept          |
| a map the call does not list        | no        | no         | not used      |

With the relation `zone_of` over `[generator, period]` and its map `zone`, the
relation `connection` over `[generator, bus]`, and a variable `p` over
`[generator, period]`, three sums have three results:

| Call                                         | Joins on            | Groups by         | Result              |
| -------------------------------------------- | ------------------- | ----------------- | ------------------- |
| `sum(p, over=generator, by=zone_of[zone])`   | `generator, period` | `zone, period`    | `[period, zone]`    |
| `sum(p, over=period, by=zone_of[zone])`      | `period, generator` | `zone, generator` | `[generator, zone]` |
| `sum(p, over=generator, by=connection[bus])` | `generator`         | `bus`             | `[bus, period]`     |

Five more rules apply to a sum through a table:

- The operand is over every column that the call joins on, and over none that
  it groups by. A column that the operand is over is joined on.
- A name in `over=` is a column of the table, or else a dimension. With the
  map `rep` of `snapshot`, `sum(x, over=snapshot, by=snapshot[rep])` joins on
  the key column `snapshot` and groups by `rep`. Where two columns are over one
  dimension, the name selects which one, so
  `sum(x, over=from, by=neighbour[to])` joins on `from` and groups by `to`.
- A name in both `over=` and `by=` is refused.
- A dimension in `over=` that no column is named after is summed away after
  the call groups the rows. So
  `sum(p, over=[generator, period], by=generator[bus])` adds up each bus over
  every period.
- A sum adds up several rows per group, and where the columns grouped by are
  the whole key, every group is one row. A sum whose groups are one row each
  is a join with no group-by, which is `at`.

Under the first rule, with `load` over `[bus]`, mathspec refuses
`sum(load * p, over=generator, by=generator[bus])` and prints:

```text
Constraint 'c': sum(by=generator[bus]) groups by ['bus'], which the expression already carries.
Move the factor carrying ['bus'] outside the operator, or group by a map into another dimension.
```

`load * sum(p, over=generator, by=generator[bus])` is accepted, because the
sum no longer has `load` inside it.

Under the last rule, with `p` over `[generator, period, zone]`, mathspec
refuses `sum(p, over=zone, by=zone_of[generator, period])` and prints:

```text
Constraint 'cap': sum(by=zone_of[generator, period]): the columns this sum groups by, ['generator', 'period'], hold the whole key ['generator', 'period'], so every group is one row and the sum adds nothing. Write at(..., by=zone_of[zone]), or group by a map.
```

### Lookups

`at(x, by=s[m])` takes the value of `x` at the label that map `m` gives each
row of `s`. It joins `x` on the maps in `by=` and groups by the key, so every
group is one row. A lookup adds up nothing, and each row of the result is the
value of `x` at one coordinate. With a variable `build` over `[bus]`,
`at(build, by=line[bus0])` has one row per line:

<figure class="diagram">
--8<-- "docs/static/relations-at.svg"
</figure>

Lines `l1` and `l2` both take the value of `build` at `north`, and `l3` takes
it at `south`.

Three rules apply to a lookup:

- A lookup reads only maps. A key column in `by=` is refused, and so is a
  relation with no map, where one combination can have several rows.
- The result gains every key column that the operand is not already over. A
  key column over a dimension that the operand is over is joined on too,
  unless a map in `by=` already refers to that dimension. With `price` over
  `[zone, period]`, `at(price, by=zone_of[zone])` joins on `zone` and
  `period`, and its result is `[generator, period]`. `at(x, by=snapshot[rep])`
  joins on `rep` alone, so the result gains the key column `snapshot`.
- No two maps in `by=` refer to one dimension, because the operand has one
  coordinate along each of its dimensions.

With `at(build, by=line[line])`, mathspec prints:

```text
Constraint 'c': at(by=line[line]) names ['line'], a column of 'line' itself. A lookup reads maps at the row. Name one of its maps, ['bus0', 'bus1'].
```

### Partitions

`shift(x, along=d, within=s[m])`, `sum_back(x, along=d, within=s[m])` and
`position(d, within=s[m])` step along the key column over `d`. They join on
the other key columns, and split the rows into groups by the maps in
`within=`. The dimensions of the result do not change. The result is absent
at a coordinate that the map gives [no group](operators.md#within). With the
map `season` of `snapshot`,
`shift(soc, along=snapshot, offset=1, edge='wrap', within=snapshot[season])`
steps back within each season:

<figure class="diagram">
--8<-- "docs/static/relations-partition.svg"
</figure>

The first snapshot of each season takes the value of the last snapshot of the
same season, and no value crosses from winter to summer.

`within=` may list two maps into one dimension, but not a key column. A
relation with no map makes no groups, so mathspec refuses it in `within=`:

```text
Constraint 'd': shift(within=sp[period]): 'sp' has no map, so it makes no groups. Declare the group as a map of the dimension shift steps along, under maps: snapshot:.
```

### Tests

A condition tests a relation or a map at the coordinates of its own entry. It
compares a map, written `s[m]`, against a label, compares two maps, or tests
that a row or a label exists. [Conditions](expressions.md#conditions) lists
when two maps may be compared. A comparison reads one map, so
`snapshot[month, weekday] == 'x'` is refused, and mathspec suggests the
rewrite on the second line of the message:

```text
Variable 'x': Cannot parse the condition "snapshot[month, weekday] == 'x'".
a comparison reads one map of 'snapshot'. Compare each map on its own: snapshot[month] == … AND snapshot[weekday] == ….
Expected end of text, found '['  (at char 8), (line:1, col:9)
```

A map alone in a condition, such as `line[bus1]`, is true where the map gives
the row a label. A relation name alone is true where the relation has a row.
On a variable, the condition leaves the variable absent at every pair that the
relation does not list:

```yaml title="flow.yaml"
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  snapshot: { dtype: int }
relations:
  connection: { dims: [generator, bus], missing: absent } # the pairs that are wired
parameters:
  load: { dims: [bus, snapshot] }
variables:
  flow:
    dims: [generator, bus, snapshot]
    where: connection
    bounds: { lower: 0 }
constraints:
  balance:
    dims: [bus, snapshot]
    expression: sum(flow, over=generator) == load
```

<figure class="diagram">
--8<-- "docs/static/relations-where-bare.svg"
</figure>

`flow` exists at the pairs that `connection` lists and is
[absent](absence.md) at every other pair, so `balance` adds up the generators
wired to each bus. `in: [connection]` in place of the `where:` gives `flow` the
same coordinates, and mathspec gives advice to write it so
([`in` on a variable](parameters-variables-constraints.md#in-on-a-variable)).

`python -m mathspec markdown flow.yaml` prints the domain of `flow` and the
constraint:

```math
\mathit{flow}_{b,g,t} \ge 0 \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \left( b,\ g \right) \in \mathrm{connection}
```

```math
\sum_{g \in \mathcal{G}} \mathit{flow}_{b,g,t} = \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

The domain of `flow` ends in the condition that `(b, g)` is in `connection`.
The columns are sorted to `(bus, generator)`, and the condition is over those
two columns, so it is the same at every snapshot. A map test prints as
$`\mathrm{bus1}(l) \text{ is defined}`$.

!!! info "See also"

    - [relations as linear maps](../../about/relations-as-linear-maps.md) for the
      same calls written as matrices
