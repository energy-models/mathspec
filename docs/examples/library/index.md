<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A component library

You can build one spec from several files, the **fragments**, each of which
states one part of it. The **surface** file declares what the components
share. Each component file declares its own math against the surface, and
[`merge`](../../howto/compose.md) joins the files into one spec. Every file
here loads and prints on its own, so you can read each file before you pick it.

The components couple through one flow variable per port, `Port_p`, so you can
read back the solved flow at every port. If no tool reads that flow, each
component can add a term to one sum instead, with no flow variable.
[Compose a spec from several files](../../howto/compose.md#a-library-of-components)
shows that way.

The names are those of PyPSA, spelled `Component_attribute` as [the PyPSA
rungs](../pypsa.md) spell them, and the math prints in the symbols of those
pages. The spec is cut to dispatch: one build, no availability profile and no
ramp limits.

## The layout

```text
examples/library/
  surface.yaml               one flow per port, one balance per bus, the objective
  generator.yaml             PyPSA's Generator
  load.yaml                  PyPSA's Load
  variants/
    commitment.yaml          a patch over the composition, not a peer
```

| Page                               | What it shows                                                  |
| ---------------------------------- | -------------------------------------------------------------- |
| [The coupling surface](surface.md) | the surface, the sign convention and the objective             |
| [Generators](generator.md)         | a file that reads `Port_p` and adds its cost to `total_cost`   |
| [Loads](load.md)                   | a file with no variable of its own                             |
| [The composed spec](composed.md)   | what `merge` returns, and the math it prints with each variant |

## Rules of the layout

- Each file holds one thing you would pick on its own. `merge` takes a whole
  fragment or none of it, so a spec with no storage never mentions storage.
- Every component file is written against one surface.
- Every name carries the component class it belongs to, because `merge` does
  not rename. `Generator_` and `Load_` keep the files apart, and the surface
  owns `Port_`, `port` and `bus`.
- A fragment states a part that the system has, and a patch states how one
  component is formulated. A second kind of component is a peer, which `merge`
  composes. A different formulation of one component edits entries that
  already exist, and `override` lays it over the composition.

## The variant

`variants/commitment.yaml` makes the generator a committed unit. It adds a
binary variable, removes the upper bound that the capacity gave `Generator_p`,
and caps the output with a constraint instead.

The patch edits `Generator_p` and names `Generator_p_nom`, which
`generator.yaml` declares, so the patch is not a spec and `to_spec` refuses it
on its own. You lay it over the composition:

```python
ms.override(ms.merge(fragments), ['variants/commitment.yaml'])
```

[The composed spec](composed.md) shows the patch and the math it makes, in a tab
of its own, which is the only place where you can read the patch as math.
