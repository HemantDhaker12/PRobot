import json
from unittest.mock import MagicMock, patch
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.issue import Issue
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.services.duplicate_detector import duplicate_detector
from app.services.triage_engine import triage_engine
from app.services.label_engine import label_engine
from app.services.pr_review_engine import pr_review_engine
from app.services.knowledge_engine import knowledge_engine


def test_duplicate_detector_no_duplicate(mock_db, mock_external_services):
    """
    If no matches are found, it should NOT mark issue as duplicate,
    and should index the issue text.
    """
    repo_id = uuid4()
    issue_id = uuid4()
    repository = Repository(id=repo_id, github_id=123, full_name="owner/repo", owner="owner", name="repo")
    issue = Issue(
        id=issue_id,
        repository_id=repo_id,
        number=1,
        title="Unique issue",
        body="Some unique text",
        state="open",
        html_url="https://github.com/owner/repo/issues/1",
        is_duplicate=False,
    )

    # Mock DB query
    mock_db.query.return_value.filter.return_value.first.side_effect = [repository, None]

    # Mock vector store search to return empty list
    mock_external_services["vector_store"]["query"].return_value = []

    # Run
    duplicate_detector.process_issue(mock_db, issue)

    # Verify
    assert issue.is_duplicate is False
    # Verify that the vector store was indexed
    mock_external_services["vector_store"]["upsert"].assert_called_once()
    # Verify no comment posted
    mock_external_services["github"]["post_comment"].assert_not_called()


def test_duplicate_detector_is_duplicate(mock_db, mock_external_services):
    """
    If a similar issue is found above threshold, it should mark it as duplicate,
    label it, post comment, and close it.
    """
    repo_id = uuid4()
    issue_id = uuid4()
    matched_issue_id = uuid4()

    repository = Repository(
        id=repo_id,
        github_id=123,
        full_name="owner/repo",
        owner="owner",
        name="repo",
        settings={"duplicate_similarity_threshold": 0.80, "duplicate_auto_close": True},
    )
    issue = Issue(
        id=issue_id,
        repository_id=repo_id,
        number=5,
        title="Duplicate error",
        body="It crashes on start",
        state="open",
        html_url="https://github.com/owner/repo/issues/5",
    )
    matched_issue = Issue(
        id=matched_issue_id,
        repository_id=repo_id,
        number=2,
        title="First error",
        body="It crashes on start",
    )

    # Mock DB queries
    def _mock_query_first(*args, **kwargs):
        # First query gets repo, second gets matching db issue
        if "Repository" in str(args) or len(args) == 0:
            return repository
        return matched_issue

    # Set up mock query chain
    mock_db.query.return_value.filter.return_value.first.side_effect = [repository, matched_issue]

    # Mock vector store return matches
    mock_external_services["vector_store"]["query"].return_value = [
        {"id": "issue_2", "similarity": 0.89, "metadata": {"number": 2, "issue_id": str(matched_issue_id)}, "document": ""}
    ]

    # Run
    duplicate_detector.process_issue(mock_db, issue)

    # Assertions
    assert issue.is_duplicate is True
    assert issue.state == "closed"
    mock_external_services["github"]["post_comment"].assert_called_once()
    mock_external_services["github"]["close_issue"].assert_called_once()


def test_triage_engine_missing_info(mock_db, mock_external_services):
    """
    If LLM reports missing variables, triage engine should comment on GitHub.
    """
    repo_id = uuid4()
    repository = Repository(id=repo_id, github_id=123, full_name="owner/repo", owner="owner", name="repo")
    issue = Issue(
        id=uuid4(),
        repository_id=repo_id,
        number=10,
        title="Error in processing",
        body="Help please",
        html_url="https://github.com/owner/repo/issues/10",
    )

    mock_db.query.return_value.filter.return_value.first.return_value = repository

    # Mock LLM to return missing reproduction steps and OS
    mock_response = {
        "os": {"present": False, "explanation": "Not mentioned"},
        "language_version": {"present": True, "explanation": "Python 3"},
        "package_version": {"present": True, "explanation": "v1.0"},
        "error_logs": {"present": True, "explanation": "Logs included"},
        "reproduction_steps": {"present": False, "explanation": "No steps"},
    }
    mock_external_services["llm"]["completion"].return_value = json.dumps(mock_response)

    # Run
    triage_engine.process_issue(mock_db, issue)

    # Verify Q&A comment posted
    mock_external_services["github"]["post_comment"].assert_called_once()
    comment = mock_external_services["github"]["post_comment"].call_args[0][2]
    assert "operating system" in comment.lower()
    assert "steps to reproduce" in comment.lower()


def test_label_engine(mock_db, mock_external_services):
    """
    Tests that label engine classifies issues and applies labels.
    """
    repo_id = uuid4()
    repository = Repository(id=repo_id, github_id=123, full_name="owner/repo", owner="owner", name="repo")
    issue = Issue(id=uuid4(), repository_id=repo_id, number=1, title="Crash on startup", body="", labels=[])

    mock_db.query.return_value.filter.return_value.first.return_value = repository

    # Mock classification response
    mock_external_services["llm"]["completion"].return_value = json.dumps({"labels": ["bug", "good-first-issue"]})

    label_engine.classify_and_label(mock_db, issue, is_pr=False)

    mock_external_services["github"]["add_labels"].assert_called_once_with("owner/repo", 1, ["bug", "good-first-issue"])


def test_pr_review_engine_passes(mock_db, mock_external_services):
    """
    Tests that PR Quality check reviews valid PRs and returns passed.
    """
    repo_id = uuid4()
    repository = Repository(id=repo_id, github_id=123, full_name="owner/repo", owner="owner", name="repo")
    pr = PullRequest(
        id=uuid4(),
        repository_id=repo_id,
        number=12,
        title="Update config",
        body="This PR resolves #55. We updated settings in code.",
        state="open",
    )

    mock_db.query.return_value.filter.return_value.first.return_value = repository

    # Mock file changes: no source code changes, so test verification is N/A
    mock_external_services["github"]["fetch_pr_files"].return_value = [{"filename": "docs/setup.md"}]

    pr_review_engine.review_pr(mock_db, pr)

    mock_external_services["github"]["post_comment"].assert_called_once()
    comment = mock_external_services["github"]["post_comment"].call_args[0][2]
    assert "✅ PASSED" in comment
    assert "fixes #55" in comment.lower() or "resolves #55" in comment.lower()
