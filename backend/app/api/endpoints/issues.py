from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.issue import Issue
from app.schemas.issue import IssueResponse  # we will create schemas next

router = APIRouter()


@router.get("", response_model=List[IssueResponse], status_code=status.HTTP_200_OK)
def list_issues(
    repository_id: Optional[UUID] = Query(None, description="Filter issues by repository UUID"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max items to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieves synced issues. Supports optional repository filtering and pagination.
    """
    query = db.query(Issue)
    if repository_id:
        query = query.filter(Issue.repository_id == repository_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{issue_id}", response_model=IssueResponse, status_code=status.HTTP_200_OK)
def get_issue(issue_id: UUID, db: Session = Depends(get_db)):
    """
    Fetch a single synced issue details by database UUID.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with ID {issue_id} not found.",
        )
    return issue
