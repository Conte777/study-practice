"""Idempotent startup seeding of the demo login account."""

import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import User

logger = logging.getLogger(__name__)


def seed_demo_user() -> None:
    """Create the demo user from env if configured and not already present."""
    if not settings.DEMO_USER or not settings.DEMO_PASSWORD:
        return
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == settings.DEMO_USER)):
            return
        db.add(
            User(
                username=settings.DEMO_USER,
                password_hash=hash_password(settings.DEMO_PASSWORD),
            )
        )
        db.commit()
        logger.info("Seeded demo user %r", settings.DEMO_USER)
