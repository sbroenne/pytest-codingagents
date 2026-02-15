"""Tree-sitter AST validation utilities for coding-agent-generated code.

Structural assertions that go beyond string matching — parse the actual
AST to verify return type annotations, docstrings, import usage, function
signatures, and call sites.

Requires the ``treesitter`` optional extra::

    pip install pytest-codingagents[treesitter]

Usage::

    from pytest_codingagents.validation.treesitter import (
        parse_python,
        find_functions,
        assert_no_syntax_errors,
        assert_function_has_return_type,
    )

    tree = parse_python(source_code)
    assert_no_syntax_errors(tree)
    assert_function_has_return_type(tree, "main")
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser
except ImportError as exc:
    raise ImportError(
        "tree-sitter dependencies not installed. "
        "Install with: pip install pytest-codingagents[treesitter]"
    ) from exc

if TYPE_CHECKING:
    from tree_sitter import Node, Tree


PY_LANGUAGE = Language(tspython.language())

_parser = Parser(PY_LANGUAGE)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_python(code: str | bytes) -> Tree:
    """Parse Python source into a tree-sitter Tree."""
    if isinstance(code, str):
        code = code.encode("utf-8")
    return _parser.parse(code)


def parse_file(path: str | Path) -> Tree:
    """Parse a Python file into a tree-sitter Tree."""
    return parse_python(Path(path).read_bytes())


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class FunctionInfo:
    """Extracted function metadata from an AST node.

    Attributes:
        name: Function name.
        node: The tree-sitter AST node.
        has_return_type: Whether a return type annotation is present.
        return_type: The return type annotation text, if present.
        has_docstring: Whether the function body starts with a docstring.
        parameters: List of parameter names.
    """

    name: str
    node: Node
    has_return_type: bool
    return_type: str | None
    has_docstring: bool
    parameters: list[str]


@dataclass
class ClassInfo:
    """Extracted class metadata from an AST node.

    Attributes:
        name: Class name.
        node: The tree-sitter AST node.
        has_docstring: Whether the class body starts with a docstring.
        bases: List of base class names.
        methods: List of method FunctionInfo objects.
    """

    name: str
    node: Node
    has_docstring: bool
    bases: list[str]
    methods: list[FunctionInfo]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _node_text(node: Node) -> str:
    """Get the UTF-8 text of a tree-sitter node."""
    return node.text.decode("utf-8") if node.text else ""


def _extract_function_info(node: Node) -> FunctionInfo:
    """Extract FunctionInfo from a function_definition node."""
    name_node = node.child_by_field_name("name")
    name = _node_text(name_node) if name_node else "<anonymous>"

    # Return type annotation
    return_type_node = node.child_by_field_name("return_type")
    has_return_type = return_type_node is not None
    return_type = _node_text(return_type_node) if return_type_node else None

    # Docstring: first expression_statement in body containing a string
    body = node.child_by_field_name("body")
    has_docstring = False
    if body and body.named_child_count > 0:
        first_stmt = body.named_children[0]
        if first_stmt.type == "expression_statement":
            expr = first_stmt.named_children[0] if first_stmt.named_child_count else None
            if expr and expr.type == "string":
                has_docstring = True

    # Parameters
    params_node = node.child_by_field_name("parameters")
    parameters: list[str] = []
    if params_node:
        for child in params_node.named_children:
            if child.type in ("identifier", "typed_parameter", "default_parameter"):
                param_name_node = (
                    child.child_by_field_name("name") if child.type != "identifier" else child
                )
                if param_name_node:
                    parameters.append(_node_text(param_name_node))

    return FunctionInfo(
        name=name,
        node=node,
        has_return_type=has_return_type,
        return_type=return_type,
        has_docstring=has_docstring,
        parameters=parameters,
    )


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------


def find_functions(tree: Tree) -> list[FunctionInfo]:
    """Find all function definitions (top-level and nested)."""
    results: list[FunctionInfo] = []

    def _visit(node: Node) -> None:
        if node.type == "function_definition":
            results.append(_extract_function_info(node))
        for child in node.children:
            _visit(child)

    _visit(tree.root_node)
    return results


def find_classes(tree: Tree) -> list[ClassInfo]:
    """Find all class definitions."""
    results: list[ClassInfo] = []

    def _visit(node: Node) -> None:
        if node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            name = _node_text(name_node) if name_node else "<anonymous>"

            # Bases
            bases: list[str] = []
            superclasses = node.child_by_field_name("superclasses")
            if superclasses:
                for child in superclasses.named_children:
                    bases.append(_node_text(child))

            # Docstring
            body = node.child_by_field_name("body")
            has_docstring = False
            if body and body.named_child_count > 0:
                first_stmt = body.named_children[0]
                if first_stmt.type == "expression_statement":
                    expr = first_stmt.named_children[0] if first_stmt.named_child_count else None
                    if expr and expr.type == "string":
                        has_docstring = True

            # Methods
            methods: list[FunctionInfo] = []
            if body:
                for child in body.named_children:
                    if child.type == "function_definition":
                        methods.append(_extract_function_info(child))

            results.append(
                ClassInfo(
                    name=name,
                    node=node,
                    has_docstring=has_docstring,
                    bases=bases,
                    methods=methods,
                )
            )

        for child in node.children:
            _visit(child)

    _visit(tree.root_node)
    return results


def find_imports(tree: Tree) -> list[str]:
    """Return all imported module names (``import X`` and ``from X import Y``)."""
    imports: list[str] = []

    def _visit(node: Node) -> None:
        if node.type == "import_statement":
            for child in node.named_children:
                if child.type == "dotted_name":
                    imports.append(_node_text(child))
                elif child.type == "aliased_import":
                    name = child.child_by_field_name("name")
                    if name:
                        imports.append(_node_text(name))
        elif node.type == "import_from_statement":
            module = node.child_by_field_name("module_name")
            if module:
                imports.append(_node_text(module))
        for child in node.children:
            _visit(child)

    _visit(tree.root_node)
    return imports


def find_calls(tree: Tree) -> list[str]:
    """Return all function/method call names (e.g. ``print``, ``os.path.join``)."""
    calls: list[str] = []

    def _visit(node: Node) -> None:
        if node.type == "call":
            func = node.child_by_field_name("function")
            if func:
                calls.append(_node_text(func))
        for child in node.children:
            _visit(child)

    _visit(tree.root_node)
    return calls


def find_decorators(tree: Tree) -> list[str]:
    """Return all decorator names found on functions and classes."""
    decorators: list[str] = []

    def _visit(node: Node) -> None:
        if node.type == "decorator":
            # The decorator node's first named child is the expression
            if node.named_child_count > 0:
                decorators.append(_node_text(node.named_children[0]))
        for child in node.children:
            _visit(child)

    _visit(tree.root_node)
    return decorators


def has_syntax_errors(tree: Tree) -> bool:
    """Check whether the parse tree contains any ERROR nodes."""

    def _visit(node: Node) -> bool:
        if node.type == "ERROR" or node.has_error:
            return True
        return any(_visit(child) for child in node.children)

    return _visit(tree.root_node)


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def assert_no_syntax_errors(tree: Tree) -> None:
    """Assert the code has no syntax errors."""
    assert not has_syntax_errors(tree), "Python source contains syntax errors"


def assert_function_exists(tree: Tree, func_name: str) -> FunctionInfo:
    """Assert a function exists and return its info."""
    funcs = find_functions(tree)
    matches = [f for f in funcs if f.name == func_name]
    assert matches, f"Function '{func_name}' not found in AST"
    return matches[0]


def assert_function_has_return_type(
    tree: Tree, func_name: str, expected: str | None = None
) -> None:
    """Assert a function has a return type annotation.

    Args:
        tree: Parsed tree-sitter Tree.
        func_name: Name of the function to check.
        expected: If provided, assert the return type matches this exact string.
    """
    func = assert_function_exists(tree, func_name)
    assert func.has_return_type, f"Function '{func_name}' has no return type annotation"
    if expected:
        assert func.return_type == expected, (
            f"Function '{func_name}' return type is {func.return_type!r}, expected {expected!r}"
        )


def assert_function_has_docstring(tree: Tree, func_name: str) -> None:
    """Assert a function has a docstring."""
    func = assert_function_exists(tree, func_name)
    assert func.has_docstring, f"Function '{func_name}' has no docstring"


def assert_class_exists(tree: Tree, class_name: str) -> ClassInfo:
    """Assert a class exists and return its info."""
    classes = find_classes(tree)
    matches = [c for c in classes if c.name == class_name]
    assert matches, f"Class '{class_name}' not found in AST"
    return matches[0]


def assert_class_has_base(tree: Tree, class_name: str, base_name: str) -> None:
    """Assert a class inherits from a specific base."""
    cls = assert_class_exists(tree, class_name)
    base_texts = " ".join(cls.bases)
    assert base_name in base_texts, (
        f"Class '{class_name}' does not inherit from '{base_name}'. Bases: {cls.bases}"
    )


def assert_no_calls_to(tree: Tree, *forbidden: str) -> None:
    """Assert none of the forbidden function names are called."""
    calls = find_calls(tree)
    for name in forbidden:
        hits = [c for c in calls if c == name or c.endswith(f".{name}")]
        assert not hits, f"Forbidden call to '{name}' found: {hits}"


def assert_imports(tree: Tree, *required: str) -> None:
    """Assert all required modules are imported."""
    imports = find_imports(tree)
    import_str = " ".join(imports)
    for mod in required:
        assert mod in import_str, f"Missing import: {mod}"


def assert_no_imports(tree: Tree, *forbidden: str) -> None:
    """Assert none of the forbidden modules are imported."""
    imports = find_imports(tree)
    import_str = " ".join(imports)
    for mod in forbidden:
        assert mod not in import_str, f"Forbidden import found: {mod}"
