<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Dimensions

A **dimension** is a set of labels that entries are indexed by, such as
`snapshot` or `generator`. `sum` reduces over a dimension. A map from one
dimension onto another is a [relation](relations.md).

## `dimensions`

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
```

Every dimension named anywhere in the file is declared here.

| Field         |                                                       |                 |
| ------------- | ----------------------------------------------------- | --------------- |
| `dtype`       | `float`, `int`, `str`, `datetime`                     | default `str`   |
| `ordered`     | whether the order of the members is part of the model | default `false` |
| `description` | free text                                             | default `null`  |

The members of a dimension arrive with the data, in the order the table gives
them. Everything indexed by the dimension is matched to its members by label.

## Order

A construct may read the order of a dimension **only** when the dimension is
declared `ordered: true`. A snapshot comes after the one before it. A generator
does not come after another generator, so a file that steps from one generator
to the next would read the row order of a data table. Five constructs read the
order, and each needs its dimension declared `ordered: true`:

| Construct                                                                          | Reads                            |
| ---------------------------------------------------------------------------------- | -------------------------------- |
| [`shift(x, along=d, offset=n)`](operators.md#shift), in an expression or a `where` | the member `n` positions back    |
| [`sum_back(x, along=d, window=n)`](operators.md#sum_back)                          | the last `n` members             |
| [`position(d)`](expressions.md#position)                                           | where a member sits along `d`    |
| [`piecewise:`](piecewise.md) with `over: d`                                        | which breakpoints are neighbours |
| [`sos:`](piecewise.md#sos) with `type: 2` and `along: d`                           | which members are consecutive    |

The loader refuses any of them along a dimension that is not ordered:

```text
Constraint 'ramp': shift(along=snapshot) reads the order of 'snapshot', which is not declared ordered, so the order would come from the row order of the data. Declare 'snapshot: {ordered: true}' under dimensions:.
```

A `dtype` does not make a dimension ordered: an `int` dimension may number
things that have no order. An `sos` entry with `type: 1` reads no order, and
`edge='wrap'` makes one `shift` cyclic without changing the dimension.

To decide whether a column of data is a dimension, a relation or a parameter,
read [declare a column of data](../../howto/declare-a-column.md).
