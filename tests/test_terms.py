# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A named expression several files add terms to.

A balance reads what every component puts into a bus, and a component file
says what it puts there: a named expression of its own, whose `adds_to:` names
the `given: expressions:` entry of its file it writes into. The given entry is
the read, and `adds_to:` the write. `merge` writes every term by name after
the body a fragment defines, or as the whole body where none does, and keeps
each term, so no file has to declare that the name is a sum.
"""

from __future__ import annotations

import pytest

from mathspec import advice, merge, override, to_markdown, to_spec, typeset, typeset_declaration
from mathspec.canonical import canonical_yaml
from mathspec.errors import LanguageError
from mathspec.typesetting import FORMATS
from tests.fixtures import BALANCE, BUS_DIMS, BUS_FRAME, INJECTION

#: A generator fleet: what it puts in is its term.
FLEET = {
    'dimensions': {**BUS_DIMS, 'generator': {'dtype': 'str'}},
    'relations': {'gen_bus': {'key': 'generator', 'values': 'bus'}},
    'variables': {'gen_p': {'dims': ['snapshot', 'generator'], 'bounds': {'lower': 0}}},
    'given': {'expressions': {'injection': {'dims': BUS_FRAME}}},
    'expressions': {
        'generator_injection': {
            'expression': 'sum(gen_p, over=generator, by=gen_bus[bus])',
            'description': 'what the generators put in',
            'adds_to': 'injection',
        }
    },
    'objective': {'sense': 'minimize', 'expression': 'sum(gen_p)'},
}

#: A demand, subtracting what it draws.
DEMAND = {
    'dimensions': BUS_DIMS,
    'parameters': {'load': {'dims': BUS_FRAME}},
    'given': {'expressions': {'injection': {'dims': BUS_FRAME}}},
    'expressions': {'demand_injection': {'expression': '-load', 'adds_to': 'injection'}},
}

#: A store, added in a second merge.
STORAGE = {
    'dimensions': {**BUS_DIMS, 'store': {'dtype': 'str'}},
    'relations': {'store_bus': {'key': 'store', 'values': 'bus'}},
    'variables': {'store_p': {'dims': ['snapshot', 'store']}},
    'given': {'expressions': {'injection': {'dims': BUS_FRAME}}},
    'expressions': {
        'store_injection': {'expression': 'sum(store_p, over=store, by=store_bus[bus])', 'adds_to': 'injection'}
    },
}

#: A network that defines the injection with a body of its own, its slack, and reads it.
SLACKED = {
    'dimensions': BUS_DIMS,
    'variables': {'slack': {'dims': BUS_FRAME}},
    'expressions': {'injection': {'expression': 'slack', 'description': 'the slack, and what the components add'}},
    'constraints': {'balance': {'dims': BUS_FRAME, 'expression': 'injection == 0'}},
}

#: The same network with its slack written as a term of the injection it reads.
SLACK_TERM = {
    'dimensions': BUS_DIMS,
    'variables': {'slack': {'dims': BUS_FRAME}},
    'given': {'expressions': {'injection': {'dims': BUS_FRAME, 'description': INJECTION}}},
    'expressions': {'slack_injection': {'expression': 'slack', 'adds_to': 'injection'}},
    'constraints': {'balance': {'dims': BUS_FRAME, 'expression': 'injection == 0'}},
}

#: A fleet that adds to the injection and caps it in its own math.
CAPPED = {**FLEET, 'constraints': {'capped': {'dims': BUS_FRAME, 'expression': 'injection <= 10'}}}


def _demand(target: str = 'injection', body: object = '-load', dims: list[str] = BUS_FRAME) -> dict[str, object]:
    """A demand whose `demand_injection` is *body* and adds to *target*, reading `injection` over *dims*."""
    term = {**body, 'adds_to': target} if isinstance(body, dict) else {'expression': body, 'adds_to': target}
    return {
        **DEMAND,
        'given': {'expressions': {'injection': {'dims': dims}}},
        'expressions': {'demand_injection': term},
    }


# ---------------------------------------------------------------------------
# one file
# ---------------------------------------------------------------------------


def test_a_contributor_loads_alone_and_its_term_is_its_named_expression():
    program = to_spec(DEMAND).program
    assert program.expressions['demand_injection'].adds_to == 'injection'
    assert program.given.expressions['injection'].dims == ('snapshot', 'bus'), 'the file reads what it adds to'


def test_a_term_round_trips_with_what_it_adds_to():
    written = to_spec(DEMAND).to_dict()['expressions']['demand_injection']
    assert written == {'expression': '-load', 'adds_to': 'injection'}, 'a term is written as a mapping to carry it'
    assert to_spec(to_spec(DEMAND).to_yaml()) == to_spec(DEMAND)


def test_a_term_is_read_by_the_math():
    """A sum it lands in is read by a constraint somewhere, so it is held to what the math admits."""
    assert to_spec(FLEET).program.expressions['generator_injection'].in_math


def test_a_contributor_reads_the_name_as_the_whole_sum():
    """Alone and composed the file reads one thing, so nothing has to refuse a file that adds and reads."""
    assert to_spec(CAPPED).program.constraints['capped'].dims == ('snapshot', 'bus')
    composed = merge([BALANCE, CAPPED, DEMAND])
    assert composed.constraints['capped'].expression == 'injection <= 10'
    assert composed.program.expressions['injection'].in_math, 'composed, the cap reads the sum of every term'


@pytest.mark.parametrize(
    ('spec', 'message'),
    [
        pytest.param(
            _demand(dims=['bus']),
            r"Named expression 'demand_injection': it adds to 'injection' over \['snapshot'\], which the given "
            r"entry's dims \['bus'\] do not name",
            id='a-term-wider-than-the-entry',
        ),
        pytest.param(
            _demand(body='injection - load'),
            r"Named expression 'demand_injection': it reads 'injection', the sum it adds to",
            id='a-term-reading-the-sum',
        ),
        pytest.param(
            _demand(target='injecton'),
            r"it adds to 'injecton', which this file does not read under 'given: expressions:'.*"
            r"Did you mean 'injection'\?",
            id='a-mistyped-target',
        ),
        pytest.param(
            {
                **DEMAND,
                'given': {'expressions': {'injection': {'dims': BUS_FRAME}, 'withdrawal': {'dims': BUS_FRAME}}},
                'expressions': {
                    'demand_injection': {'expression': 'withdrawal - load', 'adds_to': 'injection'},
                    'demand_withdrawal': {'expression': 'injection + load', 'adds_to': 'withdrawal'},
                },
            },
            r"Named expression 'demand_injection': it reads 'injection', the sum it adds to, through 'withdrawal'",
            id='two-terms-reading-each-other-s-sum',
        ),
        pytest.param(
            {**_demand(target='total'), 'expressions': {**_demand(target='total')['expressions'], 'total': '-load'}},
            r"it adds to 'total', which this file defines\. Write the term into the body of 'total'",
            id='a-target-this-file-defines',
        ),
        pytest.param(
            {
                **FLEET,
                'expressions': {
                    'generator_injection': {
                        'expression': 'sum(gen_p * gen_p * gen_p, over=generator)',
                        'adds_to': 'injection',
                    }
                },
            },
            r"'generator_injection'.*degree",
            id='a-term-of-degree-three',
        ),
        pytest.param(
            {**DEMAND, 'expressions': {**DEMAND['expressions'], 'injection': '0'}},
            r"Given expression 'injection' collides with the named expression",
            id='a-reading-beside-a-definition',
        ),
    ],
)
def test_what_a_term_may_not_be_is_refused_at_load(spec, message):
    with pytest.raises(LanguageError, match=message):
        to_spec(spec)


def test_a_frame_with_no_body_names_where_a_sum_is_read():
    """A sum no file defines is read under `given:`, so a bodiless entry is refused with that rewrite."""
    spec = {**BALANCE, 'given': {}, 'expressions': {'injection': {'dims': BUS_FRAME}}}
    with pytest.raises(
        LanguageError, match=r"has neither `expression:` nor `cases:`.*'given: expressions:'.*`adds_to:`"
    ):
        to_spec(spec)


def test_a_term_may_read_another_sum_its_file_adds_to():
    """A read of another sum makes no loop until that sum's term reads back."""
    spec = {
        **DEMAND,
        'given': {'expressions': {'injection': {'dims': BUS_FRAME}, 'withdrawal': {'dims': BUS_FRAME}}},
        'expressions': {
            'demand_injection': {'expression': 'withdrawal - load', 'adds_to': 'injection'},
            'demand_withdrawal': {'expression': 'load', 'adds_to': 'withdrawal'},
        },
    }
    assert to_spec(spec).program.expressions['demand_injection'].adds_to == 'injection'


def test_a_term_may_be_quadratic():
    """A term is held to what an objective or a constraint admits, since one of them reads the sum."""
    square = {
        **FLEET,
        'expressions': {
            'generator_injection': {'expression': 'sum(gen_p * gen_p, over=generator)', 'adds_to': 'injection'}
        },
    }
    assert to_spec(square).program.expressions['generator_injection'].adds_to == 'injection'


def test_the_advice_says_the_file_adds_a_term():
    (note,) = [note for note in advice(DEMAND) if note.kind == 'given']
    assert note.subject == 'injection'
    assert 'adds a term to it' in note.text
    assert 'merge()' in note.text, 'merge completes it, not a host model'


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------


def test_merging_adds_the_terms_by_name_in_the_order_given_and_keeps_them():
    composed = merge([FLEET, DEMAND, BALANCE])
    assert composed.expressions['injection'].expression == 'generator_injection + demand_injection'
    assert composed.expressions['demand_injection'].expression == '-load', 'each term stays a named expression'
    assert composed.expressions['demand_injection'].adds_to is None, 'the body now says what the term adds to'
    assert composed.program.expressions['generator_injection'].description == 'what the generators put in'
    assert not composed.given, 'every reading is folded into the definition, so the spec is fully defined'


def test_the_order_the_fragments_are_given_in_reaches_no_canonical_text():
    """The order sorts the terms of the sum, and the canonical form sorts them again."""
    one = merge([FLEET, DEMAND, BALANCE])
    other = merge([BALANCE, DEMAND, FLEET])
    assert canonical_yaml(one) == canonical_yaml(other)


@pytest.mark.parametrize(
    ('definer', 'body'),
    [
        pytest.param(SLACKED, 'slack + store_injection', id='a-definition-a-file-writes'),
        pytest.param(
            merge([BALANCE, DEMAND, FLEET]),
            'demand_injection + generator_injection + store_injection',
            id='a-sum-a-merge-wrote',
        ),
    ],
)
def test_a_term_follows_the_body_a_fragment_defines(definer, body):
    """A term on a name a fragment defined was refused, so a merged spec took no further term."""
    composed = merge([definer, STORAGE])
    assert composed.expressions['injection'].expression == body
    assert composed.expressions['store_injection'].adds_to is None


def test_the_definer_keeps_its_description():
    assert (
        merge([SLACKED, STORAGE]).expressions['injection'].description
        == SLACKED['expressions']['injection']['description']
    )


@pytest.mark.parametrize(
    ('stepped', 'flat', 'body'),
    [
        pytest.param(
            merge([merge([BALANCE, DEMAND, FLEET]), STORAGE]),
            merge([BALANCE, DEMAND, FLEET, STORAGE]),
            'demand_injection + generator_injection + store_injection',
            id='the-last-file-later',
        ),
        pytest.param(
            merge([merge([BALANCE]), DEMAND, FLEET, STORAGE]),
            merge([BALANCE, DEMAND, FLEET, STORAGE]),
            'demand_injection + generator_injection + store_injection',
            id='the-reader-alone-first',
        ),
        pytest.param(
            merge([merge([merge([BALANCE, FLEET]), DEMAND]), STORAGE]),
            merge([BALANCE, FLEET, DEMAND, STORAGE]),
            'generator_injection + demand_injection + store_injection',
            id='three-steps',
        ),
        pytest.param(
            merge([merge([SLACKED, FLEET]), STORAGE]),
            merge([SLACKED, FLEET, STORAGE]),
            'slack + generator_injection + store_injection',
            id='a-body-a-file-defines',
        ),
    ],
)
def test_a_sum_merged_in_steps_is_the_sum_merged_in_one(stepped, flat, body):
    """The terms join with a plain `+`, so no bracket marks which merge wrote which term.

    The canonical form reads `(a + b) + c` as `a + b + c`, so only the
    written body tells the plain join from a bracketed one.
    """
    assert stepped.expressions['injection'].expression == body
    assert flat.expressions['injection'].expression == body
    assert canonical_yaml(stepped) == canonical_yaml(flat)


def test_a_step_where_no_other_file_reads_the_sum_is_refused():
    """A merge closes every sum it has terms for, so the step that first closes one needs a reader."""
    with pytest.raises(LanguageError, match=r"add a term to 'injection', and no other fragment reads it"):
        merge([merge([FLEET, DEMAND]), BALANCE])


def test_a_term_on_a_cased_definition_is_refused():
    cased = {
        **SLACKED,
        'parameters': {'on': {'dims': BUS_FRAME, 'dtype': 'bool'}},
        'expressions': {
            'injection': {'dims': BUS_FRAME, 'cases': {'on': {'when': 'on', 'expression': 'slack'}}, 'otherwise': '0'}
        },
    }
    with pytest.raises(
        LanguageError,
        match=r"fragment '#1' defines 'injection' as `cases:`, and fragment '#2' adds a term to it\. "
        r".*Declare the cased body as an expression of its own, and define 'injection' as that name\.",
    ):
        merge([cased, STORAGE])


def test_a_reader_that_states_less_than_the_definer_is_refused():
    narrow = {
        **DEMAND,
        'parameters': {'load': {'dims': ['bus']}},
        'given': {'expressions': {'injection': {'dims': ['bus']}}},
    }
    with pytest.raises(
        LanguageError, match=r"fragment '#2' reads the given expression 'injection'.*over \['bus', 'snapshot'\]"
    ):
        merge([SLACKED, narrow])


#: A file that reads the injection and defines a name from it.
DOUBLED = {**BALANCE, 'expressions': {'doubled': {'expression': 'injection * 2'}}}

#: A term that reads what the injection reads.
FEEDBACK = {
    'dimensions': BUS_DIMS,
    'given': {'expressions': {'injection': {'dims': BUS_FRAME}, 'doubled': {'dims': BUS_FRAME}}},
    'expressions': {'feedback': {'expression': 'doubled', 'adds_to': 'injection'}},
}


def _adding(term: str, body: str, target: str, reads: str) -> dict[str, object]:
    """A file whose *term* is *body* and adds to *target*, reading *target* and *reads*."""
    return {
        'dimensions': BUS_DIMS,
        'given': {'expressions': {target: {'dims': BUS_FRAME}, reads: {'dims': BUS_FRAME}}},
        'expressions': {term: {'expression': body, 'adds_to': target}},
    }


@pytest.mark.parametrize(
    ('fragments', 'message'),
    [
        pytest.param(
            [DOUBLED, FEEDBACK],
            r"fragment '#2' adds 'feedback' to 'injection', and 'feedback' reads 'injection' back through "
            r"'doubled' of '#1', so the sum would define itself\. .*define 'doubled' without 'injection'\.",
            id='through-a-definition',
        ),
        pytest.param(
            [
                BALANCE,
                _adding('outflow', 'withdrawal', 'injection', 'withdrawal'),
                _adding('inflow', 'injection', 'withdrawal', 'injection'),
            ],
            r"fragment '#2' adds 'outflow' to 'injection', and 'outflow' reads 'injection' back through "
            r"the sum 'withdrawal', 'inflow' of '#3'",
            id='through-another-sum',
        ),
    ],
)
def test_a_term_that_reads_its_sum_through_another_fragment_is_refused(fragments, message):
    """Each file loads alone, and the composed load named the loop but not the fragments that close it."""
    with pytest.raises(LanguageError, match=message):
        merge(fragments)


def test_a_file_adds_its_own_part_as_a_term_of_what_it_reads():
    """What a definition once carried, the slack, is a term of the network's own reading."""
    composed = merge([SLACK_TERM, FLEET, DEMAND])
    assert composed.expressions['injection'].expression == 'slack_injection + generator_injection + demand_injection'
    assert composed.expressions['injection'].description == INJECTION


def test_the_sum_takes_the_readers_description():
    composed = merge([FLEET, DEMAND, BALANCE])
    assert composed.program.expressions['injection'].description == INJECTION


def test_two_readers_that_word_the_sum_apart_give_it_the_first_wording():
    capped = {**CAPPED, 'given': {'expressions': {'injection': {'dims': BUS_FRAME, 'description': 'a cap'}}}}
    assert merge([capped, BALANCE]).expressions['injection'].description == 'a cap'
    assert merge([BALANCE, capped]).expressions['injection'].description == INJECTION


def test_a_cased_term_is_added_like_any_other():
    """The sum names the term, so how the term is written is its own file's business."""
    cased = _demand(
        body={
            'dims': BUS_FRAME,
            'cases': {'peak': {'when': 'load > 5', 'expression': '-load'}},
            'otherwise': '0',
        }
    )
    composed = merge([BALANCE, cased, FLEET])
    assert composed.expressions['injection'].expression == 'demand_injection + generator_injection'
    assert composed.program.expressions['demand_injection'].in_math


@pytest.mark.parametrize(
    ('fragments', 'message'),
    [
        pytest.param(
            [FLEET, DEMAND],
            r"fragments '#1' and '#2' add a term to 'injection', and no other fragment reads it\. .*"
            r"or fix the spelling under 'given:'\.$",
            id='terms-and-nothing-else-with-no-near-miss',
        ),
        pytest.param(
            [
                BALANCE,
                {
                    **FLEET,
                    'given': {'expressions': {'injecton': {'dims': BUS_FRAME}}},
                    'expressions': {
                        'generator_injection': {**FLEET['expressions']['generator_injection'], 'adds_to': 'injecton'}
                    },
                },
            ],
            r"fragment '#2' adds a term to 'injecton', and no other fragment reads it.*Did you mean 'injection'\?",
            id='a-misspelt-given-entry',
        ),
        pytest.param(
            [
                BALANCE,
                {
                    **FLEET,
                    'given': {'expressions': {'injecton': {'dims': BUS_FRAME}}},
                    'expressions': {
                        'generator_injection': {**FLEET['expressions']['generator_injection'], 'adds_to': 'injecton'},
                        'twice': 'injecton * 2',
                    },
                },
            ],
            r"fragment '#2' adds a term to 'injecton', and no other fragment reads it.*Did you mean 'injection'\?",
            id='a-misspelt-given-entry-the-same-file-reports',
        ),
        pytest.param(
            [
                BALANCE,
                {
                    **CAPPED,
                    'given': {'expressions': {'injecton': {'dims': BUS_FRAME}}},
                    'expressions': {
                        'generator_injection': {**FLEET['expressions']['generator_injection'], 'adds_to': 'injecton'}
                    },
                    'constraints': {'capped': {'dims': BUS_FRAME, 'expression': 'injecton <= 10'}},
                },
            ],
            r"fragment '#2' adds a term to 'injecton', and no other fragment reads it.*Did you mean 'injection'\?",
            id='a-misspelt-given-entry-the-same-file-caps',
        ),
    ],
)
def test_terms_only_their_own_files_read_are_refused(fragments, message):
    """A misspelt `given:` entry loads in its own file, and is refused where nothing else reads the name.

    A reported expression builds no row, so reading the name there is not
    the use in the math the refusal asks for: `_uses` counted it, and a
    contributor that reported its misspelt sum passed the check. A
    contributor that capped its misspelt sum in its own math passed too,
    since its use counted as a read though no other fragment read the name.
    """
    with pytest.raises(LanguageError, match=message):
        merge(fragments)


@pytest.mark.parametrize(
    ('reader', 'contributor'),
    [
        pytest.param(BALANCE, FLEET, id='a-fragment-that-reads-and-adds-nothing'),
        pytest.param(SLACK_TERM, DEMAND, id='a-contributor-whose-math-reads-it'),
        pytest.param(CAPPED, DEMAND, id='a-contributor-whose-own-constraint-reads-it'),
    ],
)
def test_a_fragment_that_reads_the_sum_for_more_than_adding_lets_the_terms_land(reader, contributor):
    assert merge([reader, contributor]).program.expressions['injection'].in_math


def test_a_sum_a_sibling_declares_as_another_kind_names_that_kind():
    """A term on a name a sibling declares as a variable was refused as a misspelling nothing else reads."""
    network = {
        'dimensions': BUS_DIMS,
        'variables': {'injection': {'dims': BUS_FRAME}},
        'constraints': {'balance': {'dims': BUS_FRAME, 'expression': 'injection == 0'}},
    }
    with pytest.raises(
        LanguageError,
        match=r"fragment '#1' declares 'injection' as a variable, and fragment '#2' adds a term to it\. "
        r'Give the sum a name of its own',
    ):
        merge([network, DEMAND])


def test_readers_that_order_the_frame_apart_are_refused():
    """The sum took its dims from the first reader, so the order of the list reached the canonical text."""
    reversed_ = {**BALANCE, 'given': {'expressions': {'injection': {'dims': ['bus', 'snapshot']}}}}
    with pytest.raises(
        LanguageError,
        match=r"fragments '#1' and '#2' read the sum 'injection' over \['bus', 'snapshot'\] and "
        r"\['snapshot', 'bus'\]",
    ):
        merge([reversed_, FLEET])


def test_the_composed_sum_is_read_over_the_readers_frame():
    """The frame the readers state holds the terms to it when the composed spec loads."""
    assert merge([BALANCE, FLEET, DEMAND]).expressions['injection'].dims == BUS_FRAME


def test_one_term_alone_is_its_name():
    composed = merge([BALANCE, STORAGE])
    assert composed.expressions['injection'].expression == 'store_injection'


def test_two_definitions_collide_and_the_message_names_adds_to():
    other = {
        'dimensions': BUS_DIMS,
        'variables': {'other_slack': {'dims': BUS_FRAME}},
        'expressions': {'injection': 'other_slack'},
        'constraints': {'other_balance': {'dims': BUS_FRAME, 'expression': 'injection == 0'}},
    }
    with pytest.raises(LanguageError) as raised:
        merge([SLACKED, other])
    message = str(raised.value)
    assert "both declare the expression 'injection'" in message
    assert "At most one fragment defines a sum: the others read it under 'given: expressions:'" in message


def test_two_terms_of_one_name_collide():
    """A term is an ordinary named expression, so two fragments name theirs apart."""
    twin = {**FLEET, 'expressions': {'demand_injection': FLEET['expressions']['generator_injection']}}
    with pytest.raises(
        LanguageError,
        match=r"both declare the expression 'demand_injection', which a fragment adds to 'injection' as a term\. "
        r"Give each fragment's term a name of its own",
    ):
        merge([BALANCE, DEMAND, twin])


def test_two_readers_that_disagree_about_the_frame_are_refused():
    narrow = {**BALANCE, 'given': {'expressions': {'injection': {'dims': ['bus']}}}}
    narrow = {**narrow, 'constraints': {'balance': {'dims': ['bus'], 'expression': 'injection == 0'}}}
    with pytest.raises(LanguageError, match=r"say different things about the given expression 'injection'"):
        merge([narrow, FLEET])


def test_a_term_over_fewer_dimensions_merges_where_another_carries_the_rest():
    flat = {**DEMAND, 'parameters': {'load': {'dims': ['bus']}}}
    composed = merge([BALANCE, flat, FLEET])
    assert composed.program.expressions['injection'].dims == ('snapshot', 'bus')


@pytest.mark.parametrize(
    'body', [pytest.param({'expression': '-2 * load'}, id='a-mapping'), pytest.param('-2 * load', id='one-line')]
)
def test_a_patch_changes_a_term_s_body_and_keeps_what_it_adds_to(body):
    """A one-line patch replaced the whole block, so the term lost its `adds_to:` and left the sum unannounced."""
    doubled = override(DEMAND, [{'expressions': {'demand_injection': body}}])
    assert doubled.expressions['demand_injection'].expression == '-2 * load'
    assert doubled.expressions['demand_injection'].adds_to == 'injection'


def test_a_one_line_patch_replaces_a_cased_body():
    cased = _demand(
        body={'dims': BUS_FRAME, 'cases': {'peak': {'when': 'load > 5', 'expression': '-load'}}, 'otherwise': '0'}
    )
    laid = override(cased, [{'expressions': {'demand_injection': '-load'}}])
    assert laid.expressions['demand_injection'].cases == {}, 'the one-line body replaces the cases and the default'
    assert laid.expressions['demand_injection'].otherwise is None
    assert laid.expressions['demand_injection'].adds_to == 'injection'


def test_a_patch_drops_what_a_term_adds_to_with_null():
    reader = override(DEMAND, [{'expressions': {'demand_injection': {'adds_to': None}}}])
    assert reader.expressions['demand_injection'].adds_to is None, 'the entry is a plain named expression again'


# ---------------------------------------------------------------------------
# printing
# ---------------------------------------------------------------------------


def test_the_legend_names_the_term_the_file_adds():
    given = to_markdown(DEMAND).split('#### Given')[1]
    assert 'an expression this file adds `demand_injection` to' in given


def test_inlining_keeps_the_definition_of_a_term():
    """A term is read only through the sum it adds to, and that reads as a
    symbol, so substitution never reaches the term's body: `defined()` dropped
    it as read by the math, and the page named a term it never defined."""
    inlined = to_markdown(DEMAND, inline_expressions=True)
    assert '#### Definitions' in inlined, 'the term is the one definition the file has'
    assert '`demand_injection` over' in inlined.split('#### Definitions')[1], (
        'the term prints under its own name, as the legend says it does'
    )


@pytest.mark.parametrize('spec', [BALANCE, FLEET], ids=['a-reader', 'a-contributor'])
def test_a_given_expression_prints_no_line_of_its_own(spec):
    """The term prints as the definition it is; the name it adds to prints in the legend."""
    with pytest.raises(LanguageError, match=r"'injection' is a given expression, which prints no line of its own"):
        typeset_declaration(spec, 'injection', 'latex')


def test_the_composed_sum_prints_its_terms_by_name():
    composed = merge([FLEET, DEMAND, BALANCE])
    assert typeset_declaration(composed, 'injection', 'typst', inline_expressions=False) == (
        'italic("injection")_(t,b) = italic("generator_injection")_(t,b) + upright("demand_injection")_(t,b) '
        'quad forall t in cal(T), b in cal(B)'
    )


@pytest.mark.parametrize('fmt', sorted(FORMATS))
def test_a_contributor_and_a_composition_print_in_every_format(fmt):
    assert typeset(DEMAND, fmt), f'{fmt} rendered nothing for the contributor'
    assert typeset(merge([FLEET, DEMAND, BALANCE]), fmt), f'{fmt}: the composition'
