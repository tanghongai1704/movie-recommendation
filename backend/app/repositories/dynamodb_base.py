from __future__ import annotations

from decimal import Decimal
from typing import Any, NoReturn, Optional, TypeVar

from pydantic import BaseModel

DomainModel = TypeVar("DomainModel", bound=BaseModel)


def _to_dynamodb_value(value: Any) -> Any:
    """Convert Python numeric values to DynamoDB-compatible values."""

    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    return value


def serialize_model(model: BaseModel) -> dict[str, Any]:
    """Serialize one domain model using its canonical persistence field names."""

    return _to_dynamodb_value(model.model_dump(mode="json"))


class DynamoDBRepositoryError(Exception):
    """Raised when a DynamoDB persistence operation fails."""


class BaseDynamoDBRepository:
    """Shared DynamoDB mechanics with no entity or business-specific behavior."""

    def __init__(
        self,
        *,
        table_name: str,
        region_name: str,
        table: Any | None = None,
    ) -> None:
        if not table_name.strip():
            raise ValueError("table_name must be provided by configuration")
        if not region_name.strip():
            raise ValueError("region_name must be provided by configuration")

        self.table_name = table_name
        self.region_name = region_name
        if table is None:
            import boto3

            resource = boto3.resource("dynamodb", region_name=region_name)
            table = resource.Table(table_name)
        self._table = table

    def _handle_error(self, exc: Exception) -> NoReturn:
        try:
            from botocore.exceptions import (
                ClientError,
                NoCredentialsError,
                PartialCredentialsError,
            )
        except ModuleNotFoundError:
            raise DynamoDBRepositoryError(str(exc)) from exc

        if isinstance(exc, NoCredentialsError):
            raise DynamoDBRepositoryError("AWS credentials were not found") from exc
        if isinstance(exc, PartialCredentialsError):
            raise DynamoDBRepositoryError("AWS credentials are incomplete") from exc
        if isinstance(exc, ClientError):
            raise DynamoDBRepositoryError(f"DynamoDB error: {exc}") from exc
        raise DynamoDBRepositoryError(str(exc)) from exc

    def _create(
        self,
        model: DomainModel,
        *,
        partition_key: str,
        sort_key: str | None = None,
    ) -> DomainModel:
        expression_names = {"#pk": partition_key}
        conditions = ["attribute_not_exists(#pk)"]
        if sort_key is not None:
            expression_names["#sk"] = sort_key
            conditions.append("attribute_not_exists(#sk)")

        try:
            self._table.put_item(
                Item=serialize_model(model),
                ConditionExpression=" AND ".join(conditions),
                ExpressionAttributeNames=expression_names,
            )
            return model
        except Exception as exc:
            self._handle_error(exc)

    def _update(
        self,
        model: DomainModel,
        *,
        partition_key: str,
        sort_key: str | None = None,
    ) -> DomainModel:
        expression_names = {"#pk": partition_key}
        conditions = ["attribute_exists(#pk)"]
        if sort_key is not None:
            expression_names["#sk"] = sort_key
            conditions.append("attribute_exists(#sk)")

        try:
            self._table.put_item(
                Item=serialize_model(model),
                ConditionExpression=" AND ".join(conditions),
                ExpressionAttributeNames=expression_names,
            )
            return model
        except Exception as exc:
            self._handle_error(exc)

    def _upsert(self, model: DomainModel) -> DomainModel:
        try:
            self._table.put_item(Item=serialize_model(model))
            return model
        except Exception as exc:
            self._handle_error(exc)

    def _get(
        self,
        *,
        key: dict[str, Any],
        model_type: type[DomainModel],
    ) -> Optional[DomainModel]:
        try:
            response = self._table.get_item(Key=key)
            item = response.get("Item")
            return model_type.model_validate(item) if item else None
        except Exception as exc:
            self._handle_error(exc)

    def _delete(self, *, key: dict[str, Any]) -> bool:
        try:
            response = self._table.delete_item(
                Key=key,
                ReturnValues="ALL_OLD",
            )
            return bool(response.get("Attributes"))
        except Exception as exc:
            self._handle_error(exc)

    def _scan_all(
        self,
        *,
        model_type: type[DomainModel],
        limit: int | None = None,
    ) -> list[DomainModel]:
        if limit is not None and limit <= 0:
            raise ValueError("scan limit must be a positive integer")

        try:
            records: list[DomainModel] = []
            scan_options: dict[str, Any] = {}
            while True:
                if limit is not None:
                    scan_options["Limit"] = limit - len(records)
                response = self._table.scan(**scan_options)
                records.extend(
                    model_type.model_validate(item)
                    for item in response.get("Items", [])
                )
                if limit is not None and len(records) >= limit:
                    return records[:limit]
                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    return records
                scan_options["ExclusiveStartKey"] = last_key
        except Exception as exc:
            self._handle_error(exc)

    def _query_by_partition_key(
        self,
        *,
        partition_key: str,
        partition_value: str,
        model_type: type[DomainModel],
    ) -> list[DomainModel]:
        try:
            records: list[DomainModel] = []
            query_options: dict[str, Any] = {
                "KeyConditionExpression": "#pk = :pk",
                "ExpressionAttributeNames": {"#pk": partition_key},
                "ExpressionAttributeValues": {":pk": partition_value},
            }
            while True:
                response = self._table.query(**query_options)
                records.extend(
                    model_type.model_validate(item)
                    for item in response.get("Items", [])
                )
                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    return records
                query_options["ExclusiveStartKey"] = last_key
        except Exception as exc:
            self._handle_error(exc)
