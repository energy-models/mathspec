<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Dimensions

A **dimension** is a set of labels that entries are indexed over, such as the
hours in `snapshot` or the units in `generator`.
This page lists the keys a dimension accepts, the closed label lists of
`one_of`, and the rule for the order of a dimension.

## `dimensions`

Each key under `dimensions:` declares one dimension, and every dimension that
the file uses anywhere is declared here.

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  load: { dims: [snapshot] }
variables:
  dispatch: { dims: [snapshot, generator] }
constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load
```

`snapshot` has integer labels in a fixed order, and `generator` has string
labels in no order. `sum(dispatch, over=generator)` removes `generator`, so
`power_balance` has one row per snapshot.

| Key           | What it sets                                                                | Default |
| ------------- | --------------------------------------------------------------------------- | ------- |
| `dtype`       | the type of a label: `float`, `int`, `str` or `datetime`                    | `str`   |
| `one_of`      | [the labels a `str` dimension allows](#one_of)                              | `null`  |
| `ordered`     | whether the order of the labels is part of the spec ([`ordered`](#ordered)) | `false` |
| `description` | free text, which the typeset legend lists                                   | `null`  |

The file does not list the labels themselves. They arrive with the data, in
the order that the data table lists them. With data attached, a piece of
software that reads a spec ([a tool](../glossary.md#tool)) matches every entry
indexed over the dimension to the labels.

mathspec loads a dimension that no entry uses, and for that dimension
`python -m mathspec check` prints a message that does not refuse the file
([advice](../glossary.md#advice)).

A map from one dimension onto another is a [relation](relations.md), not a
dimension.

## `one_of`

`one_of` lists every label that a `str` dimension allows. With `one_of`
declared, mathspec checks at load the spelling of each label that a condition
compares against.

```yaml
dimensions:
  carrier: { dtype: str, one_of: [ccgt, ocgt, wind] }
  generator: { dtype: str }
relations:
  carrier_of: { key: generator, values: carrier }
variables:
  p: { dims: [generator], where: "carrier_of == 'wind'" }
```

`p` exists only at the generators whose carrier is `wind`. The relation
`carrier_of` maps each generator to one carrier, and `one_of` makes `wind` one of
three allowed labels.

A `one_of` list meets four rules:

- Each label is a string, so mathspec refuses a number such as `2030` and
  accepts the string `'2030'`.
- The list has at least one label, and each label once.
- The `dtype` is `str` by default, so `carrier: { one_of: [ccgt, ocgt, wind] }`
  declares the same dimension. mathspec refuses a `one_of` with any other
  `dtype`.
- In every other rule, the dimension is an ordinary `str` dimension.

At load, mathspec refuses a [condition](expressions.md#conditions) that
compares the dimension, or a relation column over it, against a label that is
not in the list. With `carrier_of == 'gnrtr'` in place of `'wind'` above, mathspec prints:

```text
Variable 'p': 'gnrtr' is not a label of 'carrier', which allows only ['ccgt', 'ocgt', 'wind']. Write one of them, or add 'gnrtr' to the one_of of 'carrier'.
```

mathspec lists the allowed labels and suggests two rewrites.

With data attached, a tool refuses a label
outside the list, in the table of the dimension and in every relation column
over it.

Only a dimension takes `one_of`, and a `one_of` key on a parameter is refused
as an unknown key.

## `ordered`

`ordered: true` makes the order of the labels part of the spec. Five
constructs use the order of a dimension, and each one requires `ordered: true`:

| Construct                                                                            | What it uses                     |
| ------------------------------------------------------------------------------------ | -------------------------------- |
| [`shift(x, along=d, offset=n)`](operators.md#shift), in an expression or a condition | the label `n` positions back     |
| [`sum_back(x, along=d, window=n)`](operators.md#sum_back)                            | the last `n` labels              |
| [`position(d)`](expressions.md#position)                                             | where a label sits along `d`     |
| [`piecewise:`](piecewise.md) with `over: d`                                          | which breakpoints are neighbours |
| a [special ordered set (`sos:`)](piecewise.md#sos) with `type: 2` and `along: d`     | which labels are consecutive     |

The ramp constraint below steps back one snapshot, and `snapshot` is not
declared ordered:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  ramp_limit: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator] }
constraints:
  ramp:
    dims: [snapshot, generator]
    expression: p - shift(p, along=snapshot, offset=1) <= ramp_limit
```

```text
Constraint 'ramp': shift(along=snapshot) reads the order of 'snapshot', which is not declared ordered, so the order would come from the row order of the data. Declare 'snapshot: {ordered: true}' under dimensions:.
```

The file loads once `snapshot` is declared `{ dtype: int, ordered: true }`.
With snapshots `1`, `2` and `3` attached, `shift` has a row at snapshots `2`
and `3` and none at `1`.

An `int` dimension is not ordered unless it declares `ordered: true`.

An `sos` entry of `type: 1` uses no order, so it needs no `ordered: true`.

[`edge='wrap'`](operators.md#shift) makes one `shift` cyclic, so that the first
label steps back to the last. `edge='wrap'` does not change the dimension, and
the dimension still needs `ordered: true`.

!!! info "See also"

    - [choose between a dimension, a relation and a parameter](../../howto/declare-a-column.md)
      for a column of data.
