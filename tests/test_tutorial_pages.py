# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Each tutorial shows what each step prints, and each step prints that.

A tutorial writes its files as YAML blocks, runs `python -m mathspec` from a
shell, and runs Python blocks one after another. A YAML block with a title
writes that file; one without a title replaces the top-level sections it names
in the last file written, and adds the others at the end. A step shown as a
"Command line" tab and a "Python" tab is one step with two spellings, and both
print the same thing. A text block or a rendered output right after a step is
what that step prints; a step with none after it prints nothing.
"""

from __future__ import annotations

import contextlib
import io
import re
import textwrap
from pathlib import Path

import pytest

from mathspec.__main__ import main
from mathspec.errors import LanguageError

TUTORIALS = Path(__file__).resolve().parent.parent / 'docs' / 'tutorials'
PAGES = ['first-spec.md', 'storage.md', 'several-files.md']

#: A fenced block at the start of a line, with its language and its title.
FENCE = re.compile(r'^```(\w+)(?: title="([^"]+)")?\n(.*?)^```$', re.MULTILINE | re.DOTALL)
#: A rendered output: an admonition whose indented body is what the step printed.
RENDERED = re.compile(r'^!!! example "Rendered output"\n\n((?:    .*\n|\n)+)', re.MULTILINE)
#: A top-level key of a YAML file, with every line under it.
SECTION = re.compile(r'^(\w+):.*?(?=^\w|\Z)', re.MULTILINE | re.DOTALL)
#: One tab of a "Command line" / "Python" pair, with the fence it holds.
TAB = re.compile(r'^=== "(?:Command line|Python)"\n\n    ```(bash|python)\n(.*?)^    ```$', re.MULTILINE | re.DOTALL)
#: A fenced step indented into an admonition or a tab.
INDENTED = re.compile(r'^[ \t]+```(?:yaml|bash|python)', re.MULTILINE)
#: The title of a step that is one tab of a pair.
PAIRED = 'tab'


def _steps(text: str) -> list[tuple[str, str | None, str]]:
    """Every fenced block, tab and rendered output on a page, in page order, as kind, title and body."""
    found = [(m.start(), m.group(1), m.group(2), m.group(3)) for m in FENCE.finditer(text)]
    found += [(m.start(), m.group(1), PAIRED, textwrap.dedent(m.group(2))) for m in TAB.finditer(text)]
    found += [
        (m.start(), 'rendered', None, textwrap.dedent(m.group(1)).strip() + '\n') for m in RENDERED.finditer(text)
    ]
    return [(kind, title, body) for _, kind, title, body in sorted(found)]


def _after(steps: list[tuple[str, str | None, str]], index: int) -> tuple[str, str | None, str] | None:
    """The step after *index*, past the other tab of its pair."""
    rest = steps[index + 1 :]
    if steps[index][1] == PAIRED and rest and rest[0][1] == PAIRED:
        rest = rest[1:]
    return rest[0] if rest else None


def _patch(text: str, patch: str) -> str:
    """*text* with each top-level section of *patch* in place of the one of that name, or at the end."""
    sections = {m.group(1): m.group(0) for m in SECTION.finditer(text)}
    sections |= {m.group(1): m.group(0) for m in SECTION.finditer(patch)}
    return ''.join(sections.values())


def _run(line: str) -> tuple[int, str, str]:
    """Run one `python -m mathspec` line, and return its exit status, stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = main(line.split()[3:])
    return status, out.getvalue(), err.getvalue()


@pytest.mark.parametrize('page', PAGES)
def test_every_step_the_reader_types_is_one_the_test_runs(page):
    text = (TUTORIALS / page).read_text()
    assert len(INDENTED.findall(text)) == len(TAB.findall(text)), 'a step indented into an admonition would go unrun'


@pytest.mark.parametrize('page', PAGES)
def test_every_step_prints_what_the_page_shows(page, tmp_path, monkeypatch):
    """The steps share one folder and one namespace, as a reader running them in order does."""
    monkeypatch.chdir(tmp_path)
    steps = _steps((TUTORIALS / page).read_text())
    namespace: dict[str, object] = {}
    written: Path | None = None
    for index, (kind, title, body) in enumerate(steps):
        following = _after(steps, index)
        expected = following[2].strip() if following and following[0] in ('text', 'rendered') else ''
        if kind == 'yaml':
            written = Path(title) if title else written
            assert written is not None, f'step {index} patches a file before any is written'
            written.write_text(body if title else _patch(written.read_text(), body))
        elif kind == 'bash':
            for line in body.splitlines():
                assert line.startswith('python -m mathspec '), f'step {index} runs a command the test cannot'
                status, out, err = _run(line)
                assert (out + err).strip() == expected, f'step {index} printed otherwise'
                assert status == int(bool(err)), f'step {index} exits 1 only where the file is refused'
        elif kind == 'python':
            printed = io.StringIO()
            try:
                with contextlib.redirect_stdout(printed):
                    exec(body, namespace)
            except LanguageError as e:
                assert str(e).strip() == expected, f'step {index} refused otherwise'
            else:
                assert printed.getvalue().strip() == expected, f'step {index} printed otherwise'
