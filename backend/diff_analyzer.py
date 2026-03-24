"""
diff_analyzer.py — Git Diff Extraction & Filtering.

Extracts diffs between two commit SHAs in a cloned repository,
filters out binary and non-source files, and returns structured
diff data for incremental LLM analysis.
"""

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# File extensions considered as source code (mirrors analysis_service.py).
SOURCE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".sh", ".bash", ".zsh", ".sql", ".html",
    ".css", ".yml", ".yaml", ".json", ".toml", ".xml", ".proto",
    ".tf", ".hcl", ".dockerfile", ".env", ".cfg", ".ini", ".conf",
}

# Maximum diff size to send to the LLM (chars).
MAX_DIFF_CHARS = 100_000


@dataclass
class DiffResult:
    """Structured result from a git diff extraction.

    Attributes:
        before_sha: The commit SHA before the push.
        after_sha: The commit SHA after the push.
        changed_files: List of file paths that were modified.
        diff_text: The full unified diff output (filtered, capped).
        truncated: Whether the diff was truncated due to size limits.
    """

    before_sha: str
    after_sha: str
    changed_files: list[str] = field(default_factory=list)
    diff_text: str = ""
    truncated: bool = False


def _run_git(repo_path: Path, *args: str) -> str:
    """Run a git command in the given repository and return stdout.

    Args:
        repo_path: Path to the repository root.
        *args: Git subcommand and arguments.

    Returns:
        The stdout output as a string.

    Raises:
        subprocess.CalledProcessError: If the git command fails.
    """
    cmd = ["git", "-C", str(repo_path)] + list(args)
    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return result.stdout


def extract_changed_files(
    repo_path: Path, before_sha: str, after_sha: str
) -> list[str]:
    """List files changed between two commits, filtered to source files.

    Args:
        repo_path: Path to the cloned repository.
        before_sha: The "before" commit SHA.
        after_sha: The "after" commit SHA.

    Returns:
        List of relative file paths that changed and are source files.
    """
    try:
        raw = _run_git(
            repo_path, "diff", "--name-only", "--diff-filter=ACMR",
            before_sha, after_sha,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to list changed files: %s", exc.stderr)
        return []

    all_files = [f.strip() for f in raw.strip().splitlines() if f.strip()]

    # Filter to source files only.
    source_files = [
        f for f in all_files
        if Path(f).suffix.lower() in SOURCE_EXTENSIONS
    ]

    logger.info(
        "Changed files: %d total, %d source files (between %s..%s)",
        len(all_files), len(source_files), before_sha[:8], after_sha[:8],
    )
    return source_files


def extract_diff(
    repo_path: Path, before_sha: str, after_sha: str
) -> DiffResult:
    """Extract the full unified diff between two commits.

    Only includes diffs for source code files. The output is capped
    at MAX_DIFF_CHARS to avoid overwhelming the LLM.

    Args:
        repo_path: Path to the cloned repository.
        before_sha: The "before" commit SHA.
        after_sha: The "after" commit SHA.

    Returns:
        A DiffResult containing the filtered diff text and metadata.
    """
    changed_files = extract_changed_files(repo_path, before_sha, after_sha)

    if not changed_files:
        logger.info("No source file changes detected between %s..%s",
                     before_sha[:8], after_sha[:8])
        return DiffResult(
            before_sha=before_sha,
            after_sha=after_sha,
            changed_files=[],
            diff_text="",
            truncated=False,
        )

    # Get the unified diff for source files only.
    try:
        raw_diff = _run_git(
            repo_path, "diff", "--unified=5",
            before_sha, after_sha,
            "--", *changed_files,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to extract diff: %s", exc.stderr)
        return DiffResult(
            before_sha=before_sha,
            after_sha=after_sha,
            changed_files=changed_files,
            diff_text="",
            truncated=False,
        )

    # Truncate if the diff exceeds the limit.
    truncated = False
    diff_text = raw_diff
    if len(diff_text) > MAX_DIFF_CHARS:
        diff_text = diff_text[:MAX_DIFF_CHARS]
        diff_text += (
            f"\n\n--- TRUNCATED: Diff exceeded {MAX_DIFF_CHARS} "
            f"character limit. ---\n"
        )
        truncated = True
        logger.warning(
            "Diff truncated at %d chars for %s..%s",
            MAX_DIFF_CHARS, before_sha[:8], after_sha[:8],
        )

    logger.info(
        "Extracted diff: %d chars, %d files (truncated: %s)",
        len(diff_text), len(changed_files), truncated,
    )

    return DiffResult(
        before_sha=before_sha,
        after_sha=after_sha,
        changed_files=changed_files,
        diff_text=diff_text,
        truncated=truncated,
    )
