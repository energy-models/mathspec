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
    ExpressionReference,
    Join,
    JoinColumns,
    JoinedCondition,
    Mask,
    ParameterComparison,
    ParameterDefined,
    ParameterReference,
    Partition,
    RelationComparison,
    RelationDefined,
    RelationPairComparison,
    Sum,
    Translate,
    TranslatedCondition,
    VariableDefined,
    VariableReference,
    WindowSum,
    walk,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

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
        _check_sum(node, inner, spec, context)
    elif isinstance(node, Join):
        join_dims(node.columns, inner, context, 'the expression')
    else:
        _check_translation(node, inner, spec, context)


def _not_carried(context: str, call: str, inner: frozenset[str], rewrite: str) -> str:
    """The refusal for an operator reaching a dim its operand does not carry; *rewrite* is the operator's own."""
    return f'{context}: {call} but the expression has only the dims {sorted(inner)}. {rewrite}.'


def _check_sum(node: Sum, inner: frozenset[str], spec: Spec, context: str) -> None:
    """``sum`` reduces each dim in ``over`` away, so the operand carries every one.

    The axes a join opens never reach a frame: the sum over the join closes
    every one, and the join's own rules are the sum's.
    """
    if isinstance(node.operand, Join) and node.operand.columns.axes:
        assert node.over == node.operand.columns.axes, 'a sum through a relation closes exactly the axes its join opens'
        return
    for summed in node.over:
        if summed.dimension not in inner:
            rewrite = _sum_through(summed.dimension, {s.dimension for s in node.over}, inner, spec)
            raise DimensionError(
                _not_carried(
                    context, f'sum(over={summed})', inner, rewrite or 'Remove the sum, or correct the dimension'
                )
            )


def _sum_through(summed: str, over: set[str], inner: frozenset[str], spec: Spec) -> str | None:
    """The rewrite for a sum over *summed*, a member of a dimension the operand carries, or ``None``.

    A dimension with members is one dimension in a sum, so the sum is over it
    and groups by the members the call does not sum away.
    """
    for name in sorted(inner):
        members = spec.dimensions[name].members
        dims = [dim for _, dim in members]
        if summed not in dims:
            continue
        kept = [role for role, dim in members if dim not in over]
        if len(set(dims)) < len(dims):
            by = f', by={name}[<the members to keep>]'
        else:
            by = f', by={name}[{", ".join(kept)}]' if kept else ''
        return f"'{summed}' is a member of '{name}', which is one dimension here. Write sum(..., over={name}{by})"
    return None


def join_dims(columns: JoinColumns, inner: frozenset[str], context: str, operand: str) -> frozenset[str]:
    """The dims *inner* has once *columns* joins it, an expression's or a condition's alike.

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
    if columns.name in inner and (both := sorted(inner & {columns.dim(r) for r in columns.relation.values})):
        raise DimensionError(
            f"{context}: {call} reads through '{columns.name}', and {operand} carries both '{columns.name}' and "
            f'its member {both} (dims {sorted(inner)}). Sum {both} out of the operand first, or declare the '
            f"operand over '{columns.name}' without {both}."
        )
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


def _bound_outside(
    context: str, written: str, bound: Expression, outside: frozenset[str], frame: frozenset[str], spec: Spec
) -> str:
    """The refusal of a bound over dims the variable lacks, with the rewrite for where each dim comes from.

    A looked-up bound gains a dim from the parameter it reads, from the key
    of the relation it reads through, or from both. Each source has its own
    rewrite, and the bound loads only once every rewrite it needs is made.
    """
    if isinstance(bound, ParameterReference):
        rewrite = _member_rewrite(outside, frame, spec, (bound,)) or f"Declare '{bound.name}' over the variable's dims"
        return (
            f"{context} parameter '{bound.name}' has dims {sorted(outside)} outside the variable's dims "
            f'{sorted(frame)}. {rewrite}.'
        )
    assert isinstance(bound, Join) and isinstance(bound.operand, ParameterReference), (
        'a bound is a number, a parameter, or a lookup of one'
    )
    name = bound.operand.name
    kept = sorted(outside & set(bound.operand.dims))
    rewrites = [
        *([f"declare '{name}' without {kept}"] if kept else []),
        *(
            [f"look '{name}' up through a relation keyed by the variable's dims"]
            if outside & set(bound.columns.grouped_dims)
            else []
        ),
    ]
    rewrite = ', and '.join(rewrites)
    return (
        f"{context} {written!r} has dims {sorted(outside)} outside the variable's dims {sorted(frame)}. "
        f'{rewrite[0].upper()}{rewrite[1:]}.'
    )


def _at_member(
    stray: Iterable[str],
    frame: frozenset[str],
    spec: Spec,
    operands: Iterable[Expression] = (),
    read: str | None = None,
) -> str | None:
    """The rewrite for dims in *stray* that are members of a dimension in *frame*, or ``None`` where one is not.

    An operand over a member does not align with the dimension that lists the
    member, so the file reads it at each tuple with ``at``. The rewrite names
    *read*, or else the operand in *operands* that is over the members.
    """
    wanted = sorted(stray)
    for name in sorted(frame):
        if (columns := _member_columns(name, wanted, spec)) is None:
            continue
        read = read or operand_over(operands, wanted, name)
        return (
            f'{", ".join(map(repr, wanted))} {"is a member" if len(wanted) == 1 else "are members"} of '
            f"'{name}', which is one dimension here. Read the operand at each tuple: at({read}, by={name}[{columns}])"
        )
    return None


def _spread_over(
    stray: Iterable[str],
    frame: frozenset[str],
    spec: Spec,
    operands: Iterable[Expression] = (),
    read: str | None = None,
) -> str | None:
    """The rewrite for a dimension in *stray* whose members are all in *frame*, or ``None`` where there is none.

    An operand over a dimension with members does not align with entries
    over the members, so the file spreads it over them with ``at``. Two
    members over one dimension cannot both arrive, so such a dimension has
    no spread.
    """
    for name in sorted(stray):
        members = spec.dimensions[name].members
        dims = [dim for _, dim in members]
        if not members or not set(dims) <= frame or len(set(dims)) < len(dims):
            continue
        read = read or operand_over(operands, (name,), '')
        roles = ', '.join(role for role, _ in members)
        return (
            f"'{name}' lists the members {dims}, and is one dimension here. Spread the operand over its members: "
            f'at({read}, by={name}[{roles}])'
        )
    return None


def _member_rewrite(
    stray: Iterable[str],
    frame: frozenset[str],
    spec: Spec,
    operands: Iterable[Expression] = (),
    read: str | None = None,
) -> str | None:
    """The ``at`` that brings *stray* into *frame* through a dimension with members, or ``None`` where none does."""
    wanted = sorted(stray)
    return _at_member(wanted, frame, spec, operands, read) or _spread_over(wanted, frame, spec, operands, read)


def _member_columns(name: str, wanted: list[str], spec: Spec) -> str | None:
    """The columns of the relation *name* implies over the dims *wanted*, as a call writes them, or ``None`` where one is no member."""
    members = spec.dimensions[name].members
    if not set(wanted) <= {dim for _, dim in members}:
        return None
    return ', '.join(' or '.join(role for role, dim in members if dim == d) for d in wanted)


def operand_over(operands: Iterable[Expression], over: Iterable[str], without: str) -> str:
    """The outermost name in *operands* over every dim in *over* and not over *without*, or ``...`` where none is.

    A named expression is a name the file wrote, so the walk takes it before
    the body it stands for.
    """
    wanted, named = set(over), ParameterReference | VariableReference | ExpressionReference
    found = (n for n in walk(*operands) if isinstance(n, named) and wanted <= set(n.dims) and without not in n.dims)
    return next((n.name for n in found), '...')


def check_meeting(left: Expression, right: Expression, spec: Spec, context: str, frame: frozenset[str]) -> None:
    """Two operands meet a member against the dimension that lists it only where *frame* declares both.

    A dimension with members is one plain dimension, so an operand over a
    member does not align with one over the dimension: the two meet as their
    cross product. An entry whose ``dims:`` declares both asks for that
    product; anywhere else, a sum or the objective would add it up without a
    frame that names it. *frame* is the entry's ``dims:`` less what an
    enclosing sum takes away, and empty in the objective.

    Raises:
        DimensionError: One operand carries a dimension with members, the
            other carries a member of it but not the dimension, and *frame*
            lacks one of the two.
    """
    for one, other in ((left, right), (right, left)):
        for name in sorted(set(one.dims) - set(other.dims)):
            members = [dim for _, dim in spec.dimensions[name].members]
            stray = sorted((set(members) & set(other.dims)) - set(one.dims))
            if stray and not {name, *stray} <= frame:
                read = operand_over((one,), (name,), stray[0])
                columns = _member_columns(name, stray, spec)
                onto_members = (
                    f'spread {read} over the members: at({read}, by={name}[{columns}])'
                    if stray == sorted(members)
                    else f'sum {read} to the member: sum({read}, over={name}, by={name}[{columns}])'
                )
                raise DimensionError(
                    f"{context}: an operand over {stray} meets one over '{name}'. "
                    f'{_at_member(stray, frozenset({name}), spec, (other,))}, or {onto_members}.'
                )


def check_spec(spec: Spec, program: Program, bounds: Mapping[str, tuple[Expression | None, Expression | None]]) -> None:
    """Check every entry's dim rules, on the trees *program* holds for *spec*.

    *bounds* holds each variable's bounds as its ``bounds:`` declares them,
    which for a binary are not the 0 and 1 *program* holds.

    Raises:
        DimensionError: On the first entry that breaks one.
    """
    for pname, parameter in program.parameters.items():
        _check_condition_dims(parameter.where, frozenset(parameter.dims), f"Parameter '{pname}'", spec)

    for vname, vdef in spec.variables.items():
        frame = frozenset(vdef.dims)
        context = f"Variable '{vname}'"
        _check_condition_dims(program.variables[vname].where, frame, context, spec)
        for side, bound in zip(('lower', 'upper'), bounds[vname], strict=True):
            if bound is not None and (outside := frozenset(bound.dims) - frame):
                written = getattr(vdef.bounds, side)
                raise DimensionError(_bound_outside(f'{context}: bounds.{side}', written, bound, outside, frame, spec))

    for ename, entry in program.expressions.items():
        declared = spec.expressions[ename]
        if declared.dims is None:
            continue
        frame = frozenset(declared.dims)
        if not isinstance(entry.expression, Cases):
            indexed = _check_value_dims(entry.expression, frame, f"Named expression '{ename}'", spec, 'body')
            _check_dims_are_indexed(ename, frame, indexed, 'the expression is not')
            continue
        indexed = frozenset[str]()
        for region, label in zip(entry.expression.regions, [*declared.cases, None], strict=True):
            context = case_context(ename, label)
            if label is not None:
                _check_condition_dims(region.when, frame, context, spec)
            indexed |= _check_value_dims(region.value, frame, context, spec, 'value') | frozenset(region.when.dims)
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
        _check_condition_dims(constraint.where, frame, context, spec)
        got = frozenset((*constraint.lhs.dims, *constraint.rhs.dims))
        if got != frame:
            stray, missing = sorted(got - frame), sorted(frame - got)
            operands = (constraint.lhs, constraint.rhs)
            detail = (
                f'carries dims {stray} that are not in its dims: {sorted(frame)}. '
                f'{_member_rewrite(stray, frame, spec, operands) or "Add them to dims:, or sum them out"}'
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


def _check_value_dims(node: Expression, frame: frozenset[str], context: str, spec: Spec, noun: str) -> frozenset[str]:
    """A named expression's body, or a region's value, carries only dims its ``dims:`` gives; those it carries come back.

    A wider one would give the quantity dims its entry does not, which is
    the second answer a ``dims:`` exists to avoid.
    """
    got = frozenset(node.dims)
    if stray := sorted(got - frame):
        rewrite = _member_rewrite(stray, frame, spec, (node,)) or f'Add them to dims:, or take them out of the {noun}'
        raise DimensionError(
            f'{context}: the {noun} carries dims {stray} outside the dims: {sorted(frame)}. {rewrite}.'
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


def _check_condition_dims(mask: Mask | None, frame: frozenset[str], context: str, spec: Spec) -> None:
    """A condition may only test dims the frame carries; reducing an outside dim to fit would fail open.

    The refusal names the leaf that left the frame, reading its dims as
    [`dims`][mathspec.program.Mask.dims] does.
    """
    if mask is None:
        return

    for atom in mask.atoms:
        if not (outside := [d for d in Mask(atom).dims if d not in frame]):
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
                leaf = 'a comparison of expressions'
            case CountComparison():
                leaf = f"a count over '{atom.over}'"
            case TranslatedCondition():
                leaf = f"a condition translated along '{atom.along}'"
            case JoinedCondition():
                leaf = f"a condition read through '{atom.columns.name}'"
            case _:
                assert_never(atom)
        read = atom.name if isinstance(atom, ParameterDefined | ParameterComparison | VariableDefined) else None
        rewrite = (
            _member_rewrite(outside, frame, spec, read=read)
            or 'Add them to dims:, or test a name over the declared dims'
        )
        raise DimensionError(
            f'{context}: {leaf} reads dims {outside} outside the declared dims {sorted(frame)}. {rewrite}.'
        )
