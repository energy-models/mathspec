<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Relations as linear maps

You can read a `sum` or an `at` through a
[relation](../reference/language/relations.md) as the product of a matrix and
a vector. The join and the group-by on the relations page are the two steps of
that product, and the product is the sum that a paper prints. Read on if
"joined on" and "grouped by" read to you as database words, and you want the
math behind them. Every formula below reads this spec:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
  zone: { dtype: str }
relations:
  gen_zone: { key: [generator, snapshot], values: zone, missing: absent }
parameters:
  zone_cap: { dims: [snapshot, zone] }
variables:
  p: { dims: [snapshot, generator] }
constraints:
  zonal:
    dims: [snapshot, zone]
    expression: sum(p, over=generator, by=gen_zone[zone]) <= zone_cap
  looked_up:
    dims: [snapshot, generator]
    where: gen_zone
    expression: p <= at(zone_cap, by=gen_zone[zone])
objective:
  sense: minimize
  expression: sum(p)
```

## The indicator of a relation

A relation with columns over the dimensions $`D_1, \dots, D_n`$ is a set of
rows, so it is a subset $`R \subseteq D_1 \times \dots \times D_n`$. Its
**indicator** $`\mathbf{1}_R`$ is $`1`$ at a row of the table and $`0`$
everywhere else. `key:` says that the set has one row per key tuple. So a
relation with `key: K` and `values: V` is the graph of a function
$`f: K \to V`$, and

```math
\mathbf{1}_R(k, v) = [\, f(k) = v \,].
```

By default the function is total: when the data is attached, a key tuple with
no row is [refused](../reference/language/relations.md#the-data-contract).
Under `missing: absent`, as in the spec above, the function is partial: it has
no value at a key tuple with no row. A bare relation is a subset, with no
function behind it. In the spec above, `gen_zone` is the graph of
$`f: \mathcal{G} \times \mathcal{T} \to \mathcal{Z}`$. The
[data contract](../reference/language/relations.md#the-data-contract) makes
sure of this, because the loader checks for one row per key tuple when the
data is attached.

## A join and group-by as a contraction

`sum(p, over=generator, by=gen_zone[zone])` multiplies two arrays, and sums
over the one index that they share and that the call names:

```math
y_{t,z} = \sum_{g} \mathbf{1}_R(g, t, z) \cdot p_{t,g} = \sum_{g \,:\, f(g,\,t) = z} p_{t,g}
```

The typesetter [prints](../reference/notation.md) the right-hand form. The
left-hand form is a **tensor contraction**, which multiplies arrays and sums
over an index they share. The relations page asks two questions of each
column, and each pair of answers is a position that an index can take in the
formula:

| The relations page says          | In the formula                                                       |
| -------------------------------- | -------------------------------------------------------------------- |
| joined on, the column in `over=` | $`g`$ is on both factors and summed. The result loses it.            |
| grouped by, the column in `by=`  | $`z`$ is on the indicator alone and not summed. The result gains it. |
| joined on and grouped by         | $`t`$ is on both factors and not summed. The result keeps it.        |
| neither                          | a value column not in the formula. Nothing reads it.                 |

The result carries the **free indices**, which are the indices that are not
summed. They are the indices of the operand and of the indicator together,
less the summed one, which is `(dims(x) − joined) ∪ grouped`. That is the rule
in the [expressions
reference](../reference/language/expressions.md#how-dimensions-combine), and
`join_dims` in `src/mathspec/dimensions.py` computes it. The loader refuses a
sum that breaks one of three conditions, and the formula needs each of them:

- The operand carries every column joined on, or there is nothing to match.
- The operand carries every key column that the call does not name. Otherwise
  $`t`$ would sit on the indicator alone, which is the grouped position, and a
  sum names the columns it groups by in `by=`.
- The operand carries no column grouped by. Otherwise $`z`$ would sit on both
  factors and not be summed, so the product would match the two occurrences of
  $`z`$ and not add an axis. You write that match outside the operator:
  `load * sum(p, over=generator, by=gen_bus[bus])`.

So "joined on" and "grouped by" are the two positions that an index can take
in the summation convention, applied to one product. The relations page has no
rule beyond this product.

The key column that the call does not name makes the matrix
**block-diagonal**, with one block for each value of that column. At each
$`t`$, $`M_t[z, g] = \mathbf{1}_R(g, t, z)`$ is a
$`|\mathcal{Z}| \times |\mathcal{G}|`$ matrix of zeros and ones, and
$`y_t = M_t\, p_t`$. A relation keyed by one column has one block.

## A join alone

`at(zone_cap, by=gen_zone[zone])` joins the same table, and binds the other
index:

```math
w_{t,g} = \sum_{z} \mathbf{1}_R(g, t, z) \cdot \mathrm{zone\_cap}_{t,z} = \mathrm{zone\_cap}_{t,\, f(g,\,t)}
```

The indicator and the contraction are the same, so the same free-index rule
gives the dimensions of the result. As a matrix it is $`M_t^{\mathsf{T}}`$.
Because $`R`$ is the graph of $`f`$, the sum over $`z`$ has exactly one term
where $`(g, t)`$ is in the domain of $`f`$, and no term elsewhere. So the
contraction is the composition $`\mathrm{zone\_cap} \circ f`$, which is a
**pullback**: it reads `zone_cap` at the value of $`f`$.

That one term is the difference between `at` and `sum`, and the loader decides
it from the key alone. Where the columns a call groups by hold the whole key,
every group is one row, and the group-by adds nothing.
`JoinColumns.one_row_per_group` in `src/mathspec/program.py` names this case.
A `sum` with one row per group adds up nothing, so the loader refuses it and
names `at`. An `at` reads value columns at the whole key, so each of its
groups is always one row. The
[relations page](../reference/language/relations.md#sums-through-a-relation)
quotes the message.

The two maps are **adjoint**: an inner product does not change when the matrix
moves to the other side as its transpose. For
`gen_bus: { key: generator, values: bus }`, with $`x`$ over generators and
$`y`$ over buses,

```math
\langle M x, y \rangle = \sum_{b} y_b \sum_{g} \mathbf{1}_R(g, b)\, x_g = \sum_{g} x_g \sum_{b} \mathbf{1}_R(g, b)\, y_b = \langle x, M^{\mathsf{T}} y \rangle,
```

which is why the program holds `at` as a `Join` node, and `sum(by=)` as the
same `Join` under a `Sum`. The join keeps the column that the sum removes as
an axis of its own, `Axis('generator', Column('gen_zone', 'generator'))`. That
axis runs over `generator` and stands for the column of the relation, and the
`Sum` sums over it. So a map into its own dimension, which removes one
dimension and adds the same one, still has two separate axes between the join
and the sum.

A bare relation has the same matrix, but no function behind it. A column of
$`M`$ may then hold several ones, so the join returns several rows for one
row of the operand, and no group is one row. That is why `at` through a bare
relation is refused.

## The join and the aggregate

The file fixes the formula, and an engine decides how to evaluate it. A table
stores $`\mathbf{1}_R`$ as its **support**, which is the set of rows where it
is $`1`$. The product of a matrix stored that way and a vector takes two steps:

1. Pair each row of the table with each row of the operand that agrees on
   every shared index, here $`g`$ and $`t`$. That is an inner equi-join (a
   join that matches equal values) on the columns joined on. Each pair is one
   nonzero product $`1 \cdot p_{t,g}`$, and it takes the label of the column
   grouped by, $`z`$.
2. Add the pairs that agree on the free indices, here $`(t, z)`$. That is a
   group-by on the dimensions of the result, with a sum.

lpspec, the reference engine, runs these two steps. `join_relation` in
`src/lpspec/relational/engines/polars/relations.py` is step 1. It runs one
inner join on the dimensions joined on. A select then drops the dimensions not
grouped by, and renames the column grouped by to the name of its dimension.
Step 2 is the last aggregate in `assembly.py`: a `group_by` over the
coordinates of the row, with `sum`. It runs once per constraint, after every
term is in place. Until then, lpspec keeps a sum of linear terms as a list of
terms, and adds two sums by appending one list to the other. `at` runs step 1 against the
same table and needs no step 2, because with one row per group no two pairs
have the same coordinate. Where several $`(g, t)`$ share one $`z`$, the join
returns several rows for that $`z`$, which is a column of $`M^{\mathsf{T}}`$
that holds several ones.

So the database steps and the matrix product are one computation. The join
multiplies by an entry of $`\mathbf{1}_R`$, which is $`1`$ or absent, and the
group-by is the $`\sum`$.

## Empty groups and missing values

At two kinds of position the formula has no variable to build, and there the
model that an engine builds is not the matrix product.

- An empty group is an empty sum. A zone that no generator maps to at $`t`$
  has $`y_{t,z} = 0`$, and the row reads $`0 \le \mathrm{zone\_cap}_{t,z}`$.
  The row names no variable, so an engine [does not build
  it](../reference/language/absence.md#rows-with-no-variable-terms) and
  reports that it left the row out. With `>=`, the row left out would have
  been infeasible.
- Outside the domain of $`f`$ there is no value.
  $`\mathrm{zone\_cap} \circ f`$ is undefined where $`f`$ is undefined, so
  `at` is absent there, and [absence
  spreads](../reference/language/absence.md#how-absence-travels) to the row.
  `where: gen_zone` on `looked_up` writes the domain of $`f`$ into the spec,
  so a reader sees which rows exist without opening the data. Under the
  default, `missing: refused`, the domain is every key tuple, so no key tuple
  is outside it.

## Partitions and tests

The other two uses of a relation do not multiply by $`\mathbf{1}_R`$ and sum.

- A partition steps inside a **fibre**, which is the set of members that
  $`f`$ sends to one value.
  `shift(x, along=snapshot, offset=1, within=season_of[season])` reads the
  neighbour $`t'`$ of $`t`$ with $`f(t') = f(t)`$. The fibres of $`f`$
  partition the axis, and the dimensions do not change.
- A test reads the indicator itself. The name of a relation in a `where`
  evaluates $`\mathbf{1}_R`$ at the coordinate of the entry, and keeps
  the coordinate where $`\mathbf{1}_R`$ is $`1`$.
