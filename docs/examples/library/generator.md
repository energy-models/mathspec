<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Generators

PyPSA's `Generator`, as one fragment. It owns its dimension, its relation into
`port`, its parameters, its column and its cost. It reads `Port_p` and
`total_cost` from [the surface](surface.md) under
[`given`](../../reference/language/declarations.md#given), and adds its cost to
`total_cost` as the term `Generator_cost`. `Generator_port` stands where PyPSA
writes `Generator_bus`. The surface sets the objective, so this file on its
own sets none.

The constraint is what makes the library composable.
`at(Port_p, by=Generator_port, over=port, into=generator)` pins the flow at
this component's own port rather than adding a term to the balance, so the
balance does not grow.

The file is cut to what a dispatch spec needs. A fixed build, no availability
profile and no ramp limits are three declarations PyPSA carries and this file
does not. [The PyPSA rungs](../pypsa.md) state them in full.

The math below is what this file prints on its own, with `Port_p` under
_Given_ in the legend. When it merges with the surface, `Port_p` is one
declaration again.

<!-- gallery: examples/library/generator.yaml -->
