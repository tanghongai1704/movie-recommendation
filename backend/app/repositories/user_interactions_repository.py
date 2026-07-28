from typing import Any, Optional

from app.models.user_interaction import UserInteraction
from app.repositories.dynamodb_base import (
    BaseDynamoDBRepository,
    DynamoDBRepositoryError,
)


class UserInteractionsRepository(BaseDynamoDBRepository):
    """CRUD persistence for the UserInteractions table."""

    def __init__(
        self,
        *,
        table_name: str,
        region_name: str,
        table: Any | None = None,
    ) -> None:
        super().__init__(
            table_name=table_name,
            region_name=region_name,
            table=table,
        )

    def create(self, interaction: UserInteraction) -> UserInteraction:
        try:
            return self._create(
                interaction,
                partition_key="user_id",
                sort_key="interaction_key",
            )
        except DynamoDBRepositoryError as exc:
            if not self._is_conditional_conflict(exc):
                raise
            existing = self.get(
                interaction.user_id,
                interaction.interaction_key,
            )
            if existing != interaction:
                raise
            return existing

    def get(
        self,
        user_id: str,
        interaction_key: str,
    ) -> Optional[UserInteraction]:
        return self._get(
            key={
                "user_id": user_id,
                "interaction_key": interaction_key,
            },
            model_type=UserInteraction,
        )

    def list_by_user(self, user_id: str) -> list[UserInteraction]:
        return self._query_by_partition_key(
            partition_key="user_id",
            partition_value=user_id,
            model_type=UserInteraction,
        )

    def update(self, interaction: UserInteraction) -> UserInteraction:
        return self._update(
            interaction,
            partition_key="user_id",
            sort_key="interaction_key",
        )

    def delete(self, user_id: str, interaction_key: str) -> bool:
        return self._delete(
            key={
                "user_id": user_id,
                "interaction_key": interaction_key,
            }
        )

    @staticmethod
    def _is_conditional_conflict(exc: DynamoDBRepositoryError) -> bool:
        cause = exc.__cause__
        response = getattr(cause, "response", {})
        error = response.get("Error", {}) if isinstance(response, dict) else {}
        return error.get("Code") == "ConditionalCheckFailedException"
