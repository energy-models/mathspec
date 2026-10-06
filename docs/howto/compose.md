<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Compose a spec from several files

Build one spec out of files that each state part of it. `merge` joins
**fragments**, which are the files of a component library and each declare part
of the math. `override` lays **patches** over a **base**, where the base is the
spec a framework ships and a patch is the change a project makes to it. Both functions load every fragment and the base with
[`to_spec`](../reference/language/errors.md#what-to_spec-checks) first, and
return the composed spec loaded the same way. Both take their files as a list,
and you can nest them as `override(merge([…]), […])`.

## A library of components

1. **Write the network as a spec.** It balances the injection at each bus.
   It reads the injection under
   [`given`](../reference/language/declarations.md#given), which declares a
   name that the file reads and does not build, because the component files
   build it. It sets the objective on `total_cost`, which it reads the same
   way, because each component adds its own cost. Nothing in the file names a
   component class.

   ```yaml title="network.yaml"
   dimensions:
     snapshot: { dtype: int }
     bus: { dtype: str }
   given:
     expressions:
       Bus_injection:
         dims: [snapshot, bus]
         description: what the components put into a bus
       total_cost:
         dims: []
         description: what running the system costs
   constraints:
     Bus_balance:
       dims: [snapshot, bus]
       expression: Bus_injection == 0
   objective:
     sense: minimize
     expression: total_cost
   ```

2. **Write each component file against the network.** The file declares its
   own dimension and its own math, and also reads `Bus_injection`. It states
   what it puts into a bus as a
   [term](../reference/language/declarations.md#terms), which is a named
   expression whose `adds_to:` names `Bus_injection`. A component that costs
   something adds its cost to `total_cost` the same way.

   ```yaml title="generator.yaml"
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
   given:
     expressions:
       Bus_injection: { dims: [snapshot, bus] }
       total_cost: { dims: [] }
   expressions:
     Generator_injection:
       expression: sum(Generator_p, over=generator, by=Generator_bus[bus])
       adds_to: Bus_injection
     Generator_cost:
       expression: sum(Generator_p * Generator_marginal_cost)
       adds_to: total_cost
   ```

   ```yaml title="load.yaml"
   dimensions:
     snapshot: { dtype: int }
     bus: { dtype: str }
     load: { dtype: str }
   relations:
     Load_bus: { key: load, values: bus }
   parameters:
     Load_p_set: { dims: [snapshot, load] }
   given:
     expressions:
       Bus_injection: { dims: [snapshot, bus] }
   expressions:
     Load_injection:
       expression: -sum(Load_p_set, over=load, by=Load_bus[bus])
       adds_to: Bus_injection
   ```

   Each file loads on its own and prints as math on its own. Only the
   network sets an objective, so `generator.yaml` on its own is a feasibility
   problem.

3. **Merge the files you need.** Give them as a list. A refusal names a file
   by its path, as the list gives it, and a mapping or a loaded spec by its
   place in the list, such as `'#2'`.

   ```python
   import mathspec as ms

   spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml'])
   ```

   `spec` defines `Bus_injection` as `Generator_injection + Load_injection`,
   and keeps each term as a named expression. Nothing is left under `given:`,
   so `spec` is fully defined. The objective is the network's, and
   `total_cost` is `Generator_cost`. The order of the list does not
   change the spec: [`canonical`](compare.md) writes the same text for every
   order. `merge` refuses a second file that sets an objective, because one
   fragment sets it and each other fragment adds its part to the sum that the
   objective reads.

4. **Add a component without touching the network.** A new file adds its own
   term, and `network.yaml` stays as it is.

   ```yaml title="store.yaml"
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
   given:
     expressions:
       Bus_injection: { dims: [snapshot, bus] }
   expressions:
     Store_injection:
       expression: sum(Store_p, over=store, by=Store_bus[bus])
       adds_to: Bus_injection
   ```

   Add the file to the list:

   ```python
   spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml', 'store.yaml'])
   ```

   `Bus_injection` is `Generator_injection + Load_injection + Store_injection`.
   A merged spec takes a further term the same way, so
   `ms.merge([ms.merge(['network.yaml', 'generator.yaml', 'load.yaml']), 'store.yaml'])`
   gives the same sum.

5. **Add a term that belongs to the network.** Define `Bus_injection` in the
   network file instead of reading it under `given:`. The body that the network
   file writes then comes first in the sum, every term follows it, and the
   component files stay as they are.

   ```yaml title="network_slack.yaml"
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
   given:
     expressions:
       total_cost:
         dims: []
         description: what running the system costs
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
   ```

   `Bus_injection` is `Bus_slack + Generator_injection + Load_injection`, over
   the `dims:` and with the description of `network_slack.yaml`. At most one
   file defines the sum, and each other file reads it under `given:`.

A library can also couple its components through a flow variable per port,
which each component pins at its own port.
[A component library](../examples/library/index.md) is written that way.

## What a fragment may share

| The entry                                         | What happens                                                                                                                                                                                        |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| a dimension or a relation                         | every fragment may declare it, and the ones that do say the same thing about it                                                                                                                     |
| a `description` on a shared dimension or relation | it is prose rather than a claim, and the first wording in the list is carried                                                                                                                       |
| `ordered: true` on a shared dimension             | it is a claim about the dimension rather than the dimension, so the dimension is ordered if one fragment says so                                                                                    |
| any other declaration                             | one fragment declares it, and a second is refused                                                                                                                                                   |
| an entry under `given:`                           | it is checked against the fragment that introduces the name, then folded into it. Its description fills the declaration where the introducer wrote none                                             |
| a given expression                                | the body of the definition carries no dimension that the `dims` of the reading fragment do not name                                                                                                 |
| a given entry no fragment introduces              | it stays under `given:` until a host model provides it                                                                                                                                              |
| an expression with `adds_to:`                     | the sum it names is the body one fragment defines, if any, followed by every term by its name, in the order of the list. [Terms](../reference/language/declarations.md#terms) gives what is refused |
| `objective`                                       | one fragment sets it, and a second is refused. Several fragments contribute to it as terms of a sum the objective reads                                                                             |
| `version`                                         | every fragment is written against the same one                                                                                                                                                      |
| `description` at the top of a fragment            | it is about the fragment and is not carried. Pass the composed spec's as `description=`                                                                                                             |

## A name two fragments declare

Each fragment declares its own math, so `merge` refuses a name that two
fragments declare, and the message names both files. Here two files each
declare a generator fleet:

```text
fragments 'gas.yaml' and 'coal.yaml' both declare the parameter 'Generator_p_nom'. If they are two rows of a dimension, merge the fragment once and put both rows in the data. Otherwise, rename one of them.
```

A term is a named expression, so the terms of two fragments need two names.
Name each term after its component, such as `Generator_injection` and
`Load_injection`.

## A declaration read one way and introduced another

A fragment that reads a declaration under `given:` must agree with the fragment
that introduces it. The reading fragment may say less, such as the dimensions
with no `domain`, but it may not say something different. Here a file that caps
emissions reads `Generator_p` as binary:

```yaml title="emissions.yaml"
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
given:
  variables:
    Generator_p: { dims: [snapshot, generator], domain: binary }
parameters:
  Generator_co2: { dims: [generator] }
  co2_cap: { dims: [] }
constraints:
  co2_limit:
    dims: []
    expression: sum(Generator_p * Generator_co2) <= co2_cap
```

```text
fragment 'emissions.yaml' reads the given variable 'Generator_p' as {'dims': ['snapshot', 'generator'], 'domain': 'binary'}, where 'generator.yaml' introduces it as {'dims': ['snapshot', 'generator'], 'bounds': {'lower': 0.0, 'upper': 'Generator_p_nom'}, 'domain': 'continuous', 'absence': 'undefined'}. Restate the dims as 'generator.yaml' declares them, or leave the field out.
```

Two fragments that both only read a declaration must read it the same way,
and `merge` refuses a difference, as it does for a dimension.

## A fragment that does not load on its own

A fragment is a whole spec, so `merge` loads each one before it composes
them. If `to_spec` refuses a fragment, `merge` refuses it under its own name,
with the message `to_spec` gives. No other fragment in the list can make it
load. Here the generator declares `Generator_p` and reads it under `given:` as
well:

```text
fragment 'generator.yaml' does not load on its own. Declare what it builds, and read under 'given:' what another fragment builds.
Given variable 'Generator_p' collides with the variable of the same name. Rename one of them.
```

## A base and its patches

1. **Write the base as a spec**, and each patch as the change it makes. A
   patch names only the fields it changes, and a declaration that the patch
   does not name stays as the base wrote it. A named expression that the patch
   writes on one line replaces only the body, `expression:` or `cases:`. The
   entry keeps its `dims:`, its description and its `adds_to:`, so the new body
   carries no dimension outside the kept `dims:`. The base loads on its own,
   and `override` loads it first. A patch is not a spec, so `override` does not
   load it, but lays it over the base as written and then loads the patched
   spec.

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

2. **Lay the patches on the base.** Give them as a list. A refusal names a
   patch by its path, in the same way that `merge` names a fragment.

   ```python
   import mathspec as ms

   spec = ms.override('base.yaml', ['carbon.yaml', 'operate.yaml'])
   ```

   `spec` declares `emission_cap` beside `power_balance`, and `dispatch` carries
   the mask `capacity > 0`.

3. **Remove a declaration with `null`.** A patch that does not mention a
   declaration leaves it alone, so removal needs a marker of its own.

   ```yaml title="feasibility.yaml"
   constraints:
     emission_cap: null
   objective: null
   ```

   On a declaration, `null` removes the declaration. On a field, the field
   takes its default and the declaration stays:
   `dispatch: { where: null }` gives that variable no mask, and
   `dispatch: { bounds: { upper: null } }` leaves it open above. On a section,
   `constraints: null` is refused, because a section is not a declaration and
   a `null` on it removes nothing.

4. **Put a patch that refines another after it.** `override` lays the
   patches in the order of the list, each on the result of the ones before.
   Where two patches write one field, the later one wins. A later patch may
   also edit or remove a declaration that an earlier one creates.

   ```python
   spec = ms.override('base.yaml', ['pathway.yaml', 'project.yaml'])
   ```

## What a patch may say

| The entry                            | What happens                                                                  |
| ------------------------------------ | ----------------------------------------------------------------------------- |
| some fields of a declaration         | those fields change, and the rest of the declaration stays                    |
| a whole declaration under a new name | it is added                                                                   |
| `null` under a declaration's name    | it is removed                                                                 |
| `null` on a field of a declaration   | the field takes its default, and the rest of the declaration stays            |
| `null` under a section's name        | it is refused                                                                 |
| a dimension or a relation            | it is added, or restated as the base declares it                              |
| `ordered:` on a restated dimension   | `true` makes the dimension ordered; `false` over an ordered one is refused    |
| an entry under one kind of `given:`  | it is edited, added or removed like any declaration, and the other kinds stay |
| `version`, `description`             | the patch's value replaces the base's                                         |
| a field an earlier patch writes      | the later patch's value replaces it                                           |

## A partial entry on a missing name

An entry that names only some fields must edit a declaration that the base or
an earlier patch has. `override` refuses a mistyped name, and does not read it
as a new declaration:

```text
patch 'project.yaml' edits the constraint 'power_balnce', which its base does not declare. Did you mean 'power_balance'? A patch creates a declaration only by writing it whole, and this one is not: a constraint needs `expression`.
```

To add a constraint, write the whole constraint. To change one, spell its name
as the base spells it.

## A dimension redeclared

A patch may add a dimension or a relation, and may restate one the base
declares. The restatement says what the base says: half a declaration is a
second reading of the same name, and a field written at its default is the
same as one left out. Changing one under the expressions already written
over it is refused, and so is removing one:

```text
patch 'relabelled.yaml' declares the dimension 'snapshot' as {'dtype': 'str'}, where its base declares {'dtype': 'int'}. Restate the declaration word for word, leave it out, or give the patch a dimension of its own under a name of its own.
```

`ordered` is a claim about the dimension, not the dimension. A patch may add
it, so a patch that steps along `snapshot` declares it `ordered: true` over a
base that does not. A patch may not take it back, because the base may
already step along it:

```text
patch 'unordered.yaml' says the dimension 'snapshot' is not ordered, where its base declares it ordered. A construct in the base may step along it, and a patch adds the claim of order but never withdraws it: leave `ordered` out of the patch.
```

## A section set to `null`

A section such as `constraints:` holds declarations and is not one, so
`override` refuses a `null` on it rather than read the `null` as an
instruction to empty the section:

```text
patch 'project.yaml' sets 'constraints' to null, which removes nothing. Remove the declarations one at a time, each under its own name, or leave the section out of the patch.
```

## A stale removal

`override` refuses a `null` on a declaration the base does not have, and names
the closest name the base does have:

```text
patch 'stale.yaml' removes the constraint 'power_balnce', which its base does not declare. Delete the removal from the patch, or fix the name. Did you mean 'power_balance'?
```
