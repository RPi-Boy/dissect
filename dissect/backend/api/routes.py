from fastapi import APIRouter, BackgroundTasks
from backend.api.schemas import AnalyzeRequest, AnalyzeResponse
from backend.pipeline.orchestrator import run_pipeline
from backend.pipeline.job_manager import create_job, get_job

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    job_id = create_job(request.repo_url)

    background_tasks.add_task(run_pipeline, request.repo_url, job_id)

    return {"job_id": job_id, "status": "processing"}

@router.get("/status/{job_id}")
def status(job_id: str):
    job = get_job(job_id)
    return job