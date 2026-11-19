# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""One spec under other names, so that a fragment written once states several components."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Mapping
from functools import partial
from typing import TYPE_CHECKING, Literal, cast, get_args, get_origin

from pydantic import BaseModel

from mathspec._composition import GIVEN_KINDS, OWNED_SECTIONS, SHARED_SECTIONS, _singular
from mathspec._expression_parser import NAME, REAL
from mathspec._validation import to_spec
from mathspec.errors import LanguageError, did_you_mean
from mathspec.spec import MacroSpec, Spec

if TYPE_CHECKING:
    from mathspec._composition import Source

#: One token of expression or where text: a quoted label, a number, or a name.
#: A number is matched before a name, so the exponent of ``1e6`` is not read as one.
_TOKEN = re.compile(rf"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|(?:{REAL})|\d+|(?P<name>{NAME})""")

#: What follows a keyword's name in a call: ``over=``, and not the ``==`` of a comparison.
_KEYWORD = re.compile(r'\s*=(?!=)')

_KEPT = frozenset({'description', 'one_of'})
_LABELLED = frozenset({'cases', 'links'})


def rename(source: Source, names: Mapping[str, str | None] | Callable[[str], str | None]) -> Spec:
    """*source* with each name that *names* changes replaced by its new name.

    A name is replaced everywhere it occurs in the spec: as the key of its
    entry, in ``dims:``, on the sides of a relation, in ``adds_to:``, under
    ``given:``, and in the text of every expression, ``where:``, bound, case
    and assumption. Only whole names are replaced, and the text around each
    name is unchanged. A relation column named after its dimension is renamed
    with the dimension, because an expression refers to a relation by its
    columns.

    Prose and labels stay as written: a description, the labels of
    ``one_of:``, the name of a case or of a piecewise link, and the arguments
    of a macro with the template text that uses them.

    The result is a spec like any other. So one fragment written with
    placeholder names can state several components in one merge:
    ``merge([..., rename('unit.yaml', {'unit': 'generator', ...}), ...])``.

    Args:
        source: The spec to rename: a YAML path, YAML text, a mapping, or a
            loaded [`Spec`][mathspec.spec.Spec].
        names: A map from each name to its new name, or a function. All
            names are replaced at once, so two names may swap. A function is
            called once with each name that *source* declares or lists under
            ``given:``. It returns the new name, or ``None`` to keep the name.
            In a map too, ``None`` or the same name keeps the name.

    Returns:
        The renamed spec, loaded. An empty *names* returns *source* loaded.
        A second call with the inverse map returns a spec with the canonical
        form of *source*.

    Raises:
        LanguageError: *source* does not load, or the renamed spec does not
            load. Also when a key of *names* is not a name that *source*
            declares or lists under ``given:``. Also when a new name is the
            name of an entry that is not renamed, or an argument of a macro
            whose template uses the old name.
            Also when two names get the same new name, or when an old or a new
            name is a relation column that is not named after its dimension.
        FileNotFoundError: A ``str`` with no newline that names no file.
        TypeError: *names* is neither a mapping nor a function.
    """
    spec = to_spec(source)
    declared = _declared(spec)
    if isinstance(names, Mapping):
        asked = names
    elif callable(names):
        asked = {old: names(old) for old in declared}
    else:
        msg = f'rename takes a mapping or a function as names, not {type(names).__name__}.'
        raise TypeError(msg)
    changed = _checked(asked, declared, spec)
    return to_spec(cast('dict[str, object]', _renamed(Spec, spec.to_dict(), changed)))


def _declared(spec: Spec) -> dict[str, str]:
    """Every name that *spec* declares or lists under ``given:``, with the kind of its entry for a refusal."""
    declared = {name: GIVEN_KINDS[kind] for kind in GIVEN_KINDS for name in getattr(spec.given, kind)}
    for section in (*SHARED_SECTIONS, *OWNED_SECTIONS):
        declared |= dict.fromkeys(getattr(spec, section), _singular(section))
    return declared


def _checked(names: Mapping[str, str | None], declared: Mapping[str, str], spec: Spec) -> dict[str, str]:
    """The names that change, after refusing a map that would change the meaning of *spec* or not load.

    A token in text is renamed wherever it has the spelling, so a new name that
    is the argument of a macro whose template uses the old name, or a name that
    is a relation column named after something else, would change an
    expression without a refusal.
    """
    for old in names:
        if old not in declared:
            msg = (
                f"rename cannot change '{old}', which the spec neither declares nor lists under 'given:'. "
                f'{did_you_mean(old, declared, label="Names")}'
            )
            raise LanguageError(msg)
    changed = {old: new for old, new in names.items() if new is not None and new != old}
    columns = {
        column: relation
        for relation, entry in spec.relations.items()
        for side in (entry.key, entry.values)
        if isinstance(side, Mapping)
        for column, dimension in side.items()
        if column != dimension
    }
    for old, new in changed.items():
        for macro, entry in spec.macros.items():
            if new in (*entry.args, *entry.kwargs) and old in _names_in(entry.template):
                msg = (
                    f"rename gives the {declared[old]} '{old}' the name '{new}', which is an argument of the macro "
                    f"'{macro}', whose template uses '{old}'. Choose another name."
                )
                raise LanguageError(msg)
        if (column := old if old in columns else new) in columns:
            msg = (
                f"rename changes '{old}' to '{new}', and '{column}' is also a column of the relation "
                f"'{columns[column]}'. Give the column another name in the file, or choose another name."
            )
            raise LanguageError(msg)
    for old, new in changed.items():
        if new in declared and new not in changed:
            msg = (
                f"rename gives the {declared[old]} '{old}' the name '{new}', which the {declared[new]} '{new}' "
                f'already has. Rename that one too, or choose another name.'
            )
            raise LanguageError(msg)
    for new, count in Counter(changed.values()).items():
        if count > 1:
            olds = [f"'{old}'" for old, to in changed.items() if to == new]
            msg = (
                f"rename gives {', '.join(olds[:-1])} and {olds[-1]} the one name '{new}'. Give each a name of its own."
            )
            raise LanguageError(msg)
    return changed


def _renamed(cls: type[BaseModel], entry: object, names: Mapping[str, str]) -> object:
    """*entry*, as *cls* is written, with *names* replaced wherever the schema has a name or an expression.

    The annotation of a field sets what the field contains, so a new field
    with a name or an expression is renamed without a change here. A new field
    with prose or labels needs a place in ``_KEPT`` or ``_LABELLED``. A description, the labels
    of ``one_of:`` and a fixed choice (a ``Literal``, such as a dtype) are
    kept. A field of entries has its keys renamed, except ``cases:`` and
    ``links:``, whose keys are labels of rows. Every other string is text that
    may contain names. An entry that is not a mapping is a short form of one:
    an expression on one line, or a piecewise link written as a list.
    """
    if not isinstance(entry, Mapping):
        return _in_text(entry, names)
    if cls is MacroSpec:
        return _macro(entry, names)
    out: dict[str, object] = {}
    for field, value in cast('Mapping[str, object]', entry).items():
        annotation = cls.model_fields[field].annotation
        if field in _KEPT or _is_choice(annotation):
            out[field] = value
        elif (each := _entries_of(annotation)) is not None:
            labels = field in _LABELLED
            out[field] = {
                (key if labels else names.get(key, key)): _renamed(each, item, names)
                for key, item in cast('Mapping[str, object]', value).items()
            }
        elif (model := _model_in(annotation)) is None:
            out[field] = _in_text(value, names)
        elif isinstance(value, list):
            out[field] = [_renamed(model, item, names) for item in value]
        else:
            out[field] = _renamed(model, value, names)
    return out


def _macro(entry: Mapping[str, object], names: Mapping[str, str]) -> dict[str, object]:
    """A macro renamed except for its arguments, which are names of the template and not names the spec declares."""
    formals = {*cast('list[str]', entry.get('args', [])), *cast('list[str]', entry.get('kwargs', []))}
    outside = {old: new for old, new in names.items() if old not in formals}
    return {field: _in_text(value, outside) if field == 'template' else value for field, value in entry.items()}


def _in_text(value: object, names: Mapping[str, str]) -> object:
    """*value* with every name token in *names* replaced: a string, or a list or mapping of strings."""
    if isinstance(value, str):
        return _TOKEN.sub(partial(_token, text=value, names=names), value)
    if isinstance(value, list):
        return [_in_text(item, names) for item in value]
    if isinstance(value, Mapping):
        return {_in_text(key, names): _in_text(item, names) for key, item in value.items()}
    return value


def _names_in(text: str) -> set[str]:
    """The name tokens of *text*, as the rename reads them."""
    return {match['name'] for match in _TOKEN.finditer(text) if match['name']}


def _token(match: re.Match[str], text: str, names: Mapping[str, str]) -> str:
    """One token, renamed where it is a name in *names* and not the keyword of a call, such as ``over=``."""
    name = match['name']
    if name is None or name not in names or _KEYWORD.match(text, match.end()):
        return match[0]
    return names[name]


def _entries_of(annotation: object) -> type[BaseModel] | None:
    """The class of each entry where a field maps names to entries, as ``parameters:`` and ``cases:`` do."""
    origin = get_origin(annotation)
    return _model_in(get_args(annotation)[1]) if isinstance(origin, type) and issubclass(origin, Mapping) else None


def _model_in(annotation: object) -> type[BaseModel] | None:
    """The schema class in an annotation, alone, in a list or beside ``None``, or ``None`` where it has none."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return next((model for arg in get_args(annotation) if (model := _model_in(arg)) is not None), None)


def _is_choice(annotation: object) -> bool:
    """Whether the value of a field is one of a fixed set of words, none of which is a name."""
    return get_origin(annotation) is Literal or any(_is_choice(arg) for arg in get_args(annotation))
