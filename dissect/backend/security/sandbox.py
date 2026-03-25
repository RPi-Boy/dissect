import os
import tempfile
import shutil

def create_sandbox():
    """
    Creates an isolated temp directory for safe repo operations
    """
    sandbox_path = tempfile.mkdtemp(prefix="dissect_")
    return sandbox_path


def cleanup_sandbox(path: str):
    """
    Deletes sandbox after execution
    """
    if os.path.exists(path):
        shutil.rmtree(path)