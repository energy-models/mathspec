<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA in 24 files

[PyPSA in one file](../pypsa.md) is `examples/pypsa.yaml`, one spec of some
four thousand lines. This is the same spec as 24 files under
`examples/pypsa/`, one per topic, and `merge` gives the one file back: the
two have one [canonical form](../../howto/compare.md).

Every fragment loads, prints and gets advice on its own. What it reads and does
not declare, it states under
[`given`](../../reference/language/declarations.md#given). A component that
puts something into a sum every component adds to, such as the bus balance or
the operating cost, names its share as an expression of its own, a
[term](../../reference/language/declarations.md#terms) whose `adds_to:` names
the sum. One fragment reads each sum and adds nothing to it, so the terms
always have a reader. A new component is one new file, and the network does
not change.

The split is written by `tools/pypsa_split.py` from the one file and checked
against it, so the two cannot drift. It is a proof of concept: a decision on
which of the two is the source comes after both land.

## What each file says

Three kinds of file. A **component** owns PyPSA's class of that name: its
dimension, its data, its columns, its rows, and its share of each sum. The
committable classes, `Generator`, `Link` and `Process`, are cut by feature into
a file each for the class, its commitment, its ramping and its maintenance,
and the three sets read alike because PyPSA's rows do. An **owner** reads a
sum with its description, and holds the row that reads it: the network reads
`Bus_injection`, power flow reads `Cycle_angle_sum`. **Settings** holds what
every topic reads, the weightings and the flags, and reads the totals whose
own readers, the cost, the carriers and the global constraints, a model may
leave out. It also sets the objective, which reads `total_cost`: each
component adds its capital cost to it, and the cost file adds the operating
cost at risk.

<!-- gallery: examples/pypsa -->

## Leaving a file out

A model may leave a component family out, or the cost, the carriers, the
global constraints or security, and what is left is a whole model: nothing
stays under `given:`. It may not leave the network or power flow out while a
component is in, because the component's terms would land on no name, and
`merge` says so.
