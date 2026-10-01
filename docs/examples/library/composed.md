<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The composed spec

What [the surface](surface.md), [generators](generator.md) and
[loads](load.md) make together:

```python
import mathspec as ms

spec = ms.merge(['surface.yaml', 'generator.yaml', 'load.yaml'])
```

The file below is `spec`, the spec `merge` returns, written as YAML with
every default spelled out. No
fragment holds it, and nothing in the repository commits it. `Port_p` is one
declaration here. Each component fragment read it under `given:`, and merging
folded those readings into the surface's own declaration.

The objective is the surface's, and it reads `total_cost`. The generator is
the one fragment that costs something, so `Generator_cost` is the one term of
that sum. A second priced fragment would add its own term to `total_cost`.

The math under the file has a tab per formulation. **As composed** is the spec
above. **With commitment** lays `variants/commitment.yaml` over it with
[`override`](../../howto/compose.md#a-base-and-its-patches), which makes the
generator a committed unit:

```python
committed = ms.override(spec, ['variants/commitment.yaml'])
```

A patch is refused on its own, since it edits declarations it does not
declare. So the spec it lands on is the only place its math exists, and the
tab prints the patch beside that math.

<!-- gallery: examples/library -->
