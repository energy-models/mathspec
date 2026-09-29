# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The render half of the LaTeX gate: every spec in the tree becomes a document of its own."""

from __future__ import annotations

from tools import render_tex


def test_every_spec_renders_to_a_document_of_its_own(tmp_path):
    """Two specs that share a file name wrote one document, and the second overwrote the first.

    The output was named after the file's stem alone, so
    `examples/library/generator.yaml` and `examples/pypsa/generator.yaml` both
    wrote `generator.tex`, and `compile-tex` compiled one of the two.
    """
    assert render_tex.main([str(tmp_path)]) == 0
    written = sorted(path.name for path in tmp_path.glob('*.tex'))
    assert len(written) == len(render_tex.models()), 'one document per spec, none overwritten by a namesake'
