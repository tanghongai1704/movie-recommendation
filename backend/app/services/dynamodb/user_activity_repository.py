from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

logger = logging.getLogger(__name__)


class UserActivityRepositoryError(Exception):
    """Raised when a user activity persistence operation fails."""


class UserActivityRepository:
    """Persist user activity events to DynamoDB.

    Each event is stored as a single item with a composite primary key that
    supports future retrieval by user and event time.
    """

    def __init__(self, table_name: str = "movie-recommendation-activity", region_name: Optional[str] = None) -> None:
        self.table_name = table_name
        self.region_name = region_name or "us-east-1"
        self._client = boto3.resource("dynamodb", region_name=self.region_name)
        self._table = self._client.Table(table_name)

    def save_event(self, user_id: int, event_type: str, movie_id: int, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Save a single user activity event to DynamoDB."""
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserActivityRepositoryError("user_id must be a positive integer")

        if not isinstance(movie_id, int) or movie_id <= 0:
            raise UserActivityRepositoryError("movie_id must be a positive integer")

        event_time = (timestamp or datetime.now(timezone.utc)).isoformat()
        item = {
            "user_id": user_id,
            "event_type": event_type,
            "movie_id": movie_id,
            "timestamp": event_time,
        }

        try:
            self._table.put_item(Item=item)
            logger.info("Saved activity event for user %s: %s", user_id, event_type)
            return item
        except NoCredentialsError as exc:
            raise UserActivityRepositoryError("AWS credentials were not found") from exc
        except PartialCredentialsError as exc:
            raise UserActivityRepositoryError("AWS credentials are incomplete") from exc
        except ClientError as exc:
            raise UserActivityRepositoryError(f"DynamoDB error: {exc}") from exc

    def list_events(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all activity events for a user."""
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserActivityRepositoryError("user_id must be a positive integer")

        try:
            response = self._table.query(KeyConditionExpression="user_id = :uid", ExpressionAttributeValues={":uid": user_id})
            return response.get("Items", [])
        except NoCredentialsError as exc:
            raise UserActivityRepositoryError("AWS credentials were not found") from exc
        except PartialCredentialsError as exc:
            raise UserActivityRepositoryError("AWS credentials are incomplete") from exc
        except ClientError as exc:
            raise UserActivityRepositoryError(f"DynamoDB error: {exc}") from exc
