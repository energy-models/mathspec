<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# How mathspec works

mathspec reads, checks and prints the specification of an optimisation model
([a spec](../reference/glossary.md#spec)). Other software that reads a spec
([tools](../reference/glossary.md#tool)) includes the kind that builds the
model and hands it to a solver ([an engine](../reference/glossary.md#tool)). This
page describes the path of a spec from the file to the tools that
read it, and what mathspec decides before any data exists.

## A spec and a model

A spec is stated in one YAML file, or in several files
that [`merge`](../reference/composition.md#merge) composes. It states the math
of the model in words a reader can check, and it lists four things:

- the dimensions it is indexed over, such as `snapshot` and `generator`
- the tables of data it declares, such as `load` and `cost`
- the decisions a solver makes, such as `dispatch`
- the rules those decisions obey, such as
  `sum(dispatch, over=generator) == load`

A **model** is a spec with data attached, which an engine builds for a
solver.

## From a file to a program

Running [`to_spec`](../reference/api.md#mathspec.to_spec) on a file
([loading](../reference/glossary.md#load) it) returns a `Spec`, which is the
file as written. The `Spec` has the templates
([macros](../reference/language/named.md#macros)), the descriptions, and each
[`piecewise:`](../reference/language/piecewise.md#piecewise) entry as one
entry. In the same call, mathspec turns the spec into the meaning of the file
([a `Program`](../reference/reading.md)), which is to
[compile](../reference/glossary.md#compile) it. In the program, every macro is
expanded and every name has a kind. Each call to a construct built into the
language ([an operator](../reference/language/operators.md)) has the
dimensions of its result.

mathspec checks the file against
[the eleven rules](../reference/language/index.md#the-eleven-rules) as it
compiles the file, with no data.

If the file breaks one of these rules, mathspec refuses it at load and
suggests what to write instead. In this file, the balance sums over
the wrong dimension:

```yaml title="dispatch.yaml"
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  load: { dims: [snapshot] }
  cost: { dims: [generator] }
variables:
  dispatch:
    dims: [snapshot, generator]
    bounds: { lower: 0 }
constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=snapshot) == load
objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

```text
Constraint 'power_balance': the expression carries dims ['generator'] that are not in its dims: ['snapshot']. Add them to dims:, or sum them out.
```

mathspec reports that `generator` is still in the expression after the sum
removes `snapshot`, and that `generator` is not in the `dims` of
`power_balance`. With
`sum(dispatch, over=generator)`, the file loads.

A framework that writes its math as code checks every rule when it builds the
model. So the framework finds a wrong sum only once data is attached. Here
mathspec checks the file at load, and the engine checks only the data. The split is better, because software that reads a spec with no data
([a checker](../reference/glossary.md#tool)) finds a wrong sum in continuous
integration (CI).

## What needs data

Some questions have no answer until the data is attached. mathspec cannot
know whether `load` has a row for every snapshot, or whether a value is not a
number (NaN). It cannot know whether `p_min <= p_max` is true for each
generator either. The file specifies the condition that the data must meet,
and the engine that attaches the data checks the condition.

- [`missing:`](../reference/language/absence.md#missing) on a parameter or a table that pairs labels
  ([a relation](../reference/language/relations.md)) sets what a missing row
  means. When the engine attaches the data, it refuses a missing row by default.
- An [`assumptions:`](../reference/language/assumptions.md) entry is a
  condition that the data must meet.

## The tools that read a spec

Three kinds of tool read the same file for different purposes:

- An **engine**, such as [specsolve](https://github.com/fluxopt/specsolve),
  attaches data, builds the model and hands it to a solver.
- A **renderer** prints the spec as equations. The
  [typesetter](../reference/typeset.md) in mathspec is a renderer, and it
  prints LaTeX, Typst and Markdown from the file alone.
- A **checker** reads the spec with no data, for example in CI. The
  [`check`](../reference/cli.md#check) command loads a file and prints remarks
  that change nothing ([advice](../reference/glossary.md#advice)).

Every tool reads the same `Program`, so the language defines one meaning for
every tool. Each tool
still [decides for itself](what-counts-as-language.md#what-each-tool-decides-for-itself)
what it can build.

## Formulations and their expansion

An entry that expands into others
([a formulation](../reference/glossary.md#formulation)) stays one entry in the
program. A `piecewise:` curve and an
[`sos:`](../reference/language/piecewise.md#sos) set are the two
formulations. The typesetter prints the entry as you wrote it, so a reader
sees one curve and not the variables that state it.

An engine that cannot accept the entry as written builds from its
[expansion](../reference/reading.md#formulations-written-out) instead.
Otherwise each engine would write out a curve in its own way, and two engines
could build different models from one file. Here the language defines the
expansion, so it is the same for every tool.

## Composition

You can write a large spec as several files, each one part of the math
([a fragment](../reference/glossary.md#fragment)). `merge` composes the
fragments into one spec.
[`override`](../reference/composition.md#override) lays a file of changes
([a patch](../reference/glossary.md#patch)) over a base. The result of either
is an ordinary `Spec`, which every tool reads like a spec from one file.

With one file for the whole spec, a reviewer reads all of it to check one
component. Composition is better here, because mathspec loads and typesets
each fragment on its own. So you can review one component without the rest of
the spec.

You can now judge which checks happen at load and which wait for the data,
and which tool makes each one.

!!! info "See also"

    - [the limits of the language](limits.md), for what the language can grow to
      express
    - [what counts as language](what-counts-as-language.md), for which meanings
      the language defines for every tool
    - [versions](versions.md), for how a file and a release of mathspec relate
    - [reading a spec and its program](../reference/reading.md), for the objects
      that `to_spec` returns
