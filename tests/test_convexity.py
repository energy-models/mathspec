# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""What `Program.problem_class` may claim with no data.

Both convexity verdicts are proofs, so a row here that expects ``None`` is a
reason to stay silent: a false ``True`` sends a nonconvex model to a solver
that trusts it, and a false ``False`` refuses one that would have solved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mathspec import advice
from tests.fixtures import SMALL_MODEL, expanded, override, schema_of

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'

#: Every spec under examples/, which also holds symbol tables and reference data.
SPECS = sorted(p for p in EXAMPLES.rglob('*.yaml') if not {'symbols', 'references'} & set(p.parts))

BASE = override(
    SMALL_MODEL,
    variables={'x': {'dims': ['g']}, 'y': {'dims': ['g']}},
    constraints={'r': {'dims': ['g'], 'expression': 'x <= 1'}},
    objective={'sense': 'minimize', 'expression': 'sum(x, over=g)'},
)


def _class(**patch):
    return schema_of(BASE, **patch).program.problem_class


# ---------------------------------------------------------------------------
# the kind
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('patch', 'kind'),
    [
        pytest.param({}, 'LP', id='affine-throughout'),
        pytest.param({'variables.x.domain': 'integer'}, 'MILP', id='an-integer-variable'),
        pytest.param({'variables.x.domain': 'binary'}, 'MILP', id='a-binary-variable'),
        pytest.param(
            {'sos': {'s': {'variable': 'x', 'along': 'g', 'type': 1}}, 'variables.x.bounds': {'lower': 0, 'upper': 1}},
            'MILP',
            id='a-set',
        ),
        pytest.param({'objective.expression': 'sum(x * x, over=g)'}, 'QP', id='a-quadratic-objective'),
        pytest.param({'constraints.r.expression': 'x * x <= 1'}, 'QCP', id='a-quadratic-row'),
        pytest.param(
            {'constraints.r.expression': 'x * x <= 1', 'objective.expression': 'sum(x * x, over=g)'},
            'QCP',
            id='a-quadratic-row-beside-a-quadratic-objective',
        ),
        pytest.param(
            {'objective.expression': 'sum(x * x, over=g)', 'variables.y.domain': 'binary'},
            'MIQP',
            id='a-quadratic-objective-and-a-binary',
        ),
        pytest.param(
            {'constraints.r.expression': 'x * y <= 1', 'variables.y.domain': 'integer'},
            'MIQCP',
            id='a-quadratic-row-and-an-integer',
        ),
    ],
)
def test_the_kind_names_integrality_and_where_a_quadratic_stands(patch, kind):
    assert _class(**patch).kind == kind


@pytest.mark.parametrize(
    ('method', 'kind'),
    [
        pytest.param('adjacency', 'MILP', id='adjacency-writes-binaries'),
        pytest.param('sos2', 'MILP', id='sos2-writes-a-set'),
        pytest.param('convex', 'LP', id='convex-writes-rows-alone'),
        pytest.param('lp', 'LP', id='lp-writes-rows-alone'),
    ],
)
def test_a_curve_counts_as_the_rows_its_method_writes(method, kind):
    """The footprint does not count a curve still on the program, so a kind read
    off it alone called an `adjacency` curve an LP until the spec was expanded."""
    patch = {'piecewise.cost_curve.method': method}
    if method == 'lp':
        patch['piecewise.cost_curve.links'] = [['dispatch', 'bp_x'], ['op_cost', 'bp_y', '>=']]
    spec = schema_of(EXAMPLES / 'piecewise.yaml', **patch)
    assert spec.program.problem_class.kind == kind
    assert expanded(spec).program.problem_class.kind == kind, 'the expansion agrees with the block it wrote out'


@pytest.mark.parametrize('path', SPECS, ids=lambda p: str(p.relative_to(EXAMPLES)))
def test_every_example_answers_as_its_expansion_does(path):
    spec = schema_of(path)
    before, after = spec.program.problem_class, expanded(spec).program.problem_class
    assert (before.kind, before.convex) == (after.kind, after.convex)


def test_an_affine_program_is_convex_with_nothing_to_report():
    verdict = _class(**{'variables.x.domain': 'binary'})
    assert verdict.convex is True, 'the relaxation of an affine program is convex'
    assert dict(verdict.nonconvex) == {}, 'no quadratic term, so nothing is nonconvex'
    assert dict(verdict.undecided) == {}, 'no quadratic term, so nothing waits on data'


# ---------------------------------------------------------------------------
# convex, for any data the assumptions admit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({'objective.expression': 'sum(x * x, over=g)'}, id='a-square-minimized'),
        pytest.param({'objective.expression': 'sum(3 * x * x + y * y, over=g)'}, id='a-sum-of-squares'),
        pytest.param(
            {'objective.expression': '-sum(x * x, over=g)', 'objective.sense': 'maximize'},
            id='a-negated-square-maximized',
        ),
        pytest.param({'objective.expression': 'sum(x * x / 2, over=g)'}, id='a-literal-divisor'),
        pytest.param(
            {'objective.expression': 'sum(c * x * x, over=g)', 'assumptions': {'a': {'holds': 'c >= 0'}}},
            id='a-coefficient-an-assumption-bounds',
        ),
        pytest.param(
            {'objective.expression': 'sum(c * x * x, over=g)', 'assumptions': {'a': {'holds': '0 <= c'}}},
            id='an-assumption-with-the-number-on-the-left',
        ),
        pytest.param(
            {'objective.expression': 'sum(x * x / c, over=g)', 'assumptions': {'a': {'holds': 'c > 0'}}},
            id='a-divisor-an-assumption-bounds',
        ),
        pytest.param(
            {'objective.expression': 'sum(c * x * x, over=g)', 'assumptions': {'a': {'holds': 'c > 0 AND k > 1'}}},
            id='one-conjunct-of-an-assumption',
        ),
        pytest.param({'objective.expression': 'sum((c * x) * (c * x), over=g)'}, id='identical-factors-square-c'),
        pytest.param(
            {'objective.expression': 'sum(shift(x, along=g, offset=1) * shift(x, along=g, offset=1), over=g)'},
            id='a-square-of-a-shift',
        ),
        pytest.param({'constraints.r.expression': 'x * x + y * y <= 4'}, id='a-sum-of-squares-at-most'),
        pytest.param({'constraints.r.expression': '4 >= x * x'}, id='a-square-on-the-right-of-at-least'),
        pytest.param({'constraints.r.expression': '-(x * x) >= -4'}, id='a-negated-square-at-least'),
    ],
)
def test_a_convex_quadratic_is_proven_convex(patch):
    verdict = _class(**patch)
    assert verdict.convex is True, f'undecided: {dict(verdict.undecided)}; nonconvex: {dict(verdict.nonconvex)}'


# ---------------------------------------------------------------------------
# nonconvex, for any data that builds the term
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('patch', 'label', 'says'),
    [
        pytest.param(
            {'objective.expression': 'sum(-2 * x * x, over=g)'}, 'objective', 'negative', id='a-square-minimized-down'
        ),
        pytest.param(
            {'objective.expression': 'sum(x * x, over=g)', 'objective.sense': 'maximize'},
            'objective',
            'positive',
            id='a-square-maximized',
        ),
        pytest.param(
            {'objective.expression': 'sum(x * y, over=g)'}, 'objective', 'indefinite', id='a-bilinear-objective'
        ),
        pytest.param(
            {'objective.expression': 'sum(c * x * y, over=g)', 'assumptions': {'a': {'holds': 'c < 0'}}},
            'objective',
            'indefinite',
            id='a-bilinear-objective-with-a-signed-coefficient',
        ),
        pytest.param({'constraints.r.expression': 'x * x >= 4'}, "constraint 'r'", 'positive', id='a-square-at-least'),
        pytest.param({'constraints.r.expression': 'x * y <= 4'}, "constraint 'r'", 'indefinite', id='a-bilinear-row'),
        pytest.param(
            {'constraints.r.expression': 'x * x == 4'}, "constraint 'r'", 'equality', id='a-square-in-an-equality'
        ),
    ],
)
def test_a_nonconvex_quadratic_is_named_with_the_term_that_shows_it(patch, label, says):
    verdict = _class(**patch)
    assert verdict.convex is False
    assert list(verdict.nonconvex) == [label], 'the one declaration the term stands in'
    assert says in verdict.nonconvex[label]


# ---------------------------------------------------------------------------
# undecided: only data can say
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('patch', 'says'),
    [
        pytest.param({'objective.expression': 'sum(c * x * x, over=g)'}, "bounding 'c'", id='an-unsigned-coefficient'),
        pytest.param(
            {
                'objective.expression': 'sum(c * x * x, over=g)',
                'assumptions': {'a': {'holds': 'c >= 0', 'where': 'k > 0'}},
            },
            "bounding 'c'",
            id='an-assumption-under-a-where-leaves-rows-unsigned',
        ),
        pytest.param(
            {'objective.expression': 'sum(c * x * y, over=g)'},
            'cross term',
            id='a-bilinear-with-a-coefficient-maybe-zero',
        ),
        pytest.param(
            {'objective.expression': 'sum(x * x + x * y + y * y, over=g)'},
            'cross term',
            id='a-cross-term-beside-squares-of-both',
        ),
        pytest.param(
            {'objective.expression': 'sum(x * shift(x, along=g, offset=1), over=g)'},
            'cross term',
            id='a-variable-times-its-own-shift',
        ),
        pytest.param(
            {'objective.expression': 'sum(x * x, over=g) - sum(x * x, over=g)'},
            'other sign',
            id='squares-of-both-signs',
        ),
        pytest.param(
            {'objective.expression': 'sum(c * x * x, over=g)', 'assumptions': {'a': {'holds': 'c <= 0'}}},
            'may be negative',
            id='a-coefficient-that-may-be-zero-or-negative',
        ),
        pytest.param(
            {'constraints.r.expression': 'c * x * x == 4'},
            'equality',
            id='an-equality-whose-coefficient-may-be-zero',
        ),
    ],
)
def test_a_quadratic_the_data_decides_claims_nothing(patch, says):
    verdict = _class(**patch)
    assert verdict.convex is None, f'nonconvex: {dict(verdict.nonconvex)}'
    assert dict(verdict.nonconvex) == {}, 'nothing is proven nonconvex'
    (reason,) = verdict.undecided.values()
    assert says in reason


# ---------------------------------------------------------------------------
# the one line a program prints as
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('path', 'line'),
    [
        pytest.param(
            'dispatch.yaml',
            '<Program LP: 2 dimensions, 3 parameters, 1 variable, 1 constraint, minimize>',
            id='an-lp-says-nothing-of-convexity',
        ),
        pytest.param(
            'pypsa_quadratic.yaml',
            '<Program QP, convex: 6 dimensions, 13 parameters, 2 variables, 5 constraints, minimize>',
            id='a-quadratic-kind-carries-its-verdict',
        ),
        pytest.param(
            'piecewise.yaml',
            '<Program LP: 3 dimensions, 4 parameters, 2 variables, 1 constraint, 1 curve, minimize>',
            id='a-curve-is-counted-where-there-is-one',
        ),
    ],
)
def test_a_program_prints_as_one_line_naming_its_class(path, line):
    program = schema_of(EXAMPLES / path).program
    assert repr(program) == line
    assert str(program) == line, 'str falls back to the same line'


def test_an_undecided_verdict_is_named_in_the_line():
    program = schema_of(BASE, **{'objective.expression': 'sum(c * x * x, over=g)'}).program
    assert repr(program).startswith('<Program QP, convexity undecided: ')


def test_a_program_with_no_objective_says_so():
    program = schema_of(BASE, objective=None).program
    assert repr(program).endswith(', no objective>')


# ---------------------------------------------------------------------------
# the advice: a sign to state, where stating it is the whole fix
# ---------------------------------------------------------------------------


def _convexity_notes(**patch):
    return [note for note in advice(schema_of(BASE, **patch)) if note.kind == 'convexity']


@pytest.mark.parametrize(
    ('patch', 'subject', 'holds'),
    [
        pytest.param({'objective.expression': 'sum(c * x * x, over=g)'}, 'objective', 'c >= 0', id='minimized'),
        pytest.param(
            {'objective.expression': 'sum(c * x * x, over=g)', 'objective.sense': 'maximize'},
            'objective',
            'c <= 0',
            id='maximized',
        ),
        pytest.param(
            {'objective.expression': 'sum(c * k * x * x, over=g)'}, 'objective', 'c >= 0 AND k >= 0', id='two-at-once'
        ),
        pytest.param({'constraints.r.expression': 'c * x * x <= 1'}, 'r', 'c >= 0', id='an-at-most-row'),
        pytest.param({'constraints.r.expression': 'c * x * x >= 1'}, 'r', 'c <= 0', id='an-at-least-row'),
    ],
)
def test_the_note_names_the_assumption_that_decides_it(patch, subject, holds):
    (note,) = _convexity_notes(**patch)
    assert note.subject == subject
    assert f'holds "{holds}"' in str(note)


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({'objective.expression': 'sum(c * x * x, over=g)'}, id='minimized'),
        pytest.param({'objective.expression': 'sum(c * k * x * x, over=g)'}, id='two-at-once'),
        pytest.param({'constraints.r.expression': 'c * x * x >= 1'}, id='an-at-least-row'),
    ],
)
def test_stating_what_the_note_says_proves_it_convex(patch):
    """The note is a rewrite, so applying it is the test: the file it describes is convex and draws no note."""
    (note,) = _convexity_notes(**patch)
    holds = str(note).rpartition('holds "')[2].removesuffix('".')
    fixed = {**patch, 'assumptions': {'stated': {'holds': holds}}}
    assert schema_of(BASE, **fixed).program.problem_class.convex is True
    assert _convexity_notes(**fixed) == [], 'the note goes once its assumption is stated'


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({'objective.expression': 'sum(x * x, over=g)'}, id='convex'),
        pytest.param({'objective.expression': 'sum(x * y, over=g)'}, id='nonconvex-is-a-model-the-author-may-mean'),
        pytest.param({'objective.expression': 'sum(c * x * y, over=g)'}, id='a-cross-term-no-sign-decides'),
        pytest.param(
            {'objective.expression': 'sum(c * x * x, over=g) - sum(c * y * y, over=g)'},
            id='a-sign-that-makes-one-term-convex-makes-the-other-not',
        ),
        pytest.param({'constraints.r.expression': 'c * x * x == 4'}, id='an-equality-no-sign-decides'),
        pytest.param({}, id='affine'),
    ],
)
def test_no_note_where_no_stated_sign_is_the_fix(patch):
    assert _convexity_notes(**patch) == []
