# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Name resolution — the pass that reads the syntax tree into the program vocabulary.

The grammars emit bare names and calls; resolution builds the
[`mathspec.program`][] node each stands for, so every pass after — the dim
rules, the degree rules, the typesetter, lowering — reads one vocabulary. This
module holds the [`Namespace`][] a resolution reads names from and the doors
lowering calls, one per kind of text; the walks are
[`ExpressionResolver`][] for arithmetic and
[`WhereResolver`][] for a where string. The rules
live in the language reference.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

import mathspec.degree as degree
from mathspec._expression_parser import (
    ArithmeticNode,
    ComparisonNode,
    NameNode,
    nodes,
)
from mathspec._expression_resolver import ExpressionResolver
from mathspec._where_parser import (
    UnresolvedWhereNode,
    nested,
    parse_where,
)
from mathspec._where_resolver import WhereResolver
from mathspec.errors import LanguageError, SchemaError, case_context, prefixed
from mathspec.exclusivity import overlapping
from mathspec.expansion import expand, parse_and_expand
from mathspec.program import (
    BooleanLiteral,
    Cases,
    Expression,
    ExpressionReference,
    Mask,
    MaskReference,
    Predicate,
    Region,
    Relation,
    VariableDefined,
    carries_variable,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from mathspec._expression_parser import ComparisonOperator, ParsedNode
    from mathspec._where_parser import ParsedWhere
    from mathspec.program import DeclaredDtype
    from mathspec.spec import ExpressionSpec, MaskSpec, Spec


#: What a name a file may write turns out to be. Answered by
#: [`Namespace.kind`][], so a pass reading a name switches over this rather
#: than over the stores it would otherwise have to try in order.
NameKind = Literal['variable', 'parameter', 'dimension', 'relation']


class Namespace:
    """The declared names of one spec, by kind — the whole of what a file may name, read once.

    A name has one kind: validation.py refuses one declared under two sections.
    """

    __slots__ = (
        '_loading',
        '_masks',
        '_named',
        'bodies',
        'constraints',
        'defaults',
        'dimensions',
        'dtypes',
        'given_masks',
        'leaf_dims',
        'masks',
        'parameters',
        'relations',
        'spec',
        'variables',
    )

    def __init__(self, spec: Spec) -> None:
        #: The spec the names come from — what an expression is expanded and
        #: dim-checked against, since macros, named expressions and the dim
        #: rules read entries the flat listing below does not carry.
        self.spec = spec
        variables = {**spec.variables, **spec.given.variables, **spec.given.expressions}
        parameters = {**spec.parameters, **spec.given.parameters}
        self.variables = frozenset(variables)
        self.bodies = frozenset(spec.expressions)
        #: The declared masks, read by name wherever a where string is.
        self.masks = frozenset(spec.masks)
        #: The masks this file reads under ``given:``. A where reads each as
        #: the boolean data it is to this file, so each is a parameter here too.
        self.given_masks = frozenset(spec.given.masks)
        self.parameters = frozenset(parameters) | self.given_masks
        self.dimensions = frozenset(spec.dimensions)
        #: The declared constraint names, off the flat namespace: a bare name
        #: never reaches them, so a spec may name a constraint after a variable.
        #: Consulted only in ``dual()``'s argument position.
        self.constraints = frozenset({**spec.constraints, **spec.given.constraints})
        #: name -> declared dtype, for dimensions, parameters and relations alike;
        #: what a where comparison checks its literal against.
        self.dtypes: dict[str, DeclaredDtype] = {
            **{p: pd.dtype for p, pd in parameters.items()},
            **{m: cast('DeclaredDtype', 'bool') for m in spec.given.masks},
            **{d: dd.dtype for d, dd in spec.dimensions.items()},
        }
        #: parameter name -> the value its ``missing:`` reads a missing row as,
        #: for the parameters that name one; what a where comparison reads there.
        self.defaults: dict[str, bool | float] = {
            p: pd.missing for p, pd in spec.parameters.items() if not isinstance(pd.missing, str)
        }
        #: relation name -> its columns and key, as declared.
        self.relations: dict[str, Relation] = {
            n: Relation(lk.pairs, lk.key_roles, lk.missing, lk.description) for n, lk in spec.relations.items()
        }
        #: parameter or variable name -> the dims it is read through —
        #: parameters by their ``dims``, variables by their frame. Stamped onto
        #: each leaf a where names, the way a relation leaf carries ``over``.
        self.leaf_dims: dict[str, tuple[str, ...]] = {
            **{p: tuple(pd.dims) for p, pd in parameters.items()},
            **{m: tuple(md.dims) for m, md in spec.given.masks.items()},
            **{v: tuple(vd.dims or ()) for v, vd in variables.items()},
        }
        #: named expression -> its resolved node, or ``None``, and its refusals;
        #: filled the first time anything reads the name.
        self._named: dict[str, tuple[ExpressionReference | None, tuple[str, ...]]] = {}
        #: The named expressions and masks waiting to be resolved, the one
        #: asked for first — each above the entries it reads, so it is a cycle's chain.
        self._loading: list[str] = []
        #: mask -> its resolved node, or ``None``, and its refusals; filled
        #: the first time anything reads the name.
        self._masks: dict[str, tuple[MaskReference | None, tuple[str, ...]]] = {}

    def named(self, name: str, context: str) -> ExpressionReference:
        """The ``expressions:`` entry *name* as the node that stands where its name is written.

        Resolved under the entry's own context the first time it is asked
        for, and read from then on, so a fault in it is reported once.

        Raises:
            SchemaError: The entry reads itself, or does not load.
        """
        if (refusal := self.cycle(name, context)) is not None:
            raise SchemaError(refusal)
        node, _ = self.named_entry(name)
        if node is None:
            msg = f"{context}: named expression '{name}' does not load. Its refusal is listed with it."
            raise SchemaError(msg)
        return node

    def cycle(self, name: str, context: str, through: Iterable[str] = (), *, noun: str = 'expression') -> str | None:
        """The refusal for reading *name* while it is being resolved, or ``None``; *through* names the macros the read went through."""
        if name not in self._loading:
            return None
        chain = ' -> '.join([*self._loading[self._loading.index(name) :], *through, name])
        return f'{context}: circular {noun} reference: {chain}'

    def mask(self, name: str, context: str) -> MaskReference:
        """The ``masks:`` entry *name* as the node that stands where its name is written.

        Resolved under the entry's own context the first time it is asked
        for, and read from then on, so a fault in it is reported once.

        Raises:
            SchemaError: The entry reads itself, or does not load.
        """
        if (refusal := self.cycle(name, context, noun='mask')) is not None:
            raise SchemaError(refusal)
        node, _ = self.mask_entry(name)
        if node is None:
            msg = f"{context}: mask '{name}' does not load. Its refusal is listed with it."
            raise SchemaError(msg)
        return node

    def mask_entry(self, name: str) -> tuple[MaskReference | None, tuple[str, ...]]:
        """The ``masks:`` entry *name* resolved, or ``None``, with every refusal it earned."""
        if name not in self._masks:
            self._loading.append(name)
            errors: list[str] = []
            node = _mask(name, self.spec.masks[name], self, errors)
            self._loading.pop()
            self._masks[name] = (node, tuple(errors))
        return self._masks[name]

    def named_entry(self, name: str) -> tuple[ExpressionReference | None, tuple[str, ...]]:
        """The ``expressions:`` entry *name* resolved, or ``None``, with every refusal it earned.

        The entries it reads are resolved before it, walked from a stack that
        holds the path of reads from *name* rather than by recursing into
        each, so a chain of entries however long costs no stack. An entry
        that reads one on the path is a cycle, which [`named`][] refuses
        with that path when the resolution reaches the read.
        """
        base = len(self._loading)
        self._loading.append(name)
        while len(self._loading) > base:
            top = self._loading[-1]
            if top in self._named:
                self._loading.pop()
                continue
            waiting = [n for n in self._references(top) if n not in self._named and n not in self._loading]
            if waiting:
                self._loading.append(waiting[0])
                continue
            errors: list[str] = []
            node = _named(top, self.spec.expressions[top], self, errors)
            self._named[top] = (node, tuple(errors))
            self._loading.pop()
        return self._named[name]

    def _references(self, name: str) -> tuple[str, ...]:
        """The ``expressions:`` entries the texts of entry *name* read, macros expanded, in first-mention order.

        A text that does not parse or expand reads nothing here: the
        resolution that follows reports it.
        """
        entry, context = self.spec.expressions[name], f"Named expression '{name}'"
        arithmetic: list[ParsedNode] = []
        for text in (entry.expression, *(case.expression for case in (entry.cases or {}).values()), entry.otherwise):
            if text is not None:
                try:
                    arithmetic.append(parse_and_expand(text, self, context))
                except ValueError:
                    continue
        for case in (entry.cases or {}).values():
            try:
                pending: list[ParsedWhere] = [parse_where(case.when)]
            except ValueError:
                continue
            while pending:
                node = pending.pop()
                if isinstance(node, ArithmeticNode):
                    try:
                        arithmetic.append(expand(node, self, context))
                    except ValueError:
                        continue
                else:
                    pending.extend(nested(node))
        names = (n.name for n in nodes(*arithmetic) if isinstance(n, NameNode) and n.name in self.bodies)
        return tuple(dict.fromkeys(names))

    def unordered(self, name: str) -> bool:
        """Whether the declared dimension *name* is one whose order the file does not declare part of the model."""
        return not self.spec.dimensions[name].ordered

    def kind(self, name: str) -> NameKind | None:
        """What *name* was declared as, or ``None`` where the file declares it nowhere."""
        if name in self.variables:
            return 'variable'
        if name in self.parameters:
            return 'parameter'
        if name in self.dimensions:
            return 'dimension'
        if name in self.relations:
            return 'relation'
        return None

    def unknown(self, name: str, context: str, *, allow_dims: bool, formals: Iterable[str] = ()) -> str:
        """The refusal for a *name* declared nowhere, listing what it could have been.

        Args:
            name: The name the file wrote.
            context: The entry it was found in.
            allow_dims: Whether a dimension would have been accepted there. It marks a
                where string, which reads a relation as readily as a parameter, so the
                listing carries the relations too; an expression, where a relation is not a
                value, lists the variables instead.
            formals: A macro's formals, listed first when there are any.
        """
        shown: list[tuple[str, Iterable[str]]] = [('Formals', formals)] if formals else []
        shown += (
            [
                ('Parameters', self.parameters),
                ('Dimensions', self.dimensions),
                ('Relations', self.relations),
                *([('Masks', self.masks)] if self.masks else []),
            ]
            if allow_dims
            else [('Variables', self.variables), ('Parameters', self.parameters)]
        )
        listing = '\n'.join(f'  {kind}: {sorted(names)}' for kind, names in shown)
        return f"{context}: '{name}' not found.\n{listing}\nCheck for typos, or ensure '{name}' is declared."

    def unknown_constraint(self, name: str, context: str, *, formals: Iterable[str] = ()) -> str:
        """The refusal for a ``dual(name)`` naming no constraint — nor, inside a template, a formal."""
        also = ' or a formal of this macro' if formals else ''
        return (
            f"{context}: dual({name}): '{name}' is not a declared constraint{also}.\n"
            f'  Constraints: {sorted(self.constraints)}\n'
            f"Check for typos, or declare '{name}': under 'constraints:' if this file builds the row, "
            f"or under 'given: constraints:' if it reads the dual of a row another model builds."
        )


# ---------------------------------------------------------------------------
# the seam the rest of the package uses
# ---------------------------------------------------------------------------


def mask_of(node: Predicate | None) -> Mask | None:
    """The mask an entry carries for a resolved where: ``None`` where there is none, or where every row passes."""
    if node is None or (isinstance(node, BooleanLiteral) and node.value):
        return None
    return Mask(node)


def remainder(masks: Iterable[Mask]) -> Mask:
    """The region left over: where not one of *masks* holds.

    The ``otherwise`` arm's own mask, built rather than written. ``cases:``
    carries at least one case, so there is no vacuous truth to spell.
    """
    first, *rest = masks
    left = ~first
    for mask in rest:
        left = left & ~mask
    return left


# ---------------------------------------------------------------------------
# expressions
# ---------------------------------------------------------------------------


def resolve_expression(
    node: ArithmeticNode,
    ns: Namespace,
    context: str,
    errors: list[str],
    *,
    formals: frozenset[str] = frozenset(),
) -> Expression | None:
    """Build the program tree *node* stands for, checking every name and operator call shape on the way.

    Returns:
        The tree, or ``None`` once anything failed — appending to *errors*
        rather than raising, so a caller collecting problems across a whole
        spec reports them together. Also ``None``, with nothing appended,
        where a name in *formals* stands under *node*: a macro template is
        checked by the rules a call site is before anything calls it, and
        only the call site that binds its formals has a tree to build.

    """
    before = len(errors)
    resolved = ExpressionResolver(ns, context, errors, formals=formals).build(node)
    return None if len(errors) > before else resolved


def resolve_where(
    node: Predicate | UnresolvedWhereNode,
    ns: Namespace,
    context: str,
    errors: list[str],
    self_variable: str | None = None,
) -> Predicate | None:
    """Rewrite a parsed where AST into typed predicates, folded as [`Mask`][] folds.

    Returns:
        The typed tree — a mask admitting every row or none comes back as the
        one ``BooleanLiteral`` — or ``None`` once anything failed, with the
        problems appended to *errors*.
    """
    before = len(errors)
    resolved = WhereResolver(ns, context, errors, self_variable).where(node)
    return None if len(errors) > before else Mask(cast('Predicate', resolved)).root


def resolve_where_text(
    text: str | None,
    ns: Namespace,
    context: str,
    errors: list[str],
    self_variable: str | None = None,
) -> Predicate | None:
    """Parse and resolve one where string as [`resolve_where`][] does, a parse failure appended to *errors*.

    Returns:
        ``None`` where there is no mask to read, and where reading it failed.
    """
    if text is None:
        return None
    try:
        node = parse_where(text)
    except ValueError as e:
        errors.append(f'{context}: {e}')
        return None
    return resolve_where(node, ns, context, errors, self_variable)


def resolve_expression_text(
    text: str, ns: Namespace, context: str, errors: list[str], *, ceiling: int | None
) -> Expression | None:
    """Parse, expand, resolve and degree-check one expression string that stands for a value.

    *ceiling* is the degree the position honours, and ``None`` for an
    ``expressions:`` entry's body: what the math admits
    ([`check_expression`][mathspec.degree.check_expression]) is a rule about the position
    that *reads* it, so it fires on the expanded tree of every objective and
    piecewise link, and not where an entry is declared. A constraint is
    [`resolve_constraint_text`][]'s.

    Returns:
        The typed tree, or ``None`` once anything failed, the problem appended
        to *errors*.
    """
    ast = _parsed(text, ns, context, errors)
    if ast is None:
        return None
    if isinstance(ast, ComparisonNode):
        errors.append(f'{context}: expression must not contain a comparison operator.\nGot: {text!r}')
        return None
    resolved = resolve_expression(ast, ns, context, errors)
    if resolved is None or ceiling is None:
        return resolved
    return None if _over_the_ceiling(resolved, context, errors, ceiling=ceiling) else resolved


def resolve_constraint_text(
    text: str, ns: Namespace, context: str, errors: list[str]
) -> tuple[Expression, ComparisonOperator, Expression] | None:
    """Parse, expand, resolve and degree-check one constraint string: exactly one comparison, a variable on a side (#1171).

    Returns:
        The two sides and the sense between them, or ``None`` once anything
        failed, the problem appended to *errors*.
    """
    ast = _parsed(text, ns, context, errors)
    if ast is None:
        return None
    if not isinstance(ast, ComparisonNode):
        errors.append(
            f'{context}: expression must contain exactly one comparison operator (<=, >=, ==).\nGot: {text!r}'
        )
        return None
    found = len(errors)
    resolver = ExpressionResolver(ns, context, errors)
    left, right = resolver.build(ast.left), resolver.build(ast.right)
    if len(errors) > found or left is None or right is None:
        return None
    if any(_over_the_ceiling(side, context, errors, ceiling=2) for side in (left, right)):
        return None
    if not (carries_variable(left) or carries_variable(right)):
        errors.append(
            f'{context}: neither side of the comparison carries a variable, so the row decides nothing.\n'
            f'Got: {text!r}\n'
            f'A constraint is a claim about a decision, and a comparison of numbers and parameters '
            f'is settled before the solve — no consumer builds a row for it. Name the variable it should '
            f'bound, or state the fact under `assumptions:`, where the consumer attaching the data checks it.'
        )
        return None
    return left, ast.op, right


def _parsed(text: str, ns: Namespace, context: str, errors: list[str]) -> ComparisonNode | ArithmeticNode | None:
    """*text* parsed and its macros expanded, or ``None`` with the refusal appended."""
    try:
        return parse_and_expand(text, ns, context)
    except ValueError as e:
        errors.append(prefixed(context, e))
        return None


def _over_the_ceiling(node: Expression, context: str, errors: list[str], *, ceiling: int) -> bool:
    """Whether *node* breaks the degree rules at *ceiling*, the refusal appended."""
    try:
        degree.check_expression(node, context, ceiling=ceiling)
    except LanguageError as e:
        errors.append(str(e))
        return True
    return False


def _named(name: str, entry: ExpressionSpec, ns: Namespace, errors: list[str]) -> ExpressionReference | None:
    """One ``expressions:`` entry as the node every use of it holds, or ``None`` once anything in it failed.

    A cased entry's arms are checked one by one, so every fault is collected
    rather than the first, and proved apart only once all of them resolve.
    The ``otherwise`` arm becomes the region left over, so a consumer adds
    regions rather than working out which one is left; the language proved
    the rest apart, so the regions are disjoint and total.
    """
    context = f"Named expression '{name}'"
    if not entry.cases:
        assert entry.expression is not None
        body = resolve_expression_text(entry.expression, ns, context, errors, ceiling=None)
        return None if body is None else ExpressionReference(name, body)

    found = len(errors)
    regions: list[Region] = []
    masks: dict[str, Predicate] = {}
    for case_name, case in entry.cases.items():
        arm_context = case_context(name, case_name)
        when = resolve_where_text(case.when, ns, arm_context, errors)
        if isinstance(when, BooleanLiteral):
            errors.append(_constant_arm(arm_context, value=when.value))
        elif when is not None:
            masks[case_name] = when
        value = resolve_expression_text(case.expression, ns, arm_context, errors, ceiling=None)
        if when is not None and value is not None:
            regions.append(Region(Mask(when), value))
    assert entry.otherwise is not None
    fallback = resolve_expression_text(entry.otherwise, ns, case_context(name, None), errors, ceiling=None)
    if len(errors) > found or fallback is None:
        return None
    errors.extend(f'{context}: {problem}' for problem in overlapping(masks, ns.dtypes, ns.defaults))
    if len(errors) > found:
        return None
    left_over = Region(remainder(region.when for region in regions), fallback)
    return ExpressionReference(name, Cases((*regions, left_over)))


def _mask(name: str, entry: MaskSpec, ns: Namespace, errors: list[str]) -> MaskReference | None:
    """One ``masks:`` entry as the node every use of it holds, or ``None`` once anything in it failed.

    A predicate the connectives decide is refused, since a name for every row
    or for none narrows nothing a where could not say plainly.
    """
    context = f"Mask '{name}'"
    body = resolve_where_text(entry.where, ns, context, errors)
    if body is None:
        return None
    if isinstance(body, BooleanLiteral):
        errors.append(
            f'{context}: the predicate {entry.where!r} folds to {str(body.value).lower()}, so the mask '
            f'{"admits every row" if body.value else "admits no row"} and names nothing a where needs. '
            f'Delete it, or write the predicate over the data.'
        )
        return None
    return MaskReference(name, body)


def self_existence(where: Predicate, variable: str, context: str) -> str | None:
    """The refusal for a variable whose own where asks, through a mask, whether it exists — or ``None``.

    The where resolver refuses the bare name; a mask's predicate is resolved
    under its own name, so the check runs again on the tree with every mask's
    predicate in it.
    """
    if not any(isinstance(atom, VariableDefined) and atom.name == variable for atom in Mask(where).atoms):
        return None
    return (
        f"{context}: variable '{variable}' asks whether it exists in its own where, through a mask, which "
        f'nothing can answer — the mask is what decides where it exists. Test a parameter, or another '
        f'variable declared before it.'
    )


def _constant_arm(context: str, *, value: bool) -> str:
    """The refusal for a case arm whose mask the connectives already decided.

    Cases are proved apart rather than ranked, so an always-true arm is not
    one that shadows the arms under it — it is one no other arm can be proved
    apart from, and the ``otherwise`` it leaves is empty. An always-false arm
    is the plainer half: nothing to apply to.
    """
    if value:
        return (
            f'{context}: the mask admits every row, so no other arm can hold anywhere '
            f'and `otherwise:` covers nothing. Write the expression without `cases:`, '
            f'or narrow the `when`.'
        )
    return f'{context}: the mask admits no row, so this arm never applies. Delete the arm, or widen the `when`.'
