"""
repo_processor.py — Push Event Processing & Report Management.

Orchestrates the full pipeline for GitHub push events:
1. Clone the repository (shallow, with enough history for diffs).
2. Determine if this is the first analysis or an incremental update.
3. Run full or diff-based analysis accordingly.
4. Store the report in-memory, keyed by repository full name.
"""

import asyncio
import logging
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from git import Repo, GitCommandError

from diff_analyzer import extract_diff
from services.analysis_service import analyze_repository, analyze_diff

logger = logging.getLogger(__name__)

# Base directory for temporary repo clones.
REPO_BASE_DIR = Path("/tmp/dissect/repos")


# ---------------------------------------------------------------------------
# Report Store (In-Memory)
# ---------------------------------------------------------------------------


@dataclass
class ReportRecord:
    """A stored analysis report for a repository.

    Attributes:
        repo_full_name: GitHub "owner/repo" identifier.
        repo_url: Clone URL of the repository.
        report: The latest JSON analysis result.
        last_commit_sha: The SHA of the latest analyzed commit.
        created_at: When the first report was generated.
        updated_at: When the report was last updated.
        analysis_count: How many analyses have been run.
    """

    repo_full_name: str
    repo_url: str
    report: dict[str, Any] = field(default_factory=dict)
    last_commit_sha: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = ""
    analysis_count: int = 0


# In-memory report store. Keyed by repo full name (e.g., "owner/repo").
_reports: dict[str, ReportRecord] = {}


def get_report(repo_full_name: str) -> ReportRecord | None:
    """Retrieve a stored report by repository full name.

    Args:
        repo_full_name: The GitHub "owner/repo" identifier.

    Returns:
        The ReportRecord if found, else None.
    """
    return _reports.get(repo_full_name)


def get_all_reports() -> list[ReportRecord]:
    """Return all stored reports.

    Returns:
        List of all ReportRecord objects.
    """
    return list(_reports.values())


# ---------------------------------------------------------------------------
# Push Event Processing
# ---------------------------------------------------------------------------


async def process_push_event(
    repo_full_name: str,
    clone_url: str,
    before_sha: str,
    after_sha: str,
) -> dict[str, Any]:
    """Process a GitHub push event: clone, analyze, store.

    Determines whether to run a full analysis (first time) or an
    incremental diff analysis (subsequent pushes). The repository is
    cloned into /tmp and wiped immediately after analysis completes.

    Args:
        repo_full_name: GitHub "owner/repo" identifier.
        clone_url: HTTPS clone URL for the repository.
        before_sha: The commit SHA before the push.
        after_sha: The commit SHA after the push.

    Returns:
        The analysis result as a JSON dict.
    """
    repo_id = uuid.uuid4().hex[:12]
    clone_path = REPO_BASE_DIR / repo_id
    REPO_BASE_DIR.mkdir(parents=True, exist_ok=True)

    existing_report = _reports.get(repo_full_name)
    is_initial = (
        existing_report is None
        or before_sha == "0" * 40  # GitHub sends all-zeroes for first push.
    )

    logger.info(
        "[%s] Processing push: %s..%s (mode: %s)",
        repo_full_name, before_sha[:8], after_sha[:8],
        "FULL" if is_initial else "DIFF",
    )

    loop = asyncio.get_event_loop()

    try:
        # Clone with enough depth for diff (not a full clone).
        await loop.run_in_executor(None, lambda: _clone_repo(
            clone_url, clone_path, shallow=is_initial,
        ))

        if is_initial:
            # Full analysis — same pipeline as POST /analyze.
            result = await analyze_repository(clone_path)
        else:
            # Incremental diff analysis.
            diff_result = extract_diff(clone_path, before_sha, after_sha)

            if not diff_result.diff_text.strip():
                logger.info(
                    "[%s] No source changes in push, skipping analysis.",
                    repo_full_name,
                )
                return existing_report.report

            result = await analyze_diff(
                previous_report=existing_report.report,
                diff_text=diff_result.diff_text,
                changed_files=diff_result.changed_files,
            )

        # Store/update the report.
        now = datetime.now(timezone.utc).isoformat()
        if existing_report:
            existing_report.report = result
            existing_report.last_commit_sha = after_sha
            existing_report.updated_at = now
            existing_report.analysis_count += 1
        else:
            _reports[repo_full_name] = ReportRecord(
                repo_full_name=repo_full_name,
                repo_url=clone_url,
                report=result,
                last_commit_sha=after_sha,
                updated_at=now,
                analysis_count=1,
            )

        logger.info("[%s] Analysis stored. Total analyses: %d",
                     repo_full_name,
                     _reports[repo_full_name].analysis_count)
        return result

    finally:
        # CRITICAL: Wipe the cloned repo immediately.
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)
            logger.info("[%s] Cleaned up clone at: %s",
                         repo_full_name, clone_path)


def _clone_repo(
    clone_url: str, clone_path: Path, shallow: bool = True
) -> None:
    """Clone a repository to disk.

    Args:
        clone_url: HTTPS URL to clone.
        clone_path: Local path to clone into.
        shallow: If True, clone with depth=1. If False, fetch
                 enough history for diffs (depth=50).

    Raises:
        GitCommandError: If the clone fails.
    """
    depth = 1 if shallow else 50
    logger.info("Cloning %s (depth=%d) -> %s", clone_url, depth, clone_path)
    Repo.clone_from(
        clone_url,
        str(clone_path),
        depth=depth,
        single_branch=True,
    )
