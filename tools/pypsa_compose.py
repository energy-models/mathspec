# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Write `examples/pypsa.yaml` and its relaxed variant as merges of the PyPSA fragments under `examples/pypsa/`.

    pixi run python -m tools.pypsa_compose           # rewrite the composed files
    pixi run python -m tools.pypsa_compose --check   # fail if one has drifted

The fragments are the source. A composed file is what `merge` returns for one
set of fragments, written out with a header that says so, and it is what the
PyPSA pages, the rungs and every engine read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mathspec import merge
from tools._page import ROOT
from tools._page import main as page_main

if TYPE_CHECKING:
    from pathlib import Path

FRAGMENTS = ROOT / 'examples' / 'pypsa'
COMPOSED = ROOT / 'examples' / 'pypsa.yaml'
RELAXED_COMPOSED = ROOT / 'examples' / 'pypsa_linearized_uc.yaml'

#: The fragments of the default set, in the order the composed file lists their entries.
DEFAULT = (
    'surface',
    'power_flow',
    'cost',
    'carrier',
    'global_constraints',
    'security',
    'generator/class',
    'generator/commitment',
    'generator/status_integer',
    'generator/ramping',
    'generator/maintenance',
    'link/class',
    'link/commitment',
    'link/status_integer',
    'link/ramping',
    'link/maintenance',
    'process/class',
    'process/commitment',
    'process/status_integer',
    'process/ramping',
    'process/maintenance',
    'storage_unit',
    'store',
    'line',
    'transformer',
    'load',
)

DESCRIPTION = (
    'A plain `n.optimize()`, and its multi-period and stochastic classes, in one file. Every second-stage quantity '
    'spans a `scenario` (a future dispatch is chosen in) and every asset stands in the investment `period`s its build '
    'year and lifetime span. A parameter spans `scenario` exactly when PyPSA reads it per scenario. Capacity is chosen '
    'once, before the future is known, and paid once per active period at its cost in expectation over the scenarios; '
    "operation is the expectation over the scenarios' weights, with a share priced at the tail through the CVaR rows, "
    'which stand only where a risk preference is set. A plain run feeds one scenario, one period, all-active masks and '
    'unit weights, and the model collapses to the standard one. A security-constrained run copies each branch flow '
    'limit once per outage in an `outage` set that a plain run leaves empty. Which snapshots an asset is active in, a '
    "scenario's weight, and the outage factors are data prep."
)

#: The fragments of `n.optimize(linearized_unit_commitment=True)`: the default set with the status relaxed.
RELAXED = tuple(name.replace('/status_integer', '/status_relaxed') for name in DEFAULT)

RELAXED_DESCRIPTION = (
    '`n.optimize(linearized_unit_commitment=True)`. The status, its starts and its stops of a committable generator, '
    'link and process are shares in [0, 1] rather than integers, and four rows PyPSA adds only under the keyword '
    'tighten the relaxation of a unit with a fixed build whose start and stop cost the same in every snapshot and '
    'every scenario (`constraints.py:599-699`). A modular committable unit is refused, as PyPSA refuses it. Every '
    "other row is the integer run's."
)

# REUSE-IgnoreStart
HEADER = (
    '# SPDX-FileCopyrightText: mathspec Contributors\n'
    '#\n'
    '# SPDX-License-Identifier: MIT\n'
    '#\n'
    '# Written by `python -m tools.pypsa_compose` from the fragments under\n'
    '# `examples/pypsa/`. Edit those, not this file.\n\n'
)
# REUSE-IgnoreEnd


def paths(names: tuple[str, ...]) -> list[Path]:
    """The fragment files of *names*, in that order."""
    return [FRAGMENTS / f'{name}.yaml' for name in names]


def composed(_text: str = '') -> str:
    """The composed file: the default set merged, under its header."""
    return HEADER + merge(paths(DEFAULT), description=DESCRIPTION).to_yaml()


def relaxed(_text: str = '') -> str:
    """The relaxed composed file: the relaxed set merged, under its header."""
    return HEADER + merge(paths(RELAXED), description=RELAXED_DESCRIPTION).to_yaml()


def main(argv: list[str] | None = None) -> int:
    return page_main(argv, {COMPOSED: composed, RELAXED_COMPOSED: relaxed}, 'pypsa_compose')


if __name__ == '__main__':
    raise SystemExit(main())
