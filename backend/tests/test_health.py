import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "Aadalat AI" in data["data"]["service"]


@pytest.mark.asyncio
async def test_api_version(async_client):
    response = await async_client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "capabilities" in data["data"]
    assert len(data["data"]["capabilities"]) >= 5
