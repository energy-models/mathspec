<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Dimensions

A **dimension** is a set of labels that declarations are indexed by, such as
`snapshot` or `generator`. `sum` reduces over a dimension. A map from one
dimension onto another is a [relation](relations.md).

## `dimensions`

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
```

Every dimension named anywhere in the file is declared here.

| Field         |                                   |                |
| ------------- | --------------------------------- | -------------- |
| `dtype`       | `float`, `int`, `str`, `datetime` | default `str`  |
| `description` | free text                         | default `null` |

The members of a dimension arrive with the data, in the order the table gives
them. [`shift`](operators.md#shift), `sum_back` and `position()` count along
that order, and everything indexed by the dimension is matched to its members
by label.

To decide whether a column of data is a dimension, a relation or a parameter,
read [declare a column of data](../../howto/declare-a-column.md).
