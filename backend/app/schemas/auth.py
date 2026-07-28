from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth_validation import normalize_email
from app.schemas.user import UserProfileResponse


class RegisterRequest(BaseModel):
    """Credentials and identity fields required to create an account."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class LoginRequest(BaseModel):
    """Username-or-email credentials accepted by the login endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    username: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Authenticated session returned by register and login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse
