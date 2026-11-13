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
typed expression stay with the expressions in [`lower`][mathspec._lowering.lower]:
a macro formal against a dimension, a curve's links, and every dim rule.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from typing import TYPE_CHECKING

from mathspec._expression_parser import NAME
from mathspec._operators import BUILTIN_NAMES
from mathspec._piecewise import Emitted as EmittedCurve
from mathspec._piecewise import gate_of
from mathspec._sos import Emitted as EmittedSet
from mathspec._sos import coefficients
from mathspec._yaml import read_spec
from mathspec.errors import SchemaError, did_you_mean, unordered
from mathspec.spec import NUMERIC_DTYPES, Spec

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from pathlib import Path

    from mathspec.program import Program
    from mathspec.spec import PiecewiseLinkSpec, PiecewiseSpec


def to_spec(spec: str | Path | Mapping[str, object] | Spec) -> Spec:
    """Load and validate a spec definition — the language's front door.

    Everything decidable without data is decided here: schema shape, every
    rule one entry is held to against the others, every expression and
    condition, and every macro template.

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
    """Every name a set or curve of *program* would write out that *spec* declares, or another one writes too.

    Read off the program rather than the file, since what a curve writes is
    decided by the curve as lowered — its links, its method, its mask.
    """
    emitters = [
        *((f"Sos '{name}'", EmittedSet.of(name, entry.sos_type).by_kind) for name, entry in program.sos.items()),
        *((f"piecewise '{name}'", EmittedCurve.of(name, curve).by_kind) for name, curve in program.piecewise.items()),
    ]
    errors = [
        f"piecewise '{name}': link '{row.removeprefix(f'{name}_')}' has the row '{row}', which the "
        f'expansion of the entry already writes. Rename the link.'
        for name, curve in program.piecewise.items()
        for row in EmittedCurve.of(name, curve).reused
    ]
    for context, by_kind in emitters:
        errors.extend(_collisions(spec, context, by_kind))
    errors.extend(_shared(emitters))
    return errors


def _shared(emitters: Iterable[tuple[str, Iterable[tuple[str, Iterable[str]]]]]) -> Iterator[str]:
    """The refusal for each name two expansions both write, since the second would overwrite the first."""
    first: dict[tuple[str, str], str] = {}
    for context, by_kind in emitters:
        for kind, names in by_kind:
            for one in names:
                if (owner := first.setdefault((kind, one), context)) != context:
                    yield (
                        f"{context}: its expansion writes {kind} '{one}', which {owner} also writes. Rename one of "
                        f'the entries, or the link whose row it is.'
                    )


def reference_errors(spec: Spec) -> list[str]:
    """Every cross-entry rule *spec* breaks, collected rather than raised on the first."""
    return [
        *_name_collisions(spec),
        *_frame_dimensions(spec),
        *_relation_targets(spec),
        *_map_targets(spec),
        *_index_sets(spec),
        *_fill_names(spec),
        *_bound_names(spec),
        *_sos_shapes(spec),
        *_sos_bounds(spec),
        *_piecewise_references(spec),
        *_given_constraint_collisions(spec),
    ]


def undeclared_dimension(kind: str, name: str, dimension: str, spec: Spec, *, along: bool = False) -> str:
    """The one wording for an entry naming a dimension the file does not declare, or naming a relation as one."""
    if (relation := spec.relations.get(dimension)) is None:
        return f"{kind} '{name}' references undeclared dimension '{dimension}'. Declare it under 'dimensions:'."
    dims = sorted({d for _, d in relation.pairs})
    if along:
        rewrite = f'Name one of its dimensions, {dims}.'
    elif kind in ('Parameter', 'Variable'):
        rewrite = f'Name its dimensions, {dims}, under dims:, and confine the entry with in: [{dimension}].'
    else:
        rewrite = f'Name its dimensions, {dims}.'
    return f"{kind} '{name}' names the relation '{dimension}', and a relation is not a dimension. {rewrite}"


def _flat_namespace(spec: Spec) -> list[tuple[str, Iterable[str]]]:
    """Each kind of entry whose names share the one namespace an expression reads."""
    return [
        ('dimension', spec.dimensions),
        ('relation', spec.relations),
        ('parameter', spec.parameters),
        ('given parameter', spec.given.parameters),
        ('variable', spec.variables),
        ('given variable', spec.given.variables),
        ('named expression', spec.expressions),
        ('given expression', spec.given.expressions),
        ('condition', spec.conditions),
        ('given condition', spec.given.conditions),
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
        *(('Given condition', name, g.dims) for name, g in spec.given.conditions.items()),
        *(('Constraint', name, c.dims) for name, c in spec.constraints.items()),
        *(('Named expression', name, e.dims or ()) for name, e in spec.expressions.items()),
    ]
    for kind, name, dims in frames:
        yield from (undeclared_dimension(kind, name, d, spec) for d in dims if d not in spec.dimensions)
        yield from (
            f"{kind} '{name}' names dimension '{d}' twice. Delete one."
            for d, count in Counter(dims).items()
            if count > 1
        )


def _relation_targets(spec: Spec) -> Iterator[str]:
    """A relation has at least two columns, over declared dimensions, each named once."""
    for lname, lk in spec.relations.items():
        if len(lk.pairs) < 2:
            dim = lk.pairs[0][1] if lk.pairs else '<dimension>'
            yield (
                f"Relation '{lname}' has {'one column' if lk.pairs else 'no column'} under 'dims:', and a relation "
                f'needs at least two. To give each {dim} a label, declare a map under maps: {dim}:. To mark some '
                f'of them, declare a bool parameter or a condition.'
            )
        if not isinstance(lk.dims, Mapping):
            yield from (
                f"Relation '{lname}' names dimension '{d}' twice under 'dims:'. Give the two columns names: "
                f'dims: {{{d}0: {d}, {d}1: {d}}}.'
                for d, count in Counter(lk.dims if isinstance(lk.dims, tuple) else (lk.dims,)).items()
                if count > 1
            )
        yield from (
            undeclared_dimension('Relation', lname, d, spec)
            for d in dict.fromkeys(d for _, d in lk.pairs)
            if d not in spec.dimensions
        )
        yield from (
            f"Relation '{lname}' names column '{role}' after dimension '{role}', but the column is over "
            f"'{dim}'. Rename the column after what it holds."
            for role, dim in lk.pairs
            if role in spec.dimensions and role != dim
        )


def _map_targets(spec: Spec) -> Iterator[str]:
    """A map's subject is a dimension or a relation, its name is no column of the subject, and it refers to a dimension.

    A relation with two columns over one dimension takes no map, since a call
    through it would not know which of the two the frame's dimension meets.
    """
    for subject, maps in spec.maps.items():
        head = f"maps: '{subject}'"
        if subject in spec.relations:
            pairs = spec.relations[subject].pairs
            if twice := [d for d, count in Counter(d for _, d in pairs).items() if count > 1]:
                yield (
                    f"{head} is a relation with two columns over '{twice[0]}', and a map reads one row per "
                    f'combination of its dimensions. Declare the maps on a relation over each dimension once.'
                )
        elif subject in spec.dimensions:
            pairs = ((subject, subject),)
        else:
            subjects = [*spec.dimensions, *spec.relations]
            yield (
                f'{head} is neither a dimension nor a relation, and a map gives each row of one a label. '
                f'{did_you_mean(subject, subjects, label="Subjects")}'
            )
            continue
        for role, m in maps.items():
            if not re.fullmatch(NAME, role):
                yield (
                    f'{head}: {role!r} is not a name. Start it with a letter or an underscore, then use only '
                    f'letters, digits or underscores.'
                )
            if role in dict(pairs):
                yield (
                    f"{head}: map '{role}' has the name of a column of '{subject}', which holds the row, not a "
                    f'label of it. Rename the map after what it holds.'
                )
            if m.refers_to in spec.relations:
                yield (
                    f"{head}: map '{role}' refers to the relation '{m.refers_to}', and a map gives a label of one "
                    f"dimension. Refer to one of its dimensions, or declare '{role}' on the relation instead."
                )
            elif m.refers_to not in spec.dimensions:
                yield (
                    f"{head}: map '{role}' refers to undeclared dimension '{m.refers_to}'. Declare it under 'dimensions:'."
                )
            elif role in spec.dimensions and role != m.refers_to:
                yield (
                    f"{head}: map '{role}' is named after dimension '{role}', but refers to '{m.refers_to}'. Rename the "
                    f'map after what it holds.'
                )


def _index_sets(spec: Spec) -> Iterator[str]:
    """Each entry of an ``in:`` is a relation over dimensions of the entry, leaves a combination out, and is named once."""
    entries = [
        *((f"Parameter '{name}'", name, p.dims, p.in_) for name, p in spec.parameters.items()),
        *((f"Variable '{name}'", name, v.dims, v.in_) for name, v in spec.variables.items()),
    ]
    for context, name, dims, in_ in entries:
        head = f'{context}: in: names'
        yield from (f"{head} '{r}' twice. Delete one." for r, count in Counter(in_).items() if count > 1)
        for rname in dict.fromkeys(in_):
            if (lk := spec.relations.get(rname)) is None:
                yield _not_a_relation(head, rname, spec, dims)
                continue
            if lk.missing == 'refused':
                yield (
                    f"{head} '{rname}', which under missing: refused has a row at every combination, so it "
                    f"leaves nothing out. Write missing: absent on '{rname}', or delete it from in:."
                )
            over = Counter(d for _, d in lk.pairs)
            if twice := [d for d, count in over.items() if count > 1]:
                yield (
                    f"{head} '{rname}', which has two columns over '{twice[0]}', and '{name}' has "
                    f"'{twice[0]}' once. Name a relation over each dimension once."
                )
            elif outside := [d for d in over if d not in dims]:
                yield (
                    f"{head} '{rname}', over {sorted(over)}, and '{name}' is not over {outside}. Add "
                    f"{outside} to its dims:, or delete '{rname}' from in:."
                )


def _not_a_relation(head: str, written: str, spec: Spec, dims: Sequence[str]) -> str:
    """The refusal for an ``in:`` entry that names no relation: a map, or a subject with maps, apart."""
    column = re.fullmatch(r'(\w+)\[(.+)\]', written)
    if column is not None and column[1] in spec.maps:
        return (
            f"{head} '{written}', a map of '{column[1]}', and an index set is a relation. To keep the rows the map "
            f'gives a label, write where: {written}.'
        )
    if written in spec.dimensions:
        rewrite = f"Delete '{written}' from in:, since dims: lists it." if written in dims else 'List it under dims:.'
        return f"{head} '{written}', which is a dimension, and an index set is a relation. {rewrite}"
    return f"{head} '{written}', which is not a relation. {did_you_mean(written, spec.relations, label='Relations')}"


def _fill_names(spec: Spec) -> Iterator[str]:
    """A ``missing:`` that is a name names an ``expressions:`` entry of this file, whose cases the loader can read."""
    for name, p in spec.parameters.items():
        if (fill := p.fill_from) is None or fill in spec.expressions:
            continue
        if fill in spec.given.expressions:
            yield (
                f"Parameter '{name}': missing: {fill} names an expression this file reads under given:, and the "
                f'loader reads the cases of the expression. Declare the parameter in the file that declares {fill!r}.'
            )
        else:
            yield (
                f"Parameter '{name}': missing: {fill} is neither refused, absent nor a value, and names no "
                f'expression. {did_you_mean(fill, spec.expressions, label="Expressions")}'
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
            yield undeclared_dimension('Sos', sname, entry.along, spec, along=True)
        elif entry.variable not in spec.variables:
            yield (
                f"{context}: '{entry.variable}' is not a declared variable.\n"
                f'  Variables: {sorted(spec.variables)}\n'
                "Name a variable declared under 'variables:'."
            )
        elif entry.along not in spec.variables[entry.variable].dims:
            yield (
                f"{context}: along '{entry.along}' is not a dim of variable "
                f"'{entry.variable}' (dims {list(spec.variables[entry.variable].dims)}). Set 'along:' "
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
    """Every entry a curve names by key exists and has the shape the curve needs.

    The breakpoint dim, the frame ``dims:`` states, each link's values
    parameter, and the gate. What a link's expression, its walk and the
    where carry is resolution's to say, and whether the pieces fit together
    is decided as the entry is lowered
    ([`declaration_of`][mathspec._piecewise.declaration_of]).
    """
    for name, pw in spec.piecewise.items():
        context = f"piecewise '{name}'"
        if pw.along not in spec.dimensions:
            yield undeclared_dimension('piecewise', name, pw.along, spec, along=True)
            continue
        if not spec.dimensions[pw.along].ordered:
            yield unordered(context, f'along: {pw.along}', pw.along)
        for d in pw.dims:
            if d not in spec.dimensions:
                yield undeclared_dimension('piecewise', name, d, spec)
            elif d == pw.along:
                yield (
                    f"{context}: dims: lists '{pw.along}', the breakpoint dimension. Every curve runs along it, so drop "
                    f'it from dims:.'
                )
        if len(set(pw.dims)) != len(pw.dims):
            yield f'{context}: dims repeats a dimension: {list(pw.dims)}. Write each dimension once.'
        for key, link in pw.links.items():
            yield from _piecewise_link_shape(spec, name, pw, key, link)
        if pw.activity is None:
            continue
        if (activity := gate_of(pw.activity)) is None:
            yield (
                f'{context}: activity: {pw.activity!r} is neither a variable nor a variable read through a map. '
                f'Write activity: <variable>, or activity: at(<variable>, by=<subject>[<map>]).'
            )
            continue
        if activity not in spec.variables:
            yield (
                f"{context}: activity '{activity}' is not a declared variable. Declare it as a binary "
                f'variable, or delete activity:.'
            )
        elif (domain := spec.variables[activity].domain) == 'continuous':
            yield f"{context}: activity variable '{activity}' is continuous. Declare it domain: binary."
        elif domain == 'integer' and pw.method != 'incremental':
            yield (
                f"{context}: activity variable '{activity}' is integer, and method: {pw.method} takes a binary "
                f"gate only. Write method: incremental, or declare '{activity}' domain: binary."
            )


def _piecewise_link_shape(spec: Spec, name: str, pw: PiecewiseSpec, key: str, link: PiecewiseLinkSpec) -> Iterator[str]:
    """One link's values parameter exists as the link needs it."""
    context = f"piecewise '{name}' link '{key}'"
    if link.values not in spec.parameters:
        yield f"{context}: values references undeclared parameter '{link.values}'. Declare it under 'parameters:'."
    elif (dtype := spec.parameters[link.values].dtype) not in NUMERIC_DTYPES:
        yield (
            f"{context}: values parameter '{link.values}' is declared dtype: {dtype}, and a breakpoint is a "
            f'number. Declare it dtype: float or int.'
        )
    elif pw.along not in spec.parameters[link.values].dims:
        yield (
            f"{context}: values parameter '{link.values}' is over {list(spec.parameters[link.values].dims)}, without "
            f"'{pw.along}'. Add '{pw.along}' to its dims:."
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
