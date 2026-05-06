"""Documentation coverage tests for the public MCP tool surface."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _nested_async_functions_in_setup_modules() -> set[str]:
    names: set[str] = set()
    for name in _nested_async_function_names_in_setup_modules():
        names.add(name)
    return names


def _nested_async_function_names_in_setup_modules() -> list[str]:
    names: list[str] = []
    for path in (ROOT / "src" / "tools").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("setup_"):
                for child in ast.walk(node):
                    if isinstance(child, ast.AsyncFunctionDef):
                        names.append(child.name)
    return names


def _decorated_mcp_tools_in_main() -> set[str]:
    tree = ast.parse((ROOT / "src" / "main.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "tool"
            ):
                names.add(node.name)
    return names


def test_tool_reference_documents_every_public_tool():
    documented = (ROOT / "docs" / "TOOL_REFERENCE.md").read_text(encoding="utf-8")
    tool_names = _nested_async_functions_in_setup_modules() | _decorated_mcp_tools_in_main()

    missing = sorted(name for name in tool_names if f"`{name}`" not in documented)

    assert missing == []


def test_public_tool_names_are_unique_before_fastmcp_registration():
    tool_names = _nested_async_function_names_in_setup_modules() + sorted(_decorated_mcp_tools_in_main())
    duplicates = sorted({name for name in tool_names if tool_names.count(name) > 1})

    assert duplicates == []


def test_all_declared_public_tools_are_registered_with_fastmcp():
    import main

    declared = _nested_async_functions_in_setup_modules() | _decorated_mcp_tools_in_main()
    registered = set(main.mcp._tool_manager._tools)

    assert sorted(declared - registered) == []
