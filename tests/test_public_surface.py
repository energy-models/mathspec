# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The export surface, pinned — because a consumer depends on it by name.

Four modules, one rule each: `mathspec` is what a consumer calls,
`mathspec.spec` what the file says, `mathspec.program` what it means, and
`mathspec.errors` what a consumer catches. An addition to any of them is a
decision, and the tables below are where it is recorded.
"""

from __future__ import annotations

import ast
import inspect
import types
from pathlib import Path

import pytest

import mathspec
from mathspec import errors, program, spec
from mathspec.spec import Spec

#: Every name `mathspec` promises. Grouped as a reader meets them, not
#: alphabetically: the alphabetical form is `__all__` itself, and repeating it
#: here would make the two one list checked against itself.
SURFACE = frozenset(
    {
        # the door to a file, and the three modules behind it
        'to_spec', 'spec', 'program', 'errors',
        # the verdicts a consumer asks for rather than re-deriving
        'advice',
        # typesetting, and the two inputs it takes
        'typeset', 'typeset_declaration', 'to_latex', 'to_typst', 'to_markdown', 'FormatName', 'SymbolTable',
        # the two file-level verbs: peers composed, and patches laid over a base
        'merge', 'override',
    }
)  # fmt: skip

#: What the top level holds besides functions: the three modules, and the two
#: things a consumer builds or names to pass to `typeset`.
NOT_CALLED = frozenset({'spec', 'program', 'errors', 'FormatName', 'SymbolTable'})

#: The names `mathspec.spec` exports without defining them.
SPEC_REEXPORTS = frozenset({'BUILTIN_NAMES'})

#: What `Spec` promises beyond the sections a file declares: the two ways back
#: out, the verb that writes a formulation out, and the program the file means.
#: A `model_`-prefixed name is pydantic's, not a contract this project keeps.
SPEC_SURFACE = frozenset({'to_dict', 'to_yaml', 'expand', 'program'})

#: The modules whose `__all__` a consumer imports from.
MODULES = [
    pytest.param(mathspec, id='mathspec'),
    pytest.param(spec, id='spec'),
    pytest.param(program, id='program'),
    pytest.param(errors, id='errors'),
]


def test_spec_promises_the_pinned_methods_and_nothing_else():
    """A method on `Spec` is as public as a name in `__all__`, so adding one is the same decision."""
    found = {name for name in vars(Spec) if not name.startswith(('_', 'model_')) and name not in Spec.model_fields}
    assert found == SPEC_SURFACE, (
        f'only on Spec: {sorted(found - SPEC_SURFACE)}; only in SPEC_SURFACE: {sorted(SPEC_SURFACE - found)}'
    )


def test_all_matches_the_pinned_surface():
    """Both directions, because either alone rots."""
    declared = set(mathspec.__all__)
    assert declared == SURFACE, (
        f'only in __all__: {sorted(declared - SURFACE)}; only in SURFACE: {sorted(SURFACE - declared)}'
    )


@pytest.mark.parametrize('module', MODULES)
def test_every_exported_name_is_bound(module):
    """`__all__` naming something the module does not bind is a broken import."""
    missing = sorted(n for n in module.__all__ if not hasattr(module, n))
    assert not missing, f'{module.__name__}.__all__ names unbound attributes: {missing}'


@pytest.mark.parametrize('module', MODULES)
def test_all_names_nothing_twice(module):
    names = list(module.__all__)
    assert len(names) == len(set(names)), f'duplicate name in {module.__name__}.__all__'


def _defined_by(module: object) -> set[str]:
    """Every public name *module* binds itself, the bare ``Literal`` aliases included.

    Read from the source rather than ``dir()``: an alias is a plain assignment
    with no ``__module__`` to tell it apart from an imported one, so a runtime
    walk cannot say which names the module owns and which it merely imported.
    """
    tree = ast.parse(Path(module.__file__).read_text())  # pyrefly: ignore[missing-attribute]
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return {n for n in names if not n.startswith('_')}


def test_the_program_module_exports_everything_it_defines():
    """`mathspec.__all__` exports the module, so this is the consumers' surface — both
    directions, so a public name added without a decision fails here."""
    declared = set(program.__all__)
    defined = _defined_by(program)
    assert declared == defined, (
        f'only in __all__: {sorted(declared - defined)}; defined but unexported: {sorted(defined - declared)}'
    )


def test_the_top_level_is_what_a_consumer_calls():
    """A type a consumer receives lives in `spec` or `program`, and an error in `errors`."""
    held = {n for n in mathspec.__all__ if n not in NOT_CALLED and not inspect.isfunction(getattr(mathspec, n))}
    assert not held, f'not a function, so not top level: {sorted(held)}'
    modules = {n for n in mathspec.__all__ if isinstance(getattr(mathspec, n), types.ModuleType)}
    assert modules == {'spec', 'program', 'errors'}, f'the top level re-exports {sorted(modules)}'


def test_the_spec_module_exports_every_class_it_defines():
    """`Spec` hands out its blocks, so each one is public: a block class added without a decision fails here."""
    declared = set(spec.__all__)
    classes = {n for n, obj in vars(spec).items() if inspect.isclass(obj) and obj.__module__ == spec.__name__}
    public = {n for n in classes if not n.startswith('_')}
    assert public <= declared, f'defined but unexported: {sorted(public - declared)}'
    stray = declared - _defined_by(spec) - SPEC_REEXPORTS
    assert not stray, f'exported but neither defined nor a pinned re-export: {sorted(stray)}'


def test_the_errors_module_exports_the_error_tree():
    """Every exception class is one a consumer catches, so none is left out."""
    raised = {n for n, obj in vars(errors).items() if inspect.isclass(obj) and issubclass(obj, Exception)}
    assert raised <= set(errors.__all__), f'unexported errors: {sorted(raised - set(errors.__all__))}'
    others = {n for n in errors.__all__ if not inspect.isclass(getattr(errors, n))}
    assert others == {'did_you_mean'}, f'errors exports {sorted(others)} besides the error tree'
