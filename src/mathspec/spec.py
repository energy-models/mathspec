# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The file: what it says, as every entry it may contain, rooted at [`Spec`][].

The first public state. A [`Spec`][] holds one file's sections as the entries
below, and [`BUILTIN_NAMES`][] is the closed set of operators an expression in
one may call. Nothing here has seen data; what the file means is its
[`program`][mathspec.spec.Spec.program].
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, ClassVar, Literal, Self, TypeVar, cast, get_args, override

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WithJsonSchema,
    WrapSerializer,
    field_validator,
    model_serializer,
    model_validator,
)

from mathspec._expression_parser import NAME, Sense
from mathspec._frozen import Frozen
from mathspec._operators import BUILTIN_NAMES
from mathspec.errors import did_you_mean, schema_error
from mathspec.program import (
    DimensionDtype,
    ObjectiveSense,
    ParameterDtype,
    PiecewiseMethod,
    Program,
    RelationMissing,
    SosType,
    VariableDomain,
)

if TYPE_CHECKING:
    from pydantic import GetJsonSchemaHandler, SerializerFunctionWrapHandler
    from pydantic.config import ExtraValues
    from pydantic_core import CoreSchema


__all__ = [
    'BUILTIN_NAMES',
    'AssumptionSpec',
    'BoundsSpec',
    'ConditionSpec',
    'ConstraintSpec',
    'Curvature',
    'DimensionSpec',
    'ExpressionCaseSpec',
    'ExpressionSpec',
    'Formulation',
    'GivenConditionSpec',
    'GivenConstraintSpec',
    'GivenExpressionSpec',
    'GivenParameterSpec',
    'GivenSpec',
    'GivenVariableSpec',
    'MacroSpec',
    'ObjectiveSpec',
    'ParameterSpec',
    'PiecewiseLinkSpec',
    'PiecewiseSpec',
    'RelationSpec',
    'SosSpec',
    'Spec',
    'VariableSpec',
]


_T = TypeVar('_T')

Listed = Annotated[tuple[_T, ...], WrapSerializer(lambda v, write: list(write(v)))]
"""A list in the file. It is a tuple once the spec loads, so nothing appends to it, and a list again in the file the
spec writes.
"""


def _sorted(names: tuple[str, ...]) -> tuple[str, ...]:
    """*names* sorted, still a tuple, so a sorted list stays as frozen as the rest of the spec."""
    return tuple(sorted(names))


Dims = Annotated[Listed[str], AfterValidator(_sorted)]
"""A ``dims:`` list, sorted by name as it loads. Its order reaches nothing a consumer reads, so the spec holds one order
for every file that states the same dimensions.
"""


def _by_name[V](entries: Mapping[str, V]) -> Frozen[str, V]:
    """*entries* sorted by name, still frozen, so the order a file lists them in reaches nothing a consumer reads."""
    return Frozen(dict(sorted(entries.items())))


ByName = Annotated[Frozen[str, _T], AfterValidator(_by_name)]
"""A mapping keyed by name, such as a section's entries, sorted by name as it loads."""


class _StrictSpec(BaseModel):
    """Base for every part of a spec: unknown keys are an error, not a shrug.

    A misspelled optional key would otherwise be dropped and its entry
    fall back to a default — ``boundz:`` leaves the variable unbounded,
    ``wher:`` leaves it unmasked — loading a spec the file does not describe.
    """

    model_config = ConfigDict(extra='forbid', frozen=True)

    _label: ClassVar[str]

    @model_serializer(mode='wrap')
    def _set_fields(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        """The fields the input set, a default it wrote out included, so a spec writes back what its file wrote.

        The canonical form dumps with ``exclude_defaults``, which leaves a
        default out whether the input set it or not.
        """
        return _as_set(self, cast('dict[str, object]', handler(self)))

    @model_validator(mode='before')
    @classmethod
    def _reject_unknown_keys(cls, data: object) -> object:
        """Name the near-miss, which is what a typo actually needs.

        pydantic's own ``extra='forbid'`` is the backstop; this runs first
        only for the wording.
        """
        if not isinstance(data, dict):
            return data
        known = set(cls.model_fields)
        unknown = [k for k in data if isinstance(k, str) and k not in known]
        if unknown:
            raise ValueError(
                '\n'.join(
                    f"unknown key '{k}' in {cls._label}. {did_you_mean(k, known, label='Valid keys')}" for k in unknown
                )
            )
        return data


Formulation = Literal['piecewise', 'sos']
"""A section of formulations: entries that [`Spec.expand`][] expands into ordinary entries."""

Curvature = Literal['convex', 'concave', 'either']
"""The shape a curve must have for a method to be exact on it, which the ``<entry>_curvature`` assumption states.
``convex`` and ``concave`` name the side that a bounded link limits. An entry with both links fixed states ``either``,
which any curve with a single bend meets.
"""

NUMERIC_DTYPES: frozenset[ParameterDtype] = frozenset({'float', 'int'})
"""The parameter dtypes that may appear where a number belongs, such as a coefficient, a term, a divisor or a bound. A
``str`` parameter is a label and a ``bool`` parameter is a condition, so neither is a number.
"""

_MISSING_SCHEMA: dict[str, object] = {
    'anyOf': [
        {'enum': list(get_args(RelationMissing))},
        {'type': 'boolean'},
        {'type': 'number'},
        {'enum': ['inf', '-inf']},
    ],
}

_VARIABLE_MISSING_SCHEMA: dict[str, object] = {'anyOf': [{'enum': ['absent']}, {'type': 'number'}]}

_WORDS = ', '.join(get_args(RelationMissing))


def _as_set(model: BaseModel, written: dict[str, object]) -> dict[str, object]:
    """*written* cut to the fields *model*'s input set, less a null and an empty mapping, which say nothing.

    An entry is a value inside a field rather than a field, so ``generator:
    {}`` and ``generator: {description: null}`` both stay as ``{}``.
    """
    return {
        key: value
        for key, value in written.items()
        if key in model.model_fields_set and value is not None and value != {}
    }


def _as_yaml(v: object) -> str:
    """*v* as the file spells it, so a refusal quotes the line the author wrote."""
    return str(v).lower() if isinstance(v, bool) else str(v)


def _missing_null(kind: str, rewrite: str) -> ValueError:
    """``missing: null`` reads as either the default or an absent row, so it is refused for the word that says which."""
    return ValueError(f'missing: null on {kind} says nothing. {rewrite}')


FORMULATIONS: tuple[Formulation, ...] = ('piecewise', 'sos')
"""Every formulation, in the order [`Spec.expand`][] expands them. A ``piecewise:`` entry may expand into an ``sos:``
entry, and an ``sos:`` entry expands into no curve.
"""


def _also_written_as(
    core_schema: CoreSchema, handler: GetJsonSchemaHandler, shorthand: Mapping[str, object]
) -> dict[str, object]:
    """The entry's own schema, widened to a *shorthand* its before-validator takes.

    A ``mode='before'`` rewrite is invisible to pydantic, which generates the
    schema from the post-rewrite fields alone, so the shorthand has to be added
    back by hand or an editor red-squiggles the form the file is written in.

    ``handler`` returns the definition itself on most versions and a ``$ref``
    to it on pydantic 2.10; the ref is followed, because an ``anyOf`` branch
    pointing at its own entry is a loop with the mapping form unreachable.
    """
    generated = handler(core_schema)
    if set(generated) == {'$ref'}:
        generated = handler.resolve_ref_schema(generated)
    return {'anyOf': [dict(generated), shorthand]}


def side_columns(written: str | Sequence[str] | Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    """``(role, dimension)`` per column of one side of a relation, in written order.

    A bare name or a list names each column after the dimension it is over; a
    mapping names the roles, which is what two columns over one dimension need.
    """
    if written is None:
        return ()
    if isinstance(written, Mapping):
        return tuple(written.items())
    return tuple((d, d) for d in ((written,) if isinstance(written, str) else written))


class RelationSpec(_StrictSpec):
    """A named relation between dimensions: the columns a row is keyed by, and the columns that key determines.

    Each side is a dimension, a list of them, or a mapping of column name to
    dimension where two columns share one. ``key:`` is the claim the language
    checks when the data is attached: one row per key tuple, so every ``values:`` column is a
    function of it. A relation with no ``values:`` is **bare** — every column is
    in its key, a row is its own identity, and nothing reads it::

        relations:
          gen_bus: {key: generator, values: bus}
          gen_bt: {key: [generator], values: [bus, technology]}
          zone_of: {key: [generator, period], values: zone}
          ends: {key: line, values: {bus0: bus, bus1: bus}}
          connection: {key: [generator, bus]}

    A sum joins the table on the columns ``over=`` names and every other key
    column, and groups by the columns ``by=relation[...]`` names. A lookup
    joins on the columns it names. The entry fixes no direction. A
    column is named after its own dimension or after none, so a name in a
    call reads the same as a column and as a dimension. The map itself is
    data, and arrives with the rest of it, under the relation's name, one
    column per role.
    """

    _label: ClassVar[str] = 'a relation entry'

    key: str | Dims | ByName[str]
    values: str | Dims | ByName[str] | None = None
    missing: RelationMissing = 'refused'
    """Whether every combination of the dimensions of the key needs a row. Under ``refused``, a tool refuses data that
    leaves one out. Under ``absent``, that combination has no row.
    """
    description: str | None = None

    @field_validator('missing', mode='before')
    @classmethod
    def _refused_or_absent(cls, v: object) -> object:
        """A label is data, so no value fills a gap in a map."""
        if v is None:
            raise _missing_null(
                'a relation', 'Write absent where a key combination may have no row, or leave the key out for refused.'
            )
        if v not in get_args(RelationMissing):
            msg = (
                f'missing: {_as_yaml(v)} on a relation, which takes refused or absent. A key combination with no '
                f'row is refused, or is not in the relation.'
            )
            raise ValueError(msg)
        return v

    @property
    def pairs(self) -> tuple[tuple[str, str], ...]:
        """``(role, dimension)`` per column, the key's columns first.

        The program calls the same thing [`columns`][mathspec.program.Relation.columns];
        here the table has no field of its own, being what the two sides make.
        """
        return (*side_columns(self.key), *side_columns(self.values))

    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(role for role, _ in self.pairs)

    @property
    def dims(self) -> tuple[str, ...]:
        return tuple(dim for _, dim in self.pairs)

    @property
    def key_roles(self) -> tuple[str, ...]:
        """The key roles, however ``key:`` was written."""
        return tuple(role for role, _ in side_columns(self.key))

    @property
    def value_roles(self) -> tuple[str, ...]:
        """The roles the key determines; empty for a bare relation."""
        return tuple(role for role, _ in side_columns(self.values))


class DimensionSpec(_StrictSpec):
    """A declared dimension, the dtype its coordinates must be, and whether their order means anything.

    A dimension is an axis and nothing else: it declares that the axis exists
    and what its coordinates are typed as. Which coordinates there are is data,
    and arrives when the data is attached; a ``one_of`` only names the labels a
    coordinate may have. The maps its members carry — a
    generator's bus, a snapshot's period — are top-level ``relations:``
    ([`RelationSpec`][]), keyed by their own name.
    """

    _label: ClassVar[str] = 'a dimension entry'

    dtype: DimensionDtype = 'str'
    one_of: (
        Annotated[Listed[str], Field(min_length=1, json_schema_extra={'uniqueItems': True}), AfterValidator(_sorted)]
        | None
    ) = None
    """The labels a ``str`` dimension allows, at least one and each once, sorted by name. At load, mathspec refuses a
    condition that compares the dimension, or a relation column over it, with any other label.
    """
    ordered: bool = False
    """Whether the order in which the data gives the labels is part of the spec. An operator may step or count only along
    an ordered dimension. On any other dimension, the order of the rows has no meaning.
    """
    description: str | None = None

    @field_validator('one_of', mode='before')
    @classmethod
    def _strings_listed_once(cls, v: object, info: ValidationInfo[object]) -> object:
        """A number or a flag in YAML is not the label its text spells, so it is refused rather than read as one.

        The dtype is checked first, so ``dtype: int`` with int labels is told to
        drop one_of rather than to quote labels that would then be refused.
        """
        if v is not None and info.data.get('dtype', 'str') != 'str':
            raise ValueError(
                f'is on a dimension of dtype {info.data["dtype"]}, and one_of takes only str labels. '
                'Write dtype: str, or leave one_of out.'
            )
        if not isinstance(v, (list, tuple)):
            return v
        if not v:
            raise ValueError('lists no label. List at least one, or leave one_of out.')
        if not_text := [label for label in v if not isinstance(label, str)]:
            shown = _as_yaml(not_text[0])
            raise ValueError(f"takes only strings, and {shown} is not one. Quote it: '{shown}'.")
        if twice := sorted({label for label in v if v.count(label) > 1}):
            raise ValueError(f'lists {twice[0]!r} twice. List each label once.')
        return v


class ParameterSpec(_StrictSpec):
    """A declared parameter with dims and dtype, the coordinates it has, and what a missing row of its data means."""

    _label: ClassVar[str] = 'a parameter entry'

    dims: Dims
    dtype: ParameterDtype = 'float'
    where: str | None = None
    """The condition that limits the coordinates of the parameter, in the condition grammar. Where it is false, the
    parameter is absent and a tool drops its rows of data there. ``missing:`` applies where it is true.
    """
    missing: Annotated[RelationMissing | bool | int | float, WithJsonSchema(_MISSING_SCHEMA)] = 'refused'
    description: str | None = None

    @field_validator('missing', mode='before')
    @classmethod
    def _a_reading_or_a_value(cls, v: object, info: ValidationInfo[object]) -> object:
        """``inf`` is a string to YAML and a number to the expression grammar, so it is taken as the number.

        A number on a float parameter loads as a float, so ``1`` and ``1.0`` are one spec and write one text.
        """
        if v is None:
            raise _missing_null(
                'a parameter', 'Write absent for a row that is not there, or leave the key out for refused.'
            )
        if v in ('inf', '-inf'):
            return float(cast('str', v))
        if isinstance(v, str) and v not in get_args(RelationMissing):
            msg = f'missing is the string {v!r}. It takes {_WORDS}, or a value: a number, true or false.'
            raise ValueError(msg)
        if isinstance(v, float) and math.isnan(v):
            msg = 'missing is nan, and a parameter has no nan value. Write a number, or one of ' + _WORDS + '.'
            raise ValueError(msg)
        if info.data.get('dtype') == 'float' and isinstance(v, int) and not isinstance(v, bool):
            return float(v)
        return v

    @model_validator(mode='after')
    def _a_value_fits_the_dtype(self) -> ParameterSpec:
        """A value fills rows of the column, so it has the column's dtype, and a label has none."""
        v = self.missing
        if self.dtype == 'str' and not isinstance(v, str):
            msg = f'missing: {_as_yaml(v)} on a str parameter, which takes refused or absent. A label has no value to fill.'
            raise ValueError(msg)
        if isinstance(v, str):
            return self
        if self.dtype == 'bool' and not isinstance(v, bool):
            msg = f'missing: {_as_yaml(v)} on a bool parameter, which takes true or false.'
            raise ValueError(msg)
        if self.dtype != 'bool' and isinstance(v, bool):
            msg = f'missing: {_as_yaml(v)} on a {self.dtype} parameter, which takes a number. Write 1 or 0.'
            raise ValueError(msg)
        if self.dtype == 'int' and isinstance(v, float):
            msg = f'missing: {_as_yaml(v)} on an int parameter, which takes an integer. Write one, or declare dtype: float.'
            raise ValueError(msg)
        return self


class BoundsSpec(_StrictSpec):
    """Variable bounds — each side is a finite number, a parameter name, or ``None`` where it is open.

    An omitted bound leaves the variable unbounded on that side, not
    implicitly non-negative. An infinity is refused: an open side is ``null``,
    and the other infinity leaves no value at all.
    """

    _label: ClassVar[str] = "a variable's 'bounds:'"

    lower: float | str | None = None
    upper: float | str | None = None

    @field_validator('lower', 'upper', mode='before')
    @classmethod
    def _a_number_or_a_name(cls, v: object, info: ValidationInfo[object]) -> object:
        if isinstance(v, bool):
            msg = f'bounds.{info.field_name} is a boolean. Write a number or a parameter name.'
            raise ValueError(msg)
        if isinstance(v, float) and math.isnan(v):
            msg = f'bounds.{info.field_name} is nan, which no value compares to. Write a number, or omit the bound.'
            raise ValueError(msg)
        if isinstance(v, float | int) and math.isinf(v):
            msg = f'bounds.{info.field_name} is {v}. For an open side, write {info.field_name}: null or leave it out.'
            raise ValueError(msg)
        return v

    @model_validator(mode='after')
    def _literals_do_not_cross(self) -> BoundsSpec:
        """Two numbers that leave no value between them are refused; a named bound is data."""
        if isinstance(self.lower, float) and isinstance(self.upper, float) and self.lower > self.upper:
            msg = (
                f'bounds.lower {self.lower} is above bounds.upper {self.upper}, so no value satisfies them. '
                f'Swap them, or drop one.'
            )
            raise ValueError(msg)
        return self


class VariableSpec(_StrictSpec):
    """A declared decision variable."""

    _label: ClassVar[str] = 'a variable entry'

    dims: Dims
    where: str | None = None
    bounds: BoundsSpec = BoundsSpec()
    domain: VariableDomain = 'continuous'
    missing: Annotated[Literal['absent'] | float, WithJsonSchema(_VARIABLE_MISSING_SCHEMA)] = 'absent'
    description: str | None = None

    @field_validator('missing', mode='before')
    @classmethod
    def _absent_or_a_number(cls, v: object, info: ValidationInfo[object]) -> object:
        """A variable has no data, so ``refused`` does not apply to it, and only a finite number can stand for it.

        The number stands for the variable where its mask leaves it out, so a mask must leave something out. The number
        lies in the variable's domain. The bounds hold only inside the mask, so the number may lie outside them. It
        loads as a float, as a bound does, so ``0`` and ``0.0`` are one spec. The checks run on the number as written,
        so a refusal quotes it, and skip a ``where:`` or ``domain:`` that failed to load.
        """
        if v is None:
            raise _missing_null('a variable', 'Write a number, or leave the key out for absent.')
        if v == 'absent':
            return v
        if not isinstance(v, int | float) or isinstance(v, bool) or not math.isfinite(v):
            msg = (
                f'missing: {_as_yaml(v)} on a variable, which takes absent or a finite number. A variable has no '
                f'data, so refused and a flag apply only to a parameter.'
            )
        elif 'where' in info.data and info.data['where'] is None:
            msg = (
                f'missing: {_as_yaml(v)} needs a `where:`. A variable with no `where:` exists at every '
                f'coordinate of its dimensions, so no coordinate is missing. Add a `where:`, or delete `missing:`.'
            )
        elif info.data.get('domain') == 'binary' and v not in (0, 1):
            msg = f'missing: {_as_yaml(v)} on a binary variable, which takes 0 or 1.'
        elif info.data.get('domain') == 'integer' and not float(v).is_integer():
            msg = f'missing: {_as_yaml(v)} on an integer variable, which takes an integer.'
        else:
            return float(v)
        raise ValueError(msg)


class _GivenEntrySpec(_StrictSpec):
    """Base for a ``given:`` entry, which writes the fields its file wrote and no more.

    A reading may say less than the entry it reads, so a field left out is no
    claim, where the same field at its default is one. Writing the default out
    would make ``to_spec(spec.to_dict())`` read the name as saying more than
    the file did, and [`merge`][mathspec.merge] would compare that instead.
    """


class GivenParameterSpec(_GivenEntrySpec):
    """Data this file reads and another file declares.

    It says the frame and the dtype of a [`ParameterSpec`][], which are what
    this file reads: a condition compares against the dtype, and the dim rules read
    the frame. What a missing row means is the declaring file's ``missing:``.
    """

    _label: ClassVar[str] = 'a given parameter entry'

    dims: Dims
    dtype: ParameterDtype = 'float'
    description: str | None = None


class GivenVariableSpec(_GivenEntrySpec):
    """A column this file reads and another file introduces.

    The frame and the domain are all this file states. The file that introduces
    the column owns its bounds and its mask.
    """

    _label: ClassVar[str] = 'a given variable entry'

    dims: Dims
    domain: VariableDomain = 'continuous'
    description: str | None = None


class GivenConstraintSpec(_GivenEntrySpec):
    """A row family this file reads the dual of and another model builds.

    The frame says how many duals there are and what indexes them, which is
    what ``dual()`` needs. There is no ``expression:``, because nothing here
    builds a row.
    """

    _label: ClassVar[str] = 'a given constraint entry'

    dims: Dims
    description: str | None = None


class GivenExpressionSpec(_GivenEntrySpec):
    """A named expression this file reads and another file defines.

    The frame is all this file states. This file reads the name as a quantity
    over that frame, affine in the columns, as it reads a given variable: the
    body is the definer's, and the composed spec holds the body to the rules
    of every place this file reads it.

    A named expression of this file may add to the name with ``adds_to:``.
    [`merge`][mathspec.merge] then writes every term the files
    add after the body a file defines, or as the whole body where no file
    defines it. The file itself reads the name as the whole sum, alone and
    composed.
    """

    _label: ClassVar[str] = 'a given expression entry'

    dims: Dims
    description: str | None = None


class GivenConditionSpec(_GivenEntrySpec):
    """A named condition this file reads and another file defines.

    The frame is all this file states, and it names the dims the definer's
    condition reads. A condition reads the name as data over that frame, true or false at each coordinate, since a condition reads nothing
    a solve decides: the condition is the definer's.
    """

    _label: ClassVar[str] = 'a given condition entry'

    dims: Dims
    description: str | None = None


class GivenSpec(_StrictSpec):
    """What this file reads and does not build, by kind. Closed at the five kinds."""

    _label: ClassVar[str] = "the 'given:' section"

    parameters: ByName[GivenParameterSpec] = Frozen({})
    """The parameters another file declares ([`GivenParameterSpec`][])."""
    variables: ByName[GivenVariableSpec] = Frozen({})
    """The variables another file declares ([`GivenVariableSpec`][])."""
    constraints: ByName[GivenConstraintSpec] = Frozen({})
    """The constraints another model builds ([`GivenConstraintSpec`][])."""
    expressions: ByName[GivenExpressionSpec] = Frozen({})
    """The named expressions another file defines ([`GivenExpressionSpec`][])."""
    conditions: ByName[GivenConditionSpec] = Frozen({})
    """The named conditions another file defines ([`GivenConditionSpec`][])."""

    def __bool__(self) -> bool:
        """Whether the file reads anything it does not build."""
        return bool(self.parameters or self.variables or self.constraints or self.expressions or self.conditions)


class ConstraintSpec(_StrictSpec):
    """A declared constraint: one rule, over one frame."""

    _label: ClassVar[str] = 'a constraint entry'

    dims: Dims
    where: str | None = None
    expression: str
    description: str | None = None


class ObjectiveSpec(_StrictSpec):
    """A declared objective function."""

    _label: ClassVar[str] = 'an objective entry'

    sense: ObjectiveSense = 'minimize'
    expression: str
    description: str | None = None


class MacroSpec(_StrictSpec):
    """A parameterised expression template, defined in the YAML itself.

    Language, not code: formals (``args`` positional, ``kwargs`` keyword)
    shadow the spec's names inside the template, and every call site expands in
    the syntax tree before resolution reads the expression.
    """

    _label: ClassVar[str] = 'a macro entry'

    args: Listed[str] = ()
    kwargs: Annotated[Listed[str], AfterValidator(_sorted)] = ()
    """The keyword arguments, sorted by name as the spec loads. A call passes each one by name, so their order has no
    meaning.
    """
    template: str
    description: str | None = None

    @model_validator(mode='after')
    def _check_formals(self) -> MacroSpec:
        formals = [*self.args, *self.kwargs]
        if twice := sorted({formal for formal in formals if formals.count(formal) > 1}):
            msg = f'formal {twice[0]!r} is named twice. Give each formal its own name.'
            raise ValueError(msg)
        return self


def _number_is_an_expression(value: object) -> object:
    """``expression: 0`` is how a file writes a constant — YAML reads it as an int.

    Booleans are left to fail: ``true`` is not arithmetic, and an error naming
    the type reads better than one naming ``'True'``.
    """
    return str(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value


Expression = Annotated[str, BeforeValidator(_number_is_an_expression, json_schema_input_type=str | float)]
"""An expression as a string, or a number in its place."""


class ExpressionCaseSpec(_StrictSpec):
    """One region of a named expression: the value, and when it is the value.

    Every case says where it applies. The value wherever none of them does is
    the entry's ``otherwise:``, which is written outside ``cases:`` because it
    is not a region like these — it is what is left::

        cases:
          opening: { when: "position(snapshot) == 0", expression: p_max }
        otherwise: 0
    """

    _label: ClassVar[str] = 'an expression case'

    when: str
    expression: Expression


class ExpressionSpec(_StrictSpec):
    """A named quantity: one arithmetic expression, referenced by the math or read back after a solve.

    Written in YAML as a bare string, or as a mapping once it carries a
    ``description:`` — and serialised back to whichever form it was written in,
    so a round trip through [`Spec.to_yaml`][] reproduces the file::

        expressions:
          total_generation: sum(p, over=generator)
          emissions:
            expression: sum(p * rate, over=generator)
            description: CO2 released, the quantity the cap bounds

    ``dims:`` gives the dimensions over which the quantity is indexed. A plain
    entry may leave it out, and its expression then decides them. A declared
    ``dims:`` gives exactly the dimensions over which the expression is
    indexed: an expression indexed over a dimension ``dims:`` does not give is
    refused, and so is a ``dims:`` that gives one over which the expression is
    not indexed. A quantity whose value varies by region is
    written as ``cases:`` over a declared ``dims:``, with an ``otherwise:``
    for the rest — see the language reference.

    ``adds_to:`` adds this entry as a term to the sum it names, a
    ``given: expressions:`` entry of this file: a write, where the given entry
    is the read.
    [`merge`][mathspec.merge] adds every term to that name by
    name, after the body a file defines where one does. The term is read over at most the
    frame the given entry states, and does not read the name it adds to.
    """

    _label: ClassVar[str] = 'an expression entry'

    expression: Expression | None = None
    dims: Dims | None = None
    """The dimensions of the expression, sorted by name. An entry with ``cases:`` requires it, and a plain entry without
    it takes the dimensions of its body.
    """
    cases: Annotated[Mapping[str, ExpressionCaseSpec], Field(min_length=1), AfterValidator(_by_name)] = Frozen({})
    """The cases, by the name of the row each prints, sorted by that name. mathspec proves at load that no two ``when``
    conditions overlap, so their order has no meaning.
    """
    otherwise: Expression | None = None
    """The value wherever the ``when`` of no case is true, printed as the last row."""
    adds_to: str | None = None
    """The sum this entry adds to as a term: a ``given: expressions:`` entry of this file, or ``None``."""
    description: str | None = None

    @model_validator(mode='before')
    @classmethod
    def _from_string(cls, data: object) -> object:
        return {'expression': data} if isinstance(data, str) else data

    @model_validator(mode='after')
    def _one_form_or_the_other(self) -> Self:
        """One ``expression:``, or ``cases:`` with the ``otherwise:`` and ``dims:`` they need."""
        if self.cases and self.expression is not None:
            msg = 'the named expression has both `expression:` and `cases:`. Keep one of them.'
            raise ValueError(msg)
        if not self.cases and self.expression is None:
            msg = (
                'the named expression has neither `expression:` nor `cases:`. Write one of them, or declare '
                "it under 'given: expressions:' if other files add terms to it with `adds_to:`."
            )
            raise ValueError(msg)
        if self.cases and self.dims is None:
            msg = '`cases:` needs a `dims:`. Add `dims:` with the dimensions the cases range over.'
            raise ValueError(msg)
        if self.cases and self.otherwise is None:
            msg = '`cases:` needs an `otherwise:`. Add `otherwise:` with the value where no `when` holds.'
            raise ValueError(msg)
        if self.otherwise is not None and not self.cases:
            msg = '`otherwise:` needs `cases:`. For one value everywhere, write `expression:` instead.'
            raise ValueError(msg)
        return self

    @classmethod
    @override
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, object]:
        """The published schema admits the bare string the one-line form is written as."""
        return _also_written_as(core_schema, handler, {'type': 'string'})

    @model_serializer
    def _as_written(self) -> str | dict[str, object]:
        if self.cases:
            written: dict[str, object] = {'dims': list(self.dims or [])}
            if self.description is not None:
                written['description'] = self.description
            written['cases'] = {name: case.model_dump() for name, case in self.cases.items()}
            written['otherwise'] = self.otherwise
        elif self.expression is not None and self.description is None and self.dims is None and self.adds_to is None:
            return self.expression
        else:
            written = {'dims': list(self.dims)} if self.dims is not None else {}
            written['expression'] = self.expression
            if self.description is not None:
                written['description'] = self.description
        if self.adds_to is not None:
            written['adds_to'] = self.adds_to
        return written


class ConditionSpec(_StrictSpec):
    """A named condition: one condition, read wherever a ``where:``, a ``when:`` or a ``holds:`` names it.

    Written in YAML as a bare string, or as a mapping once it carries a
    ``description:``, and serialised back to whichever form it was written in::

        conditions:
          committable: "Generator_committable AND Generator_active"
          stands:
            condition: build_year <= period_year AND period_year < build_year + lifetime
            description: the generator stands in this period

    Its bare name in another condition stands for it, inside ``count``,
    ``shift`` and ``at`` too. Its frame is the dims its condition reads, so
    it declares none. It is true or false, so it is never a value in an
    expression.
    """

    _label: ClassVar[str] = 'a condition entry'

    condition: str
    """The condition, in the condition grammar."""
    description: str | None = None

    @model_validator(mode='before')
    @classmethod
    def _from_string(cls, data: object) -> object:
        return {'condition': data} if isinstance(data, str) else data

    @classmethod
    @override
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, object]:
        """The published schema admits the bare string the one-line form is written as."""
        return _also_written_as(core_schema, handler, {'type': 'string'})

    @model_serializer
    def _as_written(self) -> str | dict[str, object]:
        if self.description is None:
            return self.condition
        return {'condition': self.condition, 'description': self.description}


class AssumptionSpec(_StrictSpec):
    """What the spec assumes of its data: a condition every coordinate it is checked at has to satisfy.

    Written in YAML as a bare string, or as a mapping once it carries a
    ``where:`` or a ``description:``, and serialised back to whichever form it
    was written in::

        assumptions:
          efficiency_is_a_fraction: "efficiency > 0 AND efficiency <= 1"
          bounds_do_not_cross:
            holds: "p_min <= p_max"
            where: "p_min"
            description: a unit with no minimum is unconstrained below

    The language decides nothing about the numbers, so the consumer attaching
    the data checks it, and refuses the data where it does not hold.
    """

    _label: ClassVar[str] = 'an assumption entry'

    holds: str
    """The condition the data must meet, in the condition grammar, at every coordinate of its dimensions where ``where`` is
    true.
    """
    where: str | None = None
    """The coordinates at which a tool checks the assumption, in the condition grammar. Without it, a tool checks every
    coordinate.
    """
    description: str | None = None
    """Why the rule exists, in the words of the author. An engine quotes it when it refuses the data."""

    @model_validator(mode='before')
    @classmethod
    def _from_string(cls, data: object) -> object:
        return {'holds': data} if isinstance(data, str) else data

    @classmethod
    @override
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, object]:
        """The published schema admits the bare string the one-line form is written as."""
        return _also_written_as(core_schema, handler, {'type': 'string'})

    @model_serializer
    def _as_written(self) -> str | dict[str, object]:
        if self.where is None and self.description is None:
            return self.holds
        written: dict[str, object] = {'holds': self.holds}
        if self.where is not None:
            written['where'] = self.where
        if self.description is not None:
            written['description'] = self.description
        return written


class PiecewiseLinkSpec(_StrictSpec):
    """One link of a piecewise entry: an expression tied to the curve through a values parameter.

    Written in YAML as ``[expression, values]`` or ``[expression, values,
    sign]``, and serialised back to exactly that form, so a round trip through
    [`Spec.to_yaml`][] reproduces the file.

    A link that names ``by: relation[column]`` reads the curve's weights
    through the relation, as ``at`` reads an array, and is written as a
    mapping. Its row is the entry's ``dims:`` with the dims the lookup reads
    replaced by the key columns it arrives at, so one link emits a row per fine
    coordinate and each reads the curve of the coarse coordinate it maps to.
    """

    _label: ClassVar[str] = 'a piecewise link'

    expression: str
    values: str
    sign: Sense = '=='
    by: str | None = None
    """The relation and column that the link reads the weights of the curve at, as ``at(..., by=)`` names them."""

    @property
    def walks(self) -> bool:
        """Whether the link reads the curve's weights through a relation, rather than on the entry's own dims."""
        return self.by is not None

    @model_validator(mode='before')
    @classmethod
    def _from_list(cls, data: object) -> object:
        if isinstance(data, list):
            if not 2 <= len(data) <= 3:
                msg = f'each link is [expression, values] or [expression, values, sign], got {data!r}.'
                raise ValueError(msg)
            return dict(zip(('expression', 'values', 'sign'), data, strict=False))
        return data

    @classmethod
    @override
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> dict[str, object]:
        """The published schema admits the ``[expression, values, sign?]`` form every link is written as."""
        list_form = {'type': 'array', 'items': {'type': 'string'}, 'minItems': 2, 'maxItems': 3}
        return _also_written_as(core_schema, handler, list_form)

    @model_serializer
    def _as_written(self) -> list[str] | dict[str, str]:
        """The list form, or the mapping form a walk cannot be written in a list."""
        if self.by is None:
            return [self.expression, self.values] if self.sign == '==' else [self.expression, self.values, self.sign]
        written = {'expression': self.expression, 'values': self.values, 'by': self.by}
        return written if self.sign == '==' else {**written, 'sign': self.sign}


PIECEWISE_METHODS = {
    'adjacency': 'a binary per segment, and a row making the two nonzero weights neighbours',
    'sos2': 'the same weights, restricted by a set the solver branches on (the sos rules)',
    'incremental': 'a filled fraction per segment, each filled only once the one before it is full, ordered by a binary',
    'convex': 'nothing, so the weights range over the hull, which is a pure LP',
    'lp': 'no weights, but one row per segment line, plus the two rows holding the domain',
}
"""The methods a ``piecewise:`` entry may declare under ``method:``, each with what it adds. ``sos2``, ``incremental`` and
``lp`` mean what they mean in ``linopy.Spec.add_piecewise_formulation`` (#695).
"""


_TWO_LINKS = {
    'lp': 'It states the curve as its segment lines, and a line is one quantity against another.',
    'convex': (
        'It relaxes the weights onto the hull, which is exact only in the direction of the sign on the '
        'bounded link, and with more than two links there is no single direction to check.'
    ),
}

_NO_WALK = {
    'lp': 'A segment line has one x quantity, and a walked link is one quantity at many coordinates.',
    'convex': 'It checks one values parameter against another, and a walk puts them over different dimensions.',
}


class PiecewiseSpec(_StrictSpec):
    """Expressions tied to one breakpoint-indexed piecewise curve per coordinate of ``dims:``.

    Mirrors ``linopy.Spec.add_piecewise_formulation``. ``links:`` maps a name
    to ``[expression, values_parameter]`` or ``[expression, values_parameter,
    sign]``: *expression* is any affine expression string over ``dims:``,
    *values_parameter* names a parameter carrying ``along`` and no dim the
    link's row lacks, and *sign* bounds the link by the curve instead of
    pinning it. The name is the link's row in the expansion, ``<entry>_<link>``.

    ``dims:`` alone decides how many curves the entry builds: one set of
    weights per coordinate of it. ``where:`` says which of those coordinates
    have a curve, and how far each runs along ``along`` where it reads that
    dim too; ``activity:`` whether a curve that exists is switched on. A link
    that walks a relation builds a row per fine coordinate, each reading the
    one curve its coarse coordinate has, so how many expressions a curve ties
    is data.
    """

    _label: ClassVar[str] = 'a piecewise entry'

    along: str
    """The dimension each curve runs along: its breakpoints, in the declared order of that dimension."""
    dims: Dims
    """The frame of the curves, sorted by name as it loads: one curve per coordinate of it."""
    links: Frozen[str, PiecewiseLinkSpec]
    """Each link by the name its row takes, ``<entry>_<link>``, in the order the file writes them: with two links pinned,
    the first is the x-axis."""
    where: str | None = None
    """Which coordinates have a curve, or every coordinate when the key is left out. Over ``dims:`` alone it states which
    curves exist; over ``along`` too, it states which breakpoints each curve runs through, for curves of unequal length.
    """
    method: PiecewiseMethod = 'adjacency'
    """Which of [`PIECEWISE_METHODS`][] restricts the weights."""
    activity: str | None = None
    """The variable that switches each curve off where it is 0, or no switch when the key is left out. A binary variable,
    or an integer one under ``method: incremental``, which from 1 up moves the curve by its point at the first breakpoint
    once per unit above 1. Written as the name of the variable, or as ``at(<variable>, by=<relation>[<column>])``.
    """
    description: str | None = None

    @property
    def curve(self) -> tuple[PiecewiseLinkSpec, PiecewiseLinkSpec]:
        """The two links as ``(x, y)``, the bounded one last.

        Two-link entries only.
        """
        x, y = self.links.values()
        return (y, x) if x.sign != '==' else (x, y)

    @model_validator(mode='before')
    @classmethod
    def _check_dims(cls, data: object) -> object:
        if isinstance(data, dict) and data.get('dims') is None:
            msg = (
                'a piecewise entry declares dims:, the dimensions with one curve per coordinate, as a variable '
                'declares its own. Write the dimensions its links are over, without any that a link adds through '
                'a relation: dims: [generator, snapshot] for a link on p over [generator, snapshot].'
            )
            raise ValueError(msg)
        return data

    @field_validator('method', mode='wrap')
    @classmethod
    def _check_method(cls, v: object, handler: ValidatorFunctionWrapHandler) -> PiecewiseMethod:
        try:
            return cast('PiecewiseMethod', handler(v))
        except ValidationError:
            options = '\n'.join(f'  {name}: {what}' for name, what in PIECEWISE_METHODS.items())
            msg = f'unknown piecewise method {v!r}. The formulations are:\n{options}'
            raise ValueError(msg) from None

    @model_validator(mode='after')
    def _check_method_shape(self) -> PiecewiseSpec:
        walked = [key for key, link in self.links.items() if link.walks]
        if walked and self.method in ('convex', 'lp'):
            msg = (
                f"method: {self.method} does not take a link that walks a relation (link '{walked[0]}'). "
                f'{_NO_WALK[self.method]} Use method: adjacency, sos2 or incremental.'
            )
            raise ValueError(msg)
        if self.method in ('convex', 'lp') and len(self.links) != 2:
            msg = (
                f'method: {self.method} takes exactly two links. {_TWO_LINKS[self.method]} Write two links, or use '
                f'method: adjacency, sos2 or incremental.'
            )
            raise ValueError(msg)
        if self.method == 'lp' and sum(link.sign != '==' for link in self.links.values()) != 1:
            msg = "method: lp needs exactly one link with a '<=' or '>=' sign. Add the sign to one link."
            raise ValueError(msg)
        if self.activity is not None and self.method in ('convex', 'lp'):
            msg = f'activity: does not work with method: {self.method}. Delete activity:, or choose another method.'
            raise ValueError(msg)
        return self

    @field_validator('links')
    @classmethod
    def _check_links(cls, v: Frozen[str, PiecewiseLinkSpec]) -> Frozen[str, PiecewiseLinkSpec]:
        if unnamed := [key for key in v if not re.fullmatch(NAME, key)]:
            msg = (
                f'links: {unnamed} {"is" if len(unnamed) == 1 else "are"} not a name. The name of a link is part of '
                f'the name of its row, <entry>_<link>, so it starts with a letter or an underscore, followed by '
                f'letters, digits or underscores.'
            )
            raise ValueError(msg)
        if len(v) < 2 and not any(link.walks for link in v.values()):
            msg = (
                'piecewise needs at least two links ([expression, values, sign?]), or one link that walks a '
                'relation. One quantity on a curve is a bound, not a curve.'
            )
            raise ValueError(msg)
        if all(link.sign != '==' for link in v.values()):
            msg = (
                "every link has a '<=' or '>=' sign, so nothing pins the point the curve is read at. Write '==' "
                'on at least one link.'
            )
            raise ValueError(msg)
        return v


SOS_TYPES = frozenset(get_args(SosType))
"""The types of special ordered set that a spec may declare."""


class SosSpec(_StrictSpec):
    """A special-ordered set over one dimension of one variable.

    One set per coordinate of the variable's ``dims`` minus ``along``; the
    members are the variable's *existing* coordinates along ``along``, in that
    dimension's declared order.

    ``type: 1`` admits at most one nonzero member, ``type: 2`` at most two,
    and those two consecutive. A consumer with the concept takes the set as
    one; [`Spec.expand`][] states it as binaries instead, and the rows it
    writes multiply by the member's own ``bounds``, which is why a member
    needs both.
    """

    _label: ClassVar[str] = 'a sos entry'

    variable: str
    #: The dimension the set runs along — one set per coordinate of the rest.
    along: str
    type: SosType
    description: str | None = None

    @field_validator('type', mode='wrap')
    @classmethod
    def _check_type(cls, v: object, handler: ValidatorFunctionWrapHandler) -> SosType:
        orders = ' or '.join(str(t) for t in sorted(SOS_TYPES))
        msg = f'sos type is {v!r}. Write type: {orders}.'
        if type(v) is not int:  # True == 1 == 1.0, and a set of order True is nothing
            raise ValueError(msg)
        try:
            return cast('SosType', handler(v))
        except ValidationError:
            raise ValueError(msg) from None


SUPPORTED_VERSIONS: tuple[int, ...] = (0,)
"""The language versions this release of mathspec loads. A language version changes only when the YAML the language accepts
changes, so it is separate from the package version. Version ``0`` is unstable and has no compatibility promise.
"""


class Spec(_StrictSpec):
    """The declared math — one YAML file, or one dict, validated. Nothing here has seen data.

    A ``Spec`` that exists has passed the whole language: constructing one by
    any route — ``to_spec``, [`model_validate`][], the constructor — runs
    every load-time check, expression pass included, and raises
    [`LanguageError`][mathspec.errors.LanguageError] on a spec the language refuses.
    Holding one is the proof, so nothing downstream checks it again. Nothing
    changes one after it loads either: a section is a read-only mapping, a
    list is a tuple, and a field cannot be set, so [`to_yaml`][] writes the
    file [`program`][] was lowered from. [`override`][mathspec.override] is
    the edit, and loads what it makes as a new spec.

    The API is the thirteen sections plus ``version`` and
    ``description``, three ways back out — [`to_dict`][] for the spec as
    data, [`to_yaml`][] for the file a reviewer reads, [`expand`][] for the
    spec with its formulations written out as plain rows — and [`program`][], the
    spec typed, which every reader after load walks. Everything else on this
    class is pydantic's, not a contract this package keeps.
    """

    _label: ClassVar[str] = 'the top level of the file'

    version: int = 0
    """The language version the file is written against. A file without it is version 0, which is unstable, so the YAML it
    accepts may change in any release. A later mathspec refuses a file whose version it cannot load.
    """
    description: str | None = None
    """What the file as a whole is, in plain prose like the ``description:`` of an entry. mathspec prints it at the top of
    the typeset document.
    """
    given: GivenSpec = GivenSpec()
    """What this file uses and does not build ([`GivenSpec`][]). It is empty when the file has no ``given:``."""
    dimensions: ByName[DimensionSpec] = Frozen({})
    relations: ByName[RelationSpec] = Frozen({})
    parameters: ByName[ParameterSpec] = Frozen({})
    conditions: ByName[ConditionSpec] = Frozen({})
    variables: ByName[VariableSpec] = Frozen({})
    expressions: ByName[ExpressionSpec] = Frozen({})
    objective: ObjectiveSpec | None = None
    constraints: ByName[ConstraintSpec] = Frozen({})
    sos: ByName[SosSpec] = Frozen({})
    piecewise: ByName[PiecewiseSpec] = Frozen({})
    assumptions: ByName[AssumptionSpec] = Frozen({})
    macros: ByName[MacroSpec] = Frozen({})

    @cached_property
    def program(self) -> Program:
        """This spec typed, section for section — what every reader after load walks.

        Computing it *is* the expression pass, so a spec the language refuses
        raises here; loading forces it, so every ask on a spec in hand is the
        one object. It mirrors the spec: a ``piecewise:`` entry still in it is
        a curve under ``program.piecewise`` and an ``sos:`` entry a set under
        ``program.sos``, and [`expand`][] is what writes either out as rows,
        so a consumer building rows reads ``spec.expand(...).program`` and
        refuses an entry it does not take.
        """
        from mathspec._lowering import lower

        return lower(self)

    @classmethod
    @override
    def model_validate(
        cls,
        obj: object,
        *,
        strict: bool | None = None,
        extra: ExtraValues | None = None,
        from_attributes: bool | None = None,
        context: object = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> Self:
        """Validate a mapping, raising this package's exception tree rather than pydantic's.

        ``__init__`` is not wrapped the same way, because defining one makes
        pydantic run every after-validator twice.
        """
        try:
            return super().model_validate(
                obj,
                strict=strict,
                extra=extra,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError as exc:
            raise schema_error(exc) from None

    @field_validator('version')
    @classmethod
    def _check_version(cls, v: int) -> int:
        """Refuse a surface this reader does not know — never interpret it."""
        if v in SUPPORTED_VERSIONS:
            return v
        from mathspec import __version__ as installed

        supported = ', '.join(str(s) for s in SUPPORTED_VERSIONS)
        msg = (
            f'the spec declares version {v}, and mathspec {installed} understands [{supported}]. '
            f'Upgrade mathspec, or write the version this file targets.'
        )
        raise ValueError(msg)

    @model_serializer(mode='wrap')
    def _drop_absence(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        """Absence is not serialised: a null, an empty mapping, a section declaring nothing, each part dropping its own.

        An empty list stays, being a value rather than an absence (``dims:
        []`` is a scalar). On the serializer so that ``model_dump``,
        [`to_dict`][] and [`to_yaml`][] agree. ``version`` is written whether
        the file wrote it or not, so a written file states the language it is
        read in.
        """
        return {'version': self.version, **_as_set(self, cast('dict[str, object]', handler(self)))}

    def to_dict(self) -> dict[str, object]:
        """The spec as plain data. ``to_spec(m.to_dict())`` reproduces it."""
        return self.model_dump()

    def to_yaml(self, *, canonical: bool = False) -> str:
        """The file a reviewer reads — including for a spec that never had one.

        The fields the file wrote, and no others: a default it writes out is
        written back, and one it leaves out is not. ``version`` is always
        written. Sections and the keys of an entry come in the schema's order.

        Args:
            canonical: Write the normal form instead: entries sorted by
                name, no field at its default, every expression printed from its parsed tree, one term
                of a sum per line. Two files that state the same spec write
                the same text, so what a diff shows is a difference in the
                spec. The normal form loads to the same spec and not to an
                equal [`Spec`][mathspec.spec.Spec], a reprinted expression
                being a different string.
        """
        if canonical:
            from mathspec._canonical import canonical_yaml

            return canonical_yaml(self)
        from mathspec._yaml import dump_yaml

        return dump_yaml(self.to_dict())

    def expand(self, *kinds: Formulation) -> Spec:
        """This spec with its formulations written out as plain variables and constraints.

        A formulation states rows rather than being one — ``piecewise:`` states
        a curve, ``sos:`` states which members of a family may be nonzero.
        Expanding one writes those rows under names prefixed with the entry's
        own, and drops the entry. The result is a different spec: it declares
        more variables and constraints, so it does not compare equal to this
        one. It declares the same dimensions and parameters, so the same data
        attaches to both. Nothing is cached, so a second call builds the
        expansion again.

        Args:
            kinds: Which formulations to write out — ``'piecewise'``,
                ``'sos'``, or none of them for every one. They go in that
                order whatever order they are asked in, because a
                ``method: sos2`` curve emits a set and no set emits a curve.

        Returns:
            The spec with those sections written out, or this same object where
            it declares none of them, so an expansion asked for the same kinds
            again returns itself. It is a spec like any other: [`to_yaml`][]
            writes it, and [`program`][] holds its rows.

        Raises:
            ValueError: *kinds* names something that is not a formulation.
        """
        wanted = _formulations(kinds)
        from mathspec._piecewise import expand_piecewise
        from mathspec._sos import expand_sets

        expanded = expand_piecewise(self) if 'piecewise' in wanted else self
        if 'sos' in wanted and expanded.sos:
            expanded = expand_sets(expanded)
        return expanded

    @model_validator(mode='after')
    def _names_are_names(self) -> Spec:
        """Every entry is keyed by something an expression could write.

        Read off the spec's own mappings rather than a list of sections, so a
        section added later cannot be forgotten here — every mapping a Spec
        carries is keyed by an entry name. ``given:`` nests its five
        mappings one level down, so they are read off [`GivenSpec`][] the
        same way.
        """
        sections = [*self, *((f'given: {kind}', group) for kind, group in self.given)]
        errors = [
            f'{section}: {name!r} is not a name. Start it with a letter or an underscore, '
            f'then use only letters, digits or underscores.'
            for section, value in sections
            if isinstance(value, Mapping)
            for name in value
            if not re.fullmatch(NAME, name)
        ]
        if errors:
            raise ValueError('\n'.join(errors))

        return self

    @model_validator(mode='after')
    def _lower(self) -> Spec:
        """Every rule that reads across entries, then every expression and condition.

        A fault in a curve's link is named against the link the file wrote. The
        rows a curve states are held to the language when [`expand`][]
        writes them out, since an expansion is a spec like any other.
        """
        _ = self.program
        return self


def _formulations(asked: tuple[str, ...]) -> tuple[Formulation, ...]:
    """What *asked* names, in [`FORMULATIONS`][] order — all of them where it names none.

    Raises:
        ValueError: A name that is not a formulation.
    """
    if unknown := [kind for kind in asked if kind not in FORMULATIONS]:
        spelled = ' and '.join(repr(kind) for kind in FORMULATIONS)
        msg = f'{unknown[0]!r} is not a formulation. Expand {spelled}, or pass none of them for every one.'
        raise ValueError(msg)
    return tuple(kind for kind in FORMULATIONS if not asked or kind in asked)
