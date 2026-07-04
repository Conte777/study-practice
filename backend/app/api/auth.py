"""Authentication: register, login, and the bearer-token guard dependency."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas import Credentials, ErrorResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=True)

# Real bcrypt hash of a throwaway password: verifying against it on the
# user-missing path keeps login timing uniform (mitigates username enumeration).
_DUMMY_HASH = "$2b$12$tYqJVQODssfC2XFv08BCseU5m3RjOorgHs3nEClTQI6ylp18wQ6wW"


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register a new user",
    responses={409: {"model": ErrorResponse, "description": "Username already taken"}},
)
async def register(
    body: Credentials,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Create an account and return a token, or 409 if the username is taken."""
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already taken") from exc
    return TokenResponse(access_token=create_access_token(body.username))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    responses={401: {"model": ErrorResponse, "description": "Invalid credentials"}},
)
async def login(
    body: Credentials,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Verify credentials and return a bearer token, or 401 on mismatch."""
    user = db.scalar(select(User).where(User.username == body.username))
    # Verify even when the user is missing to keep timing uniform across the two paths.
    hashed = user.password_hash if user else _DUMMY_HASH
    if not verify_password(body.password, hashed) or user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return TokenResponse(access_token=create_access_token(user.username))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the bearer token to a live user, or raise 401."""
    username = decode_token(credentials.credentials)
    user = db.scalar(select(User).where(User.username == username)) if username else None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
