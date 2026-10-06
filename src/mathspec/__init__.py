# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The language: what a YAML file may say, and what it means.

The top level is what a consumer calls: [`to_spec`][], the one door to a
file, and the verbs over what it returns. The rest of the surface is three
modules, each with one rule:

- [`mathspec.spec`][] is what the file *says*: [`Spec`][mathspec.spec.Spec]
  and the blocks it holds.
- [`mathspec.program`][] is what the file *means*: the
  [`Program`][mathspec.program.Program] a spec lowers to, its nodes, and the
  [`Advice`][mathspec.program.Advice] the language gives about it.
- [`mathspec.errors`][] is what a consumer catches.

Everything between them — both grammars and the tree they build — is
package-private, because a consumer reads a program instead.
"""

from mathspec import errors, program, spec
from mathspec.advising import advice
from mathspec.composition import merge, override
from mathspec.typesetting import (
    FormatName,
    SymbolTable,
    to_latex,
    to_markdown,
    to_typst,
    typeset,
    typeset_line,
)
from mathspec.validation import to_spec

__all__ = [
    'FormatName',
    'SymbolTable',
    'advice',
    'errors',
    'merge',
    'override',
    'program',
    'spec',
    'to_latex',
    'to_markdown',
    'to_spec',
    'to_typst',
    'typeset',
    'typeset_line',
]

import warnings as _warnings
from importlib import metadata as _metadata

try:
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError as e:  # pragma: no cover
    _warnings.warn(f'Could not determine version of {__name__}\n{e!s}', stacklevel=2)
    __version__ = 'unknown'
