<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The composed spec

This page shows the spec that [the surface](surface.md),
[generators](generator.md) and [loads](load.md) make together:

```python
import mathspec as ms

spec = ms.merge(['surface.yaml', 'generator.yaml', 'load.yaml'])
```

The file below is `spec`, the spec that `merge` returns, written as YAML with
every default spelled out. No fragment holds this file, and the repository does
not commit it. Each component fragment read `Port_p` under `given:`, and `merge`
folded those readings into the entry of the surface, so `Port_p` is one
entry here.

The objective comes from the surface, and it reads `total_cost`. The generator
is the only fragment with a cost, so `Generator_cost` is the only term of that
sum. A second fragment with a cost would add its own term to `total_cost`.

The math under the file has a tab per formulation: **As composed** is the spec
above, and **With commitment** lays `variants/commitment.yaml` over it with
[`override`](../../howto/compose.md#a-base-and-its-patches), which makes the
generator a committed unit:

```python
committed = ms.override(spec, ['variants/commitment.yaml'])
```

`to_spec` refuses a patch on its own, because the patch edits entries that
it does not declare. So the patch has math only on the spec it lands on, and
the tab prints the patch beside that math.

<!-- gallery:begin -->
```yaml
version: 0
dimensions:
  bus: {dtype: str, description: network nodes}
  generator: {dtype: str, description: 'generating units, each on one port'}
  load: {dtype: str, description: 'demands, each on one port'}
  port: {dtype: str, description: 'the connections components make, one label per connection'}
  snapshot: {dtype: datetime, description: dispatch periods}
relations:
  Generator_port: {key: generator, values: port}
  Load_port: {key: load, values: port}
  Port_bus: {key: port, values: bus}
parameters:
  Generator_marginal_cost:
    dims: [generator]
    dtype: float
    description: cost of one unit of output
  Generator_p_nom:
    dims: [generator]
    dtype: float
    description: nominal power
  Load_p_set:
    dims: [load, snapshot]
    dtype: float
    description: '`Load-p_set` — what a load takes in a snapshot'
variables:
  Generator_p:
    dims: [generator, snapshot]
    bounds: {lower: 0.0, upper: Generator_p_nom}
    domain: continuous
    missing: absent
    description: '`Generator-p` — what a generator produces in a snapshot'
  Port_p:
    dims: [port, snapshot]
    domain: continuous
    missing: absent
    description: what a port puts into its bus in a snapshot, negative for a withdrawal
expressions:
  Generator_cost: sum(Generator_p * Generator_marginal_cost)
  total_cost:
    dims: []
    expression: Generator_cost
    description: what running the system costs
objective: {sense: minimize, expression: total_cost}
constraints:
  Bus_nodal_balance:
    dims: [bus, snapshot]
    expression: sum(Port_p, over=port, by=Port_bus[bus]) == 0
    description: '`Bus-nodal_balance` — what the ports on a bus put in nets to nothing'
  Generator_injection:
    dims: [generator, snapshot]
    expression: at(Port_p, by=Generator_port[port]) == Generator_p
    description: 'what a generator produces is what its port injects. No PyPSA row stands for this: PyPSA
      writes the generator into the balance instead'
  Load_withdrawal:
    dims: [load, snapshot]
    expression: at(Port_p, by=Load_port[port]) == -Load_p_set
    description: 'what a load takes is what its port withdraws. No PyPSA row stands for this: PyPSA writes
      the load into the balance instead'
```

=== "As composed"

    #### Sets

    | Symbol | Meaning |
    |---|---|
    | $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — network nodes |
    | $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J}`$ — generating units, each on one port |
    | $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — demands, each on one port |
    | $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J},\ \mathrm{Load\_port}: \mathcal{D} \to \mathcal{J},\ \mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — the connections components make, one label per connection |
    | $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

    #### Parameters

    | Symbol | Meaning |
    |---|---|
    | $`\mathrm{c}`$ | `Generator_marginal_cost` over $`\mathcal{G}`$ — cost of one unit of output |
    | $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\mathcal{G}`$ — nominal power |
    | $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{D} \times \mathcal{T}`$ — `Load-p_set` — what a load takes in a snapshot |

    #### Variables

    | Symbol | Meaning |
    |---|---|
    | $`p`$ | `Generator_p` over $`\mathcal{G} \times \mathcal{T}`$ — `Generator-p` — what a generator produces in a snapshot |
    | $`f`$ | `Port_p` over $`\mathcal{J} \times \mathcal{T}`$ — what a port puts into its bus in a snapshot, negative for a withdrawal |

    #### Definitions

    | Symbol | Meaning |
    |---|---|
    | $`\mathit{Generator\_cost}`$ | `Generator_cost` (scalar) |
    | $`\mathit{total\_cost}`$ | `total_cost` (scalar) — what running the system costs |

    #### Variable domains

    **`Generator_p`**

    ```math
    0 \le p_{g,t} \le \mathrm{p}^{\mathrm{nom}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
    ```

    **`Port_p`**

    ```math
    f_{j,t} \in \mathbb{R} \qquad \forall\, j \in \mathcal{J},\ t \in \mathcal{T}
    ```

    #### Definitions

    **`Generator_cost`**

    ```math
    \mathit{Generator\_cost} = \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot \mathrm{c}_{g}
    ```

    **`total_cost`**

    ```math
    \mathit{total\_cost} = \mathit{Generator\_cost}
    ```

    #### Objective

    ```math
    \min \mathit{total\_cost}
    ```

    #### Subject to

    **`Bus_nodal_balance`**

    ```math
    \sum_{j \in \mathcal{J} \,:\, \mathrm{Port\_bus}(j) = n} f_{j,t} = 0 \qquad \forall\, n \in \mathcal{N},\ t \in \mathcal{T}
    ```

    **`Generator_injection`**

    ```math
    f_{\mathrm{Generator\_port}(g),t} = p_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
    ```

    **`Load_withdrawal`**

    ```math
    f_{\mathrm{Load\_port}(d),t} = -\mathrm{load}_{d,t} \qquad \forall\, d \in \mathcal{D},\ t \in \mathcal{T}
    ```

=== "With commitment"

    ```yaml title="variants/commitment.yaml"
    parameters:
      Generator_p_min_pu: { dims: [generator], description: "least output, per unit of nominal power" }
    variables:
      Generator_status:
        dims: [snapshot, generator]
        domain: binary
        description: "`Generator-status` — whether a unit is on in a snapshot"
      Generator_p: { bounds: { upper: null } }
    constraints:
      Generator_com_p_upper:
        description: "`Generator-com-p-upper` — a committed unit outputs at most its nominal power; off, at most nothing"
        dims: [snapshot, generator]
        expression: Generator_p <= Generator_p_nom * Generator_status
      Generator_com_p_lower:
        description: "`Generator-com-p-lower` — a committed unit outputs at least its minimum; off, at least nothing"
        dims: [snapshot, generator]
        expression: Generator_p >= Generator_p_min_pu * Generator_p_nom * Generator_status
    ```

    #### Sets

    | Symbol | Meaning |
    |---|---|
    | $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — network nodes |
    | $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J}`$ — generating units, each on one port |
    | $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — demands, each on one port |
    | $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J},\ \mathrm{Load\_port}: \mathcal{D} \to \mathcal{J},\ \mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — the connections components make, one label per connection |
    | $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |

    #### Parameters

    | Symbol | Meaning |
    |---|---|
    | $`\mathrm{c}`$ | `Generator_marginal_cost` over $`\mathcal{G}`$ — cost of one unit of output |
    | $`\underline{\mathrm{p}}`$ | `Generator_p_min_pu` over $`\mathcal{G}`$ — least output, per unit of nominal power |
    | $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\mathcal{G}`$ — nominal power |
    | $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{D} \times \mathcal{T}`$ — `Load-p_set` — what a load takes in a snapshot |

    #### Variables

    | Symbol | Meaning |
    |---|---|
    | $`p`$ | `Generator_p` over $`\mathcal{G} \times \mathcal{T}`$ — `Generator-p` — what a generator produces in a snapshot |
    | $`u`$ | `Generator_status` over $`\mathcal{G} \times \mathcal{T}`$ — `Generator-status` — whether a unit is on in a snapshot |
    | $`f`$ | `Port_p` over $`\mathcal{J} \times \mathcal{T}`$ — what a port puts into its bus in a snapshot, negative for a withdrawal |

    #### Definitions

    | Symbol | Meaning |
    |---|---|
    | $`\mathit{Generator\_cost}`$ | `Generator_cost` (scalar) |
    | $`\mathit{total\_cost}`$ | `total_cost` (scalar) — what running the system costs |

    #### Variable domains

    **`Generator_p`**

    ```math
    p_{g,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
    ```

    **`Generator_status`**

    ```math
    u_{g,t} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
    ```

    **`Port_p`**

    ```math
    f_{j,t} \in \mathbb{R} \qquad \forall\, j \in \mathcal{J},\ t \in \mathcal{T}
    ```

    #### Definitions

    **`Generator_cost`**

    ```math
    \mathit{Generator\_cost} = \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot \mathrm{c}_{g}
    ```

    **`total_cost`**

    ```math
    \mathit{total\_cost} = \mathit{Generator\_cost}
    ```

    #### Objective

    ```math
    \min \mathit{total\_cost}
    ```

    #### Subject to

    **`Bus_nodal_balance`**

    ```math
    \sum_{j \in \mathcal{J} \,:\, \mathrm{Port\_bus}(j) = n} f_{j,t} = 0 \qquad \forall\, n \in \mathcal{N},\ t \in \mathcal{T}
    ```

    **`Generator_com_p_lower`**

    ```math
    p_{g,t} \ge \underline{\mathrm{p}}_{g} \cdot \mathrm{p}^{\mathrm{nom}}_{g} \cdot u_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
    ```

    **`Generator_com_p_upper`**

    ```math
    p_{g,t} \le \mathrm{p}^{\mathrm{nom}}_{g} \cdot u_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
    ```

    **`Generator_injection`**

    ```math
    f_{\mathrm{Generator\_port}(g),t} = p_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
    ```

    **`Load_withdrawal`**

    ```math
    f_{\mathrm{Load\_port}(d),t} = -\mathrm{load}_{d,t} \qquad \forall\, d \in \mathcal{D},\ t \in \mathcal{T}
    ```
<!-- gallery:end -->
