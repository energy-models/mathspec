# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A decided variable, written back as a supplied number — the one move a subproblem makes.

A Benders subproblem, a myopic step and a rolling window each take a variable
someone else decided and read it as data. The variable becomes a parameter
under the same name, so every expression naming it goes on reading it; what
the rewrite has to keep is what the variable meant where it did not exist.

A masked variable with ``absence: undefined`` has no value outside its mask,
and a row that reads it there is not built. A parameter has no absence: a
missing row reads as ``0`` and the row stands. So each read of the variable
outside a summing operator — where its absence would have taken the row — is
proven guarded by the variable's own mask, or the mask is added to that
constraint's ``where:``, or the fix is refused, naming the reader. Inside a
summing operator an absent summand and a ``0`` one are the same sum.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mathspec.errors import LanguageError, SchemaError, did_you_mean
from mathspec.program import (
    Cases,
    GroupSum,
    Pullback,
    Sum,
    Translate,
    Variable,
    WindowSum,
    children,
    variables_of,
)
from mathspec.sos import section
from mathspec.validation import to_spec

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mathspec.program import Expression, Mask, Program, VariableDeclaration
    from mathspec.spec import Spec


def fix(spec: Spec, names: tuple[str, ...]) -> Spec:
    """*spec* with each of *names* a parameter rather than a variable; see [`Spec.fix`][mathspec.spec.Spec.fix]."""
    _refuse_names(spec, names)
    raw = spec.to_dict()
    refusals: list[str] = []
    for name in names:
        refusals += _fix_one(raw, spec, name)
    if refusals:
        raise LanguageError('\n'.join(refusals))
    _settled_rows_to_assumptions(raw, spec, frozenset(names))
    return to_spec(raw)


def _settled_rows_to_assumptions(raw: dict[str, object], spec: Spec, fixed: frozenset[str]) -> None:
    """Move every constraint that named only fixed variables into ``assumptions:``, under its own name.

    Such a row decided the fixed variables — a capacity's floor, a cap on
    what is built — and with them supplied it compares numbers, which the
    language refuses as a row and states as an assumption the consumer checks.
    """
    for name, row in spec.program.constraints.items():
        if variables_of(row.lhs, row.rhs) <= fixed:
            written = section(raw, 'constraints').pop(name)
            assert isinstance(written, dict), 'a validated spec carries each constraint as a mapping'
            declared = spec.constraints[name]
            section(raw, 'assumptions')[name] = {
                'holds': declared.expression,
                **({'where': written['where']} if written.get('where') else {}),
                'description': declared.description
                or f"constraint '{name}' decided what is now supplied, so the supplied numbers must meet it",
            }


def _refuse_names(spec: Spec, names: tuple[str, ...]) -> None:
    """Refuse a name that is not a variable this spec declares, or one given twice.

    A given variable is declared by another file, so this spec has no
    declaration to rewrite.

    Raises:
        SchemaError: One line per name refused.
    """
    variables = spec.program.variables
    lines = [
        f"fix: '{name}' is a given variable, which another file declares. Fix it on the spec that merge "
        f'composes, where it is declared.'
        if name in spec.given.variables
        else f"fix: '{name}' is not a variable of this spec. " + did_you_mean(name, variables, label='Variables')
        for name in dict.fromkeys(names)
        if name not in variables
    ]
    lines += [
        f"fix: '{name}' is given {names.count(name)} times; after the first it is a parameter, not a variable."
        for name in dict.fromkeys(names)
        if names.count(name) > 1
    ]
    if lines:
        raise SchemaError('\n'.join(lines))


def _fix_one(raw: dict[str, object], spec: Spec, name: str) -> list[str]:
    """Rewrite variable *name* in *raw* as a parameter, returning a refusal for each reader that forbids it."""
    program = spec.program
    variable, declared = program.variables[name], spec.variables[name]
    refusals = [
        f"fix: '{name}' is the variable of set '{set_name}', which restricts a decision the "
        f'fixed spec no longer makes. Fix it after expand("sos"), or drop the set.'
        for set_name, block in program.sos.items()
        if block.variable == name
    ]
    refusals += [
        f"fix: '{name}' stands in curve '{curve_name}'. Fix it after expand(), where the curve is rows."
        for curve_name, curve in program.piecewise.items()
        if name in variables_of(*(link.expression for link in curve.links)) or curve.activity == name
    ]
    guarded_by: list[str] = []
    if variable.where is not None and variable.absence == 'undefined':
        found, guarded_by = _unguarded_reads(program, name, variable)
        refusals += found
    if refusals:
        return refusals

    del section(raw, 'variables')[name]
    section(raw, 'parameters')[name] = {
        'dims': list(declared.dims),
        'dtype': 'float' if variable.domain == 'continuous' else 'int',
        **({'description': declared.description} if declared.description else {}),
    }
    mask = declared.where
    constraints = section(raw, 'constraints')
    for constraint in guarded_by:
        written = spec.constraints[constraint].where
        row = constraints[constraint]
        assert isinstance(row, dict), 'a validated spec carries each constraint as a mapping'
        row['where'] = f'({written}) AND ({mask})' if written else mask
    if holds := _held(name, variable.domain, declared.bounds.lower, declared.bounds.upper):
        assumption = f'{name}_within_bounds'
        if assumption in spec.assumptions:
            return [f"fix: the bounds of '{name}' become assumption '{assumption}', which the spec already declares."]
        section(raw, 'assumptions')[assumption] = {
            'holds': holds,
            **({'where': mask} if mask else {}),
            'description': f"'{name}' was a decision held to these bounds, so a number supplied for it is held to them too",
        }
    return []


def _held(name: str, domain: str, lower: float | str | None, upper: float | str | None) -> str:
    """The bounds and domain of a variable, as the predicate its supplied numbers must meet."""
    sides = [f'{name} >= 0', f'{name} <= 1'] if domain == 'binary' else []
    if lower is not None:
        sides.append(f'{name} >= {lower}')
    if upper is not None:
        sides.append(f'{name} <= {upper}')
    return ' AND '.join(sides)


def _unguarded_reads(program: Program, name: str, variable: VariableDeclaration) -> tuple[list[str], list[str]]:
    """The refusals, and the constraints whose ``where:`` the mask is added to, for each read absence would spread from.

    A read is guarded when a mask above it — the row's ``where:``, or the
    ``when`` of a case it stands in — holds every conjunct of the variable's
    own mask. An unguarded read directly in a constraint whose frame carries
    the variable's dims takes the mask into that constraint's ``where:``,
    which drops the rows the absence dropped. Anywhere else the mask cannot be
    carried to the row, so the fix is refused.
    """
    mask = variable.where
    assert mask is not None, 'only a masked variable has reads to guard'
    refusals: list[str] = []
    guarded_by: list[str] = []
    readers: list[tuple[str, str | None, Mask | None, tuple[str, ...], Expression]] = [
        (f"constraint '{c}'", c, row.where, row.dims, side)
        for c, row in program.constraints.items()
        for side in (row.lhs, row.rhs)
    ]
    if program.objective is not None:
        readers.append(('the objective', None, None, (), program.objective.expression))
    for label, constraint, row_mask, frame, root in readers:
        for regions, moved in _spreading_reads(root, name):
            if _guards(mask, (*((row_mask,) if row_mask is not None else ()), *regions)):
                continue
            if constraint is not None and not regions and not moved and set(variable.dims) <= set(frame):
                if constraint not in guarded_by:
                    guarded_by.append(constraint)
                continue
            where = 'through a shift or a relation' if moved else 'in a case' if regions else 'there'
            refusals.append(
                f"fix: {label} reads '{name}' outside a sum, {where}, where no mask keeps the rows "
                f"'{name}' is absent from. As a parameter it would read 0 there and the rows would stand. "
                f"Guard the read with the variable's own where:, or declare absence: zero if it is zero there."
            )
            break
    return refusals, guarded_by


def _spreading_reads(node: Expression, name: str) -> Iterator[tuple[tuple[Mask, ...], bool]]:
    """Each read of *name* under *node* that no summing operator absorbs, with the cases above it and whether it moved.

    A read has moved when a shift or a relation stands between it and the
    row, so the coordinate it is absent at is not the row's.
    """

    def visit(node: Expression, regions: tuple[Mask, ...], moved: bool) -> Iterator[tuple[tuple[Mask, ...], bool]]:
        if isinstance(node, Variable):
            if node.name == name:
                yield regions, moved
            return
        if isinstance(node, Sum | GroupSum | WindowSum):
            return
        if isinstance(node, Cases):
            for region in node.regions:
                yield from visit(region.value, (*regions, region.when), moved)
            return
        for child in children(node):
            yield from visit(child, regions, moved or isinstance(node, Translate | Pullback))

    yield from visit(node, (), False)


def _guards(mask: Mask, above: tuple[Mask, ...]) -> bool:
    """Whether some mask in *above* holds every conjunct of *mask*."""
    return any(set(mask.conjuncts) <= set(guard.conjuncts) for guard in above)
