from pydantic import BaseModel, Field


class Credentials(BaseModel):
    """Username/password body for register and login."""

    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Bearer token issued on successful login."""

    access_token: str
    token_type: str = "bearer"
