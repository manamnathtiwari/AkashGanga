"""Test configuration: use mock solver + a temporary SQLite database."""
from __future__ import annotations

import os
import tempfile

# Configure the app BEFORE importing any app modules (settings are cached).
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["AKASHGANGA_DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp_db.name}"
os.environ["AKASHGANGA_SOLVER_BACKEND"] = "mock"
os.environ["AKASHGANGA_ASTROMETRY_API_KEY"] = ""
os.environ["AKASHGANGA_UPLOAD_DIR"] = tempfile.mkdtemp()

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
