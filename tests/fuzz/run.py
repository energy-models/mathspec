# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Run a campaign over a range of seeds and group what broke.

Each seed is one mutant of one example (:mod:`tests.fuzz.mutate`), checked by
every oracle in :mod:`tests.fuzz.check` in a worker process. ``--hash-seeds``
runs every seed under two interpreter hash seeds and compares what the
accepted specs printed, so an output that depends on set order shows.

    pixi run python -m tests.fuzz --seeds 0:20000 --jobs 8
    pixi run python -m tests.fuzz --seeds 1234 -v
"""

from __future__ import annotations

import argparse
import collections
import json
import multiprocessing
import os
from pathlib import Path
from typing import Any

import yaml

#: A seed whose oracles take longer than this is reported as a hang.
TIMEOUT_S = 120


def _one(seed: int) -> dict[str, Any]:
    from tests.fuzz.check import check
    from tests.fuzz.mutate import corpus, mutant

    case = mutant(seed, _corpus(corpus))
    outcome = check(case.spec, seed)
    return {
        'seed': seed,
        'accepted': outcome.accepted,
        'digest': outcome.digest,
        'findings': [
            {'oracle': f.oracle, 'summary': f.summary, 'signature': f.signature, 'detail': f.detail}
            for f in outcome.findings
        ],
    }


_CORPUS: list[Any] = []


def _corpus(read: Any) -> list[Any]:
    if not _CORPUS:
        _CORPUS.extend(read())
    return _CORPUS


def _seeds(text: str) -> range:
    if ':' in text:
        start, stop = text.split(':')
        return range(int(start), int(stop))
    return range(int(text), int(text) + 1)


def _campaign(seeds: range, jobs: int, hash_seed: str) -> dict[int, dict[str, Any]]:
    os.environ['PYTHONHASHSEED'] = hash_seed
    records = {}
    with multiprocessing.get_context('spawn').Pool(jobs, maxtasksperchild=200) as pool:
        pending = {seed: pool.apply_async(_one, (seed,)) for seed in seeds}
        for seed, job in pending.items():
            try:
                records[seed] = job.get(timeout=TIMEOUT_S)
            except multiprocessing.TimeoutError:
                records[seed] = {'seed': seed, 'accepted': False, 'digest': '', 'findings': [
                    {'oracle': 'hang', 'summary': f'no verdict within {TIMEOUT_S} s', 'signature': 'hang', 'detail': ''}
                ]}  # fmt: skip
    return records


def _found(records: dict[int, dict[str, Any]]) -> dict[str, list[str]]:
    """Each seed with a finding, and the signatures it has, sorted: the shape a baseline file holds."""
    found = {str(seed): sorted({f['signature'] for f in r['findings']}) for seed, r in records.items()}
    return {seed: signatures for seed, signatures in found.items() if signatures}


def against_baseline(found: dict[str, list[str]], baseline: dict[str, list[str]], seeds: range) -> list[str]:
    """What differs from *baseline* over *seeds*: a finding it does not hold, and one it holds that did not recur.

    Both directions fail, as a strict ``xfail`` does: a fix that removes a
    finding leaves the baseline stale until it is written again.
    """
    problems = []
    for seed in seeds:
        now, then = set(found.get(str(seed), ())), set(baseline.get(str(seed), ()))
        problems += [f'seed {seed}: new finding — {s}' for s in sorted(now - then)]
        problems += [f'seed {seed}: no longer found, so drop it from the baseline — {s}' for s in sorted(then - now)]
    return problems


def against_kinds(found: dict[str, list[str]], kinds: dict[str, str]) -> list[str]:
    """Every signature that *kinds* does not name, with the first seed that has it."""
    seen: dict[str, str] = {}
    for seed, signatures in sorted(found.items(), key=lambda kv: int(kv[0])):
        for signature in signatures:
            seen.setdefault(signature, seed)
    return [f'a new kind of finding, first at seed {seed} — {s}' for s, seed in sorted(seen.items()) if s not in kinds]


def main(argv: list[str] | None = None) -> int:
    """Run the campaign; exit 1 on a finding, or on a difference from ``--baseline`` or ``--known``."""
    front = argparse.ArgumentParser(prog='python -m tests.fuzz')
    front.add_argument('--seeds', default='0:500', help='a seed, or a range start:stop')
    front.add_argument('--jobs', type=int, default=os.cpu_count() or 1)
    front.add_argument(
        '--hash-seeds', action='store_true', help='run twice under two hash seeds and compare the output'
    )
    front.add_argument('-v', '--verbose', action='store_true', help='print every finding in full, and the mutant')
    gate = front.add_mutually_exclusive_group()
    gate.add_argument('--baseline', type=Path, help='fail only where the findings differ from this file, seed by seed')
    gate.add_argument('--known', type=Path, help='fail only on a kind of finding this file does not name')
    gate.add_argument('--write-baseline', type=Path, help='write the findings to this file, and pass')
    args = front.parse_args(argv)

    seeds = _seeds(args.seeds)
    records = _campaign(seeds, args.jobs, '1')
    if args.hash_seeds:
        again = _campaign(seeds, args.jobs, '2')
        for seed, record in records.items():
            if record['digest'] != again[seed]['digest']:
                record['findings'].append({
                    'oracle': 'determinism', 'summary': 'the spec prints differently under another hash seed',
                    'signature': 'determinism: the spec prints differently under another hash seed', 'detail': '',
                })  # fmt: skip

    groups: dict[str, list[int]] = collections.defaultdict(list)
    for seed, record in records.items():
        for finding in record['findings']:
            groups[finding['signature']].append(seed)
            if args.verbose:
                from tests.fuzz.mutate import corpus, mutant

                case = mutant(seed, _corpus(corpus))
                print(f'--- seed {seed} ({case.source}; {case.edits}) [{finding["oracle"]}] {finding["summary"]}')
                print(yaml.safe_dump(case.spec, sort_keys=False) + finding['detail'] + '\n')
    accepted = sum(r['accepted'] for r in records.values())
    print(f'{len(seeds)} seeds, {accepted} accepted by the language')
    for signature, hit in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f'{len(hit):5d}  {signature}\n       seeds {hit[:8]}')

    found = _found(records)
    if args.write_baseline is not None:
        args.write_baseline.write_text(json.dumps(found, indent=1, sort_keys=True) + '\n', encoding='utf-8')
        print(f'wrote {len(found)} seeds with findings to {args.write_baseline}')
        return 0
    if args.baseline is not None or args.known is not None:
        path = args.baseline or args.known
        expected = json.loads(path.read_text(encoding='utf-8'))
        problems = against_baseline(found, expected, seeds) if args.baseline else against_kinds(found, expected)
        print('\n'.join(problems) or f'every finding is one {path} already holds')
        if problems and args.baseline:
            print(f'\nPrint a seed with `python -m tests.fuzz --seeds <n> -v`. After a fix, or a change to the '
                  f'mutator, write the baseline again: `python -m tests.fuzz --seeds {args.seeds} --write-baseline {path}`.')  # fmt: skip
        elif problems:
            print(f'\nPrint a seed with `python -m tests.fuzz --seeds <n> -v`, file what it shows, and add the kind '
                  f'to {path} under the issue.')  # fmt: skip
        return int(bool(problems))
    return int(bool(groups))
