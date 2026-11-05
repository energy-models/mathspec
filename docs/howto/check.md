<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Check a spec without data

This guide shows how to find the faults in a specification file
([spec](../reference/glossary.md#spec)) before you attach data or call a
solver. You need mathspec [installed](installation.md) and a spec file, here
`spec.yaml`.

## Check one file

Run the check on the file:

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

When mathspec accepts the file and has no remark that is not a refusal
([advice](../reference/glossary.md#advice)), the command and the Python loop
print nothing. The command then exits with status 0.

## Read a refusal

When mathspec refuses the file while reading it
([at load](../reference/glossary.md#load)), the command exits with status 1
and prints the message on standard error (stderr). In Python,
[`advice`](../reference/api.md#advice) and
[`to_spec`](../reference/api.md#mathspec.to_spec) raise a
[`mathspec.errors.MathSpecError`](../reference/api.md#errors) with the same
message. Here a variable entry has `boundz` in place of `bounds`:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
variables:
  dispatch:
    dims: [snapshot, generator]
    boundz: { lower: 0, upper: capacity }
```

```text
variables.dispatch: unknown key 'boundz' in a variable entry. Did you mean 'bounds'?
```

mathspec names the entry and the fault and suggests the rewrite, so fix the
file and run the check again.

## Read the advice

When mathspec accepts the file but finds a possible mistake, the command exits with status 0
and prints advice on standard output (stdout). Here the variable `slack` appears in a
minimised objective, and no constraint or bound limits `slack`:

```yaml
dimensions:
  snapshot: { dtype: int }
variables:
  x: { dims: [snapshot], bounds: { lower: 0 } }
  slack: { dims: [] }
objective:
  sense: minimize
  expression: sum(x) + slack
```

```text
Variable 'slack' makes this spec unbounded: no constraint names it, and bounds.lower is open, and the +slack term in the minimize objective improves toward it.
Give it a finite bounds.lower, or the constraint that was meant to define it.
```

mathspec names the variable and suggests the rewrite, which here is a lower
bound on `slack`.

## Check every spec in CI

A shell loop fails a continuous integration (CI) job at the first refused
file:

```bash
for spec in specs/*.yaml; do python -m mathspec check "$spec" || exit 1; done
```

The job passes when mathspec accepts every file, with or without advice.

## Check a file without mathspec installed

Where mathspec is not installed, check a file against the format description of the keys
([the schema](installation.md#set-up-editor-completion)) with a
command-line JSON Schema checker
([check-jsonschema](https://github.com/python-jsonschema/check-jsonschema)).
Run it in a CI job, or in a script that git runs before each commit (a
pre-commit hook):

```bash
uvx check-jsonschema --schemafile https://raw.githubusercontent.com/energy-models/mathspec/v{{ mathspec.release }}/schema/mathspec.schema.json spec.yaml
```

For a file that matches the schema, `check-jsonschema` exits with status 0 and prints `ok -- validation done`. For the `boundz` file above,
`check-jsonschema` exits with status 1 and names the path of the faulty entry,
`$.variables.dispatch`.

The schema covers only the keys of the file and the type of each value. It
does not cover the math inside an `expression:` or a `where:` string.

!!! info "See also"

    - [the command line reference](../reference/cli.md#check), for the output and
      exit status of `check`
    - [errors and advice](../reference/language/errors.md), for what mathspec
      refuses and what it advises about
