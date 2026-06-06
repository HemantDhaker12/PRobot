from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.pull_request import PullRequest
from app.schemas.pull_request import PullRequestResponse  # we will create schemas next

router = APIRouter()


@router.get("", response_model=List[PullRequestResponse], status_code=status.HTTP_200_OK)
def list_pull_requests(
    repository_id: Optional[UUID] = Query(None, description="Filter PRs by repository UUID"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max items to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieves synced pull requests. Supports optional repository filtering and pagination.
    """
    query = db.query(PullRequest)
    if repository_id:
        query = query.filter(PullRequest.repository_id == repository_id)
    return query.offset(skip).limit(limit).all()
