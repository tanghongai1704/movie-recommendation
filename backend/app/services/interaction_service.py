from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from app.schemas.interaction import InteractionCreate, InteractionResponse


class InteractionRepository(Protocol):
    def put_item(self, item: dict[str, Any]) -> dict[str, Any]:
        ...


class InteractionService:
    """Records user behavior for downstream analytics and ML consumers."""

    def __init__(self, repository: InteractionRepository) -> None:
        self._repository = repository

    def record(
        self,
        *,
        user_id: int,
        username: str,
        interaction: InteractionCreate,
    ) -> InteractionResponse:
        event_id = f"evt_{uuid4().hex}"
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        record: dict[str, Any] = {
            "user_id": str(user_id),
            "interaction_key": f"{created_at}#{event_id}",
            "event_id": event_id,
            "username": username,
            "event_type": interaction.event_type.value,
            "movie_id": interaction.movie_id,
            "rating": interaction.rating,
            "metadata": interaction.metadata,
            "created_at": created_at,
            "schema_version": 1,
        }
        self._repository.put_item(record)

        return InteractionResponse(
            event_id=event_id,
            user_id=user_id,
            event_type=interaction.event_type,
            movie_id=interaction.movie_id,
            rating=interaction.rating,
            created_at=created_at,
        )
