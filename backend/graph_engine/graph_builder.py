"""
graph_builder.py — Static Analysis Graph Builder.

Constructs a structural representation (DependencyGraph) of a cloned
repository using native `ast` parsing for Python and basic regex extraction
for JavaScript/TypeScript to fulfill the "Brain" expansion requirements.
"""

import ast
import logging
import os
import re
from pathlib import Path
from typing import Any

from .graph_utils import DependencyGraph, Edge, EdgeType, Node, NodeType

logger = logging.getLogger(__name__)

# Extensions supported by the graph builder.
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts"}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "vendor", "target", "coverage",
}


class PythonASTVisitor(ast.NodeVisitor):
    """Visitor to extract classes, functions, and calls from Python AST."""

    def __init__(self, filename: str, module_node: Node, graph: DependencyGraph):
        self.filename = filename
        self.module_node = module_node
        self.graph = graph
        # Track the current scope stack (Module -> Class -> Function)
        self.scope_stack: list[Node] = [module_node]
        self.calls_extracted: list[tuple[str, str]] = []  # (caller_id, callee_name)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_id = f"{self.module_node.id}.{node.name}"
        class_node = Node(
            id=class_id,
            name=node.name,
            type=NodeType.CLASS,
            file_path=self.filename,
            line_number=node.lineno,
        )
        self.graph.add_node(class_node)
        
        # Current scope contains this class
        self.graph.add_edge(Edge(
            source_id=self.scope_stack[-1].id,
            target_id=class_id,
            type=EdgeType.CONTAINS,
        ))

        self.scope_stack.append(class_node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        func_id = f"{self.scope_stack[-1].id}.{node.name}"
        func_node = Node(
            id=func_id,
            name=node.name,
            type=NodeType.FUNCTION,
            file_path=self.filename,
            line_number=node.lineno,
        )
        self.graph.add_node(func_node)

        # Current scope contains this function
        self.graph.add_edge(Edge(
            source_id=self.scope_stack[-1].id,
            target_id=func_id,
            type=EdgeType.CONTAINS,
        ))

        self.scope_stack.append(func_node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Call(self, node: ast.Call):
        caller_id = self.scope_stack[-1].id
        callee_name = None

        # Extract the name of the function being called.
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr

        if callee_name:
            self.calls_extracted.append((caller_id, callee_name))

        self.generic_visit(node)


def _parse_python_file(filepath: Path, repo_path: Path, graph: DependencyGraph) -> None:
    """Parse a single Python file using the native ast module."""
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=filepath.name)
    except (SyntaxError, Exception) as e:
        logger.debug("Failed to parse %s: %s", filepath, e)
        return

    rel_name = str(filepath.relative_to(repo_path))
    module_id = rel_name.replace("/", ".")
    module_node = Node(
        id=module_id,
        name=filepath.name,
        type=NodeType.MODULE,
        file_path=rel_name,
    )
    graph.add_node(module_node)

    visitor = PythonASTVisitor(rel_name, module_node, graph)
    visitor.visit(tree)

    # Post-process calls. We store "callee_name" rather than full ID. We'll
    # do a fuzzy Edge creation later for dashboard visual links.
    for caller_id, callee_name in visitor.calls_extracted:
        graph.add_edge(Edge(
            source_id=caller_id,
            target_id=f"UNKNOWN.{callee_name}", # Placeholder for rendering flows
            type=EdgeType.CALLS,
        ))


def _parse_js_ts_file(filepath: Path, repo_path: Path, graph: DependencyGraph) -> None:
    """Parse JS/TS files using a basic regex approach."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return

    rel_name = str(filepath.relative_to(repo_path))
    module_id = rel_name.replace("/", ".")
    module_node = Node(
        id=module_id,
        name=filepath.name,
        type=NodeType.MODULE,
        file_path=rel_name,
    )
    graph.add_node(module_node)

    # Basic regex for classes and functions
    class_matches = re.finditer(r"class\s+([a-zA-Z_$][0-9a-zA-Z_$]*)", content)
    for match in class_matches:
        cls_name = match.group(1)
        cls_id = f"{module_id}.{cls_name}"
        node = Node(id=cls_id, name=cls_name, type=NodeType.CLASS, file_path=rel_name)
        graph.add_node(node)
        graph.add_edge(Edge(source_id=module_id, target_id=cls_id, type=EdgeType.CONTAINS))

    func_matches = re.finditer(r"(?:function\s+|const\s+)([a-zA-Z_$][0-9a-zA-Z_$]*)\s*(?:=|=>|\()", content)
    for match in func_matches:
        func_name = match.group(1)
        func_id = f"{module_id}.{func_name}"
        node = Node(id=func_id, name=func_name, type=NodeType.FUNCTION, file_path=rel_name)
        graph.add_node(node)
        graph.add_edge(Edge(source_id=module_id, target_id=func_id, type=EdgeType.CONTAINS))


def build_repo_graph(repo_path: Path) -> dict[str, Any]:
    """Traverse a repository and build a static DependencyGraph.

    Args:
        repo_path: Path to the cloned repository.

    Returns:
        A serialized JSON-ready dict representing the graph.
    """
    logger.info("Building static dependency graph for %s", repo_path)
    graph = DependencyGraph()

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            filepath = Path(root) / filename
            suffix = filepath.suffix.lower()

            if suffix not in SUPPORTED_EXTENSIONS:
                continue

            # Limit size to 250KB to avoid excessive parsing times
            try:
                if filepath.stat().st_size > 250_000:
                    continue
            except OSError:
                continue

            if suffix == ".py":
                _parse_python_file(filepath, repo_path, graph)
            elif suffix in {".js", ".ts"}:
                _parse_js_ts_file(filepath, repo_path, graph)

    logger.info("Graph built: %d nodes, %d edges.", len(graph.nodes), len(graph.edges))
    return graph.to_dict()
