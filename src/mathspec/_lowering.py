# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Lower a spec to a [`Program`][] — the pass that decides every expression.

One lowering, on the language side, run when a [`Spec`][]
loads: it reads every expression and condition into the program's own
nodes, checks every rule decidable without data, and packages the
entries, section for section. The program mirrors the spec it was
lowered from: a ``piecewise:`` entry the spec still declares is a curve on
the program, and [`expand`][mathspec.spec.Spec.expand] is what writes it out
as rows.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, cast

from mathspec._dimensions import check_spec
from mathspec._divisors import zero_divisor_refusals
from mathspec._expansion import expand, parse_template
from mathspec._piecewise import (
    assumptions_of,
    declaration_of,
    lp_domain_refusal,
    refused_under_where,
    resolve_gate,
    resolve_links,
    resolve_walks,
)
from mathspec._resolution import (
    Namespace,
    mask_of,
    resolve_condition_text,
    resolve_constraint_text,
    resolve_expression,
    resolve_expression_text,
    self_existence,
)
from mathspec._validation import emitted_name_errors, reference_errors
from mathspec.errors import SchemaError, did_you_mean, prefixed
from mathspec.program import (
    And,
    Assumption,
    BooleanLiteral,
    Constant,
    Constraint,
    Dimension,
    ExpressionReference,
    Given,
    GivenParameter,
    GivenTargets,
    Mask,
    MissingFrom,
    NamedCondition,
    NamedExpression,
    Objective,
    Parameter,
    ParameterReference,
    Program,
    RelationDefined,
    Sos,
    Variable,
    VariableDefined,
    fill_values,
    variables_of,
    walk,
    walk_regions,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from mathspec.program import Condition, Expression, Gate, JoinColumns, ParameterMissing
    from mathspec.spec import AssumptionSpec, ParameterSpec, Spec


def lower(spec: Spec) -> Program:
    """Lower *spec*'s own entries, checking every rule decidable without data.

    What is checked:

    - every rule one entry is held to against the others
      ([`reference_errors`][]), before any expression
      is read, since resolution assumes each of them;
    - the expression parses, and constraints hold exactly one comparison where
      objectives hold none;
    - every referenced name resolves, and every operator is a built-in whose
      dimension arguments name declared dimensions;
    - conditions parse *and* resolve — an unknown name there is an error,
      not a silently-empty mask;
    - macro formals may shadow the spec's names but not a declared dimension, since
      ``over=snapshot`` under a formal ``snapshot`` cannot say which it means;
    - no name a set or curve writes out is one the file declares
      ([`emitted_name_errors`][]), read off the
      curve as lowered;
    - every dim rule (``dimensions.check_spec``), once names resolve.

    A ``piecewise:`` entry's links and ``where:`` are resolved here, and each
    link's row and its fit decided, on the link the file wrote, so the
    expansion writes rows the language has already held to every rule; what its method assumes of the breakpoints
    stands under the program's assumptions with the file's own, so a spec
    states what it assumes whether or not its curves are written out.

    Returns:
        The program of what *spec* declares, section for section.

    Raises:
        SchemaError: Listing every problem found, one per line. A name a set
            or curve writes that the file declares is listed once every other
            problem is gone, since it is read off the curve as lowered.
        DimensionError: Listing every dim rule an operator breaks, where
            nothing else is wrong; else the first rule an entry breaks, once
            every name resolves.
    """
    errors = reference_errors(spec)
    if errors:
        raise SchemaError('\n'.join(errors))

    ns = Namespace(spec)
    for mname, macro in spec.macros.items():
        context = f"Macro '{mname}'"
        formals = frozenset((*macro.args, *macro.kwargs))
        try:
            body_ast = expand(parse_template(mname, macro, context), ns, context)
        except ValueError as e:
            errors.append(prefixed(context, e))
            continue
        errors.extend(
            f"{context}: formal '{f}' collides with declared dimension '{f}'. Rename the formal."
            for f in sorted(formals & ns.dimensions)
        )
        resolve_expression(body_ast, ns, context, errors, formals=formals)

    entries: dict[str, ExpressionReference] = {}
    for ename in spec.expressions:
        node, refusals = ns.named_entry(ename)
        errors.extend(refusals)
        if node is not None:
            entries[ename] = node

    terms = _terms(entries, spec, ns, errors)

    conditions: dict[str, NamedCondition] = {}
    for mname, mdef in spec.conditions.items():
        named, refusals = ns.condition_entry(mname)
        errors.extend(refusals)
        if named is not None:
            body = Mask(named.body)
            conditions[mname] = NamedCondition(body, body.dims, mdef.description)

    parameter_masks = _parameter_masks(spec, ns, errors)

    variables = {}
    for vname, vdef in spec.variables.items():
        context = f"Variable '{vname}'"
        where = resolve_condition_text(vdef.where, ns, context, errors, self_variable=vname)
        if where is not None and (refusal := self_existence(where, vname, context)) is not None:
            errors.append(refusal)
        if vdef.domain == 'binary':
            lower_bound, upper_bound = Constant(0.0, dims=()), Constant(1.0, dims=())
        else:
            lower_bound, upper_bound = _bound(vdef.bounds.lower, ns), _bound(vdef.bounds.upper, ns)
        variables[vname] = Variable(
            vdef.dims,
            where=_index_mask(vname, vdef.in_, vdef.where, where, ns, context, errors),
            lower=lower_bound,
            upper=upper_bound,
            domain=vdef.domain,
            missing=vdef.missing,
            description=vdef.description,
            in_=vdef.in_,
        )

    constraints: dict[str, Constraint] = {}
    for cname, cdef in spec.constraints.items():
        context = f"Constraint '{cname}'"
        where = resolve_condition_text(cdef.where, ns, context, errors)
        if (sides := resolve_constraint_text(cdef.expression, ns, context, errors)) is not None:
            lhs, sense, rhs = sides
            constraints[cname] = Constraint(cdef.dims, lhs, sense, rhs, mask_of(where), description=cdef.description)

    objective = None
    if spec.objective is not None:
        expression = resolve_expression_text(spec.objective.expression, ns, 'The objective', errors, ceiling=2)
        if expression is not None:
            objective = Objective(spec.objective.sense, expression, spec.objective.description)

    assumptions: dict[str, Assumption] = {}
    for aname, adef in spec.assumptions.items():
        if (assumption := _assumption(aname, adef, ns, errors)) is not None:
            assumptions[aname] = assumption

    curves: dict[str, tuple[tuple[Expression, ...], dict[str, JoinColumns], Mask | None, Gate | None]] = {}
    for pname, pdef in spec.piecewise.items():
        links = resolve_links(pname, pdef, ns, errors)
        walks = resolve_walks(pname, pdef, ns, errors)
        where = mask_of(resolve_condition_text(pdef.where, ns, f"piecewise '{pname}' where", errors))
        gate = None
        if pdef.activity is not None:
            gate = resolve_gate(pname, pdef, variables, ns, errors)
            if gate is None:
                continue
        if links is None or walks is None:
            continue
        if pdef.method == 'lp' and (refusal := lp_domain_refusal(pname, pdef, links)) is not None:
            errors.append(refusal)
        curves[pname] = (links, walks, where, gate)

    linked = {pname: links for pname, (links, *_) in curves.items()}
    errors.extend(_zero_divisor_refusals(spec, variables, entries, constraints, objective, linked))
    if errors:
        raise ns.error(errors)

    roots = [side for c in constraints.values() for side in (c.lhs, c.rhs)]
    if objective is not None:
        roots.append(objective.expression)
    roots.extend(link for links in linked.values() for link in links)
    roots.extend(terms)
    in_math = frozenset(node.name for node in walk(*roots) if isinstance(node, ExpressionReference))

    piecewise = {}
    for pname, (links, walks, where, gate) in curves.items():
        piecewise[pname] = declaration_of(pname, spec.piecewise[pname], links, walks, where, gate, spec)
        for aname, assumed in assumptions_of(pname, piecewise[pname], spec.piecewise[pname].where).items():
            assumption = _assumption(aname, assumed, ns, errors)
            assert assumption is not None and not errors, 'what a method assumes is stated in the language'
            assumptions[aname] = assumption

    program = Program(
        parameters={
            name: Parameter(
                pdef.dims,
                pdef.dtype,
                _missing(pdef),
                pdef.description,
                parameter_masks.get(name),
                pdef.in_,
            )
            for name, pdef in spec.parameters.items()
        },
        variables=variables,
        constraints=constraints,
        objective=objective,
        dimensions={
            name: Dimension(dtype=ddef.dtype, one_of=ddef.one_of, ordered=ddef.ordered, description=ddef.description)
            for name, ddef in spec.dimensions.items()
        },
        relations=ns.relations,
        sos={
            name: Sos(sdef.variable, sdef.along, sos_type=sdef.type, description=sdef.description)
            for name, sdef in spec.sos.items()
        },
        piecewise=piecewise,
        assumptions=assumptions,
        expressions={
            name: NamedExpression(
                entry.body,
                entry.dims,
                in_math=name in in_math,
                description=spec.expressions[name].description,
                adds_to=spec.expressions[name].adds_to,
            )
            for name, entry in entries.items()
        },
        conditions=conditions,
        given=GivenTargets(
            parameters={
                name: GivenParameter(g.dims, g.dtype, g.description) for name, g in spec.given.parameters.items()
            },
            variables={name: Given(g.dims, g.description) for name, g in spec.given.variables.items()},
            constraints={name: Given(g.dims, g.description) for name, g in spec.given.constraints.items()},
            expressions={name: Given(g.dims, g.description) for name, g in spec.given.expressions.items()},
            conditions={name: Given(g.dims, g.description) for name, g in spec.given.conditions.items()},
        ),
        description=spec.description,
    )
    if errors := [*emitted_name_errors(spec, program), *refused_under_where(program, spec), *_fills(program)]:
        raise SchemaError('\n'.join(errors))
    check_spec(spec, program)
    return program


def _terms(entries: Iterable[str], spec: Spec, ns: Namespace, errors: list[str]) -> list[ExpressionReference]:
    """Every entry with ``adds_to:`` that loads as a term, with a refusal in *errors* for each other.

    A term that reads its own sum, directly or through the sums the file's
    other terms add to, defines that sum by itself whatever the other files
    add, so the one file decides it.
    """
    resolved = {
        name: (target, entry)
        for name in entries
        if (target := spec.expressions[name].adds_to) is not None
        and (entry := _term(name, target, spec, ns, errors)) is not None
    }
    sums: dict[str, list[ExpressionReference]] = {}
    for target, entry in resolved.values():
        sums.setdefault(target, []).append(entry)
    terms = []
    for name, (target, entry) in resolved.items():
        through = _loop(target, entry, sums)
        if through is None:
            terms.append(entry)
            continue
        via = f', through {" -> ".join(repr(sum_) for sum_ in through)}' if through else ''
        errors.append(
            f"Named expression '{name}': it reads {target!r}, the sum it adds to{via}, so the sum would define "
            f'itself. Write the term from names this file declares, and not from {target!r}.'
        )
    return terms


def _term(name: str, target: str, spec: Spec, ns: Namespace, errors: list[str]) -> ExpressionReference | None:
    """Named expression *name* as the term it writes into a given expression of its file, or ``None``.

    The given entry is what makes a misspelt target a refusal in the file that
    wrote it: a term lands only on a name its own file reads. The term is
    resolved as a use of its name, so it is held to the degree the math that
    reads the sum admits.
    """
    context = f"Named expression '{name}'"
    if target in spec.expressions:
        errors.append(
            f'{context}: it adds to {target!r}, which this file defines. Write the term into the body of '
            f"{target!r}, or read {target!r} under 'given: expressions:' and add its body as a term."
        )
        return None
    if target not in spec.given.expressions:
        errors.append(
            f"{context}: it adds to {target!r}, which this file does not read under 'given: expressions:'. "
            f'Declare {target!r} there with its dimensions, or fix the spelling. '
            f'{did_you_mean(target, spec.given.expressions)}'
        )
        return None
    entry = resolve_expression_text(name, ns, context, errors, ceiling=2)
    if entry is None:
        return None
    assert isinstance(entry, ExpressionReference), 'a term is a name, and a name resolves to the entry it names'
    return entry


def _loop(target: str, entry: ExpressionReference, sums: Mapping[str, list[ExpressionReference]]) -> list[str] | None:
    """The sums *entry* reads *target* through, by the terms in *sums*, or ``None`` where it does not read it.

    ``[]`` is a term that reads its own sum.
    """
    seen = {target}
    stack: list[tuple[list[str], frozenset[str]]] = [([], variables_of(entry))]
    while stack:
        path, reads = stack.pop()
        for read in sorted(reads):
            if read == target:
                return path
            if read in sums and read not in seen:
                seen.add(read)
                stack.append(([*path, read], variables_of(*sums[read])))
    return None


def _zero_divisor_refusals(
    spec: Spec,
    variables: Mapping[str, Variable],
    entries: Mapping[str, ExpressionReference],
    constraints: Mapping[str, Constraint],
    objective: Objective | None,
    curves: Mapping[str, tuple[Expression, ...]],
) -> list[str]:
    """[`zero_divisor_refusals`][mathspec._divisors.zero_divisor_refusals] over every expression the file declares.

    Read once every variable mask is resolved, because a masked factor spares
    a divisor wherever its mask leaves a missing row out. Only a variable that
    is absent outside its mask spares one: a ``missing:`` number stands for it
    there, and the quotient is read.
    """
    masks = {name: v.where for name, v in variables.items() if v.missing == 'absent'}
    parameters = _zero_filled(spec, entries)
    found: list[str] = []
    for name, entry in entries.items():
        found += zero_divisor_refusals(entry.body, f"Named expression '{name}'", parameters, masks)
    for name, c in constraints.items():
        for side in (c.lhs, c.rhs):
            found += zero_divisor_refusals(side, f"Constraint '{name}'", parameters, masks, c.where)
    if objective is not None:
        found += zero_divisor_refusals(objective.expression, 'The objective', parameters, masks)
    for name, links in curves.items():
        for link in links:
            found += zero_divisor_refusals(link, f"piecewise '{name}'", parameters, masks)
    return list(dict.fromkeys(found))


def _missing(pdef: ParameterSpec) -> ParameterMissing:
    """The program's ``missing``: the name of an expression sealed into a [`MissingFrom`][mathspec.program.MissingFrom]."""
    if pdef.fill_from is not None:
        return MissingFrom(pdef.fill_from)
    return cast('ParameterMissing', pdef.missing)


def _zero_filled(spec: Spec, entries: Mapping[str, ExpressionReference]) -> Mapping[str, ParameterSpec]:
    """The parameters of *spec*, where one whose ``missing:`` names an expression that states a 0 reads ``missing: 0``.

    The divisor check asks one question of a parameter: can a missing row be
    0? A 0 in any case of the expression answers it as ``missing: 0`` does.
    """
    zero = {
        name: p.model_copy(update={'missing': 0.0})
        for name, p in spec.parameters.items()
        if p.fill_from in entries and 0 in (fill_values(entries[p.fill_from].body) or ())
    }
    return {**spec.parameters, **zero}


def _fills(program: Program) -> Iterator[str]:
    """A ``missing:`` that names an expression names cases of plain numbers over dimensions of the parameter.

    A tool fills a missing row before it reads any value, so the expression
    reads no parameter and no variable: each value is a number the file
    states, and each ``when:`` tests dimensions, relations and maps.
    """
    for name, p in program.parameters.items():
        if not isinstance(p.missing, MissingFrom):
            continue
        entry = program.expressions[p.missing.expression]
        context = f"Parameter '{name}': missing: {p.missing.expression}"
        if stray := sorted(set(entry.dims) - set(p.dims)):
            yield (
                f'{context} is over {stray}, and the parameter is not (dims {list(p.dims)}). Give the expression '
                f'dims: the parameter has.'
            )
        values = fill_values(entry.expression)
        if values is None:
            yield (
                f'{context} is not cases of plain numbers. A missing row takes a number the file states: write each '
                f'`expression:` and the `otherwise:` as a number, or write the number itself as missing:.'
            )
            continue
        if p.dtype == 'int' and (fractions := [v for v in values if not v.is_integer()]):
            yield (
                f'{context} states {fractions}, and an int parameter takes whole numbers. Write whole numbers, or '
                f'declare dtype: float.'
            )
        tested: set[str] = set().union(
            *(mask.names_read for _, masks in walk_regions(entry.expression) for mask in masks)
        )
        if read := sorted(tested & program.parameters.keys()):
            yield (
                f'{context} reads {read} in a `when:`, and a missing row is filled before any value is read. Test a '
                f'dimension, a relation or a map.'
            )


def _bound(value: float | str | None, ns: Namespace) -> Constant | ParameterReference | None:
    if value is None:
        return None
    if isinstance(value, str):
        return ParameterReference(value, dims=ns.leaf_dims[value])
    return Constant(value, dims=())


def _parameter_masks(spec: Spec, ns: Namespace, errors: list[str]) -> dict[str, Mask | None]:
    """Each parameter's ``in:`` and ``where:`` as one mask, a refusal appended for each ``where:`` that reads what it may not.

    A tool evaluates a parameter's mask from the data alone, before any
    variable has a value and before any mask has been applied. So a mask reads
    dimensions, relations and parameters with neither ``in:`` nor ``where:``,
    and no masks can wait on one another.
    """
    masked = {name for name, pdef in spec.parameters.items() if pdef.where is not None or pdef.in_}
    masks: dict[str, Mask | None] = {}
    for pname in sorted(masked):
        pdef, context = spec.parameters[pname], f"Parameter '{pname}'"
        where = resolve_condition_text(pdef.where, ns, context, errors)
        masks[pname] = _index_mask(pname, pdef.in_, pdef.where, where, ns, context, errors)
        if (mask := mask_of(where)) is None:
            continue
        errors.extend(
            f"{context}: its `where:` contains variable '{v}', and a tool evaluates the `where:` of a parameter "
            f'from the data alone, before any variable has a value. Test a parameter or a map instead.'
            for v in sorted(mask.names_read & {*spec.variables, *spec.given.variables})
        )
        errors.extend(_masked_read(context, pname, read, spec) for read in sorted(mask.names_read & masked))
    return masks


def _masked_read(context: str, pname: str, read: str, spec: Spec) -> str:
    """The refusal for a parameter's ``where:`` that reads *read*, a parameter whose own mask decides its rows."""
    if read == pname:
        return (
            f"{context}: its `where:` contains '{pname}' itself, and a tool evaluates that `where:` before it "
            f"reads '{pname}'. Test a relation or another parameter."
        )
    if spec.parameters[read].where is None:
        return (
            f"{context}: its `where:` contains '{read}', which has an `in:` of its own. Test a relation that the "
            f"`in:` of '{read}' names instead."
        )
    return (
        f"{context}: its `where:` contains '{read}', which has a `where:` of its own. Test the condition in the "
        f"`where:` of '{read}', or a relation."
    )


def _index_mask(
    name: str,
    in_: tuple[str, ...],
    text: str | None,
    where: Condition | None,
    ns: Namespace,
    context: str,
    errors: list[str],
) -> Mask | None:
    """The key of each relation in *in_* and the resolved *where* as one mask, or ``None`` where neither limits anything.

    A refusal is appended where the relations already decide some of the
    ``where:``: inside them each bare relation name is true, so reading one
    there says nothing. A map read as ``subject[map]`` is a test,
    and stays.
    """
    if where is not None and in_ and (written := Mask(where)).within(in_) != written:
        errors.append(_decided_by_index_set(context, name, text, in_, written.within(in_).root))
    elif where is not None and (problem := _rows_tested(context, text, Mask(where), in_, ns)) is not None:
        errors.append(problem)
    rows: list[Condition] = [
        RelationDefined(r, tuple(sorted(ns.relations[r].dim(k) for k in ns.relations[r].key))) for r in in_
    ]
    conjuncts = [*rows, *(() if where is None else (where,))]
    return mask_of(functools.reduce(And, conjuncts)) if conjuncts else None


def _rows_tested(context: str, text: str | None, written: Mask, in_: tuple[str, ...], ns: Namespace) -> str | None:
    """The refusal for a ``where:`` that tests the rows of a relation, which ``in:`` states, or ``None``.

    ``in:`` and a bare relation name in ``where:`` would say one thing twice, so
    only ``in:`` is taken. A map read as ``subject[map]`` is a test of a label,
    and stays.
    """
    tested = sorted({a.name for a in written.atoms if isinstance(a, RelationDefined) and a.column is None})
    if not tested:
        return None
    named = ' and '.join(f"'{r}'" for r in tested)
    head = f'{context}: `where: {text}` tests the rows of {named}'
    if everywhere := [r for r in tested if ns.relations[r].missing == 'refused']:
        return (
            f"{head}, and under missing: refused '{everywhere[0]}' has a row everywhere. Delete it from the `where:`."
        )
    top = {c.name for c in written.conjuncts if isinstance(c, RelationDefined) and c.column is None}
    if not set(tested) <= top:
        return f'{head} under OR or NOT, which `in:` cannot state. Declare those rows as a bool parameter, and test that in its place.'
    rest = ', and keep the rest in the `where:`.' if len(written.conjuncts) > len(top) else ' in place of the `where:`.'
    return f'{head}, which `in:` states. Write `in: [{", ".join(sorted({*in_, *tested}))}]`{rest}'


def _decided_by_index_set(context: str, name: str, text: str | None, in_: tuple[str, ...], inside: Condition) -> str:
    """The refusal for a ``where:`` that reads a relation of the entry's own ``in:``, by what is left of it inside."""
    named = ' and '.join(f"'{r}'" for r in in_)
    head = (
        f"{context}: in: gives '{name}' coordinates only where {named} "
        f'{"has" if len(in_) == 1 else "have"} a row, so `where: {text}`'
    )
    match inside:
        case BooleanLiteral(value=True):
            return f'{head} narrows nothing. Delete the `where:`, or the relation from it.'
        case BooleanLiteral():
            return f"{head} leaves '{name}' no coordinate. Write a `where:` that holds somewhere inside the relation."
        case _:
            return f'{head} repeats the relation. Delete the relation from it.'


def _assumption(name: str, entry: AssumptionSpec, ns: Namespace, errors: list[str]) -> Assumption | None:
    """One ``assumptions:`` entry typed, or ``None`` once anything in it failed.

    A condition the connectives decide is refused: one that folds to true
    assumes nothing, and one that folds to false refuses every dataset. A
    variable is refused too, since an assumption is about the data and a
    variable is what the solver decides from it.
    """
    context = f"Assumption '{name}'"
    found = len(errors)
    holds = resolve_condition_text(entry.holds, ns, context, errors)
    where = resolve_condition_text(entry.where, ns, f'{context}, where', errors)
    if isinstance(holds, BooleanLiteral):
        errors.append(_decided_assumption(context, entry.holds, value=holds.value))
    if isinstance(where, BooleanLiteral):
        assert entry.where is not None, 'a `where:` the file did not write resolves to nothing'
        errors.append(_decided_where(context, entry.where, value=where.value))
    for mask, key in ((holds, 'holds'), (where, 'where')):
        if mask is None or isinstance(mask, BooleanLiteral):
            continue
        errors.extend(
            f"{context}: variable '{atom.name}' appears in '{key}:', and an assumption checks only data. "
            f'Name a parameter, or state the rule as a constraint.'
            for atom in Mask(mask).atoms
            if isinstance(atom, VariableDefined)
        )
    if len(errors) > found:
        return None
    assert holds is not None, 'a condition that read to nothing appended an error'
    return Assumption(Mask(holds), mask_of(where), entry.description)


def _decided_assumption(context: str, text: str, *, value: bool) -> str:
    """The refusal for a condition the connectives already decided, whose data is never read."""
    if value:
        return (
            f'{context}: the condition {text!r} folds to true, so it assumes nothing of the data. '
            f'Delete it, or name a parameter it constrains.'
        )
    return (
        f'{context}: the condition {text!r} folds to false, so it holds on no data at all. '
        f'Delete it, or write the condition the data can satisfy.'
    )


def _decided_where(context: str, text: str, *, value: bool) -> str:
    """The refusal for a ``where`` the connectives already decided, which narrows nothing or everything."""
    if value:
        return f'{context}: the `where:` condition {text!r} folds to true, so it narrows nothing. Delete the `where:`.'
    return (
        f'{context}: the `where:` condition {text!r} folds to false, so the assumption is checked on no row. '
        f'Delete the entry, or write a `where:` condition the data can satisfy.'
    )
