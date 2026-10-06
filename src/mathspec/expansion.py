# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""Macro calls, expanded into the syntax tree before resolution reads it.

A named expression is resolution's: it resolves the entry once and puts that
node where the name stood.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from mathspec._expression_parser import (
    ArithmeticNode,
    ComparisonNode,
    FunctionCallNode,
    NameListNode,
    NameNode,
    ParsedNode,
    parse_expression,
    with_children,
)
from mathspec.errors import SchemaError

if TYPE_CHECKING:
    from mathspec.resolution import Namespace
    from mathspec.spec import MacroBlock


def parse_and_expand(text: str, ns: Namespace, context: str) -> ParsedNode:
    """Parse *text* and expand every macro call in it.

    Args:
        text: The expression as the file wrote it.
        ns: Where the macros are declared.
        context: What an error names.
    """
    return expand(parse_expression(text), ns, context)


@overload
def expand(node: ArithmeticNode, ns: Namespace, context: str) -> ArithmeticNode: ...
@overload
def expand(node: ComparisonNode, ns: Namespace, context: str) -> ComparisonNode: ...


def expand(node: ParsedNode, ns: Namespace, context: str) -> ParsedNode:
    """Expand every macro call under *node*; a comparison stays a comparison and arithmetic stays arithmetic.

    Args:
        node: The parsed expression.
        ns: Where the macros are declared.
        context: What an error names.
    """
    if isinstance(node, ComparisonNode):
        return ComparisonNode(node.op, _expand(node.left, ns, context, ()), _expand(node.right, ns, context, ()))
    return _expand(node, ns, context, ())


def macro_signature(name: str, macro: MacroBlock) -> str:
    """Human-readable call signature, for error messages."""
    parts = [*macro.args, *(f'{k}=...' for k in macro.kwargs)]
    return f'{name}({", ".join(parts)})'


def parse_template(name: str, macro: MacroBlock, context: str) -> ArithmeticNode:
    """Parse a macro template, rejecting comparisons."""
    body = parse_expression(macro.template)
    if isinstance(body, ComparisonNode):
        msg = (
            f"{context}: macro '{name}' template {macro.template!r} holds a comparison. "
            f'Move the comparison into the constraint that calls the macro.'
        )
        raise SchemaError(msg)
    return body


def _expand(node: ArithmeticNode, ns: Namespace, context: str, stack: tuple[str, ...]) -> ArithmeticNode:
    """*node* with every macro call under it substituted; *stack* is the macros this walk is inside.

    A name a template reads is checked against the entries being resolved
    here, where the macros it came through are known, so a cycle closed
    through a macro is reported with the macros in its chain.
    """
    if isinstance(node, NameNode) and stack and (refusal := ns.cycle(node.name, context, stack)) is not None:
        raise SchemaError(refusal)
    if isinstance(node, FunctionCallNode) and node.name in ns.schema.macros:
        if node.name in stack:
            msg = (
                f"{context}: macro '{node.name}' calls itself through {' -> '.join([*stack, node.name])}. "
                f'Remove one of the calls in that chain.'
            )
            raise SchemaError(msg)
        return _expand_macro(node, ns, context, stack)
    return with_children(node, lambda child: _expand(child, ns, context, stack))


def _expand_macro(call: FunctionCallNode, ns: Namespace, context: str, stack: tuple[str, ...]) -> ArithmeticNode:
    """Call-by-value: arguments are expanded before substitution, and the substituted body is expanded again."""
    macro = ns.schema.macros[call.name]
    signature = macro_signature(call.name, macro)
    if len(call.args) != len(macro.args):
        msg = (
            f"{context}: macro '{call.name}' expects {len(macro.args)} "
            f'positional argument(s), and the call passes {len(call.args)}. Call it as {signature}.'
        )
        raise SchemaError(msg)
    if set(call.kwargs) != set(macro.kwargs):
        msg = (
            f"{context}: macro '{call.name}' expects the keyword argument(s) "
            f'{sorted(macro.kwargs)}, and the call passes {sorted(call.kwargs)}. Call it as {signature}.'
        )
        raise SchemaError(msg)

    bindings = {
        **{formal: _expand(arg, ns, context, stack) for formal, arg in zip(macro.args, call.args, strict=True)},
        **{formal: _expand(call.kwargs[formal], ns, context, stack) for formal in macro.kwargs},
    }
    body = parse_template(call.name, macro, context)
    substituted = _substitute(body, bindings, f"{context}: macro '{call.name}'")
    return _expand(substituted, ns, context, (*stack, call.name))


def _substitute(node: ArithmeticNode, bindings: dict[str, ArithmeticNode], caller: str) -> ArithmeticNode:
    """Replace formal-name NameNodes in *node* with their bound subtrees, and formals in a list with the names bound to them."""
    if isinstance(node, NameNode) and node.name in bindings:
        return bindings[node.name]
    if isinstance(node, NameListNode):
        return NameListNode(tuple(bound for name in node.names for bound in _names(name, node, bindings, caller)))
    return with_children(node, lambda child: _substitute(child, bindings, caller))


def _names(name: str, listed: NameListNode, bindings: dict[str, ArithmeticNode], caller: str) -> tuple[str, ...]:
    """What *name* in the list *listed* stands for: a list holds names, so a formal binds a name or a list spliced in."""
    if name not in bindings:
        return (name,)
    bound = bindings[name]
    if isinstance(bound, NameNode):
        return (bound.name,)
    if isinstance(bound, NameListNode):
        return bound.names
    msg = (
        f"{caller} writes its formal '{name}' in the list {listed}, and the call binds it to {bound}. "
        f'Bind a name, or a list of names.'
    )
    raise SchemaError(msg)
