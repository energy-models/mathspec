# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`examples/pypsa/` holds the PyPSA spec as fragments, and `examples/pypsa.yaml` is their merge.

Each fragment reads what another topic declares under `given:`. A sum every
component adds to (the bus balance, the operating cost, the global
constraints) is one each component adds a term to: a named expression of its
own, such as `Generator_injection`, whose `adds_to:` names the sum its file
reads under `given:`. The surface reads each sum without adding to it, with
its description, and power flow reads the cycle sum. So a component is one
file, and leaving it out leaves a whole model.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mathspec import merge, to_spec, typeset
from mathspec._typesetting import FORMATS
from mathspec.errors import LanguageError
from tests.fixtures import BALANCE
from tests.test_terms import DEMAND, FLEET
from tools.gallery import split_index
from tools.pypsa_compose import DEFAULT, paths

FOLDER = Path(__file__).resolve().parent.parent / 'examples' / 'pypsa'
PATHS = {path.stem: path for path in sorted(FOLDER.glob('*.yaml'))}


#: The fragment that reads each sum without adding to it, with its description.
READER = {'Cycle_angle_sum': 'power_flow'}


@pytest.mark.parametrize('name', sorted(PATHS))
def test_a_fragment_loads_on_its_own(name):
    assert to_spec(PATHS[name]).program


def test_the_default_set_is_every_fragment():
    assert sorted(DEFAULT) == sorted(PATHS), 'a fragment the composed file leaves out, or a name no file has'
    assert not merge(paths(DEFAULT)).program.given, 'every name a fragment reads, another fragment declares'


def test_each_sum_is_its_terms_by_name_and_each_term_stays():
    merged = merge(paths(DEFAULT))
    assert merged.expressions['Bus_injection'].expression == (
        'Generator_injection + Link_injection + Process_injection + StorageUnit_injection + Store_injection'
        ' + Line_injection + Transformer_injection + Load_injection'
    ), 'the terms in the order the default set lists the files'
    terms = {name for path in PATHS.values() for name, entry in to_spec(path).expressions.items() if entry.adds_to}
    assert terms <= set(merged.expressions), 'every term is a named expression of the composed spec'


#: What a model may leave out, as the fragments it drops. Security reads the
#: branches, and power flow reads what only the branches add. The surface,
#: which reads every other sum, is not listed: leaving it out leaves the terms
#: with nothing else reading them, which the test below holds.
OPTIONAL = [
    'carrier',
    'cost',
    'global_constraints',
    'security',
    'load',
    'storage_unit',
    'store',
    'generator',
    'link',
    'process',
    'line security',
    'transformer security',
    'line transformer security power_flow',
]


@pytest.mark.parametrize('dropped', OPTIONAL, ids=[d.replace(' ', '+') for d in OPTIONAL])
def test_leaving_a_topic_out_leaves_a_whole_model(dropped):
    kept = {name: path for name, path in PATHS.items() if name not in dropped.split()}
    assert len(kept) == len(PATHS) - len(dropped.split()), f'{dropped} names fragments'
    assert not merge(list(kept.values())).program.given, f'nothing that stays reads what {dropped} declares'


def test_every_sum_is_read_with_its_description_in_one_fragment_that_adds_nothing():
    specs = {stem: to_spec(path) for stem, path in PATHS.items()}
    sums = {entry.adds_to for spec in specs.values() for entry in spec.expressions.values() if entry.adds_to}
    described = {
        name: sorted(
            stem
            for stem, spec in specs.items()
            if (g := spec.given.expressions.get(name))
            and g.description
            and all(e.adds_to != name for e in spec.expressions.values())
        )
        for name in sums
    }
    assert described == {name: [READER.get(name, 'surface')] for name in sums}, (
        'the surface carries the description of every sum, and power flow that of the cycle sum'
    )


@pytest.mark.parametrize(
    ('dropped', 'sum_name'),
    [
        pytest.param('surface', 'total_cost', id='the-surface'),
        pytest.param('power_flow', 'Cycle_angle_sum', id='kirchhoff-with-the-branches-kept'),
    ],
)
def test_leaving_out_the_reader_of_a_sum_no_model_goes_without_is_refused(dropped, sum_name):
    """Only the terms read the sum without its reader, so they write into a name nothing else reads."""
    kept = {name: path for name, path in PATHS.items() if name != dropped}
    with pytest.raises(LanguageError, match=rf"add a term to '{sum_name}', and no other fragment reads it"):
        merge(list(kept.values()))


@pytest.mark.parametrize('fmt', sorted(FORMATS))
def test_every_fragment_and_the_composition_print(fmt):
    assert all(typeset(path, fmt) for path in PATHS.values()), f'a fragment rendered nothing in {fmt}'
    assert typeset(merge(list(PATHS.values())), fmt)


def test_the_split_index_names_a_hub_once_per_fragment_and_needs_a_described_reader():
    """A fragment with two terms into one sum adds to it once, and a sum nobody reads with a description has no reader to name."""
    twice = {
        **FLEET,
        'expressions': {
            **FLEET['expressions'],
            'curtailment': {'expression': 'sum(gen_p, over=generator, by=gen_bus[bus])', 'adds_to': 'injection'},
        },
    }
    specs = {'balance': to_spec(BALANCE), 'fleet': to_spec(twice), 'demand': to_spec(DEMAND)}
    index = split_index(specs)
    assert '| [fleet](fleet.md) | 0 | 1 | 0 | 1 | `injection` |' in index, 'two terms into one sum, listed once'
    assert '[`demand_injection`](demand.md), [`curtailment`](fleet.md), [`generator_injection`](fleet.md)' in index, (
        'every term of the fragment, by fragment then by name'
    )
    with pytest.raises(ValueError, match=r"no fragment that reads 'injection' without adding to it describes it"):
        split_index({'fleet': specs['fleet'], 'demand': specs['demand']})
