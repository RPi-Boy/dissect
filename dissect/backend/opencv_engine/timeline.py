def build_timeline(graph: dict, risk: str):
    """
    Creates a step-by-step attack timeline
    """

    timeline = []

    edges = graph.get("edges", [])

    for i, (src, dst) in enumerate(edges):
        timeline.append({
            "step": i + 1,
            "from": src,
            "to": dst,
            "description": f"Data flows from {src} to {dst}"
        })

    timeline.append({
        "step": len(edges) + 1,
        "event": "EXPLOIT",
        "description": f"Attack triggered → Risk Level: {risk}"
    })

    return timeline