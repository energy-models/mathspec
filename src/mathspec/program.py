# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The program: what a file declares, with names resolved and shapes fixed.

The second public state, and the one a consumer reads. A [`Program`][] is
the file typed, section for section: every entry it makes, with names
resolved, shapes fixed and every rule decidable without data checked, and no
data at all. Lowering, as a [`Spec`][mathspec.spec.Spec] loads, is the only
thing that builds one, so nothing here re-checks a hand-built one.

Node and entry classes are matched with ``isinstance``. The rules a
node's structure does not show is [`children`][]; the questions over the walk
are [`walk_regions`][], [`walk`][] and the filters beside them. A
resolved ``where`` arrives as a [`Mask`][], and what
[`advice`][mathspec.advice] says about a program as [`Advice`][]. Frozen dataclasses only — no
execution logic, and nothing imported from a consumer. How a consumer reads
one: ``docs/reference/reading.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
from functools import cached_property
from typing import TYPE_CHECKING, Literal, assert_never

from mathspec._expression_parser import Sense
from mathspec._frozen import Frozen
from mathspec.errors import did_you_mean

if TYPE_CHECKING:
    import datetime
    from collections.abc import Iterable, Iterator


__all__ = [
    'Add',
    'Advice',
    'AdviceKind',
    'And',
    'Assumption',
    'Axis',
    'BooleanLiteral',
    'Cases',
    'Column',
    'ComparisonOperator',
    'Condition',
    'ConditionReference',
    'Connective',
    'Constant',
    'Constraint',
    'ConstraintSense',
    'CountComparison',
    'DeclaredDtype',
    'Dimension',
    'DimensionComparison',
    'DimensionDtype',
    'DimensionPosition',
    'Divide',
    'Dual',
    'Expression',
    'ExpressionComparison',
    'ExpressionReference',
    'Footprint',
    'Gate',
    'Given',
    'GivenParameter',
    'GivenTargets',
    'Join',
    'JoinColumns',
    'JoinedCondition',
    'Link',
    'Mask',
    'Multiply',
    'NamedCondition',
    'NamedExpression',
    'Negate',
    'Not',
    'Objective',
    'ObjectiveSense',
    'Or',
    'Parameter',
    'ParameterComparison',
    'ParameterDefined',
    'ParameterDtype',
    'ParameterMissing',
    'ParameterReference',
    'Partition',
    'Piecewise',
    'PiecewiseMethod',
    'Power',
    'Program',
    'QuadraticPosition',
    'Reach',
    'Region',
    'Relation',
    'RelationComparison',
    'RelationDefined',
    'RelationMissing',
    'RelationPairComparison',
    'Separability',
    'Sos',
    'SosType',
    'Sum',
    'Translate',
    'TranslatedCondition',
    'TypedCondition',
    'Variable',
    'VariableDefined',
    'VariableDomain',
    'VariableMissing',
    'VariableReference',
    'WindowSum',
    'assumption_message',
    'carries_variable',
    'children',
    'condition_children',
    'is_quadratic',
    'parameters_of',
    'variables_of',
    'walk',
    'walk_regions',
]


ConstraintSense = Sense

QuadraticPosition = Literal['objective', 'constraint']
"""Where the math may contain a product of two variables: the objective or a constraint. A bound and a ``piecewise:`` link
are affine.
"""

DimensionDtype = Literal['float', 'int', 'str', 'datetime']
"""The dtypes a dimension may declare, which set what its labels are. Only a dimension may declare ``datetime``."""

ParameterDtype = Literal['float', 'int', 'bool', 'str']
"""The dtypes a parameter may declare, which set the dtype of its data column. Only a parameter may declare ``bool``."""

DeclaredDtype = ParameterDtype | DimensionDtype
"""The dtype of a name that a comparison in a condition tests. A parameter and a dimension declare it, and a relation
column has the dtype of its dimension.
"""

VariableDomain = Literal['continuous', 'integer', 'binary']
"""The domains a variable may declare."""

RelationMissing = Literal['refused', 'absent']
"""The values of ``missing:`` on a relation. Under ``refused``, a tool refuses data that leaves out a combination of the
key. Under ``absent``, that combination has no row.
"""

ParameterMissing = RelationMissing | bool | float
"""The values of ``missing:`` on a parameter: a value of [`RelationMissing`][], or the value that a missing row takes.
"""

VariableMissing = Literal['absent'] | float
"""The values of ``missing:`` on a variable. Under ``absent``, the default, a term that contains the variable has no row
where its ``where`` is false. A number is the value of the variable there, so the term takes that number and keeps its
row.
"""

ObjectiveSense = Literal['minimize', 'maximize']
"""The directions an objective may declare."""

SosType = Literal[1, 2]
"""The types of special ordered set: 1 or 2."""

PiecewiseMethod = Literal['adjacency', 'sos2', 'incremental', 'convex', 'lp']
"""The methods a ``piecewise:`` entry may declare to restrict its interpolation weights.
[`PIECEWISE_METHODS`][mathspec.spec.PIECEWISE_METHODS] lists what each method adds.
"""


# --------------------------------------------------------------------------
# Affine expressions
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Constant:
    """A scalar constant."""

    value: float
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class ParameterReference:
    """A parameter reference — contributes to the constant part."""

    name: str
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class VariableReference:
    """A variable reference — one term per existing variable row."""

    name: str
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Dual:
    """A constraint's dual — the rate the optimal objective rises with the constraint's right side, read after the solve.

    Of ``lhs <= rhs`` it is the rate in ``d`` of ``lhs <= rhs + d``, for every
    comparator and under either sense. Stands only under an
    [`NamedExpression`][] the math never reads: the loader refuses
    ``dual()`` anywhere a solver ingests. One value per coordinate of the named
    constraint's own ``dims`` frame: the leaf reshapes nothing, like a
    parameter.
    """

    constraint: str
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Negate:
    operand: Expression
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Add:
    left: Expression
    right: Expression
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Multiply:
    """Product of two operands.

    Affine where at least one factor is variable-free; degree 2 where neither
    is, which ``mathspec._degree`` admits in a [`QuadraticPosition`][] alone.
    """

    left: Expression
    right: Expression
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Power:
    """``base ** exponent``, both variable-free wherever the math reads it.

    The language refuses a variable anywhere under it (``mathspec._degree``),
    so in the program a solver sees it is degree 0 and folds to one number per
    coordinate like any other parameter arithmetic.
    """

    base: Expression
    exponent: Expression
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Divide:
    """Quotient ``numerator / divisor``, the divisor variable-free wherever the math reads it (``mathspec._degree``)."""

    numerator: Expression
    divisor: Expression
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Column:
    """One column of a relation: the relation's name, and the column's name in its entry."""

    relation: str
    name: str

    def __str__(self) -> str:
        """The column as a file writes it, ``relation[column]``."""
        return f'{self.relation}[{self.name}]'


@dataclass(frozen=True)
class Axis:
    """A position in a frame: the dimension whose labels it runs over, and the relation column it stands for.

    A declared dimension is the axis ``Axis(dimension)``. A [`Join`][]
    opens ``Axis(dimension, column)`` for each column it drops, so a column
    dropped and a column added over one dimension are two axes of one frame.
    Two axes are equal where both fields are, so a frame holds a dimension's
    own axis at most once however many join axes run over the same labels.
    """

    dimension: str
    column: Column | None = None

    def __str__(self) -> str:
        """The dimension's name, or the column's ``relation[column]`` for a join's axis."""
        return self.dimension if self.column is None else str(self.column)


@dataclass(frozen=True)
class Sum:
    """Sum ``operand`` over the axes in ``over``, removing them from the result.

    An axis in ``over`` is a dimension's own, or one a [`Join`][] under it
    opens ([`JoinColumns.axes`][]): ``sum(x, over=a, by=relation[b])``
    lowers to a ``Sum`` over a ``Join``, over the axis of each column the join
    does not group by. This node is the group-by that follows the join.
    """

    operand: Expression
    over: tuple[Axis, ...]
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Join:
    """Join ``operand`` to a relation on the columns ``columns`` joins on, one row per matching row of the relation.

    The operand carries every dim joined on. The result has the operand's
    dims, less the dims joined on, plus the dims grouped by, plus one axis
    per column joined on and not grouped by ([`JoinColumns.axes`][]), which
    stands for the relation's column and runs over its dimension. So a column
    dropped and a column added over one dimension stay two axes. A [`Sum`][] over
    those axes is the group-by that follows the join, which is how
    ``sum(x, over=a, by=relation[b])`` lowers. Where the grouped columns
    hold the relation's whole key, they determine every other column, the
    join opens no axis, and the bare ``Join`` is ``at(x,
    by=relation[a])``: one value per row of the result, fanned out where
    several key tuples share the values joined on.

    An axis is never a dim: a join that opens axes states the ``dims`` of the
    sum that closes them, and that sum removes only the dims its plain axes
    name.
    """

    operand: Expression
    columns: JoinColumns
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Translate:
    """Re-index along one dimension: the result at *t* is ``operand`` at *t - offset*.

    ``wrap`` is ``edge='wrap'`` in the file: periodic, and stated on every
    node. ``fill`` is what an acyclic shift leaves behind: ``None`` leaves the
    vacated positions absent, so the row drops; a number makes them present
    and contribute it. Always ``None`` under ``wrap``.

    ``offset`` is an integer, or the name of an integer parameter that does
    not depend on ``along`` and carries its sign in the values.

    ``partition`` is a relation with a key column over ``along``
    ([`Partition`][]), and the translation then happens inside each group
    its ``within=`` columns make: the neighbour is the one before in the same
    group, the edge is the group's, and a wrap closes each group onto itself.
    A coordinate the relation sends nowhere reaches nothing.
    """

    operand: Expression
    along: str
    offset: int | str
    wrap: bool
    fill: float | None = None
    partition: Partition | None = None
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class WindowSum:
    """Sum ``operand`` over a trailing window along one dimension.

    The result at *t* is the sum of the operand at every position from
    *t - width + 1* through *t*, so a width of 1 is the operand itself. The
    dimension survives: this replicates terms onto the positions that can see
    them rather than reducing anything away.

    ``width`` is a whole number, or the name of an integer parameter when the
    window differs per entity — a minimum up time, a rolling budget, a delivery
    horizon. A named width may not depend on the dimension being summed over.

    ``wrap`` says whether the window reaches around the start of the axis
    instead of stopping short at it, and is stated on every node.

    ``partition`` names a relation over that dimension, and the window then stops
    at each group's edge. Positions are counted inside the group, so a
    coordinate the relation places nowhere reaches nothing — not even itself.
    """

    operand: Expression
    along: str
    width: int | str
    wrap: bool
    partition: Partition | None = None
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class Region:
    """One region of a [`Cases`][]: where it applies, and the value there.

    ``when`` is stated on every region; the one the file wrote as
    ``otherwise:`` carries the negation of the others.
    """

    when: Mask
    value: Expression


@dataclass(frozen=True)
class Cases:
    """A value defined by region — exactly one region applies at each coordinate.

    The regions are disjoint and total, so a consumer adds them rather than
    ranking them. Not a shape operator: every region spans the dims the
    expression does.
    """

    regions: tuple[Region, ...]
    dims: tuple[str, ...] = field(kw_only=True)


@dataclass(frozen=True)
class ExpressionReference:
    """A use of an ``expressions:`` entry, standing where its name was written, with the entry's body under it.

    Its value is its body's: a consumer building rows steps through it, as
    [`children`][] does. It is kept as a node rather than written in so the
    typesetter can print the symbol where the name stood and define it once.
    Every use of one entry holds the one node resolution built for it, whose
    [`body`][] is the [`NamedExpression.expression`][] of that entry.
    """

    name: str
    body: Expression
    dims: tuple[str, ...] = field(kw_only=True)


Expression = (
    Constant
    | ParameterReference
    | VariableReference
    | Dual
    | Negate
    | Add
    | Multiply
    | Power
    | Divide
    | Sum
    | Join
    | Translate
    | WindowSum
    | Cases
    | ExpressionReference
)
"""The union of every expression node, which a walk over an expression takes. The set is closed, so a walk can end in
``assert_never``. Every node has ``dims``, the dimensions it is indexed over. Lowering sorts them by name, and a node
built by hand has the dims it was given. An
[`ExpressionReference`][] has the ``dims`` of its body. [`Program.roots`][], a bound and a named expression that is
``in_math`` are affine, except that at a [`QuadraticPosition`][] a [`Multiply`][] may have a variable on both sides.
"""


def children(expression: Expression) -> tuple[Expression, ...]:
    """The sub-expressions of *expression* — what every walk recurses through."""
    if isinstance(expression, ExpressionReference):
        return (expression.body,)
    if isinstance(expression, Negate):
        return (expression.operand,)
    if isinstance(expression, (Add, Multiply)):
        return (expression.left, expression.right)
    if isinstance(expression, Divide):
        return (expression.numerator, expression.divisor)
    if isinstance(expression, Power):
        return (expression.base, expression.exponent)
    if isinstance(expression, (Sum, Join, Translate, WindowSum)):
        return (expression.operand,)
    if isinstance(expression, Cases):
        return tuple(region.value for region in expression.regions)
    if isinstance(expression, (Constant, ParameterReference, VariableReference, Dual)):
        return ()
    assert_never(expression)


# --------------------------------------------------------------------------
# Entries
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Relation:
    """One declared relation: a table over its ``columns``, single-valued per ``key``.

    ``columns`` maps each role to its dimension, the key's roles first and
    each side sorted by role; ``key`` is the roles a row is
    identified by, and [`values`][] the rest — every role is a key role for
    a bare relation, which is one with no value columns. Every value is
    checked when the data is attached to be a label of its column's dimension, and the table to
    have one row per key tuple — which keeps a mistyped label from silently
    dropping its terms in the join that places them, and is what lets ``at``
    read one value.
    """

    columns: tuple[tuple[str, str], ...]
    key: tuple[str, ...]
    missing: RelationMissing = 'refused'
    """Whether every combination of the key needs a row: ``refused`` or ``absent``."""
    description: str | None = None

    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(role for role, _ in self.columns)

    @property
    def dims(self) -> tuple[str, ...]:
        """Every dimension a column is over, once, sorted by name."""
        return tuple(sorted({dim for _, dim in self.columns}))

    @property
    def values(self) -> tuple[str, ...]:
        """The roles the key determines."""
        return tuple(role for role in self.roles if role not in self.key)

    @cached_property
    def _dim_of(self) -> Mapping[str, str]:
        """Each role's dimension, built once: [`dim`][] is called per role inside loops over roles."""
        return dict(self.columns)

    def dim(self, role: str) -> str:
        return self._dim_of[role]

    def in_order(self, roles: Iterable[str]) -> tuple[str, ...]:
        """*roles* as [`columns`][] orders them: the key's first, each side sorted by role."""
        given = tuple(roles)
        return (*sorted(r for r in given if r in self.key), *sorted(r for r in given if r not in self.key))


@dataclass(frozen=True)
class JoinColumns:
    """One relation as one call joins it: the columns joined on, and the columns grouped by.

    The entry fixes no direction; the call does, and this is the one it
    named. ``name`` is the relation's, as [`Program.relations`][] keys it.
    ``joined`` and ``grouped`` are *roles*, which are column names of
    ``relation``. ``relation`` maps every role to its dimension and names the
    key. ``joined`` is
    every column the join matches the operand on: the columns that leave the
    frame, and every key column the call does not name. ``grouped`` is every
    column of the relation the result keeps: the columns that arrive, and the
    same unnamed key columns. Both are in the order of the relation's
    ``columns``: the key's first, each side sorted by role. A column in neither
    is not read, so a relation may gain a value column without changing what a
    call means.

    A column both joined on and grouped by stays in the frame. One joined on
    and not grouped by is [`dropped`][], and one grouped by and not joined
    on is [`added`][], so the frame after the call is the operand's dims,
    less the dims joined on, plus the dims grouped by.
    """

    name: str
    relation: Relation
    joined: tuple[str, ...]
    grouped: tuple[str, ...]

    def dim(self, role: str) -> str:
        """The dimension *role* ranges over."""
        return self.relation.dim(role)

    @property
    def dropped(self) -> tuple[str, ...]:
        """The roles joined on and not grouped by: what the call sums away or looks up."""
        return tuple(role for role in self.joined if role not in self.grouped)

    @property
    def added(self) -> tuple[str, ...]:
        """The roles grouped by and not joined on: what the call brings into the frame."""
        return tuple(role for role in self.grouped if role not in self.joined)

    @property
    def kept(self) -> tuple[str, ...]:
        """The roles both joined on and grouped by: the key columns the call did not name."""
        return tuple(role for role in self.joined if role in self.grouped)

    @property
    def joined_dims(self) -> tuple[str, ...]:
        return tuple(self.dim(role) for role in self.joined)

    @property
    def grouped_dims(self) -> tuple[str, ...]:
        return tuple(self.dim(role) for role in self.grouped)

    @property
    def dropped_dims(self) -> tuple[str, ...]:
        return tuple(self.dim(role) for role in self.dropped)

    @property
    def added_dims(self) -> tuple[str, ...]:
        return tuple(self.dim(role) for role in self.added)

    @property
    def one_row_per_group(self) -> bool:
        """Whether the grouped columns hold the relation's whole key, so each group is one row: a lookup, not a sum."""
        return set(self.relation.key) <= set(self.grouped)

    @property
    def axes(self) -> tuple[Axis, ...]:
        """The axis the join opens for each column it drops, empty where each group is one row.

        Each runs over the column's dimension and stands for the column, so it
        never equals that dimension's own axis. A column the grouped columns
        determine opens none: in a lookup they hold the key, and the key
        determines every column.
        """
        if self.one_row_per_group:
            return ()
        return tuple(Axis(self.dim(role), Column(self.name, role)) for role in self.dropped)


@dataclass(frozen=True)
class Partition:
    """One relation as a partition steps along it: the key column it steps along, the columns it partitions by, and the key columns it joins on.

    ``name`` is the relation's, as [`Program.relations`][] keys it.
    ``along``, ``grouped`` and ``joined`` are *roles*, which are column names
    of ``relation``. ``relation`` maps every role to its dimension and names
    the key.
    ``along`` is the one key column over the dimension stepped along, and
    the frame keeps it. ``grouped`` is the value columns ``within=`` named,
    read at the row's key: the partition's group. ``joined`` is the other key
    columns, whose dimensions the frame carries. No column is dropped and
    none is added: the frame does not change.
    """

    name: str
    relation: Relation
    along: str
    grouped: tuple[str, ...]
    joined: tuple[str, ...]

    def dim(self, role: str) -> str:
        """The dimension *role* ranges over."""
        return self.relation.dim(role)

    @property
    def along_dim(self) -> str:
        return self.dim(self.along)

    @property
    def joined_dims(self) -> tuple[str, ...]:
        return tuple(self.dim(role) for role in self.joined)


@dataclass(frozen=True)
class Dimension:
    """A dimension, as the file declares it."""

    dtype: DimensionDtype = 'str'
    """The dtype of the labels, as the file declares it. A tool checks the column of labels against it, as it checks a
    value column against ``Parameter.dtype``. It is ``str`` when the file lists the labels under ``one_of``.
    """
    one_of: tuple[str, ...] | None = None
    """The labels that the file lists under ``one_of:``, sorted by name, or ``None`` when it lists none. With data attached,
    a tool refuses any other label, in the table of the dimension and in every relation column over it.
    """
    ordered: bool = False
    """Whether the order of the labels is part of the spec. When it is, a tool keeps the labels in the order the data gives
    them.
    """
    description: str | None = None


@dataclass(frozen=True)
class Assumption:
    """A condition the file states of its data, under the name it wrote in ``assumptions:``.

    ``holds`` is true at every coordinate of its frame — the product of
    every dim the two masks name — that ``where`` admits, a missing row
    reading as false as it does in any mask. Nothing here is decidable at
    load: both sides are the data's, which is why the consumer attaching it
    checks.
    """

    holds: Mask
    where: Mask | None = None
    description: str | None = None
    """The ``description:`` that the file sets, or the sentence that a ``piecewise:`` method implies. A tool quotes it in a
    refusal, after the names of the columns, to say why the rule exists.
    """


def assumption_message(name: str, assumption: Assumption) -> str:
    """The sentence a consumer raises when the data attached to *assumption*, called *name*, fails it.

    The language's own wording, so every consumer refuses in the same words;
    a consumer appends the coordinates it saw. Where the file wrote a
    ``description:``, or a ``piecewise:`` method implied one, it trails the
    sentence: the names say which columns are wrong, and the description says
    why the rule is there.
    """
    read = ', '.join(f"'{n}'" for n in sorted(assumption.holds.names_read))
    sentence = f"assumption '{name}' does not hold for the data attached to {read}"
    return f'{sentence}: {assumption.description}' if assumption.description else sentence


@dataclass(frozen=True)
class Parameter:
    """The shape of a column; data is attached at execution time by name.

    ``dtype`` is what the entry claims the values are, and a consumer
    attaching data refuses a column that is not it — so the *entry* is
    what is read, rather than whatever the column happens to hold. It
    refuses a null or NaN value too: a coordinate with no value has no row,
    and ``inf`` is a value.
    """

    dims: tuple[str, ...]
    dtype: ParameterDtype = 'float'
    missing: ParameterMissing = 'refused'
    """What a missing row means where the parameter has coordinates, or the value it takes wherever an expression uses a
    value. A bare numeric name in a ``where`` is still true only where the data has a row.
    """
    description: str | None = None
    where: Mask | None = None
    """Where the parameter has coordinates, or ``None`` when it has every coordinate of its ``dims``. It holds each
    relation in [`on`][mathspec.program.Parameter.on] and the file's ``where:``. Where it is false, the parameter is
    absent and a tool drops its rows of data there. ``missing`` applies where it is true.
    """
    on: tuple[str, ...] = ()
    """The relations of the parameter's index set, sorted by name. A tool attaching the data refuses a row at a key
    combination one of them has no row for, before ``where`` drops anything and before ``missing`` fills anything.
    """


@dataclass(frozen=True)
class Variable:
    dims: tuple[str, ...]
    where: Mask | None = None
    """Where the variable exists, or ``None`` when it exists at every coordinate of its ``dims``. It holds each relation
    in [`on`][mathspec.program.Variable.on] and the file's ``where:``.
    """
    lower: Expression | None = None
    """A number, a parameter, or ``None`` when that side is open. An engine decides how an open side enters the model.
    """
    upper: Expression | None = None
    """As [`lower`][], for the upper side."""
    domain: VariableDomain = 'continuous'
    missing: VariableMissing = 'absent'
    description: str | None = None
    on: tuple[str, ...] = ()
    """The relations of the variable's index set, sorted by name."""


@dataclass(frozen=True)
class Given:
    """A column or a row family this program reads and does not build.

    The frame is the whole entry. A consumer looks the name up in the
    model this one is layered onto, checks the frame against what it finds,
    and refuses a name the host does not provide.
    """

    dims: tuple[str, ...]
    description: str | None = None


@dataclass(frozen=True)
class GivenParameter:
    """Data this program reads and another file declares: the frame the dim rules read, and the dtype a where compares against.

    What a missing row means is the declaring file's ``missing:``, so it is not here.
    """

    dims: tuple[str, ...]
    dtype: ParameterDtype = 'float'
    description: str | None = None


@dataclass(frozen=True)
class GivenTargets:
    """What a program reads and does not build, by kind.

    Every group is empty in a program built from one whole spec. Every group
    is frozen at construction, like every group of [`Program`][].
    """

    parameters: Mapping[str, GivenParameter] = Frozen({})
    """The parameters another file declares, by name, with the dtype that a comparison in a condition tests."""
    variables: Mapping[str, Given] = Frozen({})
    """The variables the host model provides, by name."""
    constraints: Mapping[str, Given] = Frozen({})
    """The constraints the host model builds, by name. A tool reads them back after the solver runs."""
    expressions: Mapping[str, Given] = Frozen({})
    """The named expressions the host model defines, by name."""
    conditions: Mapping[str, Given] = Frozen({})
    """The named conditions the host model defines, by name. In a condition, one is data: a [`ParameterDefined`][] of a
    boolean over its dimensions.
    """

    def __post_init__(self) -> None:
        for f in fields(self):
            object.__setattr__(self, f.name, Frozen(getattr(self, f.name)))

    def __bool__(self) -> bool:
        """Whether the program reads anything it does not build."""
        return bool(self.parameters or self.variables or self.constraints or self.expressions or self.conditions)


@dataclass(frozen=True)
class Constraint:
    """``lhs sense rhs`` for each coord combination of ``dims``.

    Either side may carry variables and constants alike; which side a
    consumer gathers them onto is its own arrangement and not stated here.
    ``where`` masks out coord combinations (row absence, like variables).
    """

    dims: tuple[str, ...]
    lhs: Expression
    sense: ConstraintSense
    rhs: Expression
    where: Mask | None = None
    description: str | None = None


@dataclass(frozen=True)
class Sos:
    """One special-ordered set per coordinate of the variable's ``dims`` minus ``along``.

    The only entry that adds neither a column nor a row: it names
    columns a consumer already has and says what may be nonzero among them. Which
    dims those are is the variable's own ``dims`` and is read from it: a
    copy here would be a second home for a fact
    ([`Program.variables`][]).
    """

    variable: str
    along: str
    sos_type: SosType
    description: str | None = None


@dataclass(frozen=True)
class Objective:
    """Objective — scalar, every reduction in it one the file wrote."""

    sense: ObjectiveSense
    expression: Expression
    description: str | None = None


@dataclass(frozen=True)
class NamedExpression:
    """A named quantity — one the math reads, or one only read back after a solve.

    ``in_math`` where the objective, a constraint or a term of a given
    expression reads it, directly or through another entry or a macro, and
    where it is such a term itself; its body then stands inside
    [`Program.roots`][] and is held to the degree rules where it is
    read. Otherwise nothing a solver sees contains it: it is a reported
    quantity, its body held to no degree, the one place a [`Dual`][] may
    stand. A bound and a ``where`` name no entry, so neither decides this.
    """

    expression: Expression
    dims: tuple[str, ...]
    """The dimensions of the entry: the ``dims:`` that an entry with cases declares, or the dimensions of the body of a
    plain entry.
    """
    in_math: bool
    description: str | None = None
    adds_to: str | None = None
    """The sum this entry adds to as a term, or ``None``."""


@dataclass(frozen=True)
class NamedCondition:
    """A named condition — a ``conditions:`` entry, read wherever a ``where``, a ``when`` or a ``holds`` names it.

    It builds nothing of its own: every use stands as a [`ConditionReference`][] with
    this condition under it, so a consumer reading a condition never looks the
    name up here.
    """

    condition: Mask
    dims: tuple[str, ...]
    """The dimensions of the condition, sorted by name."""
    description: str | None = None


@dataclass(frozen=True)
class Link:
    """One link of a ``piecewise:`` entry: an expression tied to the breakpoints a values parameter holds.

    ``name`` is the link's key in the entry, and ``<entry>_<name>`` is the row
    the expansion writes for it. ``sign`` is ``'=='`` where the link is pinned
    to the curve, and one side of it where the link is bounded by the curve
    instead. A link that walks a relation reads the curve's weights through
    it, as ``at(..., by=)`` reads an array: ``by`` is the ``relation[column]``
    the file wrote, and ``walk`` the join it resolves to. ``dims`` is the row
    the link builds: the entry's frame, or, for a walked link, that frame with
    the dims the join drops replaced by the ones it adds. ``reads`` says
    whether that row reads the entry's ``where`` through the relation, which
    it does when the mask carries every dim the join drops or keeps.
    """

    name: str
    expression: Expression
    values: str
    dims: tuple[str, ...]
    sign: ConstraintSense = '=='
    by: str | None = None
    walk: JoinColumns | None = None
    reads: bool = False

    @property
    def walks(self) -> bool:
        """Whether the link reads the curve's weights through a relation, rather than on the entry's own frame."""
        return self.walk is not None


@dataclass(frozen=True)
class Gate:
    """The variable that switches a ``piecewise:`` entry's curves on, as each curve reads it.

    ``variable`` is the variable the file named: a binary, or an integer under
    ``method: incremental``, which turns the curve off at 0 and, from 1 up,
    moves it by its point at the first breakpoint once per unit above 1.
    ``read`` is the gate at one curve: the variable on the entry's own frame,
    or the variable read through a relation, as ``at(..., by=)`` reads it.
    ``exists`` is where a curve reads the gate, and the curve is ungated
    elsewhere, its weights summing to 1; it is ``None`` where every curve
    reads it. A masked variable exists only on its mask, and a relation
    declared ``missing: absent`` may have no row for a curve, so both leave
    curves ungated; ``missing: 0`` reads the variable as 0 off its mask
    instead, which pins those curves off. Under the relation's
    ``missing: refused`` every curve has a row.
    """

    variable: str
    read: Expression
    exists: Mask | None = None


@dataclass(frozen=True)
class Piecewise:
    """A ``piecewise:`` entry as the curve it states, which [`expand`][mathspec.spec.Spec.expand] writes out as rows.

    A program of a spec that still declares one carries it here, typed; a
    program of the expanded spec carries the rows instead, under
    [`Program.variables`][] and [`Program.constraints`][], and what the
    method assumes of the breakpoints under [`Program.assumptions`][]. A
    consumer building rows takes the expanded spec.

    Attributes:
        along: The dimension each curve runs along.
        links: The links, in the order the file wrote them, each with the row
            it builds.
        method: How the weights are restricted.
        frame: The ``dims:`` the entry builds one curve per coordinate of, in
            the order the file wrote them.
        where: Which coordinates of ``frame`` have a curve — and, where it
            reads ``along`` too, how far each runs — or ``None`` where every
            coordinate has a whole curve.
        activity: The gate the weights sum to, or ``None`` where they sum
            to 1.
        description: What the file wrote under ``description:``, or ``None``.
    """

    along: str
    links: tuple[Link, ...]
    method: PiecewiseMethod
    frame: tuple[str, ...]
    where: Mask | None = None
    activity: Gate | None = None
    description: str | None = None

    @property
    def ragged(self) -> bool:
        """Whether ``where`` reads ``along``, and so says how far each curve runs rather than only which exist."""
        return self.where is not None and self.along in self.where.dims

    @property
    def curve(self) -> tuple[Link, Link]:
        """The two links as ``(x, y)``, the bounded one last. Two-link entries only."""
        x, y = self.links
        return (y, x) if x.sign != '==' else (x, y)


@dataclass(frozen=True)
class Footprint:
    """Which of the language's constructs one program uses.

    A subset, never the whole: an empty field says this program does not use
    the construct.

    Attributes:
        quadratic: Each position a product of two variable-carrying operands
            stands in; empty is affine throughout.
        domains: Every domain declared.
        sos_types: The order of each special-ordered set declared.
        kinds: Every expression node kind that appears.
    """

    quadratic: frozenset[QuadraticPosition]
    domains: frozenset[VariableDomain]
    sos_types: frozenset[SosType]
    kinds: frozenset[type[Expression]]


@dataclass(frozen=True)
class Reach:
    """One read along an axis whose distance only data can say.

    Attributes:
        label: The entry reading, as the lowering's messages label it.
        name: The parameter or relation that says how far.
        kind: An ``offset`` is a parameter's values, which
            [`Separability.resolved`][] folds in; a ``partition`` and a
            ``coordinate`` are a relation's groups, which it does not.
    """

    label: str
    name: str
    kind: Literal['offset', 'partition', 'coordinate']


@dataclass(frozen=True)
class Separability:
    """What building one dimension a window at a time asks of a driver, and what it would break.

    A rolling-horizon or myopic driver cuts an axis into windows and builds
    each on its own, and a decomposition cuts the same axis and solves each
    piece on its own. What the program can say is whether every row it builds
    is then complete inside one window: how far a row reads ahead along the
    axis, which entries tie the axis together so that no window holds
    them, and — the same fact read as a set — which rows and columns are left
    over as the border every window shares. It cannot say whether the windowed
    answer is the one a whole-horizon solve would give — a store carried over
    one row windows cleanly, and a rolling solve of it is still a different
    answer — which is the driver's design and not the spec's.

    What a row reads *behind* is not reported. A window starts where the
    driver puts it, and what its first rows meet there is the edge policy:
    the opening state a rolling horizon seeds, and the driver's to carry.

    Attributes:
        dimension: The axis asked about.
        ahead: Coordinates a window must see after its last row for every row
            it builds to be complete — what a negative ``shift`` reads. ``0``
            is pointwise; a ``shift`` of ``-2`` is ``2``.
        coupled: Each entry that ties the axis together, to what ties it
            and the one change to the spec that would not: a sum over the axis
            in a constraint, a grouping that sums it away, a wrapped
            translation, a set. No window satisfies these, and no rewrite here
            would keep the spec's meaning, so the remedy is named rather than
            applied.
        undecided: Each read along the axis whose reach only data can say —
            a named offset, a partition whose groups a window may cut, a read
            through a relation at a coordinate the data chooses.
            [`resolved`][] folds a parameter's values in.
        restarts: Each entry counting a position along the axis, which a
            window restarts at its first row. Whether that is wanted — a seed
            once per window, or once per horizon — is for the spec's author to decide, so it is
            reported rather than refused.
        linking_rows: Each constraint no one window holds whole, in entry
            order: one the axis does not index, whose row stands in every
            window, and one [`coupled`][] names. A reach the data decides is
            not one, so a row waiting on [`undecided`][] may span two windows.
        linking_columns: Each variable the axis does not index, in entry
            order, whose column every window reads. A decomposition calls a
            window a block, and with [`linking_rows`][] this is the border of
            a bordered block-diagonal form cut along the axis, whole where
            nothing is [`undecided`][] and no set runs through it. A set
            couples the axis without building a row, so it stands in neither
            field. The form is exactly that where [`ahead`][] is ``0``: a
            positive lookahead is neighbouring blocks overlapping by that much.
    """

    dimension: str
    ahead: int
    coupled: Mapping[str, str]
    undecided: tuple[Reach, ...]
    restarts: Mapping[str, str]
    linking_rows: tuple[str, ...]
    linking_columns: tuple[str, ...]

    @property
    def windowable(self) -> bool:
        """Whether every row builds complete inside a window looking [`ahead`][] past its last row.

        ``False`` while a reach is [`undecided`][], which a driver holding
        the data may resolve; [`restarts`][] do not count against it.
        """
        return not self.coupled and not self.undecided

    def resolved(self, least: Mapping[str, int]) -> Separability:
        """The same verdict with each named offset folded into [`ahead`][].

        A driver holding the data reads the least value of each parameter an
        [`undecided`][] reach names and hands it here, so the rule that
        turns a value into a reach — a negative offset reads ahead by that
        much, a positive one reads behind and asks nothing — has one home.

        Args:
            least: Parameter name to the least of its values. A reach through
                a relation — a partition, a coordinate — cannot be folded this
                way and stays undecided, as does a parameter left out.

        Raises:
            KeyError: A name no undecided reach along this axis waits on.
        """
        waiting = {reach.name for reach in self.undecided if reach.kind == 'offset'}
        for name in least:
            if name not in waiting:
                raise KeyError(
                    f"'{name}' is not a parameter that an undecided reach along '{self.dimension}' waits on. "
                    + did_you_mean(name, sorted(waiting))
                )
        folded = {reach for reach in self.undecided if reach.kind == 'offset' and reach.name in least}
        ahead = max([self.ahead, *(-least[reach.name] for reach in folded)])
        return replace(self, ahead=ahead, undecided=tuple(r for r in self.undecided if r not in folded))


@dataclass(frozen=True, kw_only=True)
class Program:
    """A complete declarative description of a mathematical program, with no data in it.

    Every group of entries is keyed by the name the file wrote, sorted by
    name, and is read-only: the mappings are wrapped at
    construction, so a consumer cannot rewrite what another consumer reads.
    Every ``dims`` and ``frame`` in it is sorted by name, whatever order the
    file writes them in. A whole program is not hashable — the entries and expression nodes
    inside it are, which is what dedup and memoisation ask for.
    """

    parameters: Mapping[str, Parameter]
    variables: Mapping[str, Variable]
    constraints: Mapping[str, Constraint]
    objective: Objective | None
    """The objective, or ``None`` when the file declares none. A solver then only tests whether the constraints can be met.
    """
    dimensions: Mapping[str, Dimension] = Frozen({})
    relations: Mapping[str, Relation] = Frozen({})
    sos: Mapping[str, Sos] = Frozen({})
    piecewise: Mapping[str, Piecewise] = Frozen({})
    """Each ``piecewise:`` entry of the spec, as the curve it states. It is empty for the program of a spec whose curves
    are expanded.
    """
    assumptions: Mapping[str, Assumption] = Frozen({})
    """What the data must satisfy, by the name that a tool quotes when it refuses data: each ``assumptions:`` entry of the
    file, then what the method of each ``piecewise:`` entry assumes of its breakpoints. mathspec checks none of them at
    load. A tool checks each when it attaches data, and refuses with [`assumption_message`][].
    """
    expressions: Mapping[str, NamedExpression] = Frozen({})
    """The ``expressions:`` that the file declares, each with whether the math uses it. None of them has a row of its own,
    and where the math uses one, it contains an [`ExpressionReference`][]. mathspec compiles every named expression, so
    it refuses at load a file whose named expression is outside the language, even one the math does not use.
    """
    conditions: Mapping[str, NamedCondition] = Frozen({})
    """The ``conditions:`` that the file declares. Each use in the program is a [`ConditionReference`][], so a tool that
    builds rows needs nothing from this mapping.
    """
    given: GivenTargets = GivenTargets()
    """What this program uses and does not build ([`GivenTargets`][]), for the host model to provide."""
    description: str | None = None
    """The ``description:`` of the file as a whole."""

    def __post_init__(self) -> None:
        """Freeze every group, so a program handed out cannot be written to."""
        for f in fields(self):
            group = getattr(self, f.name)
            if isinstance(group, Mapping):
                object.__setattr__(self, f.name, Frozen(group))

    def _by_position(self) -> Iterator[tuple[QuadraticPosition, tuple[Expression, ...]]]:
        """The row-building expressions, grouped by the position they stand in."""
        yield 'objective', (self.objective.expression,) if self.objective is not None else ()
        yield 'constraint', tuple(side for c in self.constraints.values() for side in (c.lhs, c.rhs))

    def relations_of(self, dimension: str) -> Mapping[str, Relation]:
        """The relations with a column over *dimension*, by name."""
        return Frozen({n: lk for n, lk in self.relations.items() if dimension in lk.dims})

    @property
    def roots(self) -> tuple[Expression, ...]:
        """Every tree a row is built from — the objective and both sides of each constraint.

        An [`expressions`][] entry builds no row and is not among them. Nor is
        a curve still under [`piecewise`][]: it is not a row until
        [`expand`][mathspec.spec.Spec.expand] writes it out, and its rows are in
        the program of the expansion.
        """
        return tuple(e for _, group in self._by_position() for e in group)

    @cached_property
    def footprint(self) -> Footprint:
        """Which constructs this program uses — walked once, then held.

        It answers for the rows this program holds. A curve still under
        [`piecewise`][] is not counted, so a ``sos2`` curve adds no set order
        here; ask the program of ``spec.expand('piecewise')`` for its rows.
        """
        return Footprint(
            quadratic=frozenset(
                position for position, group in self._by_position() if any(is_quadratic(e) for e in group)
            ),
            domains=frozenset(v.domain for v in self.variables.values()),
            sos_types=frozenset(s.sos_type for s in self.sos.values()),
            kinds=frozenset(type(node) for node in walk(*self.roots)),
        )

    @cached_property
    def separability(self) -> Mapping[str, Separability]:
        """Every axis, to what building it a window at a time asks and what it would break.

        The locality :doc:`the ceiling </about/ceiling>` argues in — pointwise,
        bounded halo, global — asked about the axes rather than about the
        operators, so a driver may know before it cuts a horizon whether every
        row it builds is complete inside some window.

        **A reduction means opposite things by position**, which is the whole of
        the care: in a constraint a sum over the axis ties every window to every
        other, and in the objective it is additively separable, an objective
        being a sum already.

        Every declared dimension has an entry, an axis nothing mentions being
        trivially windowable. Walked once and held, like [`footprint`][] and
        for the same reason — a program cannot change after construction — and
        answering for every axis costs what answering for one did, every
        construct that ties an axis naming the axis it ties (#248).

        It answers for the rows this program holds, as [`footprint`][] does.
        A curve still under [`piecewise`][] ties nothing here, although its
        rows sum over its breakpoint dimension; ask the program of
        ``spec.expand('piecewise')``.
        """
        from mathspec._separability import separabilities

        return Frozen(separabilities(self))


# --------------------------------------------------------------------------
# Walks, and the questions asked through them
# --------------------------------------------------------------------------


def walk_regions(*expressions: Expression) -> Iterator[tuple[Expression, tuple[Mask, ...]]]:
    """Every node under *expressions*, each with the regions it stands inside, outermost first.

    The traversal every *question* about a program is a filter of — which names
    it mentions, whether a variable stands under it, which divisions it
    contains, which rows a piece owes data at. One generator rather than that
    five-line recursion once per question: how a program is traversed is one
    fact, so a node kind [`children`][] learns to descend into reaches every
    caller at once rather than the callers that remembered.

    The regions are the ``when`` of every [`Cases`][] region the node's
    value stands under, the outermost first, which is the order the masks
    conjoin in. A node outside any ``cases:`` carries the empty tuple,
    and a ``Cases`` node carries only the regions above it, not its own. The
    tuple rather than one conjoined mask: what a consumer does with the
    regions is its own, and the conjunction is one ``&`` away.
    """
    yield from _walk_regions(expressions, ())


def _walk_regions(
    expressions: tuple[Expression, ...], above: tuple[Mask, ...]
) -> Iterator[tuple[Expression, tuple[Mask, ...]]]:
    """The recursion under [`walk_regions`][], with the regions above *expressions* carried down.

    A ``Cases`` descends by its regions rather than by [`children`][], because
    only the region pairs a value with its ``when``; every other node kind
    descends by [`children`][], which stays the one home of what sits under
    a node.
    """
    for expression in expressions:
        yield expression, above
        if isinstance(expression, Cases):
            for region in expression.regions:
                yield from _walk_regions((region.value,), (*above, region.when))
        else:
            yield from _walk_regions(children(expression), above)


def walk(*expressions: Expression) -> Iterator[Expression]:
    """Every node under *expressions*, each expression itself included, parents first.

    [`walk_regions`][] with the regions dropped, for the questions that do
    not ask where a node stands.
    """
    return (node for node, _ in walk_regions(*expressions))


def is_quadratic(expression: Expression) -> bool:
    """Whether *expression* contains a product of two variable-carrying operands.

    A structural question over the program, and unrelated consumers ask it —
    what a solver must support, which entries to build last, whether this
    form can be represented at all — so it is answered once here beside the
    other walks rather than once per consumer in its own terms.

    Whether a degree *may be written* is the language's verdict, and this is
    not a second opinion on it: by the time a program exists the question is
    which shape the expression has, and the program is what is in hand to
    answer it.
    """
    return any(
        isinstance(node, Multiply) and all(carries_variable(side) for side in (node.left, node.right))
        for node in walk(expression)
    )


def carries_variable(expression: Expression) -> bool:
    """Whether a variable appears anywhere under *expression*."""
    return any(isinstance(node, VariableReference) for node in walk(expression))


def parameters_of(*expressions: Expression) -> frozenset[str]:
    """Every parameter named anywhere under *expressions*."""
    return frozenset(node.name for node in walk(*expressions) if isinstance(node, ParameterReference))


def variables_of(*expressions: Expression) -> frozenset[str]:
    """Every variable named anywhere under *expressions*."""
    return frozenset(node.name for node in walk(*expressions) if isinstance(node, VariableReference))


# ---------------------------------------------------------------------------
# the resolved where vocabulary
# ---------------------------------------------------------------------------


ComparisonOperator = Literal['<=', '>=', '==', '!=', '<', '>']


@dataclass(frozen=True)
class BooleanLiteral:
    value: bool


@dataclass(frozen=True)
class ParameterDefined:
    """True wherever the named parameter is non-null and finite.

    ``dims`` is the parameter's own, copied off the entry during
    resolution; every leaf below that names an entry carries its dims
    (or ``over``) the same way.
    """

    name: str
    dims: tuple[str, ...]


@dataclass(frozen=True)
class VariableDefined:
    """True at the coordinates where the named variable exists."""

    name: str
    dims: tuple[str, ...]


@dataclass(frozen=True)
class ParameterComparison:
    """Compare a parameter against a literal, element-wise."""

    name: str
    op: ComparisonOperator
    value: float | str
    dims: tuple[str, ...]


@dataclass(frozen=True)
class ExpressionComparison:
    """Compare two variable-free expressions, coordinate by coordinate — ``p_min <= 0.5 * p_max``.

    ``dims`` is every dim either side carries. A side whose value is absent at
    a coordinate — a parameter row missing, a translation that vacated it —
    makes the comparison false there, as a null does in every other
    comparison; under a summing operator the absent term is one fewer.
    """

    left: Expression
    op: ComparisonOperator
    right: Expression
    dims: tuple[str, ...]


@dataclass(frozen=True)
class DimensionComparison:
    """Compare a dimension's own coordinates against a literal."""

    name: str
    op: ComparisonOperator
    value: float | str | datetime.date


@dataclass(frozen=True)
class DimensionPosition:
    """Compare where a row sits along a dimension against a position — ``position(snapshot) == 0``.

    Both sides are integers, negative counting from the end. With a
    ``partition`` the position is counted within each group the relation makes
    ([`Partition`][]), whose joined columns' dimensions the frame carries.
    """

    name: str
    op: ComparisonOperator
    position: int
    partition: Partition | None = None


@dataclass(frozen=True)
class RelationComparison:
    """Compare one value column of a keyed relation against a literal — ``period_of == 2030``.

    ``column`` is the role read, and ``dims`` the dimensions of the key
    columns: the leaf is read at them, one value per coordinate.
    """

    name: str
    column: str
    op: ComparisonOperator
    value: float | str | datetime.date
    dims: tuple[str, ...] = ()


@dataclass(frozen=True)
class RelationPairComparison:
    """Compare a value column of one keyed relation with one of another — ``from_bus != to_bus`` — row by row on the key.

    Both keys are over the same ``dims``, and the two columns are over one
    dimension, so a match is possible at all.
    """

    name: str
    column: str
    other: str
    other_column: str
    op: ComparisonOperator
    dims: tuple[str, ...] = ()


@dataclass(frozen=True)
class RelationDefined:
    """True where the relation has a row at the frame's coordinates.

    ``dims`` is what the frame supplies: the key's dimensions, whose row is
    then the one the key finds — every column's for a bare relation, where a
    row is the whole tuple.
    """

    name: str
    dims: tuple[str, ...] = ()


@dataclass(frozen=True)
class CountComparison:
    """How many coordinates *condition* admits along *over*, against a literal — ``count(points, over=bp) >= 2``.

    The count is one number per coordinate of ``dims``, which is every dim
    *condition* reads minus *over*, so a claim about each curve is written
    without saying "each curve". A condition a leaf reads arrives as a
    [`Mask`][], where a connective's operand is a bare [`Condition`][]:
    a walk recurses through the second and stops at the first.
    """

    condition: Mask
    over: str
    op: ComparisonOperator
    value: float
    dims: tuple[str, ...]


@dataclass(frozen=True)
class TranslatedCondition:
    """*operand* read ``offset`` coordinates back along one dimension — ``shift(points, along=bp, offset=1)``.

    A negative ``offset`` reads forward. Where the shift reads past the edge,
    the condition is false, as a missing row is false in any condition, so the
    file states no ``edge=``.
    """

    operand: Mask
    along: str
    offset: int
    dims: tuple[str, ...]


@dataclass(frozen=True)
class JoinedCondition:
    """*operand* read through a relation, written ``at(has_curve, by=converter_of[converter])``: a lookup [`Join`][] of a condition.

    True at a coordinate where the relation has a row and *operand* holds at
    the coordinate that row reads. False where the relation has no row, which
    is what a missing row already means in a mask. The dims ``columns``
    joins on go and the dims it groups by arrive, as a lookup
    [`Join`][]'s do.
    """

    operand: Mask
    columns: JoinColumns
    dims: tuple[str, ...]


@dataclass(frozen=True)
class Not:
    operand: Condition


@dataclass(frozen=True)
class And:
    left: Condition
    right: Condition


@dataclass(frozen=True)
class Or:
    left: Condition
    right: Condition


@dataclass(frozen=True)
class ConditionReference:
    """A use of a ``conditions:`` entry, standing where its name was written, with the entry's condition under it.

    Its truth is its body's: a consumer steps through it, as
    [`condition_children`][] does. It is kept as a node rather than written in so
    the typesetter can print the symbol where the name stood and define it
    once, as [`ExpressionReference`][] does for an expression.
    """

    name: str
    body: Condition


TypedCondition = (
    ParameterComparison
    | ExpressionComparison
    | ParameterDefined
    | VariableDefined
    | DimensionComparison
    | DimensionPosition
    | RelationComparison
    | RelationPairComparison
    | RelationDefined
    | CountComparison
    | TranslatedCondition
    | JoinedCondition
)
"""The condition nodes that refer to an entry whose kind mathspec knows at load."""

Connective = Not | And | Or
"""The boolean connectives. With [`ConditionReference`][], they are the only condition nodes that contain other condition
nodes, so a walk over a condition recurses only into these.
"""

Condition = BooleanLiteral | TypedCondition | Connective | ConditionReference
"""The union of every condition node in a program. The parser's ``Unresolved*`` nodes are not part of it, because mathspec
replaces them at load.
"""


def condition_children(condition: Condition) -> tuple[Condition, ...]:
    """The conditions under *condition* — a connective's operands, a named condition's body, and nothing under a leaf.

    What every walk over a condition recurses through, as [`children`][] is
    for an expression. A leaf has nothing under it whether or not it is
    resolved, so the grammar measures its own output with this too.
    """
    if isinstance(condition, Not):
        return (condition.operand,)
    if isinstance(condition, (And, Or)):
        return (condition.left, condition.right)
    if isinstance(condition, ConditionReference):
        return (condition.body,)
    return ()


def _atoms(where: Condition) -> Iterator[TypedCondition]:
    """Every node in *where* that reads an entry, connectives removed.

    A boolean literal yields nothing.

    Raises:
        AssertionError: An unresolved node reached the walk.
    """
    if isinstance(where, TypedCondition):
        yield where
    elif isinstance(where, BooleanLiteral | Connective | ConditionReference):
        for child in condition_children(where):
            yield from _atoms(child)
    else:
        msg = f'{type(where).__name__} reached a condition walk unresolved.'
        raise AssertionError(msg)


def _atom_dims(atom: TypedCondition) -> frozenset[str]:
    """One leaf's dims — the rule [`Mask.dims`][] is the union of.

    A parameter or variable leaf carries its own dims off the entry; a
    comparison on a dimension is read through that dimension, and a relation
    through the dimensions of the columns it is read at — its key for a
    comparison, every column for a bare existence.
    Separate from the union because the load-time frame check reports per
    leaf. Closed by ``assert_never``: a condition node added without a reading
    is a type error here, at the one place that has to grow a branch, rather
    than a wrong dim set at the first spec to use it.
    """
    match atom:
        case (
            ParameterComparison()
            | ExpressionComparison()
            | ParameterDefined()
            | VariableDefined()
            | CountComparison()
            | TranslatedCondition()
            | RelationComparison()
            | RelationPairComparison()
            | RelationDefined()
            | JoinedCondition()
        ):
            return frozenset(atom.dims)
        case DimensionComparison():
            return frozenset({atom.name})
        case DimensionPosition():
            return frozenset({atom.name, *(atom.partition.joined_dims if atom.partition is not None else ())})
        case _:
            assert_never(atom)


def _atom_names(atom: TypedCondition) -> frozenset[str]:
    """One leaf's entries, its dimension apart — the rule [`Mask.names_read`][] is the union of.

    A comparison on a dimension names no entry — a coordinate is not
    data to feed — a relation pair names both maps it compares, and a
    comparison of expressions names every parameter and relation its sides
    read, answered on the program's form of it since only a program mask is
    asked. ``assert_never``-closed for the reason [`_atom_dims`][] is: a condition
    node added without a reading is a type error at this one branch rather
    than a name silently dropped at the first spec to use it.
    """
    match atom:
        case ParameterComparison() | ParameterDefined() | VariableDefined() | RelationComparison() | RelationDefined():
            return frozenset({atom.name})
        case RelationPairComparison():
            return frozenset({atom.name, atom.other})
        case ExpressionComparison():
            return _names_under(atom.left, atom.right)
        case CountComparison():
            return atom.condition.names_read
        case TranslatedCondition():
            return atom.operand.names_read
        case JoinedCondition():
            return atom.operand.names_read | {atom.columns.name}
        case DimensionComparison() | DimensionPosition():
            return frozenset()
        case _:
            assert_never(atom)


def _names_under(*expressions: Expression) -> frozenset[str]:
    """Every parameter and relation the data has to supply for *expressions* — what a mask's ``names_read`` promises.

    [`parameters_of`][] alone misses the data an operator reads beside its
    operand: the relation a grouping or a lookup reads through, the one a
    translation or a window is partitioned by, the parameter a named offset or
    width is read from, and whatever decides which region of a cased value
    applies.
    """
    names: set[str] = set(parameters_of(*expressions))
    for node in walk(*expressions):
        if isinstance(node, Cases):
            names.update(*(region.when.names_read for region in node.regions))
        elif isinstance(node, Join):
            names.add(node.columns.name)
        elif isinstance(node, (Translate, WindowSum)):
            if node.partition is not None:
                names.add(node.partition.name)
            amount = node.offset if isinstance(node, Translate) else node.width
            if isinstance(amount, str):
                names.add(amount)
    return frozenset(names)


def _conjuncts(where: Condition) -> tuple[Condition, ...]:
    """The flatten rule behind [`Mask.conjuncts`][] — the one home of the split.

    ``a AND b AND c`` gives three, and a condition that is not an ``AND`` gives
    itself. The walk stops at the first node that is not an ``AND``: the
    conjuncts of ``a AND (b OR c)`` are ``a`` and ``b OR c``, and of
    ``NOT (a AND b)`` the single ``NOT`` — neither an ``OR`` nor a ``NOT`` is a
    claim the condition makes on its own, so neither is split.
    """
    if isinstance(where, And):
        return _conjuncts(where.left) + _conjuncts(where.right)
    return (where,)


def _fold(node: Condition) -> Condition:
    """*node* with every connective a literal or a double negation decides evaluated away.

    ``X AND True`` is ``X``, ``X OR True`` is every row, ``X AND False`` is
    none, ``NOT True`` is ``False`` and ``NOT NOT X`` is ``X``. What survives
    is a condition over data, or the one literal the whole mask reduces to —
    the invariant [`Mask`][] applies at construction, so it holds wherever
    a mask is built. A [`ConditionReference`][] is left whole: its body was folded
    when the entry was read, and refused there where it folded to a literal.
    """
    if isinstance(node, Not):
        operand = _fold(node.operand)
        if isinstance(operand, BooleanLiteral):
            return BooleanLiteral(not operand.value)
        if isinstance(operand, Not):
            return operand.operand
        return Not(operand)
    if isinstance(node, And):
        left, right = _fold(node.left), _fold(node.right)
        if isinstance(left, BooleanLiteral):
            return right if left.value else left
        if isinstance(right, BooleanLiteral):
            return left if right.value else right
        return And(left, right)
    if isinstance(node, Or):
        left, right = _fold(node.left), _fold(node.right)
        if isinstance(left, BooleanLiteral):
            return left if left.value else right
        if isinstance(right, BooleanLiteral):
            return right if right.value else left
        return Or(left, right)
    return node


def _within(node: Condition, relations: frozenset[str]) -> Condition:
    """*node* with each bare read of *relations* true, and a named condition left whole where nothing in it changes."""
    match node:
        case RelationDefined(name=name) if name in relations:
            return BooleanLiteral(value=True)
        case Not(operand=operand):
            return Not(_within(operand, relations))
        case And(left=left, right=right):
            return And(_within(left, relations), _within(right, relations))
        case Or(left=left, right=right):
            return Or(_within(left, relations), _within(right, relations))
        case ConditionReference(body=body):
            return node if (inside := _within(body, relations)) == body else inside
        case _:
            return node


@dataclass(frozen=True)
class Mask:
    """A resolved ``where`` and the questions the language answers about it.

    ``root`` is the condition a consumer dispatches on with ``isinstance``;
    every question below is derived from it. Construction folds, so a boolean
    literal stands at the root or nowhere in it, and refuses an unresolved
    tree.

    Attributes:
        root: The resolved condition the mask restricts rows by, folded.
    """

    root: Condition

    def __post_init__(self) -> None:
        object.__setattr__(self, 'root', _fold(self.root))
        _ = self.atoms  # the walk is the refusal, and runs after the fold

    @cached_property
    def atoms(self) -> tuple[TypedCondition, ...]:
        """The mask's leaves, connectives removed — the one walk the other questions read.

        Held rather than re-walked: construction takes this walk anyway, to
        refuse an unresolved tree, and a mask cannot change afterwards.
        """
        return tuple(_atoms(self.root))

    @property
    def conjuncts(self) -> tuple[Condition, ...]:
        """The conditions the mask joins with ``AND`` — its ``AND`` spine flattened, stopping at an ``OR`` or a ``NOT``."""
        return _conjuncts(self.root)

    @property
    def names_read(self) -> frozenset[str]:
        """The parameters, relations and variables the mask names."""
        return frozenset(name for atom in self.atoms for name in _atom_names(atom))

    @property
    def dims(self) -> tuple[str, ...]:
        """The dims the mask is read at, sorted by name — the union of what each leaf carries.

        Empty for a mask over nothing but literals. Read off the leaves, which
        resolution stamped with their entries' dims, so a condition built
        from resolved pieces answers exactly as an entry's own does.
        """
        return tuple(sorted({dim for atom in self.atoms for dim in _atom_dims(atom)}))

    def within(self, relations: Iterable[str]) -> Mask:
        """The mask read inside the rows of *relations*, where each of them, read at the mask's own coordinates, is true.

        A relation read anywhere else, as through ``shift`` or ``at``, is left as it is.
        """
        return Mask(_within(self.root, frozenset(relations)))

    def __invert__(self) -> Mask:
        """The mask admitting exactly the rows this one refuses — construction folds a double negation or a literal flip."""
        return Mask(Not(self.root))

    def __and__(self, other: Mask) -> Mask:
        """Both masks at once — construction absorbs a literal side rather than burying it."""
        return Mask(And(self.root, other.root))

    def __or__(self, other: Mask) -> Mask:
        """Either mask — construction absorbs a literal side rather than burying it."""
        return Mask(Or(self.root, other.root))


# --------------------------------------------------------------------------
# Advice
# --------------------------------------------------------------------------


AdviceKind = Literal['never-an-axis', 'given', 'index-set', 'unbounded']
"""The checks that an [`Advice`][] comes from. The set is closed, so a tool that filters on it can list every value."""


@dataclass(frozen=True)
class Advice:
    """One thing the language advises about a file it accepts.

    Never an error: each is what a half-written spec looks like too. A
    consumer prints it, or filters on ``kind`` and ``subject``; the text is the
    language's, so no consumer writes its own.

    Attributes:
        kind: The pass that said it.
        subject: The entry it is about — a dimension name, a variable name.
        text: The sentence, naming the rewrite.
    """

    kind: AdviceKind
    subject: str
    text: str

    def __str__(self) -> str:
        return self.text
