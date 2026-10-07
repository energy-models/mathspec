<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Check a spec without data

Catch a broken spec file before you attach data or call a solver, on your
machine and in CI.

1. **Run the check on one file.**

   ```bash
   python -m mathspec check spec.yaml
   ```

   A refusal prints its message on stderr and exits with status 1:

   ```text
   variables.p: unknown key 'boundz' in a variable entry. Did you mean 'bounds'?
   ```

   Advice is a note that does not stop the file from loading, so it prints on
   stdout and the command exits with status 0. A spec with no refusal and no
   advice prints nothing.

   ```text
   Variable 'slack' makes this spec unbounded: no constraint names it, and bounds.lower is open, and the +slack term in the minimize objective improves toward it.
   Give it a finite bounds.lower, or the constraint that was meant to define it.
   ```

2. **Run it over every spec in CI.** A refusal exits with status 1, so a
   shell loop is enough to fail the job:

   ```bash
   for spec in specs/*.yaml; do python -m mathspec check "$spec" || exit 1; done
   ```

3. **Ask from Python** where the check is one step of a longer script.
   [`to_spec`](../reference/api.md#loading) raises a `MathSpecError` for
   anything the language refuses, and [`advice`](../reference/api.md#advice)
   returns what it would print:

   ```python
   import mathspec as ms

   for note in ms.advice('spec.yaml'):
       print(note)
   ```

Without Python, the JSON schema checks the structure of the file, but nothing
inside an `expression:` or `where:` string
([editor completion and offline checking](installation.md#editor-completion-and-offline-checking)).
