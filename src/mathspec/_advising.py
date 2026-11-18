# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Advice — what is decidable without data and is a note rather than a refusal.

One door, [`advice`][], over every pass of that kind.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from mathspec._boundedness import unbounded_notes
from mathspec._dimensions import operand_over
from mathspec._validation import to_spec
from mathspec.program import Advice, Join, Mask, Program, RelationPairComparison, walk

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from pathlib import Path

    from mathspec.program import Expression
    from mathspec.spec import Spec


def advice(spec: str | Path | Mapping[str, object] | Spec | Program) -> tuple[Advice, ...]:
    """Everything the language advises about *spec*, decided without data.

    Advice is a note, not a refusal: a file with advice still loads.

    Args:
        spec: Anything [`to_spec`][] accepts, or a [`Program`][], read as
            it arrived. A ``piecewise:`` or ``sos:`` entry is read as the rows
            it states, so the answer is the one its expansion gets, with
            nothing expanded.

    Returns:
        The never-an-axis advice sorted by dimension name, then the
        cross-product advice, then one note per entry the program reads and
        does not build, then the unboundedness advice; ``str()`` of each is
        its sentence.

    Raises:
        LanguageError: *spec* does not load; [`to_spec`][] says why.
        FileNotFoundError: A ``str`` with no newline that names no file.
    """
    program = spec if isinstance(spec, Program) else to_spec(spec).program
    return tuple(_never_an_axis(program) + _cross_products(program) + _given(program) + unbounded_notes(program))


def _given(program: Program) -> list[Advice]:
    """One note per entry the program reads and does not build.

    A note rather than a refusal: the file is a spec somebody meant, and only
    the consumer can tell whether the model it is layered onto provides the
    name. An expression this file adds a term to is completed by `merge`
    rather than by a host, so its note says that instead.
    """
    given = program.given
    written = {entry.adds_to for entry in program.expressions.values()}
    return [
        *(Advice('given', name, _given_note('parameter', name)) for name in given.parameters),
        *(Advice('given', name, _given_note('variable', name)) for name in given.variables),
        *(
            Advice(
                'given',
                name,
                _term_note(name) if name in written else _given_note('expression', name),
            )
            for name in given.expressions
        ),
        *(Advice('given', name, _given_note('row family', name)) for name in given.constraints),
        *(Advice('given', name, _given_note('condition', name)) for name in given.conditions),
    ]


def _given_note(kind: str, name: str) -> str:
    return (
        f"{kind} '{name}' is read here and declared elsewhere: the model this one is layered onto provides it. "
        f'A tool refuses the spec where that model does not, over the same dims. merge() replaces this '
        f'entry with the one another file '
        f'declares{", or builds it from the terms other files add" if kind == "expression" else ""}.'
    )


def _term_note(name: str) -> str:
    return (
        f"expression '{name}' is read here, and this file adds a term to it. merge() sums the term with the "
        f'terms other files add under that name. Until then, the program reads it and does not build it.'
    )


def _never_an_axis(program: Program) -> list[Advice]:
    """One piece of advice per dimension nothing reaches.

    A dimension a relation has a column over is reached: its labels are what
    that column is checked against, and a ``where`` selects on them, so it is
    in use even where nothing is indexed by it. A dimension only a given entry
    indexes is reached too: the column exists, in another file. The relation a
    dimension with members implies is no use of its own; a reached dimension
    reaches its members.
    """
    reached: set[str] = set()
    for entry in (
        *program.parameters.values(),
        *program.variables.values(),
        *program.constraints.values(),
        *program.given.parameters.values(),
        *program.given.variables.values(),
        *program.given.expressions.values(),
        *program.given.constraints.values(),
    ):
        reached.update(entry.dims)
    reached |= _grouped_axes(program)
    reached |= {dim for name, lk in program.relations.items() if name not in program.dimensions for dim in lk.dims}
    reached |= {dim for name in reached for _, dim in program.dimensions[name].over}

    return [
        Advice(
            'never-an-axis',
            name,
            f"dimension '{name}' is never used: nothing is indexed by it, nothing "
            f'sums into it, and no relation has a column over it. Remove it, or keep it '
            f'if the entries that use it are still to be written.',
        )
        for name in program.dimensions
        if name not in reached
    ]


def _cross_products(program: Program) -> list[Advice]:
    """One note per dimension with members that ``dims:`` crosses with a member of it, or with another that shares one.

    A note rather than a refusal: the cross product is what such ``dims:``
    say, and loads. A named expression takes no ``where:``, so the entry that
    reads it keeps the pairs of one member, and draws the note where it does
    not.
    """
    notes: list[Advice] = []
    for label, name, dims, where, operands in _framed_entries(program):
        over = {dim: [member for _, member in program.dimensions[dim].over] for dim in dims}
        tuples = sorted(dim for dim in dims if over[dim])
        for one, other in combinations(tuples, 2) if label != 'Named expression' else ():
            shared = sorted(set(over[one]) & set(over[other]))
            if unjoined := [m for m in shared if not _joins(where, program, one, other, m)]:
                text = _shared_note(label, name, (one, other), shared, unjoined, program)
                notes.append(Advice('cross-product', name, text))
        notes.extend(
            Advice('cross-product', name, _beside_note(label, name, dim, member, operands, program))
            for dim in tuples
            for member in sorted(set(over[dim]) & set(dims))
        )
    return notes


def _framed_entries(
    program: Program,
) -> Iterator[tuple[str, str, tuple[str, ...], Mask | None, tuple[Expression, ...]]]:
    """Each entry the file builds over a ``dims:``: its label, name, dims, ``where:``, and operands."""
    for name, parameter in program.parameters.items():
        yield 'Parameter', name, parameter.dims, parameter.where, ()
    for name, variable in program.variables.items():
        yield 'Variable', name, variable.dims, variable.where, ()
    for name, constraint in program.constraints.items():
        yield 'Constraint', name, constraint.dims, constraint.where, (constraint.lhs, constraint.rhs)
    for name, expression in program.expressions.items():
        yield 'Named expression', name, expression.dims, None, (expression.expression,)
    for name, curve in program.piecewise.items():
        yield 'piecewise', name, curve.frame, curve.where, tuple(link.expression for link in curve.links)


def _joins(where: Mask | None, program: Program, one: str, other: str, member: str) -> bool:
    """Whether *where* keeps only the pairs of *one* and *other* that agree on *member*: an ``==`` of the two under ``AND``."""
    if where is None:
        return False
    wanted = {(one, member), (other, member)}
    return any(
        isinstance(atom, RelationPairComparison)
        and atom.op == '=='
        and {_member_of(program, atom.name, atom.column), _member_of(program, atom.other, atom.other_column)} == wanted
        for atom in where.conjuncts
    )


def _member_of(program: Program, relation: str, column: str) -> tuple[str, str] | None:
    """The dimension with members and the member that *relation*[*column*] reads, or ``None`` where it is no such read."""
    dimension = program.dimensions.get(relation)
    members = dict(dimension.over) if dimension else {}
    return (relation, members[column]) if column in members else None


def _role(program: Program, dim: str, member: str) -> str:
    """The first role of *dim* over *member*: a comparison reads one column, and of two roles over one member, either."""
    return next(role for role, over in program.dimensions[dim].over if over == member)


def _roles(program: Program, dim: str, member: str) -> str:
    """Every role of *dim* over *member*, as the refusals at load spell a call through one of them."""
    return ' or '.join(role for role, over in program.dimensions[dim].over if over == member)


def _shared_note(
    label: str, name: str, pair: tuple[str, str], shared: list[str], unjoined: list[str], program: Program
) -> str:
    one, other = pair
    quoted = ' and '.join(f"'{m}'" for m in shared)
    join = ' AND '.join(f'{one}[{_role(program, one, m)}] == {other}[{_role(program, other, m)}]' for m in unjoined)
    return (
        f"{label} '{name}': dims: lists '{one}' and '{other}', which share the member{'s' if len(shared) > 1 else ''} "
        f'{quoted}, so the entry is their cross product: each {one} meets every {other}, of its own '
        f'{" and ".join(shared)} or another. For the pairs that agree on {" and ".join(unjoined)} (the inner join), '
        f'add {join} to where:.'
    )


def _beside_note(
    label: str, name: str, dim: str, member: str, operands: tuple[Expression, ...], program: Program
) -> str:
    columns = _roles(program, dim, member)
    read, summed = operand_over(operands, (member,), dim), operand_over(operands, (dim,), member)
    return (
        f"{label} '{name}': dims: lists '{dim}' beside its member '{member}', so the entry is their cross product: "
        f'each {dim} meets every {member}, not only its own. For its own {member}, drop {member!r} from dims: and '
        f'read the operand at each tuple: at({read}, by={dim}[{columns}]). To go by {member} instead, drop {dim!r} '
        f'from dims: and sum to the member: sum({summed}, over={dim}, by={dim}[{columns}]).'
    )


def _grouped_axes(program: Program) -> set[str]:
    """The axes the expressions create beyond what any entry indexes.

    ``sum(by=)`` groups onto its target and ``at()`` spreads onto its fine
    dimension: either way, the dims the join groups by and did not join on.
    """
    axes: set[str] = set()
    for node in walk(*program.roots):
        if isinstance(node, Join):
            axes.update(node.columns.added_dims)
    return axes
