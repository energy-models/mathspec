<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Expressions

An expression is a formula over numbers,
[parameters and variables](parameters-variables-constraints.md), such as
`p * cost` or `sum(p, over=generator) >= load`. This page defines the grammar
of an expression and of a condition, and lists what mathspec refuses in each at
load.

## The arithmetic grammar

In a [constraint](parameters-variables-constraints.md#constraints), in the
[objective](parameters-variables-constraints.md#objective), in a
[named expression](named.md#expressions) and in a
[macro template](named.md#macros), every `expression:` has one grammar. The
grammar below states every form that it accepts.

```text
expression  ::= arithmetic | arithmetic COMPARATOR arithmetic
arithmetic  ::= atom | unary_sign arithmetic | arithmetic binary_sign arithmetic
             |  function_call | "(" arithmetic ")"
atom        ::= NUMBER | NAME
unary_sign  ::= "+" | "-"     binary_sign ::= "+" | "-" | "*" | "/" | "**"
COMPARATOR  ::= "<=" | ">=" | "=="
function_call ::= NAME "(" [pos_arg ("," pos_arg)*] ["," kwarg ("," kwarg)*] ")"
pos_arg     ::= arithmetic
kwarg       ::= NAME "=" (arithmetic | QUOTED | "[" NAME ("," NAME)* "]" | COLUMNS)
COLUMNS     ::= NAME "[" NAME ("," NAME)* "]"
QUOTED      ::= "'" chars "'" | '"' chars '"'
NAME        ::= [a-zA-Z_][a-zA-Z0-9_]*
NUMBER      ::= integer | float | "inf" | ".inf"
```

Four rules complete the grammar:

- mathspec applies `**` first, then unary `+` and `-`,
  then `*` and `/`, then binary `+` and `-`. So, as in Python, `-x ** 2` is
  `-(x ** 2)`.
- A float may have an exponent, as in `1e5` or `2.5e-3`.
- The same keyword twice in one call is refused, and for
  `sum(p, over=g, over=g)` mathspec prints `The objective: sum(over=) is given twice. Delete one of them.`
- An expression and a `where:` string nest at most 100 levels deep. Once
  mathspec substitutes every named expression, the limit is 300 levels.

## Where a product of two variables is allowed

The objective and the constraints accept the product of two variables, which
makes them quadratic, so a quadratic cost and a quadratic constraint both load:

```yaml
dimensions:
  g: { dtype: str }
parameters:
  wear: { dims: [g] }
  floor: { dims: [g] }
variables:
  p: { dims: [g], bounds: { lower: 0 } }
  q: { dims: [g], bounds: { lower: 0 } }
constraints:
  product: { dims: [g], expression: p * q >= floor }
objective:
  sense: minimize
  expression: sum(p * p * wear, over=g)
```

```math
\min \sum_{g \in \mathcal{G}} p_{g} \cdot p_{g} \cdot \mathrm{wear}_{g}
```

```math
p_{g} \cdot q_{g} \ge \mathrm{floor}_{g} \qquad \forall\, g \in \mathcal{G}
```

At each generator `g`, the cost multiplies `p` by itself, and the constraint
multiplies `p` by `q`. `x * x` is a square, and
[`**`](#division-and-powers) takes no variable.

Three rules limit a product. At most one factor of a product may be a sum of
more than one term. A product of two sums is refused, because it multiplies
every term of one sum by every term of the other:

```yaml
dimensions:
  g: { dtype: str }
variables:
  p: { dims: [g], bounds: { lower: 0 } }
  q: { dims: [g], bounds: { lower: 0 } }
objective:
  sense: minimize
  expression: sum(p, over=g) * sum(q, over=g)
```

```text
The objective: both factors of this product are sums of more than one term, which makes an outer product.
Multiply before you reduce: write ``sum(x * y, over=d)``, not ``sum(x, over=d) * sum(y, over=d)``.
```

mathspec suggests the rewrite, which multiplies before it sums.

Factors over different [dimensions](dimensions.md) are allowed, so
`x * y * link` with `x` over `a` and `y` over `b` loads. `link` has a value at
each pair of `a` and `b`.

The number of variables multiplied together (the degree) may be at most 2, so
a product of three variables is refused:

```yaml
dimensions:
  g: { dtype: str }
variables:
  p: { dims: [g], bounds: { lower: 0 } }
objective:
  sense: minimize
  expression: sum(p * p * p, over=g)
```

```text
The objective: this product is degree 3, and the limit is degree 2.
Multiply by a parameter instead, or declare a variable constrained to equal the inner product.
```

mathspec suggests two rewrites: a parameter in place of one variable, or a
new variable equal to the inner product.

A bound and a `piecewise:` link must stay a constant plus variables times
numbers (affine). A bound is one number per coordinate of the variable, so
it cannot be a product.

A [reported expression](named.md#reported-expressions) is not held to these
three rules, because no solver reads it.

## Division and powers

A divisor must have no variable, and a power must have no variable in its base
or its exponent. Within those limits, a divisor, a base and an exponent
accept any arithmetic over numbers and parameters. So a discount factor can
appear where it is used:

```yaml
dimensions:
  period: { dtype: int }
parameters:
  rate: { dims: [] }
  years: { dims: [period] }
  price: { dims: [period] }
variables:
  build: { dims: [period], bounds: { lower: 0 } }
constraints:
  enough: { dims: [], expression: "sum(build, over=period) >= 1" }
objective:
  sense: minimize
  expression: sum(build * price / (1 + rate) ** years, over=period)
```

```math
\min \sum_{p \in \mathcal{P}} \frac{\mathit{build}_{p} \cdot \mathrm{price}_{p}}{\left( 1 + \mathrm{rate} \right)^{\mathrm{years}_{p}}}
```

The discount factor uses the parameter `years`, which has one value per
period. The exponent cannot be the dimension `period` itself, because an
expression uses no [dimension](dimensions.md). mathspec prints this
message for `sum(build * 2 ** period, over=period)`:

```text
The objective: 'period' is a dimension, and a dimension is not a value. To use its coordinates as data, declare a parameter over it.
```

mathspec suggests the rewrite: a parameter over the dimension.

A variable in a divisor is refused in the same way, and mathspec prints this
message for `sum(cost / p, over=g)`:

```text
The objective: the divisor contains variables, which is not affine. Divide by a parameter, or precompute the reciprocal as one.
```

mathspec suggests two rewrites: a parameter as the divisor, or the
reciprocal as a parameter.

## Name resolution

Every name a spec declares is in one flat set of names (a namespace). That
namespace contains
the dimensions, [relations](relations.md), parameters, variables, named
expressions, [named conditions](named.md#conditions),
[macros](named.md#macros) and the built-in operators. Two entries with one name are
refused at load, and mathspec names both, so no name hides another. For
a parameter and a variable both called `p`, mathspec prints:

```text
Variable 'p' collides with the parameter of the same name. Rename one of them.
```

mathspec suggests the rewrite: a new name for one of the two entries.

The place of a name in a string sets which kinds of name it may be:

| Place                                  | Kinds of name it accepts                                                                                      |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| expression (`p * cost`)                | a variable, or a parameter whose values are numbers ([dtype](parameters-variables-constraints.md#parameters)) |
| dimension argument (`over=`, `along=`) | a dimension, a list of them for `over=`, or with `by=` a column of the relation where one has that name       |
| column argument (`by=`, `within=`)     | columns of one relation, written `relation[column]` or `relation[column, …]`                                  |
| condition                              | a parameter, variable, dimension, relation or named condition ([conditions](#conditions))                     |
| `bounds.lower` / `bounds.upper`        | a parameter name, or a number                                                                                 |
| the `edge` key of `shift`              | `'wrap'` in quotes, or a bare number                                                                          |
| `dual` argument (`dual(c)`)            | a constraint, resolved against the constraints alone ([named expressions](named.md#dual))                     |

A bare word in the value of a keyword argument is a name, and mathspec looks
it up. The key of a keyword argument is never a name, so `over` in
`over=generator` collides with nothing.

Four sections sit outside the flat namespace: `constraints`, `assumptions`,
`sos` and `piecewise`. No expression uses an entry of these sections by a
bare name. So an entry in one of them may share its name with an entry in the
flat namespace. It may also share its name with an entry in one of the other
three sections. Only `dual()` uses a constraint, and it uses the constraint by
its name.

A named expression with [`adds_to:`](named.md#adds_to) (a
[term](../glossary.md#term)) always adds to the named expression it names,
and never to a constraint of the same name.

## How dimensions combine

Before any data is attached, [`to_spec`](../api.md#mathspec.to_spec) works out the
dimensions of every expression. Each part of an expression (a node) has a set of dimensions:

| Node                             | Dimensions of the result       | Refused when                                                                          |
| -------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------- |
| number                           | `{}`                           |                                                                                       |
| parameter / variable             | its `dims`                     |                                                                                       |
| `-x`, `+x`                       | `dims(x)`                      |                                                                                       |
| `a + b`, `a * b`, `a / b`        | `dims(a) ∪ dims(b)`            |                                                                                       |
| `sum(x)`                         | `{}`                           | `dims(x)` is already empty                                                            |
| `sum(x, over=d)`                 | `dims(x) − {d}`                | `d ∉ dims(x)`                                                                         |
| `sum(x, over=d, by=l[c])`        | `(dims(x) − joined) ∪ grouped` | a refusal under [how a relation is used](relations.md#how-a-relation-is-used) applies |
| `at(x, by=l[c])`                 | `(dims(x) − joined) ∪ grouped` | the same refusals apply                                                               |
| `shift(x, along=d, offset=n)`    | `dims(x)`                      | `d ∉ dims(x)`                                                                         |
| `sum_back(x, along=d, window=n)` | `dims(x)`                      | `d ∉ dims(x)`                                                                         |

mathspec refuses `sum(p, over=t)` with `p` over `g` alone, and prints:

```text
The objective: sum(over=t) but the expression has only the dims ['g']. Remove the sum, or correct the dimension.
```

mathspec suggests two rewrites: no sum, or the dimension that `p` is over.

The dimensions of an expression must agree with the dimensions of its entry
(its [frame](../glossary.md#frame)), and mathspec refuses the file at load in
three cases:

- A [constraint](parameters-variables-constraints.md#constraints) requires
  `dims(lhs) ∪ dims(rhs)` to **equal** its `dims`.
- An [objective](parameters-variables-constraints.md#objective) must be over
  **no dimensions**.
- A condition and a bound parameter must not **exceed** the frame they sit in.

## Conditions

A condition is a test that is true or false at each combination of labels (a
[coordinate](../glossary.md#coordinate)), such as `capacity > 0`. Four keys
take a condition: `where:`, `holds:`, a case [`when:`](named.md#cases) and an
entry under [`conditions:`](named.md#conditions). A `where:` narrows an entry
to the coordinates where the condition is true, and leaves the others
[absent](absence.md). A tool checks a [`holds:`](assumptions.md) condition
against the data.

<figure class="diagram">
--8<-- "docs/static/absence-where-variable.svg"
</figure>

With `where: capacity > 0` on the variable `dispatch`, `dispatch` has rows for
`wind` and `gas`, and no row for `old`.

All four keys take the grammar below:

```text
condition ::= atom | "NOT" condition | condition ("AND"|"OR") condition
            |  "(" condition ")"
atom       ::= NAME | (NAME | COLUMN) COMPARATOR value | expression COMPARATOR expression
            |  POSITION COMPARATOR INTEGER | COUNT COMPARATOR INTEGER | TRANSLATED
            |  READ | "True" | "False"
COMPARATOR ::= "<=" | ">=" | "==" | "!=" | "<" | ">"
value      ::= NUMBER | QUOTED | NAME_OR_STRING | COLUMN
expression ::= the arithmetic grammar above, with no variable and no dual in it
POSITION   ::= "position" "(" NAME [ "," "within" "=" COLUMNS ] ")"
COUNT      ::= "count" "(" condition "," "over" "=" NAME ")"
TRANSLATED ::= "shift" "(" condition "," "along" "=" NAME "," "offset" "=" INTEGER ")"
READ       ::= "at" "(" condition "," "by" "=" COLUMNS ")"
COLUMN     ::= NAME "[" NAME "]"
COLUMNS    ::= NAME "[" NAME { "," NAME } "]"
QUOTED     ::= "'" chars "'" | '"' chars '"'
```

A name written alone is a bare name, and what it tests depends on the kind of
its entry.

| Written as                               | Kind of name               | Meaning                                                                                                                                                                                                                                                                        |
| ---------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `name` (bare)                            | parameter                  | For a number, it is true where the data has a row, whatever the `missing:`. For a `bool`, it is its value, and the `missing:` sets the value at a missing row ([`missing`](parameters-variables-constraints.md#missing)). `0.0` is a row, and `inflow != 0` tests for non-zero |
| `name` (bare)                            | variable                   | It is true where the variable exists                                                                                                                                                                                                                                           |
| `name` (bare)                            | relation                   | It is true where a row exists, tested at the relation's key. A `missing: absent` relation has no row for some key combinations ([`missing`](relations.md#missing)), and the bare name selects the labels that do map                                                           |
| `name` (bare)                            | dimension                  | mathspec refuses it at load                                                                                                                                                                                                                                                    |
| `name` (bare)                            | named condition            | It tests the [named condition](named.md#conditions). A given condition is true or false at each coordinate, as a `bool` parameter is                                                                                                                                           |
| `name OP value`                          | parameter                  | It compares element by element. A missing row with no `missing:` value compares false                                                                                                                                                                                          |
| `name OP value`                          | dimension                  | It filters the frame's own coordinate column                                                                                                                                                                                                                                   |
| `name OP value`, `name[col] OP value`    | relation                   | It filters a value column, tested at the relation's key. The column is required where the key determines several. A comparison uses one column. Where the relation has no row, the comparison is false for every operator, `!=` included, so `NOT` of it is true there         |
| `name OP name`, `name[a] OP name[b]`     | two relation columns       | mathspec accepts it where both relations are keyed over the same dimensions and both columns are over one dimension. `ends[bus0] != ends[bus1]` excludes a self-loop. Where either relation has no row, the comparison is false                                                |
| `expression OP expression`               | arithmetic over parameters | It compares coordinate by coordinate, over every dimension either side is over ([arithmetic in a comparison](#arithmetic-in-a-comparison)). A side with no value at a coordinate compares false                                                                                |
| `position(name) OP i`                    | dimension                  | It tests where the row sits along the dimension's own order. `0` is first, and a negative number counts from the end                                                                                                                                                           |
| `position(name, within=relation[c])`     | dimension                  | It tests the same, counted within each group the relation makes                                                                                                                                                                                                                |
| `count(condition, over=name) OP i`       | condition                  | It compares how many coordinates along the dimension the condition admits ([`count`](#count))                                                                                                                                                                                  |
| `shift(condition, along=name, offset=i)` | condition                  | It is the condition `i` coordinates back, and false at the first `i` coordinates                                                                                                                                                                                               |
| `at(condition, by=relation[c])`          | condition                  | It is the condition through the relation ([`at` in a condition](#at-in-a-condition)), and false where the relation has no row                                                                                                                                                  |
| `AND` `OR` `NOT`                         |                            | They are case-insensitive. `NOT` applies before `AND`, and `AND` before `OR`                                                                                                                                                                                                   |
| `True` / `False`                         |                            | `True` is the same as no `where`. `False` leaves an entry with no rows                                                                                                                                                                                                         |

With a dimension `bp` declared, mathspec prints for `where: "bp"`:

```text
Variable 'p': 'bp' is a dimension, and a bare dimension name is true at every coordinate. Remove it, or compare it: where: "bp > 0".
```

mathspec suggests the rewrite: a comparison, `bp > 0`, which tests the label
of each coordinate.

mathspec also refuses a bare name that the spec does not declare. For the spec
under
[`count`](#count) below, mathspec lists the names that the place accepts:

```text
Variable 'p': 'undeclared_thing' not found.
  Parameters: ['bp_x', 'points']
  Dimensions: ['bp', 'generator']
  Relations: []
Check the spelling, or declare 'undeclared_thing'.
```

mathspec ends the message with two rewrites: correct the spelling, or declare
the name.

### `count`

`count(<condition>, over=<dimension>)` returns how many coordinates along the
dimension make the condition true, and a count is compared with a whole number.
A count does not use the values of a parameter, only whether the condition is
true.
In the spec below, `p` exists only for a generator with at least two
[breakpoints](piecewise.md) where `points` is true (marked):

```yaml
dimensions:
  bp: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  bp_x: { dims: [generator, bp] }
  points: { dims: [generator, bp], dtype: bool }
variables:
  p:
    dims: [generator]
    where: "count(points, over=bp) >= 2"
    bounds: { lower: 0 }
constraints:
  cap:
    dims: [generator]
    expression: p <= 1
objective:
  sense: minimize
  expression: sum(p, over=generator)
```

```math
p_{g} \ge 0 \qquad \forall\, g \in \mathcal{G} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{points}_{g,b} \} \rvert \ge 2
```

<figure class="diagram">
--8<-- "docs/static/expressions-count.svg"
</figure>

With the data in the figure, `gas` has one marked breakpoint, so `p` has no row
for `gas`.

A count removes the dimension it counts over, as `sum(over=)` does. So the
condition above has one count per generator, and the condition is over
`generator` alone.

mathspec refuses a count along a dimension that the condition is not over.
With `p`
over `generator` and `site`, mathspec prints for `count(points, over=site)`:

```text
Variable 'p': count(<condition>, over='site') counts along a dimension the condition does not read. Count along one of 'bp' and 'generator'.
```

mathspec lists the dimensions that the condition is over.

A fraction or a parameter on the right-hand side is refused, because it must
be a literal whole number. mathspec prints this message for
`count(points, over=bp) >= 1.5`:

```text
Variable 'p': a count is compared against a value that is not a literal whole number. Write count(…, over=bp) >= <integer>.
```

mathspec suggests the rewrite: a whole number.

mathspec also refuses a comparison that a count can never fail, or never meet.
That
covers `>= 0`, `< 0` and any comparison with a negative number, and mathspec
prints this message for `count(points, over=bp) >= 0`:

```text
Variable 'p': count(…, over=bp) >= 0 holds at every coordinate, because a count is never negative. Delete the comparison, or write the bound it means.
```

mathspec suggests two rewrites: no comparison, or the bound that the
comparison means.

### `shift` in a condition

`shift(<condition>, along=<dimension>, offset=<integer>)` takes the value of
the condition `offset` coordinates back along an
[ordered](dimensions.md#ordered) dimension. It is
**false** at the first `offset` coordinates, which have no coordinate that far back, and a negative `offset` steps
forwards.

Together with `count`, a shift finds the start of a run. The `where:` below,
in the spec of the previous section, admits a generator whose marked
breakpoints form exactly one consecutive run:

```yaml
where: "count(points AND NOT shift(points, along=bp, offset=1), over=bp) == 1"
```

```math
p_{g} \ge 0 \qquad \forall\, g \in \mathcal{G} \,:\, \lvert \{ b \in \mathcal{B} \,:\, \mathrm{points}_{g,b} \wedge \neg \mathrm{points}_{g,b - 1} \} \rvert = 1
```

<figure class="diagram">
--8<-- "docs/static/expressions-shift-condition.svg"
</figure>

With the data of the previous figure, a run starts at breakpoint `0` of each
generator. The shift is false at breakpoint `0`, which has no breakpoint before
it, so a marked first breakpoint starts a run. Each generator has one start,
so `p` has a row for both.

This form of `shift` takes neither `within=` nor `edge=`, which only the
arithmetic `shift` takes.

!!! info "See also"

    - [`shift`](operators.md#shift), for `shift` in an expression.

### `at` in a condition

`at(<condition>, by=<relation>[<column>])` reads a condition over the values of
a relation at its key, as `at` reads an expression. It is true where the condition is true at the label that a row of the
relation maps to. It is **false** where the relation has no row. In
the spec below, `rate` exists only for a flow whose converter has a curve:

```yaml
dimensions:
  converter: { dtype: str }
  flow: { dtype: str }
relations:
  converter_of: { key: flow, values: converter }
parameters:
  has_curve: { dims: [converter], dtype: bool }
  cap: { dims: [flow] }
variables:
  rate:
    dims: [flow]
    where: "at(has_curve, by=converter_of[converter])"
    bounds: { lower: 0, upper: cap }
objective:
  sense: minimize
  expression: sum(rate, over=flow)
```

```math
0 \le \mathit{rate}_{f} \le \mathrm{cap}_{f} \qquad \forall\, f \in \mathcal{F} \,:\, \mathrm{has\_curve}_{\mathrm{converter\_of}(f)}
```

<figure class="diagram">
--8<-- "docs/static/expressions-at-condition.svg"
</figure>

The converter of `f3` has no curve, so `rate` has no row for `f3`.

`at` removes the column in `by=`, `converter`, and adds the key of the
relation, `flow`. So the condition is over `flow` alone, which is the frame of
`rate`.

`by=` lists one value column, or several as `relation[a, …]`, and every other
rule of [`at` in an expression](relations.md#lookups) applies.

!!! info "See also"

    - [`at`](operators.md#at), for `at` in an expression.

### The right-hand side of a comparison

An undeclared bare name on the right of a comparison is a label, so `generator == gas` tests for the label
`gas`. A declared
name on the right is refused at load.

A label must be quoted when it is not a [`NAME`](#the-arithmetic-grammar) of
letters, digits and underscores, such as `'combined-cycle'`. mathspec never
reads a quoted word as an entry. With `where: generator == combined-cycle` on
`p` in the spec under [`count`](#count), mathspec parses the right side as
arithmetic, `combined` minus `cycle`, and prints three refusals:

```text
Variable 'p': 'generator' is a dimension, and a dimension is not a value. To use its coordinates as data, declare a parameter over it.
Variable 'p': 'combined' not found.
  Variables: ['p']
  Parameters: ['bp_x', 'points']
Check the spelling, or declare 'combined'.
Variable 'p': 'cycle' not found.
  Variables: ['p']
  Parameters: ['bp_x', 'points']
Check the spelling, or declare 'cycle'.
```

The first line is about `generator` as a value in arithmetic, and the next
two are about the undeclared names `combined` and `cycle`.

mathspec checks each comparison against the `dtype` that the file declares. A `datetime`
dimension compares against a quoted date in the international standard form
(ISO 8601), such as `'2030-01-01'` or `'2030-01-01T06:00'`. mathspec refuses
a number compared against a `datetime`, and prints this for `snapshot >= 5`:

```text
Variable 'p': 'snapshot' is a datetime dimension, so comparing it to 5.0 compares against 1970-01-01. Quote an ISO date instead: snapshot >= '2030-01-01'.
```

mathspec suggests the rewrite: a quoted date.

Only a number or a `datetime` compares with `<`, `<=`, `>` and `>=`. A `str`
or a `bool` compares only with `==` and `!=`. A relation column has the
dtype of its target dimension, so the rule also applies to a column. For the
condition `generator < 'b9'` on a `str` dimension, mathspec prints:

```text
Variable 'p': 'generator' has dtype 'str', on which < is not defined. Compare it with == or !=, or precompute the comparison as a boolean parameter.
```

mathspec suggests two rewrites: `==` or `!=`, or a boolean parameter.

With data attached, a label that no coordinate has compares equal to nothing. At load,
mathspec refuses a label outside the [`one_of`](dimensions.md#one_of) list of a
dimension.

mathspec refuses a comparison of two dimensions, and prints this message for
`generator == bp`:

```text
Variable 'p': 'generator == bp' compares against dimension 'bp', and two dimensions cannot be compared. If 'bp' is a coordinate, rename the dimension or the coordinate.
```

The rewrite that mathspec suggests is for a `bp` that is meant as a label. A test that
relates two dimensions is a `bool` parameter over both, which you compute in
data preparation.

### Arithmetic in a comparison

Either side of a comparison may be an expression over parameters, such as
`p_min <= 0.5 * p_max` or `p_max <= at(bus_cap, by=bus_of[bus])`. With macros
and named expressions included, mathspec reads such a side as it reads an
[expression](#the-arithmetic-grammar). A relation column and a quoted label
are compared on their own, and never take part in arithmetic.

A variable and a `dual()` are refused in a comparison, because a condition
depends on data alone. mathspec prints this message for `shed > ramp`, with
`shed` a variable:

```text
Constraint 'shed_when_load_jumps': a condition compares expressions, and one side names a variable. Test only parameters and dimension coordinates.
```

mathspec suggests the rewrite: test only parameters and coordinates.

In the spec below, the condition compares `load` with its value at the previous snapshot. The
`shift` has `edge=0`, and a `position()` test leaves out the first snapshot:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
parameters:
  load: { dims: [snapshot] }
  ramp: { dims: [] }
variables:
  shed: { dims: [snapshot], bounds: { lower: 0 } }
constraints:
  shed_when_load_jumps:
    dims: [snapshot]
    where: "load - shift(load, along=snapshot, offset=1, edge=0) > ramp AND position(snapshot) > 0"
    expression: shed >= load - ramp
```

```math
\mathit{shed}_{t} \ge \mathrm{load}_{t} - \mathrm{ramp} \qquad \forall\, t \in \mathcal{T} \,:\, \mathrm{load}_{t} - \mathrm{load}_{t \boxminus_{0} 1} > \mathrm{ramp} \wedge \mathrm{pos}(t) > 0
```

<figure class="diagram">
--8<-- "docs/static/expressions-arithmetic.svg"
</figure>

With the data in the figure, the shift with `edge=0` is `0` at the first
snapshot, so the left side has a value everywhere. The jump at snapshot
`1` is the whole load, and the `position()` test removes that row. The jump at
snapshot `3` is `5`, below `ramp`, so `shed_when_load_jumps` has one row, at
snapshot `2`.

A comparison with a number on both sides is refused everywhere, and mathspec
prints this message for `2 < 1`:

```text
Variable 'p': '2 < 1' compares two numbers. Name the parameter one side stands for, or remove the comparison.
```

mathspec suggests two rewrites: a parameter in place of one number, or no
comparison.

!!! info "See also"

    - [`cases`](named.md#cases), for where a case `when:` may compare two
      expressions.

### `position()`

`position(dim)` returns the place of a coordinate along the order that `shift`
steps along. It does not read the label, and counts places. So, whatever
its label, the first snapshot is `position(snapshot) == 0`, and not
`snapshot == 0`:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
parameters:
  soc_initial: { dims: [] }
variables:
  soc: { dims: [snapshot], bounds: { lower: 0 } }
constraints:
  soc_start:
    dims: [snapshot]
    where: "position(snapshot) == 0"
    expression: soc == soc_initial
```

```math
\mathit{soc}_{t} = \mathrm{soc}^{\mathrm{initial}} \qquad \forall\, t \in \mathcal{T} \,:\, \mathrm{pos}(t) = 0
```

The constraint has one row, at the first snapshot. When the data is
attached, a tool refuses a position that no coordinate occupies, such as
`position(snapshot) == 10` over five snapshots.

`within=` counts the position inside each group that a
[partition](relations.md#partitions) makes. In the spec below, each period has
one starting row:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  period: { dtype: int }
relations:
  period_of: { key: snapshot, values: period }
parameters:
  soc_initial: { dims: [period] }
variables:
  soc: { dims: [snapshot], bounds: { lower: 0 } }
constraints:
  soc_start:
    dims: [snapshot]
    where: "position(snapshot, within=period_of[period]) == 0"
    expression: soc == at(soc_initial, by=period_of[period])
```

```math
\mathit{soc}_{t} = \mathrm{soc}^{\mathrm{initial}}_{\mathrm{period\_of}(t)} \qquad \forall\, t \in \mathcal{T} \,:\, \mathrm{pos}_{\mathrm{period\_of}(t)}(t) = 0
```

<figure class="diagram">
--8<-- "docs/static/expressions-position.svg"
</figure>

With the data in the figure, `soc_start` has rows at snapshots `1` and `3`,
which are the first snapshots of the two periods. Through `period_of`, each row uses the
starting value of its period.

!!! info "See also"

    - [absence](absence.md) for what a `where:` leaves absent
    - [named conditions](named.md#conditions) for a condition you name once and
      use in several places
    - [`ordered`](dimensions.md#ordered) for the dimensions that `position()`,
      `shift` and `sum_back` need to be ordered
