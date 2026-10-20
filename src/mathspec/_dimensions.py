# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Static dim-set checking — a type system whose type is a set of dim names.

Every node states its dims, so every rule is decided at load. Resolution holds
each node to the rule of its operator as it builds the node ([`check_node`][]);
the rules are the "Dim algebra" table in
``docs/reference/language/expressions.md``. [`check_spec`][] holds each entry
to its own: a constraint's two sides together are indexed over exactly its
``dims``, and a where or a bound is indexed over no dim the entry is not.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from mathspec.errors import DimensionError, case_context
from mathspec.program import (
    Cases,
    CountComparison,
    DimensionComparison,
    DimensionPosition,
    Expression,
    ExpressionComparison,
    Join,
    JoinColumns,
    JoinedPredicate,
    Mask,
    ParameterComparison,
    ParameterDefined,
    Partition,
    RelationComparison,
    RelationDefined,
    RelationPairComparison,
    Sum,
    Translate,
    TranslatedPredicate,
    VariableDefined,
    WindowSum,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from mathspec.program import Program
    from mathspec.spec import Spec


def check_node(node: Sum | Join | Translate | WindowSum, spec: Spec, context: str) -> None:
    """The dim rule *node*'s own operator holds it to, on the dims its operand states.

    Resolution calls it on each node it builds, so a tree is checked once,
    bottom up, and no pass walks it again.

    Raises:
        DimensionError: *node* breaks the rule.
    """
    inner = frozenset(node.operand.dims)
    if isinstance(node, Sum):
        _check_sum(node, inner, context)
    elif isinstance(node, Join):
        join_dims(node.columns, inner, context, 'the expression')
    else:
        _check_translation(node, inner, spec, context)


def _not_carried(context: str, call: str, inner: frozenset[str], rewrite: str) -> str:
    """The refusal for an operator reaching a dim its operand does not carry; *rewrite* is the operator's own."""
    return f'{context}: {call} but the expression has only the dims {sorted(inner)}. {rewrite}.'


def _check_sum(node: Sum, inner: frozenset[str], context: str) -> None:
    """``sum`` reduces each dim in ``over`` away, so the operand carries every one.

    The axes a join opens never reach a frame: the sum over the join closes
    every one, and the join's own rules are the sum's.
    """
    if isinstance(node.operand, Join) and node.operand.columns.axes:
        assert node.over == node.operand.columns.axes, 'a sum through a relation closes exactly the axes its join opens'
        return
    for summed in node.over:
        if summed.dimension not in inner:
            raise DimensionError(
                _not_carried(context, f'sum(over={summed})', inner, 'Remove the sum, or correct the dimension')
            )


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
    return joined(columns, inner)


def sorted_dims(*dims: Iterable[str]) -> tuple[str, ...]:
    """Every dim in *dims*, once, sorted by name: what a node states as ``dims``."""
    return tuple(sorted(set().union(*dims)))


def joined(columns: JoinColumns, inner: Iterable[str]) -> frozenset[str]:
    """The dims a join on *columns* leaves of *inner*: the dims joined on go, and the dims grouped by arrive."""
    return (frozenset(inner) - set(columns.joined_dims)) | set(columns.grouped_dims)


#: The operator name a file writes for each translation, which its refusals quote.
_VERBS: dict[type[Translate | WindowSum], str] = {Translate: 'shift', WindowSum: 'sum_back'}


def _check_translation(node: Translate | WindowSum, inner: frozenset[str], spec: Spec, context: str) -> None:
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
            indexed = _check_body_dims(entry.expression, frame, f"Named expression '{ename}'")
            _check_dims_are_indexed(ename, frame, indexed, 'the expression is not')
            continue
        indexed = frozenset[str]()
        for region, label in zip(entry.expression.regions, [*declared.cases, None], strict=True):
            context = case_context(ename, label)
            if label is not None:
                _check_where_dims(region.when, frame, context)
            indexed |= _check_value_dims(region.value, frame, context) | region.when.dims
        _check_dims_are_indexed(ename, frame, indexed, 'no case value and no `when:` is')

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
        got = frozenset((*constraint.lhs.dims, *constraint.rhs.dims))
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
        got = program.objective.expression.dims
        if got:
            raise DimensionError(
                f'{context}: the expression carries dims {sorted(got)}, and an objective is one '
                f'number. Wrap each additive term in its own sum(): '
                f'`sum(p * cost) + sum(p_nom * capex)`.'
            )


def _check_value_dims(node: Expression, frame: frozenset[str], context: str) -> frozenset[str]:
    """A region's value may only carry dims the frame does — the ``otherwise:`` included.

    A wider one would give the quantity dims its entry does not, which is
    the second answer a ``dims:`` exists to avoid.
    """
    got = frozenset(node.dims)
    if not got <= frame:
        raise DimensionError(
            f'{context}: the value carries dims {sorted(got - frame)} outside the dims: '
            f'{sorted(frame)}. Add them to dims:, or take them out of the value.'
        )
    return got


def _check_body_dims(node: Expression, frame: frozenset[str], context: str) -> frozenset[str]:
    """A plain entry's expression is indexed only over dims its ``dims:`` gives; the dims it is indexed over come back."""
    got = frozenset(node.dims)
    if not got <= frame:
        raise DimensionError(
            f'{context}: the body carries dims {sorted(got - frame)} outside the dims: {sorted(frame)}. '
            f'Add them to dims:, or take them out of the body.'
        )
    return got


def _check_dims_are_indexed(name: str, declared: frozenset[str], indexed: frozenset[str], subject: str) -> None:
    """A declared ``dims:`` gives only dims the expression is indexed over, so the entry stands for its expression.

    A dim the expression is not indexed over would make the entry constant
    along it, and then the entry would not be its expression:
    ``sum(entry, over=d)`` would load where the expression summed over ``d``
    is refused.
    """
    if extra := sorted(declared - indexed):
        raise DimensionError(
            f"Named expression '{name}': dims: gives {extra}, but {subject} indexed over {extra}. A named "
            f'expression stands for its expression, so dims: gives only the dimensions it is indexed over. Take '
            f"{extra} out of dims:; an expression that reads '{name}' still repeats it along its own other dims."
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
