"""Tests for the health check endpoint."""

import pytest


@pytest.mark.anyio
async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1.0"
    assert "status" in data
    assert "database" in data
