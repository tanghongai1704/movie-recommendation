from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.repositories.dynamodb_base import DynamoDBRepositoryError
from app.repositories.user_interactions_repository import (
    UserInteractionsRepository,
)
from app.schemas.interaction import InteractionCreate, InteractionResponse
from app.services.interaction_service import InteractionService

router = APIRouter()
security = HTTPBearer()


@dataclass(frozen=True)
class InteractionUser:
    user_id: str
    username: str


interaction_service = InteractionService(
    repository=UserInteractionsRepository(
        table_name=settings.AWS_DYNAMODB_TABLE_INTERACTIONS,
        region_name=settings.AWS_REGION,
    )
)


def get_interaction_service() -> InteractionService:
    return interaction_service


def get_interaction_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> InteractionUser:
    token = credentials.credentials
    if not token.startswith(settings.AUTH_TOKEN_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    username = token.removeprefix(settings.AUTH_TOKEN_PREFIX)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # The current demo authentication contract exposes one application user.
    return InteractionUser(user_id="1", username=username)


@router.post(
    "/users/me/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_interaction(
    payload: InteractionCreate,
    user: InteractionUser = Depends(get_interaction_user),
    service: InteractionService = Depends(get_interaction_service),
) -> InteractionResponse:
    try:
        return service.record(
            user_id=user.user_id,
            username=user.username,
            interaction=payload,
        )
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to record interaction",
        ) from exc
