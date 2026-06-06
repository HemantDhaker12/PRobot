from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from app.models.pull_request import PullRequest
from app.repositories.base import CRUDBase


class PullRequestRepository(CRUDBase[PullRequest]):
    def get_by_number(self, db: Session, repository_id: UUID, number: int) -> Optional[PullRequest]:
        """
        Fetch a pull request by repository and PR number.
        """
        return (
            db.query(self.model)
            .filter(self.model.repository_id == repository_id, self.model.number == number)
            .first()
        )


pull_request_repo = PullRequestRepository(PullRequest)
