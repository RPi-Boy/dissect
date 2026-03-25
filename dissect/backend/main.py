from fastapi import FastAPI
from backend.api.routes import router as api_router
from backend.utils.logger import setup_logger

app = FastAPI(title="DISSECT")

# Setup logging
setup_logger()

# Include API routes
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "DISSECT Hybrid Intelligence Auditor Running"}