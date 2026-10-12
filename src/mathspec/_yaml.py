# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""How this project reads and writes a YAML file.

`yaml.safe_load` implements YAML 1.1, and two of its rules are wrong for a
language whose scalars are user data; both are fixed here:

- **1.2 booleans.** ``on``/``off``/``yes``/``no``/``y``/``n`` are ordinary
  names in this language — a country code as a dimension, a mode as a relation.
  YAML 1.1 resolves them to ``True``/``False``; only ``true``/``false`` are
  booleans here, which is the YAML 1.2 core schema.
- **Duplicate keys.** 1.1 lets the last one win silently, discarding a
  declaration the file plainly contains.

The output is plain ``dict``/``str``: no loader wrapper reaches the schema
or the AST.

Every spec this package writes is laid out by ``dump_yaml``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from mathspec.errors import SchemaError

#: The YAML 1.2 core-schema booleans. No other scalar loads as a bool.
_BOOL_1_2 = re.compile(r'^(?:true|True|TRUE|false|False|FALSE)$')


if TYPE_CHECKING:
    # Typed as SafeLoader: typeshed declares CSafeLoader unconditionally, and a PyYAML without libyaml lacks it.
    _BaseLoader = yaml.SafeLoader
else:
    # Same document either way: both drive the Python Resolver and SafeConstructor.
    _BaseLoader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


class _StrictLoader(_BaseLoader):
    """SafeLoader with 1.2 booleans. Duplicate keys are checked on the nodes."""


# Rebuilt rather than edited: the table is inherited, and mutating it reconfigures PyYAML process-wide.
_StrictLoader.yaml_implicit_resolvers = {
    ch: [(tag, rx) for tag, rx in pairs if tag != 'tag:yaml.org,2002:bool']
    for ch, pairs in _BaseLoader.yaml_implicit_resolvers.items()
}
_StrictLoader.add_implicit_resolver('tag:yaml.org,2002:bool', _BOOL_1_2, list('tTfF'))


#: PyYAML's tag for ``<<:``, the one key a mapping may carry more than once.
_MERGE = 'tag:yaml.org,2002:merge'


def _check_duplicate_keys(node: yaml.Node, origin: str) -> None:
    """Reject a mapping that declares the same key twice, or a key that is not a scalar.

    Checked on the node tree before construction, so a ``<<:`` merge key that
    a mapping overrides is not a duplicate — the override is the point — and
    two merge keys are two merges, which PyYAML accumulates.
    """
    if isinstance(node, yaml.MappingNode):
        seen: dict[str, int] = {}
        pairs: list[tuple[yaml.Node, yaml.Node]] = node.value
        for key_node, value_node in pairs:
            line = key_node.start_mark.line + 1
            if not isinstance(key_node, yaml.ScalarNode):
                msg = f'{origin}:{line}: a key is a list or a mapping. Write a name as the key.'
                raise SchemaError(msg)
            key = key_node.value
            if key_node.tag == _MERGE:
                _check_duplicate_keys(value_node, origin)
                continue
            if key in seen:
                msg = (
                    f'{origin}:{line}: duplicate key {key!r}, first declared on line {seen[key]}. Rename or delete one.'
                )
                raise SchemaError(msg)
            seen[key] = line
            _check_duplicate_keys(value_node, origin)
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            _check_duplicate_keys(item, origin)


def read_yaml(path: Path | str) -> dict[str, object]:
    """Read *path* off disk and parse it, in YAML 1.2's reading of scalars."""
    return parse_yaml(Path(path).read_text(encoding='utf-8'), str(path))


def read_spec(spec: str | Path) -> dict[str, object]:
    """A spec from a file or from its text — a newline decides which a ``str`` is.

    A [`Path`][] names a file, and so does a ``str`` with no
    newline in it, since no path holds one; a ``str`` with a newline is the
    YAML itself, which every file and every ``to_yaml()`` ends with. Nothing
    else is read off the content and nothing is read off the disk to decide.

    Raises:
        FileNotFoundError: A ``str`` with no newline that names no file — a
            one-line text is told to end with one.
    """
    if isinstance(spec, str) and '\n' not in spec and not Path(spec).is_file():
        msg = f'no file named {spec!r}. End YAML text with a newline, or pass a Path for a file.'
        raise FileNotFoundError(msg)
    if isinstance(spec, Path) or '\n' not in spec:
        return read_yaml(Path(spec))
    return parse_yaml(spec, 'YAML text')


def parse_yaml(text: str, origin: str = '<string>') -> dict[str, object]:
    """Parse YAML *text* as a mapping of sections.

    Args:
        text: The YAML source.
        origin: What a load error calls this source — a file's path, or the default for text that never was one.
    """
    loader = _StrictLoader(text)
    try:
        node = loader.get_single_node()
        if node is None:
            return {}
        _check_duplicate_keys(node, origin)
        data = loader.construct_document(node)
    finally:
        loader.dispose()
    if not data:
        return {}
    if not isinstance(data, dict):
        msg = f'{origin}: the file holds a {type(data).__name__}, not a mapping of sections. Write sections such as dimensions: at the top level.'
        raise SchemaError(msg)
    return data


class _Dumper(yaml.SafeDumper):
    """A dumper writing short lists and mappings on one line and a multi-line string as a block scalar."""


def _one_line(value: object) -> bool:
    """Whether *value* is a list or a mapping that is written on one line.

    A list is, when it holds only one-line scalars and such lists. A mapping is,
    when it holds only numbers, booleans, names and such lists, as ``bounds``
    does. A declaration with a description or an expression in it keeps one key
    on each line, so its text is never quoted to fit a flow mapping. Either one
    must also fit in 80 characters, counted as Python prints each value: a
    quote the emitter adds is not counted, so no line is written twice to
    measure it.
    """
    if _width(value) > 80:
        return False
    if isinstance(value, list):
        return all(_one_line(item) if isinstance(item, list) else _plain(item) for item in value)
    return isinstance(value, dict) and all(
        _one_line(item) if isinstance(item, list) else _plain(item) and _NAME.fullmatch(str(item)) is not None
        for item in value.values()
    )


#: A value a one-line mapping may hold: a number, a boolean, or a name such as ``p_max``, ``binary`` or ``-inf``.
_NAME = re.compile(r'[\w.+-]+')


def _width(value: object) -> int:
    """How wide *value* is on one line, brackets and separators included, each scalar as ``str`` prints it."""
    if isinstance(value, list):
        return sum(_width(item) + 2 for item in value) or 2
    if isinstance(value, dict):
        return sum(len(str(key)) + _width(item) + 4 for key, item in value.items()) or 2
    return len(str(value))


def _plain(value: object) -> bool:
    """Whether *value* is a scalar written on one line, which a flow collection can hold."""
    return not isinstance(value, (dict, list)) and not (isinstance(value, str) and '\n' in value)


def _string(dumper: yaml.SafeDumper, text: str) -> yaml.ScalarNode:
    return dumper.represent_scalar('tag:yaml.org,2002:str', text, style='|' if '\n' in text else None)


def _sequence(dumper: yaml.SafeDumper, items: list[object]) -> yaml.SequenceNode:
    return dumper.represent_sequence('tag:yaml.org,2002:seq', items, flow_style=_one_line(items))


def _mapping(dumper: yaml.SafeDumper, entries: dict[object, object]) -> yaml.MappingNode:
    return dumper.represent_mapping('tag:yaml.org,2002:map', entries, flow_style=_one_line(entries))


_Dumper.add_representer(str, _string)
_Dumper.add_representer(list, _sequence)
_Dumper.add_representer(dict, _mapping)


def dump_yaml(data: dict[str, object]) -> str:
    """*data* as YAML text, in the one layout every spec this package writes shares.

    A short list or mapping of plain values is written on one line, as
    ``dims: [day, hour]`` and ``bounds: {lower: 0}``. A multi-line string is
    a block scalar. No line is wrapped, so an edit to a long description
    changes one line of a diff.
    """
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=float('inf'))
