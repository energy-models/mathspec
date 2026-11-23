# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`sos:` as a formulation: what a set is written out as, and what it may not lose.

Every claim here is one `Spec.expand` reaches with no data attached — which
entries a set emits, which coefficient links them, and that the adjacency
method is the same rows under the same names.
"""

from __future__ import annotations

import pytest

from mathspec.errors import SchemaError
from mathspec.program import Translate, VariableReference, WindowSum, walk
from tests.fixtures import SMALL_MODEL, expanded, spec_of, varied

#: A set over a bounded member, which is the smallest model `expand('sos')` acts on.
PICKED = varied(
    SMALL_MODEL,
    **{
        'parameters.floor': {'dims': ['g']},
        'variables.p.bounds': {'lower': 0, 'upper': 10},
        'constraints': {'used': {'dims': ['g'], 'expression': 'p <= c'}},
        'sos': {'pick': {'variable': 'p', 'along': 'g', 'type': 1}},
    },
)

#: The curve of `examples/sos.yaml`, as a dict a test can vary.
CURVE = {
    'dimensions': {'snapshot': {'dtype': 'int'}, 'bp': {'dtype': 'int', 'ordered': True}},
    'parameters': {'load': {'dims': ['snapshot']}, 'bp_x': {'dims': ['bp']}, 'bp_y': {'dims': ['bp']}},
    'variables': {
        'p': {'dims': ['snapshot'], 'bounds': {'lower': 0, 'upper': 100}},
        'op_cost': {'dims': ['snapshot'], 'bounds': {'lower': 0}},
    },
    'piecewise': {
        'cost_curve': {
            'along': 'bp',
            'dims': ['snapshot'],
            'method': 'sos2',
            'links': {'p': ['p', 'bp_x'], 'op_cost': ['op_cost', 'bp_y']},
        }
    },
    'constraints': {'balance': {'dims': ['snapshot'], 'expression': 'p == load'}},
    'objective': {'sense': 'minimize', 'expression': 'sum(op_cost, over=snapshot)'},
}


@pytest.mark.parametrize(
    ('bounds', 'rows'),
    [
        pytest.param(
            {'lower': 0, 'upper': 10},
            {'pick_nonzero': 'p <= 10.0 * (pick_seg)'},
            id='a-member-that-starts-at-zero-needs-one-row',
        ),
        pytest.param(
            {'lower': -5, 'upper': 10},
            {'pick_nonzero': 'p <= 10.0 * (pick_seg)', 'pick_nonzero_below': 'p >= -5.0 * (pick_seg)'},
            id='a-member-that-may-go-negative-is-held-from-below-too',
        ),
        pytest.param(
            {'lower': 'floor', 'upper': 'c'},
            {'pick_nonzero': 'p <= c * (pick_seg)', 'pick_nonzero_below': 'p >= floor * (pick_seg)'},
            id='a-bound-the-data-carries-is-a-coefficient-like-any-other',
        ),
    ],
)
def test_an_unpicked_member_is_held_at_zero_from_the_sides_its_bounds_state(bounds, rows):
    """A row multiplies by a bound rather than reading it, so a parameter needs no
    load-time knowledge of its value; and `x >= 0 * seg` is what the variable's own
    bound already says, so the second row is written only where it says more."""
    spec = spec_of(varied(PICKED, **{'variables.p.bounds': bounds}))
    expanded = spec.expand('sos')

    written = {name: c.expression for name, c in expanded.constraints.items() if name.startswith('pick_nonzero')}
    assert written == rows, 'the rows a set states, and no row that states nothing'


def test_a_set_carries_no_coefficient_of_its_own():
    """`bound:` replaced the member's upper bound in the linking row. Below it the row
    capped a picked member the set does not cap; above it the row was a looser big-M;
    a solver taking the set natively ignored it either way. So the coefficient is the
    member's own bound and nothing else, and the key is not in the language."""
    with pytest.raises(SchemaError, match="unknown key 'bound' in a sos entry"):
        spec_of(varied(PICKED, **{'sos.pick.bound': 500}))


def test_a_coefficient_of_one_is_left_out_of_the_row_rather_than_printed():
    """A binary carries no `bounds:`, and its upper bound is 1 all the same — which multiplies nothing."""
    spec = spec_of(varied(PICKED, **{'variables.p': {'dims': ['g'], 'domain': 'binary'}}))

    assert spec.expand('sos').constraints['pick_nonzero'].expression == 'p <= (pick_seg)'


def test_the_emitted_binary_carries_the_members_own_mask():
    """A member that does not exist is not in the set, so its binary is not there either."""
    spec = spec_of(varied(PICKED, **{'variables.p.where': 'flag'}))

    assert spec.expand('sos').variables['pick_seg'].where == 'flag'


def test_a_member_whose_neighbour_is_masked_keeps_its_adjacency_row():
    """The row read the binary of the segment before a member through `shift`, and
    an absent input to `shift` takes the row with it (#993). At the first member
    of a mask that starts after the first position, no row was built, so that
    member could be nonzero beside any picked segment: a curve whose run started
    late was its convex hull. A trailing window leaves the absent binary out and
    keeps the row."""
    spec = spec_of(varied(PICKED, **{'variables.p.where': 'flag', 'sos.pick.type': 2}))
    row = spec.expand('sos').program.constraints['pick_adjacency']

    shifted = [node for node in walk(row.rhs) if isinstance(node, Translate)]
    windows = [node for node in walk(row.rhs) if isinstance(node, WindowSum)]
    assert not shifted, 'no read of a binary through shift, whose absent input drops the row'
    assert [(w.operand, w.along, w.width) for w in windows] == [(VariableReference('pick_seg', dims=('g',)), 'g', 2)], (
        'one window over the segment of the member and the one before it'
    )


def test_a_set_emits_no_parameter_so_the_same_sources_bind_both():
    program, written_out = spec_of(PICKED).program, spec_of(PICKED).expand('sos').program

    assert set(written_out.parameters) == set(program.parameters), 'a set states rows and columns, never data'


def test_the_adjacency_method_is_the_sos2_curve_with_its_set_written_out():
    """The one spelling of the binaries, so the two methods cannot drift apart."""
    sos2 = spec_of(CURVE).expand().program
    adjacency = expanded(varied(CURVE, **{'piecewise.cost_curve.method': 'adjacency'}), 'piecewise').program

    assert sos2.variables == adjacency.variables
    assert sos2.constraints == adjacency.constraints
    assert not sos2.sos and not adjacency.sos, 'neither hands a solver a set'


@pytest.mark.parametrize(
    ('kinds', 'sets', 'curves'),
    [
        pytest.param(('piecewise',), ['cost_curve'], [], id='curves-only-leaves-the-set-it-emitted'),
        pytest.param(('sos',), [], ['cost_curve'], id='sets-only-reaches-no-set-a-curve-has-not-emitted-yet'),
        pytest.param((), [], [], id='both-writes-out-the-set-the-curve-emitted'),
    ],
)
def test_a_curve_emits_a_set_and_no_set_emits_a_curve(kinds, sets, curves):
    """Which is why the order is fixed rather than the caller's."""
    expanded = spec_of(CURVE).expand(*kinds)

    assert sorted(expanded.sos) == sets
    assert sorted(expanded.piecewise) == curves
