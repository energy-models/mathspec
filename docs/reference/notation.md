<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Every construct, as math

Look up any construct of the language to see the math that
[the typesetter](typeset.md) prints for it. You can also start from a symbol and
find the construct that printed it.

Each section shows the YAML of one construct, then its equation. Most fragments
come from one test spec,
[`tests/typesetting/golden/model.yaml`](https://github.com/energy-models/mathspec/blob/main/tests/typesetting/golden/model.yaml),
which holds every construct and does not make sense as an optimisation
problem. The curves come from the example specs that their section names.
[Operators](language/operators.md) says what each operator does.

The symbols are **derived** from the names in the file, so you see
$\mathrm{load}_{t}$ rather than $\ell_t$. A
[symbol table](typeset.md#symbol-tables) replaces the symbols and changes
nothing else.

<!-- notation:begin -->
### Legend

A dimension, a relation and a parameter declare no equation; what they print is the legend every spec opens with.

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str, ordered: true }
  bus: { dtype: str }
  zone: { dtype: str }
  season: { dtype: str }
  technology: { dtype: str }
  bp: { dtype: int, ordered: true } # the breakpoints every curve below runs through

relations:
  gen_bus: { key: generator, values: bus }
  zone_of: { key: bus, values: zone }
  area_of: { key: bus, values: zone, missing: absent } # a second map into the same set, to compare against; a bus may be in no area
  season_of: { key: snapshot, values: season }
  gen_zone: { key: [generator, snapshot], values: zone } # a map keyed by two dimensions: a call sums one away and joins on the other
  rep_of: { key: snapshot, values: { rep: snapshot } } # a map into its own dimension: the representative snapshot
  connection: { key: [generator, bus], missing: absent } # a bare relation, with no value columns: many-to-many, read only by sum with both ends named
  gen_bt: { key: generator, values: [bus, technology] } # one table with two value columns, read to both at once

parameters:
  p_max: { dims: [generator], missing: .inf } # a value: the legend says what a missing row reads as
  p_min: { dims: [generator] }
  cost: { dims: [generator], missing: neutral } # a reading: the legend names it
  load: { dims: [snapshot, bus] }
  is_flexible: { dims: [generator], dtype: bool, missing: false }
  zone_cap: { dims: [zone] }
  tech_cap: { dims: [bus, technology], missing: absent }
  min_up: { dims: [generator], dtype: int }
  eta: { dims: [generator] } # a Greek name that is *given*, so the rule wins and it prints as the word
  lead: { dims: [generator], dtype: int }
  budget: { dims: [] } # scalar: the legend says so rather than printing an empty product
  growth: { dims: [] } # the base of a power; the exponent is `lead`, a column
  bp_x: { dims: [generator, bp], missing: neutral } # the x-axis of every curve below, and what a derived mask is read from
  bp_y: { dims: [generator, bp], missing: neutral }
  bp_heat: { dims: [generator, bp] }
  bp_run: { dims: [generator, bp], dtype: bool } # how far each curve runs, so a piecewise entry has a mask to print
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` (`int` coordinates) with $`\mathrm{season\_of}: \mathcal{T} \to \mathcal{S},\ \mathrm{gen\_zone}: \mathcal{G} \times \mathcal{T} \to \mathcal{Z},\ \mathrm{rep\_of}: \mathcal{T} \to \mathcal{T}`$ |
| $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{gen\_bus}: \mathcal{G} \to \mathcal{B},\ \mathrm{gen\_zone}: \mathcal{G} \times \mathcal{T} \to \mathcal{Z},\ \mathrm{connection} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{gen\_bt}: \mathcal{G} \to \mathcal{B} \times \mathcal{E}`$, `connection` is `absent` where the data has no row |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{gen\_bus}: \mathcal{G} \to \mathcal{B},\ \mathrm{zone\_of}: \mathcal{B} \to \mathcal{Z},\ \mathrm{area\_of}: \mathcal{B} \to \mathcal{Z},\ \mathrm{connection} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{gen\_bt}: \mathcal{G} \to \mathcal{B} \times \mathcal{E}`$, `area_of` is `absent` where the data has no row, `connection` is `absent` where the data has no row |
| $`\mathcal{Z}`$ | index $`z`$ — `zone` with $`\mathrm{zone\_of}: \mathcal{B} \to \mathcal{Z},\ \mathrm{area\_of}: \mathcal{B} \to \mathcal{Z},\ \mathrm{gen\_zone}: \mathcal{G} \times \mathcal{T} \to \mathcal{Z}`$, `area_of` is `absent` where the data has no row |
| $`\mathcal{S}`$ | index $`s`$ — `season` with $`\mathrm{season\_of}: \mathcal{T} \to \mathcal{S}`$ |
| $`\mathcal{E}`$ | index $`e`$ — `technology` with $`\mathrm{gen\_bt}: \mathcal{G} \to \mathcal{B} \times \mathcal{E}`$ |
| $`\mathcal{A}`$ | index $`a`$ — `bp` |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{p}^{\mathrm{max}}`$ | `p_max` over $`\mathcal{G}`$, $`\infty`$ where the data has no row |
| $`\mathrm{p}^{\mathrm{min}}`$ | `p_min` over $`\mathcal{G}`$ |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{G}`$, `neutral` where the data has no row |
| $`\mathrm{load}`$ | `load` over $`\mathcal{B} \times \mathcal{T}`$ |
| $`\mathrm{is\_flexible}`$ | `is_flexible` over $`\mathcal{G}`$, `false` where the data has no row |
| $`\mathrm{zone\_cap}`$ | `zone_cap` over $`\mathcal{Z}`$ |
| $`\mathrm{tech\_cap}`$ | `tech_cap` over $`\mathcal{B} \times \mathcal{E}`$, `absent` where the data has no row |
| $`\mathrm{min\_up}`$ | `min_up` over $`\mathcal{G}`$ |
| $`\mathrm{eta}`$ | `eta` over $`\mathcal{G}`$ |
| $`\mathrm{lead}`$ | `lead` over $`\mathcal{G}`$ |
| $`\mathrm{budget}`$ | `budget` (scalar) |
| $`\mathrm{growth}`$ | `growth` (scalar) |
| $`\mathrm{bp\_x}`$ | `bp_x` over $`\mathcal{A} \times \mathcal{G}`$, `neutral` where the data has no row |
| $`\mathrm{bp\_y}`$ | `bp_y` over $`\mathcal{A} \times \mathcal{G}`$, `neutral` where the data has no row |
| $`\mathrm{bp\_heat}`$ | `bp_heat` over $`\mathcal{A} \times \mathcal{G}`$ |
| $`\mathrm{bp\_run}`$ | `bp_run` over $`\mathcal{A} \times \mathcal{G}`$ |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{dispatchable}`$ | `dispatchable` over $`\mathcal{G}`$ — a unit that dispatches and cannot be turned down |
| $`\mathrm{priced\_dispatch}`$ | `priced_dispatch` over $`\mathcal{G}`$ |

#### Variables

| Symbol | Meaning |
|---|---|
| $`p`$ | `p` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{spill}`$ | `spill` over $`\mathcal{T}`$ |
| $`\mathit{slack}`$ | `slack` over $`\mathcal{T}`$ |
| $`\theta`$ | `theta` over $`\mathcal{B}`$ |
| $`\mathit{on}`$ | `on` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{units}`$ | `units` over $`\mathcal{G}`$ |
| $`\mathit{spare}`$ | `spare` over $`\mathcal{G}`$ |
| $`\mathit{reserve}`$ | `reserve` (scalar) |
| $`\mathit{headroom}`$ | `headroom` (scalar), `neutral` where the mask leaves it out |
| $`\mathit{weight}`$ | `weight` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{fuel}`$ | `fuel` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{heat}`$ | `heat` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{op\_cost}`$ | `op_cost` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{warm}`$ | `warm` over $`\mathcal{G} \times \mathcal{T}`$ |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathrm{spend}^{\mathrm{cap}}`$ | `spend_cap` over $`\mathcal{G}`$ |
| $`\mathit{spend}`$ | `spend` over $`\mathcal{T}`$ — what a snapshot's dispatch costs |
| $`\mathrm{rating}`$ | `rating` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{lcoe}`$ | `lcoe` (scalar) |
| $`\mathit{net}`$ | `net` over $`\mathcal{T}`$ — what a snapshot spills, less what it lacks |
| $`\mathit{marginal\_price}`$ | `marginal_price` over $`\mathcal{B} \times \mathcal{T}`$ |
| $`\mathrm{startup\_cost}`$ | `startup_cost` over $`\mathcal{G} \times \mathcal{T}`$ — what starting a unit in this snapshot costs, which the horizon's edge changes |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`t \ominus^{\mathrm{relation}(t)} k`$ | `within=relation[...]` — $`t-k`$ inside the group of $`t`$ |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{relation}(t)}(t)`$ | `position(within=relation[...])` — the position of $`t`$ inside its group |
| $`\lvert \mathcal{T} \rvert`$ | the size of $`\mathcal{T}`$; $`\lvert \mathcal{T} \rvert - 1`$ is the last position |

### Variable domains

#### Lower and upper bounds

both bounds, and a where with all three connectives

```yaml
variables:
  p:
    dims: [snapshot, generator]
    where: "p_max > 0 AND NOT is_flexible OR p_min > 0"
    bounds: { lower: p_min, upper: p_max }
```

```math
\mathrm{p}^{\mathrm{min}}_{g} \le p_{g,t} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{p}^{\mathrm{max}}_{g} > 0 \wedge \neg \mathrm{is\_flexible}_{g} \vee \mathrm{p}^{\mathrm{min}}_{g} > 0
```

#### Lower bound only

```yaml
variables:
  spill:
    dims: [snapshot]
    bounds: { lower: 0 }
```

```math
\mathit{spill}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T}
```

#### Upper bound only

```yaml
variables:
  slack:
    dims: [snapshot]
    bounds: { upper: 100 }
```

```math
\mathit{slack}_{t} \le 100 \qquad \forall\, t \in \mathcal{T}
```

#### Unbounded variable

```yaml
variables:
  theta:
    dims: [bus]
```

```math
\theta_{b} \in \mathbb{R} \qquad \forall\, b \in \mathcal{B}
```

#### Binary domain

a binary domain, which is a set rather than a pair of bounds

```yaml
variables:
  on:
    dims: [snapshot, generator]
    domain: binary
```

```math
\mathit{on}_{g,t} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Bounded integer domain

an integer domain, which is both: bounds, and where the values live

```yaml
variables:
  units:
    dims: [generator]
    domain: integer
    bounds: { lower: 0, upper: 10 }
```

```math
0 \le \mathit{units}_{g} \le 10, \mathit{units}_{g} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G}
```

#### Unbounded integer domain

integer with neither bound: the domain is the whole line

```yaml
variables:
  spare:
    dims: [generator]
    domain: integer
```

```math
\mathit{spare}_{g} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G}
```

#### Scalar variable

an empty dims: a scalar entry, whose line carries no quantifier

```yaml
variables:
  reserve:
    dims: []
    bounds: { lower: 0 }
```

```math
\mathit{reserve} \ge 0
```

#### Scalar variable with a condition

scalar too, but masked, so the condition stands with no set beside it; neutral, so the legend names the reading

```yaml
variables:
  headroom:
    dims: []
    where: "budget"
    missing: neutral
    bounds: { lower: 0 }
```

```math
\mathit{headroom} \ge 0 \qquad \text{where } \mathrm{budget} \text{ is defined}
```

#### Variable in a special ordered set

the family a sos runs along

```yaml
variables:
  weight:
    dims: [snapshot, generator]
    bounds: { lower: 0, upper: 1 }
```

```math
0 \le \mathit{weight}_{g,t} \le 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Second axis of a curve

a curve's second axis

```yaml
variables:
  fuel:
    dims: [snapshot, generator]
    bounds: { lower: 0 }
```

```math
\mathit{fuel}_{g,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Third axis of a curve

its third, so one curve ties three expressions

```yaml
variables:
  heat:
    dims: [snapshot, generator]
    bounds: { lower: 0 }
```

```math
\mathit{heat}_{g,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Variable bounded by a curve

bounded by a curve rather than pinned to it

```yaml
variables:
  op_cost:
    dims: [snapshot, generator]
    bounds: { lower: 0 }
```

```math
\mathit{op\_cost}_{g,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Binary variable with a condition

a gate not every unit has, so the curve it gates is ungated where it does not exist

```yaml
variables:
  warm:
    dims: [snapshot, generator]
    domain: binary
    where: "is_flexible"
```

```math
\mathit{warm}_{g,t} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{is\_flexible}_{g}
```

### Objective

#### Products and powers in the objective

a sense, a product of two variables, a power over two parameters, a power of one of those, and the summations a scalar objective spells out beside two scalar terms

```yaml
objective:
  sense: maximize
  expression: sum(p * cost) + sum(p * p * cost) + sum(p * cost * growth ** lead) + sum(p * (growth ** lead) ** 2) + sum(p * p_max) - reserve + -headroom
```

```math
\max \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot \mathrm{cost}_{g} + \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot p_{g,t} \cdot \mathrm{cost}_{g} + \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot \mathrm{cost}_{g} \cdot \mathrm{growth}^{\mathrm{lead}_{g}} + \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot \left( \mathrm{growth}^{\mathrm{lead}_{g}} \right)^{2} + \sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot \mathrm{p}^{\mathrm{max}}_{g} - \mathit{reserve} - \mathit{headroom}
```

### Relations

#### Sum through a relation

```yaml
constraints:
  balance:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=gen_bus[bus]) + spill - slack == load
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} p_{g,t} + \mathit{spill}_{t} - \mathit{slack}_{t} = \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

#### Sum over every dimension

a sum naming no dim, whose domain is the one place the dims it took are said

```yaml
constraints:
  total:
    dims: []
    expression: sum(p) <= budget
```

```math
\sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \le \mathrm{budget}
```

#### `at` through a relation

at(), which re-indexes through a relation instead of an offset

```yaml
constraints:
  lookup:
    dims: [snapshot, bus]
    expression: spill <= at(zone_cap, by=zone_of[zone])
```

```math
\mathit{spill}_{t} \le \mathrm{zone\_cap}_{\mathrm{zone\_of}(b)} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

#### Sum into two value columns

one table read to two value columns: the domain carries a condition per column

```yaml
constraints:
  grouped_once:
    dims: [snapshot, bus, technology]
    expression: sum(p, over=generator, by=gen_bt[bus, technology]) <= tech_cap
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bt.bus}(g) = b \wedge \mathrm{gen\_bt.technology}(g) = e} p_{g,t} \le \mathrm{tech\_cap}_{b,e} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T},\ e \in \mathcal{E}
```

#### `at` through two value columns

the same table joined the other way, reading one slot through two columns

```yaml
constraints:
  looked_up_once:
    dims: [generator]
    expression: units <= at(tech_cap, by=gen_bt[bus, technology])
```

```math
\mathit{units}_{g} \le \mathrm{tech\_cap}_{\mathrm{gen\_bt.bus}(g),\mathrm{gen\_bt.technology}(g)} \qquad \forall\, g \in \mathcal{G}
```

#### Shift within one value column

a partition grouped by one named value column of a two-value table, and a position within both

```yaml
constraints:
  within_bus:
    dims: [generator]
    where: "position(generator, within=gen_bt[bus, technology]) == 0"
    expression: units <= shift(units, along=generator, offset=1, edge=0, within=gen_bt[bus])
```

```math
\mathit{units}_{g} \le \mathit{units}_{g \boxminus_{0}^{\mathrm{gen\_bt.bus}(g)} 1} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{pos}_{\left( \mathrm{gen\_bt.bus}(g),\ \mathrm{gen\_bt.technology}(g) \right)}(g) = 0
```

#### Sum through a bare relation

a sum through a bare relation: the domain is a row of the relation rather than a function's value

```yaml
constraints:
  relational:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=connection[bus]) <= load
```

```math
\sum_{g \in \mathcal{G} \,:\, \left( g,\ b \right) \in \mathrm{connection}} p_{g,t} \le \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

#### Bare relation as a condition

a bare relation as a where: the row of the frame has to be a member of the relation

```yaml
constraints:
  connected:
    dims: [snapshot, generator, bus]
    where: "connection"
    expression: p <= load
```

```math
p_{g,t} \le \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \left( g,\ b \right) \in \mathrm{connection}
```

#### Map into its own dimension

a map into its own dimension, read both ways: the frame is unchanged and the index is primed

```yaml
constraints:
  representative:
    dims: [snapshot]
    expression: sum(spill, over=snapshot, by=rep_of[rep]) <= at(spill, by=rep_of[rep])
```

```math
\sum_{t' \in \mathcal{T} \,:\, \mathrm{rep\_of}(t') = t} \mathit{spill}_{t'} \le \mathit{spill}_{\mathrm{rep\_of}(t)} \qquad \forall\, t \in \mathcal{T}
```

#### Sum through a two-key map

a grouping through a two-key map, summing one key away: the condition reads the other, and the row keeps it

```yaml
constraints:
  zonal:
    dims: [snapshot, zone]
    expression: sum(p, over=generator, by=gen_zone[zone]) <= zone_cap
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_zone}(g,\ t) = z} p_{g,t} \le \mathrm{zone\_cap}_{z} \qquad \forall\, t \in \mathcal{T},\ z \in \mathcal{Z}
```

#### Sum over the other key of a two-key map

the same table summing its other key away

```yaml
constraints:
  zonal_history:
    dims: [generator, zone]
    expression: sum(p, over=snapshot, by=gen_zone[zone]) <= zone_cap
```

```math
\sum_{t \in \mathcal{T} \,:\, \mathrm{gen\_zone}(g,\ t) = z} p_{g,t} \le \mathrm{zone\_cap}_{z} \qquad \forall\, g \in \mathcal{G},\ z \in \mathcal{Z}
```

#### Sum between the two keys of a map

the same table read between its two key columns: no value column is read, so the domain asks only that the row is there

```yaml
constraints:
  zonal_membership:
    dims: [snapshot]
    expression: sum(units, over=generator, by=gen_zone[snapshot]) <= budget
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_zone}(g,\ t) \text{ is defined}} \mathit{units}_{g} \le \mathrm{budget} \qquad \forall\, t \in \mathcal{T}
```

#### `at` through a two-key map

the same table joined the other way, reading the slot the row's own snapshot puts the generator in

```yaml
constraints:
  zonal_lookup:
    dims: [snapshot, generator]
    where: "gen_zone == 'north' AND position(generator, within=gen_zone[zone]) == 0"
    expression: p <= at(spill * zone_cap, by=gen_zone[zone])
```

```math
p_{g,t} \le \mathit{spill}_{t} \cdot \mathrm{zone\_cap}_{\mathrm{gen\_zone}(g,\ t)} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{gen\_zone}(g,\ t) = \text{'}\mathrm{north}\text{'} \wedge \mathrm{pos}_{\mathrm{gen\_zone}(g,\ t)}(g) = 0
```

### Arithmetic and literals

#### Signs, division and number literals

division, both unary signs, a sign beside a sign, floats with and without an exponent, bracketing

```yaml
constraints:
  arithmetic:
    dims: [snapshot]
    expression: >-
      sum(p / 2 + -cost - -1e-5 * p + 2.5e-7 * cost + 0.5 * p, over=generator)
      >= -sum(+p, over=generator) * -3
```

```math
\sum_{g \in \mathcal{G}} \left( \frac{p_{g,t}}{2} - \mathrm{cost}_{g} + 10^{-5} \cdot p_{g,t} + 2.5 \times 10^{-7} \cdot \mathrm{cost}_{g} + 0.5 \cdot p_{g,t} \right) \ge -\left( \sum_{g \in \mathcal{G}} p_{g,t} \right) \cdot \left( -3 \right) \qquad \forall\, t \in \mathcal{T}
```

#### Greek parameter name

a Greek-named parameter, which is given — so the convention wins and it prints as the word

```yaml
constraints:
  efficiency:
    dims: [snapshot, generator]
    expression: p <= eta * p_max
```

```math
p_{g,t} \le \mathrm{eta}_{g} \cdot \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Infinity literal

the infinity literal, which is the one way infinity prints

```yaml
constraints:
  ceiling:
    dims: [bus]
    expression: theta <= inf
```

```math
\theta_{b} \le \infty \qquad \forall\, b \in \mathcal{B}
```

### Named expressions

#### Plain expression in a constraint

names the plain expression: its symbol prints here, its definition once below

```yaml
constraints:
  budgeted:
    dims: [snapshot]
    expression: spend <= budget
```

```math
\mathit{spend}_{t} \le \mathrm{budget} \qquad \forall\, t \in \mathcal{T}
```

#### Signed sum substituted into a plus

names the signed sum on the right of a plus: inlined, its minus prints as a subtraction

```yaml
constraints:
  netted:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=gen_bus[bus]) + net == load
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{gen\_bus}(g) = b} p_{g,t} + \mathit{net}_{t} = \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

#### Cased expression in a constraint

names the cased expression: its symbol prints here, its block once below

```yaml
constraints:
  starts:
    dims: [snapshot, generator]
    expression: p <= startup_cost
```

```math
p_{g,t} \le \mathrm{startup\_cost}_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Expression with a declared frame in a constraint

names the expression with declared dims, read in the row's own order

```yaml
constraints:
  under_rating:
    dims: [snapshot, generator]
    expression: p <= rating
```

```math
p_{g,t} \le \mathrm{rating}_{g,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Plain named expression

a plain named expression: its symbol prints where it is used, its body once as a definition

```yaml
expressions:
  spend:
    expression: sum(p * cost, over=generator)
```

```math
\mathit{spend}_{t} = \sum_{g \in \mathcal{G}} p_{g,t} \cdot \mathrm{cost}_{g} \qquad \forall\, t \in \mathcal{T}
```

#### Named expression with a declared frame

dims declared in an order of their own, each one the expression is indexed over

```yaml
expressions:
  rating:
    dims: [generator, snapshot]
    expression: eta * p_max * sum(load, over=bus)
```

```math
\mathrm{rating}_{g,t} = \mathrm{eta}_{g} \cdot \mathrm{p}^{\mathrm{max}}_{g} \cdot \left( \sum_{b \in \mathcal{B}} \mathrm{load}_{b,t} \right) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Plain expression that is a signed sum

a plain expression that opens with a minus

```yaml
expressions:
  net:
    expression: -spill + slack
```

```math
\mathit{net}_{t} = -\mathit{spill}_{t} + \mathit{slack}_{t} \qquad \forall\, t \in \mathcal{T}
```

#### Expression defined by cases

a quantity defined by region: no two cases overlap, and `otherwise` is the rest

```yaml
expressions:
  startup_cost:
    dims: [snapshot, generator]
    cases:
      opening: { when: "position(snapshot) == 0", expression: cost }
      winter: { when: "position(snapshot) > 0 and season_of == 'winter'", expression: cost * 2 }
    otherwise: 0
```

```math
\mathrm{startup\_cost}_{g,t} = \begin{cases} \mathrm{cost}_{g} & \text{if } \mathrm{pos}(t) = 0 \\ \mathrm{cost}_{g} \cdot 2 & \text{if } \mathrm{pos}(t) > 0 \wedge \mathrm{season\_of}(t) = \text{'}\mathrm{winter}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Data-only expression

a data-only entry, so a where may compare it

```yaml
expressions:
  spend_cap: cost * 2
```

```math
\mathrm{spend}^{\mathrm{cap}}_{g} = \mathrm{cost}_{g} \cdot 2 \qquad \forall\, g \in \mathcal{G}
```

#### Named expression in a condition

an expressions: entry on a side, read by the name the file gave it

```yaml
constraints:
  capped:
    dims: [snapshot, generator]
    where: "spend_cap > 0 OR NOT is_flexible"
    expression: p <= p_max
```

```math
p_{g,t} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{spend}^{\mathrm{cap}}_{g} > 0 \vee \neg \mathrm{is\_flexible}_{g}
```

#### Reported expression

nothing in the math reads it, so its divisor may carry a variable

```yaml
expressions:
  lcoe: sum(p * cost) / sum(p)
```

```math
\mathit{lcoe} = \frac{\sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \cdot \mathrm{cost}_{g}}{\sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t}}
```

#### Dual of a constraint

the row dual of a constraint, the one builtin only an entry the math never reads may call

```yaml
expressions:
  marginal_price: dual(balance)
```

```math
\mathit{marginal\_price}_{b,t} = \lambda_{\mathrm{balance},b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

### Named conditions

#### Named condition

a named condition with its words: a use prints the symbol over the dims its condition reads, the condition prints once

```yaml
conditions:
  dispatchable:
    condition: "p_max > 0 AND NOT is_flexible"
```

```math
\mathrm{dispatchable}_{g} \iff \mathrm{p}^{\mathrm{max}}_{g} > 0 \wedge \neg \mathrm{is\_flexible}_{g} \qquad \forall\, g \in \mathcal{G}
```

#### Condition that reads a condition

the one-line form, reading another mask and a data-only entry

```yaml
conditions:
  priced_dispatch: "dispatchable AND spend_cap > 0"
```

```math
\mathrm{priced\_dispatch}_{g} \iff \mathrm{dispatchable}_{g} \wedge \mathrm{spend}^{\mathrm{cap}}_{g} > 0 \qquad \forall\, g \in \mathcal{G}
```

#### Named condition in a condition

a mask as the where, beside a condition of the constraint's own

```yaml
constraints:
  masked:
    dims: [snapshot, generator]
    where: "priced_dispatch AND position(snapshot) > 0"
    expression: p <= p_max
```

```math
p_{g,t} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{priced\_dispatch}_{g} \wedge \mathrm{pos}(t) > 0
```

### Shifts

#### Cyclic and acyclic shift

roll (cyclic) and shift (acyclic) in one equation

```yaml
constraints:
  ramp:
    dims: [snapshot, generator]
    expression: p - shift(p, along=snapshot, offset=1, edge='wrap') <= shift(p, along=snapshot, offset=1) + p_max
```

```math
p_{g,t} - p_{g,t \ominus 1} \le p_{g,t - 1} + \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Filled and forward shifts

the two translations `ramp` leaves out: a fill, and forwards

```yaml
constraints:
  edges:
    dims: [snapshot, generator]
    expression: >-
      shift(p, along=snapshot, offset=1, edge=0)
      <= shift(p, along=snapshot, offset=-1, edge=0) + p_max
```

```math
p_{g,t \boxminus_{0} 1} \le p_{g,t \boxplus_{0} 1} + \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Cyclic forward shift

the cyclic translation forwards, which is a fourth symbol again

```yaml
constraints:
  ahead:
    dims: [snapshot, generator]
    expression: p <= shift(p, along=snapshot, offset=-1, edge='wrap')
```

```math
p_{g,t} \le p_{g,t \oplus 1} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Composed shifts

two steps of one policy are one step; a zero step is none at all

```yaml
constraints:
  composed:
    dims: [snapshot, generator]
    expression: shift(shift(p, along=snapshot, offset=1), along=snapshot, offset=1) <= shift(p_max, along=generator, offset=0)
```

```math
p_{g,t - 2} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Nested shifts that do not compose

a named offset under a numbered one stays two steps, not their sum

```yaml
constraints:
  uncomposed:
    dims: [snapshot, generator]
    expression: shift(shift(p, along=snapshot, offset=lead, edge=0), along=snapshot, offset=1) <= p_max
```

```math
p_{g,\left( t - 1 \right) \boxminus_{0} \mathrm{lead}} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Shift along two dimensions

two dimensions translated at one leaf, each with its own policy

```yaml
constraints:
  crossed:
    dims: [snapshot, generator]
    expression: shift(shift(p, along=snapshot, offset=1, edge='wrap'), along=generator, offset=-1) <= p_max
```

```math
p_{g + 1,t \ominus 1} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Shift by a parameter offset

an offset the data carries, so it prints as a symbol rather than a number

```yaml
constraints:
  lead_time:
    dims: [snapshot, generator]
    expression: shift(p, along=snapshot, offset=lead, edge=0) <= p_max
```

```math
p_{g,t \boxminus_{0} \mathrm{lead}} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Cyclic shift within a group

a translation partitioned by a relation: the group rides on the operator

```yaml
constraints:
  in_season:
    dims: [snapshot, generator]
    expression: p <= shift(p, along=snapshot, offset=1, edge='wrap', within=season_of[season])
```

```math
p_{g,t} \le p_{g,t \ominus^{\mathrm{season\_of}(t)} 1} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Filled shift within a group

the same group, with a fill: each season's opening row is kept and given a zero

```yaml
constraints:
  held_in_season:
    dims: [snapshot, generator]
    expression: p <= shift(p, along=snapshot, offset=1, edge=0, within=season_of[season])
```

```math
p_{g,t} \le p_{g,t \boxminus_{0}^{\mathrm{season\_of}(t)} 1} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

### Trailing windows

#### Window of fixed width

a trailing window of fixed width

```yaml
constraints:
  window:
    dims: [snapshot, generator]
    expression: sum_back(on, along=snapshot, window=3) <= units
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < 3} \mathit{on}_{g,t'} \le \mathit{units}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Window with a parameter width

the same window, its width in the data and its edge wrapped

```yaml
constraints:
  history:
    dims: [snapshot, generator]
    expression: sum_back(on, along=snapshot, window=min_up, edge='wrap') <= units
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t \ominus t' < \mathrm{min\_up}} \mathit{on}_{g,t'} \le \mathit{units}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Window within a group

a window partitioned by a relation: the group rides on the operator

```yaml
constraints:
  seasonal_window:
    dims: [snapshot, generator]
    expression: sum_back(on, along=snapshot, window=3, within=season_of[season]) <= units
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t -^{\mathrm{season\_of}(t)} t' < 3} \mathit{on}_{g,t'} \le \mathit{units}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

### Piecewise curves

A curve prints as the curve it states, over the frame the entry builds one per coordinate of, and its expansion prints the rows that curve stands for. One row per `method:`, each from the spec named under it, so the symbols in this section are that spec's.

#### Adjacency method

`method: adjacency` — a binary per segment, and a row making the two nonzero weights neighbours, in `examples/ports/transport_pwl.yaml`.

Rendered with the sidecar symbol table `examples/symbols/transport_pwl.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  economies_of_scale_lam: "\\lambda"
  economies_of_scale_seg: "\\delta"
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  economies_of_scale:
    over: bp
    links:
      - [shipment, bp_x]
      - [scaled, bp_y]
```

```math
\left( \mathit{shipment}_{m,p},\ \mathit{scaled}_{m,p} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{b},\ \mathrm{y}_{b}) \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

Written out by `spec.expand()`:

```math
0 \le \lambda_{b,m,p} \le 1 \qquad \forall\, b \in \mathcal{B},\ m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\delta_{b,m,p} \in \{0, 1\} \qquad \forall\, b \in \mathcal{B},\ m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\sum_{b \in \mathcal{B}} \lambda_{b,m,p} = 1 \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\mathit{shipment}_{m,p} = \sum_{b \in \mathcal{B}} \lambda_{b,m,p} \cdot \mathrm{x}_{b} \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\mathit{scaled}_{m,p} = \sum_{b \in \mathcal{B}} \lambda_{b,m,p} \cdot \mathrm{y}_{b} \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\sum_{b \in \mathcal{B}} \delta_{b,m,p} \le 1 \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\lambda_{b,m,p} \le \delta_{b,m,p} + \delta_{b \boxminus_{0} 1,m,p} \qquad \forall\, b \in \mathcal{B},\ m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\mathrm{x}_{b} \text{ is defined} \wedge \mathrm{y}_{b} \text{ is defined} \qquad \forall\, b \in \mathcal{B}
```

#### SOS2 method

`method: sos2` — the same weights, restricted by a set the solver branches on (the sos rules), in `examples/sos.yaml`.

Rendered with the sidecar symbol table `examples/symbols/sos.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  cost_curve_lam: "\\lambda"
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  cost_curve:
    over: bp
    links:
      - [dispatch, bp_x]
      - [op_cost, bp_y]
    method: sos2
```

```math
\left( \mathit{dispatch}_{g,t},\ \mathit{op\_cost}_{g,t} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{b,g},\ \mathrm{y}_{b,g}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
0 \le \lambda_{b,g,t} \le 1 \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\sum_{b \in \mathcal{B}} \lambda_{b,g,t} = 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{dispatch}_{g,t} = \sum_{b \in \mathcal{B}} \lambda_{b,g,t} \cdot \mathrm{x}_{b,g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{op\_cost}_{g,t} = \sum_{b \in \mathcal{B}} \lambda_{b,g,t} \cdot \mathrm{y}_{b,g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\left( \lambda_{b,g,t} \right)_{b \in \mathcal{B}} \in \mathrm{SOS}2 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathrm{x}_{b,g} \text{ is defined} \wedge \mathrm{y}_{b,g} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G}
```

#### Convex method

`method: convex` — nothing, so the weights range over the hull, which is a pure LP, in `examples/piecewise.yaml`.

Rendered with the sidecar symbol table `examples/symbols/piecewise.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  cost_curve_lam: "\\lambda"
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  cost_curve:
    over: bp
    links:
      - [dispatch, bp_x]
      - [op_cost, bp_y]
    method: convex
```

```math
\left( \mathit{dispatch}_{g,t},\ \mathit{op\_cost}_{g,t} \right) \in \mathrm{conv}_{b \in \mathcal{B}}(\mathrm{x}_{b,g},\ \mathrm{y}_{b,g}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
0 \le \lambda_{b,g,t} \le 1 \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\sum_{b \in \mathcal{B}} \lambda_{b,g,t} = 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{dispatch}_{g,t} = \sum_{b \in \mathcal{B}} \lambda_{b,g,t} \cdot \mathrm{x}_{b,g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{op\_cost}_{g,t} = \sum_{b \in \mathcal{B}} \lambda_{b,g,t} \cdot \mathrm{y}_{b,g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathrm{x}_{b,g} \text{ is defined} \wedge \mathrm{y}_{b,g} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G}
```

```math
\mathrm{x}_{b \boxminus_{0} 1,g} < \mathrm{x}_{b,g} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{pos}(b) > 0
```

```math
\lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{b,g} - \mathrm{y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{x}_{b \boxplus_{0} 1,g} - \mathrm{x}_{b,g} \right) > \left( \mathrm{y}_{b \boxplus_{0} 1,g} - \mathrm{y}_{b,g} \right) \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \vee \lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{b,g} - \mathrm{y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{x}_{b \boxplus_{0} 1,g} - \mathrm{x}_{b,g} \right) < \left( \mathrm{y}_{b \boxplus_{0} 1,g} - \mathrm{y}_{b,g} \right) \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \qquad \forall\, g \in \mathcal{G}
```

#### LP method

`method: lp` — no weights, but one row per segment line, plus the two rows holding the domain, in `examples/piecewise_lp.yaml`.

Rendered with the sidecar symbol table `examples/symbols/piecewise_lp.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  cost_curve:
    over: bp
    links:
      - [dispatch, bp_x]
      - [op_cost, bp_y, ">="]
    method: lp
```

```math
\mathit{op\_cost}_{g,t} \ge \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{b,g},\ \mathrm{y}_{b,g})(\mathit{dispatch}_{g,t}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
\mathit{op\_cost}_{g,t} \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \ge \left( \mathrm{y}_{b,g} - \mathrm{y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathit{dispatch}_{g,t} - \mathrm{x}_{b,g} \right) + \mathrm{y}_{b,g} \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{pos}(b) > 0
```

```math
\mathit{dispatch}_{g,t} \ge \mathrm{x}_{b,g} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{pos}(b) = 0
```

```math
\mathit{dispatch}_{g,t} \le \mathrm{x}_{b,g} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{pos}(b) = \lvert \mathcal{B} \rvert - 1
```

```math
\mathrm{x}_{b,g} \text{ is defined} \wedge \mathrm{y}_{b,g} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G}
```

```math
\mathrm{x}_{b \boxminus_{0} 1,g} < \mathrm{x}_{b,g} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{pos}(b) > 0
```

```math
\left( \mathrm{y}_{b,g} - \mathrm{y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{x}_{b \boxplus_{0} 1,g} - \mathrm{x}_{b,g} \right) \le \left( \mathrm{y}_{b \boxplus_{0} 1,g} - \mathrm{y}_{b,g} \right) \cdot \left( \mathrm{x}_{b,g} - \mathrm{x}_{b \boxminus_{0} 1,g} \right) \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1
```

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{x}_{b,g} \text{ is defined} \} \rvert \ge 2 \qquad \forall\, g \in \mathcal{G}
```

### Special ordered sets

A set prints under Subject to, after the constraints and before the curves, because a solver holds it as a constraint. Under it are the rows it is written out as.

#### Special ordered set of type 2

at most two adjacent members nonzero, one set per snapshot

```yaml
sos:
  adjacent:
    variable: weight
    along: generator
    type: 2
```

```math
\left( \mathit{weight}_{g,t} \right)_{g \in \mathcal{G}} \in \mathrm{SOS}2 \qquad \forall\, t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
\mathit{adjacent\_seg}_{g,t} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\sum_{g \in \mathcal{G}} \mathit{adjacent\_seg}_{g,t} \le 1 \qquad \forall\, t \in \mathcal{T}
```

```math
\mathit{weight}_{g,t} \le \mathit{adjacent\_seg}_{g,t} + \mathit{adjacent\_seg}_{g \boxminus_{0} 1,t} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

### Assumptions

#### Two parameters compared

two parameters, which is arithmetic like any other

```yaml
assumptions:
  bounds_do_not_cross: "p_min <= p_max"
```

```math
\mathrm{p}^{\mathrm{min}}_{g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G}
```

#### Connective in an assumption

a connective, so the line has no relation to align on

```yaml
assumptions:
  efficiency_is_a_fraction: "eta > 0 AND eta <= 1"
```

```math
\mathrm{eta}_{g} > 0 \wedge \mathrm{eta}_{g} \le 1 \qquad \forall\, g \in \mathcal{G}
```

#### Parameter compared to a literal

one parameter against a literal

```yaml
assumptions:
  lead_times_are_short: "lead <= 3"
```

```math
\mathrm{lead}_{g} \le 3 \qquad \forall\, g \in \mathcal{G}
```

#### Two relations compared

two maps into one set, compared row by row

```yaml
assumptions:
  zones_agree: "zone_of == area_of"
```

```math
\mathrm{zone\_of}(b) = \mathrm{area\_of}(b) \qquad \forall\, b \in \mathcal{B}
```

#### Reduction in an assumption

a reduction on a side, leaving nothing to quantify

```yaml
assumptions:
  budget_covers_the_peak: "sum(p_max, over=generator) >= budget"
```

```math
\sum_{g \in \mathcal{G}} \mathrm{p}^{\mathrm{max}}_{g} \ge \mathrm{budget}
```

#### Shift in an assumption

a translation inside arithmetic, and a position keeping the vacated row out

```yaml
assumptions:
  ramps_are_gentle:
    holds: "load - shift(load, along=snapshot, offset=1, edge=0) <= budget"
    where: "position(snapshot) > 0"
```

```math
\mathrm{load}_{b,t} - \mathrm{load}_{b,t \boxminus_{0} 1} \le \mathrm{budget} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \mathrm{pos}(t) > 0
```

#### Assumption with a boolean condition

a bare bool parameter as the where

```yaml
assumptions:
  flexible_units_have_headroom:
    holds: "p_min < p_max"
    where: "is_flexible"
```

```math
\mathrm{p}^{\mathrm{min}}_{g} < \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{is\_flexible}_{g}
```

#### Assumption with a relation condition

a relation comparison as the where, over a frame two dims wide

```yaml
assumptions:
  northern_demand_is_real:
    holds: "load >= 0"
    where: "zone_of == 'north'"
```

```math
\mathrm{load}_{b,t} \ge 0 \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \mathrm{zone\_of}(b) = \text{'}\mathrm{north}\text{'}
```

### Where conditions

#### Parameter as a condition

a parameter over nothing, and a mask that is a bare parameter

```yaml
constraints:
  scalar:
    dims: [generator]
    where: "cost"
    expression: units <= budget
```

```math
\mathit{units}_{g} \le \mathrm{budget} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{cost}_{g} \text{ is defined}
```

#### Variable and label conditions

a mask on a variable's existence, and one on a dimension's label

```yaml
constraints:
  running:
    dims: [snapshot, bus]
    where: "theta AND snapshot >= 3"
    expression: theta <= load
```

```math
\theta_{b} \le \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \theta_{b} \text{ exists} \wedge t \ge 3
```

#### Position in a dimension

a position in a dimension, and the same position within a group

```yaml
constraints:
  first:
    dims: [snapshot, generator]
    where: "position(snapshot) == 0 OR position(snapshot, within=season_of[season]) == 0"
    expression: on == 1
```

```math
\mathit{on}_{g,t} = 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{pos}(t) = 0 \vee \mathrm{pos}_{\mathrm{season\_of}(t)}(t) = 0
```

#### Position counted from the end

the same two counted from the end, which print against a size rather than as themselves

```yaml
constraints:
  last:
    dims: [snapshot, generator]
    where: "position(snapshot) == -1 OR position(snapshot, within=season_of[season]) == -1"
    expression: on == 0
```

```math
\mathit{on}_{g,t} = 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{pos}(t) = \lvert \mathcal{T} \rvert - 1 \vee \mathrm{pos}_{\mathrm{season\_of}(t)}(t) = \lvert \mathcal{T}_{\mathrm{season\_of}(t)} \rvert - 1
```

#### Relation compared to a label

a relation compared to a label, to another relation, and to nothing

```yaml
constraints:
  northern:
    dims: [snapshot, bus]
    where: "zone_of == 'north' AND zone_of != area_of AND zone_of"
    expression: slack <= load
```

```math
\mathit{slack}_{t} \le \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \mathrm{zone\_of}(b) = \text{'}\mathrm{north}\text{'} \wedge \mathrm{zone\_of}(b) \neq \mathrm{area\_of}(b) \wedge \mathrm{zone\_of}(b) \text{ is defined}
```

#### Constant true condition

a mask that is only the constant true, which the language says is no mask at all — so none prints

```yaml
constraints:
  always:
    dims: [snapshot]
    where: "true"
    expression: spill >= 0
```

```math
\mathit{spill}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T}
```

#### Constant true inside a condition

the same constant *inside* a mask, where it is what the file says and prints

```yaml
constraints:
  redundant:
    dims: [snapshot]
    where: "True AND spill"
    expression: spill >= 0
```

```math
\mathit{spill}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T} \,:\, \mathit{spill}_{t} \text{ exists}
```

#### Constant false condition

the other constant mask, which says the rows are none and is worth seeing

```yaml
constraints:
  never:
    dims: [snapshot]
    where: "false"
    expression: slack >= 0
```

```math
\mathit{slack}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T} \,:\, \bot
```

#### Comparison of two expressions

a mask comparing two expressions, which prints as the arithmetic it is

```yaml
constraints:
  margin:
    dims: [snapshot, generator]
    where: "p_max - p_min > cost / 2"
    expression: p <= p_max
```

```math
p_{g,t} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{p}^{\mathrm{max}}_{g} - \mathrm{p}^{\mathrm{min}}_{g} > \frac{\mathrm{cost}_{g}}{2}
```

#### Shift and lookup in a condition

a translation under a comparison names its edge, a lookup reads through a relation, and the position keeps the vacated row out

```yaml
constraints:
  ramped:
    dims: [snapshot, bus]
    where: "load - shift(load, along=snapshot, offset=1, edge=0) <= at(zone_cap, by=zone_of[zone]) AND position(snapshot) > 0"
    expression: slack <= load
```

```math
\mathit{slack}_{t} \le \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \mathrm{load}_{b,t} - \mathrm{load}_{b,t \boxminus_{0} 1} \le \mathrm{zone\_cap}_{\mathrm{zone\_of}(b)} \wedge \mathrm{pos}(t) > 0
```

#### Reduction in a scalar condition

a reduction on a side of a scalar mask, so nothing is left to quantify

```yaml
constraints:
  covered:
    dims: []
    where: "sum(p_max, over=generator) >= budget"
    expression: sum(p) <= budget
```

```math
\sum_{g \in \mathcal{G},\ t \in \mathcal{T}} p_{g,t} \le \mathrm{budget} \qquad \text{where } \sum_{g \in \mathcal{G}} \mathrm{p}^{\mathrm{max}}_{g} \ge \mathrm{budget}
```

#### Count over a dimension

a count of the coordinates a condition admits, which reduces one dim away

```yaml
constraints:
  counted:
    dims: [bus]
    where: "count(tech_cap > 0, over=technology) >= 2"
    expression: theta <= budget
```

```math
\theta_{b} \le \mathrm{budget} \qquad \forall\, b \in \mathcal{B} \,:\, \lvert \{ e \in \mathcal{E} \,:\, \mathrm{tech\_cap}_{b,e} > 0 \} \rvert \ge 2
```

#### Count along a dimension of the frame

the same count along a dim the frame carries, so the set takes a primed dummy

```yaml
constraints:
  counted_here:
    dims: [bus, technology]
    where: "count(tech_cap > 0, over=technology) >= 2"
    expression: theta <= tech_cap
```

```math
\theta_{b} \le \mathrm{tech\_cap}_{b,e} \qquad \forall\, b \in \mathcal{B},\ e \in \mathcal{E} \,:\, \lvert \{ e' \in \mathcal{E} \,:\, \mathrm{tech\_cap}_{b,e'} > 0 \} \rvert \ge 2
```

#### Condition at the previous coordinate

a condition read one coordinate back, which is false where the translation vacates

```yaml
constraints:
  run_start:
    dims: [snapshot, bus]
    where: "load AND NOT shift(load, along=snapshot, offset=1)"
    expression: slack <= load
```

```math
\mathit{slack}_{t} \le \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \mathrm{load}_{b,t} \text{ is defined} \wedge \neg \left( \mathrm{load}_{b,t - 1} \text{ is defined} \right)
```

#### Condition through a relation

a condition read through a relation: a bus is held only where its zone has a cap at all

```yaml
constraints:
  zoned:
    dims: [bus]
    where: "at(zone_cap, by=zone_of[zone])"
    expression: theta <= budget
```

```math
\theta_{b} \le \mathrm{budget} \qquad \forall\, b \in \mathcal{B} \,:\, \mathrm{zone\_cap}_{\mathrm{zone\_of}(b)} \text{ is defined}
```
<!-- notation:end -->
