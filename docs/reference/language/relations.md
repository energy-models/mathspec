<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Relations

A **relation** is a mapping between [dimensions](dimensions.md): a generator's
bus, a snapshot's period, or the buses a generator may connect to. You declare
it as a table, and the data supplies its rows.

## `relations`

```yaml
dimensions:
  bus: { dtype: str }
  generator: { dtype: str }
  snapshot: { dtype: int }
  period: { dtype: int }
relations:
  gen_bus: { key: generator, values: bus } # each generator on one bus
  period_of: { key: snapshot, values: period }
  connection: { key: [generator, bus] } # no values: a generator may connect to several buses
```

The **key** is the combination of dimensions that is unique per row:
`key: generator` says the table has one row per generator. The **values** are
what that row determines: its bus. With no `values:`, the key is every column,
and the table is a **bare relation**.

| Field         |                                                                       |                |
| ------------- | --------------------------------------------------------------------- | -------------- |
| `key`         | required. The columns that identify a row                             |                |
| `values`      | the columns the key determines. When omitted, the key is every column | default none   |
| `description` | free text                                                             | default `null` |

A column is named after its dimension, or after no dimension. Where two columns
share a dimension, the mapping form names them: `{bus0: bus, bus1: bus}`. A
column named after a dimension it is not over, `{values: {period: zone}}`, is
refused. A call reads `period` as the name of the column, and the column and
the dimension must then agree.

### Cardinalities

| intention                                    | written                                               | cardinality                                 |
| -------------------------------------------- | ----------------------------------------------------- | ------------------------------------------- |
| each generator has one bus                   | `{key: generator, values: bus}`                       | many-to-one                                 |
| a generator may connect to several buses     | `{key: [generator, bus]}`, no `values:`               | many-to-many                                |
| a generator has one zone in each period      | `{key: [generator, period], values: zone}`            | many-to-one, keyed by a pair                |
| a snapshot has a month, a week and a weekday | `{key: snapshot, values: [month, week, weekday]}`     | many-to-one, several values                 |
| a line has two ends, both buses              | `{key: line, values: {bus0: bus, bus1: bus}}`         | many-to-one, two columns over one dimension |
| a snapshot has a representative snapshot     | `{key: snapshot, values: {rep: snapshot}}`            | many-to-one, onto itself                    |
| a snapshot has neighbours                    | `{key: {from: snapshot, to: snapshot}}`, no `values:` | many-to-many, onto itself                   |

A key that determines a value holds one column per dimension, so
`{key: {bus0: bus, bus1: bus}, values: line}` is refused, but a bare relation
may key two columns over one dimension.

### The data contract

The data for `gen_bus` arrives under the key `gen_bus`, as a table with one
column per declared column, named after it.

- One row per key tuple, so a generator on two buses is refused when the data
  is attached.
- Every value is a label of its dimension, and a value that matches none is
  refused.
- A partial map is the rows it has, so a generator in no row sits on no bus,
  which is [absence](absence.md).
- A null in any column is refused.
- Row order has no meaning, because the order comes from the
  [dimension](dimensions.md).

## How a relation is used

The declaration fixes no direction. A call **joins** the operand to the
relation on the columns they share, and **groups** what the join produces. A
call names columns of a relation as `relation[column]`, or as
`relation[column, …]` for several columns of one table. The relation is written
once, so one call reads one table.

| kind              | what it does                                                                 | written as                                         |
| ----------------- | ---------------------------------------------------------------------------- | -------------------------------------------------- |
| join and group by | rows of the operand match rows of the relation, and each group is added up   | `sum(x, over=d, by=l[c])`                          |
| join              | each row of the operand matches one row of the relation, and reads its value | `at(x, by=l[c])`                                   |
| partition         | the dimensions stay, and the rows are grouped                                | `shift`, `sum_back`, `position` with `within=l[c]` |
| test              | a row's presence keeps or cuts a coordinate                                  | `l`, or `l[c]` in a comparison, in a `where`       |

Four rules hold for every use:

1. A call names every column it reads, so `at(x, by=gen_bus)` is refused.
   Write `at(x, by=gen_bus[bus])`.
2. A value column the call does not name is not read.
3. The key is fixed, so to change it, declare a new relation.
4. A dimension the relation does not name passes through to the result.

### Sums through a relation

`sum(x, over=d, by=l[c])` sums `x` over the columns in `over=`, grouped by
the columns in `by=`. As in `sum(x, over=d)`, `over=` names what the result
loses, and `by=` names what the result gains. Either may be a list.

Each column of the relation is either **joined on** or not, and either
**grouped by** or not. The call decides both:

| column of the relation                | joined on | grouped by | in the result |
| ------------------------------------- | --------- | ---------- | ------------- |
| a column in `over=`                   | yes       | no         | removed       |
| a column in `by=`                     | no        | yes        | added         |
| a key column the call does not name   | yes       | yes        | kept          |
| a value column the call does not name | no        | no         | not read      |

With `zone_of: { key: [generator, period], values: zone }`, the bare
`connection: { key: [generator, bus] }` and `p` over `[generator, period]`:

| call                                         | joins on            | groups by         | result              |
| -------------------------------------------- | ------------------- | ----------------- | ------------------- |
| `sum(p, over=generator, by=zone_of[zone])`   | `generator, period` | `zone, period`    | `[zone, period]`    |
| `sum(p, over=period, by=zone_of[zone])`      | `period, generator` | `zone, generator` | `[generator, zone]` |
| `sum(p, over=generator, by=connection[bus])` | `generator`         | `bus`             | `[bus, period]`     |

- The result is the operand, less the dimensions in `over=`, plus the columns
  in `by=`. The operand carries every column joined on, and none that the call
  groups by, because a column the operand carries is joined on, not grouped
  by. `sum(load * p, over=generator, by=gen_bus[bus])` is refused. Write
  `load * sum(p, over=generator, by=gen_bus[bus])`.
- A name in `over=` is a column of the relation, or else a dimension. With
  `rep_of: { key: snapshot, values: { rep: snapshot } }`,
  `sum(x, over=snapshot, by=rep_of[rep])` joins on the key column `snapshot`
  and groups by `rep`. Where two columns are over one dimension, the name says
  which: `sum(x, over=from, by=nbr[to])`. A call writes every column it
  reads, so you can add a value column to a relation and no call changes its
  meaning. A name in both `over=` and `by=` is refused.
- A dimension in `over=` that no column is named after is summed away after the
  group-by. `sum(p, over=[generator, snapshot], by=gen_bus[bus])` adds up each
  bus over every snapshot.
- A sum adds up several rows per group. Where the columns grouped by hold the
  whole key, every group is one row. That is a join with no group-by, which is
  `at`, so `to_spec` refuses the sum and names `at`:

  ```text
  Constraint 'cap': sum(by=zone_of[generator, period]): the columns this sum groups by, ['generator', 'period'], hold the whole key ['generator', 'period'], so every group is one row and the sum adds nothing. Write at(..., by=zone_of[zone]), or group by a value column.
  ```

### Lookups

`at(x, by=l[c])` reads `x` at the value of column `c`, once for every row of
the relation. It joins `x` on the columns in `by=` and groups by the key, so
every group is one row.

- A lookup reads value columns. A key column in `by=` is refused, and so is a
  bare relation, where a key tuple can have several rows. Sum through them
  instead.
- The result gains the key columns, except where the operand carries them
  already. A key column over a dimension the operand carries is joined on too,
  unless a column in `by=` already matches that dimension. With `price` over
  `[zone, period]`, `at(price, by=zone_of[zone])` joins on `zone` and
  `period`, and its result is `[generator, period]`. `at(x, by=rep_of[rep])`
  joins on `rep` alone, so the result gains the key column `snapshot`.
- No two columns in `by=` are over one dimension, because the operand carries
  each dimension once, and so has one coordinate to read at.

### Partitions

`shift(x, along=d, within=l[c])`, `sum_back(x, along=d, within=l[c])` and
`position(d, within=l[c])` step along the key column over `d`, join on the
other key columns, and partition the rows by the value columns in `within=`.
The dimensions do not change. `within=` may name two columns over one
dimension, but not a key column. A bare relation partitions nothing, and a
coordinate the relation sends nowhere is in no group.

### Tests

A `where` string uses a relation at the coordinates of its own declaration. It
compares a column under `values:`, written `l[c]`, against a label, compares
two columns of one table, or tests that a row exists
([where strings](expressions.md#where-strings)). A comparison reads one column,
so `calendar[month, weekday] == 'x'` is refused.
