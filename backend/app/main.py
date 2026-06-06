from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers

# Import API endpoints directly
from app.api.endpoints import webhooks, health, metrics, issues, pull_requests, knowledge

# Initialize Logging
setup_logging()

# Initialize FastAPI Application
app = FastAPI(
    title="PRobot Backend Foundation",
    description="An AI-powered GitHub repository maintainer assistant automation engine.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register Custom Exception & Error Handlers
register_exception_handlers(app)

# Enable CORS for frontend UI (to be developed later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    start_timestamp = datetime.now(timezone.utc).isoformat()
    client_ip = request.client.host if request.client else "unknown"

    logging.info(f"Incoming request: {request.method} {request.url.path} (Client: {client_ip}, Start: {start_timestamp})")

    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        logging.info(f"Completed request: {request.method} {request.url.path} -> {response.status_code} in {duration_ms}ms")
        return response
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logging.error(f"Failed request: {request.method} {request.url.path} -> Error: {str(e)} in {duration_ms}ms")
        raise e

# Mount Routers
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
app.include_router(issues.router, prefix="/issues", tags=["Issues"])
app.include_router(pull_requests.router, prefix="/pull-requests", tags=["Pull Requests"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base"])


@app.get("/")
def read_root():
    return {
        "app": "PRobot Backend Foundation",
        "status": "running",
        "documentation": "/docs",
    }
