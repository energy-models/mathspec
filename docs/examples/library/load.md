<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Loads

This [fragment](../../reference/glossary.md#fragment) states `Load` from an open-source power system framework ([PyPSA](https://pypsa.org)).
The file declares the relation `Load_port`, the parameter `Load_p_set` and the
constraint `Load_withdrawal`. The minus sign in front of `Load_p_set` is the
only place where the file uses the sign convention of
[the surface](surface.md).

<!-- gallery:begin -->
```yaml
description: PyPSA's `Load`, wired to a port rather than straight to a bus. What a load takes is data, so the file declares no variable.
given:
  variables:
    Port_p:
      dims: [snapshot, port]
      description: declared by the surface, and fixed at each load's port by `Load_withdrawal`
dimensions:
  snapshot: { dtype: datetime, description: dispatch periods }
  port: { dtype: str, description: "the connections components make, one label per connection" }
  load: { dtype: str, description: "demands, each on one port" }
relations:
  Load_port: { key: load, values: port }
parameters:
  Load_p_set: { dims: [snapshot, load], description: "`Load-p_set` — what a load takes in a snapshot" }
constraints:
  Load_withdrawal:
    description: >-
      What a load takes is what its port withdraws. PyPSA has no row for this
      constraint, because PyPSA writes the load into the balance.
    dims: [snapshot, load]
    expression: at(Port_p, by=Load_port[port]) == -Load_p_set
```

PyPSA's `Load`, wired to a port rather than straight to a bus. What a load takes is data, so the file declares no variable.

#### Given

| Symbol | Meaning |
|---|---|
| $`f`$ | `Port_p` over $`\mathcal{T} \times \mathcal{J}`$ — declared by the surface, and fixed at each load's port by `Load_withdrawal` |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — the connections components make, one label per connection |
| $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — demands, each on one port |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{T} \times \mathcal{D}`$ — `Load-p_set` — what a load takes in a snapshot |

#### Subject to

**`Load_withdrawal`**

```math
f_{t,\mathrm{Load\_port}(d)} = -\mathrm{load}_{t,d} \qquad \forall\, t \in \mathcal{T},\ d \in \mathcal{D}
```
<!-- gallery:end -->

!!! info "See also"

    - [The coupling surface](surface.md), for the sign convention
    - [Generators](generator.md), for the component file that has a variable and a
      cost
    - [The composed spec](composed.md), for the spec once `merge` joins this file
      with the others
