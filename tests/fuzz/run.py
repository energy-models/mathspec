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
import multiprocessing
import os
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


def main(argv: list[str] | None = None) -> int:
    """Run the campaign; exit 1 if anything was found."""
    front = argparse.ArgumentParser(prog='python -m tests.fuzz')
    front.add_argument('--seeds', default='0:500', help='a seed, or a range start:stop')
    front.add_argument('--jobs', type=int, default=os.cpu_count() or 1)
    front.add_argument(
        '--hash-seeds', action='store_true', help='run twice under two hash seeds and compare the output'
    )
    front.add_argument('-v', '--verbose', action='store_true', help='print every finding in full, and the mutant')
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
    return int(bool(groups))
