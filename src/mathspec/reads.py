# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Where the model reads each ``refused`` parameter, as a mask a tool evaluates when it attaches the data.

The rule is ``docs/reference/language/absence.md``, *Where a parameter is
read*. Three walks decide it. Two run bottom-up, each over a node's own
frame: *present* is where absence has not removed the node's value, and
*live* is where the value still carries a variable term, because a row with
none is not built. The third runs top-down: *read* is where a node's value
goes into the model, and each operator hands it to its operand the way the
operator moved the value the other way — a shift by ``k`` steps it back by
``k``, a lookup becomes the sum that inverts it, and a sum the lookup.

Every step is a node a tool already evaluates. An expression enters a
predicate as ``> 0`` of an indicator, ``1`` where a predicate holds and ``0``
elsewhere, so a null from a vacated shift or a missing map row reads as
false there instead of spreading into the next sum.
"""

from __future__ import annotations

import datetime
from functools import reduce
from typing import TYPE_CHECKING, assert_never

from mathspec.program import (
    Add,
    And,
    BooleanLiteral,
    Cases,
    Constant,
    CountComparison,
    DimensionComparison,
    Divide,
    Dual,
    ExpressionComparison,
    Join,
    JoinColumns,
    Mask,
    Multiply,
    NamedExpression,
    Negate,
    Not,
    Or,
    Parameter,
    ParameterDefined,
    Power,
    Region,
    Sum,
    Translate,
    Variable,
    VariableDefined,
    WindowSum,
    children,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from mathspec.program import ConstraintDeclaration, Expression, Predicate, Program

_TRUE = BooleanLiteral(True)
_FALSE = BooleanLiteral(False)


def reads(program: Program) -> dict[str, Mask]:
    """Each ``refused`` parameter of *program*, to the mask over its own dims that holds where the model reads it."""
    walk = _Reads(program)
    walk.run()
    return {
        name: Mask(walk.read.get(name, _FALSE))
        for name, declared in program.parameters.items()
        if declared.missing == 'refused'
    }


def _and(*predicates: Predicate) -> Predicate:
    return Mask(reduce(And, predicates, _TRUE)).root


def _or(*predicates: Predicate) -> Predicate:
    return Mask(reduce(Or, predicates, _FALSE)).root


def _positive(expression: Expression, dims: tuple[str, ...]) -> Predicate:
    """Where *expression* is above zero, and false where it is null."""
    return ExpressionComparison(expression, '>', Constant(0.0), dims)


class _Reads:
    """The three walks over one program, each node's *present* and *live* held once it is asked.

    ``read`` gathers, per ``refused`` parameter, the OR of every leaf's read
    mask projected onto the parameter's dims.
    """

    def __init__(self, program: Program) -> None:
        self.program = program
        self.read: dict[str, Predicate] = {}
        self._order = {name: i for i, name in enumerate(program.dimensions)}
        self._frames: dict[Expression, frozenset[str]] = {}
        self._present: dict[Expression, Predicate] = {}
        self._live: dict[Expression, Predicate] = {}
        self._built: dict[str, Predicate] = {}

    def run(self) -> None:
        program = self.program
        for name, constraint in program.constraints.items():
            built = self.built(name, constraint)
            self.visit(constraint.lhs, built)
            self.visit(constraint.rhs, built)
        if program.objective is not None:
            expression = program.objective.expression
            self.visit(expression, self.present(expression))
        for name, variable in program.variables.items():
            exists = _TRUE if variable.where is None else VariableDefined(name, variable.dims)
            for bound in (variable.lower, variable.upper):
                if bound is not None:
                    self.visit(bound, exists)
        for entry in program.expressions.values():
            if not entry.in_math:
                self.visit(entry.expression, self.present(entry.expression))

    def built(self, name: str, constraint: ConstraintDeclaration) -> Predicate:
        """Where *constraint* has a row: its mask holds, absence removed neither side, and a variable term is left."""
        if name not in self._built:
            lhs, rhs = constraint.lhs, constraint.rhs
            where = _TRUE if constraint.where is None else constraint.where.root
            live = _or(self.live(lhs), self.live(rhs))
            self._built[name] = _and(where, self.present(lhs), self.present(rhs), live)
        return self._built[name]

    # -- frames ---------------------------------------------------------------

    def ordered(self, dims: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted(set(dims), key=self._order.__getitem__))

    def frame(self, e: Expression) -> frozenset[str]:
        if e not in self._frames:
            self._frames[e] = self._frame(e)
        return self._frames[e]

    def _frame(self, e: Expression) -> frozenset[str]:
        """The dims *e* is read over, as ``mathspec.dimensions.dims_of`` finds them when the file loads."""
        program, given = self.program, self.program.given
        match e:
            case Constant():
                return frozenset()
            case Parameter(name=name):
                return frozenset({**program.parameters, **given.parameters}[name].dims)
            case Variable(name=name):
                return frozenset({**program.variables, **given.variables, **given.expressions}[name].dims)
            case Dual(constraint=name):
                return frozenset({**program.constraints, **given.constraints}[name].dims)
            case NamedExpression(name=name):
                return frozenset(program.expressions[name].dims)
            case Cases(regions=regions):
                return frozenset().union(*(self.frame(r.value) | r.when.dims for r in regions))
            case Negate() | Add() | Multiply() | Divide() | Power():
                return frozenset().union(*(self.frame(child) for child in children(e)))
            case Sum(operand=Join(operand=inner, columns=columns)) if columns.axes:
                return self.joined(columns, self.frame(inner))
            case Sum(operand=operand, over=over):
                return self.frame(operand) - {axis.dimension for axis in over}
            case Join(operand=operand, columns=columns):
                return self.joined(columns, self.frame(operand))
            case Translate(operand=operand) | WindowSum(operand=operand):
                return self.frame(operand)
        assert_never(e)

    @staticmethod
    def joined(columns: JoinColumns, inner: frozenset[str]) -> frozenset[str]:
        return (inner - set(columns.joined_dims)) | set(columns.grouped_dims)

    # -- indicators -----------------------------------------------------------

    def everywhere(self, dim: str) -> Predicate:
        """True at every coordinate of *dim*, and read over it — an indicator's way to carry a dim its predicate does not read."""
        dtype = self.program.dimensions[dim].dtype
        label: float | str | datetime.date = (
            '' if dtype == 'str' else datetime.date.min if dtype == 'datetime' else 0.0
        )
        at = DimensionComparison(dim, '==', label)
        return Or(at, Not(at))

    def indicator(self, predicate: Predicate, dims: frozenset[str]) -> Expression:
        """``1`` where *predicate* holds and ``0`` elsewhere, over every dim of *dims*."""
        cover = _and(*(self.everywhere(d) for d in self.ordered(dims - Mask(predicate).dims)))
        if isinstance(predicate, BooleanLiteral):
            value = Constant(1.0 if predicate.value else 0.0)
            return value if isinstance(cover, BooleanLiteral) else Cases((Region(Mask(cover), value),))
        return Cases(
            (
                Region(Mask(_and(predicate, cover)), Constant(1.0)),
                Region(Mask(_and(Not(predicate), cover)), Constant(0.0)),
            )
        )

    def project(self, predicate: Predicate, dims: Iterable[str]) -> Predicate:
        """Where *predicate* holds at some coordinate of the dims it reads beyond *dims*."""
        for dim in self.ordered(Mask(predicate).dims - set(dims)):
            rest = self.ordered(Mask(predicate).dims - {dim})
            predicate = CountComparison(Mask(predicate), dim, '>', 0.0, rest)
        return predicate

    # -- present and live, bottom-up --------------------------------------------

    def present(self, e: Expression) -> Predicate:
        if e not in self._present:
            self._present[e] = self._presence(e)
        return self._present[e]

    def _presence(self, e: Expression) -> Predicate:
        """Where absence has not removed *e*, over its own frame."""
        program = self.program
        match e:
            case Constant() | Sum() | WindowSum():
                return _TRUE
            case Parameter(name=name):
                declared = program.parameters.get(name)
                if declared is not None and declared.missing != 'absent':
                    return _TRUE
                return ParameterDefined(name, self.ordered(self.frame(e)))
            case Variable(name=name):
                variable = program.variables.get(name)
                if variable is not None and (variable.where is None or variable.missing != 'absent'):
                    return _TRUE
                return VariableDefined(name, self.ordered(self.frame(e)))
            case Dual(constraint=name):
                constraint = program.constraints.get(name)
                return _TRUE if constraint is None else self.built(name, constraint)
            case Negate() | Add() | Multiply() | Divide() | Power():
                return _and(*(self.present(child) for child in children(e)))
            case Join(operand=operand, columns=columns):
                return self.forward_join(columns, self.present(operand), operand, e)
            case Translate():
                return self.forward_shift(e, self.present(e.operand), vacated=1.0)
            case Cases(regions=regions):
                return _or(*(_and(r.when.root, self.present(r.value)) for r in regions))
            case NamedExpression(body=body):
                return self.present(body)
        assert_never(e)

    def live(self, e: Expression) -> Predicate:
        if e not in self._live:
            self._live[e] = self._liveness(e)
        return self._live[e]

    def _liveness(self, e: Expression) -> Predicate:
        """Where *e* carries a variable term, over its own frame; presence is the caller's to add."""
        match e:
            case Constant() | Parameter() | Dual() | Power():
                return _FALSE
            case Variable(name=name):
                variable = self.program.variables.get(name)
                if variable is not None and variable.where is None:
                    return _TRUE
                return VariableDefined(name, self.ordered(self.frame(e)))
            case Negate(operand=operand):
                return self.live(operand)
            case Add(left=left, right=right) | Multiply(left=left, right=right):
                return _or(self.live(left), self.live(right))
            case Divide(numerator=numerator):
                return self.live(numerator)
            case Sum(operand=Join(operand=inner, columns=columns), over=over) if columns.axes:
                summand = _and(self.live(inner), self.present(inner))
                if isinstance(summand, BooleanLiteral) and not summand.value:
                    return _FALSE
                total = Sum(Join(self.indicator(summand, self.frame(inner)), columns), over)
                return _positive(total, self.ordered(self.frame(e)))
            case Sum(operand=operand):
                return self.project(_and(self.live(operand), self.present(operand)), self.frame(e))
            case WindowSum(operand=operand):
                summand = _and(self.live(operand), self.present(operand))
                if isinstance(summand, BooleanLiteral) and not summand.value:
                    return _FALSE
                window = WindowSum(
                    self.indicator(summand, self.frame(operand)), e.along, e.width, e.wrap, e.partition
                )
                return _positive(window, self.ordered(self.frame(e)))
            case Join(operand=operand, columns=columns):
                return self.forward_join(columns, self.live(operand), operand, e)
            case Translate():
                return self.forward_shift(e, self.live(e.operand), vacated=0.0)
            case Cases(regions=regions):
                return _or(*(_and(r.when.root, self.live(r.value)) for r in regions))
            case NamedExpression(body=body):
                return self.live(body)
        assert_never(e)

    def forward_join(self, columns: JoinColumns, predicate: Predicate, operand: Expression, e: Expression) -> Predicate:
        """*predicate* carried through a lookup, false where the map has no row."""
        if isinstance(predicate, BooleanLiteral) and not predicate.value:
            return _FALSE
        looked_up = Join(self.indicator(predicate, self.frame(operand)), columns)
        return _positive(looked_up, self.ordered(self.frame(e)))

    def forward_shift(self, e: Translate, predicate: Predicate, *, vacated: float) -> Predicate:
        """*predicate* carried through *e*; where *e* vacates, *vacated* stands if *e* has a fill, else false."""
        if isinstance(predicate, BooleanLiteral) and (not predicate.value or (e.wrap and e.partition is None)):
            return predicate
        fill = None if e.wrap or e.fill is None else vacated
        shifted = Translate(
            self.indicator(predicate, self.frame(e.operand)), e.along, e.offset, e.wrap, fill, e.partition
        )
        return _positive(shifted, self.ordered(self.frame(e)))

    # -- read, top-down ---------------------------------------------------------

    def visit(self, e: Expression, read: Predicate) -> None:
        """Hand *read*, the mask over *e*'s frame where its value goes into the model, down to every leaf under *e*."""
        if isinstance(read, BooleanLiteral) and not read.value:
            return
        match e:
            case Parameter(name=name):
                declared = self.program.parameters.get(name)
                if declared is not None and declared.missing == 'refused':
                    self.read[name] = _or(self.read.get(name, _FALSE), self.project(read, declared.dims))
            case Constant() | Variable() | Dual():
                return
            case Negate() | Add() | Multiply() | Divide() | Power():
                for child in children(e):
                    self.visit(child, read)
            case Sum(operand=Join(operand=inner, columns=columns)) if columns.axes:
                self.visit(inner, _and(self.back_join(columns, read, e, inner), self.present(inner)))
            case Sum(operand=operand):
                self.visit(operand, _and(read, self.present(operand)))
            case Join(operand=operand, columns=columns):
                self.visit(operand, self.back_join(columns, read, e, operand))
            case Translate():
                self.amount(e.offset, read)
                self.visit(e.operand, self.back_shift(e, read))
            case WindowSum():
                self.amount(e.width, read)
                self.visit(e.operand, _and(self.window_ahead(e, read), self.present(e.operand)))
            case Cases(regions=regions):
                for region in regions:
                    self.visit(region.value, _and(read, region.when.root))
            case NamedExpression(body=body):
                self.visit(body, read)
            case _:
                assert_never(e)

    def amount(self, amount: int | str, read: Predicate) -> None:
        """A named offset or width is read wherever the operator it sizes is."""
        if isinstance(amount, str):
            self.visit(Parameter(amount), read)

    def back_join(self, columns: JoinColumns, read: Predicate, e: Expression, operand: Expression) -> Predicate:
        """Where *operand* is read, given *read* over the frame of the join of it: the join with its columns swapped."""
        swapped = JoinColumns(columns.name, columns.relation, joined=columns.grouped, grouped=columns.joined)
        pulled: Expression = Join(self.indicator(read, self.frame(e)), swapped)
        if swapped.axes:
            pulled = Sum(pulled, swapped.axes)
        return _positive(pulled, self.ordered(self.frame(operand)))

    def back_shift(self, e: Translate, read: Predicate) -> Predicate:
        """Where the operand of *e* is read: *read* stepped back by the offset, and nothing past the edge."""
        if isinstance(read, BooleanLiteral) and e.wrap and e.partition is None:
            return read
        offset, reverse = (-e.offset, False) if isinstance(e.offset, int) else (e.offset, True)
        fill = None if e.wrap else 0.0
        frame = self.frame(e)
        stepped = Translate(self.indicator(read, frame), e.along, offset, e.wrap, fill, e.partition, reverse)
        return _positive(stepped, self.ordered(frame))

    def window_ahead(self, e: WindowSum, read: Predicate) -> Predicate:
        """Where the operand of *e* is read: some position of the window ahead of it is."""
        frame = self.frame(e)
        ahead = WindowSum(self.indicator(read, frame), e.along, e.width, e.wrap, e.partition, ahead=True)
        return _positive(ahead, self.ordered(frame))
