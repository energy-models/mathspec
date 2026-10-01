<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Fix a quantity that is data in one model and a decision in another

Write one spec in which a quantity, such as a plant's size, is chosen by the
solver in one study and given by the data in another. There are two ways:

- **Pin it in the data** where the solver may keep the quantity as a variable.
  The file and the call stay the same, and equal bounds hold the variable at
  one value.
- **Fix it with `spec.fix`** where the model must not have the variable: a
  Benders subproblem, a myopic step or a rolling window. The quantity becomes
  a parameter, so `size * on` is linear and `size` may stand in a bound.

## Equal bounds in the data

1. **Declare the quantity as a variable, with named bounds.**

   ```yaml
   dimensions:
     plant: { dtype: str }
   parameters:
     size_min: { dims: [plant] }
     size_max: { dims: [plant] }
   variables:
     size:
       dims: [plant]
       bounds: { lower: size_min, upper: size_max }
   ```

2. **Write every rule against the variable.** `rate - relmax * size <= 0` is
   one equation whether `size` is chosen or given.

3. **Pin it in the data where it is given.** Attach `size_min` and `size_max` as
   the same value for a plant whose size is fixed. Equal bounds pin a variable
   ([variables](../reference/language/declarations.md#variables)).

A pinned variable is still a variable: `size * on` is `variable * variable`,
and `size` cannot stand in another variable's `bounds:`. Where a bound has to
come from it, fix it with `spec.fix`.

## `spec.fix`

1. **Write the spec with the quantity as a variable.** Here `size` exists only
   for a candidate plant:

   ```yaml
   version: 0
   dimensions:
     plant: { dtype: str }
     snapshot: { dtype: int }
   parameters:
     size_min: { dims: [plant] }
     size_max: { dims: [plant] }
     relmax: { dims: [snapshot, plant] }
     demand: { dims: [snapshot] }
     invest: { dims: [plant] }
     fuel: { dims: [plant] }
     candidate: { dims: [plant], dtype: bool }
   variables:
     size:
       dims: [plant]
       where: candidate
       bounds: { lower: size_min, upper: size_max }
     rate:
       dims: [snapshot, plant]
       bounds: { lower: 0 }
   constraints:
     capacity:
       dims: [snapshot, plant]
       expression: rate - relmax * size <= 0
     supply:
       dims: [snapshot]
       expression: sum(rate, over=plant) >= demand
   objective:
     sense: minimize
     expression: sum(invest * size) + sum(fuel * rate)
   ```

2. **Call [`spec.fix`](../reference/api.md#mathspec.Spec.fix) with every name
   to fix, in one call.**

   ```python
   import mathspec as ms

   subproblem = ms.to_spec('plant.yaml').fix('size')
   ```

   The spec it returns differs from the file in three places:

   ```yaml
   parameters:
     size: { dims: [plant], dtype: float }
   constraints:
     capacity:
       dims: [snapshot, plant]
       where: candidate
       expression: rate - relmax * size <= 0
   assumptions:
     size_within_bounds:
       holds: size >= size_min AND size <= size_max
       where: candidate
   ```

   - **`size` is a parameter under the same name**, so every expression goes
     on reading it. A `binary` or `integer` variable becomes an `int`
     parameter.
   - **The bounds become an assumption** on the numbers you attach.
   - **A row that reads `size` outside a sum takes its mask.** `size` did not
     exist outside `candidate`, so `capacity` was not built there. As a
     parameter, `size` would read `0` there, and the row would stand.
   - **A constraint that named only fixed variables becomes an assumption**
     under its own name, because it now compares numbers.

3. **Attach `size` as data**, one value for each candidate plant, as for any
   parameter.

4. **Where the call is refused, guard the read.** A read in a case, or through
   a shift or a relation, does not take the mask. Here `capacity` reads `size`
   through a case:

   ```yaml
   expressions:
     room:
       dims: [snapshot, plant]
       cases:
         running: { when: relmax > 0, expression: relmax * size }
       otherwise: 0
   ```

   ```text
   fix: constraint 'capacity' reads 'size' outside a sum, in a case. No mask there keeps out the rows where 'size' is absent, so as a parameter it would read 0 and those rows would stand. Guard the read with the variable's own where:, or declare absence: zero if it is zero there.
   ```

   Write the variable's mask into the case, `when: candidate AND relmax > 0`,
   and the call succeeds.
