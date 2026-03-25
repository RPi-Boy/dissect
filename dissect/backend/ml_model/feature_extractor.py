def extract_features(llm_result: dict, graph: dict):
    """
    Extracts features for ML model
    """

    confidence = llm_result.get("confidence", 0.5)
    reasoning_len = len(llm_result.get("reasoning", ""))

    # Simple complexity proxy
    complexity = min(reasoning_len / 200, 1.0)

    depth = graph.get("depth", 1) / 10  # normalize

    return {
        "confidence": confidence,
        "complexity": complexity,
        "depth": depth
    }