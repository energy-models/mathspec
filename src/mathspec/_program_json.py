# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A program as plain JSON types, and back — what [`Program.to_dict`][mathspec.program.Program.to_dict] writes.

The reader exists so the suite can prove the export complete: a program that
reads back equal to itself lost nothing on the way out.
"""

from __future__ import annotations

import datetime
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import TYPE_CHECKING

from mathspec import program as p

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

#: What JSON holds.
type JSON = bool | int | float | str | list[JSON] | dict[str, JSON] | None

_NODES: dict[str, type[DataclassInstance]] = {
    name: cls
    for name, cls in vars(p).items()
    if isinstance(cls, type) and is_dataclass(cls) and cls.__module__ == p.__name__
}
_DATES: dict[str, type[datetime.date]] = {'date': datetime.date, 'datetime': datetime.datetime}
#: The nodes that name their relation rather than carry it: it sits under ``relations`` already.
_BY_NAME = (p.Direction, p.Partition)


def to_dict(program: p.Program) -> dict[str, object]:
    """*program* as nested dicts, lists and scalars that ``json.dumps(..., allow_nan=False)`` writes.

    Raises:
        ValueError: A NaN, which no node of the language holds.
    """
    return _as(_encode(program), dict)


def from_dict(data: Mapping[str, JSON]) -> p.Program:
    """The program [`to_dict`][] wrote *data* from.

    Raises:
        KeyError: A node class, or a relation a direction or partition names, that is not there.
        TypeError: *data* is not a program.
    """
    relations = _as(_decode(data['relations'], {}), dict)
    return _as(_decode(dict(data), relations), p.Program)


def _as[T](value: object, cls: type[T]) -> T:
    """*value*, refused unless it is a *cls*: what a node reads back as is known only at run time."""
    if not isinstance(value, cls):
        msg = f'{type(value).__name__} is not a {cls.__name__}.'
        raise TypeError(msg)
    return value


def _encode(value: object) -> JSON:
    """One value, dispatched on its runtime type."""
    if isinstance(value, datetime.date):
        return {'node': type(value).__name__, 'value': value.isoformat()}
    if isinstance(value, float) and math.isnan(value):
        msg = 'NaN has no JSON form, and no node of the language holds one.'
        raise ValueError(msg)
    if isinstance(value, float) and math.isinf(value):
        return {'node': 'float', 'value': 'inf' if value > 0 else '-inf'}
    if is_dataclass(value) and not isinstance(value, type):
        skip = 'relation' if isinstance(value, _BY_NAME) else None
        return {'node': type(value).__name__} | {
            f.name: _encode(getattr(value, f.name)) for f in fields(value) if f.name != skip
        }
    if isinstance(value, Mapping):
        return {'node': 'Mapping', 'entries': {_as(name, str): _encode(item) for name, item in value.items()}}
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    msg = f'{type(value).__name__} has no JSON form.'
    raise TypeError(msg)


def _decode(value: JSON, relations: Mapping[str, object]) -> object:
    """One value, dispatched on its ``node`` tag alone."""
    if isinstance(value, list):
        return tuple(_decode(item, relations) for item in value)
    if not isinstance(value, dict):
        return value
    node = _as(value['node'], str)
    if node == 'Mapping':
        return {name: _decode(item, relations) for name, item in _as(value['entries'], dict).items()}
    if node in _DATES:
        return _DATES[node].fromisoformat(_as(value['value'], str))
    if node == 'float':
        return float(_as(value['value'], str))
    cls = _NODES[node]
    kwargs = {key: _decode(item, relations) for key, item in value.items() if key != 'node'}
    if cls in _BY_NAME:
        kwargs['relation'] = relations[_as(kwargs['name'], str)]
    return cls(**kwargs)
