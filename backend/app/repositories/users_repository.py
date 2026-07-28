from typing import Any, Optional

from app.models.user import User
from app.repositories.dynamodb_base import BaseDynamoDBRepository


class UsersRepository(BaseDynamoDBRepository):
    """CRUD persistence for the Users table."""

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

    def create(self, user: User) -> User:
        return self._create(user, partition_key="user_id")

    def get(self, user_id: str) -> Optional[User]:
        return self._get(
            key={"user_id": user_id},
            model_type=User,
        )

    def list_all(self) -> list[User]:
        return self._scan_all(model_type=User)

    def update(self, user: User) -> User:
        return self._update(user, partition_key="user_id")

    def delete(self, user_id: str) -> bool:
        return self._delete(key={"user_id": user_id})
