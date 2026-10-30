<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Fix a quantity that is data in one model and a decision in another

This guide shows how to write one specification file
([spec](../reference/glossary.md#spec)) for a quantity such as the size of a plant.
In one spec with data attached ([model](../reference/glossary.md#model)) the
solver chooses the quantity, and in another you attach it as data. In a planning study the solver sizes each plant, and in an operational
study of the existing fleet you fix each size at today's capacity.
You run both from the same spec, so the math cannot drift between them. You need mathspec [installed](installation.md).

## Declare the quantity as a variable

Declare the quantity as a
[variable](../reference/language/parameters-variables-constraints.md#variables),
with bounds set to two parameters. Here `size` is the size of each plant, and
`rate` and `stock` are the variables that `size` limits:

```yaml
dimensions:
  plant: { dtype: str }
  time: { dtype: int }

parameters:
  size_min: { dims: [plant] }
  size_max: { dims: [plant] }
  relmax: { dims: [plant] }

variables:
  size:
    dims: [plant]
    bounds: { lower: size_min, upper: size_max }
  rate: { dims: [plant, time], bounds: { lower: 0 } }
  stock: { dims: [plant], bounds: { lower: 0 } }
```

## Write every rule against the variable

Write each limit that the size sets as a constraint against `size`:

```yaml
constraints:
  rate_max:
    dims: [plant, time]
    expression: rate - relmax * size <= 0
  stock_max:
    dims: [plant]
    expression: stock <= size
```

`rate_max` is one constraint whether the solver chooses `size` or you attach
it as data. `stock_max` limits the `stock` of each plant to its `size`.
`stock_max` is a constraint and not a bound, because mathspec refuses
`upper: size` in the
[bounds](../reference/language/parameters-variables-constraints.md#variables)
of a variable.

Even where you fix `size` with equal bounds ([pin](../reference/glossary.md#pin)
it), a product of `size` and another variable, such as an on/off binary, is
[quadratic](../reference/language/expressions.md#where-a-product-of-two-variables-is-allowed).

## Pin the variable in the data

Where you attach the quantity as data, pin the variable. Attach the same value to `size_min`
and `size_max` for each plant whose size is fixed. Where the two bounds
differ, the solver chooses the size between them.

## Check the spec

Put the two fences in one file, `spec.yaml`, and run `check` on it:

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
spec and has no remark to make about it
([advice](../reference/glossary.md#advice)). You then use the same file as the
spec of both models.

!!! info "See also"

    - [Check a spec without data](check.md), for how to read a refusal or advice.
    - [Variables](../reference/language/parameters-variables-constraints.md#variables),
      for every key of a variable and its bounds.
    - [Where a product of two variables is allowed](../reference/language/expressions.md#where-a-product-of-two-variables-is-allowed),
      for the products a spec may state.
