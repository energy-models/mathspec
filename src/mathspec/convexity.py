# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The walk behind [`Program.problem_class`][] — the problem kind, and convexity proven from the file alone.

The quadratic part of an objective or a row is a sum of product terms, each two
affine factors times a coefficient. A term whose two factors are one expression
is a square: positive semidefinite where its coefficient is non-negative, and
a sum of those is too. A term of two different factors is a cross term, whose
curvature the terms beside it decide. One cross term is decided alone: a bare
variable no other term reads, times a different one, puts a zero on the
diagonal beside a nonzero entry, and no matrix like that is semidefinite.

A coefficient's sign is the set of signs its value may take, out of
``{-1, 0, 1}``: a number has one, a parameter has what an assumption with no
``where:`` leaves it, and each operator combines its operands' sets.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, assert_never

from mathspec._sealed import Sealed
from mathspec.program import (
    Add,
    Cases,
    Constant,
    Divide,
    Dual,
    ExpressionComparison,
    GroupSum,
    Multiply,
    Named,
    Negate,
    Parameter,
    ParameterComparison,
    Power,
    ProblemClass,
    Pullback,
    Sum,
    Translate,
    Variable,
    WindowSum,
    carries_variable,
    children,
    is_quadratic,
    parameters_of,
    variables_of,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from mathspec.program import Expression, Predicate, PredicateOperator, ProblemKind, Program

#: The signs a value may take, a subset of ``{-1, 0, 1}``.
Signs = frozenset[int]

#: The semidefiniteness a position's quadratic part needs to be convex.
Need = Literal['psd', 'nsd', 'zero']

ANY: Signs = frozenset({-1, 0, 1})
POSITIVE: Signs = frozenset({1})
NEGATIVE: Signs = frozenset({-1})
NON_NEGATIVE: Signs = frozenset({0, 1})
NON_POSITIVE: Signs = frozenset({-1, 0})

#: The ``piecewise:`` methods whose rows need an integral variable or a set.
_INTEGRAL_METHODS = frozenset({'adjacency', 'sos2'})

_KINDS: Mapping[tuple[bool, str], ProblemKind] = {
    (False, 'LP'): 'LP',
    (True, 'LP'): 'MILP',
    (False, 'QP'): 'QP',
    (True, 'QP'): 'MIQP',
    (False, 'QCP'): 'QCP',
    (True, 'QCP'): 'MIQCP',
}

_NEEDS: Mapping[str, Need] = {'<=': 'psd', '>=': 'nsd', '==': 'zero'}

_COMPARE = {
    '<=': operator.le,
    '>=': operator.ge,
    '==': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '>': operator.gt,
}

_FLIPPED: Mapping[PredicateOperator, PredicateOperator] = {
    '<=': '>=',
    '>=': '<=',
    '<': '>',
    '>': '<',
    '==': '==',
    '!=': '!=',
}


@dataclass(frozen=True)
class _Term:
    """One product of two variable-carrying factors, and the signs its coefficient may take.

    The factors are what is left once every variable-free factor is moved into
    the coefficient, so ``-2 * p * p`` is a square of ``p`` with a negative
    coefficient; ``unsigned`` names the parameters moved there whose sign no
    assumption states.
    """

    left: Expression
    right: Expression
    scale: Signs
    unsigned: frozenset[str]

    @property
    def square(self) -> bool:
        return self.left == self.right

    def __str__(self) -> str:
        if self.square:
            return f'squares {_names(self.left)}'
        return f'multiplies {_names(self.left)} by {_names(self.right)}'


def problem_class(program: Program) -> ProblemClass:
    """The kind of *program*, and the verdict on each declaration a quadratic term stands in."""
    known = _parameter_signs(program)
    nonconvex: dict[str, str] = {}
    undecided: dict[str, str] = {}
    for label, need, sides in _positions(program):
        terms = [term for expression, scale in sides for term in _terms(expression, scale, frozenset(), known)]
        if not terms:
            continue
        verdict, reason = _verdict(terms, need)
        if verdict == 'nonconvex':
            nonconvex[label] = reason
        elif verdict == 'undecided':
            undecided[label] = reason
    return ProblemClass(kind=_kind(program), nonconvex=Sealed(nonconvex), undecided=Sealed(undecided))


def _kind(program: Program) -> ProblemKind:
    """The kind, a curve counted by the rows its method writes."""
    integral = (
        any(v.domain != 'continuous' for v in program.variables.values())
        or bool(program.sos)
        or any(curve.method in _INTEGRAL_METHODS for curve in program.piecewise.values())
    )
    quadratic = program.footprint.quadratic
    shape = 'QCP' if 'constraint' in quadratic else 'QP' if 'objective' in quadratic else 'LP'
    return _KINDS[integral, shape]


def _positions(program: Program) -> Iterator[tuple[str, Need, tuple[tuple[Expression, Signs], ...]]]:
    """Each declaration a solver checks, with the need its sense sets and each side signed as it enters.

    A row reads as ``lhs - rhs`` against zero, so its right side enters negated.
    """
    if program.objective is not None:
        need: Need = 'psd' if program.objective.sense == 'minimize' else 'nsd'
        yield 'objective', need, ((program.objective.expression, POSITIVE),)
    for name, row in program.constraints.items():
        yield f"constraint '{name}'", _NEEDS[row.sense], ((row.lhs, POSITIVE), (row.rhs, NEGATIVE))


def _verdict(terms: list[_Term], need: Need) -> tuple[Literal['convex', 'nonconvex', 'undecided'], str]:
    """Whether the terms make a convex position, a nonconvex one, or one the data decides — and why."""
    if witness := _indefinite(terms):
        return 'nonconvex', witness
    if need == 'zero':
        if all(t.square for t in terms) and (
            all(t.scale <= POSITIVE for t in terms) or all(t.scale <= NEGATIVE for t in terms)
        ):
            return 'nonconvex', (
                f'{terms[0]}, and every quadratic term is a square with a coefficient of that one strict sign, '
                f'so no data cancels the quadratic part of an equality'
            )
        return 'undecided', f'{terms[0]}, and an equality is convex only where data cancels its quadratic part'
    wanted, opposite, wrong = (
        (NON_NEGATIVE, NEGATIVE, 'negative') if need == 'psd' else (NON_POSITIVE, POSITIVE, 'positive')
    )
    blocking = next((t for t in terms if not (t.square and t.scale <= wanted)), None)
    if blocking is None:
        return 'convex', ''
    if all(t.square and t.scale <= opposite for t in terms):
        return 'nonconvex', (
            f'{terms[0]} with a {wrong} coefficient, and every quadratic term is a square like it, '
            f'so the curvature is the wrong way whatever the data'
        )
    if not blocking.square:
        return 'undecided', f'{blocking}, a cross term whose curvature the terms beside it decide with data'
    if blocking.unsigned:
        return 'undecided', (
            f'{blocking} with a coefficient whose sign the file does not state — an assumptions: entry '
            f"bounding '{min(blocking.unsigned)}' on one side of zero decides it"
        )
    certainly = 'is' if blocking.scale <= opposite else 'may be'
    return 'undecided', f'{blocking} with a coefficient that {certainly} {wrong}, beside terms of the other sign'


def _indefinite(terms: list[_Term]) -> str | None:
    """The cross term no data makes semidefinite, described, or ``None``.

    A bare variable times a different one, under a coefficient of one strict
    sign, where no other term reads the first: the Hessian's diagonal is zero
    at that variable and its entry with the second is not.
    """
    for term in terms:
        if not (isinstance(term.left, Variable) and isinstance(term.right, Variable)):
            continue
        if term.square or term.scale not in (POSITIVE, NEGATIVE):
            continue
        others = variables_of(*(side for t in terms if t is not term for side in (t.left, t.right)))
        for alone in (term.left.name, term.right.name):
            if alone not in others:
                return (
                    f"{term}, and no other quadratic term reads '{alone}' — a product like that is "
                    f'indefinite whatever the data'
                )
    return None


def _terms(node: Expression, scale: Signs, unsigned: frozenset[str], known: Mapping[str, Signs]) -> Iterator[_Term]:
    """Every product term under *node*, each with the signs it enters its position with.

    A reduction, a re-index, a window, a cases selection and a named entry pass
    *scale* to their children unchanged: each sums or selects whole terms, and
    a sum of squares under one sign is still one.
    """
    if not is_quadratic(node):
        return
    if isinstance(node, Negate):
        yield from _terms(node.operand, _negate(scale), unsigned, known)
    elif isinstance(node, Add):
        yield from _terms(node.left, scale, unsigned, known)
        yield from _terms(node.right, scale, unsigned, known)
    elif isinstance(node, Multiply):
        if carries_variable(node.left) and carries_variable(node.right):
            yield _term(node.left, node.right, scale, unsigned, known)
            return
        factor, coefficient = (node.left, node.right) if carries_variable(node.left) else (node.right, node.left)
        yield from _terms(
            factor, _times(scale, _sign(coefficient, known)), unsigned | _unsigned(coefficient, known), known
        )
    elif isinstance(node, Divide):
        yield from _terms(
            node.numerator,
            _times(scale, _reciprocal(_sign(node.divisor, known))),
            unsigned | _unsigned(node.divisor, known),
            known,
        )
    elif isinstance(node, Sum | GroupSum | Pullback | Translate | WindowSum | Cases | Named):
        for child in children(node):
            yield from _terms(child, scale, unsigned, known)
    elif isinstance(node, Constant | Parameter | Variable | Dual | Power):
        return
    else:
        assert_never(node)


def _term(
    left: Expression, right: Expression, scale: Signs, unsigned: frozenset[str], known: Mapping[str, Signs]
) -> _Term:
    """One product term, its variable-free factors moved into the coefficient.

    Two identical factors are a square as they stand, whatever they multiply
    by: ``(c * p) * (c * p)`` is ``c²p²``, which moving ``c`` out twice would
    lose the sign of.
    """
    if left == right:
        return _Term(left, right, scale, unsigned)
    left_scale, left_unsigned, left_core = _core(left, known)
    right_scale, right_unsigned, right_core = _core(right, known)
    return _Term(
        left_core,
        right_core,
        _times(scale, _times(left_scale, right_scale)),
        unsigned | left_unsigned | right_unsigned,
    )


def _core(factor: Expression, known: Mapping[str, Signs]) -> tuple[Signs, frozenset[str], Expression]:
    """*factor* with its variable-free factors peeled off, and the signs and unsigned names they carried."""
    if isinstance(factor, Named):
        return _core(factor.body, known)
    if isinstance(factor, Negate):
        signs, unsigned, core = _core(factor.operand, known)
        return _negate(signs), unsigned, core
    if isinstance(factor, Multiply) and carries_variable(factor.left) != carries_variable(factor.right):
        inner, coefficient = (
            (factor.left, factor.right) if carries_variable(factor.left) else (factor.right, factor.left)
        )
        signs, unsigned, core = _core(inner, known)
        return _times(signs, _sign(coefficient, known)), unsigned | _unsigned(coefficient, known), core
    if isinstance(factor, Divide):
        signs, unsigned, core = _core(factor.numerator, known)
        return (
            _times(signs, _reciprocal(_sign(factor.divisor, known))),
            unsigned | _unsigned(factor.divisor, known),
            core,
        )
    return POSITIVE, frozenset(), factor


def _sign(node: Expression, known: Mapping[str, Signs]) -> Signs:
    """The signs variable-free *node* may take, where a parameter takes what *known* says or any."""
    if isinstance(node, Constant):
        return frozenset({_sgn(node.value)})
    if isinstance(node, Parameter):
        return known.get(node.name, ANY)
    if isinstance(node, Negate):
        return _negate(_sign(node.operand, known))
    if isinstance(node, Add):
        return _plus(_sign(node.left, known), _sign(node.right, known))
    if isinstance(node, Multiply):
        return _times(_sign(node.left, known), _sign(node.right, known))
    if isinstance(node, Divide):
        return _times(_sign(node.numerator, known), _reciprocal(_sign(node.divisor, known)))
    if isinstance(node, Power):
        return _power(_sign(node.base, known), _literal(node.exponent))
    if isinstance(node, Sum | GroupSum | WindowSum):
        return _accumulated(_sign(node.operand, known))
    if isinstance(node, Pullback | Named):
        return _sign(children(node)[0], known)
    if isinstance(node, Translate):
        signs = _sign(node.operand, known)
        return signs if node.fill is None else signs | {_sgn(node.fill)}
    if isinstance(node, Cases):
        return frozenset().union(*(_sign(region.value, known) for region in node.regions))
    if isinstance(node, Variable | Dual):
        return ANY
    assert_never(node)


def _unsigned(coefficient: Expression, known: Mapping[str, Signs]) -> frozenset[str]:
    """The parameters under *coefficient* whose sign no assumption states."""
    return frozenset(name for name in parameters_of(coefficient) if name not in known)


def _parameter_signs(program: Program) -> dict[str, Signs]:
    """Each parameter's signs, where an assumption with no ``where:`` narrows them.

    An assumption holding only where its ``where:`` admits says nothing of the
    rows it leaves out, which a term may read.
    """
    known: dict[str, Signs] = {}
    for assumption in program.assumptions.values():
        if assumption.where is not None:
            continue
        for conjunct in assumption.predicate.conjuncts:
            if (bound := _bound(conjunct)) is not None:
                name, signs = bound
                known[name] = (known.get(name, ANY) & signs) or ANY
    return known


def _bound(conjunct: Predicate) -> tuple[str, Signs] | None:
    """The parameter one conjunct compares with a number, and the signs that leaves it."""
    if isinstance(conjunct, ParameterComparison) and not isinstance(conjunct.value, str):
        return conjunct.name, _admitted(conjunct.op, conjunct.value)
    if isinstance(conjunct, ExpressionComparison):
        if isinstance(conjunct.left, Parameter) and (value := _literal(conjunct.right)) is not None:
            return conjunct.left.name, _admitted(conjunct.op, value)
        if isinstance(conjunct.right, Parameter) and (value := _literal(conjunct.left)) is not None:
            return conjunct.right.name, _admitted(_FLIPPED[conjunct.op], value)
    return None


def _admitted(op: PredicateOperator, value: float) -> Signs:
    """The signs of the numbers ``x`` for which ``x op value`` holds."""
    signs = {0} if _COMPARE[op](0.0, value) else set()
    if op in ('>=', '>', '!=') or value > 0:
        signs.add(1)
    if op in ('<=', '<', '!=') or value < 0:
        signs.add(-1)
    return frozenset(signs)


def _literal(node: Expression) -> float | None:
    """The number *node* is, where it is one — a literal, negated or named."""
    if isinstance(node, Constant):
        return node.value
    if isinstance(node, Negate):
        value = _literal(node.operand)
        return None if value is None else -value
    if isinstance(node, Named):
        return _literal(node.body)
    return None


def _names(factor: Expression) -> str:
    """The variables *factor* reads, as a sentence names them."""
    return ', '.join(f"'{name}'" for name in sorted(variables_of(factor)))


def _sgn(value: float) -> int:
    return (value > 0) - (value < 0)


def _negate(signs: Signs) -> Signs:
    return frozenset(-s for s in signs)


def _times(left: Signs, right: Signs) -> Signs:
    return frozenset(a * b for a in left for b in right)


def _reciprocal(signs: Signs) -> Signs:
    """The signs of ``1 / x``; a divisor is nonzero wherever its row is built."""
    return (signs - {0}) or ANY


def _plus(left: Signs, right: Signs) -> Signs:
    """The signs of a sum: two opposite signs may land anywhere."""
    out: set[int] = set()
    for a in left:
        for b in right:
            out |= ANY if a == -b != 0 else {a or b}
    return frozenset(out)


def _accumulated(signs: Signs) -> Signs:
    """The signs of a sum over any number of terms, none included."""
    if signs <= NON_NEGATIVE or signs <= NON_POSITIVE:
        return signs | {0}
    return ANY


def _power(base: Signs, exponent: float | None) -> Signs:
    """The signs of ``base ** exponent``: an even whole exponent drops the sign, a positive base keeps its own."""
    if exponent is not None and exponent.is_integer() and exponent % 2 == 0:
        return frozenset(abs(s) for s in base)
    if base == POSITIVE:
        return POSITIVE
    return ANY
