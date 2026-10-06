<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# File shape

A spec file is a YAML mapping with **twelve declaration keys**, plus
`version` and `description`, and any subset of the twelve is accepted.

| Key           |                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------- |
| `dimensions`  | the dimensions ([dimensions](dimensions.md))                                                      |
| `relations`   | named relations between dimensions ([relations](relations.md))                                    |
| `parameters`  | the data the spec expects ([declarations](declarations.md))                                       |
| `variables`   | what the solver decides                                                                           |
| `given`       | what this file reads but does not build ([given](declarations.md#given))                          |
| `constraints` | the rules those decisions obey                                                                    |
| `objective`   | what is minimised or maximised                                                                    |
| `expressions` | named quantities, reusable in the math and readable after a solve ([named expressions](named.md)) |
| `macros`      | templates that take arguments ([macros](named.md#macros))                                         |
| `piecewise`   | piecewise-linear curves ([piecewise](piecewise.md))                                               |
| `sos`         | special-ordered sets ([sos](piecewise.md#sos))                                                    |
| `assumptions` | what the spec expects of its data ([assumptions](assumptions.md))                                 |

A file with no `objective` is a **feasibility problem**: it asks whether the
constraints can all be met.

## `description`

`description` is free text that says what the spec is. It is optional, and a
[typeset document](../typeset.md) prints it first.

```yaml
description: Least-cost dispatch of a generator fleet against an hourly load.
```

## `version`

`version` names the language version the file is written against. It is
optional and defaults to `0`, the one version this release knows, and it is not
the package version ([versions](../../about/versions.md)).

```yaml
version: 0
```

A version this release does not know is a load error:

```text
version: the spec declares version 1, and mathspec 0.0.0a127 understands [0].
Upgrade mathspec, or write the version this file targets.
```

## Unknown keys

An unknown key is a load error, at the top level and inside every declaration,
and the message names the nearest valid key:

```text
unknown key 'boundz' … Did you mean 'bounds'?
```

## How the YAML is read

- The document is a mapping.
- Only `true` and `false` are booleans, so `no: {dtype: str}` is a dimension
  called `no`.
- A duplicate key is a load error, and the message names both lines.
- The loader applies `<<:` merge keys, and a key the mapping declares itself
  overrides the merged value.
