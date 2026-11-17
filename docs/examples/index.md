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

<div class="grid cards tiles" markdown>

<!-- prettier-ignore -->
- **Least-cost dispatch**
    The smallest spec has a balance, a bound and a cost to minimise.
    [Open →](dispatch.md)
- **Unit commitment**
    An on/off decision has a previous status in three cases, so one
    inequality covers a running unit and a starting unit.
    [Open →](commitment.md)
- **Units with ports**
    One relation lists the ports of each unit, and a parameter with
    `where:` keeps only the output ports.
    [Open →](connection.md)
- **One construct per spec**
    Each form of the four operators and `dual` has its smallest file, beside
    its typeset equation.
    [Open →](operators.md)
- **A curve by convex combination**
    The smallest `piecewise` entry has one weight per breakpoint. The three
    pages after it state the same dispatch with another method.
    [Open →](piecewise.md)
- **A curve that is not convex**
    A binary per segment holds the weights on one segment, under the default
    method.
    [Open →](piecewise_adjacency.md)
- **A curve as a special ordered set**
    The solver holds the same restriction, in place of the binaries and their
    rows.
    [Open →](sos.md)
- **A curve as segment lines**
    The curve is a set of inequalities, and its expansion declares no
    variable.
    [Open →](piecewise_lp.md)
- **A curve filled segment by segment**
    Each segment fills only once the one before it is full. A status switches
    the curve only of a committable generator.
    [Open →](piecewise_incremental.md)
- **A component library**
    Several files compose into one spec with `merge`, each written against
    one shared fragment, the coupling surface.
    [Open →](library/index.md)
- **PyPSA**
    The model that `n.optimize()` builds in the power system modelling
    framework PyPSA is one file, and 25 fragments that compose into it.
    [Open →](pypsa/index.md)

</div>

!!! info "See also"

    - [Typeset output](../reference/typeset.md), for the formats the typesetter
      prints and their options
    - [The language reference](../reference/language/index.md), for every key a
      file accepts
