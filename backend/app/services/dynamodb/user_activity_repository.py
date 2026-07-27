from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

logger = logging.getLogger(__name__)


def _to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    return value


class DynamoDBRepositoryError(Exception):
    """Raised when a DynamoDB repository operation fails."""


class BaseDynamoDBRepository:
    """Base repository for DynamoDB table access."""

    def __init__(self, table_name: str, region_name: Optional[str] = None) -> None:
        self.table_name = table_name
        self.region_name = region_name or "us-east-1"
        self._client = boto3.resource("dynamodb", region_name=self.region_name)
        self._table = self._client.Table(table_name)

    def _handle_error(self, exc: Exception) -> None:
        if isinstance(exc, NoCredentialsError):
            raise DynamoDBRepositoryError("AWS credentials were not found") from exc
        if isinstance(exc, PartialCredentialsError):
            raise DynamoDBRepositoryError("AWS credentials are incomplete") from exc
        if isinstance(exc, ClientError):
            raise DynamoDBRepositoryError(f"DynamoDB error: {exc}") from exc
        raise DynamoDBRepositoryError(str(exc)) from exc


class MoviesRepository(BaseDynamoDBRepository):
    """Repository for movie table operations."""

    def __init__(self, table_name: str = "movie-recommendation-movies", region_name: Optional[str] = None) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._table.put_item(Item=item)
            return item
        except Exception as exc:
            self._handle_error(exc)

    def get_item(self, movie_id: Any) -> Optional[Dict[str, Any]]:
        try:
            response = self._table.get_item(Key={"movie_id": movie_id})
            return response.get("Item")
        except Exception as exc:
            self._handle_error(exc)

    def list_items(self) -> List[Dict[str, Any]]:
        try:
            response = self._table.scan()
            return response.get("Items", [])
        except Exception as exc:
            self._handle_error(exc)


class UsersRepository(BaseDynamoDBRepository):
    """Repository for user table operations."""

    def __init__(self, table_name: str = "movie-recommendation-users", region_name: Optional[str] = None) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._table.put_item(Item=item)
            return item
        except Exception as exc:
            self._handle_error(exc)

    def get_item(self, user_id: Any) -> Optional[Dict[str, Any]]:
        try:
            response = self._table.get_item(Key={"user_id": user_id})
            return response.get("Item")
        except Exception as exc:
            self._handle_error(exc)


class UserInteractionsRepository(BaseDynamoDBRepository):
    """Repository for user interaction table operations."""

    def __init__(self, table_name: str = "movie-recommendation-interactions", region_name: Optional[str] = None) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._table.put_item(Item=_to_dynamodb_value(item))
            return item
        except Exception as exc:
            self._handle_error(exc)

    def list_items(self, user_id: Any) -> List[Dict[str, Any]]:
        try:
            items: List[Dict[str, Any]] = []
            query_options: Dict[str, Any] = {
                "KeyConditionExpression": Key("user_id").eq(str(user_id)),
            }

            while True:
                response = self._table.query(**query_options)
                items.extend(response.get("Items", []))

                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    return items
                query_options["ExclusiveStartKey"] = last_key
        except Exception as exc:
            self._handle_error(exc)


class PopularMoviesRepository(BaseDynamoDBRepository):
    """Repository for popular movies table operations."""

    def __init__(self, table_name: str = "movie-recommendation-popular", region_name: Optional[str] = None) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._table.put_item(Item=item)
            return item
        except Exception as exc:
            self._handle_error(exc)

    def list_items(self) -> List[Dict[str, Any]]:
        try:
            response = self._table.scan()
            return response.get("Items", [])
        except Exception as exc:
            self._handle_error(exc)


class RecommendationCacheRepository(BaseDynamoDBRepository):
    """Repository for recommendation cache table operations."""

    def __init__(self, table_name: str = "movie-recommendation-cache", region_name: Optional[str] = None) -> None:
        super().__init__(table_name=table_name, region_name=region_name)

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._table.put_item(Item=item)
            return item
        except Exception as exc:
            self._handle_error(exc)

    def get_item(self, key: Any) -> Optional[Dict[str, Any]]:
        try:
            response = self._table.get_item(Key={"cache_key": key})
            return response.get("Item")
        except Exception as exc:
            self._handle_error(exc)
