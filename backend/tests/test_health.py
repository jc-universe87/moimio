"""Tests for the health check endpoint."""

import pytest
from app.version import __version__


@pytest.mark.anyio
async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == __version__
    assert "status" in data
    assert "database" in data
