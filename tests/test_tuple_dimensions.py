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

from mathspec import merge, override, rename, to_spec
from mathspec._advising import advice
from mathspec._typesetting import FORMATS, typeset
from mathspec.errors import LanguageError
from mathspec.program import JoinedCondition, Relation, RelationComparison, RelationPairComparison
from tests.fixtures import varied

#: The example of #1011: `connection` lists (unit, port) pairs, `trade` lists
#: two regions through an alias, and `active` is a sparse set with an ordered member.
MODEL: dict[str, Any] = {
    'dimensions': {
        'unit': {},
        'port': {},
        'bus': {},
        'region': {},
        'snapshot': {'dtype': 'int', 'ordered': True},
        'period': {'dtype': 'int', 'ordered': True},
        'connection': {'over': ['unit', 'port']},
        'from_region': {'alias': 'region'},
        'trade': {'over': ['from_region', 'region']},
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
    assert connection.over == ('port', 'unit'), 'members are sorted by name'
    assert connection.missing == 'absent', 'a tuple dimension is a sparse subset unless the file says refused'
    assert program.relations['connection'] == Relation(
        (('connection', 'connection'), ('port', 'port'), ('unit', 'unit')), ('connection',), 'refused'
    ), 'the implied relation is keyed by the dimension and has one value column per member'
    assert program.dimensions['trade'].over == ('from_region', 'region'), 'an alias lists one dimension twice'
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
        pytest.param('shipped <= at(tariff, by=trade[region])', ['trade'], id='a-member-beside-its-alias'),
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


#: A second tuple dimension that shares `unit` with `connection`, and an entry over each.
SHARED_MEMBER: dict[str, Any] = {
    'dimensions.assignment': {'over': ['unit', 'period']},
    'relations.backup': {'key': 'connection', 'values': {'spare': 'unit'}},
    'variables.sent': {'dims': ['connection']},
    'variables.on': {'dims': ['assignment']},
}


def test_a_member_column_is_compared_with_a_column_of_a_relation_keyed_alike():
    """Rule 2 of #1011: the implied relation is a relation in a comparison of two columns, as on main.

    Was: a side named after a tuple dimension was read as the dimension, so
    `connection[unit] == backup[spare]` was refused as a comparison against a relation.
    """
    constraint = {'dims': ['connection'], 'expression': 'sent <= 1', 'where': 'connection[unit] == backup[spare]'}
    spec = to_spec(varied(MODEL, **SHARED_MEMBER, **{'constraints.probe': constraint}))
    pair = RelationPairComparison('connection', 'unit', 'backup', 'spare', '==', ('connection',))
    assert spec.program.constraints['probe'].where.atoms == (pair,)


def test_two_tuple_dimensions_compare_no_member_column():
    """Two relations keyed over different dimensions compare nowhere, as on main: no entry is over both keys."""
    constraint = {'dims': ['connection'], 'expression': 'sent <= 1', 'where': 'connection[unit] == assignment[unit]'}
    message = _refusal(**SHARED_MEMBER, **{'constraints.probe': constraint})
    assert "keyed over different dimensions ('connection' by ['connection'], 'assignment' by ['assignment'])" in message
    assert 'Compare relations whose keys are over the same dimensions' in message


@pytest.mark.parametrize(
    ('cases', 'fragment'),
    [
        pytest.param(
            {'same': 'connection[unit] == backup[spare]', 'apart': 'connection[unit] != backup[spare]'},
            None,
            id='a-comparison-and-its-complement',
        ),
        pytest.param(
            {'same': 'connection[unit] == backup[spare]', 'gas': "connection[unit] == 'gas'"},
            'backup[spare] vs connection[unit] is equal',
            id='a-comparison-and-a-label',
        ),
    ],
)
def test_a_case_tests_a_member_column_against_another_column(cases, fragment):
    """The exclusivity check reads the comparison as one fact per tuple: true, false, or a row missing."""
    entry = {
        'dims': ['connection'],
        'cases': {name: {'when': when, 'expression': 'sent'} for name, when in cases.items()},
        'otherwise': 0,
    }
    patch = {**SHARED_MEMBER, 'expressions.e': entry}
    if fragment is None:
        to_spec(varied(MODEL, **patch))
    else:
        assert fragment in _refusal(**patch)


@pytest.mark.parametrize('fmt', FORMATS)
def test_a_member_column_compared_with_another_column_is_typeset(fmt):
    constraint = {'dims': ['connection'], 'expression': 'sent <= 1', 'where': 'connection[unit] == backup[spare]'}
    spec = to_spec(varied(MODEL, **SHARED_MEMBER, **{'constraints.probe': constraint}))
    text = typeset(spec, fmt).split('probe', 1)[1]
    assert 'unit' in text, f'{fmt} prints the member column'
    assert 'backup' in text, f'{fmt} prints the other relation'


def _entry(kind: str, dims: list[str]) -> dict[str, Any]:
    """An entry of *kind* over *dims*, its `where:` joining the two tuple dimensions where it has one."""
    where = 'connection[unit] == assignment[unit]'
    entries: dict[str, dict[str, Any]] = {
        'parameter': {'parameters.probe': {'dims': dims, 'where': where}},
        'variable': {'variables.probe': {'dims': dims, 'where': where}},
        'constraint': {'constraints.probe': {'dims': dims, 'expression': 'sent <= 1', 'where': where}},
        'named-expression': {'expressions.probe': {'dims': dims, 'expression': 'sent'}},
        'case': {
            'expressions.probe': {'dims': dims, 'cases': {'a': {'when': where, 'expression': 'sent'}}, 'otherwise': 0}
        },
        'piecewise': {
            'parameters.xs': {'dims': ['period']},
            'parameters.ys': {'dims': ['period']},
            'piecewise.probe': {'dims': dims, 'along': 'period', 'links': {'x': ['sent', 'xs'], 'y': ['on', 'ys']}},
        },
        'given-variable': {'given.variables.probe': {'dims': dims}},
    }
    return entries[kind]


@pytest.mark.parametrize(
    'kind', ['parameter', 'variable', 'constraint', 'named-expression', 'case', 'piecewise', 'given-variable']
)
@pytest.mark.parametrize(
    ('dims', 'fragment'),
    [
        pytest.param(['connection', 'assignment'], "which share 'unit'", id='two-sharing-a-member'),
        pytest.param(['connection', 'unit'], "lists 'connection' and its member 'unit'", id='one-beside-its-member'),
    ],
)
def test_an_entry_over_overlapping_tuple_dimensions_is_refused_whatever_its_where(kind, dims, fragment):
    """A tuple dimension is opaque, so an entry over two that share a member pairs tuples whose members differ.

    Was: the entry loaded as the cross product of the two, and a `where:` that
    compared the shared member kept the pairs of one unit.
    """
    message = _refusal(**SHARED_MEMBER, **_entry(kind, dims))
    assert fragment in message


#: `connection` and `assignment` share `unit`; `f` steps along `snapshot`, which `snap_unit` sends to a unit.
PAIRED: dict[str, Any] = varied(
    FRAGMENT,
    **{
        'dimensions.bus': {},
        'dimensions.period': {'dtype': 'int', 'ordered': True},
        'dimensions.snapshot': {'dtype': 'int', 'ordered': True},
        'dimensions.assignment': {'over': ['unit', 'period']},
        'relations.snap_unit': {'key': 'snapshot', 'values': 'unit'},
        'variables.on': {'dims': ['assignment']},
        'variables.f': {'dims': ['connection', 'snapshot']},
    },
)

_JOINED = {
    'relations.r1': {'key': ['period', 'unit'], 'missing': 'absent'},
    'relations.r2': {'key': ['port', 'unit'], 'missing': 'absent'},
}

_DEPOT = {'dimensions.depot': {'over': ['unit', 'bus']}}


def _curve(along: str) -> dict[str, Any]:
    """A curve over `assignment` whose breakpoints are over *along*."""
    links = {'x': ['on', 'xs'], 'y': ['y', 'ys']}
    return {
        'parameters.xs': {'dims': [along]},
        'parameters.ys': {'dims': [along]},
        'variables.y': {'dims': ['assignment']},
        'piecewise.curve': {'dims': ['assignment'], 'along': along, 'links': links},
    }


@pytest.mark.parametrize(
    ('refused', 'fragment', 'rewrite'),
    [
        pytest.param(
            {'variables.x': {'dims': ['connection', 'assignment']}},
            'dims: [period, port, unit], with where: a relation keyed by [period, unit] and one keyed by [port, unit]',
            {**_JOINED, 'variables.x': {'dims': ['period', 'port', 'unit'], 'where': 'r1 AND r2'}},
            id='an-entry-over-the-members',
        ),
        pytest.param(
            {'variables.x': {'dims': ['connection', 'assignment']}},
            'connection_unit: {alias: unit} and connection: {over: [connection_unit, port]}',
            {
                'dimensions.connection_unit': {'alias': 'unit'},
                'dimensions.connection': {'over': ['connection_unit', 'port']},
                'variables.x': {'dims': ['connection', 'assignment']},
            },
            id='an-alias-of-the-shared-member',
        ),
        pytest.param(
            {**_DEPOT, 'variables.x': {'dims': ['connection', 'assignment', 'depot']}},
            'dims: [bus, period, port, unit], with where: a relation keyed by [period, unit], one keyed by '
            '[bus, unit] and one keyed by [port, unit]',
            {
                **_JOINED,
                **_DEPOT,
                'relations.r3': {'key': ['bus', 'unit'], 'missing': 'absent'},
                'variables.x': {'dims': ['bus', 'period', 'port', 'unit'], 'where': 'r1 AND r2 AND r3'},
            },
            id='three-that-share-a-member-over-the-members',
        ),
        pytest.param(
            {**_DEPOT, 'variables.x': {'dims': ['connection', 'assignment', 'depot']}},
            'connection_unit: {alias: unit}, connection: {over: [connection_unit, port]}, depot_unit: '
            '{alias: unit} and depot: {over: [bus, depot_unit]}',
            {
                'dimensions.connection_unit': {'alias': 'unit'},
                'dimensions.connection': {'over': ['connection_unit', 'port']},
                'dimensions.depot_unit': {'alias': 'unit'},
                'dimensions.depot': {'over': ['bus', 'depot_unit']},
                'variables.x': {'dims': ['connection', 'assignment', 'depot']},
            },
            id='three-that-share-a-member-each-with-an-alias',
        ),
        pytest.param(
            {
                'dimensions.from_unit': {'alias': 'unit'},
                'dimensions.assignment': {'over': ['from_unit', 'period']},
                'dimensions.connection': {'over': ['from_unit', 'port']},
                'variables.x': {'dims': ['connection', 'assignment']},
            },
            'connection_from_unit: {alias: unit}',
            {
                'dimensions.from_unit': {'alias': 'unit'},
                'dimensions.connection_from_unit': {'alias': 'unit'},
                'dimensions.assignment': {'over': ['from_unit', 'period']},
                'dimensions.connection': {'over': ['connection_from_unit', 'port']},
                'variables.x': {'dims': ['connection', 'assignment']},
            },
            id='a-shared-member-that-is-an-alias',
        ),
        pytest.param(
            {'variables.x': {'dims': ['connection', 'unit']}},
            "Drop 'unit' from dims:",
            {'variables.x': {'dims': ['connection']}},
            id='a-dimension-beside-its-member',
        ),
        pytest.param(
            {'dimensions.from_unit': {'alias': 'unit'}, 'dimensions.pair': {'over': ['from_unit', 'from_unit']}},
            'from_from_unit: {alias: unit}, and list both: over: [from_from_unit, from_unit]',
            {
                'dimensions.from_unit': {'alias': 'unit'},
                'dimensions.from_from_unit': {'alias': 'unit'},
                'dimensions.pair': {'over': ['from_from_unit', 'from_unit']},
            },
            id='an-alias-twice-under-over',
        ),
        pytest.param(
            {
                'dimensions.from_unit': {'alias': 'unit'},
                'dimensions.pair': {'over': {'src': 'from_unit', 'dst': 'from_unit'}},
            },
            'src: {alias: unit}, dst: {alias: unit}, and list the names: over: [src, dst]',
            {
                'dimensions.src': {'alias': 'unit'},
                'dimensions.dst': {'alias': 'unit'},
                'dimensions.pair': {'over': ['src', 'dst']},
            },
            id='a-mapping-through-an-alias',
        ),
        pytest.param(
            {'dimensions.pair': {'over': {'unit': 'unit', 'port': 'port'}}},
            'not a mapping. List the dimensions: over: [unit, port].',
            {'dimensions.pair': {'over': ['unit', 'port']}},
            id='a-mapping-that-repeats-no-dimension',
        ),
        pytest.param(
            {'dimensions.c2': {'alias': 'connection'}},
            "Declare 'c2' with the same members instead: c2: {over: [port, unit]}.",
            {'dimensions.c2': {'over': ['port', 'unit']}},
            id='an-alias-of-a-dimension-with-members',
        ),
        pytest.param(
            _curve('period'),
            "Step along an alias of it, curve_period: {alias: period}, and declare the breakpoints over 'curve_period'.",
            {**_curve('curve_period'), 'dimensions.curve_period': {'alias': 'period'}},
            id='a-curve-along-a-member',
        ),
        pytest.param(
            {'expressions.e': 'sum(f, over=snapshot, by=snap_unit[unit])'},
            "Sum 'connection' out of the operand first",
            {'expressions.e': 'sum(sum(f, over=connection), over=snapshot, by=snap_unit[unit])'},
            id='a-join-that-adds-a-member-beside-its-dimension',
        ),
        pytest.param(
            {'objective': {'sense': 'minimize', 'expression': 'sum(flow * on)'}},
            'Declare the operands over the members, with where: a relation keyed by [period, unit] and one keyed by '
            '[port, unit].',
            {
                **_JOINED,
                'variables.flow': {'dims': ['port', 'unit'], 'where': 'r2'},
                'variables.on': {'dims': ['period', 'unit'], 'where': 'r1'},
                'objective': {'sense': 'minimize', 'expression': 'sum(flow * on)'},
            },
            id='two-operands-that-share-a-member',
        ),
    ],
)
def test_the_rewrite_an_overlap_refusal_suggests_loads(refused, fragment, rewrite):
    """A refusal that suggests a rewrite holds it out as one that loads.

    Was: an alias of an alias, a `dims:` refused again over a third dimension,
    an `at` through a dimension the operand was still over, and a curve that
    loaded only to be refused at expansion.
    """
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(PAIRED, **refused))
    assert fragment in str(caught.value)
    to_spec(varied(PAIRED, **rewrite)).expand()


def test_an_alias_per_side_opts_into_every_pair():
    """The allocation of #1011: each side lists its own alias of `region`, so the two share no member."""
    allocation = {
        'dimensions': {
            'region': {},
            'plant': {},
            'site': {},
            'supply_region': {'alias': 'region'},
            'demand_region': {'alias': 'region'},
            'supply': {'over': ['supply_region', 'plant']},
            'demand': {'over': ['demand_region', 'site']},
        },
        'variables': {'x': {'dims': ['supply', 'demand']}},
    }
    assert to_spec(allocation).program.variables['x'].dims == ('demand', 'supply')
    assert [note.subject for note in advice(allocation) if note.kind == 'never-an-axis'] == [], (
        'x reaches each member, and each alias the dimension it aliases'
    )


def test_tuple_dimensions_without_a_shared_member_share_an_entry():
    patch = {
        'dimensions.scenario_year': {'over': ['region', 'period']},
        'variables.probe': {'dims': ['connection', 'scenario_year']},
    }
    assert to_spec(varied(MODEL, **patch)).program.variables['probe'].dims == ('connection', 'scenario_year')


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
            {'dimensions.trade.over': {'from_region': 'region', 'region': 'region'}},
            (
                'dimensions.trade.over',
                'takes a list of dimensions, not a mapping. Name each member that repeats a dimension as an alias '
                'of it under dimensions:, from_region: {alias: region}, and list the names: '
                'over: [from_region, region].',
            ),
            id='a-mapping-of-members',
        ),
        pytest.param(
            {'dimensions.pair': {'over': ['region', 'region']}},
            (
                "Dimension 'pair' lists 'region' twice under 'over:'. Declare an alias of it under dimensions:, "
                'from_region: {alias: region}, and list both: over: [from_region, region].',
            ),
            id='a-dimension-twice',
        ),
        pytest.param(
            {'relations.connection': {'key': 'connection', 'values': ['unit', 'port']}},
            (
                "Relation 'connection' collides with the relation that dimension 'connection' implies, read as "
                "connection[port], connection[unit]. Delete 'connection' under relations:.",
            ),
            id='the-implied-relation-written-out',
        ),
        pytest.param(
            {'relations.connection': {'key': ['unit', 'port']}},
            ("Relation 'connection' collides with the dimension of the same name. Rename one of them.",),
            id='another-relation-of-the-same-name',
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
                'sos.pick': {'variable': 'flow', 'along': 'connection', 'type': 2},
            },
            ("Sos 'pick': type: 2 along connection reads the order of 'connection'", "over ['port', 'unit']"),
            id='sos-of-type-2',
        ),
        pytest.param(
            {'relations.r': {'key': ['connection', 'unit']}, 'variables.flow.where': 'at(r, by=connection[unit])'},
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
            ("'region' is a member of 'trade'", 'Write sum(..., over=trade, by=trade[from_region]).'),
            id='over-names-a-member-beside-its-alias',
        ),
        pytest.param(
            _constraint('flow <= capacity', ['connection', 'snapshot']),
            (
                "an operand over ['unit'] meets one over 'connection'",
                'at(capacity, by=connection[unit])',
                'sum(flow, over=connection, by=connection[unit])',
            ),
            id='a-member-operand-meets-the-tuple',
        ),
        pytest.param(
            _constraint('flow <= capacity', ['unit', 'snapshot']),
            ("meets one over 'connection'", 'sum(flow, over=connection, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple-in-a-frame-over-the-member',
        ),
        pytest.param(
            {'objective': {'sense': 'minimize', 'expression': 'sum(flow * capacity)'}},
            (
                "The objective: an operand over ['unit'] meets one over 'connection'",
                'at(capacity, by=connection[unit])',
            ),
            id='a-member-operand-meets-the-tuple-in-a-product',
        ),
        pytest.param(
            _constraint('sum(flow * capacity, over=unit) <= 1', ['connection', 'snapshot']),
            ("meets one over 'connection'", 'at(capacity, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple-under-a-sum',
        ),
        pytest.param(
            {'assumptions.a': 'at(rating, by=connection[unit, port]) > capacity'},
            ("Assumption 'a': an operand over ['unit'] meets one over 'connection'",),
            id='a-member-operand-meets-the-tuple-in-an-assumption',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'variables.y': {'dims': ['connection']},
                'piecewise.curve': {
                    'dims': ['connection'],
                    'along': 'period',
                    'links': {'x': ['y', 'xs'], 'y': ['y', 'ys']},
                    'where': 'at(rating, by=connection[unit, port]) > capacity',
                },
            },
            ("piecewise 'curve' where: an operand over ['unit'] meets one over 'connection'",),
            id='a-member-operand-meets-the-tuple-in-a-piecewise-where-its-assumptions-repeat',
        ),
        pytest.param(
            {'variables.flow.where': 'at(rating, by=connection[unit, port]) > capacity'},
            ("Variable 'flow': an operand over ['unit'] meets one over 'connection'",),
            id='a-member-operand-meets-the-tuple-in-a-condition',
        ),
        pytest.param(
            {'expressions.e': {'dims': ['unit'], 'expression': '2 * capacity'}}
            | _constraint('flow <= e', ['connection', 'snapshot']),
            ('at(e, by=connection[unit])',),
            id='a-named-expression-over-a-member-meets-the-tuple',
        ),
        pytest.param(
            {'expressions.e': {'dims': ['connection', 'snapshot'], 'expression': 'capacity'}},
            ("the body carries dims ['unit']", 'at(capacity, by=connection[unit])'),
            id='a-named-expression-body-over-a-member',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['connection', 'snapshot'],
                    'cases': {'a': {'when': "connection[unit] == 'u'", 'expression': 'capacity'}},
                    'otherwise': 'flow',
                }
            },
            ("the value carries dims ['unit']", 'at(capacity, by=connection[unit])'),
            id='a-case-value-over-a-member',
        ),
        pytest.param(
            {'variables.u': {'dims': ['unit']}} | _constraint('sum(u, over=unit, by=connection[port]) >= 0', ['port']),
            ('sum(at(u, by=connection[unit]), over=connection, by=connection[port])',),
            id='over-names-a-member-of-an-operand-without-the-dimension',
        ),
        pytest.param(
            {'variables.u': {'dims': ['unit']}} | _constraint('u <= 1', ['connection']),
            ("carries dims ['unit'] that are not in its dims", 'at(u, by=connection[unit])'),
            id='a-constraint-over-a-member-its-dims-lack',
        ),
        pytest.param(
            {'variables.flow.bounds.upper': 'capacity'},
            ("parameter 'capacity' has dims ['unit'] outside", 'at(capacity, by=connection[unit])'),
            id='a-bound-over-a-member',
        ),
        pytest.param(
            {'variables.flow.where': 'capacity > 0'},
            ("reads dims ['unit'] outside the declared dims", 'at(capacity, by=connection[unit])'),
            id='a-where-over-a-member',
        ),
        pytest.param(
            {'variables.flow.where': "connection == 'a'"},
            ("'connection' lists its members", 'no label to compare', "connection[port] == 'a'"),
            id='a-label-comparison',
        ),
        pytest.param(
            {'variables.flow.where': 'connection'},
            ('a bare dimension name is true at every coordinate', 'where: "connection[port] == \'...\'"'),
            id='a-bare-dimension-with-members',
        ),
        pytest.param(
            {**SHARED_MEMBER, 'objective': {'sense': 'minimize', 'expression': 'sum(sent * on)'}},
            ("The objective: sent * on is over 'assignment' and 'connection', which share 'unit'.",),
            id='two-tuple-dimensions-that-share-a-member-meet-in-the-objective',
        ),
        pytest.param(
            {**SHARED_MEMBER, 'expressions.e': 'sent * on'},
            ("Named expression 'e': sent * on is over 'assignment' and 'connection', which share 'unit'.",),
            id='two-tuple-dimensions-that-share-a-member-meet-in-a-named-expression',
        ),
        pytest.param(
            {**SHARED_MEMBER, **_constraint('sum(sent * on, over=assignment) <= 1', ['connection'])},
            ("Constraint 'probe': sent * on is over 'assignment' and 'connection', which share 'unit'.",),
            id='two-tuple-dimensions-that-share-a-member-meet-under-a-sum',
        ),
        pytest.param(
            {
                'relations.snap_unit': {'key': 'snapshot', 'values': 'unit'},
                'expressions.e': 'sum(flow, over=snapshot, by=snap_unit[unit])',
            },
            (
                "Named expression 'e': sum(by=snap_unit[unit]) is over 'connection' and its member 'unit', so the "
                'expression would pair every connection with every unit.',
            ),
            id='a-join-adds-a-member-beside-the-tuple',
        ),
        pytest.param(
            {
                **SHARED_MEMBER,
                **_constraint(
                    'shift(flow, along=snapshot, offset=1, within=connection[unit]) >= 0', ['connection', 'snapshot']
                ),
            },
            ("shift(within=connection[unit]) reads the order of 'connection'", 'no order'),
            id='within-through-the-dimension',
        ),
        pytest.param(
            {'dimensions.c2': {'alias': 'connection'}},
            ("Dimension 'c2': alias: 'connection' is a dimension with members.",),
            id='an-alias-of-a-dimension-with-members',
        ),
        pytest.param(
            {
                **SHARED_MEMBER,
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'piecewise.curve': {
                    'dims': ['assignment'],
                    'along': 'period',
                    'links': {'x': ['on', 'xs'], 'y': ['on', 'ys']},
                },
            },
            (
                "piecewise 'curve': along: 'period' is a member of 'assignment' in dims:, so the curve would pair "
                'every assignment with every period. Step along an alias of it, curve_period: {alias: period}, and '
                "declare the breakpoints over 'curve_period'.",
            ),
            id='a-curve-along-a-member-of-its-dimension',
        ),
        pytest.param(
            {'dimensions.ring': {'over': ['loop', 'unit']}, 'dimensions.loop': {'over': ['ring', 'port']}},
            ("Dimension 'ring' lists 'loop'", "over: ['port', 'unit']"),
            id='two-dimensions-as-members-of-each-other',
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
    relation = r'upright("connection")' if fmt == 'typst' else r'\mathrm{connection}'
    assert relation not in typeset(spec, fmt), 'the implied relation has no row of its own beside the product'


def test_a_set_of_type_1_runs_along_a_dimension_with_members():
    """A type-1 set uses no order, so a dimension without one carries it."""
    sos = {'variables.flow.bounds.upper': 1, 'sos.pick': {'variable': 'flow', 'along': 'connection', 'type': 1}}
    assert to_spec(varied(MODEL, **sos)).sos['pick'].along == 'connection'


@pytest.mark.parametrize(
    ('variables', 'unused'),
    [
        pytest.param(
            {'x': {'dims': ['snapshot']}},
            ['connection', 'from_unit', 'link', 'port', 'unit'],
            id='nothing-is-over-the-dimension',
        ),
        pytest.param(
            {'x': {'dims': ['connection']}}, ['from_unit', 'link', 'snapshot'], id='an-entry-is-over-the-dimension'
        ),
        pytest.param({'x': {'dims': ['link']}}, ['connection', 'snapshot'], id='a-member-is-an-alias'),
    ],
)
def test_the_implied_relation_does_not_count_as_a_use(variables, unused):
    """The relation the entry implies has a column over the dimension and each member, so it counted as reaching them."""
    spec = {
        'dimensions': {
            'unit': {},
            'port': {},
            'snapshot': {},
            'connection': {'over': ['unit', 'port']},
            'from_unit': {'alias': 'unit'},
            'link': {'over': ['from_unit', 'port']},
        },
        'variables': variables,
    }
    notes = sorted(note.subject for note in advice(spec) if note.kind == 'never-an-axis')
    assert notes == unused, 'an entry over the dimension reaches its members, and the implied relation reaches nothing'


def test_fragments_that_agree_on_the_members_merge():
    other = {
        'dimensions': {'port': {}, 'unit': {}, 'connection': {'over': ['port', 'unit']}},
        'variables': {'loss': {'dims': ['connection']}},
    }
    assert merge([FRAGMENT, other]).program.dimensions['connection'].over == ('port', 'unit')


@pytest.mark.parametrize(
    'connection',
    [
        pytest.param({'over': ['unit']}, id='other-members'),
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
    with pytest.raises(LanguageError, match=r"declares the dimension 'connection'"):
        override(FRAGMENT, [{'dimensions': {'connection': {'over': ['unit']}}}])


def test_rename_reaches_the_members_and_the_implied_relation():
    renamed = rename(MODEL, {'unit': 'plant', 'connection': 'link', 'region': 'zone'})
    assert renamed.dimensions['link'].over == ('plant', 'port')
    assert renamed.dimensions['trade'].over == ('from_region', 'zone'), 'an alias member keeps its name'
    assert renamed.constraints['limit'].expression == 'flow <= at(capacity, by=link[plant])'
    assert rename(renamed, {'plant': 'unit', 'link': 'connection', 'zone': 'region'}) == to_spec(MODEL)


@pytest.mark.parametrize('canonical', [False, True])
def test_a_spec_with_members_is_written_and_read_back(canonical):
    spec = to_spec(MODEL)
    assert to_spec(spec.to_yaml(canonical=canonical)).program == spec.program
