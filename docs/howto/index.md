<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# How-to guides

Each guide lists the steps toward one task, for a reader who already writes
the specification of an optimisation model ([a spec](../reference/glossary.md#spec)).
To learn the language from the start, follow the
[tutorials](../tutorials/index.md) first.

## Set up and check

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Install mathspec](installation.md)** into a Python environment, and set up
    your editor to complete the keys of a spec file.
- **[Check a spec without data](check.md)** on your machine and in continuous
    integration (CI), and read a refusal or a remark that is not one
    ([advice](../reference/glossary.md#advice)).

</div>

## Write a spec

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Choose between a dimension, a relation and a parameter](declare-a-column.md)**
    for a column of your data.
- **[State a rule that differs by case](cases.md)**, such as committable and
    non-committable generators, in one spec.
- **[Fix a quantity that is data in one model and a decision in another](pin-a-variable.md)**
    with one spec file.

</div>

## Print, compare and compose

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Print a spec as math](print.md)** in LaTeX, Markdown or a typesetting system
    ([Typst](https://typst.app)), with the symbols your field uses.
- **[Compare two specs](compare.md)** so that a diff contains only what the
    specs state differently.
- **[Compose a spec from several files](compose.md)** with
    [`merge`](../reference/composition.md#merge) for a component library, and
    with [`override`](../reference/composition.md#override) for the changes a
    project lays over a shared spec.

</div>

## Work with piecewise curves and SOS

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Write a piecewise curve out by hand](curve-by-hand.md)** where the number of
    flows on the curve is data.
- **[See what a piecewise curve or an SOS expands to](see-an-expansion.md)**
    as plain variables and constraints, for a special ordered set
    ([an SOS](../reference/glossary.md#special-ordered-set-sos)).

</div>

!!! info "See also"

    - [Tutorials](../tutorials/index.md), for a first spec built step by step.
    - [Reference](../reference/index.md), for every key and operator of the
      language.
