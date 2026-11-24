# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""What one mutant is checked against, and what a failure looks like.

No check needs an expected answer:

- **load**: [`to_spec`][mathspec.to_spec] accepts the mapping or raises a
  ``MathSpecError``. Any other exception is a crash, and so is a refusal that
  takes longer than ``SLOW_S``.
- **round trip**: the YAML an accepted spec writes, plain and canonical, reads
  back as the same spec.
- **canonical**: the form is the same for every spelling of one spec, so a
  shuffled key order and commuted terms and factors leave it as it was.
- **lower**: the program, the expansion and the program of the expansion build,
  and an expansion expanded again is the same spec.
- **print**: every format typesets the spec as written and expanded, with the
  legend and without it, and with every named expression written in; advice
  reads it.

:func:`check` returns the findings rather than raising, so a campaign can count
and group them.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import random
import re
import time
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import yaml

from mathspec import advice, to_spec, typeset
from mathspec.errors import MathSpecError
from tests.fuzz.mutate import _slots

if TYPE_CHECKING:
    from mathspec.spec import Spec

#: A refusal slower than this is a finding: everything is decided without data.
SLOW_S = 5.0

FORMATS = ('latex', 'typst', 'markdown')


@dataclass(frozen=True)
class Finding:
    """One thing a mutant broke.

    Attributes:
        oracle: Which check found it.
        summary: One line, the same for every mutant that broke it the same way.
        detail: What to read to reproduce it: the exception or the two texts.
    """

    oracle: str
    summary: str
    detail: str

    @property
    def signature(self) -> str:
        """What groups findings across seeds: the oracle and the summary with names and numbers blanked."""
        blanked = re.sub(r"'[^']*'|`[^`]*`|-?\d+(\.\d+)?(e-?\d+)?", '_', self.summary)
        return f'{self.oracle}: {blanked}'


@dataclass
class Outcome:
    """What :func:`check` concluded about one mutant."""

    accepted: bool
    findings: list[Finding]
    digest: str = ''
    """A hash of every text the accepted spec printed, to compare across interpreter hash seeds."""


def check(raw: dict[str, Any], seed: int = 0) -> Outcome:
    """Run every oracle on *raw* and return what broke."""
    started = time.perf_counter()
    try:
        spec = to_spec(copy.deepcopy(raw))
    except MathSpecError:
        seconds = time.perf_counter() - started
        slow = [Finding('slow', f'a refusal takes {seconds:.0f} s', '')] if seconds > SLOW_S else []
        return Outcome(False, slow)
    except Exception as e:
        return Outcome(False, [_crash('load', e)])

    findings: list[Finding] = []
    printed: list[str] = []
    findings += _round_trip(spec, printed)
    findings += _canonical(raw, spec, random.Random(seed))
    expanded = _lower(spec, findings)
    findings += _print(spec, expanded, printed)
    digest = hashlib.sha256('\x00'.join(printed).encode()).hexdigest()
    return Outcome(True, findings, digest)


def _round_trip(spec: Spec, printed: list[str]) -> list[Finding]:
    canonical = spec.to_yaml(canonical=True)
    printed.append(canonical)
    findings = []
    for name, text in (('to_yaml', spec.to_yaml()), ('canonical', canonical)):
        try:
            again = to_spec(text)
        except Exception as e:
            findings.append(
                Finding('round-trip', f'the {name} form does not load back: {_first(e)}', f'{text}\n{_trace(e)}')
            )
            continue
        if again.to_yaml(canonical=True) != canonical:
            findings.append(
                Finding(
                    'round-trip',
                    f'the {name} form loads back as a different spec',
                    _two(canonical, again.to_yaml(canonical=True)),
                )
            )
        if name == 'to_yaml' and again != spec:
            findings.append(Finding('round-trip', 'the to_yaml form loads back as a spec that compares unequal', text))
    return findings


def _canonical(raw: dict[str, Any], spec: Spec, rng: random.Random) -> list[Finding]:
    """One spec, spelled another way, has the canonical form it had."""
    canonical = spec.to_yaml(canonical=True)
    findings = []
    for name, respelt in (('shuffled keys', _shuffled(raw, rng)), ('commuted terms', _commuted(raw, rng))):
        if respelt is None:
            continue
        try:
            other = to_spec(respelt).to_yaml(canonical=True)
        except MathSpecError as e:
            findings.append(
                Finding('canonical', f'the spec with {name} is refused: {_first(e)}', yaml.safe_dump(respelt))
            )
            continue
        except Exception as e:
            findings.append(_crash('load', e, f' ({name})'))
            continue
        if other != canonical:
            findings.append(
                Finding('canonical', f'the spec with {name} has another canonical form', _two(canonical, other))
            )
    return findings


def _shuffled(node: Any, rng: random.Random) -> Any:
    """*node* with every mapping's keys in another order, and the lists as they were."""
    if isinstance(node, dict):
        items = list(node.items())
        rng.shuffle(items)
        return {key: _shuffled(value, rng) for key, value in items}
    if isinstance(node, list):
        return [_shuffled(value, rng) for value in node]
    return node


def _commuted(raw: dict[str, Any], rng: random.Random) -> dict[str, Any] | None:
    """*raw* with the operands of some ``+`` and ``*`` swapped, or None where no expression parses as Python."""
    respelt, changed = copy.deepcopy(raw), False
    for path, value in list(_slots(respelt)):
        if not (path and isinstance(value, str) and path[-1] in ('expression', 'otherwise', 'template')):
            continue
        try:
            tree = ast.parse(value, mode='eval')
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult)) and rng.random() < 0.5:
                node.left, node.right = node.right, node.left
                changed = True
        parent = respelt
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = ast.unparse(tree)
    return respelt if changed else None


def _lower(spec: Spec, findings: list[Finding]) -> Spec | None:
    for name, step in (('program', lambda: spec.program), ('expand', spec.expand)):
        try:
            step()
        except Exception as e:
            findings.append(_crash(name, e))
            return None
    expanded = spec.expand()
    try:
        expanded.program  # noqa: B018 — building the program is the check
        twice = expanded.expand()
    except Exception as e:
        findings.append(_crash('expand', e, ' (the expansion)'))
        return None
    if twice.to_yaml(canonical=True) != expanded.to_yaml(canonical=True):
        findings.append(
            Finding(
                'expand',
                'expanding an expansion changes it',
                _two(expanded.to_yaml(canonical=True), twice.to_yaml(canonical=True)),
            )
        )
    return expanded


def _print(spec: Spec, expanded: Spec | None, printed: list[str]) -> list[Finding]:
    findings = []
    variants = [
        ('as written', spec, {}),
        ('no legend', spec, {'legend': False}),
        ('inlined', spec, {'inline_expressions': True}),
    ]
    if expanded is not None:
        variants.append(('expanded', expanded, {}))
    for fmt in FORMATS:
        for form, which, options in variants:
            try:
                printed.append(typeset(which, fmt, **options))
            except Exception as e:
                findings.append(_crash(f'typeset-{fmt}', e, f' ({form})'))
    try:
        printed.extend(str(note) for note in advice(spec))
    except Exception as e:
        findings.append(_crash('advice', e))
    return findings


def _crash(where: str, e: BaseException, context: str = '') -> Finding:
    return Finding(f'crash-{where}', f'{type(e).__name__}{context}: {_first(e)}', _trace(e))


def _first(e: BaseException) -> str:
    text = str(e).strip()
    return text.splitlines()[0][:200] if text else type(e).__name__


def _trace(e: BaseException) -> str:
    return ''.join(traceback.format_exception(e))[-6000:]


def _two(before: str, after: str) -> str:
    return f'--- before\n{before}\n--- after\n{after}'
