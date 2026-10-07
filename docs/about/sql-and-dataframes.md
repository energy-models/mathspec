<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A spec in SQL and dataframe terms

This page explains each construct of a spec in relational terms. Read it if you
think in SQL, polars or pandas, and want to know what a line of a spec does to
the tables it reads. The [language reference](../reference/language/index.md)
holds the rules. This page only translates them.
[Relations as linear maps](relations-as-linear-maps.md) gives the same
operators in the terms of linear algebra.

The spec below is used throughout. A generator `p` serves the load at its bus in
each snapshot:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
  bus: { dtype: str }
relations:
  gen_bus: { key: generator, values: bus }
parameters:
  load: { dims: [snapshot, bus] }
  p_max: { dims: [generator] }
  cost: { dims: [generator], missing: neutral }
  ramp: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator], bounds: { lower: 0, upper: p_max }, where: "p_max > 0" }
constraints:
  balance:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=gen_bus[bus]) == load
  ramp_up:
    dims: [snapshot, generator]
    expression: p - shift(p, along=snapshot, offset=1) <= ramp
objective:
  sense: minimize
  expression: sum(p * cost)
```

## Declarations are tables

**A dimension is the domain of a key column.** `generator` is the set of
labels a `generator` column may hold. One point of the model, such as one
snapshot for one generator, is a _coordinate_: one value of each key column.

**A parameter is a table keyed by its `dims`.** `load` is a table with the
columns `snapshot`, `bus` and one value column, and its primary key is
`(snapshot, bus)`. A null value is refused. A row that is not there is the only
gap a parameter has, and its [`missing:`](../reference/language/declarations.md#a-missing-row)
says what that gap means.

**A variable and a constraint are tables of rows to build.** `p` has one
decision variable per coordinate of `(snapshot, generator)`. `balance` has one
row per coordinate of `(snapshot, bus)`.

**A relation is a table whose `key:` is its primary key.**
`gen_bus: { key: generator, values: bus }` is a two-column table with one row
per generator. With the default `missing: refused`, every generator must have a
row. With `missing: absent`, a generator may have no row.

## Absence is a missing row

**A `where:` is a `WHERE` on the rows a declaration builds.** `p` has no decision
variable for a generator with `p_max = 0`. The coordinate is not set to zero.
It does not exist, so every expression that reads it sees no row.

**Arithmetic is an inner join on the shared key columns.** `p * cost` joins the
table of `p` and the table of `cost` on `generator`. A key column only one side
carries is crossed, so `p * cost` has the columns `snapshot` and `generator`. A
coordinate with no row on either side has no row in the result. Under the
default `missing: refused`, a parameter has every row, so the join drops only
what a `where:` or a `missing: absent` left out. The
[dimension table](../reference/language/expressions.md#how-dimensions-combine)
gives the key columns of every expression before any data exists.

**`missing: neutral` turns the join into a left join that fills the gap.**
`cost` is `missing: neutral`, so a generator with no `cost` row reads `0`, as
`COALESCE(cost.value, 0)` after a `LEFT JOIN` does. A `missing:` value, such as
`missing: 1`, fills with that value instead.

[Absence and where](../reference/language/absence.md) holds the full rules,
including where a summing operator stops a missing row from spreading.

## Operators are queries

Each operator below is one query shape. In the SQL column, `rest` stands for every key
column of the operand that the operator does not name, and `x` holds the
operand's value.

| Operator                         | SQL                                                                                           | polars                                                                 |
| -------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `sum(x, over=d)`                 | `SELECT rest, SUM(value) FROM x GROUP BY rest`                                                | `x.group_by(rest).agg(pl.col('value').sum())`                          |
| `sum(x)`                         | `SELECT SUM(value) FROM x`                                                                    | `x.select(pl.col('value').sum())`                                      |
| `sum(x, over=d, by=R[c])`        | `SELECT rest, R.c, SUM(value) FROM x JOIN R ON x.d = R.d GROUP BY rest, R.c`                  | `x.join(R, on=d).group_by([*rest, c]).agg(pl.col('value').sum())`      |
| `at(x, by=R[c])`                 | `SELECT R.key, rest, value FROM R JOIN x ON R.c = x.c`                                        | `R.join(x, on=c)`                                                      |
| `shift(x, along=d, offset=n)`    | `LAG(value, n) OVER (PARTITION BY rest ORDER BY d)`, and the first `n` rows are dropped       | `pl.col('value').shift(n).over(rest, order_by=d)`, then drop the nulls |
| `shift(…, edge=v)`               | `LAG(value, n, v) OVER (PARTITION BY rest ORDER BY d)`                                        | `pl.col('value').shift(n, fill_value=v).over(rest, order_by=d)`        |
| `sum_back(x, along=d, window=n)` | `SUM(value) OVER (PARTITION BY rest ORDER BY d ROWS BETWEEN n - 1 PRECEDING AND CURRENT ROW)` | `pl.col('value').rolling_sum(n, min_samples=1).over(rest, order_by=d)` |

The SQL is a reading aid, not a lowering. Four points need more than the query
in the table:

- **`shift` and `sum_back` count positions of the dimension, not rows of the
  table.** `LAG` steps over a missing row to the row before it. `shift` reads the
  missing row instead, and the result is absent there. The window functions
  above are exact only where every position has a row.
- **`edge='wrap'` has no window-function spelling.** In `shift`, the first
  position reads the last one. In `sum_back`, the window reaches around to the
  end of the dimension.
- **`window=p` has no frame spelling.** `p` is a parameter, so each entity has
  its own window length. A SQL frame takes a constant. Write it as a self-join
  on the positions from `d - p + 1` to `d`.
- **`within=R[c]` adds the group to the partition.** `shift(…, within=R[c])` is
  `PARTITION BY rest, R.c`, after a join with `R`.

The table covers `sum`, `at`, `shift` and `sum_back`. The
[operator reference](../reference/language/operators.md) holds every operator,
and says what each one accepts and refuses.

## Why there is no join operator

The language has no general `join`. A join opens a key column for each column it
sums away, and that column is not a dimension, so no declaration can carry it.
`sum(by=)` and `at(by=)` join and close the column in one call. The
[limits](limits.md#deliberate-non-primitives) page holds the refusal and its
rewrite.

So a spec combines two tables only through arithmetic, `sum(by=)` and
`at(by=)`. A query outside the language, such as a pivot, a string operation or
a join on a computed column, is [data preparation](limits.md#what-counts-as-data-preparation). It happens
before the data reaches the spec.
