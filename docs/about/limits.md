<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The limits of the language

This page describes which constructs can be added to the language and who
adds each, which requests mathspec refuses, and what you write instead. The
[language index](../reference/language/index.md#the-eleven-rules) lists the rules that the specification of an optimisation model
([a spec](../reference/glossary.md#spec)) must obey.

## New constructs

A new construct is one of four kinds, and mathspec refuses a construct of any
other kind. The kinds differ in who must do the work. It falls on the author of a file,
the developers of mathspec, or the developers of each piece of software that builds
models ([an engine](../reference/glossary.md#tool)).

An [**operator**](../reference/language/operators.md), such as `sum` or
`shift`, is built into the language, and no file can add one. Only the
developers of mathspec add one, and a new operator is the most work. Every
engine must implement it, and the [typesetter](../reference/typeset.md) must
print it in LaTeX, in the typesetting system [Typst](https://typst.app), and
in Markdown.

A closed set of operators is better here than a set that a file or a plugin
can extend. With a closed set, every piece of software that reads a spec
([a tool](../reference/glossary.md#tool)) can read every file. Suppose that a modeller writes a `roll` operator as a
Python function. The engine that has the function builds the model, but the
typesetter cannot print `roll`. Software that reads a spec without data
([a checker](../reference/glossary.md#tool)) cannot load the file either. A template substituted into an expression
([a macro](../reference/language/named.md#macros)) does most of what such a
function would do.

A new operator must meet the conditions that the
[contributing guide](../contributing.md#what-a-new-operator-has-to-satisfy)
lists. The first two exist so that a macro can call every operator, and so
that an engine can build every model in chunks. A macro passes on what a
modeller writes only as the value of a keyword argument. So an operator that
takes everything in that form is one that a macro can call.

An engine builds the model one chunk of rows at a time. For each row of its
result, `sum(p, over=g)` reads one row per generator, and
`shift(p, along=t, offset=1)` reads the row before. Chunks work only because
every operator reads a bounded number of rows for each row of its result.

mathspec refuses a macro that calls itself, because nothing bounds how far it
expands. A new operator must not call itself, for the same reason.

mathspec accepts a new operator whatever the highest power of a variable in
its result ([its degree](../reference/language/expressions.md#division-and-powers)),
because the [product rule](../reference/language/expressions.md#where-a-product-of-two-variables-is-allowed)
applies to every operator.

A macro, a formulation and a section are the other three kinds:

- A file declares a macro under
  [`macros:`](../reference/language/named.md#macros). A new macro
  needs no change to any engine, because a macro uses only operators that
  exist.
- A [**formulation**](../reference/language/piecewise.md) is an entry that
  expands into ordinary variables and constraints before the model is built.
  Only the developers of mathspec add one, and the work falls on mathspec. An
  engine that cannot accept a formulation may build from its
  [expansion](../reference/reading.md#formulations-written-out) instead. In a file, you can
  combine a formulation with other constructs as you can a macro. When mathspec expands a formulation, it adds no parameter, so
  [`spec.expand()`](../reference/spec.md#mathspec.spec.Spec.expand) needs no
  data beyond the tables that the spec already declares.
- A **section** is a top-level key of a spec file, such as `variables:`. Only the developers of mathspec add one. A new section must
  meet three conditions. It states something that no other section states,
  mathspec can check its entries without data, and the typesetter prints
  them. The
  [`given:`](../reference/language/parameters-variables-constraints.md#given)
  section, which lists entries that another file of the spec
  ([a fragment](../reference/glossary.md#fragment)) declares, meets all three.

## What mathspec refuses

mathspec refuses a request for one of four reasons. They are solver
capability, meaning that needs data or code, a construct the language already
has, and a computation on the data.

### Solver capability

mathspec refuses a construct that only some solvers take, or that no solver
takes, so that every engine can build every file. This limit changes as
solvers change.

| Request                                                             | Why refused                                                                                    | What you write instead                                                            |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Indicator constraints, which apply only when a binary variable is 1 | Only some solvers take them.                                                                   | A linear constraint. Every solver takes one.                                      |
| Normalisation, `x / sum(x)`                                         | A quotient with a variable divisor is not linear, and no linear or quadratic solver takes one. | A constraint on the ratio, or a parameter as the divisor. Both are linear in `x`. |

### Meaning that needs data or code

mathspec refuses a request when [`to_spec`](../reference/api.md#mathspec.to_spec)
could no longer read the file without data or without running code. This
limit does not depend on what solvers take.

| Request                                                      | Why refused                                                                                                                            | What you write instead                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Arbitrary Python                                             | mathspec cannot check it, and the typesetter cannot print it.                                                                          | A [macro](../reference/language/named.md#macros), or [data preparation](#data-preparation). You compute in data preparation what the language cannot state.                                                                                                                                                                        |
| `**` with a variable in the base or the exponent             | mathspec reads [the degree](../reference/language/expressions.md#division-and-powers) only from a product written out.                 | A product written out, such as `x * x` for a square. `**` over parameters and numbers loads.                                                                                                                                                                                                                                       |
| An `if`, a loop, or entries that depend on the data          | The rows of an entry would depend on values known only when the data is attached.                                                      | The dimensions under `dims:` and a [`where:`](../reference/language/absence.md#where) condition. Together they set which rows an entry has, and a tool may loop over specs.                                                                                                                                                        |
| A `count(...)` compared against a parameter or an expression | Only a tool with the data attached can check a bound that a [`count`](../reference/language/expressions.md#count) takes from a column. | A parameter from data preparation. The [example for the energy system framework PyPSA](../examples/pypsa_ladder.md) declares `StorageUnit_inactive_snapshots` and `Store_inactive_snapshots`, and has no assumption that compares them with `count(NOT {c}_active, over=snapshot)`. A count compared against a whole number loads. |

### Constructs the language already has

mathspec refuses a request when a construct that exists already states the
same thing.

| Request                                                                                                                                         | Why refused                                                                                                         | What you write instead                                                                                                                                                                                                                                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A `where` comparing a column of a table that pairs labels ([a relation](../reference/language/relations.md)) against the dimension it maps into | Two dimensions cannot be compared, so mathspec refuses the comparison. The relation already lists each pair.        | A sum or a lookup through the relation. `sum(x, over=d, by=relation[c])` adds each value of `x` to the coordinate that the relation lists for it, and `at(x, by=relation[c])` takes the value at that coordinate ([operators](../reference/language/operators.md#sum)). |
| A vocabulary for tracked metrics: `impacts:`, `effects:`, a `costs` dimension                                                                   | A tracked metric is already a [named expression](../reference/language/named.md#expressions).                       | An `impact` dimension and one named expression. A constraint can cap the expression, the objective can weight it, and a tool reads it back after the solver runs.                                                                                                       |
| Helpers for one domain, such as `reduce_carrier_dim`                                                                                            | A macro already states a helper.                                                                                    | A [component library](../examples/library/index.md) of macros. Its macros use only the operators that exist.                                                                                                                                                            |
| A Python application programming interface (API) for building specs                                                                             | The file is already the API, and the file is what you review and diff.                                              | YAML, or a `dict` with the same keys. A tool can combine dicts before it calls `to_spec`.                                                                                                                                                                               |
| A `join` operator apart from `sum` and `at`, such as `sum(join(p, gen_bus), over=generator)`                                                    | [`sum(by=)` and `at(by=)` already state a join](relations-as-linear-maps.md#why-the-language-has-no-join-operator). | A sum or a lookup with `by=`, as in the first row.                                                                                                                                                                                                                      |

### Data preparation

mathspec refuses a request that changes the tables themselves, such as
resampling a time series. You make that change before the data is attached, in
the work that turns raw data into the tables a spec declares
([data preparation](../reference/glossary.md#data-preparation)).

Once the data is attached, a column computed with the data-analysis library
[pandas](https://pandas.pydata.org) and a column computed by an expression look
the same. So mathspec sets one rule for where a quantity is computed. A
quantity that an expression can compute from other parameters belongs in the
spec. A quantity that no expression can compute, such as the result of a search
over a network, comes from data preparation.

The set of independent loops in a network (a cycle basis) belongs in data
preparation. A cycle basis requires the topology of the network, and only the
data contains the topology. So the spec declares `cycle_incidence` as a
parameter.

The window of the shortest time a unit stays on (its minimum up time) belongs
in the spec.
The spec already declares the parameter `min_up_time`. So
[`sum_back(window=min_up_time)`](../reference/language/operators.md#sum_back)
takes the width of each window from that parameter, and you write no `where:` to fix the width.

A check on a column, such as `p_min <= p_max`, is a condition on the data
([an assumption](../reference/language/assumptions.md)). Every tool that reads
the spec must get the same result from the check. So the spec states the check as an
assumption, and the engine that attaches the data runs it.

| Request                                                                                         | Why refused                                                                                                  | What you write instead                                                                                                                                                                   |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Resampling, clustering, file input and output, unit conversion, combining and reindexing tables | Each one changes the tables themselves, which the spec only declares. The list has no end.                   | Data preparation. The spec declares the result as a parameter.                                                                                                                           |
| Unit checking at load                                                                           | mathspec would need a grammar of units to check them. You already apply the units when you convert the data. | One unit system from data preparation. The `description:` states the system, and an [`assumptions:`](../reference/language/assumptions.md) entry states a range that the data must meet. |

You can now judge whether a request is a macro, a change to mathspec, a parameter from data preparation, or a refused request.

!!! info "See also"

    - [what counts as language](what-counts-as-language.md), for the meanings
      that the language defines once for every tool
    - [why the language has no join operator](relations-as-linear-maps.md#why-the-language-has-no-join-operator),
      for the refused `join` operator
    - [what each tool decides for itself](what-counts-as-language.md#what-each-tool-decides-for-itself),
      for the refusals that a tool makes for its own solver
