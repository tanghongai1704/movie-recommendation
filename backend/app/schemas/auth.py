from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Existing login request contract."""

    username: str  # Username supplied for authentication.
    password: str  # Plaintext credential accepted only at the transport boundary.


class TokenResponse(BaseModel):
    """Existing bearer-token response contract."""

    access_token: str  # Token used to authenticate subsequent requests.
    token_type: str = "bearer"  # Authorization scheme associated with access_token.


class AuthenticatedUserResponse(BaseModel):
    """Compatibility identity response for the existing demo auth endpoint."""

    user_id: str  # Canonical Users.user_id for the authenticated principal.
    username: str  # Canonical Users.username for the authenticated principal.
    role: str = "user"  # Derived authorization label; it is not persisted in Users.
