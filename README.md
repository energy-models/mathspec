<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# mathspec

<!--- --8<-- [start:badges] -->

[![CI](https://img.shields.io/github/actions/workflow/status/energy-models/mathspec/ci.yml?style=flat-square&branch=main)](https://github.com/energy-models/mathspec/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/mathspec?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/mathspec)
[![pypi-version](https://img.shields.io/pypi/v/mathspec.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/mathspec)
[![python-version](https://img.shields.io/pypi/pyversions/mathspec?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/mathspec)
[![Documentation build status](https://readthedocs.org/projects/mathspec/badge/?version=latest&style=flat-square)](https://mathspec.readthedocs.io)

<!--- --8<-- [end:badges] -->

**Write the specification (spec) of an optimisation model as a YAML file. Check it and print it
as math, with no data and no solver.**

A spec declares four things: the dimensions it runs over, such as `snapshot`
and `generator`; the data it expects, such as `load` and `cost`; the decisions
the solver makes, such as `dispatch`; and the rules those decisions obey, such
as `sum(dispatch, over=generator) == load`. The file [below](#example) is a
complete spec.

<!--- --8<-- [start:benefits] -->

- **Check specs in CI, with no data.** A wrong name or
  dimension fails when the file loads, and the error names the fix.
  [Errors →](https://mathspec.readthedocs.io/en/latest/reference/language/errors/)
- **Publish the math you solve.** The equations in the paper
  print from the file the solver reads.
  [Typeset →](https://mathspec.readthedocs.io/en/latest/reference/typeset/)
- **One spec, many tools.** Engines, renderers and analysers read the spec
  through one public API, so no two of them can read the file differently.
  [Program API →](https://mathspec.readthedocs.io/en/latest/reference/program/)
- **Write full-size specs.** The spec of PyPSA's `n.optimize()` model is
  one file, with stochastic, multi-period and quadratic variants.
  [PyPSA in one file →](https://mathspec.readthedocs.io/en/latest/examples/pypsa/)

<!--- --8<-- [end:benefits] -->

## Example

<!--- --8<-- [start:model] -->

```yaml title="dispatch.yaml"
description: Least-cost dispatch of a generator fleet against an hourly load.

dimensions:
  snapshot: { dtype: int, description: dispatch periods }
  generator: { description: generating units }

parameters:
  capacity: { dims: [generator], description: installed capacity }
  load: { dims: [snapshot], description: demand to be met }
  cost: { dims: [generator], description: marginal cost }

variables:
  dispatch:
    description: output of a generator in a snapshot
    dims: [snapshot, generator]
    where: "capacity > 0"
    bounds: { lower: 0, upper: capacity }

constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load

objective:
  sense: minimize
  expression: sum(dispatch * cost)
```

<!--- --8<-- [end:model] -->

### The math it prints

The typesetter prints the file above as math, with no data and no solver.
Markdown is one of three formats, and GitHub renders it here.

<!-- Prettier pads the legend tables that the generator emits unpadded, so the
     two would rewrite each other forever. The range keeps this file formatted
     and the block below byte-for-byte what the typesetter printed. -->
<!-- prettier-ignore-start -->
<!-- readme-math:begin -->

Least-cost dispatch of a generator fleet against an hourly load.

#### Variable domains

**`dispatch`**

```math
0 \le \mathit{dispatch}_{t,g} \le \mathrm{capacity}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{capacity}_{g} > 0
```

#### Objective

```math
\min \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} \mathit{dispatch}_{t,g} \cdot \mathrm{cost}_{g}
```

#### Subject to

**`power_balance`**

```math
\sum_{g \in \mathcal{G}} \mathit{dispatch}_{t,g} = \mathrm{load}_{t} \qquad \forall\, t \in \mathcal{T}
```

<details>
<summary>The whole document: a symbol table, and the legend it prints</summary>

Least-cost dispatch of a generator fleet against an hourly load.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{S}`$ | index $`s`$ — `snapshot` — dispatch periods |
| $`\mathcal{G}`$ | index $`g`$ — `generator` — generating units |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\bar p`$ | `capacity` over $`\mathcal{G}`$ — installed capacity |
| $`\ell`$ | `load` over $`\mathcal{S}`$ — demand to be met |
| $`c`$ | `cost` over $`\mathcal{G}`$ — marginal cost |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{dispatch}`$ | `dispatch` over $`\mathcal{S} \times \mathcal{G}`$ — output of a generator in a snapshot |

#### Variable domains

**`dispatch`**

$`0 \le \mathit{dispatch}_{s,g} \le \bar p_{g} \qquad \forall\, s \in \mathcal{S},\ g \in \mathcal{G} \,:\, \bar p_{g} > 0`$

#### Objective

$`\min \sum_{s \in \mathcal{S},\ g \in \mathcal{G}} \mathit{dispatch}_{s,g} \cdot c_{g}`$

#### Subject to

**`power_balance`**

$`\sum_{g \in \mathcal{G}} \mathit{dispatch}_{s,g} = \ell_{s} \qquad \forall\, s \in \mathcal{S}`$

</details>

<!-- readme-math:end -->
<!-- prettier-ignore-end -->

Each format is one call:

```python
import mathspec as ms

spec = ms.to_spec('dispatch.yaml')

ms.to_markdown(spec)
ms.to_latex(spec)
ms.to_typst(spec)
```

A [symbol table](https://mathspec.readthedocs.io/en/latest/reference/typeset/#symbol-tables) gives the names their
conventional spelling, as in the folded block.
[Print a spec as math](https://mathspec.readthedocs.io/en/latest/howto/print/) does the same from a shell.

## Engines and other tools

<!--- --8<-- [start:engines] -->

mathspec builds nothing and solves nothing itself. Instead,
[specsolve](https://github.com/fluxopt/specsolve) and
[linopy](https://github.com/PyPSA/linopy) build a model from a spec and its
data, and solve it. Support in both is work in progress. Any other tool can
read the same spec through the
[Program API](https://mathspec.readthedocs.io/en/latest/reference/program/).
The solid boxes are mathspec; the dashed boxes are outside it.

```mermaid
flowchart LR
    accTitle: What mathspec does, and what other tools do with a spec
    accDescr: A YAML file loads into a Spec and the Program it lowers to. mathspec checks the spec and prints it as math, with no data. Outside mathspec, drawn dashed, an engine such as specsolve or linopy reads the same spec, takes your data and returns your answers, and any other tool, such as a renderer or an analyser, reads the same spec through the Program API.
    Y(["your spec<br/>one YAML file"]) --> SPEC["<b>Spec</b> and the <b>Program</b> it lowers to<br/><i>checked before any data exists</i>"]
    SPEC --> CHECK["<b>check it</b><br/>python -m mathspec check"]
    SPEC --> SHOW["<b>print it as math</b><br/>LaTeX · Typst · Markdown"]
    SPEC -.-> OTHER["<b>your own tool</b><br/>a renderer · an analyser · …<br/>reads the Program API"]
    SPEC -.-> ENGINE["<b>an engine</b><br/>specsolve · linopy<br/>builds and solves the model"]
    DATA[("your data")] -.-> ENGINE
    ENGINE -.-> ANS(["your answers"])
    classDef outside stroke-dasharray:5 4
    class ENGINE,DATA,ANS,OTHER outside
```

<!--- --8<-- [end:engines] -->

## Documentation

The documentation is at <https://mathspec.readthedocs.io>.

## Installation

See [installation](https://mathspec.readthedocs.io/en/latest/howto/installation/). To work on mathspec, see
[contributing](https://mathspec.readthedocs.io/en/latest/contributing/#setting-up-a-development-environment).

## Prior art

Every file under `src/` was written in [specsolve](https://github.com/fluxopt/specsolve)
and extracted here. The keys come from
[Calliope](https://github.com/calliope-project/calliope): math in YAML, one
block per component, `dims:` and a `where:` string. `sum(over=)` and the
dimension rules take their names from [linopy](https://github.com/PyPSA/linopy).

## Status

Alpha, pre-1.0.

<!--- --8<-- [start:status] -->

**Breaking changes land without a deprecation cycle.** Pin an exact version if
you depend on this, and read the
[changelog](https://github.com/energy-models/mathspec/blob/main/CHANGELOG.md)
before upgrading. The test suite passes every construct through the schema,
the parsers and all three typeset formats, and compiles the LaTeX. The YAML that
mathspec accepts can still change.

<!--- --8<-- [end:status] -->

## Contributors

Thanks go to these people
([emoji key](https://allcontributors.org/docs/en/emoji-key)). The
all-contributors bot keeps the table below. To add someone, comment
`@all-contributors please add @login for code` on an issue.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/brynpickering"><img src="https://github.com/brynpickering.png?v=4&size=100" width="100px" height="100px" alt="Bryn Pickering"/><br /><sub><b>Bryn Pickering</b></sub></a><br /><a href="https://github.com/search?type=pullrequests&q=is%3Apr+author%3Abrynpickering+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2023-01-01..2026-08-13%29%29&s=created&o=desc" title="Code">💻</a> <a href="https://github.com/search?type=commits&q=author%3Abrynpickering+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Documentation">📖</a> <a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Abrynpickering+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Abrynpickering+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Project Management">📆</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+author%3Abrynpickering+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Maintenance">🚧</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+reviewed-by%3Abrynpickering+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2023-01-01..2026-08-13%29%29&s=created&o=desc" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/search?type=commits&q=author%3Abrynpickering+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://fxbumann.de"><img src="https://avatars.githubusercontent.com/u/117816358?v=4&size=100" width="100px" height="100px" alt="Felix Bumann"/><br /><sub><b>Felix Bumann</b></sub></a><br /><a href="https://github.com/search?type=commits&q=author%3AFBumann+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Code">💻</a> <a href="https://github.com/search?type=commits&q=author%3AFBumann+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Documentation">📖</a> <a href="https://github.com/search?type=commits&q=author%3AFBumann+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Tests">⚠️</a> <a href="https://github.com/search?type=commits&q=author%3AFBumann+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+author%3AFBumann+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Afluxopt%2Fspecsolve+created%3A%3C2026-08-21%29%29&s=created&o=desc" title="Maintenance">🚧</a> <a href="https://github.com/search?type=issues&q=is%3Aissue+author%3AFBumann+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Afluxopt%2Fspecsolve+created%3A%3C2026-08-21%29%29&s=created&o=desc" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+reviewed-by%3AFBumann+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Afluxopt%2Fspecsolve+created%3A%3C2026-08-21%29%29&s=created&o=desc" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://fabianhofmann.org"><img src="https://avatars.githubusercontent.com/u/19226431?v=4&size=100" width="100px" height="100px" alt="Fabian Hofmann"/><br /><sub><b>Fabian Hofmann</b></sub></a><br /><a href="https://github.com/search?type=commits&q=author%3AFabianHofmann+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Code">💻</a> <a href="https://github.com/search?type=commits&q=author%3AFabianHofmann+repo%3Aenergy-models%2Fmathspec&s=committer-date&o=desc" title="Documentation">📖</a> <a href="https://github.com/search?type=issues&q=is%3Aissue+author%3AFabianHofmann+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Afluxopt%2Fspecsolve+created%3A%3C2026-08-21%29%29&s=created&o=desc" title="Bug reports">🐛</a> <a href="https://github.com/search?type=issues&q=is%3Aissue+author%3AFabianHofmann+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Afluxopt%2Fspecsolve+created%3A%3C2026-08-21%29%29&s=created&o=desc" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+reviewed-by%3AFabianHofmann+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Afluxopt%2Fspecsolve+created%3A%3C2026-08-21%29%29&s=created&o=desc" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+author%3AFabianHofmann+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Afluxopt%2Fspecsolve+created%3A%3C2026-08-21%29%29&s=created&o=desc" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/coroa"><img src="https://avatars.githubusercontent.com/u/2552981?v=4&size=100" width="100px" height="100px" alt="Jonas Hörsch"/><br /><sub><b>Jonas Hörsch</b></sub></a><br /><a href="https://github.com/energy-models/mathspec/commits?author=coroa" title="Code">💻</a> <a href="#ideas-coroa" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/energy-models/mathspec/pulls?q=is%3Apr+reviewed-by%3Acoroa" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.pfenninger.org"><img src="https://avatars.githubusercontent.com/u/141709?v=4&size=100" width="100px" height="100px" alt="Stefan Pfenninger-Lee"/><br /><sub><b>Stefan Pfenninger-Lee</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Asjpfenninger+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+reviewed-by%3Asjpfenninger+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2023-01-01..2026-08-13%29%29&s=created&o=desc" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://orcid.org/0000-0003-2288-6423"><img src="https://avatars.githubusercontent.com/u/72193617?v=4&size=100" width="100px" height="100px" alt="Ivan Ruiz Manuel"/><br /><sub><b>Ivan Ruiz Manuel</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Airm-codebase+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/search?type=pullrequests&q=is%3Apr+reviewed-by%3Airm-codebase+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2023-01-01..2026-08-13%29%29&s=created&o=desc" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://cp.ethz.ch/people/person-detail.tim-troendle.html"><img src="https://avatars.githubusercontent.com/u/3090386?v=4&size=100" width="100px" height="100px" alt="Tim Tröndle"/><br /><sub><b>Tim Tröndle</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Atimtroendle+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jnnr"><img src="https://avatars.githubusercontent.com/u/32454596?v=4&size=100" width="100px" height="100px" alt="Jann Launer"/><br /><sub><b>Jann Launer</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Ajnnr+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Ajnnr+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.flombardi.org"><img src="https://avatars.githubusercontent.com/u/26432077?v=4&size=100" width="100px" height="100px" alt="Francesco Lombardi"/><br /><sub><b>Francesco Lombardi</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3AFLomb+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jmorrisnrel"><img src="https://avatars.githubusercontent.com/u/90803675?v=4&size=100" width="100px" height="100px" alt="James Morris"/><br /><sub><b>James Morris</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Ajmorrisnrel+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/sstroemer"><img src="https://avatars.githubusercontent.com/u/8915976?v=4&size=100" width="100px" height="100px" alt="Stefan Strömer"/><br /><sub><b>Stefan Strömer</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3Asstroemer+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://portalrecerca.uab.cat/en/persons/alexander-de-tom%C3%A1s-pascual"><img src="https://avatars.githubusercontent.com/u/79085248?v=4&size=100" width="100px" height="100px" alt="Alexander de Tomás Pascual"/><br /><sub><b>Alexander de Tomás Pascual</b></sub></a><br /><a href="https://github.com/search?type=issues&q=is%3Aissue+author%3ALexPascal+%28repo%3Aenergy-models%2Fmathspec+OR+%28repo%3Acalliope-project%2Fcalliope+created%3A2018-04-16..2026-08-13%29%29&s=created&o=desc" title="Bug reports">🐛</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## Licence

The code is [MIT](https://github.com/energy-models/mathspec/blob/main/LICENSE), and the prose is
[CC-BY-4.0](https://github.com/energy-models/mathspec/blob/main/LICENSES/CC-BY-4.0.txt).
