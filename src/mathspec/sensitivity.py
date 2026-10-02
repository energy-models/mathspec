# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""How the optimal objective moves with a parameter, written as a reported expression over the duals.

At an optimum the objective's rate of change in a parameter ``q`` is what ``q``
moves directly, plus, for every row that reads ``q``, the row's dual times how
far ``q`` raises the row's right side against its left. ``dual(c)`` is the rate
the optimal objective rises with the right side of ``c``
(``docs/reference/language/named.md``), so a row ``lhs <= rhs`` contributes
``dual(c) * d(rhs - lhs)/dq`` whatever its comparator and whatever the sense.

How far ``q`` moves a row is read off the row's tree from the root down, the
seed multiplied by each factor it passes and summed back over every dimension
the parameter does not carry. The walk spells what it multiplies by, so it
stops at an operator it cannot write back: a shift, a relation, a window, a
case.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from mathspec.dimensions import dims_of
from mathspec.errors import LanguageError, SchemaError, did_you_mean
from mathspec.program import (
    Add,
    Constant,
    Divide,
    Dual,
    Multiply,
    Named,
    Negate,
    Parameter,
    Power,
    Sum,
    Variable,
    parameters_of,
)
from mathspec.sos import section
from mathspec.validation import to_spec

if TYPE_CHECKING:
    from mathspec.program import Expression
    from mathspec.spec import Spec


def sensitivity(spec: Spec, names: tuple[str, ...]) -> Spec:
    """*spec* with ``<name>_sensitivity`` reported for each of *names*; see [`Spec.sensitivity`][mathspec.spec.Spec.sensitivity]."""
    program = spec.program
    unknown = [
        f"sensitivity: '{name}' is a given parameter, which another file declares. Ask for it on the merged "
        f'spec, where every row that reads it is.'
        if name in spec.given.parameters
        else f"sensitivity: '{name}' is not a parameter of this spec. "
        + did_you_mean(name, program.parameters, label='Parameters')
        for name in dict.fromkeys(names)
        if name not in program.parameters
    ]
    if unknown:
        raise SchemaError('\n'.join(unknown))
    raw = spec.to_dict()
    for name in dict.fromkeys(names):
        entry = f'{name}_sensitivity'
        if entry in spec.expressions:
            raise LanguageError(f"sensitivity: '{entry}' is already an expression of this spec.")
        section(raw, 'expressions')[entry] = {
            'expression': _derivative(spec, name),
            'description': f"how fast the optimal objective rises per unit of '{name}', read from the duals",
        }
    return to_spec(raw)


def _derivative(spec: Spec, name: str) -> str:
    """The rate of the optimal objective in parameter *name*, as an expression over the duals.

    Raises:
        LanguageError: No objective; a bound or an operator the walk cannot
            write back reads *name*; or nothing reads it.
    """
    program = spec.program
    if program.objective is None:
        raise LanguageError(f"sensitivity of '{name}': the spec declares no objective to differentiate.")
    if bounded := [v for v, d in program.variables.items() if name in parameters_of(*_bounds(d.lower, d.upper))]:
        raise LanguageError(
            f"sensitivity of '{name}': it bounds variable '{bounded[0]}', and a bound's price is a reduced cost, "
            f'which no expression reads. Write the bound as a constraint.'
        )
    terms = [
        term
        for term, _ in _pulled(program.objective.expression, _Seed(1, None, frozenset()), name, spec, 'the objective')
    ]
    for label, row in program.constraints.items():
        if name not in parameters_of(row.lhs, row.rhs):
            continue
        seed = _Seed(1, f'dual({label})', frozenset(row.dims))
        found = [
            *_pulled(row.rhs, seed, name, spec, f"constraint '{label}'"),
            *_pulled(row.lhs, seed.negated(), name, spec, f"constraint '{label}'"),
        ]
        if row.where is not None and any(pointwise for _, pointwise in found):
            raise LanguageError(
                f"sensitivity of '{name}': constraint '{label}' has a where:, and where it deletes a row the "
                f'dual is absent and would take the whole rate with it. Read it where no mask deletes a row.'
            )
        terms += [term for term, _ in found]
    if not terms:
        raise LanguageError(f"sensitivity of '{name}': neither the objective nor a constraint reads it.")
    return _joined(terms)


def _joined(terms: list[str]) -> str:
    """The terms as one sum, a negative term written as a subtraction."""
    text = terms[0]
    for term in terms[1:]:
        text += f' - {term[1:]}' if term.startswith('-') else f' + {term}'
    return text


@dataclass(frozen=True)
class _Seed:
    """The rate of a row in the node the walk stands at: a sign, the product so far, and the dims it carries.

    ``text`` is ``None`` while the product is still ``1``.
    """

    sign: int
    text: str | None
    carried: frozenset[str]

    def negated(self) -> _Seed:
        return replace(self, sign=-self.sign)

    def times(self, factor: str, dims: frozenset[str]) -> _Seed:
        return _Seed(self.sign, factor if self.text is None else f'{self.text} * {factor}', self.carried | dims)

    def over(self, divisor: str, dims: frozenset[str]) -> _Seed:
        return _Seed(self.sign, f'{self.text or 1} / {divisor}', self.carried | dims)

    def spelled(self, summed: list[str]) -> str:
        text = self.text or '1'
        for dim in summed:
            text = f'sum({text}, over={dim})'
        return f'-{text}' if self.sign < 0 else text


def _bounds(*bounds: Expression | None) -> tuple[Expression, ...]:
    return tuple(bound for bound in bounds if bound is not None)


def _pulled(node: Expression, seed: _Seed, name: str, spec: Spec, label: str) -> list[tuple[str, bool]]:
    """What each read of *name* under *node* contributes, summed back to *name*'s dims, and whether it was pointwise."""
    if name not in parameters_of(node):
        return []
    if isinstance(node, Parameter):
        extra = sorted(seed.carried - frozenset(spec.program.parameters[name].dims))
        return [(seed.spelled(extra), not extra)]
    if isinstance(node, Negate):
        return _pulled(node.operand, seed.negated(), name, spec, label)
    if isinstance(node, Add):
        return [*_pulled(node.left, seed, name, spec, label), *_pulled(node.right, seed, name, spec, label)]
    if isinstance(node, Multiply):
        return [
            *_pulled(node.left, _times(seed, node.right, spec, label), name, spec, label),
            *_pulled(node.right, _times(seed, node.left, spec, label), name, spec, label),
        ]
    if isinstance(node, Divide):
        if name in parameters_of(node.divisor):
            raise LanguageError(
                f"sensitivity of '{name}': {label} divides by it, which this derivation does not carry."
            )
        divided = seed.over(_factor(node.divisor, label), dims_of(node.divisor, spec, label))
        return _pulled(node.numerator, divided, name, spec, label)
    if isinstance(node, Sum):
        if clash := seed.carried & frozenset(node.over):
            raise LanguageError(
                f"sensitivity of '{name}': {label} sums over {min(clash)} inside a factor that carries it, "
                f'and the one name cannot be both.'
            )
        return _pulled(node.operand, seed, name, spec, label)
    if isinstance(node, Named):
        return _pulled(node.body, seed, name, spec, label)
    raise LanguageError(
        f"sensitivity of '{name}': {label} reads it through {type(node).__name__}, which this derivation does "
        f'not carry yet: only arithmetic and sum(over=) lie between a row and the parameter.'
    )


def _times(seed: _Seed, factor: Expression, spec: Spec, label: str) -> _Seed:
    """The seed multiplied by the other side of a product, a negated or negative factor folded into the sign."""
    sign = 1
    while isinstance(factor, Negate):
        sign, factor = -sign, factor.operand
    if isinstance(factor, Constant) and factor.value < 0:
        sign, factor = -sign, Constant(-factor.value)
    scaled = seed if sign == 1 else seed.negated()
    if isinstance(factor, Constant) and factor.value == 1:
        return scaled
    return scaled.times(_factor(factor, label), dims_of(factor, spec, label))


def _factor(node: Expression, label: str) -> str:
    """*node* spelled as one factor of a product: bare where it is a name or a number, bracketed otherwise."""
    text = _spelled(node, label)
    return text if isinstance(node, Parameter | Variable | Named | Constant | Dual | Sum) else f'({text})'


def _spelled(node: Expression, label: str) -> str:
    """*node* written back as an expression string, every operation bracketed.

    Raises:
        LanguageError: An operator other than arithmetic and ``sum(over=)``.
    """
    if isinstance(node, Constant):
        return repr(node.value) if node.value >= 0 else f'({node.value!r})'
    if isinstance(node, Parameter | Variable | Named):
        return node.name
    if isinstance(node, Dual):
        return f'dual({node.constraint})'
    if isinstance(node, Negate):
        return f'-({_spelled(node.operand, label)})'
    if isinstance(node, Add | Multiply | Divide | Power):
        left, right = (
            (node.left, node.right)
            if isinstance(node, Add | Multiply)
            else ((node.numerator, node.divisor) if isinstance(node, Divide) else (node.base, node.exponent))
        )
        symbol = {Add: '+', Multiply: '*', Divide: '/', Power: '**'}[type(node)]
        return f'({_spelled(left, label)}) {symbol} ({_spelled(right, label)})'
    if isinstance(node, Sum):
        text = _spelled(node.operand, label)
        for dim in node.over:
            text = f'sum({text}, over={dim})'
        return text
    raise LanguageError(
        f'sensitivity: {label} multiplies by a {type(node).__name__}, which this derivation cannot write back yet.'
    )
