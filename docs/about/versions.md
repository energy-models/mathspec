<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Versions

mathspec numbers its releases and its file format separately, because most
releases change the package and leave the file format alone.

## The package version and the language version

The **package version** numbers a release of mathspec, such as the latest,
`{{ mathspec.release }}`. The release workflow reads it from the
[git tag](https://github.com/energy-models/mathspec/blob/main/RELEASING.md#the-version).
So the tag, the changelog heading and the package file (wheel) on the Python
Package Index (PyPI) all have the same number.

The **language version** numbers the file format. A file states a
specification of an optimisation model ([a spec](../reference/glossary.md#spec))
and declares its language version in the top-level
[`version:` key](../reference/language/file.md#version). The language version
changes only when what the language accepts changes. Language version `0` is unstable. Any release can change what a version-`0`
file means, or stop loading it.

## Why not one number

With one number, a file would declare
the release of mathspec it was written for. Suppose a release fixes how the
[typesetter](../reference/typeset.md) prints a sum, and changes nothing that a
file means. With one number, every file would have to declare the new
release, or mathspec would need a list of the releases that changed the
format. That list is the language version.

With two numbers, a file whose language version is 1 or above loads in every
release of mathspec that reads that version. You change the `version:` line of a file only when the
language version changes. At load, mathspec
[refuses a language version](../reference/language/file.md#version) that the
installed release does not read.

You can now judge why a file declares the language version and not the
release, and why most releases leave a file untouched.

!!! info "See also"

    - [pin the version](../howto/installation.md#pin-the-version), for how a spec
      file and a tool each [pin](../reference/glossary.md#pin) a number
    - [`version`](../reference/language/file.md#version), for what the key
      accepts and the message for a version that a release does not read
    - [the changelog](../reference/changelog.md), for what each release changed
