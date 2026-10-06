<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Named expressions and macros

An `expressions:` entry names a quantity once, for the math to read or for a
solve to report. A `macros:` entry is a template that takes arguments, which
the loader substitutes into an expression before anything reads it.

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

An entry is a bare string, or a mapping with a `description:` and a `dims:`.
The `dims:` are the **frame**, the dimensions the quantity is read over. When
`dims:` is left out, the body decides the frame. When `dims:` is declared, the
loader refuses a body that carries a dimension the frame does not name. The
body may carry fewer dimensions, and then the quantity is constant along the
rest, so a constraint over the whole frame reads it at every coordinate.

```yaml
expressions:
  cap:
    dims: [snapshot, generator]
    expression: p_max
    description: the nominal capacity, the same in every snapshot
```

[`adds_to:`](declarations.md#terms) adds this expression as a term to the sum
it names. The sum is a [given expression](declarations.md#given-expressions)
of the same file, and [`merge`](../../howto/compose.md#a-library-of-components)
adds the entry to it by its own name.

Where the objective or a constraint names it, the body is substituted there, and
the [degree limit](expressions.md#where-a-product-of-two-variables-is-allowed)
applies where it is read. Where nothing in the math names it, the entry is
[reported](#reported-expressions).

## `cases`

Write a quantity with several regimes as `cases:`, and write the rule that
reads it once. The commitment state a unit carries into a snapshot is `1`
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

- No two cases may claim one coordinate. `to_spec` refuses the file when two
  `when:` masks can be true at once:

  > `Named expression 'previous_status'`: cases `always_on` and `boundary` both
  > claim the value where committable is false, the position of snapshot is 0.
  > Narrow one of the two `when:` strings by the negation of the other, or drop
  > the wider one and let `otherwise:` cover that region.

  The cases carry no order.

- A `when:` must be a question the data answers. `True`, `False`, and a mask
  that folds to one of them, such as `committable OR True`, are refused.

- A pair the check cannot decide is refused. For example,
  `position(snapshot) == 0` and `position(snapshot) == -1` pick the same row on
  a dimension with one member, so count from one end only.

- In a block of two or more cases, a `when:` may not compare expressions, such
  as `c > 2 * k`, because the loader cannot prove such a case apart from the
  others before the data arrives. Precompute the test as a boolean parameter. A
  block with one case may compare expressions, because its `otherwise:` claims
  only what the case leaves.

- Each `when:` and each value sits inside the frame, and a narrower case
  broadcasts as a parameter with fewer dimensions does.

A claimed coordinate can still have no value: the `otherwise:` above has none at
the first snapshot, where a case claims every unit. To give such a coordinate a
value, widen a `when`, give the `shift` an `edge=`, or set `absence: zero` on
the masked variable.

`cases:` is not accepted inside a `macros:` template.

## Reported expressions

A named expression is either **in the math** or **reported**, and the
objective and the constraints decide which:

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

`system_cost` is in the math, while `delivered` and `lcoe` are reported.

An entry is in the math when the objective, a constraint or a `piecewise:`
link reaches it, directly or through another entry or a macro. A bound and a
`where` name no entry.

A reported entry has **no** degree limit, so it may divide by a variable, raise
one to a power, and multiply two sums. It may not hold a comparison. A
constraint that names such an entry is refused under the constraint's own name.

### Reading a constraint's dual

`dual(c)` reads the **row dual** of the constraint `c`: the shadow price a solve
puts on that row, over the `dims` of `c`. Only a reported entry may call it.
`to_spec` refuses it in a constraint, the objective, a `piecewise:` link, or an
entry that one of those inlines:

```text
Constraint 'd': a dual exists only after a solve, so it cannot stand here. Keep the entry
that reads it out of constraints, the objective, bounds and where.
```

`dual(c)` is the rate at which the optimal objective rises as the right side
of `c` rises. Read `lhs <= rhs` as `lhs <= rhs + d`: the dual is the rate in `d`
at `d = 0`. The rule is the same for `<=`, `>=` and `==`, and under `minimize`
and `maximize`, so an equality has a dual with a sign too. The side you write a
term on decides the sign: `p <= cap` and `-p >= -cap` state one row, and their
duals are opposite.

| Under `minimize`, a binding row | Its dual                             |
| ------------------------------- | ------------------------------------ |
| `p <= cap`                      | at most 0                            |
| `p >= load`                     | at least 0                           |
| `sum(p, over=g) == load`        | the price of one more unit of `load` |

A row that `c`'s `where:` deletes has no dual.

## `macros`

A macro declares its arguments and its template:

```yaml
macros:
  weighted_sum:
    args: [array, weights] # positional formals, default []
    kwargs: [over] # keyword formals, default []
    template: sum(array * weights, over=over)
```

- A template holds arithmetic, and no comparison.
- An argument may itself use macros and named expressions.
- The formal arguments are the names under `args` and `kwargs`. Inside a
  template, a formal hides a name the spec declares, but a formal may not
  collide with a declared dimension.
- The loader checks the number of arguments at each call site. It reports a
  cycle of macros with the chain of names that forms it.
- `to_spec` checks every template against every rule a call site is held to,
  whether or not anything calls it. A formal is left for the call site to bind.
- A formal may stand in a list, as in `sum(x, over=[d, snapshot])`. There the
  call binds it to a name, or to a list of names that is spliced in.

Write a composition of the [built-in operators](operators.md) as a macro.
[The limits](../../about/limits.md#requests-the-language-refuses) list what the
language will not express.
