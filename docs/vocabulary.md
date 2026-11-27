<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# The words of mathspec, specsolve and datarecord

This page is a worksheet and is not for merge. It records the word each
package uses for one meaning, one meaning per line, so that a comment or an
edit applies to one row.

- mathspec and specsolve are read from `main`, at `5f1464c` and `eca6957`.
- datarecord is read from the branch of
  [energy-models/datarecord#144](https://github.com/energy-models/datarecord/pull/144),
  at `6272e07`, and not from its `main`.
- A word in _italics_ exists only in an open mathspec pull request or issue.
- An empty cell means that the package has no word.

| Status | Meaning                                                     |
| ------ | ----------------------------------------------------------- |
| 🔴     | mismatch: different words for the same thing                |
| 🟢     | aligned: every package that has a word uses the same one    |
| 🔵     | kept apart: different things, so different words on purpose |
| ⚪     | one package only                                            |

## One meaning per line

The site colours each word by the status of its row, and the buttons show the
rows of one status.

<div id="vocabulary-filter"></div>

<!-- prettier-ignore-start -->
| Meaning | mathspec | specsolve | datarecord | Status | Note | Agreed word | Decided in |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a dimension whose labels are tuples | _tuple dimension_, _multi-dim_ | | multi-dimension | 🔴 | mathspec has not picked a word ([#1011](https://github.com/energy-models/mathspec/issues/1011)) | | |
| one part of a tuple label, such as `bus` of `connection` | column, `role` in the code, _member_ | column | field | 🔴 | datarecord#144 waits on mathspec | | |
| the labels of one dimension, in order, as data | | index | axis | 🔴 | both words mean something else in another package, as the second table shows | | |
| the dimension that the values of a property or a map are labels of | `values:`, _`dim:`_ | `values:` | `refers` | 🔴 | open in [#1000](https://github.com/energy-models/mathspec/issues/1000) | | |
| the value where the data has no row | `missing:` | `missing:` | `default` | 🔴 | on hold until [#940](https://github.com/energy-models/mathspec/issues/940) | | |
| one named item of the declaration | entry | declaration | "a spec" | 🔴 | in datarecord an `AttributeSpec` or a `PropertySpec` | | |
| the condition that narrows an entry | condition, `where:` | mask | | 🔴 | the mathspec prose rules avoid "mask" | | |
| a construct built into the language | operator | primitive | | 🔴 | the mathspec prose rules say "never primitive" | | |
| a table held in memory | table | table, frame | frame | 🔴 | "frame" means something else in mathspec | | |
| any software that reads the artefact | tool | | reader | 🔴 | "tool" means something else in datarecord | | |
| software that builds the model from data | engine | engine | framework | 🔴 | datarecord says "engine" for DuckDB | | |
| a set of labels that things are indexed over | dimension | dimension | dimension | 🟢 | "dim" on datarecord `main` | | |
| one member of that set | label | label | label | 🟢 | | | |
| one position across all the dimensions of an entry | coordinate | coordinate | coordinate | 🟢 | "point" on datarecord `main` | | |
| the labels a dimension allows, listed in the declaration | `one_of` | `one_of` | `one_of` | 🟢 | | | |
| no value at a coordinate | absent | absent | | 🟢 | | | |
| the problem stated without data | spec | spec | | 🟢 | | | |
| a spec with data, which a solver takes | model | model | model | 🟢 | | | |
| to combine data with a spec | attach | attach | | 🟢 | | | |
| to say no and give the rewrite | refuse | refuse | refuse | 🟢 | | | |
| a modelling framework such as PyPSA | framework | | framework | 🟢 | | | |
| the list of combinations that exist | bare relation | relation | multi-dimension | 🔵 | the same table of tuples, an index only in datarecord ([#1000](https://github.com/energy-models/mathspec/issues/1000)) | | |
| a label of another dimension, per row | relation with `values:`, _mapping_ | relation | property | 🔵 | a property may also be a number or text ([#1000](https://github.com/energy-models/mathspec/issues/1000)) | | |
| input numbers over dimensions | parameter | parameter | attribute | 🔵 | recorded as different in [#1000](https://github.com/energy-models/mathspec/issues/1000) | | |
| what the solver decides | variable | variable | attribute | 🔵 | datarecord stores the results of a solve as attributes | | |
| a dimension whose labels are single values | | | flat dimension | ⚪ | new in datarecord#144 | | |
| the dimensions an entry is indexed over, as a noun | frame | | | ⚪ | mathspec and datarecord both say "indexed over" | | |
| what data may exist, and its types | | | schema | ⚪ | | | |
| a module that translates to one framework | | | tool | ⚪ | | | |
<!-- prettier-ignore-end -->

## One word per line

Each word below has more than one meaning across the three packages. The site
colours a meaning green where another package states it in the same words, and
red where no other package does.

<!-- prettier-ignore-start -->
| Word | mathspec | specsolve | datarecord | Agreed | Decided in |
| --- | --- | --- | --- | --- | --- |
| axis | an index that a join opens (`Axis`) | how a sweep splits the data (`EachWindow`) | the labels of a dimension in one record, in order | | |
| index | the subscript letter of a dimension in printed math | the labels of a dimension, in order | the key columns of the owner map | | |
| frame | the dimensions an entry is indexed over | a DataFrame | a DataFrame | | |
| relation | an entry under `relations:` | an entry under `relations:` | a DuckDB relation object | | |
| tool | any software that reads a spec | | a module under `datarecord.tools` | | |
| engine | a tool that attaches data and builds the model | a tool that attaches data and builds the model | DuckDB | | |
| spec | the problem stated without data | the problem stated without data | one `AttributeSpec` or `PropertySpec` | | |
| member | a label of a dimension, _one part of a tuple_ | | not to be written for a label | | |
<!-- prettier-ignore-end -->
