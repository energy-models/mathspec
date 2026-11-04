<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# What counts as public API

The public application programming interface (API) of mathspec is the set of
names you import from it, such as
[`to_spec`](../reference/api.md#mathspec.to_spec) and
[`to_latex`](../reference/typeset.md). A function joins it when both of these
are true:

1. The function returns the same result for the same specification of an
   optimisation model ([a spec](../reference/glossary.md#spec)).
   `to_spec('spec.yaml')` returns the same `Spec` today, tomorrow, and on a
   machine with no data and no solver. A function whose result depends on
   data, a solver, the network or the clock cannot join. The rule exists because software that reads a spec without data
   ([a checker](../reference/glossary.md#tool)) and software that builds the
   model ([an engine](../reference/glossary.md#tool)) must get one result.
2. Every rule that the function applies is on a page of the reference. So you
   could rewrite the function in another programming language from the pages
   alone, and get the same result. The rule exists because software that reads a spec
   ([a tool](../reference/glossary.md#tool)) may be written in another programming language. Such a tool has only the pages to go by.

The test file `tests/test_public_surface.py` lists the names that `mathspec`
exports and the list of public modules. So a name joins or leaves the top
level of the public API only with a change to that test.

## A key or a function

Where a feature can be a key in the file, it is a key and not a function. A function argument, such as an option on `to_spec`, could set the feature
instead. A key is
better here, because a key shows up in a git diff. The [typesetter](../reference/typeset.md) prints the key, and an engine written in another programming
language reads it. An option on a function changes what the file means
without a trace in the file.

## The size of the public API

A small public API is better here than a public module for every helper,
because a small API follows from the second rule. Any release can change a private module, such as the one that computes the
dimensions of an expression. A tool that needs the
dimensions of an expression instead reads the `dims` of a node in the compiled
spec ([a `Program`](../reference/program.md)).

You can now judge whether a function belongs in the public API, and whether a
feature belongs in the file as a key.

!!! info "See also"

    - [the Python API](../reference/api.md), for the module of each public name
      and the [guarantees](../reference/api.md#guarantees) that every public
      function keeps
    - [the limits of the language](limits.md), for which operators and sections
      can be added to the language
    - [what each tool decides for itself](what-counts-as-language.md#what-each-tool-decides-for-itself),
      for the reasons a tool may refuse a spec
