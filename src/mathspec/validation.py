# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The front door, and the rules an entry is held to against the others before any expression is read.

[`to_spec`][] reads a spec definition into a [`Spec`][].
[`reference_errors`][] holds the rules one entry is held to against
the others — a name declared once, a frame over declared dimensions, a bound
naming a numeric parameter, a set over one dim of one variable, a curve
through parameters carrying its breakpoints — which lowering runs before it
reads any expression, since resolution assumes every one of them.
[`emitted_name_errors`][] is read off the program instead: what an entry's
expansion writes is decided by the entry as lowered. The rules that need a
typed expression stay with the expressions in [`lower`][mathspec.lowering.lower]:
a macro formal against a dimension, a curve's links, and every dim rule.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import TYPE_CHECKING

from mathspec._yaml import read_spec
from mathspec.errors import SchemaError, unordered
from mathspec.operators import BUILTIN_NAMES
from mathspec.piecewise import Emitted as EmittedCurve
from mathspec.sos import Emitted as EmittedSet
from mathspec.sos import coefficients
from mathspec.spec import NUMERIC_DTYPES, Spec, side_columns

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

    from mathspec.program import Program


def to_spec(spec: str | Path | Mapping[str, object] | Spec) -> Spec:
    """Load and validate a spec definition — the language's front door.

    Everything decidable without data is decided here: schema shape, every
    rule one entry is held to against the others, every expression and
    where string, and every macro template.

    Args:
        spec: A YAML path — a [`Path`][], or a ``str`` with no
            newline in it — the YAML text itself as a ``str`` with one, a
            mapping, or a loaded [`Spec`][].

    Returns:
        The spec *as the file declares it*, ``piecewise:`` intact.

    Raises:
        LanguageError: Anything the language does not accept, a text that is
            not a mapping of sections included.
        FileNotFoundError: A ``str`` with no newline that names no file.
    """
    if isinstance(spec, (list, tuple)):
        msg = 'to_spec takes one file, one dict or one Spec, not a list. Merge the entries into one dict.'
        raise SchemaError(msg)
    if isinstance(spec, Spec):
        return spec
    return Spec.model_validate(spec if isinstance(spec, Mapping) else read_spec(spec))


def emitted_name_errors(spec: Spec, program: Program) -> list[str]:
    """Every name a set or curve of *program* would write out that *spec* already declares.

    Read off the program rather than the file, since what a curve writes is
    decided by the curve as lowered — its links, its method, its mask.
    """
    by_entry = [
        *((f"Sos '{name}'", EmittedSet.of(name, entry.sos_type).by_kind) for name, entry in program.sos.items()),
        *((f"piecewise '{name}'", EmittedCurve.of(name, curve).by_kind) for name, curve in program.piecewise.items()),
    ]
    return [error for context, by_kind in by_entry for error in _collisions(spec, context, by_kind)]


def reference_errors(spec: Spec) -> list[str]:
    """Every cross-entry rule *spec* breaks, collected rather than raised on the first."""
    return [
        *_name_collisions(spec),
        *_frame_dimensions(spec),
        *_relation_targets(spec),
        *_bound_names(spec),
        *_sos_shapes(spec),
        *_sos_bounds(spec),
        *_piecewise_references(spec),
        *_given_constraint_collisions(spec),
    ]


def undeclared_dimension(kind: str, name: str, dimension: str) -> str:
    """The one wording for an entry naming a dimension the file does not declare."""
    return f"{kind} '{name}' references undeclared dimension '{dimension}'. Declare it under 'dimensions:'."


def _flat_namespace(spec: Spec) -> list[tuple[str, Iterable[str]]]:
    """Each kind of entry whose names share the one namespace an expression reads, in file order."""
    return [
        ('dimension', spec.dimensions),
        ('relation', spec.relations),
        ('parameter', spec.parameters),
        ('given parameter', spec.given.parameters),
        ('variable', spec.variables),
        ('given variable', spec.given.variables),
        ('named expression', spec.expressions),
        ('given expression', spec.given.expressions),
        ('mask', spec.masks),
        ('given mask', spec.given.masks),
        ('macro', spec.macros),
    ]


def _name_collisions(spec: Spec) -> Iterator[str]:
    """A name is declared once, and never as a built-in operator."""
    seen: dict[str, str] = {}
    for kind, group in _flat_namespace(spec):
        for name in group:
            if name in BUILTIN_NAMES:
                yield f"{kind.capitalize()} '{name}' collides with the built-in operator '{name}'. Rename the {kind}."
            if name in seen:
                yield (
                    f"{kind.capitalize()} '{name}' collides with the {seen[name]} of the same name. Rename one of them."
                )
            else:
                seen[name] = kind


def _given_constraint_collisions(spec: Spec) -> Iterator[str]:
    """A row family is either built here or given, never both.

    Constraint names sit outside the flat namespace [`_name_collisions`][]
    walks, so this is the one place the two constraint sections meet.
    """
    for name in spec.given.constraints:
        if name in spec.constraints:
            yield f"Given constraint '{name}' is also declared under 'constraints:'. Delete one of the two."


def _frame_dimensions(spec: Spec) -> Iterator[str]:
    """Every frame is a product of distinct, declared dimensions."""
    frames = [
        *(('Parameter', name, p.dims) for name, p in spec.parameters.items()),
        *(('Variable', name, v.dims) for name, v in spec.variables.items()),
        *(('Given parameter', name, g.dims) for name, g in spec.given.parameters.items()),
        *(('Given variable', name, g.dims) for name, g in spec.given.variables.items()),
        *(('Given expression', name, g.dims) for name, g in spec.given.expressions.items()),
        *(('Given constraint', name, g.dims) for name, g in spec.given.constraints.items()),
        *(('Given mask', name, g.dims) for name, g in spec.given.masks.items()),
        *(('Constraint', name, c.dims) for name, c in spec.constraints.items()),
        *(('Named expression', name, e.dims or []) for name, e in spec.expressions.items()),
    ]
    for kind, name, dims in frames:
        yield from (undeclared_dimension(kind, name, d) for d in dims if d not in spec.dimensions)
        yield from (
            f"{kind} '{name}' names dimension '{d}' twice. Delete one."
            for d, count in Counter(dims).items()
            if count > 1
        )


def _relation_targets(spec: Spec) -> Iterator[str]:
    """A relation has at least two columns over declared dimensions, each named once, and a key naming some of them."""
    for lname, lk in spec.relations.items():
        if len(lk.pairs) < 2:
            yield (
                f"Relation '{lname}' has {len(lk.pairs)} column(s), and needs at least two under 'key:' and "
                f"'values:'. For a label on one dimension, declare a parameter instead."
            )
        if not lk.key_roles:
            yield f"Relation '{lname}' names no key column. Name the columns that identify a row under 'key:'."
        for side, written in (('key', lk.key), ('values', lk.values)):
            yield from (
                f"Relation '{lname}' names dimension '{d}' twice under '{side}:'. Give the two columns roles: "
                f'{side}: {{{d}0: {d}, {d}1: {d}}}.'
                for d, count in Counter(dim for _, dim in side_columns(written)).items()
                if count > 1 and not isinstance(written, dict)
            )
        yield from (
            f"Relation '{lname}' names column '{role}' under both 'key:' and 'values:'. Rename the value column: "
            f'values: {{<name>: {dict(lk.pairs)[role]}}}.'
            for role in dict.fromkeys(lk.key_roles)
            if role in lk.value_roles
        )
        yield from (
            undeclared_dimension('Relation', lname, d) for d in dict.fromkeys(lk.dims) if d not in spec.dimensions
        )
        yield from (
            f"Relation '{lname}' names column '{role}' after dimension '{role}', but the column is over "
            f"'{dim}'. Rename the column after what it holds."
            for role, dim in lk.pairs
            if role in spec.dimensions and role != dim
        )
        if lk.value_roles:
            yield from (
                f"Relation '{lname}' has two key columns over '{d}' "
                f'({[k for k in lk.key_roles if dict(lk.pairs)[k] == d]}). Key the table by one column over '
                f"each dimension, or move one of them to 'values:'."
                for d, count in Counter(dict(lk.pairs)[k] for k in lk.key_roles).items()
                if count > 1
            )


def _bound_names(spec: Spec) -> Iterator[str]:
    """A named bound is a numeric parameter, declared here or given."""
    parameters = {**spec.parameters, **spec.given.parameters}
    for vname, vdef in spec.variables.items():
        for side in ('lower', 'upper'):
            val = getattr(vdef.bounds, side)
            if not isinstance(val, str):
                continue
            if val in parameters:
                dtype = parameters[val].dtype
                if dtype not in NUMERIC_DTYPES:
                    yield (
                        f"Variable '{vname}' bounds.{side}: '{val}' is a {dtype} parameter. Declare it "
                        f'dtype: float or int, or bound the variable by a numeric parameter.'
                    )
                continue
            detail = (
                f"'{val}' is not a declared parameter. Declare it under 'parameters:', or write a number"
                if val.isidentifier()
                else f'bounds take a parameter name or a number, not an expression (got {val!r}). '
                f'Precompute it as a parameter'
            )
            yield f"Variable '{vname}' bounds.{side}: {detail}."


def _sos_shapes(spec: Spec) -> Iterator[str]:
    """A set runs along one dim of one declared variable, and a variable carries one set."""
    claimed: dict[str, str] = {}
    for sname, entry in spec.sos.items():
        context = f"Sos '{sname}'"
        if entry.along not in spec.dimensions:
            yield (undeclared_dimension('Sos', sname, entry.along))
        elif entry.variable not in spec.variables:
            yield (
                f"{context}: '{entry.variable}' is not a declared variable.\n"
                f'  Variables: {sorted(spec.variables)}\n'
                "Name a variable declared under 'variables:'."
            )
        elif entry.along not in spec.variables[entry.variable].dims:
            yield (
                f"{context}: along '{entry.along}' is not a dim of variable "
                f"'{entry.variable}' (dims {spec.variables[entry.variable].dims}). Set 'along:' "
                f'to one of these dims.'
            )
        elif entry.type == 2 and not spec.dimensions[entry.along].ordered:
            yield unordered(context, f'type: 2 along {entry.along}', entry.along)
        elif entry.variable in claimed:
            yield (
                f"{context}: variable '{entry.variable}' already carries the set declared by "
                f"'{claimed[entry.variable]}'. Declare a second variable, "
                f'or write the other restriction as a constraint.'
            )
        else:
            claimed[entry.variable] = sname


def _sos_bounds(spec: Spec) -> Iterator[str]:
    """A set states what the binaries it expands to state: each side of a member carries a coefficient.

    The rewrite holds an unpicked member at zero from both sides, so a side
    the spec leaves open leaves the member free of it. Either coefficient
    may be a parameter, because a row multiplies by it rather than reading
    it. Decided here rather than where the rewrite runs, so a set the
    language cannot state twice is refused before any data exists.
    """
    for sname, entry in spec.sos.items():
        if (member := spec.variables.get(entry.variable)) is None:
            continue
        context = f"Sos '{sname}'"
        below, above = coefficients(member.domain, member.bounds.lower, member.bounds.upper)
        if below is None:
            yield (
                f"{context}: variable '{entry.variable}' has no lower bound, and the set expands to rows "
                f'that hold an unpicked member at zero from below as well as above. Declare bounds.lower, '
                f'as a number or a parameter.'
            )
        if above is None:
            yield (
                f"{context}: variable '{entry.variable}' has no upper bound, and the set expands to rows "
                f'that hold an unpicked member at zero from above as well as below. Declare bounds.upper, '
                f'as a number or a parameter.'
            )


def _piecewise_references(spec: Spec) -> Iterator[str]:
    """A curve runs along a declared dimension through numeric values parameters carrying it, gated by a binary, masked by a bool."""
    for name, pw in spec.piecewise.items():
        context = f"piecewise '{name}'"
        if pw.over not in spec.dimensions:
            yield undeclared_dimension('piecewise', name, pw.over)
            continue
        if not spec.dimensions[pw.over].ordered:
            yield unordered(context, f'over: {pw.over}', pw.over)
        for i, link in enumerate(pw.links):
            if link.values not in spec.parameters:
                yield f"{context}: link {i} values references undeclared parameter '{link.values}'. Declare it under 'parameters:'."
            elif (dtype := spec.parameters[link.values].dtype) not in NUMERIC_DTYPES:
                yield (
                    f"{context}: link {i} values parameter '{link.values}' is declared dtype: {dtype}, and a "
                    f'breakpoint is a number. Declare it dtype: float or int.'
                )
            elif pw.over not in spec.parameters[link.values].dims:
                yield (
                    f"{context}: link {i} values parameter '{link.values}' has dims "
                    f"{spec.parameters[link.values].dims}, without '{pw.over}'. Add '{pw.over}' to its dims."
                )
        if (activity := pw.activity) is not None:
            if activity not in spec.variables:
                yield (
                    f"{context}: activity '{activity}' is not a declared variable. Declare it as a binary "
                    f'variable, or delete activity:.'
                )
            elif spec.variables[activity].domain != 'binary':
                yield (
                    f"{context}: activity variable '{activity}' is {spec.variables[activity].domain}. "
                    f'Declare it domain: binary.'
                )
        if (points := pw.points) is None or pw.nominated is not None:
            continue
        if points not in spec.parameters:
            yield f"{context}: points references undeclared parameter '{points}'. Declare it under 'parameters:'."
        elif (dtype := spec.parameters[points].dtype) != 'bool':
            yield f"{context}: points parameter '{points}' is {dtype}. Declare it dtype: bool."
        elif pw.over not in spec.parameters[points].dims:
            yield (
                f"{context}: points parameter '{points}' has dims {spec.parameters[points].dims}, "
                f"without '{pw.over}'. Add '{pw.over}' to its dims."
            )


def _collisions(spec: Spec, context: str, by_kind: Iterable[tuple[str, Iterable[str]]]) -> Iterator[str]:
    """The refusal for each name *context*'s expansion writes that the file already declares, by kind.

    An emitted variable joins the flat namespace, so any entry there
    takes its name; a constraint, a set and an assumption each have their own.
    """
    sections = {'named expression': 'expressions', 'sos': 'sos', 'given variable': 'given: variables'}
    declared: dict[str, dict[str, str]] = {
        'variable': {name: kind for kind, group in _flat_namespace(spec) for name in group},
        'constraint': dict.fromkeys(spec.constraints, 'constraint'),
        'sos': dict.fromkeys(spec.sos, 'sos'),
        'assumption': dict.fromkeys(spec.assumptions, 'assumption'),
    }
    for kind, names in by_kind:
        yield from (
            f"{context}: its expansion writes {kind} '{one}', which this file already declares under "
            f"'{sections.get(declared[kind][one], declared[kind][one] + 's')}:'. Rename one of them."
            for one in names
            if one in declared[kind]
        )
