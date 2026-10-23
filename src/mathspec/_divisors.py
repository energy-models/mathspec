# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The load-time refusal of a divisor that the file itself makes 0.

Two things put that 0 in: a missing row of a ``missing: 0`` parameter, and
the edge of a shift written ``edge=0``. No data can repair either. A guard
spares a divisor of the first kind where it is false at every missing row: a
conjunct of the ``where`` of the declaration, of the ``when`` of a case, or of
the mask of a ``missing: absent`` variable that is a factor of the quotient,
since an absent factor makes the whole product absent. A guard holds only at
the coordinate it is read at, so a sum, a window, a shift or a lookup drops
every guard from outside it.
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
    """A refusal for each ``missing: 0`` parameter or ``edge=0`` shift that can make a divisor under *expression* 0.

    *masks* are the ``where`` masks of the variables that are absent outside
    them, and *where* is the mask of the
    declaration that holds *expression*. A named expression is not entered:
    it is read over its own frame, so it is checked as its own entry.
    """
    causes = dict.fromkeys(_zero_divisors(expression, parameters, masks, _spared(where)))
    return [f'{context}: the divisor {cause}' for cause in causes]


def _missing_zero(name: str) -> str:
    """Why a missing row of *name* makes the divisor 0, and the three rewrites that remove it."""
    return (
        f"reads '{name}', which is declared missing: 0, so a missing row of '{name}' makes the divisor 0, which "
        f'no number divides by. Declare missing: refused, absent, or a value other than 0, or guard the quotient '
        f'with a where such as "{name} > 0".'
    )


def _edge_zero(along: str) -> str:
    """Why the edge of an ``edge=0`` shift makes the divisor 0. No guard spares it, so the rewrite is the edge."""
    return (
        f'is 0 where shift(along={along}, edge=0) vacates, which no number divides by. '
        f"Write edge='wrap', or an edge= value other than 0."
    )


def _zero_divisors(
    e: Expression, parameters: Mapping[str, ParameterSpec], masks: Mapping[str, Mask | None], spared: frozenset[str]
) -> Iterator[str]:
    """Why each divisor under *e* can be 0, for each cause *spared* does not leave out."""
    match e:
        case Multiply() | Divide():
            for factor in _factors(e):
                if isinstance(factor, VariableReference):
                    spared |= _spared(masks.get(factor.name))
            if isinstance(e, Divide) and (cause := _zero_in(e.divisor, parameters, spared)) is not None:
                yield cause
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


def _zero_in(e: Expression, parameters: Mapping[str, ParameterSpec], spared: frozenset[str]) -> str | None:
    """Why the file can make *e* 0, or ``None`` where it cannot.

    The cause is a ``missing: 0`` parameter not in *spared*, or a shift
    written ``edge=0``, which no guard spares. A factor, the numerator of a
    quotient, the base of a power, and the operand of a sum, a shift, a lookup
    or a named expression make *e* 0 where they are 0; a sum of terms only
    where every term is, so ``p + 1`` never is; a case where any region is.
    """
    match e:
        case ParameterReference(name=name):
            declared = parameters.get(name)
            zero = declared is not None and declared.missing == 0 and name not in spared
            return _missing_zero(name) if zero else None
        case Translate(along=along, fill=fill) if fill == 0:
            return _edge_zero(along)
        case Sum(operand=operand) | WindowSum(operand=operand) | Translate(operand=operand) | Join(operand=operand):
            return _zero_in(operand, parameters, frozenset())
        case Negate(operand=operand) | ExpressionReference(body=operand):
            return _zero_in(operand, parameters, spared)
        case Multiply(left=left, right=right):
            return _zero_in(left, parameters, spared) or _zero_in(right, parameters, spared)
        case Divide(numerator=numerator):
            return _zero_in(numerator, parameters, spared)
        case Power(base=base):
            return _zero_in(base, parameters, spared)
        case Add(left=left, right=right):
            cause = _zero_in(left, parameters, spared)
            return cause if cause is not None and _zero_in(right, parameters, spared) is not None else None
        case Cases(regions=regions):
            return next(
                (c for r in regions if (c := _zero_in(r.value, parameters, spared | _spared(r.when)))),
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
