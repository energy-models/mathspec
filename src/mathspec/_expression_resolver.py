# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The expression walk of name resolution: an arithmetic syntax tree into the program's expression nodes.

Every operator call is read here — its shape against [`BUILTINS`][],
its dimension and relation arguments against the namespace — and the node it
stands for is built. [`mathspec.resolution`][] holds the namespace and the
doors that call this.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never, cast

from mathspec._expression_parser import (
    MAX_DEPTH,
    ArithmeticNode,
    BinaryOperatorNode,
    ColumnsNode,
    FunctionCallNode,
    KeywordNode,
    NameListNode,
    NameNode,
    NumberNode,
    UnaryOperatorNode,
    depth,
    literal_number,
    names_in,
    shown,
)
from mathspec.dimensions import dims_of
from mathspec.errors import DimensionError, SchemaError, did_you_mean, unordered
from mathspec.operators import (
    AMOUNTS,
    BUILTINS,
    EDGE_WRAP,
    call_shape_error,
    edge_error,
    unknown_operator_message,
)
from mathspec.program import (
    Add,
    Axis,
    Constant,
    Divide,
    Dual,
    Expression,
    Join,
    JoinColumns,
    Multiply,
    Negate,
    Parameter,
    Partition,
    Power,
    RelationDeclaration,
    Sum,
    Translate,
    Variable,
    WindowSum,
    carries_variable,
    children,
)
from mathspec.spec import NUMERIC_DTYPES

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mathspec.resolution import Namespace


#: An ``edge=`` as a translation carries it: whether it wraps, and the number
#: the vacated positions contribute where it does not.
_Edge = tuple[bool, float | None]

#: How deep a resolved tree may be, with every named expression it reads
#: written in. Every pass after resolution recurses over this tree. The limit
#: is three times what one text may nest, because a text reads other texts: a
#: chain of 200 entries survived every pass on a default stack and 250 did not
#: (#643).
MAX_RESOLVED_DEPTH = 3 * MAX_DEPTH


@dataclass(frozen=True)
class ExpressionResolver:
    """One resolution walk over an expression, and the three things every step of it reads.

    A node that cannot be built comes back as ``None`` with its refusal
    appended to ``errors``; every sibling is still read, so a declaration
    with two faults reports both. ``formals`` are a macro template's formals:
    a formal has no kind until a call site binds it, so a node one stands
    under is ``None`` with nothing appended.
    """

    ns: Namespace
    context: str
    errors: list[str]
    formals: frozenset[str] = frozenset()

    def _formal(self, value: ArithmeticNode) -> bool:
        """Whether *value* is a formal, left for the call site to bind."""
        return isinstance(value, NameNode) and value.name in self.formals

    def build(self, node: ArithmeticNode) -> Expression | None:
        """The program tree *node* stands for, held to [`MAX_RESOLVED_DEPTH`][] before anything walks it.

        The depth is measured with every named expression written in, since
        that is the tree every later pass recurses over, and measured with an
        explicit stack, since a recursion would be the crash it prevents.
        """
        resolved = self.arith(node)
        if resolved is None or (found := depth(resolved, children)) <= MAX_RESOLVED_DEPTH:
            return resolved
        self.errors.append(
            f'{self.context}: the expression nests {found} levels deep, with its named expressions written in, '
            f'and the limit is {MAX_RESOLVED_DEPTH}. Write the terms as one sum() over a dimension, or '
            f'precompute the deepest part as a parameter.'
        )
        return None

    def arith(self, node: ArithmeticNode) -> Expression | None:
        """The program node *node* stands for, or ``None``.

        A quoted keyword or a name list in arithmetic arrives through a macro
        formal bound to one.
        """
        if isinstance(node, NumberNode):
            return Constant(node.value)
        if isinstance(node, NameNode):
            return self._name(node)
        if isinstance(node, UnaryOperatorNode):
            operand = self.arith(node.operand)
            if operand is None:
                return None
            return Negate(operand) if node.op == '-' else operand
        if isinstance(node, BinaryOperatorNode):
            return self._binary(node)
        if isinstance(node, FunctionCallNode):
            return self._call(node)
        if isinstance(node, KeywordNode):
            self.errors.append(
                f'{self.context}: {node.value!r} is a quoted keyword, which is allowed only as an operator '
                f"argument, such as edge='wrap'. Write names and numbers without quotes."
            )
            return None
        if isinstance(node, NameListNode):
            self.errors.append(
                f'{self.context}: {node} is a list of names, which is allowed only as an operator argument, '
                f'such as over=[snapshot, generator]. Write the terms out and add them.'
            )
            return None
        if isinstance(node, ColumnsNode):
            self.errors.append(
                f'{self.context}: {node} names columns of a relation, which is allowed only as an operator '
                f'argument, such as at(x, by={node}). A relation is not a value.'
            )
            return None
        assert_never(node)

    def _binary(self, node: BinaryOperatorNode) -> Expression | None:
        """A subtraction is an addition of the negation, so a program has one additive node."""
        left, right = self.arith(node.left), self.arith(node.right)
        if left is None or right is None:
            return None
        match node.op:
            case '+':
                return Add(left, right)
            case '-':
                return Add(left, Negate(right))
            case '*':
                return Multiply(left, right)
            case '/':
                return Divide(left, right)
            case '**':
                return Power(left, right)
            case _:
                assert_never(node.op)

    def _name(self, node: NameNode) -> Expression | None:
        """A bare name as the variable, parameter or named expression it declares; a dimension or relation is not a value.

        A named expression arrives as the one node [`Namespace.named`][]
        built for it; the cast is the one place a
        [`Named`][mathspec.program.Named] enters a tree typed as a program's,
        which lowering makes true.
        """
        if node.name in self.formals:
            return None
        if node.name in self.ns.bodies:
            try:
                return cast('Expression', self.ns.named(node.name, self.context))
            except SchemaError as e:
                self.errors.append(str(e))
                return None
        match self.ns.kind(node.name):
            case 'variable':
                return Variable(node.name)
            case 'parameter':
                dtype = self.ns.dtypes.get(node.name)
                if dtype is not None and dtype not in NUMERIC_DTYPES:
                    self.errors.append(not_a_number(node.name, dtype, self.context))
                    return None
                return Parameter(node.name)
            case 'dimension':
                self.errors.append(
                    f"{self.context}: '{node.name}' is a dimension, and a dimension is "
                    f'not a value. To use its coordinates as data, declare a parameter over it.'
                )
                return None
            case 'relation':
                self.errors.append(
                    f"{self.context}: '{node.name}' is a relation, and a relation is not a value. Use its "
                    f'columns as sum(x, over=<column>, by={node.name}[<column>]) or in a where, or declare a '
                    f'parameter to carry numbers.'
                )
                return None
            case _:
                self.errors.append(self.ns.unknown(node.name, self.context, allow_dims=False, formals=self.formals))
                return None

    def _call(self, node: FunctionCallNode) -> Expression | None:
        """An operator call as the node it is: its shape checked, and each kwarg read by the kind the operator declares for it.

        Every argument is read even after one failed, so a call with two
        faults reports both. A formal anywhere under the call builds nothing
        and refuses nothing.
        """
        if node.name not in BUILTINS:
            self.errors.append(f'{self.context}: {unknown_operator_message(node.name)}')
            return None
        builtin = BUILTINS[node.name]
        shape_error = call_shape_error(node.name, len(node.args), node.kwargs)
        if shape_error is not None:
            self.errors.append(f'{self.context}: {shape_error}')
        if node.name == 'dual':
            return None if shape_error is not None else self._dual(node)
        args = [self.arith(a) for a in node.args]
        along: str | None = None
        over: tuple[str, ...] | None = None
        amounts: dict[str, int | str | None] = {}
        edge: _Edge | None = None
        unread = False
        for key, value in node.kwargs.items():
            match builtin.kind_of(key):
                case 'edge':
                    edge = self._edge(value, node.name)
                    unread |= edge is None
                case 'dimension':
                    if key == 'along':
                        along = self._dim_ref(value, node.name, key)
                        unread |= along is None
                    else:
                        over = self._over(value, node.name, relation='by' in node.kwargs)
                        unread |= over is None
                case 'value':
                    amounts[key] = self._amount(value, node.name, key)
                    unread |= amounts[key] is None
                case 'columns' | None:
                    pass
        columns = None
        if (key := next((k for k in builtin.column_kwargs if k in node.kwargs), None)) is not None:
            columns = self.columns_ref(node.kwargs[key], node.name, key)
            unread |= columns is None
        if shape_error is not None or unread or not args or args[0] is None:
            return None
        operand = args[0]
        if node.name == 'sum':
            return self._sum(operand, over, columns)
        if node.name == 'at':
            assert columns is not None, 'the call shape requires at(by=)'
            return self._at(operand, columns)
        assert along is not None, 'the call shape requires along='
        partition = None
        if columns is not None and (partition := self.partition(columns, node.name, along)) is None:
            return None
        return self._translation(node.name, operand, along, amounts, edge, partition)

    def _sum(self, operand: Expression, over: tuple[str, ...] | None, columns: ColumnsNode | None) -> Expression | None:
        """A plain sum over the dims *over* names, or a sum through a relation, grouped by *columns*.

        Through a relation, the join and the sum over the axes it opens are one
        call, so no axis is ever left open. A name in *over* that is no column
        of the relation is a dim, summed away after the group-by.
        """
        if columns is None:
            if over is None:
                return self._bare_sum(operand)
            return Sum(operand, tuple(Axis(d) for d in over))
        assert over is not None, 'the call shape requires over= beside by='
        grouping = self._grouping(columns, over)
        if grouping is None:
            return None
        join, plain = grouping
        grouped = Sum(Join(operand, join), join.axes)
        return Sum(grouped, tuple(Axis(d) for d in plain)) if plain else grouped

    def _at(self, operand: Expression, columns: ColumnsNode) -> Expression | None:
        """``at(x, by=relation[column])``: *operand* read at the value of *columns* each row of the relation holds."""
        try:
            inner = dims_of(operand, self.ns.schema, self.context)
        except DimensionError as e:
            self.errors.append(str(e))
            return None
        join = self.lookup(columns, inner)
        return None if join is None else Join(operand, join)

    def _translation(
        self,
        operator: str,
        operand: Expression,
        along: str,
        amounts: Mapping[str, int | str | None],
        edge: _Edge | None,
        partition: Partition | None,
    ) -> Expression | None:
        """``shift`` or ``sum_back`` from its read arguments, or ``None`` with the refusal appended."""
        if self.ns.unordered(along):
            self.errors.append(unordered(self.context, f'{operator}(along={along})', along))
            return None
        wrap, fill = edge if edge is not None else (False, None)
        if operator == 'shift':
            offset = amounts['offset']
            assert offset is not None
            if not self._edge_fits(operand, offset, wrap=wrap, fill=fill):
                return None
            return Translate(operand, along, offset, wrap=wrap, fill=fill, partition=partition)
        if fill is not None:
            self.errors.append(
                f"{self.context}: sum_back(edge=...) takes 'wrap' or nothing. To add a constant, "
                f'write it in the expression.'
            )
            return None
        width = amounts['window']
        assert width is not None
        return WindowSum(operand, along, width, wrap=wrap, partition=partition)

    def _bare_sum(self, operand: Expression) -> Expression | None:
        """``sum(x)`` with no ``over=`` or ``by=`` reduces every dim the operand carries, which it has to carry some of."""
        try:
            inner = dims_of(operand, self.ns.schema, self.context)
        except DimensionError as e:
            self.errors.append(str(e))
            return None
        if not inner:
            self.errors.append(
                f'{self.context}: sum() has no over= or by=, and its operand has no dimensions to sum over. '
                f'Remove the sum.'
            )
            return None
        return Sum(operand, tuple(Axis(d) for d in sorted(inner)))

    def _edge_fits(self, operand: Expression, offset: int | str, *, wrap: bool, fill: float | None) -> bool:
        """What a ``shift``'s ``edge=`` may say, and where saying nothing is an answer.

        Every rule here is decidable from the file — whether the operand
        carries a variable, whether the offset is named, what the edge is
        written as — so a file breaking one is refused at load rather than by
        whoever lowers it.
        """
        if wrap:
            return True
        has_var = carries_variable(operand)
        if has_var and fill is not None and fill != 0:
            self.errors.append(
                f'{self.context}: shift(edge={fill:g}) reads a variable, and over a variable only edge=0 is '
                f'allowed. Write edge=0, and add the constant to the expression.'
            )
            return False
        if fill is None and _vacates(offset) and not has_var:
            self.errors.append(_shift_over_data_message(self.context))
            return False
        if fill is None and isinstance(offset, str):
            self.errors.append(f'{self.context}: {_named_offset_edge_message(offset)}')
            return False
        return True

    def _amount(self, value: ArithmeticNode, operator: str, key: str) -> int | str | None:
        """``offset=`` or ``window=``: a whole number in the operator's range, or the name of a parameter.

        Closed so that [`mathspec.dimensions._check_named_amount`][] sees
        every parameter an amount carries, and so that a program's
        ``offset`` and ``width`` are the ``int | str`` they say.
        """
        words = AMOUNTS[operator]
        if (literal := literal_number(value)) is not None:
            if not (literal.value.is_integer() and literal.value >= words.minimum):
                self.errors.append(f'{self.context}: {operator}({key}=...) {words.form}')
                return None
            return int(literal.value)
        bare = _without_sign(value)
        if not isinstance(bare, NameNode):
            self.errors.append(
                f'{self.context}: {operator}({key}=) takes a number or the name of an integer parameter. '
                f'Precompute it as a parameter.'
            )
            return None
        if self.ns.kind(bare.name) != 'parameter':
            if self._name(bare) is not None:
                self.errors.append(f'{self.context}: {operator}({key}=...) {words.form}')
            return None
        if (dtype := self.ns.dtypes[bare.name]) != 'int':
            self.errors.append(
                f"{self.context}: {operator}({key}={bare.name}) counts positions, but '{bare.name}' is declared "
                f'dtype: {dtype}. Declare it dtype: int.'
            )
            return None
        if isinstance(value, UnaryOperatorNode) and value.op == '-':
            self.errors.append(
                f'{self.context}: {operator}({key}=-{bare.name}) negates a named {words.noun}. {words.negated}'
            )
            return None
        return bare.name

    def _edge(self, value: ArithmeticNode, operator: str) -> _Edge | None:
        """``edge=``: the closed keyword ``wrap``, or a number to contribute; a name here is a typo."""
        if self._formal(value):
            return None
        if isinstance(value, KeywordNode):
            if value.value == EDGE_WRAP:
                return True, None
            self.errors.append(f'{self.context}: {edge_error(operator, repr(value.value))}')
            return None
        if isinstance(value, NameNode):
            if value.name == EDGE_WRAP:
                self.errors.append(
                    f"{self.context}: {operator}(edge={EDGE_WRAP}) has no quotes. Write edge='{EDGE_WRAP}'."
                )
                return None
            self.errors.append(f'{self.context}: {edge_error(operator, value.name)}')
            return None
        if (literal := literal_number(value)) is None:
            self.errors.append(
                f"{self.context}: {operator}(edge=) holds an expression, and edge= takes the keyword '{EDGE_WRAP}' "
                f'or a number. Write the number itself.'
            )
            return None
        return False, literal.value

    def _dim_ref(self, value: ArithmeticNode, operator: str, key: str) -> str | None:
        """An operator kwarg whose *value* must name a declared dimension."""
        if self._formal(value):
            return None
        if not isinstance(value, NameNode):
            self.errors.append(
                f'{self.context}: {operator}({key}=...) is not a name. Write the name of a declared dimension.'
            )
            return None
        if value.name not in self.ns.dimensions:
            self.errors.append(
                _undeclared_dim(self.context, operator, f'{key}={value.name}', value.name, self.ns, self.formals)
            )
            return None
        return value.name

    def _dual(self, node: FunctionCallNode) -> Dual | None:
        """``dual(c)`` as the leaf it is, its one argument the name of a declared constraint.

        Constraints sit outside the flat namespace, so this store is consulted
        only here — a bare name in arithmetic never reaches it. A dual standing
        where the math is built is refused separately
        ([`mathspec.degree`][]); this pass only types the name.
        """
        (value,) = node.args
        if self._formal(value):
            return None
        if not isinstance(value, NameNode):
            self.errors.append(
                f'{self.context}: dual() takes the name of a declared constraint. Write dual(<constraint>), '
                f'without quotes.'
            )
            return None
        if value.name not in self.ns.constraints:
            self.errors.append(self.ns.unknown_constraint(value.name, self.context, formals=self.formals))
            return None
        return Dual(value.name)

    def _over(self, value: ArithmeticNode, operator: str, *, relation: bool) -> tuple[str, ...] | None:
        """``over=``: a dimension or a list of them, and beside ``by=`` the columns of the relation too, each a bare name.

        Beside ``by=`` a name is read against the relation in [`_grouping`][],
        so only a plain sum checks its names here.
        """
        if self._formal(value):
            return None
        if isinstance(value, ColumnsNode):
            self.errors.append(
                f'{self.context}: {operator}(over={value}) names a relation, and over= takes bare names. Write '
                f'over={shown(value.columns)}. Beside by={value.relation}[...], a name in over= is a column of '
                f"'{value.relation}', or a dimension."
            )
            return None
        names = names_in(value)
        if not names:
            self.errors.append(
                f'{self.context}: {operator}(over=...) is not a name. Write a declared dimension, or a list of them.'
            )
            return None
        if any(n in self.formals for n in names):
            return None
        found = len(self.errors)
        if not relation:
            for n in names:
                if n not in self.ns.dimensions:
                    self.errors.append(_undeclared_dim(self.context, operator, f'over={n}', n, self.ns, self.formals))
        if repeated := sorted({n for n in names if names.count(n) > 1}):
            self.errors.append(
                f'{self.context}: {operator}(over={shown(names)}) names {", ".join(map(repr, repeated))} twice. '
                f'Name each one once.'
            )
        return names if len(self.errors) == found else None

    def columns_ref(self, value: ArithmeticNode, operator: str, key: str) -> ColumnsNode | None:
        """A kwarg naming columns of one relation, ``relation[column, …]``, each a column the relation declares.

        The relation is written once and its columns after it, so one call
        reads one table by the grammar alone.
        """
        if self._formal(value):
            return None
        if not isinstance(value, ColumnsNode):
            self.errors.append(self._not_columns(value, operator, key))
            return None
        if value.relation in self.formals:
            return None
        if (problem := self.not_a_relation(value.relation, operator, key)) is not None:
            self.errors.append(problem)
            return None
        shape = self.ns.relations[value.relation]
        if unknown := [c for c in value.columns if c not in shape.roles and c not in self.formals]:
            self.errors.append(
                f'{self.context}: {operator}({key}={value}) names {unknown}, which is no column of '
                f"'{value.relation}'. Name one of its columns, {list(shape.roles)}."
            )
            return None
        if any(c in self.formals for c in value.columns):
            return None
        if len(set(value.columns)) < len(value.columns):
            self.errors.append(f'{self.context}: {operator}({key}={value}) names a column twice. Name each once.')
            return None
        return value

    def _not_columns(self, value: ArithmeticNode, operator: str, key: str) -> str:
        """Why *value* is not a column selection, with the selection it most likely meant."""
        ns, context = self.ns, self.context
        if isinstance(value, NameNode) and value.name in ns.relations:
            return (
                f'{context}: {operator}({key}={value.name}) names the relation and none of its columns. Write '
                f"{key}={value.name}[<column>], with a column of '{value.name}': "
                f'{list(ns.relations[value.name].roles)}.'
            )
        if isinstance(value, NameNode) and value.name in ns.dimensions:
            over_here = [
                f'{n}[{r}]' for n, shape in ns.relations.items() for r, dim in shape.columns if dim == value.name
            ]
            hint = (
                f'Columns over {value.name!r}: {over_here}'
                if over_here
                else f'No relation has a column over {value.name!r}.'
            )
            return (
                f"{context}: {operator}({key}={value.name}): '{value.name}' is a dimension, and {key}= takes "
                f'columns of a relation, written relation[column]. {hint}'
            )
        return (
            f'{context}: {operator}({key}=...) takes columns of one relation. Write relation[column] or '
            f'relation[column, ...].'
        )

    def _grouping(self, columns: ColumnsNode, over: tuple[str, ...]) -> tuple[JoinColumns, tuple[str, ...]] | None:
        """How ``sum(x, over=..., by=relation[...])`` joins the relation, and the dims it sums away with no column.

        A name in *over* is a column of the relation where it has one, and a
        dimension otherwise, summed away after the group-by. The declaration
        refuses a column named after a dimension it is not over, so the two
        readings never disagree. Every column a call touches is written in it,
        so a relation may gain a column without changing what the call means.
        """
        name, into_roles = columns.relation, columns.columns
        ns, shape = self.ns, self.ns.relations[name]
        call = f'sum(by={columns})'
        from_roles = tuple(n for n in over if n in shape.roles)
        plain = tuple(n for n in over if n not in shape.roles)
        if unknown := [n for n in plain if n not in ns.dimensions]:
            self.errors.append(
                f"{self.context}: {call}: over={unknown[0]} names no column of '{name}', whose columns are "
                f'{list(shape.roles)}, and no dimension{_or_a_formal(self.formals)}. '
                f'{did_you_mean(unknown[0], [*shape.roles, *ns.dimensions], label="Names")}'
            )
            return None
        if not from_roles:
            self.errors.append(
                f"{self.context}: {call}: over={shown(over)} names no column of '{name}', so the sum reads nothing "
                f"through '{name}'. Name in over= the column that the operand is joined on: "
                f'{_columns_over(shape, plain)}.'
            )
            return None
        join = self._checked_join(name, call, from_roles, into_roles)
        if join is None:
            return None
        if join.one_row_per_group:
            self.errors.append(
                f'{self.context}: {call}: the columns this sum groups by, {list(join.grouped)}, hold the whole key '
                f'{list(shape.key)}, so every group is one row and the sum adds nothing. Write '
                f'{_lookup_rewrite(name, from_roles, plain)}, or group by a value column.'
            )
            return None
        return join, plain

    def lookup(self, columns: ColumnsNode, inner: frozenset[str]) -> JoinColumns | None:
        """How ``at`` reads the columns *columns* names, at an operand carrying *inner*.

        The operand is joined on the named columns, and on each other key
        column over a dim it carries that the named columns do not already
        match. The rest of the key arrives. So a map into its own dimension
        joins on the value column alone, and the key column arrives.
        """
        name, call = columns.relation, f'at(by={columns})'
        shape = self.ns.relations[name]
        if not shape.values:
            self.errors.append(
                f"{self.context}: {call}: '{name}' has every column in its key, so it has no value column for at() "
                f'to read. Sum through it instead.'
            )
            return None
        if keyed := [r for r in columns.columns if r in shape.key]:
            self.errors.append(
                f"{self.context}: {call} names {keyed}, a key column of '{name}'. A lookup reads value columns "
                f'at the key. Name one of the value columns, {list(shape.values)}, or sum through the key column.'
            )
            return None
        matched = inner - {shape.dim(r) for r in columns.columns}
        into = tuple(r for r in shape.key if shape.dim(r) not in matched)
        return self._checked_join(name, call, columns.columns, into)

    def _checked_join(
        self, name: str, call: str, from_roles: tuple[str, ...], into_roles: tuple[str, ...]
    ) -> JoinColumns | None:
        """The join of relation *name* between the columns that leave the frame and the columns that arrive."""
        context = self.context
        shape = self.ns.relations[name]
        if both := sorted(set(from_roles) & set(into_roles)):
            self.errors.append(f'{context}: {call}: over= and by= both name {both}. Name different columns in each.')
            return None
        for roles in (from_roles, into_roles):
            dims = [shape.dim(r) for r in roles]
            if shared := sorted({d for d in dims if dims.count(d) > 1}):
                self.errors.append(
                    f'{context}: {call}: {list(roles)} are columns over one dimension, {shared}, and the operand '
                    f'carries each dimension once. Read one of them per call.'
                )
                return None
        kept = tuple(r for r in shape.key if r not in from_roles and r not in into_roles)
        return JoinColumns(name, shape, (*from_roles, *kept), (*into_roles, *kept))

    def partition(self, columns: ColumnsNode, operator: str, along_dim: str) -> Partition | None:
        """How a partition (``shift``, ``sum_back``, ``position``) steps along the relation *columns* names.

        It steps along the one key column over *along_dim* (a key has one
        column per dimension), joins on the other key columns and groups by the
        value columns *columns* names. ``None`` where the relation has no key
        column over that dimension, or names a column that is not a value column.
        """
        context = self.context
        name, within_roles = columns.relation, columns.columns
        shape = self.ns.relations[name]
        call = f'{operator}(within={columns})'
        if not shape.values:
            self.errors.append(
                f"{context}: {call}: '{name}' has every column in its key, so it makes no groups. Move the group "
                f'columns under values:, and keep under key: the column {operator} steps along.'
            )
            return None
        over_keys = [r for r in shape.key if shape.dim(r) == along_dim]
        if not over_keys:
            self.errors.append(
                f"{context}: {call}: '{name}' has no key column over '{along_dim}'. Its key is {list(shape.key)}."
            )
            return None
        if keyed := [r for r in within_roles if r in shape.key]:
            self.errors.append(
                f"{context}: {call}: within= names {keyed}, a key column of '{name}'. Name one of its value "
                f'columns, {list(shape.values)}.'
            )
            return None
        (along,) = over_keys
        joined = tuple(r for r in shape.key if r != along)
        return Partition(name, shape, along, within_roles, joined)

    def not_a_relation(self, name: str, operator: str, key: str) -> str | None:
        """Why *name*, written before the columns of a selection, is not a relation; ``None`` where it is one."""
        ns, context = self.ns, self.context
        if name in ns.relations:
            return None
        if name in ns.dimensions:
            return (
                f"{context}: {operator}({key}={name}[...]): '{name}' is a dimension, not a relation. Write the "
                f'relation first and its columns after it: {key}=<relation>[<column>].'
            )
        return (
            f'{context}: {operator}({key}={name}[...]) does not name a relation{_or_a_formal(self.formals)}. '
            f'{did_you_mean(name, ns.relations, label="Relations")}\n'
            f"Declare it under 'relations:' as {name}: {{key: <the columns a row is identified by>, "
            f'values: <the columns they determine>}}.'
        )


def not_a_number(name: str, dtype: str, context: str) -> str:
    """Why a ``str`` or ``bool`` parameter is refused where a value belongs; the rewrite is the dtype's own."""
    if dtype == 'str':
        instead = (
            f'Compare it in a where '
            f'("{name} == \'some_label\'"), and carry the numbers it picks out in a '
            f'parameter of its own.'
        )
    else:
        instead = f'Name it in a where ("{name}", "NOT {name}"), or declare it dtype: int to multiply by 0 and 1.'
    return f"{context}: '{name}' is declared dtype: {dtype}, and an expression reads only float and int. {instead}"


def _undeclared_dim(context: str, operator: str, call: str, name: str, ns: Namespace, formals: frozenset[str]) -> str:
    return (
        f'{context}: {operator}({call}) does not name a declared dimension{_or_a_formal(formals)}. '
        f'{did_you_mean(name, ns.dimensions, label="Dimensions")}\n'
        f"Declare '{name}' under 'dimensions:', or correct the spelling."
    )


def _lookup_rewrite(name: str, columns: tuple[str, ...], plain: tuple[str, ...]) -> str:
    """The ``at`` a sum that groups by the whole key means, with its plain dims summed around it.

    The columns the sum joins on become the columns ``at`` reads. A dim in
    ``over=`` with no column of the relation is summed after the group-by, so
    the rewrite sums it around the ``at`` too, or that dim stays in the frame.
    """
    lookup = f'at(..., by={name}[{", ".join(columns)}])'
    return f'sum({lookup}, over={shown(plain)})' if plain else lookup


def _columns_over(shape: RelationDeclaration, dims: tuple[str, ...]) -> str:
    """The columns of *shape* over each of *dims*, for the writer who named a dimension where a column was meant."""
    over = {d: [r for r in shape.roles if shape.dim(r) == d] for d in dims}
    if named := [f'the columns over {d!r} are {roles}' for d, roles in over.items() if roles]:
        return ', '.join(named)
    return f'its columns are {list(shape.roles)}, over {sorted(set(shape.dims))}'


def _or_a_formal(formals: frozenset[str]) -> str:
    """The words a refusal inside a template adds, since a formal would have stood there too."""
    return ' or a formal argument of this macro' if formals else ''


def _without_sign(value: ArithmeticNode) -> ArithmeticNode:
    """*value* under its sign, if it carries one."""
    return value.operand if isinstance(value, UnaryOperatorNode) else value


def _vacates(offset: int | str) -> bool:
    """Whether a translation leaves anything behind.

    A literal zero step reaches every coordinate from itself, so there is no
    vacated position for an ``edge=`` to answer for and the refusal has
    nothing to refuse. A *named* offset may be zero in the data and is not
    known here, so it vacates until proved otherwise.
    """
    return offset != 0


def _named_offset_edge_message(name: str) -> str:
    """Why a named offset must say what the vacated positions contribute.

    The absent edge propagates through a presence frame keyed by the translated
    dimension alone, and a per-entity offset vacates a different slot for each
    entity — which that frame cannot say. Refused rather than answered wrongly
    (#850); the two edges that write their own answer are allowed.
    """
    return (
        f'shift(offset={name}) needs an edge=, because a named offset cannot leave its vacated positions '
        f'absent yet.\n'
        f"Add edge='wrap' for a cyclic translation, or edge=<number> for what the "
        f'vacated positions contribute.'
    )


def _shift_over_data_message(context: str) -> str:
    """The three ways out of a translation over data with no ``edge=``, the third being two things at once."""
    return (
        f'{context}: shift() over an expression with no variable leaves the vacated positions with no '
        f'value. Write which you mean:\n'
        f"  shift(x, along=d, offset=n, edge='wrap')   the dimension really is cyclic\n"
        f'  shift(x, along=d, offset=n, edge=0)        the vacated positions contribute zero\n'
        f'  ...and a where: excluding them        the vacated rows should not exist at all\n'
        f'A where: alone does not remove this refusal, and edge=0 alone keeps a row whose bound is that zero.'
    )
