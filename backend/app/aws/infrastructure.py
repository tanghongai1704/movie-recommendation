from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import boto3
from botocore.config import Config as BotocoreConfig

from app.core.config import Settings
from app.core.config_validation import ConfigurationError

logger = logging.getLogger("movie_recommendation.aws")


class AWSResourceValidationError(ConfigurationError):
    """Raised when configured AWS resources cannot be used safely."""


@dataclass(frozen=True)
class AWSClients:
    dynamodb_resource: Any
    s3_client: Any
    sagemaker_client: Any | None
    sagemaker_runtime_client: Any | None
    sts_client: Any | None = None


def create_aws_session(settings: Settings) -> Any:
    """Create one boto3 Session using profile or the default provider chain."""

    session_options: dict[str, Any] = {
        "region_name": settings.aws.region,
    }
    if settings.aws.profile:
        session_options["profile_name"] = settings.aws.profile
    return boto3.Session(**session_options)


def create_aws_clients(
    settings: Settings,
    *,
    session: Any | None = None,
) -> AWSClients:
    """Create configured SDK clients once for application-wide reuse."""

    client_config = BotocoreConfig(
        connect_timeout=settings.aws.connect_timeout_seconds,
        read_timeout=settings.aws.read_timeout_seconds,
        retries={
            "max_attempts": settings.aws.max_attempts,
            "mode": settings.aws.retry_mode,
        },
    )
    session = session or create_aws_session(settings)
    common: dict[str, Any] = {"config": client_config}
    if settings.aws.endpoint_url:
        common["endpoint_url"] = settings.aws.endpoint_url

    dynamodb_resource = session.resource("dynamodb", **common)
    s3_client = session.client("s3", **common)
    sagemaker_client = (
        session.client("sagemaker", **common)
        if settings.sagemaker.enabled
        else None
    )
    sagemaker_runtime_client = (
        session.client("sagemaker-runtime", **common)
        if settings.sagemaker.enabled
        else None
    )
    sts_client = session.client("sts", **common)
    clients = AWSClients(
        dynamodb_resource=dynamodb_resource,
        s3_client=s3_client,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=sagemaker_runtime_client,
        sts_client=sts_client,
    )
    if settings.aws.validate_resources:
        validate_aws_resources(settings=settings, clients=clients)
    return clients


def validate_aws_resources(
    *,
    settings: Settings,
    clients: AWSClients,
) -> None:
    """Validate required data stores; report SageMaker as optional health."""

    try:
        sts = clients.sts_client
        if sts is None:
            session = create_aws_session(settings)
            options = (
                {"endpoint_url": settings.aws.endpoint_url}
                if settings.aws.endpoint_url
                else {}
            )
            sts = session.client("sts", **options)
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

    except AWSResourceValidationError:
        raise
    except Exception as exc:
        raise AWSResourceValidationError(
            "AWS startup validation failed. Verify identity, Region, IAM "
            "permissions, DynamoDB tables, and S3 settings."
        ) from exc

    # Personalized inference is deliberately allowed to be stopped between
    # demos/training runs. It must not take guest browsing or core APIs down.
    if settings.sagemaker.enabled:
        try:
            if clients.sagemaker_client is None:
                raise AWSResourceValidationError(
                    "SageMaker client was not initialized"
                )
            endpoint = clients.sagemaker_client.describe_endpoint(
                EndpointName=settings.sagemaker.endpoint_name
            )
            status = str(endpoint.get("EndpointStatus", "Unknown"))
            if status != "InService":
                logger.warning(
                    "SageMaker endpoint is not ready endpoint=%s status=%s",
                    settings.sagemaker.endpoint_name,
                    status,
                )
        except Exception as exc:
            logger.warning(
                "SageMaker startup health check failed endpoint=%s "
                "error_type=%s; personalized requests will return a "
                "controlled error until the endpoint is available",
                settings.sagemaker.endpoint_name or "unconfigured",
                type(exc).__name__,
            )
