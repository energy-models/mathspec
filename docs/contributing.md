<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Contributing

This guide shows how to report a bug, set up a clone of mathspec, change it,
and submit the change. You need git and a GitHub account.

## Report a bug or ask a question

<div class="grid cards" markdown>

- [:material-bug: Report a bug](https://github.com/energy-models/mathspec/issues/new?template=BUG-REPORT.yml)
- [:material-file-document: Report a docs issue](https://github.com/energy-models/mathspec/issues/new?template=DOCS.yml)
- [:material-lightbulb-on: Request a change](https://github.com/energy-models/mathspec/issues/new?template=FEATURE-REQUEST.yml)
- [:material-chat-question: Ask a question](https://github.com/energy-models/mathspec/discussions)

</div>

To find a first change to make, start with the
[good first issues](https://github.com/energy-models/mathspec/contribute).

## Setting up a development environment

Every command of the project runs in an environment and package manager
([pixi](https://pixi.prefix.dev/)), which installs Python and the tools that
the checks use.

Fork [the repository](https://github.com/energy-models/mathspec) on GitHub,
and clone your fork:

```sh
git clone https://github.com/<your-account>/mathspec.git
cd mathspec
```

Install pixi, as its
[official instructions](https://pixi.prefix.dev/latest/installation/) describe.
Then, in your clone, install the environment and the commit hooks:

```sh
pixi install
pixi run pre-commit-install
```

On every commit, the hooks format Python, Markdown, YAML and TOML. They also
lint and type-check the Python, check spelling, and check the licence headers.

To check that the environment works, run the test suite:

```sh
pixi run test
```

The run ends with a summary line that counts the passed tests and has no
`failed` count.

## Run the checks before you push

To run the checks by hand, use these commands:

```sh
pixi run lint           # every commit hook, over every file
pixi run test           # the test suite
pixi run test-coverage  # the test suite, with a coverage report
pixi run compile-tex    # every spec in the tree, printed to standalone LaTeX and compiled
pixi run ci             # lint, test, a strict docs build and compile-tex
```

The checks on each pull request (CI) run the same four tasks as
`pixi run ci`. CI also checks the version headings in `CHANGELOG.md`.

## Change the documentation

The pages under `docs/` are Markdown, and a static site generator
([Zensical](https://zensical.org/)) builds them from `mkdocs.yml`. The build
is strict, so a dead link or a stale anchor fails it.

Each page is one of the four kinds that [Diátaxis](https://diataxis.fr)
defines, and its kind sets its folder:

- a tutorial, in `docs/tutorials/`
- a how-to guide, in `docs/howto/`
- reference, in `docs/reference/`, with the example pages in `docs/examples/`
- explanation, in `docs/about/`, which is the About section of the nav

A page that a spec writer does not need goes under Development in the nav.
The
[docs-writing skill](https://github.com/energy-models/mathspec/blob/main/.claude/skills/docs-writing/SKILL.md)
sets the rules that each kind meets. The
[prose-writing skill](https://github.com/energy-models/mathspec/blob/main/.claude/skills/prose-writing/SKILL.md)
sets the rules for sentences in pages, issues and PRs. Inside `docs/`, link
relatively. Outside it, write the full GitHub URL.

To preview the site while you edit, run:

```sh
pixi run docs-serve
```

The site is then at <http://127.0.0.1:8000>, and it rebuilds when you save a
page.

??? question "I have updated the README.md"

    The home page includes six named sections of the README, and not a copy:

    - the badges
    - the benefits
    - what a spec declares
    - the example spec
    - the engines
    - the status note

    A section is delimited in the README by
    `:::md <!--- --8<-- [start:name] -->` and
    `:::md <!--- --8<-- [end:name] -->`, and `docs/index.md` includes it with
    `:::md --8<-- "README.md:name"`. Edit inside the markers, and the next
    build shows the change.

    Keep the sections free of links, or link absolutely. A relative link
    resolves against `docs/index.md` on the site and against the repository
    root on GitHub, and only one of those can be right.

??? question "I have changed what a spec prints"

    A tool writes some blocks of the docs, and `tests/test_docs.py` lists
    every page that contains one in its `GENERATED` table. A test compares
    each block to its generator. To change a block, run its generator and read
    the diff:

    ```bash
    pixi run python -m tools.home_math       # docs/index.md and README.md, from examples/dispatch.yaml
    pixi run python -m tools.notation        # docs/reference/notation.md, from tests/typesetting/golden/model.yaml
    pixi run python -m tools.spec_math       # the operator table on docs/reference/language/operators.md
    pixi run python -m tools.gallery         # the example pages, from examples/
    pixi run python -m tools.expansion_math  # docs/howto/see-an-expansion.md, from tests/expand/
    ```

    Each of these tools takes `--check`, which reports drift and writes
    nothing. Two more sets of files are generated, and their failing tests
    print the same commands:

    ```bash
    pixi run python -m tools.schema              # schema/mathspec.schema.json
    pixi run python -m tests.typesetting.golden  # tests/typesetting/golden/*.out
    ```

??? question "I want to add a new page"

    Add a Markdown file under the folder of its kind, and add it to the `nav` key in `mkdocs.yml`:

    ```yaml
    nav:
      - How-to guides:
          - howto/index.md
          - My page: howto/my-page.md
    ```

    The page then appears under How-to guides. `pixi run test` fails for a
    page with no `nav` entry.

    The Python API has three fixed pages, and a new module gets no page of
    its own. A plugin that writes pages from docstrings
    ([mkdocstrings](https://mkdocstrings.github.io/)) renders the Spec API and
    Program API pages from the whole of `mathspec.spec` and
    `mathspec.program`. A new name in either module appears in the next
    build. A new name at the top level of
    `mathspec` needs its own `:::` entry on the
    [Python API](reference/api.md) page.

## What a new operator has to satisfy

A construct built into the language, which no file can add, is an
[operator](reference/glossary.md#operator). mathspec accepts a new operator
only when it meets these conditions:

- A template substituted into an expression
  ([a macro](reference/language/named.md#macros)) can call the operator.
  Everything a modeller passes to the operator is the value of a keyword
  argument, such as `over=snapshot`.
- It reads a bounded number of rows for each row of its result. It may filter
  rows on a column they already have, or join each row against a parameter or
  a relation. It may also read neighbouring rows at a fixed offset, or only
  the coordinate labels.
- If it reads every row, it reads them in one pass over the data. That pass
  ends before a tool that builds the model
  ([an engine](reference/glossary.md#tool)) builds its first chunk of rows.
- It does not call itself. mathspec refuses the same recursion in a macro
  and suggests which call to remove.

[New constructs](about/limits.md#new-constructs) explains the first two
conditions.

## Name the classes

One construct passes through three layers of the code. Each class name has a
suffix that identifies its layer:

| Layer                                                                | Suffix | Example                                |
| -------------------------------------------------------------------- | ------ | -------------------------------------- |
| YAML (`mathspec.spec`)                                               | `Spec` | `VariableSpec`, `PiecewiseSpec`        |
| Syntax (`mathspec._expression_parser`, `mathspec._condition_parser`) | `Node` | `NameNode`, `UnresolvedComparisonNode` |
| Program (`mathspec.program`)                                         | none   | `Variable`, `Piecewise`                |

In the program, the node for a use of a name ends in `Reference`.
`VariableReference` refers to a `Variable`, and `ExpressionReference` refers
to a `NamedExpression`.

A node class is named after the operation, not after the operator in the
file. One operator can resolve to two nodes:

| Operator           | Node                | Operation                                            |
| ------------------ | ------------------- | ---------------------------------------------------- |
| `sum(over=)`       | `Sum`               | a sum that removes the dimensions it names           |
| `sum(by=)`         | `Sum` over a `Join` | a join, and the sum over the axes that the join adds |
| `at(by=)`          | `Join`              | a join whose groups are one row, with no sum over it |
| `shift(along=)`    | `Translate`         | a re-index along one dimension                       |
| `sum_back(along=)` | `WindowSum`         | a sum over a trailing window                         |

No name is abbreviated, except the acronym `Sos` and the key `dims`.

## Add an operator

An operator has a class in every layer of the code, so you change each layer
in order:

1. Check that the operator meets the
   [conditions](#what-a-new-operator-has-to-satisfy).
1. Start with the grammar, which usually needs no change, because `f(x, k=v)`
   already parses.
1. Declare the signature in `_operators.BUILTINS`. The signature lists the
   keyword arguments by kind, and the usage line that a refusal quotes.
1. Write the node in `program.py`, and how `_expression_resolver.py` builds
   the node from the signature. Name the node class as
   [Name the classes](#name-the-classes) sets.
1. Write the dimension rule in `_dimensions.py`, and the degree rule in
   `_degree.py`.
1. Write how `_typesetting` prints the node in LaTeX, Typst and Markdown.
1. Call the operator in `tests/typesetting/golden/model.yaml`. A test fails
   until that file calls every operator.
1. Add the entry to the [language reference](reference/language/operators.md).

Then regenerate the golden files and the notation page, and read the diff:

```bash
pixi run python -m tests.typesetting.golden
pixi run python -m tools.notation
```

The operator is finished when three things are true:

- `to_spec` compiles it into the program.
- The typesetter prints it in all three formats.
- An engine builds the same model from a spec that uses the new operator and
  from that spec written out by hand.

## Submit a change

--8<-- "CONTRIBUTING.md:docs"

The pull request page then lists the CI checks. The change is ready for review
when every check passes.

!!! info "See also"

    - [CONTRIBUTING.md](https://github.com/energy-models/mathspec/blob/main/CONTRIBUTING.md),
      for the licence of a contribution
    - [AGENTS.md](https://github.com/energy-models/mathspec/blob/main/AGENTS.md),
      for what a change is held to and when to run each gate
    - [the limits of the language](about/limits.md), for the constructs mathspec
      refuses
