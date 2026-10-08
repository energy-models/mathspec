# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The GEMS comparison's tabs, from the cases under `tests/gems/`.

    pixi run python -m tools.gems_math           # rewrite every block
    pixi run python -m tools.gems_math --check   # fail if one has drifted

Each block is one row of tabs: the GEMS excerpt in `gems.yml`, the spec in
`mathspec.yaml` that says the same thing, and what the typesetter prints from
that spec. A case GEMS has no excerpt for leaves its excerpt file out.
"""

from __future__ import annotations

from mathspec import to_spec
from mathspec.typesetting import to_markdown
from tools._page import ROOT, splice, tab, without_header
from tools._page import main as page_main
from tools.expansion_math import HEADING

PAGE = ROOT / 'docs' / 'about' / 'gems.md'
CASES = ROOT / 'tests' / 'gems'
BLOCKS = ('axes', 'boundary', 'masks', 'ports')


def block(name: str) -> str:
    """The row of tabs for case *name*: the GEMS excerpt, the spec, and the math it prints."""
    case = CASES / name
    excerpt = case / 'gems.yml'
    gems = [tab('GEMS', f'```yaml\n{excerpt.read_text().strip()}\n```')] if excerpt.exists() else []
    math = to_markdown(to_spec(case / 'mathspec.yaml'), numbered=False, legend=False).strip()
    return '\n\n'.join(
        (
            *gems,
            tab('mathspec', f'```yaml\n{without_header(case / "mathspec.yaml")}\n```'),
            tab('Math', HEADING.sub(r'_\1_', math)),
        )
    )


def rendered_page(page: str) -> str:
    """Prettier wants a blank line on each side of the markers, so each block carries them."""
    for name in BLOCKS:
        page = splice(page, f'<!-- gems:{name}:begin -->', f'<!-- gems:{name}:end -->', f'\n{block(name)}\n')
    return page


def main(argv: list[str] | None = None) -> int:
    return page_main(argv, {PAGE: rendered_page}, 'gems_math')


if __name__ == '__main__':
    raise SystemExit(main())
