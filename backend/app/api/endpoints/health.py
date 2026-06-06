import logging
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
def health_check(response: Response, db: Session = Depends(get_db)):
    """
    Performs critical dependencies ping checks (PostgreSQL & Redis)
    to report overall health status.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logging.error(f"Health Check: Database connection failed: {str(e)}")
        db_status = "unhealthy"

    redis_status = "healthy"
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=3)
        r.ping()
    except Exception as e:
        logging.error(f"Health Check: Redis connection failed: {str(e)}")
        redis_status = "unhealthy"

    overall_status = "healthy"
    if db_status == "unhealthy" or redis_status == "unhealthy":
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status,
    }
