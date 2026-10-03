# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""What the language raises: the error tree, and the one wording a consumer's own refusals share."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pydantic import ValidationError


#: What ``mathspec.errors`` promises a consumer.
__all__ = ['DimensionError', 'LanguageError', 'MathSpecError', 'SchemaError', 'did_you_mean']


class MathSpecError(ValueError):
    """Base class for every error this package raises on purpose."""


class LanguageError(MathSpecError):
    """The spec is not sayable in the language, or does not obey its rules."""


class SchemaError(LanguageError):
    """What a load refuses: an unknown key, a bad ``dtype``, a duplicate YAML key, an unparseable or unresolvable expression."""


class DimensionError(LanguageError):
    """A dim-set rule was violated. Raised at load time, before any data."""


def did_you_mean(name: str, known: Iterable[str], *, label: str = 'Declared', listing: bool = True) -> str:
    """The repair clause for an unrecognised name: the near miss, or the set, or nothing where *listing* is off."""
    candidates = sorted(known)
    near = difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)
    if near:
        return f"Did you mean '{near[0]}'?"
    return f'{label}: {", ".join(candidates) or "nothing"}.' if listing else ''


def schema_error(exc: ValidationError) -> LanguageError:
    """A pydantic ``ValidationError`` as one of ours.

    Returns the original [`LanguageError`][] subclass where exactly one
    error carries one, and a [`SchemaError`][] otherwise.
    """
    errors = exc.errors()
    lines = []
    for error in errors:
        message = error.get('msg', '').removeprefix('Value error, ')
        where = '.'.join(str(part) for part in error.get('loc', ()))
        lines.append(f'{where}: {message}' if where else message)
    text = '\n'.join(lines) or str(exc)

    if len(errors) == 1:
        original = errors[0].get('ctx', {}).get('error')
        if isinstance(original, LanguageError):
            return type(original)(text)
    return SchemaError(text)


def prefixed(context: str, e: ValueError) -> str:
    """*e* under *context*, once — an expansion error already carries it."""
    return str(e) if str(e).startswith(context) else f'{context}: {e}'


def case_context(name: str, label: str | None) -> str:
    """The context an error inside one arm of a cased expression is reported under.

    Args:
        name: The named expression the arm belongs to.
        label: The case's name, or ``None`` for the block's ``otherwise:``.
    """
    where = 'otherwise' if label is None else f"case '{label}'"
    return f"Named expression '{name}', {where}"
