# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""What `Spec.sensitivity` writes, and where it refuses to write anything.

The rate is only as right as its sign, and the sign is what `dual(c)` means:
the rise of the optimal objective with the right side of `c`. The numbers
behind that reading were checked against finite differences on HiGHS; the
rows here pin the expression the derivation writes, which no solver is needed
to read.
"""

from __future__ import annotations

import pytest

from mathspec import LanguageError, SchemaError
from tests.fixtures import schema_of, varied
from tests.test_fixing import MONOLITH

SUBPROBLEM = schema_of(MONOLITH).fix('cap').to_dict()


def _written(model, *names, **patch) -> dict[str, str]:
    spec = schema_of(model, **patch).sensitivity(*names)
    return {name: spec.expressions[f'{name}_sensitivity'].expression for name in names}


def test_the_cut_of_a_benders_subproblem():
    """The objective reads `cap` directly, and `capacity` reads it on its right side."""
    assert _written(SUBPROBLEM, 'cap', 'load') == {
        'cap': 'invest + sum(dual(capacity) * avail, over=snapshot)',
        'load': 'dual(balance)',
    }


def test_the_rate_is_over_the_parameters_own_dims():
    program = schema_of(SUBPROBLEM).sensitivity('cap', 'load').program
    assert program.expressions['cap_sensitivity'].dims == ('generator',), 'summed back over snapshot'
    assert program.expressions['load_sensitivity'].dims == ('snapshot',)
    assert not program.expressions['cap_sensitivity'].in_math, 'a reported expression: no solver sees it'


@pytest.mark.parametrize(
    ('capacity', 'written'),
    [
        pytest.param('p <= cap * avail', 'invest + sum(dual(capacity) * avail, over=snapshot)', id='on-the-right'),
        pytest.param('cap * avail >= p', 'invest - sum(dual(capacity) * avail, over=snapshot)', id='on-the-left'),
        pytest.param('p <= 2 * cap * avail', 'invest + sum(dual(capacity) * avail * 2.0, over=snapshot)', id='scaled'),
        pytest.param('p <= -(-cap) * avail', 'invest + sum(dual(capacity) * avail, over=snapshot)', id='negated-twice'),
        pytest.param('p == cap * avail', 'invest + sum(dual(capacity) * avail, over=snapshot)', id='an-equality'),
        pytest.param(
            'p - cap * avail / 2 <= 0', 'invest + sum(dual(capacity) / 2.0 * avail, over=snapshot)', id='divided'
        ),
    ],
)
def test_the_rows_sides_decide_the_sign_and_its_comparator_does_not(capacity, written):
    assert _written(SUBPROBLEM, 'cap', **{'constraints.capacity.expression': capacity})['cap'] == written


def test_maximize_takes_the_same_expression():
    """The dual is the rise of the objective with the right side under either sense, so nothing flips."""
    raw = varied(SUBPROBLEM, objective={'sense': 'maximize', 'expression': '-sum(cap * invest) - sum(p * cost)'})
    assert _written(raw, 'cap')['cap'] == '-invest + sum(dual(capacity) * avail, over=snapshot)'


def test_a_masked_row_summed_back_is_one_summand_fewer():
    written = _written(SUBPROBLEM, 'cap', **{'constraints.capacity.where': 'avail > 0'})
    assert written['cap'] == 'invest + sum(dual(capacity) * avail, over=snapshot)'


@pytest.mark.parametrize(
    ('names', 'patch', 'says'),
    [
        pytest.param(('capp',), {}, "'capp' is not a parameter of this spec. Did you mean 'cap'", id='a-near-miss'),
        pytest.param(('p',), {}, "'p' is not a parameter", id='a-variable'),
    ],
)
def test_a_name_that_is_not_a_parameter_is_refused(names, patch, says):
    with pytest.raises(SchemaError, match=says):
        _written(SUBPROBLEM, *names, **patch)


@pytest.mark.parametrize(
    ('name', 'patch', 'says'),
    [
        pytest.param(
            'cap',
            {'constraints.capacity.expression': 'p <= shift(cap, along=generator, offset=1, edge=0) * avail'},
            'through Translate',
            id='through-a-shift',
        ),
        pytest.param('cap', {'constraints.capacity.expression': 'p / cap <= avail'}, 'divides by it', id='a-divisor'),
        pytest.param(
            'cap',
            {'constraints.capacity.expression': 'p <= avail * sum(cap, over=generator)'},
            'sums over generator inside a factor that carries it',
            id='a-sum-over-a-dim-the-factor-outside-carries',
        ),
        pytest.param(
            'load', {'constraints.balance.where': 'load > 0'}, 'has a where:', id='a-masked-row-read-pointwise'
        ),
        pytest.param('avail', {'variables.p.bounds': {'lower': 0, 'upper': 'avail'}}, 'bounds variable', id='a-bound'),
        pytest.param(
            'invest', {'objective.expression': 'sum(p * cost)'}, 'neither the objective nor a constraint', id='unread'
        ),
    ],
)
def test_what_the_derivation_cannot_carry_is_refused(name, patch, says):
    with pytest.raises(LanguageError, match=says):
        _written(SUBPROBLEM, name, **patch)


def test_an_entry_of_that_name_is_refused():
    with pytest.raises(LanguageError, match="'cap_sensitivity' is already an expression"):
        _written(SUBPROBLEM, 'cap', expressions={'cap_sensitivity': 'sum(avail)'})
