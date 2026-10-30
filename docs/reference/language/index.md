<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The language

A spec is one YAML file that states an optimisation problem without its data.
The file declares the dimensions that index the problem, the data the spec
expects, the decisions the solver makes, and the rules those decisions obey. The pages in this section list every key such a file
accepts, and the rules such a file must meet. The
[glossary](../glossary.md) defines each word these pages use, such as
_entry_, _coordinate_ and _absent_, in one fixed sense.

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[File shape](file.md)** lists the top-level keys of a spec file, and how mathspec reads the YAML.
- **[Given, parameters, variables, objective and constraints](parameters-variables-constraints.md)** lists the keys of the data, the decisions, the goal and the rules, and of the `given:` section.
- **[Dimensions](dimensions.md)** lists the keys of a dimension, the set of labels that entries are indexed over.
- **[Relations](relations.md)** lists the keys of a relation, a table that maps one dimension onto another, and how each operator uses a relation.
- **[Expressions](expressions.md)** defines the grammar of arithmetic and of conditions, and how dimensions combine.
- **[Named expressions, conditions and macros](named.md)** lists the keys of the three kinds of named piece of an expression.
- **[Operators](operators.md)** lists every operator, such as `sum` and `shift`, and the math each one prints.
- **[Piecewise curves and SOS](piecewise.md)** lists the keys of a piecewise-linear curve and of a special ordered set (SOS).
- **[Assumptions](assumptions.md)** lists the keys that state what a spec expects of its data.
- **[Absence and where](absence.md)** describes which rows do not exist, and how absence spreads through an expression.
- **[Errors and advice](errors.md)** lists what mathspec refuses at load, and what it advises without refusing.

</div>

## A whole spec

The file below is a complete spec, which states the least-cost dispatch of a
fleet of generators against an hourly load.

```yaml title="dispatch.yaml"
description: Least-cost dispatch of a generator fleet against an hourly load.

dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }

parameters:
  load: { dims: [snapshot] }
  cost: { dims: [generator] }
  capacity: { dims: [generator] }

variables:
  dispatch:
    dims: [snapshot, generator]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }

constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

`python -m mathspec markdown dispatch.yaml --no-legend` prints the math that
the file states. It prints one heading for the variable domains, one for the
objective and one for the constraints, and under them these three equations:

```math
0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{capacity}_{g} > 0
```

```math
\min \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
```

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

The variable `dispatch` exists only where `capacity > 0`, and the objective
sums over both dimensions. `power_balance` has one row per snapshot, because
the sum removes `generator`.

## The eleven rules

A file obeys these eleven rules. Where a rule needs no data, mathspec refuses
the file when [`to_spec`](../api.md#mathspec.to_spec) reads it, before any data
exists ([at load](../glossary.md#load)). In the message, mathspec suggests the
rewrite.

| #   | Rule                                                                                                                                                                                                                          | Stated in full                                                            |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 1   | A file has thirteen section keys, plus `version` and `description`. mathspec refuses an unknown key, and suggests the nearest valid key.                                                                                      | [File shape](file.md)                                                     |
| 2   | `to_spec` checks at load every rule that needs no data.                                                                                                                                                                       | [Errors and advice](errors.md)                                            |
| 3   | Every name is declared once. mathspec refuses a parameter and a dimension that are both called `snapshot`.                                                                                                                    | [Names](expressions.md#name-resolution)                                   |
| 4   | The kind of a name sets where the name may appear. A dimension follows `over=` or `along=`, and is never multiplied.                                                                                                          | [Names](expressions.md#name-resolution)                                   |
| 5   | `a + b` is over the dimensions of `a` and of `b` together. The expression of a constraint is over exactly its `dims`, and the objective is over none.                                                                         | [How dimensions combine](expressions.md#how-dimensions-combine)           |
| 6   | At the coordinates it excludes, a `where:` on a variable makes the variable absent. A `where:` on a constraint makes the row absent.                                                                                          | [Absence](absence.md)                                                     |
| 7   | A row that uses an absent variable is absent. Inside a `sum`, an absent term is left out, and the row stays.                                                                                                                  | [Absence](absence.md#how-absence-travels)                                 |
| 8   | A tool refuses a row missing from a data table, unless the `missing:` of the entry sets the row to absent, neutral, or a value.                                                                                               | [Absence](absence.md#what-creates-absence)                                |
| 9   | Two variables may be multiplied in the objective and in a constraint, up to degree two, and not in a bound or a `piecewise:` link. `x / y` and `a ** b` need their divisor, their base and their exponent free of variables.  | [Expressions](expressions.md#where-a-product-of-two-variables-is-allowed) |
| 10  | The operators are `sum`, `sum_back`, `at` and `shift`. A file cannot add an operator.                                                                                                                                         | [Operators](operators.md)                                                 |
| 11  | A construct that steps or counts along a dimension needs the dimension declared `ordered: true`. These are `shift` in an expression or a condition, `sum_back`, `position`, `piecewise` with `over:`, and `sos` of `type: 2`. | [`ordered`](dimensions.md#ordered)                                        |

!!! info "See also"

    - [errors and advice](errors.md) for the refusals these rules produce
    - [the limits of the language](../../about/limits.md) for what a file cannot
      state, and why
