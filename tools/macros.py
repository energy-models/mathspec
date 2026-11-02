# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The release and the language version, as variables a page may write.

A page that states the current release, or points at the schema of the release
it documents, would go stale on every tag if it typed the number. The version
comes from the git tag and is never written into a file, so the macros plugin
of `mkdocs.yml` renders these at build time, fences included:

- `{{ mathspec.release }}`: the latest release reachable from `HEAD`. A
  raw.githubusercontent.com address of the schema takes its tag, `v` and the
  release, so a reader validates against a released schema even on a build
  from `main`.
- `{{ mathspec.language_version }}`: the highest of `SUPPORTED_VERSIONS`.
"""

from __future__ import annotations

import re
import subprocess
from functools import cache
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from mathspec.spec import SUPPORTED_VERSIONS

if TYPE_CHECKING:
    from zensical.extensions.macros import MacroEnv

ROOT = Path(__file__).resolve().parent.parent


def _git(*args: str) -> str:
    """`git` from the repository root, raising when it fails."""
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _release() -> str:
    """The latest tag reachable from `HEAD`, because the installed metadata is stale in a checkout."""
    try:
        return _git('describe', '--tags', '--abbrev=0').removeprefix('v')
    except (OSError, subprocess.CalledProcessError):
        return re.sub(r'\.dev\d+.*$', '', version('mathspec'))


@cache
def values() -> dict[str, str]:
    """The value of each variable, computed once per build."""
    return {
        'release': _release(),
        'language_version': str(max(SUPPORTED_VERSIONS)),
    }


def define_env(env: MacroEnv) -> None:
    """What the macros plugin calls to read the variables, as `mathspec.<name>`."""
    env.variables['mathspec'] = values()
