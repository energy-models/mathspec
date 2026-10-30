<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Background and history

The specification of an optimisation model ([a spec](../reference/glossary.md#spec)) takes its shape from development efforts in the [Calliope](https://github.com/calliope-project/calliope) energy system framework.
The language of a spec has evolved considerably since porting to the framework-agnostic mathspec project.
This evolution has moved the math further out of code and into a file that any piece of software ([a tool](../reference/glossary.md#tool)) can read.

<figure class="diagram">
--8<-- "docs/static/history-timeline.svg"
</figure>

## The problem

In most energy system modelling frameworks, the math lives in the source code as calls to a library such as [Pyomo](https://github.com/Pyomo/pyomo) or [linopy](https://github.com/PyPSA/linopy).
A reader who wants the equations has to read that code or hand-written duplications of that math.
A user cannot add a constraint without writing code and the documentation and the code can easily drift apart.
A constraint can also only be validated by building a model with data.

Calliope set out to solve all four problems by moving the math into a human-readable YAML file.
mathspec has continued that mission and has gone beyond what was achieved in Calliope, introducing even more features to make it easier to write and validate your math.

## Initial development record

| When        | What                                                                                                                                                                                                                                                               | Source                                                                                                                                                                                                                                                        |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2020-08     | Calliope maintainers begin discussions on YAML math formulations.                                                                                                                                                                                                  | [#100](https://github.com/calliope-project/calliope/issues/100#issuecomment-682017208)                                                                                                                                                                        |
| 2021-05     | [@sjpfenninger](https://github.com/sjpfenninger) sets the goal: every constraint in YAML, and the math documentation generated from it.                                                                                                                            | [#360](https://github.com/calliope-project/calliope/issues/360), [#361](https://github.com/calliope-project/calliope/issues/361)                                                                                                                              |
| 2023-02     | [@brynpickering](https://github.com/brynpickering)'s parser lands, with `foreach` and the equation grammar. `where` is a string parsed with the parsing library pyparsing, and constraints are built from `constraints.yaml` on the labelled-array library xarray. | [PR #397](https://github.com/calliope-project/calliope/pull/397), [#408](https://github.com/calliope-project/calliope/pull/408), [#411](https://github.com/calliope-project/calliope/pull/411)                                                                |
| 2023        | A user can replace the built-in math with their own file. The documentation of the math is generated from a built model. A schema validates the math files.                                                                                                        | [PR #414](https://github.com/calliope-project/calliope/pull/414), [#442](https://github.com/calliope-project/calliope/pull/442), [#454](https://github.com/calliope-project/calliope/pull/454)                                                                |
| 2024-01     | The syntax is documented, and 0.7.0.dev2 is the first published release with all of its math in YAML.                                                                                                                                                              | [PR #456](https://github.com/calliope-project/calliope/pull/456), [0.7.0.dev2](https://github.com/calliope-project/calliope/releases/tag/v0.7.0.dev2)                                                                                                         |
| 2024 - 2026 | Calliope adds piecewise constraints, direct Gurobi and HiGHS solver engines, dispatch and MGA math, and post-solve expressions.                                                                                                                                    | [PR #551](https://github.com/calliope-project/calliope/pull/551), [#569](https://github.com/calliope-project/calliope/pull/569), [#716](https://github.com/calliope-project/calliope/pull/716), [#839](https://github.com/calliope-project/calliope/pull/839) |
| 2026-03     | [@FBumann](https://github.com/FBumann) creates lpspec (later specsolve): declarative linear and mixed-integer linear programs (LP and MILP) on a streaming relational query library. Its math language develops from a port of Calliope's.                         | [specsolve](https://github.com/fluxopt/specsolve), [PR #336](https://github.com/fluxopt/specsolve/pull/336)                                                                                                                                                   |
| 2026-08     | The language and the typesetter are extracted from specsolve into a repository of their own. specsolve becomes one engine among many.                                                                                                                              | [PR #17](https://github.com/energy-models/mathspec/pull/17)                                                                                                                                                                                                   |
| 2026-08     | The [PyPSA](https://github.com/PyPSA/PyPSA) math is written as a spec to prove its viability.                                                                                                                                                                      | [PR #134](https://github.com/energy-models/mathspec/pull/134) to [#143](https://github.com/energy-models/mathspec/pull/143)                                                                                                                                   |
| 2026-09     | Calliope 0.7.0 is released, its first stable release with YAML math; the Calliope math is rewritten as a spec to prove its viability.                                                                                                                              | [0.7.0](https://github.com/calliope-project/calliope/releases/tag/v0.7.0), [PR #770](https://github.com/energy-models/mathspec/pull/770)                                                                                                                      |
| 2026-09     | The first post-alpha release of `mathspec` is published on the Python Package Index; specsolve depends on mathspec 0.1.0 and fluxopt math is written as a spec.                                                                                                    | [0.1.0](https://pypi.org/project/mathspec/0.1.0), [specsolve #1754](https://github.com/fluxopt/specsolve/pull/1754), [fluxopt #358](https://github.com/fluxopt/fluxopt/pull/358)                                                                              |

## People and organisations

Calliope is developed in the [calliope-project](https://github.com/calliope-project) organisation by those listed in its [AUTHORS](https://github.com/calliope-project/calliope/blob/main/AUTHORS) file.
specsolve is developed by [@FBumann](https://github.com/FBumann) in the [fluxopt](https://github.com/fluxopt) organisation.
mathspec is developed in the framework-agnostic [energy-models](https://github.com/energy-models) organisation ([contributors](https://github.com/energy-models/mathspec/graphs/contributors)).

--8<-- "README.md:contributors"

!!! info "See also"

    - [versions](versions.md), for how the package version and the language
      version relate
    - [how mathspec works](overview.md), for what mathspec does with a spec today
