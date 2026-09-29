<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Examples

Each page here shows one whole spec as the file and as the math it prints.
Every spec is a file under `examples/` in the repository.

- [Least-cost dispatch](dispatch.md) is the smallest whole spec. It has a
  balance, a bound and a cost to minimise.
- [Unit commitment](commitment.md) adds a start-up ramp. One quantity is defined
  by region, so a single inequality covers both regimes.
- [One construct per spec](operators.md) declares each operator in the smallest
  file that can, and prints the equation beside it.
- [A curve by convex combination](piecewise.md) is the floor of the `piecewise`
  family: one weight per breakpoint, one row summing them to 1, and one row per
  link. The three pages after it are the same spec, restricted another way.
- [A curve that is not convex](piecewise_adjacency.md) adds a binary per segment
  and the two rows that hold the weights on it. This is what the default method
  builds.
- [A curve as a special-ordered set](sos.md) hands that same restriction to the
  solver. The binaries and their rows are gone, and a declaration stands where
  they were.
- [A curve as segment lines](piecewise_lp.md) states the curve as inequalities
  instead of breakpoints, and declares no auxiliary variable at all.
- [A component library](library/index.md) is several files that compose into
  one spec. Each file reads the coupling surface and prints on its own, and the
  composed page shows what `merge` returns.

The PyPSA parity pages, from [PyPSA in one file](pypsa.md) on, are a proof of
concept. They sit in the Development section, and
[PyPSA in 24 files](pypsa/index.md) is the same spec composed from fragments.

[Typeset the math](../reference/typeset.md) prints your own.
