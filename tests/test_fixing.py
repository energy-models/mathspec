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
from tests.fixtures import SMALL_MODEL, schema_of, varied

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'

BASE = varied(
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
MASKED = varied(BASE, **{'variables.cap.where': 'flag'})


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


def test_fixing_a_binary_makes_the_program_continuous():
    spec = _fixed(BASE, 'cap', **{'variables.cap.domain': 'binary', 'variables.cap.bounds': {}})
    assert {v.domain for v in spec.program.variables.values()} == {'continuous'}, (
        'the only integer decision is supplied now'
    )


@pytest.mark.parametrize(
    ('patch', 'holds'),
    [
        pytest.param({}, 'cap >= 0.0 AND cap <= cap_max', id='a-number-and-a-parameter'),
        pytest.param(
            {'variables.cap.domain': 'binary', 'variables.cap.bounds': {}}, 'cap >= 0 AND cap <= 1', id='a-binary'
        ),
        pytest.param(
            {'variables.cap.domain': 'binary', 'variables.cap.bounds': {'lower': 0, 'upper': 1}},
            'cap >= 0 AND cap <= 1',
            id='a-binary-whose-bounds-restate-its-domain',
        ),
    ],
)
def test_the_bounds_become_an_assumption_on_the_supplied_numbers(patch, holds):
    written = _fixed(BASE, 'cap', **patch).to_dict()['assumptions']['cap_within_bounds']
    assert written['holds'] == holds


def test_an_assumption_the_bounds_would_overwrite_is_refused():
    with pytest.raises(LanguageError, match="the bounds of 'cap' become 'cap_within_bounds', which the spec already"):
        _fixed(BASE, 'cap', assumptions={'cap_within_bounds': {'holds': 'cap_max >= 0'}})


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


def test_fixing_two_masked_variables_together_is_fixing_them_one_at_a_time():
    """Each parameter keeps its own variable's reading, so no row's `where:` has two masks to merge."""
    spec = schema_of(
        MASKED,
        **{
            'parameters.flag2': {'dims': ['g'], 'dtype': 'bool'},
            'variables.spare': {'dims': ['g'], 'bounds': {'lower': 0}, 'where': 'flag2'},
            'constraints.within.expression': 'p <= cap + spare',
        },
    )
    together = spec.fix('cap', 'spare')
    assert {name: together.program.parameters[name].missing for name in ('cap', 'spare')} == {
        'cap': 'absent',
        'spare': 'absent',
    }, 'each masked variable is absent outside its own mask'
    assert together.to_dict() == spec.fix('cap').fix('spare').to_dict()


# ---------------------------------------------------------------------------
# a masked variable: where it did not exist, its parameter has no row
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('model', 'patch', 'missing'),
    [
        pytest.param(BASE, {}, 'refused', id='a-variable-at-every-coordinate-needs-every-row'),
        pytest.param(MASKED, {}, 'absent', id='a-masked-variable-is-absent-outside-its-mask'),
        pytest.param(MASKED, {'variables.cap.missing': 'neutral'}, 'neutral', id='a-neutral-variable-still-reads-zero'),
    ],
)
def test_the_parameter_reads_a_missing_row_as_the_variable_read_its_mask(model, patch, missing):
    assert _fixed(model, 'cap', **patch).program.parameters['cap'].missing == missing


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({}, id='pointwise'),
        pytest.param({'constraints.within.where': 'c > 0'}, id='under-another-mask'),
        pytest.param({'constraints.within.where': 'flag'}, id='under-its-own-mask'),
        pytest.param(
            {'constraints.within': {'dims': [], 'expression': 'sum(p - cap, over=g) <= 0'}}, id='inside-a-sum'
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
            id='in-a-case',
        ),
    ],
)
def test_every_read_keeps_its_meaning_and_no_row_changes(patch):
    """A parameter read `0` where the variable had been absent, so a read outside a sum took the variable's mask
    into its row, and a read in a case was refused. Absent where the variable was, the parameter means what the
    variable meant at every read, and the rows stay as the file wrote them."""
    written = schema_of(MASKED, **patch).to_dict()['constraints']['within'].get('where')
    fixed = _fixed(MASKED, 'cap', **patch)
    assert fixed.to_dict()['constraints']['within'].get('where') == written
    assert fixed.program.parameters['cap'].missing == 'absent'


def test_the_pypsa_capacities_are_fixed_without_changing_a_row():
    """Each capacity keeps its variable's `missing:`, so no constraint gains a mask; what only decided capacity
    moves to assumptions, and only the risk measure still shares a column across snapshots."""
    spec = schema_of(EXAMPLES / 'pypsa.yaml')
    names = [name for name in spec.program.variables if name.endswith(('_nom_ext', '_n_mod'))]
    fixed = spec.fix(*names)
    masks = {name: row.where for name, row in spec.program.constraints.items()}
    assert [name for name, row in fixed.program.constraints.items() if row.where != masks[name]] == [], (
        'no constraint gained a where'
    )
    assert fixed.program.separability['snapshot'].linking_columns == ('CVaR_a', 'CVaR_theta', 'CVaR'), (
        'the risk measure is taken over every snapshot, and nothing else links two'
    )


# ---------------------------------------------------------------------------
# refused, with the reason named
# ---------------------------------------------------------------------------


def test_a_read_through_a_shift_is_refused_by_the_language():
    """A shift over an expression with no variable needs `edge=`, so the fixed spec does not load, and the reload
    names the rewrite."""
    with pytest.raises(SchemaError, match=r'shift\(\) over a variable-free expression'):
        _fixed(MASKED, 'cap', **{'constraints.within.expression': 'p <= shift(cap, along=g, offset=1)'})


@pytest.mark.parametrize(
    ('names', 'says'),
    [
        pytest.param(('capp',), "'capp' is not a variable of this spec. Did you mean 'cap'", id='a-near-miss'),
        pytest.param(('c',), "'c' is not a variable", id='a-parameter'),
        pytest.param(('cap', 'cap'), "'cap' is given 2 times", id='twice'),
        pytest.param(('q',), "'q' is a given variable, which another file declares", id='a-given-variable'),
    ],
)
def test_a_name_that_is_not_a_variable_is_refused(names, says):
    with pytest.raises(SchemaError, match=says):
        _fixed(BASE, *names, given={'variables': {'q': {'dims': ['g']}}})


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
    assert sorted(subproblem.constraints) == ['balance', 'capacity']


def test_a_variable_a_curve_names_is_fixed_after_the_expansion():
    spec = schema_of(EXAMPLES / 'piecewise.yaml')
    with pytest.raises(LanguageError, match="'dispatch' stands in curve 'cost_curve'"):
        spec.fix('dispatch')
    assert 'dispatch' in spec.expand().fix('dispatch').program.parameters, 'written out, the curve is rows that read it'
