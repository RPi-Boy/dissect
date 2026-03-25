def apply_rules(features: dict, graph: dict):
    """
    Deterministic fallback scoring
    """

    score = 0

    # Rule 1: High confidence + deep flow
    if features["confidence"] > 0.7 and graph.get("depth", 0) > 5:
        score += 0.4

    # Rule 2: Complex reasoning (long explanation)
    if features["complexity"] > 0.6:
        score += 0.3

    # Rule 3: Multiple paths → higher risk
    if graph.get("paths", 1) > 2:
        score += 0.3

    return min(score, 1.0)