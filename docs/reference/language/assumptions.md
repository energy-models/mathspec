<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Assumptions

This page describes the `assumptions:` section, which states what the data
attached to a spec must satisfy. mathspec reads each assumption at load,
checks the dimensions and dtypes of its condition, and prints it in the
[typeset document](../typeset.md). mathspec does not check the data itself,
because mathspec holds no data. Software that reads a spec
([a tool](../glossary.md#tool)), such as the tool that attaches data and builds
the model (an engine), runs each check.

## `assumptions`

An assumption is a named [condition](expressions.md#conditions) that every
row of the data must meet. In the spec below, the lower bound of each
generator must not exceed its upper bound:

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  p_min: { dims: [generator] }
  p_max: { dims: [generator] }
variables:
  p:
    dims: [generator]
    bounds: { lower: p_min, upper: p_max }
objective:
  sense: minimize
  expression: sum(p, over=generator)
assumptions:
  bounds_do_not_cross: "p_min <= p_max"
```

```math
\mathrm{p}^{\mathrm{min}}_{g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G}
```

The typesetter prints the assumption under its own _Assumptions_ heading, over
every generator.

An entry is one condition string, or a mapping when it has more than the
condition. `bounds_do_not_cross: "p_min <= p_max"` above is the short
form of `bounds_do_not_cross: { holds: "p_min <= p_max" }`.

| Key           | Required | Default | What it does                                                                                                                         |
| ------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `holds`       | yes      |         | States, in the [condition grammar](expressions.md#conditions), the condition the data must meet.                                     |
| `where`       | no       | `null`  | Selects, in the same grammar, the combinations of labels (the [coordinates](../glossary.md#coordinate)) the condition is checked at. |
| `description` | no       | `null`  | Describes why the rule is there. A tool that refuses the data quotes it.                                                             |

An entry has no `dims:`. Its condition must be true at every coordinate of the
dimensions that `holds` and `where` use together. As in any `where:`, a condition
over fewer dimensions than that repeats along the others.

## Conditions in an assumption

A condition may use everything the
[condition grammar](expressions.md#conditions) accepts, including arithmetic
on either side of a comparison. The spec below states three assumptions: a
range, a sum over all generators, and a comparison with the previous snapshot:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  eta: { dims: [generator] }
  p_max: { dims: [generator] }
  peak: { dims: [] }
  load: { dims: [snapshot] }
  ramp_limit: { dims: [] }
variables:
  p:
    dims: [snapshot, generator]
    bounds: { lower: 0, upper: p_max }
constraints:
  meet_load:
    dims: [snapshot]
    expression: sum(p, over=generator) == load
objective:
  sense: minimize
  expression: sum(p)
assumptions:
  efficiency_is_a_fraction: "eta > 0 AND eta <= 1"
  peak_is_reachable: "sum(p_max, over=generator) >= peak"
  ramps_are_gentle:
    holds: "load - shift(load, along=snapshot, offset=1, edge=0) <= ramp_limit"
    where: "position(snapshot) > 0"
    description: the first snapshot has no predecessor to ramp from
```

```math
\mathrm{eta}_{g} > 0 \wedge \mathrm{eta}_{g} \le 1 \qquad \forall\, g \in \mathcal{G}
```

```math
\sum_{g \in \mathcal{G}} \mathrm{p}^{\mathrm{max}}_{g} \ge \mathrm{peak}
```

```math
\mathrm{load}_{t} - \mathrm{load}_{t \boxminus_{0} 1} \le \mathrm{ramp\_limit} \qquad \forall\, t \in \mathcal{T} \,:\, \mathrm{pos}(t) > 0
```

The first assumption is checked for every generator, and the second is checked
once for the whole spec. The third is checked at every snapshot except the first,
because its `where:` leaves the first one out.

A [`where:`](absence.md#where) leaves out the rows where it is false. With data
attached, the tool never checks a row that the `where:` leaves out. Where a
parameter in the `where:` has no value, its comparison is false, so the
`where:` leaves that row out too.

## Refused assumptions

mathspec refuses an assumption at load when it can decide the condition
without data. A condition that is true whatever the data is (it folds to true)
assumes nothing:

```text
Assumption 'sound': the condition 'c > 0 OR true' folds to true, so it assumes nothing of the data. Delete it, or name a parameter it constrains.
```

`c > 0 OR true` is true whatever the value of `c` is.

A condition that folds to false holds on no data, and for `c > 0 AND false`
mathspec prints:

```text
Assumption 'sound': the condition 'c > 0 AND false' folds to false, so it holds on no data at all. Delete it, or write the condition the data can satisfy.
```

mathspec suggests two rewrites: no entry, or a condition that the data can
satisfy.

A `where:` that folds is refused in the same way. One that folds to true
narrows nothing:

```text
Assumption 'sound': the `where:` condition 'c > 0 OR true' folds to true, so it narrows nothing. Delete the `where:`.
```

That `where:` admits every row, so mathspec suggests the rewrite: no
`where:`.

One that folds to false leaves no row for the tool to check:

```text
Assumption 'sound': the `where:` condition 'c > 0 AND false' folds to false, so the assumption is checked on no row. Delete the entry, or write a `where:` condition the data can satisfy.
```

That `where:` admits no row, so the tool checks nothing.

A tool checks an assumption against the data only, so mathspec refuses a
variable in its condition. For a bare variable name `p` in `holds:`, mathspec prints:

```text
Assumption 'sound': variable 'p' appears in 'holds:', and an assumption checks only data. Name a parameter, or state the rule as a constraint.
```

mathspec suggests two rewrites: a parameter in the condition, or the rule
stated as a constraint.

mathspec also
[refuses](parameters-variables-constraints.md#constraints) a constraint with
no variable on either side, and suggests an `assumptions:` entry as the
rewrite.

## What a curve assumes

A [`piecewise:`](piecewise.md) entry named `curve` adds assumptions of its
own. [`to_spec`](../api.md#mathspec.to_spec) derives them from the `method:` of the entry, its `points:` and
the sign on its links. The typesetter prints them under the same _Assumptions_
heading as the assumptions you write, and
[`spec.expand()`](../spec.md#mathspec.spec.Spec.expand) writes them out as
`assumptions:` entries with these names:

| Entry               | Added for               | What it requires                                                                                                 |
| ------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `curve_complete`    | every entry             | every values parameter has a row at every breakpoint the curve runs through                                      |
| `curve_increasing`  | `convex`, `lp`          | the breakpoints of the pinned link, or of the first link where both are pinned, strictly increase along `over`   |
| `curve_curvature`   | `convex`, `lp`          | with a `>=` link the curve is convex, with a `<=` link concave, and with both links pinned it bends one way only |
| `curve_breakpoints` | `lp`                    | each curve has at least two breakpoints                                                                          |
| `curve_contiguous`  | an entry with `points:` | the marked breakpoints form one consecutive run of at least one                                                  |

For an [`lp`](piecewise.md#method) entry named `cost_curve`, with its second link signed `>=`, the
typesetter prints the first three added assumptions as:

```math
\mathrm{bp\_x}_{g,b} \text{ is defined} \wedge \mathrm{bp\_y}_{g,b} \text{ is defined} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B}
```

```math
\mathrm{bp\_x}_{g,b \boxminus_{0} 1} < \mathrm{bp\_x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) > 0
```

```math
\left( \mathrm{bp\_y}_{g,b} - \mathrm{bp\_y}_{g,b \boxminus_{0} 1} \right) \cdot \left( \mathrm{bp\_x}_{g,b \boxplus_{0} 1} - \mathrm{bp\_x}_{g,b} \right) \le \left( \mathrm{bp\_y}_{g,b \boxplus_{0} 1} - \mathrm{bp\_y}_{g,b} \right) \cdot \left( \mathrm{bp\_x}_{g,b} - \mathrm{bp\_x}_{g,b \boxminus_{0} 1} \right) \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1
```

The first requires a row in both tables at every breakpoint. The second
requires that `bp_x` rise from one breakpoint to the next. The third requires
that each segment be no steeper than the one after it, which makes the curve convex.

!!! info "See also"

    - [Reading a spec and its program](../reading.md#what-the-data-has-to-satisfy)
      for how a tool runs these checks.
    - [Piecewise curves and SOS](piecewise.md) for the entries that add
      assumptions of their own.
