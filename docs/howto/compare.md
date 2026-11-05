<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Compare two specs

This guide shows how to diff two specification files
([specs](../reference/glossary.md#spec)) so that the diff contains only what
the two specs state differently. You need mathspec
[installed](installation.md) and two spec files that load.

## Write a spec in the canonical form

Write one spec in one fixed layout for a spec
([the canonical form](../reference/glossary.md#canonical-form)), to standard
output (stdout), or to a file with `-o canonical.yaml`. Here
`spec.yaml` is the base spec on
[composing specs](../reference/composition.md#override), a least-cost dispatch
spec:

=== "Command line"

    ```bash
    python -m mathspec canonical spec.yaml
    ```

=== "Python"

    ```python
    import mathspec as ms

    print(ms.to_spec('spec.yaml').to_yaml(canonical=True), end='')
    ```

```text
version: {{ mathspec.language_version }}
dimensions:
  generator: {dtype: str}
  snapshot: {dtype: int}
parameters:
  capacity: {dims: [generator], dtype: float}
  cost: {dims: [generator], dtype: float}
  load: {dims: [snapshot], dtype: float}
variables:
  dispatch:
    dims: [snapshot, generator]
    bounds: {lower: 0.0, upper: capacity}
    domain: continuous
    missing: absent
objective:
  sense: minimize
  expression: sum(cost * dispatch)
constraints:
  power_balance:
    dims: [snapshot]
    expression: sum(dispatch, over=generator) == load
```

The sections come in a fixed order, the names within a section are sorted,
and `dispatch` has its defaults `domain: continuous` and `missing: absent`
written out. The objective is `sum(cost * dispatch)`, although the file has
`sum(dispatch * cost)`, because mathspec writes the factors of a product in a
fixed order.

Keep this Python session open, because later steps use `ms`.

## Diff two files

Write both specs in the canonical form, and diff the two. Here `before.yaml`
is the `spec.yaml` above, and in `after.yaml` the objective has twice the
cost:

=== "Command line"

    ```bash
    python -m mathspec diff before.yaml after.yaml
    ```

=== "Python"

    ```python
    import difflib

    before = ms.to_spec('before.yaml').to_yaml(canonical=True)
    after = ms.to_spec('after.yaml').to_yaml(canonical=True)
    diff = difflib.unified_diff(before.splitlines(True), after.splitlines(True), 'before.yaml', 'after.yaml')
    print(''.join(diff), end='')
    ```

```diff
--- before.yaml
+++ after.yaml
@@ -14,7 +14,7 @@
     missing: absent
 objective:
   sense: minimize
-  expression: sum(cost * dispatch)
+  expression: sum((2 * cost) * dispatch)
 constraints:
   power_balance:
     dims: [snapshot]
```

The one changed line is the objective, with the factor 2 in brackets. When
the specs differ, the command exits with status 1, and the
[command line reference](../reference/cli.md#diff) lists every exit status. In
Python, where the specs differ, `before == after` is `False`.

## Make `git diff` show the canonical form

<!-- prettier-ignore -->
1. Tell git which files are specs, and which command writes them out:

    ```bash
    echo 'specs/*.yaml diff=mathspec' >> .gitattributes
    git config diff.mathspec.textconv "python -m mathspec canonical"
    ```

2. Run `git diff` as usual. `git diff` now shows no difference for a change
    that writes `sum(dispatch * cost)` as `sum(cost * dispatch)`, and one line
    for a change that doubles a coefficient. After the header lines, `git diff`
    prints:

    ```diff
    @@ -14,7 +14,7 @@ variables:
         missing: absent
     objective:
       sense: minimize
    -  expression: sum(cost * dispatch)
    +  expression: sum((2 * cost) * dispatch)
     constraints:
       power_balance:
         dims: [snapshot]
    ```

The files in the repository stay as you wrote them, with their comments, and
only the diff changes.

!!! warning

    Match only spec files in `.gitattributes`, because git runs the command on
    every file that the pattern matches. mathspec refuses a YAML file that is
    not a spec, so `git diff` shows the refusal for that file.

## Check in CI that a change leaves the spec the same

To check that a change only moves declarations or reorders the terms of a sum,
run a continuous integration (CI) job. In the job, write out the file on the main
branch and compare that file with the file in the change:

```bash
git show origin/main:spec.yaml > before.yaml
python -m mathspec diff before.yaml spec.yaml
```

The job fails when the two specs differ, and the log of the job lists the
lines that changed.

!!! info "See also"

    - [`canonical`](../reference/cli.md#canonical), for the options of the
      command.
    - [`diff`](../reference/cli.md#diff), for the options and exit status of the
      command.
    - [Comparing two specs](../reference/reading.md#comparing-two-specs), for what
      mathspec sorts when it writes the canonical form.
