import logging
from sqlalchemy.orm import Session
from app.models.issue import Issue
from app.repositories.issue_repo import issue_repo
from app.repositories.repository_repo import repository_repo
from app.repositories.base import CRUDBase
from app.models.embedding_record import EmbeddingRecord
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.github_service import github_service


class DuplicateDetector:
    """
    Analyzes issues for duplication. Generates embeddings, queries vector store,
    annotates issues, and closes duplicates based on repository threshold settings.
    """

    def process_issue(self, db: Session, issue: Issue) -> None:
        repository = repository_repo.get(db, issue.repository_id)
        if not repository:
            logging.error(f"Repository {issue.repository_id} not found for issue {issue.id}")
            return

        # Fetch configurations from repository settings
        settings = repository.settings or {}
        enabled = settings.get("duplicate_detection_enabled", True)
        if not enabled:
            logging.info(f"Duplicate detection disabled for repository {repository.full_name}")
            return

        threshold = settings.get("duplicate_similarity_threshold", 0.82)
        auto_close = settings.get("duplicate_auto_close", True)

        # Prepare text representation for embedding
        issue_text = f"Title: {issue.title}\n\nDescription: {issue.body or ''}"

        # Generate local embedding
        query_vector = embedding_service.get_embedding(issue_text)

        logging.info(f"Searching duplicate issues for {repository.full_name}#{issue.number}")
        matches = vector_store.query_similar(
            collection_name="issue_embeddings",
            query_embedding=query_vector,
            repository_id=str(repository.id),
            limit=5,
            similarity_threshold=threshold,
        )

        # Filter out self-matches
        valid_matches = [m for m in matches if m["metadata"].get("number") != issue.number]

        if valid_matches:
            best_match = valid_matches[0]
            matched_number = best_match["metadata"].get("number")
            matched_issue_id = best_match["metadata"].get("issue_id")
            similarity = best_match["similarity"]

            logging.info(
                f"Duplicate detected: {repository.full_name}#{issue.number} "
                f"is a duplicate of #{matched_number} (similarity: {similarity:.2f})"
            )

            # Update issue status in PostgreSQL
            issue.is_duplicate = True
            if matched_issue_id:
                # Find database ID of matched issue to associate
                matched_db_issue = db.query(Issue).filter(Issue.id == matched_issue_id).first()
                if matched_db_issue:
                    issue.duplicate_of_id = matched_db_issue.id
            db.commit()

            # Post reference comment on GitHub
            comment_body = (
                f"🤖 **PRobot Duplicate Detection**\n\n"
                f"Hi @{issue.html_url.split('/')[-3]}, this issue looks very similar to "
                f"#{matched_number} (semantic match: {similarity * 100:.1f}%).\n\n"
                f"To keep the conversation focused, we are marking this issue as a duplicate. "
                f"If you believe this is in error, please comment to reopen."
            )
            github_service.post_comment(repository.full_name, issue.number, comment_body)

            # Apply label on GitHub
            github_service.add_labels(repository.full_name, issue.number, ["duplicate"])

            # Optionally close issue on GitHub
            if auto_close:
                github_service.close_issue(repository.full_name, issue.number)
                issue.state = "closed"
                db.commit()
        else:
            logging.info(f"No duplicate detected for {repository.full_name}#{issue.number}. Indexing issue.")
            # If it's a unique issue, index it for future searches
            vector_id = f"issue_{str(issue.id)}"
            vector_store.upsert_embeddings(
                collection_name="issue_embeddings",
                ids=[vector_id],
                embeddings=[query_vector],
                metadatas=[{"repository_id": str(repository.id), "number": issue.number, "issue_id": str(issue.id)}],
                documents=[issue_text],
            )

            # Save the embedding record in PostgreSQL metadata
            embedding_repo = CRUDBase(EmbeddingRecord)
            embedding_repo.create(
                db,
                obj_in={
                    "repository_id": repository.id,
                    "entity_type": "issue",
                    "entity_id": str(issue.id),
                    "chunk_index": 0,
                    "text_content": issue_text,
                    "vector_id": vector_id,
                },
            )


duplicate_detector = DuplicateDetector()
