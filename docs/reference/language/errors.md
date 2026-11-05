<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Errors and advice

This page describes what mathspec prints about a spec before any data is
attached. [`to_spec`](../api.md#mathspec.to_spec) refuses a file that breaks a rule of
the language, and raises an error. [`advice`](../api.md#advice) reads a file
that loads, and returns a message about a part of the file that looks wrong
but breaks no rule (**advice**).

## What `to_spec` checks

`to_spec` attaches no data, and before it returns a `Spec`, it parses the file,
resolves every name, and checks every dimension rule. It checks how many
variables each expression multiplies together
([its degree](expressions.md#where-a-product-of-two-variables-is-allowed)), and
reads every condition. It also checks every
[macro template](named.md#macros), including the templates that nothing calls.
A `piecewise:` entry is checked against every rule that its expansion would be
held to.

In each message, mathspec names the entry, says what is wrong, and suggests what to write instead. In
the spec below, the constraint `balance` uses `p_charge`, which the file does
not declare:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
parameters:
  capacity: { dims: [] }
  efficiency: { dims: [] }
  load: { dims: [snapshot] }
variables:
  dispatch: { dims: [snapshot], bounds: { lower: 0, upper: capacity } }
  soc: { dims: [snapshot], bounds: { lower: 0 } }
constraints:
  balance:
    dims: [snapshot]
    expression: dispatch - p_charge == load
objective:
  sense: minimize
  expression: sum(dispatch, over=snapshot)
```

```text
Constraint 'balance': 'p_charge' not found.
  Variables: ['dispatch', 'soc']
  Parameters: ['capacity', 'efficiency', 'load']
Check the spelling, or declare 'p_charge'.
```

mathspec lists the variables and parameters that the file does declare, so
that you can find a misspelt name among them.

`to_spec` reads every expression and every `where:` in the file, and then
lists, one to a line, each fault it finds. In the spec below, each of two
constraints sums over a dimension over which its expression is not indexed:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  load: { dims: [snapshot] }
variables:
  p: { dims: [snapshot], bounds: { lower: 0 } }
  q: { dims: [generator], bounds: { lower: 0 } }
constraints:
  balance:
    dims: [snapshot]
    expression: sum(p, over=generator) == load
  cap:
    dims: [generator]
    expression: sum(q, over=snapshot) <= 1
objective:
  sense: minimize
  expression: sum(p)
```

`to_spec` raises a `DimensionError`, and mathspec prints both faults:

```text
Constraint 'balance': sum(over=generator) but the expression has only the dims ['snapshot']. Remove the sum, or correct the dimension.
Constraint 'cap': sum(over=snapshot) but the expression has only the dims ['generator']. Remove the sum, or correct the dimension.
```

Both faults break a dimension rule, so the error is a `DimensionError`.

In the spec
below, one constraint uses an undeclared name, and the other shifts along a
dimension that is not ordered:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str }
parameters:
  load: { dims: [snapshot] }
variables:
  p: { dims: [snapshot, generator], bounds: { lower: 0 } }
constraints:
  balance:
    dims: [snapshot]
    expression: sum(p, over=generator) == demand
  cap:
    dims: [snapshot, generator]
    expression: p <= shift(p, along=generator, offset=1, edge=0)
objective:
  sense: minimize
  expression: sum(p)
```

`to_spec` raises a `SchemaError`, and lists both faults, the undeclared name
first:

```text
Constraint 'balance': 'demand' not found.
  Variables: ['p']
  Parameters: ['load']
Check the spelling, or declare 'demand'.
Constraint 'cap': shift(along=generator) reads the order of 'generator', which is not declared ordered, so the order would come from the row order of the data. Declare 'generator: {ordered: true}' under dimensions:.
```

A name that nothing declares breaks no dimension rule, so the error is a
`SchemaError`.

When every expression loads, `to_spec` checks the rules on whole entries. One
such rule requires the expression of a constraint to be indexed over exactly
its `dims:`. For that rule, `to_spec` raises a `DimensionError` that lists only
the first entry that breaks it.

## What `advice` warns about

`mathspec.advice(spec)` returns a tuple of
[`mathspec.program.Advice`](../program.md), one per piece of advice. On the
[command line](../cli.md), `python -m mathspec check spec.yaml` prints each
one on standard output. mathspec does not refuse a file for its
advice, so the file still loads and `check` exits `0`.

| `kind`          | The file has…                                                                                                                                                         | The advice is…                                                           |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `never-an-axis` | a dimension that indexes nothing, that nothing sums into, and that no relation has a column over                                                                      | remove it, or keep it if the entries that use it are still to be written |
| `given`         | a parameter, column, named expression or set of constraint rows (a row family) that it uses and does not declare ([given](parameters-variables-constraints.md#given)) | the file this one is layered onto provides it                            |
| `unbounded`     | a variable that no constraint, set or curve uses, whose objective term pushes it towards a bound it does not have                                                     | give it a finite bound, or the constraint that was meant to define it    |

In the spec below, `region` indexes nothing, and `slack` has no lower bound
while a lower `slack` lowers the minimised objective:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  region: { dtype: str }
parameters:
  load: { dims: [snapshot] }
variables:
  p: { dims: [snapshot], bounds: { lower: 0 } }
  slack: { dims: [] }
constraints:
  balance:
    dims: [snapshot]
    expression: p == load
objective:
  sense: minimize
  expression: sum(p, over=snapshot) + slack
```

=== "Command line"

    ```bash
    python -m mathspec check spec.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    for note in ms.advice('spec.yaml'):
        print(note)
    ```

Both commands print the same two messages of advice:

```text
dimension 'region' is never used: nothing is indexed by it, nothing sums into it, and no relation has a column over it. Remove it, or keep it if the entries that use it are still to be written.
Variable 'slack' makes this spec unbounded: no constraint names it, and bounds.lower is open, and the +slack term in the minimize objective improves toward it.
Give it a finite bounds.lower, or the constraint that was meant to define it.
```

The first message is `never-an-axis` advice, and the second is `unbounded`
advice.

A spec that lists `load` under `given:` instead of `parameters:` also gets
`given` advice. Between the two messages above, mathspec then prints
this line:

```text
parameter 'load' is read here and declared elsewhere: the model this one is layered onto provides it. A tool refuses the spec where that model does not, over the same dims. merge() replaces this entry with the one another file declares.
```

In this advice, mathspec states that [`merge`](../composition.md#merge) replaces the given
entry with the entry that another file declares.

`advice` is silent where the answer depends on the data. An objective
coefficient that is a parameter can have either sign, so the spec above with
`penalty * slack` in place of `slack` gets no `unbounded` advice. A spec whose
`where:` leaves one slice of a variable with no constraint row also gets none.

## Error classes

Every error that mathspec raises is an instance of `MathSpecError`, which is a
`ValueError`. The classes are in the module
[`mathspec.errors`](../api.md#errors). An `except` clause on a class below also
catches its subclasses:

| Class            | Subclass of     | What it reports                                                                                                                                                    |
| ---------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `MathSpecError`  | `ValueError`    | Every error mathspec raises, as the root class.                                                                                                                    |
| `LanguageError`  | `MathSpecError` | Something in the spec: a construct outside the language, or a dimension set that does not compose.                                                                 |
| `SchemaError`    | `LanguageError` | Something in the file: an unknown key, a malformed entry, a name that nothing declares, or a [symbol table](../typeset.md#symbol-tables) that mathspec cannot use. |
| `DimensionError` | `LanguageError` | Dimensions that disagree, such as a constraint whose expression is not indexed over its `dims:`.                                                                   |

When `to_spec` lists several faults, the error is a `DimensionError` if every
fault breaks a dimension rule. It is a `SchemaError` if any fault is of
[another kind](#what-to_spec-checks).

!!! info "See also"

    - [The limits of the language](../../about/limits.md#what-mathspec-refuses)
      for what mathspec refuses, and what to write instead.
    - [The command line](../cli.md) for the `check` command, which prints the
      advice and the refusals of a file.
