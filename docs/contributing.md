<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Contributing

Report a bug, ask a question, or change mathspec itself.

## How to contribute

<div class="grid cards" markdown>

- [:material-bug: Report a bug](https://github.com/energy-models/mathspec/issues/new?template=BUG-REPORT.yml)
- [:material-file-document: Report a docs issue](https://github.com/energy-models/mathspec/issues/new?template=DOCS.yml)
- [:material-lightbulb-on: Request a change](https://github.com/energy-models/mathspec/issues/new?template=FEATURE-REQUEST.yml)
- [:material-chat-question: Ask a question](https://github.com/energy-models/mathspec/discussions)

</div>

The [good first issues](https://github.com/energy-models/mathspec/contribute)
are the bugs and feature requests to start with.

## Setting up a development environment

You run every command of the project in [pixi](https://pixi.prefix.dev/).

1. Install pixi following the
   [official instructions](https://pixi.prefix.dev/latest/installation/).
1. In your clone of the repository, install the environment and the commit hooks:

```sh
pixi install
pixi run pre-commit-install
```

On every commit, the hooks format Python, Markdown, YAML and TOML, lint and
type-check the Python, and check the licence headers. These commands
run the same checks, and the rest of what CI checks, by hand:

- `pixi run lint`: every commit hook, over every file.
- `pixi run test`: the test suite. `pixi run test-coverage` adds coverage.
- `pixi run compile-tex`: print every spec in the tree to standalone LaTeX and
  compile it.
- `pixi run ci`: lint, tests, a strict docs build and the LaTeX compile. This is
  what CI runs, so run it before you push.

## Documentation

The pages under `docs/` are Markdown, built by
[Zensical](https://zensical.org/) from `mkdocs.yml`. The build is strict: a
dead link or a stale anchor fails it. A page with no `nav` entry does not fail
the build, and `pixi run test` is what reports it. `pixi run docs-serve` builds
the site and serves it at <http://127.0.0.1:8000>, rebuilding when a page
changes.

??? question "I have updated the README.md"

    The home page includes named sections of the README rather than a copy: the
    badges, the benefits, the example spec, the engines and the status note. A section
    is delimited in the README by `:::md <!--- --8<-- [start:name] -->` and
    `:::md <!--- --8<-- [end:name] -->`, and `docs/index.md` pulls it in with
    `:::md --8<-- "README.md:name"`. Edit inside the markers, and the site
    follows.

    Keep the sections link-free, or link absolutely. A relative link resolves
    against `docs/index.md` on the site and against the repository root on GitHub,
    and only one of those can be right.

??? question "I have changed what a spec prints"

    Every page that carries a block a tool writes is listed in
    `tests/test_docs.py`'s `GENERATED` table, and a test compares each block to
    its generator. Regenerate rather than edit, and read the diff:

    ```bash
    pixi run python -m tools.home_math   # docs/index.md and README.md, from examples/dispatch.yaml
    pixi run python -m tools.notation    # docs/reference/notation.md, from tests/typesetting/golden/model.yaml
    pixi run python -m tools.spec_math   # the operator table on docs/reference/language/operators.md
    pixi run python -m tools.gallery     # the example pages, from examples/
    ```

    Each tool takes `--check` to report drift without writing.

??? question "I want to add a new page"

    Add a Markdown file under `docs/`, then add it to the `nav` key in
    `mkdocs.yml`:

    ```yaml
    nav:
      - Home: index.md
      - My Page: my-page.md
    ```

    The module pages under Development are generated from the docstrings, so a
    new module appears in the next build. A new public name also needs its own
    `:::` entry on the [Python API](reference/api.md) page.

## Naming across the layers

The same construct passes through three layers, and each layer names it in full
with a suffix that says which layer it is:

| Layer                        | Suffix               | Example                                |
| ---------------------------- | -------------------- | -------------------------------------- |
| YAML block (`mathspec.spec`) | `Block`              | `VariableBlock`, `PiecewiseBlock`      |
| Syntax (`mathspec.*_parser`) | `Node`               | `NameNode`, `UnresolvedComparisonNode` |
| Program (`mathspec.program`) | none / `Declaration` | `Variable`, `VariableDeclaration`      |

A node names the operation, not the function a file writes. One function can
resolve to two nodes, so the spelling in the file cannot decide the name.

| File verb          | Node                | What the node names                                  |
| ------------------ | ------------------- | ---------------------------------------------------- |
| `sum(over=)`       | `Sum`               | axes removed from the result                         |
| `sum(by=)`         | `Sum` over a `Join` | a join, and the sum over the axes that the join adds |
| `at(by=)`          | `Join`              | a join whose groups are one row, with no sum over it |
| `shift(along=)`    | `Translate`         | a re-index along one dimension                       |
| `sum_back(along=)` | `WindowSum`         | a sum over a trailing window                         |

No name is abbreviated.

## Adding an operator

Start with the grammar, which usually needs no change because `f(x, k=v)`
already parses. Then declare the signature in `operators.BUILTINS`. The
signature holds the number of arguments and says which arguments name
dimensions, and resolution reads it from there. Then write the node in
`program.py` and how resolution builds it, the dimension rule in
`dimensions.py`, the degree rule in `degree.py`, and the entry in the
[language reference](reference/language/operators.md).

## Submitting changes

--8<-- "CONTRIBUTING.md:docs"
