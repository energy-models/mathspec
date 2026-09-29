<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# The CHP patch

A patch of [Calliope in fragments](../index.md). What Calliope's example `chp_htp.yaml` changes in the base: `balance_conversion` holds only for a plant with no turbine type. Its rows are [the CHP fragment](../extensions/chp_htp.md). A patch is not a spec, so it prints as the declarations it writes, in the spec it lands on.

<!-- gallery:begin -->
```python
ms.override(
    ms.merge(base + ['extensions/chp_htp.yaml']),
    ['variants/chp_htp.yaml'],
)
```

```yaml title="variants/chp_htp.yaml"
constraints:
  balance_conversion:
    description: >-
      `balance_conversion` for a plant with no turbine type — a conversion
      technology puts out, before its losses, what it takes in after them.
      Extraction and backpressure plants have rows of their own
    where: base_tech == 'conversion' AND NOT include_storage AND NOT turbine_type
```

**`balance_conversion`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_out\_inc\_eff}_{n,i,c,t} = \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{conversion}\text{'} \wedge \neg \mathrm{include\_storage}_{n,i} \wedge \neg \left( \mathrm{turbine\_type}_{n,i} \text{ is defined} \right)
```
<!-- gallery:end -->
