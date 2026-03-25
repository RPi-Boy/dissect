# Dissect - Project Learnings

## Technical Gotchas & Bug Fixes

### Empty Exception Strings (FastAPI/Python)
- **Problem**: When capturing exceptions in a background task (e.g., `str(exc)`), some exception types or specific failure cases (like some LLM API timeouts or status errors) can return an empty string. This resulted in API responses showing `"error": ""` which was unhelpful for debugging.
- **Fix**: In `main.py`, the error capture was updated to use a fallback to `repr(exc)` and include the exception's class name:
  ```python
  error_msg = str(exc) or repr(exc)
  job.error = f"[{type(exc).__name__}] {error_msg}"
  ```
- **Context**: Discovered during testing with the `expressjs/express` repository where a high-latency timeout occurred.

### Git Sync Divergence
- **Insight**: When multiple collaborators (or an agent and a teammate) work on different parts of the same repository, `git pull` without a configured reconciliation strategy (`merge`, `rebase`, or `ff-only`) will fail. 
- **Fix**: Explicitly configured `git config pull.rebase false` to use the standard merge strategy, allowing the backend and frontend changes to co-exist.
