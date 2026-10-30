---
# SPDX-FileCopyrightText: mathspec contributors
# SPDX-License-Identifier: CC-BY-4.0
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# mathspec

--8<-- "README.md:tagline"

--8<-- "README.md:badges"

[Start the tutorial](tutorials/first-spec.md){ .md-button .md-button--primary }
[See the examples](examples/index.md){ .md-button }
[Read the language](reference/language/index.md){ .md-button }

</div>

---

<div class="landing" markdown>

## What it is for

<div class="grid cards" markdown>

--8<-- "README.md:benefits"

</div>

## The spec

--8<-- "README.md:spec"

--8<-- "README.md:model"

## The math it prints

mathspec prints the math below from the file above. The call that prints it
is in the How tab.

<!-- home-math:begin -->

=== "The math"

    Least-cost dispatch of a generator fleet against a load in each dispatch period.

    #### Sets

    | Symbol | Meaning |
    |---|---|
    | $`\mathcal{S}`$ | index $`s`$ — `snapshot` — dispatch periods |
    | $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units |

    #### Parameters

    | Symbol | Meaning |
    |---|---|
    | $`\bar p`$ | `capacity` over $`\mathcal{G}`$ — installed capacity |
    | $`\ell`$ | `load` over $`\mathcal{S}`$ — demand to be met |
    | $`c`$ | `cost` over $`\mathcal{G}`$ — marginal cost |

    #### Variables

    | Symbol | Meaning |
    |---|---|
    | $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{S} \times \mathcal{G}`$ — output of a generator in a snapshot |

    #### Variable domains

    **`dispatch`**

    ```math
    0 \le \mathit{dispatch}_{s,g} \le \bar p_{g} \qquad \forall\, s \in \mathcal{S},\ g \in \mathcal{G} \,:\, \bar p_{g} > 0
    ```

    #### Objective

    ```math
    \min \sum_{s \in \mathcal{S},\ g \in \mathcal{G}} \mathit{dispatch}_{s,g} \cdot c_{g}
    ```

    #### Subject to

    **`power_balance`**

    ```math
    \sum_{g \in \mathcal{G}} \mathit{dispatch}_{s,g} = \ell_{s} \qquad \forall\, s \in \mathcal{S}
    ```

=== "LaTeX"

    ```latex
    \noindent Least-cost dispatch of a generator fleet against a load in each dispatch period.

    \paragraph{Sets}
    \begin{description}
    \item[{$\mathcal{S}$}] index $s$ --- \texttt{snapshot} --- dispatch periods
    \item[{$\mathcal{G}$}] index $g$ --- \texttt{generator} --- generating units
    \end{description}

    \paragraph{Parameters}
    \begin{description}
    \item[{$\bar p$}] \texttt{capacity} over $\mathcal{G}$ --- installed capacity
    \item[{$\ell$}] \texttt{load} over $\mathcal{S}$ --- demand to be met
    \item[{$c$}] \texttt{cost} over $\mathcal{G}$ --- marginal cost
    \end{description}

    \paragraph{Variables}
    \begin{description}
    \item[{$\mathit{dispatch}$}] \texttt{dispatch} over $\mathcal{S} \times \mathcal{G}$ --- output of a generator in a snapshot
    \end{description}

    \paragraph{Variable domains}
    \begin{align*}
    \text{dispatch} && 0 \le \mathit{dispatch}_{s,g} & \le \bar p_{g} && \forall\, s \in \mathcal{S},\ g \in \mathcal{G} \,:\, \bar p_{g} > 0
    \end{align*}

    \paragraph{Objective}
    \begin{align*}
     && \min & \sum_{s \in \mathcal{S},\ g \in \mathcal{G}} \mathit{dispatch}_{s,g} \cdot c_{g}
    \end{align*}

    \paragraph{Subject to}
    \begin{align*}
    \text{power\_balance} && \sum_{g \in \mathcal{G}} \mathit{dispatch}_{s,g} & = \ell_{s} && \forall\, s \in \mathcal{S}
    \end{align*}
    ```

=== "How"

    ```python
    import mathspec as ms

    symbols = {
        'notation': 'latex',
        'dimensions': {
            'snapshot': {'index': 's', 'set': '\\mathcal{S}'},
            'generator': {'index': 'g', 'set': '\\mathcal{G}'},
        },
        'names': {
            'cost': 'c',
            'load': '\\ell',
            'capacity': '\\bar p',
        },
    }

    spec = ms.to_spec('dispatch.yaml')

    ms.to_latex(spec, symbols=symbols)
    ms.to_typst(spec)
    ms.to_markdown(spec)
    ```

    `symbols` sets the symbol for each name. Pass a dict, a YAML path
    or a `SymbolTable`. It is optional: drop it and the same spec prints from the
    names in the file, as $\mathrm{load}_t$ and $\mathrm{capacity}_g$.

    Or from a shell, where the table is that same YAML on disk. `--standalone` emits
    a document that compiles, rather than a fragment to `\input`:

    ```bash
    python -m mathspec latex dispatch.yaml --symbols dispatch.symbols.yaml
    python -m mathspec typst dispatch.yaml --standalone -o dispatch.typ
    ```

    [Typeset output](reference/typeset.md) documents the three functions, their
    options and symbol tables. Each reads the same file every other page here
    loads.

<!-- home-math:end -->

## Engines and other tools

--8<-- "README.md:engines"

## Where to next

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Tutorials](tutorials/index.md)** teach the language in three lessons, and
    in the first you build the file above one section at a time.
- **[How-to guides](howto/index.md)** list the steps for one task, such as
    checking a spec without data or printing it as math.
- **[Reference](reference/index.md)** describes what a file may contain and
    what it means, key by key, with whole specs beside their math.
- **[About](about/index.md)** explains why the language has the shape it has.
- **[Development](reference/reading.md)** covers how an engine or a renderer reads
    a spec, and how to contribute to mathspec.

</div>

## Install it

[Install mathspec](howto/installation.md) from PyPI with pip, uv or pixi.

!!! warning "Alpha software"

    --8<-- "README.md:status"

</div>
