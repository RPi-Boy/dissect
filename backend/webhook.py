"""
webhook.py — GitHub Webhook Receiver.

Handles incoming GitHub push events. Verifies the HMAC-SHA256 signature,
instantly returns 200 OK, and dispatches processing to a background task
via FastAPI.BackgroundTasks.
"""

import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from repo_processor import process_push_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhook"])


def _verify_signature(payload_body: bytes, signature_header: str | None) -> None:
    """Verify the GitHub webhook HMAC-SHA256 signature.

    Args:
        payload_body: The raw request body bytes.
        signature_header: The X-Hub-Signature-256 header value.

    Raises:
        HTTPException: 401 if the signature is missing or invalid.
    """
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")

    if not secret:
        logger.warning(
            "GITHUB_WEBHOOK_SECRET is not set — skipping signature verification. "
            "This is INSECURE in production!"
        )
        return

    if not signature_header:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Hub-Signature-256 header.",
        )

    # GitHub sends: sha256=<hex_digest>
    if not signature_header.startswith("sha256="):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature format. Expected 'sha256=...'",
        )

    expected_sig = signature_header[7:]  # Strip "sha256=" prefix.
    computed_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_sig, expected_sig):
        logger.warning("Webhook signature verification FAILED.")
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature.",
        )

    logger.info("Webhook signature verified successfully.")


async def _handle_push_background(
    repo_full_name: str,
    clone_url: str,
    before_sha: str,
    after_sha: str,
) -> None:
    """Background task wrapper for push event processing.

    Catches all exceptions so background failures don't crash the server.

    Args:
        repo_full_name: GitHub "owner/repo" identifier.
        clone_url: HTTPS clone URL for the repository.
        before_sha: Commit SHA before the push.
        after_sha: Commit SHA after the push.
    """
    try:
        logger.info(
            "[Webhook] Starting background processing for %s (%s..%s)",
            repo_full_name, before_sha[:8], after_sha[:8],
        )
        result = await process_push_event(
            repo_full_name=repo_full_name,
            clone_url=clone_url,
            before_sha=before_sha,
            after_sha=after_sha,
        )
        vuln_count = len(result.get("vulnerabilities", []))
        risk_score = result.get("repository_overview", {}).get("overall_risk_score", "?")
        logger.info(
            "[Webhook] Analysis complete for %s — Risk: %s, Vulnerabilities: %d",
            repo_full_name, risk_score, vuln_count,
        )
    except Exception as exc:
        logger.error(
            "[Webhook] Background processing failed for %s: %s",
            repo_full_name, repr(exc), exc_info=True,
        )


@router.post("/webhook", status_code=200)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    """Receive GitHub webhook events.

    Verifies the HMAC signature, then instantly returns 200 OK.
    Push events are dispatched to a background task for analysis.

    Only 'push' events are processed; all others are acknowledged
    but ignored.

    Args:
        request: The incoming HTTP request.
        background_tasks: FastAPI background task manager.
        x_hub_signature_256: GitHub's HMAC signature header.
        x_github_event: The type of GitHub event.

    Returns:
        A JSON acknowledgement message.
    """
    # Read raw body for signature verification.
    body = await request.body()

    # Verify webhook signature.
    _verify_signature(body, x_hub_signature_256)

    # Only process push events.
    if x_github_event != "push":
        logger.info("[Webhook] Ignoring non-push event: %s", x_github_event)
        return {"status": "ok", "message": f"Event '{x_github_event}' ignored."}

    # Parse the payload.
    payload: dict[str, Any] = await request.json()

    # Extract relevant fields.
    repo_data = payload.get("repository", {})
    repo_full_name = repo_data.get("full_name", "unknown/unknown")
    clone_url = repo_data.get("clone_url", "")
    before_sha = payload.get("before", "")
    after_sha = payload.get("after", "")
    pusher = payload.get("pusher", {}).get("name", "unknown")
    ref = payload.get("ref", "unknown")

    logger.info(
        "[Webhook] Push received: %s by %s on %s (%s..%s)",
        repo_full_name, pusher, ref, before_sha[:8], after_sha[:8],
    )

    # Validate required fields.
    if not clone_url or not after_sha:
        logger.warning("[Webhook] Missing clone_url or after SHA — ignoring.")
        return {"status": "ok", "message": "Missing required payload fields."}

    # Dispatch to background task — DO NOT BLOCK.
    background_tasks.add_task(
        _handle_push_background,
        repo_full_name=repo_full_name,
        clone_url=clone_url,
        before_sha=before_sha,
        after_sha=after_sha,
    )

    return {
        "status": "ok",
        "message": f"Push event received for {repo_full_name}. Analysis queued.",
        "repo": repo_full_name,
        "ref": ref,
    }
