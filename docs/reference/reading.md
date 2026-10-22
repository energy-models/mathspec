<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Reading a spec and its program

Use `Spec` and `Program` to write a tool that reads a spec, such as an engine
that builds models, a renderer or a checker.

## `Spec` and `Program`

A `Spec` holds the file as written: its `macros:`, its descriptions, and a
`piecewise:` entry as one entry. A `Program` holds what the file means:
every macro expanded, every name typed, every operator resolved to a node, and
every dimension and degree rule already checked. A curve stays one curve there
until [`spec.expand()`](#formulations-written-out) writes it out. The
[Program API](program.md) documents every class a program holds.

Each tool reads the object that holds what it needs:

| Tool                       | Reads                                       |
| -------------------------- | ------------------------------------------- |
| The typesetter             | `spec.program`, or a `Program` handed to it |
| `advice`                   | `spec.program`                              |
| An engine that builds rows | the program of an expansion                 |
| A tool that rewrites files | the `Spec`, which alone holds the text      |

The program keeps each curve as the one entry the file states, so the
typesetter and `advice` read the spec the author wrote. A program does not
hold its spec: a tool handed a bare `Program` has what the file means, not the
file.

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
    over: bp
    links:
      - [p, bp_x]
      - [cost, bp_y, ">="]
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
sorted(rows.constraints)  # ['curve_convexity', 'curve_link0', 'curve_link1', 'target']
sorted(rows.variables)  # ['cost', 'curve_lam', 'p']
```

`to_spec` takes a path, the YAML, a mapping or a `Spec`. `spec.program` is the
program built when the spec loaded, so every read of `spec.program` returns the
same object. Each `piecewise:` entry is a typed curve under
`program.piecewise`, and each `sos:` entry is a set under `program.sos`. Every
parameter the program declares is one the file declared.

## Formulations written out

A program holds each curve and each set as one entry until
[`Spec.expand()`](spec.md#mathspec.spec.Spec.expand) writes it out. An engine that
builds rows reads the program of `spec.expand('piecewise')` if it takes a set,
and the program of `spec.expand()` if it does not. The program of an expansion
holds no curve:

```python
sorted(rows.piecewise)  # []
```

## What the data has to satisfy

`program.assumptions` maps a name to an `Assumption`: each entry the file
declared, and each one a curve's method derives
([what a curve assumes](language/assumptions.md#what-a-curve-assumes)). An
`Assumption` carries `holds`, the condition it checks, the `where` it is checked under, and the
`description` that a refusal ends with. The `holds` and the `where` are
both `Mask` objects. `assumption_message` returns the message for an assumption the data
does not meet:

```python
from mathspec.program import Assumption, assumption_message

sorted(program.assumptions)  # ['cost_is_never_negative', 'curve_complete', 'curve_curvature', 'curve_increasing']
isinstance(program.assumptions['curve_increasing'], Assumption)  # True
message = assumption_message('curve_increasing', program.assumptions['curve_increasing'])
message  # "assumption 'curve_increasing' does not hold for the data attached to 'bp_x': piecewise 'curve': method: convex requires strictly increasing breakpoints in 'bp_x' along 'bp'"
written = assumption_message('cost_is_never_negative', program.assumptions['cost_is_never_negative'])
written  # "assumption 'cost_is_never_negative' does not hold for the data attached to 'bp_y': a negative cost is a gain the objective would chase"
```

`program.parameters[name].missing` says what a missing row of that parameter
means: `'refused'`, `'absent'`, or the value that the row reads as. A given
parameter is a `GivenParameter` under `program.given.parameters`, with its
`dims` and `dtype` and no `missing` or `where`, because the file that
declares the parameter says. The program of `spec.expand(...)` reports the same values.
`program.relations[name].missing` is `'refused'` or `'absent'`.

Under `'refused'`, the engine does not build the model from a table with a
missing row, and names the coordinate. Each engine decides whether it raises at
the first gap or lists them all. A value is read wherever a value is read: in an
expression, in a bound, and in a comparison in a mask. A `ParameterDefined` on
a numeric parameter asks whether the data has a row, so a value does not answer
it. A `ParameterDefined` on a `bool` parameter reads the value. Under
`'absent'`, a bound that reads a missing row leaves that side open.

`program.parameters[name].where` is the parameter's mask, or `None` where it
has every coordinate of its `dims`. The engine applies the mask first: outside
it the parameter is absent wherever it is read, and the engine drops the rows of
the data there when it attaches. Then it applies `missing:` to the coordinates
the mask keeps: a value fills a missing row there, and `'refused'` asks for a
row only there. A mask reads no variable, and no mask reads its own parameter,
so the engine can evaluate each mask from the data before it reads the
parameter
([a parameter's mask](language/parameters-variables-constraints.md#a-parameters-mask)).

An engine must refuse a divisor that is `0` in a row it builds, whatever made it
`0`: a missing row, a value or a constant
([zero divisors in the data](language/absence.md#zero-divisors-in-the-data)).

## Nodes and masks

Import the node classes from `mathspec.program` to test a node with
`isinstance` and to read its fields. `children()` walks an expression node's
operands, and `condition_children()` walks a condition's. `walk()` yields every
node under an expression, parents first, and `walk_regions()` yields each node
with the `cases:` regions it stands inside, outermost first.

An `ExpressionReference` stands where an `expressions:` entry is used. Its `body` is the
entry's expression, the same object that `program.expressions[name].expression`
holds, and its value is the body's value. `children()` steps into the body, so
a walk reads through it.

Every expression node has `dims`: the dimensions over which it is indexed,
sorted by name. A sum has the dimensions its operand has,
less the ones it sums over. A `Join` under a sum through a relation has the
dimensions of that sum. A `Join` also opens one `Axis` for each column it
drops, but an axis is not a dimension and is not in `dims`. An
`ExpressionReference` has the dimensions of its body.

A node's `dims` are always sorted by name. The order of `dimensions:` and the
order of an entry's `dims:` do not change them. An entry that declares
`dims: [snapshot, generator]` has
`program.expressions[name].dims == ('snapshot', 'generator')`, and each
`ExpressionReference` to it has `dims == ('generator', 'snapshot')`.

A `ConditionReference` stands where a `conditions:` entry is read. Its `body` is the
condition of the entry, the root of `program.conditions[name].condition`, and it is true
where the body is true. `condition_children()` steps into the body, so `.atoms`,
`.names_read` and `.dims` read through it, and an engine that builds rows needs
nothing from `program.conditions`.

Every `where` arrives as a `Mask`, whose `.root` is the resolved condition.
The mask also answers four questions:

- `.conjuncts` flattens the `AND` spine, and stops at an `OR` or a `NOT`.
- `.names_read` gives the entries the mask names.
- `.atoms` gives its leaves, with the connectives removed.
- `.dims` gives the dimensions the mask is read at.

A comparison of expressions arrives as an `ExpressionComparison`. Its two
sides are program expressions like a constraint's, and its `dims` are every
dimension either side carries. Its `names_read` are every parameter and relation
that the sides read, including the relation that a grouping reads through.

A name compared against a literal does not arrive this way. `p_max > 5` is a
`ParameterComparison` and `1 * p_max > 5` is an `ExpressionComparison`, though
both mask the same coordinates.

Three conditions read another condition rather than an entry. A
`CountComparison` carries the mask it counts and the dimension it counts away.
A `TranslatedCondition` carries the mask it reads at a neighbouring
coordinate. A `JoinedCondition` carries the mask it reads through a
relation, and the `JoinColumns` it joins on and groups by. Each holds that
mask as a `Mask`, where a connective holds a bare condition, so the walk
recurses through a connective and stops at these. `.names_read` and `.dims` see
through all three, and the relation a `JoinedCondition` reads is in its
`.names_read`.

`Mask(condition)` answers the same four questions of any resolved condition,
and `~`, `&` and `|` combine masks into a mask. A mask simplifies as it is
built, so a boolean literal is either the root of the mask or does not appear in
it. A `Region`'s `when` is a `Mask` too.

## What a program does not build

`program.given.parameters`, `program.given.variables`,
`program.given.expressions`, `program.given.conditions` and
`program.given.constraints` name what the spec reads and does not build
([given](language/parameters-variables-constraints.md#given)). Every other group tells a tool what
to build, but these five name what to look up in the host model, which is the
model that this spec is layered onto. An expression reads a given expression as
a `VariableReference` of that name, over the frame under `program.given.expressions`. A
condition reads a given condition as a `ParameterDefined` of that name, which is
boolean data over the frame under `program.given.conditions`.
An entry of `program.expressions` whose `adds_to` names a given expression is
a term this file adds to it. The name is still one that the program reads and
does not build.

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
layer.given.constraints['balance'].dims  # ('snapshot', 'bus')
```

The host model provides each name: it holds a column or a row family of that
name. An engine that builds the program checks that the host provides each name
on the same frame, and refuses the program where it does not. An engine with
no host model refuses a program that has any name in these five groups. `advice`
returns one note of kind `given` per name
([what `advice` warns about](language/errors.md#what-advice-warns-about)).

## Asking what a program uses

`program.footprint` says which of the language's constructs one program uses.
It answers only for the rows the program holds. A curve still on the program
is not a row, so its constructs count on the program of the expansion:

```python
footprint = rows.footprint

sorted(footprint.quadratic)  # []
sorted(footprint.domains)  # ['continuous']
sorted(footprint.sos_types)  # []
kinds = sorted(kind.__name__ for kind in footprint.kinds)
kinds  # ['Constant', 'Multiply', 'ParameterReference', 'Sum', 'VariableReference']
```

Every field is a set, and an empty field means the program does not use the
construct. The engine decides whether its solver takes a construct
([what counts as language](../about/what-counts-as-language.md#what-each-tool-decides-for-itself)).
The footprint does not report convexity, because convexity depends on the
numbers.

## Asking whether an axis can be cut

For each axis, `program.separability` says whether every row of the program
fits inside one window along that axis. A storage balance that reads the
previous snapshot fits, and an annual emissions cap does not. Like the
footprint, it answers for the rows the program holds. The rows of the curve sum
over `bp`, so only the expanded program shows that tie:

```python
program.separability['bp'].windowable  # True
rows.separability['bp'].windowable  # False
rows.separability['generator'].linking_rows  # ('target',)
rows.separability['generator'].linking_columns  # ()
tied = rows.separability['generator'].coupled["constraint 'target'"]
tied.partition(' (')[0]  # 'sums over generator'
'sum_back(window=n)' in tied  # True
```

Every declared axis has an entry. A coupling that a `piecewise:` expansion
introduced is named under the entry the expansion emitted.

- `coupled` names each entry that ties the whole axis together: a sum
  over the axis in a constraint, a grouping that sums the axis away, a wrapped
  shift, or a set. In brackets, each entry names the one change that would
  remove the tie.
- `undecided` lists each read whose reach only the data can decide, as a `Reach`:
  the entry, the parameter or relation it reads, and the kind of read. A
  caller that holds the data hands the smallest value of each named parameter
  to `resolved`, which returns the report with those reads decided.
- `restarts` names each entry that counts a `position()` along the axis.
- `linking_rows` names each constraint that no single window holds.
- `linking_columns` names each variable the axis does not index, whose column
  every window reads.
- `ahead` is how many coordinates a window must see past its last row: `0`
  where every row is pointwise, and `2` for a `shift` of `-2`.
- `windowable` is false while anything is coupled or undecided.

A sum over the axis in the objective ties nothing. The report says nothing
about whether the windowed answer equals the whole-horizon answer.

## Writing a spec back out

`spec.to_dict()` returns the spec as plain data, and `spec.to_yaml()` returns
that data as a file. Both round-trip, so `to_spec(spec.to_dict()) == spec`.

`to_yaml()` writes every value, so `domain: continuous` is written out. It
leaves out a `null` and an empty section, but it writes `dims: []`, because
that says the entry is a scalar.

`to_yaml()` writes a short list on one line, such as `dims: [snapshot, generator]`.
It also writes a short mapping of numbers and names on one line, such as
`bounds: {lower: 0, upper: p_max}`. An entry with a description or an
expression keeps one key on each line, even for an expression as short as
`sum(p)`. The writer puts a list or a mapping on one line only when the whole
line, indent and key included, holds 100 characters or fewer. It does not wrap a
long line, and it writes a multi-line expression as a block scalar (`|-`). It
writes a description of two
or more sentences as a folded block (`>-`) with one sentence on each line, and
YAML reads the line breaks back as single spaces. `to_yaml(canonical=True)`
writes the same layout.

## Comparing two specs

`to_yaml(canonical=True)` writes the normal form. Every file that states the
same spec gives the same normal form, so a diff of two normal forms shows only
where the specs differ.

```python
spec.to_yaml(canonical=True) == to_spec(spec.to_yaml(canonical=True)).to_yaml(canonical=True)  # True
```

- The sections come in one order, whatever order the file wrote them in:
  `version`, `description`, `given`, `dimensions`, `relations`, `parameters`,
  `conditions`, `variables`, `expressions`, `objective`, `constraints`, `sos`,
  `piecewise`, `assumptions`, `macros`. The keys of an entry also come in one
  order.
- Entries are sorted by name within each section.
- Every expression is printed from its parsed tree, so the spacing and the
  brackets are the printer's rather than the author's.
- The terms of a sum are sorted, and so are the factors of a product and the
  keyword arguments of a call. Subtraction, division, exponentiation and a
  call's positional arguments keep the order the file wrote, because moving
  those changes what the spec says.
- A sum of two or more terms is broken one term to a line, each under its
  own sign. A term that changes is then one line of a diff.
- A constant is never folded into another. `2 * 3` stays `2 * 3`, so a
  reviewer sees a changed coefficient in the diff.

Four things are left as the file wrote them: a condition in the `where`
grammar, the order of the regions under `cases:`, the order of an entry's
`dims`, and the order of a piecewise entry's links. A difference in any of them
is a difference in the text.

The normal form sorts `dimensions:`. This changes no dims of the program,
because a frame the loader derives is sorted by name.

The normal form states the same spec, but it does not load to a `Spec` equal
to the original, because a reprinted expression is a different string. Writing
the normal form out again gives the same text, as the line above shows.

`python -m mathspec canonical spec.yaml` writes it from a shell, and
`python -m mathspec diff before.yaml after.yaml` prints where two specs differ
in it. [Compare two specs](../howto/compare.md) shows how to diff two files in
this form.

A new mathspec release can change the normal form, for example how it lays out
a list. So compare two normal forms that the same mathspec wrote. Do not store
a normal form, or a hash of one, as the identity of a spec. To compare with a
file that an older mathspec wrote, load the file with `to_spec` and write its
normal form again:

```python
to_spec('curve.yaml').to_yaml(canonical=True) == spec.to_yaml(canonical=True)  # True
```
