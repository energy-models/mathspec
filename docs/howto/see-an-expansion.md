<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# See what a piecewise curve or an SOS expands to

This guide shows how to write a piecewise curve (a
[`piecewise:`](../reference/language/piecewise.md) entry) or a special ordered
set (an [SOS](../reference/glossary.md#special-ordered-set-sos)) out as plain
entries. You can then hand the expanded file to software that builds the model
([an engine](../reference/glossary.md#tool)) but cannot read an
[`sos:`](../reference/language/piecewise.md#sos) entry.

You need mathspec [installed](installation.md) and the specification of an
optimisation model ([a spec](../reference/glossary.md#spec)) that loads.

## Write a piecewise curve out

Save the spec in the "Before" tab below as `before.yaml`, and load it. Its
curve has `method: sos2`:

```python
import mathspec as ms

spec = ms.to_spec('before.yaml')
```

Write out only the piecewise curve with `spec.expand('piecewise')`, which keeps
every `sos:` entry. Then write out both with `spec.expand()`:

<!-- prettier-ignore-start -->
<!-- expansion:curve:begin -->

=== "Before"

    === "YAML"

        ```yaml
        dimensions:
          bp: { dtype: int, ordered: true }

        parameters:
          x_bp: { dims: [bp] }
          y_bp: { dims: [bp] }

        variables:
          x: { dims: [], bounds: { lower: 0 } }
          y: { dims: [], bounds: { lower: 0 } }

        piecewise:
          curve:
            over: bp
            method: sos2
            links:
              - [x, x_bp]
              - [y, y_bp]
        ```

    === "Math"

        _Variable domains_

        **`x`**

        ```math
        x \ge 0
        ```

        **`y`**

        ```math
        y \ge 0
        ```

        _Subject to_

        **`curve`**

        ```math
        \left( x,\ y \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}^{\mathrm{bp}}_{b},\ \mathrm{y}^{\mathrm{bp}}_{b})
        ```

        _Assumptions_

        **`curve_complete`**

        ```math
        \mathrm{x}^{\mathrm{bp}}_{b} \text{ is defined} \wedge \mathrm{y}^{\mathrm{bp}}_{b} \text{ is defined} \qquad \forall\, b \in \mathcal{B}
        ```

=== "`expand('piecewise')`"

    === "YAML"

        ```yaml
        dimensions:
          bp: { dtype: int, ordered: true }

        parameters:
          x_bp: { dims: [bp] }
          y_bp: { dims: [bp] }

        variables:
          x: { dims: [], bounds: { lower: 0 } }
          y: { dims: [], bounds: { lower: 0 } }
          curve_lam:
            dims: [bp]
            bounds: { lower: 0, upper: 1 }
            description: convex-combination weight on a breakpoint

        constraints:
          curve_convexity:
            dims: []
            expression: sum(curve_lam, over=bp) == 1
          curve_link0:
            dims: []
            expression: (x) == sum(curve_lam * x_bp, over=bp)
          curve_link1:
            dims: []
            expression: (y) == sum(curve_lam * y_bp, over=bp)

        sos:
          curve:
            variable: curve_lam
            along: bp
            type: 2

        assumptions:
          curve_complete:
            holds: x_bp AND y_bp
            description: >-
              piecewise 'curve': every breakpoint the curve runs through needs a row in
              'x_bp', 'y_bp'. A missing row does not shorten the curve. Attach the rows, or declare points: to say how far the curve
              runs.
        ```

    === "Math"

        _Variable domains_

        **`x`**

        ```math
        x \ge 0
        ```

        **`y`**

        ```math
        y \ge 0
        ```

        **`curve_lam`**

        ```math
        0 \le \mathit{curve\_lam}_{b} \le 1 \qquad \forall\, b \in \mathcal{B}
        ```

        _Subject to_

        **`curve_convexity`**

        ```math
        \sum_{b \in \mathcal{B}} \mathit{curve\_lam}_{b} = 1
        ```

        **`curve_link0`**

        ```math
        x = \sum_{b \in \mathcal{B}} \mathit{curve\_lam}_{b} \cdot \mathrm{x}^{\mathrm{bp}}_{b}
        ```

        **`curve_link1`**

        ```math
        y = \sum_{b \in \mathcal{B}} \mathit{curve\_lam}_{b} \cdot \mathrm{y}^{\mathrm{bp}}_{b}
        ```

        **`curve`**

        ```math
        \left( \mathit{curve\_lam}_{b} \right)_{b \in \mathcal{B}} \in \mathrm{SOS}2
        ```

        _Assumptions_

        **`curve_complete`**

        ```math
        \mathrm{x}^{\mathrm{bp}}_{b} \text{ is defined} \wedge \mathrm{y}^{\mathrm{bp}}_{b} \text{ is defined} \qquad \forall\, b \in \mathcal{B}
        ```

=== "`expand()`"

    === "YAML"

        ```yaml
        dimensions:
          bp: { dtype: int, ordered: true }

        parameters:
          x_bp: { dims: [bp] }
          y_bp: { dims: [bp] }

        variables:
          x: { dims: [], bounds: { lower: 0 } }
          y: { dims: [], bounds: { lower: 0 } }
          curve_lam:
            dims: [bp]
            bounds: { lower: 0, upper: 1 }
            description: convex-combination weight on a breakpoint
          curve_seg:
            dims: [bp]
            domain: binary
            description: a binary per segment, 1 where the two members it spans may be nonzero

        constraints:
          curve_convexity:
            dims: []
            expression: sum(curve_lam, over=bp) == 1
          curve_link0:
            dims: []
            expression: (x) == sum(curve_lam * x_bp, over=bp)
          curve_link1:
            dims: []
            expression: (y) == sum(curve_lam * y_bp, over=bp)
          curve_pick:
            dims: []
            expression: sum(curve_seg, over=bp) <= 1
          curve_adjacency:
            dims: [bp]
            expression: curve_lam <= (curve_seg + shift(curve_seg, along=bp, offset=1, edge=0))

        assumptions:
          curve_complete:
            holds: x_bp AND y_bp
            description: >-
              piecewise 'curve': every breakpoint the curve runs through needs a row in
              'x_bp', 'y_bp'. A missing row does not shorten the curve. Attach the rows, or declare points: to say how far the curve
              runs.
        ```

    === "Math"

        _Variable domains_

        **`x`**

        ```math
        x \ge 0
        ```

        **`y`**

        ```math
        y \ge 0
        ```

        **`curve_lam`**

        ```math
        0 \le \mathit{curve\_lam}_{b} \le 1 \qquad \forall\, b \in \mathcal{B}
        ```

        **`curve_seg`**

        ```math
        \mathit{curve\_seg}_{b} \in \{0, 1\} \qquad \forall\, b \in \mathcal{B}
        ```

        _Subject to_

        **`curve_convexity`**

        ```math
        \sum_{b \in \mathcal{B}} \mathit{curve\_lam}_{b} = 1
        ```

        **`curve_link0`**

        ```math
        x = \sum_{b \in \mathcal{B}} \mathit{curve\_lam}_{b} \cdot \mathrm{x}^{\mathrm{bp}}_{b}
        ```

        **`curve_link1`**

        ```math
        y = \sum_{b \in \mathcal{B}} \mathit{curve\_lam}_{b} \cdot \mathrm{y}^{\mathrm{bp}}_{b}
        ```

        **`curve_pick`**

        ```math
        \sum_{b \in \mathcal{B}} \mathit{curve\_seg}_{b} \le 1
        ```

        **`curve_adjacency`**

        ```math
        \mathit{curve\_lam}_{b} \le \mathit{curve\_seg}_{b} + \mathit{curve\_seg}_{b \boxminus_{0} 1} \qquad \forall\, b \in \mathcal{B}
        ```

        _Assumptions_

        **`curve_complete`**

        ```math
        \mathrm{x}^{\mathrm{bp}}_{b} \text{ is defined} \wedge \mathrm{y}^{\mathrm{bp}}_{b} \text{ is defined} \qquad \forall\, b \in \mathcal{B}
        ```

<!-- expansion:curve:end -->
<!-- prettier-ignore-end -->

`expand('piecewise')` writes the curve out as the weights `curve_lam`, the row
that makes them sum to one and one row per entry of `links:`. The call keeps the SOS that the curve states as an `sos:` entry,
and `expand()` writes that SOS out too. `curve_complete`, a statement about the data
([an assumption](../reference/language/assumptions.md)), stays in the spec
after either call writes the curve out.

Keep this Python session open, because later steps use `spec` and `ms`.

## Print the expansion as math

Print `before.yaml` with each entry that expands
([formulation](../reference/glossary.md#formulation)) written out as plain
entries:

=== "Command line"

    ```bash
    python -m mathspec markdown before.yaml --expand
    ```

=== "Python"

    ```python
    print(ms.to_markdown(spec.expand()))
    ```

The command and the Python call print the symbol tables of the spec, then the
math. The "Math" tab under `expand()` in the section above contains the same
math without the symbol tables.

## Write an SOS out

Save the spec in the "Before" tab below as `sos.yaml`, and write it out with
`ms.to_spec('sos.yaml').expand()`. In this spec, the `sos:` entry `pick`
requires at most one member of `p` to be non-zero:

<!-- prettier-ignore-start -->
<!-- expansion:set:begin -->

=== "Before"

    === "YAML"

        ```yaml
        dimensions:
          g: { dtype: str }

        variables:
          p:
            dims: [g]
            bounds: { lower: 0, upper: 10 }

        sos:
          pick:
            variable: p
            along: g
            type: 1
        ```

    === "Math"

        _Variable domains_

        **`p`**

        ```math
        0 \le p_{g} \le 10 \qquad \forall\, g \in \mathcal{G}
        ```

        _Subject to_

        **`pick`**

        ```math
        \left( p_{g} \right)_{g \in \mathcal{G}} \in \mathrm{SOS}1
        ```

=== "`expand()`"

    === "YAML"

        ```yaml
        dimensions:
          g: { dtype: str }

        variables:
          p:
            dims: [g]
            bounds: { lower: 0, upper: 10 }
          pick_seg:
            dims: [g]
            domain: binary
            description: a binary per member, 1 where that member may be nonzero

        constraints:
          pick_pick:
            dims: []
            expression: sum(pick_seg, over=g) <= 1
          pick_nonzero:
            dims: [g]
            expression: p <= 10.0 * (pick_seg)
        ```

    === "Math"

        _Variable domains_

        **`p`**

        ```math
        0 \le p_{g} \le 10 \qquad \forall\, g \in \mathcal{G}
        ```

        **`pick_seg`**

        ```math
        \mathit{pick\_seg}_{g} \in \{0, 1\} \qquad \forall\, g \in \mathcal{G}
        ```

        _Subject to_

        **`pick_pick`**

        ```math
        \sum_{g \in \mathcal{G}} \mathit{pick\_seg}_{g} \le 1
        ```

        **`pick_nonzero`**

        ```math
        p_{g} \le 10 \cdot \mathit{pick\_seg}_{g} \qquad \forall\, g \in \mathcal{G}
        ```

<!-- expansion:set:end -->
<!-- prettier-ignore-end -->

`expand()` replaces `pick` with the binary variable `pick_seg` and two
constraints.

## Check the expanded spec

Load the expanded spec again, to check that mathspec accepts it as a spec of
its own:

```python
ms.to_spec(spec.expand().to_yaml())
```

The call returns a `Spec` without an error. Save the YAML text that `to_yaml()`
returns as a file, and hand the file to an engine that reads only plain
entries.

!!! info "See also"

    - [`Spec.expand()`](../reference/spec.md#mathspec.spec.Spec.expand), for every
      argument the call accepts and what it returns
    - [the rows of an SOS written out](../reference/language/piecewise.md#what-a-set-is-written-out-as),
      for the rows of each constraint that `expand()` writes for an SOS
    - [writing a formulation out](../reference/language/piecewise.md),
      for the entries that each formulation adds
    - [write a piecewise curve out by hand](curve-by-hand.md), for a curve whose
      number of flows is data
