<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# What counts as public API

A function may join the public API of the package, as `to_spec` and
`to_latex` did, when both of these are true:

1. The same file gives the same answer. `to_spec('spec.yaml')` returns the same
   `Spec` today, tomorrow, and on a machine with no data and no solver. A
   function whose answer depends on data, a solver, the network or the clock
   cannot join.
2. No rule lives only in the code. Every rule the function applies is written
   on a page of this reference, so somebody could rewrite the function in
   another language from the pages alone and get the same answer.

Where a feature can be a key in the file, it is one, because a key shows up in
a git diff, the typesetter prints it, and an engine in another language reads
it.

The operators a spec may use are a separate question, answered by
[the limits](limits.md).

## What every function keeps

- A function keeps no state. It uses no registry, no plugin, and no setting
  that changes what a spec means. `symbols=` on the typesetter is an allowed
  option, because it changes how `load` prints and nothing about what `load`
  is.
- A function returns a value or raises an error, and nothing between.
  `to_spec` either returns a `Spec` or raises an error that names the rewrite.
  `advice()` is separate: it reports on a file the language accepts, and
  changes nothing.
- A function writes nothing out unless the caller asks. A `piecewise:` or
  `sos:` block stays a block until the caller calls
  [`spec.expand()`](../reference/api.md#mathspec.Spec.expand).

Each engine decides what a solver or file format can take, how the numbers
attach to the names, and which solver runs
([what counts as language](what-counts-as-language.md#what-each-tool-decides-for-itself)).
