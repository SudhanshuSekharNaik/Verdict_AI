import asyncio
import os
import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

# Set test environment
root_dir = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, root_dir)
sys.path.insert(0, str(Path(root_dir) / "backend"))

from app.main import app
from app.database.session import AsyncSessionLocal, engine
from app.models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
