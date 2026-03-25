import os
import shutil
from backend.config import settings
from backend.security.validator import validate_repo

def clone_repo(repo_url: str):
    validate_repo(repo_url)

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(settings.REPO_DIR, repo_name)

    # Clean if already exists
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    os.makedirs(settings.REPO_DIR, exist_ok=True)

    clone_cmd = f"git clone {repo_url} {repo_path}"
    result = os.system(clone_cmd)

    if result != 0:
        raise Exception("Failed to clone repository")

    return repo_path