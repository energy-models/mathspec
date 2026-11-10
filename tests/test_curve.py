# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`curve(x=, y=)` in a constraint, and the `breakpoints:` parameter it reads.

A constraint with a curve term loads as the `piecewise:` entry it states, so
every claim here compares it with that entry written out by hand.
"""

from __future__ import annotations

import pytest

from mathspec import to_spec
from mathspec.errors import LanguageError
from tests.fixtures import raw_of, varied

CURVE_YAML = """
dimensions:
  generator: {}
  snapshot: {dtype: int, ordered: true}
parameters:
  fuel_curve: {dims: [generator], breakpoints: p}
  load: {dims: [snapshot]}
variables:
  p: {dims: [snapshot, generator], bounds: {lower: 0}}
  fuel: {dims: [snapshot, generator], bounds: {lower: 0}}
  running: {dims: [snapshot, generator], domain: binary}
constraints:
  balance:
    dims: [snapshot]
    expression: sum(p, over=generator) == load
  fuel_use:
    dims: [snapshot, generator]
    expression: fuel == curve(x=p, y=fuel_curve)
objective:
  sense: minimize
  expression: sum(fuel)
"""
CURVE = raw_of(CURVE_YAML)

#: The same spec with the curve written as the `piecewise:` entry it loads as, over plain names for the two the
#: parameter brings: `fuel_curve_breakpoint` for `fuel_curve.breakpoint`, `fuel_curve_p` for `fuel_curve.p`.
BY_HAND = varied(
    CURVE,
    **{
        'dimensions.fuel_curve_breakpoint': {'dtype': 'int', 'ordered': True},
        'parameters.fuel_curve': {'dims': ['generator', 'fuel_curve_breakpoint'], 'missing': 'absent'},
        'parameters.fuel_curve_p': {'dims': ['generator', 'fuel_curve_breakpoint'], 'missing': 'absent'},
        'piecewise.fuel_use': {
            'along': 'fuel_curve_breakpoint',
            'dims': ['snapshot', 'generator'],
            'where': 'fuel_curve_p',
            'links': {'x': ['p', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve']},
        },
    },
)
del BY_HAND['constraints']['fuel_use']


def _plain(loaded: object) -> str:
    """*loaded* as text, with each dotted name of `fuel_curve` spelt as `BY_HAND` declares it."""
    return repr(loaded).replace('fuel_curve.', 'fuel_curve_')


def _pair(expression: str, links: dict[str, list[str]], **entry: str) -> tuple[dict, dict]:
    """The curve spec with *expression* in `fuel_use`, and the hand-written entry with *links* and *entry*."""
    curve = varied(CURVE, **{'constraints.fuel_use.expression': expression})
    by_hand = varied(
        BY_HAND, **{'piecewise.fuel_use.links': links}, **{f'piecewise.fuel_use.{k}': v for k, v in entry.items()}
    )
    return curve, by_hand


@pytest.mark.parametrize(
    ('expression', 'links', 'entry'),
    [
        pytest.param(
            'fuel == curve(x=p, y=fuel_curve)',
            {'x': ['p', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve']},
            {},
            id='pinned',
        ),
        pytest.param(
            "fuel >= curve(x=p, y=fuel_curve, method='sos2')",
            {'x': ['p', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve', '>=']},
            {'method': 'sos2'},
            id='bounded-sos2',
        ),
        pytest.param(
            "fuel >= curve(x=p, y=fuel_curve, method='lp')",
            {'x': ['p', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve', '>=']},
            {'method': 'lp'},
            id='lp',
        ),
        pytest.param(
            "fuel <= curve(x=p, y=fuel_curve, method='convex')",
            {'x': ['p', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve', '<=']},
            {'method': 'convex'},
            id='convex',
        ),
        pytest.param(
            "fuel >= curve(x=p, y=fuel_curve, active=running, method='incremental')",
            {'x': ['p', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve', '>=']},
            {'method': 'incremental', 'activity': 'running'},
            id='gated-incremental',
        ),
        pytest.param(
            'curve(x=p, y=fuel_curve) <= fuel',
            {'x': ['p', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve', '>=']},
            {},
            id='curve-on-the-left-flips-the-sign',
        ),
        pytest.param(
            'fuel >= curve(x=p, y=fuel_curve) + 5',
            {'x': ['p', 'fuel_curve_p'], 'y': ['fuel - 5', 'fuel_curve', '>=']},
            {},
            id='a-term-beside-the-curve-moves-across',
        ),
        pytest.param(
            '-curve(x=p, y=fuel_curve) >= -fuel',
            {'x': ['p', 'fuel_curve_p'], 'y': ['-(-fuel)', 'fuel_curve', '>=']},
            {},
            id='a-subtracted-curve-negates-the-rest',
        ),
        pytest.param(
            'fuel == curve(x=2 * p - 1, y=fuel_curve)',
            {'x': ['(2 * p) - 1', 'fuel_curve_p'], 'y': ['fuel', 'fuel_curve']},
            {},
            id='an-affine-x',
        ),
    ],
)
def test_a_curve_lowers_and_expands_as_the_piecewise_entry_it_states(expression, links, entry):
    curve, by_hand = (to_spec(raw) for raw in _pair(expression, links, **entry))
    (ours,), (theirs,) = curve.program.piecewise.values(), by_hand.program.piecewise.values()
    assert _plain((ours.links, ours.where, ours.activity)) == repr((theirs.links, theirs.where, theirs.activity)), (
        'the curve term is the entry with links x and y, over the rows of its parameter'
    )
    assert ours.from_curve and not theirs.from_curve, 'only the constraint wrote a curve term'
    expanded, written = curve.expand(), by_hand.expand()
    assert _plain(expanded.program.constraints) == repr(written.program.constraints), 'both expand to the same rows'
    assert _plain(expanded.program.variables) == repr(written.program.variables), 'both expand to the same variables'


def test_a_breakpoints_parameter_brings_its_dimension_and_its_x_values():
    """A tool attaches the rows of `fuel_curve` as two tables over its breakpoints, numbered in order of x."""
    program = to_spec(CURVE).program
    dimension = program.dimensions['fuel_curve.breakpoint']
    assert (dimension.dtype, dimension.ordered) == ('int', True), 'the breakpoints are numbered, in order'
    assert program.parameters['fuel_curve'].dims == ('fuel_curve.breakpoint', 'generator')
    assert program.parameters['fuel_curve.p'].dims == ('fuel_curve.breakpoint', 'generator')
    assert {program.parameters[n].missing for n in ('fuel_curve', 'fuel_curve.p')} == {'absent'}, (
        'a curve stops where its rows stop'
    )


def test_the_file_keeps_its_constraint_and_its_parameter_as_written():
    spec = to_spec(CURVE)
    assert to_spec(spec.to_yaml()) == spec, 'the round trip writes the curve term back'
    assert 'curve(x=p, y=fuel_curve)' in spec.to_yaml(canonical=True)
    assert 'fuel_use' not in spec.program.constraints, 'the program carries the curve as a curve'
    assert {'fuel_use_x', 'fuel_use_y'} <= set(spec.expand().constraints), 'a row per link, named after it'


def test_a_condition_reads_the_x_values_and_the_breakpoints_by_a_dot():
    spec = to_spec(
        varied(
            CURVE,
            **{'conditions.has_curve': 'count(fuel_curve.p, over=fuel_curve.breakpoint) > 0'},
            **{'constraints.fuel_use.where': 'has_curve'},
        )
    )
    assert spec.program.conditions['has_curve'].dims == ('generator',)


@pytest.mark.parametrize(
    ('patch', 'message'),
    [
        pytest.param(
            {'constraints.fuel_use.expression': 'fuel == curve(x=p, y=fuel_curve) + curve(x=p, y=fuel_curve)'},
            "Constraint 'fuel_use': it has 2 curve(...) terms, and a constraint reads one curve. Write one "
            'constraint per curve, each with its own variable.',
            id='two-curves-in-one-constraint',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': 'fuel == 2 * curve(x=p, y=fuel_curve)'},
            "Constraint 'fuel_use': curve(...) stands inside another term, and the curve is read as one term of "
            'one side, added or subtracted. Move the other operations to the other side, or onto a variable of '
            'their own.',
            id='a-curve-inside-a-product',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': 'fuel == curve(p, y=fuel_curve)'},
            "Constraint 'fuel_use': curve(...) takes a positional argument, and it takes keywords only. Write "
            "curve(x=<expression>, y=<parameter>[, active=<variable>][, method='<method>']).",
            id='a-positional-argument',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': 'fuel == curve(x=p, y=fuel_curve, gate=running)'},
            "Constraint 'fuel_use': curve(...) takes gate=, and it takes keywords only.",
            id='an-unknown-keyword',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': 'fuel == curve(x=p)'},
            "Constraint 'fuel_use': curve(...) has no y=.",
            id='no-y',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': 'fuel == curve(x=p, y=load)'},
            "Constraint 'fuel_use': curve(y=load) reads a parameter declared with breakpoints: <axis>, and load "
            'is not one. Declare breakpoints: <axis> on the parameter, so that its rows are the breakpoints of a '
            'curve.',
            id='y-without-breakpoints',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': "fuel == curve(x=p, y=fuel_curve, method='auto')"},
            "Constraint 'fuel_use': curve(method='auto') is not a method. Write one of 'adjacency', 'sos2', "
            "'incremental', 'convex', 'lp'.",
            id='an-unknown-method',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': "fuel == curve(x=p, y=fuel_curve, method='lp')"},
            "Constraint 'fuel_use': curve(method='lp') states the curve as its segment lines, which bound one side "
            'of it, and the constraint is ==. Write <= or >=, or another method.',
            id='lp-pinned',
        ),
        pytest.param(
            {'constraints.fuel_use.expression': "fuel >= curve(x=p, y=fuel_curve, active=running, method='lp')"},
            "Constraint 'fuel_use': curve(method='lp') takes no active=, because it states no weights for a gate "
            "to switch. Delete active=, or write method='incremental'.",
            id='lp-gated',
        ),
        pytest.param(
            {'expressions.fuel_use_value': 'curve(x=p, y=fuel_curve)'},
            "Named expression 'fuel_use_value': curve(...) is a term of a constraint, which states the curve as "
            'rows, and it stands here outside one. Declare a variable v, write v == curve(x=<expression>, '
            "y=<parameter>[, active=<variable>][, method='<method>']) under constraints:, and read v here.",
            id='a-curve-in-a-named-expression',
        ),
        pytest.param(
            {'objective.expression': 'sum(curve(x=p, y=fuel_curve))'},
            'The objective: curve(...) is a term of a constraint',
            id='a-curve-in-the-objective',
        ),
        pytest.param(
            {'parameters.fuel_curve.missing': 'absent'},
            'breakpoints: p with missing: absent. Each curve runs over the rows its data has, so a row past the last '
            'breakpoint is absent. Delete missing:.',
            id='a-missing-value-on-a-curve',
        ),
        pytest.param(
            {'parameters.fuel_curve.dtype': 'bool'},
            'breakpoints: p on a bool parameter, and a curve is numbers. Declare dtype: float.',
            id='a-curve-of-labels',
        ),
        pytest.param(
            {'parameters.fuel_curve.breakpoints': '1p'},
            "breakpoints: '1p' is not a name.",
            id='an-axis-that-is-not-a-name',
        ),
        pytest.param(
            {'parameters.fuel_curve.breakpoints': 'breakpoint'},
            'breakpoints: breakpoint names the x axis after the dimension the curve brings, '
            '<parameter>.breakpoint. Name the axis after what its x values are, such as p.',
            id='an-axis-named-breakpoint',
        ),
        pytest.param(
            {'conditions.has_curve': 'fuel_curve.power > 0'},
            "conditions.has_curve: 'fuel_curve.power' is not part of the curve 'fuel_curve'. Write 'fuel_curve.p' "
            "for its x values, or 'fuel_curve.breakpoint' for its breakpoints.",
            id='a-dot-past-the-axis',
        ),
        pytest.param(
            {'objective.expression': 'sum(load.p * fuel)'},
            "objective.expression: 'load.p' reads part of a curve, and 'load' is no parameter with breakpoints:. "
            "Declare breakpoints: <axis> on parameter 'load', and write 'load.<axis>' or 'load.breakpoint'.",
            id='a-dot-on-a-parameter-without-breakpoints',
        ),
        pytest.param(
            {'conditions.has_curve': 'count(fuel_curve_p, over=generator) > 0'},
            "'fuel_curve_p' not found.",
            id='the-x-values-without-the-dot',
        ),
        pytest.param(
            {'variables.fuel.dims': ['snapshot', 'generator', 'fuel_curve_breakpoint']},
            "'fuel_curve_breakpoint'",
            id='the-breakpoints-without-the-dot',
        ),
        pytest.param(
            {
                'piecewise.fuel_use': {
                    'along': 'snapshot',
                    'dims': ['generator'],
                    'links': {'a': ['sum(p, over=snapshot)', 'load'], 'b': ['sum(fuel, over=snapshot)', 'load']},
                }
            },
            "Constraint 'fuel_use': its curve loads as piecewise 'fuel_use', and the file declares piecewise "
            "'fuel_use' already. Rename one.",
            id='a-piecewise-entry-of-the-same-name',
        ),
    ],
)
def test_a_curve_the_language_refuses_is_refused_at_load_with_its_rewrite(patch, message):
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(CURVE, **patch))
    assert message in str(caught.value)
