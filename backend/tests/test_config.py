import os
import unittest
from unittest.mock import patch

from app.core.config import Settings
from app.core.config_validation import ConfigurationError


class ConfigurationTests(unittest.TestCase):
    def canonical_environment(self) -> dict[str, str]:
        return {
            "JWT_SECRET_KEY": "x" * 32,
            "AWS_REGION": "ap-southeast-1",
            "AWS_VALIDATE_CREDENTIALS": "False",
            "AWS_VALIDATE_RESOURCES": "False",
            "AWS_DYNAMODB_MOVIES_TABLE": "Movies",
            "AWS_DYNAMODB_POPULAR_TABLE": "PopularMovies",
            "AWS_DYNAMODB_USERS_TABLE": "Users",
            "AWS_DYNAMODB_INTERACTIONS_TABLE": "UserInteractions",
            "AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE": (
                "RecommendationCache"
            ),
            "AWS_DYNAMODB_POPULAR_LIST_ID": "top_rated_all",
            "AWS_S3_BUCKET": "movie-recommendation-test",
            "AWS_S3_DATASET_PREFIX": "datasets/",
            "AWS_S3_RAW_PREFIX": "datasets/raw/",
            "AWS_S3_PROCESSED_PREFIX": "datasets/processed/",
            "AWS_S3_SERVING_PREFIX": "inference/",
            "AWS_S3_TRAINING_PREFIX": "training/",
            "AWS_S3_MODEL_PREFIX": "models/",
            "AWS_S3_OUTPUT_PREFIX": "evaluation/",
            "AWS_S3_INTERACTION_EXPORT_PREFIX": "datasets/exports/",
        }

    def test_loads_canonical_configuration_sections(self) -> None:
        environment = self.canonical_environment()
        environment.update(
            {
                "API_PREFIX": "/service/v1",
                "CORS_ALLOWED_ORIGINS": (
                    "https://app.example.com,https://admin.example.com"
                ),
                "AWS_S3_MODEL_PREFIX": "/models/current",
                "AWS_ENDPOINT_URL": "http://localhost:4566/",
                "RECOMMENDATION_CACHE_TTL_SECONDS": "600",
            }
        )

        with patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_environment()

        self.assertEqual(settings.api.prefix, "/service/v1")
        self.assertEqual(
            settings.api.cors_allowed_origins,
            ("https://app.example.com", "https://admin.example.com"),
        )
        self.assertEqual(settings.aws.endpoint_url, "http://localhost:4566")
        self.assertEqual(settings.s3.model_prefix, "models/current/")
        self.assertEqual(settings.s3.raw_prefix, "datasets/raw/")
        self.assertEqual(settings.cache.ttl_seconds, 600)
        self.assertEqual(settings.authentication.algorithm, "HS256")

    def test_blank_aws_placeholders_use_default_credential_chain(self) -> None:
        environment = self.canonical_environment()
        environment.update(
            {
                "AWS_ACCESS_KEY_ID": "",
                "AWS_SECRET_ACCESS_KEY": "",
                "AWS_SESSION_TOKEN": "",
                "AWS_ENDPOINT_URL": "",
                "AWS_VALIDATE_CREDENTIALS": "True",
            }
        )

        with patch("boto3.Session") as session:
            session.return_value.get_credentials.return_value = object()
            with patch.dict(os.environ, environment, clear=True):
                settings = Settings.from_environment()
                self.assertNotIn("AWS_ACCESS_KEY_ID", os.environ)
                self.assertNotIn("AWS_SECRET_ACCESS_KEY", os.environ)
                self.assertNotIn("AWS_SESSION_TOKEN", os.environ)
                self.assertNotIn("AWS_ENDPOINT_URL", os.environ)

        self.assertIsNone(settings.aws.endpoint_url)

    def test_supports_legacy_environment_names_during_migration(self) -> None:
        environment = {
            "JWT_SECRET": "y" * 32,
            "AWS_REGION": "ap-southeast-1",
            "AWS_VALIDATE_CREDENTIALS": "False",
            "AWS_VALIDATE_RESOURCES": "False",
            "AWS_DYNAMODB_TABLE_MOVIES": "Movies",
            "AWS_DYNAMODB_TABLE_POPULAR": "PopularMovies",
            "AWS_DYNAMODB_TABLE_USERS": "Users",
            "AWS_DYNAMODB_TABLE_INTERACTIONS": "UserInteractions",
            "AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE": (
                "RecommendationCache"
            ),
            "AWS_DYNAMODB_POPULAR_LIST_ID": "top_rated_all",
            "AWS_S3_BUCKET": "movie-recommendation-test",
            "AWS_S3_DATASET_PREFIX": "datasets/",
            "AWS_S3_RAW_PREFIX": "datasets/raw/",
            "AWS_S3_PROCESSED_PREFIX": "datasets/processed/",
            "AWS_S3_SERVING_PREFIX": "inference/",
            "AWS_S3_TRAINING_PREFIX": "training/",
            "AWS_S3_MODEL_PREFIX": "models/",
            "AWS_S3_OUTPUT_PREFIX": "evaluation/",
            "AWS_S3_INTERACTION_EXPORT_PREFIX": "datasets/exports/",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_environment()

        self.assertEqual(settings.authentication.secret_key, "y" * 32)
        self.assertEqual(settings.dynamodb.movies_table, "Movies")
        self.assertEqual(
            settings.dynamodb.recommendation_cache_table,
            "RecommendationCache",
        )

    def test_rejects_conflicting_primary_and_legacy_names(self) -> None:
        environment = self.canonical_environment()
        environment["AWS_DYNAMODB_TABLE_MOVIES"] = "DifferentMovies"

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(
                ConfigurationError,
                "Conflicting environment variables",
            ):
                Settings.from_environment()

    def test_rejects_missing_required_configuration(self) -> None:
        environment = self.canonical_environment()
        del environment["AWS_S3_BUCKET"]

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(
                ConfigurationError,
                "AWS_S3_BUCKET",
            ):
                Settings.from_environment()

    def test_rejects_invalid_api_and_aws_values(self) -> None:
        cases = [
            ("API_PREFIX", "api/v1", "must start"),
            ("AWS_REGION", "singapore", "valid AWS region"),
            ("AWS_ENDPOINT_URL", "localhost:4566", "HTTP"),
            ("JWT_ALGORITHM", "RS256", "must be HS256"),
            ("AWS_RETRY_MODE", "forever", "legacy, standard, or adaptive"),
            ("CORS_ALLOWED_ORIGINS", "example.com", "HTTP"),
            (
                "CORS_ALLOWED_ORIGINS",
                "*,https://example.com",
                "cannot combine",
            ),
            (
                "AWS_ACCESS_KEY_ID",
                "incomplete-key",
                "must be set together",
            ),
        ]

        for name, value, message in cases:
            with self.subTest(name=name):
                environment = self.canonical_environment()
                environment[name] = value
                with patch.dict(os.environ, environment, clear=True):
                    with self.assertRaisesRegex(
                        ConfigurationError,
                        message,
                    ):
                        Settings.from_environment()

    def test_rejects_incomplete_explicit_aws_credentials(self) -> None:
        environment = self.canonical_environment()
        environment.update(
            {
                "AWS_ACCESS_KEY_ID": "A" * 20,
                "AWS_SECRET_ACCESS_KEY": "short-secret",
            }
        )

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(
                ConfigurationError,
                "complete 40-character",
            ):
                Settings.from_environment()

    def test_sagemaker_endpoint_is_required_only_when_enabled(self) -> None:
        environment = self.canonical_environment()
        environment["AWS_SAGEMAKER_ENABLED"] = "True"

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(
                ConfigurationError,
                "AWS_SAGEMAKER_ENDPOINT_NAME",
            ):
                Settings.from_environment()

    def test_endpoint_name_enables_sagemaker_for_existing_env_files(self) -> None:
        environment = self.canonical_environment()
        environment["AWS_SAGEMAKER_ENDPOINT_NAME"] = "movie-rec-endpoint"

        with patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_environment()

        self.assertTrue(settings.sagemaker.enabled)
        self.assertEqual(
            settings.sagemaker.endpoint_name,
            "movie-rec-endpoint",
        )


if __name__ == "__main__":
    unittest.main()
