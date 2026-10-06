<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Python API

This page documents every name that `import mathspec` exports, grouped by
task. The top level holds what you call. Three modules hold the rest:

| Module             | Holds                                                   | Documented on             |
| ------------------ | ------------------------------------------------------- | ------------------------- |
| `mathspec.spec`    | what the file says: `Spec` and its blocks               | [Spec API](spec.md)       |
| `mathspec.program` | what the file means: `Program`, its nodes, and `Advice` | [Program API](program.md) |
| `mathspec.errors`  | what you catch: the error tree, and `did_you_mean`      | [Errors](#errors) below   |

<!-- prettier-ignore-start -->

## Loading

::: mathspec.to_spec
    options:
      show_root_heading: true
      show_root_toc_entry: true
      heading_level: 3

## Composing

[Compose a spec from several files](../howto/compose.md) shows both in use.

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

## Typesetting

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

::: mathspec.typeset_declaration
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

## Advice

`advice` returns a tuple of [`Advice`](program.md#mathspec.program.Advice).

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
