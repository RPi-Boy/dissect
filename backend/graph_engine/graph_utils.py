"""
graph_utils.py — Data structures for the Dissect Graph Engine.

This module defines the basic Node and Edge primitives used to represent
the codebase's structural topology (e.g., function call graphs, class
hierarchies, and module imports).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"
    UNKNOWN = "unknown"


class EdgeType(str, Enum):
    CALLS = "calls"
    IMPORTS = "imports"
    EXTENDS = "extends"
    CONTAINS = "contains"


@dataclass
class Node:
    """Represents a structural entity in the codebase."""
    id: str  # Unique identifier (e.g., "module.class.function")
    name: str
    type: NodeType
    file_path: str
    line_number: int | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "properties": self.properties,
        }


@dataclass
class Edge:
    """Represents a relationship between two Nodes."""
    source_id: str
    target_id: str
    type: EdgeType
    weight: int = 1
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.type.value,
            "weight": self.weight,
            "properties": self.properties,
        }


@dataclass
class DependencyGraph:
    """A directed graph representing the codebase structure."""
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        if node.id not in self.nodes:
            self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a JSON-ready dictionary."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
        }
