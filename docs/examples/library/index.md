<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A component library

A component library is several files that
[`merge`](../../reference/composition.md#merge) composes into one spec. Each
file is a whole spec that states one part of a larger one (a
[fragment](../../reference/glossary.md#fragment)). mathspec loads each
fragment on its own, and [the typesetter](../../reference/typeset.md) prints
it. One fragment declares the names every component shares (the
[surface](../../reference/glossary.md#surface)), and each component file
declares its own math against the surface.

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[The coupling surface](surface.md)** declares the flow, the balance and
    the objective that every component file uses.
- **[Generators](generator.md)** is a component file with a variable of its
    own and a cost that adds to `total_cost`.
- **[Loads](load.md)** is a component file with no variable of its own.
- **[The composed spec](composed.md)** contains what `merge` returns, and the
    math of the merged spec with and without the
    [patch](../../reference/glossary.md#patch).

</div>

The components couple through one flow variable per port, `Port_p`.

The names are those of an open-source power system framework
([PyPSA](https://pypsa.org)), spelled `Component_attribute` as on
[PyPSA in one file](../pypsa_ladder.md). The typesetter prints the math in the
symbols of that page.

## The layout

```text
examples/library/
  surface.yaml               one flow per port, one balance per bus, the objective
  generator.yaml             PyPSA's Generator
  load.yaml                  PyPSA's Load
  variants/
    commitment.yaml          a patch over the composed spec
```

Each component file sits beside the surface, and the patch sits in its own
folder.

## How the files divide the spec

- `merge` takes the whole of a fragment or none of it.
- A component file states one class of PyPSA component, such as `Generator`
  (a component class). `merge` joins a second component class as another
  fragment. A patch changes one component class, and
  [`override`](../../reference/composition.md#override) lays the patch over
  the composed spec.
- Every entry a component file declares, apart from its dimensions, has the
  prefix of its component class. The prefixes `Generator_` and `Load_`
  separate the names of the two component files, and the surface declares the
  names with `Port_` and `Bus_`. Every file declares `snapshot` and `port`
  alike.

!!! info "See also"

    - [Composing specs](../../reference/composition.md), for what `merge` and
      `override` accept and what mathspec refuses
    - [Compose a spec from several files](../../howto/compose.md#build-a-spec-from-a-library-of-components),
      for a library whose components add a term to one sum instead of sharing a
      flow variable
    - [The composed spec](composed.md), for the patch and the math it adds
    - [The glossary](../../reference/glossary.md), for fragment, surface, term and
      patch
