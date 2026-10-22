# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The fuzzer in ``tests/fuzz/`` still reaches accepted specs, and every case it found still fails.

The campaign itself is ``pixi run python -m tests.fuzz``. This module keeps
the mutator honest and holds each finding, reduced, as a strict ``xfail`` run
through the same oracles, so the day its fix lands it XPASSes and the marker
comes off.
"""

from __future__ import annotations

from typing import Any

import pytest

from mathspec import to_spec
from mathspec.errors import MathSpecError
from tests.fuzz.check import check
from tests.fuzz.mutate import corpus, mutant

#: Of this many seeds, at least ``ACCEPTED`` of the mutants must load, or the accepted-spec oracles see too little.
SEEDS = 300
ACCEPTED = 0.05

CORPUS = corpus()


def test_every_example_passes_every_oracle() -> None:
    """The corpus the mutants start from is clean, so a finding is the mutation's."""
    broken = {name: [f.summary for f in check(spec).findings] for name, spec in CORPUS}
    broken = {name: summaries for name, summaries in broken.items() if summaries and name not in UNCLEAN}
    assert not broken, f'examples that fail an oracle unedited: {broken}'


def test_enough_mutants_stay_inside_the_language() -> None:
    accepted = 0
    for seed in range(SEEDS):
        try:
            to_spec(mutant(seed, CORPUS).spec)
            accepted += 1
        except MathSpecError:
            pass
    assert accepted >= ACCEPTED * SEEDS, f'only {accepted} of {SEEDS} mutants load'


def test_a_seed_is_the_whole_reproduction() -> None:
    one, two = mutant(11, CORPUS), mutant(11, CORPUS)
    assert (one.source, one.spec, one.edits) == (two.source, two.spec, two.edits), 'the same seed draws the same mutant'


def _found(reason: str) -> Any:
    return pytest.mark.xfail(reason=reason, raises=AssertionError, strict=True)


#: Two cases that claim apart, written in either order.
CASED: dict[str, Any] = {
    'dimensions': {'t': {'dtype': 'int', 'ordered': True}},
    'parameters': {'flag': {'dims': ['t'], 'dtype': 'bool'}, 'a': {'dims': ['t']}, 'b': {'dims': ['t']}},
    'variables': {'x': {'dims': ['t']}},
    'expressions': {
        'e': {
            'dims': ['t'],
            'cases': {
                'second': {'when': 'NOT flag', 'expression': 'b'},
                'first': {'when': 'flag', 'expression': 'a'},
            },
            'otherwise': 'x',
        }
    },
    'constraints': {'c': {'dims': ['t'], 'expression': 'x <= e'}},
}

#: A relation keyed by two named columns over one dimension, written in the order the canonical form does not choose.
KEYED: dict[str, Any] = {
    'dimensions': {'t': {'dtype': 'int', 'ordered': True}, 'g': {'dtype': 'str'}},
    'relations': {'window': {'key': {'start': 't', 'g': 'g', 'covered': 't'}, 'missing': 'absent'}},
    'variables': {'x': {'dims': ['g', 't']}},
    'constraints': {'c': {'dims': ['g', 't'], 'expression': 'sum(x, over=covered, by=window[start]) <= 1'}},
}

#: A curve stated as lines, between a variable over ``g`` and one over ``s`` and ``g``.
LINES: dict[str, Any] = {
    'dimensions': {'s': {'dtype': 'int'}, 'g': {'dtype': 'str'}, 'bp': {'dtype': 'int', 'ordered': True}},
    'parameters': {'bx': {'dims': ['g', 'bp']}, 'by': {'dims': ['g', 'bp']}},
    'variables': {'x': {'dims': ['g'], 'bounds': {'lower': 0}}, 'y': {'dims': ['s', 'g'], 'bounds': {'lower': 0}}},
    'piecewise': {'curve': {'over': 'bp', 'links': [['x', 'bx'], ['y', 'by', '>=']], 'method': 'lp'}},
    'objective': {'sense': 'minimize', 'expression': 'sum(y)'},
}

#: The examples whose unedited form a finding below already names.
UNCLEAN = {
    'generator_maintenance.yaml', 'link_maintenance.yaml', 'process_maintenance.yaml',
    'storage_unit.yaml', 'store.yaml', 'pypsa.yaml',
}  # fmt: skip

REDUCED = [
    pytest.param(
        CASED,
        marks=_found('#890 — the canonical form keeps cases: in file order, though the cases carry no order'),
        id='the order of cases',
    ),
    pytest.param(
        KEYED,
        marks=_found(
            '#890 — the canonical form keeps the columns of a relation written as a mapping, key: or values:, in file order'
        ),
        id='the order of named relation columns',
    ),
    pytest.param(
        LINES,
        marks=_found('#891 — a method: lp curve over links with different dims loads, and its expansion is refused'),
        id='a curve as lines over links of different dims',
    ),
]


@pytest.mark.parametrize('raw', REDUCED)
def test_a_reduced_case_passes_every_oracle(raw: dict[str, Any]) -> None:
    findings = check(raw).findings
    assert not findings, '\n'.join(f'[{f.oracle}] {f.summary}\n{f.detail[-800:]}' for f in findings)
