# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""``python -m mathspec <command> spec.yaml`` — the shell front.

``check`` loads the file and prints the language's advice; ``canonical``
writes the spec in the form two files that state the same spec share; ``diff``
writes two specs in that form and prints where they differ; one further command per
typeset format, read off [`mathspec._typesetting.FORMATS`][]. Every command reads
the file as written, and nothing here writes a formulation out unasked.
The typeset commands take ``--expand``, because a shell cannot compose
[`expand`][mathspec.spec.Spec.expand] the way a caller does and the rows are a
different document; ``check`` has no such flag, because advice reads an entry
as the rows it states.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from mathspec._advising import advice
from mathspec._typesetting import FORMATS, typeset
from mathspec._validation import to_spec
from mathspec.errors import MathSpecError


def parser() -> argparse.ArgumentParser:
    """The commands, built from ``FORMATS``."""
    front = argparse.ArgumentParser(prog='python -m mathspec')
    commands = front.add_subparsers(dest='command', required=True)

    check = commands.add_parser('check', help='load a spec, and print what the language advises')
    check.add_argument('spec', help='path to a mathspec YAML file')

    canonical = commands.add_parser('canonical', help='write a spec in the form two files that state it share')
    canonical.add_argument('spec', help='path to a mathspec YAML file')
    canonical.add_argument('-o', '--out', help='write here instead of stdout')

    diff = commands.add_parser('diff', help='print where two specs differ in the canonical form, and exit 1 if they do')
    diff.add_argument('before', help='path to a mathspec YAML file')
    diff.add_argument('after', help='path to a mathspec YAML file')

    for name in FORMATS:
        command = commands.add_parser(name, help=f'render a spec as {name}')
        command.add_argument('spec', help='path to a mathspec YAML file')
        command.add_argument('-o', '--out', help='write here instead of stdout')
        command.add_argument('--symbols', help='sidecar YAML saying how names should print')
        command.add_argument('--standalone', action='store_true', help='emit a compilable document')
        command.add_argument('--no-legend', action='store_true', help='omit the tables of symbols and notation')
        command.add_argument('--no-numbers', action='store_true', help='leave the equations unnumbered')
        command.add_argument(
            '--inline-expressions', action='store_true', help='substitute each named expression where it is used'
        )
        command.add_argument(
            '--expand',
            action='store_true',
            help='print the variables and constraints the piecewise: and sos: entries state, not the entries',
        )
    return front


def _diff(before: str, after: str) -> int:
    """Print a unified diff of the canonical forms of *before* and *after*, and return ``diff``'s exit status.

    The status is 0 when the two specs are the same, 1 when they differ, and 2
    when the language refuses either file, so a CI job reads it as it reads
    ``diff``. Both forms are written now, by this mathspec, so a release that
    changes the form changes both sides alike.
    """
    try:
        old, new = (to_spec(path).to_yaml(canonical=True) for path in (before, after))
    except MathSpecError as e:
        sys.stderr.write(f'{e}\n')
        return 2
    sys.stdout.writelines(
        difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), before, after)
    )
    return int(old != new)


def main(argv: list[str] | None = None) -> int:
    """Run one command; a refused file is its message on stderr and exit status 1.

    Advice is not a refusal: ``check`` prints it and exits 0. ``diff`` keeps
    ``diff``'s exit statuses, so two specs that differ exit 1 and a refused file
    exits 2.
    """
    args = parser().parse_args(argv)
    if args.command == 'check':
        try:
            notes = advice(args.spec)
        except MathSpecError as e:
            sys.stderr.write(f'{e}\n')
            return 1
        sys.stdout.write(''.join(f'{note}\n' for note in notes))
        return 0
    if args.command == 'diff':
        return _diff(args.before, args.after)
    if args.command == 'canonical':
        try:
            text = to_spec(args.spec).to_yaml(canonical=True)
        except MathSpecError as e:
            sys.stderr.write(f'{e}\n')
            return 1
    else:
        spec = to_spec(args.spec).expand() if args.expand else args.spec
        text = typeset(
            spec,
            args.command,
            symbols=args.symbols,
            standalone=args.standalone,
            legend=not args.no_legend,
            numbered=not args.no_numbers,
            inline_expressions=args.inline_expressions,
        )
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
