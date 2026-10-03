# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The one rule every benchmark here keeps: a round starts from empty caches.

The two grammars cache each text they parse, so a second load of the same file
in one process skips most of the work. A benchmark that repeats a call without
emptying them measures the cache: `examples/pypsa.yaml` loads in 0.14 s warm
and 0.62 s cold. A user who runs `python -m mathspec` meets the cold cost.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

#: Rounds per benchmark when `--codspeed` measures wall time.
ROUNDS = 5


def clear_caches() -> None:
    """Empty every `functools` cache in a loaded `mathspec` module, found by looking, so a new one is not missed."""
    for name, module in list(sys.modules.items()):
        if name.split('.')[0] == 'mathspec':
            for value in vars(module).values():
                if callable(getattr(value, 'cache_clear', None)):
                    value.cache_clear()


@pytest.fixture
def cold(benchmark: object) -> Callable[..., object]:
    """Measure a call, each round from empty caches; the caller builds its input outside the timing."""

    def measure(target: Callable[..., object], *args: object, **kwargs: object) -> object:
        def setup() -> tuple[tuple[object, ...], dict[str, object]]:
            clear_caches()
            return args, kwargs

        return benchmark.pedantic(target, setup=setup, rounds=ROUNDS)

    return measure
