from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.repository_repo import repository_repo
from app.schemas.repository import ReindexRequest  # we will create schemas next
from app.workers.tasks import async_reindex_repository_knowledge

router = APIRouter()


@router.post("/reindex-knowledge", status_code=status.HTTP_202_ACCEPTED)
def reindex_knowledge(request_in: ReindexRequest, db: Session = Depends(get_db)):
    """
    Triggers an asynchronous background Celery task to crawl the repository
    (README, CONTRIBUTING, docs/) and rebuild RAG semantic search indexes.
    """
    if request_in.repository_id:
        repository = repository_repo.get(db, request_in.repository_id)
    elif request_in.full_name:
        repository = repository_repo.get_by_full_name(db, request_in.full_name)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either repository_id or full_name must be provided in request payload.",
        )

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not registered in PRobot. Send a webhook or register it first.",
        )

    # Trigger async indexing
    async_reindex_repository_knowledge.delay(str(repository.id))

    return {
        "success": True,
        "message": f"Knowledge base re-indexing initiated for {repository.full_name}.",
        "repository_id": str(repository.id),
    }
