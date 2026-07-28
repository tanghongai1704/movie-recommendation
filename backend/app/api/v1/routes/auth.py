from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies.auth import get_auth_service, get_current_user
from app.container import jwt_service
from app.models.user import User
from app.repositories.dynamodb_base import DynamoDBRepositoryError
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import (
    CompleteOnboardingRequest,
    UpdateProfileRequest,
    UserProfileResponse,
    UserState,
)
from app.services.auth_service import (
    AccountConflictError,
    AuthService,
    InvalidCredentialsError,
)

router = APIRouter()


def to_profile_response(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        onboarding_genres=user.onboarding_genres or [],
        onboarding_completed=user.onboarding_completed,
        last_active_at=user.last_active_at,
        user_state=(
            UserState.RETURNING_USER
            if user.onboarding_completed
            else UserState.FIRST_LOGIN
        ),
    )


def create_session_response(user: User) -> TokenResponse:
    issued_token = jwt_service.issue_access_token(user.user_id)
    return TokenResponse(
        access_token=issued_token.token,
        expires_in=issued_token.expires_in,
        user=to_profile_response(user),
    )


@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        user = service.register(
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
        return create_session_response(user)
    except AccountConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to create account",
        ) from exc


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        user = service.authenticate(
            identity=payload.username,
            password=payload.password,
        )
        return create_session_response(user)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to authenticate",
        ) from exc


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: User = Depends(get_current_user)) -> Response:
    del user
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", response_model=UserProfileResponse)
@router.get("/users/me/profile", response_model=UserProfileResponse)
def get_profile(user: User = Depends(get_current_user)) -> UserProfileResponse:
    return to_profile_response(user)


@router.patch("/users/me/profile", response_model=UserProfileResponse)
def update_profile(
    payload: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> UserProfileResponse:
    try:
        updated = service.update_profile(
            user_id=user.user_id,
            email=payload.email,
            username=payload.username,
        )
        return to_profile_response(updated)
    except AccountConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to update profile",
        ) from exc


@router.put("/users/me/onboarding", response_model=UserProfileResponse)
def complete_onboarding(
    payload: CompleteOnboardingRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> UserProfileResponse:
    try:
        updated = service.complete_onboarding(
            user_id=user.user_id,
            onboarding_genres=payload.onboarding_genres,
        )
        return to_profile_response(updated)
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to complete onboarding",
        ) from exc
