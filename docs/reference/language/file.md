<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# File shape

A spec file is a YAML mapping with **thirteen section keys**, plus
`version` and `description`, and any subset of the thirteen is accepted.

| Key           |                                                                                                           |
| ------------- | --------------------------------------------------------------------------------------------------------- |
| `given`       | what this file reads but does not build ([given](parameters-variables-constraints.md#given))              |
| `dimensions`  | the dimensions ([dimensions](dimensions.md))                                                              |
| `relations`   | named relations between dimensions ([relations](relations.md))                                            |
| `parameters`  | the data the spec expects ([parameters](parameters-variables-constraints.md#parameters))                  |
| `conditions`  | named conditions, read by name in a `where:`, a `when:` or a `holds:` ([conditions](named.md#conditions)) |
| `variables`   | what the solver decides                                                                                   |
| `expressions` | named quantities, reusable in the math and readable after a solve ([named expressions](named.md))         |
| `objective`   | what is minimised or maximised                                                                            |
| `constraints` | the rules those decisions obey                                                                            |
| `sos`         | special-ordered sets ([sos](piecewise.md#sos))                                                            |
| `piecewise`   | piecewise-linear curves ([piecewise](piecewise.md))                                                       |
| `assumptions` | what the spec expects of its data ([assumptions](assumptions.md))                                         |
| `macros`      | templates that take arguments ([macros](named.md#macros))                                                 |

A file with no `objective` is a **feasibility problem**: it asks whether the
constraints can all be met.

The order of the sections, and the order of the entries in a section, change
nothing. `to_spec` sorts the entries of each section by name, and the entries
under each kind of `given:` too. The program, the typeset document and
`to_yaml()` list them in that order, so a file that declares `p` before `flow`
under `variables:` prints `flow` first.

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

An unknown key is a load error, at the top level and inside every entry,
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
