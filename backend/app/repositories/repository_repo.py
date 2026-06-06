from typing import Optional
from sqlalchemy.orm import Session
from app.models.repository import Repository
from app.repositories.base import CRUDBase


class RepositoryRepository(CRUDBase[Repository]):
    def get_by_github_id(self, db: Session, github_id: int) -> Optional[Repository]:
        """
        Fetch a repository using the official GitHub unique ID.
        """
        return db.query(self.model).filter(self.model.github_id == github_id).first()

    def get_by_full_name(self, db: Session, full_name: str) -> Optional[Repository]:
        """
        Fetch a repository using the slug full name (e.g. "owner/repo").
        """
        return db.query(self.model).filter(self.model.full_name == full_name).first()


repository_repo = RepositoryRepository(Repository)
