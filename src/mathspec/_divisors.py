# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The load-time refusal of a divisor that a missing row of a ``missing: 0`` parameter makes 0.

The language puts that 0 in, so no data can repair it. A guard spares the
divisor where it is false at every missing row: a conjunct of the ``where``
of the declaration, of the ``when`` of a case, or of the mask of a
``missing: absent`` variable that is a factor of the quotient, since an absent
factor makes the whole product absent. A guard holds only at the coordinate it is read at, so a
sum, a window, a shift or a lookup drops every guard from outside it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mathspec.program import (
    Add,
    Cases,
    ConditionReference,
    Divide,
    ExpressionReference,
    Join,
    Mask,
    Multiply,
    Negate,
    ParameterComparison,
    ParameterDefined,
    ParameterReference,
    Power,
    Sum,
    Translate,
    VariableReference,
    WindowSum,
    children,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from mathspec.program import ComparisonOperator, Condition, Expression
    from mathspec.spec import ParameterSpec


def zero_divisor_refusals(
    expression: Expression,
    context: str,
    parameters: Mapping[str, ParameterSpec],
    masks: Mapping[str, Mask | None],
    where: Mask | None = None,
) -> list[str]:
    """A refusal for each ``missing: 0`` parameter that can make a divisor under *expression* 0.

    *masks* are the ``where`` masks of the variables that are absent outside
    them, and *where* is the mask of the
    declaration that holds *expression*. A named expression is not entered:
    it is read over its own frame, so it is checked as its own entry.
    """
    names = dict.fromkeys(_zero_divisors(expression, parameters, masks, _spared(where)))
    return [
        f"{context}: the divisor reads '{name}', which is declared missing: 0, so a missing row of '{name}' "
        f'makes the divisor 0, which no number divides by. Declare missing: refused, absent, or a value other '
        f'than 0, or guard the quotient with a where such as "{name} > 0".'
        for name in names
    ]


def _zero_divisors(
    e: Expression, parameters: Mapping[str, ParameterSpec], masks: Mapping[str, Mask | None], spared: frozenset[str]
) -> Iterator[str]:
    """Each parameter not in *spared* whose missing row zeroes a divisor under *e*."""
    match e:
        case Multiply() | Divide():
            for factor in _factors(e):
                if isinstance(factor, VariableReference):
                    spared |= _spared(masks.get(factor.name))
            if isinstance(e, Divide) and (name := _zero_where_missing(e.divisor, parameters, spared)) is not None:
                yield name
        case Cases(regions=regions):
            for region in regions:
                yield from _zero_divisors(region.value, parameters, masks, spared | _spared(region.when))
            return
        case Sum() | WindowSum() | Translate() | Join():
            spared = frozenset()
        case ExpressionReference():
            return
    for child in children(e):
        yield from _zero_divisors(child, parameters, masks, spared)


def _factors(e: Expression) -> tuple[Expression, ...]:
    """The factors of the product *e* heads, through a negation; a divisor is no factor, since it never is absent alone."""
    match e:
        case Multiply(left=left, right=right):
            return _factors(left) + _factors(right)
        case Divide(numerator=numerator):
            return _factors(numerator)
        case Negate(operand=operand):
            return _factors(operand)
    return (e,)


def _zero_where_missing(e: Expression, parameters: Mapping[str, ParameterSpec], spared: frozenset[str]) -> str | None:
    """The ``missing: 0`` parameter not in *spared* whose missing row makes *e* 0, or ``None`` where no missing row can.

    A factor, the numerator of a quotient, the base of a power, and the
    operand of a sum, a shift, a lookup or a named expression make *e* 0 where
    they are 0; a sum of terms only where every term is, so ``p + 1`` never
    is; a case where any region is.
    """
    match e:
        case ParameterReference(name=name):
            declared = parameters.get(name)
            return name if declared is not None and declared.missing == 0 and name not in spared else None
        case Sum(operand=operand) | WindowSum(operand=operand) | Translate(operand=operand) | Join(operand=operand):
            return _zero_where_missing(operand, parameters, frozenset())
        case Negate(operand=operand) | ExpressionReference(body=operand):
            return _zero_where_missing(operand, parameters, spared)
        case Multiply(left=left, right=right):
            return _zero_where_missing(left, parameters, spared) or _zero_where_missing(right, parameters, spared)
        case Divide(numerator=numerator):
            return _zero_where_missing(numerator, parameters, spared)
        case Power(base=base):
            return _zero_where_missing(base, parameters, spared)
        case Add(left=left, right=right):
            name = _zero_where_missing(left, parameters, spared)
            return name if name is not None and _zero_where_missing(right, parameters, spared) is not None else None
        case Cases(regions=regions):
            return next(
                (n for r in regions if (n := _zero_where_missing(r.value, parameters, spared | _spared(r.when)))),
                None,
            )
    return None


def _spared(mask: Mask | None) -> frozenset[str]:
    """The parameters whose every missing row *mask* leaves out, read off its ``AND`` spine."""
    if mask is None:
        return frozenset()
    return frozenset(name for conjunct in mask.conjuncts for name in _left_out(conjunct))


def _left_out(conjunct: Condition) -> frozenset[str]:
    """The parameter a conjunct is false at wherever its row is missing and it reads as 0."""
    match conjunct:
        case ParameterDefined(name=name):
            return frozenset({name})
        case ParameterComparison(name=name, op=op, value=float() | int() as value) if not _holds(0.0, op, value):
            return frozenset({name})
        case ConditionReference(body=body):
            return _spared(Mask(body))
    return frozenset()


def _holds(left: float, op: ComparisonOperator, right: float) -> bool:
    """Whether ``left <op> right`` holds."""
    match op:
        case '<':
            return left < right
        case '<=':
            return left <= right
        case '>':
            return left > right
        case '>=':
            return left >= right
        case '==':
            return left == right
        case '!=':
            return left != right
