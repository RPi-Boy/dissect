"""
git_service.py — Git Repository Cloning & Lifecycle Management.

Handles cloning a git repository to a temporary directory and ensures
strict cleanup via shutil.rmtree() in a try...finally block. The repo
is wiped the moment the processing callback completes or fails.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Callable, TypeVar

from git import Repo, GitCommandError

logger = logging.getLogger(__name__)

# Base directory for temporary repo storage.
REPO_BASE_DIR = Path("/tmp/dissect/repos")

T = TypeVar("T")


def clone_and_process(repo_url: str, callback: Callable[[Path], T]) -> T:
    """Clone a git repository, run a callback on it, then clean up.

    The repository is cloned into /tmp/dissect/repos/<uuid>/ and is
    unconditionally deleted after the callback returns — regardless
    of whether the callback succeeds or raises an exception.

    Args:
        repo_url: HTTPS URL of the git repository to clone.
        callback: A callable that receives the Path to the cloned repo
                  root and returns a result of type T.

    Returns:
        The return value of the callback.

    Raises:
        GitCommandError: If the clone operation fails.
        Any exception raised by the callback is re-raised after cleanup.
    """
    repo_id = uuid.uuid4().hex[:12]
    clone_path = REPO_BASE_DIR / repo_id

    # Ensure the base directory exists.
    REPO_BASE_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Cloning repository: %s -> %s", repo_url, clone_path)

    try:
        Repo.clone_from(
            repo_url,
            str(clone_path),
            depth=1,           # Shallow clone — we only need latest snapshot.
            single_branch=True,
        )
        logger.info("Clone complete: %s (%s)", repo_url, clone_path)

        # Execute the processing callback on the cloned repo.
        result = callback(clone_path)
        return result

    except GitCommandError as exc:
        logger.error("Git clone failed for %s: %s", repo_url, exc)
        raise

    finally:
        # CRITICAL: Unconditionally wipe the cloned repo from disk.
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)
            logger.info("Cleaned up repository at: %s", clone_path)
