"""Typed AST helpers shared by architecture-heavy tests."""

from __future__ import annotations

import ast


def module_body(tree: ast.AST) -> list[ast.stmt]:
    """Return the top-level statements for an exec-mode AST."""
    if not isinstance(tree, ast.Module):
        raise AssertionError(f"Expected ast.Module, got {type(tree).__name__}")
    return tree.body
