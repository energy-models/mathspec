# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Static dim-set checking — a type system whose type is a set of dim names.

Every node's dim set is computable before any data is attached, so this pass runs
at load on the resolved tree. The per-node rules are the "Dim algebra" table in
``docs/reference/language/expressions.md``; a constraint's two sides together
must equal its ``dims``, and a where or a bound may not exceed the frame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from mathspec.errors import DimensionError, case_context
from mathspec.program import (
    Add,
    Cases,
    Constant,
    CountComparison,
    DimensionComparison,
    DimensionPosition,
    Divide,
    Dual,
    Expression,
    ExpressionComparison,
    ExpressionReference,
    Join,
    JoinColumns,
    JoinedPredicate,
    Mask,
    Multiply,
    Negate,
    ParameterComparison,
    ParameterDefined,
    ParameterReference,
    Partition,
    Power,
    RelationComparison,
    RelationDefined,
    RelationPairComparison,
    Sum,
    Translate,
    TranslatedPredicate,
    VariableDefined,
    VariableReference,
    WindowSum,
    children,
)

if TYPE_CHECKING:
    from mathspec.program import Program
    from mathspec.spec import Spec


def dims_of(node: Expression, spec: Spec, context: str) -> frozenset[str]:
    """The dim set of a resolved expression, checking every rule on the way.

    Raises:
        DimensionError: On the first rule broken.
    """
    if isinstance(node, Constant):
        return frozenset()

    if isinstance(node, ParameterReference):
        return frozenset({**spec.parameters, **spec.given.parameters}[node.name].dims)

    if isinstance(node, VariableReference):
        columns = {**spec.variables, **spec.given.variables, **spec.given.expressions}
        return frozenset(columns[node.name].dims or ())

    if isinstance(node, Dual):
        return frozenset({**spec.constraints, **spec.given.constraints}[node.constraint].dims)

    if isinstance(node, ExpressionReference):
        return _named_dims(node, spec, context)

    if isinstance(node, Cases):
        return frozenset().union(*(dims_of(region.value, spec, context) for region in node.regions))

    if isinstance(node, Negate | Add | Multiply | Power | Divide):
        return frozenset().union(*(dims_of(child, spec, context) for child in children(node)))

    if isinstance(node, Sum):
        return _sum_dims(node, spec, context)
    inner = dims_of(node.operand, spec, context)
    if isinstance(node, Join):
        assert not node.columns.axes, 'a join that opens axes is read only by the sum that closes them'
        return join_dims(node.columns, inner, context, 'the expression')
    if isinstance(node, Translate | WindowSum):
        return _translation_dims(node, inner, spec, context)

    assert_never(node)


def _named_dims(node: ExpressionReference, spec: Spec, context: str) -> frozenset[str]:
    """An entry's declared frame where it has one — a narrower arm or body broadcasts along the rest — else its body's."""
    declared = spec.expressions[node.name].dims
    if declared is not None:
        return frozenset(declared)
    return dims_of(node.body, spec, context)


def _not_carried(context: str, call: str, inner: frozenset[str], rewrite: str) -> str:
    """The refusal for an operator reaching a dim its operand does not carry; *rewrite* is the operator's own."""
    return f'{context}: {call} but the expression has only the dims {sorted(inner)}. {rewrite}.'


def _sum_dims(node: Sum, spec: Spec, context: str) -> frozenset[str]:
    """``sum`` reduces each dim in ``over`` away, so the operand carries every one.

    The axes a join opens never reach a frame: the sum over the join closes
    every one, so its frame is the join's frame less them.
    """
    if isinstance(node.operand, Join) and node.operand.columns.axes:
        join = node.operand
        assert node.over == join.columns.axes, 'a sum through a relation closes exactly the axes its join opens'
        return join_dims(join.columns, dims_of(join.operand, spec, context), context, 'the expression')
    inner = dims_of(node.operand, spec, context)
    for summed in node.over:
        if summed.dimension not in inner:
            raise DimensionError(
                _not_carried(context, f'sum(over={summed})', inner, 'Remove the sum, or correct the dimension')
            )
    return inner - {axis.dimension for axis in node.over}


def join_dims(columns: JoinColumns, inner: frozenset[str], context: str, operand: str) -> frozenset[str]:
    """The dims *inner* has once *columns* joins it, an expression's or a predicate's alike.

    The dims joined on go and the dims grouped by arrive. A column both
    joined on and grouped by keeps its dim. The call a refusal quotes is
    ``at`` where each group is one row, and ``sum`` otherwise.

    Raises:
        DimensionError: *operand* does not carry a dim the call joins on, or
            already carries one the call adds.
    """
    lookup = columns.one_row_per_group
    named = columns.dropped if lookup else columns.added
    call = f'{"at" if lookup else "sum"}(by={columns.name}[{", ".join(named)}])'
    if missing := sorted(set(columns.dropped_dims) - inner):
        if lookup:
            raise DimensionError(
                f'{context}: {call} joins on {missing}, which {operand} does not carry (dims '
                f'{sorted(inner)}). To group by those columns, use sum() instead.'
            )
        raise DimensionError(
            _not_carried(
                context, f'{call} joins on {missing} to sum it away,', inner, 'Remove the sum, or correct the dimension'
            )
        )
    added, dropped = set(columns.added_dims), set(columns.dropped_dims)
    if clash := sorted((added & inner) - dropped):
        raise DimensionError(
            f'{context}: {call} groups by {clash}, which the expression already carries.\n'
            f'Move the factor carrying {clash} outside the operator, or group by a column over another '
            f'dimension.'
        )
    _check_joined(call, columns, inner, context)
    return (inner - set(columns.joined_dims)) | set(columns.grouped_dims)


#: The operator name a file writes for each translation, which its refusals quote.
_VERBS: dict[type[Translate | WindowSum], str] = {Translate: 'shift', WindowSum: 'sum_back'}


def _translation_dims(node: Translate | WindowSum, inner: frozenset[str], spec: Spec, context: str) -> frozenset[str]:
    """``shift`` and ``sum_back`` keep every dim, and a named amount and a partition are checked here."""
    verb = _VERBS[type(node)]
    if node.along not in inner:
        raise DimensionError(
            _not_carried(
                context,
                f'{verb}(along={node.along})',
                inner,
                f'Name a dimension the operand carries, or remove the {verb}',
            )
        )
    _check_named_amount(node, verb, inner, spec, context)
    if node.partition is not None:
        within = f'{node.partition.name}[{", ".join(node.partition.grouped)}]'
        _check_joined(f'{verb}(along={node.along}, within={within})', node.partition, inner, context)
    return inner


def _check_joined(call: str, use: JoinColumns | Partition, inner: frozenset[str], context: str) -> None:
    """The columns a call joins on are matched at their dimensions, so the operand carries every one, each once.

    Two joined columns over one dimension would match the operand's one
    coordinate twice: the ``over=`` column and an unnamed key column, or two
    unnamed key columns. A partition joins on the key columns it does not
    step along.
    """
    dims = use.joined_dims
    if missing := sorted(set(dims) - inner):
        raise DimensionError(
            f'{context}: {call} joins on {missing} (columns {[r for r in use.joined if use.dim(r) in missing]} '
            f"of '{use.name}'), which the expression does not carry (dims {sorted(inner)}). Index the "
            f'operand over them, or name them in the call.'
        )
    if twice := sorted({d for d in dims if dims.count(d) > 1}):
        raise DimensionError(
            f"{context}: {call} joins '{use.name}' on {twice} through more than one column. Join on "
            f'different dimensions, or use a relation whose key columns are over different dimensions.'
        )


def _check_named_amount(
    node: Translate | WindowSum, verb: str, inner: frozenset[str], spec: Spec, context: str
) -> None:
    """The two rules of an ``offset=`` or ``window=`` naming a parameter that need the operand's dims; resolution holds it to its dtype."""
    kwarg, amount = ('offset', node.offset) if isinstance(node, Translate) else ('window', node.width)
    if not isinstance(amount, str):
        return
    declared = {**spec.parameters, **spec.given.parameters}[amount]
    if node.along in declared.dims:
        raise DimensionError(
            f"{context}: {verb}({kwarg}={amount}) steps along '{node.along}', and '{amount}' is declared over "
            f"{sorted(declared.dims)}. Declare '{amount}' over dims without '{node.along}'."
        )
    groups = (
        frozenset(node.partition.dim(v) for v in node.partition.grouped) if node.partition is not None else frozenset()
    )
    if stray := sorted(frozenset(declared.dims) - inner - groups):
        raise DimensionError(
            f"{context}: {verb}({kwarg}={amount}): '{amount}' varies over {stray}, which the expression does "
            f"not carry (dims {sorted(inner)}). Declare '{amount}' over dims the expression carries, or group "
            f'by a relation into one of {stray}.'
        )


# ---------------------------------------------------------------------------
# entry-level rules
# ---------------------------------------------------------------------------


def check_spec(spec: Spec, program: Program) -> None:
    """Check every entry's dim rules, on the trees *program* holds for *spec*.

    Raises:
        DimensionError: On the first entry that breaks one.
    """
    for vname, vdef in spec.variables.items():
        frame = frozenset(vdef.dims)
        context = f"Variable '{vname}'"
        _check_where_dims(program.variables[vname].where, frame, context)
        for side in ('lower', 'upper'):
            bound = getattr(vdef.bounds, side)
            if isinstance(bound, str):
                bdims = frozenset({**spec.parameters, **spec.given.parameters}[bound].dims)
                if not bdims <= frame:
                    raise DimensionError(
                        f"{context}: bounds.{side} parameter '{bound}' has dims "
                        f"{sorted(bdims - frame)} outside the variable's dims "
                        f"{sorted(frame)}. Declare '{bound}' over the variable's dims."
                    )

    for ename, entry in program.expressions.items():
        declared = spec.expressions[ename]
        if declared.dims is None:
            continue
        frame = frozenset(declared.dims)
        if not isinstance(entry.expression, Cases):
            _check_body_dims(entry.expression, spec, frame, f"Named expression '{ename}'")
            continue
        for region, label in zip(entry.expression.regions, [*declared.cases, None], strict=True):
            context = case_context(ename, label)
            if label is not None:
                _check_where_dims(region.when, frame, context)
            _check_value_dims(region.value, spec, frame, context)

    for ename, entry in program.expressions.items():
        if entry.adds_to is None:
            continue
        stated = program.given.expressions[entry.adds_to].dims
        if extra := [d for d in entry.dims if d not in stated]:
            raise DimensionError(
                f"Named expression '{ename}': it adds to {entry.adds_to!r} over {extra}, which the given entry's "
                f'dims {list(stated)} do not name. Add {extra} to those dims, or leave them out of the term.'
            )

    for cname, constraint in program.constraints.items():
        frame = frozenset(constraint.dims)
        context = f"Constraint '{cname}'"
        _check_where_dims(constraint.where, frame, context)
        got = dims_of(constraint.lhs, spec, context) | dims_of(constraint.rhs, spec, context)
        if got != frame:
            stray, missing = sorted(got - frame), sorted(frame - got)
            detail = (
                f'carries dims {stray} that are not in its dims: {sorted(frame)}. Add them to dims:, or sum them out'
                if stray
                else f'does not carry {missing}, which its dims: declares. Remove them from dims:, or use them '
                f'in the expression'
            )
            raise DimensionError(f'{context}: the expression {detail}.')

    if program.objective is not None:
        context = 'The objective'
        got = dims_of(program.objective.expression, spec, context)
        if got:
            raise DimensionError(
                f'{context}: the expression carries dims {sorted(got)}, and an objective is one '
                f'number. Wrap each additive term in its own sum(): '
                f'`sum(p * cost) + sum(p_nom * capex)`.'
            )


def _check_value_dims(node: Expression, spec: Spec, frame: frozenset[str], context: str) -> None:
    """A region's value may only carry dims the frame does — the ``otherwise:`` included.

    A wider one would give the quantity dims its entry does not, which is
    the second answer a ``dims:`` exists to avoid.
    """
    got = dims_of(node, spec, context)
    if not got <= frame:
        raise DimensionError(
            f'{context}: the value carries dims {sorted(got - frame)} outside the dims: '
            f'{sorted(frame)}. Add them to dims:, or take them out of the value.'
        )


def _check_body_dims(node: Expression, spec: Spec, frame: frozenset[str], context: str) -> None:
    """A plain entry's body may only carry dims its declared frame does; fewer is constant along the rest."""
    got = dims_of(node, spec, context)
    if not got <= frame:
        raise DimensionError(
            f'{context}: the body carries dims {sorted(got - frame)} outside the dims: {sorted(frame)}. '
            f'Add them to dims:, or take them out of the body.'
        )


def _check_where_dims(
    mask: Mask | None,
    frame: frozenset[str],
    context: str,
) -> None:
    """A predicate may only test dims the frame carries; reducing an outside dim to fit would fail open.

    The refusal names the leaf that left the frame, reading its dims as
    [`dims`][mathspec.program.Mask.dims] does.
    """
    if mask is None:
        return

    for atom in mask.atoms:
        if not (outside := sorted(Mask(atom).dims - frame)):
            continue
        match atom:
            case ParameterDefined() | ParameterComparison():
                leaf = f"where-parameter '{atom.name}'"
            case VariableDefined():
                leaf = f"where-variable '{atom.name}'"
            case DimensionComparison() | DimensionPosition():
                leaf = f"where-dimension '{atom.name}'"
            case RelationComparison() | RelationPairComparison() | RelationDefined():
                leaf = f"where-relation '{atom.name}'"
            case ExpressionComparison():
                leaf = 'a where-comparison of expressions'
            case CountComparison():
                leaf = f"a where-count over '{atom.over}'"
            case TranslatedPredicate():
                leaf = f"a where-predicate translated along '{atom.along}'"
            case JoinedPredicate():
                leaf = f"a where-predicate read through '{atom.columns.name}'"
            case _:
                assert_never(atom)
        raise DimensionError(
            f'{context}: {leaf} reads dims {outside} outside the declared dims {sorted(frame)}. '
            f'Add them to dims:, or test a name over the declared dims.'
        )
