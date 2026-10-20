# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Write `examples/pypsa.yaml` as the merge of the PyPSA fragments under `examples/pypsa/`.

    pixi run python -m tools.pypsa_compose           # rewrite the composed file
    pixi run python -m tools.pypsa_compose --check   # fail if it has drifted

The fragments are the source. The composed file is what `merge` returns for
the default set, written out with a header that says so, and it is what the
PyPSA index page, the rungs and every engine read.
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
    'generator/ramping',
    'generator/maintenance',
    'link/class',
    'link/commitment',
    'link/ramping',
    'link/maintenance',
    'process/class',
    'process/commitment',
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


def main(argv: list[str] | None = None) -> int:
    return page_main(argv, {COMPOSED: composed}, 'pypsa_compose')


if __name__ == '__main__':
    raise SystemExit(main())
