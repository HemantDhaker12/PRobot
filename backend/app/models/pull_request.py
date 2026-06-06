from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseUUIDModel


class PullRequest(BaseUUIDModel):
    __tablename__ = "pull_requests"

    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(20), nullable=False, default="open")  # open, closed, merged
    html_url = Column(String(500), nullable=False)
    is_draft = Column(Boolean, nullable=False, default=False)

    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    comments = relationship("IssueComment", back_populates="pull_request", cascade="all, delete-orphan")
