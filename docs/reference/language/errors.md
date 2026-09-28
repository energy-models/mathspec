<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Errors and limits

## What `to_spec` checks

`to_spec` attaches no data. Before it returns a `Spec`, it parses the file,
resolves every name, checks every dimension rule and every degree, and reads
every `where` string and every macro template, including the templates that
nothing calls. A `piecewise:` block is checked against every rule its expansion
would be held to. Anything the language refuses is refused there.

Every message names what went wrong and what to do about it:

```text
Constraint 'balance', equation 0: 'p_charge' not found.
  Variables: ['dispatch', 'soc']
  Parameters: ['capacity', 'load', 'efficiency']
Check for typos, or ensure 'p_charge' is declared.
```

## What `advice` warns about

`ms.advice(spec)` returns a tuple of `ms.Advice`, one per warning, and
`python -m mathspec check spec.yaml` prints them. Advice is a warning: the file
loads.

| `kind`          | The file has…                                                                                                     | The advice says…                                                      |
| --------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `never-an-axis` | a dimension nothing is indexed by, nothing aggregates into and no relation targets                                | remove it, or keep it knowingly if its declarations are still to come |
| `given`         | a parameter, column, named expression or row family it reads and does not build ([given](declarations.md#given))  | the model this one is layered onto provides it                        |
| `unbounded`     | a variable that no constraint, set or curve uses, whose objective term pushes it towards a bound it does not have | give it a finite bound, or the constraint that was meant to define it |
| `convexity`     | a quadratic objective or row that is convex only if a parameter has a sign that no assumption states              | the assumption to state, with the sign that proves it convex          |

```text
Variable 'slack' makes this spec unbounded: no constraint names it, and
bounds.lower is open, which is the direction a +slack term improves a minimize
objective in. No data can change that, so the solve would answer `unbounded`
and name nothing.
Give it a finite bounds.lower, or the constraint that was meant to define it.
```

A `convexity` note names every parameter in the declaration whose sign no
assumption states, and one assumption that states all of their signs:

```text
The objective is convex for all data once 'cost' is never negative, and no
assumption states that, so only the data decides now.
State it: an assumptions: entry with no where: that holds "cost >= 0".
```

A spec that states that assumption is convex for all data that passes it, and
it gets no note. There is no note for a declaration that is
[nonconvex](../reading.md#asking-what-kind-of-problem-it-is), because a
nonconvex model can be intended. There is also no note where a stated sign
cannot decide convexity, such as for a product of two different variables.

`advice` is silent where the answer depends on the data: an objective
coefficient that is a parameter, or a `where:` that leaves one slice of a
variable with no constraint row.

## Which error you get

| Class            | Subclass of     |                                                                                                                                 |
| ---------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `MathSpecError`  | `ValueError`    | The root                                                                                                                        |
| `LanguageError`  | `MathSpecError` | Something in the spec: a construct outside the language, a dimension set that does not compose, or a name that nothing declares |
| `SchemaError`    | `LanguageError` | Something in the file: an unknown key, a malformed declaration, or a bad symbol table                                           |
| `DimensionError` | `LanguageError` | Dimensions that disagree, such as a constraint whose expression does not equal its `dims`                                       |

Every one of these is reproducible from the YAML alone.

## What the language will not express

What the language refuses, and what to write instead, is in
[the limits](../../about/limits.md#deliberate-non-primitives).
