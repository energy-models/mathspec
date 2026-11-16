# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A dimension that lists its members under `over:`: what loads, what it implies, and what is refused.

Its label is the tuple of its members, and it is one plain dimension in every
operator. A member is read through the relation the entry implies, which has
the name of the dimension.
"""

from __future__ import annotations

from typing import Any

import pytest

from mathspec import merge, rename, to_spec
from mathspec._typesetting import FORMATS, typeset
from mathspec.errors import LanguageError
from mathspec.program import JoinedCondition, Relation, RelationComparison
from tests.fixtures import varied

#: The example of #1011: `connection` lists (unit, port) pairs, `trade` lists
#: two regions by role, and `active` is a sparse set with an ordered member.
MODEL: dict[str, Any] = {
    'dimensions': {
        'unit': {},
        'port': {},
        'bus': {},
        'region': {},
        'snapshot': {'dtype': 'int', 'ordered': True},
        'period': {'dtype': 'int', 'ordered': True},
        'connection': {'over': ['unit', 'port']},
        'trade': {'over': {'src': 'region', 'dst': 'region'}},
    },
    'relations': {
        'connection_bus': {'key': 'connection', 'values': 'bus'},
        'active': {'key': ['unit', 'period'], 'missing': 'absent'},
    },
    'parameters': {
        'capacity': {'dims': ['unit']},
        'rating': {'dims': ['unit', 'port']},
        'tariff': {'dims': ['region']},
        'load': {'dims': ['bus', 'snapshot']},
    },
    'variables': {
        'flow': {'dims': ['connection', 'snapshot'], 'bounds': {'lower': 0}},
        'shipped': {'dims': ['trade'], 'bounds': {'lower': 0}},
        'both': {'dims': ['connection', 'unit']},
    },
    'constraints': {
        'limit': {'dims': ['connection', 'snapshot'], 'expression': 'flow <= at(capacity, by=connection[unit])'},
        'balance': {
            'dims': ['bus', 'snapshot'],
            'expression': 'sum(flow, over=connection, by=connection_bus[bus]) == load',
        },
    },
}


FRAGMENT: dict[str, Any] = {
    'dimensions': {'unit': {}, 'port': {}, 'connection': {'over': ['unit', 'port']}},
    'variables': {'flow': {'dims': ['connection']}},
}


def _refusal(**patch: Any) -> str:
    """The message `to_spec` refuses the model patched with, and it has to refuse."""
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(MODEL, **patch))
    return str(caught.value)


def _constraint(expression: str, dims: list[str]) -> dict[str, Any]:
    return {'constraints.probe': {'dims': dims, 'expression': expression}}


def test_a_dimension_with_members_implies_a_relation_of_its_name():
    program = to_spec(MODEL).program
    connection = program.dimensions['connection']
    assert connection.over == (('port', 'port'), ('unit', 'unit')), 'members are (role, dimension), sorted by role'
    assert connection.missing == 'absent', 'a tuple dimension is a sparse subset unless the file says refused'
    assert program.relations['connection'] == Relation(
        (('connection', 'connection'), ('port', 'port'), ('unit', 'unit')), ('connection',), 'refused'
    ), 'the implied relation is keyed by the dimension and has one value column per member'
    assert program.dimensions['trade'].over == (('dst', 'region'), ('src', 'region')), 'a role names each member'
    assert program.dimensions['unit'].over == (), 'a plain dimension has no members'


def test_the_order_of_the_members_changes_nothing():
    swapped = varied(MODEL, **{'dimensions.connection': {'over': ['port', 'unit']}})
    assert to_spec(swapped) == to_spec(MODEL)


@pytest.mark.parametrize('missing', ['absent', 'refused'])
def test_missing_says_whether_the_full_product_is_required(missing):
    spec = to_spec(varied(MODEL, **{'dimensions.connection.missing': missing}))
    assert spec.program.dimensions['connection'].missing == missing
    assert spec.program.relations['connection'].missing == 'refused', 'every tuple has its members, either way'


@pytest.mark.parametrize(
    ('expression', 'dims'),
    [
        pytest.param('flow <= at(capacity, by=connection[unit])', ['connection', 'snapshot'], id='one-member'),
        pytest.param('flow <= at(rating, by=connection[unit, port])', ['connection', 'snapshot'], id='every-member'),
        pytest.param('shipped <= at(tariff, by=trade[src])', ['trade'], id='a-member-by-role'),
        pytest.param(
            'sum(flow, over=connection, by=connection[port]) >= 0', ['port', 'snapshot'], id='sum-to-a-member'
        ),
        pytest.param('sum(flow, over=connection) >= 0', ['snapshot'], id='sum-the-tuples-away'),
    ],
)
def test_a_member_is_read_through_the_implied_relation(expression, dims):
    constraint = to_spec(varied(MODEL, **_constraint(expression, dims))).program.constraints['probe']
    assert sorted({*constraint.lhs.dims, *constraint.rhs.dims}) == sorted(dims)


def test_a_bound_reads_a_parameter_of_a_member():
    spec = to_spec(varied(MODEL, **{'variables.flow.bounds.upper': 'at(capacity, by=connection[unit])'}))
    assert spec.program.variables['flow'].upper.dims == ('connection',)


def test_a_condition_compares_a_member_label():
    spec = to_spec(varied(MODEL, **{'variables.flow.where': "connection[unit] == 'gas'"}))
    (atom,) = spec.program.variables['flow'].where.atoms
    assert atom == RelationComparison('connection', 'unit', '==', 'gas', ('connection',))


def test_a_sparse_set_with_an_ordered_member_is_read_at_a_tuple():
    """Rule 9 of #1011: `active` stays a bare relation over (unit, period), and an entry over `connection` reads it with `at`."""
    built = {'dims': ['connection', 'period'], 'where': 'at(active, by=connection[unit])'}
    spec = to_spec(varied(MODEL, **{'variables.built': built}))
    (atom,) = spec.program.variables['built'].where.atoms
    assert isinstance(atom, JoinedCondition)
    assert spec.program.variables['built'].where.dims == ('connection', 'period')


@pytest.mark.parametrize(
    ('patch', 'fragments'),
    [
        pytest.param(
            {'dimensions.pair': {'over': ['connection', 'bus']}},
            (
                "Dimension 'pair' lists 'connection' under 'over:', and 'connection' has members of its own",
                "over: ['bus', 'port', 'unit']",
            ),
            id='a-tuple-dimension-as-a-member',
        ),
        pytest.param(
            {'dimensions.pair': {'over': ['unit', 'nope']}},
            ("Dimension 'pair' references undeclared dimension 'nope'",),
            id='an-undeclared-member',
        ),
        pytest.param(
            {'dimensions.connection.ordered': True},
            ('dimensions.connection', '`ordered: true`', 'no order', "over ['port', 'unit']", 'where:'),
            id='ordered',
        ),
        pytest.param(
            {'dimensions.connection.one_of': ['a']},
            ('dimensions.connection', '`one_of:`', 'the label is the tuple of its members', 'one_of: of a member'),
            id='one-of',
        ),
        pytest.param(
            {'dimensions.connection.dtype': 'str'},
            ('dimensions.connection', '`dtype:`', 'the label is the tuple of its members', 'dtype: of a member'),
            id='dtype',
        ),
        pytest.param(
            {'dimensions.bus.missing': 'refused'},
            ('dimensions.bus', '`missing:`', 'without `over:`', 'Delete `missing:`'),
            id='missing-without-members',
        ),
        pytest.param(
            {'dimensions.connection.missing': 0},
            ('missing: 0 on a dimension', 'takes absent or refused'),
            id='missing-is-a-number',
        ),
        pytest.param(
            {'dimensions.connection.over': []},
            ('dimensions.connection.over', 'lists no member', 'leave `over:` out'),
            id='no-member',
        ),
        pytest.param(
            {'dimensions.pair': {'over': {'port': 'unit', 'bus': 'bus'}}},
            ("Dimension 'pair' names member 'port' after dimension 'port', but the member is over 'unit'", 'Rename'),
            id='a-role-named-after-another-dimension',
        ),
        pytest.param(
            {'dimensions.pair': {'over': ['region', 'region']}},
            ("Dimension 'pair' lists 'region' twice under 'over:'", 'over: {region0: region, region1: region}'),
            id='a-dimension-twice-in-the-list-form',
        ),
        pytest.param(
            {'relations.connection': {'key': ['unit', 'port']}},
            ("Relation 'connection' collides with the dimension of the same name",),
            id='a-declared-relation-of-the-same-name',
        ),
        pytest.param(
            _constraint("shift(flow, along=connection, offset=1, edge='wrap') >= 0", ['connection', 'snapshot']),
            ("shift(along=connection) reads the order of 'connection'", 'no order', "over ['port', 'unit']"),
            id='shift',
        ),
        pytest.param(
            _constraint('sum_back(flow, along=connection, window=2) >= 0', ['connection', 'snapshot']),
            ("sum_back(along=connection) reads the order of 'connection'", 'no order'),
            id='sum-back',
        ),
        pytest.param(
            {'variables.flow.where': 'position(connection) == 0'},
            ("position(connection) reads the order of 'connection'", 'no order'),
            id='position',
        ),
        pytest.param(
            _constraint(
                "shift(flow, along=snapshot, offset=1, edge='wrap', within=connection[unit]) >= 0",
                ['connection', 'snapshot'],
            ),
            ("shift(within=connection[unit]) reads the order of 'connection'", 'no order'),
            id='within',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['connection']},
                'parameters.ys': {'dims': ['connection']},
                'variables.x': {'dims': []},
                'variables.y': {'dims': []},
                'piecewise.curve': {'dims': [], 'along': 'connection', 'links': {'x': ['x', 'xs'], 'y': ['y', 'ys']}},
            },
            ("piecewise 'curve': along: connection reads the order of 'connection'", 'no order'),
            id='piecewise',
        ),
        pytest.param(
            {
                'variables.flow.bounds.upper': 1,
                'sos.pick': {'variable': 'flow', 'along': 'connection', 'type': 1},
            },
            ("Sos 'pick': along: connection", 'lists its members', "over ['port', 'unit']"),
            id='sos',
        ),
        pytest.param(
            _constraint('at(both, by=connection[unit]) >= 0', ['connection']),
            (
                "at(by=connection[unit]) reads through 'connection'",
                "carries both 'connection' and its member ['unit']",
                "Sum ['unit'] out of the operand first",
            ),
            id='an-operand-with-the-tuple-and-a-member',
        ),
        pytest.param(
            _constraint('sum(flow, over=unit) >= 0', ['connection', 'snapshot']),
            (
                "'unit' is a member of 'connection'",
                'sum(..., over=connection, by=connection[port])',
            ),
            id='over-names-a-member',
        ),
        pytest.param(
            _constraint('sum(flow, over=unit, by=connection[port]) >= 0', ['port', 'snapshot']),
            ("over=unit names a member of 'connection'", 'sum(..., over=connection, by=connection[port])'),
            id='over-names-a-member-beside-by',
        ),
        pytest.param(
            _constraint('sum(flow, over=unit, by=connection_bus[bus]) >= 0', ['bus', 'snapshot']),
            ("'unit' is a member of 'connection'", 'write over=connection.'),
            id='over-names-a-member-beside-another-relation',
        ),
        pytest.param(
            _constraint('sum(flow, over=[unit, port]) >= 0', ['snapshot']),
            ("'unit' is a member of 'connection'", 'Write sum(..., over=connection).'),
            id='over-names-every-member',
        ),
        pytest.param(
            _constraint('sum(shipped, over=region) >= 0', ['trade']),
            ("'region' is a member of 'trade'", 'by=trade[<the members to keep>]'),
            id='over-names-a-dimension-two-roles-are-over',
        ),
        pytest.param(
            _constraint('flow <= capacity', ['connection', 'snapshot']),
            ("carries dims ['unit'] that are not in its dims", 'at(capacity, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple',
        ),
        pytest.param(
            {'variables.flow.bounds.upper': 'capacity'},
            ("parameter 'capacity' has dims ['unit'] outside", 'at(capacity, by=connection[unit])'),
            id='a-bound-over-a-member',
        ),
        pytest.param(
            {'variables.flow.where': 'capacity > 0'},
            ("reads dims ['unit'] outside the declared dims", 'at(..., by=connection[unit])'),
            id='a-where-over-a-member',
        ),
        pytest.param(
            {'variables.flow.where': "connection == 'a'"},
            ("'connection' lists its members", 'no label to compare', "connection[port] == 'a'"),
            id='a-label-comparison',
        ),
    ],
)
def test_what_a_tuple_dimension_does_not_take_is_refused_with_the_rewrite(patch, fragments):
    message = _refusal(**patch)
    for fragment in fragments:
        assert fragment in message


def test_no_advice_about_a_tuple_dimension_where_none_is_in_play():
    """A stray dimension that is no member keeps the advice it had."""
    message = _refusal(**_constraint('flow <= load', ['connection', 'snapshot']))
    assert 'Add them to dims:, or sum them out' in message
    assert 'at(' not in message, 'bus is no member of connection'


@pytest.mark.parametrize('fmt', FORMATS)
@pytest.mark.parametrize(
    ('missing', 'relation'),
    [pytest.param('absent', 'subset_of', id='a-subset'), pytest.param('refused', 'equal', id='the-full-product')],
)
def test_the_legend_prints_the_members(fmt, missing, relation):
    spec = to_spec(varied(FRAGMENT, **{'dimensions.connection.missing': missing}))
    ops = FORMATS[fmt].operators
    c, p, u = ((r'cal(%s)' if fmt == 'typst' else r'\mathcal{%s}') % letter for letter in 'CPU')
    assert f'{c} {ops[relation]} {p} {ops["times"]} {u}' in typeset(spec, fmt), f'{fmt} prints the product'
    assert 'connection}:' not in typeset(spec, fmt), 'the implied relation has no row of its own beside the product'


def test_fragments_that_agree_on_the_members_merge():
    other = {
        'dimensions': {'port': {}, 'unit': {}, 'connection': {'over': ['port', 'unit']}},
        'variables': {'loss': {'dims': ['connection']}},
    }
    assert merge([FRAGMENT, other]).program.dimensions['connection'].over == (('port', 'port'), ('unit', 'unit'))


@pytest.mark.parametrize(
    'connection',
    [
        pytest.param({'over': ['unit']}, id='other-members'),
        pytest.param({'over': {'unit': 'unit', 'side': 'port'}}, id='other-roles'),
        pytest.param({'over': ['unit', 'port'], 'missing': 'refused'}, id='other-missing'),
        pytest.param({}, id='no-members'),
    ],
)
def test_fragments_that_disagree_on_the_members_are_refused(connection):
    other = {
        'dimensions': {'port': {}, 'unit': {}, 'connection': connection},
        'variables': {'loss': {'dims': ['connection']}},
    }
    with pytest.raises(LanguageError, match=r"say different things about the dimension 'connection'") as raised:
        merge([FRAGMENT, other])
    assert 'Make the two identical' in str(raised.value)


def test_a_patch_cannot_change_the_members():
    from mathspec import override

    with pytest.raises(LanguageError, match=r"declares the dimension 'connection'"):
        override(FRAGMENT, [{'dimensions': {'connection': {'over': ['unit']}}}])


def test_rename_reaches_the_members_and_the_implied_relation():
    renamed = rename(MODEL, {'unit': 'plant', 'connection': 'link', 'region': 'zone'})
    assert renamed.dimensions['link'].over == ('plant', 'port')
    assert dict(renamed.dimensions['trade'].over) == {'src': 'zone', 'dst': 'zone'}, 'a role keeps its name'
    assert renamed.constraints['limit'].expression == 'flow <= at(capacity, by=link[plant])'
    assert rename(renamed, {'plant': 'unit', 'link': 'connection', 'zone': 'region'}) == to_spec(MODEL)


@pytest.mark.parametrize(
    'names', [pytest.param({'src': 'origin'}, id='from-a-role'), pytest.param({'bus': 'src'}, id='to-a-role')]
)
def test_rename_refuses_a_name_that_is_a_role(names):
    """A token is renamed wherever it is spelt, so a role named after no dimension would change with an entry of its name."""
    model = varied(MODEL, **{'parameters.src': {'dims': []}}) if 'src' in names else MODEL
    with pytest.raises(LanguageError, match=r"'src' is also a member of the dimension 'trade'"):
        rename(model, names)


@pytest.mark.parametrize('canonical', [False, True])
def test_a_spec_with_members_is_written_and_read_back(canonical):
    spec = to_spec(MODEL)
    assert to_spec(spec.to_yaml(canonical=canonical)).program == spec.program
