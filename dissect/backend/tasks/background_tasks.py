from backend.pipeline.orchestrator import run_pipeline

def run_analysis_async(repo_url: str, job_id: str):
    """
    Wrapper for async execution
    """
    run_pipeline(repo_url, job_id)