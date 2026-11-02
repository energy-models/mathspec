<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# File shape

A spec file is a YAML mapping, and this page lists its top-level keys and the
rules by which mathspec reads the YAML.

## Top-level keys

The top level of a spec file has **thirteen section keys**, plus `version` and
`description`. mathspec accepts any subset of the thirteen, so a file that
declares only `dimensions:` loads.

| Key           | What the section declares                                                                                          |
| ------------- | ------------------------------------------------------------------------------------------------------------------ |
| `given`       | what this file uses and another file declares ([given](parameters-variables-constraints.md#given))                 |
| `dimensions`  | the sets of labels that entries are indexed over ([dimensions](dimensions.md))                                     |
| `relations`   | named tables that map one dimension onto another ([relations](relations.md))                                       |
| `parameters`  | the data the spec expects ([parameters](parameters-variables-constraints.md#parameters))                           |
| `conditions`  | named conditions, used by name in a `where:`, a `when:` or a `holds:` ([conditions](named.md#conditions))          |
| `variables`   | what the solver decides ([variables](parameters-variables-constraints.md#variables))                               |
| `expressions` | named quantities, used again in the math and readable once the solver runs ([named expressions](named.md))         |
| `objective`   | what the solver minimises or maximises ([objective](parameters-variables-constraints.md#objective))                |
| `constraints` | the rules that the decisions obey ([constraints](parameters-variables-constraints.md#constraints))                 |
| `sos`         | sets of variables of which few may be non-zero ([special ordered sets, SOS](piecewise.md#sos))                     |
| `piecewise`   | piecewise-linear curves ([piecewise](piecewise.md))                                                                |
| `assumptions` | what the spec expects of its data ([assumptions](assumptions.md))                                                  |
| `macros`      | templates that take arguments, substituted into an expression before anything reads it ([macros](named.md#macros)) |

## `version`

`version` is the version of the language that the file is written against.
The key is optional and defaults to `{{ mathspec.language_version }}`, the one
version that mathspec {{ mathspec.release }} reads. The language version is
not the [version of the mathspec package](../../about/versions.md).

<!-- prettier-ignore -->
```yaml
version: {{ mathspec.language_version }}
```

A file with this line loads exactly as a file without it.

At load, mathspec refuses a version that it does not read:

```yaml
version: 1
dimensions:
  snapshot: { dtype: int }
```

```text
version: the spec declares version 1, and mathspec {{ mathspec.release }} understands [{{ mathspec.language_version }}]. Upgrade mathspec, or write the version this file targets.
```

In the message, mathspec prints its installed release and the versions of the language that it reads.

## `description`

`description` is optional free text that describes the spec, and the text
comes first in a [typeset document](../typeset.md), above the math.

```yaml
description: Least-cost dispatch of a generator fleet against an hourly load.
```

The value must be a string, and mathspec checks nothing else in it.

## Unknown keys

mathspec refuses an unknown key at load, at the top level and inside every
entry, and suggests the nearest valid key:

```yaml
dimensions:
  generator: { dtype: str }
variables:
  p:
    dims: [generator]
    boundz: { lower: 0 }
```

```text
variables.p: unknown key 'boundz' in a variable entry. Did you mean 'bounds'?
```

mathspec starts the message with the path to the entry, `variables.p`.

## How the YAML is read

mathspec reads the file by four rules, some of which other YAML readers do
not follow:

- The document is a mapping, so a list or a single value at the top level is
  refused.
- Only `true` and `false` are booleans, so `no: { dtype: str }` declares a
  dimension called `no`, and does not declare one called `false`.
- A key that appears twice in one mapping is refused, and mathspec names
  both lines, such as
  `spec.yaml:3: duplicate key 'generator', first declared on line 2. Rename or delete one.`
- mathspec applies YAML keys that copy another mapping (merge keys,
  `<<:`), and a key that the mapping declares
  itself overrides the merged value.

The last rule lets one entry reuse the keys of another:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
variables:
  p: &positive
    dims: [snapshot, generator]
    bounds: { lower: 0 }
  q:
    <<: *positive
    dims: [generator]
```

`q` takes the bounds of `p`, and its own `dims: [generator]` replaces the
`dims` that it merged.

!!! info "See also"

    - [the language](index.md) for the rules that every spec obeys
    - [errors and advice](errors.md) for what mathspec refuses at load
