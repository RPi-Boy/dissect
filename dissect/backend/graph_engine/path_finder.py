def find_paths(edges):
    """
    Finds simple paths in graph (DFS)
    """

    graph = {}

    for src, dst in edges:
        if src not in graph:
            graph[src] = []
        graph[src].append(dst)

    paths = []

    def dfs(node, path):
        path.append(node)

        if node not in graph:
            paths.append(list(path))
        else:
            for neighbor in graph[node]:
                dfs(neighbor, path)

        path.pop()

    for start in graph:
        dfs(start, [])

    return paths