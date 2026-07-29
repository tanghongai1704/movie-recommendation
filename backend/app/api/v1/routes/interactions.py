from typing import Annotated
from uuid import UUID, uuid5

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.container import interaction_service
from app.models.user import User
from app.repositories.dynamodb_base import DynamoDBRepositoryError
from app.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    UserMovieRatingResponse,
    UserMovieReactionResponse,
)
from app.services.interaction_service import InteractionService

router = APIRouter()

INTERACTION_EVENT_NAMESPACE = UUID(
    "8f323ede-e01f-53b9-b850-72d0915a65ad"
)


def get_interaction_service() -> InteractionService:
    return interaction_service


def generate_event_id(
    *,
    user_id: str,
    idempotency_key: str,
    payload: InteractionCreate,
) -> UUID:
    """Generate a stable event ID for one user, key, and canonical payload."""

    canonical_request = payload.model_dump_json()
    return uuid5(
        INTERACTION_EVENT_NAMESPACE,
        f"{user_id}\x1f{idempotency_key}\x1f{canonical_request}",
    )


@router.post(
    "/users/me/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_interaction(
    payload: InteractionCreate,
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=16,
            max_length=200,
            pattern=r"^[\x21-\x7E]+$",
        ),
    ],
    user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
) -> InteractionResponse:
    try:
        return service.record(
            user_id=user.user_id,
            username=user.username,
            event_id=generate_event_id(
                user_id=user.user_id,
                idempotency_key=idempotency_key,
                payload=payload,
            ),
            interaction=payload,
        )
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to record interaction",
        ) from exc


@router.get(
    "/users/me/ratings/{movie_id}",
    response_model=UserMovieRatingResponse,
)
def get_current_user_rating(
    movie_id: str,
    user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
) -> UserMovieRatingResponse:
    try:
        return service.get_latest_rating(
            user_id=user.user_id,
            movie_id=movie_id,
        )
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load rating",
        ) from exc


@router.get(
    "/users/me/reactions/{movie_id}",
    response_model=UserMovieReactionResponse,
)
def get_current_user_reaction(
    movie_id: str,
    user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
) -> UserMovieReactionResponse:
    try:
        return service.get_latest_reaction(
            user_id=user.user_id,
            movie_id=movie_id,
        )
    except DynamoDBRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load reaction",
        ) from exc
