<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Errors and limits

`to_spec` refuses a broken file before you attach data, and `advice` warns
about a file that loads but looks wrong.

## What `to_spec` checks

`to_spec` attaches no data. Before it returns a `Spec`, it parses the file,
resolves every name, checks every dimension rule and every degree, and reads
every `where` string and every macro template, including the templates that
nothing calls. A `piecewise:` block is checked against every rule its expansion
would be held to. Everything the language refuses, `to_spec` refuses there.

Every message names what went wrong and what to do about it:

```text
Constraint 'balance': 'p_charge' not found.
  Variables: ['dispatch', 'soc']
  Parameters: ['capacity', 'efficiency', 'load']
Check the spelling, or declare 'p_charge'.
```

## What `advice` warns about

`ms.advice(spec)` returns a tuple of `ms.Advice`, one per warning, and
`python -m mathspec check spec.yaml` prints them. Advice is only a warning, so the
file still loads.

| `kind`          | The file has…                                                                                                     | The advice says…                                                      |
| --------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `never-an-axis` | a dimension nothing is indexed by, nothing aggregates into and no relation targets                                | remove it, or keep it knowingly if its declarations are still to come |
| `given`         | a parameter, column, named expression or row family it reads and does not build ([given](declarations.md#given))  | the model this one is layered onto provides it                        |
| `unbounded`     | a variable that no constraint, set or curve uses, whose objective term pushes it towards a bound it does not have | give it a finite bound, or the constraint that was meant to define it |

```text
Variable 'slack' makes this spec unbounded: no constraint names it, and
bounds.lower is open, and the +slack term in the minimize objective improves
toward it.
Give it a finite bounds.lower, or the constraint that was meant to define it.
```

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

You can reproduce each of these errors from the YAML alone.

## What the language will not express

[The limits](../../about/limits.md#requests-the-language-refuses) list what the
language refuses, and what to write instead.
