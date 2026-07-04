"""Database engine, session factory, and schema bootstrap.

Uses SQLAlchemy's ``create_all`` for schema creation (no Alembic).
ponytail: ``create_all`` is enough for this project; add Alembic only if
migrations against existing data become a real requirement.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import Base

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
# Login holds a connection through the slow bcrypt verify, so a 50-user burst
# exhausts the default 5+10 pool. Give Postgres real headroom; sqlite (tests)
# uses a pool that rejects these kwargs, so skip them there.
# ponytail: static sizes; wire to settings only if load profiles start varying.
_pool_args = {} if _is_sqlite else {"pool_size": 20, "max_overflow": 40}

engine = create_engine(
    settings.DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args, **_pool_args
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create all tables that do not yet exist."""
    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
