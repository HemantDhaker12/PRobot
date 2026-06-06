from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseUUIDModel


class Issue(BaseUUIDModel):
    __tablename__ = "issues"

    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(20), nullable=False, default="open")  # open, closed
    html_url = Column(String(500), nullable=False)

    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)

    # list of active labels applied by PRobot or manual maintainers
    labels = Column(JSONB, nullable=False, default=list)

    # Relationships
    repository = relationship("Repository", back_populates="issues")
    comments = relationship("IssueComment", back_populates="issue", cascade="all, delete-orphan")

    # self-referencing relationship for duplicate tracking
    duplicate_of = relationship("Issue", remote_side="Issue.id", backref="duplicates")
