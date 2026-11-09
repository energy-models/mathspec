<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Reading a spec and its program

mathspec gives software that reads a spec (a [tool](glossary.md#tool)) two
objects for each spec. The `Spec` contains the
file as written, and the `Program` contains what the file means. This page
describes what each object contains, and what a tool reads from it.

## `Spec` and `Program`

A `Spec` contains the [`macros:`](language/named.md#macros), the descriptions,
and each piecewise curve (a [`piecewise:`](language/piecewise.md) entry) as one
entry. In a `Program`, every macro is expanded, every name is typed, and every
operator is a node. mathspec checks how the dimensions of
[each expression combine](language/expressions.md#how-dimensions-combine) and
[where a product of variables is allowed](language/expressions.md#where-a-product-of-two-variables-is-allowed)
before it returns the program.

Each tool reads the object that contains what the tool needs. A tool that
builds a model from a spec and hands the model to a solver is an
[engine](glossary.md#tool):

| Tool                               | Reads                                       |
| ---------------------------------- | ------------------------------------------- |
| [The typesetter](typeset.md)       | `spec.program`, or a `Program` handed to it |
| [`advice`](api.md#mathspec.advice) | `spec.program`                              |
| An engine that builds rows         | the program of an expansion                 |
| A tool that rewrites files         | the `Spec`, the only object with the text   |

Neither object changes after it loads. A section of a `Spec` is a read-only
mapping, a list is a tuple, and no field can be set, so `spec.to_yaml()` writes
the file that `spec.program` comes from. To change a spec, lay a patch over it
with [`override`](api.md#mathspec.override), which loads the result as a new
spec.

At load, mathspec sorts each of these lists by name, because their order in
the file changes nothing:

- the entries of each section, and of each kind under `given:`
- each `dims:` list
- each side of a relation, with the columns of the key first
- the cases under `cases:`
- the `kwargs:` of a macro
- the labels under `one_of:`

A curve stays one entry in the program until
[`spec.expand()`](#formulations-written-out) writes the curve out as rows. So
the typesetter and `advice` read the curve as the author wrote it.

The curve below [expands](language/piecewise.md) into a weight per breakpoint,
a convexity row and one row per link:

```yaml title="curve.yaml"
dimensions:
  generator: { dtype: str }
  bp: { dtype: int, ordered: true }
parameters:
  bp_x: { dims: [generator, bp] }
  bp_y: { dims: [generator, bp] }
variables:
  p:
    dims: [generator]
    bounds: { lower: 0 }
  cost:
    dims: [generator]
    bounds: { lower: 0 }
piecewise:
  curve:
    along: bp
    dims: [generator]
    links:
      p: [p, bp_x]
      cost: [cost, bp_y, ">="]
    method: convex
assumptions:
  cost_is_never_negative:
    holds: "bp_y >= 0"
    description: a negative cost is a gain the objective would chase
constraints:
  target:
    dims: []
    expression: sum(p, over=generator) >= 100
objective:
  sense: minimize
  expression: sum(cost)
```

```python
from mathspec import to_spec

spec = to_spec('curve.yaml')
program = spec.program
sorted(program.constraints)  # ['target']
sorted(program.piecewise)  # ['curve']

rows = spec.expand('piecewise').program
sorted(rows.constraints)  # ['curve_convexity', 'curve_cost', 'curve_p', 'target']
sorted(rows.variables)  # ['cost', 'curve_lam', 'p']
```

The program of `curve.yaml` contains one constraint and one curve. The program
of its expansion contains the rows that the curve states instead: a convexity
row, a row per link, and a weight variable `curve_lam`.

mathspec builds `spec.program` when [`to_spec`](api.md#mathspec.to_spec) loads
the spec, so each time a tool reads `spec.program`, it gets the same object.

Each `piecewise:` entry is a typed curve under `program.piecewise`. Each
special ordered set (an [SOS](glossary.md#special-ordered-set-sos)) under
[`sos:`](language/piecewise.md#sos) is a set under `program.sos`. Every
parameter in the program is one that the file declares.

## Formulations written out

[`Spec.expand()`](spec.md#mathspec.spec.Spec.expand) writes each curve and
each set out as ordinary rows. An engine whose solver takes an SOS reads the program of
`spec.expand('piecewise')`. An engine whose solver takes no SOS reads the
program of `spec.expand()`.

```python
sorted(rows.piecewise)  # []
```

The program of an expansion has no `piecewise` entries.

## What the data has to satisfy

`program.assumptions` maps a name to an `Assumption`. The mapping contains each
assumption that the file declares, and each one that a curve's method
[derives](language/assumptions.md#what-a-curve-assumes).
An `Assumption` has three fields:

- `holds` is the condition that the data must meet.
- `where` is the condition that selects the coordinates where `holds` is
  checked.
- `description` is the text that a refusal ends with.

`holds` and `where` are both a [`Mask`](#nodes-and-conditions), the resolved
form of a condition. An assumption may contain a `VariableDefined`, which is
true where the variable exists, and a `ConstraintDefined`, which is true where
the constraint has a row. A tool checks such an assumption once it knows the
rows of the model, before it solves
([rows of the model](language/assumptions.md#rows-of-the-model)). [`assumption_message`](program.md#mathspec.program.assumption_message)
returns the message a tool prints for
an assumption that the data does not meet:

```python
from mathspec.program import Assumption, assumption_message

sorted(program.assumptions)  # ['cost_is_never_negative', 'curve_complete', 'curve_curvature', 'curve_increasing']
isinstance(program.assumptions['curve_increasing'], Assumption)  # True
message = assumption_message('curve_increasing', program.assumptions['curve_increasing'])
message  # "assumption 'curve_increasing' does not hold for the data attached to 'bp_x': piecewise 'curve': method: convex requires strictly increasing breakpoints in 'bp_x' along 'bp'"
written = assumption_message('cost_is_never_negative', program.assumptions['cost_is_never_negative'])
written  # "assumption 'cost_is_never_negative' does not hold for the data attached to 'bp_y': a negative cost is a gain the objective would chase"
```

The program contains the one assumption that the file declares, and three that
the `convex` method derives for the curve. In the second message, the text after
the colon is the description that the file sets.

## Missing rows

`program.parameters[name].missing` is what the file sets under
[`missing:`](language/absence.md#missing) for a missing row of that parameter.
It is
`'refused'`, `'absent'`, or the value that a tool uses for the row.
`program.relations[name].missing` is `'refused'` or `'absent'`, and
`program.relations[name].confines` is `True` where the relation confines
parameters. The program of
`spec.expand(...)` has the same `missing` values.

A [given](language/parameters-variables-constraints.md#given) parameter is a
`GivenParameter` under `program.given.parameters`, and not under
`program.parameters`. It has its `dims`, `dtype` and `description`, and no
`missing` or `where`, because both are set in the fragment that declares the
parameter.

With data attached, an engine refuses a parameter under `'refused'` that has a
missing row, and reports the coordinate. Each engine decides whether
it raises at the first gap or lists every gap.

A tool reads the value of a row in an expression, in a bound, and in a
comparison in a condition. Under `'absent'`, a tool leaves a bound open where
the parameter has no row.

`program.parameters[name].where` is a [`Mask`](#nodes-and-conditions) for the
`where:` of the parameter, or `None` when the parameter has every coordinate
of its `dims`. With data attached, an engine applies the condition before
`missing:`, as
[`where` on a parameter](language/parameters-variables-constraints.md#where)
describes. The condition contains no variable and no parameter with a `where:`
of its own. So an engine can evaluate every such condition before it reads any
parameter that has a `where:`.

`program.parameters[name].confined_by` lists the relations under `confines: true` whose
key dimensions the parameter has, by name. With data attached, an engine
refuses a row of the parameter at a key combination that one of them has no
row for, and reads the parameter as absent there. It does this before it
applies the `where:`, and so before `missing:`, as
[`confines`](language/relations.md#confines) describes. The confinement is not
part of `program.parameters[name].where`, because an engine drops a row
outside the `where:` and refuses a row outside the relation.

With data attached, an engine must refuse a divisor that is `0` in a row it
builds, and name the divisor. The same applies to a term of a sum that it
adds. The `0` can come from a missing row, from the data, or from constants
that cancel
([zero divisors in the data](language/absence.md#zero-divisors-in-the-data)).
Where a `where:`, a case or an absent variable leaves the row out, an engine
refuses nothing, because no row exists. A reported quotient is absent where its
divisor is `0`, and is not refused.

A bare parameter name in a condition is a `ParameterDefined` node. The page on
[conditions](language/expressions.md#conditions) defines where it is true.

## Nodes and conditions

The node classes in `mathspec.program` support `isinstance` tests, and their
fields are public. [`children()`](program.md#mathspec.program.children) walks
an expression node's operands, and
[`condition_children()`](program.md#mathspec.program.condition_children) walks
a condition's. [`walk()`](program.md#mathspec.program.walk) yields every node
under an expression, parents first.
[`walk_regions()`](program.md#mathspec.program.walk_regions) yields each node with the
[`cases:`](language/named.md#cases) regions that contain it, outermost first.

An `ExpressionReference` is the node for a use of an `expressions:` entry. Its
`body` is the entry's expression, the same object as
`program.expressions[name].expression`, and its value is the body's value.
`children()` steps into the body, so `walk()` continues through it.

Every expression node has `dims`, the dimensions that it is indexed over,
sorted by name. A sum has the dimensions of its operand, less the ones it sums
over. A `Join` under a sum through a relation has the dimensions of that sum.
A `Join` also opens an index per dropped column (an `Axis`). An axis is not a dimension and is not in `dims`. An
`ExpressionReference` has the dimensions of its body.

The order of `dimensions:` and the order of an entry's `dims:` do not change
a node's `dims`. An entry that declares `dims: [snapshot, generator]` has
`program.expressions[name].dims == ('generator', 'snapshot')`, and each
`ExpressionReference` to it has the same `dims`.

A `ConditionReference` is the node for a use of a `conditions:` entry. Its
`body` is the root of `program.conditions[name].condition`, and the reference
is true where the body is true. `condition_children()` steps into the body, so
`.atoms`, `.names_read` and `.dims` include the body's. An engine that builds
rows therefore needs nothing from `program.conditions`.

Every `where` arrives as a `Mask`, and `Mask(condition)` builds one from any
resolved condition. `~` negates a
`Mask`, and `&` and `|` combine two of them into a new `Mask`. mathspec simplifies a `Mask` as it
builds one, so a boolean literal is either its root or does not appear in it.
A `Region`'s `when` is a `Mask` too, and every `Mask` has five attributes:

- `.root` is the resolved condition.

- `.conjuncts` flattens the top-level chain of `AND`s, and stops at an `OR`
  or a `NOT`.
- `.names_read` is the set of entries that the condition uses.
- `.atoms` is the tuple of its leaves, without the connectives.
- `.dims` is the tuple of dimensions that the condition is indexed over,
  sorted by name.

A comparison of expressions arrives as an `ExpressionComparison`. Its two
sides are program expressions, as a constraint's are, and its `dims` are every
dimension that either side has. Its `names_read` are every parameter and
relation that the sides use, including the relation of a grouping.

A name compared against a literal is a different node. `p_max > 5` is a
`ParameterComparison` and `1 * p_max > 5` is an `ExpressionComparison`, though
both are true at the same coordinates.

A comparison on a relation column is a `RelationComparison`, and a comparison
of two relation columns is a `RelationPairComparison`. The page on [conditions](language/expressions.md#conditions) defines both,
and both are false for every operator where the relation has no row.

Three conditions contain another condition rather than an entry. A
`CountComparison` contains the condition that it counts and the dimension that
it counts away. A `TranslatedCondition` contains the condition that it
evaluates at a neighbouring coordinate. A `JoinedCondition` contains the
condition that it evaluates through a relation, and the `JoinColumns` that it
joins on and groups by.

Each of the three contains its inner condition as a `Mask`, whereas a
connective contains a bare condition. So `condition_children()` recurses through a
connective and stops at these three conditions. `.names_read` and `.dims`
include the conditions inside all three, and the relation of a
`JoinedCondition` is in its `.names_read`.

## What a program does not build

`program.given` has five groups: `parameters`, `variables`, `expressions`,
`conditions` and `constraints`. They list the names under
[`given:`](language/parameters-variables-constraints.md#given), which are the
names that the spec uses but does not build. Every other group of the program lists what a tool
builds. The five `given` groups list what the tool looks up in the model below the spec (the host model).

An expression uses a given expression as a `VariableReference` of that name.
Its declared dimensions (its [frame](glossary.md#frame)) are under `program.given.expressions`. A condition uses a given condition as a `ParameterDefined` of that name. That
`ParameterDefined` tests boolean data over the frame under
`program.given.conditions`.

An entry of `program.expressions` whose `adds_to` lists a given expression is
a named expression that the spec adds to the given expression (a
[term](glossary.md#term)). The
given expression is still a name that the program uses and does not build.

```python
layer = to_spec(
    {
        'dimensions': {'snapshot': {'dtype': 'int'}, 'bus': {'dtype': 'str'}},
        'given': {
            'variables': {'p': {'dims': ['snapshot', 'bus']}},
            'constraints': {'balance': {'dims': ['snapshot', 'bus']}},
        },
        'parameters': {'rate': {'dims': ['bus']}},
        'constraints': {'cap': {'dims': [], 'expression': 'sum(p * rate) <= 100'}},
        'expressions': {'price': {'expression': 'dual(balance)'}},
    }
).program

sorted(layer.variables)  # []
sorted(layer.given.variables)  # ['p']
layer.given.constraints['balance'].dims  # ('bus', 'snapshot')
```

A tool that builds `layer` creates no variable, and takes `p` and the rows of the constraint `balance` (a
[row family](glossary.md#given)) from the host model.

The host model provides a name when it has a column or a row family of that
name. An engine that builds a model from the program checks that the host
model provides each name on the same frame. The engine refuses the program
where the host model does not. An engine with no host model refuses a program
that has any name in these five groups.

`advice` returns one piece of advice of kind `given` for each name.

## `footprint`

`program.footprint` lists the constructs of the language that one program
uses. It covers only the rows in the program. A curve still in the program is
not a row, so its constructs count on the program of the expansion:

```python
footprint = rows.footprint

sorted(footprint.quadratic)  # []
sorted(footprint.domains)  # ['continuous']
sorted(footprint.sos_types)  # []
kinds = sorted(kind.__name__ for kind in footprint.kinds)
kinds  # ['Constant', 'Multiply', 'ParameterReference', 'Sum', 'VariableReference']
```

The expanded curve has no quadratic term, no SOS, and only continuous
variables. Every field is a set, and an empty field means that the program
does not use the construct.

Each engine decides whether its solver takes a construct. The footprint has no field for convexity.

## `separability`

For each dimension, `program.separability` states whether every row of the program fits inside one run of adjacent
coordinates along the dimension (a window).
A storage balance that uses the previous snapshot fits, and an annual
emissions cap does not. The rows of the curve sum over `bp`, which ties every coordinate of `bp`
together. Only the expanded program has that tie:

```python
program.separability['bp'].windowable  # True
rows.separability['bp'].windowable  # False
rows.separability['generator'].linking_rows  # ('target',)
rows.separability['generator'].linking_columns  # ()
tied = rows.separability['generator'].coupled["constraint 'target'"]
tied.partition(' (')[0]  # 'sums over generator'
'sum_back(window=n)' in tied  # True
```

The program with the curve as one entry can be cut along `bp`, and its
expansion cannot. Along `generator`, the constraint `target` ties every
generator together, and the report contains the change that would remove the
tie.

Every declared dimension has a report, and a coupling that a `piecewise:`
expansion introduces is listed under the entry that the expansion emits. A
report has these attributes:

- `coupled` lists each entry that ties the whole dimension together. Such an entry is a sum over the dimension in a constraint, a grouping that
  sums it away, a wrapped shift, or an `sos:` set. In brackets, each entry states the change that would remove the tie.
- `undecided` lists each `shift` or join whose reach, the number of
  coordinates that it looks across, is known only when the data is attached.
  Each is a `Reach`, with the entry, the parameter or relation that the entry
  uses, and the kind of use.
- `resolved()` is a method that takes a mapping from a parameter under `undecided` to the least of its
  values. It returns the report with each `shift` offset in the mapping folded
  into `ahead`. A reach through a
  relation stays undecided, and a name that no undecided reach uses raises
  `KeyError`.
- `restarts` lists each entry that counts a `position()` along the dimension.
- `linking_rows` lists each constraint that no single window contains.
- `linking_columns` lists each variable that the dimension does not index.
  Every window uses the column of such a variable.
- `ahead` is the number of coordinates that a window must see past its last
  row. It is `0` where every row is pointwise, and `2` for a `shift` of `-2`.
- `windowable` is false while anything is coupled or undecided.

A sum over the dimension in the objective ties nothing. The report does not
state whether the windowed answer equals the whole-horizon answer.

## `to_dict` and `to_yaml`

`spec.to_dict()` returns the spec as plain data, and `spec.to_yaml()` returns
that data as a file. Both round-trip, so `to_spec(spec.to_dict()) == spec`.

`to_yaml()` writes the fields that the file sets, and no others. A default
that the file states, such as `ordered: false`, is written back, and a default
that the file leaves out, such as `domain: continuous`, is not. For a spec that
`merge`, `override` or `expand` builds, `to_yaml()` writes the fields that the
fragments and mathspec set.

`to_yaml()` always writes `version:`, so a written file states the language
version it is read in. It leaves out a `null` and an empty section. It writes
`dims: []`, because `dims: []` declares a scalar. It also writes an empty
entry, such as `generator: {}`, because the entry still declares its name.

`to_yaml()` writes a short list on one line, such as
`dims: [generator, snapshot]`, and a short mapping of numbers and names, such
as `bounds: {lower: 0, upper: p_max}`. It writes each key of an entry with a
description or an expression on its own line, even for an expression as short
as `sum(p)`.

`to_yaml()` puts a list or a mapping on one line only when the whole line,
indent and key included, is 100 characters or fewer. It does not wrap a long
line, and it writes a multi-line expression as a block scalar (`|-`). It
writes a description of two or more sentences as a folded block (`>-`), with
one sentence on each line. A YAML parser reads the line breaks back as single
spaces. `to_yaml(canonical=True)` writes the same layout.

## Comparing two specs

`to_yaml(canonical=True)` writes the **canonical form**, which is one fixed
layout for a spec. mathspec writes the same canonical form for every file that
states the same spec, so two canonical forms differ only where the specs
differ.

```python
spec.to_yaml(canonical=True) == to_spec(spec.to_yaml(canonical=True)).to_yaml(canonical=True)  # True
```

Writing the canonical form out again gives the same text. The canonical form
has these rules:

- The sections come in one fixed order: `version`, `description`, `given`,
  `dimensions`, `relations`, `parameters`, `conditions`, `variables`,
  `expressions`, `objective`, `constraints`, `sos`, `piecewise`,
  `assumptions`, `macros`. The keys of an entry also come in one order.
- Entries are sorted by name within each section, and so is every other list
  that mathspec [sorts at load](#spec-and-program).
- A field that has its default value is left out, whether the file wrote it
  or not. `version` is the one exception, so `version: 0` stays.
- Every expression is printed from its parsed tree, so the spacing and the
  brackets are the printer's rather than the author's.
- The terms of a sum are sorted with their signs, so `y - x` is written as
  `-x + y`. The factors of a product, the keyword arguments of a call, and a
  list of names or the columns of a relation in a call, such as
  `over=[generator, snapshot]`, are sorted too.
- A sum of two or more terms is broken one term to a line, each under its
  own sign.
- A constant is never folded into another, so `2 * 3` stays `2 * 3`.
- Every condition under `where:`, `when:`, `condition:` and `holds:` is
  printed from its parsed tree too. `AND`, `OR` and `NOT` print in upper
  case, the operands of `AND` and of `OR` are sorted, and a bracket stays only
  where the grammar needs it, or around a comparison under `NOT`.
- The two sides of a comparison keep their places, in an expression and in a
  condition, so `p_max > 0` and `0 < p_max` are two texts.
- Division, exponentiation and a call's positional arguments keep the order of
  the file. So do a piecewise entry's links, because mathspec names the rows of
  each link after its position, as in `curve_link0`.

The canonical form states the same spec, but it does not load to a `Spec`
equal to the original. A reprinted expression is a different string.

A new mathspec release can change the canonical form, such as how mathspec
lays out a list. Two canonical forms are comparable only when the same release
wrote them. So a canonical form, or a hash of one, is not an identity for a
spec.
Loading a file with `to_spec` and writing it again gives the canonical form of
the installed release:

```python
to_spec('curve.yaml').to_yaml(canonical=True) == spec.to_yaml(canonical=True)  # True
```

The two canonical forms are equal.

!!! info "See also"

    - [Spec API](spec.md), for every class in a `Spec`
    - [Program API](program.md), for every class in a program
    - [`canonical`](cli.md#canonical) and [`diff`](cli.md#diff), for the canonical
      form from a shell
    - [compare two specs](../howto/compare.md), to diff two files in the canonical
      form
    - [conditions](language/expressions.md#conditions), for where each condition
      node is true
    - [what `advice` warns about](language/errors.md#what-advice-warns-about), for
      the advice of kind `given`
    - [what each tool decides for itself](../about/what-counts-as-language.md#what-each-tool-decides-for-itself),
      for the constructs an engine's solver takes
