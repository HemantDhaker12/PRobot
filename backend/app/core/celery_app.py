from celery import Celery
from app.core.config import settings

# Initialize Celery app instance
celery_app = Celery(
    "probot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery Configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Configure task routes or defaults if needed
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Auto-discover task files
    imports=["app.workers.tasks"],
)
