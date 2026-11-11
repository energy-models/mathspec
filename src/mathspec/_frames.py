# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The frames of a spec with multi-dimensions: which axes a combination keeps, and how a node is read over another frame.

A multi-dimension stands for its members in a frame, so a frame never holds a
multi-dimension beside one of its members, nor two multi-dimensions that share
a member. Combining two frames keeps a multi-dimension and absorbs the plain
dimensions among its members; an operator that needs a member as an axis of
its own reads its operand over the members instead. Both readings are
[`Reframe`][mathspec.program.Reframe] nodes, and a condition's leaves are each
wrapped in a [`ReframedCondition`][mathspec.program.ReframedCondition], so a
tool never infers a conversion.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, overload

from mathspec._frozen import Frozen
from mathspec.errors import DimensionError
from mathspec.program import (
    And,
    BooleanLiteral,
    Condition,
    ConditionReference,
    Mask,
    Not,
    Or,
    Reframe,
    ReframedCondition,
    atom_dims,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from mathspec.program import Expression


class Frames:
    """The frame rules of one spec, read off the members of its multi-dimensions."""

    __slots__ = ('over',)

    def __init__(self, over: Mapping[str, tuple[str, ...]]) -> None:
        self.over: Mapping[str, tuple[str, ...]] = Frozen({m: members for m, members in over.items() if members})

    def members(self, dims: Iterable[str]) -> frozenset[str]:
        """The plain dimensions *dims* stand for, a multi-dimension for its members."""
        return frozenset(member for d in dims for member in self.over.get(d, (d,)))

    def clash(self, dims: Iterable[str]) -> tuple[str, str, str] | None:
        """Two multi-dimensions in *dims* and a member they share, the first in name order, or ``None``."""
        multis = sorted(d for d in set(dims) if d in self.over)
        for a, b in combinations(multis, 2):
            if shared := sorted(set(self.over[a]) & set(self.over[b])):
                return a, b, shared[0]
        return None

    def union(self, *dims: Iterable[str], context: str) -> tuple[str, ...]:
        """The frame that combines *dims*: every axis once, a plain member absorbed by its multi-dimension.

        Raises:
            DimensionError: Two multi-dimensions of the union share a member,
                so no frame holds both.
        """
        axes = set().union(*dims)
        if (clash := self.clash(axes)) is not None:
            raise DimensionError(overlap(context, *clash, self.over))
        absorbed = self.members(d for d in axes if d in self.over)
        return tuple(sorted(d for d in axes if d in self.over or d not in absorbed))

    def within(self, dims: Iterable[str], target: Iterable[str]) -> tuple[str, ...] | None:
        """The axes of *target* that *dims* reads, or ``None`` where *dims* stands for a member *target* lacks."""
        dims, target = tuple(dims), tuple(target)
        if not self.members(dims) <= self.members(target):
            return None
        read = self.members(dims)
        return tuple(sorted(axis for axis in target if read & self.members((axis,))))

    def unstacked(self, dims: Iterable[str], names: Iterable[str]) -> tuple[str, ...]:
        """*dims* with each multi-dimension that holds one of *names* as a member read over its members."""
        names = frozenset(names)
        out: set[str] = set()
        for d in dims:
            out.update(self.over[d] if d in self.over and names & set(self.over[d]) else (d,))
        return tuple(sorted(out))

    def reframed(self, expression: Expression, target: Iterable[str]) -> Expression:
        """*expression* read over the axes of *target* it reads, or *expression* itself where it is read over them already.

        Left as it is where it stands for a member *target* lacks, so the
        frame check that follows names the stray dimension.
        """
        dims = self.within(expression.dims, target)
        if dims is None or dims == expression.dims:
            return expression
        if isinstance(expression, Reframe):
            expression = expression.operand
        return expression if dims == expression.dims else Reframe(expression, dims=dims)

    @overload
    def reframed_mask(self, mask: Mask, target: Iterable[str]) -> Mask: ...
    @overload
    def reframed_mask(self, mask: None, target: Iterable[str]) -> None: ...
    def reframed_mask(self, mask: Mask | None, target: Iterable[str]) -> Mask | None:
        """*mask* with each leaf read over the axes of *target* it reads, before any connective combines it.

        A leaf is converted on its own, so ``NOT`` of a leaf that is false off a
        multi-dimension stays true there once it is read over the members.
        """
        if mask is None or not self.over:
            return mask
        target = tuple(target)
        return Mask(self._condition(mask.root, target))

    def _condition(self, node: Condition, target: tuple[str, ...]) -> Condition:
        if isinstance(node, Not):
            return Not(self._condition(node.operand, target))
        if isinstance(node, And):
            return And(self._condition(node.left, target), self._condition(node.right, target))
        if isinstance(node, Or):
            return Or(self._condition(node.left, target), self._condition(node.right, target))
        if isinstance(node, ConditionReference):
            return ConditionReference(node.name, self._condition(node.body, target))
        if isinstance(node, BooleanLiteral):
            return node
        if isinstance(node, ReframedCondition):
            node = node.operand
        dims = tuple(sorted(atom_dims(node)))
        within = self.within(dims, target)
        return node if within is None or within == dims else ReframedCondition(node, dims=within)


def overlap(context: str, a: str, b: str, member: str, over: Mapping[str, tuple[str, ...]]) -> str:
    """The refusal for two multi-dimensions that share *member* meeting in one frame."""
    members = sorted({*over[a], *over[b]})
    return (
        f"{context}: '{a}' and '{b}' both combine '{member}', so no frame holds both. Index one of them by its "
        f'members and confine it with where: {b}, or declare one dimension over {members}.'
    )


def no_order(context: str, call: str, dimension: str, over: Mapping[str, tuple[str, ...]]) -> str:
    """The refusal for stepping or counting along a multi-dimension, whose labels have no order."""
    return (
        f"{context}: {call} steps along '{dimension}', which combines {list(over[dimension])} and has no order. "
        f'Step along one of its members.'
    )
