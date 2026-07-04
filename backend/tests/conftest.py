"""Test configuration: local service URLs, a throwaway sqlite DB, shared helpers.

Env is set before importing the app so ``Settings`` (and the lru-cached ES/Redis
clients) bind to host-published compose ports. The DB uses a temp sqlite file so
the contract/unit suite runs without Postgres; ES/Redis integration tests skip
gracefully when their service is unreachable.
"""

import io
import os
import tempfile

os.environ.setdefault(
    "DATABASE_URL", f"sqlite:///{os.path.join(tempfile.gettempdir(), 'ks_test.db')}"
)
os.environ.setdefault("ELASTICSEARCH_URL", "http://localhost:9200")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest  # noqa: E402 — must follow env setup above
from docx import Document as DocxDocument  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.auth import get_current_user  # noqa: E402
from app.core.db import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, User  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: needs live ES/Redis (compose)")


def make_docx(text: str) -> bytes:
    """Build an in-memory .docx with one paragraph per line of ``text``."""
    doc = DocxDocument()
    for line in text.splitlines() or [text]:
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def es_available() -> bool:
    """Return True if the compose Elasticsearch is reachable."""
    from app.services.es import get_client

    try:
        return bool(get_client().ping())
    except Exception:
        return False


def redis_available() -> bool:
    """Return True if the compose Redis is reachable."""
    from app.services.cache import get_client

    try:
        return bool(get_client().ping())
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _schema():
    """Recreate the DB schema around each test for isolation."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    """Authenticated client: auth is bypassed so tests focus on their endpoint.

    Real auth behaviour is exercised separately in ``test_auth.py`` via ``raw_client``.
    """
    app.dependency_overrides[get_current_user] = lambda: User(username="tester")
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def raw_client() -> TestClient:
    """Client with real auth enforced (no dependency override)."""
    return TestClient(app)
