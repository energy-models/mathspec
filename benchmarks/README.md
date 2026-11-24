<!--
SPDX-FileCopyrightText: mathspec Contributors
SPDX-License-Identifier: MIT
-->

# `benchmarks/` — what each verb costs

This folder measures each public verb on the specs a user writes: `to_spec`,
`advice`, `typeset` in each format, `to_yaml(canonical=True)`, `expand`,
`merge`, `override`, a load that is refused, and `import mathspec`. Each verb
that reads a spec runs on three examples and on two sizes of a synthetic spec
(`synthetic.py`), so a verb whose cost grows faster than the file shows in the
ratio between the two sizes.

## Run it

| Command                                 | What it does                                         |
| --------------------------------------- | ---------------------------------------------------- |
| `pixi run test`                         | Calls each benchmark once, as a test. No timing.     |
| `pixi run pytest benchmarks --codspeed` | Measures wall time, five rounds each, and prints it. |
| CodSpeed workflow, on a pull request    | Counts instructions, and compares with `main`.       |

The CodSpeed workflow is a report, not a gate. It reports only when the
repository is connected at [codspeed.io](https://codspeed.io).

To compare a branch with `main` on your machine, run the second command on
each and compare the tables. The `Rel. StdDev` column says how much wall time
moves from round to round; a change smaller than that needs the CodSpeed count.

## Write a benchmark

- **Each round starts from empty caches.** The two grammars cache each text
  they parse, so a repeated call in one process skips most of the parse. Use
  the `cold` fixture, which empties every `functools` cache in `mathspec`
  before each round. `test_harness.py` fails if a cache stays full.
- **Build the input outside the timing.** Give `cold` the verb and its
  arguments, and load the spec before the call.
- **A new public verb gets a benchmark here**, on the inputs of `INPUTS` if it
  reads a spec.
- **A scaling curve is a local job.** Call `spec_text(n)` with a larger `n` on
  your machine. CI keeps to the two sizes in `INPUTS`, because the CPU
  simulator runs many times slower than the code.
