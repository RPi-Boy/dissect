import re
from backend.graph_engine.path_finder import find_paths

def build_graph(code: str):
    """
    Very simplified static analysis graph
    """

    nodes = set()
    edges = []

    lines = code.split("\n")

    for i, line in enumerate(lines):
        if "(" in line and ")" in line:
            func = line.strip()
            nodes.add(func)

            # connect to next line (simple flow)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                edges.append((func, next_line))

    paths = find_paths(edges)

    return {
        "nodes": list(nodes),
        "edges": edges,
        "depth": len(edges),
        "paths": len(paths)
    }