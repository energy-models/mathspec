# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The example gallery, as a Markdown extension the site enables.

`tools.gallery` holds the blocks and stays importable where python-markdown is
not installed, which is every test environment but the docs one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from markdown import Extension
from markdown.preprocessors import Preprocessor

from tools.gallery import expand

if TYPE_CHECKING:
    from markdown import Markdown

#: Between `pymdownx.snippets` (32) and python-markdown's whitespace pass
#: (30), so a block reaches `tools.mdx_github_math` and superfences whole.
PRIORITY = 31


class _Gallery(Preprocessor):
    """`expand` over the whole page, before the math in a block is rewritten for arithmatex."""

    def run(self, lines: list[str]) -> list[str]:
        return expand('\n'.join(lines)).split('\n')


class GalleryExtension(Extension):
    """The extension `mkdocs.yml` names as `tools.mdx_gallery`."""

    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802  # python-markdown's own spelling
        md.preprocessors.register(_Gallery(md), 'gallery', PRIORITY)


def makeExtension(**kwargs: Any) -> GalleryExtension:  # noqa: N802  # python-markdown's own spelling
    """What python-markdown calls when the extension is named as a string."""
    return GalleryExtension(**kwargs)
