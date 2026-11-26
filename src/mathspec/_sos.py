# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Expand ``sos:`` entries into the binaries and rows that state the same restriction.

A set becomes ordinary entries under names prefixed with the entry's own,
the way a ``piecewise:`` entry becomes weights and rows; what it emits is
tabled in ``docs/reference/language/piecewise.md``. An unpicked member is held
at zero from both sides, so the rewrite states the same feasible set whatever
sign the member takes — what it needs is a coefficient on each side, which a
spec declaring a set without is refused at load for
([`mathspec.spec.Spec`][] validates it) rather than here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mathspec.spec import AssumptionSpec, Spec

if TYPE_CHECKING:
    from mathspec.program import SosType

Coefficients = tuple[float | str | None, float | str | None]


def coefficients(domain: str, lower: float | str | None, upper: float | str | None) -> Coefficients:
    """What a member's two linking rows multiply its binary by, ``None`` on a side the spec leaves open.

    The 0 and 1 a binary's domain fixes, which no ``bounds:`` carries;
    otherwise the member's own declared bounds, each a number or the name of a
    parameter. A parameter is a coefficient like any other: it is what the row
    multiplies by, and no rewrite needs to know its value. Nothing else is a
    coefficient: a number below the bound would cap a picked member the set
    does not cap, and one above it is a looser row than the bound already
    states.
    """
    if domain == 'binary':
        return 0.0, 1.0
    return lower, upper


@dataclass(frozen=True)
class Emitted:
    """Every name one set's expansion writes, spelled once for the emitter and the collision check.

    The linking row is named after what it says, which the two orders do not
    share: order 2 admits a member in either half of one segment, and order 1
    admits it alone. ``below`` is the same row from underneath, written only
    where the member may be nonzero below zero.
    """

    seg: str
    pick: str
    link: str

    @classmethod
    def of(cls, name: str, order: SosType) -> Emitted:
        """The names set *name* of *order* writes."""
        admits = 'adjacency' if order == 2 else 'nonzero'
        return cls(f'{name}_seg', f'{name}_pick', f'{name}_{admits}')

    @property
    def below(self) -> str:
        """The linking row from underneath."""
        return f'{self.link}_below'

    @property
    def bounded(self) -> str:
        """The assumption that the parameters the linking rows multiply by are finite."""
        return f'{self.seg.removesuffix("_seg")}_bounded'

    @property
    def by_kind(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Each name by the kind of entry it would collide with."""
        return (
            ('variable', (self.seg,)),
            ('constraint', (self.pick, self.link, self.below)),
            ('assumption', (self.bounded,)),
        )


_SEGMENTS = {
    1: 'a binary per member, 1 where that member may be nonzero',
    2: 'a binary per segment, 1 where the two members it spans may be nonzero',
}


def expand_sets(spec: Spec) -> Spec:
    """*spec* with every ``sos:`` entry written out as binaries and the rows that link them.

    The curves an expansion wrote out ride along, because a spec whose
    curves are already written out is the one this is usually asked of.
    """
    raw = spec.model_dump()
    for name in list(spec.sos):
        emit(raw, name)
    return Spec.model_validate(raw)


def emit(raw: dict[str, object], name: str) -> None:
    """Write what the set *name* states as entries of *raw*, and drop the entry.

    Args:
        raw: A spec as data, mid-expansion, declaring the set and the variable
            it runs over.
        name: Which set to lower.
    """
    sets = section(raw, 'sos')
    entry = sets.pop(name)
    assert isinstance(entry, dict), 'a validated spec carries each set as a mapping'
    variable, over, order = entry['variable'], entry['along'], entry['type']
    member = section(raw, 'variables')[variable]
    assert isinstance(member, dict), 'a validated spec carries each variable as a mapping'
    dims = list(member['dims'])
    emitted = Emitted.of(name, order)

    section(raw, 'variables')[emitted.seg] = {
        'dims': dims,
        **({'where': member['where']} if member.get('where') else {}),
        'domain': 'binary',
        'description': _SEGMENTS[order],
    }
    picked = emitted.seg if order == 1 else f'sum_back({emitted.seg}, along={over}, window=2)'
    constraints = section(raw, 'constraints')
    constraints[emitted.pick] = {
        'dims': [d for d in dims if d != over],
        'expression': f'sum({emitted.seg}, over={over}) <= 1',
    }
    below, above = _coefficients(member)
    constraints[emitted.link] = {'dims': dims, 'expression': f'{variable} <= {_scaled(above, picked)}'}
    if below != 0.0:
        constraints[emitted.below] = {'dims': dims, 'expression': f'{variable} >= {_scaled(below, picked)}'}
    for assumed_name, assumed in assumptions_of(name, variable, below, above, member.get('where')).items():
        section(raw, 'assumptions')[assumed_name] = assumed.model_dump()


def assumptions_of(
    name: str, variable: str, below: float | str, above: float | str, where: object
) -> dict[str, AssumptionSpec]:
    """What set *name* assumes of the bounds it links its members through, by the name a refusal quotes.

    A bound that is a parameter can be infinite, or missing, in the data,
    and the linking row then multiplies a binary by no finite number. Nothing
    sees a value before data is attached, so the set states the condition and
    the tool that attaches the data checks it. A bare numeric name in a
    condition is true where the parameter has a row and its value is finite,
    which is the condition. The member's own ``where:`` is the assumption's, so
    a member that does not exist needs no bound. A spec that still declares
    the set derives the same text at load, so the data is held to what the
    expansion needs on either side of [`Spec.expand`][mathspec.spec.Spec.expand].
    """
    named = [bound for bound in dict.fromkeys((above, below)) if isinstance(bound, str)]
    if not named:
        return {}
    assert where is None or isinstance(where, str), 'a validated spec carries a where: as text'
    quoted = ' and '.join(f"'{bound}'" for bound in named)
    return {
        Emitted.of(name, 1).bounded: AssumptionSpec(
            holds=' AND '.join(named),
            where=where,
            description=f"sos '{name}': each member of '{variable}' is linked to its binary through {quoted}, "
            'so every member needs a finite value there. Attach a finite bound, or leave the member out with '
            f"a where: on '{variable}'.",
        )
    }


def _scaled(factor: float | str, picked: str) -> str:
    """The binaries a member is admitted by, times *factor*.

    A coefficient of 1 is left out. It is the common one — a weight and a binary
    are both bounded by 1 — and ``x <= 1 * (seg)`` is a factor every reader of
    the row has to work out means nothing.
    """
    return f'({picked})' if factor == 1.0 else f'{factor} * ({picked})'


def _coefficients(member: dict[str, object]) -> tuple[float | str, float | str]:
    """The two coefficients as an expression writes them, read off the member."""
    declared = member.get('bounds')
    assert declared is None or isinstance(declared, dict), 'a validated spec carries `bounds:` as a mapping'
    lower, upper = (declared.get('lower'), declared.get('upper')) if declared else (None, None)
    assert isinstance(lower, float | str | None) and isinstance(upper, float | str | None), (
        'a bound is a number, the name of a parameter, or open'
    )
    below, above = coefficients(str(member.get('domain', 'continuous')), lower, upper)
    assert below is not None and above is not None, 'a set with a side left open is refused at load'
    return below, above


def section(raw: dict[str, object], name: str) -> dict[str, object]:
    """The *name* section of the raw spec, created empty where the file declares none."""
    section = raw.setdefault(name, {})
    assert isinstance(section, dict), f'{name}: is a mapping in a validated spec'
    return section
