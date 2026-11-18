<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# TIMES

TIMES is the long-term energy system model of the IEA's Energy Technology
Systems Analysis Programme (ETSAP), written in GAMS. These pages state parts
of its core equations as specs, each with the TIMES names it ports, read at
[TIMES `d9a6a25`](https://github.com/etsap-TIMES/TIMES_model/tree/d9a6a25).
The sets and coefficients that TIMES computes in its own data preparation,
such as `RTP_VINTYR` and `COEF_CPT`, arrive as data.

- **[Capacity transfer and capacity–activity](capacity.md)** states `EQ_CPT`
  and the upper form of `EQ_CAPACT`.
- **[Trade between regions](trade.md)** states `IRE_FLO` with a workaround,
  because mathspec refuses an entry over one dimension twice.

Issue [#969](https://github.com/energy-models/mathspec/issues/969) lists what
else a port of TIMES needs, and the workaround for each gap.
