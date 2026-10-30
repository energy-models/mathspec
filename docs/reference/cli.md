<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Command line

mathspec runs from a shell as `python -m mathspec`, followed by a command and
the path to the specification of an optimisation model
([a spec](glossary.md#spec)). This page lists every command, its arguments and
flags, and its exit status. The page also lists what each command writes to the
standard output (stdout) and the error output (stderr). `python -m mathspec
--help` lists the six commands:

```text
usage: python -m mathspec [-h] {check,canonical,diff,latex,markdown,typst} ...
```

| Command     | What it does                                                                                         |
| ----------- | ---------------------------------------------------------------------------------------------------- |
| `check`     | loads a spec, and prints what mathspec reports without refusing ([advice](glossary.md#advice))       |
| `canonical` | writes a spec in the layout equal specs share ([the canonical form](reading.md#comparing-two-specs)) |
| `diff`      | prints where two specs differ in the canonical form                                                  |
| `latex`     | prints a spec as LaTeX equations                                                                     |
| `markdown`  | prints a spec as Markdown equations                                                                  |
| `typst`     | prints a spec as equations in a typesetting language without TeX (Typst)                             |

Every command reads the file as written, and reads no data.

`-h` or `--help` after a command prints the usage of that command.

For an unknown command, or a missing argument, `python -m mathspec` prints the
usage on stderr and exits with status 2.

## `check`

`check` loads a spec with [`to_spec`](api.md#mathspec.to_spec) and prints its
[advice](glossary.md#advice). `check` attaches no data, so `check` reports
nothing that depends on data. `check` takes one path:

```text
usage: python -m mathspec check [-h] spec
```

| Argument | What it is                   |
| -------- | ---------------------------- |
| `spec`   | path to a mathspec YAML file |

| Result                        | stdout                                  | stderr              | Exit status |
| ----------------------------- | --------------------------------------- | ------------------- | ----------- |
| the spec loads with no advice | nothing                                 | nothing             | 0           |
| the spec loads with advice    | each piece of advice, one after another | nothing             | 0           |
| mathspec refuses the file     | nothing                                 | the refusal message | 1           |

Here `slack.yaml` declares a variable `slack` that appears in no constraint,
has no lower bound, and enters an objective that is minimised:

```yaml title="slack.yaml"
dimensions:
  snapshot: { dtype: int }
parameters:
  load: { dims: [snapshot] }
variables:
  supply: { dims: [snapshot], bounds: { lower: 0 } }
  slack: { dims: [snapshot] }
constraints:
  balance:
    dims: [snapshot]
    expression: supply >= load
objective:
  sense: minimize
  expression: sum(supply + slack)
```

=== "Command line"

    ```bash
    python -m mathspec check slack.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    for advice in ms.advice('slack.yaml'):
        print(advice)
    ```

The command and the call print the same advice:

```text
Variable 'slack' makes this spec unbounded: no constraint names it, and bounds.lower is open, and the +slack term in the minimize objective improves toward it.
Give it a finite bounds.lower, or the constraint that was meant to define it.
```

The advice states the variable, why the spec is unbounded, and two rewrites.
Advice is not a refusal, so `check` succeeds.

For a file with a misspelt key, `check` prints the refusal on stderr, and
mathspec suggests the closest key:

```text
variables.x: unknown key 'boundz' in a variable entry. Did you mean 'bounds'?
```

## `canonical`

`canonical` loads a spec and writes it in the
[canonical form](reading.md#comparing-two-specs). `canonical` writes the same
text for two files that differ only in the order of their entries, or of the
parts of a sum. In Python,
[`spec.to_yaml(canonical=True)`](spec.md#mathspec.spec.Spec.to_yaml) returns
the text that `canonical` writes. `canonical` takes one path, and an optional
output file:

```text
usage: python -m mathspec canonical [-h] [-o OUT] spec
```

| Argument or flag | What it is                          | Default |
| ---------------- | ----------------------------------- | ------- |
| `spec`           | path to a mathspec YAML file        |         |
| `-o`, `--out`    | path of a file to write the form to | stdout  |

| Result                    | stdout                                   | stderr              | Exit status |
| ------------------------- | ---------------------------------------- | ------------------- | ----------- |
| the spec loads            | the canonical form, unless `-o` is given | nothing             | 0           |
| mathspec refuses the file | nothing                                  | the refusal message | 1           |

`-o` overwrites its file.

## `diff`

`diff` writes two specs in the canonical form and prints the lines that
differ, in the format of `diff -u` (a unified diff). For two files that exist,
`diff` keeps the exit statuses of the `diff` program. So a script or a
continuous integration (CI) job tests the exit status as it tests that of
`diff`. `diff` takes two paths:

```text
usage: python -m mathspec diff [-h] before after
```

| Argument | What it is                   |
| -------- | ---------------------------- |
| `before` | path to a mathspec YAML file |
| `after`  | path to a mathspec YAML file |

| Result                       | stdout                                | stderr              | Exit status |
| ---------------------------- | ------------------------------------- | ------------------- | ----------- |
| the two specs are the same   | nothing                               | nothing             | 0           |
| the two specs differ         | a unified diff of the canonical forms | nothing             | 1           |
| mathspec refuses either file | nothing                               | the refusal message | 2           |

Here `before.yaml` is `base.yaml` from [composing
specs](composition.md#override), the spec an override extends
([a base](glossary.md#base)). `after.yaml` is the same file with a description
on the parameter `cost`:

```bash
python -m mathspec diff before.yaml after.yaml
```

```diff
--- before.yaml
+++ after.yaml
@@ -4,7 +4,10 @@
   snapshot: {dtype: int}
 parameters:
   capacity: {dims: [generator], dtype: float}
-  cost: {dims: [generator], dtype: float}
+  cost:
+    dims: [generator]
+    dtype: float
+    description: what a unit costs
   load: {dims: [snapshot], dtype: float}
 variables:
   dispatch:
```

Only `cost` changes. `canonical` writes `dtype: float` on every
parameter, so `dtype: float` appears on both sides.

## `latex`, `markdown` and `typst`

Each typeset command prints a spec as equations in one format. The three
commands take the same flags, and each flag except `-o` and `--expand` matches
a keyword of [`to_latex`, `to_typst` and `to_markdown`](typeset.md):

```text
usage: python -m mathspec latex [-h] [-o OUT] [--symbols SYMBOLS]
                                [--standalone] [--no-legend] [--no-numbers]
                                [--inline-expressions] [--expand]
                                spec
```

| Argument or flag       | Python keyword            | What it does                                                                                                             | Default                               |
| ---------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- |
| `spec`                 | `spec`                    | reads the spec from this path                                                                                            |                                       |
| `-o`, `--out`          | none                      | writes the document to this file instead of stdout                                                                       | stdout                                |
| `--symbols`            | `symbols`                 | reads how each name prints ([a symbol table](typeset.md#symbol-tables)) from this YAML file                              | symbols derived from the names        |
| `--standalone`         | `standalone=True`         | prints a document that compiles on its own                                                                               | a document to include in a larger one |
| `--no-legend`          | `legend=False`            | leaves out the tables of symbols and notation                                                                            | the legend printed                    |
| `--no-numbers`         | `numbered=False`          | leaves the equations unnumbered                                                                                          | the equations numbered                |
| `--inline-expressions` | `inline_expressions=True` | substitutes each named expression without cases into every equation that uses it, instead of defining it once            | each named expression defined once    |
| `--expand`             | none                      | prints the variables, constraints and assumptions that the `piecewise:` and `sos:` entries state, instead of the entries | the entries as written                |

[`spec.expand()`](spec.md#mathspec.spec.Spec.expand) returns the spec that
`--expand` prints.

| Result                    | stdout                             | stderr                                                                    | Exit status |
| ------------------------- | ---------------------------------- | ------------------------------------------------------------------------- | ----------- |
| the spec loads            | the document, unless `-o` is given | nothing                                                                   | 0           |
| mathspec refuses the file | nothing                            | a Python traceback that ends with the error class and the refusal message | 1           |

Here the base prints without its legend:

=== "Command line"

    ```bash
    python -m mathspec latex before.yaml --no-legend
    ```

=== "Python"

    ```python
    import mathspec as ms

    print(ms.to_latex('before.yaml', legend=False))
    ```

```text
\paragraph{Variable domains}
\begin{align}
\text{dispatch} && 0 \le \mathit{dispatch}_{t,g} & \le \mathrm{capacity}_{g} && \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
\end{align}

\paragraph{Objective}
\begin{align}
 && \min & \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
\end{align}

\paragraph{Subject to}
\begin{align}
\text{power\_balance} && \sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} & = \mathrm{load}_{t} && \forall\, t \in \mathcal{T}
\end{align}
```

With `--no-legend`, the document starts at Variable domains and has no tables
of symbols.

## A missing file

For a `spec`, `before` or `after` path with no file, every command exits with
status 1 and prints a Python traceback on stderr. The last line of the traceback
contains the path:

```text
FileNotFoundError: no file named 'missing.yaml'. End YAML text with a newline, or pass a Path for a file.
```

!!! info "See also"

    - [Check a spec without data](../howto/check.md)
    - [Print a spec as math](../howto/print.md)
    - [Compare two specs](../howto/compare.md)
    - [Errors and advice](language/errors.md), for what mathspec refuses at load
      and what advice reports
    - [Typeset output](typeset.md), for the document each typeset command prints
