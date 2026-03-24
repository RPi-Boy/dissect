"""
main.py — Dissect Backend: FastAPI Application Entry Point.

Provides API endpoints for registering git repositories and triggering
AI-powered security analysis. Uses FastAPI BackgroundTasks for async
processing so the client receives an immediate 200 OK.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field

from services.git_service import clone_and_process
from services.analysis_service import analyze_repository
from webhook import router as webhook_router
from repo_processor import get_report, get_all_reports

# ---------------------------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------------------------

# Load environment variables from .env file.
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Dissect",
    description=(
        "AI-powered application security analysis engine. "
        "Register a git repository and receive a comprehensive "
        "vulnerability report with attack chain mapping."
    ),
    version="0.1.0",
)

# CORS — allow all origins during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the webhook router.
app.include_router(webhook_router)

# ---------------------------------------------------------------------------
# In-Memory Job Store
# ---------------------------------------------------------------------------


class JobStatus(str, Enum):
    """Possible states for an analysis job."""

    QUEUED = "queued"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRecord(BaseModel):
    """Internal record for tracking the state of an analysis job."""

    job_id: str
    repo_url: str
    status: JobStatus = JobStatus.QUEUED
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


# Simple in-memory store. Replace with a database for production.
_jobs: dict[str, JobRecord] = {}

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""

    repo_url: HttpUrl = Field(
        ...,
        description="HTTPS URL of the public git repository to analyze.",
        examples=["https://github.com/user/repo.git"],
    )


class AnalyzeResponse(BaseModel):
    """Immediate response returned when an analysis job is queued."""

    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Response for checking the status of an analysis job."""

    job_id: str
    repo_url: str
    status: JobStatus
    created_at: str
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Background Task: Repository Analysis Pipeline
# ---------------------------------------------------------------------------


async def process_repo_analysis(job_id: str, repo_url: str) -> None:
    """Background task that clones, analyzes, and stores the result.

    This function is passed to FastAPI's BackgroundTasks so the client
    receives an immediate 200 OK while processing happens asynchronously.

    Args:
        job_id: Unique identifier for this analysis job.
        repo_url: HTTPS URL of the git repository to analyze.
    """
    job = _jobs[job_id]

    try:
        # Phase 1: Clone the repository.
        job.status = JobStatus.CLONING
        logger.info("[Job %s] Cloning repository: %s", job_id, repo_url)

        # clone_and_process is synchronous (GitPython), run in executor.
        # The callback receives the repo path, performs analysis, and
        # the repo is wiped in the finally block of clone_and_process.
        async def _analyze_callback(repo_path: Path) -> dict[str, Any]:
            """Async analysis callback executed inside clone_and_process."""
            job.status = JobStatus.ANALYZING
            logger.info("[Job %s] Analyzing codebase...", job_id)
            return await analyze_repository(repo_path)

        # Because clone_and_process is synchronous but our callback is async,
        # we need to bridge the two worlds. We use a sync wrapper that runs
        # the async callback in the current event loop.
        loop = asyncio.get_event_loop()

        def _sync_callback(repo_path: Path) -> dict[str, Any]:
            """Sync wrapper to run the async analysis in the event loop."""
            job.status = JobStatus.ANALYZING
            logger.info("[Job %s] Analyzing codebase...", job_id)
            future = asyncio.run_coroutine_threadsafe(
                analyze_repository(repo_path), loop
            )
            return future.result(timeout=120)

        result = await loop.run_in_executor(
            None, lambda: clone_and_process(repo_url, _sync_callback)
        )

        # Phase 2: Store the result.
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc).isoformat()
        job.result = result
        logger.info("[Job %s] Analysis complete.", job_id)

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now(timezone.utc).isoformat()
        # Use repr() to ensure the error is never an empty string.
        error_msg = str(exc) or repr(exc)
        job.error = f"[{type(exc).__name__}] {error_msg}"
        logger.error("[Job %s] Analysis failed: %s", job_id, repr(exc), exc_info=True)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Dissect",
        "version": "0.1.0",
    }


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=202,
    tags=["Analysis"],
    summary="Register a repository for security analysis",
)
async def analyze_repo(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Register a git repository and queue it for AI security analysis.

    Returns immediately with a job ID. Use GET /jobs/{job_id} to poll
    for results.

    Args:
        request: Contains the repo_url to analyze.
        background_tasks: FastAPI background task manager.

    Returns:
        AnalyzeResponse with the job_id and current status.
    """
    job_id = uuid.uuid4().hex[:12]
    repo_url_str = str(request.repo_url)

    # Create the job record.
    job = JobRecord(job_id=job_id, repo_url=repo_url_str)
    _jobs[job_id] = job

    logger.info("[Job %s] Queued analysis for: %s", job_id, repo_url_str)

    # Schedule the background task.
    background_tasks.add_task(process_repo_analysis, job_id, repo_url_str)

    return AnalyzeResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message=(
            f"Analysis queued for {repo_url_str}. "
            f"Poll GET /jobs/{job_id} for results."
        ),
    )


@app.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["Jobs"],
    summary="Get the status of an analysis job",
)
async def get_job_status(job_id: str):
    """Retrieve the current status and result of an analysis job.

    Args:
        job_id: The unique job identifier returned by POST /analyze.

    Returns:
        JobStatusResponse with status, result, or error.

    Raises:
        HTTPException: 404 if the job_id is not found.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return JobStatusResponse(
        job_id=job.job_id,
        repo_url=job.repo_url,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error,
    )


@app.get(
    "/jobs",
    response_model=list[JobStatusResponse],
    tags=["Jobs"],
    summary="List all analysis jobs",
)
async def list_jobs():
    """List all analysis jobs and their current statuses.

    Returns:
        A list of all JobStatusResponse records.
    """
    return [
        JobStatusResponse(
            job_id=j.job_id,
            repo_url=j.repo_url,
            status=j.status,
            created_at=j.created_at,
            completed_at=j.completed_at,
            result=j.result,
            error=j.error,
        )
        for j in _jobs.values()
    ]


# ---------------------------------------------------------------------------
# Report Endpoints (Webhook-generated analysis results)
# ---------------------------------------------------------------------------


@app.get(
    "/reports",
    tags=["Reports"],
    summary="List all webhook-generated analysis reports",
)
async def list_reports():
    """List all stored analysis reports from webhook pushes.

    Returns:
        A list of report summaries.
    """
    reports = get_all_reports()
    return [
        {
            "repo": r.repo_full_name,
            "risk_score": r.report.get("repository_overview", {}).get(
                "overall_risk_score", None
            ),
            "last_commit": r.last_commit_sha[:8] if r.last_commit_sha else None,
            "analysis_count": r.analysis_count,
            "updated_at": r.updated_at,
        }
        for r in reports
    ]


@app.get(
    "/reports/{owner}/{repo}",
    tags=["Reports"],
    summary="Get the full analysis report for a repository",
)
async def get_report_by_name(owner: str, repo: str):
    """Retrieve the full analysis report for a repository.

    Args:
        owner: The GitHub repository owner.
        repo: The GitHub repository name.

    Returns:
        The full report record.

    Raises:
        HTTPException: 404 if no report exists.
    """
    full_name = f"{owner}/{repo}"
    record = get_report(full_name)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for '{full_name}'.",
        )
    return {
        "repo": record.repo_full_name,
        "repo_url": record.repo_url,
        "last_commit": record.last_commit_sha,
        "analysis_count": record.analysis_count,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "report": record.report,
    }
