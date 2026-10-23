# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The condition walk of name resolution: a parsed condition into the program's typed conditions.

A bare name, a comparison, a count and a condition read through a relation
or along a dimension are each typed here against the namespace, and a
comparison of expressions hands its sides to the expression walk.
[`mathspec._resolution`][] holds the namespace and the doors that call this.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, assert_never, cast

import mathspec._degree as degree
from mathspec._condition_parser import (
    ColumnNode,
    UnresolvedComparisonNode,
    UnresolvedConditionCallNode,
    UnresolvedConditionNode,
    UnresolvedCountNode,
)
from mathspec._dimensions import join_dims, sorted_dims
from mathspec._expansion import expand
from mathspec._expression_parser import (
    ArithmeticNode,
    FunctionCallNode,
    KeywordNode,
    NameNode,
    literal_number,
    nodes,
)
from mathspec._expression_resolver import ExpressionResolver, condition_compared
from mathspec.errors import DimensionError, LanguageError, SchemaError, did_you_mean, prefixed, unordered
from mathspec.program import (
    Add,
    And,
    BooleanLiteral,
    ComparisonOperator,
    Condition,
    ConditionReference,
    Constant,
    CountComparison,
    DimensionComparison,
    DimensionPosition,
    Divide,
    Expression,
    ExpressionComparison,
    JoinedCondition,
    Mask,
    Multiply,
    Negate,
    Not,
    Or,
    ParameterComparison,
    ParameterDefined,
    Power,
    RelationComparison,
    RelationDefined,
    RelationPairComparison,
    TranslatedCondition,
    TypedCondition,
    VariableDefined,
    carries_variable,
    variables_of,
    walk,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mathspec._resolution import Namespace
    from mathspec.program import DeclaredDtype

#: Why a mask may not read a given expression. The namespace stores a given
#: expression with the variables, because it is read as a column, so this
#: refusal names it separately.
GIVEN_IN_A_CONDITION = (
    'A given expression may hold a variable, and a condition is read before variables exist — it may test '
    'parameters and dimension coordinates only.'
)


@dataclass(frozen=True)
class ConditionResolver:
    """One resolution walk over a condition, and the things every step of it reads.

    A node that cannot be typed comes back unresolved with its refusal
    appended to ``errors``; every sibling is still read, so a mask with two
    faults reports both. ``self_variable`` is the variable whose own
    ``where`` is being read, which may not ask whether it exists. A side
    that is an expression is built by an [`ExpressionResolver`][] over
    the same namespace.
    """

    ns: Namespace
    context: str
    errors: list[str]
    self_variable: str | None = None

    @property
    def _expressions(self) -> ExpressionResolver:
        return ExpressionResolver(self.ns, self.context, self.errors)

    def build(self, node: Condition | UnresolvedConditionNode) -> Condition | UnresolvedConditionNode:
        """One condition node typed, or returned unresolved with its refusal appended."""
        if isinstance(node, BooleanLiteral | TypedCondition | ConditionReference):
            return node
        if isinstance(node, NameNode):
            return self._bare_name(node)
        if isinstance(node, UnresolvedComparisonNode):
            return self._comparison(node)
        if isinstance(node, UnresolvedConditionCallNode):
            return self._condition_call(node)
        if isinstance(node, UnresolvedCountNode):
            return self._count(node)
        if isinstance(node, Not):
            return Not(self._child(node.operand))
        if isinstance(node, And):
            return And(self._child(node.left), self._child(node.right))
        if isinstance(node, Or):
            return Or(self._child(node.left), self._child(node.right))
        assert_never(node)

    @property
    def conditions(self) -> frozenset[str]:
        """Every named condition this file declares or is given."""
        return self.ns.conditions | self.ns.given_conditions

    def _child(self, node: Condition | UnresolvedConditionNode) -> Condition:
        """A connective's child, typed as resolved: an unresolved one survives only with its refusal appended."""
        return cast('Condition', self.build(node))

    def _bare_name(self, node: NameNode) -> Condition | UnresolvedConditionNode:
        """A bare name: a named condition's body, a parameter's or relation's definedness, or a variable's existence."""
        ns, context = self.ns, self.context
        if node.name in ns.conditions:
            try:
                return ns.condition(node.name, context)
            except SchemaError as e:
                self.errors.append(str(e))
                return node
        kind = ns.kind(node.name)
        if kind is None:
            self.errors.append(ns.unknown(node.name, context, allow_dims=True))
            return node
        match kind:
            case 'parameter':
                declared = ns.spec.parameters.get(node.name)
                if declared is not None and declared.missing == 'refused' and declared.dtype in ('int', 'str'):
                    rewrite = (
                        f'Declare `missing: absent`, or compare the label: where: "{node.name} == \'...\'".'
                        if declared.dtype == 'str'
                        else f'Declare `missing: neutral` or `absent`, or compare the value: where: "{node.name} > 0".'
                    )
                    self.errors.append(
                        f"{context}: '{node.name}' is declared dtype: {declared.dtype} and missing: refused, so it "
                        f'has a row at every coordinate and the bare name is true at every coordinate — the mask '
                        f'has no effect. {rewrite}'
                    )
                    return node
                return ParameterDefined(node.name, ns.leaf_dims[node.name])
            case 'dimension':
                self.errors.append(
                    f"{context}: '{node.name}' is a dimension, and a bare dimension "
                    f'name is true at every coordinate. '
                    f'Remove it, or compare it: where: "{node.name} > 0".'
                )
            case 'relation':
                shape = ns.relations[node.name]
                dims = tuple(sorted(shape.dim(k) for k in shape.key))
                if len(set(dims)) < len(dims):
                    self.errors.append(
                        f"{context}: '{node.name}' has two columns over one dimension ({list(shape.roles)}), so a "
                        f'bare name is ambiguous. Compare a column: '
                        f'{node.name}[{shape.values[0] if shape.values else shape.roles[-1]}] == ....'
                    )
                    return node
                return RelationDefined(node.name, dims)
            case 'variable':
                if node.name == self.self_variable:
                    self.errors.append(
                        f"{context}: variable '{node.name}' tests itself in its own where. "
                        f'Test a parameter, or another variable.'
                    )
                else:
                    return VariableDefined(node.name, ns.leaf_dims[node.name])
        return node

    def _condition_call(self, node: UnresolvedConditionCallNode) -> Condition | UnresolvedConditionNode:
        """``shift(<condition>, along=, offset=)`` or ``at(<condition>, by=relation[column])`` — the two operators that read a condition and answer one.

        ``count`` answers a number, so it stands on a comparison's side and
        [`_count`][] reads it there. Anything else naming a condition is
        refused here rather than resolved into arithmetic it cannot be.

        An operand that failed to resolve is handed straight back: resolution
        collects problems rather than raising, and asking an unresolved
        condition for its dims asserts instead of refusing.
        """
        context, found = self.context, len(self.errors)
        if node.name == 'count':
            self.errors.append(
                f'{context}: count() answers a number, and a condition is true or false. Compare it: '
                f'count(<condition>, over=<dimension>) <op> <integer>.'
            )
            return node
        if node.name not in ('shift', 'at'):
            self.errors.append(
                f"{context}: '{node.name}()' does not read a condition, and only shift(), at() and count() do. "
                f'Compare the condition, or name a parameter carrying it.'
            )
            return node
        operand = self._child(node.operand)
        if len(self.errors) > found:
            return node
        if node.name == 'at':
            return self._joined(node, Mask(operand))
        if (refusal := _kwargs_error(context, 'shift', node.kwargs, required=('along', 'offset'))) is not None:
            self.errors.append(refusal)
            return node
        along = node.kwargs['along']
        offset = literal_number(node.kwargs['offset'])
        if not isinstance(along, NameNode) or self.ns.kind(along.name) != 'dimension':
            self.errors.append(
                f'{context}: shift(<condition>, along=) is not a declared dimension. Name a declared dimension.'
            )
            return node
        if offset is None or not offset.value.is_integer():
            self.errors.append(
                f'{context}: shift(<condition>, offset=) is not a literal whole number. Write an integer.'
            )
            return node
        mask = Mask(operand)
        if along.name not in mask.dims:
            self.errors.append(
                f"{context}: shift(<condition>, along='{along.name}') steps along a dimension the condition does "
                f'not read. Step along one of {_listed(list(mask.dims))}.'
            )
            return node
        if self.ns.unordered(along.name):
            self.errors.append(unordered(context, f'shift(<condition>, along={along.name})', along.name))
            return node
        return TranslatedCondition(mask, along.name, int(offset.value), mask.dims)

    def _joined(self, node: UnresolvedConditionCallNode, mask: Mask) -> Condition | UnresolvedConditionNode:
        """``at(<condition>, by=relation[column])`` — the condition read through a relation, as ``at`` reads an array.

        The columns are read by the rules an expression's ``at`` is, so the one
        refusal a file meets for a bad read is the same in a ``where:`` and in
        an expression.
        """
        context = self.context
        if (refusal := _kwargs_error(context, 'at', node.kwargs, required=('by',))) is not None:
            self.errors.append(refusal)
            return node
        columns = self._expressions.columns_ref(node.kwargs['by'], 'at', 'by')
        by = None if columns is None else self._expressions.lookup(columns, frozenset(mask.dims))
        if by is None:
            return node
        try:
            dims = join_dims(by, frozenset(mask.dims), context, 'the condition')
        except DimensionError as refusal:
            self.errors.append(self.ns.refused_dims(refusal))
            return node
        return JoinedCondition(mask, by, sorted_dims(dims))

    def _count(self, node: UnresolvedCountNode) -> Condition | UnresolvedConditionNode:
        """``count(<condition>, over=<dim>) <op> <integer>`` — how many coordinates the condition admits.

        The reduction leaves every dim but ``over``, so the count is one
        number per remaining coordinate and a claim about each group needs no
        word for the group.
        """
        context, found = self.context, len(self.errors)
        operand = self._child(node.call.operand)
        if len(self.errors) > found:
            return node
        if (refusal := _kwargs_error(context, 'count', node.call.kwargs, required=('over',))) is not None:
            self.errors.append(refusal)
            return node
        over = node.call.kwargs['over']
        if not isinstance(over, NameNode) or self.ns.kind(over.name) != 'dimension':
            self.errors.append(
                f'{context}: count(<condition>, over=) is not a declared dimension. Name a declared dimension.'
            )
            return node
        value = literal_number(node.value)
        if value is None or not value.value.is_integer():
            self.errors.append(
                f'{context}: a count is compared against a value that is not a literal whole number. '
                f'Write count(…, over={over.name}) {node.op} <integer>.'
            )
            return node
        if (decided := _decided_count(node.op, value.value)) is not None:
            self.errors.append(
                f'{context}: count(…, over={over.name}) {node.op} {value} holds at {decided} coordinate, because '
                f'a count is never negative. Delete the comparison, or write the bound it means.'
            )
            return node
        mask = Mask(operand)
        if over.name not in mask.dims:
            self.errors.append(
                f"{context}: count(<condition>, over='{over.name}') counts along a dimension the condition does "
                f'not read. Count along one of {_listed(list(mask.dims))}.'
            )
            return node
        dims = tuple(d for d in mask.dims if d != over.name)
        return CountComparison(mask, over.name, node.op, value.value, dims)

    def _comparison(self, node: UnresolvedComparisonNode) -> Condition | UnresolvedConditionNode:
        """``side <op> side``, read for what each side is.

        A ``position()`` call on the left is the position form. A name against
        a literal or a second column is the plain form the dtype rules are
        written for, unless a side names a parameter or an ``expressions:``
        entry against the other, which is arithmetic however plain it looks.
        Everything else is a comparison of expressions.
        """
        if isinstance(node.left, FunctionCallNode) and node.left.name == 'position':
            return self._position(node.left, node)
        compared = [name for side in (node.left, node.right) if (name := _side_name_or_none(side)) is not None]
        if named := [name for name in compared if name in self.conditions]:
            self.errors.append(condition_compared(named[0], self.context))
            return node
        plain = self._plain(node)
        if plain is None:
            return self._expression_comparison(node)
        return self._plain_comparison(node, plain)

    def _plain(self, node: UnresolvedComparisonNode) -> _Plain | None:
        """The comparison as ``name <op> literal`` or ``name <op> name``, or ``None`` where the language reads it as arithmetic.

        A side that is arithmetic makes it so, and so does a name that is a
        value — a parameter or an ``expressions:`` entry — against another,
        however plain the two look.
        """
        ns = self.ns
        name, right = _side_name(node.left), node.right
        value: float | str | None
        quoted = isinstance(right, KeywordNode)
        if isinstance(right, KeywordNode):
            value = right.value
        elif isinstance(right, ColumnNode):
            value = right.shown
        elif (literal := literal_number(right)) is not None:
            value = literal.value
        else:
            value = _side_name(right)
            if value is not None and (value in ns.bodies or ns.kind(value) == 'parameter'):
                return None
        if name is None or value is None or name in ns.bodies:
            return None
        return _Plain(name, node.op, value, quoted)

    def _expression_comparison(self, node: UnresolvedComparisonNode) -> ExpressionComparison | UnresolvedComparisonNode:
        """``expression <op> expression``: each side expanded, typed and held to what a mask may read.

        A side is read as an expression is — macros and named expressions
        expand, every operator and dim rule applies — except that it names no
        variable and no dual, since a mask is built before either exists.
        """
        ns, context = self.ns, self.context
        found = len(self.errors)
        sides: list[Expression] = []
        for side in (node.left, node.right):
            if isinstance(side, ColumnNode | KeywordNode):
                self.errors.append(_not_arithmetic(context, side))
                continue
            if any(isinstance(n, FunctionCallNode) and n.name == 'count' for n in nodes(side)):
                self.errors.append(
                    f'{context}: count() is not alone on the left of its comparison. '
                    f'Write count(<condition>, over=<dimension>) <op> <integer>.'
                )
                continue
            try:
                expanded = expand(side, ns, context)
            except ValueError as e:
                self.errors.append(prefixed(context, e))
                continue
            if (resolved := self._expressions.build(expanded)) is not None:
                sides.append(resolved)
        if len(self.errors) > found:
            return node
        assert len(sides) == 2, 'a side of a condition builds or refuses, since a condition holds no formal'
        dims: set[str] = set()
        for side in sides:
            if given := sorted(variables_of(side) & set(ns.spec.given.expressions)):
                self.errors.append(
                    f'{context}: a condition compares expressions, and one side reads the given expression '
                    f'{given[0]!r}. {GIVEN_IN_A_CONDITION}'
                )
            elif carries_variable(side):
                self.errors.append(
                    f'{context}: a condition compares expressions, and one side names a variable. Test only '
                    f'parameters and dimension coordinates.'
                )
            elif degree.calls_dual(side):
                self.errors.append(
                    f'{context}: a condition compares expressions, and one side reads a dual. Test only parameters '
                    f'and dimension coordinates.'
                )
            else:
                try:
                    degree.check_expression(side, context)
                    dims |= set(side.dims)
                except LanguageError as e:
                    self.errors.append(str(e))
        if len(self.errors) > found:
            return node
        left, right = sides
        if all(_is_number(side) for side in sides):
            self.errors.append(
                f"{context}: '{node.left} {node.op} {node.right}' compares two numbers. Name the parameter one "
                f'side stands for, or remove the comparison.'
            )
            return node
        return ExpressionComparison(left, node.op, right, sorted_dims(dims))

    def _position(
        self, call: FunctionCallNode, node: UnresolvedComparisonNode
    ) -> DimensionPosition | UnresolvedComparisonNode:
        """``position(dim[, within=relation[column]]) <op> i``: the name a dimension, the relation keyed over it."""
        ns, context = self.ns, self.context
        shape = _position_shape(call)
        if shape is None:
            self.errors.append(
                f'{context}: this position() call is not of the form '
                f'position(<dim>[, within=<relation>[<column>]]). Write it in that form.'
            )
            return node
        dimension, within = shape
        index = None if isinstance(node.right, ColumnNode | KeywordNode) else literal_number(node.right)
        if index is None or not index.value.is_integer():
            self.errors.append(
                f'{context}: position({dimension}) is compared against a value that is not a literal integer. '
                f'Write position({dimension}) {node.op} <integer>, where 0 is first and -1 is last.'
            )
            return node
        position = int(index.value)
        if dimension not in ns.dimensions:
            self.errors.append(
                f"{context}: position() counts along a dimension's coordinates, and "
                f"'{dimension}' is {_declared_as(ns, dimension)}. "
                f'{did_you_mean(dimension, ns.dimensions, label="Dimensions")}'
            )
            return node
        if ns.unordered(dimension):
            self.errors.append(unordered(context, f'position({dimension})', dimension))
            return node
        if within is None:
            return DimensionPosition(dimension, node.op, position)
        columns = self._expressions.columns_ref(within, 'position', 'within')
        partition = None if columns is None else self._expressions.partition(columns, 'position', dimension)
        if partition is None:
            return node
        return DimensionPosition(dimension, node.op, position, partition)

    def _plain_comparison(self, node: UnresolvedComparisonNode, plain: _Plain) -> Condition | UnresolvedConditionNode:
        """``name <op> literal``, or the one structural form ``relation <op> relation``."""
        ns, context = self.ns, self.context
        value = plain.value
        left_name, left_column = _split_column(plain.name)
        if not plain.quoted and isinstance(value, str):
            right_name, right_column = _split_column(value)
            if (rhs_kind := ns.kind(right_name)) is not None:
                if rhs_kind == 'relation' and ns.kind(left_name) == 'relation':
                    left = self._relation_column(left_name, left_column or None, plain.name, plain.op)
                    right = self._relation_column(right_name, right_column or None, value, plain.op)
                    if left is None or right is None:
                        return node
                    if (refusal := _relation_pair_error(context, plain, value, ns, left, right)) is not None:
                        self.errors.append(refusal)
                        return node
                    dims = tuple(sorted(ns.relations[left_name].dim(k) for k in ns.relations[left_name].key))
                    return RelationPairComparison(left_name, left, right_name, right, plain.op, dims)
                given = right_name in ns.spec.given.expressions
                self.errors.append(_declared_rhs_error(context, plain, value, rhs_kind, given=given))
                return node

        kind = ns.kind(left_name)
        if kind is None:
            self.errors.append(ns.unknown(left_name, context, allow_dims=True))
            return node
        if left_column and kind != 'relation':
            self.errors.append(
                f"{context}: '{plain.name}' reads a column of '{left_name}', which is {_declared_as(ns, left_name)}. "
                f'Only a relation has columns.'
            )
            return node
        column = None
        dtype: DeclaredDtype | None = None
        if kind == 'relation':
            column = self._relation_column(left_name, left_column or None, plain.name, plain.op)
            if column is None:
                return node
            dtype = ns.dtypes[ns.relations[left_name].dim(column)]
        elif kind in ('parameter', 'dimension'):
            dtype = ns.dtypes[left_name]
        if dtype is not None:
            typed = self._typed_literal(plain, dtype)
            if typed is None:
                return node
            value = typed

        match kind:
            case 'parameter':
                assert not isinstance(value, datetime.date)
                return ParameterComparison(left_name, plain.op, value, ns.leaf_dims[left_name])
            case 'dimension':
                return DimensionComparison(left_name, plain.op, value)
            case 'relation':
                assert column is not None
                shape = ns.relations[left_name]
                return RelationComparison(
                    left_name, column, plain.op, value, tuple(sorted(shape.dim(k) for k in shape.key))
                )
            case 'variable' if left_name in ns.spec.given.expressions:
                self.errors.append(
                    f"{context}: where references the given expression '{left_name}'. {GIVEN_IN_A_CONDITION}"
                )
            case 'variable':
                self.errors.append(
                    f"{context}: where references variable '{left_name}'. Test only parameters "
                    f'and dimension coordinates.'
                )
        return node

    def _relation_column(self, name: str, column: str | None, spelling: str, op: ComparisonOperator) -> str | None:
        """The value column a where-comparison on relation *name* reads, or the refusal.

        A comparison reads one value per coordinate, so the relation is keyed
        and the column is one the key determines; unsaid, it is the one value
        column where there is exactly one.
        """
        ns, context = self.ns, self.context
        shape = ns.relations[name]
        if not shape.values:
            self.errors.append(
                f"{context}: '{spelling}' compares a column of '{name}', which has every column in its key. "
                f"Declare that column under values:, or test the bare name '{name}' for whether a row exists."
            )
            return None
        if column is None:
            if len(shape.values) != 1:
                self.errors.append(
                    f"{context}: '{spelling}': '{name}' has {len(shape.values)} value columns ({list(shape.values)}), "
                    f'so name one: {name}[{shape.values[0]}].'
                )
                return None
            return shape.values[0]
        if column not in shape.roles:
            self.errors.append(
                f"{context}: '{spelling}': '{column}' is not a column of '{name}', whose columns are {list(shape.roles)}."
            )
            return None
        if column in shape.key:
            self.errors.append(
                f"{context}: '{spelling}': '{column}' is a key column of '{name}'. Compare the coordinate itself, "
                f'{shape.dim(column)} {op} ..., or a value column.'
            )
            return None
        return column

    def _inequality_rewrite(self, node: _Plain, dtype: DeclaredDtype) -> str:
        """What to write in place of an inequality on a value whose dtype does not define one.

        Only an ordered dimension has a place to select by, so only it is told
        about ``position()``; everywhere else that hint names a construct that
        cannot apply.
        """
        if dtype == 'bool':
            return f"Test the bare name, '{node.name}' or 'not {node.name}'"
        name = _split_column(node.name)[0]
        if self.ns.kind(name) == 'dimension' and not self.ns.unordered(name):
            return f'Select members by their place with position({name}) {node.op} n, or compare it with == or !='
        return 'Compare it with == or !=, or precompute the comparison as a boolean parameter'

    def _typed_literal(self, node: _Plain, dtype: DeclaredDtype) -> float | str | datetime.date | None:
        """The comparison's literal, checked against the declared dtype.

        Getting it wrong is silent: polars reads a datetime column against an
        integer as an epoch offset, so ``snapshot > 0`` drops every coordinate
        before 1970 without a word (#460). Returns ``None`` once it has recorded
        an error, so the caller leaves the node unresolved.
        """
        context = self.context
        value = node.value
        text = isinstance(value, str)

        if node.op not in ('==', '!=') and dtype not in _INEQUALITY_DTYPES:
            rewrite = self._inequality_rewrite(node, dtype)
            self.errors.append(
                f"{context}: '{node.name}' has dtype '{dtype}', on which {node.op} is not defined. {rewrite}."
            )
            return None

        if dtype == 'datetime':
            if not text:
                self.errors.append(
                    f"{context}: '{node.name}' is a datetime dimension, so comparing it to "
                    f'{value!r} compares against 1970-01-01. Quote an ISO date instead: '
                    f"{node.name} {node.op} '2030-01-01'."
                )
                return None
            try:
                return (
                    datetime.datetime.fromisoformat(value)
                    if _HAS_TIME.search(value)
                    else datetime.date.fromisoformat(value)
                )
            except ValueError:
                self.errors.append(
                    f"{context}: '{node.name}' is a datetime dimension and {value!r} is not an "
                    f"ISO date. Write '2030-01-01' or '2030-01-01T06:00'."
                )
                return None

        if dtype == 'str' and not text:
            self.errors.append(
                f"{context}: '{node.name}' has dtype 'str', so comparing it to the number "
                f'{value!r} matches no label. Quote it if it is one: {node.name} {node.op} '
                f"'{value:g}'."
            )
            return None
        if dtype in ('int', 'float', 'bool') and text:
            self.errors.append(
                f"{context}: '{node.name}' has dtype '{dtype}', so comparing it to the string "
                f'{value!r} matches nothing. Drop the quotes if it is a number.'
            )
            return None
        return value


#: An ISO literal carrying a time-of-day, which decides date vs datetime.
_HAS_TIME = re.compile(r'[T ]\d')

#: The dtypes on which a condition may use an inequality: <, <=, > or >=. A
#: ``str`` or ``bool`` compares only with == and !=.
_INEQUALITY_DTYPES: tuple[DeclaredDtype, ...] = ('float', 'int', 'datetime')


def _declared_as(ns: Namespace, name: str) -> str:
    kind = ns.kind(name)
    return f'a {kind}' if kind else 'not declared'


class _Plain(NamedTuple):
    """A where-comparison read as ``name <op> literal`` or ``name <op> name`` — the shape the dtype rules are written for.

    ``quoted`` says the right-hand side arrived in quotes, and so is a label
    rather than a name to look up.
    """

    name: str
    op: ComparisonOperator
    value: float | str
    quoted: bool


def _side_name_or_none(side: ArithmeticNode | ColumnNode | KeywordNode) -> str | None:
    """The bare name a side spells, or ``None`` — a quoted label is no name."""
    return side.name if isinstance(side, NameNode) else None


def _side_name(side: ArithmeticNode | ColumnNode) -> str | None:
    """The name a side of a where-comparison spells — bare or ``relation[column]`` — or ``None`` where it is arithmetic."""
    if isinstance(side, NameNode):
        return side.name
    if isinstance(side, ColumnNode):
        return side.shown
    return None


def _split_column(name: str) -> tuple[str, str]:
    """``relation[column]`` as its two names, and a bare name with an empty column: the one reader of a side's spelling."""
    relation, _, column = name.partition('[')
    return relation, column.removesuffix(']')


def _position_shape(call: FunctionCallNode) -> tuple[str, ArithmeticNode | None] | None:
    """``(dim, within)`` off a ``position(...)`` call, or ``None`` where the call is not of that shape."""
    if len(call.args) != 1 or not isinstance(call.args[0], NameNode) or set(call.kwargs) - {'within'}:
        return None
    return call.args[0].name, call.kwargs.get('within')


def _kwargs_error(
    context: str, name: str, kwargs: Mapping[str, ArithmeticNode], required: tuple[str, ...]
) -> str | None:
    """Why *kwargs* is not what *name* takes over a condition, or ``None`` where it is.

    A condition-reading call takes exactly the keywords named here. The
    arithmetic forms of these operators take more — an ``edge=``, a ``within=`` —
    and each is refused rather than ignored, since a condition answers the
    vacated coordinate itself and a grouped form has nobody asking for it yet.
    """
    missing = [key for key in required if key not in kwargs]
    if missing:
        return f'{context}: {name}(<condition>) needs {_listed([f"{key}=" for key in missing])}.'
    if extra := sorted(set(kwargs) - set(required)):
        return (
            f'{context}: {name}(<condition>) does not take {_listed([f"{key}=" for key in extra])}. '
            f'It takes only {_listed([f"{key}=" for key in required])}.'
        )
    return None


def _decided_count(op: str, value: float) -> str | None:
    """Whether comparing a count with *op* against *value* is settled by the count never being negative.

    Returns ``'every'`` where the comparison always holds, ``'no'`` where it
    never does, and ``None`` where the data decides.
    """
    if value < 0:
        return 'every' if op in ('>', '>=', '!=') else 'no'
    if value == 0 and op in ('>=', '<'):
        return 'every' if op == '>=' else 'no'
    return None


def _listed(items: list[str]) -> str:
    """``'a'``, ``'a' and 'b'``, ``'a', 'b' and 'c'`` — one rule, so every message reads the same."""
    quoted = [f"'{item}'" for item in items]
    if len(quoted) <= 1:
        return quoted[0] if quoted else 'nothing'
    return f'{", ".join(quoted[:-1])} and {quoted[-1]}'


def _is_number(side: Expression) -> bool:
    """Whether *side* is arithmetic over literals alone — a value the language can fold, and a condition may not test."""
    return all(isinstance(n, Constant | Negate | Add | Multiply | Divide | Power) for n in walk(side))


def _not_arithmetic(context: str, side: ColumnNode | KeywordNode) -> str:
    """Why a relation column or a quoted label may not stand on a side of a comparison of expressions."""
    if isinstance(side, ColumnNode):
        return (
            f"{context}: '{side.shown}' is a relation column in arithmetic. Compare it alone against a literal "
            f'or a column, or carry the value in a parameter.'
        )
    return (
        f"{context}: '{side.value}' is a quoted label, which is compared against one name. Put the name alone on "
        f'the other side, or drop the quotes if it is a number.'
    )


def _declared_rhs_error(context: str, node: _Plain, value: str, kind: str, *, given: bool = False) -> str:
    """Why the right-hand side of a where-comparison may not name a variable, a relation or a dimension.

    A given expression is filed with the variables, and *given* says the name is one.
    """
    comparison = f"'{node.name} {node.op} {value}'"
    if given:
        return f'{context}: {comparison} compares against the given expression {value!r}. {GIVEN_IN_A_CONDITION}'
    if kind == 'variable':
        return (
            f'{context}: {comparison} compares against variable {value!r}. '
            f'Test only parameters and dimension coordinates.'
        )
    if kind == 'relation':
        return (
            f'{context}: {comparison} compares {node.name!r} against relation {value!r}. Compare against a '
            f'literal, or put a relation over the same dimensions on the left.'
        )
    return (
        f'{context}: {comparison} compares against dimension {value!r}, and two dimensions cannot be '
        f'compared. If {value!r} is a coordinate, rename the dimension or the coordinate.'
    )


def _relation_pair_error(context: str, node: _Plain, other: str, ns: Namespace, left: str, right: str) -> str | None:
    """Why two relation columns may not be compared, or ``None`` where they may.

    Both relations are read at their keys, so the keys must be over the same
    dimensions or no row carries both; and the two columns must be over one
    dimension, or no value of one is ever a value of the other. Both wrong
    answers are silent, and a build's data library decides which one. Two
    columns over a dimension outside ``_INEQUALITY_DTYPES`` compare only with
    == and !=.
    """
    comparison = f"'{node.name} {node.op} {other}'"
    left_name, right_name = _split_column(node.name)[0], _split_column(other)[0]
    ls, rs = ns.relations[left_name], ns.relations[right_name]
    left_keys, right_keys = {ls.dim(k) for k in ls.key}, {rs.dim(k) for k in rs.key}
    if left_keys != right_keys:
        return (
            f'{context}: {comparison} compares relations keyed over different dimensions '
            f"('{left_name}' by {sorted(left_keys)}, '{right_name}' by {sorted(right_keys)}). Compare relations "
            f'whose keys are over the same dimensions.'
        )
    if ls.dim(left) != rs.dim(right):
        return (
            f"{context}: {comparison} compares '{node.name}' (a column over '{ls.dim(left)}') with "
            f"'{other}' (a column over '{rs.dim(right)}'). Compare two columns over the same dimension."
        )
    dtype = ns.dtypes[ls.dim(left)]
    if node.op not in ('==', '!=') and dtype not in _INEQUALITY_DTYPES:
        return (
            f"{context}: {comparison} compares two columns over '{ls.dim(left)}', of dtype '{dtype}', "
            f'on which {node.op} is not defined. Compare them with == or !=, or precompute the comparison as a '
            'boolean parameter.'
        )
    return None
