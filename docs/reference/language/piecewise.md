<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Piecewise curves and SOS

`piecewise:` states a curve through breakpoints. `sos:` states a family of
variables of which only one, or only two neighbours, may be non-zero. Both are
**formulations**: entries that expand into ordinary variables and constraints
before the model is built. [`spec.expand()`](#writing-a-formulation-out) writes
that expansion out.

## `piecewise`

A `piecewise` entry ties two or more expressions to one piecewise-linear curve,
which is given as breakpoints: the corner values each expression takes
together.

```yaml
piecewise:
  chp:
    over: bp # breakpoint dimension
    links:
      - [power, power_bp] # [expression, values-parameter]
      - [fuel, fuel_bp]
      - [heat, heat_bp]
    method: adjacency # how the weights are restricted — below
    activity: null # optional: a binary variable that the weights sum to

  # a two-link entry may bound one side instead of pinning it
  fuel_cap:
    over: bp
    links:
      - [power, power_bp]
      - [fuel, fuel_bp, "<="]
```

| Part of a link |                                                                                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| _expression_   | Any affine expression. The simplest is a bare variable name                                                                                  |
| _values_       | A parameter that carries the `over` dimension, plus any dimensions the link expressions carry. A dimension the links do not carry is refused |
| _sign_         | `<=` or `>=`. At most one per entry, and only in an entry with exactly two links. It bounds the link instead of pinning it                   |

| Key        |                                                                                          |                     |
| ---------- | ---------------------------------------------------------------------------------------- | ------------------- |
| `over`     | required. The breakpoint dimension                                                       |                     |
| `links`    | required. Two or more links                                                              |                     |
| `method`   | `adjacency`, `sos2`, `convex` or `lp`: how the weights are restricted ([below](#method)) | default `adjacency` |
| `activity` | a binary variable that gates the curve ([below](#activity))                              | default `null`      |
| `points`   | how far each curve runs, where the curves are not all the same length ([below](#points)) | default `null`      |

An entry states one weight per breakpoint in `[0, 1]`, a row making the weights
sum to 1, and a row per link tying its expression to the weighted breakpoints.
The breakpoint order is the order of `over`, which is an
[ordered](dimensions.md#order) dimension. What an entry assumes of
its numbers is on [what a curve assumes](assumptions.md#what-a-curve-assumes).

### `activity`

`activity:` names a binary variable, and the weights then sum to that variable
instead of to 1, so `0` pins the curve off.

The gate is an ordinary variable entry:

```yaml
variables:
  running:
    dims: [snapshot, generator]
    domain: binary
    where: committable # only some units have a commitment decision
```

Where the gate does not exist, the curve is ungated. To have no curve there
instead, put `missing: neutral` on the gate.

### `points`

A values parameter with a missing row does not build a shorter curve, because
the [assumption](assumptions.md#what-a-curve-assumes) of the entry refuses the
data. To give a curve fewer breakpoints than the dimension holds, set `points:`
to one of the values parameters of the entry, and the curve runs as far as that
parameter has rows:

```yaml
piecewise:
  cost_curve:
    over: bp
    points: bp_x # this curve runs as far as its own breakpoints do
    links:
      - [p, bp_x]
      - [op_cost, bp_y]
```

Each values parameter declares `missing: neutral`, because its table stops
where the curve stops ([missing breakpoints](#missing-breakpoints)). A row
missing from `bp_y` where `bp_x` has one is still refused. Where the length is
its own data, name a boolean parameter instead, whose marked breakpoints must
be one consecutive run, anywhere along the dimension.

### Missing breakpoints

A parameter that an entry reads takes [`missing:`](parameters-variables-constraints.md#a-missing-row)
like any other parameter, and reads it the same inside and outside the curve.
A values parameter of a curve with `points:` may **not** be `refused`, because
the curve stops where the mask stops, so the table has no rows past it by
design. `refused` says that every row is there, so the curve never runs short
and a mask that names the table marks every breakpoint. `to_spec` refuses the
file:

```text
parameter 'bp_y' is refused where a row is missing, and piecewise 'cost_curve' reads it under points: 'bp_x', which stops the curve where its rows stop. Declare missing: neutral, absent, or a value of its dtype.
```

Declare `missing: neutral` or `absent` on each values parameter of the entry.
The two build the same curve, because the curve reads a table only inside the
mask, and there the `<entry>_complete` assumption still refuses a missing row.
They differ where an expression outside the curve reads the table: `neutral`
reads `0` there, and `absent` removes the term. Use `absent` where no number
stands for a breakpoint the curve does not have, and `neutral` where `0` does.
A values parameter of a curve with no `points:`, and a boolean `points:` mask,
read the default, `refused`.

### `method`

`method` says how the weights are restricted once they exist.

| `method`                | What it adds                                                                  |                                                                |
| ----------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `adjacency` _(default)_ | an [`sos:`](#sos) entry over the weights, written out as binaries             | the curve, built                                               |
| `sos2`                  | an [`sos:`](#sos) entry over the weights, left as a set                       | the curve, stated for a solver that branches on the set itself |
| `convex`                | nothing                                                                       | the hull, which is a pure linear program                       |
| `lp`                    | no weights at all: one row per segment line, plus two rows holding the domain | the curve as its own lines                                     |

`convex` takes exactly two links and no `activity:`, and the shape it needs is
an [assumption](assumptions.md#what-a-curve-assumes).

`lp` states the curve as its segment lines. It needs **exactly two links**, one
of them bounded with `<=` or `>=`, and no `activity:`:

```yaml
piecewise:
  cost_curve:
    over: bp
    method: lp
    links:
      - [p, bp_x]
      - [op_cost, bp_y, ">="] # cost bounded below by the curve
```

Where the number of links is data, write the formulation out ([a curve by
hand](../../howto/curve-by-hand.md)).

## `sos`

An `sos` entry declares a **special-ordered set**: one dimension of one
variable, and how many members of that set may be non-zero at once.

```yaml
sos:
  pick_one_size:
    variable: build # the variable the set is over
    along: size # the dimension it runs along — one set per coordinate of the rest
    type: 1 # 1: at most one non-zero; 2: at most two, and consecutive
```

A set is over **one** variable, and a variable holds **one** set, so a second
entry naming the same variable is a load error.

A member the variable's `where` masks out is not in the set. The order is the
order of the `along` dimension, which is
[ordered](dimensions.md#order) for `type: 2`.

### What a set is written out as

`spec.expand('sos')` states the set as binaries: one per member for `type: 1`,
one per segment for `type: 2`. A member the binaries do not admit is held at
zero, from above and from below. For a set `s` over variable `x` along `d`, let
`admitted` be `(s_seg)` at `type: 1` and `(s_seg + shift(s_seg, along=d,
offset=1, edge=0))` at `type: 2`:

| Emitted                                            |                                                   |
| -------------------------------------------------- | ------------------------------------------------- |
| `s_seg`                                            | a binary over `x`'s own dims, masked as `x` is    |
| `s_pick`: `sum(s_seg, over=d) <= 1`                | at most one is picked                             |
| `s_nonzero` (`type: 1`), `s_adjacency` (`type: 2`) | `x <= upper * admitted`                           |
| the same name plus `_below`                        | `x >= lower * admitted`, where `lower` is not `0` |

`upper` and `lower` are the `bounds:` of the member, a number or a parameter,
and for a binary member they are `0` and `1`. `to_spec` refuses a spec where a
member has no `bounds.lower`, or no `bounds.upper` and no `domain: binary`. A
name the expansion writes that the file already declares is refused at load too.

## Writing a formulation out

[`Spec.expand()`](../spec.md#mathspec.spec.Spec.expand) replaces the entry
with the variables and constraints it states.
[See what a curve or a set expands to](../../howto/see-an-expansion.md) shows a
spec before and after.

- Every name written out starts with the name of the entry, so the weights of
  the curve `curve` are `curve_lam`.
- No formulation emits a parameter, so the same data attaches to a spec and its
  expansion, and reads the same in both.
- The assumptions a `method:` implies become `assumptions:` entries with the
  same names.
