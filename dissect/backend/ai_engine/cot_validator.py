def validate_reasoning(reasoning: str) -> bool:
    """
    Basic Chain-of-Thought validator.
    Checks if reasoning includes logical flow indicators.
    """

    if not reasoning or len(reasoning.strip()) < 20:
        return False

    keywords = [
        "input", "flow", "data", "query",
        "execution", "unsanitized", "user",
        "database", "function"
    ]

    score = sum(1 for k in keywords if k.lower() in reasoning.lower())

    return score >= 2