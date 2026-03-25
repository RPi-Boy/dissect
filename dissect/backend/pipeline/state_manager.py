from backend.pipeline.job_manager import update_job
from backend.constants import *

def update_state(job_id: str, state: str, progress: int):
    update_job(job_id, {
        "status": state,
        "progress": progress
    })

def mark_completed(job_id: str, result: dict):
    update_job(job_id, {
        "status": STATE_COMPLETED,
        "progress": 100,
        "result": result
    })