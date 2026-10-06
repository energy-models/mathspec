<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Named expressions, masks and macros

An `expressions:` entry names a quantity once, for the math to read or for a
solve to report. A `masks:` entry names a `where` predicate once, for every
`where:` that reads it. A `macros:` entry is a template with arguments,
substituted before anything reads it.

## `expressions`

A constraint or the objective may use a named expression, and a solve may
report its value:

```yaml
dimensions:
  generator: { dtype: str }
parameters:
  rate: { dims: [generator] }
variables:
  p: { dims: [generator] }
expressions:
  total_generation: sum(p, over=generator)
  emissions:
    expression: sum(p * rate, over=generator)
    description: CO2 released, the quantity a cap would bound
```

It is a bare string, or a mapping with a `description:` and a `dims:`. The
`dims:` are the **frame**, the dimensions the quantity is read over. Left out,
the body decides the frame. Declared, the body may carry no dimension the
frame does not name, which the loader checks, and it may carry fewer: the
quantity is then constant along the rest, and a constraint over the whole frame
reads it at every coordinate.

```yaml
expressions:
  cap:
    dims: [snapshot, generator]
    expression: p_max
    description: the nominal capacity, the same in every snapshot
```

[`adds_to:`](entries.md#terms) adds this expression as a term to the sum
it names. The sum is a [given expression](entries.md#given-expressions)
of the same file, and [`merge`](../../howto/compose.md#a-library-of-components)
adds the entry to it by its own name.

Where the objective or a constraint names it, the body is substituted there,
and the [degree limit](expressions.md#where-a-product-of-two-variables-is-allowed)
applies where it is read. Where nothing in the math names it, the entry is
[reported](#reported-expressions).

## `cases`

A quantity with several regimes is written as cases, and the rule that reads it
is written once. The commitment state a unit carries into a snapshot is `1`
for a unit that is never switched off, an initial condition at the first
snapshot, and the previous snapshot's status everywhere else:

```yaml
expressions:
  previous_status:
    description: the commitment state a unit carries into a snapshot
    dims: [snapshot, generator]
    cases:
      always_on:
        when: "not committable"
        expression: 1
      boundary:
        when: "committable and position(snapshot) == 0"
        expression: status_initial
    otherwise: shift(status, along=snapshot, offset=1)
constraints:
  ramp_up:
    dims: [snapshot, generator]
    expression: >-
      p - shift(p, along=snapshot, offset=1, edge=0)
      <= ramp_limit * previous_status + start_up_limit * (1 - previous_status)
```

Each case prints as one row of the definition, and `otherwise:` as the last:

$$\mathit{previous\_status}_{t,g} = \begin{cases} 1 & \text{if } \neg \mathrm{committable}_{g} \cr \mathrm{status}^{\mathrm{initial}}_{g} & \text{if } \mathrm{committable}_{g} \wedge \mathrm{pos}(t) = 0 \cr \mathit{status}_{t - 1,g} & \text{otherwise} \end{cases} \qquad \forall\thinspace t \in \mathcal{T},\enspace g \in \mathcal{G}$$

A named expression carries **exactly one** of `expression:` and `cases:`.

| Key         |                                                                              |
| ----------- | ---------------------------------------------------------------------------- |
| `dims`      | required with `cases:`. The **frame**: the dimensions every case ranges over |
| `cases`     | a map of named cases, each with a `when:` mask and an `expression:`          |
| `otherwise` | required. The value at every coordinate the cases leave                      |

### The rules that keep the cases apart

- **No two cases may claim one coordinate.** If two `when:` masks can hold at
  once, the file is refused at load:

  > `Named expression 'previous_status'`: cases `always_on` and `boundary` both
  > claim the value where committable is false, the position of snapshot is 0. A
  > coordinate two cases claim has two values, so it has none — narrow one of the
  > two `when:` strings by the negation of the other, or drop the wider one and
  > let `otherwise:` carry that region.

  The cases carry no order.

- **A `when:` must be a question the data answers.** `True`, `False`, and a mask
  that folds to one of them, such as `committable OR True`, are refused.

- **A pair the check cannot decide is refused.** `position(snapshot) == 0`
  against `position(snapshot) == -1` pick the same row on an axis with one
  member. Count from one end only.

- **In a block of two or more cases, a `when:` may not compare expressions**,
  such as `c > 2 * k`. Nothing proves such a case apart from the others before
  the data arrives. Precompute the test as a boolean parameter. A block with one
  case may compare expressions: its `otherwise:` claims only what the case
  leaves.

- **Each `when:` and each value sits inside the frame.** A narrower case
  broadcasts as a parameter with fewer dimensions does.

A claimed coordinate can still have no value: the `otherwise:` above has none
at the first snapshot, where a case claims every unit. To close such a hole,
widen a `when`, give the `shift` an `edge=`, or set `missing: neutral` on the
masked variable.

`cases:` is not accepted inside a `macros:` template.

## Reported expressions

A named expression is either **in the math** or **reported**. The objective
and the constraints decide which:

```yaml
dimensions:
  generator: { dtype: str }
  snapshot: { dtype: int }
parameters:
  marginal_cost: { dims: [generator] }
variables:
  p: { dims: [snapshot, generator] }
expressions:
  system_cost: sum(sum(p * marginal_cost, over=generator), over=snapshot)
  delivered: sum(sum(p, over=generator), over=snapshot)
  lcoe: system_cost / delivered
objective: { sense: minimize, expression: system_cost }
```

`system_cost` is in the math. `delivered` and `lcoe` are reported.

An entry is in the math when the objective, a constraint or a `piecewise:`
link reaches it, directly or through another entry or a macro. A bound and a
`where` name no entry.

**No degree limit applies to a reported entry**: it may divide by a variable,
raise one to a power, and multiply two sums. A comparison stays out. A
constraint that names such an entry is refused under the constraint's own name.

### Reading a constraint's dual

`dual(c)` reads the **row dual** of the constraint `c`: the shadow price a solve
puts on that row, over `c`'s own `dims`. Only a reported entry may call it. In a
constraint, the objective, a piecewise link, or an entry one of those inlines,
it is refused:

```text
Constraint 'd': a dual exists only after a solve; the math cannot read one —
keep the entry that carries it out of constraints, the objective, bounds and where.
```

`dual(c)` is the rate at which the optimal objective rises as the right side
of `c` rises. Read `lhs <= rhs` as `lhs <= rhs + d`: the dual is the rate in `d`
at `d = 0`. The rule is the same for `<=`, `>=` and `==`, and under `minimize`
and `maximize`, so an equality has a dual with a sign too. Which side a term is
written on decides the sign: `p <= cap` and `-p >= -cap` state one row, and their
duals are opposite.

| Under `minimize`, a binding row | Its dual                             |
| ------------------------------- | ------------------------------------ |
| `p <= cap`                      | at most 0                            |
| `p >= load`                     | at least 0                           |
| `sum(p, over=g) == load`        | the price of one more unit of `load` |

A row that `c`'s `where:` deletes has no dual.

## `masks`

A mask names a [`where` predicate](expressions.md#where-strings) once. A
`where:`, a `when:` or a `holds:` then reads it by name:

```yaml
dimensions:
  period: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  build_year: { dims: [generator] }
  lifetime: { dims: [generator] }
  period_year: { dims: [period] }
  p_nom: { dims: [generator] }
masks:
  stands:
    where: build_year <= period_year AND period_year < build_year + lifetime
    description: the generator stands in this period
variables:
  p:
    dims: [period, generator]
    where: stands
    bounds: { lower: 0, upper: p_nom }
constraints:
  ramp_up:
    dims: [period, generator]
    where: stands AND shift(stands, along=period, offset=1)
    expression: p - shift(p, along=period, offset=1) <= 0.5 * p_nom
```

The typeset document prints the mask's symbol where it is read. The symbol is
upright, as data is. The predicate prints once, under _Masks_, with ⟺ where an
expression prints =:

```math
\mathrm{stands}_{e,g} \iff \mathrm{build\_year}_{g} \le \mathrm{period\_year}_{e} \wedge \mathrm{period\_year}_{e} < \mathrm{build\_year}_{g} + \mathrm{lifetime}_{g} \qquad \forall\, e \in \mathcal{E},\ g \in \mathcal{G}
```

```math
p_{e,g} - p_{e - 1,g} \le 0.5 \cdot \mathrm{p}^{\mathrm{nom}}_{g} \qquad \forall\, e \in \mathcal{E},\ g \in \mathcal{G} \,:\, \mathrm{stands}_{e,g} \wedge \mathrm{stands}_{e - 1,g}
```

| Field         |                                                 |                |
| ------------- | ----------------------------------------------- | -------------- |
| `where`       | required. The predicate, in the `where` grammar |                |
| `description` | free text                                       | default `null` |

An entry with no `description:` may be the bare `where` string.

- **A bare mask name stands for its predicate.** It does so in a `where:`, a
  `when:` and a `holds:`, under `NOT`, and inside `count`, `shift` and `at`.
  The rows are the rows the predicate written out gives.
- **The predicate gives the frame.** A mask runs over the dimensions its
  predicate reads, in the order `dimensions:` declares them, and the symbol
  prints with those indices. A mask declares no `dims:`. A use over more
  dimensions reads the mask as the same along the rest, and `shift` reads it
  back along a dimension of its frame only.
- **A mask may read another mask**, and a named expression that reads data
  only. A cycle is refused with its chain:

  ```text
  Mask 'again': circular mask reference: again -> again
  ```

- **A mask is never a number.** In arithmetic or in a comparison it is
  refused:

  ```text
  Named expression 'e': 'stands' is a mask, which is true or false where it is read, and not a number. Write it bare in the where — stands, or NOT stands — rather than comparing it or computing with it.
  ```

- **A predicate that folds to `True` or `False` is refused**, since it names
  every row or none.
- **A variable's own `where:` may not ask, through a mask, whether the
  variable exists.** The loader refuses this as it refuses the bare name.

Another file reads a mask under [`given: masks`](entries.md#given-masks).

## `macros`

A macro is a template that takes arguments and is substituted into an expression
before anything reads it:

```yaml
macros:
  weighted_sum:
    args: [array, weights] # positional formals, default []
    kwargs: [over] # keyword formals, default []
    template: sum(array * weights, over=over)
```

- A template holds arithmetic, and no comparison.
- An argument may itself use macros and named expressions.
- Inside a template, the formal parameters shadow the names the spec
  declares. A formal may not collide with a declared dimension.
- The number of arguments is checked at each call site. A cycle is reported with
  its reference chain.
- Every template is held at load to every rule a call site is, whether or not it
  is called. A formal is left for the call site to bind.
- A formal may stand in a list, as in `sum(x, over=[d, snapshot])`. There the
  call binds it to a name, or to a list of names that is spliced in.

A composition of the [built-in operators](operators.md) belongs here. What
the language will not express is in
[the limits](../../about/limits.md#deliberate-non-primitives).
