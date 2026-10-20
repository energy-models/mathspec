# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""One spec under other names, so a fragment written once serves several sets of names."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
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


def rename(source: Source, names: Mapping[str, str]) -> Spec:
    """*source* with each name in *names* replaced by its new name.

    A name is replaced everywhere the spec writes it: as the key of its entry,
    in ``dims:``, on a relation's sides, in ``adds_to:``, and in every
    expression, ``where:``, bound, case and assumption that reads it,
    ``given:`` included. Only whole names are replaced, and the text around
    each keeps its layout. A relation column spelt like a renamed name is
    renamed with it, since the column is how a call reads the relation.
    Prose is kept as written: a description, a case's label, and a macro's
    formals and the template text that reads them.

    The result composes as any spec does, so one fragment written over
    placeholder names serves several classes:
    ``merge([..., rename('unit.yaml', {'unit': 'generator', ...}), ...])``.

    Args:
        source: The spec to rename: a YAML path, YAML text, a mapping, or a
            loaded [`Spec`][mathspec.spec.Spec].
        names: Each name to its new name. All of them are replaced at once,
            so two names may swap.

    Returns:
        The renamed spec, loaded. An empty *names* returns *source* loaded,
        and renaming back with the inverse map returns a spec with the
        canonical form of *source*.

    Raises:
        LanguageError: *source* does not load; a name in *names* is one
            *source* neither declares nor reads under ``given:``; a new name
            is one *source* keeps for an entry that is not renamed; two names
            take one new name; or the renamed spec does not load.
        FileNotFoundError: A ``str`` with no newline that names no file.
    """
    spec = to_spec(source)
    _checked(names, _declared(spec))
    return to_spec(cast('dict[str, object]', _renamed(Spec, spec.to_dict(), names)))


def _declared(spec: Spec) -> dict[str, str]:
    """Every name *spec* declares or reads under ``given:``, with what it is, which a refusal says."""
    declared = {name: GIVEN_KINDS[kind] for kind in GIVEN_KINDS for name in getattr(spec.given, kind)}
    for section in (*SHARED_SECTIONS, *OWNED_SECTIONS):
        declared |= dict.fromkeys(getattr(spec, section), _singular(section))
    return declared


def _checked(names: Mapping[str, str], declared: Mapping[str, str]) -> None:
    """Refuse a map that renames nothing the spec has, or lands two names on one."""
    for old in names:
        if old not in declared:
            msg = (
                f"rename names '{old}', which the spec neither declares nor reads under 'given:'. "
                f'{did_you_mean(old, declared)}'
            )
            raise LanguageError(msg)
    for old, new in names.items():
        if new in declared and new not in names:
            msg = (
                f"rename gives the {declared[old]} '{old}' the name '{new}', which the spec keeps for its "
                f"{declared[new]} '{new}'. Rename that one too, or choose another name."
            )
            raise LanguageError(msg)
    for new, count in Counter(names.values()).items():
        if count > 1:
            olds = [f"'{old}'" for old, to in names.items() if to == new]
            msg = (
                f"rename gives {', '.join(olds[:-1])} and {olds[-1]} the one name '{new}'. Give each a name of its own."
            )
            raise LanguageError(msg)


def _renamed(cls: type[BaseModel], entry: object, names: Mapping[str, str]) -> object:
    """*entry*, as *cls* is written, with *names* replaced wherever the schema holds a name or an expression.

    The schema decides what each field holds, so a field added to it is
    renamed without a change here. A description and a fixed choice (a
    ``Literal``, such as a dtype) are kept. A field of entries has its keys
    renamed, except ``cases:``, whose keys label rows. Every other string is
    text that names stand in. An entry that is not a mapping is a short form
    of one: an expression on one line, or a piecewise link written as a list.
    """
    if not isinstance(entry, Mapping):
        return _in_text(entry, names)
    if cls is MacroSpec:
        return _macro(entry, names)
    out: dict[str, object] = {}
    for field, value in cast('Mapping[str, object]', entry).items():
        annotation = cls.model_fields[field].annotation
        if field == 'description' or _is_choice(annotation):
            out[field] = value
        elif (each := _entries_of(annotation)) is not None:
            labels = field == 'cases'
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
    """A macro renamed around its formals, which are the template's own names and nothing the spec declares."""
    formals = {*cast('list[str]', entry.get('args', [])), *cast('list[str]', entry.get('kwargs', []))}
    outside = {old: new for old, new in names.items() if old not in formals}
    return {field: _in_text(value, outside) if field == 'template' else value for field, value in entry.items()}


def _in_text(value: object, names: Mapping[str, str]) -> object:
    """*value* with every name token in *names* replaced: a string, or the lists and mappings strings sit in."""
    if isinstance(value, str):
        return _TOKEN.sub(partial(_token, text=value, names=names), value)
    if isinstance(value, list):
        return [_in_text(item, names) for item in value]
    if isinstance(value, Mapping):
        return {_in_text(key, names): _in_text(item, names) for key, item in value.items()}
    return value


def _token(match: re.Match[str], text: str, names: Mapping[str, str]) -> str:
    """One token, renamed where it is a name in *names* and not the keyword of a call, such as ``over=``."""
    name = match['name']
    if name is None or name not in names or _KEYWORD.match(text, match.end()):
        return match[0]
    return names[name]


def _entries_of(annotation: object) -> type[BaseModel] | None:
    """The class of each entry where a field maps names to entries, as ``parameters:`` and ``cases:`` do."""
    return _model_in(get_args(annotation)[1]) if get_origin(annotation) is dict else None


def _model_in(annotation: object) -> type[BaseModel] | None:
    """The schema class an annotation holds, alone, in a list or beside ``None``; ``None`` where it holds none."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return next((model for arg in get_args(annotation) if (model := _model_in(arg)) is not None), None)


def _is_choice(annotation: object) -> bool:
    """Whether a field holds one of a fixed set of words, which no name can stand in."""
    return get_origin(annotation) is Literal or any(_is_choice(arg) for arg in get_args(annotation))
