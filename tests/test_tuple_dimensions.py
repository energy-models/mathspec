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
from mathspec._dimensions import sorted_dims
from mathspec._typesetting import FORMATS, typeset
from mathspec.errors import DimensionError, LanguageError, SchemaError
from mathspec.program import Join, JoinedCondition, Relation, RelationComparison, RelationPairComparison, Sum
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


_SPREAD_EACH = (
    'and spread each operand onto them: at(<operand>, by=assignment[period, unit]) and at(<operand>, '
    'by=connection[port, unit])'
)
_KEYED = 'with where: a relation keyed by [period, unit] and one keyed by [port, unit]'


@pytest.mark.parametrize(
    ('kind', 'rewrite'),
    [
        pytest.param('constraint', _SPREAD_EACH, id='constraint'),
        pytest.param('named-expression', _SPREAD_EACH, id='named-expression'),
        pytest.param('case', _SPREAD_EACH, id='case'),
        pytest.param('parameter', _KEYED, id='parameter'),
        pytest.param('variable', _KEYED, id='variable'),
        pytest.param('piecewise', _KEYED, id='piecewise'),
        pytest.param('given-variable', _KEYED, id='given-variable'),
    ],
)
def test_an_overlap_refusal_suggests_a_spread_only_to_an_entry_with_an_expression(kind, rewrite):
    """An entry without an expression has no operand to spread, so its join over the members is a `where:`.

    Was: a variable over two dimensions that share a member was told to
    spread each operand, and the flat `dims:` it was given lost the join.
    """
    message = _refusal(**SHARED_MEMBER, **_entry(kind, ['connection', 'assignment']))
    assert f'Write the entry over the members, dims: [period, port, unit], {rewrite}.' in message


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

_DEPOT = {'dimensions.depot': {'over': ['unit', 'bus']}, 'variables.stock': {'dims': ['depot']}}


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
            _constraint('flow + on <= 1', ['connection', 'assignment']),
            'dims: [period, port, unit], and spread each operand onto them: at(<operand>, by=assignment[period, unit]) '
            'and at(<operand>, by=connection[port, unit])',
            _constraint(
                'at(flow, by=connection[port, unit]) + at(on, by=assignment[period, unit]) <= 1',
                ['period', 'port', 'unit'],
            ),
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
            {'variables.x': {'dims': ['connection', 'assignment']}},
            _KEYED,
            {
                'relations.plugged': {'key': ['port', 'unit'], 'missing': 'absent'},
                'relations.busy': {'key': ['period', 'unit'], 'missing': 'absent'},
                'variables.x': {'dims': ['period', 'port', 'unit'], 'where': 'plugged AND busy'},
            },
            id='a-variable-over-the-members-with-a-relation-for-each',
        ),
        pytest.param(
            {'variables.x': {'dims': ['connection', 'assignment', 'unit']}},
            "If every pair is meant, leave 'unit' out, and let connection list its own alias",
            {
                'dimensions.connection_unit': {'alias': 'unit'},
                'dimensions.connection': {'over': ['connection_unit', 'port']},
                'variables.x': {'dims': ['connection', 'assignment']},
            },
            id='an-alias-of-the-shared-member-beside-the-member',
        ),
        pytest.param(
            {**_DEPOT, **_constraint('flow + on + stock <= 1', ['connection', 'assignment', 'depot'])},
            'dims: [bus, period, port, unit], and spread each operand onto them: at(<operand>, '
            'by=assignment[period, unit]), at(<operand>, by=connection[port, unit]) and at(<operand>, '
            'by=depot[bus, unit])',
            {
                **_DEPOT,
                **_constraint(
                    'at(flow, by=connection[port, unit]) + at(on, by=assignment[period, unit]) '
                    '+ at(stock, by=depot[bus, unit]) <= 1',
                    ['bus', 'period', 'port', 'unit'],
                ),
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
            'Spread each operand onto its members: at(on, by=assignment[period, unit]) and '
            'at(flow, by=connection[port, unit]).',
            {
                'objective': {
                    'sense': 'minimize',
                    'expression': 'sum(at(flow, by=connection[port, unit]) * at(on, by=assignment[period, unit]))',
                }
            },
            id='two-operands-that-share-a-member',
        ),
        pytest.param(
            _constraint('flow >= 0', ['unit', 'port']),
            'Spread the operand onto its members: at(flow, by=connection[port, unit]).',
            _constraint('at(flow, by=connection[port, unit]) >= 0', ['unit', 'port']),
            id='an-operand-over-the-dimension-in-an-entry-over-the-members',
        ),
        pytest.param(
            {'variables.w': {'dims': ['unit', 'port']}, **_constraint('w <= flow', ['unit', 'port'])},
            'or spread flow onto the members: at(flow, by=connection[port, unit]).',
            {
                'variables.w': {'dims': ['unit', 'port']},
                **_constraint('w <= at(flow, by=connection[port, unit])', ['unit', 'port']),
            },
            id='an-operand-over-the-dimension-meets-one-over-the-members',
        ),
        pytest.param(
            {
                'parameters.open': {'dims': ['connection'], 'dtype': 'bool'},
                'variables.w': {'dims': ['unit', 'port'], 'where': 'open'},
            },
            'Spread the operand onto its members: at(open, by=connection[port, unit]).',
            {
                'parameters.open': {'dims': ['connection'], 'dtype': 'bool'},
                'variables.w': {'dims': ['unit', 'port'], 'where': 'at(open, by=connection[port, unit])'},
            },
            id='a-where-over-the-dimension-on-an-entry-over-the-members',
        ),
        pytest.param(
            _constraint('at(flow, by=connection[unit]) >= 0', ['unit', 'port']),
            'List every member to spread the operand onto them: at(flow, by=connection[port, unit]).',
            _constraint('at(flow, by=connection[port, unit]) >= 0', ['unit', 'port']),
            id='a-spread-that-leaves-a-member-out',
        ),
        pytest.param(
            _constraint('at(flow, by=connection[unit]) >= 0', ['unit']),
            "To add up over ['port'], write sum(flow, over=connection, by=connection[unit]).",
            _constraint('sum(flow, over=connection, by=connection[unit]) >= 0', ['unit']),
            id='a-spread-that-leaves-a-member-out-summed',
        ),
    ],
)
def test_the_rewrite_a_refusal_suggests_loads(refused, fragment, rewrite):
    """A refusal that suggests a rewrite holds it out as one that loads.

    Was: an alias of an alias, a `dims:` refused again over a third dimension,
    an `at` through a dimension the operand was still over, a curve that
    loaded only to be refused at expansion, and a variable told to spread
    operands it does not have.
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


#: Two dimensions with members that share `unit`, and entries over each and over the members.
SPREAD: dict[str, Any] = varied(
    MODEL,
    **{
        'dimensions.assignment': {'over': ['unit', 'period']},
        'dimensions.side': {'alias': 'port'},
        'dimensions.link': {'over': ['unit', 'side']},
        'parameters.open': {'dims': ['connection'], 'dtype': 'bool'},
        'parameters.limit': {'dims': ['connection']},
        'variables.y': {'dims': ['assignment']},
        'variables.x': {'dims': ['connection', 'period']},
        'variables.w': {'dims': ['unit', 'port', 'snapshot']},
        'variables.on_link': {'dims': ['link']},
    },
)


def _spread_refusal(**patch: Any) -> str:
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(SPREAD, **patch))
    return str(caught.value)


@pytest.mark.parametrize(
    'by',
    [pytest.param('connection[unit, port]', id='as-declared'), pytest.param('connection[port, unit]', id='swapped')],
)
def test_at_spreads_an_operand_over_the_dimension_onto_its_members(by):
    """Rule 6 of #1011: `at` by every member of the dimension its operand is over was refused as a lookup that joins on what the operand lacks."""
    patch = _constraint(f'w <= at(flow, by={by})', ['unit', 'port', 'snapshot'])
    spread = to_spec(varied(SPREAD, **patch)).program.constraints['probe'].rhs
    assert isinstance(spread, Join)
    assert spread.dims == ('port', 'snapshot', 'unit'), 'the dimension goes and its members arrive'
    assert spread.columns.joined == ('connection',), 'the operand is matched on the tuple'
    assert spread.columns.grouped == ('port', 'unit'), 'every member arrives, sorted by role'
    assert spread.columns.axes == (), 'the members identify one tuple, so the join opens no axis to sum'


def test_a_sum_by_every_member_still_adds_up():
    """The sum is 0 where no tuple exists and the spread is absent there, so the two stay two programs."""
    patch = _constraint('w <= sum(flow, over=connection, by=connection[unit, port])', ['unit', 'port', 'snapshot'])
    summed = to_spec(varied(SPREAD, **patch)).program.constraints['probe'].rhs
    assert isinstance(summed, Sum)
    assert isinstance(summed.operand, Join)
    assert len(summed.operand.columns.axes) == 1, 'the sum closes the axis over the dimension'


@pytest.mark.parametrize(
    ('patch', 'spreads'),
    [
        pytest.param(
            _constraint('w <= at(flow, by=connection[unit, port])', ['unit', 'port', 'snapshot']),
            {'connection'},
            id='a-row',
        ),
        pytest.param(
            {'variables.w.bounds.upper': 'at(limit, by=connection[unit, port])'}, {'connection'}, id='a-bound'
        ),
        pytest.param(
            _constraint('w <= sum(flow, over=connection, by=connection[unit, port])', ['unit', 'port', 'snapshot']),
            set(),
            id='a-sum-by-every-member',
        ),
    ],
)
def test_the_footprint_names_each_dimension_a_row_spreads(patch, spreads):
    """A spread is a `Join` in `footprint.kinds`, as a sum by every member is, so the kinds alone hid it from an engine."""
    footprint = to_spec(varied(SPREAD, **patch)).program.footprint
    assert footprint.spreads == spreads, 'the dimensions read at the tuples of their members'


def _curve(x: str, x_dims: list[str], by: str | None = None) -> dict[str, Any]:
    """A curve over `connection` whose link `x` reads *x* over `a`, which is over *x_dims*, walking *by* where given."""
    link = {'expression': x, 'values': 'xs'} | ({'by': by} if by else {})
    return {
        'parameters.xs': {'dims': ['period']},
        'parameters.ys': {'dims': ['period']},
        'variables.a': {'dims': x_dims},
        'variables.b': {'dims': ['connection']},
        'piecewise.curve': {'dims': ['connection'], 'along': 'period', 'links': {'x': link, 'y': ['b', 'ys']}},
    }


@pytest.mark.parametrize(
    ('expression', 'frame'),
    [
        pytest.param(
            'x <= at(at(y, by=assignment[unit, period]), by=connection[unit])',
            ['connection', 'period'],
            id='a-left-join-of-two-dimensions-that-share-a-member',
        ),
        pytest.param(
            'sum(at(flow, by=connection[unit, port]), over=port) >= 0',
            ['unit', 'snapshot'],
            id='a-sum-after-the-spread',
        ),
        pytest.param(
            "shift(at(flow, by=connection[unit, port]), along=snapshot, offset=1, edge='wrap') <= w",
            ['unit', 'port', 'snapshot'],
            id='a-shift-along-another-dimension',
        ),
        pytest.param(
            'y >= at(shift(at(y, by=assignment[unit, period]), along=period, offset=1), by=assignment[unit, period])',
            ['assignment'],
            id='a-shift-along-a-member-read-back-at-each-tuple',
        ),
    ],
)
def test_a_spread_loads_in_a_constraint(expression, frame):
    """Rule 6 of #1011: each of these was refused, as an `at` that joins on a member the operand lacks."""
    row = to_spec(varied(SPREAD, **_constraint(expression, frame))).program.constraints['probe']
    assert sorted_dims(row.lhs.dims, row.rhs.dims) == tuple(sorted(frame)), 'the row is over its dims: and no more'


@pytest.mark.parametrize(
    ('patch', 'read', 'dims'),
    [
        pytest.param(
            {'expressions.e': {'dims': ['side', 'unit'], 'expression': 'at(on_link, by=link[unit, side])'}},
            lambda program: program.expressions['e'].expression,
            ('side', 'unit'),
            id='an-alias-member-arrives-as-the-alias',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['from_region', 'region'],
                    'expression': 'at(shipped, by=trade[from_region, region])',
                }
            },
            lambda program: program.expressions['e'].expression,
            ('from_region', 'region'),
            id='one-dimension-twice-through-an-alias',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['unit', 'port', 'snapshot'],
                    'expression': 'at(flow, by=connection[unit, port])',
                }
            },
            lambda program: program.expressions['e'].expression,
            ('port', 'snapshot', 'unit'),
            id='a-named-expression',
        ),
        pytest.param(
            {
                'expressions.e': {'dims': ['connection', 'snapshot'], 'expression': '2 * flow'},
                'expressions.f': {
                    'dims': ['unit', 'port', 'snapshot'],
                    'expression': 'at(e, by=connection[unit, port])',
                },
            },
            lambda program: program.expressions['f'].expression,
            ('port', 'snapshot', 'unit'),
            id='a-named-expression-as-the-operand',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['unit', 'port', 'snapshot'],
                    'cases': {'open': {'when': 'at(open, by=connection[unit, port])', 'expression': 'w'}},
                    'otherwise': '0',
                }
            },
            lambda program: program.expressions['e'].expression,
            ('port', 'snapshot', 'unit'),
            id='one-case-and-otherwise',
        ),
        pytest.param(
            {'variables.w.bounds.upper': 'at(limit, by=connection[unit, port])'},
            lambda program: program.variables['w'].upper,
            ('port', 'unit'),
            id='a-bound',
        ),
        pytest.param(
            {'variables.w.where': 'at(open, by=connection[unit, port])'},
            lambda program: program.variables['w'].where,
            ('port', 'unit'),
            id='a-condition',
        ),
        pytest.param(
            {'variables.w.where': 'at(limit > 0, by=connection[port, unit])'},
            lambda program: program.variables['w'].where,
            ('port', 'unit'),
            id='a-comparison-in-a-condition',
        ),
        pytest.param(
            _curve('at(a, by=connection[unit, port])', ['unit', 'port']),
            lambda program: program.piecewise['curve'].links[0].expression,
            ('connection',),
            id='the-rewrite-of-a-piecewise-link-that-names-every-member',
        ),
        pytest.param(
            _curve('at(a, by=connection[unit])', ['unit']),
            lambda program: program.piecewise['curve'].links[0].expression,
            ('connection',),
            id='the-rewrite-of-a-piecewise-link-that-names-one-member',
        ),
    ],
)
def test_a_spread_loads_in_an_entry_that_is_no_constraint(patch, read, dims):
    """Rule 6 of #1011: a spread reads as a lookup does in every entry, and the rewrite a refused `by:` suggests loads."""
    assert read(to_spec(varied(SPREAD, **patch)).program).dims == dims, 'the entry is over the dims the reads bring'


@pytest.mark.parametrize(
    ('patch', 'error', 'fragments'),
    [
        pytest.param(
            _constraint('at(flow, by=connection[unit]) >= 0', ['unit', 'snapshot']),
            DimensionError,
            (
                "at(by=connection[unit]) lists ['unit'] of the members ['port', 'unit'] of 'connection'",
                'at(flow, by=connection[port, unit])',
                'sum(flow, over=connection, by=connection[unit])',
            ),
            id='a-partial-list',
        ),
        pytest.param(
            {'variables.w.where': 'at(open, by=connection[port])'},
            DimensionError,
            (
                "Variable 'w': at(by=connection[port]) lists ['port'] of the members ['port', 'unit']",
                'at(..., by=connection[port, unit])',
            ),
            id='a-partial-list-in-a-condition',
        ),
        pytest.param(
            {'relations.r': {'key': ['connection', 'unit']}, 'variables.w.where': 'at(r, by=connection[unit, port])'},
            DimensionError,
            ("carries both 'connection' and its member ['unit']", "Sum ['unit'] out of the operand first"),
            id='an-operand-with-the-dimension-and-a-member',
        ),
        pytest.param(
            _constraint('w <= flow', ['unit', 'port', 'snapshot']),
            DimensionError,
            (
                "an operand over ['port', 'unit'] meets one over 'connection'",
                'at(w, by=connection[port, unit])',
                'spread flow onto the members: at(flow, by=connection[port, unit])',
            ),
            id='an-operand-over-every-member-meets-the-dimension',
        ),
        pytest.param(
            _constraint('flow >= 0', ['unit', 'port', 'snapshot']),
            DimensionError,
            ("carries dims ['connection'] that are not in its dims", 'at(flow, by=connection[port, unit])'),
            id='a-constraint-over-the-members-reads-the-dimension',
        ),
        pytest.param(
            {'expressions.e': {'dims': ['unit', 'port', 'snapshot'], 'expression': '2 * flow'}},
            DimensionError,
            ("the body carries dims ['connection']", 'at(flow, by=connection[port, unit])'),
            id='a-named-expression-over-the-members-reads-the-dimension',
        ),
        pytest.param(
            {'variables.w.bounds.upper': 'limit'},
            DimensionError,
            ("parameter 'limit' has dims ['connection'] outside", 'at(limit, by=connection[port, unit])'),
            id='a-bound-over-the-dimension',
        ),
        pytest.param(
            {'variables.w.where': 'open'},
            DimensionError,
            ("reads dims ['connection'] outside the declared dims", 'at(open, by=connection[port, unit])'),
            id='a-where-over-the-dimension',
        ),
        pytest.param(
            _curve('a', ['unit', 'port'], 'connection[unit, port]'),
            DimensionError,
            (
                "piecewise 'curve' link 'x': by: connection[unit, port] names members of 'connection'",
                'at(<expression>, by=connection[unit, port])',
            ),
            id='a-piecewise-link-that-walks-every-member',
        ),
        pytest.param(
            _curve('a', ['unit'], 'connection[unit]'),
            DimensionError,
            (
                "piecewise 'curve' link 'x': by: connection[unit] names members of 'connection'",
                'at(<expression>, by=connection[unit])',
            ),
            id='a-piecewise-link-that-walks-one-member',
        ),
        pytest.param(
            _curve('a', ['connection'], 'connection[connection]'),
            SchemaError,
            ("at(by=connection[connection]) names ['connection'], a key column of 'connection'",),
            id='a-piecewise-link-that-walks-the-key',
        ),
        pytest.param(
            _constraint('at(flow, by=connection_bus[bus]) >= 0', ['bus', 'snapshot']),
            DimensionError,
            ("at(by=connection_bus[bus]) joins on ['bus']", 'use sum() instead'),
            id='a-relation-keyed-by-the-dimension-is-no-spread',
        ),
        pytest.param(
            _constraint(
                "shift(at(flow, by=connection[unit, port]), along=connection, offset=1, edge='wrap') >= 0",
                ['unit', 'port', 'snapshot'],
            ),
            SchemaError,
            ("shift(along=connection) reads the order of 'connection'",),
            id='a-shift-along-the-dimension',
        ),
    ],
)
def test_a_spread_that_does_not_load_is_refused_with_the_rewrite(patch, error, fragments):
    """A refusal names the rewrite, and its class says whether a dim rule refused it."""
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(SPREAD, **patch))
    assert type(caught.value) is error, f'{error.__name__}, the class a dim rule or the language raises here'
    for fragment in fragments:
        assert fragment in str(caught.value), f'the refusal says {fragment!r}'


def _stray(**entry: Any) -> dict[str, Any]:
    """*entry* beside `on` and `lim`, over `connection` and `snapshot`, and `v`, a variable over the members."""
    return {
        'parameters.on': {'dims': ['connection', 'snapshot'], 'dtype': 'bool'},
        'parameters.lim': {'dims': ['connection', 'snapshot']},
        'variables.v': {'dims': ['unit', 'port']},
        **entry,
    }


@pytest.mark.parametrize(
    ('patch', 'message'),
    [
        pytest.param(
            _stray(**_constraint('flow >= 0', ['unit', 'port'])),
            "Constraint 'probe': the expression carries dims ['connection', 'snapshot'] that are not in its dims: "
            "['port', 'unit']. Add them to dims:, or sum them out.",
            id='a-constraint',
        ),
        pytest.param(
            _stray(**{'expressions.e': {'dims': ['unit', 'port'], 'expression': '2 * flow'}}),
            "Named expression 'e': the body carries dims ['connection', 'snapshot'] outside the dims: ['port', "
            "'unit']. Add them to dims:, or take them out of the body.",
            id='a-named-expression',
        ),
        pytest.param(
            _stray(**{'variables.v.bounds.upper': 'lim'}),
            "Variable 'v': bounds.upper parameter 'lim' has dims ['connection', 'snapshot'] outside the variable's "
            "dims ['port', 'unit']. Declare 'lim' over the variable's dims.",
            id='a-bound',
        ),
        pytest.param(
            _stray(**{'variables.v.where': 'on'}),
            "Variable 'v': where-parameter 'on' reads dims ['connection', 'snapshot'] outside the declared dims "
            "['port', 'unit']. Add them to dims:, or test a name over the declared dims.",
            id='a-where',
        ),
    ],
)
def test_no_spread_is_suggested_where_a_dimension_would_stay_outside(patch, message):
    """A spread brings the members of one dimension, so it is the rewrite only where that dimension is all that is outside.

    Was: the message suggested `at(flow, by=connection[port, unit])`, which
    the loader refused again for `snapshot`.
    """
    with pytest.raises(DimensionError) as caught:
        to_spec(varied(SPREAD, **patch))
    assert str(caught.value) == message


_CASES = {'dims': ['unit', 'port', 'snapshot'], 'otherwise': '0'}


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param(
            {
                'expressions.e': {
                    **_CASES,
                    'cases': {
                        'open': {'when': 'at(open, by=connection[unit, port])', 'expression': 'w'},
                        'shut': {'when': 'not at(open, by=connection[unit, port])', 'expression': '2 * w'},
                    },
                }
            },
            id='a-spread-and-its-negation',
        ),
        pytest.param(
            {
                'conditions.is_open': {'condition': 'at(open, by=connection[port, unit])'},
                'expressions.e': {
                    **_CASES,
                    'cases': {
                        'open': {'when': 'at(open, by=connection[unit, port])', 'expression': 'w'},
                        'shut': {'when': 'not is_open', 'expression': '2 * w'},
                    },
                },
            },
            id='the-members-in-another-order-through-a-named-condition',
        ),
    ],
)
def test_cases_split_by_a_spread_condition_load(patch):
    """A spread reaches one row of the dimension, so a condition and its negation claim no tuple together.

    Was: the pair was refused as one only the data decides, though the same
    split through a lookup loads.
    """
    to_spec(varied(SPREAD, **patch))


def test_cases_that_both_admit_a_spread_condition_are_refused_with_the_tuple():
    cases = {
        'open': {'when': 'at(open, by=connection[unit, port])', 'expression': 'w'},
        'wide': {'when': 'w_on', 'expression': '2 * w'},
    }
    patch = {
        'parameters.w_on': {'dims': ['unit', 'port'], 'dtype': 'bool'},
        'expressions.e': {**_CASES, 'cases': cases},
    }
    with pytest.raises(SchemaError) as caught:
        to_spec(varied(SPREAD, **patch))
    assert (
        "cases 'open' and 'wide' both claim the value where open through connection[port, unit] is true, w_on is true."
        in str(caught.value)
    )


@pytest.mark.parametrize('fmt', FORMATS)
def test_a_spread_prints_the_tuple_as_the_index(fmt):
    spec = varied(
        FRAGMENT,
        **{
            'parameters.open': {'dims': ['connection'], 'dtype': 'bool'},
            'variables.w': {'dims': ['unit', 'port'], 'where': 'at(open, by=connection[unit, port])'},
            'constraints.probe': {'dims': ['unit', 'port'], 'expression': 'w <= at(flow, by=connection[unit, port])'},
        },
    )
    printed = typeset(to_spec(spec), fmt)
    index = FORMATS[fmt].parenthesise(FORMATS[fmt].joined(['p', 'u'], ''))
    for name in ('flow', 'open'):
        read = FORMATS[fmt].subscript(
            FORMATS[fmt].upright(name) if name == 'open' else FORMATS[fmt].italic(name), [index]
        )
        assert read in printed, f'{fmt} reads {name} at the tuple of its members, in the order the legend lists them'


@pytest.mark.parametrize('fmt', FORMATS)
def test_a_member_read_inside_a_spread_prints_as_the_index_of_the_member(fmt):
    """A gather inside a spread printed `capacity_{connection.unit((p, u))}`, which is `capacity_u`."""
    spec = varied(
        FRAGMENT,
        **{
            'parameters.capacity': {'dims': ['unit']},
            'variables.w': {'dims': ['unit', 'port']},
            'constraints.probe': {
                'dims': ['unit', 'port'],
                'expression': 'w <= at(flow * at(capacity, by=connection[unit]), by=connection[unit, port])',
            },
        },
    )
    printed = typeset(to_spec(spec), fmt)
    out = FORMATS[fmt]
    assert out.subscript(out.upright('capacity'), ['u']) in printed, f'{fmt} reads capacity at the unit of the tuple'


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
            {'dimensions.pair': {'over': ['nope', 'nope']}},
            (
                "Dimension 'pair' references undeclared dimension 'nope'.",
                "Dimension 'pair' lists 'nope' twice under 'over:'. Declare an alias of it under dimensions:, "
                'from_nope: {alias: nope}, and list both: over: [from_nope, nope].',
            ),
            id='an-undeclared-dimension-twice',
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


@pytest.mark.parametrize(
    ('expression', 'dims'),
    [
        pytest.param('shipped >= 0', ['region'], id='two-members-over-one-dimension'),
        pytest.param('flow >= 0', ['unit', 'snapshot'], id='a-member-the-dims-lack'),
    ],
)
def test_no_spread_is_advised_where_it_would_be_refused(expression, dims):
    """The refusal of a stray dimension suggests `at` by every member only where that call loads in the entry."""
    message = _refusal(**_constraint(expression, dims))
    assert 'Add them to dims:, or sum them out' in message
    assert 'at(' not in message, 'the spread needs every member in dims:, each over a dimension of its own'


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
