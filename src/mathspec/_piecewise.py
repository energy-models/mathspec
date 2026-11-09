# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Expand ``piecewise:`` entries into plain variables and constraints.

An entry becomes ordinary affine declarations when a caller asks
[`expand`][mathspec.spec.Spec.expand] for them, under names prefixed with the
entry's own; what each method emits is tabled in
``docs/reference/language/piecewise.md``. Every rule an entry is held to is
decided as the spec loads, before its rows are written: the names it
references in [`reference_errors`][mathspec._validation.reference_errors], its
links and its ``where:`` as lowering types them, and the fit of each link's row
to its expression, its values and the mask in [`declaration_of`][]. A refusal
names the link or key the file wrote rather than an emitted declaration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import mathspec._sos as sos
from mathspec._expression_parser import NAME, ColumnsNode, FunctionCallNode, NameNode, columns_of, parse_expression
from mathspec._expression_resolver import ExpressionResolver
from mathspec._resolution import mask_of, resolve_condition_text, resolve_expression_text
from mathspec.errors import DimensionError, SchemaError
from mathspec.program import Gate, Join, Link, Piecewise, PiecewiseMethod, Variable, carries_variable
from mathspec.spec import AssumptionSpec, Curvature, PiecewiseLinkSpec, PiecewiseSpec, Spec, VariableSpec

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from mathspec._resolution import Namespace
    from mathspec.program import Expression, JoinColumns, Mask, Program, Relation


_UNGATED = '_ungated'


# ---------------------------------------------------------------------------
# the mask, as each shape of row reads it
# ---------------------------------------------------------------------------


def _masks(where: str | None, along: str, *, ragged: bool) -> tuple[str | None, str | None, str | None]:
    """The entry's ``where:`` as three shapes of row read it: ``(mask, frame, exists)``.

    A **ragged** where reads the breakpoint dim, so it says how far each curve
    runs: a row over the frame and that dim takes it as written (*mask*), and
    a row over the frame alone, which cannot read that dim, takes the count of
    breakpoints it admits (*exists*). A where over the frame alone says which
    curves exist: every row conjoins it as written (*frame*, and *exists*),
    and no row is ragged (*mask* is ``None``).
    """
    if ragged:
        return where, None, f'count({where}, over={along}) > 0'
    return None, where, where


def _all_of(*clauses: str | None) -> str | None:
    """The where admitting a row only where every clause given does, or ``None`` where none of them speaks.

    A lone clause passes through as it was written, so an entry with no
    ``where:`` emits exactly the string it always did. Joined clauses are
    parenthesised, because a disjunction inside one of them would otherwise
    bind only its last operand to the ``AND``.
    """
    kept = [clause for clause in clauses if clause]
    if len(kept) <= 1:
        return kept[0] if kept else None
    return ' AND '.join(f'({clause})' for clause in kept)


def _operand(mask: str) -> str:
    """The mask as one operand of a connective: a bare name as it is, anything else parenthesised."""
    return mask if re.fullmatch(NAME, mask) else f'({mask})'


def _shifted(over: str, mask: str, offset: int) -> str:
    """*mask* read *offset* breakpoints back, false where that vacates."""
    return f'shift({mask}, along={over}, offset={offset})'


def _neighbours(over: str, mask: str | None) -> str:
    """Where a breakpoint and the one before it are both there: the rows a claim about a segment is true of."""
    if mask is None:
        return f'position({over}) > 0'
    return f'{_operand(mask)} AND {_shifted(over, mask, 1)}'


def _edge(over: str, mask: str | None, end: Literal['first', 'last']) -> str:
    """The first or last breakpoint of each curve: where the mask holds and does not one step outward.

    The vacated edge of a ``shift`` in a ``where`` is false, which is what
    makes the head and the tail of the axis their own edge.
    """
    if mask is None:
        return f'position({over}) == {0 if end == "first" else -1}'
    return f'{_operand(mask)} AND NOT {_shifted(over, mask, 1 if end == "first" else -1)}'


def _pieces(over: str, mask: str | None) -> str:
    """Where a breakpoint and the one after it are both there: the rows a segment, sat at its lower breakpoint, is true of."""
    if mask is None:
        return f'position({over}) != -1'
    return f'{_operand(mask)} AND {_shifted(over, mask, -1)}'


def _interior(over: str, mask: str | None) -> str:
    """Where a breakpoint has one on either side: the rows a claim about a bend is true of."""
    if mask is None:
        return f'position({over}) > 0 AND position({over}) != -1'
    return f'{_operand(mask)} AND {_shifted(over, mask, 1)} AND {_shifted(over, mask, -1)}'


# ---------------------------------------------------------------------------
# what an entry assumes of its numbers
# ---------------------------------------------------------------------------


def _curvature_required(curve: Piecewise) -> Curvature | None:
    """The curvature *curve*'s method is only exact for, or ``None`` if any shape works.

    A bounded link binds from one side, and that side is the hull boundary the
    weights are driven onto: ``>=`` reaches the lower one, which is the curve
    itself only where the curve is convex. ``lp`` states that boundary as its
    segment lines and ``convex`` relaxes the weights onto it, so the two rest
    on the same shape and read the same sign for it. The opposite bend is
    silently wrong rather than merely loose.

    With both links pinned the weights range over the whole hull, and what
    drives them within it is the objective rather than the entry. There the
    most a method states is ``'either'``: a mixed curve is wrong whichever way
    the pressure runs, and a single bend is exact one of the two ways.
    """
    if curve.method not in ('convex', 'lp'):
        return None
    if (sign := curve.curve[1].sign) == '==':
        return 'either'
    return 'convex' if sign == '>=' else 'concave'


def assumptions_of(name: str, curve: Piecewise, where: str | None) -> dict[str, AssumptionSpec]:
    """What entry *name* assumes of its numbers, by the name the document prints and a refusal quotes.

    Every curve assumes its breakpoints are there, because a missing row does
    not shorten a curve. Under a ragged ``where:`` its tables are not
    ``refused``, so a breakpoint missing inside the mask would read as their
    ``missing:`` and, under ``missing: 0``, sit the curve on the origin. A walked link's breakpoints are over
    its own rows, so each is asked of the rows that link reads the curve at,
    under a name of its own. A curve has an x-axis only where two links tie
    it, so the increasing condition — and the shape it is checked with —
    exist only there; ``lp`` alone needs a segment to state a line for; a
    ragged ``where:`` must mark one run.

    Each condition is a where string over the parameters the file declared,
    so *where* is the entry's ``where:`` as the file wrote it — a typed mask
    has no text — and *curve* says how each row reads it. The expansion
    writes the conditions into ``assumptions:``, and a spec that still
    declares the entry derives the same text at load. Each is asked only
    where a curve runs, so the ``where:`` goes into every one of them: a
    spec written out and read back holds the data to what the entry did.
    """
    d = curve.along
    mask, frame, exists = _masks(where, d, ragged=curve.ragged)
    if mask is not None:
        rewrite = f'Attach the rows, or narrow where: {mask!r} to where the curve runs.'
    elif where is not None:
        rewrite = f"Attach the rows, or test '{d}' in where: {where!r} too, so that it sets how far each curve runs."
    else:
        rewrite = 'Attach the rows, or declare a where: that sets how far the curve runs.'
    assumed: dict[str, AssumptionSpec] = {}
    if values := [link.values for link in curve.links if not link.walks]:
        assumed[f'{name}_complete'] = AssumptionSpec(
            holds=' AND '.join(dict.fromkeys(values)),
            where=where,
            description=f"piecewise '{name}': every breakpoint the curve runs through needs a row in "
            f'{_quoted(values)}. A missing row does not shorten the curve. {rewrite}',
        )
    for link in curve.links:
        if link.walks:
            assumed[f'{name}_{link.name}_complete'] = AssumptionSpec(
                holds=link.values,
                where=through(where, link) if link.reads else _all_of(link.walk.name if link.walk else None, where),
                description=f"piecewise '{name}' link '{link.name}': every breakpoint the curve runs through needs a "
                f"row in '{link.values}' at every row of the link. A missing row does not shorten "
                f'the curve. {rewrite}',
            )
    curvature = _curvature_required(curve)
    if curvature is not None:
        x, y = (link.values for link in curve.curve)
        assumed[f'{name}_increasing'] = AssumptionSpec(
            holds=f'{_back(x, d, 1)} < {x}',
            where=_all_of(frame, _neighbours(d, mask)),
            description=f"piecewise '{name}': method: {curve.method} requires strictly increasing breakpoints "
            f"in '{x}' along '{d}'",
        )
        assumed[f'{name}_curvature'] = _bends(name, curve, x, y, curvature, mask=mask, frame=frame, exists=exists)
    if curve.method == 'lp':
        assumed[f'{name}_breakpoints'] = AssumptionSpec(
            holds=f'count({mask or curve.curve[0].values}, over={d}) >= 2',
            where=exists,
            description=f"piecewise '{name}': method: lp needs at least two breakpoints per curve. Use method: "
            f'adjacency, sos2 or convex, which hold the link to the points the curve does have.',
        )
    if mask is not None:
        assumed[f'{name}_contiguous'] = AssumptionSpec(
            holds=f'count({_edge(d, mask, "first")}, over={d}) == 1',
            where=exists,
            description=f"piecewise '{name}': where: {mask!r} must mark a consecutive run of at least one "
            f'breakpoint per curve, because {_GAP[curve.method]}.',
        )
    return assumed


_GAP: dict[PiecewiseMethod, str] = {
    'adjacency': 'the weights are nonzero only on two neighbouring breakpoints, and a gap leaves no neighbour across it',
    'sos2': 'the weights are nonzero only on two neighbouring breakpoints, and a gap leaves no neighbour across it',
    'convex': 'the checks on the shape compare a breakpoint with its neighbours, so a bend across a gap goes unchecked',
    'lp': "the chord row joins a breakpoint to the one before it, and the domain rows sit on the curve's own first "
    'and last',
    'incremental': 'a segment is filled only once the one before it is full, and a gap leaves a segment with no end',
}


_ASSUMED = ('complete', 'increasing', 'curvature', 'breakpoints', 'contiguous')


def through(text: str | None, link: Link) -> str | None:
    """*text* as *link*'s row reads it: through the link's relation where the row reads the where so, else as written."""
    if text is None or not link.reads:
        return text
    return f'at({text}, by={link.by})'


def _walked(text: str, dims: Iterable[str], link: Link | None) -> str:
    """*text*, over *dims*, as *link*'s row reads it: through its relation where the walk drops one of *dims*.

    A gate over fewer dims than the curve may carry none the walk drops, and
    then reads as written on the link's row, as a where does.
    """
    if link is None or link.walk is None or not set(dims) & set(link.walk.dropped_dims):
        return text
    return f'at({text}, by={link.by})'


def _on_walk(text: str | None, link: Link) -> str | None:
    """*text* as *link*'s row reads it, admitted only at the keys its relation has a row for.

    A relation declared ``missing: absent`` may lack a key, and there the
    walked read of the curve is absent, so the row would pin the link's
    expression to an empty sum, or to the first breakpoint under
    ``incremental``. A where read through the relation is already false
    there, and under ``missing: refused`` every key has a row.
    """
    if link.walk is None or link.reads or link.walk.relation.missing == 'refused':
        return through(text, link)
    return _all_of(link.walk.name, text)


def _quoted(names: Iterable[str]) -> str:
    """Parameter names as a refusal lists them, in link order and without repeats."""
    return ', '.join(f"'{name}'" for name in dict.fromkeys(names))


def _back(parameter: str, over: str, offset: int) -> str:
    """*parameter* read *offset* breakpoints back, the vacated row filled with zero and excluded by the ``where``.

    ``edge=0`` is what the language admits over data, and the mask beside it
    is what keeps the invented zero from ever being read.
    """
    return f'shift({parameter}, along={over}, offset={offset}, edge=0)'


def _bends(
    name: str,
    curve: Piecewise,
    x: str,
    y: str,
    curvature: Curvature,
    *,
    mask: str | None,
    frame: str | None,
    exists: str | None,
) -> AssumptionSpec:
    """The curve bends the way *curvature* says, as a comparison of the two slopes at each breakpoint.

    The slopes are compared as a cross-product rather than as two quotients,
    so nothing divides by a run the increasing condition is what rules out.
    ``either`` is one bend in *some* direction, which is a claim about the
    whole axis rather than about a breakpoint: it counts the bends that go the
    wrong way and asks that one of the two directions has none.
    """
    d = curve.along
    rise, run = f'({y} - {_back(y, d, 1)})', f'({x} - {_back(x, d, 1)})'
    next_rise, next_run = f'({_back(y, d, -1)} - {y})', f'({_back(x, d, -1)} - {x})'
    bend = f'{rise} * {next_run} {{}} {next_rise} * {run}'
    interior = _interior(d, mask)
    shape = 'a single bend' if curvature == 'either' else f'a {curvature} curve'
    description = (
        f"piecewise '{name}': method: {curve.method} is exact only for {shape}, and '{y}' over '{x}' along "
        f"'{d}' is not one, so the answer is wrong rather than loose. Use method: adjacency "
        f'or sos2, which take a curve of any shape.'
    )
    if curvature == 'either':
        up, down = bend.format('>'), bend.format('<')
        return AssumptionSpec(
            holds=f'count({up} AND {interior}, over={d}) == 0 OR count({down} AND {interior}, over={d}) == 0',
            where=exists,
            description=description,
        )
    return AssumptionSpec(
        holds=bend.format('<=' if curvature == 'convex' else '>='),
        where=_all_of(frame, interior),
        description=description,
    )


# ---------------------------------------------------------------------------
# the names an entry writes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Emitted:
    """Every name one entry's expansion may write, spelled once for the emitter and the collision check.

    Every name is reserved whichever method the entry declares: which method
    writes which is the method's business, and a collision is the file's
    either way. ``set`` holds the names a method that states a set writes
    through [`mathspec._sos.emit`][].
    """

    name: str
    lam: str
    convexity: str
    set: sos.Emitted
    chord: str
    domain_lo: str
    domain_hi: str
    delta: str
    order: str
    delta_bound: str
    fill_order: str
    binary_order: str
    active_bound: str
    links: tuple[str, ...]
    assumptions: tuple[str, ...]

    @classmethod
    def of(cls, name: str, curve: Piecewise) -> Emitted:
        """The names entry *name* writes, a link's row named after the link."""
        return cls(
            name,
            f'{name}_lam',
            f'{name}_convexity',
            sos.Emitted.of(name, 2),
            f'{name}_chord',
            f'{name}_domain_lo',
            f'{name}_domain_hi',
            f'{name}_delta',
            f'{name}_order',
            f'{name}_delta_bound',
            f'{name}_fill_order',
            f'{name}_binary_order',
            f'{name}_active_bound',
            tuple(f'{name}_{link.name}' for link in curve.links),
            (
                *(f'{name}_{what}' for what in _ASSUMED),
                *(f'{name}_{link.name}_complete' for link in curve.links if link.walks),
            ),
        )

    @property
    def ungated(self) -> str:
        """The second gate row, where the gate variable does not exist."""
        return self.convexity + _UNGATED

    def written(self, method: PiecewiseMethod, *, gated: bool, ungated: bool) -> tuple[str, ...]:
        """The variables and constraints [`expand`][mathspec.spec.Spec.expand] declares for an entry of *method*.

        *gated* is whether the entry names an ``activity:``, and *ungated*
        whether some curve does not read it, as [`leaves_ungated`][] says. The set a
        ``sos2`` or ``adjacency`` entry states is written out too, since
        ``expand()`` writes every set.
        """
        if method == 'lp':
            return (self.chord, self.domain_lo, self.domain_hi)
        if method == 'incremental':
            links = (*self.links, *(row + _UNGATED for row in self.links)) if ungated else self.links
            order = (self.delta_bound, self.fill_order, self.binary_order)
            return (self.delta, self.order, *order, *((self.active_bound,) if gated else ()), *links)
        convexity = (self.convexity, self.ungated) if ungated else (self.convexity,)
        restriction = (self.set.seg, self.set.pick, self.set.link) if method in ('sos2', 'adjacency') else ()
        return (self.lam, *convexity, *self.links, *restriction)

    @property
    def rows(self) -> tuple[str, ...]:
        """Every constraint the entry writes for itself, its link rows aside."""
        return (
            self.convexity,
            self.ungated,
            self.set.pick,
            self.set.link,
            self.set.below,
            self.chord,
            self.domain_lo,
            self.domain_hi,
            self.delta_bound,
            self.fill_order,
            self.binary_order,
            self.active_bound,
            *(row + _UNGATED for row in self.links),
        )

    @property
    def reused(self) -> tuple[str, ...]:
        """Each link row whose name the entry's own rows, variables or assumptions already take."""
        own = {self.lam, self.set.seg, self.delta, self.order, *self.rows, *self.assumptions}
        return tuple(row for row in self.links if row in own)

    @property
    def by_kind(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Each name by the kind of declaration it would collide with."""
        return (
            ('variable', (self.lam, self.set.seg, self.delta, self.order)),
            ('constraint', (*self.rows, *self.links)),
            ('sos', (self.name,)),
            ('assumption', self.assumptions),
        )


def leaves_ungated(gate: VariableSpec | Variable, relation: Relation | None = None) -> bool:
    """Whether a curve gated by *gate*, read through *relation* if any, can run ungated, which takes a second row.

    A masked gate is absent off its mask, and there the curve sums to 1;
    ``missing: 0`` reads the gate as 0 there instead, which one row states.
    A relation declared ``missing: absent`` may have no row for a curve, and
    there the read is absent whatever the gate's ``missing:``. Under
    ``missing: refused`` every curve has a row.
    """
    absent = relation is not None and relation.missing == 'absent'
    return absent or (gate.where is not None and gate.missing != 0)


def gate_of(text: str) -> str | None:
    """The variable an ``activity:`` names, or ``None`` where it is neither a bare name nor ``at(<name>, by=...)``.

    The weights sum to the gate, so it is a binary as written, or read
    through a relation as ``at`` reads it. What the ``by=`` names is
    resolution's to refuse, with the refusals ``at`` gives.
    """
    try:
        node = parse_expression(text)
    except SchemaError:
        return None
    match node:
        case NameNode(name):
            return name
        case FunctionCallNode('at', (NameNode(name),), kwargs) if set(kwargs) == {'by'}:
            return name
        case _:
            return None


def gate_text(text: str, gate: VariableSpec | Variable, read: Expression) -> tuple[str, str | None]:
    """The gate as a curve reads it, and the where a curve reads it under, or ``None`` where every curve does.

    *text* is the ``activity:`` the file wrote, and *read* the expression it
    resolved to. Where [`leaves_ungated`][] says a curve can run ungated,
    the where is the read itself, which exists where the gate and the row of
    its relation both do. Under ``missing: 0`` a walked gate reads 0 off its
    mask, so the relation alone decides, and its name is the where.
    """
    walk = read.columns if isinstance(read, Join) else None
    if not leaves_ungated(gate, None if walk is None else walk.relation):
        return text, None
    return text, text if walk is None or gate.missing != 0 else walk.name


# ---------------------------------------------------------------------------
# the entry as lowering types it
# ---------------------------------------------------------------------------


def resolve_links(name: str, pw: PiecewiseSpec, ns: Namespace, errors: list[str]) -> tuple[Expression, ...] | None:
    """Block *name*'s link expressions typed, in link order, or ``None`` once one failed, its refusal appended.

    A link is read affinely, so it is held to degree 1 where it is read.
    """
    links = [
        resolve_expression_text(link.expression, ns, f"piecewise '{name}' link '{key}'", errors, ceiling=1)
        for key, link in pw.links.items()
    ]
    if any(link is None for link in links):
        return None
    return tuple(link for link in links if link is not None)


def resolve_walks(name: str, pw: PiecewiseSpec, ns: Namespace, errors: list[str]) -> dict[str, JoinColumns] | None:
    """Entry *name*'s walks by link key, each read as ``at(..., by=)`` reads its relation, or ``None`` once one failed.

    The expansion writes a walked row as ``at(<entry>_lam, by=<relation>[<column>])``,
    so a walk is held to every rule that call is held to, and refused here on
    the link the file wrote. Each refusal is appended to *errors*.
    """
    walks: dict[str, JoinColumns] = {}
    failed = False
    weights = frozenset((*pw.dims, pw.along))
    for key, link in pw.links.items():
        if link.by is None:
            continue
        resolver = ExpressionResolver(ns, f"piecewise '{name}' link '{key}'", errors)
        columns = walked_columns(link.by, resolver)
        if columns is None or (walk := resolver.lookup(columns, weights)) is None:
            failed = True
        else:
            walks[key] = walk
    return None if failed else walks


def walked_columns(by: str, resolver: ExpressionResolver) -> ColumnsNode | None:
    """A ``by:`` key as ``at(..., by=)`` reads it, or ``None`` with its refusal appended to *resolver*'s errors.

    The expansion pastes *by* into an ``at`` call as text, so anything but
    ``relation[column, ...]`` is refused before the text is read, and the
    columns are then held to every rule ``at`` holds them to.
    """
    if (columns := columns_of(by)) is None:
        resolver.errors.append(
            f'{resolver.context}: by: {by!r} is not a relation with its columns in brackets. Write '
            f'by: <relation>[<column>], as in at(..., by=).'
        )
        return None
    return resolver.columns_ref(columns, 'at', 'by')


def resolve_gate(
    name: str, pw: PiecewiseSpec, variables: Mapping[str, Variable], ns: Namespace, errors: list[str]
) -> Gate | None:
    """Entry *name*'s gate typed, *variables* being the spec's as lowered, or ``None`` once it failed.

    The gate is resolved as the expression the file wrote, so a walked gate
    is held to every rule ``at(..., by=)`` is held to before anything reads
    its relation. Each refusal is appended to *errors*.
    """
    assert pw.activity is not None
    variable = gate_of(pw.activity)
    assert variable is not None, 'reference_errors refuses a gate of any other shape'
    declared = variables[variable]
    context = f"piecewise '{name}' activity"
    if (read := resolve_expression_text(pw.activity, ns, context, errors, ceiling=1)) is None:
        return None
    _, exists_text = gate_text(pw.activity, declared, read)
    if exists_text is None:
        return Gate(variable, read)
    if not isinstance(read, Join):
        return Gate(variable, read, declared.where)
    exists = mask_of(resolve_condition_text(exists_text, ns, context, errors))
    return None if exists is None else Gate(variable, read, exists)


def lp_domain_refusal(name: str, pw: PiecewiseSpec, links: tuple[Expression, ...]) -> str | None:
    """The refusal for a ``method: lp`` curve whose x-link carries no variable, or ``None``.

    The method bounds the curve's domain with two rows comparing the x-link
    against the first and the last breakpoint, and a row with no variable
    decides nothing. Decided on the link the file wrote, rather than on the
    row the expansion would write under a name the file never declared.
    """
    x = pw.curve[0]
    i, key = next((i, key) for i, (key, link) in enumerate(pw.links.items()) if link is x)
    if carries_variable(links[i]):
        return None
    return (
        f"piecewise '{name}' link '{key}': method: lp bounds the domain with rows on {x.expression!r}, which "
        f'carries no variable. Name a variable in the link, or use method: convex, sos2 or adjacency.'
    )


def declaration_of(
    name: str,
    pw: PiecewiseSpec,
    links: tuple[Expression, ...],
    walks: dict[str, JoinColumns],
    where: Mask | None,
    gate: Gate | None,
    spec: Spec,
) -> Piecewise:
    """Entry *name* as the program carries it, with *links*, *walks*, *where* and *gate* typed, every fit rule decided.

    A walk reads the curve's weights at the entry's own dims, so it drops
    dims of ``dims:``, joins on dims of ``dims:``, and adds dims of its own.
    Each link's row is ``dims:``, or its refinement through the link's walk;
    its expression carries exactly that row, its values parameter varies
    along it and the breakpoint dim and nothing else, and the ``where:``
    tests ``dims:`` and the breakpoint dim alone. A walked row reads the where
    through its relation when the mask carries a dim the walk drops. The gate
    lands inside ``dims:``. Decided here, on the link the file wrote, rather
    than on the rows the expansion writes, whose refusal would name
    ``<entry>_lam``, a variable the author never wrote.

    Raises:
        DimensionError: A walk that does not fit ``dims:``, a link that does
            not fit its row, or a where or a gate outside ``dims:``.
    """
    ctx = f"piecewise '{name}'"
    for key, walk in walks.items():
        _walk_fits(f"{ctx} link '{key}'", pw, walk)
    rows = {key: _row(pw, walks.get(key)) for key in pw.links}
    for node, (key, row) in zip(links, rows.items(), strict=True):
        _link_fits(ctx, key, pw, frozenset(node.dims), row)
    for (key, link), row in zip(pw.links.items(), rows.values(), strict=True):
        _values_fit(spec, ctx, key, pw, link, row)
    _where_fits(ctx, pw, where, walks)
    if gate is not None:
        _gate_fits(ctx, pw, gate, walks)
    carried = frozenset(where.dims if where is not None else ()) - {pw.along}
    typed = tuple(
        Link(
            key,
            node,
            link.values,
            rows[key],
            link.sign,
            link.by,
            walks.get(key),
            _reads(walks.get(key), carried),
        )
        for node, (key, link) in zip(links, pw.links.items(), strict=True)
    )
    return Piecewise(pw.along, typed, pw.method, tuple(pw.dims), where, activity=gate, description=pw.description)


def _walk_fits(ctx: str, entry: PiecewiseSpec, walk: JoinColumns) -> None:
    """A walk reads the curve's weights, which are over ``dims:`` and the breakpoint dim, at dims of ``dims:``.

    ``at`` itself admits more: a lookup at a dim the weights do not carry,
    or into one they do, or through the breakpoint dim. Each is a row that
    reads no curve, one curve twice, or a different curve per breakpoint, so
    it is refused in terms of the entry, where the rewrite is an edit to
    ``dims:`` or to the walk.
    """
    dropped, added = set(walk.dropped_dims), set(walk.added_dims)
    if entry.along in dropped:
        raise DimensionError(
            f"{ctx}: by: {walk.name} looks the curve up at '{entry.along}', the breakpoint dimension, and the row "
            f'of a link uses every breakpoint of its curve. Name a column over one of {list(entry.dims)}.'
        )
    if missing := sorted(dropped - set(entry.dims)):
        raise DimensionError(
            f'{ctx}: by: {walk.name} looks the curve up at {missing}, which is not in dims: {list(entry.dims)}. Name a '
            f'column over one of {list(entry.dims)}, or add {missing} to dims:.'
        )
    if not added:
        raise DimensionError(
            f'{ctx}: by: {walk.name} adds no dimension, because its key {sorted(walk.joined_dims)} is already '
            f'in dims:. Drop the key from dims:, so that the walk adds it.'
        )
    if framed := sorted(added & {*entry.dims, entry.along}):
        raise DimensionError(
            f'{ctx}: by: {walk.name} adds {framed}, which the curve is already over. Walk through a relation '
            f'whose key is over a dimension outside dims: and along:.'
        )
    if entry.along in walk.joined_dims:
        raise DimensionError(
            f"{ctx}: by: {walk.name} is keyed on '{entry.along}', the breakpoint dimension, so a row of the "
            f'link could take each breakpoint from a different curve. Walk through a relation whose key leaves '
            f"out '{entry.along}'."
        )


def _row(entry: PiecewiseSpec, walk: JoinColumns | None) -> tuple[str, ...]:
    """The dims one link's row is built over: ``dims:``, or its refinement through the link's walk.

    The added dims stand where the dropped ones did, so a walked row reads in
    the shape of the curve it ties rather than in relation order.
    """
    if walk is None:
        return tuple(entry.dims)
    dropped, added = set(walk.dropped_dims), sorted(set(walk.added_dims))
    refined: list[str] = []
    for d in entry.dims:
        for kept in added if d in dropped else [d]:
            if kept not in refined:
                refined.append(kept)
    return tuple(refined)


def _reads(walk: JoinColumns | None, carried: frozenset[str]) -> bool:
    """Whether a walked link's row reads the entry's ``where:`` through its relation; ``False`` for one that does not walk.

    A walked row is over the dims the walk adds, where a mask over a dim it
    drops cannot be read as written. Read through the relation it can, as
    ``at`` reads it: the read joins the mask on the dims it carries and
    brings in the rest of the key, which the row is over too (*carried* is
    what the mask carries, the breakpoint dim aside). A mask carrying none
    the walk drops is over dims the row keeps, and reads as written.
    """
    return walk is not None and bool(frozenset(walk.dropped_dims) & carried)


def _link_fits(ctx: str, key: str, entry: PiecewiseSpec, found: frozenset[str], own: tuple[str, ...]) -> None:
    """A link expression carries exactly its row's frame — the rule a constraint's own ``dims:`` holds to.

    Both directions are refused because both broadcast one side of the row.
    A stray dim multiplies the rows the link builds; a missing one repeats
    the same row across it, which pins the expression to one operating point
    along a dimension the curve varies over. Neither is sayable another way,
    so neither is guessed.
    """
    if entry.along in found:
        raise DimensionError(
            f"{ctx}: link '{key}' expression is over the breakpoint dimension '{entry.along}', which only its "
            f'values parameter is over. Sum the expression over {entry.along!r}, or index it by another dimension.'
        )
    if stray := sorted(found - set(own)):
        raise DimensionError(
            f"{ctx}: link '{key}' expression is over {stray}, and its row {list(own)} is not, so every "
            f'coordinate of {stray} would share one curve. Add {stray} to dims:, sum it out, or look the curve '
            f'up through a relation with by: <relation>[<column>].'
        )
    if added := sorted(set(own) - found - set(entry.dims)):
        by = entry.links[key].by
        raise DimensionError(
            f"{ctx}: link '{key}' expression is not over {added}, which by: {by} adds to its row {list(own)}, "
            f'so one value of the expression would lie on every curve along {added} at once. Write an '
            f'expression over {added}, or walk through a relation whose key leaves out {added}.'
        )
    if missing := sorted(set(own) - found):
        raise DimensionError(
            f"{ctx}: link '{key}' expression is not over {missing}, and its row {list(own)} is, so one value "
            f'of the expression would lie on every curve along {missing} at once. Drop {missing} from dims:, '
            f'or write an expression over {missing}.'
        )


def _values_fit(
    spec: Spec, ctx: str, key: str, entry: PiecewiseSpec, link: PiecewiseLinkSpec, own: tuple[str, ...]
) -> None:
    """A values parameter varies along its own link's row and the breakpoint dim, and nothing else.

    Its own link's, because a walked link's curve is read per fine
    coordinate: ``bp_power`` is per flow where the entry's frame is per
    converter, and comparing it against the frame would refuse it.
    """
    if stray := [d for d in spec.parameters[link.values].dims if d != entry.along and d not in own]:
        rewrite = (
            f"Drop {stray} from '{link.values}', or add {stray} to dims:."
            if link.by is None
            else f"by: {link.by} sets that row, so declare '{link.values}' over dimensions of {list(own)} and "
            f"'{entry.along}'."
        )
        raise DimensionError(
            f"{ctx}: link '{key}' values parameter '{link.values}' is over {stray}, and its row {list(own)} "
            f'is not, so a row of the link would have no single curve. {rewrite}'
        )


def _where_fits(ctx: str, entry: PiecewiseSpec, where: Mask | None, walks: dict[str, JoinColumns]) -> None:
    """An entry's ``where:`` tests ``dims:`` and the breakpoint dim, and nothing else.

    A walked link's values parameter carries the link's own row, so a where
    naming it is refused here too: raggedness is the curve's. A dim a walk
    produces is refused without the advice to add it to ``dims:``, which the
    walk would then refuse.
    """
    dims = where.dims if where is not None else ()
    stray = sorted(set(dims) - set(entry.dims) - {entry.along})
    for key, walk in walks.items():
        if into := [d for d in stray if d in walk.added_dims]:
            raise DimensionError(
                f"{ctx}: where {entry.where!r} tests {into}, which link '{key}' adds through its relation. A "
                f'where: sets which curves exist, one per coordinate of dims: {list(entry.dims)}, and only the rows of '
                f'the link are over {into}. Test {list(entry.dims)} in the where:, or declare a where: over {into} on '
                f'the variable of the link, so that its rows are absent.'
            )
    if stray:
        raise DimensionError(
            f'{ctx}: where {entry.where!r} tests {stray}, which is not in dims: {list(entry.dims)}. A where: sets '
            f'which curves exist, and cannot add coordinates. Add {stray} to dims:, or drop it from the where:.'
        )


def _gate_fits(ctx: str, entry: PiecewiseSpec, gate: Gate, walks: dict[str, JoinColumns]) -> None:
    """An entry's gate is over dims of ``dims:`` once it is looked up, and nothing else.

    The advice to add a stray dim to ``dims:`` is left out where ``dims:``
    would refuse it: the breakpoint dim, and a dim a walk adds.
    """
    if not (stray := sorted(set(gate.read.dims) - set(entry.dims))):
        return
    unlistable = {entry.along, *(d for walk in walks.values() for d in walk.added_dims)}
    listable = not unlistable & set(stray)
    if entry.activity != gate.variable:
        found = f'over {stray} after the lookup'
        rewrite = 'Look it up through a relation that leaves it over dims:' + (
            f', or add {stray} to dims:.' if listable else '.'
        )
    else:
        found = f'over {stray}'
        rewrite = (f'Add {stray} to dims:, or gate' if listable else 'Gate') + (
            f' with a variable over dims:, or read the gate through a relation with '
            f'activity: at({gate.variable}, by=<relation>[<column>]).'
        )
    raise DimensionError(
        f"{ctx}: activity '{gate.variable}' is {found}, which is not in dims: {list(entry.dims)}. The gate switches "
        f'the curve of one coordinate of dims:. {rewrite}'
    )


# ---------------------------------------------------------------------------
# the rows an entry writes
# ---------------------------------------------------------------------------


class _Expansion:
    """One ``piecewise:`` entry, written out into the raw spec.

    Every rule the entry is held to was decided as the spec loaded, so what
    is left is writing: the link text the file wrote, on the row the program
    says each link builds, under the where each row reads.
    """

    def __init__(self, spec: Spec, raw: dict[str, object], name: str, pw: PiecewiseSpec, curve: Piecewise) -> None:
        self.spec = spec
        self.raw = raw
        self.name = name
        self.pw = pw
        self.curve = curve
        self.emitted = Emitted.of(name, curve)
        self.frame = list(curve.frame)
        self.mask, self.frame_mask, self.exists = _masks(pw.where, pw.along, ragged=curve.ragged)

    def expand(self) -> None:
        """Write the entry's declarations into the raw spec."""
        if self.pw.method == 'lp':
            self._segment_lines()
        elif self.pw.method == 'incremental':
            self._increments()
        else:
            self._weights()
        self._assumptions()

    def _assumptions(self) -> None:
        """What the method assumes of the numbers, written into the spec the expansion returns.

        A formulation states its conditions the way it states its rows, so a
        spec that has been written out carries them as language rather than
        as something a consumer has to know to ask for.
        """
        assumptions = sos.section(self.raw, 'assumptions')
        for name, assumed in assumptions_of(self.name, self.curve, self.pw.where).items():
            assumptions[name] = assumed.model_dump()

    # -- emitters ----------------------------------------------------------

    def _constraint(self, name: str, dims: Iterable[str], expression: str, where: str | None = None) -> None:
        sos.section(self.raw, 'constraints')[name] = {
            'dims': list(dims),
            **({'where': where} if where else {}),
            'expression': expression,
        }

    def _weights(self) -> None:
        """The convex-combination form: weights, their convexity, a row per link, and the method's restriction."""
        pw, emitted, d = self.pw, self.emitted, self.pw.along
        sos.section(self.raw, 'variables')[emitted.lam] = {
            'dims': [*self.frame, d],
            **({'where': pw.where} if pw.where else {}),
            'bounds': {'lower': 0.0, 'upper': 1.0},
            'description': 'convex-combination weight on a breakpoint',
        }
        for suffix, where, gate in self._gate_rows():
            self._constraint(
                emitted.convexity + suffix,
                self.frame,
                f'sum({emitted.lam}, over={d}) == {"1" if gate is None else f"({gate})"}',
                _all_of(self.exists, where),
            )
        for cname, written, link in zip(emitted.links, pw.links.values(), self.curve.links, strict=True):
            self._constraint(
                cname,
                link.dims,
                f'({written.expression}) {link.sign} sum({self._weights_read(link)} * {link.values}, over={d})',
                _on_walk(self.exists, link),
            )
        if pw.method in ('sos2', 'adjacency'):
            sos.section(self.raw, 'sos')[self.name] = {'variable': emitted.lam, 'along': d, 'type': 2}

    def _increments(self) -> None:
        """The incremental form: a fill fraction per segment, filled in order, and a row per link.

        ``linopy``'s ``_add_incremental`` under its names. A segment sits at
        its lower breakpoint, so ``delta`` exists where the next breakpoint
        does too. Each link is its value at the curve's first breakpoint, times
        the gate, plus every filled fraction of each segment's rise; the row
        stands at that first breakpoint, where the value is read. A gate that
        does not exist everywhere splits each link row in two, as it splits
        the convexity row of the weights.
        """
        pw, emitted, d = self.pw, self.emitted, self.pw.along
        dims = [*self.frame, d]
        pieces = _all_of(self.frame_mask, _pieces(d, self.mask))
        variables = sos.section(self.raw, 'variables')
        variables[emitted.delta] = {
            'dims': dims,
            'where': pieces,
            'bounds': {'lower': 0.0, 'upper': 1.0},
            'description': 'the filled fraction of a segment',
        }
        variables[emitted.order] = {
            'dims': dims,
            'where': pieces,
            'domain': 'binary',
            'description': '1 where a segment may be filled, which the one before it must be first',
        }
        self._constraint(emitted.delta_bound, dims, f'{emitted.delta} <= {emitted.order}')
        self._constraint(emitted.fill_order, dims, f'{emitted.delta} <= shift({emitted.delta}, along={d}, offset=1)')
        self._constraint(emitted.binary_order, dims, f'{emitted.order} <= shift({emitted.delta}, along={d}, offset=1)')
        if (gate := self._gate_rows()[0][2]) is not None:
            self._constraint(emitted.active_bound, dims, f'{emitted.delta} <= {gate}')
        first = _all_of(self.frame_mask, _edge(d, self.mask, 'first'))
        for cname, written, link in zip(emitted.links, pw.links.values(), self.curve.links, strict=True):
            filled = f'sum({_walked(emitted.delta, self.frame, link)} * ({_back(link.values, d, -1)} - {link.values}), over={d})'
            for suffix, where, gate in self._gate_rows(link):
                start = link.values if gate is None else f'{link.values} * ({gate})'
                self._constraint(
                    cname + suffix,
                    [*link.dims, d],
                    f'({written.expression}) {link.sign} {start} + {filled}',
                    _all_of(_on_walk(first, link), where),
                )

    def _weights_read(self, link: Link) -> str:
        """How one link reads the curve's weights: by name, or through the relation that refines its frame.

        The walk is an ``at``, so the weights stay on the curve's own frame and
        the spec never names them — which is the whole reason the entry emits
        the row rather than the file writing it.
        """
        if not link.walks:
            return self.emitted.lam
        return f'at({self.emitted.lam}, by={link.by})'

    def _gate_rows(self, link: Link | None = None) -> tuple[tuple[str, str | None, str | None], ...]:
        """What the weights sum to, as ``(name suffix, where, gate)``, the gate ``None`` where they sum to 1.

        One row where the gate exists at every coordinate the entry builds a curve
        for, and **two** where it does not. A gate is a variable, so a masked one
        has coordinates where it does not exist — and there the entry is ungated,
        which is the ``1`` an entry with no ``activity:`` gets. Written as a single
        row it would instead be *no row*: absence does not spread out of a
        reduction, so the right-hand side would take the row with it and leave the
        weights without the convexity that makes them a curve at all (#1158).

        ``missing: 0`` is the other reading and stays one row — the gate is 0
        where it does not exist, so the curve is pinned off there. A gate read
        through a relation declared ``missing: absent`` takes two whatever its
        ``missing:``, since the relation may have no row for a curve.

        *link* reads the gate and its where as its row does: through its
        relation where either carries a dim the walk drops.
        """
        gate, activity = self.curve.activity, self.pw.activity
        if gate is None or activity is None:
            return (('', None, None),)
        read, exists = gate_text(activity, self.spec.variables[gate.variable], gate.read)
        read = _walked(read, gate.read.dims, link)
        if exists is None:
            return (('', None, read),)
        assert gate.exists is not None
        exists = _walked(exists, gate.exists.dims if isinstance(gate.read, Join) else gate.read.dims, link)
        return (('', exists, read), (_UNGATED, f'NOT {_operand(exists)}', None))

    def _segment_lines(self) -> None:
        """The segment-line form: a row per segment, and the two domain rows.

        The chord sits at the later breakpoint, so the first has none and its
        ``where:`` and ``edge=0`` travel together — without the exclusion the
        vacated position is a spurious line through the origin; under a mask the
        first breakpoint is the curve's own. The row is multiplied through by the
        run rather than dividing, which keeps its sense only because the
        breakpoints are strictly monotone. The domain rows are ``linopy``'s
        ``_add_lp`` rows under its names, each sitting on the edge of the curve
        the mask marks, which is why the mask has to be one run. Every row here
        is written from the link expressions and the breakpoint values, none of
        which the entry masks, so a ``where`` over the frame alone is conjoined
        onto each rather than inherited as the weight rows inherit it.
        """
        pw, emitted, d = self.pw, self.emitted, self.pw.along
        x_link, y_link = pw.curve
        mask, frame = self.mask, self.frame_mask
        dims = (*self.frame, d)
        run = f'({x_link.values} - {_back(x_link.values, d, 1)})'
        rise = f'({y_link.values} - {_back(y_link.values, d, 1)})'
        self._constraint(
            emitted.chord,
            dims,
            f'({y_link.expression}) * {run} {y_link.sign} '
            f'{rise} * (({x_link.expression}) - {x_link.values}) + {y_link.values} * {run}',
            _all_of(frame, _neighbours(d, mask)),
        )
        for cname, sense, end in ((emitted.domain_lo, '>=', 'first'), (emitted.domain_hi, '<=', 'last')):
            self._constraint(
                cname, dims, f'({x_link.expression}) {sense} {x_link.values}', _all_of(frame, _edge(d, mask, end))
            )


def refused_under_where(program: Program, spec: Spec) -> Iterator[str]:
    """A refusal for each values parameter of a curve with a ragged ``where:`` that reads a missing row as ``refused``.

    A ragged ``where:`` says the curve stops short of the breakpoint dim, so
    its tables have no row past the mask by design. ``refused`` says every
    row is there: the curve never runs short.
    """
    for entry_name, curve in program.piecewise.items():
        if not curve.ragged:
            continue
        for name in dict.fromkeys(link.values for link in curve.links):
            if 'refused' in spec.parameters[name].readings:
                yield (
                    f"parameter '{name}' is refused where a row is missing, and it is a values parameter of "
                    f"piecewise '{entry_name}' under where: '{spec.piecewise[entry_name].where}', which sets where "
                    f'each curve ends. Declare missing: absent, or a value of its dtype.'
                )


def expand_piecewise(spec: Spec) -> Spec:
    """*spec* with every ``piecewise:`` entry written out — *spec* itself where it declares none.

    A ``method: adjacency`` entry states its restriction as the set
    ``method: sos2`` states, and then that set is written out here too: the
    binaries are what the method *is*, so the spec that comes back carries no
    set of its own ([`mathspec._sos.emit`][] is where they are spelled).
    Each entry's rows and names are read off the program *spec* lowered to.
    """
    if not spec.piecewise:
        return spec
    program = spec.program
    raw = spec.model_dump()
    raw.setdefault('variables', {})
    raw.setdefault('constraints', {})
    for name, pw in spec.piecewise.items():
        _Expansion(spec, raw, name, pw, program.piecewise[name]).expand()
    raw['piecewise'].clear()
    for name, pw in spec.piecewise.items():
        if pw.method == 'adjacency':
            sos.emit(raw, name)
    return Spec.model_validate(raw)
