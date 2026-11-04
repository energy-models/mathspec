<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Write a piecewise curve out by hand

This guide shows how to tie several flows to one curve in a specification file
([spec](../reference/glossary.md#spec)) where the number of flows is data. A boiler has two flows on its curve, and a combined heat and power (CHP) unit
has three. Both are converters, in one spec. In a [`piecewise:`](../reference/language/piecewise.md)
entry the number of flows is fixed in the file. Instead, write out by hand the plain variables and constraints that such an entry expands into. You need mathspec
[installed](installation.md) and the curve data of each converter.

## Write the entries out

<!-- prettier-ignore -->
1. Declare the dimensions, the mapping from each flow to its converter
    (a [relation](../reference/language/relations.md)), and the data of the
    curves:

    ```yaml
    dimensions:
      converter: { dtype: str }
      flow: { dtype: str }
      time: { dtype: int }
      bp: { dtype: int, ordered: true }

    relations:
      converter_of: { key: flow, values: converter }

    parameters:
      bp_present: { dims: [converter, bp], dtype: bool }
      bp_rate: { dims: [flow, bp] }
    ```

    Each flow belongs to one converter through `converter_of`. The corners of
    each curve ([breakpoints](../reference/glossary.md#breakpoint)) are the
    labels of `bp`, a dimension in a fixed order
    ([ordered](../reference/language/dimensions.md#ordered)). `bp_present` is
    true at each breakpoint that the curve of a converter runs through.
    `bp_rate` is the rate of each flow at each breakpoint.

2. Declare each breakpoint's share of the operating point (its weight) as a
    variable over `bp`. With data attached, `weight` exists only at the
    breakpoints a curve runs through, because of its
    [`where:`](../reference/language/absence.md) condition:

    ```yaml
    variables:
      rate: { dims: [flow, time] }
      weight:
        dims: [converter, time, bp]
        where: bp_present
        bounds: { lower: 0, upper: 1 }
    ```

3. Restrict the weights so that at most two neighbouring weights are non-zero (a
    special ordered set, an [`sos:`](../reference/language/piecewise.md#sos)
    entry). `type: 2` sets that limit, which is the restriction that mathspec
    writes for [`method: sos2`](../reference/language/piecewise.md#method):

    ```yaml
    sos:
      on_one_segment: { variable: weight, along: bp, type: 2 }
    ```

4. Write the row that makes the weights of each converter sum to one (the
    convexity row), and one row per flow:

    ```yaml
    constraints:
      one_operating_point:
        dims: [converter, time]
        expression: sum(weight, over=bp) == 1
      on_the_curve:
        dims: [flow, time]
        expression: rate == sum(at(weight, by=converter_of[converter]) * bp_rate, over=bp)
    ```

    `on_the_curve` is indexed over `flow`, and
    [`at`](../reference/language/operators.md#at) takes `weight` through
    `converter_of`. mathspec prints the constraint as:

    ```math
    \mathit{rate}_{f,t} = \sum_{b \in \mathcal{B}} \mathit{weight}_{\mathrm{converter\_of}(f),t,b} \cdot \mathrm{bp\_rate}_{f,b} \qquad \forall\, f \in \mathcal{F},\ t \in \mathcal{T}
    ```

    The weight has the index $\mathrm{converter\_of}(f)$, so each flow
    uses the weights of its own converter.

## Check the spec

Put the four YAML fences in one file, `spec.yaml`, and run `check` on it:

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

The command and the Python loop print nothing, because mathspec accepts the
spec. A converter with a fourth flow then adds one row to the data of
`converter_of` and one row per breakpoint to the data of `bp_rate`. The spec
stays as it is.

!!! info "See also"

    - [Check a spec without data](check.md), for how to read a refusal or advice.
    - [piecewise curves and SOS](../reference/language/piecewise.md), for the
      entries that mathspec writes for each `method:` of a `piecewise:` entry
    - [see what a piecewise curve or an SOS expands to](see-an-expansion.md), to
      compare the entries that `expand()` writes with this spec
