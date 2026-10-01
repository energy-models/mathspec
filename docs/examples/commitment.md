<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Unit commitment

This spec adds a commitment decision and a start-up ramp to least-cost
dispatch. Read `previous_status` first, then `ramp_up`: the state a unit
carries into a snapshot has three regimes, stated once as a
[`cases:`](../reference/language/named.md#cases) block, and `ramp_up` reads it
the way it reads a parameter. The block prints once below, under
**Definitions**.

<!-- gallery: examples/commitment.yaml -->
