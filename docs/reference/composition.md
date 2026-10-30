<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Composing specs

mathspec builds one specification of an optimisation model
([a spec](glossary.md#spec)) from several files with two functions,
[`merge`](api.md#mathspec.merge) and [`override`](api.md#mathspec.override).
This page describes what each function does with its files, what it carries
into the result, and every refusal it can give.

`merge` joins whole specs as peers ([fragments](glossary.md#fragment)), such
as the files of a [component library](../examples/library/index.md).
`override` lays files that state only a change ([patches](glossary.md#patch))
over a spec that another party extends ([a base](glossary.md#base)). A base is
often the spec that a framework ships.

```python
import mathspec as ms

library = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml'])
project = ms.override('base.yaml', ['carbon.yaml'])
```

`merge` joins three fragments into `library`, and `override` lays the patch
`carbon.yaml` over `base.yaml` to give `project`.

Each function takes its files as a list, and raises `TypeError` for one path
in place of a list. An item of the list is a path to a YAML file, YAML text, a
mapping or a loaded [`Spec`](spec.md#mathspec.spec.Spec). So the result of one
call can be an item of the next, as in `override(merge([…]), […])`.

In a refusal, mathspec names a file by its path as it is written in the list. It
names a mapping or a loaded spec by its place in the list, such as `'#2'`.

## `merge`

`merge(fragments, description=None)` loads each fragment with
[`to_spec`](api.md#mathspec.to_spec), joins their entries into one spec, and
returns that spec loaded. `merge` refuses a name that two fragments declare,
and renames nothing. The `description=` argument sets the description of the
merged spec.

The three files below form a small library, and each name in it has a prefix
of its own, such as `Generator_` or `Load_`. `network.yaml` states the
balance at each bus. It lists `Bus_injection`, what the components put into
each bus, under the section for names another file declares
([`given:`](language/parameters-variables-constraints.md#given)). Each
component file adds its part as a
[named expression](language/named.md#expressions) that adds to a sum
([a term](language/named.md#adds_to)).

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

Each file loads and prints on its own. `generator.yaml` sets no objective, so
alone the file states a problem with nothing to minimise ([a feasibility
problem](language/parameters-variables-constraints.md#objective)). `merge`
joins the three:

```python
spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml'])
print(spec.to_yaml())
```

```text
version: 0
dimensions:
  snapshot: {dtype: int}
  bus: {dtype: str}
  generator: {dtype: str}
  load: {dtype: str}
relations:
  Generator_bus: {key: generator, values: bus}
  Load_bus: {key: load, values: bus}
parameters:
  Generator_p_nom: {dims: [generator], dtype: float}
  Generator_marginal_cost: {dims: [generator], dtype: float}
  Load_p_set: {dims: [snapshot, load], dtype: float}
variables:
  Generator_p:
    dims: [snapshot, generator]
    bounds: {lower: 0.0, upper: Generator_p_nom}
    domain: continuous
    missing: absent
expressions:
  Generator_injection: sum(Generator_p, over=generator, by=Generator_bus[bus])
  Generator_cost: sum(Generator_p * Generator_marginal_cost)
  Load_injection: -sum(Load_p_set, over=load, by=Load_bus[bus])
  Bus_injection:
    dims: [snapshot, bus]
    expression: Generator_injection + Load_injection
    description: what the components put into a bus
  total_cost:
    dims: []
    expression: Generator_cost
    description: what running the system costs
objective: {sense: minimize, expression: total_cost}
constraints:
  Bus_balance:
    dims: [snapshot, bus]
    expression: Bus_injection == 0
```

<figure class="diagram">
--8<-- "docs/static/composition-merge-terms.svg"
</figure>

The merged spec has no `given:` section, because `merge` builds each sum that
a fragment lists under `given:` from its terms. `Bus_injection` is the sum of
the two terms, and each term stays a named expression without its `adds_to:`.
The objective is the one that `network.yaml` sets.

### Each kind of entry

Two fragments may share a [dimension](language/dimensions.md), a
[relation](language/relations.md), a given entry or a sum.

| The entry                                         | What `merge` does                                                                                                                |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| a dimension or a relation                         | accepts it from every fragment that declares it, where every fragment declares it the same way                                   |
| a `description` on a shared dimension or relation | keeps the first wording in the list                                                                                              |
| `ordered: true` on a shared dimension             | makes the dimension ordered if one fragment sets it                                                                              |
| `missing:` on a shared relation                   | requires the same value from every fragment that declares the relation, where `missing: refused` and no `missing:` are one value |
| an entry under `given:`                           | checks it against the fragment that declares the name, then folds it in ([given entries](#given-entries))                        |
| an expression with `adds_to:`                     | adds it as a term to the sum in its `adds_to:` ([terms and sums](#terms-and-sums))                                               |
| `objective`                                       | takes it from the one fragment that sets it, and refuses a second                                                                |
| `version`                                         | requires the same value from every fragment                                                                                      |
| `description` at the top of a fragment            | drops it                                                                                                                         |
| any other entry                                   | takes it from the one fragment that declares it, and refuses a second                                                            |

### Terms and sums

`merge` builds each sum from the terms that fragments add to it. The merged
body is the body that one fragment defines, if any, followed by every term by
its name, in list order. The list order changes only the order in which the
terms are written. So the layout that equal specs share
([the canonical form](reading.md#comparing-two-specs)) is the same for every
order:

```python
a = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml'])
b = ms.merge(['load.yaml', 'generator.yaml', 'network.yaml'])
a.expressions['Bus_injection'].expression
# 'Generator_injection + Load_injection'
b.expressions['Bus_injection'].expression
# 'Load_injection + Generator_injection'
a.to_yaml(canonical=True) == b.to_yaml(canonical=True)
# True
```

The two bodies list the terms in different orders, and the canonical forms
are equal.

Two terms of one sum never collide, because each term is a named expression
with a name of its own, such as `Generator_injection` and `Load_injection`.

A fragment may define the sum itself instead of listing it under `given:`.
`merge` then keeps the `dims:` and the description of that fragment. Here
`network_slack.yaml` defines `Bus_injection` as the variable `Bus_slack`:

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

```python
spec = ms.merge(['network_slack.yaml', 'generator.yaml', 'load.yaml'])
spec.expressions['Bus_injection'].expression
# 'Bus_slack + Generator_injection + Load_injection'
```

`Bus_slack` comes first, then the terms in list order.

A merged spec defines every sum it has terms for, so a later `merge` adds
further terms to the body of that sum. Here `store.yaml` is the store fragment
of [compose a spec from several
files](../howto/compose.md#add-a-component-to-a-library):

```python
two_steps = ms.merge([ms.merge(['network.yaml', 'generator.yaml', 'load.yaml']), 'store.yaml'])
one_step = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml', 'store.yaml'])
two_steps.expressions['Bus_injection'].expression
# 'Generator_injection + Load_injection + Store_injection'
one_step.expressions['Bus_injection'].expression
# 'Generator_injection + Load_injection + Store_injection'
```

`merge` gives `Bus_injection` the same three terms in the same order either
way.

### Given entries

A given entry is a name that a file lists under
[`given:`](language/parameters-variables-constraints.md#given). `merge` folds
each given entry into the entry of the fragment that declares the name. The
fragment that lists the name may state less than the file that declares it,
such as the dimensions of a variable with no `domain`.

| The given entry                   | What `merge` does                                                                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| any kind, declared by a fragment  | checks it against the declaring fragment, and gives the merged entry the description of the given entry, where the declaration has none                 |
| any kind, listed by two fragments | requires both to list it the same way, as for a dimension                                                                                               |
| a given expression                | checks the body that the other fragment declares by the rules of [given expressions](language/parameters-variables-constraints.md#given-expressions)    |
| a given condition                 | checks the condition that the other fragment declares by the rules of [given conditions](language/parameters-variables-constraints.md#given-conditions) |
| any kind, declared by no fragment | keeps it under `given:`                                                                                                                                 |

Here `price.yaml` lists `co2_price` under `given:`, and no other fragment
declares it:

```yaml title="price.yaml"
given:
  parameters:
    co2_price: { dims: [] }
  variables:
    Generator_p: { dims: [snapshot, generator] }
  expressions:
    total_cost: { dims: [] }
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  Generator_co2: { dims: [generator] }
expressions:
  co2_cost:
    expression: co2_price * sum(Generator_p * Generator_co2)
    adds_to: total_cost
```

```python
spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml', 'price.yaml'])
print(spec.to_yaml())
```

```text
version: 0
given:
  parameters:
    co2_price: {dims: []}
…
```

`co2_price` stays under `given:`, and `merge` builds `total_cost` from its
terms `Generator_cost` and `co2_cost`:

```python
spec.expressions['total_cost'].expression
# 'Generator_cost + co2_cost'
```

## `override`

`override(base, patches)` loads the base with `to_spec` and lays each patch
over the result of the ones before it, in list order. `override` returns the
patched spec loaded. A patch is not a spec, so `override` does not load a patch alone.

A patch lists only the fields it changes. An entry or a field that the patch
leaves out stays as the base declares it. Here `operate.yaml` adds a
[`where:`](language/absence.md#where) condition to one variable, and
`carbon.yaml` adds a parameter and a constraint:

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

```python
spec = ms.override('base.yaml', ['carbon.yaml', 'operate.yaml'])
print(spec.to_yaml())
```

```text
version: 0
dimensions:
  snapshot: {dtype: int}
  generator: {dtype: str}
parameters:
  capacity: {dims: [generator], dtype: float}
  cost: {dims: [generator], dtype: float}
  load: {dims: [snapshot], dtype: float}
  emission_rate: {dims: [generator], dtype: float}
variables:
  dispatch:
    dims: [snapshot, generator]
    where: capacity > 0
    bounds: {lower: 0.0, upper: capacity}
    domain: continuous
    missing: absent
objective:
  sense: minimize
  expression: sum(dispatch * cost)
constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load
  emission_cap:
    dims: []
    expression: sum(dispatch * emission_rate) <= 1000
```

<figure class="diagram">
--8<-- "docs/static/composition-override-where.svg"
</figure>

`override` keeps the dimensions and bounds of `dispatch`, and adds the `where:`
that `operate.yaml` writes. With `capacity = {wind: 10, gas: 5, old: 0}`, the
patched `dispatch` has no row at `old`.

### `null` in a patch

- On an entry, `override` removes the entry. For
  `constraints: {emission_cap: null}`, `override` removes that constraint.
- On a field, `override` restores the default of that field and keeps the
  entry. For `dispatch: {where: null}`, `override` gives the variable no
- On the section `objective`, `override` removes the objective.
- On any other section, `override` refuses `null`.

### What a patch writes

| The patch writes                                                     | What `override` does                                                                                                                                                           |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| some fields of an entry                                              | changes those fields, and keeps the rest of the entry                                                                                                                          |
| a whole entry under a new name                                       | adds it                                                                                                                                                                        |
| a named expression as a [bare string](language/named.md#expressions) | replaces only its body, `expression:` or `cases:`, and keeps its `dims:`, description and `adds_to:`, so the new body may have no dimension outside those `dims:`              |
| `null` on an entry, a field or a section                             | applies the rule in [`null` in a patch](#null-in-a-patch)                                                                                                                      |
| a dimension or a relation                                            | adds it, or accepts it restated as the base declares it, field by field, where a field left out equals its default                                                             |
| `ordered:` on a restated dimension                                   | makes the dimension ordered for `true`, and refuses `false` over an ordered dimension                                                                                          |
| `missing:` on a relation, alone or with other fields                 | changes whether every key combination needs a row, as on a parameter                                                                                                           |
| an entry under one kind of `given:`                                  | edits, adds or removes it like any entry, and keeps the other kinds                                                                                                            |
| `version`, `description`                                             | replaces the value of the base                                                                                                                                                 |
| a field that an earlier patch writes                                 | replaces that value                                                                                                                                                            |
| a term on a base that lists the sum under `given:`                   | keeps the sum under `given:` and keeps the term with its `adds_to:`, and builds no body                                                                                        |
| a term on a base that defines the sum                                | refuses the patch ([a term on a merged sum](#a-term-on-a-merged-sum))                                                                                                          |
| the body of a merged sum without one term                            | replaces the body, and keeps the left-out term as a named expression that no sum uses ([remove a term from a merged sum](../howto/compose.md#remove-a-term-from-a-merged-sum)) |
| `adds_to: null` on a term                                            | keeps the entry as a named expression that adds to nothing                                                                                                                     |

## Refusals

In each message, mathspec names the entry and suggests the change that
removes the refusal, and in most it also names the file.

### A name two fragments declare

Here `gas.yaml` and `coal.yaml` are two copies of a generator file, and both
declare `Generator_p_nom`:

```text
fragments 'gas.yaml' and 'coal.yaml' both declare the parameter 'Generator_p_nom'. If they are two rows of a dimension, merge the fragment once and put both rows in the data. Otherwise, rename one of them.
```

mathspec suggests two rewrites: one fragment with both generators as rows
of the data, or a new name for one of the two parameters.

### A given entry that disagrees with its declaration

Here `emissions.yaml` lists `Generator_p` as binary under `given:`, and
`generator.yaml` declares it as continuous:

```yaml title="emissions.yaml"
given:
  variables:
    Generator_p: { dims: [snapshot, generator], domain: binary }
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  Generator_co2: { dims: [generator] }
  co2_cap: { dims: [] }
constraints:
  co2_limit:
    dims: []
    expression: sum(Generator_p * Generator_co2) <= co2_cap
```

`merge` refuses `emissions.yaml` because the two domains differ:

```text
fragment 'emissions.yaml' reads the given variable 'Generator_p' as {'dims': ['snapshot', 'generator'], 'domain': 'binary'}, where 'generator.yaml' introduces it as {'dims': ['snapshot', 'generator'], 'bounds': {'lower': 0.0, 'upper': 'Generator_p_nom'}, 'domain': 'continuous', 'missing': 'absent'}. Restate the dims as 'generator.yaml' declares them, or leave the field out.
```

### A fragment that does not load alone

Where `to_spec` refuses a fragment, `merge` names the fragment, then quotes
the message of `to_spec`. No other fragment in the list can make that fragment
load. Here `generator.yaml` declares `Generator_p` and also lists it under
`given:`, so the two entries collide:

```text
fragment 'generator.yaml' does not load on its own. Declare what it builds, and read under 'given:' what another fragment builds.
Given variable 'Generator_p' collides with the variable of the same name. Rename one of them.
```

### A partial entry under a new name

A patch that lists only some fields of an entry must edit an entry that the
base, or an earlier patch, declares. `override` refuses a misspelt name, and
does not take it as a new entry. Here `project.yaml` writes
`power_balnce: {dims: [snapshot]}`, and mathspec suggests the closest name:

```text
patch 'project.yaml' edits the constraint 'power_balnce', which its base does not declare. Did you mean 'power_balance'? A patch creates an entry only by writing it whole, and this one is not: a constraint needs `expression`.
```

### A dimension restated differently

Here `relabelled.yaml` writes `snapshot: {dtype: str}` over a base that
declares `snapshot: {dtype: int}`. `override` refuses the patch because the
two `dtype` values differ:

```text
patch 'relabelled.yaml' declares the dimension 'snapshot' as {'dtype': 'str'}, where its base declares {'dtype': 'int'}. A patch adjusts the math, not the coordinate space the math is already written over: each field but `ordered` has to read as the base reads it, and a field the patch leaves out reads as its default. Restate the dimension as its base declares it, leave it out, or give the patch a dimension of its own under a name of its own.
```

### `ordered: false` over an ordered dimension

Here `unordered.yaml` writes `snapshot: {dtype: int, ordered: false}` over a
base that declares `snapshot` ordered. `override` refuses the patch because
it removes `ordered`:

```text
patch 'unordered.yaml' says the dimension 'snapshot' is not ordered, where its base declares it ordered. A patch can add `ordered: true` but cannot remove it, because a construct in the base may step along it. Leave `ordered` out of the patch.
```

### A section set to `null`

`override` refuses [`null` on a section](#null-in-a-patch) other than
`objective`. Here
`project.yaml` writes `constraints: null`, and mathspec suggests two
rewrites:

```text
patch 'project.yaml' sets 'constraints' to null, which removes nothing. Remove the entries one at a time, each under its own name, or leave the section out of the patch.
```

### `null` on an entry the base does not declare

`override` refuses a `null` on an entry that the base does not declare. Here
`stale.yaml` writes `constraints: {power_balnce: null}`, and mathspec suggests
the closest name that the base declares:

```text
patch 'stale.yaml' removes the constraint 'power_balnce', which its base does not declare. Delete the removal from the patch, or fix the name. Did you mean 'power_balance'?
```

### A term on a merged sum

Here a patch that declares a store and its term `Store_injection` is laid over
the merged library. mathspec refuses the term because the base defines
`Bus_injection`:

```text
Named expression 'Store_injection': it adds to 'Bus_injection', which this file defines. Write the term into the body of 'Bus_injection', or read 'Bus_injection' under 'given: expressions:' and add its body as a term.
```

!!! info "See also"

    - [Compose a spec from several files](../howto/compose.md), for the order of
      the calls and the store fragment
    - [`merge`](api.md#mathspec.merge) and [`override`](api.md#mathspec.override),
      for the signatures
    - [`adds_to`](language/named.md#adds_to), for what mathspec refuses in a term
    - [A component library](../examples/library/index.md), for a library written
      with both functions
