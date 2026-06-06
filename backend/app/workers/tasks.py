import logging
from uuid import UUID
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.comment import IssueComment
from app.models.issue import Issue
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.models.webhook_event import WebhookEvent
from app.models.embedding_record import EmbeddingRecord
from app.repositories.base import CRUDBase
from app.repositories.repository_repo import repository_repo
from app.repositories.issue_repo import issue_repo
from app.repositories.pull_request_repo import pull_request_repo
from app.repositories.webhook_event_repo import webhook_event_repo
from app.services.duplicate_detector import duplicate_detector
from app.services.triage_engine import triage_engine
from app.services.label_engine import label_engine
from app.services.pr_review_engine import pr_review_engine
from app.services.knowledge_engine import knowledge_engine
from app.utils.helpers import chunk_text
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store


@celery_app.task(bind=True, max_retries=3)
def process_webhook_event(self, event_id: str) -> None:
    """
    Main webhook coordinator task.
    Reads WebhookEvent from PostgreSQL, parses repository references, syncs metadata,
    and dispatches specific sub-tasks for active automated maintainer engines.
    """
    logging.info(f"Processing webhook event: {event_id}")
    db: Session = SessionLocal()
    try:
        # 1. Fetch event
        event = webhook_event_repo.get(db, UUID(event_id))
        if not event:
            logging.warning(f"Webhook event not found in database: {event_id}. Retrying task in 2 seconds...")
            raise self.retry(exc=ValueError(f"Webhook event {event_id} not found"), countdown=2, max_retries=5)

        payload = event.payload
        event_type = event.event_type

        # 2. Extract repository metadata
        repo_data = payload.get("repository", {})
        repo_github_id = repo_data.get("id")
        repo_full_name = repo_data.get("full-name") or repo_data.get("full_name")
        repo_owner_data = repo_data.get("owner", {})
        repo_owner = repo_owner_data.get("login") or repo_owner_data.get("name")
        repo_name = repo_data.get("name")

        if not all([repo_github_id, repo_full_name, repo_owner, repo_name]):
            logging.warning(f"Incomplete repository data in event {event_id}. Skipping sync.")
            event.status = "processed"
            db.commit()
            return

        # 3. Upsert Repository in database
        repository = repository_repo.get_by_github_id(db, repo_github_id)
        if not repository:
            logging.info(f"Creating new Repository entry for: {repo_full_name}")
            default_settings = {
                "duplicate_detection_enabled": True,
                "duplicate_similarity_threshold": 0.82,
                "duplicate_auto_close": True,
                "triage_enabled": True,
                "labeling_enabled": True,
                "pr_guardian_enabled": True,
                "knowledge_assistant_enabled": True,
                "labels": label_engine.DEFAULT_LABELS,
            }
            repository = repository_repo.create(
                db,
                obj_in={
                    "github_id": repo_github_id,
                    "full_name": repo_full_name,
                    "owner": repo_owner,
                    "name": repo_name,
                    "settings": default_settings,
                },
            )
        else:
            # Sync repo name/owner changes
            repository.full_name = repo_full_name
            repository.owner = repo_owner
            repository.name = repo_name
            db.commit()

        # 4. Handle specific event types
        if event_type == "issues":
            action = payload.get("action")
            issue_data = payload.get("issue", {})
            issue_number = issue_data.get("number")
            issue_title = issue_data.get("title")
            issue_body = issue_data.get("body")
            issue_state = issue_data.get("state")
            issue_html_url = issue_data.get("html_url")

            # Extract labels list
            issue_labels = [lbl.get("name") for lbl in issue_data.get("labels", []) if lbl.get("name")]

            # Sync Issue in PostgreSQL
            issue = issue_repo.get_by_number(db, repository.id, issue_number)
            if not issue:
                issue = issue_repo.create(
                    db,
                    obj_in={
                        "repository_id": repository.id,
                        "number": issue_number,
                        "title": issue_title,
                        "body": issue_body,
                        "state": issue_state,
                        "html_url": issue_html_url,
                        "labels": issue_labels,
                    },
                )
            else:
                issue.title = issue_title
                issue.body = issue_body
                issue.state = issue_state
                issue.labels = issue_labels
                db.commit()

            # Dispatch issue sub-tasks
            if action == "opened":
                logging.info(f"Issue opened: {repository.full_name}#{issue_number}")
                # Run Duplicate issue checker
                async_detect_duplicates.delay(str(issue.id))
                # Run issue triage
                async_triage_issue.delay(str(issue.id))
                # Run labeling
                async_label_issue_or_pr.delay(str(issue.id), False)
                # Run Q&A knowledge assistant
                async_process_question_issue.delay(str(issue.id))

            elif action == "closed":
                # Add to resolved issues index in Chroma
                async_index_closed_issue.delay(str(issue.id))

        elif event_type == "pull_request":
            action = payload.get("action")
            pr_data = payload.get("pull_request", {})
            pr_number = pr_data.get("number")
            pr_title = pr_data.get("title")
            pr_body = pr_data.get("body")
            pr_state = pr_data.get("state")
            pr_html_url = pr_data.get("html_url")
            pr_draft = pr_data.get("draft", False)

            # Sync PR in PostgreSQL
            pr_obj = pull_request_repo.get_by_number(db, repository.id, pr_number)
            if not pr_obj:
                pr_obj = pull_request_repo.create(
                    db,
                    obj_in={
                        "repository_id": repository.id,
                        "number": pr_number,
                        "title": pr_title,
                        "body": pr_body,
                        "state": pr_state,
                        "html_url": pr_html_url,
                        "is_draft": pr_draft,
                    },
                )
            else:
                pr_obj.title = pr_title
                pr_obj.body = pr_body
                pr_obj.state = pr_state
                pr_obj.is_draft = pr_draft
                db.commit()

            # Dispatch PR sub-tasks
            if action in ("opened", "synchronize", "edited"):
                if not pr_draft:
                    # Run Quality review checks
                    async_review_pr.delay(str(pr_obj.id))
                    # Run labeling
                    async_label_issue_or_pr.delay(str(pr_obj.id), True)

        elif event_type == "issue_comment":
            # For logging and capturing resolution details on closed issues
            action = payload.get("action")
            comment_data = payload.get("comment", {})
            github_comment_id = comment_data.get("id")
            comment_body = comment_data.get("body")
            author = comment_data.get("user", {}).get("login")

            # Check if this comment belongs to an issue or PR synced
            issue_payload_data = payload.get("issue", {})
            issue_number = issue_payload_data.get("number")

            if issue_number and action == "created":
                issue_obj = issue_repo.get_by_number(db, repository.id, issue_number)
                if issue_obj:
                    # Save comment
                    comment_repo = CRUDBase(IssueComment)
                    comment_repo.create(
                        db,
                        obj_in={
                            "repository_id": repository.id,
                            "issue_id": issue_obj.id,
                            "github_comment_id": github_comment_id,
                            "body": comment_body,
                            "author": author,
                        },
                    )

        event.status = "processed"
        db.commit()

    except Exception as exc:
        logging.error(f"Error processing webhook event: {str(exc)}", exc_info=True)
        # Setup retry mechanism or update to failed
        db_retry = SessionLocal()
        event_retry = webhook_event_repo.get(db_retry, UUID(event_id))
        if event_retry:
            event_retry.status = "failed"
            event_retry.error_message = str(exc)
            db_retry.commit()
        db_retry.close()
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()


@shared_task
def async_detect_duplicates(issue_id: str) -> None:
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter(Issue.id == UUID(issue_id)).first()
        if issue:
            duplicate_detector.process_issue(db, issue)
    finally:
        db.close()


@shared_task
def async_triage_issue(issue_id: str) -> None:
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter(Issue.id == UUID(issue_id)).first()
        if issue:
            triage_engine.process_issue(db, issue)
    finally:
        db.close()


@shared_task
def async_label_issue_or_pr(entity_id: str, is_pr: bool) -> None:
    db = SessionLocal()
    try:
        if is_pr:
            pr = db.query(PullRequest).filter(PullRequest.id == UUID(entity_id)).first()
            if pr:
                label_engine.classify_and_label(db, pr, is_pr=True)
        else:
            issue = db.query(Issue).filter(Issue.id == UUID(entity_id)).first()
            if issue:
                label_engine.classify_and_label(db, issue, is_pr=False)
    finally:
        db.close()


@shared_task
def async_review_pr(pr_id: str) -> None:
    db = SessionLocal()
    try:
        pr = db.query(PullRequest).filter(PullRequest.id == UUID(pr_id)).first()
        if pr:
            pr_review_engine.review_pr(db, pr)
    finally:
        db.close()


@shared_task
def async_process_question_issue(issue_id: str) -> None:
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter(Issue.id == UUID(issue_id)).first()
        if issue:
            # Simple keyword or label check: does it ask a question?
            is_question = "question" in (issue.labels or [])
            if not is_question:
                # Fallback: check if the body ends with a question mark or LLM check
                desc = (issue.body or "").strip().lower()
                is_question = desc.endswith("?") or "how to" in desc or "how do i" in desc

            if is_question:
                logging.info(f"Issue {issue.number} classified as a question. Invoking Knowledge Assistant.")
                knowledge_engine.answer_question_issue(db, issue)
    finally:
        db.close()


@shared_task
def async_index_closed_issue(issue_id: str) -> None:
    """
    Task to run when an issue is closed.
    Indices the resolved issue and its history in RAG embeddings.
    """
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter(Issue.id == UUID(issue_id)).first()
        if issue and not issue.is_duplicate:
            # Sync closing issues into KnowledgeBase (Feature 5 resolved issues)
            repository = db.query(Repository).filter(Repository.id == issue.repository_id).first()
            if repository:
                # We can re-trigger index closed issue or run individual document indexing
                # For simplicity, we just chunk and embed this specific issue and add to solved issues
                comments = db.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
                comments_text = "\n".join([f"- {c.author}: {c.body}" for c in comments])
                resolved_text = (
                    f"Resolved Issue #{issue.number}\n"
                    f"Title: {issue.title}\n"
                    f"Description: {issue.body or ''}\n"
                    f"Resolution Comments:\n{comments_text}"
                )

                chunks = chunk_text(resolved_text, chunk_size=800, chunk_overlap=150)
                for idx, chunk in enumerate(chunks):
                    vector_id = f"resolved_issue_{str(issue.id)}_{idx}"
                    embedding = embedding_service.get_embedding(chunk)

                    # Save to Chroma
                    vector_store.upsert_embeddings(
                        collection_name="resolved_issue_embeddings",
                        ids=[vector_id],
                        embeddings=[embedding],
                        metadatas=[{"repository_id": str(repository.id), "issue_number": issue.number}],
                        documents=[chunk],
                    )

                    # Save PostgreSQL record
                    db_record = EmbeddingRecord(
                        repository_id=repository.id,
                        entity_type="resolved_issue",
                        entity_id=str(issue.id),
                        chunk_index=idx,
                        text_content=chunk,
                        vector_id=vector_id,
                    )
                    db.add(db_record)
                db.commit()
                logging.info(f"Indexed resolved issue #{issue.number} successfully.")
    finally:
        db.close()


@shared_task
def async_reindex_repository_knowledge(repository_id: str) -> None:
    db = SessionLocal()
    try:
        repository = db.query(Repository).filter(Repository.id == UUID(repository_id)).first()
        if repository:
            knowledge_engine.reindex_repository(db, repository)
    finally:
        db.close()
