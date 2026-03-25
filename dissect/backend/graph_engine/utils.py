def normalize_graph(graph: dict):
    """
    Ensures graph consistency
    """

    nodes = list(set(graph.get("nodes", [])))
    edges = list(set(graph.get("edges", [])))

    return {
        "nodes": nodes,
        "edges": edges,
        "depth": graph.get("depth", len(edges)),
        "paths": graph.get("paths", 1)
    }


def get_entry_points(graph: dict):
    """
    Find nodes with no incoming edges
    """

    incoming = set(dst for _, dst in graph["edges"])
    return [node for node in graph["nodes"] if node not in incoming]