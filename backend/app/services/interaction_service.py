from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.models.user_interaction import (
    InteractionAction,
    InteractionType,
    UserInteraction,
    format_interaction_timestamp,
)
from app.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    UserMovieRatingResponse,
    UserMovieReactionResponse,
)


class InteractionRepository(Protocol):
    """Persistence boundary used by InteractionService."""

    def create(self, item: UserInteraction) -> UserInteraction:
        ...

    def list_by_user(self, user_id: str) -> list[UserInteraction]:
        ...


class InteractionService:
    """Records user behavior for downstream analytics and ML consumers."""

    def __init__(self, repository: InteractionRepository) -> None:
        self._repository = repository

    def record(
        self,
        *,
        user_id: str,
        username: str,
        event_id: UUID,
        interaction: InteractionCreate,
    ) -> InteractionResponse:
        # username remains in the method signature for route compatibility but is
        # intentionally not duplicated in the canonical interaction record.
        del username

        timestamp = interaction.timestamp
        timestamp_text = format_interaction_timestamp(timestamp)
        record = UserInteraction(
            user_id=user_id,
            interaction_key=(
                f"{timestamp_text}#{interaction.movie_id}#{event_id}"
            ),
            event_id=event_id,
            movie_id=interaction.movie_id,
            interaction_type=interaction.interaction_type,
            interaction_action=InteractionAction(
                interaction.interaction_action.value
            ),
            interaction_value=interaction.interaction_value,
            timestamp=timestamp,
            session_id=interaction.session_id,
        )
        stored = self._repository.create(record)

        return InteractionResponse.model_validate(stored.model_dump())

    def get_latest_rating(
        self,
        *,
        user_id: str,
        movie_id: str,
    ) -> UserMovieRatingResponse:
        """Return the most recent rating event for one user and movie."""

        ratings = [
            interaction
            for interaction in self._repository.list_by_user(user_id)
            if interaction.movie_id == movie_id
            and interaction.interaction_type == InteractionType.RATING
            and interaction.interaction_action
            in {
                InteractionAction.SET,
                InteractionAction.CLEAR,
                InteractionAction.RATING_SUBMIT,
            }
        ]
        latest = max(
            ratings,
            key=lambda interaction: (
                interaction.timestamp,
                interaction.interaction_key,
            ),
            default=None,
        )
        return UserMovieRatingResponse(
            movie_id=movie_id,
            rating=(
                latest.interaction_value
                if latest is not None
                and latest.interaction_action != InteractionAction.CLEAR
                else None
            ),
        )

    def get_latest_reaction(
        self,
        *,
        user_id: str,
        movie_id: str,
    ) -> UserMovieReactionResponse:
        """Return the most recent reaction event for one user and movie."""

        reactions = [
            interaction
            for interaction in self._repository.list_by_user(user_id)
            if interaction.movie_id == movie_id
            and interaction.interaction_type == InteractionType.REACTION
            and interaction.interaction_action
            in {
                InteractionAction.SET,
                InteractionAction.CLEAR,
                InteractionAction.REACTION_LIKE,
                InteractionAction.REACTION_DISLIKE,
            }
        ]
        latest = max(
            reactions,
            key=lambda interaction: (
                interaction.timestamp,
                interaction.interaction_key,
            ),
            default=None,
        )
        reaction = None
        if latest is not None:
            if latest.interaction_action == InteractionAction.REACTION_LIKE:
                reaction = "like"
            elif (
                latest.interaction_action
                == InteractionAction.REACTION_DISLIKE
            ):
                reaction = "dislike"
            elif latest.interaction_action == InteractionAction.SET:
                reaction = (
                    "like" if latest.interaction_value == 1 else "dislike"
                )
        return UserMovieReactionResponse(
            movie_id=movie_id,
            reaction=reaction,
        )
