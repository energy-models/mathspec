# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`examples/pypsa/` is `examples/pypsa.yaml` cut into topic fragments, and `merge` gives the same model back.

Each fragment reads what another topic declares under `given:`. A sum every
component adds to (the bus balance, the operating cost, the global
constraints) is one each component adds a term to: a named expression of its
own, such as `Generator_injection`, whose `adds_to:` names the sum its file
reads under `given:`. One fragment reads each sum without adding to it, with
its description. So a component is a family of files, and leaving the family
out leaves a whole model.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mathspec import FORMATS, LanguageError, merge, to_spec, typeset
from mathspec.canonical import canonical_yaml
from tests.fixtures import BALANCE
from tests.test_terms import DEMAND, FLEET
from tools.gallery import split_index
from tools.pypsa_split import SOURCE, SUM_HOME, Model, _term_block, fragments

FOLDER = Path(__file__).resolve().parent.parent / 'examples' / 'pypsa'
PATHS = {path.stem: path for path in sorted(FOLDER.glob('*.yaml'))}


@pytest.fixture(scope='module')
def model() -> Model:
    return Model()


@pytest.mark.parametrize('name', sorted(PATHS))
def test_a_fragment_loads_on_its_own(name):
    assert to_spec(PATHS[name]).program


def test_the_fragments_merge_to_the_one_file(model):
    merged = merge(list(PATHS.values()), description=model.data['description'])
    assert canonical_yaml(merged) == canonical_yaml(to_spec(SOURCE))
    assert not merged.program.given, 'every name a fragment reads, another fragment declares'


def test_each_sum_is_its_terms_by_name_and_each_term_stays(model):
    merged = merge(list(PATHS.values()))
    assert merged.expressions['Bus_injection'].expression == (
        'Generator_injection + Line_injection + Link_injection + Load_injection + Process_injection'
        ' + StorageUnit_injection + Store_injection + Transformer_injection'
    ), 'the terms in the order the files are given in'
    assert set(model.terms) <= set(merged.expressions), 'every term is a named expression of the composed spec'


def test_the_fragments_are_what_the_splitter_writes(model):
    written = fragments(model)
    assert sorted(written) == sorted(PATHS), 'one file per topic, and no stale one'
    assert all(PATHS[name].read_text() == text for name, text in written.items())


#: What a model may leave out, as the fragment names or name prefixes it
#: drops. A component comes as a family; security reads the branches. The
#: reader of a sum no model goes without is not listed: leaving it out leaves
#: its terms with nothing else reading them, which the test below holds.
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
    'generator_ramping',
    'link_ramping',
    'process_ramping',
    'line security',
    'transformer security',
    'line transformer security power_flow',
]


def _family(name: str, dropped: list[str]) -> bool:
    return any(name == d or (name.startswith(f'{d}_') and d in ('generator', 'link', 'process')) for d in dropped)


@pytest.mark.parametrize('dropped', OPTIONAL, ids=[d.replace(' ', '+') for d in OPTIONAL])
def test_leaving_a_topic_out_leaves_a_whole_model(dropped):
    kept = {name: path for name, path in PATHS.items() if not _family(name, dropped.split())}
    assert len(kept) < len(PATHS), f'{dropped} names a fragment'
    assert not merge(list(kept.values())).program.given, f'nothing that stays reads what {dropped} declares'


def test_every_sum_is_read_with_its_description_in_one_fragment_that_adds_nothing(model):
    described = {
        name: sorted(
            stem
            for stem, path in PATHS.items()
            if (g := (spec := to_spec(path)).given.expressions.get(name))
            and g.description
            and all(e.adds_to != name for e in spec.expressions.values())
        )
        for name in model.sums
    }
    assert described == {name: [SUM_HOME.get(name, 'settings')] for name in model.sums}, (
        'the reader of a sum no model goes without carries its description, and settings carries the rest'
    )


@pytest.mark.parametrize(
    ('dropped', 'sum_name'),
    [
        pytest.param('network', 'Bus_injection', id='the-bus-balance'),
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


@pytest.mark.parametrize(
    'block',
    [
        pytest.param('  Name: a + b', id='one-line'),
        pytest.param('  Name: >-\n      a\n      + b', id='folded'),
        pytest.param('  Name:\n    expression: a + b', id='mapping'),
        pytest.param('  Name: {expression: a + b}', id='flow-mapping'),
        pytest.param('  Name: a\n    + b', id='one-line-continued'),
    ],
)
def test_a_term_block_carries_its_body_in_every_source_form(block):
    """A body the head line does not hold whole was dropped or nested.

    A folded body follows a `>-` on the head line, and a plain body may run on
    to the next line; the splitter kept only the head line. A flow mapping was
    nested under `expression:`.
    """
    assert yaml.safe_load(_term_block(block, 'hub')) == {'Name': {'expression': 'a + b', 'adds_to': 'hub'}}


def test_the_split_index_names_a_hub_once_per_fragment_and_needs_a_described_reader():
    """A fragment with two terms into one sum adds to it once, and a sum nobody reads with a description has no reader to name."""
    twice = {
        **FLEET,
        'expressions': {
            **FLEET['expressions'],
            'curtailment': {'expression': 'sum(gen_p, by=gen_bus, over=generator, into=bus)', 'adds_to': 'injection'},
        },
    }
    specs = {'balance': to_spec(BALANCE), 'fleet': to_spec(twice), 'demand': to_spec(DEMAND)}
    index = split_index(specs)
    assert '| [fleet](fleet.md) | 0 | 1 | 0 | 1 | `injection` |' in index, 'two terms into one sum, listed once'
    assert '[`demand_injection`](demand.md), [`curtailment`](fleet.md), [`generator_injection`](fleet.md)' in index, (
        'every term of the fragment, by fragment then by name'
    )
    with pytest.raises(ValueError, match=r"no fragment reads 'injection' with a description and adds nothing to it"):
        split_index({'fleet': specs['fleet'], 'demand': specs['demand']})
