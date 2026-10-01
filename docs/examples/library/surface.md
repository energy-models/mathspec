<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The coupling surface

The surface every other file in the library is written against. It declares one
`Port_p` per port, one balance per bus, and the relation that says which bus a
port sits on. It sets the objective on `total_cost`, which it reads under
[`given`](../../reference/language/declarations.md#given): each component that
costs something adds its cost to that sum. Nothing in it names a component
class, so it is the one file that does not change when a component class is
added.

PyPSA gives each component class a bus column and sums the classes into
`Bus-nodal_balance`. Here a component is wired to a port and the port to a bus,
so the balance sums ports and stays as written however many fragments merge.
The [how-to guide](../../howto/compose.md) shows the same shape with fewer
names.

A flow is positive where the port injects into its bus. Every component reads
that convention, and no component restates it.

<!-- gallery: examples/library/surface.yaml -->
