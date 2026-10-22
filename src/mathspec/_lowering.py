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

from typing import TYPE_CHECKING

from mathspec._dimensions import check_spec, sorted_dims
from mathspec._divisors import zero_divisor_refusals
from mathspec._expansion import expand, parse_template
from mathspec._piecewise import assumptions_of, curve_frame, lp_domain_refusal, refused_under_points, resolve_links
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
    Assumption,
    BooleanLiteral,
    Constant,
    Constraint,
    Dimension,
    ExpressionReference,
    Given,
    GivenParameter,
    GivenTargets,
    Link,
    Mask,
    NamedCondition,
    NamedExpression,
    Objective,
    Parameter,
    ParameterReference,
    Piecewise,
    Program,
    Sos,
    Variable,
    VariableDefined,
    variables_of,
    walk,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from mathspec.program import Expression
    from mathspec.spec import AssumptionSpec, Spec


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

    A ``piecewise:`` entry's links are resolved and its frame checked here, on
    the link the file wrote, so the expansion writes rows the language has
    already held to every rule; what its method assumes of the breakpoints
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
            conditions[mname] = NamedCondition(body, tuple(sorted(body.dims)), mdef.description)

    parameter_masks = _parameter_masks(spec, ns, errors)

    variables = {}
    for vname, vdef in spec.variables.items():
        where = resolve_condition_text(vdef.where, ns, f"Variable '{vname}'", errors, self_variable=vname)
        if where is not None and (refusal := self_existence(where, vname, f"Variable '{vname}'")) is not None:
            errors.append(refusal)
        if vdef.domain == 'binary':
            lower_bound, upper_bound = Constant(0.0, dims=()), Constant(1.0, dims=())
        else:
            lower_bound, upper_bound = _bound(vdef.bounds.lower, ns), _bound(vdef.bounds.upper, ns)
        variables[vname] = Variable(
            tuple(vdef.dims),
            where=mask_of(where),
            lower=lower_bound,
            upper=upper_bound,
            domain=vdef.domain,
            missing=vdef.missing,
            description=vdef.description,
        )

    constraints: dict[str, Constraint] = {}
    for cname, cdef in spec.constraints.items():
        context = f"Constraint '{cname}'"
        where = resolve_condition_text(cdef.where, ns, context, errors)
        if (sides := resolve_constraint_text(cdef.expression, ns, context, errors)) is not None:
            lhs, sense, rhs = sides
            constraints[cname] = Constraint(
                tuple(cdef.dims), lhs, sense, rhs, mask_of(where), description=cdef.description
            )

    objective = None
    if spec.objective is not None:
        expression = resolve_expression_text(spec.objective.expression, ns, 'The objective', errors, ceiling=2)
        if expression is not None:
            objective = Objective(spec.objective.sense, expression, spec.objective.description)

    assumptions: dict[str, Assumption] = {}
    for aname, adef in spec.assumptions.items():
        if (assumption := _assumption(aname, adef, ns, errors)) is not None:
            assumptions[aname] = assumption

    curves: dict[str, tuple[Expression, ...]] = {}
    for pname, pdef in spec.piecewise.items():
        links = resolve_links(pname, pdef, ns, errors)
        if links is None:
            continue
        if pdef.method == 'lp' and (refusal := lp_domain_refusal(pname, pdef, links)) is not None:
            errors.append(refusal)
        curves[pname] = links

    errors.extend(_zero_divisor_refusals(spec, variables, entries, constraints, objective, curves))
    if errors:
        raise ns.error(errors)

    roots = [side for c in constraints.values() for side in (c.lhs, c.rhs)]
    if objective is not None:
        roots.append(objective.expression)
    roots.extend(link for links in curves.values() for link in links)
    roots.extend(terms)
    in_math = frozenset(node.name for node in walk(*roots) if isinstance(node, ExpressionReference))

    piecewise = {}
    for pname, links in curves.items():
        pdef = spec.piecewise[pname]
        piecewise[pname] = Piecewise(
            over=pdef.over,
            links=tuple(Link(node, link.values, link.sign) for node, link in zip(links, pdef.links, strict=True)),
            method=pdef.method,
            frame=curve_frame(spec, pname, pdef, links),
            activity=pdef.activity,
            points=pdef.points,
            description=pdef.description,
        )
        for aname, assumed in assumptions_of(pname, piecewise[pname]).items():
            assumption = _assumption(aname, assumed, ns, errors)
            assert assumption is not None and not errors, 'what a method assumes is stated in the language'
            assumptions[aname] = assumption

    program = Program(
        parameters={
            name: Parameter(tuple(pdef.dims), pdef.dtype, pdef.missing, pdef.description, parameter_masks.get(name))
            for name, pdef in spec.parameters.items()
        },
        variables=variables,
        constraints=constraints,
        objective=objective,
        dimensions={
            name: Dimension(dtype=ddef.dtype, ordered=ddef.ordered, description=ddef.description)
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
                _frame_of(name, entry, spec),
                in_math=name in in_math,
                description=spec.expressions[name].description,
                adds_to=spec.expressions[name].adds_to,
            )
            for name, entry in entries.items()
        },
        conditions=conditions,
        given=GivenTargets(
            parameters={
                name: GivenParameter(tuple(g.dims), g.dtype, g.description) for name, g in spec.given.parameters.items()
            },
            variables={name: Given(tuple(g.dims), g.description) for name, g in spec.given.variables.items()},
            constraints={name: Given(tuple(g.dims), g.description) for name, g in spec.given.constraints.items()},
            expressions={name: Given(tuple(g.dims), g.description) for name, g in spec.given.expressions.items()},
            conditions={name: Given(tuple(g.dims), g.description) for name, g in spec.given.conditions.items()},
        ),
        description=spec.description,
    )
    if errors := [*emitted_name_errors(spec, program), *refused_under_points(spec)]:
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
    found: list[str] = []
    for name, entry in entries.items():
        found += zero_divisor_refusals(entry.body, f"Named expression '{name}'", spec.parameters, masks)
    for name, c in constraints.items():
        for side in (c.lhs, c.rhs):
            found += zero_divisor_refusals(side, f"Constraint '{name}'", spec.parameters, masks, c.where)
    if objective is not None:
        found += zero_divisor_refusals(objective.expression, 'The objective', spec.parameters, masks)
    for name, links in curves.items():
        for link in links:
            found += zero_divisor_refusals(link, f"piecewise '{name}'", spec.parameters, masks)
    return list(dict.fromkeys(found))


def _frame_of(name: str, entry: ExpressionReference, spec: Spec) -> tuple[str, ...]:
    """The dims an entry is read over: the ``dims:`` it declares, as written, else the body's, sorted by name."""
    declared = spec.expressions[name].dims
    return entry.dims if declared is None else tuple(declared)


def _bound(value: float | str | None, ns: Namespace) -> Constant | ParameterReference | None:
    if value is None:
        return None
    if isinstance(value, str):
        return ParameterReference(value, dims=sorted_dims(ns.leaf_dims[value]))
    return Constant(value, dims=())


def _parameter_masks(spec: Spec, ns: Namespace, errors: list[str]) -> dict[str, Mask | None]:
    """Each parameter's ``where:`` typed, a refusal appended for each mask nothing can evaluate.

    A consumer evaluates a parameter's mask when it attaches the data, before
    any variable has a value, and before the parameter itself has rows to
    read. So a mask may not read a variable, and the masks may not read one
    another in a cycle: each would need its own answer first.
    """
    masks: dict[str, Mask | None] = {}
    for pname, pdef in spec.parameters.items():
        if pdef.where is None:
            continue
        context = f"Parameter '{pname}'"
        mask = masks[pname] = mask_of(resolve_condition_text(pdef.where, ns, context, errors))
        if mask is not None:
            errors.extend(
                f"{context}: its `where:` reads variable '{v}', and a parameter's mask is evaluated from the data "
                f'alone, before any variable has a value. Test a parameter or a relation instead.'
                for v in sorted(mask.names_read & {*spec.variables, *spec.given.variables})
            )
    errors.extend(_mask_cycles(masks))
    return masks


def _mask_cycles(masks: Mapping[str, Mask | None]) -> Iterator[str]:
    """A refusal for each parameter whose mask reads itself, directly or through other parameters' masks."""
    reads = {name: mask.names_read & masks.keys() for name, mask in masks.items() if mask is not None}
    for start in sorted(reads):
        chain = _chain_back(start, reads)
        if chain is None:
            continue
        if len(chain) == 2:
            yield (
                f"Parameter '{start}': its `where:` reads '{start}' itself, and whether a row is there is what "
                f'the mask decides. Test a relation or another parameter.'
            )
        else:
            yield (
                f"Parameter '{start}': its `where:` reads itself through {' -> '.join(chain)}, so no mask can be "
                f'evaluated first. Test a relation or a parameter that has no mask.'
            )


def _chain_back(start: str, reads: Mapping[str, frozenset[str]]) -> tuple[str, ...] | None:
    """The shortest chain of masks from *start* back to *start*, or ``None`` where none returns."""
    chains: dict[str, tuple[str, ...]] = {start: (start,)}
    frontier = [start]
    while frontier:
        current = frontier.pop(0)
        for nxt in sorted(reads.get(current, ())):
            if nxt == start:
                return (*chains[current], start)
            if nxt not in chains:
                chains[nxt] = (*chains[current], nxt)
                frontier.append(nxt)
    return None


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
