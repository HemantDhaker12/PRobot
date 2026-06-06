from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from app.models.webhook_event import WebhookEvent
from app.models.issue import Issue
from app.models.pull_request import PullRequest


def test_health_endpoint(client: TestClient):
    """
    Test GET /health.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "healthy"
    assert response.json()["redis"] == "healthy"


def test_metrics_endpoint(client: TestClient, mock_db):
    """
    Test GET /metrics.
    """
    # Configure mock DB count returns
    mock_db.query.return_value.count.return_value = 5
    mock_db.query.return_value.group_by.return_value.all.return_value = [("processed", 10), ("failed", 2)]

    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json()["repositories_count"] == 5
    assert response.json()["pull_requests_count"] == 5
    assert response.json()["webhook_events"]["processed"] == 10
    assert response.json()["webhook_events"]["failed"] == 2


def test_issues_endpoints(client: TestClient, mock_db):
    """
    Test GET /issues and GET /issues/{id}.
    """
    mock_id = uuid4()
    mock_issue = Issue(
        id=mock_id,
        repository_id=uuid4(),
        number=1,
        title="Test Issue",
        body="Detailed description",
        state="open",
        html_url="https://github.com/owner/repo/issues/1",
        is_duplicate=False,
        labels=["bug"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock list
    mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_issue]
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_issue]

    # Test list issues
    response = client.get("/issues")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test Issue"

    # Mock detail fetch
    mock_db.query.return_value.filter.return_value.first.return_value = mock_issue

    # Test get single issue
    response_detail = client.get(f"/issues/{str(mock_id)}")
    assert response_detail.status_code == 200
    assert response_detail.json()["id"] == str(mock_id)


def test_webhook_github_missing_signature(client: TestClient):
    """
    Test POST /webhooks/github returns 422 Unprocessable Entity if headers are missing.
    """
    response = client.post(
        "/webhooks/github",
        json={"action": "opened"},
    )
    assert response.status_code == 422  # validation error due to missing headers


def test_webhook_github_success(client: TestClient, mock_db, monkeypatch):
    """
    Test successful POST /webhooks/github event receipt and task enqueueing.
    """
    # Mock signature verification function to return True
    import app.api.endpoints.webhooks as webhooks_module
    monkeypatch.setattr(webhooks_module, "verify_github_signature", lambda *args, **kwargs: True)

    # Mock repository queries
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Mock repository create
    mock_event = WebhookEvent(
        id=uuid4(),
        delivery_id="delivery-12345",
        event_type="issues",
        payload={"action": "opened"},
        status="pending",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()

    # Stub repo return creation
    monkeypatch.setattr(webhooks_module.webhook_event_repo, "get_by_delivery_id", lambda *args: None)
    monkeypatch.setattr(webhooks_module.webhook_event_repo, "create", lambda *args, **kwargs: mock_event)

    headers = {
        "X-GitHub-Event": "issues",
        "X-GitHub-Delivery": "delivery-12345",
        "X-Hub-Signature-256": "sha256=test_signature",
    }

    response = client.post(
        "/webhooks/github",
        json={
            "action": "opened",
            "repository": {
                "id": 123,
                "full_name": "owner/repo",
                "name": "repo",
                "owner": {"login": "owner"}
            },
            "issue": {
                "number": 1,
                "title": "Bug report",
                "body": "Crash on startup",
                "state": "open",
                "html_url": "https://github.com/owner/repo/issues/1"
            }
        },
        headers=headers,
    )

    assert response.status_code == 202
    assert response.json()["success"] is True
    assert response.json()["event_id"] == str(mock_event.id)


def test_verify_github_signature_success(caplog):
    import logging
    from app.utils.helpers import verify_github_signature
    import hmac
    import hashlib

    payload = b'{"action": "test"}'
    secret = "super_secret_key"
    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"

    with caplog.at_level(logging.INFO):
        res = verify_github_signature(payload, expected_signature, secret)
        assert res is True

        # Verify that all logs were correctly generated
        assert "Webhook signature verification started. Configured webhook secret length: 16" in caplog.text
        assert f"Received signature header: {expected_signature}" in caplog.text
        assert f"Calculated signature: sha256={mac.hexdigest()}" in caplog.text
        assert "Signature verification result: True" in caplog.text


def test_verify_github_signature_failure(caplog):
    import logging
    from app.utils.helpers import verify_github_signature

    payload = b'{"action": "test"}'
    secret = "super_secret_key"
    invalid_signature = "sha256=invalidhashvalue12345"

    with caplog.at_level(logging.INFO):
        res = verify_github_signature(payload, invalid_signature, secret)
        assert res is False

        # Verify failure logs
        assert "Webhook signature verification started. Configured webhook secret length: 16" in caplog.text
        assert f"Received signature header: {invalid_signature}" in caplog.text
        assert "Signature verification result: False" in caplog.text

