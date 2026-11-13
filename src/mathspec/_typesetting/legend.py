# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The legend: the glossary of symbols, and a row for each notation the equations use.

What the equations use is read off the program before anything prints
([`notice`][]), so the legend explains every symbol the walk will print and
nothing the walk decides is asked of it twice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from mathspec._typesetting.format import LegendItem, number
from mathspec.program import (
    CountComparison,
    DimensionComparison,
    DimensionPosition,
    ExpressionComparison,
    JoinedCondition,
    MissingFrom,
    Translate,
    TranslatedCondition,
    WindowSum,
    walk_regions,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from mathspec._typesetting.format import Format, OperatorName
    from mathspec._typesetting.symbols import Symbols
    from mathspec.program import Expression, Mask, ParameterMissing, Program, Relation

TranslationPolicy = Literal['plain', 'wrap', 'edge']

PositionForm = Literal['plain', 'grouped', 'from_end']


def policy_of(node: Translate | WindowSum) -> TranslationPolicy:
    """Which translation symbol *node* prints with: cyclic, filled at the edge, or plain."""
    if node.wrap:
        return 'wrap'
    if isinstance(node, Translate) and node.fill is not None:
        return 'edge'
    return 'plain'


@dataclass(frozen=True)
class Noticed:
    """What the equations use that the legend has to explain.

    Attributes:
        policies: Each translation policy some ``shift`` or ``sum_back`` prints.
        grouped: Whether some translation is counted inside the group of a map.
        positions: Each form a ``position()`` prints in.
        numeric_coordinates: Each dimension whose index is compared against a
            number, where "position 3" and "the coordinate 3" are both
            readings of a line.
    """

    policies: frozenset[TranslationPolicy]
    grouped: bool
    positions: frozenset[PositionForm]
    numeric_coordinates: frozenset[str]


def notice(program: Program) -> Noticed:
    """What printing *program* uses, read off every tree the walk prints."""
    policies: set[TranslationPolicy] = set()
    grouped = False
    positions: set[PositionForm] = set()
    numeric: set[str] = set()

    def expressions(*roots: Expression) -> None:
        nonlocal grouped
        for node, regions in walk_regions(*roots):
            if isinstance(node, WindowSum) or (isinstance(node, Translate) and node.offset != 0):
                policies.add(policy_of(node))
                grouped = grouped or node.partition is not None
            for region in regions:
                masks(region)

    seen: set[int] = set()

    def masks(mask: Mask) -> None:
        if id(mask) in seen:
            return
        seen.add(id(mask))
        for atom in mask.atoms:
            if isinstance(atom, DimensionComparison) and isinstance(atom.value, int | float):
                numeric.add(atom.name)
            elif isinstance(atom, DimensionPosition):
                positions.add('grouped' if atom.partition is not None else 'plain')
                if atom.position < 0:
                    positions.add('from_end')
            elif isinstance(atom, ExpressionComparison):
                expressions(atom.left, atom.right)
            elif isinstance(atom, CountComparison):
                masks(atom.condition)
            elif isinstance(atom, TranslatedCondition | JoinedCondition):
                masks(atom.operand)

    expressions(*program.roots)
    for entry in program.expressions.values():
        expressions(entry.expression)
    for curve in program.piecewise.values():
        expressions(*(link.expression for link in curve.links))
    for named in program.conditions.values():
        masks(named.condition)
    for entry in (*program.constraints.values(), *program.variables.values(), *program.parameters.values()):
        if entry.where is not None:
            masks(entry.where)
    for assumption in program.assumptions.values():
        masks(assumption.holds)
        if assumption.where is not None:
            masks(assumption.where)
    return Noticed(frozenset(policies), grouped, frozenset(positions), frozenset(numeric))


_NO_ROW = 'where the data has no row'

_NO_LABEL = 'where the data gives no label'

_MASKED_OUT = 'where the mask leaves it out'


@dataclass(frozen=True)
class Legend:
    """The glossary, spelled with one program's symbols in one format."""

    program: Program
    symbols: Symbols
    format: Format
    parameter_masks: Mapping[str, str] = field(default_factory=dict)
    index_sets: Mapping[str, str] = field(default_factory=dict)

    def _op(self, name: OperatorName) -> str:
        return self.format.operators[name]

    def glossaries(self, noticed: Noticed, defined: Iterable[str]) -> list[tuple[str, list[LegendItem]]]:
        """The given entries, sets, parameters, conditions, variables and definitions, each with its symbol, its dims and its description, then the notation.

        *defined* names the expressions that print under their own symbol, so
        a legend row stands exactly where a symbol does.
        """
        fmt, program = self.format, self.program
        sets = [
            self._item(
                self.symbols.set[d],
                f'index {fmt.math(self.symbols.index[d])} {fmt.dash} {fmt.mono(d)}{self._coords(d, noticed)}',
                entry.description,
            )
            for d, entry in program.dimensions.items()
        ]
        parameters = [
            self._item(
                self.symbols.name[p],
                f'{fmt.mono(p)}{self._over(list(entry.dims), p)}{self._only_where(p)}{self._missing(entry.missing)}',
                entry.description,
            )
            for p, entry in program.parameters.items()
        ]
        variables = [
            self._item(
                self.symbols.name[v],
                f'{fmt.mono(v)}{self._over(list(entry.dims), v)}{self._missing(entry.missing, "absent", _MASKED_OUT)}',
                entry.description,
            )
            for v, entry in program.variables.items()
        ]
        given = [
            *(
                self._item(
                    self.symbols.name[g],
                    f'{fmt.mono(g)}{self._over(list(entry.dims))}, data another file declares',
                    entry.description,
                )
                for g, entry in program.given.parameters.items()
            ),
            *(
                self._item(self.symbols.name[g], f'{fmt.mono(g)}{self._over(list(entry.dims))}', entry.description)
                for g, entry in program.given.variables.items()
            ),
            *(
                self._item(
                    self.symbols.name[g],
                    f'{fmt.mono(g)}{self._over(list(entry.dims))}, '
                    + (
                        f'an expression this file adds {", ".join(fmt.mono(t) for t in terms)} to'
                        if (terms := [t for t, e in program.expressions.items() if e.adds_to == g])
                        else 'an expression another file defines'
                    ),
                    entry.description,
                )
                for g, entry in program.given.expressions.items()
            ),
            *(
                self._item(
                    self.symbols.constraint[g],
                    f'{fmt.mono(g)}{self._over(list(entry.dims))}, a row family this file reads the dual of',
                    entry.description,
                )
                for g, entry in program.given.constraints.items()
            ),
            *(
                self._item(
                    self.symbols.name[g],
                    f'{fmt.mono(g)}{self._over(list(entry.dims))}, a condition another file defines',
                    entry.description,
                )
                for g, entry in program.given.conditions.items()
            ),
        ]
        shown = set(defined)
        definitions = [
            self._item(self.symbols.name[e], f'{fmt.mono(e)}{self._over(list(entry.dims))}', entry.description)
            for e, entry in program.expressions.items()
            if e in shown
        ]
        conditions = [
            self._item(self.symbols.name[m], f'{fmt.mono(m)}{self._over(list(entry.dims))}', entry.description)
            for m, entry in program.conditions.items()
        ]
        groups = (
            ('Given', given),
            ('Sets', sets),
            ('Parameters', parameters),
            ('Conditions', conditions),
            ('Variables', variables),
            ('Definitions', definitions),
            ('Notation', self._notation(noticed)),
        )
        return [(title, items) for title, items in groups if items]

    def _item(self, symbol: str, what: str, description: str | None) -> LegendItem:
        meaning = f'{what} {self.format.dash} {self.format.escape(description)}' if description else what
        return LegendItem(symbol, meaning)

    def _over(self, dims: list[str], entry: str | None = None) -> str:
        """The domain of a legend row: *entry*'s index set where it has one, else the product of its sets."""
        if entry in self.index_sets:
            return f' over {self.format.math(self.index_sets[entry])}'
        if not dims:
            return ' (scalar)'
        product = self.format.joined([self.symbols.set[d] for d in dims], self._op('times'))
        return f' over {self.format.math(product)}'

    def _only_where(self, parameter: str) -> str:
        mask = self.parameter_masks.get(parameter)
        return '' if mask is None else f', only where {self.format.math(mask)}'

    def _missing(self, value: ParameterMissing, default: str = 'refused', where: str = _NO_ROW) -> str:
        """What *where* means: the reading or the value ``missing:`` names, and nothing for the *default* reading."""
        if value == default:
            return ''
        if isinstance(value, MissingFrom):
            return f', {self.format.math(self.symbols.name[value.expression])} {where}'
        if isinstance(value, str | bool):
            shown = self.format.mono(str(value).lower())
        else:
            shown = self.format.math(number(value, self.format))
        return f', {shown} {where}'

    def _signatures(self, name: str, lk: Relation, dim: str) -> list[str]:
        """The parts of table *name* that touch *dim*: the relation inside its product, and each map from its subject.

        A relation prints as ``connection ⊆ P x U`` under each of its
        dimensions. A map prints as ``carrier: U → C`` under its subject's
        dimensions and the one it refers to, its subject a set symbol for a
        dimension and the relation's name for a relation.
        """
        own = {lk.dim(r) for r in lk.key}
        dimension = name in self.program.dimensions and lk.key == (name,)
        subject = self.symbols.set[name] if dimension else self.format.upright(name)
        signatures = []
        if not dimension and dim in own:
            product = self.format.joined([self.symbols.set[lk.dim(r)] for r in lk.key], self._op('times'))
            signatures.append(f'{self.format.upright(name)} {self._op("subset_of")} {product}')
        signatures.extend(
            f'{self.format.upright(role)}: {subject} {self._op("maps_to")} {self.symbols.set[lk.dim(role)]}'
            for role in lk.values
            if dim in own or lk.dim(role) == dim
        )
        return signatures

    def _coords(self, dim: str, noticed: Noticed) -> str:
        """The dimension's carried structure: the labels its ``one_of`` allows, each relation over it and map from or into it, and each that may leave a row out.

        The dtype is named only where an equation compared the index against a
        number, the one place "position 3" and "the coordinate 3" are both
        readings of a line.
        """
        carried = self.program.relations_of(dim)
        clauses = []
        if dim in noticed.numeric_coordinates:
            clauses.append(f' ({self.format.mono(self.program.dimensions[dim].dtype)} coordinates)')
        if (labels := self.program.dimensions[dim].one_of) is not None:
            clauses.append(f' (labels {", ".join(self.format.mono(m) for m in labels)})')
        if carried:
            signatures = [part for c, lk in carried.items() for part in self._signatures(c, lk, dim)]
            clauses.append(f' with {self.format.math(self.format.joined(signatures, ""))}')
            own = {c: {lk.dim(r) for r in lk.key} for c, lk in carried.items()}
            clauses.extend(
                f', {self.format.mono(c)} is {self.format.mono("absent")} {_NO_ROW}'
                for c, lk in carried.items()
                if lk.missing == 'absent' and dim in own[c]
            )
            clauses.extend(
                f', {self.format.mono(f"{c}[{role}]")} is {self.format.mono("absent")} {_NO_LABEL}'
                for c, lk in carried.items()
                for role in lk.partial
                if dim in own[c] or lk.dim(role) == dim
            )
        return ''.join(clauses)

    def _notation(self, noticed: Noticed) -> list[LegendItem]:
        """A row for each translation and position symbol printed; plain ``t-k`` needs none.

        The meaning is the spec spelling the symbol stands for, so the row
        holds no claim the language reference does not already make.
        """
        fmt, dash = self.format, self.format.dash
        relation = fmt.apply(fmt.upright('map'), 't')
        shifted, t = fmt.math('t-k'), fmt.math('t')
        items = []
        if 'wrap' in noticed.policies:
            cyclic = fmt.mono("edge='wrap'")
            items.append(LegendItem(f't {self._op("cyclic_minus")} k', f'{cyclic} {dash} {shifted}, cyclic'))
        if 'edge' in noticed.policies:
            items.append(
                LegendItem(
                    f't {fmt.subscript(self._op("edge_minus"), ["v"])} k',
                    f'{fmt.mono("edge=v")} {dash} {shifted}, and {fmt.math("v")} past the edge',
                )
            )
        if noticed.grouped:
            items.append(
                LegendItem(
                    f't {fmt.superscript(self._op("cyclic_minus"), relation)} k',
                    f'{fmt.mono("within=subject[map]")} {dash} {shifted} inside the group of {t}',
                )
            )
        if noticed.positions:
            items.append(
                LegendItem(
                    fmt.apply(self._op('position'), 't'),
                    f'{fmt.mono("position()")} {dash} the position of {t}, counted from {fmt.math("0")}; {t} is the label',
                )
            )
        if 'grouped' in noticed.positions:
            items.append(
                LegendItem(
                    fmt.apply(fmt.subscript(self._op('position'), [relation]), 't'),
                    f'{fmt.mono("position(within=subject[map])")} {dash} the position of {t} inside its group',
                )
            )
        if 'from_end' in noticed.positions:
            size = fmt.cardinality(fmt.script('T'))
            last = f'{size} {self._op("minus")} 1'
            items.append(
                LegendItem(size, f'the size of {fmt.math(fmt.script("T"))}; {fmt.math(last)} is the last position')
            )
        return items
