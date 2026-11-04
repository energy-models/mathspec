<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# What counts as language

The language defines some meanings of the specification of an optimisation
model ([a spec](../reference/glossary.md#spec)). It defines them for all
software that reads a spec ([every tool](../reference/glossary.md#tool)), and
each tool decides the rest for itself. An engine, a renderer and a checker
can all read one spec
([the tools that read a spec](overview.md#the-tools-that-read-a-spec)).

One test separates what the language defines from what a tool decides. The
test is whether two tools that answered a question about the file differently
would give the file two meanings. Suppose the engine sums `p` over `generator`, and the renderer
prints a sum over `snapshot`. The file now has two meanings, and that is
wrong. So the language defines what `sum(p, over=generator)` means, and both
tools read the definition instead of working it out.

Suppose instead that the engine writes the model in one solver's file format,
and the renderer sets the page width to 80 characters. The two tools differ,
and nothing is wrong, because each tool decides those things for itself.

## What the language defines

Five rules follow from that test:

- A name means one thing, so `p` cannot be a variable in the engine and a
  parameter in the renderer.
- The set of constructs built into the language
  ([operators](../reference/language/operators.md)) is
  [closed](limits.md#new-constructs).
- Each operator has one rule for the dimensions of its result.
  `sum(p, over=generator, by=gen_bus[bus])` groups by `bus` for every tool.
- mathspec decides when `to_spec` reads the file
  ([at load](../reference/glossary.md#load)) whether an expression is linear or quadratic
  ([its degree](../reference/language/expressions.md#where-a-product-of-two-variables-is-allowed)).
  Whether `x * y` is allowed does not depend on which engine builds the model.
- An entry that expands into ordinary entries
  ([a formulation](../reference/glossary.md#formulation)) has one meaning for
  every tool. A [`piecewise:`](../reference/language/piecewise.md#piecewise)
  entry and a cap on non-zero members
  ([an SOS](../reference/glossary.md#special-ordered-set-sos)) under
  [`sos:`](../reference/language/piecewise.md#sos) each state ordinary variables and constraints.
  [`spec.expand()`](../reference/spec.md#mathspec.spec.Spec.expand) writes them
  out the same way for every tool.

## What each tool decides for itself

A tool can refuse a spec for a reason of its own. One engine takes only a
literal offset in [`shift`](../reference/language/operators.md#shift).
Another has no SOS, and a file format has no way to write a quadratic constraint.
None of these is a disagreement about what the file means, so mathspec
settles none of them at load.

Here a refusal by each tool is better than a refusal by mathspec of every
construct that some tool cannot build. Otherwise every other
tool loses the construct too. If mathspec refused `sos:` because one engine has no
SOS, no engine could build an SOS from a spec.

So the test works in both directions. A rule about what the file _means_ goes
into the language, and a rule about what one tool can _build_ stays with that
tool.

You can now judge whether a rule belongs in the language or in a tool.

!!! info "See also"

    - [the limits of the language](limits.md), for which operators and sections
      can be added to the language
    - [how mathspec works](overview.md), for the tools that read a spec
