import pytest
from unittest.mock import MagicMock
from fastapi import status


def test_health_check_all_healthy(client, mock_db, monkeypatch):
    # Mock DB execute to not raise any exception (mock_db is already a MagicMock, so execute will succeed by default)
    mock_db.execute.reset_mock()
    mock_db.execute.side_effect = None

    # Mock Redis connection to succeed
    mock_redis_client = MagicMock()
    mock_redis_client.ping = MagicMock(return_value=True)
    mock_from_url = MagicMock(return_value=mock_redis_client)

    monkeypatch.setattr("app.api.endpoints.health.redis.from_url", mock_from_url)

    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {
        "status": "healthy",
        "database": "healthy",
        "redis": "healthy"
    }

    # Verify db.execute was called once
    mock_db.execute.assert_called_once()
    # Verify redis.from_url was called
    mock_from_url.assert_called_once()


def test_health_check_db_unhealthy(client, mock_db, monkeypatch):
    # Mock DB execute to raise an exception
    mock_db.execute.side_effect = Exception("DB connection timeout")

    # Mock Redis connection to succeed
    mock_redis_client = MagicMock()
    mock_redis_client.ping = MagicMock(return_value=True)
    mock_from_url = MagicMock(return_value=mock_redis_client)

    monkeypatch.setattr("app.api.endpoints.health.redis.from_url", mock_from_url)

    response = client.get("/health")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data == {
        "status": "unhealthy",
        "database": "unhealthy",
        "redis": "healthy"
    }

    # Reset side effect for subsequent tests
    mock_db.execute.side_effect = None


def test_health_check_redis_unhealthy(client, mock_db, monkeypatch):
    mock_db.execute.reset_mock()
    mock_db.execute.side_effect = None

    # Mock Redis connection to raise an exception
    mock_from_url = MagicMock(side_effect=Exception("Redis connection refused"))

    monkeypatch.setattr("app.api.endpoints.health.redis.from_url", mock_from_url)

    response = client.get("/health")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data == {
        "status": "unhealthy",
        "database": "healthy",
        "redis": "unhealthy"
    }


def test_health_check_both_unhealthy(client, mock_db, monkeypatch):
    # Mock DB to fail
    mock_db.execute.side_effect = Exception("DB down")

    # Mock Redis to fail
    mock_from_url = MagicMock(side_effect=Exception("Redis down"))

    monkeypatch.setattr("app.api.endpoints.health.redis.from_url", mock_from_url)

    response = client.get("/health")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data == {
        "status": "unhealthy",
        "database": "unhealthy",
        "redis": "unhealthy"
    }

    # Reset side effect
    mock_db.execute.side_effect = None
