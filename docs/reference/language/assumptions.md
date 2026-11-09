<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Assumptions

This page describes the `assumptions:` section, which states what the data
attached to a spec must satisfy. mathspec reads each assumption at load,
checks the dimensions and dtypes of its condition, refuses one that the
`where:` of the model's own entries already break
([rows of the model](#rows-of-the-model)), and prints it in the
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

## Rows of the model

A bare variable name in an assumption is true where the variable exists, and a
bare constraint name is true where the constraint has a row. Which rows exist
is known once the data is attached, before any solve. The spec below bounds the
dispatch `p` of each generator with one constraint for each combination of two
flags, and the assumption requires a bound wherever `p` exists:

```yaml
dimensions:
  generator: { dtype: str }
  snapshot: { dtype: int, ordered: true }
parameters:
  p_nom: { dims: [generator] }
  p_max_pu: { dims: [snapshot, generator], missing: 1 }
  extendable: { dims: [generator], dtype: bool, missing: false }
  committable: { dims: [generator], dtype: bool, missing: false }
variables:
  p: { dims: [snapshot, generator] }
  p_nom_opt: { dims: [generator], where: extendable, bounds: { lower: 0 } }
  status: { dims: [snapshot, generator], where: committable, domain: binary }
constraints:
  p_upper_fixed:
    dims: [snapshot, generator]
    where: NOT extendable AND NOT committable
    expression: p <= p_max_pu * p_nom
  p_upper_extendable:
    dims: [snapshot, generator]
    where: extendable AND NOT committable
    expression: p <= p_max_pu * p_nom_opt
  p_upper_committable:
    dims: [snapshot, generator]
    where: committable
    expression: p <= p_max_pu * p_nom * status
assumptions:
  dispatch_has_an_upper_bound:
    holds: p_upper_fixed OR p_upper_extendable OR p_upper_committable
    where: p
    description: every dispatch row is bounded above
```

```math
\mathrm{p}^{\mathrm{upper,fixed}}_{t,g} \text{ has a row} \vee \mathrm{p}^{\mathrm{upper,extendable}}_{t,g} \text{ has a row} \vee \mathrm{p}^{\mathrm{upper,committable}}_{t,g} \text{ has a row} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, p_{t,g} \text{ exists}
```

At load, mathspec decides an assumption whose every test is a bare variable
or constraint name. It reads each variable as existing where its `where:`
holds, and each constraint as having a row where its `where:` holds. If
`p_upper_committable` had `where: committable AND NOT extendable`, no
constraint would bound a unit that is both extendable and committable, and
mathspec prints:

```text
Assumption 'dispatch_has_an_upper_bound': the `where:` conditions of the entries it names leave a gap where extendable is true, committable is true. There its `where:` holds and its `holds:` does not, so data with a row there fails it. Add a constraint whose `where:` holds there, or widen the `where:` of an entry that `holds:` names.
```

mathspec suggests two rewrites: a constraint for the missing case, or a wider
`where:` on a constraint that `holds:` names.

A constraint row can still be absent where its `where:` holds, for example
where a term outside a `sum` is [absent](absence.md#how-absence-travels). So
the tool that attaches the data also checks the assumption, row by row.
For the same reason, the `where:` of a constraint shows a gap only in
`holds:`, outside any `NOT`. In the assumption's own `where:`, or under a
`NOT`, it would claim rows that the data can leave out. mathspec leaves the
whole check to the tool in five cases:

- the assumption also compares a value, such as `where: "p AND p_nom > 0"`
- it names a constraint in its `where:`, or under a `NOT`
- it names an entry that another file declares under
  [`given:`](parameters-variables-constraints.md#given)
- it reads two variables whose `where:` name each other
- it contains a condition that mathspec cannot split into regions without
  data, as [refused cases](named.md#refused-cases) lists, or more than 8192
  regions

Only an assumption may name a constraint in a condition. In the `where:` of a
variable or in a named condition, mathspec refuses the name, as for
`where: p_upper_committable` on `p`:

```text
Variable 'p': 'p_upper_committable' is a constraint, and only an assumption's `holds:` or `where:` may test whether it has a row, by its bare name. Test the `where:` of 'p_upper_committable' here instead.
```

mathspec suggests the constraint's own `where:` as the rewrite.

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

The solver decides the value of a variable, and a tool checks an assumption
before any solve. So mathspec refuses a variable compared with a value or
inside arithmetic. For `holds: "p > 0"`, mathspec prints:

```text
Assumption 'sound': 'p' is a variable. The solver decides its value, so an assumption tests only whether it has a row: write its bare name, or state the bound as a constraint.
```

mathspec suggests two rewrites: the bare name `p`, which tests whether the
variable exists ([rows of the model](#rows-of-the-model)), or a constraint.

mathspec also
[refuses](parameters-variables-constraints.md#constraints) a constraint with
no variable on either side, and suggests an `assumptions:` entry as the
rewrite.

## What a curve assumes

A [`piecewise:`](piecewise.md) entry named `curve` adds assumptions of its
own. [`to_spec`](../api.md#mathspec.to_spec) derives them from the `method:` of the entry, its `where:` and
the signs on its links. Each one has the `where:` of the entry, so a tool
checks it only where a curve runs. The typesetter prints them under the same
_Assumptions_ heading as the assumptions you write, and
[`spec.expand()`](../spec.md#mathspec.spec.Spec.expand) writes them out as
`assumptions:` entries with these names:

| Entry                   | Added for                                                                 | What it requires                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `curve_complete`        | an entry with a link that does not walk a relation                        | every values parameter of such a link has a row at every breakpoint the curve runs through                       |
| `curve_<link>_complete` | a [link that walks a relation](piecewise.md#a-link-that-walks-a-relation) | the values parameter of the link has a row at every breakpoint, at every row of the link                         |
| `curve_increasing`      | `convex`, `lp`                                                            | the breakpoints of the pinned link, or of the first link where both are pinned, strictly increase along `along`  |
| `curve_curvature`       | `convex`, `lp`                                                            | with a `>=` link the curve is convex, with a `<=` link concave, and with both links pinned it bends one way only |
| `curve_breakpoints`     | `lp`                                                                      | each curve has at least two breakpoints                                                                          |
| `curve_contiguous`      | a [`where:` over `along`](piecewise.md#curves-of-unequal-length)          | the marked breakpoints form one consecutive run of at least one                                                  |

For an [`lp`](piecewise.md#method) entry named `cost_curve`, with its second link signed `>=`, the
typesetter prints the first three added assumptions as:

```math
\mathrm{bp\_x}_{b,g} \text{ is defined} \wedge \mathrm{bp\_y}_{b,g} \text{ is defined} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G}
```

```math
\mathrm{bp\_x}_{b \boxminus_{0} 1,g} < \mathrm{bp\_x}_{b,g} \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{pos}(b) > 0
```

```math
\left( \mathrm{bp\_y}_{b,g} - \mathrm{bp\_y}_{b \boxminus_{0} 1,g} \right) \cdot \left( \mathrm{bp\_x}_{b \boxplus_{0} 1,g} - \mathrm{bp\_x}_{b,g} \right) \le \left( \mathrm{bp\_y}_{b \boxplus_{0} 1,g} - \mathrm{bp\_y}_{b,g} \right) \cdot \left( \mathrm{bp\_x}_{b,g} - \mathrm{bp\_x}_{b \boxminus_{0} 1,g} \right) \qquad \forall\, b \in \mathcal{B},\ g \in \mathcal{G} \,:\, \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1
```

The first requires a row in both tables at every breakpoint. The second
requires that `bp_x` rise from one breakpoint to the next. The third requires
that each segment be no steeper than the one after it, which makes the curve convex.

!!! info "See also"

    - [Reading a spec and its program](../reading.md#what-the-data-has-to-satisfy)
      for how a tool runs these checks.
    - [Piecewise curves and SOS](piecewise.md) for the entries that add
      assumptions of their own.
