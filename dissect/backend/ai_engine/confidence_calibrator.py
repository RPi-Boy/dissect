def calibrate_confidence(confidence: float, valid_reasoning: bool) -> float:
    """
    Adjust LLM confidence based on reasoning validity.
    """

    if not valid_reasoning:
        confidence *= 0.6
    else:
        confidence *= 1.1

    # Clamp between 0 and 1
    return max(0.0, min(1.0, confidence))