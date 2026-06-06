from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.repository import Repository
from app.models.issue import Issue
from app.models.pull_request import PullRequest
from app.models.webhook_event import WebhookEvent

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
def get_metrics(db: Session = Depends(get_db)):
    """
    Exposes key operational parameters and analytics of PRobot assistant.
    """
    # Active entities
    repo_count = db.query(Repository).count()
    issue_count = db.query(Issue).count()
    pr_count = db.query(PullRequest).count()

    # Webhook stats
    webhook_stats = (
        db.query(WebhookEvent.status, func.count(WebhookEvent.id))
        .group_by(WebhookEvent.status)
        .all()
    )
    
    events_summary = {status_name: count for status_name, count in webhook_stats}

    # Duplicate count
    duplicate_count = db.query(Issue).filter(Issue.is_duplicate == True).count()

    return {
        "repositories_count": repo_count,
        "issues": {
            "total_count": issue_count,
            "duplicate_count": duplicate_count,
        },
        "pull_requests_count": pr_count,
        "webhook_events": {
            "pending": events_summary.get("pending", 0),
            "processed": events_summary.get("processed", 0),
            "failed": events_summary.get("failed", 0),
        }
    }
