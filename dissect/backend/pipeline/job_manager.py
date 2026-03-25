import uuid
from datetime import datetime

# In-memory store (replace with Redis later if needed)
JOBS = {}

def create_job(repo_url: str):
    job_id = str(uuid.uuid4())

    JOBS[job_id] = {
        "job_id": job_id,
        "repo_url": repo_url,
        "status": "created",
        "created_at": str(datetime.utcnow()),
        "progress": 0,
        "result": None
    }

    return job_id


def update_job(job_id: str, data: dict):
    if job_id in JOBS:
        JOBS[job_id].update(data)


def get_job(job_id: str):
    return JOBS.get(job_id, {"error": "Job not found"})