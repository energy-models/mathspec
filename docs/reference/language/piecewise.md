<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Piecewise curves and SOS

This page describes the two kinds of entry that expand into ordinary entries
([**formulations**](../glossary.md#formulation)). They expand before the tool
that builds the model (an [engine](../glossary.md#tool)) reads the spec. An
`sos:` entry lets only one
member of a variable, or only two neighbouring members, be non-zero. A
`piecewise:` entry ties two or more quantities to one piecewise-linear curve.

[`Spec.expand()`](../spec.md#mathspec.spec.Spec.expand) replaces each
formulation entry with the variables, constraints and assumptions it states,
and returns a new `Spec`. `expand('sos')` writes out only the `sos:` entries.
`expand('piecewise')` writes out the `piecewise:` entries, with the sets that
an `adjacency` curve adds. The expansion has three properties:

- Every name it writes starts with the name of the entry. The curve `chp` has
  one number per corner point (a [breakpoint](../glossary.md#breakpoint)) in
  `chp_lam`, and its rows include `chp_convexity` and `chp_link0`.
- No formulation writes a parameter. The same data attaches to a spec and to
  its expansion, and has the same meaning in both.
- The [assumptions of a curve](assumptions.md#what-a-curve-assumes) become
  `assumptions:` entries.

## `sos`

An `sos` entry states a set with few non-zero members (a
**special ordered set**, or SOS). It limits how many members of a variable
along one dimension are non-zero at once. In the spec below, each site builds
at most one size:

```yaml
dimensions:
  site: { dtype: str }
  size: { dtype: str }
parameters:
  cost: { dims: [site, size] }
  max_build: { dims: [size] }
variables:
  build:
    dims: [site, size]
    bounds: { lower: 0, upper: max_build }
constraints:
  enough:
    dims: []
    expression: sum(build) >= 10
sos:
  pick_one_size:
    variable: build
    along: size
    type: 1
objective:
  sense: minimize
  expression: sum(cost * build)
```

```math
\left( \mathit{build}_{s,i} \right)_{i \in \mathcal{I}} \in \mathrm{SOS}1 \qquad \forall\, s \in \mathcal{S}
```

The entry states one set per site, and each set runs along `size`.

| Key        | What it does                                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `variable` | Sets the variable that the set is over.                                                                                              |
| `along`    | Sets the dimension the set runs along. The entry states one set per [coordinate](../glossary.md#coordinate) of the other dimensions. |
| `type`     | `1`: at most one member is non-zero. `2`: at most two members are non-zero, and they are consecutive.                                |

A set is over **one** variable, and a variable has **one** set. At load, mathspec
refuses a second entry that lists the same variable:

```text
Sos 'again': variable 'build' already carries the set declared by 'pick_one_size'. Declare a second variable, or write the other restriction as a constraint.
```

mathspec suggests two rewrites: a second variable, or the other restriction
written as a constraint.

A member that the `where:` of the variable leaves out
([absent](absence.md#where)) is not in the set. The members follow the order of the `along` dimension. For `type: 2`, that
dimension must be declared [ordered](dimensions.md#ordered), because
"consecutive" depends on its order.

### What a set is written out as

`spec.expand('sos')` states the set as binary variables: one per member for
`type: 1`, and one per segment between two members for `type: 2`. A member
that the binaries do not admit is held at zero, from above and from below. For
a set `s` over the variable `x` along `d`, let `admitted` be `s_seg` for
`type: 1`, and `s_seg + shift(s_seg, along=d, offset=1, edge=0)` for `type: 2`:

| Written out                                        | What it states                                                         |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| `s_seg`                                            | a binary variable over the dimensions of `x`, with the `where:` of `x` |
| `s_pick`                                           | `sum(s_seg, over=d) <= 1`: at most one is picked                       |
| `s_nonzero` (`type: 1`), `s_adjacency` (`type: 2`) | `x <= upper * admitted`                                                |
| the same name plus `_below`                        | `x >= lower * admitted`, written only where `lower` is not `0`         |

Each command below prints the spec above with its set written out:

=== "Command line"

    ```bash
    python -m mathspec markdown spec.yaml --expand
    ```

=== "Python"

    ```python
    import mathspec as ms

    print(ms.to_markdown(ms.to_spec('spec.yaml').expand('sos')))
    ```

The output of each command contains these two rows:

```math
\sum_{i \in \mathcal{I}} \mathit{pick\_one\_size\_seg}_{s,i} \le 1 \qquad \forall\, s \in \mathcal{S}
```

```math
\mathit{build}_{s,i} \le \mathrm{max\_build}_{i} \cdot \mathit{pick\_one\_size\_seg}_{s,i} \qquad \forall\, s \in \mathcal{S},\ i \in \mathcal{I}
```

The lower bound of `build` is `0`, so the expansion writes no
`pick_one_size_nonzero_below` row.

`upper` and `lower` are the `bounds:` of the member, each a number or a parameter, and for a binary member they are `1` and `0`. mathspec refuses a member
with no `bounds.lower`, or with no `bounds.upper` and no `domain: binary`, and with `bounds: { upper: max_build }` on `build` it prints:

```text
Sos 'pick_one_size': variable 'build' has no lower bound, and the set expands to rows that hold an unpicked member at zero from below as well as above. Declare bounds.lower, as a number or a parameter.
```

The `_below` row of the expansion needs a lower bound, so that an unpicked
`build` is zero.

mathspec also refuses a name that the expansion writes when the file already declares it, such as a variable `pick_one_size_seg`:

```text
Sos 'pick_one_size': its expansion writes variable 'pick_one_size_seg', which this file already declares under 'variables:'. Rename one of them.
```

`pick_one_size_seg` is the name of the binary variable that the expansion
writes.

!!! info "See also"

    - [the command line](../cli.md#latex-markdown-and-typst), for the
      `--expand` flag.

## `piecewise`

A `piecewise` entry states a curve through breakpoints, which are the corner
values that the expressions take together. In the spec below, each generator
has a table of power, fuel and heat at each breakpoint `bp`, and straight lines
join the breakpoints:

```yaml
dimensions:
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  power_bp: { dims: [generator, bp] }
  fuel_bp: { dims: [generator, bp] }
  heat_bp: { dims: [generator, bp] }
variables:
  power: { dims: [generator], bounds: { lower: 0 } }
  fuel: { dims: [generator], bounds: { lower: 0 } }
  heat: { dims: [generator], bounds: { lower: 0 } }
piecewise:
  chp:
    over: bp
    links:
      - [power, power_bp]
      - [fuel, fuel_bp]
      - [heat, heat_bp]
objective:
  sense: minimize
  expression: sum(fuel, over=generator)
```

```math
\left( \mathit{power}_{g},\ \mathit{fuel}_{g},\ \mathit{heat}_{g} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b},\ \mathrm{heat}^{\mathrm{bp}}_{g,b}) \qquad \forall\, g \in \mathcal{G}
```

The [typesetter](../typeset.md) prints the entry as one membership. For each generator, the
triple of power, fuel and heat lies on the curve that the three breakpoint
tables draw over `bp`.

Except under `method: lp`, an entry states a weight in [0, 1] per breakpoint.
It adds a row that makes the weights sum to one. It also adds a row per link
that ties the expression of the link to the weighted breakpoints.

Each item under `links:` is a **link**, which is a list of two or three parts:

| Part of a link | What it is                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _expression_   | Any linear expression plus a constant ([affine](expressions.md#where-a-product-of-two-variables-is-allowed)). The simplest one is a bare variable name. |
| _values_       | A parameter over the `over` dimension, plus any dimensions over which the link expressions are indexed.                                                 |
| _sign_         | `<=`, `>=` or `==`. Without a sign, the link is `==`.                                                                                                   |

| Key        | Required | Default     | What it does                                                                                      |
| ---------- | -------- | ----------- | ------------------------------------------------------------------------------------------------- |
| `over`     | yes      |             | Sets the breakpoint dimension.                                                                    |
| `links`    | yes      |             | Lists two or more links.                                                                          |
| `method`   | no       | `adjacency` | Sets how the weights are restricted: `adjacency`, `sos2`, `convex` or `lp` ([`method`](#method)). |
| `activity` | no       | `null`      | Sets a binary variable that switches the curve on and off ([`activity`](#activity)).              |
| `points`   | no       | `null`      | Where the curves differ in length, sets how far each curve runs ([`points`](#points)).            |

mathspec refuses a values parameter over a dimension over which no link
expression is indexed. Only an entry with exactly two links may sign a link with
`<=` or `>=`, and only one of its links. At load, mathspec refuses a sign other
than `<=`, `>=` and `==`.

The breakpoints follow the order of the
`over` dimension, so that dimension must be declared
[ordered](dimensions.md#ordered). Without `ordered: true`, mathspec refuses the
file at load:

```text
piecewise 'chp': over: bp reads the order of 'bp', which is not declared ordered, so the order would come from the row order of the data. Declare 'bp: {ordered: true}' under dimensions:.
```

`bp` is not ordered, so the row order of the data would set the order of the
breakpoints.

A link with `<=` or `>=` bounds its expression by the curve, and a link with
`==` pins it to the curve.
In the spec above, with the entry `fuel_cap` below in place of `chp`, the fuel use may lie
anywhere below the curve:

```yaml
piecewise:
  fuel_cap:
    over: bp
    links:
      - [power, power_bp]
      - [fuel, fuel_bp, "<="]
```

```math
\mathit{fuel}_{g} \le \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b})(\mathit{power}_{g}) \qquad \forall\, g \in \mathcal{G}
```

The typesetter now prints the curve as a function of `power`, with `fuel`
bounded above by it.

!!! info "See also"

    - [what a curve assumes](assumptions.md#what-a-curve-assumes), for the
      checks that an entry adds on its breakpoint data.

### `method`

`method` sets how the weights are restricted once they exist.

| `method`                | What it adds                                                                | What it states                                                       |
| ----------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `adjacency` _(default)_ | an [`sos:`](#sos) entry over the weights, written out as binaries           | the curve exactly, through binaries                                  |
| `sos2`                  | an [`sos:`](#sos) entry over the weights, left as a set                     | the curve, for a solver that branches on the set itself              |
| `convex`                | nothing                                                                     | the curve's smallest convex region (its convex hull), with no binary |
| `lp`                    | no weights at all: one row per segment, plus two rows that bound the domain | the curve as its own segment lines                                   |

`convex` takes exactly two links and no `activity:`. Its hull equals the curve
only when the curve has the right shape, and an
[assumption](assumptions.md#what-a-curve-assumes) states that shape.

`lp` needs **exactly two links**, **exactly one** of them with a `<=` or `>=` sign, and no
`activity:`:

```yaml
dimensions:
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  bp_x: { dims: [generator, bp] }
  bp_y: { dims: [generator, bp] }
variables:
  p: { dims: [generator], bounds: { lower: 0 } }
  op_cost: { dims: [generator] }
constraints:
  enough:
    dims: []
    expression: sum(p, over=generator) >= 1
piecewise:
  cost_curve:
    over: bp
    method: lp
    links:
      - [p, bp_x]
      - [op_cost, bp_y, ">="]
objective:
  sense: minimize
  expression: sum(op_cost, over=generator)
```

```math
\mathit{op\_cost}_{g} \ge \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{bp\_x}_{g,b},\ \mathrm{bp\_y}_{g,b})(p_{g}) \qquad \forall\, g \in \mathcal{G}
```

The cost of each generator is bounded below by the curve, and no weight
variable is stated.

Without the sign, mathspec refuses the file at load:

```text
piecewise.cost_curve: method: lp needs exactly one link with a '<=' or '>=' sign. Add the sign to one link.
```

mathspec suggests the rewrite: a sign on one of the two links.

### `activity`

`activity:` sets the binary on-off switch of the curve (the gate). The weights then sum to the gate instead of to one. Where the gate is
`0`, every weight is zero and the curve is switched off. The gate is an
ordinary variable entry, and it may have a [`where:`](absence.md#where):

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  power_bp: { dims: [generator, bp] }
  fuel_bp: { dims: [generator, bp] }
  committable: { dims: [generator], dtype: bool }
variables:
  power: { dims: [snapshot, generator], bounds: { lower: 0 } }
  fuel: { dims: [snapshot, generator], bounds: { lower: 0 } }
  running:
    dims: [snapshot, generator]
    domain: binary
    where: committable
piecewise:
  fuel_use:
    over: bp
    links:
      - [power, power_bp]
      - [fuel, fuel_bp]
    activity: running
objective:
  sense: minimize
  expression: sum(fuel)
```

```math
\left( \mathit{power}_{t,g},\ \mathit{fuel}_{t,g} \right) \in \begin{cases} \mathit{running}_{t,g} & \text{if } \mathrm{committable}_{g} \\ 1 & \text{otherwise} \end{cases} \cdot \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

<figure class="diagram">
--8<-- "docs/static/piecewise-activity.svg"
</figure>

The curve is scaled by `running` where `committable` is true, and by 1
elsewhere. With data for gas and wind, at each snapshot gas has the scale
`running` and wind has the scale `1`.

Where the gate is [absent](absence.md), the curve is ungated. With
`missing: neutral` on the gate, the absent gate is `0`, so the curve is
switched off there.

With `missing: neutral` on the gate, the typesetter prints the curve scaled by
`running` alone.

### `points`

With `points:` set to one of the values parameters of the entry, a curve has
fewer breakpoints than the dimension has. The curve then runs as far as that
parameter has rows:

```yaml
dimensions:
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  bp_x: { dims: [generator, bp], missing: neutral }
  bp_y: { dims: [generator, bp], missing: neutral }
variables:
  p: { dims: [generator], bounds: { lower: 0 } }
  op_cost: { dims: [generator] }
constraints:
  enough:
    dims: []
    expression: sum(p, over=generator) >= 1
piecewise:
  cost_curve:
    over: bp
    points: bp_x
    links:
      - [p, bp_x]
      - [op_cost, bp_y]
objective:
  sense: minimize
  expression: sum(op_cost, over=generator)
```

```math
\left( p_{g},\ \mathit{op\_cost}_{g} \right) \in \mathrm{pwl}_{b \in \mathcal{B} \,:\, \mathrm{bp\_x}_{g,b} \text{ is defined}}(\mathrm{bp\_x}_{g,b},\ \mathrm{bp\_y}_{g,b}) \qquad \forall\, g \in \mathcal{G}
```

<figure class="diagram">
--8<-- "docs/static/piecewise-points.svg"
</figure>

The curve of each generator now runs over the breakpoints where `bp_x` is
defined, and no further. Each values parameter declares
[`missing: neutral`](#missing-breakpoints), because its table stops where the
curve stops.

With data attached, the software that runs the `cost_curve_complete`
[assumption](assumptions.md#what-a-curve-assumes) ([a tool](../glossary.md#tool))
still refuses a row missing from `bp_y` where `bp_x` has one. Without
`points:`, the tool refuses every missing row under that assumption, so a
missing row makes no shorter curve.

Where the length of each curve is its own data, `points:` may instead be a
boolean parameter over the same dimensions. The curve then runs over the
breakpoints that the parameter marks. The marked breakpoints must form one
consecutive run, which may start anywhere along the dimension. The tool that
runs the `<entry>_contiguous` assumption checks that run.

### Missing breakpoints

A parameter that an entry uses takes a
[`missing:`](parameters-variables-constraints.md#missing) value like any other
parameter, and has the same value inside and outside the curve.

A values parameter of a curve with no `points:`, and a boolean `points:`
parameter, default to `refused`. A values parameter of a curve with
`points:` must declare a `missing:` other than `refused`. The curve stops where the rows of `bp_x`
stop, so the table has no rows past that point, and
`refused` requires every row. With `missing: refused` on `bp_y`, mathspec
refuses the file at load:

```text
parameter 'bp_y' is refused where a row is missing, and piecewise 'cost_curve' reads it under points: 'bp_x', which stops the curve where its rows stop. Declare missing: neutral, absent, or a value of its dtype.
```

mathspec lists the `missing:` values that it accepts: `neutral`, `absent`,
or a value of the dtype.

Under `neutral` and under `absent`, the curve is the same, because the curve
uses a table only inside the run of its breakpoints. With data attached, the
tool that runs `<entry>_complete` still refuses a missing row there. The two differ where an expression
outside the curve uses the table:

<figure class="diagram">
--8<-- "docs/static/piecewise-missing.svg"
</figure>

Under `neutral` the missing row of `bp_y` is `0`, and under `absent` `bp_y` has no row there, so a term that uses it is absent.

!!! info "See also"

    - [Write a piecewise curve out by hand](../../howto/curve-by-hand.md) for a
      curve whose number of links is data.
    - [See what a piecewise curve or an SOS expands to](../../howto/see-an-expansion.md)
      for a spec printed before and after its expansion.
    - [Formulations written out](../reading.md#formulations-written-out) for the
      program of an expansion.
