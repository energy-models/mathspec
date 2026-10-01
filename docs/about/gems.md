<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# mathspec and GEMS

This page compares mathspec with GEMS, for a reader who knows one of the two
and weighs the other. Each section states the difference first. Then it shows a
GEMS excerpt, the spec that says the same thing, and the math mathspec prints
from that spec.

[GEMS](https://github.com/AntaresSimulatorTeam/GEMS) is the component
modelling language of RTE, the French transmission system operator. A GEMS
library declares models. A system file declares components and connects
their ports. Two interpreters, Antares Simulator and GemsPy, read both files
and solve the problem. A mathspec file states a spec, and an engine builds the
model and solves it. [GEMS in ten files](../examples/gems/index.md) writes a
whole GEMS library as one file for each GEMS model.

The comparison uses GEMS
[v0.4.0](https://github.com/AntaresSimulatorTeam/GEMS/releases/tag/v0.4.0),
released on 21 August 2026, and GemsPy
[v0.1.3](https://github.com/AntaresSimulatorTeam/GemsPy/tree/v0.1.3), the
GemsPy release that GEMS v0.4.0 names as compatible. The run
configuration excerpt under [Boundaries](#boundaries) is the one exception.
GEMS documents that file after v0.4.0, at commit
[`897a69c`](https://github.com/AntaresSimulatorTeam/GEMS/blob/897a69c4f9b879599a12cc2d28485d4db742222b/doc/user-guide/input-files/optimization-configuration.md),
and GemsPy v0.1.3 already reads it.

## Dimensions

A spec declares its own [dimensions](../reference/language/dimensions.md). A
GEMS quantity has two possible axes, time and scenario. A parameter or a
variable sets two flags to say which axes it carries. The GEMS
[roadmap](https://github.com/AntaresSimulatorTeam/GEMS/blob/v0.4.0/doc/home/roadmap.md)
lists custom sets and dimensions as work in progress, for multi-horizon
investment studies first. The spec below states that case. A
[relation](../reference/language/relations.md) places each time step in an
investment period, and each time step reads the capacity of its period.

<!-- gems:axes:begin -->

=== "GEMS"

    ```yaml
    # GEMS v0.4.0, libraries/basic_models_library.yml, lines 106-117
    - id: p_min
      scenario-dependent: true
      time-dependent: true
    - id: p_max
      scenario-dependent: true
      time-dependent: true
    - id: generation_cost
      scenario-dependent: false
      time-dependent: false
    - id: co2_emission_factor
      scenario-dependent: false
      time-dependent: false
    ```

=== "mathspec"

    ```yaml
    description: >-
      Generation capped by the capacity of its investment period. The file
      declares the period dimension, and a relation places each time step in a
      period.
    dimensions:
      time: { dtype: int, description: time steps }
      period: { dtype: int, description: investment periods }
      generator: { description: dispatchable units }
    relations:
      period_of: { key: time, values: period }
    parameters:
      investment_cost: { dims: [period, generator], description: cost of one unit of capacity }
      generation_cost: { dims: [generator], description: cost of one unit of generation }
      demand: { dims: [time], description: demand to be met }
    variables:
      capacity: { dims: [period, generator], bounds: { lower: 0 }, description: capacity in service }
      generation: { dims: [time, generator], bounds: { lower: 0 }, description: generation }
    constraints:
      within_capacity:
        dims: [time, generator]
        expression: generation <= at(capacity, by=period_of, over=period, into=time)
      meets_demand:
        dims: [time]
        expression: sum(generation, over=generator) == demand
    objective:
      sense: minimize
      expression: sum(investment_cost * capacity) + sum(generation_cost * generation)
    ```

=== "Math"

    Generation capped by the capacity of its investment period. The file declares the period dimension, and a relation places each time step in a period.

    _Objective_

    ```math
    \min \sum_{p \in \mathcal{P},\ g \in \mathcal{G}} \mathrm{investment\_cost}_{p,g} \cdot \mathit{capacity}_{p,g} + \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathrm{generation}^{\mathrm{cost}}_{g} \cdot \mathit{generation}_{t,g}
    ```

    _Subject to_

    **`within_capacity`**

    ```math
    \mathit{generation}_{t,g} \le \mathit{capacity}_{\mathrm{period\_of}(t),g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

    **`meets_demand`**

    ```math
    \sum_{g \in \mathcal{G}} \mathit{generation}_{t,g} = \mathrm{demand}_{t} \qquad \forall\, t \in \mathcal{T}
    ```

    _Variable domains_

    **`capacity`**

    ```math
    \mathit{capacity}_{p,g} \ge 0 \qquad \forall\, p \in \mathcal{P},\ g \in \mathcal{G}
    ```

    **`generation`**

    ```math
    \mathit{generation}_{t,g} \ge 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
    ```

<!-- gems:axes:end -->

## Boundaries

A spec states what a time shift reads at the edge of the horizon. A GEMS
model does not. In GEMS, `level[t+1]` at the last time step reads what the run
configuration says. `cyclic`, the default, wraps to the first time step, and
`drop` builds no row at that time step. So one GEMS model can give two
different problems, and the model file does not say which one. In a spec,
[`shift`](../reference/language/operators.md#shift) carries `edge=` in the
expression. `edge='wrap'` wraps, and a `shift` with no `edge=` builds no row
where the step leaves the dimension. The configuration excerpt below is the
example in the GEMS documentation, which names the storage model of another
GEMS library.

<!-- gems:boundary:begin -->

=== "GEMS"

    ```yaml
    # GEMS v0.4.0, libraries/basic_models_library.yml, lines 184-188
    constraints:
      - id: initial_level_constraint
        expression: level[0] = initial_level * reservoir_capacity
      - id: Level equation
        expression: level[t+1] = level + efficiency_injection * p_injection - efficiency_withdrawal * p_withdrawal

    # GEMS 897a69c, after v0.4.0, doc/user-guide/input-files/optimization-configuration.md, lines 374-379
    models:
      - id: antares_legacy_models.short_term_storage
        out-of-bounds-processing:
          constraints:
            - id: level_equation
              mode: cyclic
    ```

=== "mathspec"

    ```yaml
    description: The GEMS storage level equation, with its wrap at the end of the horizon.
    dimensions:
      time: { dtype: int, description: time steps }
      storage: { description: reservoirs }
    parameters:
      initial_level: { dims: [storage], description: "first level, as a share of the reservoir capacity" }
      reservoir_capacity: { dims: [storage], description: largest level }
      efficiency_injection: { dims: [storage], description: share of an injection that reaches the level }
      efficiency_withdrawal: { dims: [storage], description: level taken by one unit of withdrawal }
    variables:
      p_injection: { dims: [time, storage], bounds: { lower: 0 }, description: injection }
      p_withdrawal: { dims: [time, storage], bounds: { lower: 0 }, description: withdrawal }
      level: { dims: [time, storage], bounds: { lower: 0, upper: reservoir_capacity }, description: level }
    constraints:
      initial_level_constraint:
        dims: [time, storage]
        where: "position(time) == 0"
        expression: level == initial_level * reservoir_capacity
      level_equation:
        dims: [time, storage]
        expression: >-
          level == shift(level + efficiency_injection * p_injection - efficiency_withdrawal * p_withdrawal,
          along=time, offset=1, edge='wrap')
    ```

=== "Math"

    The GEMS storage level equation, with its wrap at the end of the horizon.

    _Subject to_

    **`initial_level_constraint`**

    ```math
    \mathit{level}_{t,s} = \mathrm{initial\_level}_{s} \cdot \mathrm{reservoir\_capacity}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S} \,:\, \mathrm{pos}(t) = 0
    ```

    **`level_equation`**

    ```math
    \mathit{level}_{t,s} = \mathit{level}_{t \ominus 1,s} + \mathrm{efficiency\_injection}_{s} \cdot p^{\mathrm{injection}}_{t \ominus 1,s} - \mathrm{efficiency\_withdrawal}_{s} \cdot p^{\mathrm{withdrawal}}_{t \ominus 1,s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

    _Variable domains_

    **`p_injection`**

    ```math
    p^{\mathrm{injection}}_{t,s} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

    **`p_withdrawal`**

    ```math
    p^{\mathrm{withdrawal}}_{t,s} \ge 0 \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

    **`level`**

    ```math
    0 \le \mathit{level}_{t,s} \le \mathrm{reservoir\_capacity}_{s} \qquad \forall\, t \in \mathcal{T},\ s \in \mathcal{S}
    ```

<!-- gems:boundary:end -->

## Masks

A spec removes rows and variables one coordinate at a time with `where:`
([absence](../reference/language/absence.md)). The GEMS expression grammar
has no condition, so a GEMS constraint applies to every component of its
model. A component that needs a different rule needs a different model. The
spec below writes two regimes over one `generator` dimension. Only a generator
with capacity has a generation variable. Only a generator with a ramp limit in
the data gets a ramp row. GEMS has no excerpt to show.

<!-- gems:masks:begin -->

=== "mathspec"

    ```yaml
    description: >-
      Generation exists only where a generator has capacity, and a ramp limit
      holds only for the generators the data gives one.
    dimensions:
      time: { dtype: int, description: time steps }
      generator: { description: dispatchable units }
    parameters:
      p_max: { dims: [generator], description: most generation }
      ramp_limit: { dims: [generator], description: largest rise from one time step to the next }
      demand: { dims: [time], description: demand to be met }
      generation_cost: { dims: [generator], description: cost of one unit of generation }
    variables:
      generation:
        dims: [time, generator]
        where: "p_max > 0"
        bounds: { lower: 0, upper: p_max }
        description: generation
    constraints:
      ramp_up:
        dims: [time, generator]
        where: ramp_limit
        expression: generation - shift(generation, along=time, offset=1) <= ramp_limit
      meets_demand:
        dims: [time]
        expression: sum(generation, over=generator) == demand
    objective:
      sense: minimize
      expression: sum(generation_cost * generation)
    ```

=== "Math"

    Generation exists only where a generator has capacity, and a ramp limit holds only for the generators the data gives one.

    _Objective_

    ```math
    \min \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathrm{generation}^{\mathrm{cost}}_{g} \cdot \mathit{generation}_{t,g}
    ```

    _Subject to_

    **`ramp_up`**

    ```math
    \mathit{generation}_{t,g} - \mathit{generation}_{t - 1,g} \le \mathrm{ramp\_limit}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{ramp\_limit}_{g} \text{ is defined}
    ```

    **`meets_demand`**

    ```math
    \sum_{g \in \mathcal{G}} \mathit{generation}_{t,g} = \mathrm{demand}_{t} \qquad \forall\, t \in \mathcal{T}
    ```

    _Variable domains_

    **`generation`**

    ```math
    0 \le \mathit{generation}_{t,g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{p}^{\mathrm{max}}_{g} > 0
    ```

<!-- gems:masks:end -->

## Printed math

Every **Math** tab on this page is printed from the spec beside it, by the
[typesetter](../reference/typeset.md). The typesetter prints LaTeX, Typst and
Markdown, so a paper shows the equations that the solver gets. GemsPy has
no printer, and the GEMS documentation writes the math of its
[quick-start model](https://github.com/AntaresSimulatorTeam/GEMS/blob/v0.4.0/doc/getting-started/quick-start/adequacy-math-model.md)
by hand.

## Ports and connections

The two languages say the same thing here. A GEMS port carries an expression
from one component to another, and `sum_connections` adds what all the
connections of a port bring. A relation holds the same connections as data,
and [`sum`](../reference/language/operators.md#sum) with `by=`, `over=` and
`into=` adds over them. The spec below is the GEMS bus and load. In
[GEMS in ten files](../examples/gems/index.md), each GEMS model is a file of
its own. There a port is a given expression, and each connected file adds a
[term](../reference/language/declarations.md#terms) to it with `adds_to:`. So
the bus file names no model that connects to it, as in GEMS.

<!-- gems:ports:begin -->

=== "GEMS"

    ```yaml
    # GEMS v0.4.0, libraries/basic_models_library.yml, lines 21-52
    - id: bus
      parameters:
        - id: spillage_cost
        - id: unsupplied_energy_cost
      variables:
        - id: spillage
          lower-bound: 0
          variable-type: continuous
        - id: unsupplied_energy
          lower-bound: 0
          variable-type: continuous
      ports:
        - id: balance_port
          type: flow
      binding-constraints:
        - id: balance
          expression: sum_connections(balance_port.flow) = spillage - unsupplied_energy
      objective-contributions:
        - id: objective
          expression: sum(spillage_cost * spillage + unsupplied_energy_cost * unsupplied_energy)
    - id: load
      parameters:
        - id: load
          time-dependent: true
          scenario-dependent: true
      ports:
        - id: balance_port
          type: flow
      port-field-definitions:
        - port: balance_port
          field: flow
          definition: -load
    ```

=== "mathspec"

    ```yaml
    description: >-
      The GEMS bus and load. A relation holds the connections, and a sum through
      it is `sum_connections`.
    dimensions:
      time: { dtype: int, description: time steps }
      bus: { description: "`bus` components" }
      load: { description: "`load` components" }
    relations:
      Load_balance_port: { key: [load, bus], description: "connections from a load's `balance_port` to a bus" }
    parameters:
      Bus_spillage_cost: { dims: [bus], description: cost of one unit of spillage }
      Bus_unsupplied_energy_cost: { dims: [bus], description: cost of one unit of unsupplied energy }
      Load_load: { dims: [time, load], description: demand }
    variables:
      Bus_spillage: { dims: [time, bus], bounds: { lower: 0 }, description: spillage }
      Bus_unsupplied_energy: { dims: [time, bus], bounds: { lower: 0 }, description: unsupplied energy }
    expressions:
      Load_balance_port_flow:
        expression: -Load_load
        description: "`balance_port.flow` of a load"
    constraints:
      Bus_balance:
        dims: [time, bus]
        expression: >-
          sum(Load_balance_port_flow, by=Load_balance_port, over=load, into=bus)
          == Bus_spillage - Bus_unsupplied_energy
    objective:
      sense: minimize
      expression: sum(Bus_spillage_cost * Bus_spillage + Bus_unsupplied_energy_cost * Bus_unsupplied_energy)
    ```

=== "Math"

    The GEMS bus and load. A relation holds the connections, and a sum through it is `sum_connections`.

    _Objective_

    ```math
    \min \sum_{t \in \mathcal{T},\ b \in \mathcal{B}} \left( \mathrm{Bus\_spillage\_cost}_{b} \cdot \mathit{Bus\_spillage}_{t,b} + \mathrm{Bus\_unsupplied\_energy\_cost}_{b} \cdot \mathit{Bus\_unsupplied\_energy}_{t,b} \right)
    ```

    _Subject to_

    **`Bus_balance`**

    ```math
    \sum_{l \in \mathcal{L} \,:\, \left( l,\ b \right) \in \mathrm{Load\_balance\_port}} \mathrm{Load\_balance\_port\_flow}_{t,l} = \mathit{Bus\_spillage}_{t,b} - \mathit{Bus\_unsupplied\_energy}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    _Definitions_

    **`Load_balance_port_flow`**

    ```math
    \mathrm{Load\_balance\_port\_flow}_{t,l} = -\mathrm{Load\_load}_{t,l} \qquad \forall\, t \in \mathcal{T},\ l \in \mathcal{L}
    ```

    _Variable domains_

    **`Bus_spillage`**

    ```math
    \mathit{Bus\_spillage}_{t,b} \ge 0 \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

    **`Bus_unsupplied_energy`**

    ```math
    \mathit{Bus\_unsupplied\_energy}_{t,b} \ge 0 \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
    ```

<!-- gems:ports:end -->

## Features outside mathspec

- **GEMS builds and solves.** Antares Simulator and GemsPy read a library and
  a system, and give the problem to a solver. mathspec has no engine.
- **GEMS splits a run.** Its run configuration cuts the horizon into blocks,
  and can solve by Benders decomposition, with investment in a master problem
  and operation in subproblems. A spec does not say how an engine solves it.
- **GEMS aggregates results.** A taxonomy file, a metrics catalog and a view
  configuration turn a solved run into views. The language refuses a
  vocabulary for tracked metrics, and a named expression does the same work
  ([the limits](limits.md#deliberate-non-primitives)).
