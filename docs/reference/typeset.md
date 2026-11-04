<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Typeset output

The typesetting functions `to_latex`, `to_typst` and `to_markdown`
(the typesetter) print the specification of an optimisation model
([a spec](glossary.md#spec)) as equations. They print LaTeX, Markdown, or a
typesetting language without TeX (Typst). They read the file alone, so
they need no data and no solver. This page describes the document they print,
what each format adds to it, and the line they print for one entry.

Here `spec.yaml` declares the variable `dispatch` over `snapshot` and
`generator`, the named piece of math
([a named expression](language/named.md#expressions)) `spend` and the
constraint `balance`. `spec.yaml` also lists `Bus_injection` under the
section for names another file declares
([`given:`](language/parameters-variables-constraints.md#given)):

```yaml title="spec.yaml"
given:
  expressions:
    Bus_injection: { dims: [snapshot] }
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
parameters:
  capacity: { dims: [generator] }
  cost: { dims: [generator] }
  load: { dims: [snapshot] }
variables:
  dispatch: { dims: [snapshot, generator], bounds: { lower: 0, upper: capacity } }
expressions:
  spend:
    dims: [snapshot]
    expression: sum(dispatch * cost, over=generator)
constraints:
  balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load
objective:
  sense: minimize
  expression: sum(spend)
```

The three commands, or the three functions, print the document for this spec:

=== "Command line"

    ```bash
    python -m mathspec latex spec.yaml
    python -m mathspec typst spec.yaml
    python -m mathspec markdown spec.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    spec = ms.to_spec('spec.yaml')

    print(ms.to_latex(spec))
    print(ms.to_typst(spec))
    print(ms.to_markdown(spec))
    ```

Each command or call prints the whole document in one format.

Each function takes a path, YAML text, a mapping, a `Spec` or a `Program`.
Given a spec, each function prints what the file means once compiled
([its program](reading.md#spec-and-program)). Given a `Program`, each function
prints that program. A file that mathspec refuses before any data exists ([at
load](glossary.md#load)) does not print.

The three functions call `typeset(spec, fmt, …)`, whose `fmt` argument is
`'latex'`, `'markdown'` or `'typst'`. `typeset(spec, 'latex')` returns the same
text as `to_latex(spec)`.

## Options

The three functions take the same keywords, and the
[command line reference](cli.md#latex-markdown-and-typst) lists each keyword
with its flag and its default. The [Python API](api.md#the-typesetting-api)
lists each signature.

### Symbol tables

A **symbol table** is a mapping, usually a YAML file, that sets the symbol of
each name. With no
table, the typesetter derives each symbol from the name in the file, such as
$\mathrm{load}_t$ and $\mathrm{capacity}_g$. A table replaces those symbols
with the ones you choose, such as $\ell$ for `load`. The
`symbols` keyword takes a path to a YAML file, a dict with the keys of that
file, or a [`ms.SymbolTable`](api.md#mathspec.SymbolTable). The table
`dispatch.symbols.yaml` below is `examples/symbols/dispatch.yaml` without its
comments:

```yaml title="dispatch.symbols.yaml"
notation: latex
dimensions:
  snapshot: { index: s, set: "\\mathcal{S}" }
  generator: { index: g, set: "\\mathcal{G}" }
names:
  cost: c
  load: "\\ell"
  capacity: "\\bar p"
```

Here [`typeset_line`](#typeset_line) prints the constraint `balance` with the
table:

```python
ms.typeset_line('spec.yaml', 'balance', 'latex', symbols='dispatch.symbols.yaml')
# \sum_{g \in \mathcal{G}} \mathit{dispatch}_{s,g} = \ell_{s} \qquad \forall\, s \in \mathcal{S}
```

With the table, `snapshot` has the index $s$ and `load` the symbol $\ell$.
`dispatch` is not in the table, so `dispatch` prints with its derived symbol.

| Key          | What it sets                                                                                               |
| ------------ | ---------------------------------------------------------------------------------------------------------- |
| `notation`   | `latex` or `typst`, the notation of the symbols. Required                                                  |
| `dimensions` | an `index` letter and a `set` symbol for each dimension, both optional                                     |
| `names`      | a symbol for each parameter, variable, named expression or [named condition](language/named.md#conditions) |

The typesetter prints each symbol as you wrote it, and does not translate
between notations. So `to_typst` refuses a table with `notation: latex` and
suggests the notation to write:

```text
symbol table: written in latex, but this render is typst. Write a typst table.
```

The typesetter refuses a key that matches no name in the spec. The names
include every name that an entry adds when it expands into ordinary entries
([a formulation](glossary.md#formulation)). The typesetter suggests the
closest match:

```text
symbol table: 'costs' under names: is not declared by the spec. Did you mean 'cost'?
```

A symbol table changes only how names print, and nothing that the file means.

## The document

The document has a fixed order: the spec's `description:` opens it, the
tables of symbols (the legend) follow, and the math comes last.

- The legend has the headings Given, Sets, Parameters, Conditions, Variables,
  Definitions and Notation. The legend lists the description of every
  dimension, parameter and variable. Notation has an entry for each symbol that
  the typesetter prints for an index that [`shift`](language/operators.md#shift)
  moves or [`position()`](language/expressions.md#position) counts. Notation lists the spec spelling of each symbol.
- The math has the headings Conditions, Variable domains, Definitions,
  Objective, Subject to and Assumptions. Under Subject to, the constraints
  come first, then the special ordered sets (SOS) of
  [`sos:`](language/piecewise.md#sos), then the
  [curves](language/piecewise.md#piecewise). Each part is in file order.

The typesetter does not break lines, so a wide equation runs off the page.

Named expressions, named conditions, curves and assumptions each print in a
form of their own:

- The typesetter prints the symbol of a named expression in each equation
  that contains it, and its body once, in file order, under Definitions. With
  [`inline_expressions`](cli.md#latex-markdown-and-typst), the typesetter
  substitutes each named expression into its equations. Under either
  setting, the typesetter prints the definition line of an expression with
  [cases](language/named.md#cases), an expression outside the math
  ([a reported expression](language/named.md#reported-expressions)) and a
  [term](language/named.md#adds_to).
- The typesetter prints a [named condition](language/named.md#conditions) as
  an upright symbol in each equation that contains it, and its condition once, joined by ⟺, under Conditions. A named condition prints as its symbol under
  either setting of `inline_expressions`.
- A [`piecewise:`](language/piecewise.md) entry prints as one line, which
  quantifies the curve over the dimensions of the entry. The entry states one
  curve at each coordinate. With [`--expand`](cli.md#latex-markdown-and-typst),
  the typesetter prints the entries the curve expands into
  ([its expansion](glossary.md#expansion)).
- An [`assumptions:`](language/assumptions.md) entry prints last, under
  Assumptions, beside the assumptions on the corners of each curve
  ([its breakpoints](glossary.md#breakpoint)). For a
  spec that assumes nothing of its data, the document has no Assumptions
  heading.

### Descriptions

A `description:` prints as plain text, with **one exception**: a name in
backticks, such as `` `capital_cost` ``, prints in monospace in every format.
The typesetter escapes every other character that is markup in the output
format.

## LaTeX

`to_latex` prints LaTeX for the standard LaTeX package for equations
(amsmath). Each heading of the document is a `\paragraph`, and each table of
the legend is a `description` list. The equations under one heading are one
`align` environment. With `numbered=False`, the environment is `align*`, which
numbers no equation.

Without `standalone`, the output is a LaTeX body without a preamble, to include
in a larger document. With `standalone=True`, the output opens with a preamble
and closes with `\end{document}`, so the output compiles on its own:

```latex
\documentclass[11pt]{article}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[margin=2.5cm]{geometry}
\allowdisplaybreaks
\begin{document}
```

`\allowdisplaybreaks` lets a long `align` environment run onto the next page.

## Typst

`to_typst` prints Typst. `to_typst` prints each heading of the document with
`==`, and each table of the legend as a term list. Each equation is a display
`$ … $` block. With numbered equations, each part of the math opens with `#set
math.equation(numbering: "(1)")`.

Typst needs no preamble, so the output compiles with or without `standalone`.
With `standalone=True`, the output opens with two lines that set the page:

```typst
#set page(margin: 2.5cm)
#set text(size: 11pt)
```

The first line sets the margin, and the second the font size.

## Markdown

`to_markdown` prints Markdown that GitHub and GitLab render. `to_markdown`
prints each heading of the document with `####`, and each table of the legend
as a Markdown table with the columns Symbol and Meaning. Each equation is a ` ```math ` fence of its own. The name of the entry, where
it has one, is in bold above the fence.

Inline math is between ``$`…`$``, the one inline pair that GitHub and GitLab
read verbatim. `to_markdown` never prints `$…$` or `$$…$$`, and `to_latex`
prints the same math with no Markdown delimiters.

`to_markdown` numbers no equation, so `numbered` changes nothing. With
`standalone=True`, the output opens with the heading `## The math`.

## `typeset_line`

`typeset_line(spec, name, fmt, *, symbols=None, inline_expressions=True)`
returns the line of the document for one entry. The entry is a named
expression, a named condition, a constraint, a special ordered set, a curve,
an assumption or a variable. The line has its quantifier, but no document,
label, number or math delimiters. `spec` is anything the other functions
take, `fmt` is the format, as for `typeset`, and `symbols` is a symbol table
as for the other functions. `typeset_line` takes no
`standalone`, `legend` or `numbered`. Here `typeset_line` prints `spend` and
`balance`:

```python
ms.typeset_line('spec.yaml', 'spend', 'latex')
# \mathit{spend}_{t} = \sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g} \qquad \forall\, t \in \mathcal{T}
ms.typeset_line('spec.yaml', 'balance', 'latex')
# \sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

Each line ends with its quantifier over $\mathcal{T}$, and the line of `spend`
has its symbol on the left.

A Markdown line has no delimiters either, and it renders inside the inline
pair:

```python
line = ms.typeset_line('spec.yaml', 'balance', 'markdown')
print(f'The balance holds: $`{line}`$')
```

On GitHub, the sentence renders with the equation inline.

A single line comes with no Definitions part, so `typeset_line`
substitutes each named expression without cases that the line uses. With
`inline_expressions=False`, `typeset_line` prints each named expression as its
symbol.
An expression with cases always prints as its symbol, and a second call with
the name of the expression prints its definition.

`typeset_line` refuses a name that is none of the seven kinds, and suggests
the closest match:

```text
'balnce' is not a named expression, condition, constraint, special ordered set, curve, assumption or variable. Did you mean 'balance'?
```

`typeset_line` also refuses a name under
[`given:`](language/parameters-variables-constraints.md#given), because a given
entry prints in the legend and has no line of its own. The message points to
the legend:

```text
'Bus_injection' is a given expression, which prints no line of its own. Call typeset() for the whole spec, and find it in the legend under 'Given'.
```

!!! info "See also"

    - [Command line](cli.md#latex-markdown-and-typst), for the flag and the
      default of each option
    - [Print a spec as math](../howto/print.md), for the steps
    - [See what a piecewise curve or an SOS expands
      to](../howto/see-an-expansion.md), for the entries that `--expand` prints
    - [Every operator as math](language/operators.md#every-operator-as-math), for
      what each operator prints
    - [Every construct, as math](notation.md), for what each construct prints
