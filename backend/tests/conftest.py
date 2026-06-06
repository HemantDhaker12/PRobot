import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.services.github_service import github_service


@pytest.fixture
def mock_db() -> MagicMock:
    """
    Fixture providing a mocked SQLAlchemy session.
    """
    mock_session = MagicMock(spec=Session)
    # Mock commit, rollback, add, refresh, query methods
    mock_session.commit = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.add = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.query = MagicMock()
    return mock_session


@pytest.fixture
def client(mock_db) -> TestClient:
    """
    Fixture providing a FastAPI TestClient with database session overridden.
    """
    def _override_get_db():
        try:
            yield mock_db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """
    Fixture to mock all external network-connected service dependencies.
    """
    # 1. Mock Embedding Service
    mock_get_embedding = MagicMock(return_value=[0.15] * 384)
    mock_get_embeddings = MagicMock(return_value=[[0.15] * 384])
    monkeypatch.setattr(embedding_service, "get_embedding", mock_get_embedding)
    monkeypatch.setattr(embedding_service, "get_embeddings", mock_get_embeddings)

    # 2. Mock Vector Store (ChromaDB)
    mock_upsert = MagicMock()
    mock_query = MagicMock(return_value=[])
    mock_delete = MagicMock()
    monkeypatch.setattr(vector_store, "upsert_embeddings", mock_upsert)
    monkeypatch.setattr(vector_store, "query_similar", mock_query)
    monkeypatch.setattr(vector_store, "delete_embeddings", mock_delete)
    monkeypatch.setattr(vector_store, "delete_by_repository", mock_delete)

    # 3. Mock LLM Service (Groq)
    mock_completion = MagicMock(return_value="{}")
    monkeypatch.setattr(llm_service, "chat_completion", mock_completion)

    # 4. Mock GitHub Service
    mock_post_comment = MagicMock(return_value={"id": 123456})
    mock_add_labels = MagicMock(return_value=[{"name": "bug"}])
    mock_remove_label = MagicMock()
    mock_close_issue = MagicMock(return_value={"state": "closed"})
    mock_fetch_pr_files = MagicMock(return_value=[])
    mock_fetch_file = MagicMock(return_value="# Doc Content")
    mock_fetch_dir = MagicMock(return_value=[])

    monkeypatch.setattr(github_service, "post_comment", mock_post_comment)
    monkeypatch.setattr(github_service, "add_labels", mock_add_labels)
    monkeypatch.setattr(github_service, "remove_label", mock_remove_label)
    monkeypatch.setattr(github_service, "close_issue", mock_close_issue)
    monkeypatch.setattr(github_service, "fetch_pr_files", mock_fetch_pr_files)
    monkeypatch.setattr(github_service, "fetch_file_content", mock_fetch_file)
    monkeypatch.setattr(github_service, "fetch_repo_directory", mock_fetch_dir)

    return {
        "embedding": {"get_embedding": mock_get_embedding, "get_embeddings": mock_get_embeddings},
        "vector_store": {"upsert": mock_upsert, "query": mock_query, "delete": mock_delete},
        "llm": {"completion": mock_completion},
        "github": {
            "post_comment": mock_post_comment,
            "add_labels": mock_add_labels,
            "close_issue": mock_close_issue,
            "fetch_pr_files": mock_fetch_pr_files,
            "fetch_file_content": mock_fetch_file,
            "fetch_repo_directory": mock_fetch_dir,
        },
    }
