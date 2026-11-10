# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""``curve(x=, y=)`` in a constraint, and the ``breakpoints:`` parameter it reads.

A macro of the language: a constraint with one ``curve`` term loads as the
``piecewise:`` entry it states, under the constraint's name, with two links.
The link ``x`` ties the x expression to the x values of the curve, and the
link ``y`` ties the rest of the constraint to its values, with the sign of
the comparison. A parameter ``Y`` that declares ``breakpoints: <axis>`` brings
the breakpoint dimension ``Y.breakpoint`` and the parameter of its x values
``Y.<axis>``, which the program carries as any other.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast

from pydantic import ValidationError

from mathspec._expression_parser import (
    NAME,
    BinaryOperatorNode,
    ComparisonNode,
    FunctionCallNode,
    KeywordNode,
    NameNode,
    UnaryOperatorNode,
    nodes,
    operand,
    parse_expression,
)
from mathspec._frozen import Frozen
from mathspec._operators import CURVE, CURVE_USAGE
from mathspec.errors import SchemaError, did_you_mean
from mathspec.spec import PIECEWISE_METHODS, DimensionSpec, ParameterSpec, PiecewiseSpec

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mathspec._expression_parser import ArithmeticNode, Sense
    from mathspec.spec import ConstraintSpec, Spec

BREAKPOINT = 'breakpoint'
"""What follows the dot in the name of the dimension a ``breakpoints:`` parameter brings."""
_FLIPPED: dict[Sense, Sense] = {'<=': '>=', '>=': '<=', '==': '=='}
_DOTTED = re.compile(rf'(?<![\w.])({NAME})\.({NAME})(?![\w(])')


def breakpoint_dimension(name: str) -> str:
    """The dimension that numbers the breakpoints of the ``breakpoints:`` parameter *name*, in order of x."""
    return f'{name}.{BREAKPOINT}'


def x_values(name: str, axis: str) -> str:
    """The parameter of the x values of the ``breakpoints:`` parameter *name*, whose x axis is *axis*."""
    return f'{name}.{axis}'


def _texts(node: object, path: tuple[str, ...]) -> Iterator[tuple[tuple[str, ...], str]]:
    """Every string the file wrote under *node* but a description, with the keys that lead to it."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, Mapping):
        for key, value in node.items():
            if key != 'description':
                yield from _texts(value, (*path, str(key)))
    elif isinstance(node, Sequence):
        for value in node:
            yield from _texts(value, path)


def _dot_errors(spec: Spec, curved: Mapping[str, ParameterSpec]) -> Iterator[str]:
    """A dotted name reads the x values or the breakpoint dimension of a ``breakpoints:`` parameter, and nothing else."""
    for path, text in _texts(spec.model_dump(exclude_defaults=True), ()):
        where = '.'.join(path[:2])
        for match in _DOTTED.finditer(text):
            name, part = match.groups()
            if name not in curved:
                yield (
                    f"{where}: '{match.group()}' reads part of a curve, and '{name}' is no parameter with "
                    f"breakpoints:. Declare breakpoints: <axis> on parameter '{name}', and write "
                    f"'{name}.<axis>' or '{name}.{BREAKPOINT}'."
                )
            elif part not in (axis := cast('str', curved[name].breakpoints), BREAKPOINT):
                yield (
                    f"{where}: '{match.group()}' is not part of the curve '{name}'. Write '{name}.{axis}' for its "
                    f"x values, or '{name}.{BREAKPOINT}' for its breakpoints."
                )


def desugared(spec: Spec) -> Spec:
    """*spec* as lowering reads it: each ``curve`` constraint a ``piecewise:`` entry, each curve parameter over its breakpoints.

    Nothing is validated again: every part is built from entries that loaded.

    Raises:
        SchemaError: Listing every curve or breakpoint parameter the language refuses.
    """
    curved = {name: p for name, p in spec.parameters.items() if p.breakpoints is not None}
    entries = curve_entries(spec)
    if not curved and not entries:
        return spec
    parameters = dict(spec.parameters)
    dimensions = dict(spec.dimensions)
    errors = list(dict.fromkeys(_dot_errors(spec, curved)))
    for name, p in curved.items():
        axis = cast('str', p.breakpoints)
        dim, x = breakpoint_dimension(name), x_values(name, axis)
        dims = [*p.dims, dim]
        dimensions[dim] = DimensionSpec(
            dtype='int', ordered=True, description=f"the breakpoints of '{name}', numbered in order of {axis}"
        )
        parameters[name] = p.model_copy(update={'dims': tuple(sorted(dims)), 'missing': 'absent', 'breakpoints': None})
        parameters[x] = ParameterSpec(
            dims=dims, missing='absent', description=f"the {axis} at each breakpoint of '{name}'"
        )
    piecewise = dict(spec.piecewise)
    for name, entry in entries.items():
        if isinstance(entry, str):
            errors.append(entry)
        elif name in piecewise:
            errors.append(
                f"Constraint '{name}': its curve loads as piecewise '{name}', and the file declares piecewise "
                f"'{name}' already. Rename one."
            )
        else:
            piecewise[name] = entry
    if errors:
        raise SchemaError('\n'.join(errors))
    constraints = {name: c for name, c in spec.constraints.items() if name not in entries}
    return spec.model_copy(
        update={
            'dimensions': Frozen(dict(sorted(dimensions.items()))),
            'parameters': Frozen(dict(sorted(parameters.items()))),
            'constraints': Frozen(constraints),
            'piecewise': Frozen(piecewise),
        }
    )


def curve_entries(spec: Spec) -> dict[str, PiecewiseSpec | str]:
    """Each constraint of *spec* with a ``curve`` term, as the ``piecewise:`` entry it loads as, or its refusal.

    A constraint whose text does not parse is left to the expression pass,
    which refuses it with the grammar's own words.
    """
    found: dict[str, PiecewiseSpec | str] = {}
    for name, constraint in spec.constraints.items():
        try:
            ast = parse_expression(constraint.expression)
        except SchemaError:
            continue
        calls = [node for node in nodes(ast) if isinstance(node, FunctionCallNode) and node.name == CURVE]
        if calls and isinstance(ast, ComparisonNode):
            found[name] = _entry(f"Constraint '{name}'", constraint, ast, calls, spec)
    return found


def _entry(
    context: str, constraint: ConstraintSpec, ast: ComparisonNode, calls: list[FunctionCallNode], spec: Spec
) -> PiecewiseSpec | str:
    """The ``piecewise:`` entry one ``curve`` constraint loads as, or the refusal that says what to rewrite."""
    if len(calls) > 1:
        return (
            f'{context}: it has {len(calls)} curve(...) terms, and a constraint reads one curve. Write one constraint '
            f'per curve, each with its own variable.'
        )
    (call,) = calls
    split = _split(ast, call)
    if split is None:
        return (
            f'{context}: curve(...) stands inside another term, and the curve is read as one term of one side, '
            f'added or subtracted. Move the other operations to the other side, or onto a variable of their own.'
        )
    value, sense = split
    if call.args or (unknown := sorted(set(call.kwargs) - {'x', 'y', 'active', 'method'})):
        shown = 'a positional argument' if call.args else f'{unknown[0]}='
        return f'{context}: curve(...) takes {shown}, and it takes keywords only. Write {CURVE_USAGE}.'
    if missing := [k for k in ('x', 'y') if k not in call.kwargs]:
        return f'{context}: curve(...) has no {missing[0]}=. Write {CURVE_USAGE}.'
    y = call.kwargs['y']
    curved = [n for n, p in spec.parameters.items() if p.breakpoints is not None]
    if not isinstance(y, NameNode) or y.name not in curved:
        return (
            f'{context}: curve(y={y}) reads a parameter declared with breakpoints: <axis>, and {y} is not one. '
            f'Declare breakpoints: <axis> on the parameter, so that its rows are the breakpoints of a curve. '
            f'{did_you_mean(str(y), curved)}'
        ).rstrip()
    method = call.kwargs.get('method', KeywordNode('adjacency'))
    if not isinstance(method, KeywordNode) or method.value not in PIECEWISE_METHODS:
        return f'{context}: curve(method={method}) is not a method. Write one of {", ".join(map(repr, PIECEWISE_METHODS))}.'
    if method.value == 'lp' and sense == '==':
        return (
            f"{context}: curve(method='lp') states the curve as its segment lines, which bound one side of it, and "
            f'the constraint is ==. Write <= or >=, or another method.'
        )
    if 'active' in call.kwargs and method.value in ('lp', 'convex'):
        return (
            f'{context}: curve(method={method}) takes no active=, because it states no weights for a gate to '
            f"switch. Delete active=, or write method='incremental'."
        )
    parameter = spec.parameters[y.name]
    axis = cast('str', parameter.breakpoints)
    where = x_values(y.name, axis) if constraint.where is None else f'({constraint.where}) AND {x_values(y.name, axis)}'
    raw = {
        'along': breakpoint_dimension(y.name),
        'dims': list(constraint.dims),
        'links': {'x': [str(call.kwargs['x']), x_values(y.name, axis)], 'y': [value, y.name, sense]},
        'where': where,
        'method': method.value,
        'description': constraint.description,
    }
    if 'active' in call.kwargs:
        raw['activity'] = str(call.kwargs['active'])
    try:
        return PiecewiseSpec.model_validate(raw)
    except ValidationError as e:
        return f'{context}: ' + '\n'.join(error['msg'].removeprefix('Value error, ') for error in e.errors())


def _split(ast: ComparisonNode, call: FunctionCallNode) -> tuple[str, Sense] | None:
    """The rest of the constraint as the expression the curve bounds, and the sign it is bounded with.

    ``None`` where the call is not a term of one side, added or subtracted.
    """
    for curved, other, sense in ((ast.left, ast.right, ast.op), (ast.right, ast.left, _FLIPPED[ast.op])):
        terms = _terms(curved, 1)
        signs = [sign for sign, term in terms if term is call]
        if not signs:
            continue
        if len(signs) != 1:
            return None
        rest = [(sign, term) for sign, term in terms if term is not call]
        value = _difference(other, rest)
        if signs[0] == 1:
            return value, _FLIPPED[sense]
        return f'-({value})', sense
    return None


def _terms(node: ArithmeticNode, sign: int) -> list[tuple[int, ArithmeticNode]]:
    """*node* as the terms it adds, each with the sign it is added with."""
    if isinstance(node, BinaryOperatorNode) and node.op in ('+', '-'):
        return [*_terms(node.left, sign), *_terms(node.right, sign if node.op == '+' else -sign)]
    if isinstance(node, UnaryOperatorNode):
        return _terms(node.operand, sign if node.op == '+' else -sign)
    return [(sign, node)]


def _difference(other: ArithmeticNode, rest: list[tuple[int, ArithmeticNode]]) -> str:
    """*other* minus the terms in *rest*, as text the expression grammar reads back."""
    text = str(other)
    for sign, term in rest:
        text = f'{text} {"-" if sign == 1 else "+"} {operand(term)}'
    return text
