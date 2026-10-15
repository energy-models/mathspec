<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Fix a quantity that is data in one model and a decision in another

Write one spec in which a quantity, such as a plant's size, is chosen by the
solver in one study and given by the data in another. The file stays the same
in both studies, and only the data changes.

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
   the same value for a plant whose size is fixed. Equal bounds pin a variable,
   which fixes it to that value
   ([variables](../reference/language/declarations.md#variables)).

A pinned variable is still a variable, so `size * on` is
`variable * variable`, and `size` cannot stand in the `bounds:` of another
variable. Where a bound must use the size, attach the size as a parameter too.
