def enforce_policy(repo_url: str, code_size: int):
    """
    Basic policy enforcement
    """

    if code_size > 5_000_000:  # 5MB limit
        raise Exception("Repository too large for analysis")

    if "test" in repo_url.lower():
        return "LOW_PRIORITY"

    return "STANDARD"