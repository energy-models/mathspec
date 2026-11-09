<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Understanding a spec in SQL and dataframe terms

This page describes the declarations and operators of the specification of an
optimisation model ([a spec](../reference/glossary.md#spec)) as tables and
queries. It is for a reader who thinks in SQL, or in a dataframe library such as
[polars](https://pola.rs) or [pandas](https://pandas.pydata.org). The rules
themselves are in the [language reference](../reference/language/index.md).

Every query below is over this spec, in which generators meet the load at their
bus in each snapshot:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
  bus: { dtype: str }
relations:
  gen_bus: { key: generator, values: bus }
parameters:
  load: { dims: [snapshot, bus] }
  capacity: { dims: [generator] }
  cost: { dims: [generator], missing: 0 }
  ramp_limit: { dims: [generator] }
variables:
  dispatch:
    dims: [snapshot, generator]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }
constraints:
  power_balance:
    dims: [snapshot, bus]
    expression: sum(dispatch, over=generator, by=gen_bus[bus]) == load
  ramp_up:
    dims: [snapshot, generator]
    expression: dispatch - shift(dispatch, along=snapshot, offset=1) <= ramp_limit
objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

`dispatch` is the output of each generator in each snapshot. `power_balance`
requires the output at each bus to meet the load, and `ramp_up` limits how fast a
generator raises its output. The spec loads.

## Declarations

A [dimension](../reference/language/dimensions.md) is the domain of a key
column. `generator` is the set of labels that a `generator` column may contain.
One point of the dimensions of an entry, such as one generator in one snapshot,
is a **coordinate**: one value of each key column.

A [parameter](../reference/language/parameters-variables-constraints.md#parameters)
is a table indexed by its `dims`. `load` is a table with the columns
`snapshot`, `bus` and one value column, and its primary key is
`(snapshot, bus)`.

A gap in the data is a row that is not in the table. With data attached, a tool
refuses a null value, so leave the row out instead of writing a null. The
[`missing:`](../reference/language/absence.md#missing-on-a-parameter) key of the
parameter sets what the gap means.

A [variable](../reference/language/parameters-variables-constraints.md#variables)
and a [constraint](../reference/language/parameters-variables-constraints.md#constraints)
are tables of the rows that a tool builds. `dispatch` has one decision variable
per coordinate of `(snapshot, generator)`, and `power_balance` has one row per
coordinate of `(snapshot, bus)`.

A [relation](../reference/language/relations.md) is a table whose `key:` is its
primary key. `gen_bus: { key: generator, values: bus }` is a table with two
columns and one row per generator. Under the default `missing: refused`, every
generator needs a row. Under [`missing: absent`](../reference/language/relations.md#missing),
a generator may have no row.

## Absence

A [`where:`](../reference/language/absence.md#where) is a SQL `WHERE` on the
rows that a declaration builds. Where `capacity` is `0`, `dispatch` has no
decision variable, so the coordinate is [absent](../reference/glossary.md#absence).
Absent is different from zero, because zero is a value. An expression that uses
an absent coordinate has no row there either.

Arithmetic is an inner join on the shared key columns. `dispatch * cost` joins
the table of `dispatch` and the table of `cost` on `generator`. A key column
that only one side has is crossed, so `dispatch * cost` has the columns
`snapshot` and `generator`. Where either side has no row, the result has no
row. Under the default `missing: refused`, a parameter has every row, so the
join drops only the rows that a `where:` or a `missing: absent` left out.

A `missing:` value turns the join into a left join that fills the gap. `cost`
declares `missing: 0`, so a generator with no `cost` row has a cost of `0`, as
`COALESCE(cost.value, 0)` after a `LEFT JOIN` gives.

## Operators

The table covers [`sum`](../reference/language/operators.md#sum),
[`at`](../reference/language/operators.md#at),
[`shift`](../reference/language/operators.md#shift) and
[`sum_back`](../reference/language/operators.md#sum_back), and each one is one
query shape. In the table, `x` is the table of the operand and `value` is its
value column. `rest` is every key column of `x` that the operator does not name.

| Operator                         | SQL                                                                                           | polars                                                                 |
| -------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `sum(x, over=d)`                 | `SELECT rest, SUM(value) FROM x GROUP BY rest`                                                | `x.group_by(rest).agg(pl.col('value').sum())`                          |
| `sum(x)`                         | `SELECT SUM(value) FROM x`                                                                    | `x.select(pl.col('value').sum())`                                      |
| `sum(x, over=d, by=R[c])`        | `SELECT rest, R.c, SUM(value) FROM x JOIN R ON x.d = R.d GROUP BY rest, R.c`                  | `x.join(R, on=d).group_by([*rest, c]).agg(pl.col('value').sum())`      |
| `at(x, by=R[c])`                 | `SELECT R.key, rest, value FROM R JOIN x ON R.c = x.c`                                        | `R.join(x, on=c)`                                                      |
| `shift(x, along=d, offset=n)`    | `LAG(value, n) OVER (PARTITION BY rest ORDER BY d)`, and the first `n` rows are dropped       | `pl.col('value').shift(n).over(rest, order_by=d)`, then drop the nulls |
| `shift(…, edge=v)`               | `LAG(value, n, v) OVER (PARTITION BY rest ORDER BY d)`                                        | `pl.col('value').shift(n, fill_value=v).over(rest, order_by=d)`        |
| `sum_back(x, along=d, window=n)` | `SUM(value) OVER (PARTITION BY rest ORDER BY d ROWS BETWEEN n - 1 PRECEDING AND CURRENT ROW)` | `pl.col('value').rolling_sum(n, min_samples=1).over(rest, order_by=d)` |

The SQL column uses the window functions of the SQL:2011 standard, which
PostgreSQL, DuckDB and SQLite run as written. The polars column needs polars
1.21 or later, the first release with `min_samples=`.

The queries state what an operator means, not how a tool computes it. They are
exact except in four cases:

- `shift` and `sum_back` count positions of the dimension, not rows of the
  table. `LAG` steps over a missing row to the row before it. Where the position
  before has no row, the result of `shift` is absent instead.
- `edge='wrap'` has no window-function form. In `shift`, the first position
  takes the value of the last. In `sum_back`, a window that reaches past the
  start continues from the end of the dimension.
- A `window=` given as a parameter, such as `window=min_up`, has no frame form.
  Each entity then has its own window length, and a SQL frame takes a
  constant. Write it as a self-join on the positions from `d - min_up + 1` to
  `d`.
- `within=R[c]` adds the group to the partition. After a join with `R`,
  `shift(…, within=R[c])` is `PARTITION BY rest, R.c`.

## Queries outside the language

A spec combines two tables only through arithmetic, `sum(by=)` and `at(by=)`.
Each of `sum(by=)` and `at(by=)` joins with a relation and drops the key column
of the join in the same call. A separate `join` would return a table with a key
column that no dimension declares, so mathspec has no `join` operator.

You run any other query, such as a pivot, a string operation or a join on a
computed column, before the data is attached. That work is
[data preparation](../reference/glossary.md#data-preparation).

You can now read each line of a spec as a query, and judge where a literal
query differs from the spec.

!!! info "See also"

    - [operators](../reference/language/operators.md), for every operator and
      what it accepts and refuses
    - [how dimensions combine](../reference/language/expressions.md#how-dimensions-combine),
      for the key columns of every expression before any data is attached
    - [how absence travels](../reference/language/absence.md#how-absence-travels),
      for how a sum leaves out an absent term
    - [why the language has no join operator](relations-as-linear-maps.md#why-the-language-has-no-join-operator),
      for the same argument in linear algebra
    - [data preparation](limits.md#data-preparation), for the rule on where a
      quantity is computed
