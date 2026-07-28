from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from app.models.user_interaction import UserInteraction
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
        interaction: InteractionCreate,
    ) -> InteractionResponse:
        # username remains in the method signature for route compatibility but is
        # intentionally not duplicated in the canonical interaction record.
        del username

        timestamp = datetime.now(timezone.utc)
        record = UserInteraction(
            user_id=user_id,
            interaction_key=(
                f"{timestamp.isoformat().replace('+00:00', 'Z')}"
                f"#{interaction.movie_id}"
            ),
            movie_id=interaction.movie_id,
            interaction_type=interaction.interaction_type,
            interaction_value=interaction.interaction_value,
            timestamp=timestamp,
            session_id=interaction.session_id,
        )
        self._repository.create(record)

        return InteractionResponse.model_validate(record.model_dump())
