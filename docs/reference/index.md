<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Reference

The reference pages describe exactly what mathspec accepts, what it refuses,
and what it prints. The [tutorials](../tutorials/index.md) teach the
language to a reader who has not yet written the specification of an
optimisation model ([a spec](glossary.md#spec)).

## The language

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[The language](language/index.md)** lists the rules a spec file must meet, and
    which page states each rule in full.
- **[File shape](language/file.md)** lists the top-level keys of a spec file, and
    how mathspec reads the YAML.
- **[Given, parameters, variables, objective and constraints](language/parameters-variables-constraints.md)**
    lists the keys of the data, the decisions, the rules and the goal, and of the
    `given:` section.
- **[Dimensions](language/dimensions.md)** lists the keys of a named set of
    labels (a dimension).
- **[Relations](language/relations.md)** lists the keys of a table between two
    dimensions (a relation), and how an expression uses a relation.
- **[Expressions](language/expressions.md)** defines the grammar of arithmetic and of
    conditions, and how dimensions combine.
- **[Named expressions, conditions and macros](language/named.md)** describes the
    three ways to name a piece of an expression and use it again.
- **[Operators](language/operators.md)** lists every construct built into the
    language (an operator), such as `sum` and `shift`, and the math mathspec
    prints for each.
- **[Piecewise curves and SOS](language/piecewise.md)** lists the keys of a
    piecewise-linear curve and of a special ordered set (SOS).
- **[Assumptions](language/assumptions.md)** lists the keys that state what a spec
    expects of its data.
- **[Absence and where](language/absence.md)** describes which rows do not
    exist (absent), and how absence spreads through an expression.
- **[Errors and advice](language/errors.md)** lists what mathspec refuses at load,
    and what it advises without refusing.

</div>

## Tools and the Python API

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Composing specs](composition.md)** describes the rules that
    [`merge`](api.md#mathspec.merge) and [`override`](api.md#mathspec.override)
    follow when they build one spec from several files.
- **[Typeset output](typeset.md)** describes the document that mathspec prints
    in each output format, LaTeX, Typst and Markdown.
- **[Command line](cli.md)** lists every command of `python -m mathspec`, its
    flags with their Python keywords, and its exit codes.
- **[Python API](api.md)** lists every public function of the `mathspec`
    package, and where each class is documented.

</div>

## Glossary and changelog

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Glossary](glossary.md)** defines each word these pages use in a fixed sense.
- **[Changelog](changelog.md)** lists what changed in each release.

</div>

## Examples

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Examples](../examples/index.md)** are whole specs, each beside the math
    that mathspec prints from it.

</div>

!!! info "See also"

    - [Reading a spec and its program](reading.md), reference for a person who
      writes a tool that reads a spec, such as an engine or a renderer
