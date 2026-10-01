<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# PyPSA, the relaxed commitment

Rungs 12, 44 and 47 of [PyPSA in one file](pypsa.md): `n.optimize(linearized_unit_commitment=True)`, stated on rungs 1 and 7
in a file of its own. Each network is the spine plus the script's own additions.

The file covers generators, links and loads with a fixed build, in one
scenario, with every asset active in every snapshot. Only a generator is
committable. A committable link or process, an extendable build, scenarios and
`active` are out of this file's scope. [PyPSA in one file](pypsa.md) states
them for the integer run, and the keyword relaxes them in the same way.

## Rung 12 — linearized unit commitment

| PyPSA                                                               | status | note                                                  |
| ------------------------------------------------------------------- | ------ | ----------------------------------------------------- |
| [`Generator-status`, `-start_up`, `-shut_down`](#variable-domains)  | done   | shares in [0, 1]                                      |
| [`Generator-com-p-before`](#generator-com-p-before)                 | done   | where start and stop cost the same — a data-prep bool |
| [`Generator-com-p-current`](#generator-com-p-current)               | done   |                                                       |
| [`Generator-com-partly-start-up`](#generator-com-partly-start-up)   | done   |                                                       |
| [`Generator-com-partly-shut-down`](#generator-com-partly-shut-down) | done   |                                                       |

<!-- gallery: examples/references/pypsa/rung_12_linearized_uc.py -->

## Rung 44 — the integer file's commitment rows, relaxed

`n.optimize(linearized_unit_commitment=True)` builds the same commitment rows as
the integer run, except the four tightening rows: the keyword only relaxes the
status, start and stop to shares in [0, 1] (`variables.py:81-88`) and adds the
tightening rows (`constraints.py:650`). So this file states each row that
[PyPSA in one file](pypsa.md) states for a fixed committable generator:

- A unit still serving the down time it brought in stays off
  (`constraints.py:622-628`).
- A ramp row stands where a unit has a ramp limit or only a start-up or
  shut-down ramp, and a missing limit reads as the full build
  (`constraints.py:1046-1055`). The earlier file built no row for a start-up
  ramp alone, and read a missing start-up or shut-down ramp as `0`, which kept
  a unit that came in off from starting.
- A maintainable unit is taken off for its events. The maintenance start stays
  a binary under the keyword (`variables.py:234-259`), and the product of
  status and maintenance enters the commitment rows through the `maint-status`
  rows (`constraints.py:425-458`). A maintainable unit that is not committable
  loses the same share of its fixed rows (`constraints.py:135-145`).

The rung adds five cheap units under a swinging load. A start costs more than a
stop, so PyPSA does not tighten them and the rung isolates these rows. Each
binds: PyPSA solves to `7400.0`. Without the brought-in down time it solves to
`6540.0`; without the start-up ramp, to `7164.0`; with the missing start-up and
shut-down ramps read as `0`, to `8060.0`; with the committable unit not
maintainable, to `7310.0`; with the fixed unit not maintainable, to `7100.0`.

| PyPSA                                                                                                                                                                                       | status | note                                                                           |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------ |
| [`Generator-com-status-min_down_time_must_stay_up`](#generator-com-status-min_down_time_must_stay_up)                                                                                       | done   |                                                                                |
| [`Generator-p-ramp_limit_up`](#generator-p-ramp_limit_up), [`-down`](#generator-p-ramp_limit_down) for a start-up or shut-down ramp alone, and a missing limit                              | done   | `Generator_ramp_up_rate` and the other three rates read a missing limit as `1` |
| [`Generator-maint-*`](#generator-maint-event-count), [`Generator-maint-status-*`](#generator-maint-status-le-status)                                                                        | done   | fixed units only, as the file states no extendable build                       |
| [`Generator-com-p-lower`](#generator-com-p-lower), [`-upper`](#generator-com-p-upper), [`Generator-fix-p-lower`](#generator-fix-p-lower), [`-upper`](#generator-fix-p-upper) in maintenance | done   |                                                                                |

<!-- gallery: examples/references/pypsa/rung_44_linearized_commitment.py -->

## Rung 47 — ramps and signs, as the integer file states them

This rung brings five rows of [PyPSA in one file](pypsa.md) into this file,
each on the fixed builds of this file's surface:

- The four tightening rows read each ramp limit filled to the full build where
  it is missing (`constraints.py:313-318`). They read `Generator_ramp_up_rate`
  and the other three rates. The earlier file read a missing limit as `0`.
- A ramp limit is given per snapshot and read at the later of the two
  snapshots (`constraints.py:1040-1041`). A row is absent at a snapshot where
  neither the limit nor the start-up or shut-down ramp has a value
  (`constraints.py:1046-1047`, `1136`, `1154`).
- A unit that came in running with a `p_init` ramps from it into the first
  snapshot (`constraints.py:1091-1094`, `1102-1104`). Where `p_init` has no
  value, the unit carries no ramp row at the first snapshot.
- A unit that is not committable carries ramp rows with its status fixed at
  `1` (`constraints.py:1073-1079`). The assumption
  `Generator_came_in_running_unless_committable` refuses such a unit that came
  in off, as the integer file does.
- Each generator and load term enters the bus balance with its component's
  `sign` (`constraints.py:1428-1429`, `:1538`).

The rung adds a relax bus with a tightened unit that has only start-up and
shut-down ramps, a committable unit whose ramp limit lifts at the third
snapshot, a dear committable unit that came in running at `p_init=40`, a fixed
unit with ramp limits, a unit of sign `-1`, a load of sign `1` and a dear
backup. Each binds: PyPSA solves to `12862.5`. With the missing limits read as
`0` in the two partly rows, it solves to `14085.64`. With the ramp limit at
`0.25` in every snapshot, it solves to `14554.75`. Without the `p_init`, it
solves to `8437.5`. Without the fixed unit's ramp limits, it solves to
`12800.0`. With the unit's sign at `1`, it solves to `12592.5`. With the load's
sign at `-1`, it solves to `13887.5`.

| PyPSA                                                                                                                                                                                                                               | status | note                                                                          |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------- |
| [`Generator-com-p-before`](#generator-com-p-before), [`-current`](#generator-com-p-current), [`-partly-start-up`](#generator-com-partly-start-up), [`-partly-shut-down`](#generator-com-partly-shut-down) with a missing ramp limit | done   | the four rates read a missing limit as `1`                                    |
| [`Generator-p-ramp_limit_up`](#generator-p-ramp_limit_up), [`-down`](#generator-p-ramp_limit_down) per snapshot                                                                                                                     | done   | `Generator_ramp_limit_up` and `-down` over `[snapshot, generator]`            |
| [`Generator-p-ramp_limit_up`](#generator-p-ramp_limit_up), [`-down`](#generator-p-ramp_limit_down) at the first snapshot from `p_init`                                                                                              | done   | `Generator_previous_p` opens at `Generator_status_initial * Generator_p_init` |
| [`Generator-p-ramp_limit_up`](#generator-p-ramp_limit_up), [`-down`](#generator-p-ramp_limit_down) for a unit that is not committable                                                                                               | done   | `Generator_ramp_up_allowance` and `-down` read the status as `1`              |
| [`Bus-nodal_balance`](#bus-nodal_balance) with `sign`                                                                                                                                                                               | done   | `Generator_sign` and `Load_sign`                                              |

<!-- gallery: examples/references/pypsa/rung_47_linearized_ramps.py -->

## The file

<!-- gallery: examples/pypsa_linearized_uc.yaml -->
