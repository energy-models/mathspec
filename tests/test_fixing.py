# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""What `Spec.fix` keeps when a decision becomes a supplied number.

The rewrite a driver writes by hand is wrong twice, and silently (#303): a
masked variable becomes a parameter that reads `0` where the variable did not
exist, so rows the mask dropped stand again, and a binary becomes a float.
Most rows here pin one of the two, or a reader the mask cannot reach.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mathspec import LanguageError, SchemaError
from tests.fixtures import SMALL_MODEL, override, schema_of

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'

BASE = override(
    SMALL_MODEL,
    parameters={**SMALL_MODEL['parameters'], 'cap_max': {'dims': ['g']}},
    variables={
        'p': {'dims': ['g'], 'bounds': {'lower': 0}},
        'cap': {'dims': ['g'], 'bounds': {'lower': 0, 'upper': 'cap_max'}},
    },
    constraints={
        'within': {'dims': ['g'], 'expression': 'p <= cap'},
        'demand': {'dims': [], 'expression': 'sum(p, over=g) >= k'},
    },
    objective={'sense': 'minimize', 'expression': 'sum(c * p + 2 * cap, over=g)'},
)

#: `cap` exists only where `flag`, and is read outside a sum by `within`.
MASKED = override(BASE, **{'variables.cap.where': 'flag'})


def _fixed(model=BASE, *names, **patch):
    return schema_of(model, **patch).fix(*names)


# ---------------------------------------------------------------------------
# the variable becomes a parameter, and everything goes on reading it
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('domain', 'dtype'),
    [
        pytest.param('continuous', 'float', id='continuous'),
        pytest.param('integer', 'int', id='integer'),
        pytest.param('binary', 'int', id='a-binary-is-an-int-never-a-float-or-a-mask'),
    ],
)
def test_a_fixed_variable_is_a_parameter_of_its_domain(domain, dtype):
    spec = _fixed(BASE, 'cap', **{'variables.cap.domain': domain})
    assert 'cap' not in spec.program.variables
    assert spec.program.parameters['cap'].dims == ('g',)
    assert spec.program.parameters['cap'].dtype == dtype


def test_every_expression_goes_on_reading_the_name():
    spec = _fixed(BASE, 'cap')
    assert repr(spec.program.constraints['within'].rhs) == "Parameter(name='cap')", 'the row reads the number now'
    assert spec.program.problem_class.kind == 'LP'


def test_fixing_a_binary_makes_the_program_continuous():
    spec = _fixed(BASE, 'cap', **{'variables.cap.domain': 'binary', 'variables.cap.bounds': {}})
    assert (
        schema_of(BASE, **{'variables.cap.domain': 'binary', 'variables.cap.bounds': {}}).program.problem_class.kind
        == 'MILP'
    )
    assert spec.program.problem_class.kind == 'LP', 'the only integer decision is supplied now'


@pytest.mark.parametrize(
    ('patch', 'holds'),
    [
        pytest.param({}, 'cap >= 0.0 AND cap <= cap_max', id='a-number-and-a-parameter'),
        pytest.param(
            {'variables.cap.domain': 'binary', 'variables.cap.bounds': {}}, 'cap >= 0 AND cap <= 1', id='a-binary'
        ),
    ],
)
def test_the_bounds_become_an_assumption_on_the_supplied_numbers(patch, holds):
    written = _fixed(BASE, 'cap', **patch).to_dict()['assumptions']['cap_within_bounds']
    assert written['holds'] == holds


def test_an_unbounded_variable_assumes_nothing():
    spec = _fixed(BASE, 'cap', **{'variables.cap.bounds': {}})
    assert 'cap_within_bounds' not in spec.program.assumptions


def test_a_row_that_only_decided_the_fixed_variable_is_an_assumption():
    """`floor` names only `cap`. Fixed, it compares numbers, which the loader
    refuses as a row; stated as an assumption, the consumer checks the numbers against it."""
    spec = _fixed(BASE, 'cap', **{'constraints.floor': {'dims': ['g'], 'where': 'flag', 'expression': 'cap >= c'}})
    assert 'floor' not in spec.program.constraints
    assumption = spec.to_dict()['assumptions']['floor']
    assert (assumption['holds'], assumption['where']) == ('cap >= c', 'flag'), 'the row and its mask, as written'


def test_fixing_one_at_a_time_is_fixing_them_together():
    spec = schema_of(
        BASE,
        **{
            'variables.spare': {'dims': ['g'], 'bounds': {'lower': 0}},
            'constraints.within.expression': 'p <= cap + spare',
        },
    )
    assert spec.fix('cap').fix('spare').to_dict() == spec.fix('cap', 'spare').to_dict()


# ---------------------------------------------------------------------------
# a masked variable: where it did not exist, it must still take the row
# ---------------------------------------------------------------------------


def test_an_unguarded_read_takes_the_mask_into_the_row():
    """`within` reads `cap` pointwise. Where `flag` is false there was no `cap`
    and no row; as a parameter `cap` reads 0 there, and `p <= 0` would stand."""
    spec = _fixed(MASKED, 'cap')
    assert spec.to_dict()['constraints']['within']['where'] == 'flag'


def test_the_mask_joins_a_where_the_row_already_has():
    spec = _fixed(MASKED, 'cap', **{'constraints.within.where': 'c > 0'})
    assert spec.to_dict()['constraints']['within']['where'] == '(c > 0) AND (flag)'


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({'constraints.within.where': 'flag'}, id='the-row-is-already-masked'),
        pytest.param({'constraints.within.where': 'c > 0 AND flag'}, id='the-row-mask-holds-it-among-others'),
        pytest.param(
            {'constraints.within': {'dims': [], 'expression': 'sum(p - cap, over=g) <= 0'}},
            id='a-sum-absorbs-the-absence',
        ),
        pytest.param({'variables.cap.absence': 'zero'}, id='zero-outside-the-mask-is-what-a-missing-row-reads'),
    ],
)
def test_a_guarded_read_leaves_the_row_as_written(patch):
    written = schema_of(MASKED, **patch).to_dict()['constraints']['within'].get('where')
    assert _fixed(MASKED, 'cap', **patch).to_dict()['constraints']['within'].get('where') == written


def test_the_pypsa_capacities_are_guarded_where_they_are_read():
    """Every pointwise read of an extendable capacity already stands under
    `..._extendable`, so the fix adds no mask; what only decided capacity moves
    to assumptions, and dispatch no longer shares a column across snapshots."""
    spec = schema_of(EXAMPLES / 'pypsa.yaml')
    names = [name for name in spec.program.variables if name.endswith('_nom_ext')] + ['Generator_n_mod']
    fixed = spec.fix(*names)
    masks = {name: row.where for name, row in spec.program.constraints.items()}
    assert [name for name, row in fixed.program.constraints.items() if row.where != masks[name]] == [], (
        'no constraint gained a where'
    )
    assert fixed.program.separability['snapshot'].linking_columns == (), 'no column links two snapshots'


# ---------------------------------------------------------------------------
# refused, with the reader named
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('patch', 'says'),
    [
        pytest.param(
            {'constraints.within.expression': 'p <= shift(cap, along=g, offset=1)'},
            "constraint 'within' reads 'cap' outside a sum, through a shift",
            id='through-a-shift',
        ),
        pytest.param(
            {
                'expressions': {
                    'room': {
                        'dims': ['g'],
                        'cases': {'built': {'when': 'c > 0', 'expression': 'cap'}},
                        'otherwise': 0,
                    }
                },
                'constraints.within.expression': 'p <= room',
            },
            "constraint 'within' reads 'cap' outside a sum, in a case",
            id='in-a-case-its-mask-does-not-guard',
        ),
    ],
)
def test_a_read_the_mask_cannot_reach_is_refused(patch, says):
    with pytest.raises(LanguageError, match=says):
        _fixed(MASKED, 'cap', **patch)


def test_a_case_under_the_mask_is_guarded():
    patch = {
        'expressions': {
            'room': {
                'dims': ['g'],
                'cases': {'built': {'when': 'flag', 'expression': 'cap'}},
                'otherwise': 0,
            }
        },
        'constraints.within.expression': 'p <= room',
    }
    assert 'where' not in _fixed(MASKED, 'cap', **patch).to_dict()['constraints']['within']


@pytest.mark.parametrize(
    ('names', 'says'),
    [
        pytest.param(('capp',), "'capp' is not a variable of this spec. Did you mean 'cap'", id='a-near-miss'),
        pytest.param(('c',), "'c' is not a variable", id='a-parameter'),
        pytest.param(('cap', 'cap'), "'cap' is given 2 times", id='twice'),
    ],
)
def test_a_name_that_is_not_a_variable_is_refused(names, says):
    with pytest.raises(SchemaError, match=says):
        _fixed(BASE, *names)


def test_a_set_on_the_variable_is_refused():
    with pytest.raises(LanguageError, match="'cap' is the variable of set 's'"):
        _fixed(BASE, 'cap', sos={'s': {'variable': 'cap', 'along': 'g', 'type': 1}})


#: The monolith of specsolve's `examples/benders/`: capacity and dispatch in one plan.
MONOLITH = {
    'dimensions': {'snapshot': {'dtype': 'int'}, 'generator': {'dtype': 'str'}},
    'parameters': {
        'invest': {'dims': ['generator']},
        'cost': {'dims': ['generator']},
        'load': {'dims': ['snapshot']},
        'avail': {'dims': ['snapshot', 'generator']},
    },
    'variables': {
        'cap': {'dims': ['generator'], 'bounds': {'lower': 0, 'upper': 100}},
        'p': {'dims': ['snapshot', 'generator'], 'bounds': {'lower': 0}},
    },
    'constraints': {
        'capacity': {'dims': ['snapshot', 'generator'], 'expression': 'p <= cap * avail'},
        'balance': {'dims': ['snapshot'], 'expression': 'sum(p, over=generator) >= load'},
    },
    'objective': {'sense': 'minimize', 'expression': 'sum(cap * invest) + sum(p * cost)'},
}


def test_the_benders_subproblem_is_a_call_on_the_monolith():
    """specsolve ships the subproblem as a second file with `cap` renamed; the call states the same rows."""
    monolith = schema_of(MONOLITH).program
    subproblem = schema_of(MONOLITH).fix('cap').program
    assert monolith.separability['snapshot'].linking_columns == ('cap',), 'capacity links every snapshot'
    assert subproblem.separability['snapshot'].linking_columns == (), 'fixed, each snapshot is its own block'
    assert subproblem.problem_class.kind == 'LP'
    assert sorted(subproblem.constraints) == ['balance', 'capacity']


def test_a_variable_a_curve_names_is_fixed_after_the_expansion():
    spec = schema_of(EXAMPLES / 'piecewise.yaml')
    with pytest.raises(LanguageError, match="'dispatch' stands in curve 'cost_curve'"):
        spec.fix('dispatch')
    assert 'dispatch' in spec.expand().fix('dispatch').program.parameters, 'written out, the curve is rows that read it'
