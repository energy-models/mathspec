<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Write a piecewise curve out by hand

Tie a number of flows to one curve where that number is data: a boiler ties two
flows and a CHP (combined heat and power) unit ties three, in one spec. A
[`piecewise:`](../reference/language/piecewise.md) block lists its links in the
file, so the file fixes the number of flows. Write the formulation out by hand,
and the data sets the number of flows.

1. **Declare the weights as a variable over the breakpoint dimension**, masked
   to how far each curve runs:

   ```yaml
   variables:
     weight: # the convex combination, one per converter and period
       dims: [converter, time, bp]
       where: bp_present # how far each curve runs
       bounds: { lower: 0, upper: 1 }
   ```

2. **Restrict the weights with an `sos:` block.** `type: 2` lets at most two
   consecutive weights be non-zero, which is the restriction that `method: sos2`
   writes:

   ```yaml
   sos:
     on_one_segment: { variable: weight, along: bp, type: 2 }
   ```

3. **Write the convexity row, and one row per flow.** The relation
   `converter_of` maps each flow to its converter, so the data sets how many
   flows a converter has:

   ```yaml
   constraints:
     one_operating_point:
       dims: [converter, time]
       expression: sum(weight, over=bp) == 1
     on_the_curve: # one row per flow
       dims: [flow, time]
       expression: rate == sum(at(weight, by=converter_of, over=converter, into=flow) * bp_rate, over=bp)
   ```

A converter with a fourth flow is then one more row in the data.
