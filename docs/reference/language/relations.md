<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Relations

A **relation** is a table that maps between [dimensions](dimensions.md), such
as the bus of each generator. The period of each snapshot and the buses that a
generator may connect to are also relations. The file declares the columns of
the table, and the rows come with the data. This page lists the keys of a
relation, the data it expects, and how each operator uses a relation.

## `relations`

Each key under `relations:` declares one relation.

```yaml
dimensions:
  bus: { dtype: str }
  generator: { dtype: str }
  snapshot: { dtype: int }
  period: { dtype: int }
relations:
  gen_bus: { key: generator, values: bus } # each generator on one bus
  period_of: { key: snapshot, values: period }
  connection: { key: [generator, bus], missing: absent } # no values: a generator may connect to several buses
```

The **key** is the combination of columns that is unique per row, so
`key: generator` means that `gen_bus` has one row per generator. The **values**
are what that row determines, which for `gen_bus` is the bus. A relation with
no `values:` is a **bare relation**, and its key is every column.

| Key           | What it sets                                                     | Default   |
| ------------- | ---------------------------------------------------------------- | --------- |
| `key`         | required. The columns that identify a row                        |           |
| `values`      | the columns that the key determines                              | `null`    |
| `missing`     | `refused` or `absent`: whether every key combination needs a row | `refused` |
| `description` | free text                                                        | `null`    |

A column is named after its dimension, or after no dimension. Where two
columns share a dimension, each column has its own name in the mapping form, as in
`{bus0: bus, bus1: bus}`. A column named after a dimension that it is not over
is refused, because mathspec reads the name of a column as its dimension.
With `zp: { key: generator, values: { period: zone } }`, mathspec prints:

```text
Relation 'zp' names column 'period' after dimension 'period', but the column is over 'zone'. Rename the column after what it holds.
```

mathspec suggests one rewrite, which is to rename the column.

### Cardinalities

The key and the values set how many rows each label may have (the
cardinality of the relation):

| What the relation states                     | Written                                                  | Cardinality                                 |
| -------------------------------------------- | -------------------------------------------------------- | ------------------------------------------- |
| each generator has one bus                   | `{key: generator, values: bus}`                          | many-to-one                                 |
| a generator may connect to several buses     | `{key: [generator, bus], missing: absent}`               | many-to-many                                |
| a generator has one zone in each period      | `{key: [generator, period], values: zone}`               | many-to-one, keyed by a pair                |
| a snapshot has a month, a week and a weekday | `{key: snapshot, values: [month, week, weekday]}`        | many-to-one, several values                 |
| a line has two ends, both buses              | `{key: line, values: {bus0: bus, bus1: bus}}`            | many-to-one, two columns over one dimension |
| a snapshot has a representative snapshot     | `{key: snapshot, values: {rep: snapshot}}`               | many-to-one, onto itself                    |
| a snapshot has neighbours                    | `{key: {from: snapshot, to: snapshot}, missing: absent}` | many-to-many, onto itself                   |

A key that determines a value has one column per dimension, so
`{key: {bus0: bus, bus1: bus}, values: line}` is refused:

```text
Relation 'ends' has two key columns over 'bus' (['bus0', 'bus1']). Key the table by one column over each dimension, or move one of them to 'values:'.
```

mathspec suggests two rewrites: one key column over each dimension, or one
column moved under `values:`.

A bare relation may key two columns over one dimension.

### The data contract

With data attached, the data for `gen_bus` is a table named `gen_bus`, with
one column per declared column, named after it. A piece of software that reads
a spec ([a tool](../glossary.md#tool)) requires five things of the table:

- The table has one row per key combination, so a generator on two buses is refused.
- Every value is a label of its dimension, and a value that matches no label is
  refused.
- The table has a row for every combination of the dimensions of its key,
  unless the relation declares [`missing: absent`](#missing).
- A null in any column is refused.
- The order of the rows has no meaning, because the order comes from the
  [dimension](dimensions.md#ordered).

### `missing`

`missing:` sets whether every combination of the dimensions of the key needs a
row. For `gen_bus` the key is `generator`, so every generator needs a row.

```yaml
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  line: { dtype: str }
relations:
  gen_bus: { key: generator, values: bus } # refused: every generator is on a bus
  line_to: { key: line, values: bus, missing: absent } # an open end is meant
  connection: { key: [generator, bus], missing: absent } # most pairs are not connected
```

At `l3`, the data of `line_to` has no row, so `line_to` is absent there.

| `missing:`            | Result                                                                                                                              |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `refused`, by default | a tool refuses the relation when the data is attached, and names the key combination                                                |
| `absent`              | a key combination with no row is not in the relation, so a line with no `line_to` row ends at no bus, which is [absent](absence.md) |

`missing:` applies only to the key. The values cannot be missing, because a
null is refused and every value must be a label of its dimension.

At load, mathspec refuses `missing: neutral` on a relation:

```text
relations.gen_bus.missing: missing: neutral on a relation, which takes refused or absent. A key combination with no row is refused, or is not in the relation.
```

mathspec lists the two values that a relation takes.

A bare relation also needs a row for every key combination. So under the
default `refused`, `connection` needs a row for every generator and bus. Most bare relations are sparse, so they declare `missing: absent`, and a
pair with no row is then not in the relation.

The typeset legend lists `` `line_to` is `absent` where the data has no row ``
beside each dimension of the relation, and nothing for `refused`.

## How a relation is used

A relation fixes no direction, so the same table can map generators to buses
or buses to generators. A call **joins** the expression it acts on (its
operand) to the relation on their shared columns. It then **groups** the rows
that it has joined. In a call, the columns of a relation are written as
`relation[column]`, or as `relation[column, …]` for several columns of one
table. The relation appears
once, so one call uses one table.

| Kind              | What it does                                                                 | Written as                                         |
| ----------------- | ---------------------------------------------------------------------------- | -------------------------------------------------- |
| join and group by | rows of the operand match rows of the relation, and each group is added up   | `sum(x, over=d, by=l[c])`                          |
| join              | each row of the operand matches one row of the relation, and takes its value | `at(x, by=l[c])`                                   |
| partition         | the dimensions stay, and the rows are grouped                                | `shift`, `sum_back`, `position` with `within=l[c]` |
| test              | a coordinate stays where the relation has a row                              | `l`, or `l[c]` in a comparison, in a condition     |

Four rules apply to every use of a relation in a call:

1. A call lists every column it uses.
2. A value column that the call does not list is not used.
3. The key of a relation cannot change in a call.
4. A dimension that no column of the relation is over passes through to the
   result.

Under the first rule, mathspec refuses `at(x, by=gen_bus)`, and the message
lists the columns of the relation:

```text
Constraint 'c': at(by=gen_bus) names the relation and none of its columns. Write by=gen_bus[<column>], with a column of 'gen_bus': ['generator', 'bus'].
```

### Sums through a relation

`sum(x, over=d, by=l[c])` sums `x` over the columns in `over=`, grouped by
the columns in `by=`. As in `sum(x, over=d)`, `over=` lists what the result loses and `by=` lists
what it gains, and either one may be a list. A sum through a relation adds
each row of `x` only to the groups that the relation lists for it. A row that
the relation does not list is left out.

`north` adds up `wind` and `gas`, and `south` is `solar` alone.

Each column of the relation is either **joined on** or not, and either
**grouped by** or not, and the call sets both:

| Column of the relation                | Joined on | Grouped by | In the result |
| ------------------------------------- | --------- | ---------- | ------------- |
| a column in `over=`                   | yes       | no         | removed       |
| a column in `by=`                     | no        | yes        | added         |
| a key column the call does not list   | yes       | yes        | kept          |
| a value column the call does not list | no        | no         | not used      |

With `zone_of: { key: [generator, period], values: zone }`, the bare
`connection: { key: [generator, bus], missing: absent }`, and a variable `p`
over `[generator, period]`, three sums have three results:

| Call                                         | Joins on            | Groups by         | Result              |
| -------------------------------------------- | ------------------- | ----------------- | ------------------- |
| `sum(p, over=generator, by=zone_of[zone])`   | `generator, period` | `zone, period`    | `[zone, period]`    |
| `sum(p, over=period, by=zone_of[zone])`      | `period, generator` | `zone, generator` | `[generator, zone]` |
| `sum(p, over=generator, by=connection[bus])` | `generator`         | `bus`             | `[bus, period]`     |

Five more rules apply to a sum through a relation:

- The operand is over every column that the call joins on, and over none that
  it groups by. A column that the operand is over is joined on.
- A name in `over=` is a column of the relation, or else a dimension. With
  `rep_of: { key: snapshot, values: { rep: snapshot } }`,
  `sum(x, over=snapshot, by=rep_of[rep])` joins on the key column `snapshot`
  and groups by `rep`. Where two columns are over one dimension, the name
  selects which one. With
  `nbr: { key: { from: snapshot, to: snapshot }, missing: absent }`,
  `sum(x, over=from, by=nbr[to])` joins on `from` and groups by `to`.
- A name in both `over=` and `by=` is refused.
- A dimension in `over=` that no column is named after is summed away after
  the call groups the rows. So `sum(p, over=[generator, snapshot], by=gen_bus[bus])` adds
  up each bus over every snapshot.
- A sum adds up several rows per group, and where the columns grouped by are
  the whole key, every group is one row. A sum whose groups are one row each
  is a join with no group-by, which is `at`.

Under the first rule, with `load` over `[bus]`, mathspec refuses
`sum(load * p, over=generator, by=gen_bus[bus])` and prints:

```text
Constraint 'c': sum(by=gen_bus[bus]) groups by ['bus'], which the expression already carries.
Move the factor carrying ['bus'] outside the operator, or group by a column over another dimension.
```

`load * sum(p, over=generator, by=gen_bus[bus])` is accepted, because the sum
no longer has `load` inside it.

Under the last rule, with `p` over `[generator, period, zone]`, mathspec
refuses `sum(p, over=zone, by=zone_of[generator, period])` and prints:

```text
Constraint 'cap': sum(by=zone_of[generator, period]): the columns this sum groups by, ['generator', 'period'], hold the whole key ['generator', 'period'], so every group is one row and the sum adds nothing. Write at(..., by=zone_of[zone]), or group by a value column.
```

mathspec suggests the rewrite: `at`, which takes one row per group.

### Lookups

`at(x, by=l[c])` takes the value of `x` at column `c`, once for every row of
the relation. It joins `x` on the columns in `by=` and groups by the key, so
every group is one row. A lookup adds up nothing, and each row of the result is
the value of `x` at one coordinate. With `line_bus: { key: line, values: bus }`
and a variable `build` over `[bus]`, `at(build, by=line_bus[bus])` has one row
per line:

Lines `l1` and `l2` both take the value of `build` at `north`, and `l3` takes
it at `south`.

Three rules apply to a lookup:

- A lookup uses only value columns. A key column in `by=` is refused, and so is
  a bare relation, where one key combination can have several rows.
- The result gains every key column that the operand is not already over. A key column over a dimension that the operand is over is joined on
  too, unless a column in `by=` already matches that dimension. With `price`
  over `[zone, period]`, `at(price, by=zone_of[zone])` joins on `zone` and
  `period`, and its result is `[generator, period]`. `at(x, by=rep_of[rep])`
  joins on `rep` alone, so the result gains the key column `snapshot`.
- No two columns in `by=` are over one dimension, because the
  operand has one coordinate along each of its dimensions.

### Partitions

`shift(x, along=d, within=l[c])`, `sum_back(x, along=d, within=l[c])` and
`position(d, within=l[c])` step along the key column over `d`. They join on the
other key columns, and split the rows into groups by the value columns in
`within=`. The dimensions of the result do not change. The result is absent at a
coordinate that the relation maps to [no group](operators.md#within). With
`season_of: { key: snapshot, values: season }`,
`shift(soc, along=snapshot, offset=1, edge='wrap', within=season_of[season])`
steps back within each season:

The first snapshot of each season takes the value of the last snapshot of the
same season, and no value crosses from winter to summer.

`within=` may list two columns over one dimension, but not a key column. A
bare relation makes no groups, so mathspec refuses it in `within=`:

```text
Constraint 'd': shift(within=sp[period]): 'sp' has every column in its key, so it makes no groups. Move the group columns under values:, and keep under key: the column shift steps along.
```

mathspec suggests the rewrite: the columns split between `key:` and `values:`.

### Tests

A condition tests a relation at the coordinates of its own entry. It compares
a value column, written `l[c]`, against a label, compares two relation columns, or tests that a row exists.
[Conditions](expressions.md#conditions) lists when two columns may be compared. A
comparison uses one column, so `calendar[month, weekday] == 'x'` is refused,
and mathspec suggests the rewrite:

```text
Variable 'x': Cannot parse the condition "calendar[month, weekday] == 'x'".
a comparison reads one column of 'calendar'. Compare each column on its own: calendar[month] == … AND calendar[weekday] == ….
Expected end of text, found '['  (at char 8), (line:1, col:9)
```

mathspec suggests the rewrite on the second line of the message.

At the key of the relation, a bare relation name in a `where:` tests that a
row exists. On a variable, the condition leaves the variable absent at every pair
that the relation does not list:

```yaml title="flow.yaml"
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  snapshot: { dtype: int }
relations:
  connection: { key: [generator, bus], missing: absent } # the pairs that are wired
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

`flow` exists at the pairs that `connection` lists and is [absent](absence.md)
at every other pair, so `balance` adds up the generators wired to each bus.

`python -m mathspec markdown flow.yaml` prints the domain of `flow` and the
constraint:

```math
\mathit{flow}_{g,b,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \left( g,\ b \right) \in \mathrm{connection}
```

```math
\sum_{g \in \mathcal{G}} \mathit{flow}_{g,b,t} = \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

The domain of `flow` ends in the condition that `(g, b)` is in `connection`.
The condition is over `(generator, bus)`, so it is the same at every snapshot.

!!! info "See also"

    - [relations as linear maps](../../about/relations-as-linear-maps.md) for the
      same calls written as matrices
