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
maps:
  load: { port: port }
parameters:
  Load_p_set: { dims: [snapshot, load], description: "`Load-p_set` — what a load takes in a snapshot" }
constraints:
  Load_withdrawal:
    description: >-
      What a load takes is what its port withdraws. PyPSA has no row for this
      constraint, because PyPSA writes the load into the balance.
    dims: [snapshot, load]
    expression: at(Port_p, by=load[port]) == -Load_p_set
```

PyPSA's `Load`, wired to a port rather than straight to a bus. What a load takes is data, so the file declares no variable.

#### Given

| Symbol | Meaning |
|---|---|
| $`f`$ | `Port_p` over $`\mathcal{J} \times \mathcal{T}`$ — declared by the surface, and fixed at each load's port by `Load_withdrawal` |

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{port}: \mathcal{D} \to \mathcal{J}`$ — demands, each on one port |
| $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{port}: \mathcal{D} \to \mathcal{J}`$ — the connections components make, one label per connection |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{D} \times \mathcal{T}`$ — `Load-p_set` — what a load takes in a snapshot |

#### Subject to

**`Load_withdrawal`**

```math
f_{\mathrm{port}(d),t} = -\mathrm{load}_{d,t} \qquad \forall\, d \in \mathcal{D},\ t \in \mathcal{T}
```
<!-- gallery:end -->

!!! info "See also"

    - [The coupling surface](surface.md), for the sign convention
    - [Generators](generator.md), for the component file that has a variable and a
      cost
    - [The composed spec](composed.md), for the spec once `merge` joins this file
      with the others
