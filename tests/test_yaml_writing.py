# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The layout every spec this package writes shares: short lists and value maps on one line."""

from __future__ import annotations

import pytest

import mathspec as ms
from mathspec._yaml import dump_yaml
from tests.fixtures import SPECS

LONG = 'a description that runs past the eighty columns a terminal shows, and keeps going after it'


@pytest.mark.parametrize(
    ('data', 'written'),
    [
        pytest.param({'dims': ['snapshot', 'generator']}, 'dims: [snapshot, generator]\n', id='a-list-of-names'),
        pytest.param({'dims': []}, 'dims: []\n', id='an-empty-list'),
        pytest.param({'bounds': {'lower': 0, 'upper': 'p_max'}}, 'bounds: {lower: 0, upper: p_max}\n', id='bounds'),
        pytest.param(
            {'p': {'dims': ['snapshot'], 'domain': 'binary'}},
            'p: {dims: [snapshot], domain: binary}\n',
            id='a-declaration-of-words',
        ),
        pytest.param(
            {'links': [['p', 'bp_x'], ['cost', 'bp_y']]},
            'links: [[p, bp_x], [cost, bp_y]]\n',
            id='a-list-of-short-lists',
        ),
        pytest.param(
            {'p': {'dims': ['snapshot'], 'description': 'output of a generator'}},
            'p:\n  dims: [snapshot]\n  description: output of a generator\n',
            id='a-declaration-with-a-description-keeps-a-key-to-a-line',
        ),
        pytest.param(
            {'balance': {'expression': 'p - load == 0'}},
            'balance:\n  expression: p - load == 0\n',
            id='a-declaration-with-an-expression-of-several-words-keeps-a-key-to-a-line',
        ),
        pytest.param(
            {'objective': {'sense': 'minimize', 'expression': 'sum(p)'}},
            'objective:\n  sense: minimize\n  expression: sum(p)\n',
            id='an-expression-of-one-word-keeps-a-key-to-a-line',
        ),
        pytest.param(
            {'labels': ['München', 'Zürich', 'Göteborg', 'Kraków', 'Łódź', 'Málaga', 'Thessaloníki', 'Ålesund']},
            'labels: [München, Zürich, Göteborg, Kraków, Łódź, Málaga, Thessaloníki, Ålesund]\n',
            id='a-name-with-an-accent-counts-as-its-characters',
        ),
        pytest.param(
            {'labels': ['north_sea_offshore_wind', 'baltic_offshore_wind', 'iberian_solar', 'alpine_run_of_river']},
            'labels:\n- north_sea_offshore_wind\n- baltic_offshore_wind\n- iberian_solar\n- alpine_run_of_river\n',
            id='a-list-past-80-characters-is-one-item-to-a-line',
        ),
        pytest.param({'p': {'description': LONG}}, f'p:\n  description: {LONG}\n', id='a-long-line-is-not-wrapped'),
        pytest.param(
            {'expression': 'p\n- load\n== 0'},
            'expression: |-\n  p\n  - load\n  == 0\n',
            id='a-multi-line-string-is-a-block-scalar',
        ),
        pytest.param(
            {'links': [['p\n+ q', 'bp_x']]},
            'links:\n- - |-\n    p\n    + q\n  - bp_x\n',
            id='nor-is-a-list-holding-a-multi-line-string',
        ),
        pytest.param(
            {'p': {'description': 'Output of a unit. It is never negative.'}},
            'p:\n  description: >-\n    Output of a unit.\n    It is never negative.\n',
            id='prose-is-one-sentence-to-a-line',
        ),
        pytest.param(
            {'p': {'description': 'Output, e.g. the power a unit sends.'}},
            'p:\n  description: Output, e.g. the power a unit sends.\n',
            id='an-abbreviation-does-not-end-a-sentence',
        ),
        pytest.param(
            {'p': {'description': 'Output of a unit.  It is never negative.'}},
            'p:\n  description: Output of a unit.  It is never negative.\n',
            id='two-spaces-between-sentences-keep-the-text-on-one-line',
        ),
        pytest.param(
            {'p': {'description': 'Output of a unit. It is never negative. '}},
            "p:\n  description: 'Output of a unit. It is never negative. '\n",
            id='a-trailing-space-keeps-the-text-on-one-line',
        ),
    ],
)
def test_the_layout(data, written):
    """Each case under a file's description, as a spec's sections sit under its root, which is a block mapping."""
    assert dump_yaml({'description': 'one case', **data}) == f'description: one case\n{written}', (
        'the text written, whole'
    )


@pytest.mark.parametrize('path', SPECS, ids=lambda path: path.stem)
def test_every_spec_written_back_out_reads_as_itself(path):
    """A folded description reads back as the one-line string it was, so the spec is equal, not merely alike."""
    spec = ms.to_spec(path)
    assert ms.to_spec(spec.to_yaml()) == spec
