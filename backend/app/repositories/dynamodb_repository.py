from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, NoReturn, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from pydantic import BaseModel, ValidationError

from app.models.movie import Movie
from app.models.popular_movie import PopularMovie
from app.models.recommendation_cache import RecommendationCache
from app.models.user import User
from app.models.user_interaction import UserInteraction

logger = logging.getLogger(__name__)


def _to_dynamodb_value(value: Any) -> Any:
    """Convert Python numeric values to DynamoDB-compatible values."""

    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    return value


def _serialize(model: BaseModel) -> dict[str, Any]:
    """Serialize a canonical model without introducing persistence aliases."""

    return _to_dynamodb_value(model.model_dump(mode="json"))


class DynamoDBRepositoryError(Exception):
    """Raised when a DynamoDB repository operation fails."""


class BaseDynamoDBRepository:
    """Base repository containing DynamoDB connection and error handling only."""

    def __init__(self, table_name: str, region_name: Optional[str] = None) -> None:
        self.table_name = table_name
        self.region_name = region_name or "us-east-1"
        self._client = boto3.resource("dynamodb", region_name=self.region_name)
        self._table = self._client.Table(table_name)

    def _handle_error(self, exc: Exception) -> NoReturn:
        if isinstance(exc, NoCredentialsError):
            raise DynamoDBRepositoryError("AWS credentials were not found") from exc
        if isinstance(exc, PartialCredentialsError):
            raise DynamoDBRepositoryError("AWS credentials are incomplete") from exc
        if isinstance(exc, ClientError):
            raise DynamoDBRepositoryError(f"DynamoDB error: {exc}") from exc
        raise DynamoDBRepositoryError(str(exc)) from exc

    def _scan_all(self) -> list[dict[str, Any]]:
        """Read every scan page so callers do not silently lose records."""

        items: list[dict[str, Any]] = []
        scan_options: dict[str, Any] = {}
        while True:
            response = self._table.scan(**scan_options)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            scan_options["ExclusiveStartKey"] = last_key


class MoviesRepository(BaseDynamoDBRepository):
    """DynamoDB operations for canonical Movies records."""

    def __init__(
        self,
        table_name: str = "movie-recommendation-movies",
        region_name: Optional[str] = None,
    ) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: Movie) -> Movie:
        try:
            self._table.put_item(Item=_serialize(item))
            return item
        except Exception as exc:
            self._handle_error(exc)

    def get_item(self, movie_id: str) -> Optional[Movie]:
        try:
            response = self._table.get_item(Key={"movie_id": movie_id})
            record = response.get("Item")
            return Movie.model_validate(record) if record else None
        except Exception as exc:
            self._handle_error(exc)

    def list_items(self) -> list[Movie]:
        try:
            return [Movie.model_validate(item) for item in self._scan_all()]
        except Exception as exc:
            self._handle_error(exc)


class UsersRepository(BaseDynamoDBRepository):
    """DynamoDB operations for canonical Users records."""

    def __init__(
        self,
        table_name: str = "movie-recommendation-users",
        region_name: Optional[str] = None,
    ) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: User) -> User:
        try:
            self._table.put_item(Item=_serialize(item))
            return item
        except Exception as exc:
            self._handle_error(exc)

    def get_item(self, user_id: str) -> Optional[User]:
        try:
            response = self._table.get_item(Key={"user_id": user_id})
            record = response.get("Item")
            return User.model_validate(record) if record else None
        except Exception as exc:
            self._handle_error(exc)


class UserInteractionsRepository(BaseDynamoDBRepository):
    """DynamoDB operations for canonical UserInteractions records."""

    def __init__(
        self,
        table_name: str = "movie-recommendation-interactions",
        region_name: Optional[str] = None,
    ) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: UserInteraction) -> UserInteraction:
        try:
            self._table.put_item(Item=_serialize(item))
            return item
        except Exception as exc:
            self._handle_error(exc)

    def list_items(self, user_id: str) -> list[UserInteraction]:
        try:
            items: list[dict[str, Any]] = []
            query_options: dict[str, Any] = {
                "KeyConditionExpression": Key("user_id").eq(user_id),
            }

            while True:
                response = self._table.query(**query_options)
                items.extend(response.get("Items", []))
                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    return [UserInteraction.model_validate(item) for item in items]
                query_options["ExclusiveStartKey"] = last_key
        except Exception as exc:
            self._handle_error(exc)


class PopularMoviesRepository(BaseDynamoDBRepository):
    """DynamoDB operations for canonical PopularMovies records."""

    def __init__(
        self,
        table_name: str = "movie-recommendation-popular",
        region_name: Optional[str] = None,
    ) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: PopularMovie) -> PopularMovie:
        try:
            self._table.put_item(Item=_serialize(item))
            return item
        except Exception as exc:
            self._handle_error(exc)

    def list_items(self) -> list[PopularMovie]:
        try:
            return [PopularMovie.model_validate(item) for item in self._scan_all()]
        except Exception as exc:
            self._handle_error(exc)


class RecommendationCacheRepository(BaseDynamoDBRepository):
    """DynamoDB operations for canonical RecommendationCache records."""

    def __init__(
        self,
        table_name: str = "movie-recommendation-cache",
        region_name: Optional[str] = None,
    ) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: RecommendationCache) -> RecommendationCache:
        try:
            self._table.put_item(Item=_serialize(item))
            return item
        except Exception as exc:
            self._handle_error(exc)

    def get_item(
        self,
        user_id: str,
        scenario: str,
    ) -> Optional[RecommendationCache]:
        try:
            response = self._table.get_item(
                Key={
                    "user_id": user_id,
                    "scenario": scenario,
                }
            )
            record = response.get("Item")
            if not record:
                return None
            try:
                return RecommendationCache.model_validate(record)
            except ValidationError:
                logger.warning(
                    "Ignoring a legacy or invalid recommendation cache entry",
                    extra={"user_id": user_id, "scenario": scenario},
                )
                return None
        except Exception as exc:
            self._handle_error(exc)
