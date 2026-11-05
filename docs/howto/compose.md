<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Compose a spec from several files

This guide shows how to build one specification
([spec](../reference/glossary.md#spec)) out of several files. Use
[`merge`](../reference/composition.md#merge) to join partial spec files
([fragments](../reference/glossary.md#fragment)), such as the files of a
component library. Use
[`override`](../reference/composition.md#override) to lay files of changes
([patches](../reference/glossary.md#patch)) over a whole spec
([a base](../reference/glossary.md#base)), such as the spec a framework ships.
You need mathspec [installed](installation.md), and Python to call the two
functions.

## Build a spec from a library of components

<!-- prettier-ignore -->
1. Write the network as a spec. Its constraint `Bus_balance` sets
    `Bus_injection` to zero at each bus, and its objective is to minimise
    `total_cost`. The file lists both as names that another file declares
    ([`given:`](../reference/language/parameters-variables-constraints.md#given)),
    and `network.yaml` declares no component.

    ```yaml title="network.yaml"
    given:
      expressions:
        Bus_injection:
          dims: [snapshot, bus]
          description: what the components put into a bus
        total_cost:
          dims: []
          description: what running the system costs
    dimensions:
      snapshot: { dtype: int }
      bus: { dtype: str }
    constraints:
      Bus_balance:
        dims: [snapshot, bus]
        expression: Bus_injection == 0
    objective:
      sense: minimize
      expression: total_cost
    ```

2. Write each component as a spec against the network. Each component
    lists under `given:` each sum it adds to, and adds to each one a named
    expression with `adds_to:`
    ([a term](../reference/glossary.md#term)):

    ```yaml title="generator.yaml"
    given:
      expressions:
        Bus_injection: { dims: [snapshot, bus] }
        total_cost: { dims: [] }
    dimensions:
      snapshot: { dtype: int }
      bus: { dtype: str }
      generator: { dtype: str }
    relations:
      Generator_bus: { key: generator, values: bus }
    parameters:
      Generator_p_nom: { dims: [generator] }
      Generator_marginal_cost: { dims: [generator] }
    variables:
      Generator_p: { dims: [snapshot, generator], bounds: { lower: 0, upper: Generator_p_nom } }
    expressions:
      Generator_injection:
        expression: sum(Generator_p, over=generator, by=Generator_bus[bus])
        adds_to: Bus_injection
      Generator_cost:
        expression: sum(Generator_p * Generator_marginal_cost)
        adds_to: total_cost
    ```

    ```yaml title="load.yaml"
    given:
      expressions:
        Bus_injection: { dims: [snapshot, bus] }
    dimensions:
      snapshot: { dtype: int }
      bus: { dtype: str }
      load: { dtype: str }
    relations:
      Load_bus: { key: load, values: bus }
    parameters:
      Load_p_set: { dims: [snapshot, load] }
    expressions:
      Load_injection:
        expression: -sum(Load_p_set, over=load, by=Load_bus[bus])
        adds_to: Bus_injection
    ```

    Name each term after its component, such as `Generator_injection`, so that
    no two fragments
    [declare the same name](../reference/composition.md#a-name-two-fragments-declare).

3. Check each file on its own. `check` prints a remark that is not a
    refusal ([advice](../reference/glossary.md#advice)) for each name the file
    lists under `given:`, and does not refuse the file. On `load.yaml`, the
    command and the Python loop print one line:

    === "Command line"

        ```bash
        python -m mathspec check load.yaml
        ```

    === "Python"

        ```python
        import mathspec as ms

        for note in ms.advice('load.yaml'):
            print(note)
        ```

    ```text
    expression 'Bus_injection' is read here, and this file adds a term to it. merge() sums the term with the terms other files add under that name. Until then, the program reads it and does not build it.
    ```

    mathspec advises that `merge` completes the sum. On `network.yaml`, mathspec advises instead that `merge` takes each
    name from the file that declares it, or builds it from terms.

    Keep this Python session open, because later steps use `ms`.

4. Merge the files that you need, as a list:

    ```python
    spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml'])
    print(spec.expressions['Bus_injection'].expression)
    print(spec.expressions['total_cost'].expression)
    ```

    ```text
    Generator_injection + Load_injection
    Generator_cost
    ```

    `merge` builds each sum from its terms.

## Add a component to a library

Add a new file with a term of its own, and leave `network.yaml` as it is.

<!-- prettier-ignore -->
1. As in the steps above, write the component against the network:

    ```yaml title="store.yaml"
    given:
      expressions:
        Bus_injection: { dims: [snapshot, bus] }
    dimensions:
      snapshot: { dtype: int, ordered: true }
      bus: { dtype: str }
      store: { dtype: str }
    relations:
      Store_bus: { key: store, values: bus }
    parameters:
      Store_e_nom: { dims: [store] }
    variables:
      Store_p: { dims: [snapshot, store] }
      Store_e: { dims: [snapshot, store], bounds: { lower: 0, upper: Store_e_nom } }
    constraints:
      Store_energy_balance:
        dims: [snapshot, store]
        expression: Store_e == shift(Store_e, along=snapshot, offset=1, edge='wrap') - Store_p
    expressions:
      Store_injection:
        expression: sum(Store_p, over=store, by=Store_bus[bus])
        adds_to: Bus_injection
    ```

2. Add the file to the list:

    ```python
    spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml', 'store.yaml'])
    ```

    `Bus_injection` is now
    `Generator_injection + Load_injection + Store_injection`.

To add a term to a spec that is already merged, pass that spec as one item of
the list:

```python
spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml'])
spec = ms.merge([spec, 'store.yaml'])
```

After this two-step merge, `Bus_injection` is the same sum as after the list
of four files. Add a term with `merge` and not with a patch.

## Write part of the sum in the network file

To put part of the sum in the network file itself, define `Bus_injection`
there, and leave it out of `given:`. The component files stay
as they are.

<!-- prettier-ignore -->
1. Write the body of the sum in the network file:

    ```yaml title="network_slack.yaml"
    given:
      expressions:
        total_cost:
          dims: []
          description: what running the system costs
    dimensions:
      snapshot: { dtype: int }
      bus: { dtype: str }
    variables:
      Bus_slack: { dims: [snapshot, bus] }
    expressions:
      Bus_injection:
        dims: [snapshot, bus]
        expression: Bus_slack
        description: what the components put into a bus
    constraints:
      Bus_balance:
        dims: [snapshot, bus]
        expression: Bus_injection == 0
    objective:
      sense: minimize
      expression: total_cost
    ```

2. Merge it with the components:

    ```python
    spec = ms.merge(['network_slack.yaml', 'generator.yaml', 'load.yaml'])
    ```

    `Bus_injection` is `Bus_slack + Generator_injection + Load_injection`. The
    body in the network file comes first, and every term follows it.

## Lay patches over a base

<!-- prettier-ignore -->
1. Write the base for [`override`](../reference/composition.md#override) as a
    least-cost dispatch spec that mathspec loads on its own.

    ```yaml title="base.yaml"
    dimensions:
      snapshot: { dtype: int }
      generator: { dtype: str }
    parameters:
      capacity: { dims: [generator] }
      cost: { dims: [generator] }
      load: { dims: [snapshot] }
    variables:
      dispatch: { dims: [snapshot, generator], bounds: { lower: 0, upper: capacity } }
    constraints:
      power_balance:
        dims: [snapshot]
        expression: sum(dispatch, over=generator) == load
    objective:
      sense: minimize
      expression: sum(dispatch * cost)
    ```

2. Write in each patch only the fields to change.
    To add an entry, write it whole under a new name:

    ```yaml title="operate.yaml"
    variables:
      dispatch: { where: "capacity > 0" }
    ```

    ```yaml title="carbon.yaml"
    parameters:
      emission_rate: { dims: [generator] }
    constraints:
      emission_cap:
        dims: []
        expression: sum(dispatch * emission_rate) <= 1000
    ```

3. Lay the patches on the base, as a list:

    ```python
    spec = ms.override('base.yaml', ['carbon.yaml', 'operate.yaml'])
    ```

    `spec` declares `emission_cap` beside `power_balance`. With data attached,
    `dispatch` exists only where `capacity > 0` (a
    [condition](../reference/glossary.md#condition)).

## Remove an entry or a field with a patch

<!-- prettier-ignore -->
1. Write `null` under the name of each entry to remove:

    ```yaml title="feasibility.yaml"
    constraints:
      emission_cap: null
    objective: null
    ```

    The spec that `ms.override('base.yaml', ['carbon.yaml', 'feasibility.yaml'])`
    returns has `power_balance` as its only constraint, and no objective.

2. Write `null` on a field to give the field its default, and keep the entry.
    With `dispatch: { where: null }`, the variable has no condition. With
    `dispatch: { bounds: { upper: null } }`, it has no upper bound.

To empty a section, write `null` on each of its entries, because mathspec
refuses [`constraints: null`](../reference/composition.md#null-in-a-patch).

## Refine one patch with another

Here `project.yaml` is a patch on `carbon.yaml` from the steps above, with a
new expression for `emission_cap` only:

```yaml title="project.yaml"
constraints:
  emission_cap:
    expression: sum(dispatch * emission_rate) <= 500
```

[`override`](../reference/composition.md#override) replaces the fields of an
earlier patch with those of a later one, so put the refining patch after the
patch it refines:

```python
spec = ms.override('base.yaml', ['carbon.yaml', 'project.yaml'])
print(spec.constraints['emission_cap'].expression)
```

```text
sum(dispatch * emission_rate) <= 500
```

`emission_cap` has the `dims: []` of `carbon.yaml` and the limit of
`project.yaml`.

## Remove a term from a merged sum

To drop a term, write the body of the sum again without it, in a patch, and
lay the patch after the last `merge`:

```yaml title="no_load.yaml"
expressions:
  Bus_injection: Generator_injection
```

```python
spec = ms.override(ms.merge(['network.yaml', 'generator.yaml', 'load.yaml']), ['no_load.yaml'])
```

`Bus_injection` is then `Generator_injection` alone, and `Load_injection` stays
in the spec as a named expression that no sum includes.

!!! info "See also"

    - [composing specs](../reference/composition.md), for every rule of `merge`
      and `override`
    - [what a patch writes](../reference/composition.md#what-a-patch-writes),
      for each change you can make with a patch
    - [a term on a merged sum](../reference/composition.md#a-term-on-a-merged-sum),
      for why a term is added with `merge` and not with a patch
    - [refusals](../reference/composition.md#refusals), for each message that
      `merge` and `override` give
    - [a spec in several files](../tutorials/several-files.md), for a lesson in which
      you build a library step by step
    - [a component library](../examples/library/index.md), for a larger library
