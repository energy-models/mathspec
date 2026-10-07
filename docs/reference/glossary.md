<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Glossary

We use several words in these docs with one fixed sense.
Unlike constructs like `parameter` or `macro` (defined in their respective [language pages](language/index.md)), no single reference page defines these words.

## The file and its readers

**Spec**
: Short for specification. A spec is the optimisation problem that a file
states: its dimensions, the data it expects, its decisions and its rules, but
no data. In Python it is a `Spec`, the file as written and checked, which
`to_spec` returns
([reading a spec and its program](reading.md#spec-and-program)).

**Model**
: A spec with data attached, which an engine builds and a solver takes.
mathspec alone cannot hold a model.

**Program**
: What the file means once it has been parsed by mathspec: every name typed, every macro expanded,
every operator a node.
In Python it is a `Program`, accessed at `spec.program`.

**Consumer**
: A tool that reads a spec: an **engine** that attaches data and builds the model, a **renderer** such as the typesetter, or a **checker**.

**Load**
: What the `to_spec` method does. "Refused at load" means `to_spec` raises, before any
data exists.

**Attach**
: What a consumer does when it combines data with a program.
A consumer can only check a rule involving data after it has attached; mathspec checks no such rule itself.
The docs will never say "bind" when they refer to this, so that **bound** means one thing: a lower or upper
limit on a variable ([variables](language/parameters-variables-constraints.md#variables)).

**Provide**
: What a host model does for a name under `given:`, when layering several files.
The host model will hold a column or a row family of that name, on the same frame.
A consumer is responsible for checking that the host provides each given name
([what a program does not build](reading.md#what-a-program-does-not-build)).

**Entry**
: One named item under one of the top-level keys: one dimension, one
parameter, one constraint ([file shape](language/file.md)).

## Coordinates

**Label**
: One member of a dimension, `wind` say. The labels arrive with the data, in
the order that `shift`, `sum_back` and `position()` count along.

**Coordinate**
: One point of an entry's dimensions: one generator in one snapshot. A
variable has one column at each coordinate it is built at, and a constraint
has one row.

**Frame**
: The dimensions over which an entry ranges.
The data of an expression, a mask and a bound parameter must fit inside their defined frame
([how dimensions combine](language/expressions.md#how-dimensions-combine)).

**Group**
: The labels of a relation `value` column, used for grouping the relation's keys.
`within=<column>` can be used to apply `shift`, `sum_back` or `position()` separately per group.

## Masks and absence

**Mask** · **predicate**
: A predicate is a true-or-false expression in the
[where grammar](language/expressions.md#where-strings). A mask is a predicate
on an entry, and the coordinates it admits.

**Absence**
: No value at a coordinate. A masked-out variable has no column there, and a
row that reads it is not built ([absence](language/absence.md)).

**Missing row**
: A coordinate that a parameter's or a relation's table has no row for. Its
`missing:` says what it is: refused when the data is attached (`refused`, the
default), absence (`absent`), `0` in arithmetic and false in a `where`
(`neutral`), or a value
([a missing row](language/parameters-variables-constraints.md#a-missing-row)).

## Kinds of construct

**Primitive**
: A construct built into the language, which every engine implements and the
typesetter prints.
This covers the operators and the `where` comparisons.

**Formulation**
: An entry that states ordinary variables and constraints rather than being
one: `piecewise:` and `sos:` ([piecewise curves and SOS](language/piecewise.md)).

New constructs (primitives, formulations, macros) are not allowed ([how a new construct enters](../about/limits.md#adding-a-new-construct)).

## Words with two senses

The meaning of some words changes depending on the context in which they appear in the docs.

| Word     | One sense                                               | The other sense                                               |
| -------- | ------------------------------------------------------- | ------------------------------------------------------------- |
| row      | a constraint at one coordinate                          | one line of a parameter's or a relation's table               |
| column   | a variable at one coordinate                            | one column of a data table or a relation                      |
| set      | an `sos:` entry                                         | the set symbol of a dimension, $\mathcal{G}$, in the legend   |
| regime   | one case of a [`cases:`](language/named.md#cases) block | one of two constraints, each under its own `where:`           |
| domain   | a variable's `continuous`, `integer` or `binary`        | the rows that hold a curve's link inside its breakpoint range |
| program  | `spec.program`, the typed spec                          | a linear or quadratic program, the problem a solver takes     |
| the rows | the constraint rows of a spec                           | the expanded spec: the spec a formulation is written out as   |
