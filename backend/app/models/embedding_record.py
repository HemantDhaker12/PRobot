from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseUUIDModel


class EmbeddingRecord(BaseUUIDModel):
    __tablename__ = "embedding_records"

    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)

    # entity_type describes what kind of content: "issue", "documentation", "resolved_issue"
    entity_type = Column(String(50), nullable=False, index=True)

    # entity_id contains unique identifier: e.g. issue_id or file path
    entity_id = Column(String(255), nullable=False, index=True)

    # chunk_index tracks parts of document (for RAG chunking, starts at 0)
    chunk_index = Column(Integer, nullable=False, default=0)

    # text_content is the original chunk text embedded
    text_content = Column(Text, nullable=False)

    # vector_id references unique id of vector in ChromaDB collection
    vector_id = Column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    repository = relationship("Repository", back_populates="embedding_records")
