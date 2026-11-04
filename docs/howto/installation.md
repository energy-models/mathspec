<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Install mathspec

This guide shows how to install mathspec, pin its version and set up your editor to complete the keys of a specification file
([spec](../reference/glossary.md#spec)). You need Python 3.12 or above.

## Install the package

Install the released package from the Python Package Index (PyPI) with the
tool that manages your environment:

=== "pip"

    ```bash
    pip install mathspec
    ```

=== "uv"

    ```bash
    uv add mathspec
    ```

=== "pixi"

    ```bash
    pixi add --pypi mathspec
    ```

The package is now installed in that environment, and you can
[check that it runs](#check-that-mathspec-runs) before you write a spec.

To work on mathspec itself from a clone, instead follow
[setting up a development environment](../contributing.md#setting-up-a-development-environment).

## Pin the version

The current language version is {{ mathspec.language_version }}, and the current release is {{ mathspec.release }}.
To pin what a spec file means, set its
[`version:` key](../reference/language/file.md#version) to the language
version you wrote it for. If you build software that reads a spec
([a tool](../reference/glossary.md#tool)) on the Python API, such as
specsolve, pin one exact mathspec release:

```bash
pip install mathspec=={{ mathspec.release }}
```

## Set up editor completion

mathspec ships the file
[`schema/mathspec.schema.json`](https://github.com/energy-models/mathspec/blob/v{{ mathspec.release }}/schema/mathspec.schema.json),
which lists the keys of a spec file in a machine-readable format description
(a [JSON Schema](https://json-schema.org)).
Your editor reads the schema to complete keys as you type. In VS Code:

<!-- prettier-ignore -->
1. Install the
    [Red Hat YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml).
2. In `.vscode/settings.json`, map the schema to your spec files for the whole
    workspace:

    ```jsonc
    // .vscode/settings.json
    "yaml.schemas": { "https://raw.githubusercontent.com/energy-models/mathspec/v{{ mathspec.release }}/schema/mathspec.schema.json": ["specs/*.yaml"] }
    ```

    To map the schema for one file only, instead put a comment with the schema
    address (a modeline) on the first line of that file:

    ```yaml
    # yaml-language-server: $schema=https://raw.githubusercontent.com/energy-models/mathspec/v{{ mathspec.release }}/schema/mathspec.schema.json
    ```

The editor now completes the keys of a spec file, and marks a key that the
schema does not list.

## Check that mathspec runs

Run the command line:

```bash
python -m mathspec --help
```

The command prints the six commands that mathspec has.

!!! info "See also"

    - [The command line reference](../reference/cli.md), for each command with its
      options.
    - [Versions](../about/versions.md), for why the language version and the
      release differ.
