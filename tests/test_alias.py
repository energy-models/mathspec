# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A dimension that is an alias of another: the same labels under a second name, so an entry is over them twice."""

from typing import Any

import pytest
import yaml

from mathspec import advice, to_spec, typeset
from mathspec.errors import LanguageError
from tests.fixtures import SMALL_MODEL, varied

#: `g` twice: `from_g` is an alias of it, `link` a parameter over both, and a constraint reading the far end.
TWICE: dict[str, Any] = varied(
    SMALL_MODEL,
    **{
        'dimensions.from_g': {'alias': 'g'},
        'parameters.link': {'dims': ['from_g', 'g'], 'missing': 0},
        'constraints.inflow': {'dims': ['g'], 'expression': 'p == sum(link * at(p, by=from_g[g]), over=from_g)'},
    },
)


def test_an_alias_has_the_labels_dtype_and_order_of_its_dimension():
    dimension = to_spec(TWICE).program.dimensions['from_g']
    assert dimension.alias == 'g', 'the program names the dimension whose labels the alias has'
    assert (dimension.dtype, dimension.ordered) == ('str', True), 'dtype and order come from g'


def test_an_alias_is_ordered_where_its_dimension_is():
    """`shift` along an alias steps as it does along the dimension it aliases."""
    to_spec(
        varied(
            TWICE,
            **{
                'variables.x': {'dims': ['from_g']},
                'constraints.ramp': {'dims': ['from_g'], 'expression': 'x >= shift(x, along=from_g, offset=1, edge=0)'},
            },
        )
    )


def test_an_alias_writes_back_only_its_alias():
    spec = to_spec(TWICE)
    assert yaml.safe_load(spec.to_yaml())['dimensions']['from_g'] == {'alias': 'g'}, 'the alias sets nothing else'
    assert to_spec(spec.to_yaml()) == spec, 'the file round-trips'


@pytest.mark.parametrize('fmt', ['markdown', 'latex', 'typst'])
def test_an_alias_prints_as_a_primed_index_over_the_same_set(fmt: str):
    """The read through the alias is the identity, so the far end prints at the primed index, not through a function."""
    out = typeset(to_spec(TWICE), fmt)
    assert "g'" in out, 'the alias is the index of g, primed'
    assert 'from_g(' not in out and 'g(' not in out.replace("g'", ''), 'the identity relation prints no function'


@pytest.mark.parametrize(
    ('patch', 'message'),
    [
        pytest.param(
            {'dimensions.from_g': {'alias': 'g', 'dtype': 'int'}},
            "is an alias of 'g', and takes its dtype, labels and order from it. Delete dtype:, or set it on 'g'.",
            id='a-dtype-of-its-own',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'g', 'ordered': False}},
            'Delete ordered:',
            id='an-order-of-its-own',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'nope'}},
            "Dimension 'from_g': alias: 'nope' is no declared dimension.",
            id='an-undeclared-dimension',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'from_g'}},
            "Dimension 'from_g': alias: 'from_g' is the dimension itself.",
            id='itself',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'g'}, 'dimensions.to_g': {'alias': 'from_g'}},
            "Dimension 'to_g': alias: 'from_g' is an alias of 'g' itself. Write alias: g.",
            id='an-alias-of-an-alias',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'g'}, 'relations.from_g': {'key': 'from_g', 'values': 'g'}},
            "Relation 'from_g' collides with the relation that dimension 'from_g' implies, read as from_g[g]. "
            "Delete 'from_g' under relations:.",
            id='its-relation-declared-again',
        ),
        pytest.param(
            {'dimensions.from_g': {'alias': 'g'}, 'relations.from_g': {'key': 'h', 'values': 'g'}},
            "Relation 'from_g' collides with the dimension of the same name. Rename one of them.",
            id='another-relation-under-its-name',
        ),
    ],
)
def test_an_alias_that_says_more_or_less_than_its_dimension_is_refused(patch: dict[str, Any], message: str):
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(SMALL_MODEL, **patch))
    assert message in str(caught.value)


@pytest.mark.parametrize(
    ('frame', 'expression', 'indexed'),
    [
        pytest.param(['g'], 'p == sum(sum(w, over=g), over=from_g, by=from_g[g])', "w_{g',g''}", id='under-g'),
        pytest.param(['from_g', 'g'], 'x == sum(sum(w, over=g), over=from_g)', "w_{g'',g'''}", id='under-both'),
        pytest.param(['from_g', 'g'], 'x == sum(sum(w, over=from_g), over=g)', "w_{g''',g''}", id='under-both-swapped'),
    ],
)
def test_a_sum_inside_an_entry_over_the_alias_takes_an_index_of_its_own(
    frame: list[str], expression: str, indexed: str
):
    """A sum over `g` inside a sum over its alias printed `w_{g',g'}`: its dummy took the alias's own index.

    The alias prints as `g'`, and a reduction primes its dummy once per
    enclosing use of the dimension, so the sum over `g` under `∀ g` also
    printed `g'`, and the two indices of `w` read as one. Under `∀ g', g`
    both sums printed `g''`: the inner dummy skipped every dimension's index
    but not the dummy of the sum around it.
    """
    spec = to_spec(
        varied(
            SMALL_MODEL,
            **{
                'dimensions.from_g': {'alias': 'g'},
                'variables.w': {'dims': ['from_g', 'g']},
                'variables.x': {'dims': ['from_g', 'g']},
                'constraints.out': {'dims': frame, 'expression': expression},
            },
        )
    )
    assert indexed in typeset(spec, 'markdown'), 'each sum takes an index no dimension and no enclosing sum prints'


#: `from_h` is an alias of `h`, and no relation and no entry other than `p` is over either.
ALIASED_H: dict[str, Any] = varied(
    SMALL_MODEL, relations={}, variables={'p': {'dims': ['g']}}, **{'dimensions.from_h': {'alias': 'h'}}
)


@pytest.mark.parametrize(
    ('patch', 'unused'),
    [
        pytest.param({}, ['from_h', 'h'], id='nothing-uses-the-alias'),
        pytest.param({'variables.w': {'dims': ['from_h']}}, [], id='an-entry-is-over-the-alias'),
    ],
)
def test_the_relation_an_alias_implies_reaches_no_dimension(patch: dict[str, Any], unused: list[str]):
    """An alias nothing used drew no advice: the relation it implies counted as a column over both dimensions."""
    notes = advice(varied(ALIASED_H, **patch))
    assert [n.subject for n in notes if n.kind == 'never-an-axis'] == unused, (
        'an unused alias is advised, and an alias in use reaches the dimension whose labels it has'
    )


def test_a_condition_compares_the_label_an_alias_reads():
    """`from_g[g] == 'a'` was refused as a column of a dimension: a condition did not read the relation the alias implies."""
    out = typeset(to_spec(varied(TWICE, **{'parameters.link.where': "from_g[g] == 'a'"})), 'markdown')
    assert "only where $`g' = " in out, 'the condition reads the label at the primed index'
