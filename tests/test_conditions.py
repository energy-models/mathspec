# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A named condition is written once under ``conditions:`` and read by name in any other condition (#803).

A use stands as a `ConditionReference` with the condition under it, so every question
asked of the name is asked of the condition, and the typesetter still prints the
name. Another file reads a named condition under ``given: conditions:`` as the boolean
data it is to that file, and `merge` folds the reading into the definition.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from mathspec import advice, merge, override, to_spec, typeset, typeset_line
from mathspec._typesetting import FORMATS
from mathspec.errors import LanguageError
from mathspec.program import ConditionReference, Mask, ParameterDefined, VariableDefined
from tests.fixtures import SMALL_MODEL, varied

#: A unit stands in a period between its build year and its retirement, and
#: two families of rows read that test: the core's capacity and a ramp.
DIMS: dict[str, Any] = {'period': {'dtype': 'int', 'ordered': True}, 'generator': {'dtype': 'str'}}
FRAME = ['period', 'generator']
STANDS = 'build_year <= period_year AND period_year < build_year + lifetime'

CORE: dict[str, Any] = {
    'dimensions': DIMS,
    'parameters': {
        'build_year': {'dims': ['generator']},
        'lifetime': {'dims': ['generator']},
        'period_year': {'dims': ['period']},
        'p_nom': {'dims': ['generator']},
    },
    'conditions': {'stands': {'where': STANDS, 'description': 'the unit stands in this period'}},
    'variables': {'p': {'dims': FRAME, 'where': 'stands', 'bounds': {'lower': 0}}},
    'constraints': {'cap': {'dims': FRAME, 'where': 'stands', 'expression': 'p <= p_nom'}},
    'objective': {'sense': 'minimize', 'expression': 'sum(p, over=[period, generator])'},
}

RAMPING: dict[str, Any] = {
    'dimensions': DIMS,
    'given': {'variables': {'p': {'dims': FRAME}}, 'conditions': {'stands': {'dims': FRAME}}},
    'parameters': {'ramp': {'dims': ['generator']}},
    'constraints': {
        'ramp_up': {
            'dims': FRAME,
            'where': 'stands AND shift(stands, along=period, offset=1)',
            'expression': 'p - shift(p, along=period, offset=1) <= ramp',
        }
    },
}


def test_a_named_condition_stands_where_its_name_is_written_with_its_condition_under_it():
    program = to_spec(CORE).program
    where = program.constraints['cap'].where
    assert where is not None and isinstance(where.root, ConditionReference), 'the use keeps the name the file wrote'
    assert where.root.body == program.conditions['stands'].where.root, 'and carries the condition the entry declares'
    assert program.conditions['stands'].dims == ('period', 'generator')
    assert where.names_read == {'build_year', 'lifetime', 'period_year'}, 'a mask reads what its condition reads'
    assert where.dims == {'period', 'generator'}


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({'constraints.cap.where': 'NOT stands'}, id='under-a-connective'),
        pytest.param({'constraints.cap.where': 'stands AND shift(stands, along=period, offset=1)'}, id='in-shift'),
        pytest.param(
            {'assumptions.lives': {'holds': 'lifetime > 0', 'where': 'stands'}}, id='as-an-assumption-s-where'
        ),
        pytest.param({'assumptions.ever': 'count(stands, over=period) >= 1'}, id='in-count'),
        pytest.param(
            {
                'expressions.share': {
                    'dims': FRAME,
                    'cases': {'standing': {'when': 'stands', 'expression': 'p_nom'}},
                    'otherwise': 0,
                }
            },
            id='as-a-when',
        ),
        pytest.param(
            {'conditions.old': 'stands AND lifetime > 30', 'constraints.cap.where': 'old'}, id='in-another-mask'
        ),
        pytest.param(
            {'expressions.half': 'p_nom / 2', 'conditions.big': 'half > 10', 'constraints.cap.where': 'big'},
            id='reading-a-data-only-expression',
        ),
        pytest.param({'conditions.stands': STANDS}, id='the-one-line-form'),
    ],
)
def test_a_named_condition_is_read_wherever_a_where_string_is(patch):
    spec = to_spec(varied(CORE, **patch))
    assert to_spec(spec.to_yaml()).program == spec.program, 'the file reads back to the same program'


def test_the_one_line_form_writes_back_as_written():
    spec = to_spec(varied(CORE, **{'conditions.stands': STANDS}))
    assert spec.to_dict()['conditions'] == {'stands': STANDS}, 'a mask with no words is one where string'


def test_a_named_condition_declares_no_frame():
    """A declared frame wider than the condition printed a use over an index no quantifier binds.

    ``young`` over ``[period, generator]`` read only ``lifetime``. A use over
    ``[generator]`` loaded, and every format printed ``young`` with a period
    index under a quantifier over generators alone. The condition gives a mask
    its frame, so the closed schema now refuses ``dims:`` on a mask.
    """
    young = {
        'conditions.young': {'dims': FRAME, 'where': 'lifetime > 10'},
        'constraints.total': {'dims': ['generator'], 'where': 'young', 'expression': 'sum(p, over=period) <= p_nom'},
    }
    with pytest.raises(LanguageError, match=r"conditions\.young: unknown key 'dims' in a condition entry"):
        to_spec(varied(CORE, **young))


def test_a_variable_that_asks_through_a_named_condition_whether_it_exists_is_refused():
    """The where resolver refused the bare name only: a mask's condition is read under the mask's own name."""
    with pytest.raises(
        LanguageError, match=r"variable 'p' asks whether it exists in its own `where:`, through a named condition"
    ):
        to_spec(varied(CORE, **{'conditions.live': 'p', 'variables.p.where': 'live'}))


def test_a_named_condition_may_ask_whether_another_variable_exists():
    spec = to_spec(varied(CORE, **{'conditions.dispatched': 'p', 'constraints.cap.where': 'dispatched'}))
    where = spec.program.constraints['cap'].where
    assert where is not None and VariableDefined('p', ('period', 'generator')) in where.atoms


@pytest.mark.parametrize(
    ('patch', 'says'),
    [
        pytest.param({'conditions': {'a': 'b', 'b': 'a'}}, 'circular condition reference: a -> b -> a', id='a-cycle'),
        pytest.param({'conditions': {'a': 'a'}}, 'circular condition reference: a -> a', id='a-mask-reading-itself'),
        pytest.param({'conditions': {'a': 'True'}}, 'folds to true, so it admits every row', id='always-true'),
        pytest.param({'conditions': {'a': 'NOT True'}}, 'folds to false, so it admits no row', id='always-false'),
        pytest.param(
            {'conditions': {'a': 'c > 0'}, 'expressions.e': 'c * a'},
            "'a' is a named condition, which is true or false where it is read, and not a number",
            id='a-mask-in-arithmetic',
        ),
        pytest.param(
            {'conditions': {'a': 'c > 0'}, 'variables.p.where': 'a == 1'},
            "'a' is a named condition, which is true or false where it is read, and not a number",
            id='a-mask-compared',
        ),
        pytest.param(
            {'given.conditions.m': {'dims': ['g']}, 'expressions.e': 'c * m'},
            "'m' is a named condition, which is true or false where it is read, and not a number",
            id='a-given-mask-in-arithmetic',
        ),
        pytest.param(
            {'given.expressions.ge': {'dims': ['g']}, 'conditions': {'a': 'ge > 0'}},
            "where references the given expression 'ge'",
            id='a-mask-reading-a-given-expression',
        ),
        pytest.param({'conditions': {'c': 'flag'}}, "Condition 'c' collides with the parameter", id='a-name-taken'),
        pytest.param({'conditions': {'a': 'nope'}}, "Condition 'a': 'nope' not found", id='an-unknown-name'),
        pytest.param(
            {'conditions': {'a': 'c > 0'}, 'variables.r.where': 'a'},
            "outside the declared dims ['h']",
            id='a-use-over-a-frame-the-condition-leaves',
        ),
    ],
)
def test_what_a_named_condition_may_not_be_is_refused_at_load(patch, says):
    with pytest.raises(LanguageError, match=None) as raised:
        to_spec(varied(SMALL_MODEL, **patch))
    assert says in str(raised.value), 'the refusal names the mask and what to write instead'


def test_cases_split_by_a_named_condition_are_proved_apart_through_its_condition():
    """The overlap check evaluates a when on a grid of the data it reads, and a mask's data is its condition's."""
    case = {
        'dims': ['g'],
        'cases': {'on': {'when': 'a', 'expression': 1}, 'off': {'when': 'flag', 'expression': 2}},
        'otherwise': 0,
    }
    with pytest.raises(LanguageError, match=r"cases 'on' and 'off' both claim the value where flag is true"):
        to_spec(varied(SMALL_MODEL, **{'conditions.a': 'flag', 'expressions.e': case}))
    apart = varied(case, **{'cases.off.when': 'NOT a'})
    assert to_spec(varied(SMALL_MODEL, **{'conditions.a': 'flag', 'expressions.e': apart}))


# ---------------------------------------------------------------------------
# another file's mask
# ---------------------------------------------------------------------------


def test_a_fragment_reads_another_file_s_named_condition_as_boolean_data():
    """#803's ramp read `active == 1` under `given: expressions:`, which a where may not read."""
    program = to_spec(RAMPING).program
    where = program.constraints['ramp_up'].where
    assert where is not None and ParameterDefined('stands', ('period', 'generator')) in where.atoms, (
        'alone, the reading is data the host provides'
    )
    assert sorted(program.given.conditions) == ['stands']


def test_check_notes_the_named_condition_a_fragment_reads():
    """Every other given kind had a note saying who provides it, and a given condition had none."""
    notes = {(note.kind, note.subject): note.text for note in advice(RAMPING)}
    assert "condition 'stands' is read here and declared elsewhere" in notes[('given', 'stands')]


@pytest.mark.parametrize(
    'fragments',
    [
        pytest.param([CORE, RAMPING], id='the-definer-first'),
        pytest.param([RAMPING, CORE], id='the-reader-first'),
    ],
)
def test_merge_folds_the_reading_into_the_named_condition_another_fragment_defines(fragments):
    program = merge(fragments).program
    assert not program.given, 'the reading is spent once the definer is in the composition'
    where = program.constraints['ramp_up'].where
    assert where is not None and isinstance(where.conjuncts[0], ConditionReference), (
        'the composed row reads the mask by name'
    )


@pytest.mark.parametrize(
    ('reader', 'says'),
    [
        pytest.param(
            varied(RAMPING, **{'given.conditions.stands.dims': ['generator'], 'constraints.ramp_up.where': 'stands'}),
            "reads the given condition 'stands'",
            id='a-reader-that-states-less-than-the-frame',
        ),
        pytest.param(
            varied(
                RAMPING,
                **{'given.conditions': {}, 'given.parameters.stands': {'dims': FRAME, 'dtype': 'bool'}},
            ),
            "reads 'stands' as a given parameter, where '#1' introduces it under 'conditions:'",
            id='a-mask-read-as-a-parameter',
        ),
    ],
)
def test_a_reading_the_definer_does_not_answer_is_refused(reader, says):
    with pytest.raises(LanguageError) as raised:
        merge([CORE, reader])
    assert says in str(raised.value)


def test_a_reader_that_states_a_frame_wider_than_the_named_condition_s_is_refused():
    """A reader stated a superset of the condition's dims, and the merge took it.

    A mask's frame is the dims its condition reads, which no file chooses, so
    a wider reading only defers the failure to the composed load.
    """
    definer = varied(CORE, **{'conditions.stands': 'lifetime > 0'})
    reader = varied(RAMPING, **{'constraints.ramp_up.where': 'stands'})
    with pytest.raises(LanguageError) as raised:
        merge([definer, reader])
    assert "reads the given condition 'stands' as {'dims': ['period', 'generator']}" in str(raised.value), (
        'the refusal names the frame the reader states'
    )
    assert "introduces it over ['generator']" in str(raised.value), "and the frame the definer's condition reads"


def test_two_fragments_that_define_one_named_condition_collide():
    other = {'dimensions': DIMS, 'parameters': {'retired': {'dims': ['generator'], 'dtype': 'bool'}}}
    with pytest.raises(LanguageError, match=r"fragments '#1' and '#2' both declare the condition 'stands'"):
        merge([CORE, {**other, 'conditions': {'stands': 'NOT retired'}}])


def test_a_patch_rewrites_a_named_condition_s_condition():
    laid = override(CORE, [{'conditions': {'stands': {'where': 'lifetime > 0'}}}])
    assert laid.conditions['stands'].where == 'lifetime > 0'
    assert laid.conditions['stands'].description == 'the unit stands in this period', (
        'a patch says only what it changes'
    )


# ---------------------------------------------------------------------------
# typesetting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('fmt', sorted(FORMATS))
def test_a_named_condition_prints_its_symbol_where_it_is_read_and_its_condition_once(fmt):
    printed = typeset(CORE, fmt)
    defined = typeset_line(CORE, 'stands', fmt)
    assert printed.count(FORMATS[fmt].operators['iff']) == 1, 'the condition prints once, as the definition'
    assert defined.split()[0].replace('\\_', '_').count('stands') == 1, 'the definition opens with the symbol'
    assert FORMATS[fmt].operators['iff'] in defined, 'a condition is defined with iff, not equated'
    assert 'the unit stands in this period' in printed, 'the legend carries its words'


@pytest.mark.parametrize('fmt', sorted(FORMATS))
def test_a_given_condition_prints_in_the_legend_and_no_line_of_its_own(fmt):
    assert 'a condition another file defines' in typeset(RAMPING, fmt)
    with pytest.raises(LanguageError, match=r"'stands' is a given condition, which prints no line of its own"):
        typeset_line(RAMPING, 'stands', fmt)


def test_the_fixtures_are_never_mutated():
    before = copy.deepcopy((CORE, RAMPING))
    merge([CORE, RAMPING])
    assert before == (CORE, RAMPING)


def test_a_named_condition_with_no_declared_frame_takes_the_dims_its_condition_reads():
    spec = to_spec(varied(SMALL_MODEL, **{'conditions.a': 'c > 0 AND flag'}))
    assert spec.program.conditions['a'].dims == ('g',)
    assert spec.program.conditions['a'].where == Mask(spec.program.conditions['a'].where.root), (
        'the condition is folded'
    )
