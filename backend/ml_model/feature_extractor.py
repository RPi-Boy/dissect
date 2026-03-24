"""
feature_extractor.py — Heuristic Metric Extraction.

Extracts static structural and keyword-based features from a repository
to feed into the ML risk scoring model. Designed to be blazingly fast
and provide an immediate heuristic before the LLM finishes.
"""

import math
import os
import re
from pathlib import Path

# Sensitive keywords that raise risk heuristics
SENSITIVE_KEYWORDS = {
    "password", "secret", "token", "api_key", "credentials",
    "eval(", "exec(", "os.system", "subprocess", "shell=True",
    "unsafe", "insecure", "todo_security", "hack", "FIXME: security"
}

# High-risk files to watch out for
RISKY_FILES = {
    ".env", ".npmrc", "id_rsa", "config.json", "credentials.json"
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "vendor", "target", "coverage",
}


def extract_features(repo_path: Path) -> dict[str, float]:
    """Extract quantitative security heuristics from the codebase.

    Args:
        repo_path: Directory of the cloned repository.

    Returns:
        Dictionary mapping feature names to normalized scores.
    """
    total_loc = 0
    num_files = 0
    sensitive_keyword_hits = 0
    risky_files_found = 0
    max_complexity = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            num_files += 1
            if filename in RISKY_FILES:
                risky_files_found += 1

            filepath = Path(root) / filename
            try:
                # Skip large files for speed
                if filepath.stat().st_size > 500_000:
                    continue
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            lines = content.splitlines()
            total_loc += len(lines)

            # Keyword scanning
            content_lower = content.lower()
            for kw in SENSITIVE_KEYWORDS:
                sensitive_keyword_hits += content_lower.count(kw)

            # Heuristic complexity (depth of indentation)
            file_max_indent = 0
            for line in lines:
                stripped = line.lstrip()
                if stripped:
                    indent = len(line) - len(stripped)
                    file_max_indent = max(file_max_indent, indent)
            
            # Rough proxy for cyclomatic complexity based on indent depth
            proxy_complexity = file_max_indent // 4
            max_complexity = max(max_complexity, proxy_complexity)

    # Normalize features into continuous floats or discrete flags
    return {
        "log_loc": math.log1p(total_loc),
        "file_count": float(num_files),
        "keyword_density": sensitive_keyword_hits / max(1, total_loc) * 1000,
        "risky_files": float(risky_files_found),
        "max_complexity": float(max_complexity)
    }
