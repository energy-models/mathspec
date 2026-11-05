<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Python API

The `mathspec` package provides the functions that load, compose, print and
check the specification of an optimisation model ([a spec](glossary.md#spec)).
This page lists each of them with its signature, its arguments and the errors
it raises, grouped by task. The functions you call are at the top level, and
the classes, constants and errors are in three modules:

| What it is                                                                                                                                     | It lives in        | Such as                                        | Documented on             |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ---------------------------------------------- | ------------------------- |
| a function you call                                                                                                                            | `mathspec`         | `to_spec`, `merge`, `typeset`, `advice`        | this page                 |
| the `Spec` that `to_spec` returns, the entries of a `Spec`, and the operators an expression may call                                           | `mathspec.spec`    | `Spec`, `VariableSpec`, `BUILTIN_NAMES`        | [Spec API](spec.md)       |
| the `Program` that `spec.program` returns, the nodes of a `Program`, and what mathspec reports without refusing ([advice](glossary.md#advice)) | `mathspec.program` | `Program`, `Sum`, `Mask`, `Advice`             | [Program API](program.md) |
| an error you catch, and the helper that suggests a name                                                                                        | `mathspec.errors`  | `LanguageError`, `SchemaError`, `did_you_mean` | [Errors](#errors) below   |

`SymbolTable` and the type `FormatName` are also at the top level. You pass a
`SymbolTable` as the `symbols` argument of a function that prints math
([a typesetting function](typeset.md)). You pass a `FormatName`, such as
`'latex'`, as the `fmt` argument of `typeset` or `typeset_line`.

A module whose name starts with an underscore is private
([what counts as public API](../about/what-counts-as-public-api.md)).

## Guarantees

Every public function keeps three guarantees:

- A function keeps no state, and uses no registry, no plugin, and no setting
  that changes what a spec means.
- A function returns a value or raises an error, and nothing between.
  `to_spec` either returns a `Spec`, or raises an error that suggests the
  rewrite. `advice()` reports on a file that loads, and changes nothing.
- A function writes out no entry that expands into ordinary entries
  ([a formulation](glossary.md#formulation)) unless the caller asks. A
  [`piecewise:`](language/piecewise.md) or [`sos:`](language/piecewise.md#sos)
  entry stays one entry until the caller calls
  [`spec.expand()`](spec.md#mathspec.spec.Spec.expand).

<!-- prettier-ignore-start -->

## `to_spec`

::: mathspec.to_spec
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

## `merge` and `override`

[Composing specs](composition.md) describes what `merge` and `override` do
with their files, and [compose a spec from several files](../howto/compose.md)
lists the steps.

::: mathspec.merge
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

::: mathspec.override
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

## The typesetting API


::: mathspec.to_latex
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

::: mathspec.to_typst
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

::: mathspec.to_markdown
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

::: mathspec.typeset
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

::: mathspec.typeset_line
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

::: mathspec.FormatName
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

::: mathspec.SymbolTable
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

## `advice`

`advice` returns a tuple of [`Advice`](program.md#mathspec.program.Advice),
one for each piece of [advice](glossary.md#advice).

::: mathspec.advice
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

## Errors

::: mathspec.errors
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3
      members_order: source

<!-- prettier-ignore-end -->

!!! info "See also"

    - [Spec API](spec.md)
    - [Program API](program.md)
    - [Typeset output](typeset.md)
    - [Errors and advice](language/errors.md)
