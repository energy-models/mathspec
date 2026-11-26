<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Allow at most one of several options

This guide shows how to let a solver choose at most one option for each site,
such as one technology, with an `sos:` entry. It then shows the constraints to
write when a site may choose more than one. You need a specification file
([spec](../reference/glossary.md#spec)) that already loads.

## Declare the options along one dimension

Declare the options as a
[dimension](../reference/language/dimensions.md), and the choice as one
variable over it. Give the variable both bounds, because mathspec refuses an
`sos:` entry over a variable without them:

```yaml
dimensions:
  site: { dtype: str }
  technology: { dtype: str }

parameters:
  max_capacity: { dims: [technology] }
  cost: { dims: [site, technology] }
  demand: { dims: [] }

variables:
  capacity:
    dims: [site, technology]
    bounds: { lower: 0, upper: max_capacity }

constraints:
  meet_demand:
    dims: []
    expression: sum(capacity) >= demand

objective:
  sense: minimize
  expression: sum(cost * capacity)
```

`capacity` is the capacity of each technology at each site, and a technology
that a site does not build has a capacity of zero.

## Add an `sos` entry

Add an [`sos:`](../reference/language/piecewise.md#sos) entry over the
variable, along the dimension of the options, with `type: 1`:

```yaml
sos:
  one_technology:
    variable: capacity
    along: technology
    type: 1
```

```math
\left( \mathit{capacity}_{s,t} \right)_{t \in \mathcal{T}} \in \mathrm{SOS}1 \qquad \forall\, s \in \mathcal{S}
```

At each site, at most one technology now has a capacity that is not zero.

If two neighbouring options may both be non-zero, such as two stages of a
heat pump, write `type: 2`. Declare the dimension
[ordered](../reference/language/dimensions.md#ordered) too.

## Allow up to a number of options

An `sos:` entry allows one option, or two neighbouring ones. To allow up to a
number of options at each site, write a binary variable per option and two
constraints instead of the `sos:` entry:

```yaml
parameters:
  max_technologies: { dims: [site] }

variables:
  built:
    dims: [site, technology]
    domain: binary

constraints:
  capacity_if_built:
    dims: [site, technology]
    expression: capacity <= max_capacity * built
  few_technologies:
    dims: [site]
    expression: sum(built, over=technology) <= max_technologies
```

```math
\mathit{capacity}_{s,t} \le \mathrm{max\_capacity}_{t} \cdot \mathit{built}_{s,t} \qquad \forall\, s \in \mathcal{S},\ t \in \mathcal{T}
```

```math
\sum_{t \in \mathcal{T}} \mathit{built}_{s,t} \le \mathrm{max\_technologies}_{s} \qquad \forall\, s \in \mathcal{S}
```

A technology has capacity only where its `built` is 1, and each site builds at
most `max_technologies` of them.

## Check the spec

Put the fences of the first two steps in one file, `spec.yaml`, and run
`check` on it:

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
spec and has no remark to make about it
([advice](../reference/glossary.md#advice)).

!!! info "See also"

    - [`sos`](../reference/language/piecewise.md#sos), for every key of a set
      and the rows it is written out as.
    - [See what a piecewise curve or an SOS expands to](see-an-expansion.md),
      for the expansion of your own set.
