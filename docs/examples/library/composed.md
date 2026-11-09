<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The composed spec

[`merge`](../../reference/composition.md#merge) composes [the surface](surface.md),
[generators](generator.md) and [loads](load.md) into one spec:

```python
import mathspec as ms

spec = ms.merge(['surface.yaml', 'generator.yaml', 'load.yaml'])
```

The file below is `spec` written as YAML, with every default spelled out. The
file is not one of the files under `examples/library/`.

Each component fragment lists `Port_p` under
[`given:`](../../reference/glossary.md#given), and `merge` folds each given
`Port_p` into the entry the surface declares. So `Port_p` is one entry here.

The surface sets the objective, which is to minimise `total_cost`. The
generator file is the only fragment with a cost, so `merge` builds
`total_cost` from the one [term](../../reference/glossary.md#term) `Generator_cost`. A second fragment with a cost
would add its own term to `total_cost`.

Under the file, the "As composed" tab has the spec above. The "With
commitment" tab has that spec with the
[patch](../../reference/glossary.md#patch) `variants/commitment.yaml` laid over
it by [`override`](../../reference/composition.md#override):

```python
committed = ms.override(spec, ['variants/commitment.yaml'])
```

The patch makes the
generator a unit that is on or off in each dispatch period (a
[committed unit](../commitment.md)).
[`to_spec`](../../reference/api.md#to_spec) refuses the patch on its own,
because the patch sets only the bounds of `Generator_p`, whose dimensions only
`generator.yaml` declares. So the patch has math only on the spec it is laid
over, and the tab has the patch beside that math.

<!-- gallery:begin -->
```yaml
version: 0
dimensions:
  snapshot: {dtype: datetime, description: dispatch periods}
  bus: {dtype: str, description: network nodes}
  port: {dtype: str, description: 'the connections components make, one label per connection'}
  generator: {dtype: str, description: 'generating units, each on one port'}
  load: {dtype: str, description: 'demands, each on one port'}
relations:
  Port_bus: {key: port, values: bus}
  Generator_port: {key: generator, values: port}
  Load_port: {key: load, values: port}
parameters:
  Generator_p_nom:
    dims: [generator]
    dtype: float
    description: nominal power
  Generator_marginal_cost:
    dims: [generator]
    dtype: float
    description: cost of one unit of output
  Load_p_set:
    dims: [snapshot, load]
    dtype: float
    description: '`Load-p_set` — what a load takes in a snapshot'
variables:
  Port_p:
    dims: [snapshot, port]
    domain: continuous
    missing: absent
    description: what a port puts into its bus in a snapshot, negative for a withdrawal
  Generator_p:
    dims: [snapshot, generator]
    bounds: {lower: 0.0, upper: Generator_p_nom}
    domain: continuous
    missing: absent
    description: '`Generator-p` — what a generator produces in a snapshot'
expressions:
  Generator_cost: sum(Generator_p * Generator_marginal_cost)
  total_cost:
    dims: []
    expression: Generator_cost
    description: what running the system costs
objective: {sense: minimize, expression: total_cost}
constraints:
  Bus_nodal_balance:
    dims: [snapshot, bus]
    expression: sum(Port_p, over=port, by=Port_bus[bus]) == 0
    description: '`Bus-nodal_balance` — what the ports on a bus put in sums to zero'
  Generator_injection:
    dims: [snapshot, generator]
    expression: at(Port_p, by=Generator_port[port]) == Generator_p
    description: What a generator produces is what its port injects. PyPSA has no row for this constraint,
      because PyPSA writes the generator into the balance.
  Load_withdrawal:
    dims: [snapshot, load]
    expression: at(Port_p, by=Load_port[port]) == -Load_p_set
    description: What a load takes is what its port withdraws. PyPSA has no row for this constraint, because
      PyPSA writes the load into the balance.
```

=== "As composed"

    #### Sets

    | Symbol | Meaning |
    |---|---|
    | $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
    | $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — network nodes |
    | $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N},\ \mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J},\ \mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — the connections components make, one label per connection |
    | $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J}`$ — generating units, each on one port |
    | $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — demands, each on one port |

    #### Parameters

    | Symbol | Meaning |
    |---|---|
    | $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\mathcal{G}`$ — nominal power |
    | $`\mathrm{c}`$ | `Generator_marginal_cost` over $`\mathcal{G}`$ — cost of one unit of output |
    | $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{T} \times \mathcal{D}`$ — `Load-p_set` — what a load takes in a snapshot |

    #### Variables

    | Symbol | Meaning |
    |---|---|
    | $`f`$ | `Port_p` over $`\mathcal{T} \times \mathcal{J}`$ — what a port puts into its bus in a snapshot, negative for a withdrawal |
    | $`p`$ | `Generator_p` over $`\mathcal{T} \times \mathcal{G}`$ — `Generator-p` — what a generator produces in a snapshot |

    #### Definitions

    | Symbol | Meaning |
    |---|---|
    | $`\mathit{Generator\_cost}`$ | `Generator_cost` (scalar) |
    | $`\mathit{total\_cost}`$ | `total_cost` (scalar) — what running the system costs |

    #### Variable domains

    **`Port_p`**

    ```math
    f_{t,j} \in \mathbb{R} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
    ```

    **`Generator_p`**

    ```math
    0 \le p_{t,g} \le \mathrm{p}^{\mathrm{nom}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    #### Definitions

    **`Generator_cost`**

    ```math
    \mathit{Generator\_cost} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \mathrm{c}_{g}
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
    \sum_{j \in \mathcal{J} \,:\, \mathrm{Port\_bus}(j) = n} f_{t,j} = 0 \qquad \forall\, t \in \mathcal{T},\ n \in \mathcal{N}
    ```

    **`Generator_injection`**

    ```math
    f_{t,\mathrm{Generator\_port}(g)} = p_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    **`Load_withdrawal`**

    ```math
    f_{t,\mathrm{Load\_port}(d)} = -\mathrm{load}_{t,d} \qquad \forall\, t \in \mathcal{T},\ d \in \mathcal{D}
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
        description: "`Generator-com-p-upper` — a committed unit outputs at most its nominal power, and an off unit outputs nothing"
        dims: [snapshot, generator]
        expression: Generator_p <= Generator_p_nom * Generator_status
      Generator_com_p_lower:
        description: "`Generator-com-p-lower` — a committed unit outputs at least its minimum, and an off unit has no floor"
        dims: [snapshot, generator]
        expression: Generator_p >= Generator_p_min_pu * Generator_p_nom * Generator_status
    ```

    #### Sets

    | Symbol | Meaning |
    |---|---|
    | $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
    | $`\mathcal{N}`$ | index $`n`$ — `bus` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N}`$ — network nodes |
    | $`\mathcal{J}`$ | index $`j`$ — `port` with $`\mathrm{Port\_bus}: \mathcal{J} \to \mathcal{N},\ \mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J},\ \mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — the connections components make, one label per connection |
    | $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{Generator\_port}: \mathcal{G} \to \mathcal{J}`$ — generating units, each on one port |
    | $`\mathcal{D}`$ | index $`d`$ — `load` with $`\mathrm{Load\_port}: \mathcal{D} \to \mathcal{J}`$ — demands, each on one port |

    #### Parameters

    | Symbol | Meaning |
    |---|---|
    | $`\mathrm{p}^{\mathrm{nom}}`$ | `Generator_p_nom` over $`\mathcal{G}`$ — nominal power |
    | $`\mathrm{c}`$ | `Generator_marginal_cost` over $`\mathcal{G}`$ — cost of one unit of output |
    | $`\mathrm{load}`$ | `Load_p_set` over $`\mathcal{T} \times \mathcal{D}`$ — `Load-p_set` — what a load takes in a snapshot |
    | $`\underline{\mathrm{p}}`$ | `Generator_p_min_pu` over $`\mathcal{G}`$ — least output, per unit of nominal power |

    #### Variables

    | Symbol | Meaning |
    |---|---|
    | $`f`$ | `Port_p` over $`\mathcal{T} \times \mathcal{J}`$ — what a port puts into its bus in a snapshot, negative for a withdrawal |
    | $`p`$ | `Generator_p` over $`\mathcal{T} \times \mathcal{G}`$ — `Generator-p` — what a generator produces in a snapshot |
    | $`u`$ | `Generator_status` over $`\mathcal{T} \times \mathcal{G}`$ — `Generator-status` — whether a unit is on in a snapshot |

    #### Definitions

    | Symbol | Meaning |
    |---|---|
    | $`\mathit{Generator\_cost}`$ | `Generator_cost` (scalar) |
    | $`\mathit{total\_cost}`$ | `total_cost` (scalar) — what running the system costs |

    #### Variable domains

    **`Port_p`**

    ```math
    f_{t,j} \in \mathbb{R} \qquad \forall\, t \in \mathcal{T},\ j \in \mathcal{J}
    ```

    **`Generator_p`**

    ```math
    p_{t,g} \ge 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    **`Generator_status`**

    ```math
    u_{t,g} \in \{0, 1\} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    #### Definitions

    **`Generator_cost`**

    ```math
    \mathit{Generator\_cost} = \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \mathrm{c}_{g}
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
    \sum_{j \in \mathcal{J} \,:\, \mathrm{Port\_bus}(j) = n} f_{t,j} = 0 \qquad \forall\, t \in \mathcal{T},\ n \in \mathcal{N}
    ```

    **`Generator_injection`**

    ```math
    f_{t,\mathrm{Generator\_port}(g)} = p_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    **`Load_withdrawal`**

    ```math
    f_{t,\mathrm{Load\_port}(d)} = -\mathrm{load}_{t,d} \qquad \forall\, t \in \mathcal{T},\ d \in \mathcal{D}
    ```

    **`Generator_com_p_upper`**

    ```math
    p_{t,g} \le \mathrm{p}^{\mathrm{nom}}_{g} \cdot u_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    **`Generator_com_p_lower`**

    ```math
    p_{t,g} \ge \underline{\mathrm{p}}_{g} \cdot \mathrm{p}^{\mathrm{nom}}_{g} \cdot u_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```
<!-- gallery:end -->

!!! info "See also"

    - [`merge`](../../reference/composition.md#merge) and [`override`](../../reference/composition.md#override), for what each function
      accepts and what mathspec refuses
    - [Given](../../reference/glossary.md#given), [term](../../reference/glossary.md#term) and [patch](../../reference/glossary.md#patch) in the glossary
    - [Unit commitment](../commitment.md), for commitment stated in one file
