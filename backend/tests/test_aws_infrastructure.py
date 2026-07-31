import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.aws.infrastructure import (
    AWSClients,
    AWSResourceValidationError,
    create_aws_session,
    validate_aws_resources,
)


class FakeSTSClient:
    def get_caller_identity(self) -> dict[str, str]:
        return {"Arn": "test"}


class FakeDynamoDBClient:
    KEY_SCHEMAS = {
        "Movies": [("movie_id", "HASH")],
        "PopularMovies": [("list_id", "HASH")],
        "Users": [("user_id", "HASH")],
        "UserInteractions": [
            ("user_id", "HASH"),
            ("interaction_key", "RANGE"),
        ],
        "RecommendationCache": [
            ("user_id", "HASH"),
            ("scenario", "RANGE"),
        ],
    }

    def describe_table(self, *, TableName: str) -> dict[str, object]:
        return {
            "Table": {
                "TableStatus": "ACTIVE",
                "KeySchema": [
                    {"AttributeName": name, "KeyType": key_type}
                    for name, key_type in self.KEY_SCHEMAS[TableName]
                ],
            }
        }


class FakeS3Client:
    def __init__(self) -> None:
        self.head_calls = 0
        self.prefixes: list[str] = []

    def head_bucket(self, *, Bucket: str) -> None:
        del Bucket
        self.head_calls += 1

    def list_objects_v2(
        self,
        *,
        Bucket: str,
        Prefix: str,
        MaxKeys: int,
    ) -> dict[str, object]:
        del Bucket, MaxKeys
        self.prefixes.append(Prefix)
        return {}


class UnavailableSageMakerClient:
    def describe_endpoint(self, *, EndpointName: str) -> dict[str, str]:
        del EndpointName
        raise RuntimeError("endpoint is intentionally stopped")


def test_settings() -> SimpleNamespace:
    return SimpleNamespace(
        aws=SimpleNamespace(
            region="ap-southeast-1",
            endpoint_url=None,
            connect_timeout_seconds=3,
            read_timeout_seconds=10,
            max_attempts=3,
            retry_mode="standard",
        ),
        dynamodb=SimpleNamespace(
            movies_table="Movies",
            popular_table="PopularMovies",
            users_table="Users",
            interactions_table="UserInteractions",
            recommendation_cache_table="RecommendationCache",
        ),
        s3=SimpleNamespace(
            bucket="bucket",
            dataset_prefix="app/data/",
            raw_prefix="app/data/raw/",
            processed_prefix="app/data/processed/",
            serving_prefix="app/data/serving/",
            training_prefix="app/data/training/",
            model_prefix="app/models/",
            output_prefix="app/outputs/",
            interaction_export_prefix="app/events/",
        ),
        sagemaker=SimpleNamespace(enabled=False, endpoint_name=None),
    )


class AWSInfrastructureTests(unittest.TestCase):
    def make_clients(
        self,
        *,
        sagemaker_client: object | None = None,
    ) -> tuple[AWSClients, FakeS3Client]:
        dynamodb_client = FakeDynamoDBClient()
        s3_client = FakeS3Client()
        return (
            AWSClients(
                dynamodb_resource=SimpleNamespace(
                    meta=SimpleNamespace(client=dynamodb_client)
                ),
                s3_client=s3_client,
                sagemaker_client=sagemaker_client,
                sagemaker_runtime_client=None,
                sts_client=FakeSTSClient(),
            ),
            s3_client,
        )

    def test_validates_identity_tables_keys_bucket_and_prefix_access(self) -> None:
        clients, s3_client = self.make_clients()

        validate_aws_resources(
            settings=test_settings(),
            clients=clients,
        )

        self.assertEqual(s3_client.head_calls, 1)
        self.assertEqual(len(s3_client.prefixes), 8)

    def test_rejects_deployed_key_schema_mismatch(self) -> None:
        clients, _ = self.make_clients()
        clients.dynamodb_resource.meta.client.KEY_SCHEMAS["Movies"] = [
            ("id", "HASH")
        ]
        try:
            with self.assertRaisesRegex(
                AWSResourceValidationError,
                "key schema mismatch",
            ):
                validate_aws_resources(
                    settings=test_settings(),
                    clients=clients,
                )
        finally:
            clients.dynamodb_resource.meta.client.KEY_SCHEMAS["Movies"] = [
                ("movie_id", "HASH")
            ]

    def test_unavailable_sagemaker_does_not_block_core_startup(self) -> None:
        settings = test_settings()
        settings.sagemaker.enabled = True
        settings.sagemaker.endpoint_name = "movie-rec-endpoint"
        clients, _ = self.make_clients(
            sagemaker_client=UnavailableSageMakerClient()
        )

        with self.assertLogs("movie_recommendation.aws", level="WARNING"):
            validate_aws_resources(settings=settings, clients=clients)

    def test_session_uses_region_and_default_credential_chain(self) -> None:
        settings = test_settings()

        with patch("app.aws.infrastructure.boto3.Session") as session:
            create_aws_session(settings)

        session.assert_called_once_with(region_name="ap-southeast-1")


if __name__ == "__main__":
    unittest.main()
