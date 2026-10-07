<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Dimensions

A **dimension** is an axis of the spec, such as `snapshot` or `generator`.
Entries are indexed by it, and `sum` reduces over it. A map from one axis
onto another is a [relation](relations.md).

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

**Only an ordered dimension has an order a construct may read.** A snapshot
comes after the one before it. A generator does not come after another
generator, and a file that steps from one to the next would read the row order
of a data table. Five constructs read the order, and each needs its dimension
declared `ordered: true`:

| Construct                                                                          | Reads                            |
| ---------------------------------------------------------------------------------- | -------------------------------- |
| [`shift(x, along=d, offset=n)`](operators.md#shift), in an expression or a `where` | the member `n` positions back    |
| [`sum_back(x, along=d, window=n)`](operators.md#sum_back)                          | the last `n` members             |
| [`position(d)`](expressions.md#position)                                           | where a member sits along `d`    |
| [`piecewise:`](piecewise.md) with `over: d`                                        | which breakpoints are neighbours |
| [`sos:`](piecewise.md#sos) with `type: 2` and `along: d`                           | which members are consecutive    |

The loader refuses any of them along a dimension that is not ordered:

```text
Constraint 'ramp': shift(along=snapshot) reads the order of 'snapshot', which is not declared ordered, so the order it read would be the row order of the data. Declare the order part of the model with 'snapshot: {ordered: true}' under dimensions:.
```

A `dtype` does not make a dimension ordered: an `int` dimension may number
things that have no order. An `sos` entry with `type: 1` reads no order, and
`edge='wrap'` makes one `shift` cyclic without changing the dimension.

Whether to declare a column of data as a dimension, a relation or a parameter
is decided in [declare a column of data](../../howto/declare-a-column.md).
