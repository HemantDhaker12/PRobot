from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseUUIDModel


class IssueComment(BaseUUIDModel):
    __tablename__ = "issue_comments"

    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), nullable=True)
    pull_request_id = Column(UUID(as_uuid=True), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=True)

    github_comment_id = Column(BigInteger, unique=True, nullable=False, index=True)
    body = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)

    # Relationships
    repository = relationship("Repository", back_populates="comments")
    issue = relationship("Issue", back_populates="comments")
    pull_request = relationship("PullRequest", back_populates="comments")
