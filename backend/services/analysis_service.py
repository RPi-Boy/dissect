"""
analysis_service.py — Codebase Concatenation & OpenRouter LLM Analysis.

This module handles two responsibilities:
1. Traversing a cloned repository and concatenating all relevant source
   files into a single string context for the LLM.
2. Calling the OpenRouter API with a primary/fallback model pipeline,
   strict timeouts, and retry logic on 429/5xx errors.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from openai import AsyncOpenAI, APITimeoutError, APIStatusError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Model fallback array (OpenRouter slugs).
PRIMARY_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
FALLBACK_MODEL = "minimax/minimax-m2.7"

# Hard timeout per API call in seconds.
LLM_TIMEOUT_SECONDS = 60

# File extensions considered as "source code" for analysis.
SOURCE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".sh", ".bash", ".zsh", ".sql", ".html",
    ".css", ".yml", ".yaml", ".json", ".toml", ".xml", ".proto",
    ".tf", ".hcl", ".dockerfile", ".env", ".cfg", ".ini", ".conf",
}

# Directories to always skip during traversal.
SKIP_DIRS: set[str] = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "vendor", "target",
    ".tox", ".mypy_cache", ".pytest_cache", "coverage",
    ".terraform", ".serverless",
}

# Maximum characters to send to the LLM (protect against huge repos).
MAX_CONTEXT_CHARS = 200_000

# The system prompt loaded from MODEL_PROMPT.md at module init.
_SYSTEM_PROMPT: str | None = None


def _load_system_prompt() -> str:
    """Load the system prompt from MODEL_PROMPT.md.

    Searches for the file relative to this module's parent directories.

    Returns:
        The contents of MODEL_PROMPT.md with the placeholder removed.

    Raises:
        FileNotFoundError: If MODEL_PROMPT.md cannot be located.
    """
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is not None:
        return _SYSTEM_PROMPT

    # Walk upward from this file to find MODEL_PROMPT.md.
    search_dir = Path(__file__).resolve().parent.parent.parent
    prompt_path = search_dir / "MODEL_PROMPT.md"

    if not prompt_path.exists():
        # Fallback: try the backend's parent directory.
        prompt_path = Path(__file__).resolve().parent.parent.parent / "MODEL_PROMPT.md"

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"MODEL_PROMPT.md not found. Searched: {search_dir}"
        )

    raw = prompt_path.read_text(encoding="utf-8")
    # Remove the placeholder marker — the actual code will be injected.
    _SYSTEM_PROMPT = raw.replace("[INSERT_CONCATENATED_CODEBASE_HERE]", "").strip()
    logger.info("Loaded system prompt from: %s (%d chars)", prompt_path, len(_SYSTEM_PROMPT))
    return _SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Codebase Concatenation
# ---------------------------------------------------------------------------

def concatenate_codebase(repo_path: Path) -> str:
    """Traverse a repository and concatenate all source files.

    Walks the directory tree, skips irrelevant directories and binary files,
    and returns a single string with each file delimited by its relative path.

    Args:
        repo_path: Absolute path to the root of the cloned repository.

    Returns:
        A concatenated string of all source files, capped at MAX_CONTEXT_CHARS.
    """
    parts: list[str] = []
    total_chars = 0

    for root, dirs, files in os.walk(repo_path):
        # Prune skipped directories in-place to avoid descending into them.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in sorted(files):
            filepath = Path(root) / filename
            suffix = filepath.suffix.lower()

            if suffix not in SOURCE_EXTENSIONS:
                continue

            # Skip files larger than 500 KB — likely generated or vendored.
            try:
                if filepath.stat().st_size > 500_000:
                    continue
            except OSError:
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue

            relative = filepath.relative_to(repo_path)
            block = f"\n--- FILE: {relative} ---\n{content}\n"

            if total_chars + len(block) > MAX_CONTEXT_CHARS:
                parts.append(
                    f"\n--- TRUNCATED: Context limit of {MAX_CONTEXT_CHARS} "
                    f"characters reached. ---\n"
                )
                logger.warning(
                    "Codebase concatenation truncated at %d chars for %s",
                    total_chars, repo_path,
                )
                break

            parts.append(block)
            total_chars += len(block)
        else:
            # Only break the outer loop if the inner loop broke (truncation).
            continue
        break

    concatenated = "".join(parts)
    logger.info(
        "Concatenated %d files (%d chars) from %s",
        len(parts), len(concatenated), repo_path,
    )
    return concatenated


# ---------------------------------------------------------------------------
# OpenRouter LLM Integration
# ---------------------------------------------------------------------------

def _get_openai_client() -> AsyncOpenAI:
    """Create an AsyncOpenAI client configured for OpenRouter.

    Returns:
        An AsyncOpenAI instance pointed at the OpenRouter API.

    Raises:
        ValueError: If OPENROUTER_API_KEY is not set.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Please configure it in your .env file."
        )

    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=httpx.Timeout(LLM_TIMEOUT_SECONDS, connect=10.0),
    )


async def call_llm_with_fallback(codebase_context: str) -> dict[str, Any]:
    """Call the OpenRouter LLM API with primary/fallback model pipeline.

    Attempts the primary model first. If it fails due to timeout, rate
    limiting (HTTP 429), or a server error (HTTP 5xx), the exact same
    payload is retried with the fallback model.

    Args:
        codebase_context: The concatenated source code to analyze.

    Returns:
        Parsed JSON dict matching the MODEL_PROMPT.md schema.

    Raises:
        Exception: If both primary and fallback models fail.
    """
    system_prompt = _load_system_prompt()
    client = _get_openai_client()

    models = [PRIMARY_MODEL, FALLBACK_MODEL]
    last_error: Exception | None = None

    for i, model in enumerate(models):
        model_label = "PRIMARY" if i == 0 else "FALLBACK"
        logger.info("[%s] Attempting LLM call with model: %s", model_label, model)

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a security analysis AI. You MUST respond "
                            "with ONLY valid JSON. No markdown, no explanation, "
                            "no code fences. Just the raw JSON object."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"{system_prompt}\n\n"
                            f"### SOURCE CODE TO ANALYZE:\n{codebase_context}"
                        ),
                    },
                ],
                temperature=0.1,
                max_tokens=16384,
            )

            raw_content = response.choices[0].message.content or ""

            # Strip potential markdown code fences from the response.
            cleaned = raw_content.strip()
            if cleaned.startswith("```"):
                # Remove opening fence (e.g., ```json)
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            result = json.loads(cleaned)
            logger.info("[%s] LLM analysis successful with model: %s", model_label, model)
            return result

        except APITimeoutError as exc:
            logger.warning(
                "[%s] Timeout after %ds with model %s: %s",
                model_label, LLM_TIMEOUT_SECONDS, model, exc,
            )
            last_error = exc

        except APIStatusError as exc:
            if exc.status_code == 429 or exc.status_code >= 500:
                logger.warning(
                    "[%s] HTTP %d from model %s: %s",
                    model_label, exc.status_code, model, exc.message,
                )
                last_error = exc
            else:
                # Non-retriable error (e.g., 401 Unauthorized) — fail fast.
                logger.error(
                    "[%s] Non-retriable HTTP %d from model %s: %s",
                    model_label, exc.status_code, model, exc.message,
                )
                raise

        except json.JSONDecodeError as exc:
            logger.error(
                "[%s] Failed to parse JSON from model %s response: %s",
                model_label, model, exc,
            )
            last_error = exc

    # Both models failed.
    raise RuntimeError(
        f"All LLM models failed. Last error: {last_error}"
    ) from last_error


async def analyze_repository(repo_path: Path) -> dict[str, Any]:
    """Orchestrate the full analysis pipeline for a cloned repository.

    1. Concatenates the codebase into a single string.
    2. Sends it to the LLM via OpenRouter with fallback logic.
    3. Returns the structured JSON analysis result.

    Args:
        repo_path: Path to the root of the cloned repository.

    Returns:
        The LLM's security analysis as a parsed JSON dict.
    """
    logger.info("Starting analysis for repository at: %s", repo_path)

    codebase_context = concatenate_codebase(repo_path)

    if not codebase_context.strip():
        logger.warning("No source files found in repository: %s", repo_path)
        return {
            "repository_overview": {
                "primary_language": "unknown",
                "overall_risk_score": 0,
                "executive_summary": "No analyzable source files were found in this repository.",
            },
            "attack_surfaces": [],
            "vulnerabilities": [],
            "attack_chains": [],
        }

    result = await call_llm_with_fallback(codebase_context)
    logger.info("Analysis complete for repository: %s", repo_path)
    return result


# ---------------------------------------------------------------------------
# Incremental Diff Analysis
# ---------------------------------------------------------------------------

DIFF_ANALYSIS_PROMPT = """You are an elite Application Security Architect. You have previously analyzed a repository and produced the threat model below.

### PREVIOUS THREAT MODEL:
{previous_report}

### NEW CODE CHANGES (git diff):
The following files were modified: {changed_files}

```diff
{diff_text}
```

### YOUR TASK:
Analyze ONLY the new code changes above. Determine if they introduce new vulnerabilities, fix existing ones, or create new attack surfaces. Then produce an UPDATED version of the full threat model JSON that merges your new findings with the previous report.

RULES:
1. If a previous vulnerability is FIXED by the diff, remove it from the vulnerabilities array.
2. If a NEW vulnerability is introduced, add it with a new sequential ID.
3. Update the overall_risk_score if the changes meaningfully affect it.
4. Update the executive_summary to reflect the latest state.
5. Output ONLY valid JSON matching the original schema. No markdown, no explanation.
"""


async def analyze_diff(
    previous_report: dict[str, Any],
    diff_text: str,
    changed_files: list[str],
) -> dict[str, Any]:
    """Perform incremental analysis using only the git diff.

    Sends the previous report and the new diff to the LLM, which
    merges new findings into an updated threat model.

    Args:
        previous_report: The last full analysis result (JSON dict).
        diff_text: The unified diff output between two commits.
        changed_files: List of file paths that changed.

    Returns:
        An updated threat model JSON dict.
    """
    logger.info("Starting diff analysis for %d changed files", len(changed_files))

    prompt = DIFF_ANALYSIS_PROMPT.format(
        previous_report=json.dumps(previous_report, indent=2),
        changed_files=", ".join(changed_files),
        diff_text=diff_text,
    )

    client = _get_openai_client()
    models = [PRIMARY_MODEL, FALLBACK_MODEL]
    last_error: Exception | None = None

    for i, model in enumerate(models):
        model_label = "PRIMARY" if i == 0 else "FALLBACK"
        logger.info("[DIFF-%s] Attempting diff analysis with: %s", model_label, model)

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a security analysis AI. You MUST respond "
                            "with ONLY valid JSON. No markdown, no explanation, "
                            "no code fences. Just the raw JSON object."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.1,
                max_tokens=16384,
            )

            raw_content = response.choices[0].message.content or ""
            cleaned = raw_content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            result = json.loads(cleaned)
            logger.info("[DIFF-%s] Diff analysis successful with: %s", model_label, model)
            return result

        except APITimeoutError as exc:
            logger.warning("[DIFF-%s] Timeout with %s: %s", model_label, model, exc)
            last_error = exc

        except APIStatusError as exc:
            if exc.status_code == 429 or exc.status_code >= 500:
                logger.warning("[DIFF-%s] HTTP %d from %s", model_label, exc.status_code, model)
                last_error = exc
            else:
                raise

        except json.JSONDecodeError as exc:
            logger.error("[DIFF-%s] JSON parse failed from %s: %s", model_label, model, exc)
            last_error = exc

    raise RuntimeError(
        f"All LLM models failed for diff analysis. Last error: {last_error}"
    ) from last_error


# ---------------------------------------------------------------------------
# Report Formatting
# ---------------------------------------------------------------------------

def format_report_as_markdown(report: dict[str, Any]) -> str:
    """Convert a JSON report dict into a formatted Markdown string.

    Args:
        report: The analysis JSON dict.

    Returns:
        A formatted Markdown string.
    """
    overview = report.get("repository_overview", {})
    lang = overview.get("primary_language", "Unknown")
    risk = overview.get("overall_risk_score", "0")
    summary = overview.get("executive_summary", "No summary available.")

    md = [
        f"# Security Analysis Report",
        f"\n## Repository Overview",
        f"- **Primary Language**: {lang}",
        f"- **Overall Risk Score**: {risk}/10",
        f"\n### Executive Summary",
        f"{summary}",
    ]

    # Attack Surfaces
    surfaces = report.get("attack_surfaces", [])
    if surfaces:
        md.append("\n## Attack Surfaces")
        for s in surfaces:
            md.append(f"### {s.get('surface_name', 'Unnamed Surface')}")
            md.append(f"**Files**: {', '.join(s.get('files_involved', []))}")
            md.append(f"\n{s.get('description', 'No description.')}")

    # Vulnerabilities
    vulns = report.get("vulnerabilities", [])
    if vulns:
        md.append("\n## Vulnerabilities")
        for v in vulns:
            md.append(f"### [{v.get('id', 'VULN')}] {v.get('title', 'Untitled Bug')}")
            md.append(f"- **Severity**: {v.get('severity', 'Unknown')}")
            md.append(f"- **Location**: `{v.get('file', 'Unknown')}` (Line: {v.get('line_number_estimate', 'N/A')})")
            md.append(f"\n#### Description\n{v.get('description', 'No description.')}")
            md.append(f"\n#### Remediation\n{v.get('remediation', 'No remediation.')}")

    # Attack Chains
    chains = report.get("attack_chains", [])
    if chains:
        md.append("\n## Attack Chains")
        for c in chains:
            md.append(f"### {c.get('chain_name', 'Unnamed Attack')}")
            md.append(f"**Impact**: {c.get('impact', 'Unknown')}")
            md.append("\n#### Steps:")
            for i, step in enumerate(c.get("steps", []), 1):
                md.append(f"{i}. {step}")

    return "\n".join(md)
