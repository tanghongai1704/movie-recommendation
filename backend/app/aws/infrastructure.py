from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import boto3
from botocore.config import Config as BotocoreConfig

from app.core.config import Settings
from app.core.config_validation import ConfigurationError


class AWSResourceValidationError(ConfigurationError):
    """Raised when configured AWS resources cannot be used safely."""


@dataclass(frozen=True)
class AWSClients:
    dynamodb_resource: Any
    s3_client: Any
    sagemaker_client: Any | None
    sagemaker_runtime_client: Any | None


def create_aws_clients(settings: Settings) -> AWSClients:
    """Create configured SDK clients once for application-wide reuse."""

    client_config = BotocoreConfig(
        connect_timeout=settings.aws.connect_timeout_seconds,
        read_timeout=settings.aws.read_timeout_seconds,
        retries={
            "max_attempts": settings.aws.max_attempts,
            "mode": settings.aws.retry_mode,
        },
    )
    common = {
        "region_name": settings.aws.region,
        "endpoint_url": settings.aws.endpoint_url,
        "config": client_config,
    }
    dynamodb_resource = boto3.resource("dynamodb", **common)
    s3_client = boto3.client("s3", **common)
    sagemaker_client = (
        boto3.client("sagemaker", **common)
        if settings.sagemaker.enabled
        else None
    )
    sagemaker_runtime_client = (
        boto3.client("sagemaker-runtime", **common)
        if settings.sagemaker.enabled
        else None
    )
    clients = AWSClients(
        dynamodb_resource=dynamodb_resource,
        s3_client=s3_client,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=sagemaker_runtime_client,
    )
    if settings.aws.validate_resources:
        validate_aws_resources(settings=settings, clients=clients)
    return clients


def validate_aws_resources(
    *,
    settings: Settings,
    clients: AWSClients,
) -> None:
    """Fail startup if credentials, tables, keys, bucket or endpoint differ."""

    try:
        sts = boto3.client(
            "sts",
            region_name=settings.aws.region,
            endpoint_url=settings.aws.endpoint_url,
        )
        sts.get_caller_identity()

        dynamodb_client = clients.dynamodb_resource.meta.client
        expected_tables = {
            settings.dynamodb.movies_table: (("movie_id", "HASH"),),
            settings.dynamodb.popular_table: (("list_id", "HASH"),),
            settings.dynamodb.users_table: (("user_id", "HASH"),),
            settings.dynamodb.interactions_table: (
                ("user_id", "HASH"),
                ("interaction_key", "RANGE"),
            ),
            settings.dynamodb.recommendation_cache_table: (
                ("user_id", "HASH"),
                ("scenario", "RANGE"),
            ),
        }
        for table_name, expected_keys in expected_tables.items():
            table = dynamodb_client.describe_table(TableName=table_name)[
                "Table"
            ]
            if table.get("TableStatus") != "ACTIVE":
                raise AWSResourceValidationError(
                    f"DynamoDB table is not ACTIVE: {table_name}"
                )
            actual_keys = tuple(
                (item["AttributeName"], item["KeyType"])
                for item in table.get("KeySchema", [])
            )
            if actual_keys != expected_keys:
                raise AWSResourceValidationError(
                    "DynamoDB key schema mismatch for "
                    f"{table_name}: expected {expected_keys}, got {actual_keys}"
                )

        clients.s3_client.head_bucket(Bucket=settings.s3.bucket)
        for prefix in (
            settings.s3.dataset_prefix,
            settings.s3.raw_prefix,
            settings.s3.processed_prefix,
            settings.s3.features_prefix,
            settings.s3.serving_prefix,
            settings.s3.training_prefix,
            settings.s3.model_prefix,
            settings.s3.output_prefix,
            settings.s3.interaction_export_prefix,
        ):
            clients.s3_client.list_objects_v2(
                Bucket=settings.s3.bucket,
                Prefix=prefix,
                MaxKeys=1,
            )

        if settings.sagemaker.enabled:
            if clients.sagemaker_client is None:
                raise AWSResourceValidationError(
                    "SageMaker client was not initialized"
                )
            endpoint = clients.sagemaker_client.describe_endpoint(
                EndpointName=settings.sagemaker.endpoint_name
            )
            if endpoint.get("EndpointStatus") != "InService":
                raise AWSResourceValidationError(
                    "Configured SageMaker endpoint is not InService"
                )
    except AWSResourceValidationError:
        raise
    except Exception as exc:
        raise AWSResourceValidationError(
            "AWS startup validation failed. Verify identity, Region, IAM "
            "permissions, DynamoDB tables, S3 bucket, and SageMaker settings."
        ) from exc
