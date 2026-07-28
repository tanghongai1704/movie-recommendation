from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.models.user_interaction import (
    UserInteraction,
    format_interaction_timestamp,
)
from app.schemas.interaction import InteractionCreate, InteractionResponse


class InteractionRepository(Protocol):
    """Persistence boundary used by InteractionService."""

    def create(self, item: UserInteraction) -> UserInteraction:
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
            interaction_action=interaction.interaction_action,
            interaction_value=interaction.interaction_value,
            timestamp=timestamp,
            session_id=interaction.session_id,
        )
        stored = self._repository.create(record)

        return InteractionResponse.model_validate(stored.model_dump())
