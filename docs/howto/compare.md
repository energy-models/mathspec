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

2. **Diff two files once.** Give each file to the command, and diff the two
   outputs:

   ```bash
   diff <(python -m mathspec canonical before.yaml) <(python -m mathspec canonical after.yaml)
   ```

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

4. **Keep specs in the canonical form in CI.** Then a plain diff of the files
   shows what the form shows, with no git setup. `--write` rewrites a file in
   the form, and drops its YAML comments because the form holds none:

   ```bash
   python -m mathspec canonical --write spec.yaml
   ```

   `--check` writes nothing, but exits with status 1 if the file is not in the
   form, and names the rewrite:

   ```text
   spec.yaml is not in the canonical form. Run `python -m mathspec canonical --write spec.yaml` to rewrite it.
   ```

   Check every spec, and fail the job if one of them fails:

   ```bash
   status=0
   for spec in specs/*.yaml; do python -m mathspec canonical --check "$spec" || status=1; done
   exit $status
   ```

5. **Compare from Python** where the comparison is one step of a longer
   script. [`to_yaml`](../reference/spec.md#mathspec.spec.Spec.to_yaml) writes the
   same text with `canonical=True`:

   ```python
   import mathspec as ms

   before = ms.to_spec('before.yaml').to_yaml(canonical=True)
   after = ms.to_spec('after.yaml').to_yaml(canonical=True)
   print(before == after)
   ```
