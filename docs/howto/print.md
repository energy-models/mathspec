<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Print a spec as math

This guide shows how to turn a specification file
([spec](../reference/glossary.md#spec)) into the math of a paper or a report, and keep the printed math current. You need mathspec [installed](installation.md) and a spec file that loads. The
examples use this least-cost dispatch spec, saved as `spec.yaml`:

```yaml title="spec.yaml"
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
  cost: { dims: [generator] }
  load: { dims: [snapshot] }
variables:
  dispatch: { dims: [snapshot, generator], bounds: { lower: 0, upper: capacity } }
constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load
objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

## Print the math

Print the spec as Markdown:

=== "Command line"

    ```bash
    python -m mathspec markdown spec.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    print(ms.to_markdown('spec.yaml'))
    ```

The output starts with three tables of symbols, for the sets, the parameters
and the variables. The bounds of each variable, the objective and the
constraints follow, with one equation each. The command and the Python call
print the power balance as:

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

Without a file that maps names to symbols
([a symbol table](../reference/typeset.md#symbol-tables)), mathspec picks the
symbols itself. It prints the name `load` as $\mathrm{load}$ and gives
`snapshot` the index $t$.

Keep this Python session open, because later steps use `ms`.

## Give the symbols your field's spelling

Write a symbol table beside the spec, as `spec.symbols.yaml`:

```yaml title="spec.symbols.yaml"
notation: latex

dimensions:
  snapshot: { index: s, set: "\\mathcal{S}" }
  generator: { index: g, set: "\\mathcal{G}" }

names:
  cost: c
  load: "\\ell"
  capacity: "\\bar p"
```

Pass the table with `--symbols`, or `symbols=` in Python:

=== "Command line"

    ```bash
    python -m mathspec markdown spec.yaml --symbols spec.symbols.yaml
    ```

=== "Python"

    ```python
    print(ms.to_markdown('spec.yaml', symbols='spec.symbols.yaml'))
    ```

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{s,g} = \ell_{s} \qquad \forall\, s \in \mathcal{S}
```

The power balance now has $\ell$ for `load` and $s$ for `snapshot`.

When a key in the table matches nothing in the spec, such as `demand: "\\ell"`
under `names:`, mathspec refuses the table. The command stops with a
traceback, and `to_markdown` raises a `SchemaError`. The last line of the traceback is the message, which lists the
names that the spec declares:

```text
mathspec.errors.SchemaError: symbol table: 'demand' under names: is not declared by the spec. Declared: capacity, cost, dispatch, load, power_balance.
```

## Print for Typst

To print for a typesetting system ([Typst](https://typst.app)), write a
[symbol table](../reference/typeset.md#symbol-tables) with `notation: typst`.
Given the LaTeX table above, mathspec refuses to print Typst:

=== "Command line"

    ```bash
    python -m mathspec typst spec.yaml --symbols spec.symbols.yaml
    ```

=== "Python"

    ```python
    ms.to_typst('spec.yaml', symbols='spec.symbols.yaml')
    ```

```text
mathspec.errors.SchemaError: symbol table: written in latex, but this render is typst. Write a typst table.
```

mathspec suggests the rewrite: a second table with `notation: typst`.

## Set a symbol for a name that only an expansion adds

When mathspec writes a curve out as plain entries
([an expansion](../reference/glossary.md#expansion)), it adds names that the
file does not declare. A symbol table may also set a symbol for such a name.
Here `curve.yaml` states a cost curve over the dimension `bp`:

```yaml title="curve.yaml"
dimensions:
  bp: { dtype: int, ordered: true }
parameters:
  power_bp: { dims: [bp] }
  cost_bp: { dims: [bp] }
variables:
  power: { dims: [], bounds: { lower: 0 } }
  cost: { dims: [], bounds: { lower: 0 } }
piecewise:
  cost_curve:
    over: bp
    links:
      - [power, power_bp]
      - [cost, cost_bp]
objective:
  sense: minimize
  expression: cost
```

When mathspec expands `cost_curve`
([`piecewise`](../reference/language/piecewise.md)), it adds one weight per
breakpoint of the curve, as the variable `cost_curve_lam`.
Set its symbol in a table, and print the expansion:

```yaml title="curve.symbols.yaml"
notation: latex
dimensions:
  bp: { index: k }
names:
  cost_curve_lam: "\\lambda"
```

=== "Command line"

    ```bash
    python -m mathspec markdown curve.yaml --expand --symbols curve.symbols.yaml
    ```

=== "Python"

    ```python
    print(ms.to_markdown(ms.to_spec('curve.yaml').expand(), symbols='curve.symbols.yaml'))
    ```

The command and the Python call print the weights as $\lambda_{k}$. Without the expansion, mathspec
accepts the same table and prints the curve as one line.

## Write a document that compiles

Write the spec as a whole LaTeX or Typst document, with a preamble that wraps
the equations:

=== "Command line"

    ```bash
    python -m mathspec latex spec.yaml --symbols spec.symbols.yaml --standalone -o spec.tex
    python -m mathspec typst spec.yaml --standalone -o spec.typ
    ```

=== "Python"

    ```python
    from pathlib import Path

    Path('spec.tex').write_text(ms.to_latex('spec.yaml', symbols='spec.symbols.yaml', standalone=True))
    Path('spec.typ').write_text(ms.to_typst('spec.yaml', standalone=True))
    ```

The commands and the Python code write `spec.tex` and `spec.typ`, each a document that compiles on its
own. Compile `spec.tex` with a LaTeX compiler
([tectonic](https://tectonic-typesetting.github.io)), as `tectonic spec.tex`,
or `spec.typ` with `typst compile spec.typ`. Each command writes `spec.pdf`.

To put the math inside a paper, a report or documentation instead, leave out
the preamble. Without `--standalone`, or with `standalone=False`, you `\input`
the output into a LaTeX document or `#include` it into a Typst one. For
documentation written in Markdown, write the Markdown output to a file that a
page of the documentation includes.

## Keep the document current

Run the command of [write a document that compiles](#write-a-document-that-compiles)
again before you build a documentation site.

Where make or another build system writes the document, add a rule so that
mathspec prints the math whenever the spec or the table changes. In a
Makefile, write the rule:

```make
spec.tex: spec.yaml spec.symbols.yaml
	python -m mathspec latex $< --symbols spec.symbols.yaml --standalone -o $@
```

`make spec.tex` now writes the document again whenever either file is newer
than `spec.tex`.

!!! info "See also"

    - [typeset output](../reference/typeset.md), for every option and every key
      mathspec accepts in a symbol table
    - [the command line reference](../reference/cli.md#latex-markdown-and-typst),
      for the flags of each typeset command
