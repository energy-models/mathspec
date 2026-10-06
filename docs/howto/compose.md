<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Compose a spec from several files

Build one spec out of files that each say part of it. `merge` composes
**fragments**: the files of a component library, each owning part of the math.
`override` lays **patches** over a **base**: the spec a framework ships, and
the change a project makes to it. Each loads every fragment and the base with
[`to_spec`](../reference/language/errors.md#what-to_spec-checks) before it
composes them, and hands back the composed spec loaded the same way. Each
takes its files as a list, and the two compose as `override(merge([…]), […])`.

## A library of components

1. **Write the network as a spec.** It balances the injection at a bus, and
   reads the injection under
   [`given`](../reference/language/declarations.md#given): what the components
   put in is theirs to say. It sets the objective on `total_cost`, which it
   reads the same way: what each component costs is the component's to say.
   Nothing in it names a component class.

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

2. **Write each component file against the network.** It declares its own
   dimension and its own math. It reads `Bus_injection` too, and says what it
   puts into a bus as a named expression, a
   [term](../reference/language/declarations.md#terms) whose `adds_to:` names
   `Bus_injection`. A component that costs something adds its cost to
   `total_cost` the same way.

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

   Each file loads on its own and prints as math on its own. Only the
   network sets an objective, so `generator.yaml` on its own is a feasibility
   problem.

3. **Merge the files you need.** Give them as a list. A refusal names a file
   by its path as the list gives it, and a mapping or a loaded spec by its
   place in the list, such as `'#2'`.

   ```python
   import mathspec as ms

   spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml'])
   ```

   `spec` defines `Bus_injection` as `Generator_injection + Load_injection`,
   and keeps each term as a named expression. Nothing is left under `given:`,
   so `spec` is fully defined. The objective is the network's, and
   `total_cost` is `Generator_cost`. The order of the list changes no
   meaning: [`canonical`](compare.md) writes the same text for every order.
   A second file that sets an objective is refused: one fragment sets it,
   and each other one adds its part to the sum it reads.

4. **Add a component without touching the network.** A new file adds its own
   term, and `network.yaml` stays as it is.

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

   Add the file to the list:

   ```python
   spec = ms.merge(['network.yaml', 'generator.yaml', 'load.yaml', 'store.yaml'])
   ```

   `Bus_injection` is `Generator_injection + Load_injection + Store_injection`.
   A merged spec takes a further term the same way, so
   `ms.merge([ms.merge(['network.yaml', 'generator.yaml', 'load.yaml']), 'store.yaml'])`
   gives the same sum.

5. **Give the network a part of its own.** Define the sum in one file instead
   of reading it there. The body that file writes comes first, and every term
   follows it. The component files stay as they are.

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
   ```

   `Bus_injection` is `Bus_slack + Generator_injection + Load_injection`, over
   the `dims:` and with the description of `network_slack.yaml`. One file at
   most defines the sum. Each other file reads it under `given:`.

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
| a given expression                                | the definition's body carries no dimension the reader's `dims` do not name                                                                                                                          |
| a given mask                                      | the reader's `dims` name the dimensions the defining fragment's predicate reads, no more and no fewer                                                                                               |
| a given entry no fragment introduces              | it stays under `given:` until a host model provides it                                                                                                                                              |
| an expression with `adds_to:`                     | the sum it names is the body one fragment defines, if any, followed by every term by its name, in the order of the list. [Terms](../reference/language/declarations.md#terms) gives what is refused |
| `objective`                                       | one fragment sets it, and a second is refused. Several fragments contribute to it as terms of a sum the objective reads                                                                             |
| `version`                                         | every fragment is written against the same one                                                                                                                                                      |
| `description` at the top of a fragment            | it is about the fragment and is not carried. Pass the composed spec's as `description=`                                                                                                             |

## A name two fragments declare

Fragments own their math, so a name two of them declare is refused, both
named. Here two files each say what a generator fleet is:

```text
fragments 'gas.yaml' and 'coal.yaml' both declare the parameter 'Generator_p_nom'. Two of the same kind of thing are two rows of a dimension rather than two fragments: merge the fragment once, and let the data carry both. Different math under one spelling is a rename: call one of them something else.
```

A term is a named expression like any other, so the terms of two fragments
need two names. Name each term after its component, such as
`Generator_injection` and `Load_injection`.

## A column read one way and introduced another

What a fragment states about a column it reads has to agree with the fragment
that introduces the column. The reader may say less, such as the frame with no
`domain`, and may not say something else. Here a file that caps emissions
reads `Generator_p` as binary:

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

```text
fragment 'emissions.yaml' reads the given variable 'Generator_p' as {'dims': ['snapshot', 'generator'], 'domain': 'binary'}, where 'generator.yaml' introduces it as {'dims': ['snapshot', 'generator'], 'bounds': {'lower': 0.0, 'upper': 'Generator_p_nom'}, 'domain': 'continuous', 'absence': 'undefined'}. A given declaration says the same as the declaration it is folded into, or less: restate the frame as the introducer declares it, or leave the field out.
```

Two fragments that both only read a column have to read it the same way, and
a difference is refused as it is for a dimension.

## A fragment that does not load on its own

A fragment is a whole spec, so `merge` loads each one before it composes
them. A fragment `to_spec` refuses is refused under its own name, with the
refusal `to_spec` gives. A sibling cannot make it load. Here the generator
declares `Generator_p` and reads it under `given:` as well:

```text
fragment 'generator.yaml' does not load on its own. A fragment is a whole spec: it declares what it builds, and reads what a sibling builds under 'given:'.
Given variable 'Generator_p' collides with the variable of the same name. Names share one flat namespace — rename one of them.
```

## A base and its patches

1. **Write the base as a spec**, and each patch as the change it makes. A
   patch names only the fields it changes. A declaration a patch does not name
   stays as the base wrote it. A named expression the patch writes on one line
   replaces only the body, `expression:` or `cases:`. The entry keeps its
   `dims:`, its description and its `adds_to:`, so the new body carries no
   dimension outside the kept `dims:`. The base loads on its own, and
   `override` loads it first. A patch is not a spec, so it is laid over as written, and the
   patched spec is loaded after.

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
   patch by its path, as `merge` names a fragment.

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

   A `null` makes what it names absent. On a declaration, the declaration is
   removed. On a field, the field takes its default and the declaration stays:
   `dispatch: { where: null }` gives that variable no mask, and
   `dispatch: { bounds: { upper: null } }` leaves it open above. Higher up,
   `constraints: null` is refused, because a section is not a declaration and
   nulling it removes nothing.

4. **Put a patch that refines another after it.** `override` lays the
   patches in the order of the list, each on the result of the ones before.
   Where two patches write one field, the later one wins. A later patch may
   also edit or remove a declaration an earlier one creates.

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

An entry naming some fields has to land on a declaration the base or an
earlier patch has. A mistyped name is refused rather than read as a new
declaration:

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
patch 'relabelled.yaml' declares the dimension 'snapshot' as {'dtype': 'str'}, where its base declares {'dtype': 'int'}. A patch adjusts the math, not the coordinate space the math is already written over: restate the declaration word for word, leave it out, or give the patch a dimension of its own under a name of its own.
```

`ordered` is a claim about the dimension, not the dimension. A patch may add
it, so a patch that steps along `snapshot` declares it `ordered: true` over a
base that does not. A patch may not take it back, because the base may
already step along it:

```text
patch 'unordered.yaml' says the dimension 'snapshot' is not ordered, where its base declares it ordered. A construct in the base may step along it, and a patch adds the claim of order but never withdraws it: leave `ordered` out of the patch.
```

## A section set to `null`

A `null` removes the declaration it names. A section holds declarations rather
than being one, so nulling a section is refused rather than read as emptying
it:

```text
patch 'project.yaml' sets 'constraints' to null, which removes nothing: the removal marker names one declaration, and a section is not one. Remove the declarations one at a time, each under its own name, or leave the section out of the patch.
```

## A stale removal

A removal says what the base has, so a removal of a declaration the base does
not have is refused with the near miss:

```text
patch 'stale.yaml' removes the constraint 'power_balnce', which its base does not declare. A removal is a claim about what is there, so a stale one is a patch that no longer describes the spec it lands on. Did you mean 'power_balance'?
```
