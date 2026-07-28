from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import auth_service
from app.core.security import TokenClaims
from app.models.user import User
from app.services.auth_service import AuthService, UserNotFoundError

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    auto_error=False,
    description="JWT access token returned by register or login.",
)


def get_auth_service() -> AuthService:
    return auth_service


def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
    service: AuthService = Depends(get_auth_service),
) -> User:
    # The middleware performs signature and claim validation. This dependency
    # supplies OpenAPI security metadata and resolves the current Users record.
    del credentials
    claims = getattr(request.state, "auth", None)
    if not isinstance(claims, TokenClaims):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return service.get_user(claims.user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_completed_onboarding(
    user: User = Depends(get_current_user),
) -> User:
    if not user.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Onboarding must be completed before personalized recommendations",
        )
    return user
