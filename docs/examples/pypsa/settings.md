<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Settings

One of the [24 fragments](index.md) of `examples/pypsa.yaml`: the weightings, the risk preference and the flags every topic reads. It reads the eight totals whose readers may be left out, `total_cost`, `scenario_opex`, `Carrier_additions` and the five global-constraint sums, under `given:`, so the terms the components add to them always have a reader. It sets the objective, which reads `total_cost`.

<!-- gallery: examples/pypsa/settings.yaml -->
