# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The closed set of built-in operators and their call shapes.

One home for each signature: a composition is a macro, and the set is closed
to a file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class Builtin:
    """The call shape of one built-in operator.

    Keyword arguments come in four kinds, and the kind decides what resolution
    turns the value into: ``dimension_kwargs`` name a dimension or a list of
    them (``sum(x, over=generator)``); ``column_kwargs`` name columns of one
    relation, written ``relation[column, …]`` (``sum(x, over=generator,
    by=gen_bus[bus])``), and beside one a ``dimension_kwargs`` name is a
    column of that relation where it has one; ``edge_kwargs`` take a closed
    keyword or a number;
    ``required_value_kwargs`` are ordinary values that must be present — a
    number, never a name to resolve (``shift(..., offset=1)``).

    Every operator takes one positional argument, the expression; every
    dimension or column it names arrives in a kwarg *value*, which is what
    lets a macro pass one as a formal. ``usage`` is the wording every refusal
    quotes back.
    """

    usage: str
    dimension_kwargs: tuple[str, ...] = ()
    column_kwargs: tuple[str, ...] = ()
    edge_kwargs: tuple[str, ...] = ()
    required_value_kwargs: tuple[str, ...] = ()
    #: Keyword arguments the call may omit. Their *kind* still comes from the
    #: tuples above. This says only that the operator has a result without them.
    optional_kwargs: tuple[str, ...] = ()
    #: Kwargs required exactly when the call names columns. A sum through a
    #: relation names the columns that leave, so the key columns it keeps are
    #: the ones it does not name.
    with_columns: tuple[str, ...] = ()

    @property
    def required(self) -> frozenset[str]:
        """Every keyword the call must carry."""
        return (
            frozenset(self.dimension_kwargs) | frozenset(self.column_kwargs) | frozenset(self.required_value_kwargs)
        ) - frozenset(self.optional_kwargs)

    def kind_of(self, kwarg: str) -> Literal['dimension', 'columns', 'edge', 'value'] | None:
        """What resolution turns the value of *kwarg* into, or ``None`` where the operator does not declare it."""
        if kwarg in self.dimension_kwargs:
            return 'dimension'
        if kwarg in self.column_kwargs:
            return 'columns'
        if kwarg in self.edge_kwargs:
            return 'edge'
        if kwarg in self.required_value_kwargs:
            return 'value'
        return None


#: The closed operator set. ``relation[column, …]`` is the one form that
#: addresses a relation, and a relation carries its own dimensions, so no
#: sibling kwarg restates them. ``by=`` on ``sum`` names the columns a sum
#: groups by, and on ``at`` the columns a lookup reads. ``within=`` on
#: ``shift`` and ``sum_back`` partitions the axis the operator steps along: it
#: says which rows are neighbours, not which group a term is added to.
BUILTINS: dict[str, Builtin] = {
    'sum': Builtin(
        'sum(<expr>), sum(<expr>, over=<dim>) or sum(<expr>, over=<column>, by=<relation>[<column>])',
        dimension_kwargs=('over',),
        column_kwargs=('by',),
        optional_kwargs=('over', 'by'),
        with_columns=('over',),
    ),
    'at': Builtin(
        'at(<expr>, by=<relation>[<column>])',
        column_kwargs=('by',),
    ),
    'sum_back': Builtin(
        "sum_back(<expr>, along=<dim>, window=<n|parameter>[, edge='wrap'][, within=<relation>[<column>]])",
        dimension_kwargs=('along',),
        column_kwargs=('within',),
        required_value_kwargs=('window',),
        edge_kwargs=('edge',),
        optional_kwargs=('within',),
    ),
    'shift': Builtin(
        "shift(<expr>, along=<dim>, offset=<n>[, edge='wrap'|<number>][, within=<relation>[<column>]])",
        dimension_kwargs=('along',),
        column_kwargs=('within',),
        required_value_kwargs=('offset',),
        edge_kwargs=('edge',),
        optional_kwargs=('within',),
    ),
    'dual': Builtin('dual(<constraint>)'),
}

BUILTIN_NAMES = frozenset(BUILTINS)


class Amount(NamedTuple):
    """What the errors of an operator that steps along an axis say about the amount it takes."""

    #: The word for the amount.
    noun: str
    #: What to write instead of negating a named one at the call site.
    negated: str
    #: The least whole number a literal may be.
    minimum: float
    #: What a literal must be written as, after ``operator(kwarg=...)``.
    form: str


#: The amount each operator that steps along a dimension takes, by operator name.
AMOUNTS: dict[str, Amount] = {
    'shift': Amount(
        'offset',
        'Negate the values of the parameter instead.',
        -math.inf,
        'must be a whole number, or the name of an integer parameter.',
    ),
    'sum_back': Amount(
        'width',
        'A width has no sign. Remove the minus.',
        1,
        'must be a whole number of at least 1, or the name of an integer parameter.',
    ),
}

#: The one closed keyword an ``edge=`` accepts. Everything else in that
#: position is a number: the value the vacated positions contribute.
EDGE_WRAP = 'wrap'


def edge_error(name: str, given: str) -> str:
    """Why an ``edge=`` value is not one the language has."""
    return (
        f'{name}(edge={given}) is not an edge value.\n'
        f"Write edge='{EDGE_WRAP}', a number for the vacated positions, or omit edge= to drop their rows."
    )


def call_shape_error(name: str, positional: int, kwargs: Iterable[str]) -> str | None:
    """Why a call to *name* does not fit its signature; ``None`` if it fits."""
    builtin = BUILTINS[name]
    keys = set(kwargs)
    optional = {*builtin.edge_kwargs, *builtin.optional_kwargs}
    if keys & set(builtin.column_kwargs) and (unsaid := sorted(frozenset(builtin.with_columns) - keys)):
        return (
            f'{name}() through a relation does not name {", ".join(f"{k}=" for k in unsaid)}. A sum through a '
            f'relation names in over= the columns it sums away.\n'
            f'Write: {builtin.usage}'
        )
    fits = positional == 1 and keys - optional == builtin.required
    return None if fits else f'{name}() expects {builtin.usage}'


def unknown_operator_message(name: str) -> str:
    """The one wording for "that is not an operator"."""
    return (
        f"Unknown operator '{name}'.\n"
        f'Available: {sorted(BUILTIN_NAMES)}\n'
        f"Define '{name}' as a macro under 'macros:' if it composes built-ins. "
        f'A file cannot add an operator: see docs/about/limits.md.'
    )
