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
from mathspec.errors import LanguageError
from mathspec.program import Join, JoinedCondition, Relation, RelationComparison, RelationPairComparison, Sum
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
        pytest.param('both <= capacity', ['connection', 'unit'], id='an-entry-over-the-dimension-and-a-member'),
    ],
)
def test_a_member_is_read_through_the_implied_relation(expression, dims):
    constraint = to_spec(varied(MODEL, **_constraint(expression, dims))).program.constraints['probe']
    assert sorted({*constraint.lhs.dims, *constraint.rhs.dims}) == sorted(dims)


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param(_constraint('flow <= capacity', ['connection', 'unit', 'snapshot']), id='a-constraint'),
        pytest.param(
            {'expressions.e': {'dims': ['connection', 'unit', 'snapshot'], 'expression': 'flow * capacity'}},
            id='a-named-expression',
        ),
        pytest.param(
            _constraint('sum(flow * capacity, over=snapshot) <= both', ['connection', 'unit']),
            id='under-a-sum-that-keeps-both',
        ),
        pytest.param({'variables.both.where': 'at(rating, by=connection[unit, port]) > capacity'}, id='a-condition'),
        pytest.param(
            {
                'constraints.probe': {
                    'dims': ['connection', 'unit'],
                    'expression': 'both <= 1',
                    'where': 'at(rating, by=connection[unit, port]) > capacity',
                }
            },
            id='a-constraint-where',
        ),
        pytest.param(
            {
                'parameters.p': {
                    'dims': ['connection', 'unit'],
                    'where': 'at(rating, by=connection[unit, port]) > capacity',
                }
            },
            id='a-parameter-where',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['connection', 'unit', 'snapshot'],
                    'cases': {
                        'a': {
                            'when': 'at(rating, by=connection[unit, port]) > capacity',
                            'expression': 'flow * capacity',
                        }
                    },
                    'otherwise': 'flow * capacity',
                }
            },
            id='a-case',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'variables.w': {'dims': ['connection']},
                'variables.v': {'dims': ['unit']},
                'variables.y': {'dims': ['connection', 'unit']},
                'piecewise.curve': {
                    'dims': ['connection', 'unit'],
                    'along': 'period',
                    'links': {'x': ['w + v', 'xs'], 'y': ['y', 'ys']},
                },
            },
            id='a-piecewise-link',
        ),
    ],
)
def test_a_frame_over_the_dimension_and_its_member_takes_the_cross_product(patch):
    """Rule 11 of #1011: where `dims:` declares both, a member operand meets the dimension, and the entry loads."""
    to_spec(varied(MODEL, **patch))


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


@pytest.mark.parametrize(
    ('where', 'dims', 'pair'),
    [
        pytest.param(
            'connection[unit] == assignment[unit]',
            ['connection', 'assignment'],
            ('connection', 'unit', 'assignment', 'unit', '==', ('assignment', 'connection')),
            id='an-inner-join-on-the-shared-member',
        ),
        pytest.param(
            'assignment[unit] != connection[unit]',
            ['connection', 'assignment'],
            ('assignment', 'unit', 'connection', 'unit', '!=', ('assignment', 'connection')),
            id='an-inner-join-written-the-other-way-round',
        ),
        pytest.param(
            'connection[unit] == backup[spare]',
            ['connection'],
            ('connection', 'unit', 'backup', 'spare', '==', ('connection',)),
            id='a-relation-keyed-by-the-dimension',
        ),
    ],
)
def test_a_member_column_is_compared_with_another_relation_column(where, dims, pair):
    """Rule 2 of #1011: the implied relation is a relation in a comparison of two columns, as on main.

    Was: a side named after a tuple dimension was read as the dimension, so
    `connection[unit] == assignment[unit]` was refused as a comparison of two
    dimensions, and `connection[unit] == backup[spare]` as one against a relation.
    """
    expression = ' + '.join({'connection': 'sent', 'assignment': 'on'}[d] for d in dims) + ' <= 1'
    constraint = {'constraints.probe': {'dims': dims, 'expression': expression, 'where': where}}
    spec = to_spec(varied(MODEL, **SHARED_MEMBER, **constraint))
    assert spec.program.constraints['probe'].where.atoms == (RelationPairComparison(*pair),)


@pytest.mark.parametrize(
    ('cases', 'fragment'),
    [
        pytest.param(
            {'joined': 'connection[unit] == assignment[unit]', 'apart': 'connection[unit] != assignment[unit]'},
            None,
            id='the-join-and-its-complement',
        ),
        pytest.param(
            {'joined': 'connection[unit] == assignment[unit]', 'gas': "connection[unit] == 'gas'"},
            'assignment[unit] vs connection[unit] is equal',
            id='the-join-and-a-label',
        ),
    ],
)
def test_a_case_tests_the_inner_join(cases, fragment):
    """The exclusivity check reads the join as one fact per pair of tuples: true, false, or a row missing."""
    entry = {
        'dims': ['connection', 'assignment'],
        'cases': {name: {'when': when, 'expression': 'sent + on'} for name, when in cases.items()},
        'otherwise': 0,
    }
    patch = {**SHARED_MEMBER, 'expressions.e': entry}
    if fragment is None:
        to_spec(varied(MODEL, **patch))
    else:
        assert fragment in _refusal(**patch)


@pytest.mark.parametrize('fmt', FORMATS)
def test_the_inner_join_is_typeset(fmt):
    where = 'connection[unit] == assignment[unit]'
    constraint = {'dims': ['connection', 'assignment'], 'expression': 'sent + on <= 1', 'where': where}
    spec = to_spec(varied(MODEL, **SHARED_MEMBER, **{'constraints.probe': constraint}))
    text = typeset(spec, fmt)
    assert 'unit' in text.split('probe', 1)[1], f'{fmt} prints the shared member on both sides'


JOIN = 'connection[unit] == assignment[unit]'
ADVISED_JOIN = 'add assignment[unit] == connection[unit] to where:'


def _cross_products(subject: str, **patch: Any) -> list[str]:
    """The cross-product advice on *subject*, in the model with `assignment` beside `connection`, patched with *patch*."""
    notes = advice(varied(MODEL, **SHARED_MEMBER, **patch))
    return [note.text for note in notes if note.kind == 'cross-product' and note.subject == subject]


def _over_both(where: str | None = None) -> dict[str, Any]:
    entry = {'dims': ['connection', 'assignment'], 'expression': 'sent + on <= 1'}
    return {'constraints.probe': entry if where is None else {**entry, 'where': where}}


@pytest.mark.parametrize(
    ('subject', 'patch', 'fragments'),
    [
        pytest.param(
            'probe',
            _over_both(),
            [
                "Constraint 'probe': dims: lists 'assignment' and 'connection', which share the member 'unit', "
                'so the entry is their cross product',
                ADVISED_JOIN,
            ],
            id='two-dimensions-share-a-member',
        ),
        pytest.param('probe', _over_both(JOIN.replace('==', '!=')), [ADVISED_JOIN], id='a-where-that-keeps-others'),
        pytest.param(
            'probe', _over_both(f"{JOIN} OR connection[port] == 'p1'"), [ADVISED_JOIN], id='the-join-in-an-or'
        ),
        pytest.param(
            'pair',
            {'variables.pair': {'dims': ['connection', 'assignment']}},
            ["Variable 'pair': dims: lists 'assignment' and 'connection'", ADVISED_JOIN],
            id='a-variable',
        ),
        pytest.param(
            'pair',
            {
                'dimensions.plug': {'over': ['unit', 'port', 'period']},
                'variables.pair': {'dims': ['connection', 'plug']},
            },
            [
                "which share the members 'port' and 'unit'",
                'add connection[port] == plug[port] AND connection[unit] == plug[unit] to where:',
            ],
            id='two-shared-members',
        ),
        pytest.param(
            'pair',
            {
                'dimensions.plug': {'over': ['unit', 'port', 'period']},
                'variables.pair': {'dims': ['connection', 'plug'], 'where': 'connection[unit] == plug[unit]'},
            },
            ["which share the members 'port' and 'unit'", 'add connection[port] == plug[port] to where:'],
            id='one-of-two-shared-members-joined',
        ),
        pytest.param(
            'probe',
            _constraint('flow <= capacity', ['connection', 'unit', 'snapshot']),
            [
                "Constraint 'probe': dims: lists 'connection' beside its member 'unit', so the entry is their "
                'cross product',
                "drop 'unit' from dims: and read the operand at each tuple: at(capacity, by=connection[unit])",
                "drop 'connection' from dims: and sum to the member: sum(flow, over=connection, by=connection[unit])",
            ],
            id='a-dimension-beside-its-member',
        ),
        pytest.param(
            'e',
            {'expressions.e': {'dims': ['connection', 'unit', 'snapshot'], 'expression': 'flow * capacity'}},
            [
                "Named expression 'e': dims: lists 'connection' beside its member 'unit'",
                'at(capacity, by=connection[unit])',
            ],
            id='a-named-expression',
        ),
        pytest.param(
            'p',
            {'parameters.p': {'dims': ['connection', 'unit']}},
            ["Parameter 'p': dims: lists 'connection' beside", 'at(..., by=connection[unit])'],
            id='a-parameter',
        ),
        pytest.param(
            'pair',
            {'variables.pair': {'dims': ['trade', 'region']}},
            ["'trade' beside its member 'region'", 'at(..., by=trade[dst or src])'],
            id='a-member-by-role',
        ),
        pytest.param(
            'curve',
            {
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'variables.w': {'dims': ['connection']},
                'variables.v': {'dims': ['unit']},
                'variables.y': {'dims': ['connection', 'unit']},
                'piecewise.curve': {
                    'dims': ['connection', 'unit'],
                    'along': 'period',
                    'links': {'x': ['w + v', 'xs'], 'y': ['y', 'ys']},
                },
            },
            ["piecewise 'curve': dims: lists 'connection' beside its member 'unit'", 'at(v, by=connection[unit])'],
            id='a-curve',
        ),
    ],
)
def test_check_advises_on_a_cross_product_through_a_member(subject, patch, fragments):
    """Rule 11 of #1011: the entry loads as the cross product, and `check` names the rewrite it likely meant."""
    (note,) = _cross_products(subject, **patch)
    for fragment in fragments:
        assert fragment in note


@pytest.mark.parametrize(
    ('subject', 'patch'),
    [
        pytest.param('probe', _over_both(JOIN), id='the-inner-join'),
        pytest.param('probe', _over_both('assignment[unit] == connection[unit]'), id='the-join-the-other-way'),
        pytest.param('probe', _over_both(f"{JOIN} AND connection[port] == 'p1'"), id='the-join-and-another-filter'),
        pytest.param(
            'e',
            {'expressions.e': {'dims': ['connection', 'assignment'], 'expression': 'sent + on'}},
            id='a-named-expression-its-reader-filters',
        ),
        pytest.param('limit', {}, id='a-dimension-beside-no-member'),
        pytest.param('pair', {'variables.pair': {'dims': ['connection', 'trade']}}, id='two-dimensions-share-nothing'),
    ],
)
def test_no_cross_product_advice_where_the_entry_says_what_it_means(subject, patch):
    assert not _cross_products(subject, **patch), 'the entry keeps only the pairs of one member, or crosses nothing'


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
        'dimensions.link': {'over': {'unit': 'unit', 'side': 'port'}},
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
    ('patch', 'entry', 'dims'),
    [
        pytest.param(
            _constraint('on_link <= at(capacity, by=link[unit])', ['link'])
            | {'expressions.e': {'dims': ['port', 'unit'], 'expression': 'at(on_link, by=link[unit, side])'}},
            'expressions.e',
            ('port', 'unit'),
            id='a-role-arrives-as-its-dimension',
        ),
        pytest.param(
            _constraint('x <= at(at(y, by=assignment[unit, period]), by=connection[unit])', ['connection', 'period']),
            'constraints.probe',
            ('connection', 'period'),
            id='a-left-join-of-two-dimensions-that-share-a-member',
        ),
        pytest.param(
            _constraint('sum(at(flow, by=connection[unit, port]), over=port) >= 0', ['unit', 'snapshot']),
            'constraints.probe',
            ('snapshot', 'unit'),
            id='a-sum-after-the-spread',
        ),
        pytest.param(
            _constraint(
                "shift(at(flow, by=connection[unit, port]), along=snapshot, offset=1, edge='wrap') <= w",
                ['unit', 'port', 'snapshot'],
            ),
            'constraints.probe',
            ('port', 'snapshot', 'unit'),
            id='a-shift-along-another-dimension',
        ),
        pytest.param(
            _constraint(
                'y >= at(shift(at(y, by=assignment[unit, period]), along=period, offset=1), by=assignment[unit, period])',
                ['assignment'],
            ),
            'constraints.probe',
            ('assignment',),
            id='a-shift-along-a-member-read-back-at-each-tuple',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['unit', 'port', 'snapshot'],
                    'expression': 'at(flow, by=connection[unit, port])',
                }
            },
            'expressions.e',
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
            'expressions.f',
            ('port', 'snapshot', 'unit'),
            id='a-named-expression-as-the-operand',
        ),
        pytest.param(
            {'variables.w.bounds.upper': 'at(limit, by=connection[unit, port])'},
            'variables.w.upper',
            ('port', 'unit'),
            id='a-bound',
        ),
        pytest.param(
            {'variables.w.where': 'at(open, by=connection[unit, port])'},
            'variables.w.where',
            ('port', 'unit'),
            id='a-condition',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'variables.a': {'dims': ['unit', 'port']},
                'variables.b': {'dims': ['connection']},
                'piecewise.curve': {
                    'dims': ['connection'],
                    'along': 'period',
                    'links': {'x': ['at(a, by=connection[unit, port])', 'xs'], 'y': ['b', 'ys']},
                },
            },
            'variables.b.where',
            None,
            id='the-rewrite-of-a-piecewise-link-that-walks-the-dimension',
        ),
        pytest.param(
            {'variables.w.where': 'at(limit > 0, by=connection[port, unit])'},
            'variables.w.where',
            ('port', 'unit'),
            id='a-comparison-in-a-condition',
        ),
    ],
)
def test_a_spread_loads_wherever_a_lookup_does(patch, entry, dims):
    program = to_spec(varied(SPREAD, **patch)).program
    section, name, *field = entry.split('.')
    found = getattr(program, section)[name]
    if section == 'constraints':
        assert sorted_dims(found.lhs.dims, found.rhs.dims) == dims
    elif dims is not None:
        assert getattr(found, *field or ['expression']).dims == dims


@pytest.mark.parametrize(
    ('patch', 'fragments'),
    [
        pytest.param(
            _constraint('at(flow, by=connection[unit]) >= 0', ['unit', 'snapshot']),
            (
                "at(by=connection[unit]) lists ['unit'] of the members ['port', 'unit'] of 'connection'",
                'at(flow, by=connection[port, unit])',
                'sum(flow, over=connection, by=connection[unit])',
            ),
            id='a-partial-list',
        ),
        pytest.param(
            {'variables.w.where': 'at(open, by=connection[port])'},
            (
                "Variable 'w': at(by=connection[port]) lists ['port'] of the members ['port', 'unit']",
                'at(..., by=connection[port, unit])',
            ),
            id='a-partial-list-in-a-condition',
        ),
        pytest.param(
            _constraint('at(shipped, by=trade[src, dst]) >= 0', ['region']),
            (
                "at(by=trade[src, dst]): the members ['dst', 'src'] of 'trade' are both over 'region'",
                'sum(shipped, over=trade, by=trade[dst])',
            ),
            id='two-members-over-one-dimension',
        ),
        pytest.param(
            _constraint('at(both, by=connection[unit, port]) >= 0', ['unit', 'port']),
            ("carries both 'connection' and its member ['unit']", "Sum ['unit'] out of the operand first"),
            id='an-operand-with-the-dimension-and-a-member',
        ),
        pytest.param(
            _constraint('w <= flow', ['unit', 'port', 'snapshot']),
            (
                "an operand over ['port', 'unit'] meets one over 'connection'",
                'at(w, by=connection[port, unit])',
                'spread flow over the members: at(flow, by=connection[port, unit])',
            ),
            id='an-operand-over-every-member-meets-the-dimension',
        ),
        pytest.param(
            _constraint('flow >= 0', ['unit', 'port', 'snapshot']),
            ("carries dims ['connection'] that are not in its dims", 'at(flow, by=connection[port, unit])'),
            id='a-constraint-over-the-members-reads-the-dimension',
        ),
        pytest.param(
            {'expressions.e': {'dims': ['unit', 'port', 'snapshot'], 'expression': '2 * flow'}},
            ("the body carries dims ['connection']", 'at(flow, by=connection[port, unit])'),
            id='a-named-expression-over-the-members-reads-the-dimension',
        ),
        pytest.param(
            {'variables.w.bounds.upper': 'limit'},
            ("parameter 'limit' has dims ['connection'] outside", 'at(limit, by=connection[port, unit])'),
            id='a-bound-over-the-dimension',
        ),
        pytest.param(
            {'variables.w.where': 'open'},
            ("reads dims ['connection'] outside the declared dims", 'at(open, by=connection[port, unit])'),
            id='a-where-over-the-dimension',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'variables.a': {'dims': ['unit', 'port']},
                'variables.b': {'dims': ['connection']},
                'piecewise.curve': {
                    'dims': ['connection'],
                    'along': 'period',
                    'links': {
                        'x': {'expression': 'a', 'values': 'xs', 'by': 'connection[unit, port]'},
                        'y': ['b', 'ys'],
                    },
                },
            },
            (
                "piecewise 'curve' link 'x': by: connection[unit, port] spreads the curve over the members",
                'at(<expression>, by=connection[unit, port])',
            ),
            id='a-piecewise-link-that-walks-the-dimension',
        ),
        pytest.param(
            _constraint('at(flow, by=connection_bus[bus]) >= 0', ['bus', 'snapshot']),
            ("at(by=connection_bus[bus]) joins on ['bus']", 'use sum() instead'),
            id='a-relation-keyed-by-the-dimension-is-no-spread',
        ),
        pytest.param(
            _constraint(
                "shift(at(flow, by=connection[unit, port]), along=connection, offset=1, edge='wrap') >= 0",
                ['unit', 'port', 'snapshot'],
            ),
            ("shift(along=connection) reads the order of 'connection'",),
            id='a-shift-along-the-dimension',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['unit', 'port', 'snapshot'],
                    'cases': {
                        'open': {'when': 'at(open, by=connection[unit, port])', 'expression': 'w'},
                        'shut': {'when': 'not at(open, by=connection[unit, port])', 'expression': '2 * w'},
                    },
                    'otherwise': '0',
                }
            },
            (
                "cases 'open' and 'shut' cannot be told apart before the data arrives",
                "at(by=connection[port, unit]) is true only where 'connection' lists the tuple",
                "an entry over 'connection'",
            ),
            id='a-spread-in-two-cases',
        ),
    ],
)
def test_a_spread_that_does_not_load_is_refused_with_the_rewrite(patch, fragments):
    message = _spread_refusal(**patch)
    for fragment in fragments:
        assert fragment in message


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
            _constraint('sum(flow * capacity, over=unit) <= both', ['connection', 'unit', 'snapshot']),
            ("meets one over 'connection'", 'at(capacity, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple-under-a-sum-over-the-member-the-frame-declares',
        ),
        pytest.param(
            _constraint('sum(flow * capacity) <= both', ['connection', 'unit']),
            ("meets one over 'connection'", 'at(capacity, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple-under-a-sum-over-everything',
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
                'variables.y': {'dims': ['connection', 'unit']},
                'piecewise.curve': {
                    'dims': ['connection', 'unit'],
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
        pytest.param({'x': {'dims': ['snapshot']}}, ['connection', 'port', 'unit'], id='nothing-is-over-the-dimension'),
        pytest.param({'x': {'dims': ['connection']}}, ['snapshot'], id='an-entry-is-over-the-dimension'),
    ],
)
def test_the_implied_relation_does_not_count_as_a_use(variables, unused):
    """The relation the entry implies has a column over the dimension and each member, so it counted as reaching them."""
    spec = {
        'dimensions': {'unit': {}, 'port': {}, 'snapshot': {}, 'connection': {'over': ['unit', 'port']}},
        'variables': variables,
    }
    notes = sorted(note.subject for note in advice(spec) if note.kind == 'never-an-axis')
    assert notes == unused, 'an entry over the dimension reaches its members, and the implied relation reaches nothing'


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
