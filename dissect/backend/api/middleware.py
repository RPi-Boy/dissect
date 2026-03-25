from fastapi import Request
import time
from backend.utils.logger import logger

async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} completed in {duration:.4f}s")

    return response