# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A decided variable, written back as a supplied number — the one move a subproblem makes.

A Benders subproblem, a myopic step and a rolling window each take a variable
someone else decided and read it as data. The variable becomes a parameter
under the same name, so every expression naming it goes on reading it, and the
parameter takes the variable's ``missing:``: a coordinate the variable's mask
left out is a missing row of the parameter, and means what it meant before.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mathspec.errors import LanguageError, SchemaError, did_you_mean
from mathspec.program import variables_of
from mathspec.sos import section
from mathspec.validation import to_spec

if TYPE_CHECKING:
    from mathspec.program import Program
    from mathspec.spec import BoundsBlock, Spec


def fix(spec: Spec, names: tuple[str, ...]) -> Spec:
    """*spec* with each of *names* a parameter rather than a variable; see [`Spec.fix`][mathspec.spec.Spec.fix]."""
    _refuse_names(spec, names)
    if refusals := [line for name in names for line in _check(spec, name)]:
        raise LanguageError('\n'.join(refusals))
    raw = spec.to_dict()
    for name in names:
        _rewrite(raw, spec, name)
    _settled_rows_to_assumptions(raw, spec.program, frozenset(names))
    return to_spec(raw)


def _refuse_names(spec: Spec, names: tuple[str, ...]) -> None:
    """Refuse a name that is not a variable this spec declares, or one given twice.

    A given variable is declared by another file, so this spec has no
    declaration to rewrite.

    Raises:
        SchemaError: One line per name refused.
    """
    variables = spec.program.variables
    lines = [
        f"fix: '{name}' is a given variable, which another file declares. Fix it on the merged spec, "
        f'where a fragment declares it.'
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


def _check(spec: Spec, name: str) -> list[str]:
    """The refusals for variable *name*.

    Every name is checked before the first one is rewritten, so a refused
    call changes nothing.
    """
    program = spec.program
    declared = spec.variables[name]
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
    assumption = f'{name}_within_bounds'
    if assumption in spec.assumptions and _held(name, declared.domain, declared.bounds):
        refusals.append(f"fix: the bounds of '{name}' become '{assumption}', which the spec already declares.")
    return refusals


def _rewrite(raw: dict[str, object], spec: Spec, name: str) -> None:
    """Rewrite variable *name* in *raw* as a parameter that reads a missing row as the variable read its mask.

    A variable with no ``where:`` exists at every coordinate, so its parameter
    keeps the default, ``error``, and a supplied table short of a row is refused.
    """
    declared = spec.variables[name]
    del section(raw, 'variables')[name]
    section(raw, 'parameters')[name] = {
        'dims': list(declared.dims),
        'dtype': 'float' if declared.domain == 'continuous' else 'int',
        **({'missing': declared.missing} if declared.where else {}),
        **({'description': declared.description} if declared.description else {}),
    }
    mask = declared.where
    if holds := _held(name, declared.domain, declared.bounds):
        section(raw, 'assumptions')[f'{name}_within_bounds'] = {
            'holds': holds,
            **({'where': mask} if mask else {}),
            'description': f"'{name}' was a decision held to these bounds, so a number supplied for it is held to them too",
        }


def _settled_rows_to_assumptions(raw: dict[str, object], program: Program, fixed: frozenset[str]) -> None:
    """Move every constraint that named only fixed variables into ``assumptions:``, under its own name.

    Such a row decided the fixed variables — a capacity's floor, a cap on
    what is built — and with them supplied it compares numbers, which the
    language refuses as a row and states as an assumption the consumer checks.
    """
    for name, row in program.constraints.items():
        if variables_of(row.lhs, row.rhs) <= fixed:
            written = section(raw, 'constraints').pop(name)
            assert isinstance(written, dict), 'a validated spec carries each constraint as a mapping'
            section(raw, 'assumptions')[name] = {
                'holds': written['expression'],
                **({'where': written['where']} if written.get('where') else {}),
                'description': written.get('description')
                or f"constraint '{name}' decided what is now supplied, so the supplied numbers must meet it",
            }


def _held(name: str, domain: str, bounds: BoundsBlock) -> str:
    """The bounds and domain of a variable, as the predicate its supplied numbers must meet.

    A binary's ``0`` and ``1`` stand in for a bound it leaves out or states
    as the same number, so each side is written once.
    """
    implied = {'>=': 0, '<=': 1} if domain == 'binary' else {}
    sides = [*implied.items()]
    sides += [
        (op, bound)
        for op, bound in (('>=', bounds.lower), ('<=', bounds.upper))
        if bound not in (None, implied.get(op))
    ]
    return ' AND '.join(f'{name} {op} {bound}' for op, bound in sides)
