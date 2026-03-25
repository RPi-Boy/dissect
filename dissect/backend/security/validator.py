from backend.config import settings

def validate_repo(repo_url: str):
    """
    Ensures repo is from allowed sources
    """

    if not any(domain in repo_url for domain in settings.ALLOWED_DOMAINS):
        raise Exception("Repository source not allowed")

    if not repo_url.startswith("https://"):
        raise Exception("Only HTTPS repos are allowed")

    return True