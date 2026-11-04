<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# State a rule that differs by case

This guide shows how to write, in the specification of an optimisation model
([a spec](../reference/glossary.md#spec)), a rule whose form differs between
members of a [dimension](../reference/language/dimensions.md).
Committable and non-committable generators are the usual example of members
that share one rule form (a case). A committable generator has an
on/off decision, and the others do not. Where the form of the rule differs, you
write one named parameter, variable or constraint
([an entry](../reference/glossary.md#entry)) per case. Where only a quantity in
the rule differs, you name the quantity once per case and write the rule once.
You need mathspec [installed](installation.md) and a spec with a `generator`
dimension.

## Write one entry per case

<!-- prettier-ignore -->
1. Put the case in the data. A `bool` parameter is true for the generators
    in the case. Where there are more than two cases, a `str` parameter instead
    sets the case of each generator.

2. Write one entry per case, each with its own
    [`where:`](../reference/language/absence.md) condition, so that, with data attached,
    the entry has rows only where its condition is true. Here `committable` is the `bool`
    parameter of step 1:

    ```yaml
    dimensions:
      snapshot: { dtype: int }
      generator: { dtype: str }

    parameters:
      capacity: { dims: [generator] }
      min_output: { dims: [generator] }
      committable: { dims: [generator], dtype: bool }

    variables:
      dispatch: { dims: [snapshot, generator], bounds: { lower: 0, upper: capacity } }
      on: { dims: [snapshot, generator], where: committable, domain: binary }

    constraints:
      floor_committed:
        dims: [snapshot, generator]
        where: committable
        expression: dispatch >= min_output * on
      ceiling_committed:
        dims: [snapshot, generator]
        where: committable
        expression: dispatch <= capacity * on
    ```

    With data attached, `floor_committed` and `ceiling_committed` have rows only for committable generators. The `bounds:` of `dispatch`
    limit a non-committable generator to `capacity` alone.

3. Where the other case has a rule of its own, write it as a further entry
    under the negated condition. Here you declare `max_output` beside
    `min_output`, over `generator`:

    ```yaml
    constraints:
      ceiling_free:
        dims: [snapshot, generator]
        where: "NOT committable"
        expression: dispatch <= max_output
    ```

    With data attached, `ceiling_free` has rows only for non-committable
    generators.

## Name a quantity that differs by case

Name the quantity with one expression per case
([`cases:`](../reference/language/named.md#cases)). Then write the rule
against it once:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }

parameters:
  capacity: { dims: [generator] }
  committable: { dims: [generator], dtype: bool }

variables:
  dispatch: { dims: [snapshot, generator], bounds: { lower: 0 } }
  on: { dims: [snapshot, generator], where: committable, domain: binary }

expressions:
  available:
    dims: [snapshot, generator]
    cases:
      committed:
        when: committable
        expression: capacity * on
    otherwise: capacity

constraints:
  ceiling:
    dims: [snapshot, generator]
    expression: dispatch <= available
```

`available` is `capacity * on` where `committable` is true, and `capacity` for
every other generator.

## Check the result

Save the spec of the last section as `spec.yaml`. The spec of step 2 also
works, with `ceiling_free` and a `max_output` parameter added. Run
`check` on `spec.yaml`:

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
spec.

!!! info "See also"

    - [Check a spec without data](check.md), for how to read a refusal or advice.
    - [absence and `where`](../reference/language/absence.md), for what a `where:`
      condition does to a row
    - [`cases`](../reference/language/named.md#cases), for every key mathspec
      accepts in a case
    - [refused cases](../reference/language/named.md#refused-cases), for what
      mathspec refuses in a case
