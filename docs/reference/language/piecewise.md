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
  `chp_lam`, and its rows include `chp_convexity` and `chp_power`.
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

A `piecewise` entry states one curve through breakpoints for each coordinate
of its `dims:`. The breakpoints are the corner values that the expressions
take together. In the spec below, each generator has a table of power, fuel
and heat at each breakpoint `bp`, and straight lines join the breakpoints:

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
    along: bp
    dims: [generator]
    links:
      power: [power, power_bp]
      fuel: [fuel, fuel_bp]
      heat: [heat, heat_bp]
objective:
  sense: minimize
  expression: sum(fuel, over=generator)
```

```math
\left( \mathit{power}_{g},\ \mathit{fuel}_{g},\ \mathit{heat}_{g} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b},\ \mathrm{heat}^{\mathrm{bp}}_{g,b}) \qquad \forall\, g \in \mathcal{G}
```

The [typesetter](../typeset.md) prints the entry as one membership: for each
generator, power, fuel and heat lie together on the curve through the three
breakpoint tables.

Under the default `method`, the expansion writes a weight in [0, 1] per
breakpoint and a row that makes the weights sum to one. It also writes one row
per link, which ties the expression of the link to the weighted breakpoints.
`incremental` and `lp` write other rows ([`method`](#method)).

Each item under `links:` is a **link**: a name and a list of two or three
parts. The name of a link sets the name of its row, `<entry>_<link>`, so the
expansion writes the link `power` of `chp` as the row `chp_power`.

| Part of a link | What it is                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _expression_   | Any linear expression plus a constant ([affine](expressions.md#where-a-product-of-two-variables-is-allowed)). The simplest one is a bare variable name. |
| _values_       | A parameter over the `along` dimension. Its other dimensions are dimensions of the row of the link.                                                     |
| _sign_         | `<=`, `>=` or `==`. Without a sign, the link is `==` ([signs](#signs)).                                                                                 |

A link that [walks a relation](#a-link-that-walks-a-relation) is a mapping
instead, with the keys `expression`, `values`, `by` and, where it has one,
`sign`.

| Key        | Required | Default     | What it does                                                                                                                                        |
| ---------- | -------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `along`    | yes      |             | Sets the breakpoint dimension.                                                                                                                      |
| `dims`     | yes      |             | Sets the dimensions of the curves. The entry states one curve per coordinate ([`dims`](#dims)).                                                     |
| `links`    | yes      |             | Lists the links by name: two or more, or one link that walks a relation.                                                                            |
| `where`    | no       | `null`      | Sets which curves exist, and how far each one runs ([`where`](#where)).                                                                             |
| `method`   | no       | `adjacency` | Sets the rows that the expansion writes for each curve ([`method`](#method)).                                                                       |
| `activity` | no       | `null`      | Sets the binary variable that switches the curve on and off, by its name or as `at(<variable>, by=<relation>[<column>])` ([`activity`](#activity)). |

The breakpoints follow the order of the `along` dimension, so that dimension
must be declared [ordered](dimensions.md#ordered). Without `ordered: true`,
mathspec refuses the file at load:

```text
piecewise 'chp': along: bp reads the order of 'bp', which is not declared ordered, so the order would come from the row order of the data. Declare 'bp: {ordered: true}' under dimensions:.
```

mathspec suggests the rewrite: `ordered: true` on `bp`.

A link must not take the name of a row or variable that the expansion adds
for the entry, such as `convexity` or `lam`. For a link named `lam`, mathspec prints:

```text
piecewise 'chp': link 'lam' has the row 'chp_lam', which the expansion of the entry already writes. Rename the link.
```

mathspec suggests the rewrite: another name for the link.

When the expansions of two entries write a row of the same name, mathspec
refuses the file and names both entries.

!!! info "See also"

    - [what a curve assumes](assumptions.md#what-a-curve-assumes), for the
      checks that an entry adds on its breakpoint data.

### `dims`

`dims:` sets the dimensions of the curves, in the order written. The entry
states one curve, with its own weights, at each coordinate of `dims:`. Every
curve runs along `along`, so `dims:` must not include that dimension.

The row of a link is over `dims:`, or over the dimensions of its
[walk](#a-link-that-walks-a-relation). The expression of a link must be over
exactly the dimensions of its row. With `power` and `fuel` over
`[snapshot, generator]` and an entry with `dims: [generator]`, mathspec
prints:

```text
piecewise 'fuel_use': link 'power' expression is over ['snapshot'], and its row ['generator'] is not, so every coordinate of ['snapshot'] would share one curve. Add ['snapshot'] to dims:, sum it out, or look the curve up through a relation with by: <relation>[<column>].
```

mathspec suggests three rewrites: `snapshot` in `dims:`, a sum over
`snapshot`, or a walk through a relation. mathspec also refuses an expression
that is not over a dimension of its row. One value of the expression would
then lie on several curves at once.

A quantity can vary along a dimension that the breakpoints do not, such as
the power of a generator at each snapshot. That dimension goes in `dims:`:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  power_bp: { dims: [generator, bp] }
  fuel_bp: { dims: [generator, bp] }
variables:
  power: { dims: [snapshot, generator], bounds: { lower: 0 } }
  fuel: { dims: [snapshot, generator], bounds: { lower: 0 } }
piecewise:
  fuel_use:
    along: bp
    dims: [snapshot, generator]
    links:
      power: [power, power_bp]
      fuel: [fuel, fuel_bp]
objective:
  sense: minimize
  expression: sum(fuel)
```

```math
\left( \mathit{power}_{t,g},\ \mathit{fuel}_{t,g} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b}) \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

The entry states one curve per snapshot and generator. The breakpoint tables
are over `[generator, bp]`, so each generator has one curve shape, and each
snapshot has its own point on it.

### Signs

A link with no sign, or with `==`, is pinned to the curve: its expression
equals the weighted breakpoints. A link with `<=` or `>=` is bounded by the
curve instead. In the first spec on this page, with the entry `fuel_cap` below
in place of `chp`, the fuel use may lie anywhere below the curve:

```yaml
piecewise:
  fuel_cap:
    along: bp
    dims: [generator]
    links:
      power: [power, power_bp]
      fuel: [fuel, fuel_bp, "<="]
```

```math
\mathit{fuel}_{g} \le \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b})(\mathit{power}_{g}) \qquad \forall\, g \in \mathcal{G}
```

The typesetter now prints the curve as a function of `power`, with `fuel`
bounded above by it.

Any number of links may have a sign, but at least one link must be pinned.
The pinned link sets the point on the curve at which the other links are
read. With a sign on every link, mathspec refuses the file at load:

```text
piecewise.chp.links: every link has a '<=' or '>=' sign, so nothing pins the point the curve is read at. Write '==' on at least one link.
```

With a sign on two of three links, the entry below loads in place of `chp`:

```yaml
piecewise:
  chp:
    along: bp
    dims: [generator]
    links:
      power: [power, power_bp]
      fuel: [fuel, fuel_bp, ">="]
      heat: [heat, heat_bp, "<="]
```

```math
\left( \mathit{power}_{g},\ \mathit{fuel}_{g},\ \mathit{heat}_{g} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b},\ \mathrm{heat}^{\mathrm{bp}}_{g,b}) + \{0\} \times \mathbb{R}_{\ge 0} \times \mathbb{R}_{\le 0} \qquad \forall\, g \in \mathcal{G}
```

The typesetter prints the point on the curve plus a cone. The `{0}` keeps the
pinned `power` on the curve, `fuel` may lie any amount above the curve, and
`heat` any amount below it.

`convex` and `lp` take exactly two links ([`method`](#method)). At load,
mathspec refuses a sign other than `<=`, `>=` and `==`.

### A link that walks a relation

On a link with `by: relation[column]`, mathspec looks the weights of the
curve up through a [relation](relations.md#lookups), as
[`at(x, by=relation[column])`](operators.md#at) looks up the value of `x`. The
row of the link is over `dims:`, with the dimension of `column` replaced by
the key columns of the relation. Each row lies on the curve of the coordinate
it maps to, so the number of rows is known only when the data is attached:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  converter: { dtype: str }
  flow: { dtype: str }
  bp: { dtype: int, ordered: true }
relations:
  converter_of: { key: flow, values: converter }
parameters:
  bp_rate: { dims: [flow, bp] }
  price: { dims: [flow] }
variables:
  rate: { dims: [flow, snapshot], bounds: { lower: 0 } }
piecewise:
  operating_point:
    along: bp
    dims: [converter, snapshot]
    links:
      rate: { expression: rate, values: bp_rate, by: "converter_of[converter]" }
objective:
  sense: minimize
  expression: sum(price * rate)
```

```math
\left( \mathit{rate}_{f,t} \right)_{f \in \mathcal{F} \,:\, \mathrm{converter\_of}(f) = c} \in \mathrm{pwl}_{b \in \mathcal{B}}(\left( \mathrm{bp\_rate}_{f,b} \right)_{f \in \mathcal{F} \,:\, \mathrm{converter\_of}(f) = c}) \qquad \forall\, c \in \mathcal{C},\ t \in \mathcal{T}
```

For each converter and snapshot, the rates of all flows of the converter lie
on one curve. A converter with two flows and a converter with five share the
entry, and a sixth flow is a row in `converter_of`.

The expansion writes the row `operating_point_rate` over `[flow, snapshot]`.
Each flow uses the weights of its converter:

```math
\mathit{rate}_{f,t} = \sum_{b \in \mathcal{B}} \mathit{operating\_point\_lam}_{\mathrm{converter\_of}(f),t,b} \cdot \mathrm{bp\_rate}_{f,b} \qquad \forall\, f \in \mathcal{F},\ t \in \mathcal{T}
```

These rules apply to a walked link:

- One walked link is enough for an entry. The expansion writes a row for each
  flow of a converter, and those rows share the weights.
- The values parameter is over the row of the link, so `bp_rate` is per flow,
  not per converter.
- `column` is over a dimension of `dims:`. The walk adds the key columns of the
  relation that are over dimensions outside `dims:` and `along`, and joins on
  the others.
- mathspec holds a walk to every rule of [`at`](relations.md#lookups), and quotes
  the link in the refusal.
- If the relation declares [`missing: absent`](relations.md#missing), the
  expansion adds `converter_of` to the `where:` of the row, so a flow with no
  converter has no row.
- `method: convex` and `method: lp` take no walked link, and the other methods
  do.

### `where`

`where:` is a [condition](expressions.md#conditions) that sets which curves
exist and, over `along`, how far each one runs. Over `dims:` alone, it sets
which coordinates have a curve:

```yaml
dimensions:
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  bp_x: { dims: [generator, bp] }
  bp_y: { dims: [generator, bp] }
  has_curve: { dims: [generator], dtype: bool }
variables:
  p: { dims: [generator], bounds: { lower: 0 } }
  op_cost: { dims: [generator] }
constraints:
  enough:
    dims: []
    expression: sum(p, over=generator) >= 1
piecewise:
  cost_curve:
    along: bp
    dims: [generator]
    where: has_curve
    links:
      p: [p, bp_x]
      op_cost: [op_cost, bp_y]
objective:
  sense: minimize
  expression: sum(op_cost, over=generator)
```

```math
\left( p_{g},\ \mathit{op\_cost}_{g} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{bp\_x}_{g,b},\ \mathrm{bp\_y}_{g,b}) \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{has\_curve}_{g}
```

Only a generator where `has_curve` is true has a curve. For any other
generator, the expansion writes no weights and no rows. There `p` and
`op_cost` are free, and `bp_x` and `bp_y` need no rows.

A coordinate outside the `where:` has no curve. A coordinate with an
[`activity:`](#activity) gate has a curve that the solver may switch off.
mathspec refuses a `where:` over a dimension that is neither in `dims:` nor
`along`, because a condition cannot add coordinates.

On the row of a walked link, the expansion looks the `where:` up through the
relation of the link. In the
[walk example](#a-link-that-walks-a-relation), with a boolean parameter
`has_curve` over `[converter]` and `where: has_curve`, the expansion writes the row
`operating_point_rate` with
`where: at(has_curve, by=converter_of[converter])`:

```math
\mathit{rate}_{f,t} = \sum_{b \in \mathcal{B}} \mathit{operating\_point\_lam}_{\mathrm{converter\_of}(f),t,b} \cdot \mathrm{bp\_rate}_{f,b} \qquad \forall\, f \in \mathcal{F},\ t \in \mathcal{T} \,:\, \mathrm{has\_curve}_{\mathrm{converter\_of}(f)}
```

The row exists at every flow of a converter with a curve. A flow of a
converter with no curve needs no row in `bp_rate`.

mathspec refuses a `where:` over a dimension that a walk adds, because a curve
exists per coordinate of `dims:`. With a boolean parameter `active` over
`[flow]` as the `where:`, mathspec prints:

```text
piecewise 'operating_point': where 'active' tests ['flow'], which link 'rate' adds through its relation. A where: sets which curves exist, one per coordinate of dims: ['converter', 'snapshot'], and only the rows of the link are over ['flow']. Test ['converter', 'snapshot'] in the where:, or declare a where: over ['flow'] on the variable of the link, so that its rows are absent.
```

mathspec suggests two rewrites: a condition over `dims:`, or a `where:` on
`rate`.

#### Curves of unequal length

A `where:` over `along` sets how far each curve runs. Without one, every curve
runs over every breakpoint, and a missing row does not shorten a curve. With a
values parameter of the entry as the `where:`, each curve runs as far as that
parameter has rows:

```yaml
dimensions:
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  bp_x: { dims: [generator, bp], missing: 0 }
  bp_y: { dims: [generator, bp], missing: 0 }
variables:
  p: { dims: [generator], bounds: { lower: 0 } }
  op_cost: { dims: [generator] }
constraints:
  enough:
    dims: []
    expression: sum(p, over=generator) >= 1
piecewise:
  cost_curve:
    along: bp
    dims: [generator]
    where: bp_x
    links:
      p: [p, bp_x]
      op_cost: [op_cost, bp_y]
objective:
  sense: minimize
  expression: sum(op_cost, over=generator)
```

```math
\left( p_{g},\ \mathit{op\_cost}_{g} \right) \in \mathrm{pwl}_{b \in \mathcal{B} \,:\, \mathrm{bp\_x}_{g,b} \text{ is defined}}(\mathrm{bp\_x}_{g,b},\ \mathrm{bp\_y}_{g,b}) \qquad \forall\, g \in \mathcal{G}
```

<figure class="diagram">
--8<-- "docs/static/piecewise-where.svg"
</figure>

The curve of each generator now runs over the breakpoints where `bp_x` is
defined, and no further. The file declares
[`missing: 0`](#missing-breakpoints) on each values parameter, because its
table stops where the curve stops.

A row over `dims:` alone, such as the row that makes the weights sum to one,
has no `along` dimension. The expansion writes that row with
`where: count(bp_x, over=bp) > 0`, so a curve exists where the `where:` admits
at least one breakpoint.

With data attached, the software that checks the `cost_curve_complete`
[assumption](assumptions.md#what-a-curve-assumes) (a
[tool](../glossary.md#tool)) still refuses a row missing from `bp_y` where
`bp_x` has one.

Where the length of each curve is its own data, the `where:` may instead be a
boolean parameter over `dims:` and `along`. The breakpoints that it marks must
form one consecutive run, which may start anywhere along the dimension. A
tool checks this against the `<entry>_contiguous` assumption.

A condition over `dims:` and one over `along` combine:
`where: has_curve AND bp_x` sets which generators have a curve and how far
each one runs.

### Missing breakpoints

A parameter that an entry uses takes a
[`missing:`](parameters-variables-constraints.md#missing) value like any other
parameter, and has the same value inside and outside the curve.

A values parameter defaults to `refused`. Under a `where:` over `along`,
a values parameter must declare a `missing:` other than `refused`. The curve
stops where the rows of `bp_x` stop, so the table has no rows past that point,
and `refused` requires every row. With `missing: refused` on `bp_y`, mathspec
refuses the file at load:

```text
parameter 'bp_y' is refused where a row is missing, and it is a values parameter of piecewise 'cost_curve' under where: 'bp_x', which sets where each curve ends. Declare missing: absent, or a value of its dtype.
```

mathspec lists the `missing:` values that it accepts: `absent`, or a value of
the dtype.

Under `absent` and under a value, the curve is the same, because the
expansion uses a table only where the curve runs. With data attached, a tool
that checks `<entry>_complete` still refuses a missing row there. The two
differ where an expression outside the curve uses the table:

<figure class="diagram">
--8<-- "docs/static/piecewise-missing.svg"
</figure>

Under `missing: 0`, the missing row of `bp_y` is `0`. Under `absent`, `bp_y`
has no row there, so a term that uses it is absent.

### `method`

`method` sets the rows that the expansion writes for each curve.

| `method`                | What it adds                                                                | What it states                                                       |
| ----------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `adjacency` _(default)_ | an [`sos:`](#sos) entry over the weights, written out as binaries           | the curve exactly, through binaries                                  |
| `sos2`                  | an [`sos:`](#sos) entry over the weights, left as a set                     | the curve, for a solver that branches on the set itself              |
| `incremental`           | no weights: a filled fraction and a binary per segment, filled in order     | the curve exactly, through binaries                                  |
| `convex`                | nothing                                                                     | the curve's smallest convex region (its convex hull), with no binary |
| `lp`                    | no weights at all: one row per segment, plus two rows that bound the domain | the curve as its own segment lines                                   |

`convex` takes exactly two links, no walked link and no `activity:`. Its hull
equals the curve only when the curve has the right shape, and an
[assumption](assumptions.md#what-a-curve-assumes) states that shape.

`lp` needs **exactly two links**, **exactly one** of them with a `<=` or `>=`
sign, no walked link and no `activity:`:

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
    along: bp
    dims: [generator]
    method: lp
    links:
      p: [p, bp_x]
      op_cost: [op_cost, bp_y, ">="]
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

Under `incremental`, the expansion writes the rows that the modelling library
[linopy](https://linopy.readthedocs.io) writes for a curve that a gate switches
or that is not convex. Each segment has the label of its lower breakpoint. For
an entry `e` along `bp`:

| Written out        | What it states                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| `e_delta`          | a variable in [0, 1] per segment: the fraction of the segment that is filled                                |
| `e_order`          | a binary variable per segment                                                                               |
| `e_delta_bound`    | `e_delta <= e_order`: only a segment whose binary is 1 fills                                                |
| `e_fill_order`     | `e_delta <= shift(e_delta, along=bp, offset=1)`: a segment fills no further than the one before it          |
| `e_binary_order`   | `e_order <= shift(e_delta, along=bp, offset=1)`: a binary is 1 only when the segment before it is full      |
| `e_active_bound`   | `e_delta <=` the gate, written only with `activity:`                                                        |
| `e_<link>`         | the expression of the link against its value at the first breakpoint, times the gate, plus each filled rise |
| `e_<link>_ungated` | the same row without the gate, written only where the gate is absent                                        |

`incremental` takes two or more links, a walked link and `activity:`. The
[incremental example](../../examples/piecewise_incremental.md) is a spec with
curves of unequal length and a gate that only some generators have.

### `activity`

`activity:` sets the binary on-off switch of the curve (the gate). The
weights then sum to the gate instead of to one, and under `incremental` the
gate bounds each filled fraction. Where the gate is `0`, the curve is switched
off. The gate is an ordinary variable entry, and it may have a
[`where:`](absence.md#where):

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
    along: bp
    dims: [snapshot, generator]
    links:
      power: [power, power_bp]
      fuel: [fuel, fuel_bp]
    activity: running
objective:
  sense: minimize
  expression: sum(fuel)
```

```math
\left( \mathit{power}_{t,g},\ \mathit{fuel}_{t,g} \right) \in \begin{cases} \mathit{running}_{t,g} & \text{if } \mathrm{committable}_{g} \\ 1 & \text{otherwise} \end{cases} \cdot \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b}) \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

<figure class="diagram">
--8<-- "docs/static/piecewise-activity.svg"
</figure>

The curve is scaled by `running` where `committable` is true, and by 1
elsewhere. With data for gas and wind, at each snapshot gas has the scale
`running` and wind has the scale `1`.

Where the gate is [absent](absence.md), the curve is ungated, as under
`missing: 1`. With `missing: 0` on the gate, the gate is `0` outside its
`where:`, so the curve is switched off there. The typesetter then prints the
curve scaled by `running` alone.

The gate must have no dimension that `dims:` does not include, unless it walks
a relation. A gate over fewer dimensions switches every curve
that it covers, so a gate over `[generator]` switches the curve of a generator
at every snapshot.

#### A gate that walks a relation

On a gate written as
[`at(<variable>, by=<relation>[<column>])`](operators.md#at), mathspec looks
the variable up through a [relation](relations.md#lookups), as `at` looks up
any value. Here `running` is per unit, and the status of its unit switches
the curve of each generator:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  unit: { dtype: str }
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
relations:
  unit_of: { key: generator, values: unit, missing: absent }
parameters:
  power_bp: { dims: [generator, bp] }
  fuel_bp: { dims: [generator, bp] }
variables:
  power: { dims: [snapshot, generator], bounds: { lower: 0 } }
  fuel: { dims: [snapshot, generator], bounds: { lower: 0 } }
  running: { dims: [snapshot, unit], domain: binary }
piecewise:
  fuel_use:
    along: bp
    dims: [snapshot, generator]
    links:
      power: [power, power_bp]
      fuel: [fuel, fuel_bp]
    activity: at(running, by=unit_of[unit])
objective:
  sense: minimize
  expression: sum(fuel)
```

```math
\left( \mathit{power}_{t,g},\ \mathit{fuel}_{t,g} \right) \in \begin{cases} \mathit{running}_{t,\mathrm{unit\_of}(g)} & \text{if } \mathit{running}_{t,\mathrm{unit\_of}(g)} \text{ exists} \\ 1 & \text{otherwise} \end{cases} \cdot \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{power}^{\mathrm{bp}}_{g,b},\ \mathrm{fuel}^{\mathrm{bp}}_{g,b}) \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

The weights of each curve sum to `at(running, by=unit_of[unit])`. Because
`unit_of` declares [`missing: absent`](relations.md#missing), a generator may
have no row in it. That generator has no gate, so its curve is ungated. With
`missing: 0` on the gate, the gate is `0` outside its `where:`, so the curve
is switched off there. Only a generator with no row in `unit_of` then stays
ungated.

After the lookup, the gate must be over dimensions of `dims:` only. With
`running` over `[snapshot, unit, period]`, mathspec refuses the file at load:

```text
piecewise 'fuel_use': activity 'running' is over ['period'] after the lookup, which is not in dims: ['snapshot', 'generator']. The gate switches the curve of one coordinate of dims:. Look it up through a relation that leaves it over dims:, or add ['period'] to dims:.
```

!!! info "See also"

    - [See what a piecewise curve or an SOS expands to](../../howto/see-an-expansion.md)
      for a spec printed before and after its expansion.
    - [Formulations written out](../reading.md#formulations-written-out) for the
      program of an expansion.
