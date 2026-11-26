# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The grammar, and the two parsers over it: of an expression string and of a where string.

Nothing here resolves names or decides what a term may be where it stands:
a parse result holds what was written, as the nodes of the one syntax tree.
"""

import operator
import re
from collections.abc import Iterator
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import mathspec.program as program_module
from mathspec._grammar import is_name, parse_condition, parse_expression
from mathspec._syntax import (
    MAX_DEPTH,
    AndNode,
    BinaryOperatorNode,
    BooleanNode,
    ColumnsNode,
    ComparisonNode,
    FunctionCallNode,
    KeywordNode,
    NameListNode,
    NameNode,
    NotNode,
    NumberNode,
    OrNode,
    UnaryOperatorNode,
    children,
    depth,
    nodes,
)
from mathspec.errors import SchemaError
from mathspec.program import And, Not, Or, ParameterDefined, _conjuncts
from tests.grammar.generate import NAMES, NUMBERS, ODD


def test_a_parse_holds_no_node_of_the_program():
    """A where string parses to the syntax tree's own connectives, and resolution builds the program's from them.

    The grammar built `mathspec.program`'s `And`, `Or`, `Not` and
    `BooleanLiteral` around unresolved leaves, so a tree typed as a program's
    condition was one no consumer of a condition could read.
    """
    tree = parse_condition('a AND NOT b OR True')
    assert tree == OrNode(AndNode(NameNode('a'), NotNode(NameNode('b'))), BooleanNode(True))
    program_nodes = [node for node in nodes(tree) if type(node).__module__ == program_module.__name__]
    assert not program_nodes, 'every node of a parse is a syntax node'


@pytest.mark.parametrize(
    'text',
    [
        pytest.param('p * cost + 1', id='arithmetic'),
        pytest.param('sum(p, over=g) <= cap', id='a-comparison'),
        pytest.param("shift(p, along=t, offset=1, edge='wrap')", id='a-call-with-a-label'),
        pytest.param('at(x, by=gen_bus[bus]) != 0', id='a-comparison-only-a-condition-makes'),
    ],
)
def test_the_two_parsers_read_one_grammar(text):
    """One grammar reads every string, so a string with no reserved word in it is one tree to both parsers."""
    assert parse_expression(text) == parse_condition(text), 'the same tree whichever key the string stands under'


def test_only_a_where_string_reserves_its_words():
    """`AND`, `OR`, `NOT`, `True` and `False` are names in an expression and words in a where string."""
    assert parse_expression('not + true') == BinaryOperatorNode('+', NameNode('not'), NameNode('true'))
    assert parse_condition('not true') == NotNode(BooleanNode(True))


def _reads_as_one_name(text: str) -> bool:
    try:
        return parse_condition(text) == NameNode(text)
    except SchemaError:
        return False


@pytest.mark.parametrize(
    'text', sorted({*NAMES, *NUMBERS, *ODD, '', ' ', ' x', 'x ', '(x)', 'a b', 'a-b', 'a.b', '1x', "'x'", 'f(x)'})
)
def test_a_name_is_what_the_parser_reads_as_one_name(text):
    """`is_name` answers without the parser, so this holds its answer to the parser's over the fuzzer's vocabulary."""
    assert is_name(text) == _reads_as_one_name(text), f'{text!r}: is_name and the parser part'


@pytest.mark.parametrize(
    ('text', 'node_type', 'attrs'),
    [
        pytest.param('42', NumberNode, {'value': 42}, id='an-integer'),
        pytest.param('3.14', NumberNode, {'value': pytest.approx(3.14)}, id='a-decimal'),
        pytest.param('p_max', NameNode, {'name': 'p_max'}, id='a-name'),
        pytest.param('a + b', BinaryOperatorNode, {'op': '+'}, id='a-binary-operator'),
        pytest.param('-x', UnaryOperatorNode, {'op': '-'}, id='a-unary-operator'),
        pytest.param('p <= p_max', ComparisonNode, {'op': '<='}, id='a-comparison'),
        pytest.param('sum(p, over=g) == load', ComparisonNode, {'op': '=='}, id='a-comparison-over-a-call'),
        pytest.param('sum(p, over=generator)', FunctionCallNode, {'name': 'sum'}, id='a-call'),
    ],
)
def test_an_expression_parses_to_its_node(text, node_type, attrs):
    node = parse_expression(text)
    assert isinstance(node, node_type)
    for attr, expected in attrs.items():
        assert getattr(node, attr) == expected


@pytest.mark.parametrize(
    ('text', 'tree'),
    [
        pytest.param(
            'a + b * c',
            BinaryOperatorNode('+', NameNode('a'), BinaryOperatorNode('*', NameNode('b'), NameNode('c'))),
            id='multiplication-binds-tighter-than-addition',
        ),
        pytest.param(
            '(a + b) * c',
            BinaryOperatorNode('*', BinaryOperatorNode('+', NameNode('a'), NameNode('b')), NameNode('c')),
            id='parentheses-override-precedence',
        ),
        pytest.param(
            '-a ** 2',
            UnaryOperatorNode('-', BinaryOperatorNode('**', NameNode('a'), NumberNode(2))),
            id='a-negation-is-over-the-power-not-under-it',
        ),
        pytest.param(
            '-a * b',
            BinaryOperatorNode('*', UnaryOperatorNode('-', NameNode('a')), NameNode('b')),
            id='a-negation-binds-tighter-than-a-product',
        ),
    ],
)
def test_precedence(text, tree):
    assert parse_expression(text) == tree


def test_a_call_carries_its_positional_and_keyword_arguments():
    node = parse_expression('sum(p * cost, over=generator)')
    assert len(node.args) == 1, 'one positional argument; the keyword is not among them'
    assert isinstance(node.args[0], BinaryOperatorNode), 'the argument is an expression, not just a name'
    assert 'over' in node.kwargs


def test_a_parsed_node_pickles_and_stays_frozen():
    """A node crosses a process, and its keyword arguments still refuse a write on the far side."""
    import pickle

    node = parse_expression('sum(p, over=snapshot)')
    copy = pickle.loads(pickle.dumps(node))
    assert copy == node
    with pytest.raises(TypeError, match='does not support item assignment'):
        operator.setitem(copy.kwargs, 'over', NameNode('generator'))


@pytest.mark.parametrize(
    ('rewrite', 'error', 'match'),
    [
        pytest.param(
            lambda node: setattr(node, 'op', '>='), FrozenInstanceError, 'cannot assign', id='a-comparison-sense'
        ),
        pytest.param(
            lambda node: operator.setitem(node.left.kwargs, 'over', NameNode('snapshot')),
            TypeError,
            'does not support item assignment',
            id='a-reduction-axis',
        ),
    ],
)
def test_a_parsed_expression_cannot_be_rewritten_under_another_pass(rewrite, error, match):
    """A pass handed a parsed tree could rewrite the operand another one reads.

    The expression nodes were plain dataclasses while every where and program
    node was frozen (#197): `node.op = '<='` flipped a shared comparison and
    `node.kwargs['over'] = ...` re-aimed a reduction, with no error anywhere.
    """
    node = parse_expression('sum(p * cost, over=generator) == load')
    with pytest.raises(error, match=match):
        rewrite(node)


def test_a_call_copies_the_kwargs_it_is_handed():
    """A caller's own dict is copied on the way in, so holding it is not a back door either."""
    passed = {'over': NameNode('generator')}
    built = FunctionCallNode('sum', (NameNode('p'),), passed)
    passed['over'] = NameNode('snapshot')
    assert built.kwargs == {'over': NameNode('generator')}, 'the dict handed in was copied, not aliased'
    assert isinstance(hash(built), int), 'kwargs sits outside the hash, so a call hashes like every other node'


@pytest.mark.parametrize(
    ('text', 'rewrite'),
    [
        pytest.param('p = p_max', r'Write == for equality', id='a-lone-equals'),
        pytest.param('p ^ 2', r"power is written '\*\*', not '\^'", id='caret-for-power'),
        pytest.param('0 <= p <= p_max', r'Split the chain into two constraints', id='a-chained-comparison'),
    ],
)
def test_a_parse_failure_names_the_rewrite(text, rewrite):
    """The predictable mistakes are refused with their rewrite, not the grammar's complaint alone."""
    with pytest.raises(SchemaError, match=rewrite):
        parse_expression(text)


@pytest.mark.parametrize(
    'fragment',
    [pytest.param('Cannot parse', id='the-refusal'), pytest.param('Expected', id='the-grammar-s-complaint')],
)
def test_a_failure_with_no_diagnosis_still_shows_the_grammar_s_complaint(fragment):
    with pytest.raises(SchemaError, match=fragment):
        parse_expression('a +')


def test_an_exponent_may_be_negated_and_a_negation_stacked():
    assert parse_expression('2 ** -1').right == UnaryOperatorNode('-', NumberNode(1))
    assert parse_expression('--x') == UnaryOperatorNode('-', UnaryOperatorNode('-', NameNode('x')))


def test_a_keyword_given_twice_is_refused_not_overwritten():
    with pytest.raises(SchemaError, match='sum\\(over=\\) is given twice'):
        parse_expression('sum(p, over=snapshot, over=generator)')


def test_a_list_of_names_is_a_kwarg_value():
    """`by=[a, b]` is one value, so the operator reads one grouping and not two."""
    node = parse_expression('sum(p, by=[a, b])')
    assert node.kwargs['by'] == NameListNode(('a', 'b'))


@pytest.mark.parametrize(
    'text',
    [
        pytest.param('sum(p, by=[a,])', id='a-trailing-comma'),
        pytest.param('sum(p, by=[])', id='no-names-at-all'),
        pytest.param('sum(p, by=[a b])', id='a-missing-comma'),
        pytest.param('sum(p, by=[a)', id='an-unclosed-bracket'),
    ],
)
def test_a_list_the_grammar_cannot_read_is_refused_at_load(text):
    with pytest.raises(SchemaError, match='Cannot parse the expression'):
        parse_expression(text)


@pytest.mark.parametrize(
    ('parse', 'text', 'tree'),
    [
        pytest.param(
            parse_expression, 'p + [c]', BinaryOperatorNode('+', NameNode('p'), NameListNode(('c',))), id='a-list'
        ),
        pytest.param(
            parse_expression, "'wrap' * 2", BinaryOperatorNode('*', KeywordNode('wrap'), NumberNode(2)), id='a-label'
        ),
        pytest.param(
            parse_expression, 'p < cap', ComparisonNode('<', NameNode('p'), NameNode('cap')), id='a-strict-comparison'
        ),
        pytest.param(
            parse_expression,
            '(p <= 1) + 1',
            BinaryOperatorNode('+', ComparisonNode('<=', NameNode('p'), NumberNode(1)), NumberNode(1)),
            id='a-comparison-under-an-operator',
        ),
        pytest.param(
            parse_condition, 'p + 1', BinaryOperatorNode('+', NameNode('p'), NumberNode(1)), id='arithmetic-alone'
        ),
        pytest.param(
            parse_condition,
            '(True) > 0',
            ComparisonNode('>', BooleanNode(True), NumberNode(0)),
            id='a-literal-compared',
        ),
        pytest.param(
            parse_condition,
            "ends[bus0, bus1] == 'x'",
            ComparisonNode('==', ColumnsNode('ends', ('bus0', 'bus1')), KeywordNode('x')),
            id='two-columns-compared',
        ),
    ],
)
def test_the_grammar_reads_a_term_wherever_a_term_may_stand(parse, text, tree):
    """What a term may be where it stands is not the grammar's to say.

    Each of these is refused at load, by resolution, which names the entry and
    the rewrite (`TestATermIsHeldToItsPlaceInResolution`). The grammar refused
    them itself, as a parse failure at a character.
    """
    assert parse(text) == tree, 'the tree says what was written'


@pytest.mark.parametrize(
    ('text', 'tree'),
    [
        pytest.param(
            '(ends[bus0]) == 1', ComparisonNode('==', ColumnsNode('ends', ('bus0',)), NumberNode(1)), id='a-column'
        ),
        pytest.param("g == ('wind')", ComparisonNode('==', NameNode('g'), KeywordNode('wind')), id='a-label'),
        pytest.param('NOT (NOT a)', NotNode(NotNode(NameNode('a'))), id='a-negation'),
    ],
)
def test_parentheses_group_any_term(text, tree):
    assert parse_condition(text) == tree, 'the parentheses leave no node'


def test_a_keyword_may_stand_before_a_positional_argument():
    """A call's arguments are read in any order, whether it reads arithmetic or a condition."""
    assert parse_expression('sum(over=g, p)') == parse_expression('sum(p, over=g)')
    assert parse_condition('shift(along=t, offset=1, a > 0)') == parse_condition('shift(a > 0, along=t, offset=1)')


def test_a_token_needs_no_space_before_the_next():
    assert parse_condition('p>0AND q<.infOR r') == parse_condition('p > 0 AND q < .inf OR r')


@pytest.mark.parametrize(
    ('text', 'value'),
    [
        pytest.param('1e5', 1e5, id='a-bare-exponent'),
        pytest.param('2.5E-3', 2.5e-3, id='an-upper-case-negative-exponent'),
        pytest.param('1e+3', 1e3, id='a-signed-exponent'),
        pytest.param('7.e2', 700.0, id='a-trailing-point-mantissa'),
    ],
)
def test_scientific_notation_is_a_number(text, value):
    assert parse_expression(text) == NumberNode(value)
    assert parse_condition(f'p > {text}').right == NumberNode(value), 'a where side is the expression grammar'


@pytest.mark.parametrize('spelling', ['inf', '.inf'])
def test_inf_is_a_literal(spelling):
    """Both spellings, since `bounds: {upper: .inf}` is how YAML writes it."""
    assert parse_expression(f'p <= {spelling}').right == NumberNode(float('inf'))
    assert parse_condition(f'p < {spelling}').right == NumberNode(float('inf')), 'and a where reads it as one too'


@pytest.mark.parametrize('name', ['inflow', 'influx', 'infeed', 'infrastructure', 'inf_max'])
def test_a_name_may_begin_with_inf(name):
    """`Literal('inf')` matched a prefix, so `inflow` parsed as `inf` and failed on `low`."""
    assert parse_expression(f'a + {name}').right == NameNode(name)


@pytest.mark.parametrize(
    ('text', 'node_type', 'attrs'),
    [
        pytest.param('True', BooleanNode, {'value': True}, id='a-literal'),
        pytest.param('p_max', NameNode, {'name': 'p_max'}, id='a-bare-name'),
        pytest.param('p_max > 0', ComparisonNode, {'op': '>', 'right': NumberNode(0)}, id='a-comparison'),
        pytest.param('a AND b', AndNode, {}, id='and'),
        pytest.param('a OR b', OrNode, {}, id='or'),
        pytest.param('NOT a', NotNode, {}, id='not'),
    ],
)
def test_a_where_string_parses_to_its_node(text, node_type, attrs):
    """A bare name parses to an existence check; what it *names* is
    resolution's problem, not the parser's."""
    node = parse_condition(text)
    assert isinstance(node, node_type)
    for attr, expected in attrs.items():
        assert getattr(node, attr) == expected


def test_and_binds_tighter_than_or():
    assert parse_condition('a OR b AND c') == OrNode(NameNode('a'), AndNode(NameNode('b'), NameNode('c')))


def test_not_takes_one_comparison():
    """`NOT` binds tighter than `AND` and looser than a comparison, and a second `NOT` needs its brackets."""
    assert parse_condition('NOT a > 0 AND b') == AndNode(
        NotNode(ComparisonNode('>', NameNode('a'), NumberNode(0))), NameNode('b')
    )
    with pytest.raises(SchemaError, match='Cannot parse the condition'):
        parse_condition('NOT NOT a')


def _flag(name: str) -> ParameterDefined:
    return ParameterDefined(name, ())


@pytest.mark.parametrize(
    ('condition', 'expected'),
    [
        (_flag('a'), ['a']),
        (And(_flag('a'), _flag('b')), ['a', 'b']),
        (And(And(_flag('a'), _flag('b')), _flag('c')), ['a', 'b', 'c']),
    ],
    ids=['single', 'pair', 'chain'],
)
def test_conjuncts_flattens_the_and_spine(condition, expected):
    """A chain the grammar left-folds into nested `And`s comes back flat (#312).

    `_conjuncts` is the one home of the flatten rule; `Mask.conjuncts` is the
    door a consumer asks it through."""
    assert [n.name for n in _conjuncts(condition)] == expected


@pytest.mark.parametrize(
    'condition',
    [
        Or(_flag('a'), _flag('b')),
        Not(_flag('a')),
        Or(And(_flag('a'), _flag('b')), _flag('c')),
        Not(And(_flag('a'), _flag('b'))),
    ],
    ids=['or', 'not', 'or-of-and', 'not-of-and'],
)
def test_conjuncts_does_not_split_or_or_not(condition):
    assert _conjuncts(condition) == (condition,), 'a non-AND top node is its own only conjunct'


@pytest.mark.parametrize(
    ('text', 'right'),
    [
        ("g == 'wind'", KeywordNode('wind')),
        ('g == "wind"', KeywordNode('wind')),
        ("g == 'combined-cycle'", KeywordNode('combined-cycle')),
        ("g == 'CCGT 400MW'", KeywordNode('CCGT 400MW')),
        ("t > '2030-01-01'", KeywordNode('2030-01-01')),
        ("g == 'it\\'s'", KeywordNode("it's")),
        ('g == wind', NameNode('wind')),
    ],
    ids=['single', 'double', 'hyphen', 'space', 'date', 'escaped quote', 'bare'],
)
def test_a_quoted_right_hand_side_is_a_label(text, right):
    """Quoting says "label, not name" (#460): unquoted, `combined-cycle` or `CCGT 400MW` was
    unsayable, and a bare word may name an entry."""
    node = parse_condition(text)
    assert isinstance(node, ComparisonNode)
    assert node.right == right


def test_a_relation_column_is_named_in_brackets():
    """`ends[bus0]` names a column on a where side, as the node a call's `by=` names its columns in."""
    assert parse_condition('ends[bus0] != ends[bus1]') == ComparisonNode(
        '!=', ColumnsNode('ends', ('bus0',)), ColumnsNode('ends', ('bus1',))
    )


@pytest.mark.parametrize(
    ('text', 'columns'),
    [
        pytest.param('at(x, by=gen_bus[bus])', ColumnsNode('gen_bus', ('bus',)), id='one-column'),
        pytest.param('at(x, by=slot_of[bus, tech])', ColumnsNode('slot_of', ('bus', 'tech')), id='several-columns'),
        pytest.param('at(x, by = slot_of [ bus , tech ])', ColumnsNode('slot_of', ('bus', 'tech')), id='spaced'),
    ],
)
def test_a_column_selection_names_one_relation_and_its_columns(text, columns):
    """The relation is written once, before its columns, so a kwarg cannot name columns of two tables."""
    assert parse_expression(text).kwargs['by'] == columns, 'one relation, its columns in the order written'


@pytest.mark.parametrize(
    ('text', 'op', 'right', 'kwargs'),
    [
        ('position(snapshot) == 0', '==', NumberNode(0), {}),
        ('position(snapshot) != 0', '!=', NumberNode(0), {}),
        ('position(snapshot) > 0', '>', NumberNode(0), {}),
        ('position(snapshot) <= -2', '<=', UnaryOperatorNode('-', NumberNode(2)), {}),
        ('position(snapshot) == -1', '==', UnaryOperatorNode('-', NumberNode(1)), {}),
        (
            'position(snapshot, within=period_of[a]) == 0',
            '==',
            NumberNode(0),
            {'within': ColumnsNode('period_of', ('a',))},
        ),
        (
            'position(snapshot, within=period_of[a, b]) == 0',
            '==',
            NumberNode(0),
            {'within': ColumnsNode('period_of', ('a', 'b'))},
        ),
    ],
    ids=['first', 'not first', 'after the first', 'band from the back', 'last', 'grouped', 'grouped within columns'],
)
def test_position_is_a_call_on_the_left_hand_side(text, op, right, kwargs):
    """`position(dim)` is the left-hand side, so every comparator reads one way (#32), and it arrives as the
    call the expression grammar builds; what its arguments may be is resolution's to say."""
    node = parse_condition(text)
    assert isinstance(node, ComparisonNode)
    assert node.left == FunctionCallNode('position', (NameNode('snapshot'),), kwargs)
    assert node.op == op
    assert node.right == right


@pytest.mark.parametrize(
    'text',
    ['p > 0.5 * q', '(a + b) <= c', '-p < 1', 'sum(p, over=g) >= k', '2 < p', 'position(t) + 1 == 0'],
    ids=[
        'arithmetic-on-the-right',
        'a-bracketed-sum',
        'a-negated-name',
        'a-reduction',
        'a-literal-on-the-left',
        'position-inside-arithmetic',
    ],
)
def test_a_side_is_any_arithmetic_to_the_grammar(text):
    """The grammar hands both sides over bare; what the language admits on a side is decided in resolution,
    where the spec is (`TestAWhereSideIsReadInResolution`)."""
    assert isinstance(parse_condition(text), ComparisonNode)


def test_a_bracketed_condition_is_still_a_condition():
    """`(a > 0) AND b` groups a comparison; only `(a + b) <= c` brackets arithmetic."""
    assert isinstance(parse_condition('(a > 0) AND b'), AndNode)


def test_a_condition_is_an_argument_of_a_call():
    """`count`, `shift` and `at` read a condition, which arrives as the call's argument like any other."""
    assert parse_condition('count(c > 0, over=g) >= 2') == ComparisonNode(
        '>=',
        FunctionCallNode('count', (ComparisonNode('>', NameNode('c'), NumberNode(0)),), {'over': NameNode('g')}),
        NumberNode(2),
    )


def test_a_where_side_is_held_to_the_depth_an_expression_is():
    with pytest.raises(SchemaError, match='nests 121 deep'):
        parse_condition(' + '.join(['p'] * 120) + ' > 0')


@pytest.mark.parametrize(
    ('text', 'rewrite'),
    [
        pytest.param('p_max > 0 & committable', r'Write AND', id='ampersand'),
        pytest.param('p_max > 0 && committable', r'Write AND', id='doubled-ampersand'),
        pytest.param('p_max > 0 | committable', r'Write OR', id='pipe'),
        pytest.param('p_max > 0 || committable', r'Write OR', id='doubled-pipe'),
        pytest.param('~committable', r'Write NOT before the condition', id='tilde'),
        pytest.param('!committable', r'Write NOT before the condition', id='bang'),
        pytest.param('status = 0', r'is not a comparison. Write ==', id='a-lone-equals'),
    ],
)
def test_a_where_parse_failure_names_the_rewrite(text, rewrite):
    """The connective habits of pandas and C are refused with their rewrite, not the grammar's complaint alone."""
    with pytest.raises(SchemaError, match=rewrite):
        parse_condition(text)


def test_a_legal_where_operator_is_never_diagnosed():
    """`!=`, `<` and `>` are conditions here, unlike on the expression side, so no diagnosis may fire on them."""
    assert parse_condition('status != 0') == ComparisonNode('!=', NameNode('status'), NumberNode(0.0))
    assert parse_condition('p_max < 5') == ComparisonNode('<', NameNode('p_max'), NumberNode(5.0))


def test_an_unrelated_parse_failure_says_nothing_about_positions():
    with pytest.raises(SchemaError) as excinfo:
        parse_condition('p_max >')
    assert 'position()' not in str(excinfo.value)


def test_a_string_parses_to_one_shared_tree():
    """Drop the memo and this passes on `==` alone — `is` is the claim."""
    text = 'sum(p * cost, over=generator) == load'
    assert parse_expression(text) is parse_expression(text), 'the same expression string parses to one tree'
    assert parse_condition('p_max > 0') is parse_condition('p_max > 0'), 'and so does the same where string'


def test_a_parse_failure_is_raised_every_time_it_is_asked_for():
    """A memo that cached the failure would hand the second caller a traceback from the first."""
    for _ in range(2):
        with pytest.raises(SchemaError, match=r"power is written '\*\*'"):
            parse_expression('p ^ 2')


@pytest.mark.parametrize(
    ('text', 'parse', 'rewrite'),
    [
        pytest.param(
            ' + '.join(['x'] * 400),
            parse_expression,
            r'sum\(\) rather than writing the terms out',
            id='a-long-chain-of-terms',
        ),
        pytest.param(
            ' AND '.join(['p'] * 400), parse_condition, r'carrying part of the test', id='a-long-chain-of-conditions'
        ),
    ],
)
def test_a_tree_too_deep_to_walk_is_refused_with_its_rewrite(text, parse, rewrite):
    """These raised `RecursionError` out of `to_spec`, which documents `LanguageError` — a crash, not a refusal.

    A long chain parses fine and builds a tree the passes over it cannot
    recurse, so the file nests deeper than anything can walk.
    """
    with pytest.raises(SchemaError) as excinfo:
        parse(text)
    message = str(excinfo.value)
    assert 'past the 100 levels' in message, 'the refusal names the limit'
    assert re.search(rewrite, message), 'and the rewrite that avoids it'


def test_the_depth_the_repository_writes_is_nowhere_near_the_limit():
    """The cap is only a cap if it is far above what a model says; 100 is chosen against a deepest-in-tree of 18."""
    written = parse_expression('sum(Generator_p * Generator_marginal_cost * snapshot_weightings_objective)')
    assert depth(written, children) < MAX_DEPTH // 4, 'a real expression sits well inside the limit'
    assert depth(parse_expression(' + '.join(['x'] * 99)), children) <= MAX_DEPTH, 'and the limit itself is admitted'


# ---------------------------------------------------------------------------
# Printing a node back as the file writes it
# ---------------------------------------------------------------------------


def _fixture_expressions() -> list[str]:
    """Every expression string the node fixture writes, cases arms included."""
    import yaml

    def strings(node: object) -> Iterator[str]:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ('expression', 'otherwise') and isinstance(value, str):
                    yield value
                else:
                    yield from strings(value)
        elif isinstance(node, list):
            for item in node:
                yield from strings(item)

    fixture = Path(__file__).resolve().parent / 'fixtures' / 'every_program_node.yaml'
    return sorted(set(strings(yaml.safe_load(fixture.read_text()))))


@pytest.mark.parametrize('text', _fixture_expressions())
def test_a_parsed_tree_prints_to_text_that_parses_to_the_same_tree(text):
    """The grammar's inverse, over the fixture the node fence maintains.

    A printer that drops a bracket or a kwarg produces text that still parses,
    and the tree it parses to is the evidence — nothing else here compares two
    trees built from two spellings of one expression.
    """
    tree = parse_expression(text)
    assert parse_expression(str(tree)) == tree, f'`{text}` printed as `{tree}`, which is a different tree'


@pytest.mark.parametrize(
    ('text', 'printed'),
    [
        pytest.param('p + q', 'p + q', id='a-sum-of-two-leaves-needs-no-brackets'),
        pytest.param('p + q * r', 'p + (q * r)', id='an-operator-operand-is-bracketed'),
        pytest.param('(p + q) * r', '(p + q) * r', id='and-so-is-the-one-the-file-bracketed'),
        pytest.param('-p', '-p', id='a-sign-on-a-leaf-stands-bare'),
        pytest.param('-(p + q)', '-(p + q)', id='and-brackets-what-it-negates'),
        pytest.param('sum(p, over=t) >= 0', 'sum(p, over=t) >= 0', id='a-call-carries-its-kwargs'),
        pytest.param('sum(p, by=[a, b]) >= 0', 'sum(p, by=[a, b]) >= 0', id='a-list-kwarg-keeps-its-brackets'),
        pytest.param("shift(p, along=t, edge='wrap') >= 0", "shift(p, along=t, edge='wrap') >= 0", id='a-keyword'),
        pytest.param('p >= q * r', 'p >= q * r', id='a-comparison-takes-its-sides-bare'),
        pytest.param('p >= 2', 'p >= 2', id='a-whole-number-keeps-no-fraction'),
        pytest.param('p >= 2.5', 'p >= 2.5', id='and-a-fractional-one-keeps-its-own'),
        pytest.param('p <= inf', 'p <= inf', id='an-infinity-prints-as-the-literal-it-parsed-from'),
    ],
)
def test_a_node_prints_as_the_file_writes_it(text, printed):
    assert str(parse_expression(text)) == printed, 'the spelling is the one a file could be written with'


# ---------------------------------------------------------------------------
# Reserved words, quoted labels and parentheses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'text',
    [
        pytest.param('NOT', id='a-bare-not'),
        pytest.param('x AND AND', id='and-after-and'),
        pytest.param('p > 0 OR or', id='lower-case-or'),
        pytest.param('f(x, and=1)', id='a-keyword-named-and'),
    ],
)
def test_a_where_string_refuses_a_reserved_word_as_a_name(text):
    """These read an entry named ``NOT``, ``AND`` or ``or``, where ``NOT x`` reads the word (#1040)."""
    with pytest.raises(SchemaError, match='a where string reserves in any case'):
        parse_condition(text)


@pytest.mark.parametrize(
    'text',
    [
        pytest.param('android', id='and-as-a-prefix'),
        pytest.param('notional > 0', id='not-as-a-prefix'),
        pytest.param('x_or_y', id='or-inside'),
        pytest.param('true_flag', id='true-as-a-prefix'),
    ],
)
def test_a_name_that_only_contains_a_reserved_word_is_a_name(text):
    node = parse_condition(text)
    name = node.left if isinstance(node, ComparisonNode) else node
    assert name == NameNode(text.split()[0]), 'a word inside a longer name is no keyword'


@pytest.mark.parametrize(
    ('parse', 'text', 'label'),
    [
        pytest.param(parse_expression, r"shift(p, edge='\xa2')", 'xa2', id='a-hex-escape-is-not-decoded'),
        pytest.param(parse_expression, r"shift(p, edge='\0')", '0', id='a-nul-escape-is-not-decoded'),
        pytest.param(parse_expression, r"shift(p, edge='a\tb')", 'a\tb', id='a-tab-escape-is-a-tab'),
        pytest.param(parse_expression, "shift(p,  edge='a\tb')", 'a\tb', id='a-tab-is-a-tab-wherever-it-stands'),
        pytest.param(parse_expression, r"shift(p, edge='it\'s')", "it's", id='an-expression-label-escapes-its-quote'),
        pytest.param(parse_condition, r"x == 'it\'s'", "it's", id='a-where-label-escapes-its-quote'),
        pytest.param(
            parse_condition, r"shift(q, edge='it\'s') > 0", "it's", id='and-so-does-one-in-an-arithmetic-call'
        ),
    ],
)
def test_a_quoted_label_reads_its_escapes_as_the_reference_states(parse, text, label):
    """Numeric escapes decoded as pyparsing's f-string bug decoded them (#1039), a label took an escape in a where string and none in an expression (#1042), and a tab became spaces to the next tab stop (#1044)."""
    found = [node.value for node in nodes(parse(text)) if isinstance(node, KeywordNode)]
    assert found == [label], f'{text} holds the label {label!r}'


@pytest.mark.parametrize(
    'label', ["it's", 'a\\b', 'a\tb', 'two\nlines', ''], ids=['quote', 'backslash', 'tab', 'newline', 'empty']
)
def test_a_label_prints_as_text_that_reads_back_as_the_label(label):
    printed = str(KeywordNode(label))
    assert parse_condition(f'x == {printed}') == ComparisonNode('==', NameNode('x'), KeywordNode(label)), (
        f'{label!r} printed as {printed}, which reads back as another label'
    )


@pytest.mark.parametrize('parse', [parse_expression, parse_condition], ids=['expression', 'condition'])
def test_parentheses_cost_no_depth(parse):
    """Sixty redundant parentheses were refused as nesting past 100 levels, when pyparsing ran out of stack (#1041).

    Parentheses leave no node in the tree and the parser does not recurse, so
    no number of them reaches the cap or the interpreter's stack.
    """
    assert parse('(' * 5000 + 'x' + ')' * 5000) == NameNode('x'), 'five thousand parentheses around a name are the name'


@pytest.mark.parametrize(
    'text',
    [
        pytest.param('a OR (b OR c)', id='an-or-on-the-right-of-an-or'),
        pytest.param('a AND (b AND c)', id='an-and-on-the-right-of-an-and'),
        pytest.param('(a OR b) AND c', id='an-or-under-an-and'),
        pytest.param('NOT (a > 0) OR NOT (NOT b)', id='negations'),
        pytest.param("count(tech == 'wind' AND NOT at(a, by=r[c]), over=g) >= 2", id='a-condition-in-a-call'),
        pytest.param('(a > 0) + 1 > (b AND c)', id='a-condition-where-a-number-goes'),
    ],
)
def test_a_parsed_condition_prints_to_text_that_parses_to_the_same_tree(text):
    tree = parse_condition(text)
    assert parse_condition(str(tree)) == tree, f'`{text}` printed as `{tree}`, which is a different tree'
