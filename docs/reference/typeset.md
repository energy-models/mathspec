<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Typeset the math

`to_latex`, `to_typst` and `to_markdown` print a spec as LaTeX, Typst or
Markdown equations, from the file alone, without attaching data or running a
solver.

```python
import mathspec as ms

spec = ms.to_spec('spec.yaml')  # read and checked once, then printed three ways

print(ms.to_latex(spec))  # amsmath align
print(ms.to_typst(spec))  # compiles without a TeX toolchain
print(ms.to_markdown(spec))  # renders as-is on GitHub
```

Each function takes a path, the YAML, a mapping, a `Spec` or a `Program`, and
prints `spec.program` for a spec or the `Program` it was handed. A
[program](reading.md#spec-and-program) is what the file means, with every name
typed. From a shell, `python -m mathspec latex spec.yaml` prints the same, and
`typst` or `markdown` in place of `latex` picks the format.

[Print a spec as math](../howto/print.md) is the recipe, and
[every operator as math](language/operators.md#every-operator-as-math) shows
what each operator prints.

## Options

The three functions take the same keywords, and the command line spells each as
a flag. The [Python API](api.md#typesetting) gives each signature.

|                      |                        |                                                                                                                                 |
| -------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `symbols`            | `--symbols FILE`       | How the names print. See [symbol tables](#symbol-tables). Default: derived from the names in the file                           |
| `standalone`         | `--standalone`         | Emit a document that compiles. Default: a fragment to include                                                                   |
| `legend`             | `--no-legend`          | Print the table of sets, parameters, variables and definitions above the math. Default: on                                      |
| `numbered`           | `--no-numbers`         | Number the equations. Default: on                                                                                               |
| `inline_expressions` | `--inline-expressions` | Substitute each named expression that the math reads into the equations that read it, instead of defining it once. Default: off |
| —                    | `--expand`             | Print the variables and constraints the `piecewise:` and `sos:` blocks state, rather than the blocks. Default: off              |

`-o FILE` writes to a file instead of stdout.

- The spec's `description:` opens the document.
- A `piecewise:` block prints as one line, which quantifies the curve over the
  frame of the block, because the block states one curve at each coordinate of
  that frame. To print its rows, print
  [`spec.expand()`](api.md#mathspec.Spec.expand) or pass `--expand`
  ([see an expansion](../howto/see-an-expansion.md)).
- An [`assumptions:`](language/assumptions.md) entry prints under an
  **Assumptions** heading, last, beside what each curve assumes of its
  breakpoints. A spec that assumes nothing of its data prints no such
  heading.
- A [named expression](language/named.md) prints its symbol where it is used
  and its body once, under a **Definitions** heading, in declaration order. A
  `cases:` block, a [reported entry](language/named.md#reported-expressions)
  and a [term](language/declarations.md#terms) keep their definition line
  under either `inline_expressions` setting.
- Wherever the math moves an index, which every `shift` does, the document
  prints a line saying what that notation means.
- A file that does not load does not print.
- The typesetter does not break lines, so a wide equation runs off the page.

## Markdown's delimiters

`to_markdown` prints math between the two pairs GitHub and GitLab read
verbatim: ``$`…`$`` inline, and a ` ```math ` fence for a block. It never
prints `$…$` or `$$…$$`. For a renderer that reads `$…$` alone, print with
`to_latex` and write that renderer's delimiters around the result.

## Descriptions

A `description:` prints as plain text, with **one exception**: a name in
backticks, such as `` `capital_cost` ``, prints in monospace in every output
format. The typesetter escapes every other character that the output format
would read as markup. The legend prints the description of every
dimension, parameter and variable.

## Printing one declaration on its own

`typeset_declaration` returns the line that the document prints for one named
expression, constraint, assumption or variable. The line has its quantifier,
but no document, label, number or math delimiters:

```python
ms.typeset_declaration('spec.yaml', 'spend', 'latex')
# \mathit{spend}_{t} = \sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g} \qquad \forall\, t \in \mathcal{T}
ms.typeset_declaration('spec.yaml', 'balance', 'latex')
# \sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

It takes what the other functions take, plus the name, the format and an
optional `symbols` table. A Markdown line arrives without delimiters too, so put
it inside the inline pair:

```python
line = ms.typeset_declaration('spec.yaml', 'balance', 'markdown')
print(f'The balance holds: $`{line}`$')
```

A single line has no _Definitions_ section beside it, so
`typeset_declaration` substitutes each plain named expression that the line
uses. A cased expression prints as its symbol, and a second call with its
name prints its block.

`typeset_declaration` refuses a name that is none of the four kinds, and names
the closest match. It also refuses a name declared as two of them, such as a
constraint and a variable.

## Symbol tables

With no table, the symbols are **derived** from the names in the file, such as
$\mathrm{load}_t$ and $\mathrm{capacity}_g$. A symbol table replaces them with
the symbols you choose, such as $\ell$ for `load`. Pass a path to a YAML file,
the same keys as a dict, or a `ms.SymbolTable`:

```yaml
# dispatch.symbols.yaml
notation: latex
dimensions:
  snapshot: { index: s, set: "\\mathcal{S}" }
  generator: { index: g, set: "\\mathcal{G}" }
names:
  cost: c
  load: "\\ell"
  capacity: "\\bar p"
```

```python
ms.to_latex('dispatch.yaml', symbols='dispatch.symbols.yaml')
```

| Section      |                                                                                 |
| ------------ | ------------------------------------------------------------------------------- |
| `notation`   | **Required.** `latex` or `typst`: the language the entries are written in       |
| `dimensions` | For each dimension, an `index` letter and a `set` symbol. Either may be omitted |
| `names`      | For each parameter, variable or named expression, its symbol                    |

The typesetter prints each entry as you wrote it and does not translate
between notations, so `to_typst` refuses a table with `notation: latex`. A key
that names nothing in the spec, and nothing that its `piecewise:` or `sos:`
blocks expand into, is an error that names the closest match.

Nothing in a symbol table changes what the file means.
