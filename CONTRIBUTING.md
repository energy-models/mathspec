<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Contributing guidelines

We're glad you're reading this; we welcome all contributors!

Some of the resources to look at if you're interested in contributing:

- Look at open issues tagged with ["help wanted"](https://github.com/energy-models/mathspec/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) and ["good first issue"](https://github.com/energy-models/mathspec/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- Look at the [contributing guide in our documentation](https://mathspec.readthedocs.io/en/latest/contributing/)

## Licensing

Copyright (c) 2026 mathspec contributors.
By contributing to mathspec, such as by opening a pull request, you represent that your contributions are your own original work and that you have the right to license them.
You also agree that your contributions are licensed under the MIT licence for code, and under the CC-BY-4.0 licence for documentation and prose.

## Reporting bugs and requesting features

You can open an issue on GitHub to report bugs or request new mathspec features.
Follow these links to submit your issue:

- [Report bugs or other problems while running mathspec](https://github.com/energy-models/mathspec/issues/new?template=BUG-REPORT.yml).
  If reporting an error, please include a full traceback in your issue.

- [Request features that mathspec does not already include](https://github.com/energy-models/mathspec/issues/new?template=FEATURE-REQUEST.yml).

- [Report missing or inconsistent information in our documentation](https://github.com/energy-models/mathspec/issues/new?template=DOCS.yml).

- [Any other issue](https://github.com/energy-models/mathspec/issues/new).

## Submitting changes

Look at the [development guide in our documentation](https://mathspec.readthedocs.io/en/latest/contributing/) for information on how to get set up for development.

<!--- the "--8<--" html comments define what part of this file to add to the index page of the documentation -->
<!--- --8<-- [start:docs] -->

To contribute a change:

1. Fork the repository and set up a development environment, as the [development guide](https://mathspec.readthedocs.io/en/latest/contributing/#setting-up-a-development-environment) describes.
1. In your clone, create a feature branch (`git checkout -b new-fix-or-feature`).
1. Commit your changes to the feature branch.
1. Push the branch to GitHub (`git push origin new-fix-or-feature`).
1. On GitHub, open a [pull request](https://github.com/energy-models/mathspec/pull/new/main) from the feature branch.

When you contribute for the first time, ask your reviewer to [add you as a contributor](https://allcontributors.org/en/bot/).

### Open a pull request

Before you open a pull request (PR), check that you have:

- Written the PR title as a conventional commit subject, as [Write the PR title](#write-the-pr-title) describes.
- Added the PR's line to `CHANGELOG.md`, if the PR needs one.
- Added or updated the documentation for your change.
- Added tests for new functionality.

In the PR body, summarise what changed and why.

### Write the PR title

Merges are squashed, so the **PR title** becomes the commit on `main`. Write it
so it also works as the line you add to `CHANGELOG.md` by hand. It must be a
[conventional commit](https://www.conventionalcommits.org) subject:

```text
<type>[(scope)]: <subject>

feat(language): a coordinate may declare its own label space
fix(parser): a where clause with a trailing comma loads
docs(language): a comparison on a relation is false where the relation has no row
```

A `feat`, `fix`, `perf`, `refactor`, `docs` or `revert` PR adds its title,
with a link to the PR, under `## Upcoming version` in `CHANGELOG.md`. A
`chore`, `test`, `ci`, `build` or `style` PR adds no line. The
`Conventional commit subject` check enforces the format on every pull request,
and the `Changelog line` check enforces the line. The label `no changelog`
opts a PR out of the second.
See [RELEASING.md](https://github.com/energy-models/mathspec/blob/main/RELEASING.md).

Beyond the subject line, write the body that the change needs: what changed,
and its impact.

### Follow the code conventions

The code follows the [Style Guide for Python Code (PEP 8)](https://www.python.org/dev/peps/pep-0008/).
The formatter and linter [`ruff`](https://docs.astral.sh/ruff/) applies the rules that `pyproject.toml` sets, such as the maximum line length.
The commit hooks run `ruff` on every commit.
You can also set up your editor to run `ruff` when you save a file, as the `ruff` documentation describes.

Write a docstring in the [Google docstring style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
In `src/`, `ruff` checks the form of each docstring, but it does not require a docstring on every name.

<!--- --8<-- [end:docs] -->

## Releases

A release is a PR that renames `## Upcoming version` in `CHANGELOG.md` to the
version and the day, such as `## 0.1.0 (2026-10-01)`. The PR also edits the
section into the release notes. When the PR merges, the release workflow tags the
release, opens the GitHub release and publishes the package to PyPI.

The version comes from the git tag at build time and is never written in the
source tree. `mathspec.__version__` returns it from the installed package
metadata.

See [RELEASING.md](https://github.com/energy-models/mathspec/blob/main/RELEASING.md) for the steps, what to do when one
fails, and the one-time repository setup.
