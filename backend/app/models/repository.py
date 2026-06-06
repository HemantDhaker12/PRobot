from sqlalchemy import BigInteger, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseUUIDModel


class Repository(BaseUUIDModel):
    __tablename__ = "repositories"

    github_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), unique=True, nullable=False, index=True)
    owner = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)

    # settings stores configurations: custom duplicate thresholds, labels list, triage checklists, etc.
    settings = Column(JSONB, nullable=False, default=dict)

    # Relationships
    issues = relationship("Issue", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")
    comments = relationship("IssueComment", back_populates="repository", cascade="all, delete-orphan")
    embedding_records = relationship("EmbeddingRecord", back_populates="repository", cascade="all, delete-orphan")
