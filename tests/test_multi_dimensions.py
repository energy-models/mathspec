# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A multi-dimension: which frames meet it, the node each meeting lowers to, and what is refused at load."""

from __future__ import annotations

from typing import Any

import pytest

from mathspec._validation import to_spec
from mathspec.errors import LanguageError
from mathspec.program import (
    Constraint,
    DimensionDefined,
    Not,
    ParameterReference,
    Program,
    Reframe,
    ReframedCondition,
    Sum,
    Translate,
    VariableReference,
    walk,
)
from tests.fixtures import varied

MODEL: dict[str, Any] = {
    'dimensions': {
        'unit': {},
        'bus': {},
        'period': {},
        'snapshot': {'dtype': 'int', 'ordered': True},
        'zone': {},
        'connection': {'over': ['unit', 'bus']},
        'active': {'over': ['unit', 'period']},
    },
    'relations': {'zone_of': {'key': 'bus', 'values': 'zone'}},
    'parameters': {
        'capacity': {'dims': ['unit']},
        'load': {'dims': ['bus', 'snapshot']},
        'output': {'dims': ['connection'], 'dtype': 'bool', 'missing': False},
        'zone_load': {'dims': ['zone']},
    },
    'variables': {
        'flow': {'dims': ['connection', 'snapshot'], 'bounds': {'lower': 0, 'upper': 'capacity'}},
        'spread': {'dims': ['bus', 'snapshot', 'unit']},
    },
}


def _program(**patch: Any) -> Program:
    return to_spec(varied(MODEL, **patch)).program


def _constraint(dims: list[str], expression: str, where: str | None = None) -> Constraint:
    entry = {'dims': dims, 'expression': expression, **({'where': where} if where else {})}
    return _program(**{'constraints.c': entry}).constraints['c']


def _refusal(**patch: Any) -> str:
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(MODEL, **patch))
    return str(caught.value)


def test_a_member_meets_its_multi_dimension_read_at_each_listed_combination():
    """``flow <= capacity``: capacity over [unit] is gathered at each connection's unit."""
    c = _constraint(['connection', 'snapshot'], 'flow <= capacity')
    assert c.rhs == Reframe(ParameterReference('capacity', dims=('unit',)), dims=('connection',))


def test_a_variable_bound_over_a_member_is_read_at_each_combination():
    bound = _program().variables['flow'].upper
    assert bound == Reframe(ParameterReference('capacity', dims=('unit',)), dims=('connection',))


@pytest.mark.parametrize(
    ('over', 'dims', 'operand_dims'),
    [
        pytest.param('unit', ('bus', 'snapshot'), ('bus', 'snapshot', 'unit'), id='one-member-projects-onto-the-other'),
        pytest.param('[unit, bus]', ('snapshot',), ('bus', 'snapshot', 'unit'), id='every-member'),
        pytest.param('connection', ('snapshot',), ('connection', 'snapshot'), id='the-whole-multi-dimension'),
    ],
)
def test_a_sum_reads_its_operand_over_the_axes_it_names(over, dims, operand_dims):
    c = _constraint(list(dims), f'sum(flow, over={over}) <= 1')
    assert isinstance(c.lhs, Sum)
    assert c.lhs.dims == dims, f'sum(over={over}) leaves {dims}'
    assert c.lhs.operand.dims == operand_dims, 'the operand is read over the axes the sum removes'


def test_a_sum_over_a_multi_dimension_runs_a_flat_operand_over_the_listed_combinations():
    c = _constraint(['snapshot'], 'sum(spread, over=connection) <= 1')
    assert isinstance(c.lhs, Sum)
    assert c.lhs.operand == Reframe(
        VariableReference('spread', dims=('bus', 'snapshot', 'unit')), dims=('connection', 'snapshot')
    )


def test_a_flat_constraint_reads_a_multi_dimension_spread_over_its_members():
    """The scatter: flow is absent at a pair connection does not list, so the row is too."""
    c = _constraint(['bus', 'snapshot', 'unit'], 'spread <= flow')
    assert c.rhs == Reframe(
        VariableReference('flow', dims=('connection', 'snapshot')), dims=('bus', 'snapshot', 'unit')
    )


def test_a_shift_along_a_plain_dimension_keeps_the_multi_dimension():
    c = _constraint(['connection', 'snapshot'], 'flow - shift(flow, along=snapshot, offset=1) <= 1')
    shifted = c.lhs.right.operand
    assert isinstance(shifted, Translate)
    assert shifted.operand.dims == ('connection', 'snapshot'), 'snapshot is no member, so nothing is spread'


def test_a_sum_through_a_relation_on_a_member_reads_the_members():
    c = _constraint(['snapshot', 'zone'], 'sum(flow, over=[unit, bus], by=zone_of[zone]) <= zone_load')
    reframed = [n for n in walk(c.lhs) if isinstance(n, Reframe)]
    assert [n.dims for n in reframed] == [('bus', 'snapshot', 'unit')], 'the join reads bus as an axis of its own'


def test_a_bare_multi_dimension_in_a_condition_holds_at_its_listed_combinations():
    c = _constraint(['bus', 'snapshot', 'unit'], 'spread <= 1', where='connection')
    assert c.where is not None
    assert c.where.root == ReframedCondition(DimensionDefined('connection'), dims=('bus', 'unit'))


def test_each_leaf_is_spread_before_a_negation_reads_it():
    """``NOT output`` holds off connection, where the flat twin's ``output`` has no row."""
    c = _constraint(['bus', 'snapshot', 'unit'], 'spread <= 1', where='NOT output')
    assert c.where is not None
    assert isinstance(c.where.root, Not)
    assert isinstance(c.where.root.operand, ReframedCondition)


def test_a_mask_over_a_member_is_read_at_each_combination():
    c = _constraint(['connection', 'snapshot'], 'flow <= 1', where='capacity > 0')
    assert c.where is not None
    assert c.where.dims == ('connection',)


@pytest.mark.parametrize(
    ('patch', 'fragment'),
    [
        pytest.param({'dimensions.pair': {'over': ['unit', 'unit']}}, "lists 'unit' twice", id='a-member-listed-twice'),
        pytest.param({'dimensions.pair': {'over': ['unit']}}, 'at least 2', id='one-member'),
        pytest.param(
            {'dimensions.pair': {'over': ['unit', 'bus'], 'ordered': True}},
            'belongs on a member',
            id='a-multi-dimension-takes-no-order',
        ),
        pytest.param(
            {'dimensions.pair': {'over': ['unit', 'site']}},
            "undeclared dimension 'site'",
            id='an-undeclared-member',
        ),
        pytest.param(
            {'dimensions.pair': {'over': ['connection', 'period']}},
            'List the plain dimensions',
            id='a-multi-dimension-as-a-member',
        ),
        pytest.param(
            {'parameters.x': {'dims': ['connection', 'unit']}},
            "names 'unit' beside 'connection'",
            id='a-member-beside-its-multi-dimension',
        ),
        pytest.param(
            {'parameters.x': {'dims': ['connection', 'active']}},
            "'active' and 'connection' both combine 'unit'",
            id='two-multi-dimensions-sharing-a-member-in-dims',
        ),
        pytest.param(
            {
                'variables.on': {'dims': ['active', 'snapshot']},
                'constraints.c': {
                    'dims': ['snapshot'],
                    'expression': 'sum(flow, over=connection) <= sum(on + flow, over=unit)',
                },
            },
            "'active' and 'connection' both combine 'unit'",
            id='two-multi-dimensions-sharing-a-member-in-arithmetic',
        ),
        pytest.param(
            {
                'constraints.c': {
                    'dims': ['connection', 'snapshot'],
                    'expression': 'shift(flow, along=connection, offset=1) <= 1',
                }
            },
            'has no order',
            id='shift-along-a-multi-dimension',
        ),
        pytest.param(
            {
                'constraints.c': {
                    'dims': ['connection', 'snapshot'],
                    'expression': 'flow <= 1',
                    'where': 'position(connection) == 0',
                }
            },
            'has no order',
            id='position-of-a-multi-dimension',
        ),
        pytest.param(
            {
                'constraints.c': {
                    'dims': ['connection', 'snapshot'],
                    'expression': 'flow <= 1',
                    'where': "connection == 'a'",
                }
            },
            'Compare one of its members',
            id='a-multi-dimension-compared-to-a-label',
        ),
        pytest.param(
            {'relations.role_of': {'key': 'connection', 'values': 'period'}},
            'declare a parameter over [connection]',
            id='a-relation-column-over-a-multi-dimension',
        ),
        pytest.param(
            {'sos.s': {'variable': 'flow', 'along': 'connection', 'type': 1}},
            'has no order',
            id='a-set-along-a-multi-dimension',
        ),
    ],
)
def test_a_multi_dimension_is_refused_where_it_cannot_stand(patch, fragment):
    assert fragment in _refusal(**patch)
