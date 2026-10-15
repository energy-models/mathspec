<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# State a rule that differs by regime

Write one spec in which a rule takes a different form for some members of a
dimension, with no second file. Each group of members that shares one form is a
regime, and committable and non-committable generators are the usual case.

1. **Put the regime in the data.** A `bool` parameter says which members are
   in it; a `str` parameter names one of several:

   ```yaml
   parameters:
     committable: { dims: [generator], dtype: bool }
   ```

2. **Write one entry per regime, each under its own `where:`.** The entry
   builds rows only where its mask holds, so a regime that needs no row gets
   none:

   ```yaml
   dimensions:
     snapshot: { dtype: int }
     generator: { dtype: str }

   parameters:
     capacity: { dims: [generator] }
     min_output: { dims: [generator] }
     committable: { dims: [generator], dtype: bool }

   variables:
     dispatch: { dims: [snapshot, generator], bounds: { lower: 0, upper: capacity } }
     on: { dims: [snapshot, generator], where: committable, domain: binary }

   constraints:
     floor_committed:
       dims: [snapshot, generator]
       where: committable
       expression: dispatch >= min_output * on
     ceiling_committed:
       dims: [snapshot, generator]
       where: committable
       expression: dispatch <= capacity * on
   ```

   Here a non-committable generator is bounded by `capacity` alone, through the
   variable's `bounds:`. Where the other regime has a rule of its own, write
   it as a third entry under `where: "NOT committable"`.

3. **Where the regime changes a quantity rather than a rule, name the
   quantity with `cases:`** and write the rule once against it:

   ```yaml
   dimensions:
     snapshot: { dtype: int }
     generator: { dtype: str }

   parameters:
     capacity: { dims: [generator] }
     committable: { dims: [generator], dtype: bool }

   variables:
     dispatch: { dims: [snapshot, generator], bounds: { lower: 0 } }
     on: { dims: [snapshot, generator], where: committable, domain: binary }

   expressions:
     available:
       dims: [snapshot, generator]
       cases:
         committed:
           when: committable
           expression: capacity * on
       otherwise: capacity

   constraints:
     ceiling:
       dims: [snapshot, generator]
       expression: dispatch <= available
   ```

   `otherwise:` takes every coordinate the cases leave.

4. **Check it** with `python -m mathspec check spec.yaml`. The check refuses
   a pair of masks that can both hold, and a case with no `otherwise:`, with a
   message that names the rewrite.

What a `where:` means is under [absence](../reference/language/absence.md);
what `cases:` accepts is under
[named expressions](../reference/language/named.md#cases).
