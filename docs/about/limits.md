<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The limits of the language

A spec can only say what the language has words for. This page says which words
can be added, and which cannot. Read it before you ask for a new operator, section
or keyword. For the rules a spec itself has to obey, read
[the eleven rules](../reference/language/index.md#the-eleven-rules).

## Adding a new construct

New constructs can be added, although the overhead to do so varies by kind.

- **A macro** is a template with arguments, written in the file under `macros:`.
  Adding one costs nothing: it uses only operators that exist, so no engine has
  to change ([macros](../reference/language/named.md#macros)).
- **A primitive** is an operator built into the language: `sum`, `sum_back`,
  `at`, `shift`, and the `where` comparisons. Adding one is the most work:
  every engine that builds models has to implement it, and the typesetter has
  to print it in LaTeX, Typst and Markdown.
- **A formulation** is an entry that expands into ordinary variables and
  constraints before the model is built. `piecewise:` and `sos:` are the two
  formulations. A formulation is as much work to build as a primitive, but a
  file combines it with other constructs as freely as a macro. It emits
  variables, constraints and assumptions, and no parameter, so
  [`spec.expand()`](../reference/language/piecewise.md#writing-a-formulation-out)
  writes it out with the data the spec already expects.
- **A section** is a top-level key that holds entries of one kind, such as
  `variables:` or `given:`. A new section enters when all three of these are
  true: it states something no other section states, a file decides it without
  data, and the typesetter prints it. `given:` met all three. It is the only
  section that says a parameter, a column, a named expression or a row family
  belongs to another file, which lets a component file load and print on its
  own.

No other constructs are possible.
See our [table of refusals](#requests-the-language-refuses) for our justification for this decision.

### What a new primitive has to satisfy

A macro must be able to call a new primitive, so everything a modeller can pass
in goes in the value of a keyword argument, such as `over=snapshot`.

An operator must say how many rows it reads for each output row.
`sum(p, over=g)` reads one row per generator, and `shift(p, along=t, offset=1)`
reads the row before. Each reads a bounded number of rows per output row, so an
engine builds the model one chunk of rows at a time. An operator that calls itself is refused, because
nothing bounds how far it expands.

| The operator                                     | Allowed?                                        |
| ------------------------------------------------ | ----------------------------------------------- |
| filters rows on a column they already carry      | yes                                             |
| joins each row against a parameter or a relation | yes                                             |
| reads a fixed number of neighbouring rows        | yes                                             |
| reads only the coordinate labels                 | yes                                             |
| reads every row                                  | yes, at one full pass before any chunk builds   |
| calls itself                                     | no, and the message names what to write instead |

The degree of the result does not decide whether a new primitive is allowed,
because the
[product rule](../reference/language/expressions.md#where-a-product-of-two-variables-is-allowed)
holds for every operator.

A new primitive is finished when the loader lowers it into the program, the
typesetter prints it in all three formats, and an engine's build of a spec that uses it matches
its build of the same spec written out by hand.

### Three kinds of refusal

| The language refuses it because…           | Examples                                                                                                                          | Can it change?                             |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **one solver cannot take it**              | indicator constraints; a quadratic constraint ([solver capability](what-counts-as-language.md#what-each-tool-decides-for-itself)) | yes, solver by solver                      |
| **the file would stop being the artifact** | arbitrary Python, whose content no loader can check and no typesetter can print                                                   | no                                         |
| **this project puts the work elsewhere**   | data preparation such as resampling; helpers for one domain; Python that decides which entries exist                              | it could; this project does not want it to |

## What counts as data preparation

Once attached, a column computed in pandas looks the same as a column the
language could derive. One rule tells them apart:

> Data preparation computes what the spec cannot state. The language derives
> what it can from the data the spec already expects.

A cycle basis is the first kind, because it needs the network's topology and
only the data has that. So `cycle_incidence` arrives as a parameter. A minimum
up time is the second kind, because `min_up_time` is a column the spec already
expects. So `sum_back(window=min_up_time)` reads the width from the column, and
you supply no window mask.

Checking a column is neither kind. Two tools that read the spec must not
answer `p_min <= p_max` differently, so the file states the check as
[an assumption](../reference/language/assumptions.md), and the tool that
attaches the numbers runs it.

## Requests the language refuses

Each row is a request the language refuses, with the reason and what to write
instead.

| Request                                                                                      | Why refused                                                                                                                                                                                               | Instead                                                                                                                                                                                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Resampling, clustering, file IO, unit conversion                                             | not math                                                                                                                                                                                                  | do it in data preparation, and pass a parameter                                                                                                                                                                                                                                                                                                        |
| Unit checking at load                                                                        | a `unit: MW` on a parameter is a claim that nothing checks against the column, and it needs a grammar of units the language then maintains                                                                | convert to one unit system in data preparation, and name it in the `description:`. A range the data has to meet is an [`assumptions:`](../reference/language/assumptions.md) entry                                                                                                                                                                     |
| Array operations such as `merge` and `reindex`                                               | there is no end to them                                                                                                                                                                                   | data preparation                                                                                                                                                                                                                                                                                                                                       |
| Helpers for one domain, such as `reduce_carrier_dim`                                         | writes one field's vocabulary into the language                                                                                                                                                           | a component library of macros over the operators that exist                                                                                                                                                                                                                                                                                            |
| A vocabulary for tracked metrics: `impacts:`, `effects:`, a `costs` axis                     | a named expression already does this                                                                                                                                                                      | an `impact` dimension and one named expression. Cap it with a constraint, weight it in the objective, read it back after the solve                                                                                                                                                                                                                     |
| `**` with a variable in the base or the exponent                                             | the exponent would decide the degree, and `to_spec` reads no data                                                                                                                                         | `x * x` for a square. `**` over parameters and numbers is allowed                                                                                                                                                                                                                                                                                      |
| Normalisation, `x / sum(x)`                                                                  | dividing by a variable is not a polynomial, and no solver takes it                                                                                                                                        | write the ratio as a constraint, or fix the denominator                                                                                                                                                                                                                                                                                                |
| An `if`, a loop, or entries that depend on the data                                          | `to_spec` could no longer read the file without the data                                                                                                                                                  | `where:` masks and `dims:` dimensions. A tool may loop over specs                                                                                                                                                                                                                                                                                      |
| A Python API for building specs                                                              | the spec is the file you review and diff                                                                                                                                                                  | YAML, or a `dict` with the same keys, merged before `to_spec`                                                                                                                                                                                                                                                                                          |
| A `where` comparing a relation column against the dimension it maps into                     | the relation already pairs the two, and a mask over the pair is the same fact in a bigger shape                                                                                                           | place the quantity with `sum(by=)`, or read it with `at(by=)` ([operators](../reference/language/operators.md#sum))                                                                                                                                                                                                                                    |
| A `join` operator apart from `sum` and `at`, such as `sum(join(p, gen_bus), over=generator)` | a join adds an axis for each column that the sum then removes. That axis is not a dimension, so no entry can carry it. One call adds the axis and removes it again, so no file can leave an axis in place | `sum(p, over=generator, by=gen_bus[bus])` adds up each group, and `at(x, by=gen_bus[bus])` reads one row ([relations](../reference/language/relations.md#how-a-relation-is-used))                                                                                                                                                                      |
| A `count(...)` compared against a parameter or an expression                                 | a count is a whole number of coordinates, and the loader decides it without data. A bound read from a column can only be decided when the data is attached                                                | data preparation supplies the number, and the spec trusts it. The PyPSA example does this for `StorageUnit_inactive_snapshots` and `Store_inactive_snapshots`: no assumption checks them against `count(NOT {c}_active, over=snapshot)`. Compare against a literal ([counting](../reference/language/expressions.md#counting-what-a-predicate-admits)) |
