# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Several files into one spec, each checked as a spec where it is one.

Two verbs, and they answer different questions. [`merge`][] composes
**peers**: fragments that each own part of the math, where a name two of them
declare is a collision. [`override`][] lays **patches** over a **base**: what a
framework ships and a project extends, where a name the patch declares is the
point. They compose as ``override(merge([...]), [...])``, which builds the spec
and then configures the run.

Each verb takes its files as a list. The order of the list is the order a sum
writes its terms in, and the order patches are laid in. A refusal names a file
by its path as the list gives it, and anything else by its place in the list,
such as ``'#2'``.

[`merge`][] writes nothing a fragment did not write, except a ``+``. It
joins fragments' text in one place, a named expression that terms add to;
every other block is copied as written, refused where two fragments own it,
or held identical where it is a dimension or a relation.
What that means for each section:

* **A dimension or a relation every fragment may declare**, and the ones that
  do have to say the same thing about it. Prose is not a claim, so two
  descriptions of one dimension agree, and the first one given is carried.
* **Every other declaration is owned.** A name two fragments declare is refused,
  both named.
* **One fragment sets the objective.** A second one is refused, both named.
  Where several files contribute to it, the objective reads a sum, and each
  file adds its part to that sum with ``adds_to:``.
* **Terms add to a named expression.** ``adds_to:`` adds a named
  expression as a term to the sum it names, a ``given: expressions:`` entry
  of its own fragment. The term keeps its name in the composed spec. Where a fragment
  defines that name with one ``expression:``, the composed body is that
  body followed by every term, in the order the fragments are given in,
  so a composed spec takes more terms in a later merge. A definition
  written as ``cases:`` takes no term. Where no fragment defines the
  name, the composed spec defines it as its terms, over the frame the
  readers state in one order. Some fragment then has to read the name for
  more than adding to it: read it without adding to it, or use it in its
  math. A name only its terms read, or only one fragment reads, is what a
  misspelt ``given:`` entry looks like, so it is refused. A term that
  reads its own sum through another fragment is refused, both named.
* **A given declaration is folded** into the declaration that introduces the
  name, once the reader is checked to say the same as the introducer or less.
  A given expression's body may carry no dimension its reader does not state,
  and a name read as one kind and introduced as another is refused. A
  reader's description fills a declaration its owner left undescribed.
  Two fragments that both read a name have to read it over one frame, as a
  set. What no fragment introduces stays under ``given:`` until a host model
  provides it.

A patch says only what it changes, because declarations are laid over a field
at a time::

    constraints:
      ramp: {dims: [snapshot, generator, investment_period]}

A fragment is a [`Spec`][mathspec.spec.Spec] of its own, and a base is one
too: each goes through [`to_spec`][mathspec.validation.to_spec] before anything is
composed, so a composed spec never hides a file that does not load alone. A
patch is not one. It names only what it changes and may carry ``null`` where a
declaration would go, so it is laid over as written, and the result goes
through [`to_spec`][mathspec.validation.to_spec] like any other file.

What a patch may say, and what is refused:

* **A partial entry edits, and a whole one creates.** An entry that does not
  validate as a declaration on its own has to land on one the base declares,
  and a miss is refused with the near miss named.
* **Patches are laid in order.** Each is laid on the base with every
  earlier patch laid on it, so a later patch wins a field an earlier one
  writes, and edits or removes a declaration an earlier one creates.
* **A patch adjusts the math, not the coordinate space.** A ``dimensions`` or
  ``relations`` entry may be added or restated word for word, never changed and
  never removed.
* ``null`` **makes what it names absent.** A declaration set to ``null`` is
  removed, and a removal of what the base does not declare is refused. A field
  set to ``null`` is dropped, and takes its default when the result loads:
  ``variables: {p: {bounds: {upper: null}}}`` opens that bound. A whole section
  set to ``null`` is refused, because it removes nothing.
* **``given:`` is laid over one kind at a time**, by the same rules as any
  owned section.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, cast, get_args, get_origin

from pydantic import BaseModel, ValidationError

from mathspec._yaml import read_spec
from mathspec.errors import LanguageError, did_you_mean, schema_error
from mathspec.program import variables_of
from mathspec.spec import GivenBlock, Spec
from mathspec.validation import to_spec

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from mathspec.program import Program

SHARED_SECTIONS = ('dimensions', 'relations')

OWNED_SECTIONS = tuple(
    name
    for name, field in Spec.model_fields.items()
    if get_origin(field.annotation) is dict and name not in SHARED_SECTIONS
)

GIVEN_KINDS = {
    'parameters': 'given parameter',
    'variables': 'given variable',
    'constraints': 'given constraint',
    'expressions': 'given expression',
}

#: What a fragment, a base or a patch may be given as.
type Source = str | Path | Mapping[str, object] | Spec

IRREGULAR = {
    'piecewise': 'piecewise curve',
    'sos': 'special-ordered set',
    'objective': 'objective',
}


def merge(fragments: Sequence[Source], description: str | None = None) -> Spec:
    """*fragments* composed as peers, each owning the math it declares.

    Args:
        fragments: Each fragment as a YAML path, YAML text, a mapping, or a
            loaded [`Spec`][mathspec.spec.Spec]. A sum writes its terms in
            the order of the list.
        description: What the composed spec is. A fragment's own
            ``description`` is about the fragment, and is not carried.

    Returns:
        The composed spec, loaded. A given declaration a sibling introduces is
        folded away; one nothing introduces stays under ``given:``.

    Raises:
        LanguageError: A fragment does not load on its own; two fragments
            declare one name; two fragments say different things about one
            dimension, relation or given declaration; a fragment reads a name as
            something other than what its sibling introduces, as another kind
            of thing, or over fewer dimensions than its body carries; a fragment
            adds a term to a variable, a parameter, a constraint or a
            definition written as ``cases:``; a term reads its own sum through
            another fragment; a name no fragment defines is read by nothing
            but the fragments that add a term to it, or by one fragment alone;
            the readers of such a name write its dims in different orders; two
            fragments are written against different language versions; two
            fragments set the objective; or the composed spec does not load.
        FileNotFoundError: A ``str`` with no newline that names no file.
        TypeError: *fragments* is one path rather than a list.
    """
    loaded = {name: _fragment(name, fragment) for name, fragment in _labelled(fragments, 'fragments').items()}
    read = {name: spec.to_dict() for name, spec in loaded.items()}
    merged: dict[str, object] = {'version': _one_version(read)}
    if description is not None:
        merged['description'] = description
    for section in SHARED_SECTIONS:
        if agreed := _agreed(read, section, _singular(section), 'give one of them a name of its own'):
            merged[section] = agreed
    asked = {name: spec.given.model_dump(exclude_unset=True) for name, spec in loaded.items()}
    readings = {
        kind: _agreed(asked, kind, label, 'read it over one frame', claims=_reading_claims)
        for kind, label in GIVEN_KINDS.items()
    }
    for section in OWNED_SECTIONS:
        if claimed := _claimed(read, section):
            merged[section] = claimed
    summed = _summed(loaded, merged, readings['expressions'], read)
    if expressions := {**_mapping(merged.get('expressions')), **summed}:
        merged['expressions'] = {key: _without(block, 'adds_to') for key, block in expressions.items()}
    if given := _folded(read, merged, loaded, readings):
        merged['given'] = given
    if (objective := _one_objective(read)) is not None:
        merged['objective'] = objective
    return to_spec(merged)


def _labelled(sources: Sequence[Source], noun: str) -> dict[str, Source]:
    """*sources* under what a refusal calls each: a path as the list gives it, and anything else its place.

    A lone string is a sequence of letters, and each letter would be read as
    the path of a file, so it is refused with the list it was meant to be.
    """
    if isinstance(sources, str | Path):
        msg = f'the {noun} are a list, and this is one path: pass [{str(sources)!r}].'
        raise TypeError(msg)
    return {_label(place, source): source for place, source in enumerate(sources, 1)}


def _label(place: int, source: Source) -> str:
    """A file's path, which [`read_spec`][mathspec._yaml.read_spec] tells from YAML text by its lack of a newline."""
    if isinstance(source, Path) or (isinstance(source, str) and '\n' not in source):
        return str(source)
    return f'#{place}'


def _fragment(name: str, source: Source) -> Spec:
    """One fragment loaded as the spec it is on its own, refused under its own name where it is not one."""
    try:
        return to_spec(source)
    except LanguageError as e:
        msg = (
            f"fragment '{name}' does not load on its own. A fragment is a whole spec: it declares "
            f"what it builds, and reads what a sibling builds under 'given:'.\n{e}"
        )
        raise type(e)(msg) from None


def _one_version(read: Mapping[str, dict[str, object]]) -> int:
    """The language version every fragment is written against."""
    declared = {name: cast('int', sections['version']) for name, sections in read.items()}
    if len(set(declared.values())) > 1:
        spelled = ', '.join(f"'{name}' says {version}" for name, version in declared.items())
        raise LanguageError(
            f'the fragments are written against different language versions: {spelled}. One spec has '
            f'one version, so write every fragment against the same one.'
        )
    return next(iter(declared.values()), 0)


def _author_of(read: Mapping[str, dict[str, object]], section: str, key: str) -> str:
    """The first fragment declaring *key* under *section*, for a message that names both sides."""
    return next(name for name, sections in read.items() if key in _mapping(sections.get(section)))


def _said(read: Mapping[str, dict[str, object]], section: str, key: str) -> object:
    """The first description of *key* under *section*, in the order the fragments are given in."""
    return next(
        (
            said
            for sections in read.values()
            if (said := _mapping(_mapping(sections.get(section)).get(key)).get('description'))
        ),
        None,
    )


def _claims(block: object) -> object:
    """*block* without its prose, which is what the declaration says rather than a remark about it."""
    return {key: value for key, value in block.items() if key != 'description'} if isinstance(block, dict) else block


def _reading_claims(block: object) -> object:
    """What a reading claims: its fields but the prose, with the frame as a set, since two files read one name over one frame however they list it."""
    claims = _mapping(_claims(block))
    return {**claims, 'dims': frozenset(cast('list[str]', claims.get('dims', [])))}


def _agreed(
    read: Mapping[str, dict[str, object]],
    section: str,
    label: str,
    repair: str,
    *,
    claims: Callable[[object], object] = _claims,
) -> dict[str, object]:
    """One block every fragment may declare, peers that say the same thing folded together.

    Equality of the claims rather than "the same or less": between peers
    neither declaration is the one being restated, so a field only one of them
    writes is a difference nothing settles. *claims* says what a block claims;
    a reading's frame is a set. Prose is not a claim, so the first description
    given is carried.
    """
    merged: dict[str, object] = {}
    for name, sections in read.items():
        for key, block in _mapping(sections.get(section)).items():
            if key in merged and claims(merged[key]) != claims(block):
                raise LanguageError(
                    f"fragments '{_author_of(read, section, key)}' and '{name}' say different things about "
                    f'the {label} {key!r}: {merged[key]!r} against {block!r}. A declaration two fragments '
                    f'share is one both say the same thing about: make the two identical, or {repair}.'
                )
            merged.setdefault(key, block)
    for key, block in merged.items():
        if said := _said(read, section, key):
            merged[key] = {**_mapping(block), 'description': said}
    return merged


def _claimed(read: Mapping[str, dict[str, object]], section: str) -> dict[str, object]:
    """One block of owned declarations, a name claimed twice being the refusal."""
    merged: dict[str, object] = {}
    for name, sections in read.items():
        for key, block in _mapping(sections.get(section)).items():
            if key in merged:
                author = _author_of(read, section, key)
                if section == 'expressions' and (target := _adds(read[author], key) or _adds(sections, key)):
                    raise LanguageError(
                        f"fragments '{author}' and '{name}' both declare the expression {key!r}, which a fragment "
                        f'adds to {target!r} as a term. A term shares one namespace with every named expression: '
                        f"name each fragment's term apart, such as after its component."
                    )
                hint = (
                    ' A sum several fragments add to is defined by one of them at most: each other reads it '
                    "under 'given: expressions:' and adds its part with `adds_to:`."
                    if section == 'expressions'
                    else ''
                )
                raise LanguageError(
                    f"fragments '{author}' and '{name}' both declare the "
                    f'{_singular(section)} {key!r}. Two of the same kind of thing are two rows of a dimension '
                    f'rather than two fragments: merge the fragment once, and let the data carry both. '
                    f'Different math under one spelling is a rename: call one of them something else.{hint}'
                )
            merged[key] = block
    return merged


def _adds(sections: Mapping[str, object], key: str) -> str | None:
    """The name one fragment's expression *key* adds to as a term, or ``None`` where it is no term."""
    return cast('str | None', _as_mapping(_mapping(sections.get('expressions')).get(key)).get('adds_to'))


def _terms(read: Mapping[str, dict[str, object]], key: str) -> list[tuple[str, str]]:
    """Every term the fragments add to *key*, with the fragment that adds it, in the order they are given in."""
    return [
        (name, term)
        for name, sections in read.items()
        for term in _mapping(sections.get('expressions'))
        if _adds(sections, term) == key
    ]


def _summed(
    loaded: Mapping[str, Spec],
    merged: Mapping[str, object],
    readings: Mapping[str, object],
    read: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    """Every name a fragment adds a term to, its body the definer's followed by every term by name.

    The terms join with a plain ``+``, the loosest operator there is, so a
    sum composed in two merges reads as the one composed in one. Where no
    fragment defines the name, the terms are the body, over the frame the
    readers state; the composed load holds the terms to it either way.
    """
    summed: dict[str, object] = {}
    defined = _mapping(merged.get('expressions'))
    for key, reading in readings.items():
        terms = _terms(read, key)
        if not terms:
            continue
        contributors = [name for name, _ in terms]
        _undeclared(read, merged, key, contributors[0])
        names = [term for _, term in terms]
        if key in defined:
            base = _as_mapping(defined[key])
            summed[key] = {**base, 'expression': ' + '.join([cast('str', base['expression']), *names])}
            continue
        _read_elsewhere(loaded, key, contributors)
        block: dict[str, object] = {'dims': _frame(read, key), 'expression': ' + '.join(names)}
        if said := _mapping(reading).get('description'):
            block['description'] = said
        summed[key] = block
    _acyclic(loaded, {key: _terms(read, key) for key in summed})
    return summed


def _undeclared(read: Mapping[str, dict[str, object]], merged: Mapping[str, object], key: str, adder: str) -> None:
    """Refuse a term on a name a fragment declares as something a term cannot follow, naming what declares it."""
    section = next((section for section in OWNED_SECTIONS if key in _mapping(merged.get(section))), None)
    if section is None:
        return
    author = _author_of(read, section, key)
    if section == 'expressions':
        if not _as_mapping(_mapping(merged['expressions'])[key]).get('cases'):
            return
        raise LanguageError(
            f"fragment '{author}' defines {key!r} as `cases:`, and fragment '{adder}' adds a term to it. A term "
            f'follows one body, and a set of cases is no one body: name the cased body as its own expression, '
            f'and define {key!r} as that name.'
        )
    raise LanguageError(
        f"fragment '{author}' declares {key!r} as a {_singular(section)}, and fragment '{adder}' adds a term to "
        f'it. A term adds to a named expression: give the sum a name of its own, or read the '
        f"{_singular(section)} under 'given: {section}:' and add no term to it."
    )


def _acyclic(loaded: Mapping[str, Spec], terms: Mapping[str, list[tuple[str, str]]]) -> None:
    """Refuse a term that reads its own sum through a name another fragment defines.

    Each fragment refuses a term that reads its sum through its own names at
    load. A loop across fragments shows only once they compose, where the
    composed load would name the loop and no fragment, so it is refused here
    with the fragments that close it.
    """
    reads: dict[str, frozenset[str]] = {}
    owner: dict[str, str] = {}
    for name, spec in loaded.items():
        for key, expression in spec.program.expressions.items():
            reads[key] = variables_of(expression.expression)
            owner.setdefault(key, name)
    for key, added in terms.items():
        reads[key] = reads.get(key, frozenset()) | {term for _, term in added}
    for key, added in terms.items():
        for adder, term in added:
            if (path := _path(reads, term, key)) is None:
                continue
            through = ', '.join(
                f"{step!r} of '{owner[step]}'" if step in owner else f'the sum {step!r}' for step in path[1:-1]
            )
            raise LanguageError(
                f"fragment '{adder}' adds {term!r} to {key!r}, and {term!r} reads {key!r} back through "
                f'{through}, so the sum would define itself. A term may not read what reads its sum: write '
                f'{term!r} from something else, or define {path[-2]!r} without {key!r}.'
            )


def _path(reads: Mapping[str, frozenset[str]], start: str, goal: str) -> list[str] | None:
    """The names from *start* to *goal* along what each name reads, both ends included, or ``None``."""
    trail = {start: [start]}
    frontier = [start]
    while frontier:
        name = frontier.pop()
        for step in sorted(reads.get(name, ())):
            if step == goal:
                return [*trail[name], goal]
            if step not in trail:
                trail[step] = [*trail[name], step]
                frontier.append(step)
    return None


def _frame(read: Mapping[str, dict[str, object]], key: str) -> list[str]:
    """The dims every fragment reads the sum *key* over, in the order they all write.

    No fragment defines the sum, so no fragment's order is the one to take:
    the first reader's would make the order of the list reach the canonical
    text, which keeps a declaration's dims as written.
    """
    frames = [
        (name, cast('list[str]', entry['dims']))
        for name, sections in read.items()
        if (entry := _mapping(_mapping(_mapping(sections.get('given')).get('expressions')).get(key)))
    ]
    (first, dims), *rest = frames
    for name, other in rest:
        if other != dims:
            raise LanguageError(
                f"fragments '{first}' and '{name}' read the sum {key!r} over {dims} and {other}. No fragment "
                f'defines the sum, so its frame is the order its readers write: write the dims in one order '
                f'in every file.'
            )
    return dims


def _read_elsewhere(loaded: Mapping[str, Spec], key: str, contributors: list[str]) -> None:
    """Refuse terms that write into a name nothing but the terms reads.

    A fragment reads the name for more than adding to it where it reads it
    under ``given:`` and adds nothing, or uses it in its math. A name only
    its terms read, or only one fragment reads, is what a misspelt ``given:``
    entry looks like, since the file that uses the sum reads it under the
    right spelling, so the refusal names the near miss among the names the
    fragments read.
    """
    readers = {name: spec for name, spec in loaded.items() if key in spec.program.given.expressions}
    if len(readers) > 1 and any(name not in contributors or _uses(spec.program, key) for name, spec in readers.items()):
        return
    known = {
        n
        for spec in loaded.values()
        for n in (*spec.program.given.expressions, *(n for n, e in spec.program.expressions.items() if not e.adds_to))
    }
    spelled = ', '.join(f"'{name}'" for name in contributors[:-1])
    who = f"fragments {spelled} and '{contributors[-1]}' add" if spelled else f"fragment '{contributors[0]}' adds"
    near = f' {hint}' if (hint := did_you_mean(key, known - {key}, listing=False)) else ''
    raise LanguageError(
        f'{who} a term to {key!r}, and no other fragment reads it: none reads it without adding to it, or '
        f'uses it in its math. A term writes into a sum the rest of the spec reads: add the fragment that '
        f"reads it, or fix the spelling under 'given:'.{near}"
    )


def _uses(program: Program, key: str) -> bool:
    """Whether *program*'s math reads the given expression *key*, which it reads as a column.

    A reported expression builds no row, so a read there is not a read in the
    math, and a fragment whose only use of the name is to report it is still
    one that may have misspelt it.
    """
    trees = [
        *program.roots,
        *(e.expression for e in program.expressions.values() if e.in_math),
        *(link.expression for curve in program.piecewise.values() for link in curve.links),
    ]
    return key in variables_of(*trees)


def _as_mapping(block: object) -> dict[str, object]:
    """A named expression as ``to_dict`` wrote it, the one-line form read as its mapping."""
    return cast('dict[str, object]', block) if isinstance(block, dict) else {'expression': block}


def _without(block: object, field: str) -> object:
    """*block* with *field* dropped, where it is a mapping that has it."""
    return {f: v for f, v in block.items() if f != field} if isinstance(block, dict) else block


def _folded(
    read: Mapping[str, dict[str, object]],
    merged: Mapping[str, object],
    loaded: Mapping[str, Spec],
    readings: Mapping[str, dict[str, object]],
) -> dict[str, object]:
    """The ``given:`` block the composition still carries, once every reading a sibling introduces is spent.

    A given declaration is what a fragment expects of a name a sibling owns.
    Where the sibling is in the composition the expectation is checked and
    then dropped, so the composed spec declares the name once. A reader's
    description fills a declaration its owner left undescribed, and yields to
    one the owner wrote.
    """
    left: dict[str, object] = {}
    for kind, agreed in readings.items():
        introduced = _mapping(merged.get(kind))
        for key, block in agreed.items():
            _same_kind(read, merged, kind, key)
            if key in introduced:
                _fits(read, loaded, kind, key, block, introduced[key])
            if key in introduced and (said := _mapping(block).get('description')):
                owned = _as_mapping(introduced[key])
                if not owned.get('description'):
                    introduced[key] = {**owned, 'description': said}
        kept = {key: block for key, block in agreed.items() if key not in introduced}
        if kept:
            left[kind] = kept
    return left


def _reader_of(read: Mapping[str, dict[str, object]], kind: str, key: str) -> str:
    """The first fragment reading *key* under ``given: {kind}:``."""
    return next(name for name, sections in read.items() if key in _mapping(_mapping(sections.get('given')).get(kind)))


def _fits(
    read: Mapping[str, dict[str, object]],
    loaded: Mapping[str, Spec],
    kind: str,
    key: str,
    reading: object,
    introduced: object,
) -> None:
    """Refuse a reading that says more than the declaration it folds into.

    A reading states the frame its introducer declares, and every other field
    it writes is the introducer's. A given expression is the one kind whose
    frame may be wider than the composed body: a body over fewer dimensions
    broadcasts, and the composed load refuses a row it would repeat.
    """
    stated = set(cast('list[str]', _mapping(reading)['dims']))
    if kind == 'expressions':
        frame = set(_definer_frame(loaded, key))
        fits = frame <= stated
    else:
        frame = set(cast('list[str]', _mapping(introduced)['dims']))
        fits = frame == stated
    fields = {f: v for f, v in _mapping(_claims(reading)).items() if f != 'dims'}
    if fits and all(_mapping(introduced).get(f) == v for f, v in fields.items()):
        return
    how = f'over {sorted(frame)}' if kind == 'expressions' else f'as {introduced!r}'
    raise LanguageError(
        f"fragment '{_reader_of(read, kind, key)}' reads the {GIVEN_KINDS[kind]} {key!r} as {reading!r}, where "
        f"'{_author_of(read, kind, key)}' introduces it {how}. A given declaration says the same as the "
        f'declaration it is folded into, or less: restate the frame as the introducer declares it, or leave '
        f'the field out.'
    )


def _definer_frame(loaded: Mapping[str, Spec], key: str) -> frozenset[str]:
    """The frame of the composed body of *key*: the frame its definer declares, else its body's with every term's."""
    frame: set[str] = set()
    for spec in loaded.values():
        declared = spec.expressions[key].dims if key in spec.expressions else None
        if declared is not None:
            return frozenset(declared)
        if key in spec.program.expressions:
            frame |= set(spec.program.expressions[key].dims)
        frame |= {d for e in spec.program.expressions.values() if e.adds_to == key for d in e.dims}
    return frozenset(frame)


READ_KINDS = ('parameters', 'variables', 'expressions')


def _same_kind(read: Mapping[str, dict[str, object]], merged: Mapping[str, object], kind: str, key: str) -> None:
    """Refuse a given declaration whose name a sibling introduces as another kind of thing."""
    if kind not in READ_KINDS:
        return
    for other in READ_KINDS:
        if other != kind and key in _mapping(merged.get(other)):
            raise LanguageError(
                f"fragment '{_reader_of(read, kind, key)}' reads {key!r} as a {GIVEN_KINDS[kind]}, where "
                f"'{_author_of(read, other, key)}' introduces it under '{other}:'. A given declaration reads a "
                f"name as the kind of thing its introducer declares: move it under 'given: {other}:'."
            )


def _one_objective(read: Mapping[str, dict[str, object]]) -> object | None:
    """The objective the one fragment that sets it wrote, or ``None`` where none sets one.

    A composed spec has one objective, so a second is a collision like a name
    two fragments declare. Several files add to it through a sum that the
    fragment setting the objective reads.
    """
    declared = [name for name, sections in read.items() if sections.get('objective')]
    if len(declared) > 1:
        first, second, *_ = declared
        raise LanguageError(
            f"fragments '{first}' and '{second}' both set the objective. A composed spec has one objective, "
            f"and one fragment sets it: read a sum under 'given: expressions:' in that fragment, and add "
            f'each part to it with `adds_to:`.'
        )
    return read[declared[0]]['objective'] if declared else None


def override(base: Source, patches: Sequence[Source]) -> Spec:
    """*base* with each patch laid over it in turn.

    Args:
        base: The spec being extended: a YAML path, YAML text, a mapping, or a
            loaded [`Spec`][mathspec.spec.Spec].
        patches: Each patch as a YAML path, YAML text, a mapping, or a loaded
            [`Spec`][mathspec.spec.Spec]. Each is laid on the base with every
            earlier patch laid on it, so a later patch wins a field an earlier
            one writes.

    Returns:
        The patched spec, loaded.

    Raises:
        LanguageError: The base does not load; the patched spec does not
            load; a patch edits or removes a declaration its base does not
            declare; a patch creates one that is not whole; a patch redeclares
            or removes a dimension or a relation; or a patch sets a whole
            section to ``null``.
        FileNotFoundError: A ``str`` with no newline that names no file.
        TypeError: *patches* is one path rather than a list.
    """
    read = {name: _declarations(patch) for name, patch in _labelled(patches, 'patches').items()}
    result = to_spec(base).to_dict()
    for name, patch in read.items():
        result = _lay_over(result, deepcopy(patch), name)
    return to_spec(result)


def _declarations(source: Source) -> dict[str, object]:
    """A patch as the mapping it declares, whatever shape it arrived in.

    Deliberately not [`to_spec`][mathspec.validation.to_spec]: a patch carrying a
    ``null`` or naming only the field it changes is not a spec.
    """
    if isinstance(source, Spec):
        return source.to_dict()
    if isinstance(source, Mapping):
        return dict(source)
    return read_spec(source)


def _mapping(value: object) -> dict[str, object]:
    """*value* as the mapping a section or a declaration is, an absent one read as empty.

    A file is read before it is validated, so nothing here has checked the
    shape; the closed schema refuses any other shape when the result loads.
    """
    return cast('dict[str, object]', value or {})


def _singular(section: str) -> str:
    """What one entry in *section* is called, ``sos`` and ``piecewise`` not being plurals."""
    return IRREGULAR.get(section, section[:-1])


def _entry_class(owner: type[BaseModel], field: str) -> type[BaseModel]:
    """The schema's own class for one entry under *field* of *owner*.

    Read off the annotation rather than listed here, so a section added to the
    schema cannot be laid over by a rule that does not know what it is made of.
    """
    annotation = owner.model_fields[field].annotation
    inner = [arg for arg in get_args(annotation) if arg is not type(None)]
    return cast('type[BaseModel]', inner[-1] if inner else annotation)


def _whole(cls: type[BaseModel], block: object) -> bool:
    """Whether *block* is a declaration on its own, which is what lets a patch create one."""
    try:
        cls.model_validate(block)
    except ValidationError:
        return False
    return True


def _incomplete(label: str, cls: type[BaseModel], block: object) -> str:
    """What *block* is short of, in the schema's own words rather than a second list."""
    fields = cls.model_fields
    missing = sorted(name for name, field in fields.items() if field.is_required() and name not in _mapping(block))
    if missing:
        return f'{_a(label)} needs {_and_list(missing)}'
    try:
        cls.model_validate(block)
    except ValidationError as e:
        return str(schema_error(e))
    raise AssertionError(f'{_a(label)} asked what it is short of is whole: {block!r}')


def _a(noun: str) -> str:
    """*noun* under the article that reads: an objective, a constraint."""
    return f'an {noun}' if noun[0] in 'aeiou' else f'a {noun}'


def _and_list(names: Iterable[str]) -> str:
    """``a``, ``a and b``, ``a, b and c``: the field names a message ends on."""
    spelled = [f'`{name}`' for name in names]
    if len(spelled) == 1:
        return spelled[0]
    return f'{", ".join(spelled[:-1])} and {spelled[-1]}'


def _lay_over(base: dict[str, object], patch: dict[str, object], name: str) -> dict[str, object]:
    """One patch over one base, a section at a time, the base left as it was."""
    laid = dict(base)
    for key, value in patch.items():
        if key == 'given':
            laid[key] = _given(_mapping(laid.get(key)), _section(value, key, name), name)
        elif key in SHARED_SECTIONS:
            laid[key] = _shared(_mapping(laid.get(key)), _section(value, key, name), key, name)
        elif key in OWNED_SECTIONS:
            block = _section(value, key, name)
            if key == 'expressions':
                block = {
                    entry: _body(over) if entry in _mapping(laid.get(key)) else over for entry, over in block.items()
                }
            laid[key] = _owned(_mapping(laid.get(key)), block, _singular(key), _entry_class(Spec, key), name)
        elif key == 'objective':
            laid = _objective(laid, value, name)
        elif value is None:
            laid.pop(key, None)
        else:
            laid[key] = value
    return laid


def _body(over: object) -> object:
    """A patch's edit to a named expression, the one-line form read as a new body that keeps the entry's other fields.

    The one-line form writes a body and nothing else, so laid over an entry
    it replaces the body, whether an ``expression:`` or ``cases:``, and keeps
    what the entry says beside it, such as what a term ``adds_to:``.
    """
    return {'expression': over, 'cases': None, 'otherwise': None} if isinstance(over, str) else over


def _section(value: object, where: str, name: str) -> dict[str, object]:
    """The block a patch writes under one section, a ``null`` section being refused rather than read as empty.

    A section is not a declaration, so the removal marker does not reach it. An
    empty mapping laid over a base says nothing either, and this is the spelling
    a writer reaches for when they mean to empty the section.
    """
    if value is None:
        raise LanguageError(
            f"patch '{name}' sets '{where}' to null, which removes nothing: the removal marker names one "
            f'declaration, and a section is not one. Remove the declarations one at a time, each under its '
            f'own name, or leave the section out of the patch.'
        )
    return cast('dict[str, object]', value)


def _given(declared: dict[str, object], patch: dict[str, object], name: str) -> dict[str, object]:
    """The ``given:`` block, one kind laid over at a time, so naming the columns keeps the row families.

    A kind the block does not have is carried as written, and the closed
    schema refuses it at load.
    """
    out = dict(declared)
    for kind, block in patch.items():
        if kind in GIVEN_KINDS:
            cls = _entry_class(GivenBlock, kind)
            entries = _section(block, f'given: {kind}:', name)
            out[kind] = _owned(_mapping(out.get(kind)), entries, GIVEN_KINDS[kind], cls, name)
        else:
            out[kind] = block
    return out


def _shared(declared: dict[str, object], patch: dict[str, object], section: str, name: str) -> dict[str, object]:
    """One ``dimensions`` or ``relations`` block: a patch adds one or restates one, never changes or drops it.

    The restatement is compared for equality rather than field by field: a
    patch that names half a declaration is as much a second reading of the
    coordinate space as one that names another value.
    """
    out = dict(declared)
    singular = _singular(section)
    for key, block in patch.items():
        if block is None:
            raise LanguageError(
                f"patch '{name}' removes the {singular} '{key}'. The coordinate space is what the math is "
                f'written over, and a patch adjusts the math rather than the space: leave the {singular} out '
                f'of the patch, and remove the declarations written over it one at a time.'
            )
        if key not in out:
            out[key] = block
        elif out[key] != block:
            raise LanguageError(
                f"patch '{name}' declares the {singular} '{key}' as {block!r}, where its base "
                f'declares {out[key]!r}. A patch adjusts the math, not the coordinate space the math is '
                f'already written over: restate the declaration word for word, leave it out, or give the '
                f'patch {_a(singular)} of its own under a name of its own.'
            )
    return out


def _owned(
    declared: dict[str, object], patch: dict[str, object], label: str, cls: type[BaseModel], name: str
) -> dict[str, object]:
    """One section of the math, each entry editing what is there or creating what is whole."""
    out = dict(declared)
    for key, block in patch.items():
        if block is None:
            _removed(out, key, label, name)
        elif key in out:
            out[key] = _field_by_field(out[key], block)
        elif _whole(cls, block):
            out[key] = block
        else:
            raise LanguageError(
                f"patch '{name}' edits the {label} '{key}', which its base does not declare. "
                f'{did_you_mean(key, list(out))} A patch creates a declaration only by writing it whole, '
                f'and this one is not: {_incomplete(label, cls, block)}.'
            )
    return out


def _removed(out: dict[str, object], key: str, label: str, name: str) -> None:
    """Delete what the patch nulled, refusing a removal its base cannot satisfy."""
    if key not in out:
        raise LanguageError(
            f"patch '{name}' removes the {label} '{key}', which its base does not declare. "
            f'A removal is a claim about what is there, so a stale one is a patch that no longer describes '
            f'the spec it lands on. ' + did_you_mean(key, list(out))
        )
    del out[key]


def _objective(laid: dict[str, object], patch: object, name: str) -> dict[str, object]:
    """The one declaration that is not keyed by a name, laid over by the same three rules."""
    out = dict(laid)
    standing = out.get('objective')
    cls = _entry_class(Spec, 'objective')
    if patch is None:
        if standing is None:
            raise LanguageError(
                f"patch '{name}' removes the objective, which its base does not declare. A removal is a "
                f'claim about what is there, and a spec with no objective is already the feasibility '
                f'problem this patch is asking for.'
            )
        del out['objective']
    elif standing is not None:
        out['objective'] = _field_by_field(standing, patch)
    elif _whole(cls, patch):
        out['objective'] = patch
    else:
        raise LanguageError(
            f"patch '{name}' edits the objective, which its base does not declare. A patch creates the "
            f'objective only by writing it whole, and this one is not: {_incomplete("objective", cls, patch)}.'
        )
    return out


def _field_by_field(under: object, over: object) -> object:
    """*over* laid on *under*: mappings merge, ``None`` drops the field, and everything else replaces.

    A dropped field takes the schema's default when the result loads, which
    is what makes ``upper: null`` an open bound and ``domain: null`` a
    continuous variable, whatever the schema lets a file write there.
    """
    if isinstance(under, dict) and isinstance(over, dict):
        merged = dict(under)
        for key, value in over.items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = _field_by_field(merged.get(key), value)
        return merged
    return over
