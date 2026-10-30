<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Glossary

On every page, the mathspec documentation uses each word below in one fixed
sense. A key of the file, such as `parameters:` or `macros:`, is defined on its
[language page](language/index.md), and the entry here links that page.

## Absence

Absence is the lack of a value at a [coordinate](#coordinate). A variable
that a [`where:`](#where) leaves out has no [column](#column) at that
coordinate. An absent value is not zero, and the rules for an expression that
uses one are in [how absence travels](language/absence.md#how-absence-travels).

## Advice

Advice is what mathspec reports about a file that loads but looks wrong.
`mathspec.advice(spec)` returns it, and `python -m mathspec check` prints it.
A dimension that no entry is indexed over gets advice of the kind
`never-an-axis`
([what advice warns about](language/errors.md#what-advice-warns-about)).

## Attach

An [engine](#tool) attaches data: it combines tables of data with a spec. A
rule about the data, such as "every generator has a cost", can be checked only
after the data is attached. mathspec checks no such rule itself.

## Bare relation

A bare relation is a relation with no `values:`, so every column identifies a
row. A bare relation lists which combinations of labels exist, and a `where:`
on it is true where a row exists ([relations](language/relations.md)).

## Base

A base is a whole spec that another party extends, such as the spec that a
framework ships. `override` lays [patches](#patch) over a base
([composing specs](composition.md#override)).

## Breakpoint

A breakpoint is one corner of a `piecewise:` curve, at one label of its
ordered `over` dimension. There the expressions under `links:` take their
values from the data. Straight lines join neighbouring breakpoints
([piecewise](language/piecewise.md#piecewise)).

## Canonical form

The canonical form is one fixed way to write a spec. Two files that state the
same spec have the same canonical form, even when their spacing differs. The
order of their entries, and of the parts of a sum, makes no difference either.
`python -m mathspec canonical` prints the canonical form, and `diff` compares
two files through it ([compare two specs](../howto/compare.md), [command
line](cli.md)).

## Column

A column is one variable at one coordinate, so a variable indexed over
`generator` has one column per generator. In a data table or a relation, a
column is one named field of the table.

## Compile

To compile a spec is to turn it into its [program](#program). `to_spec`
compiles the spec in the same call that loads the file. When `to_spec`
compiles the spec, mathspec checks every rule that the file alone settles
([how mathspec works](../about/overview.md)).

## Condition

A condition is a true-or-false expression, written in the
[condition grammar](language/expressions.md#conditions). A condition under
[`where:`](language/absence.md#where) selects the rows of an entry, and a
condition under [`when:`](language/named.md#cases) selects the rows of one
case of an expression. An entry under `conditions:` declares a named condition
([named conditions](language/named.md#conditions)). When the data is attached,
a tool checks each condition that an assumption requires (`holds:`)
([assumptions](language/assumptions.md)).

## Coordinate

A coordinate is one point of the dimensions of an entry, such as one generator
in one snapshot. A variable has one column at each coordinate it is built at,
and a constraint has one row at each coordinate.

## Data preparation

Before the data is attached, data preparation is the work of turning raw data
into the tables that a spec declares as parameters and relations. You compute
in data preparation anything that the mathspec language cannot state
([what counts as data preparation](../about/limits.md#data-preparation)).

## Entry

An entry is one named item under one [section](#section), such as one
dimension, one parameter or one constraint. In Python, an entry is an instance
of a `*Spec` class in `mathspec.spec`, such as `VariableSpec`. In a program, an
entry is an instance of the class with the same name without `Spec` in
`mathspec.program`, such as `Variable` ([file shape](language/file.md)).

## Expansion

The expansion of a spec is the spec with each [formulation](#formulation)
written out as the variables, constraints and assumptions it states.
`spec.expand()` returns the expansion, and `--expand` prints it. Every name
that a formulation adds starts with the name of the formulation ([writing a
formulation out](language/piecewise.md)). So one variable of the curve
`fuel_cap` is `fuel_cap_lam`.

## Formulation

A formulation is an entry that expands into ordinary variables, constraints
and assumptions before the model is built. `piecewise:` and `sos:` are the two
formulations ([piecewise curves and SOS](language/piecewise.md)). A file cannot
add a formulation, and a change to mathspec can.

## Fragment

A fragment is a whole spec that states one part of a larger spec. An example
is the generator file of a set of files that `merge` joins
([a component library](../examples/library/index.md)). `merge` joins fragments
as peers, and each fragment loads on its own ([composing
specs](composition.md#merge)).

## Frame

The frame of an entry is the set of dimensions it is indexed over. The
dimensions of an expression, of a condition and of a parameter in the bounds of
the entry must fit inside that frame. A constraint indexed over `snapshot`
cannot use a parameter over `generator` without summing `generator` away ([how
dimensions combine](language/expressions.md#how-dimensions-combine)).

## Given

A given entry is a name that a file uses and another file declares, listed
under `given:`. A given entry can be a parameter, a variable, a named expression, a
named condition, or the rows of one constraint (a row family). Another file, or
the engine that this spec is attached to, **provides** the name. The provider
has an entry of the same kind and name, over the same dimensions. With data
attached, a tool checks that each given name is provided
([given](language/parameters-variables-constraints.md#given), [what a program
does not build](reading.md#what-a-program-does-not-build)).

## Group

A group is the set of rows of a relation that share one label in a value
column. `within=<relation>[<column>]` makes `shift`, `sum_back` or
`position()` work separately in each group, such as each season of a year
([partitions](language/relations.md#partitions)).

## Label

A label is one member of a dimension, such as `wind` in `generator`. The
labels arrive with the data, in the order that `shift`, `sum_back` and
`position()` count along.

## Load

To load a file is to run `to_spec` on it. "mathspec refuses the file at load"
means that `to_spec` raises an error before any data exists. mathspec refuses
a misspelt variable name in a constraint at load
([errors and advice](language/errors.md)).

## Macro

A macro is a template that takes arguments and is substituted into an
expression before any tool reads it. A file declares its own macros under
`macros:`, so a macro is the one construct a file can add
([macros](language/named.md#macros)).

## Missing row

A missing row is a coordinate for which the table of a parameter or a relation
has no row. The `missing:` key of the entry sets how a tool treats that
coordinate ([`missing` on a
parameter](language/absence.md#missing-on-a-parameter)).

## Model

A model is a spec with data attached, and a solver takes the model. mathspec
has no data, so mathspec alone cannot build a model. A file or a `Spec` in hand
is a spec, and only what an engine builds from it is a model.

## Operator

An operator is a construct built into the language
([operators](language/operators.md)). Every engine implements each operator,
and the functions that print math
([the typesetter](typeset.md)) print it. The operators include `sum`,
`sum_back`, `at`, `shift`, and the comparisons in a condition. A file cannot
add an operator. A change to mathspec can add one, and the [contributing
page](../contributing.md#what-a-new-operator-has-to-satisfy) lists what a new
operator has to satisfy.

## Ordered

A dimension is ordered when the file declares it `ordered: true`. Five
constructs use the order of the labels and require an ordered dimension. They
are `shift`, `sum_back`, `position()`, a `piecewise:` curve and an `sos:` set
of `type: 2`. A `dtype` of `int` does not make a dimension ordered
([order](language/dimensions.md#ordered)).

## Patch

A patch is a file that states only a change to a base, such as one project's
edits to a framework's spec. `override` does not load a patch alone, and lays
the patch over the base and loads the result ([composing
specs](composition.md#override)).

## Pin

To pin a variable is to give it one value as both its lower and its upper
bound. A pinned variable is still a variable in the spec. So even where `size`
is pinned, `size * on` is a product of two variables ([fix a
quantity](../howto/pin-a-variable.md)).

## Program

A program is what the file means once mathspec has [compiled](#compile) it.
In a program, every name is typed, every macro is expanded, and every operator
is a node with the dimensions of its result. In Python, a program is a
`Program`, which `spec.program` returns ([Program API](program.md)).

A linear or quadratic program that a solver takes is a [model](#model), not a
program in this sense.

## Row

A row is one constraint at one coordinate, so a constraint indexed over
`snapshot` has one row per snapshot. In a data table or a relation, a row is
one line of the table ([missing row](#missing-row)).

## Rung

A rung is one step of a series of example networks (the PyPSA ladder) that
an open-source power system modelling framework ([PyPSA](https://pypsa.org))
solves. Each rung states one
`n.optimize()` keyword in full ([PyPSA in one file](../examples/pypsa_ladder.md)).

## Section

A section is a top-level key of a file, such as `parameters:` or `given:`,
together with the entries under it. Every top-level key except `version` and
`description` is a section key, thirteen in all
([file shape](language/file.md)).

A heading of a typeset document, such as Definitions, is a heading of the
document, not a section in this sense.

## Spec

A spec is the optimisation problem stated by one file, or by the files that
`merge` joins. It declares its dimensions, its decisions, its rules and the
data it expects, but no values. The word is short for specification. In
Python, a spec is a `Spec`, which contains the file as written and checked, and
which `to_spec` returns ([reading a spec and its
program](reading.md#spec-and-program)). A file that declares `generator`,
`snapshot`, `dispatch` and a balance constraint is a spec before any table of
costs exists.

## Special ordered set (SOS)

A special ordered set (SOS) is an `sos:` entry over one dimension of one
variable. With `type: 1`, at most one member is non-zero. With `type: 2`, at
most two consecutive members are non-zero ([sos](language/piecewise.md#sos)).

## Surface

A surface is the fragment that declares what the other fragments of a library
share, such as the flows, the balances and the objective. Each other fragment
is written against the surface ([the coupling
surface](../examples/library/surface.md)).

## Term

A term is a named expression that adds to a sum another file declares. The
value of the term's `adds_to:` key is a given expression of the same file, and
that given expression means the whole sum. When `merge` joins the fragments,
the sum contains the terms of every fragment ([terms](language/named.md#adds_to)).

A part of a sum written inside one expression, such as `p * cost` in
`sum(p * cost) + sum(q)`, is not a term in this sense.

## Tool

A tool is any piece of software that reads a spec. There are three kinds:

- An **engine** attaches data and builds the model, as the model builder
  [specsolve](https://github.com/fluxopt/specsolve) does.
- A **renderer** prints the spec, as the [typesetter](typeset.md) prints LaTeX,
  Typst and Markdown.
- A **checker** reports on the spec without building it, as
  [`advice`](language/errors.md#what-advice-warns-about) does.

## `where:`

A `where:` narrows an entry to the coordinates where its condition is true,
and leaves the entry absent everywhere else. In Python, the value of a
`where:` is a `Mask` object ([nodes and
conditions](reading.md#nodes-and-conditions)).

!!! info "See also"

    - [The language](language/index.md), for every key of a file
    - [Reading a spec and its program](reading.md), for the objects a tool reads
