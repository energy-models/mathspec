# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A spec of *n* component classes, for a cost that grows with the size of the file.

The real examples stop at the 4,431 lines of `examples/pypsa.yaml`, so they
cannot show whether a verb grows faster than the file. Each class here is one
PyPSA-like component: a dimension of its own mapped to a bus, a capacity, an
output bounded by it where the unit is active, a ramp row up and one down
through `shift`, and two terms added to the shared balance and cost. The two
ramp rows share their `where:` text, as the rows of one PyPSA component do, so
a load hits the parse cache as a real file does.
"""

from __future__ import annotations


def component(k: int) -> dict[str, str]:
    """The YAML lines class *k* puts under each section, by section."""
    u = f'unit{k}'
    return {
        'dimensions': f'  {u}: {{ dtype: str }}\n',
        'relations': f'  {u}_bus: {{ key: {u}, values: bus }}\n',
        'parameters': (
            f'  {u}_cap: {{ dims: [{u}] }}\n'
            f'  {u}_cost: {{ dims: [{u}] }}\n'
            f'  {u}_ramp: {{ dims: [{u}] }}\n'
            f'  {u}_active: {{ dims: [{u}], dtype: bool }}\n'
        ),
        'variables': (
            f'  {u}_p:\n'
            f'    dims: [snapshot, {u}]\n'
            f'    where: {u}_active AND {u}_cap > 0\n'
            f'    bounds: {{ lower: 0, upper: {u}_cap }}\n'
        ),
        'expressions': (
            f'  {u}_injection:\n'
            f'    expression: sum({u}_p, by={u}_bus, over={u}, into=bus)\n'
            f'    adds_to: injection\n'
            f'  {u}_cost_total:\n'
            f'    expression: sum({u}_p * {u}_cost)\n'
            f'    adds_to: total_cost\n'
        ),
        'constraints': (
            f'  {u}_ramp_up:\n'
            f'    dims: [snapshot, {u}]\n'
            f'    where: {u}_active\n'
            f'    expression: {u}_p - shift({u}_p, along=snapshot, offset=1) <= {u}_ramp * {u}_cap\n'
            f'  {u}_ramp_down:\n'
            f'    dims: [snapshot, {u}]\n'
            f'    where: {u}_active\n'
            f'    expression: shift({u}_p, along=snapshot, offset=1) - {u}_p <= {u}_ramp * {u}_cap\n'
        ),
    }


def spec_text(n: int) -> str:
    """The YAML text of a spec with *n* component classes, a balance and an objective."""
    parts = [component(k) for k in range(n)]
    sections = {name: ''.join(part[name] for part in parts) for name in parts[0]}
    return (
        f'description: {n} synthetic component classes\n'
        'dimensions:\n'
        '  snapshot: { dtype: int }\n'
        '  bus: { dtype: str }\n'
        f'{sections["dimensions"]}'
        f'relations:\n{sections["relations"]}'
        f'parameters:\n{sections["parameters"]}'
        f'variables:\n{sections["variables"]}'
        'given:\n'
        '  expressions:\n'
        '    injection: { dims: [snapshot, bus] }\n'
        '    total_cost: { dims: [] }\n'
        f'expressions:\n{sections["expressions"]}'
        'constraints:\n'
        '  balance:\n'
        '    dims: [snapshot, bus]\n'
        '    expression: injection == 0\n'
        f'{sections["constraints"]}'
        'objective:\n'
        '  sense: minimize\n'
        '  expression: total_cost\n'
    )
