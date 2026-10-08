<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Examples

Open a page here to see one whole spec as the YAML file and as the math that
the typesetter prints from it. Every spec is a file under `examples/` in the
repository.

- [Least-cost dispatch](dispatch.md) is the smallest whole spec, with a balance,
  a bound and a cost to minimise.
- [Unit commitment](commitment.md) adds an on/off decision and a start-up ramp.
  One quantity has three cases, so a single inequality covers a running unit
  and a starting unit.
- [One construct per spec](operators.md) shows each operator in the smallest
  file that uses it, beside the equation it prints.
- [A component library](library/index.md) is several files that compose into
  one spec. Each file reads the shared declarations of one surface file and
  prints on its own. The composed page shows what `merge` returns.

The PyPSA pages start at [PyPSA in one file](pypsa.md). They state the model
that PyPSA builds, as a proof of concept, and they sit in the Development
section. [PyPSA in 24 files](pypsa/index.md) composes the same spec from
fragments.

[GEMS in ten files](gems/index.md) is a proof of concept too.

To print the math of your own spec, see
[Typeset the math](../reference/typeset.md).
