<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Relations as linear maps

A [`sum`](../reference/language/operators.md#sum) or an
[`at`](../reference/language/operators.md#at) through a table that maps
coordinates ([a relation](../reference/language/relations.md)) is the product
of a matrix and a vector. The relations page describes the same sum in
database words, "joined on" and "grouped by". The matrix form is the sum in
the form a paper uses.

Every formula below is over this spec:

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

`zonal` contains a sum of `p` through `gen_zone`, and `looked_up` a lookup of
`zone_cap` through `gen_zone`. The spec loads.

## The indicator of a relation

A relation with columns over the dimensions $`D_1, \dots, D_n`$ is a set of
rows, so it is a subset $`R \subseteq D_1 \times \dots \times D_n`$. Its
**indicator** $`\mathbf{1}_R`$ is $`1`$ at a row of the table and $`0`$
everywhere else. [`key:`](../reference/language/relations.md#relations)
declares that the set has one row per combination of key labels (a key
tuple). So a relation with `key: K` and `values: V` is the set of pairs
$`(k, f(k))`$ of a function $`f: K \to V`$ (its graph), and

```math
\mathbf{1}_R(k, v) = [\, f(k) = v \,].
```

The bracket is $`1`$ where $`f(k) = v`$ and $`0`$ elsewhere.

By default the function has a value at every key tuple (it is total). With data attached, the tool that builds the model
([an engine](../reference/glossary.md#tool)) checks for
[one row per key tuple](../reference/language/relations.md#the-data-contract).
The engine refuses a key tuple with no row.
Under [`missing: absent`](../reference/language/relations.md#missing), the
function has no value at a key tuple with no row (it is partial). With $`\mathcal{G}`$, $`\mathcal{T}`$ and $`\mathcal{Z}`$ the sets of
generators, snapshots and zones, `gen_zone` in the spec above is the graph of
a partial $`f: \mathcal{G} \times \mathcal{T} \to \mathcal{Z}`$.

A relation with no `values:`
([a bare relation](../reference/glossary.md#bare-relation)) is a subset with no function behind it. So one generator may sit in several
rows, each with its own zone. By default a bare relation also lists every key tuple, so one
that does not must declare `missing: absent`.

Every column of a bare relation is in its key, so the relation has no value
column for `at` to read. At load, mathspec refuses `at` through a bare relation.

## A join and group-by as a contraction

`sum(p, over=generator, by=gen_zone[zone])` multiplies the indicator of
`gen_zone` by `p`, and sums over the one index that they share and that the
call lists in `over=`:

```math
y_{t,z} = \sum_{g} \mathbf{1}_R(g, t, z) \cdot p_{t,g} = \sum_{g \,:\, f(g,\,t) = z} p_{t,g}
```

The typesetter [prints](../reference/notation.md) the right-hand form. The left-hand form is a sum over an index that two factors share (a
**tensor contraction**). The relations page describes each column of the
relation by two properties. Each pair of properties is a position that an
index can take in the formula:

| On the relations page                                         | In the formula                                                       |
| ------------------------------------------------------------- | -------------------------------------------------------------------- |
| joined on, the column in `over=`                              | $`g`$ is on both factors and summed. It is not in the result.        |
| grouped by, the column in `by=`                               | $`z`$ is on the indicator alone and not summed. It is in the result. |
| joined on and grouped by, a key column the call does not name | $`t`$ is on both factors and not summed. It is in the result.        |
| neither, a value column the call does not name                | The column is not in the formula, and the sum does not use it.       |

The result has the **free indices**, which are the indices that are not
summed. They are the indices of the operand and of the indicator together,
less the summed one.

mathspec refuses a sum at load when the sum breaks one of two conditions, and the
formula needs each of them:

- The operand has every column joined on, including each key column that the
  call does not name. Without `snapshot`, $`t`$ would sit on the indicator
  alone, which is the grouped position, and a sum lists the columns it groups
  by in `by=`.
- The operand has no column grouped by. Otherwise $`z`$ would sit on both
  factors and not be summed. Then the product would match the two occurrences
  of $`z`$, and the result would gain no extra index (an axis) for $`z`$. You
  write that match outside the operator, as in
  `zone_cap * sum(p, over=generator, by=gen_zone[zone])`.

At each $`t`$, the matrix $`M_t[z, g] = \mathbf{1}_R(g, t, z)`$ has one row
per zone and one column per generator, with entries of zero and one, and
$`y_t = M_t\, p_t`$. Over all snapshots, the key column that the call does not name makes the
matrix zero outside one block per snapshot (**block-diagonal**). A relation keyed by one column has one block.

## A lookup through a relation

`at(zone_cap, by=gen_zone[zone])` joins the same table, and sums over the
other index:

```math
w_{t,g} = \sum_{z} \mathbf{1}_R(g, t, z) \cdot \mathrm{zone\_cap}_{t,z} = \mathrm{zone\_cap}_{t,\, f(g,\,t)}
```

The indicator and the contraction are the same as for the sum, so the same
free-index rule sets the dimensions of the result. As a matrix, `at` is
$`M_t^{\mathsf{T}}`$. The key tuples where $`f`$ has a value are its domain. Because $`R`$ is the
graph of $`f`$, the sum over $`z`$ has exactly one term at each key tuple in
the domain.
It has no term elsewhere. So the contraction is the composition
$`\mathrm{zone\_cap} \circ f`$, which is a **pullback**: the value of
`zone_cap` at $`f(g, t)`$.

That one term is the difference between `at` and `sum`, and mathspec decides
the difference at load from the key alone. Where the columns a call groups by
include the whole key, every group is one row. An `at` is evaluated at the
whole key, so each of its groups is always one row. A `sum` with one row per
group adds up nothing, so mathspec refuses it, and the message suggests `at`.

The two maps are **adjoint**. The sum of elementwise products (the inner
product) does not change when the matrix moves to the other side, flipped
over its diagonal (its transpose). With $`x`$ over generators and $`v`$ over
zones at one snapshot $`t`$,

```math
\langle M_t x, v \rangle = \sum_{z} v_z \sum_{g} \mathbf{1}_R(g, t, z)\, x_g = \sum_{g} x_g \sum_{z} \mathbf{1}_R(g, t, z)\, v_z = \langle x, M_t^{\mathsf{T}} v \rangle.
```

Both maps contract the same indicator. So the compiled spec
([the program](../reference/program.md)) has `at` as a `Join` node, and
`sum(by=)` as the same `Join` under a `Sum`.

## Why the language has no join operator

Two operators, `sum(by=)` and `at(by=)`, are better here than a `join` and a
`sum`. A separate `join` operator would return the product before the sum, with an
axis for the column grouped by, $`z`$. `sum(by=)` and `at(by=)` already add
that axis and remove it in one call, so a `join` would add nothing that a file
cannot state. mathspec refuses `join` as an unknown operator, and the message
lists the operators that exist.

## How an engine evaluates the product

The file states the formula, and an engine decides how to evaluate it. A
table lists the **support** of $`\mathbf{1}_R`$, which is the set of rows
where $`\mathbf{1}_R`$ is $`1`$. An engine can multiply a matrix stored that
way by a vector in two steps:

1. The engine pairs each row of the table with each row of the operand that
   agrees on every shared index, here $`g`$ and $`t`$. That is a join on the columns joined on that
   matches equal values (an inner equi-join). Each
   pair is one nonzero product $`1 \cdot p_{t,g}`$, and it takes the label of
   the column grouped by, $`z`$.
2. The engine adds the pairs that agree on the free indices, here $`(t, z)`$.
   That is a sum grouped by the dimensions of the result.

For `at`, an engine runs step 1 only, because with one row per group no two
pairs have the same coordinate. Where several $`(g, t)`$ share one $`z`$, the
engine gets several rows for that $`z`$. Those rows are a column of
$`M_t^{\mathsf{T}}`$ with several ones.

So the database steps and the matrix product are one computation. The join step has only the entries where $`\mathbf{1}_R`$ is $`1`$, and the group-by is the
$`\sum`$.

## Empty groups and missing values

At two kinds of position the matrix product has no term.

- An empty group is an empty sum. With data attached, a zone that no
  generator maps to at $`t`$ has $`y_{t,z} = 0`$, and the row is
  $`0 \le \mathrm{zone\_cap}_{t,z}`$. The row has no variable. It exists once the data is attached. At load,
  mathspec refuses only a constraint whose expression has no variable, and the
  expression of `zonal` has `p`.
- Outside the domain of $`f`$ there is no value.
  $`\mathrm{zone\_cap} \circ f`$ is undefined where $`f`$ is undefined, so
  `at` has no row there (it is [absent](../reference/glossary.md#absence)), and
  [absence spreads](../reference/language/absence.md#how-absence-travels) to
  the row. Under the default, no key tuple is outside the domain. With
  [`where: gen_zone`](../reference/language/absence.md#where), `looked_up`
  declares the domain of $`f`$ in the spec, so a reader sees which rows exist
  without opening the data.

## Partitions and tests

The other two uses of a relation, a
[partition](../reference/language/relations.md#partitions) and a
[test](../reference/language/relations.md#tests), are not matrix products. An
operator with `within=`, such as `shift`, works separately on each set of
members that $`f`$ sends to one value (a fibre). The dimensions of the result
do not change. With `season_of: { key: snapshot, values: season }`,
`shift(soc, along=snapshot, offset=1, edge='wrap', within=season_of[season])`
steps back within each season:

Each season is one fibre of `season_of`, so no value crosses from winter to
summer.

A test is the indicator itself. In a `where`, the name of a
relation is $`\mathbf{1}_R`$ at the coordinate of the entry.

You can now judge the dimensions of a sum or an `at` through a relation, and
why the language has no `join` operator.

!!! info "See also"

    - [relations](../reference/language/relations.md), for every key a relation
      accepts
    - [how dimensions combine](../reference/language/expressions.md#how-dimensions-combine),
      for the rule that sets the free indices of every expression
    - [how absence travels](../reference/language/absence.md#how-absence-travels),
      for figures of the rows that absence removes
    - [sums through a relation](../reference/language/relations.md#sums-through-a-relation),
      for the message mathspec prints when it refuses a sum with one row per group
    - [constructs the language already has](limits.md#constructs-the-language-already-has),
      for the refused `join` operator and what you write instead
    - [the notation page](../reference/notation.md), for how the typesetter
      prints each use
