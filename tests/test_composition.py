# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Two verbs, and what each one refuses.

`merge` composes peers, so a name two fragments declare is a collision. The
order they are given in orders the terms of a sum and nothing else, and a
fragment's name only labels it in a refusal. `override` lays a base and its
patches in order, so a name the patch declares is the point, and a later patch
wins a field an earlier one writes. A patch that lands on nothing, a dimension
redeclared or removed under the expressions written over it, and a whole
section set to null are each a spec that would otherwise load and mean
something nobody wrote.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import pytest
import yaml

import mathspec.spec as spec_module
from mathspec import merge, override, to_markdown, to_spec
from mathspec.canonical import canonical_yaml
from mathspec.errors import LanguageError
from tests.fixtures import DISPATCH_MODEL, SMALL_MODEL, varied

if TYPE_CHECKING:
    from pathlib import Path

#: The coupling surface a component library agrees on: one flow per port, and
#: one balance per bus. The two fragments below read `flow` under `given:`, so
#: each is a spec on its own as well as a piece of the composition.
SURFACE = {
    'dimensions': {'snapshot': {'dtype': 'int'}, 'port': {'dtype': 'str'}, 'bus': {'dtype': 'str'}},
    'relations': {'port_bus': {'key': 'port', 'values': 'bus'}},
    'variables': {'flow': {'dims': ['snapshot', 'port']}},
    'constraints': {
        'balance': {'dims': ['snapshot', 'bus'], 'expression': 'sum(flow, over=port, by=port_bus[bus]) == 0'}
    },
}

SUPPLY = {
    'dimensions': {'snapshot': {'dtype': 'int'}, 'port': {'dtype': 'str'}, 'generator': {'dtype': 'str'}},
    'relations': {'gen_port': {'key': 'generator', 'values': 'port'}},
    'given': {'variables': {'flow': {'dims': ['snapshot', 'port']}}},
    'parameters': {'gen_cost': {'dims': ['generator']}, 'gen_p_max': {'dims': ['generator']}},
    'variables': {'gen_p': {'dims': ['snapshot', 'generator'], 'bounds': {'lower': 0, 'upper': 'gen_p_max'}}},
    'constraints': {
        'gen_injects': {
            'dims': ['snapshot', 'generator'],
            'expression': 'at(flow, by=gen_port[port]) == gen_p',
        }
    },
    'objective': {'sense': 'minimize', 'expression': 'sum(gen_p * gen_cost)'},
}

DEMAND = {
    'dimensions': {'snapshot': {'dtype': 'int'}, 'port': {'dtype': 'str'}, 'demand': {'dtype': 'str'}},
    'relations': {'dem_port': {'key': 'demand', 'values': 'port'}},
    'given': {'variables': {'flow': {'dims': ['snapshot', 'port']}}},
    'parameters': {'dem_load': {'dims': ['snapshot', 'demand']}},
    'constraints': {
        'dem_withdraws': {
            'dims': ['snapshot', 'demand'],
            'expression': 'at(flow, by=dem_port[port]) == -dem_load',
        }
    },
}

LIBRARY = [SURFACE, SUPPLY, DEMAND]

#: The objective of a composed cost model, set by one file and read off a sum
#: the other files add a term each to (#801).
OBJECTIVE = {
    'given': {'expressions': {'total_cost': {'dims': [], 'description': 'what the system costs'}}},
    'objective': {'sense': 'minimize', 'expression': 'total_cost'},
}


def _priced(name: str) -> dict[str, object]:
    """A fragment that builds *name* and adds what it costs to `total_cost`."""
    return {
        'dimensions': {name: {'dtype': 'str'}},
        'parameters': {f'{name}_cost': {'dims': [name]}},
        'variables': {f'{name}_p': {'dims': [name], 'bounds': {'lower': 0}}},
        'given': {'expressions': {'total_cost': {'dims': []}}},
        'expressions': {
            f'{name}_spend': {'expression': f'sum({name}_p * {name}_cost)', 'adds_to': 'total_cost'},
        },
    }


GENERATOR, STORE = _priced('generator'), _priced('store')


def test_a_fragment_reads_what_a_sibling_declares():
    """`supply` reads `flow` under `given:`, so it is a spec on its own and a piece of the composition."""
    assert to_markdown(SUPPLY), 'a fragment prints as math on its own'
    spec = merge(LIBRARY)
    assert sorted(spec.variables) == ['flow', 'gen_p'], "both fragments' columns are in the one spec"
    assert not spec.given, 'the reading is spent once the fragment that builds the column is in the composition'
    assert to_markdown(spec), 'a composed library prints as math'


def test_a_fragment_that_does_not_load_on_its_own_is_refused():
    """A sibling's declarations must not make a broken file load: a fragment is a spec before it is a piece."""
    unread = {key: value for key, value in SUPPLY.items() if key != 'given'}
    with pytest.raises(LanguageError, match=r"fragment '#2' does not load on its own") as raised:
        merge([SURFACE, unread, DEMAND])
    assert "'flow' not found" in str(raised.value), "the fragment's own refusal follows, so the fix is named"


def test_the_balance_does_not_grow_when_a_component_type_is_added():
    """What the port convention buys: a component pins its own flow rather than adding a term."""
    three = merge(LIBRARY).constraints['balance'].expression
    storage = {
        'dimensions': {'snapshot': {'dtype': 'int'}, 'port': {'dtype': 'str'}, 'store': {'dtype': 'str'}},
        'relations': {'st_port': {'key': 'store', 'values': 'port'}},
        'given': {'variables': {'flow': {'dims': ['snapshot', 'port']}}},
        'parameters': {'st_capacity': {'dims': ['store']}},
        'variables': {'st_p': {'dims': ['snapshot', 'store'], 'bounds': {'lower': 0, 'upper': 'st_capacity'}}},
        'constraints': {
            'st_injects': {
                'dims': ['snapshot', 'store'],
                'expression': 'at(flow, by=st_port[port]) == st_p',
            }
        },
    }
    four = merge([*LIBRARY, storage]).constraints['balance'].expression
    assert three == four, 'the balance is written once, whatever is plugged into it'


@pytest.mark.parametrize(
    'fragments',
    [
        pytest.param(LIBRARY, id='one-objective'),
        pytest.param([OBJECTIVE, GENERATOR, STORE], id='an-objective-on-a-sum'),
    ],
)
def test_the_order_of_the_fragments_reaches_no_canonical_text(fragments):
    """The order sorts the terms of a sum, and the canonical form sorts them again."""
    assert canonical_yaml(merge(fragments)) == canonical_yaml(merge(fragments[::-1]))


def test_the_fragments_are_never_mutated():
    before = copy.deepcopy(LIBRARY)
    merge(LIBRARY)
    assert before == LIBRARY, 'a composed spec is a new spec, and the fragments are untouched'


@pytest.mark.parametrize(
    ('fragments', 'says'),
    [
        pytest.param(
            [SUPPLY, {**DEMAND, 'parameters': {**DEMAND['parameters'], 'gen_cost': {'dims': ['demand']}}}],
            'two rows of a dimension',
            id='one-name-declared-twice',
        ),
        pytest.param(
            [SUPPLY, {**DEMAND, 'dimensions': {**DEMAND['dimensions'], 'snapshot': {'dtype': 'str'}}}],
            'give one of them a name of its own',
            id='one-dimension-described-two-ways',
        ),
    ],
)
def test_a_disagreement_between_fragments_is_refused(fragments, says):
    """No order of the fragments settles any of these, so each is a refusal rather than a rule."""
    with pytest.raises(LanguageError) as raised:
        merge(fragments)
    message = str(raised.value)
    assert says in message, 'the refusal names the rewrite rather than only what is wrong'
    assert "'#1'" in message and "'#2'" in message, 'a disagreement names both fragments by their place in the list'


def _said(fragment: dict[str, object], section: str, name: str, words: str) -> dict[str, object]:
    """*fragment* with the declaration *name* under *section* described as *words*."""
    block = copy.deepcopy(fragment)
    entries = block[section] if section != 'given' else block['given']['variables']
    entries[name] = {**entries[name], 'description': words}
    return block


#: Two fragments that word one declaration differently.
WORDED = [
    pytest.param('dimensions', 'snapshot', id='a-shared-dimension'),
    pytest.param('given', 'flow', id='a-reading-nothing-introduces'),
]


@pytest.mark.parametrize(('section', 'name'), WORDED)
def test_prose_two_fragments_word_apart_is_the_first_one_given(section, name):
    """Prose is not a claim, so two wordings agree, and the first fragment given carries its own."""
    supply, demand = _said(SUPPLY, section, name, 'an hour'), _said(DEMAND, section, name, 'a step')
    composed = merge([supply, demand])
    carried = composed.dimensions[name] if section == 'dimensions' else composed.given.variables[name]
    assert carried.description == 'an hour', 'the claim is carried whole, under the wording of the first fragment'


def test_a_peer_s_description_is_carried_where_the_first_one_given_has_none():
    supply = _said(SUPPLY, 'dimensions', 'snapshot', 'an hour')
    assert merge([DEMAND, supply]).dimensions['snapshot'].description == 'an hour', (
        'the first fragment says nothing, so the wording of the second is carried'
    )


def _ordered(fragment: dict[str, object]) -> dict[str, object]:
    """*fragment* with ``snapshot`` declared ordered."""
    return {**fragment, 'dimensions': {**fragment['dimensions'], 'snapshot': {'dtype': 'int', 'ordered': True}}}


@pytest.mark.parametrize(
    'fragments',
    [
        pytest.param([SUPPLY, _ordered(DEMAND)], id='the-second-says-ordered'),
        pytest.param([_ordered(SUPPLY), DEMAND], id='the-first-says-ordered'),
    ],
)
def test_a_dimension_one_fragment_declares_ordered_is_ordered_in_the_composition(fragments):
    """Each fragment loads alone, and two that differed only in ``ordered`` were refused as saying different things."""
    assert merge(fragments).dimensions['snapshot'].ordered, 'ordered is a claim one fragment adds to the space'


def _mapped(missing: str | None) -> dict[str, object]:
    """A fragment that declares only `port_bus`, with *missing* written, or no `missing:` where it is ``None``."""
    relation = {'key': 'port', 'values': 'bus'} | ({} if missing is None else {'missing': missing})
    return {'dimensions': {'port': {'dtype': 'str'}, 'bus': {'dtype': 'str'}}, 'relations': {'port_bus': relation}}


@pytest.mark.parametrize(
    ('fragments', 'missing'),
    [
        pytest.param([SURFACE, _mapped('refused')], 'refused', id='the-default-written-out'),
        pytest.param(
            [varied(SURFACE, **{'relations.port_bus.missing': 'absent'}), _mapped('absent')], 'absent', id='both-absent'
        ),
    ],
)
def test_two_fragments_that_say_one_missing_agree(fragments, missing):
    """A written `missing: refused` was refused against an omitted one, as two fragments saying different things."""
    assert merge(fragments).relations['port_bus'].missing == missing


@pytest.mark.parametrize(
    'fragments',
    [
        pytest.param([SURFACE, _mapped('absent')], id='refused-against-absent'),
        pytest.param([_mapped('absent'), SURFACE], id='absent-against-refused'),
    ],
)
def test_two_fragments_that_read_a_missing_key_apart_are_refused(fragments):
    """Neither reading settles the other: a key left out is refused under one, and belongs to no group under the other."""
    with pytest.raises(LanguageError, match=r"say different things about the relation 'port_bus'") as raised:
        merge(fragments)
    assert 'make the two identical' in str(raised.value), 'the refusal names the rewrite'


@pytest.mark.parametrize(
    ('owner', 'carried'),
    [
        pytest.param(None, 'what a port puts into its bus', id='the-owner-says-nothing'),
        pytest.param('a flow', 'a flow', id='the-owner-s-own-wins'),
    ],
)
def test_a_reader_s_description_fills_a_declaration_that_has_none(owner, carried):
    """A reader's words about a name were dropped when the name was folded, even where the owner wrote none."""
    surface = _said(SURFACE, 'variables', 'flow', owner) if owner else SURFACE
    supply = _said(SUPPLY, 'given', 'flow', 'what a port puts into its bus')
    composed = merge([surface, supply, DEMAND])
    assert composed.variables['flow'].description == carried


@pytest.mark.parametrize(
    'composed',
    [
        pytest.param(lambda: merge([OBJECTIVE, GENERATOR, STORE]), id='in-one-list'),
        pytest.param(lambda: merge([merge([OBJECTIVE, GENERATOR]), STORE]), id='in-steps'),
    ],
)
def test_a_composed_objective_reads_the_sum_its_fragments_add_to(composed):
    spec = composed()
    assert spec.objective is not None
    assert (spec.objective.sense, spec.objective.expression) == ('minimize', 'total_cost'), (
        'the objective is carried as the one file that sets it wrote it'
    )
    assert spec.expressions['total_cost'].expression == 'generator_spend + store_spend', (
        'each file adds its cost as a term of the sum the objective reads'
    )


@pytest.mark.parametrize(
    'fragments',
    [
        pytest.param(
            [SURFACE, SUPPLY, {**DEMAND, 'objective': {'sense': 'minimize', 'expression': 'sum(dem_load)'}}],
            id='two-objectives',
        ),
        pytest.param(
            [SUPPLY, {**DEMAND, 'objective': {'sense': 'maximize', 'expression': 'sum(dem_load)'}}],
            id='two-objectives-that-run-opposite-ways',
        ),
        pytest.param(
            [OBJECTIVE, GENERATOR, {**STORE, 'objective': {'sense': 'minimize', 'expression': 'total_cost'}}],
            id='an-objective-on-a-sum-and-one-more',
        ),
    ],
)
def test_two_fragments_that_set_the_objective_are_refused(fragments):
    """`merge` summed the objectives, by a rule that no other section has; a second objective now collides."""
    with pytest.raises(LanguageError, match=r'both set the objective') as raised:
        merge(fragments)
    message = str(raised.value)
    assert 'given: expressions:' in message and '`adds_to:`' in message, 'the refusal names the rewrite'
    first, second = [i for i, f in enumerate(fragments, 1) if 'objective' in f]
    assert f"'#{first}'" in message and f"'#{second}'" in message, 'both fragments that set it are named'


def test_one_fragment_s_objective_is_carried_as_it_was_written():
    objective = merge(LIBRARY).objective
    assert objective is not None
    assert objective.expression == SUPPLY['objective']['expression']


def test_fragments_written_against_two_language_versions_are_refused(monkeypatch):
    """This reader knows one version, so a second is stood up for the fragments to disagree about."""
    monkeypatch.setattr(spec_module, 'SUPPORTED_VERSIONS', (0, 1))
    with pytest.raises(LanguageError, match=r'One spec has one version') as raised:
        merge([{**SUPPLY, 'version': 0}, {**DEMAND, 'version': 1}])
    assert "'#1' says 0" in str(raised.value) and "'#2' says 1" in str(raised.value), 'both are named'


def test_the_description_belongs_to_the_composition():
    described = merge([SURFACE, {**SUPPLY, 'description': 'a fleet'}, DEMAND], description='a fleet against a load')
    assert described.description == 'a fleet against a load'
    assert merge([SURFACE, {**SUPPLY, 'description': 'a fleet'}, DEMAND]).description is None, (
        "no fragment's own description is carried"
    )


def test_merge_composes_the_model_and_override_configures_the_run():
    """The two verbs meet by taking and returning what the other does."""
    run = override(merge(LIBRARY), [{'variables': {'gen_p': {'where': 'gen_p_max > 0'}}}])
    assert to_spec(run).variables['gen_p'].where == 'gen_p_max > 0'


def test_every_section_a_fragment_owns_reaches_the_composition():
    """`merge` listed its sections by hand, so `assumptions:` fell out of every composed spec."""
    assumed = {**DEMAND, 'assumptions': {'dem_load_positive': 'dem_load >= 0'}}
    composed = merge([SURFACE, SUPPLY, assumed])
    assert sorted(composed.assumptions) == ['dem_load_positive'], "the fragment's assumption is in the one spec"


def test_a_fragment_is_a_path_as_readily_as_a_mapping(tmp_path):
    surface = tmp_path / 'surface.yaml'
    surface.write_text(to_spec(SURFACE).to_yaml(), encoding='utf-8')
    assert merge([str(surface), SUPPLY, DEMAND]) == merge(LIBRARY)


def _written(folder: Path, fragments: list[dict[str, object]]) -> list[Path]:
    """Each of *fragments* written as a file of its own, in the order given."""
    paths = [folder / f'{n}.yaml' for n in range(len(fragments))]
    for path, fragment in zip(paths, fragments, strict=True):
        path.write_text(yaml.safe_dump(fragment), encoding='utf-8')
    return paths


def test_a_refusal_names_a_file_by_its_path(tmp_path):
    """A file is named as the list gives it, and anything else by its place in the list."""
    unread = {key: value for key, value in SUPPLY.items() if key != 'given'}
    with pytest.raises(LanguageError, match=r'does not load on its own') as raised:
        merge(_written(tmp_path, [SURFACE, unread, DEMAND]))
    assert f"fragment '{tmp_path / '1.yaml'}'" in str(raised.value), 'the refusal names the file'


@pytest.mark.parametrize(
    'verb', [pytest.param(merge, id='merge'), pytest.param(lambda p: override(p, p), id='override')]
)
def test_one_path_where_a_list_is_asked_for_is_refused(tmp_path, verb):
    """A string is a sequence of letters, and each letter was read as the path of a file."""
    path = str(_written(tmp_path, [SURFACE])[0])
    with pytest.raises(TypeError, match=r'this is one path') as raised:
        verb(path)
    assert f'[{path!r}]' in str(raised.value), 'the refusal names the rewrite, which is a list of the one path'


#: A patch that adds what it needs and a constraint that reads it, so the
#: composed spec is one `to_spec` accepts rather than only one that lays.
CARBON = {
    'parameters': {'co2': {'dims': ['generator']}},
    'constraints': {'co2_cap': {'dims': [], 'expression': 'sum(p * co2) <= 100'}},
}

#: A base that reads a solved spec: one given column, one given constraint and
#: an expression over the constraint, so a patch to `given:` is checked by
#: `to_spec` rather than only laid.
GIVEN_BASE = {
    'dimensions': {'g': {'dtype': 'str'}},
    'given': {'variables': {'p': {'dims': ['g']}}, 'constraints': {'cap': {'dims': ['g']}}},
    'expressions': {'price': {'expression': 'dual(cap)'}},
}

#: `DISPATCH_MODEL` with no objective, for the patches that ask about one.
FEASIBILITY = {k: v for k, v in DISPATCH_MODEL.items() if k != 'objective'}


def test_a_patch_names_only_the_field_it_changes():
    laid = override(DISPATCH_MODEL, [{'variables': {'p': {'where': 'p_max > 0'}}}])
    p = laid.variables['p']
    assert (p.dims, p.bounds.lower, p.bounds.upper, p.where) == (['snapshot', 'generator'], 0, 'p_max', 'p_max > 0'), (
        'the fields the patch does not name are the ones the base declared'
    )


def test_the_base_and_the_patches_are_never_mutated():
    """The guarantee belongs to the function rather than to the caller's discipline."""
    patches = [CARBON, {'variables': {'p': {'where': 'p_max > 0'}}}]
    before = copy.deepcopy((DISPATCH_MODEL, patches))
    override(DISPATCH_MODEL, patches)
    assert before == (DISPATCH_MODEL, patches), 'a patched base is a new mapping, and both inputs are untouched'


def test_a_whole_declaration_is_created_and_the_model_loads():
    spec = override(DISPATCH_MODEL, [CARBON])
    assert 'co2_cap' in spec.constraints
    assert to_markdown(spec), 'a composed spec is one a reviewer can read as math'


@pytest.mark.parametrize(
    ('patch', 'says'),
    [
        pytest.param({'constraints': {'balnce': {'dims': ['snapshot']}}}, "Did you mean 'balance'?", id='a-near-miss'),
        pytest.param(
            {'constraints': {'co2_cap': {'dims': []}}}, 'a constraint needs `expression`', id='short-of-a-field'
        ),
        pytest.param({'parameters': {'co2': {'dtype': 'float'}}}, 'a parameter needs `dims`', id='short-of-its-frame'),
        pytest.param(
            {'expressions': {'spend': {'dims': ['snapshot']}}},
            'one `expression:` or a set of `cases:`',
            id='short-of-what-it-says',
        ),
        pytest.param(
            {'given': {'variables': {'flow': {'domain': 'binary'}}}},
            'a given variable needs `dims`',
            id='a-given-column-short-of-its-frame',
        ),
    ],
)
def test_a_partial_entry_that_lands_on_nothing_is_refused(patch, says):
    """The typo case: laying a partial entry on nothing would invent a declaration nothing refers to."""
    with pytest.raises(LanguageError, match=r'does not declare') as raised:
        override(DISPATCH_MODEL, [patch])
    assert says in str(raised.value), 'the refusal says what the entry is short of, or what it nearly named'


def test_a_null_removes_a_declaration_and_the_model_still_loads():
    laid = override(DISPATCH_MODEL, [{'constraints': {'balance': None}}])
    assert laid.constraints == {}, 'the declaration is gone rather than emptied'


def test_a_stale_removal_is_refused():
    with pytest.raises(LanguageError, match=r"'balnce'.*does not declare.*Did you mean 'balance'\?"):
        override(DISPATCH_MODEL, [{'constraints': {'balnce': None}}])


@pytest.mark.parametrize(
    ('patch', 'field', 'default'),
    [
        pytest.param({'variables': {'p': {'where': None}}}, lambda s: s.variables['p'].where, None, id='a-mask'),
        pytest.param(
            {'variables': {'p': {'bounds': {'upper': None}}}},
            lambda s: s.program.variables['p'].upper,
            None,
            id='a-bound-two-levels-down',
        ),
        pytest.param(
            {'variables': {'p': {'domain': None}}},
            lambda s: s.variables['p'].domain,
            'continuous',
            id='a-field-that-takes-no-null',
        ),
        pytest.param({'version': None}, lambda s: s.version, 0, id='a-top-level-field-that-takes-no-null'),
    ],
)
def test_a_null_field_takes_its_default(patch, field, default):
    """`null` makes what it names absent: a declaration is removed, and a field takes its default.

    A field that takes no null was the case that failed: `domain: null` was laid
    as a value the schema refuses, so a patch could not put a field back to its
    default.
    """
    base = varied(
        DISPATCH_MODEL,
        **{'description': 'dispatch', 'variables.p.where': 'p_max > 0', 'variables.p.domain': 'integer'},
    )
    laid = override(base, [patch])
    assert field(laid) == default
    assert laid.variables['p'].bounds.lower == 0, 'a field the patch does not name stays as the base wrote it'


@pytest.mark.parametrize(
    ('patches', 'field', 'value'),
    [
        pytest.param(
            [{'variables': {'p': {'bounds': {'upper': 'p_max'}}}}, {'variables': {'p': {'bounds': {'upper': 'cost'}}}}],
            lambda s: s.variables['p'].bounds.upper,
            'cost',
            id='one-field-twice',
        ),
        pytest.param(
            [{'objective': {'sense': 'maximize'}}, {'objective': {'sense': 'minimize'}}],
            lambda s: s.objective.sense,
            'minimize',
            id='the-objective-twice',
        ),
        pytest.param(
            [CARBON, {'constraints': {'co2_cap': {'expression': 'sum(p * co2) <= 50'}}}],
            lambda s: s.constraints['co2_cap'].expression,
            'sum(p * co2) <= 50',
            id='an-edit-to-what-an-earlier-patch-creates',
        ),
        pytest.param(
            [CARBON, {'constraints': {'co2_cap': None}}],
            lambda s: sorted(s.constraints),
            ['balance'],
            id='a-removal-of-what-an-earlier-patch-creates',
        ),
    ],
)
def test_a_later_patch_is_laid_on_what_the_earlier_ones_make(patches, field, value):
    """Patches are laid in the order given, so a project patch overrides a pathway patch without a nested call.

    Two patches that wrote one field were refused, and layering one on the
    other took a second `override` around the first.
    """
    assert field(override(DISPATCH_MODEL, patches)) == value


def test_a_patch_adds_a_dimension_and_may_restate_one_it_shares():
    laid = override(
        DISPATCH_MODEL,
        [{'dimensions': {'snapshot': {'dtype': 'int', 'ordered': True}, 'investment_period': {'dtype': 'int'}}}],
    )
    assert sorted(laid.dimensions) == ['generator', 'investment_period', 'snapshot'], (
        'the dimension the patch adds joins the two the base declares, and the restated one is not doubled'
    )


@pytest.mark.parametrize(
    ('dimension', 'restated', 'ordered'),
    [
        pytest.param('generator', {'dtype': 'str', 'ordered': False}, False, id='false-written-out'),
        pytest.param('generator', {'dtype': 'str', 'ordered': True}, True, id='widened-to-ordered'),
        pytest.param('snapshot', {'dtype': 'int'}, True, id='ordered-left-out'),
        pytest.param('generator', {}, False, id='defaults-left-out'),
    ],
)
def test_a_patch_restates_a_dimension_as_the_schema_reads_it(dimension, restated, ordered):
    """A written ``ordered: false`` differed from the omitted one, and a patch could not add the claim."""
    laid = override(DISPATCH_MODEL, [{'dimensions': {dimension: restated}}])
    assert laid.dimensions[dimension].ordered is ordered


def test_a_patch_that_withdraws_ordered_is_refused():
    with pytest.raises(LanguageError, match=r"says the dimension 'snapshot' is not ordered") as raised:
        override(DISPATCH_MODEL, [{'dimensions': {'snapshot': {'dtype': 'int', 'ordered': False}}}])
    assert 'leave `ordered` out of the patch' in str(raised.value), 'the refusal names the rewrite'


@pytest.mark.parametrize(
    ('patch', 'says'),
    [
        pytest.param(
            {'dimensions': {'snapshot': {'dtype': 'str'}}},
            'adjusts the math, not the coordinate space',
            id='declared-as-something-else',
        ),
        pytest.param(
            {'dimensions': {'snapshot': {}}},
            'a field the patch leaves out reads as its default',
            id='restated-in-part',
        ),
        pytest.param(
            {'dimensions': {'snapshot': None}},
            'remove the declarations written over it one at a time',
            id='removed',
        ),
    ],
)
def test_a_patch_that_rewrites_a_dimension_is_refused(patch, says):
    """A dimension changed under the expressions already written over it is a different spec, silently.

    The refusal asked for the declaration word for word, where a restatement that leaves out a field
    at its default is accepted.
    """
    with pytest.raises(LanguageError) as raised:
        override(DISPATCH_MODEL, [patch])
    assert says in str(raised.value), 'the refusal names the rewrite rather than only what is wrong'


#: `SURFACE` with `port_bus` declared `missing: absent`.
ABSENT_SURFACE = varied(SURFACE, **{'relations.port_bus.missing': 'absent'})


@pytest.mark.parametrize(
    ('base', 'relation', 'missing'),
    [
        pytest.param(SURFACE, {'missing': 'absent'}, 'absent', id='the-reading-alone'),
        pytest.param(SURFACE, {'key': 'port', 'values': 'bus', 'missing': 'absent'}, 'absent', id='restated-absent'),
        pytest.param(ABSENT_SURFACE, {'missing': 'refused'}, 'refused', id='back-to-the-default'),
        pytest.param(ABSENT_SURFACE, {'missing': None}, 'refused', id='null-puts-back-the-default'),
        pytest.param(SURFACE, {'key': 'port', 'values': 'bus', 'missing': 'refused'}, 'refused', id='default-written'),
        pytest.param(ABSENT_SURFACE, {'key': 'port', 'values': 'bus'}, 'absent', id='restated-without-one'),
    ],
)
def test_a_patch_changes_what_a_key_the_map_leaves_out_means(base, relation, missing):
    """`missing:` is a claim about the data, not the coordinate space, and a patch that wrote it was refused as one."""
    assert override(base, [{'relations': {'port_bus': relation}}]).relations['port_bus'].missing == missing


@pytest.mark.parametrize(
    ('base', 'written', 'missing'),
    [
        pytest.param(DISPATCH_MODEL, 'neutral', 'neutral', id='a-reading'),
        pytest.param(
            varied(DISPATCH_MODEL, **{'parameters.cost.missing': 'absent'}),
            None,
            'refused',
            id='null-puts-back-the-default',
        ),
    ],
)
def test_a_patch_changes_what_a_missing_row_of_a_parameter_means(base, written, missing):
    assert override(base, [{'parameters': {'cost': {'missing': written}}}]).parameters['cost'].missing == missing


@pytest.mark.parametrize(
    ('section', 'name', 'declared'),
    [
        pytest.param('parameters', 'c', {'dims': ['g']}, id='a-parameter'),
        pytest.param('relations', 'lk', {'key': 'g', 'values': 'h'}, id='a-relation'),
    ],
)
def test_the_default_missing_written_out_is_the_spec_that_leaves_it_out(section, name, declared):
    """`missing: refused` loaded to a different spec than no `missing:`, and wrote a different canonical text."""
    omitted = to_spec(varied(SMALL_MODEL, **{f'{section}.{name}': declared}))
    written = to_spec(varied(SMALL_MODEL, **{f'{section}.{name}': {**declared, 'missing': 'refused'}}))
    assert written == omitted, 'the default written out is the default'
    assert canonical_yaml(written) == canonical_yaml(omitted), 'so both spellings write one text'


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({'constraints': None}, id='an-owned-section'),
        pytest.param({'dimensions': None}, id='a-shared-section'),
        pytest.param({'given': {'variables': None}}, id='one-kind-of-given'),
    ],
)
def test_a_whole_section_set_to_null_is_refused(patch):
    """Nulling a section reads as emptying it, and laying it silently changed nothing at all."""
    with pytest.raises(LanguageError, match=r'removes nothing') as raised:
        override(DISPATCH_MODEL, [patch])
    assert 'one at a time' in str(raised.value), 'the refusal names the rewrite, which is one null per declaration'


def test_the_objective_is_laid_over_field_by_field():
    laid = override(DISPATCH_MODEL, [{'objective': {'sense': 'maximize'}}])
    assert laid.objective is not None
    assert (laid.objective.sense, laid.objective.expression) == ('maximize', 'sum(p * cost)'), (
        'the sense the patch names changes, and the expression the base wrote stays'
    )


def test_the_objective_can_be_removed_and_the_model_is_a_feasibility_problem():
    laid = override(DISPATCH_MODEL, [{'objective': None}])
    assert laid.objective is None


def test_a_whole_objective_is_created_where_the_base_has_none():
    laid = override(FEASIBILITY, [{'objective': DISPATCH_MODEL['objective']}])
    assert laid.objective is not None


@pytest.mark.parametrize(
    ('patch', 'says'),
    [
        pytest.param({'objective': None}, 'already the feasibility problem', id='removing-one-that-is-not-there'),
        pytest.param(
            {'objective': {'sense': 'maximize'}}, 'an objective needs `expression`', id='editing-one-that-is-not-there'
        ),
    ],
)
def test_an_objective_a_base_does_not_declare_is_refused(patch, says):
    with pytest.raises(LanguageError, match=r'does not declare') as raised:
        override(FEASIBILITY, [patch])
    assert says in str(raised.value)


def test_a_patch_over_one_kind_of_given_leaves_the_other_alone():
    """`given:` is laid over a kind at a time, so patching the columns cannot drop the row families."""
    laid = override(GIVEN_BASE, [{'given': {'variables': {'p': {'domain': 'binary'}}}}])
    p = laid.given.variables['p']
    assert (p.dims, p.domain) == (['g'], 'binary'), 'the given column is edited field by field like any declaration'
    assert sorted(laid.given.constraints) == ['cap'], 'the kind the patch did not name is still there'


@pytest.mark.parametrize(
    ('base', 'reads'),
    [
        pytest.param(GIVEN_BASE, ['p', 'q'], id='a-base-that-already-reads'),
        pytest.param({'dimensions': {'g': {'dtype': 'str'}}}, ['q'], id='a-base-that-reads-nothing-yet'),
    ],
)
def test_a_whole_given_entry_is_created_and_the_model_loads(base, reads):
    """A patch adds a column to read, whether or not the base opened the block."""
    laid = override(base, [{'given': {'variables': {'q': {'dims': ['g']}}}}])
    assert sorted(laid.given.variables) == reads, 'the created column joins whatever the base read'


def test_a_patch_is_a_path_as_readily_as_a_mapping(tmp_path):
    """Whatever every other verb takes, so a patch travels as a file rather than as a script."""
    patch = tmp_path / 'carbon.yaml'
    patch.write_text('parameters:\n  co2: {dims: [generator]}\n', encoding='utf-8')
    laid = override(DISPATCH_MODEL, [str(patch)])
    assert 'co2' in laid.parameters


def test_a_base_that_does_not_load_is_refused_though_a_patch_would_mend_it():
    """A base is a spec a framework ships, so one that does not load is refused before a patch reaches it."""
    unpriced = {**DISPATCH_MODEL, 'parameters': {k: v for k, v in DISPATCH_MODEL['parameters'].items() if k != 'cost'}}
    with pytest.raises(LanguageError, match=r"'cost' not found"):
        override(unpriced, [{'parameters': {'cost': {'dims': ['generator']}}}])


def test_a_loaded_spec_is_a_base_as_readily_as_a_mapping():
    laid = override(to_spec(DISPATCH_MODEL), [CARBON])
    assert 'co2_cap' in laid.constraints


@pytest.mark.parametrize(
    ('kind', 'entry'),
    [
        pytest.param('parameters', {'dims': ['g'], 'dtype': 'bool'}, id='a-parameter'),
        pytest.param('expressions', {'dims': ['g']}, id='an-expression'),
    ],
)
def test_a_patch_creates_a_given_entry_of_every_kind(kind, entry):
    """`override` lays `given:` over by the kinds `merge` folds, so a kind added to one reaches the other."""
    laid = override(GIVEN_BASE, [{'given': {kind: {'r': entry}}}])
    assert getattr(laid.given, kind)['r'].dims == ['g']
    assert sorted(laid.given.variables) == ['p'], 'the kinds the patch did not name are still there'
