<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# About

The pages in this section describe why mathspec is the way it is. They
describe the background, compare choices, and argue for the rules that the
reference pages only state. Read them away from a task, when you want to
understand a rule before you rely on it.

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Background and history](history.md)** describes where mathspec comes from,
    from the YAML math of the energy system framework
    [Calliope](https://github.com/calliope-project/calliope) to the releases of mathspec itself.
- **[How mathspec works](overview.md)** describes what
    mathspec decides about the specification of an optimisation model
    ([a spec](../reference/glossary.md#spec)) before any data exists.
- **[The limits of the language](limits.md)** describes which constructs can be
    added to the language, and which requests mathspec refuses and why.
- **[Versions](versions.md)** describes how the version of the package and the
    version of the language relate, and why there are two.
- **[Relations as linear maps](relations-as-linear-maps.md)** describes a sum
    through a table that pairs labels
    ([a relation](../reference/language/relations.md)) as the product of a matrix and a vector.
- **[What counts as language](what-counts-as-language.md)** describes what the
    language defines for every piece of software that reads a spec
    ([a tool](../reference/glossary.md#tool)), and what each tool decides.
- **[What counts as public API](what-counts-as-public-api.md)** describes when a
    function joins the application programming interface (API) of mathspec, and
    why the API stays small.

</div>

!!! info "See also"

    - the [tutorials](../tutorials/index.md), to learn by writing a spec
    - the [reference](../reference/index.md), for what each key accepts
