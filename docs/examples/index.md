<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Examples

Each example page contains the specification of one optimisation model
([a spec](../reference/glossary.md#spec)) twice. The page has the YAML file,
and the math that [the typesetter](../reference/typeset.md) prints from the file.
Every spec is a file under `examples/` in the repository, and the test suite
loads each one. Open a page to see whether the language can state a problem
like yours, and what each line of the file means.

<div class="grid cards" markdown>

<!-- prettier-ignore -->
- **[Least-cost dispatch](dispatch.md)** is the smallest spec with a balance,
    a bound and a cost to minimise.
- **[Unit commitment](commitment.md)** states `previous_status` in three
    [cases](../reference/language/named.md#cases), so one inequality covers a
    running unit and a starting unit.
- **[Units with ports](connection.md)** is a spec with one
    [relation](../reference/language/relations.md) for the ports of each unit,
    and a parameter whose
    [`where:`](../reference/language/parameters-variables-constraints.md#where)
    keeps only the output ports.
- **[One construct per spec](operators.md)** contains the smallest file for
    each form of the four [operators](../reference/language/operators.md) and
    [`dual`](../reference/language/named.md#dual), each file beside its
    typeset equation.
- **[A curve by convex combination](piecewise.md)** is the smallest
    [`piecewise`](../reference/language/piecewise.md) entry, with one weight
    per breakpoint. The three pages after it state the same dispatch with
    another method.
- **[A curve that is not convex](piecewise_adjacency.md)** holds the weights
    on one segment with a binary per segment, under the default method.
- **[A curve as a special ordered set](sos.md)** leaves the same restriction
    to the solver, in place of the binaries and their rows.
- **[A curve as segment lines](piecewise_lp.md)** states the curve as
    inequalities, and its expansion declares no variable.
- **[A curve filled segment by segment](piecewise_incremental.md)** fills
    each segment only once the one before it is full. Its curves have
    different lengths, and a status switches the curve only of a committable
    generator.
- **[A component library](library/index.md)** is several files that
    [`merge`](../reference/composition.md#merge) composes into one spec, each
    written against one shared [fragment](../reference/glossary.md#fragment)
    (the [surface](../reference/glossary.md#surface)).

</div>

An open-source power system modelling framework
([PyPSA](https://pypsa.org)) has its own pages in the Development section,
which start at [PyPSA in one file](pypsa_ladder.md). They state the model that PyPSA
builds, as a proof that the language can state it.
[PyPSA in 25 files](pypsa/index.md) states the same spec in fragments
that `merge` composes.

!!! info "See also"

    - [Typeset output](../reference/typeset.md), for the formats the typesetter
      prints and their options
    - [The language reference](../reference/language/index.md), for every key a
      file accepts
