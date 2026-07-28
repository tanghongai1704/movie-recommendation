from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import (
    AuthenticatedUserResponse,
    LoginRequest,
    TokenResponse,
)

security = HTTPBearer()
router = APIRouter()


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        "iat": datetime.now(timezone.utc),
        "role": "user",
    }
    return f"dummy-token-for-{username}"


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if payload.username != "demo" or payload.password != "password123":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(payload.username)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=AuthenticatedUserResponse)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUserResponse:
    token = credentials.credentials
    if not token.startswith("dummy-token-for-"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = token.replace("dummy-token-for-", "")
    return AuthenticatedUserResponse(user_id="1", username=username)
