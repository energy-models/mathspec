# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`Program.reads` holds exactly where the model reads each `refused` parameter.

The check is differential. An oracle here builds the rows of a small model on
random data the way the absence rules say, and records every parameter
coordinate that a built row, a bound of an existing variable, the objective or
a reported expression reads. It shares no code with `mathspec.reads`, which
states the same set as a mask without data. Each mask is then evaluated on the
same data and must hold at exactly the coordinates the oracle recorded.

The oracle covers what the models below use: no partition and no piecewise.
"""

from __future__ import annotations

import copy
import itertools
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest

from mathspec import to_spec
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
    JoinedPredicate,
    Multiply,
    NamedExpression,
    NamedMask,
    Negate,
    Not,
    Or,
    Parameter,
    ParameterComparison,
    ParameterDefined,
    Power,
    Sum,
    Translate,
    Variable,
    VariableDefined,
    WindowPredicate,
    WindowSum,
    children,
)

if TYPE_CHECKING:
    from mathspec.program import Expression, Predicate, Program

LABELS: dict[str, list[Any]] = {'t': [0, 1, 2, 3, 4], 'g': ['a', 'b', 'c', 'd'], 'bus': ['n', 's', 'w']}

BASE: dict[str, Any] = {
    'dimensions': {'t': {'dtype': 'int', 'ordered': True}, 'g': {'dtype': 'str'}, 'bus': {'dtype': 'str'}},
    'relations': {'gen_bus': {'key': 'g', 'values': 'bus'}},
    'parameters': {'cap': {'dims': ['g', 't']}},
    'variables': {'x': {'dims': ['t', 'g'], 'where': 'cap > 1'}, 'y': {'dims': ['t', 'g']}},
}

Coord = dict[str, Any]


def _key(dims: tuple[str, ...], coord: Coord) -> tuple[Any, ...]:
    return tuple(coord[d] for d in dims)


@dataclass
class Data:
    """One draw of data: a table per parameter, keyed by its dims in declaration order, and the bus of each unit."""

    tables: dict[str, dict[tuple[Any, ...], float]]
    bus_of: dict[str, str]


def _draw(program: Program, seed: int) -> Data:
    """Full tables for `refused` parameters, sparse ones for `absent`; mostly zeros, so a mask leaves most rows out.

    A `refused` table is full, so the oracle can read any coordinate and record
    the read; the mask says which of them the model reads.
    """
    rng = random.Random(seed)
    tables: dict[str, dict[tuple[Any, ...], float]] = {}
    for name, declared in program.parameters.items():
        table = {}
        for key in itertools.product(*(LABELS[d] for d in declared.dims)):
            if declared.missing == 'refused' or rng.random() < 0.6:
                table[key] = float(
                    rng.randint(1, 3)
                    if declared.dtype == 'int'
                    else rng.randint(0, 1)
                    if declared.dtype == 'bool'
                    else rng.choice([0, 0, 0, 1, 2])
                )
        tables[name] = table
    return Data(tables, {g: rng.choice(LABELS['bus']) for g in LABELS['g']})


class Oracle:
    """Builds the rows of *program* on *data* by the absence rules, recording each parameter coordinate read."""

    def __init__(self, program: Program, data: Data) -> None:
        self.program = program
        self.data = data
        self.reads: dict[str, set[tuple[Any, ...]]] = {name: set() for name in program.parameters}

    # -- values: None is absence; otherwise the variable columns and the parameter coordinates a value holds --

    def value(self, e: Expression, at: Coord) -> tuple[frozenset[Any], frozenset[Any]] | None:
        match e:
            case Constant() | Dual():
                return frozenset(), frozenset()
            case Parameter(name=name):
                declared = self.program.parameters[name]
                key = _key(declared.dims, at)
                if key not in self.data.tables[name] and declared.missing == 'absent':
                    return None
                return frozenset(), frozenset({(name, key)})
            case Variable(name=name):
                declared = self.program.variables[name]
                if declared.where is None or self.holds(declared.where.root, at):
                    return frozenset({(name, _key(declared.dims, at))}), frozenset()
                return None if declared.missing == 'absent' else (frozenset(), frozenset())
            case Negate() | Add() | Multiply() | Divide() | Power():
                parts = [self.value(child, at) for child in children(e)]
                if any(part is None for part in parts):
                    return None
                columns = parts[0][0] if isinstance(e, Divide) else frozenset().union(*(p[0] for p in parts))
                return columns, frozenset().union(*(p[1] for p in parts))
            case Sum(operand=Join(operand=inner, columns=columns)) if columns.axes:
                return self.total(self.value(inner, row) for row in self.rows(columns, at, inner_frame=True))
            case Sum(operand=operand, over=over):
                summed = [axis.dimension for axis in over]
                return self.total(
                    self.value(operand, {**at, **dict(zip(summed, labels, strict=True))})
                    for labels in itertools.product(*(LABELS[d] for d in summed))
                )
            case Join(columns=columns):
                [row] = self.rows(columns, at, inner_frame=True) or [None]
                return None if row is None else self.value(e.operand, row)
            case Translate():
                source = self.shifted(e.along, at, e.offset, e.wrap)
                if source is None:
                    return None if e.fill is None else (frozenset(), self.amount_read(e.offset, at))
                found = self.value(e.operand, {**at, e.along: source})
                return None if found is None else (found[0], found[1] | self.amount_read(e.offset, at))
            case WindowSum():
                width = self.amount(e.width, at)
                sources = [self.shifted(e.along, at, k, e.wrap) for k in range(width)]
                summed = self.total(self.value(e.operand, {**at, e.along: s}) for s in sources if s is not None)
                return summed[0], summed[1] | self.amount_read(e.width, at)
            case Cases(regions=regions):
                whens = [self.holds(region.when.root, at, evaluated=True) for region in regions]
                return next((self.value(r.value, at) for r, w in zip(regions, whens, strict=True) if w), None)
            case NamedExpression(body=body):
                return self.value(body, at)
        raise AssertionError(f'the oracle does not build {type(e).__name__}')

    @staticmethod
    def total(parts: Any) -> tuple[frozenset[Any], frozenset[Any]]:
        present = [p for p in parts if p is not None]
        return frozenset().union(*(p[0] for p in present)), frozenset().union(*(p[1] for p in present))

    def amount(self, amount: int | str, at: Coord) -> int:
        if isinstance(amount, int):
            return amount
        return int(self.data.tables[amount][_key(self.program.parameters[amount].dims, at)])

    def amount_read(self, amount: int | str, at: Coord) -> frozenset[Any]:
        if isinstance(amount, int):
            return frozenset()
        return frozenset({(amount, _key(self.program.parameters[amount].dims, at))})

    def shifted(self, along: str, at: Coord, offset: int | str, wrap: bool) -> Any | None:
        """The label *offset* positions before *at* along *along*, or None past the edge."""
        labels = LABELS[along]
        i = labels.index(at[along]) - self.amount(offset, at)
        if wrap:
            return labels[i % len(labels)]
        return labels[i] if 0 <= i < len(labels) else None

    def rows(self, columns: JoinColumns, at: Coord, *, inner_frame: bool) -> list[Coord]:
        """Each row of the relation matching *at* on the grouped columns, as a coordinate of the joined side."""
        assert columns.name == 'gen_bus' and inner_frame
        table = [{'g': g, 'bus': b} for g, b in self.data.bus_of.items()]
        matching = [r for r in table if all(r[role] == at[columns.dim(role)] for role in columns.grouped)]
        return [{**at, **{columns.dim(role): r[role] for role in columns.joined}} for r in matching]

    # -- predicates over data, for the masks a model writes and the masks mathspec derives --

    def holds(self, p: Predicate, at: Coord, *, evaluated: bool = False) -> bool:
        """Whether *p* holds at *at*; where *evaluated*, the model evaluates *p* there, so each bare flag is read.

        Both sides of a connective are evaluated, as the model evaluates them.
        """
        match p:
            case BooleanLiteral(value=value):
                return value
            case And(left=left, right=right):
                sides = self.holds(left, at, evaluated=evaluated), self.holds(right, at, evaluated=evaluated)
                return all(sides)
            case Or(left=left, right=right):
                sides = self.holds(left, at, evaluated=evaluated), self.holds(right, at, evaluated=evaluated)
                return any(sides)
            case Not(operand=operand):
                return not self.holds(operand, at, evaluated=evaluated)
            case NamedMask(body=body):
                return self.holds(body, at, evaluated=evaluated)
            case ParameterComparison(name=name, op=op, value=literal):
                found = self.data.tables[name].get(_key(self.program.parameters[name].dims, at))
                return found is not None and _compare(found, op, literal)
            case ParameterDefined(name=name):
                declared = self.program.parameters[name]
                key = _key(declared.dims, at)
                if declared.dtype != 'bool':
                    return key in self.data.tables[name]
                if evaluated and declared.missing == 'refused':
                    self.reads[name].add(key)
                return bool(self.data.tables[name].get(key, 0.0))
            case VariableDefined(name=name):
                where = self.program.variables[name].where
                return where is None or self.holds(where.root, at)
            case DimensionComparison(name=name, op=op, value=literal):
                return _compare(at[name], op, literal)
            case CountComparison(predicate=predicate, over=over, op=op, value=literal):
                found = [self.holds(predicate.root, {**at, over: label}, evaluated=evaluated) for label in LABELS[over]]
                return _compare(sum(found), op, literal)
            case WindowPredicate():
                found = [
                    self.holds(p.operand.root, {**at, p.along: s}, evaluated=evaluated) for s in self.window(p, at)
                ]
                return any(found)
            case JoinedPredicate(operand=operand, columns=columns):
                [row] = self.rows(columns, at, inner_frame=True) or [None]
                return row is not None and self.holds(operand.root, row, evaluated=evaluated)
            case ExpressionComparison(left=left, op=op, right=right):
                sides = self.number(left, at), self.number(right, at)
                return None not in sides and _compare(sides[0], op, sides[1])
        raise AssertionError(f'the oracle does not evaluate {type(p).__name__}')

    def window(self, p: WindowPredicate, at: Coord) -> list[Any]:
        offset, width = self.amount(p.offset, at), self.amount(p.width, at)
        steps = range(offset, offset + width)
        labels = [self.shifted(p.along, at, -k if p.ahead else k, p.wrap) for k in steps]
        return [label for label in labels if label is not None]

    def number(self, e: Expression, at: Coord) -> float | None:
        """The value of a variable-free expression a derived mask compares, None where it is absent."""
        match e:
            case Constant(value=value):
                return value
            case Cases(regions=regions):
                return next((self.number(r.value, at) for r in regions if self.holds(r.when.root, at)), None)
            case Sum(operand=Join(operand=inner, columns=columns)) if columns.axes:
                found = [self.number(inner, row) for row in self.rows(columns, at, inner_frame=True)]
                return sum(v for v in found if v is not None)
            case Join(operand=inner, columns=columns):
                [row] = self.rows(columns, at, inner_frame=True) or [None]
                return None if row is None else self.number(inner, row)
        raise AssertionError(f'the oracle does not compute {type(e).__name__}')

    # -- the model --

    def build(self) -> None:
        program = self.program
        for constraint in program.constraints.values():
            for at in _coords(constraint.dims):
                if constraint.where is not None and not self.holds(constraint.where.root, at, evaluated=True):
                    continue
                sides = self.value(constraint.lhs, at), self.value(constraint.rhs, at)
                if None in sides or not (sides[0][0] | sides[1][0]):
                    continue
                self.record(sides[0][1] | sides[1][1])
        if program.objective is not None and (found := self.value(program.objective.expression, {})) is not None:
            self.record(found[1])
        for variable in program.variables.values():
            for at in _coords(variable.dims):
                if variable.where is not None and not self.holds(variable.where.root, at, evaluated=True):
                    continue
                for bound in (variable.lower, variable.upper):
                    if bound is not None and (found := self.value(bound, at)) is not None:
                        self.record(found[1])
        for entry in program.expressions.values():
            if not entry.in_math:
                for at in _coords(entry.dims):
                    if (found := self.value(entry.expression, at)) is not None:
                        self.record(found[1])

    def record(self, reads: frozenset[Any]) -> None:
        for name, key in reads:
            self.reads[name].add(key)


def _coords(dims: tuple[str, ...]) -> list[Coord]:
    return [dict(zip(dims, labels, strict=True)) for labels in itertools.product(*(LABELS[d] for d in dims))]


def _compare(left: Any, op: str, right: Any) -> bool:
    return {
        '<': left < right,
        '<=': left <= right,
        '>': left > right,
        '>=': left >= right,
        '==': left == right,
        '!=': left != right,
    }[op]


#: Each model reads `p` (and in some, `load` or `lead`) at one position the contract lists.
MODELS = [
    pytest.param(
        {'variables.z': {'dims': ['g'], 'where': 'p0 > 0', 'bounds': {'upper': 'p'}}},
        id='a-bound',
    ),
    pytest.param({'constraints.c': {'dims': ['t', 'g'], 'expression': 'x <= p'}}, id='a-row-over-more-dims'),
    pytest.param({'constraints.c': {'dims': ['t'], 'expression': 'sum(p * x, over=g) <= 1'}}, id='a-summand'),
    pytest.param(
        {
            'parameters.a': {'dims': ['g'], 'missing': 'absent'},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'a * y <= p'},
        },
        id='an-absent-factor',
    ),
    pytest.param(
        {'parameters.load': {'dims': ['t']}, 'constraints.c': {'dims': ['t'], 'expression': 'sum(x, over=g) >= load'}},
        id='a-row-with-no-variable-left',
    ),
    pytest.param(
        {'constraints.c': {'dims': ['t', 'g'], 'where': 'p > 0', 'expression': 'y <= 1'}}, id='only-in-a-where'
    ),
    pytest.param({'constraints.c': {'dims': ['t', 'g'], 'where': 'p0 > 0', 'expression': 'y <= p'}}, id='a-masked-row'),
    pytest.param(
        {
            'parameters.q': {'dims': ['t']},
            'constraints.c': {'dims': ['t', 'g'], 'expression': "x <= shift(q, along=t, offset=1, edge='wrap')"},
        },
        id='a-shift-that-wraps',
    ),
    pytest.param(
        {
            'parameters.q': {'dims': ['t']},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'x <= shift(q, along=t, offset=2, edge=0)'},
        },
        id='a-shift-with-an-edge',
    ),
    pytest.param(
        {
            'parameters.q': {'dims': ['t']},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'x <= shift(q, along=t, offset=-1, edge=0)'},
        },
        id='a-shift-ahead',
    ),
    pytest.param(
        {'constraints.c': {'dims': ['t', 'g'], 'expression': 'x - shift(y, along=t, offset=1) <= p'}},
        id='a-row-a-shift-vacates',
    ),
    pytest.param(
        {
            'parameters.q': {'dims': ['t']},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'x <= sum_back(q, along=t, window=3)'},
        },
        id='a-window',
    ),
    pytest.param(
        {
            'parameters.w': {'dims': ['g'], 'dtype': 'int'},
            'parameters.q': {'dims': ['t', 'g']},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'x <= sum_back(q * y, along=t, window=w)'},
        },
        id='a-named-window',
    ),
    pytest.param(
        {
            'parameters.lead': {'dims': ['g'], 'dtype': 'int'},
            'parameters.q': {'dims': ['t', 'g']},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'x <= shift(q, along=t, offset=lead, edge=0)'},
        },
        id='a-named-offset',
    ),
    pytest.param(
        {
            'parameters.price': {'dims': ['bus']},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'x <= at(price, by=gen_bus[bus])'},
        },
        id='a-lookup',
    ),
    pytest.param(
        {'constraints.c': {'dims': ['t', 'bus'], 'expression': 'sum(p * x, over=g, by=gen_bus[bus]) <= 1'}},
        id='a-sum-through-a-relation',
    ),
    pytest.param({'expressions.r': 'sum(p * x, over=[t, g])'}, id='a-reported-expression'),
    pytest.param({'objective': {'sense': 'minimize', 'expression': 'sum(p * x, over=[t, g])'}}, id='the-objective'),
    pytest.param(
        {
            'expressions.e': {
                'dims': ['t', 'g'],
                'cases': {'on': {'when': 'p0 > 0', 'expression': 'p * y'}},
                'otherwise': 'y',
            },
            'constraints.c': {'dims': ['t', 'g'], 'expression': 'e <= 1'},
        },
        id='a-case',
    ),
    pytest.param(
        {
            'variables.s': {'dims': ['t', 'g'], 'where': 'p0 > 0', 'missing': 0},
            'constraints.c': {'dims': ['t', 'g'], 'expression': 's + y <= p'},
        },
        id='a-variable-read-as-a-number',
    ),
    pytest.param(
        {
            'parameters.on': {'dims': ['g'], 'dtype': 'bool'},
            'variables.z': {'dims': ['g'], 'where': 'on', 'bounds': {'upper': 'p'}},
        },
        id='a-flag-masking-a-variable',
    ),
    pytest.param(
        {
            'parameters.on': {'dims': ['t', 'g'], 'dtype': 'bool'},
            'expressions.e': {
                'dims': ['t', 'g'],
                'cases': {'on': {'when': 'on', 'expression': 'p * x'}},
                'otherwise': 'x',
            },
            'constraints.c': {'dims': ['t', 'g'], 'where': 'p0 > 0', 'expression': 'e <= 1'},
        },
        id='a-flag-in-a-case',
    ),
    pytest.param(
        {
            'parameters.on': {'dims': ['t', 'g'], 'dtype': 'bool'},
            'constraints.c': {'dims': ['t', 'g'], 'where': 'shift(on, along=t, offset=1)', 'expression': 'y <= 1'},
        },
        id='a-flag-shifted-in-a-where',
    ),
    pytest.param(
        {
            'parameters.bus_on': {'dims': ['bus'], 'dtype': 'bool'},
            'constraints.c': {'dims': ['t', 'g'], 'where': 'at(bus_on, by=gen_bus[bus])', 'expression': 'y <= 1'},
        },
        id='a-flag-through-a-map',
    ),
    pytest.param(
        {
            'parameters.on': {'dims': ['t', 'g'], 'dtype': 'bool'},
            'variables.z': {'dims': ['g'], 'where': 'count(on, over=t) > 1', 'bounds': {'upper': 'p'}},
        },
        id='a-flag-counted',
    ),
    pytest.param(
        {'constraints.c': {'dims': ['t', 'g'], 'where': 'p0 AND p0 > 0', 'expression': 'y <= 1'}},
        id='a-guard-reads-no-number',
    ),
]


def _model(patch: dict[str, Any]) -> dict[str, Any]:
    spec = copy.deepcopy(BASE)
    spec['parameters'].update({'p': {'dims': ['g']}, 'p0': {'dims': ['g']}})
    for path, value in patch.items():
        section, _, name = path.partition('.')
        if name:
            spec.setdefault(section, {})[name] = value
        else:
            spec[section] = value
    return spec


@pytest.mark.parametrize('seed', range(12))
@pytest.mark.parametrize('patch', MODELS)
def test_a_mask_holds_where_the_model_reads_the_parameter(patch, seed):
    program = to_spec(_model(patch)).program
    data = _draw(program, seed)
    oracle = Oracle(program, data)
    oracle.build()
    for name, mask in program.reads.items():
        dims = program.parameters[name].dims
        masked = {_key(dims, at) for at in _coords(dims) if oracle.holds(mask.root, at)}
        assert masked == oracle.reads[name], (
            f"'{name}' is read at {sorted(oracle.reads[name])}, the mask says {sorted(masked)}"
        )


def test_only_refused_parameters_have_a_mask():
    """A missing row of an `absent` parameter or one that names a value is never refused, so it has no mask."""
    patch = {
        'parameters.a': {'dims': ['g'], 'missing': 'absent'},
        'parameters.v': {'dims': ['g'], 'missing': 0},
        'constraints.c': {'dims': ['t', 'g'], 'expression': 'y <= a + v + p'},
    }
    assert set(to_spec(_model(patch)).program.reads) == {'cap', 'p', 'p0'}, 'refused parameters only'


def test_a_bound_is_read_where_its_variable_exists():
    program = to_spec(_model({'variables.z': {'dims': ['g'], 'where': 'p0 > 0', 'bounds': {'upper': 'p'}}})).program
    assert program.reads['p'].root == VariableDefined('z', ('g',))


def test_a_shift_back_is_read_ahead():
    """The row at `t` reads `q` at `t - 1`, so `q` at `t` is read where the row one step ahead is built."""
    patch = {
        'parameters.q': {'dims': ['t']},
        'constraints.c': {'dims': ['t', 'g'], 'expression': "x <= shift(q, along=t, offset=1, edge='wrap')"},
    }
    root = to_spec(_model(patch)).program.reads['q'].root
    assert isinstance(root, CountComparison) and root.over == 'g'
    window = root.predicate.root
    assert isinstance(window, WindowPredicate) and window.ahead and window.offset == 1 and window.wrap
