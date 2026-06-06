"""initial migration

Revision ID: 0001
Revises: 
Create Date: 2026-06-05 22:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Repositories Table
    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_repositories_github_id"), "repositories", ["github_id"], unique=True)
    op.create_index(op.f("ix_repositories_full_name"), "repositories", ["full_name"], unique=True)
    op.create_index(op.f("ix_repositories_id"), "repositories", ["id"], unique=True)

    # 2. WebhookEvents Table
    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delivery_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_webhook_events_delivery_id"), "webhook_events", ["delivery_id"], unique=True)
    op.create_index(op.f("ix_webhook_events_id"), "webhook_events", ["id"], unique=True)

    # 3. Issues Table
    op.create_table(
        "issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("html_url", sa.String(length=500), nullable=False),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False),
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("labels", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["duplicate_of_id"], ["issues.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_issues_id"), "issues", ["id"], unique=True)
    op.create_index(op.f("ix_issues_number"), "issues", ["number"], unique=False)

    # 4. PullRequests Table
    op.create_table(
        "pull_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("html_url", sa.String(length=500), nullable=False),
        sa.Column("is_draft", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_pull_requests_id"), "pull_requests", ["id"], unique=True)
    op.create_index(op.f("ix_pull_requests_number"), "pull_requests", ["number"], unique=False)

    # 5. IssueComments Table
    op.create_table(
        "issue_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pull_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("github_comment_id", sa.BigInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_issue_comments_github_comment_id"), "issue_comments", ["github_comment_id"], unique=True)
    op.create_index(op.f("ix_issue_comments_id"), "issue_comments", ["id"], unique=True)

    # 6. EmbeddingRecords Table
    op.create_table(
        "embedding_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("vector_id", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_embedding_records_entity_id"), "embedding_records", ["entity_id"], unique=False)
    op.create_index(op.f("ix_embedding_records_entity_type"), "embedding_records", ["entity_type"], unique=False)
    op.create_index(op.f("ix_embedding_records_id"), "embedding_records", ["id"], unique=True)
    op.create_index(op.f("ix_embedding_records_vector_id"), "embedding_records", ["vector_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_embedding_records_vector_id"), table_name="embedding_records")
    op.drop_index(op.f("ix_embedding_records_id"), table_name="embedding_records")
    op.drop_index(op.f("ix_embedding_records_entity_type"), table_name="embedding_records")
    op.drop_index(op.f("ix_embedding_records_entity_id"), table_name="embedding_records")
    op.drop_table("embedding_records")

    op.drop_index(op.f("ix_issue_comments_id"), table_name="issue_comments")
    op.drop_index(op.f("ix_issue_comments_github_comment_id"), table_name="issue_comments")
    op.drop_table("issue_comments")

    op.drop_index(op.f("ix_pull_requests_number"), table_name="pull_requests")
    op.drop_index(op.f("ix_pull_requests_id"), table_name="pull_requests")
    op.drop_table("pull_requests")

    op.drop_index(op.f("ix_issues_number"), table_name="issues")
    op.drop_index(op.f("ix_issues_id"), table_name="issues")
    op.drop_table("issues")

    op.drop_index(op.f("ix_webhook_events_id"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_delivery_id"), table_name="webhook_events")
    op.drop_table("webhook_events")

    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_full_name"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_github_id"), table_name="repositories")
    op.drop_table("repositories")
