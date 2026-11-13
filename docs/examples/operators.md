<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# One construct per spec

This page has a section for each call form of the four
[operators](../reference/language/operators.md), `sum`, `at`, `shift` and
`sum_back`, and of [`dual`](../reference/language/named.md#dual). Each section
contains the smallest spec that uses the form, and the equation that
[the typesetter](../reference/typeset.md) prints from that spec. The
[operators page](../reference/language/operators.md#every-operator-as-math)
lists the same equations in one table, without the files.

<!-- gallery:begin -->
### `sum(array)`

`examples/operators/sum_all.yaml`

```yaml
description: >-
  Every dimension at once: `sum(array)` lists no dimension and collapses every
  one.

dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }

parameters:
  budget: { dims: [] }

variables:
  p:
    dims: [snapshot, generator]
    bounds: { lower: 0 }

constraints:
  fleet_budget:
    dims: []
    expression: sum(p) <= budget

objective: { sense: minimize, expression: sum(p) }
```

$`\sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \le \mathrm{budget}`$

### `sum(array, over=dim)`

`examples/operators/sum.yaml`

```yaml
description: >-
  The plain reduction: `sum(array, over=dim)` collapses one dimension.

dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }

parameters:
  limit: { dims: [snapshot] }

variables:
  p:
    dims: [snapshot, generator]
    bounds: { lower: 0 }

constraints:
  fleet_total:
    dims: [snapshot]
    expression: sum(p, over=generator) <= limit

objective: { sense: minimize, expression: sum(p) }
```

$`\sum_{g \in \mathcal{G}} p_{g,t} \le \mathrm{limit}_{t} \qquad \forall\, t \in \mathcal{T}`$

### `sum(array, over=[a, …])`

`examples/operators/sum_list.yaml`

```yaml
description: >-
  Several dimensions at once: `sum(array, over=[a, b])` collapses each
  dimension in the list.

dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
  carrier: { dtype: str }

parameters:
  limit: { dims: [carrier] }

variables:
  p:
    dims: [snapshot, generator, carrier]
    bounds: { lower: 0 }

constraints:
  carrier_total:
    dims: [carrier]
    expression: sum(p, over=[snapshot, generator]) <= limit

objective: { sense: minimize, expression: sum(p) }
```

$`\sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{c,g,t} \le \mathrm{limit}_{c} \qquad \forall\, c \in \mathcal{C}`$

### `sum(array, over=dim, by=subject[m])`

`examples/operators/sum_by.yaml`

```yaml
description: >-
  A sum by group: `sum(array, over=dim, by=subject[m])` groups the result by
  the label that map `m` gives each row. The data of the map, not the file,
  sets which generator sits at which bus.

dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
  bus: { dtype: str }

maps:
  generator: { bus: bus }

parameters:
  limit: { dims: [snapshot, bus] }

variables:
  p:
    dims: [snapshot, generator]
    bounds: { lower: 0 }

constraints:
  bus_total:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=generator[bus]) <= limit

objective: { sense: minimize, expression: sum(p) }
```

$`\sum_{g \in \mathcal{G} \,:\, \mathrm{bus}(g) = b} p_{g,t} \le \mathrm{limit}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}`$

### `sum(array, over=dim, by=subject[m]), joining on the rest of the key`

`examples/operators/sum_by_columns.yaml`

```yaml
description: >-
  A sum that keeps a key column: `sum(array, over=dim, by=subject[m])` joins
  on the column over `dim` and groups by map `m`. The sum also joins on the
  key column that the call does not list. It keeps that column, so each zone
  gets one total per period.

dimensions:
  generator: { dtype: str }
  period: { dtype: int }
  zone: { dtype: str }

relations:
  zone_of: { dims: [generator, period] }

maps:
  zone_of: { zone: zone }

parameters:
  demand: { dims: [zone, period] }

variables:
  p:
    dims: [generator, period]
    bounds: { lower: 0 }

constraints:
  zone_balance:
    dims: [zone, period]
    expression: sum(p, over=generator, by=zone_of[zone]) >= demand

objective: { sense: minimize, expression: sum(p) }
```

$`\sum_{g \in \mathcal{G} \,:\, \mathrm{zone}(g,\ e) = z} p_{g,e} \ge \mathrm{demand}_{e,z} \qquad \forall\, e \in \mathcal{E},\ z \in \mathcal{Z}`$

### `sum(array, over=[dim, …], by=subject[m, …])`

`examples/operators/sum_by_column_lists.yaml`

```yaml
description: >-
  Several columns and maps: `sum(array, over=[dim, …], by=subject[m, …])`
  joins on both columns of the relation and groups by both of its maps.

dimensions:
  generator: { dtype: str }
  period: { dtype: int }
  bus: { dtype: str }
  technology: { dtype: str }

relations:
  slot_of: { dims: [generator, period] }

maps:
  slot_of: { bus: bus, technology: technology }

parameters:
  cap: { dims: [bus, technology] }

variables:
  p:
    dims: [generator, period]
    bounds: { lower: 0 }

constraints:
  slot_cap:
    dims: [bus, technology]
    expression: sum(p, over=[generator, period], by=slot_of[bus, technology]) <= cap

objective: { sense: minimize, expression: sum(p) }
```

$`\sum_{g \in \mathcal{G},\ e \in \mathcal{E} \,:\, \mathrm{bus}(g,\ e) = b \wedge \mathrm{technology}(g,\ e) = t} p_{g,e} \le \mathrm{cap}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}`$

### `at(array, by=subject[m])`

`examples/operators/at.yaml`

```yaml
description: >-
  The join without a grouping: `at(array, by=subject[m])` takes, for each
  `snapshot`, the value at the `period` that the map gives that snapshot.

dimensions:
  snapshot: { dtype: int }
  period: { dtype: int }

maps:
  snapshot: { period: period }

parameters:
  cap: { dims: [period] }

variables:
  p:
    dims: [snapshot]
    bounds: { lower: 0 }

constraints:
  within_cap:
    dims: [snapshot]
    expression: p <= at(cap, by=snapshot[period])

objective: { sense: minimize, expression: sum(p) }
```

$`p_{t} \le \mathrm{cap}_{\mathrm{period}(t)} \qquad \forall\, t \in \mathcal{T}`$

### `at(array, by=subject[m]), two maps into one dimension`

`examples/operators/at_columns.yaml`

```yaml
description: >-
  One of two maps: where a subject has two maps into one dimension,
  `at(array, by=subject[m])` takes the value at the label of map `m`. Here `m`
  is `bus0`, the sending end of a line.

dimensions:
  line: { dtype: str }
  bus: { dtype: str }

maps:
  line: { bus0: bus, bus1: bus }

parameters:
  cap: { dims: [bus] }

variables:
  f:
    dims: [line]
    bounds: { lower: 0 }

constraints:
  sending_cap:
    dims: [line]
    expression: f <= at(cap, by=line[bus0])

objective: { sense: minimize, expression: sum(f) }
```

$`f_{l} \le \mathrm{cap}_{\mathrm{bus0}(l)} \qquad \forall\, l \in \mathcal{L}`$

### `shift(array, along=dim, offset=n)`

`examples/operators/shift.yaml`

```yaml
description: >-
  A shift with no `edge=`: the vacated position is absent, so the constraint
  has no row there.

dimensions:
  snapshot: { dtype: int, ordered: true }

variables:
  p:
    dims: [snapshot]
    bounds: { lower: 0 }

constraints:
  no_faster_than_before:
    dims: [snapshot]
    expression: p <= shift(p, along=snapshot, offset=1)

objective: { sense: minimize, expression: sum(p) }
```

$`p_{t} \le p_{t - 1} \qquad \forall\, t \in \mathcal{T}`$

### `shift(array, along=dim, offset=n, edge='wrap')`

`examples/operators/shift_wrap.yaml`

```yaml
description: >-
  A cyclic shift: the horizon wraps, so the first position takes the value of
  the last and no position is vacated.

dimensions:
  snapshot: { dtype: int, ordered: true }

variables:
  p:
    dims: [snapshot]
    bounds: { lower: 0 }

constraints:
  no_faster_than_before:
    dims: [snapshot]
    expression: p <= shift(p, along=snapshot, offset=1, edge='wrap')

objective: { sense: minimize, expression: sum(p) }
```

$`p_{t} \le p_{t \ominus 1} \qquad \forall\, t \in \mathcal{T}`$

### `shift(array, along=dim, offset=n, edge=v)`

`examples/operators/shift_edge.yaml`

```yaml
description: >-
  A shift with a value at the edge: the vacated position contributes the
  `edge=` value, here 0, instead of being absent. The constraint has a row
  there.

dimensions:
  snapshot: { dtype: int, ordered: true }

variables:
  p:
    dims: [snapshot]
    bounds: { lower: 0 }

constraints:
  no_faster_than_before:
    dims: [snapshot]
    expression: p <= shift(p, along=snapshot, offset=1, edge=0)

objective: { sense: minimize, expression: sum(p) }
```

$`p_{t} \le p_{t \boxminus_{0} 1} \qquad \forall\, t \in \mathcal{T}`$

### `shift(array, along=dim, offset=p, edge=…)`

`examples/operators/shift_by_parameter.yaml`

```yaml
description: >-
  A shift by an offset that differs per entity: `offset=` is an integer
  parameter. Each technology is shifted by its own lead time.

dimensions:
  technology: { dtype: str }
  month: { dtype: int, ordered: true }

parameters:
  lead: { dims: [technology], dtype: int }
  demand: { dims: [technology, month] }

variables:
  order:
    dims: [technology, month]
    bounds: { lower: 0 }

constraints:
  arrives_after_its_lead:
    dims: [technology, month]
    expression: shift(order, along=month, offset=lead, edge=0) >= demand

objective: { sense: minimize, expression: sum(order) }
```

$`\mathit{order}_{m \boxminus_{0} \mathrm{lead},t} \ge \mathrm{demand}_{m,t} \qquad \forall\, m \in \mathcal{M},\ t \in \mathcal{T}`$

### `shift(array, along=dim, offset=n, within=subject[m])`

`examples/operators/shift_partitioned.yaml`

```yaml
description: >-
  A shift inside a group: each season wraps on itself. A season's first
  snapshot takes the value of that season's last, and no value crosses from one
  season into the next.

dimensions:
  snapshot: { dtype: int, ordered: true }
  season: { dtype: str }

maps:
  snapshot: { season: season }

variables:
  p:
    dims: [snapshot]
    bounds: { lower: 0 }

constraints:
  no_faster_than_before_in_season:
    dims: [snapshot]
    expression: p <= shift(p, along=snapshot, offset=1, edge='wrap', within=snapshot[season])

objective: { sense: minimize, expression: sum(p) }
```

$`p_{t} \le p_{t \ominus^{\mathrm{season}(t)} 1} \qquad \forall\, t \in \mathcal{T}`$

### `sum_back(array, along=dim, window=n)`

`examples/operators/sum_back.yaml`

```yaml
description: >-
  A trailing window of a fixed width: a unit that started in the last three
  hours is still on.

dimensions:
  unit: { dtype: str }
  hour: { dtype: int, ordered: true }

parameters:
  min_up: { dims: [unit], dtype: int }

variables:
  started:
    dims: [unit, hour]
    domain: binary
  on:
    dims: [unit, hour]
    domain: binary

constraints:
  stays_up_its_own_time:
    dims: [unit, hour]
    expression: sum_back(started, along=hour, window=3) <= on

objective: { sense: minimize, expression: sum(on) }
```

$`\sum_{h' \in \mathcal{H} \,:\, 0 \le h - h' < 3} \mathit{started}_{h',u} \le \mathit{on}_{h,u} \qquad \forall\, h \in \mathcal{H},\ u \in \mathcal{U}`$

### `sum_back(array, along=dim, window=p)`

`examples/operators/sum_back_by_parameter.yaml`

```yaml
description: >-
  A trailing window whose width is data: `window=` is an integer parameter. A
  unit stays up for its own minimum up time.

dimensions:
  unit: { dtype: str }
  hour: { dtype: int, ordered: true }

parameters:
  min_up: { dims: [unit], dtype: int }

variables:
  started:
    dims: [unit, hour]
    domain: binary
  on:
    dims: [unit, hour]
    domain: binary

constraints:
  stays_up_its_own_time:
    dims: [unit, hour]
    expression: sum_back(started, along=hour, window=min_up) <= on

objective: { sense: minimize, expression: sum(on) }
```

$`\sum_{h' \in \mathcal{H} \,:\, 0 \le h - h' < \mathrm{min\_up}} \mathit{started}_{h',u} \le \mathit{on}_{h,u} \qquad \forall\, h \in \mathcal{H},\ u \in \mathcal{U}`$

### `sum_back(array, along=dim, window=p, edge='wrap')`

`examples/operators/sum_back_wrap.yaml`

```yaml
description: >-
  A trailing window on a day that repeats, so the window at the first hour
  reaches back into the last.

dimensions:
  unit: { dtype: str }
  hour: { dtype: int, ordered: true }

parameters:
  min_up: { dims: [unit], dtype: int }

variables:
  started:
    dims: [unit, hour]
    domain: binary
  on:
    dims: [unit, hour]
    domain: binary

constraints:
  stays_up_its_own_time:
    dims: [unit, hour]
    expression: sum_back(started, along=hour, window=min_up, edge='wrap') <= on

objective: { sense: minimize, expression: sum(on) }
```

$`\sum_{h' \in \mathcal{H} \,:\, 0 \le h \ominus h' < \mathrm{min\_up}} \mathit{started}_{h',u} \le \mathit{on}_{h,u} \qquad \forall\, h \in \mathcal{H},\ u \in \mathcal{U}`$

### `sum_back(array, along=dim, window=n, within=subject[m])`

`examples/operators/sum_back_partitioned.yaml`

```yaml
description: >-
  A window inside a group: the window stops at the first hour of each day.

dimensions:
  unit: { dtype: str }
  hour: { dtype: int, ordered: true }
  day: { dtype: str }

maps:
  hour: { day: day }

variables:
  started:
    dims: [unit, hour]
    domain: binary
  on:
    dims: [unit, hour]
    domain: binary

constraints:
  stays_up_inside_its_day:
    dims: [unit, hour]
    expression: sum_back(started, along=hour, window=3, within=hour[day]) <= on

objective: { sense: minimize, expression: sum(on) }
```

$`\sum_{h' \in \mathcal{H} \,:\, 0 \le h -^{\mathrm{day}(h)} h' < 3} \mathit{started}_{h',u} \le \mathit{on}_{h,u} \qquad \forall\, h \in \mathcal{H},\ u \in \mathcal{U}`$

### `dual(constraint)`

`examples/operators/dual.yaml`

```yaml
description: >-
  After the solver runs, `dual(constraint)` has the constraint's dimensions,
  and each value is the marginal value of the constraint at that
  coordinate (its shadow price).

dimensions:
  snapshot: { dtype: int }

parameters:
  load: { dims: [snapshot] }

variables:
  p:
    dims: [snapshot]
    bounds: { lower: 0 }

constraints:
  balance:
    dims: [snapshot]
    expression: p >= load

expressions:
  price: dual(balance)

objective: { sense: minimize, expression: sum(p) }
```

$`\mathit{price}_{t} = \lambda_{\mathrm{balance},t} \qquad \forall\, t \in \mathcal{T}`$
<!-- gallery:end -->

!!! info "See also"

    - [Operators](../reference/language/operators.md), for what each operator
      accepts and what mathspec refuses
    - [`dual`](../reference/language/named.md#dual), for the entries that may call
      `dual`
    - [Typeset output](../reference/typeset.md), for the three formats the
      typesetter prints
