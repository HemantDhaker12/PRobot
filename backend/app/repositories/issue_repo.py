from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from app.models.issue import Issue
from app.repositories.base import CRUDBase


class IssueRepository(CRUDBase[Issue]):
    def get_by_number(self, db: Session, repository_id: UUID, number: int) -> Optional[Issue]:
        """
        Fetch a single issue by repository and issue number.
        """
        return (
            db.query(self.model)
            .filter(self.model.repository_id == repository_id, self.model.number == number)
            .first()
        )

    def get_open_issues(self, db: Session, repository_id: UUID) -> List[Issue]:
        """
        Fetch all open issues for a given repository.
        """
        return (
            db.query(self.model)
            .filter(self.model.repository_id == repository_id, self.model.state == "open")
            .all()
        )


issue_repo = IssueRepository(Issue)
