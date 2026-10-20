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

`Generator`, `Link` and `Process` are each a folder of layers. The class reads
its commitment flag under `given:`, and exactly one of `commitment.yaml` and
`commitment_none.yaml` declares it. The commitment reads its status the same
way, from `status_integer.yaml` or `status_relaxed.yaml`.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from mathspec import merge, to_spec, typeset
from mathspec._typesetting import FORMATS
from mathspec.errors import LanguageError
from tests.fixtures import BALANCE
from tests.test_terms import DEMAND, FLEET
from tools.gallery import fragment_name, split_index
from tools.pypsa_compose import DEFAULT, paths

FOLDER = Path(__file__).resolve().parent.parent / 'examples' / 'pypsa'
PATHS = {fragment_name(path): path for path in sorted(FOLDER.rglob('*.yaml'))}
DEFAULT_PATHS = dict(zip(DEFAULT, paths(DEFAULT), strict=True))
CLASSES = ('generator', 'link', 'process')
LAYERS = ('commitment', 'commitment_none', 'status_integer', 'status_relaxed', 'ramping', 'maintenance')
OUTSIDE_THE_DEFAULT = ('commitment_none', 'status_relaxed')


#: The fragment that reads each sum without adding to it, with its description.
READER = {'Cycle_angle_sum': 'power_flow'}


@pytest.mark.parametrize('name', sorted(PATHS))
def test_a_fragment_loads_on_its_own(name):
    assert to_spec(PATHS[name]).program


def test_the_default_set_is_every_fragment_but_the_alternatives():
    alternatives = {'risk_neutral', *(f'{kind}/{layer}' for kind in CLASSES for layer in OUTSIDE_THE_DEFAULT)}
    assert sorted({*DEFAULT, *alternatives}) == sorted(PATHS), (
        'a fragment the composed file leaves out, or a name no file has'
    )
    assert not merge(paths(DEFAULT)).program.given, 'every name a fragment reads, another fragment declares'


def test_each_sum_is_its_terms_by_name_and_each_term_stays():
    merged = merge(paths(DEFAULT))
    assert merged.expressions['Bus_injection'].expression == (
        'Generator_injection + Link_injection + Process_injection + StorageUnit_injection + Store_injection'
        ' + Line_injection + Transformer_injection + Load_injection'
    ), 'the terms in the order the default set lists the files'
    terms = {name for path in PATHS.values() for name, entry in to_spec(path).expressions.items() if entry.adds_to}
    assert terms <= set(merged.expressions), 'every term is a named expression of the composed spec'


#: What the default set may leave out, as the fragments it drops, a folder
#: dropping every layer in it. Security reads the branches, and power flow
#: reads what only the branches add. The surface, which reads every other sum,
#: is not listed: leaving it out leaves the terms with nothing else reading
#: them, which the test below holds.
OPTIONAL = [
    'carrier',
    'global_constraints',
    'security',
    'load',
    'storage_unit',
    'store',
    'generator',
    'link',
    'process',
    'generator/ramping',
    'generator/maintenance',
    'link/ramping link/maintenance',
    'process/ramping process/maintenance',
    'line security',
    'transformer security',
    'line transformer security power_flow',
]


@pytest.mark.parametrize('dropped', OPTIONAL, ids=[d.replace(' ', '+') for d in OPTIONAL])
def test_leaving_a_topic_out_leaves_a_whole_model(dropped):
    gone = dropped.split()
    kept = {name: path for name, path in DEFAULT_PATHS.items() if name not in gone and name.split('/')[0] not in gone}
    assert len(kept) < len(DEFAULT_PATHS), f'{dropped} names fragments'
    assert not merge(list(kept.values())).program.given, f'nothing that stays reads what {dropped} declares'


def test_every_sum_is_read_with_its_description_in_one_fragment_that_adds_nothing():
    specs = {name: to_spec(path) for name, path in PATHS.items()}
    defined = {name for spec in specs.values() for name, entry in spec.expressions.items() if not entry.adds_to}
    sums = {e.adds_to for spec in specs.values() for e in spec.expressions.values() if e.adds_to} - defined
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
    kept = {name: path for name, path in DEFAULT_PATHS.items() if name != dropped}
    with pytest.raises(LanguageError, match=rf"add a term to '{sum_name}', and no other fragment reads it"):
        merge(list(kept.values()))


@pytest.mark.parametrize('fmt', sorted(FORMATS))
def test_every_fragment_and_the_composition_print(fmt):
    assert all(typeset(path, fmt) for path in PATHS.values()), f'a fragment rendered nothing in {fmt}'
    assert typeset(merge(paths(DEFAULT)), fmt)


def _whole(layers: tuple[str, ...]) -> bool:
    """Whether a class with *layers* is a whole model.

    It takes one commitment file. The commitment takes one status file, and
    the relaxed status reads the ramp rates. No commitment declares the status
    itself, so it takes no status file.
    """
    taken = set(layers)
    if ('commitment' in taken) == ('commitment_none' in taken):
        return False
    status = taken & {'status_integer', 'status_relaxed'}
    if 'commitment_none' in taken:
        return not status
    return len(status) == 1 and ('status_relaxed' not in taken or 'ramping' in taken)


@pytest.mark.parametrize('kind', CLASSES)
@pytest.mark.parametrize(
    'layers',
    [combo for k in range(len(LAYERS) + 1) for combo in itertools.combinations(LAYERS, k)],
    ids=lambda layers: '+'.join(layers) or 'alone',
)
def test_a_class_is_whole_exactly_when_its_slots_are_filled_once(kind, layers):
    """A slot no file fills leaves a name unread, a slot two files fill declares it twice."""
    others = [path for name, path in DEFAULT_PATHS.items() if not name.startswith(f'{kind}/')]
    files = [*others, *(FOLDER / kind / f'{layer}.yaml' for layer in ('class', *layers))]
    try:
        whole = not merge(files).program.given
    except LanguageError:
        whole = False
    assert whole == _whole(layers), f'{kind} with {layers or "no layer"}: whole is {whole}'


def _signature(spec, name):
    """What a reader under `given:` may state about *name*: its kind, its frame and its type."""
    program = spec.program
    if name in spec.parameters:
        return 'parameters', tuple(spec.parameters[name].dims), spec.parameters[name].dtype
    if name in spec.variables:
        return 'variables', tuple(spec.variables[name].dims), spec.variables[name].domain
    if name in program.expressions:
        return 'expressions', tuple(program.expressions[name].dims)
    return 'masks', tuple(program.masks[name].dims)


@pytest.mark.parametrize('kind', CLASSES)
def test_no_commitment_declares_what_the_commitment_declares_alike(kind):
    """Ramping and maintenance read these names from whichever file is in, so the two must agree name for name.

    The integer status is the commitment's: the relaxed one differs from it on purpose.
    """
    empty, commitment, status = (
        to_spec(FOLDER / kind / f'{name}.yaml') for name in ('commitment_none', 'commitment', 'status_integer')
    )
    names = [*empty.parameters, *empty.variables, *empty.expressions, *empty.masks]
    assert len(names) == 9, (
        'the interface is the flag, the status data, the status and its moves, two expressions and a mask'
    )

    def full(name):
        return _signature(status if name in status.variables else commitment, name)

    differ = {n: (_signature(empty, n), full(n)) for n in names if _signature(empty, n) != full(n)}
    assert not differ, f'{kind}: no commitment and the commitment declare these differently: {differ}'


@pytest.mark.parametrize('kind', CLASSES)
def test_no_commitment_refuses_a_committable_unit(kind):
    """Without it, a committable unit in data with no commitment layer would have no output limits."""
    component = kind.capitalize()
    assumption = to_spec(FOLDER / kind / 'commitment_none.yaml').assumptions[f'{component}_none_committable']
    assert assumption.holds == f'NOT {component}_committable', 'the data may hold no committable unit'


@pytest.mark.parametrize(
    ('files', 'whole'),
    [
        pytest.param(('risk',), True, id='risk'),
        pytest.param(('risk_neutral',), True, id='risk-neutral'),
        pytest.param((), False, id='neither'),
        pytest.param(('risk', 'risk_neutral'), False, id='both'),
    ],
)
def test_a_model_takes_exactly_one_risk_file(files, whole):
    """The components read `CVaR_omega` under `given:`, and only the two risk files declare it."""
    others = [path for name, path in DEFAULT_PATHS.items() if name != 'risk']
    try:
        merged = not merge([*others, *(FOLDER / f'{name}.yaml' for name in files)]).program.given
    except LanguageError:
        merged = False
    assert merged == whole, f'with {files or "no risk file"}: whole is {merged}'


def test_no_risk_preference_refuses_a_set_one():
    """Without it, a risk preference in the data of a model with no risk layer would be ignored."""
    spec = to_spec(FOLDER / 'risk_neutral.yaml')
    assert spec.assumptions['CVaR_omega_unset'].holds == 'NOT CVaR_omega', 'the data may set no risk preference'
    assert spec.parameters['CVaR_omega'].dims == to_spec(FOLDER / 'risk.yaml').parameters['CVaR_omega'].dims, (
        'the two risk files declare the flag alike'
    )


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
