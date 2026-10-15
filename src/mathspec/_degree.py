# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Degree — the one admissibility rule that is a scope choice (docs/about/limits.md).

**Degree 2 in the math, degree 1 in what stands beside it.** An objective and a
constraint both take ``variable * variable``; a *bound* and a ``piecewise:``
link do not — each of those is read affinely. An ``expressions:`` entry is not
degree-checked where it is written: the math reading it is checked where it
reads, at that position's own ceiling, and an entry the math never reads
(``NamedExpression.in_math``) is held to no degree.

A degree-2 product has a second rule: **at most one factor may be a sum of
terms**. ``sum(x, over=i) * sum(y, over=j)`` is a cross join whose size the
file states nowhere. Factors carrying *different dims* are not that: ``x[i] *
y[j]`` broadcasts.
"""

from __future__ import annotations

from mathspec.errors import LanguageError
from mathspec.program import (
    Add,
    Divide,
    Dual,
    Expression,
    Multiply,
    Power,
    Sum,
    VariableReference,
    WindowSum,
    carries_variable,
    children,
    walk,
)


def check_binary(node: Multiply | Divide | Power, context: str, *, ceiling: int) -> None:
    """Check that *node* stays inside the degree its position allows.

    Args:
        node: The product, quotient or power to judge.
        context: What to name in the message — the entry being read.
        ceiling: The highest degree this position can honour — 2 in an
            objective or a constraint, 1 everywhere else.

    Raises:
        LanguageError: A product of two variable-carrying factors where the
            position allows only degree 1 or where both factors are sums of
            terms, a power over anything carrying a variable, a divisor carrying
            a variable.
    """
    where = f'{context}: ' if context else ''
    if isinstance(node, Power):
        if carries_variable(node):
            raise LanguageError(_a_variable_under_a_power_message(where))
        return
    if isinstance(node, Divide):
        if carries_variable(node.divisor):
            raise LanguageError(
                f'{where}the divisor contains variables, which is not affine. '
                f'Divide by a parameter, or precompute the reciprocal as one.'
            )
        return
    if not (carries_variable(node.left) and carries_variable(node.right)):
        return
    if ceiling < 2:
        raise LanguageError(_degree_two_here_message(where))
    if (degree := _degree(node)) > ceiling:
        raise LanguageError(_above_the_ceiling_message(where, degree))
    _check_single_term_factor(node, where)


def _degree(node: Expression) -> int:
    """The polynomial degree *node* stands for, counted structurally.

    A product adds its factors' degrees and a division keeps the dividend's
    ([`check_binary`][] has already refused a divisor carrying a variable);
    everything else — a sum, a reduction, a shape operator — is the highest
    degree beneath it. No data, so this answers at ``check`` time, which is
    what stops a cubic from reaching a consumer to be refused by whichever one
    happens to notice.
    """
    if isinstance(node, VariableReference):
        return 1
    if isinstance(node, Multiply):
        return _degree(node.left) + _degree(node.right)
    if isinstance(node, Divide):
        return _degree(node.numerator)
    return max((_degree(child) for child in children(node)), default=0)


def _above_the_ceiling_message(where: str, degree: int) -> str:
    """About the product's own degree, since ``p * p * p`` is two admissible products nested."""
    return (
        f'{where}this product is degree {degree}, and the limit is degree 2.\n'
        f'Multiply by a parameter instead, or declare a variable constrained to equal the inner product.'
    )


def _a_variable_under_a_power_message(where: str) -> str:
    return (
        f'{where}`**` has a variable in its base or exponent.\n'
        f'Write the product out, such as `x * x` for a square, or precompute the factor as a parameter. '
        f'See docs/about/limits.md.'
    )


def _degree_two_here_message(where: str) -> str:
    return (
        f'{where}both factors of a product contain variables, which is degree 2, and only the objective '
        f'and constraints allow degree 2.\n'
        f'Multiply the variable by a parameter instead, or write the product in a constraint of its own, '
        f'with a variable holding the result.'
    )


def _check_single_term_factor(node: Multiply, where: str) -> None:
    """Refuse a degree-2 product of two multi-term factors."""
    if not (_multi_term(node.left) and _multi_term(node.right)):
        return
    raise LanguageError(
        f'{where}both factors of this product are sums of more than one term, which makes an outer product.\n'
        f'Multiply before you reduce: write ``sum(x * y, over=d)``, not '
        f'``sum(x, over=d) * sum(y, over=d)``.'
    )


def _multi_term(node: Expression) -> bool:
    """Whether *node* stands for more than one variable term at a coordinate.

    A reduction does, and so does an addition of two variable-carrying
    operands; a product is multi-term exactly when one of its factors is, a
    coefficient not multiplying the count. Structural, so it needs no data.
    """
    return any(_joins_terms(found) for found in walk(node))


def _joins_terms(node: Expression) -> bool:
    """Whether *node* itself makes several terms of one: a reduction over a variable, or a sum of two variable-carrying sides.

    A lookup and a translation re-index and are not reductions: they move a
    term, leaving one term where there was one.
    """
    if isinstance(node, Sum | WindowSum):
        return carries_variable(node.operand)
    return isinstance(node, Add) and carries_variable(node.left) and carries_variable(node.right)


def check_expression(node: Expression, context: str, *, ceiling: int = 1) -> None:
    """What the math admits at one position: no dual anywhere under *node*, then [`check_binary`][] everywhere in it.

    Asked of the resolved tree, so a dual or a product reached through a
    macro or a named expression is caught alongside one written in place.
    What a plan node can represent is the consumer's question, not this one's.

    Raises:
        LanguageError: A dual, which exists only after a solve; or what
            [`check_binary`][] refuses.
    """
    for found in walk(node):
        if isinstance(found, Dual):
            raise LanguageError(
                f'{context}: a dual exists only after a solve, so it cannot stand here. Keep the entry '
                f'that reads it out of constraints, the objective, bounds and where.'
            )
        if isinstance(found, Multiply | Divide | Power):
            check_binary(found, context, ceiling=ceiling)


def calls_dual(node: Expression) -> bool:
    """Whether a [`Dual`][mathspec.program.Dual] stands anywhere under *node*."""
    return any(isinstance(found, Dual) for found in walk(node))
