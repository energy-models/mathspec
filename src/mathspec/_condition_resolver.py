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
from typing import TYPE_CHECKING, NamedTuple

import mathspec._degree as degree
from mathspec._dimensions import join_dims, sorted_dims
from mathspec._divisors import zero_divisor_refusals
from mathspec._expression_resolver import ExpressionResolver, condition_compared
from mathspec._syntax import (
    AndNode,
    BooleanNode,
    ColumnsNode,
    ComparisonNode,
    FunctionCallNode,
    KeywordNode,
    NameListNode,
    NameNode,
    NotNode,
    OrNode,
    ParsedNode,
    literal_number,
    nodes,
)
from mathspec.errors import DimensionError, LanguageError, SchemaError, did_you_mean, unordered
from mathspec.program import (
    Add,
    And,
    BooleanLiteral,
    ComparisonOperator,
    Condition,
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
    VariableDefined,
    carries_variable,
    variables_of,
    walk,
)

if TYPE_CHECKING:
    from mathspec._resolution import Namespace
    from mathspec.program import DeclaredDtype

GIVEN_IN_A_CONDITION = (
    'A given expression may hold a variable, and a condition is read before variables exist — it may test '
    'parameters and dimension coordinates only.'
)

_CONDITION_CALLS: dict[str, tuple[tuple[str, ...], str]] = {
    'shift': (('along', 'offset'), 'shift(<condition>, along=<dimension>, offset=<integer>)'),
    'at': (('by',), 'at(<condition>, by=<relation>[<column>])'),
    'count': (('over',), 'count(<condition>, over=<dimension>) <op> <integer>'),
}


class _Entry(NamedTuple):
    """A side of a comparison that names one entry: bare, or as one column of a relation."""

    name: str
    column: str | None = None

    def __str__(self) -> str:
        return self.name if self.column is None else f'{self.name}[{self.column}]'


class _Plain(NamedTuple):
    """A comparison read as ``name <op> literal`` or ``name <op> name`` — the shape the dtype rules are written for.

    ``value`` is a number, a quoted label, or a name still to look up.
    """

    left: _Entry
    op: ComparisonOperator
    value: float | str | _Entry


@dataclass(frozen=True)
class ConditionResolver:
    """One resolution walk over a condition, and the things every step of it reads.

    A node that cannot be typed comes back as ``None`` with its refusal
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

    def build(self, node: ParsedNode) -> Condition | None:
        """The condition *node* stands for, or ``None`` with its refusal appended."""
        if isinstance(node, BooleanNode):
            return BooleanLiteral(node.value)
        if isinstance(node, NameNode):
            return self._bare_name(node)
        if isinstance(node, ComparisonNode):
            return self._comparison(node)
        if isinstance(node, FunctionCallNode):
            return self._condition_call(node)
        if isinstance(node, NotNode):
            inner = self.build(node.operand)
            return None if inner is None else Not(inner)
        if isinstance(node, AndNode | OrNode):
            left, right = self.build(node.left), self.build(node.right)
            if left is None or right is None:
                return None
            return And(left, right) if isinstance(node, AndNode) else Or(left, right)
        self.errors.append(_not_a_condition(self.context, node))
        return None

    @property
    def conditions(self) -> frozenset[str]:
        """Every named condition this file declares or is given."""
        return self.ns.conditions | self.ns.given_conditions

    def _bare_name(self, node: NameNode) -> Condition | None:
        """A bare name: a named condition's body, a parameter's or relation's definedness, or a variable's existence."""
        ns, context = self.ns, self.context
        if node.name in ns.conditions:
            try:
                return ns.condition(node.name, context)
            except SchemaError as e:
                self.errors.append(str(e))
                return None
        match ns.kind(node.name):
            case None:
                self.errors.append(ns.unknown(node.name, context, allow_dims=True))
            case 'parameter':
                declared = ns.spec.parameters.get(node.name)
                if (
                    declared is not None
                    and declared.missing == 'refused'
                    and declared.where is None
                    and declared.dtype in ('int', 'str')
                ):
                    rewrite = (
                        f'Declare `missing: absent`, or compare the label: where: "{node.name} == \'...\'".'
                        if declared.dtype == 'str'
                        else f'Declare `missing: absent` or a value, or compare the value: where: "{node.name} > 0".'
                    )
                    self.errors.append(
                        f"{context}: '{node.name}' is declared dtype: {declared.dtype} and missing: refused, so it "
                        f'has a row at every coordinate and the bare name is true at every coordinate — the mask '
                        f'has no effect. {rewrite}'
                    )
                    return None
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
                    return None
                return RelationDefined(node.name, dims)
            case 'variable':
                if node.name != self.self_variable:
                    return VariableDefined(node.name, ns.leaf_dims[node.name])
                self.errors.append(
                    f"{context}: variable '{node.name}' tests itself in its own where. "
                    f'Test a parameter, or another variable.'
                )
        return None

    def _operand(self, call: FunctionCallNode) -> Mask | None:
        """The one condition *call* reads, held to the keywords ``_CONDITION_CALLS`` gives the operator over a condition.

        The arithmetic forms of these operators take more — an ``edge=``, a
        ``within=`` — and each is refused rather than ignored, since a
        condition answers the vacated coordinate itself and a grouped form
        has nobody asking for it yet.
        """
        name = call.name.lower()
        required, usage = _CONDITION_CALLS[name]
        if len(call.args) != 1:
            self.errors.append(
                f'{self.context}: {name}() over a condition reads one condition, and this call passes '
                f'{len(call.args)}. Write {usage}.'
            )
            return None
        if (condition := self.build(call.args[0])) is None:
            return None
        keys = [f'{key}=' for key in required]
        if missing := [f'{key}=' for key in required if key not in call.kwargs]:
            self.errors.append(f'{self.context}: {name}(<condition>) needs {_listed(missing)}.')
            return None
        if extra := sorted(set(call.kwargs) - set(required)):
            self.errors.append(
                f'{self.context}: {name}(<condition>) does not take {_listed([f"{key}=" for key in extra])}. '
                f'It takes only {_listed(keys)}.'
            )
            return None
        return Mask(condition)

    def _condition_call(self, node: FunctionCallNode) -> Condition | None:
        """``shift(<condition>, along=, offset=)`` or ``at(<condition>, by=relation[column])`` — the two operators that read a condition and answer one.

        ``count`` answers a number, so it stands on a comparison's side and
        [`_count`][] reads it there. Anything else naming a condition is
        refused here rather than resolved into arithmetic it cannot be.
        """
        context = self.context
        if node.name == 'count':
            self.errors.append(
                f'{context}: count() answers a number, and a condition is true or false. Compare it: '
                f'count(<condition>, over=<dimension>) <op> <integer>.'
            )
            return None
        if node.name not in ('shift', 'at'):
            self.errors.append(
                f"{context}: '{node.name}()' does not read a condition, and only shift(), at() and count() do. "
                f'Compare the condition, or name a parameter carrying it.'
            )
            return None
        if (mask := self._operand(node)) is None:
            return None
        if node.name == 'at':
            return self._joined(node, mask)
        along = node.kwargs['along']
        offset = literal_number(node.kwargs['offset'])
        if not isinstance(along, NameNode) or self.ns.kind(along.name) != 'dimension':
            self.errors.append(
                f'{context}: shift(<condition>, along=) is not a declared dimension. Name a declared dimension.'
            )
            return None
        if offset is None or not offset.value.is_integer():
            self.errors.append(
                f'{context}: shift(<condition>, offset=) is not a literal whole number. Write an integer.'
            )
            return None
        if along.name not in mask.dims:
            self.errors.append(
                f"{context}: shift(<condition>, along='{along.name}') steps along a dimension the condition does "
                f'not read. Step along one of {_listed(list(mask.dims))}.'
            )
            return None
        if self.ns.unordered(along.name):
            self.errors.append(unordered(context, f'shift(<condition>, along={along.name})', along.name))
            return None
        return TranslatedCondition(mask, along.name, int(offset.value), mask.dims)

    def _joined(self, node: FunctionCallNode, mask: Mask) -> Condition | None:
        """``at(<condition>, by=relation[column])`` — the condition read through a relation, as ``at`` reads an array.

        The columns are read by the rules an expression's ``at`` is, so the one
        refusal a file meets for a bad read is the same in a ``where:`` and in
        an expression.
        """
        columns = self._expressions.columns_ref(node.kwargs['by'], 'at', 'by')
        by = None if columns is None else self._expressions.lookup(columns, frozenset(mask.dims))
        if by is None:
            return None
        try:
            dims = join_dims(by, frozenset(mask.dims), self.context, 'the condition')
        except DimensionError as refusal:
            self.errors.append(self.ns.refused_dims(refusal))
            return None
        return JoinedCondition(mask, by, sorted_dims(dims))

    def _count(self, call: FunctionCallNode, node: ComparisonNode) -> Condition | None:
        """``count(<condition>, over=<dim>) <op> <integer>`` — how many coordinates the condition admits.

        The reduction leaves every dim but ``over``, so the count is one
        number per remaining coordinate and a claim about each group needs no
        word for the group.
        """
        context = self.context
        if (mask := self._operand(call)) is None:
            return None
        over = call.kwargs['over']
        if not isinstance(over, NameNode) or self.ns.kind(over.name) != 'dimension':
            self.errors.append(
                f'{context}: count(<condition>, over=) is not a declared dimension. Name a declared dimension.'
            )
            return None
        value = literal_number(node.right)
        if value is None or not value.value.is_integer():
            self.errors.append(
                f'{context}: a count is compared against a value that is not a literal whole number. '
                f'Write count(…, over={over.name}) {node.op} <integer>.'
            )
            return None
        if (decided := _decided_count(node.op, value.value)) is not None:
            self.errors.append(
                f'{context}: count(…, over={over.name}) {node.op} {value} holds at {decided} coordinate, because '
                f'a count is never negative. Delete the comparison, or write the bound it means.'
            )
            return None
        if over.name not in mask.dims:
            self.errors.append(
                f"{context}: count(<condition>, over='{over.name}') counts along a dimension the condition does "
                f'not read. Count along one of {_listed(list(mask.dims))}.'
            )
            return None
        dims = tuple(d for d in mask.dims if d != over.name)
        return CountComparison(mask, over.name, node.op, value.value, dims)

    def _comparison(self, node: ComparisonNode) -> Condition | None:
        """``side <op> side``, read for what each side is.

        A ``count()`` or a ``position()`` call on the left is the form of
        that name. A name against a literal or a second column is the plain
        form the dtype rules are written for, unless a side names a parameter
        or an ``expressions:`` entry against the other, which is arithmetic
        however plain it looks. Everything else is a comparison of
        expressions.
        """
        if isinstance(node.left, FunctionCallNode) and node.left.name.lower() == 'count':
            return self._count(node.left, node)
        if isinstance(node.left, FunctionCallNode) and node.left.name == 'position':
            return self._position(node.left, node)
        for side in (node.left, node.right):
            if isinstance(side, ColumnsNode) and len(side.columns) != 1:
                each = ' AND '.join(f'{side.relation}[{column}] == …' for column in side.columns)
                self.errors.append(
                    f"{self.context}: '{side}' names {len(side.columns)} columns, and a comparison reads one "
                    f"column of '{side.relation}'. Compare each column on its own: {each}."
                )
                return None
            if isinstance(side, NameNode) and side.name in self.conditions:
                self.errors.append(condition_compared(side.name, self.context))
                return None
        plain = self._plain(node)
        if plain is None:
            return self._expression_comparison(node)
        return self._plain_comparison(plain)

    def _plain(self, node: ComparisonNode) -> _Plain | None:
        """The comparison as ``name <op> literal`` or ``name <op> name``, or ``None`` where the language reads it as arithmetic.

        A side that is arithmetic makes it so, and so does a name that is a
        value — a parameter or an ``expressions:`` entry — against another,
        however plain the two look.
        """
        ns = self.ns
        left, right = _entry(node.left), node.right
        value: float | str | _Entry | None
        if isinstance(right, KeywordNode):
            value = right.value
        elif (literal := literal_number(right)) is not None:
            value = literal.value
        else:
            value = _entry(right)
            if (
                value is not None
                and value.column is None
                and (value.name in ns.bodies or ns.kind(value.name) == 'parameter')
            ):
                return None
        if left is None or value is None or (left.column is None and left.name in ns.bodies):
            return None
        return _Plain(left, node.op, value)

    def _expression_comparison(self, node: ComparisonNode) -> ExpressionComparison | None:
        """``expression <op> expression``: each side expanded, typed and held to what a mask may read.

        A side is read as an expression is — macros and named expressions
        expand, every operator and dim rule applies — except that it names no
        variable and no dual, since a mask is built before either exists.
        """
        ns, context = self.ns, self.context
        found = len(self.errors)
        sides: list[Expression] = []
        for side in (node.left, node.right):
            if isinstance(side, ColumnsNode | KeywordNode):
                self.errors.append(_not_arithmetic(context, side))
                continue
            if any(isinstance(n, FunctionCallNode) and n.name == 'count' for n in nodes(side)):
                self.errors.append(
                    f'{context}: count() is not alone on the left of its comparison. '
                    f'Write count(<condition>, over=<dimension>) <op> <integer>.'
                )
                continue
            if (resolved := self._expressions.build(side)) is not None:
                sides.append(resolved)
        if len(self.errors) > found:
            return None
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
                self.errors.extend(zero_divisor_refusals(side, context, ns.spec.parameters, {}))
        if len(self.errors) > found:
            return None
        left, right = sides
        if all(_is_number(side) for side in sides):
            self.errors.append(
                f"{context}: '{node.left} {node.op} {node.right}' compares two numbers. Name the parameter one "
                f'side stands for, or remove the comparison.'
            )
            return None
        return ExpressionComparison(left, node.op, right, sorted_dims(dims))

    def _position(self, call: FunctionCallNode, node: ComparisonNode) -> DimensionPosition | None:
        """``position(dim[, within=relation[column]]) <op> i``: the name a dimension, the relation keyed over it."""
        ns, context = self.ns, self.context
        shape = _position_shape(call)
        if shape is None:
            self.errors.append(
                f'{context}: this position() call is not of the form '
                f'position(<dim>[, within=<relation>[<column>]]). Write it in that form.'
            )
            return None
        dimension, within = shape
        index = literal_number(node.right)
        if index is None or not index.value.is_integer():
            self.errors.append(
                f'{context}: position({dimension}) is compared against a value that is not a literal integer. '
                f'Write position({dimension}) {node.op} <integer>, where 0 is first and -1 is last.'
            )
            return None
        position = int(index.value)
        if dimension not in ns.dimensions:
            self.errors.append(
                f"{context}: position() counts along a dimension's coordinates, and "
                f"'{dimension}' is {_declared_as(ns, dimension)}. "
                f'{did_you_mean(dimension, ns.dimensions, label="Dimensions")}'
            )
            return None
        if ns.unordered(dimension):
            self.errors.append(unordered(context, f'position({dimension})', dimension))
            return None
        if within is None:
            return DimensionPosition(dimension, node.op, position)
        columns = self._expressions.columns_ref(within, 'position', 'within')
        partition = None if columns is None else self._expressions.partition(columns, 'position', dimension)
        if partition is None:
            return None
        return DimensionPosition(dimension, node.op, position, partition)

    def _plain_comparison(self, plain: _Plain) -> Condition | None:
        """``name <op> literal``, or the one structural form ``relation <op> relation``.

        A bare word on the right that the file declares nowhere is the label
        it spells, as ``tech == wind`` is.
        """
        ns, context = self.ns, self.context
        left, op = plain.left, plain.op
        named = [side for side in (left, plain.value) if isinstance(side, _Entry)]
        for side in named:
            if side.column is not None and (kind := ns.kind(side.name)) != 'relation':
                self.errors.append(
                    ns.unknown(side.name, context, allow_dims=True)
                    if kind is None
                    else f"{context}: '{side}' reads a column of '{side.name}', which is a {kind}. "
                    f'Only a relation has columns.'
                )
                return None
        value: float | str
        if not isinstance(plain.value, _Entry):
            value = plain.value
        elif (rhs_kind := ns.kind(plain.value.name)) is None:
            value = plain.value.name
        elif rhs_kind == 'relation' and ns.kind(left.name) == 'relation':
            return self._relation_pair(left, op, plain.value)
        else:
            given = plain.value.name in ns.spec.given.expressions
            self.errors.append(_declared_rhs_error(context, left, op, plain.value, rhs_kind, given=given))
            return None

        kind = ns.kind(left.name)
        if kind is None:
            self.errors.append(ns.unknown(left.name, context, allow_dims=True))
            return None
        column = None
        dtype: DeclaredDtype | None = None
        labelled: str | None = None
        if kind == 'relation':
            column = self._relation_column(left, op)
            if column is None:
                return None
            labelled = ns.relations[left.name].dim(column)
            dtype = ns.dtypes[labelled]
        elif kind in ('parameter', 'dimension'):
            dtype = ns.dtypes[left.name]
            labelled = left.name if kind == 'dimension' else None
        typed: float | str | datetime.date = value
        if dtype is not None:
            checked = self._typed_literal(left, op, value, dtype)
            if checked is None:
                return None
            typed = checked
        if labelled in ns.one_of and typed not in ns.one_of[labelled]:
            self.errors.append(
                f"{context}: {typed!r} is not a label of '{labelled}', which allows only "
                f"{list(ns.one_of[labelled])}. Write one of them, or add {typed!r} to the one_of of '{labelled}'."
            )
            return None

        match kind:
            case 'parameter':
                assert not isinstance(typed, datetime.date)
                return ParameterComparison(left.name, op, typed, ns.leaf_dims[left.name])
            case 'dimension':
                return DimensionComparison(left.name, op, typed)
            case 'relation':
                assert column is not None
                shape = ns.relations[left.name]
                return RelationComparison(left.name, column, op, typed, tuple(sorted(shape.dim(k) for k in shape.key)))
            case 'variable' if left.name in ns.spec.given.expressions:
                self.errors.append(
                    f"{context}: where references the given expression '{left.name}'. {GIVEN_IN_A_CONDITION}"
                )
            case 'variable':
                self.errors.append(
                    f"{context}: where references variable '{left.name}'. Test only parameters "
                    f'and dimension coordinates.'
                )
        return None

    def _relation_pair(self, left: _Entry, op: ComparisonOperator, right: _Entry) -> RelationPairComparison | None:
        """``relation[a] <op> relation[b]``: a value column of each, read at keys over the same dimensions."""
        ns = self.ns
        left_column, right_column = self._relation_column(left, op), self._relation_column(right, op)
        if left_column is None or right_column is None:
            return None
        refusal = _relation_pair_error(self.context, left, op, right, ns, left_column, right_column)
        if refusal is not None:
            self.errors.append(refusal)
            return None
        shape = ns.relations[left.name]
        dims = tuple(sorted(shape.dim(k) for k in shape.key))
        return RelationPairComparison(left.name, left_column, right.name, right_column, op, dims)

    def _relation_column(self, side: _Entry, op: ComparisonOperator) -> str | None:
        """The value column a where-comparison on the relation *side* names reads, or the refusal.

        A comparison reads one value per coordinate, so the relation is keyed
        and the column is one the key determines; unsaid, it is the one value
        column where there is exactly one.
        """
        context, name, column, spelling = self.context, side.name, side.column, str(side)
        shape = self.ns.relations[name]
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

    def _inequality_rewrite(self, left: _Entry, op: ComparisonOperator, dtype: DeclaredDtype) -> str:
        """What to write in place of an inequality on a value whose dtype does not define one.

        Only an ordered dimension has a place to select by, so only it is told
        about ``position()``; everywhere else that hint names a construct that
        cannot apply.
        """
        if dtype == 'bool':
            return f"Test the bare name, '{left}' or 'not {left}'"
        name = left.name
        if self.ns.kind(name) == 'dimension' and not self.ns.unordered(name):
            return f'Select members by their place with position({name}) {op} n, or compare it with == or !='
        return 'Compare it with == or !=, or precompute the comparison as a boolean parameter'

    def _typed_literal(
        self, left: _Entry, op: ComparisonOperator, value: float | str, dtype: DeclaredDtype
    ) -> float | str | datetime.date | None:
        """The comparison's literal, checked against the declared dtype.

        Getting it wrong is silent: polars reads a datetime column against an
        integer as an epoch offset, so ``snapshot > 0`` drops every coordinate
        before 1970 without a word (#460). Returns ``None`` once it has recorded
        an error.
        """
        context = self.context

        if op not in ('==', '!=') and dtype not in _INEQUALITY_DTYPES:
            rewrite = self._inequality_rewrite(left, op, dtype)
            self.errors.append(f"{context}: '{left}' has dtype '{dtype}', on which {op} is not defined. {rewrite}.")
            return None

        if dtype == 'datetime':
            if not isinstance(value, str):
                self.errors.append(
                    f"{context}: '{left}' is a datetime dimension, so comparing it to "
                    f'{value!r} compares against 1970-01-01. Quote an ISO date instead: '
                    f"{left} {op} '2030-01-01'."
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
                    f"{context}: '{left}' is a datetime dimension and {value!r} is not an "
                    f"ISO date. Write '2030-01-01' or '2030-01-01T06:00'."
                )
                return None

        if dtype == 'str' and not isinstance(value, str):
            self.errors.append(
                f"{context}: '{left}' has dtype 'str', so comparing it to the number "
                f'{value!r} matches no label. Quote it if it is one: {left} {op} '
                f"'{value:g}'."
            )
            return None
        if dtype in ('int', 'float', 'bool') and isinstance(value, str):
            self.errors.append(
                f"{context}: '{left}' has dtype '{dtype}', so comparing it to the string "
                f'{value!r} matches nothing. Drop the quotes if it is a number.'
            )
            return None
        return value


_HAS_TIME = re.compile(r'[T ]\d')

_INEQUALITY_DTYPES: tuple[DeclaredDtype, ...] = ('float', 'int', 'datetime')


def _declared_as(ns: Namespace, name: str) -> str:
    kind = ns.kind(name)
    return f'a {kind}' if kind else 'not declared'


def _entry(side: ParsedNode) -> _Entry | None:
    """The entry a side of a comparison names — bare, or as one column of a relation — or ``None`` where it is anything else."""
    if isinstance(side, NameNode):
        return _Entry(side.name)
    if isinstance(side, ColumnsNode) and len(side.columns) == 1:
        return _Entry(side.relation, side.columns[0])
    return None


def _position_shape(call: FunctionCallNode) -> tuple[str, ParsedNode | None] | None:
    """``(dim, within)`` off a ``position(...)`` call, or ``None`` where the call is not of that shape."""
    if len(call.args) != 1 or not isinstance(call.args[0], NameNode) or set(call.kwargs) - {'within'}:
        return None
    return call.args[0].name, call.kwargs.get('within')


def _not_a_condition(context: str, node: ParsedNode) -> str:
    """Why *node* may not stand where a condition goes: a label, a list and a column test nothing, and arithmetic is a number."""
    if isinstance(node, KeywordNode):
        return (
            f'{context}: {node} is a quoted label, which is compared against one name. Write the name and the '
            f'comparison before it, as in tech == {node}.'
        )
    if isinstance(node, NameListNode):
        return (
            f'{context}: [{", ".join(node.names)}] is a list of names, which is allowed only as an operator '
            f'argument. Name one entry, or compare one.'
        )
    if isinstance(node, ColumnsNode):
        return (
            f"{context}: '{node}' names a column of '{node.relation}' and tests nothing. Compare it, as in "
            f"{node} == ..., or test the bare name '{node.relation}' for whether a row exists."
        )
    return f'{context}: \'{node}\' is a number, and a condition is true or false. Compare it: where: "{node} > 0".'


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


def _not_arithmetic(context: str, side: ColumnsNode | KeywordNode) -> str:
    """Why a relation column or a quoted label may not stand on a side of a comparison of expressions."""
    if isinstance(side, ColumnsNode):
        return (
            f"{context}: '{side}' is a relation column in arithmetic. Compare it alone against a literal "
            f'or a column, or carry the value in a parameter.'
        )
    return (
        f"{context}: '{side.value}' is a quoted label, which is compared against one name. Put the name alone on "
        f'the other side, or drop the quotes if it is a number.'
    )


def _declared_rhs_error(
    context: str, left: _Entry, op: ComparisonOperator, right: _Entry, kind: str, *, given: bool = False
) -> str:
    """Why the right-hand side of a where-comparison may not name a variable, a relation or a dimension.

    A given expression is filed with the variables, and *given* says the name is one.
    """
    value = str(right)
    comparison = f"'{left} {op} {value}'"
    if given:
        return f'{context}: {comparison} compares against the given expression {value!r}. {GIVEN_IN_A_CONDITION}'
    if kind == 'variable':
        return (
            f'{context}: {comparison} compares against variable {value!r}. '
            f'Test only parameters and dimension coordinates.'
        )
    if kind == 'relation':
        return (
            f'{context}: {comparison} compares {str(left)!r} against relation {value!r}. Compare against a '
            f'literal, or put a relation over the same dimensions on the left.'
        )
    return (
        f'{context}: {comparison} compares against dimension {value!r}, and two dimensions cannot be '
        f'compared. If {value!r} is a coordinate, rename the dimension or the coordinate.'
    )


def _relation_pair_error(
    context: str,
    left: _Entry,
    op: ComparisonOperator,
    right: _Entry,
    ns: Namespace,
    left_column: str,
    right_column: str,
) -> str | None:
    """Why two relation columns may not be compared, or ``None`` where they may.

    Both relations are read at their keys, so the keys must be over the same
    dimensions or no row carries both; and the two columns must be over one
    dimension, or no value of one is ever a value of the other. Both wrong
    answers are silent, and a build's data library decides which one. Two
    columns over a dimension outside ``_INEQUALITY_DTYPES`` compare only with
    == and !=.
    """
    comparison = f"'{left} {op} {right}'"
    left_name, right_name = left.name, right.name
    ls, rs = ns.relations[left_name], ns.relations[right_name]
    left_keys, right_keys = {ls.dim(k) for k in ls.key}, {rs.dim(k) for k in rs.key}
    if left_keys != right_keys:
        return (
            f'{context}: {comparison} compares relations keyed over different dimensions '
            f"('{left_name}' by {sorted(left_keys)}, '{right_name}' by {sorted(right_keys)}). Compare relations "
            f'whose keys are over the same dimensions.'
        )
    if ls.dim(left_column) != rs.dim(right_column):
        return (
            f"{context}: {comparison} compares '{left}' (a column over '{ls.dim(left_column)}') with "
            f"'{right}' (a column over '{rs.dim(right_column)}'). Compare two columns over the same dimension."
        )
    dtype = ns.dtypes[ls.dim(left_column)]
    if op not in ('==', '!=') and dtype not in _INEQUALITY_DTYPES:
        return (
            f"{context}: {comparison} compares two columns over '{ls.dim(left_column)}', of dtype '{dtype}', "
            f'on which {op} is not defined. Compare them with == or !=, or precompute the comparison as a '
            'boolean parameter.'
        )
    return None
