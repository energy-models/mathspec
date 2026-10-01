<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Least-cost dispatch

The smallest file that is a whole spec: generators with a capacity, an hourly
load to meet, and a cost to minimise. It is the spec on the
[home page](../index.md).

The `where:` on `dispatch` deletes the rows where a generator has no capacity
([absence](../reference/language/absence.md)). `sum(dispatch, over=generator)`
names the dimension it reduces, so the constraint's `dims` is what remains.

<!-- gallery: examples/dispatch.yaml -->
