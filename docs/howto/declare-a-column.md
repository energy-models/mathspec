<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Choose between a dimension, a relation and a parameter

This guide shows how to choose the declaration for a
[column](../reference/glossary.md#column) of your data, in
the specification of an optimisation model
([a spec](../reference/glossary.md#spec)). The choice depends on what you do
with the column in the spec, not on how you store the column. You need a spec
file and the columns of the data you plan to attach to the spec.

## Look up what you do with the column

Use the first row that fits what you do with the column in the spec:

| In the spec you…                                                                  | For example                                                     | So declare it as                                                                                                        |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| index parameters, variables or constraints over the rows the column lists         | `generator`, `snapshot`                                         | a [`dimension`](../reference/language/dimensions.md)                                                                    |
| look up a label of another dimension, one per row                                 | the bus of each generator                                       | a [`relation`](../reference/language/relations.md) to `bus`, a dimension                                                |
| list which pairs of two dimensions exist, with no value                           | `connection`, the buses a generator may connect to              | a `relation` with no `values:` and [`missing: absent`](../reference/language/relations.md#missing)                      |
| use its numbers in an expression or a bound                                       | `cost` per generator, `availability` per generator and snapshot | a [`parameter`](../reference/language/parameters-variables-constraints.md#parameters) over the dimensions that index it |
| test its values in a [condition](../reference/language/expressions.md#conditions) | `fuel`, `is_committable`                                        | a `str` or `bool` parameter                                                                                             |

## Declare each kind of column

The spec below declares at least one column for each row of the table. Save it as `spec.yaml`:

```yaml title="spec.yaml"
dimensions:
  generator: { dtype: str }
  snapshot: { dtype: int }
  bus: { dtype: str }

relations:
  gen_bus: { key: generator, values: bus }
  connection: { key: [generator, bus], missing: absent }

parameters:
  cost: { dims: [generator] }
  availability: { dims: [generator, snapshot] }
  load: { dims: [snapshot, bus] }
  fuel: { dims: [generator], dtype: str }
  is_committable: { dims: [generator], dtype: bool }

variables:
  dispatch: { dims: [snapshot, generator], bounds: { lower: 0, upper: availability } }
  reserve:
    dims: [snapshot, generator, bus]
    where: connection
    bounds: { lower: 0, upper: availability }

constraints:
  balance:
    dims: [snapshot, bus]
    expression: sum(dispatch, over=generator, by=gen_bus[bus]) == load
  reserve_need:
    dims: [snapshot, bus]
    expression: sum(reserve, over=generator) >= 0.1 * load
  gas_limit:
    dims: [snapshot, generator]
    where: "fuel == 'gas'"
    expression: dispatch <= 0.5 * availability
  min_committed:
    dims: [snapshot, generator]
    where: is_committable
    expression: dispatch >= 0.2 * availability

objective:
  sense: minimize
  expression: sum(cost * dispatch)
```

With data attached, `reserve` exists only for the pairs that `connection`
lists. `gas_limit` and `min_committed` exist only where the tests on `fuel` and
`is_committable` hold.

## Check the declaration

Run `check` on `spec.yaml`:

=== "Command line"

    ```bash
    python -m mathspec check spec.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    for note in ms.advice('spec.yaml'):
        print(note)
    ```

The command and the Python loop print nothing, because mathspec accepts the
spec and has no remark that is not a refusal
([advice](../reference/glossary.md#advice)).

!!! info "See also"

    - [Check a spec without data](check.md), for how to read a refusal or advice.
    - [Dimensions](../reference/language/dimensions.md),
      [relations](../reference/language/relations.md) and
      [parameters](../reference/language/parameters-variables-constraints.md#parameters),
      for every key of each declaration.
