# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The harness measures what it says it measures."""

from __future__ import annotations

import sys

from benchmarks.conftest import clear_caches
from mathspec import to_spec
from tests.fixtures import EXAMPLES


def test_a_round_starts_with_every_cache_empty():
    """Without the clear, a repeated load hits the parse caches, and the benchmark measures the cache."""
    to_spec(EXAMPLES / 'pypsa.yaml')
    clear_caches()
    caches = {
        f'{name}.{attr}': value.cache_info().currsize
        for name, module in sys.modules.items()
        if name.split('.')[0] == 'mathspec'
        for attr, value in vars(module).items()
        if callable(getattr(value, 'cache_info', None))
    }
    assert caches, 'the parse caches are found by looking, so finding none means the search broke'
    assert not any(caches.values()), f'caches left full: {caches}'
