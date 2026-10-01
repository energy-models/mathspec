<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Fix a quantity that is data in one model and a decision in another

Write one spec in which a quantity, such as a plant's size, is chosen by the
solver in one study and given by the data in another. The file does not change
between the two. The data does.

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
come from it, ship the column as a parameter too.

## Fix it in the spec instead

Where a driver decides the quantity and the model it solves must not, call
[`spec.fix`](../reference/api.md#mathspec.Spec.fix). A Benders subproblem, a
myopic step and a rolling window each do this:

```python
subproblem = spec.fix('size')
```

`size` becomes a parameter under the same name, so every expression goes on
reading it. Its bounds become the assumption `size_within_bounds`. A
constraint that named only `size` becomes an assumption too, because it now
compares numbers. Where `size` has a `where:` and `absence: undefined`, each
row that reads it outside a sum has to stand under that mask: `fix` adds the
mask to a constraint's `where:`, or refuses and names the reader.
