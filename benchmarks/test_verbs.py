# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Every public verb, on the specs a user writes.

Each verb that reads a spec runs on three real examples and on two sizes of
`synthetic.spec_text`, so a verb that grows faster than the file shows in the
ratio between the two. The verbs that take their own kind of input run on
one input each.
"""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

import pytest

from benchmarks.conftest import ROUNDS
from benchmarks.synthetic import spec_text
from mathspec import FORMATS, LanguageError, advice, merge, override, to_spec, typeset
from tests.fixtures import EXAMPLES

if TYPE_CHECKING:
    from collections.abc import Iterator

INPUTS = [
    pytest.param(EXAMPLES / 'dispatch.yaml', id='dispatch'),
    pytest.param(EXAMPLES / 'pypsa_linearized_uc.yaml', id='pypsa_linearized_uc'),
    pytest.param(EXAMPLES / 'pypsa.yaml', id='pypsa'),
    *(pytest.param(spec_text(n), id=f'synthetic-{n}') for n in (10, 100)),
]


@pytest.mark.parametrize('source', INPUTS)
def test_load(cold, source):
    """`to_spec`: read, validate and lower. Every other verb starts here."""
    cold(to_spec, source)


@pytest.mark.parametrize('source', INPUTS)
def test_advice(cold, source):
    """`advice`, which `python -m mathspec check` prints after the load."""
    cold(advice, to_spec(source))


@pytest.mark.parametrize('fmt', FORMATS)
@pytest.mark.parametrize('source', INPUTS)
def test_typeset(cold, source, fmt):
    cold(typeset, to_spec(source), fmt)


@pytest.mark.parametrize('source', INPUTS)
def test_canonical_yaml(cold, source):
    """`to_yaml(canonical=True)`, which `python -m mathspec canonical --check` compares against."""
    cold(to_spec(source).to_yaml, canonical=True)


@pytest.mark.parametrize('name', ['piecewise', 'sos'])
def test_expand(cold, name):
    """`Spec.expand`, the rows the `piecewise:` and `sos:` blocks state."""
    cold(to_spec(EXAMPLES / f'{name}.yaml').expand)


def test_merge(cold):
    """`merge` of the 24 topic fragments that `examples/pypsa.yaml` is cut into."""
    fragments = sorted((EXAMPLES / 'pypsa').glob('*.yaml'))
    assert len(fragments) == 24, 'the docstring counts the fragments'
    cold(merge, fragments)


def test_override(cold):
    """`override` of the library's commitment patch over the merged library."""
    library = EXAMPLES / 'library'
    base = merge([library / f'{name}.yaml' for name in ('surface', 'generator', 'load')])
    cold(override, base, [library / 'variants' / 'commitment.yaml'])


def refuse(text: str) -> str:
    """The message `to_spec` refuses *text* with."""
    try:
        to_spec(text)
    except LanguageError as error:
        return str(error)
    msg = 'the spec loaded'
    raise AssertionError(msg)


def test_refusal(cold):
    """`examples/pypsa.yaml` with an undeclared name in one constraint; the refusal lists every declared name."""
    typo = '  Bench_typo:\n    dims: [scenario, snapshot, generator]\n    expression: Generator_pp >= 0\n'
    text = (EXAMPLES / 'pypsa.yaml').read_text(encoding='utf-8')
    text = text.replace('\nconstraints:\n', f'\nconstraints:\n{typo}', 1)
    assert "'Generator_pp' not found" in cold(refuse, text), 'the load is refused for the typo, not for another reason'


@pytest.fixture
def mathspec_modules() -> Iterator[None]:
    """Put the `mathspec` modules this process loaded back after a test that imports new ones."""
    saved = {name: module for name, module in sys.modules.items() if name.split('.')[0] == 'mathspec'}
    yield
    for name in [name for name in sys.modules if name.split('.')[0] == 'mathspec']:
        del sys.modules[name]
    sys.modules.update(saved)


def forget_mathspec() -> tuple[tuple[str], dict[str, object]]:
    """Drop every `mathspec` module, so the next import runs each module body again."""
    for name in [name for name in sys.modules if name.split('.')[0] == 'mathspec']:
        del sys.modules[name]
    return ('mathspec',), {}


def test_import(benchmark, mathspec_modules):
    """`import mathspec`, with its dependencies already loaded: the part of the import this project controls."""
    benchmark.pedantic(importlib.import_module, setup=forget_mathspec, rounds=ROUNDS)
