<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Compare two specs

Diff two spec files so that the diff shows only what the specs state
differently. A plain text diff also shows the order of entries, spacing
and the order of the terms in a sum. The **canonical form** is one fixed way
to write a spec, and it removes those differences. [Comparing two specs](../reference/reading.md#comparing-two-specs)
lists what the form sorts and what it keeps.

1. **Write one spec in the canonical form.**

   ```bash
   python -m mathspec canonical spec.yaml
   ```

   The command writes the form to stdout, or to a file with
   `-o canonical.yaml`. A file the language refuses prints its message on
   stderr and exits with status 1.

2. **Diff two files once.** Give both files to `diff`:

   ```bash
   python -m mathspec diff before.yaml after.yaml
   ```

   The command writes each spec in the canonical form and prints a unified
   diff of the two. It exits with status 0 when the specs are the same, and
   with status 1 when they differ, as `diff` does. A file the language refuses
   prints its message on stderr and exits with status 2.

3. **Make `git diff` show the canonical form.** Tell git which files are
   specs, and which command writes them out:

   ```bash
   echo 'specs/*.yaml diff=mathspec' >> .gitattributes
   git config diff.mathspec.textconv "python -m mathspec canonical"
   ```

   The files in the repository stay as you wrote them, and only the diff
   changes. A commit that writes `sum(dispatch * cost)` as
   `sum(cost * dispatch)` then shows no difference, and a commit that changes a
   coefficient shows one line:

   ```diff
    objective:
      sense: minimize
   -  expression: sum(cost * dispatch)
   +  expression: sum((2 * cost) * dispatch)
   ```

   Match only spec files in `.gitattributes`, because git runs the command on
   every file the pattern matches, and a YAML file that is not a spec fails to
   load.

4. **Check in CI that a change leaves the spec as it was.** A change that only
   moves declarations or reorders the terms of a sum states the same spec.
   Compare the file on the main branch with the file in the change:

   ```bash
   git show origin/main:spec.yaml > before.yaml
   python -m mathspec diff before.yaml spec.yaml
   ```

   The job fails when the specs differ, and its log shows the lines that
   changed. The files in the repository stay as you wrote them, with their
   comments. The same mathspec writes both forms when the job runs, so a new
   mathspec release does not make the job fail.

5. **Compare from Python** where the comparison is one step of a longer
   script. [`to_yaml`](../reference/spec.md#mathspec.spec.Spec.to_yaml) writes the
   same text with `canonical=True`:

   ```python
   import mathspec as ms

   before = ms.to_spec('before.yaml').to_yaml(canonical=True)
   after = ms.to_spec('after.yaml').to_yaml(canonical=True)
   print(before == after)
   ```
