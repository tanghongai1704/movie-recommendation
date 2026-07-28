from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.models.user import User
from app.repositories.dynamodb_base import DynamoDBRepositoryError
from app.repositories.user_interactions_repository import (
    UserInteractionsRepository,
)
from app.schemas.interaction import InteractionCreate, InteractionResponse
from app.services.interaction_service import InteractionService

router = APIRouter()

interaction_service = InteractionService(
    repository=UserInteractionsRepository(
        table_name=settings.AWS_DYNAMODB_TABLE_INTERACTIONS,
        region_name=settings.AWS_REGION,
    )
)


def get_interaction_service() -> InteractionService:
    return interaction_service


@router.post(
    "/users/me/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_interaction(
    payload: InteractionCreate,
    user: User = Depends(get_current_user),
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
