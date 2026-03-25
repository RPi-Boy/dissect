from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    repo_url: str

class AnalyzeResponse(BaseModel):
    job_id: str
    status: str

class ReportResponse(BaseModel):
    vulnerability: str
    risk: str
    confidence: float
    fix: str