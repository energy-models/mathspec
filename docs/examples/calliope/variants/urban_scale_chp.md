<!--
SPDX-FileCopyrightText: Calliope contributors
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0 AND Apache-2.0
-->

# The urban-scale CHP patch

A patch of [Calliope in fragments](../index.md). What the urban-scale example changes in the base: `balance_conversion` holds for every conversion technology but `chp`. Its rows are [the urban-scale fragment](../extensions/urban_scale_chp.md). A patch is not a spec, so it prints as the declarations it writes, in the spec it lands on.

<!-- gallery:begin -->
```python
ms.override(
    ms.merge(base + ['extensions/urban_scale_chp.yaml']),
    ['variants/urban_scale_chp.yaml'],
)
```

```yaml title="variants/urban_scale_chp.yaml"
constraints:
  balance_conversion:
    description: >-
      `balance_conversion` for every conversion technology but `chp` — it
      puts out, before its losses, what it takes in after them
    where: base_tech == 'conversion' AND NOT include_storage AND NOT techs == chp
```

**`balance_conversion`**

```math
\sum_{c \in \mathcal{C}} \mathit{flow\_out\_inc\_eff}_{n,i,c,t} = \sum_{c \in \mathcal{C}} \mathit{flow\_in\_inc\_eff}_{n,i,c,t} \qquad \forall\, n \in \mathcal{N},\ i \in \mathcal{I},\ t \in \mathcal{T} \,:\, \mathrm{base\_tech}_{i} = \text{'}\mathrm{conversion}\text{'} \wedge \neg \mathrm{include\_storage}_{n,i} \wedge \neg \left( i = \text{'}\mathrm{chp}\text{'} \right)
```
<!-- gallery:end -->
