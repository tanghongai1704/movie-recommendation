"""Describe or invoke the configured SageMaker recommendation endpoint.

Examples:
    python scripts/test_sagemaker_endpoint.py --describe
    python scripts/test_sagemaker_endpoint.py --invoke \
        --scenario onboarding_user --genre Action --genre Drama
    python scripts/test_sagemaker_endpoint.py --invoke \
        --scenario returning_user --request-file request.json
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import sys
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT.parent / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)

from app.aws.infrastructure import create_aws_clients
from app.core.config import settings
from app.schemas.sagemaker import SageMakerRecommendationRequest
from app.services.sagemaker_recommendation_provider import (
    SageMakerRecommendationProvider,
)
from app.services.recommendation_provider import RecommendationProviderError


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--describe", action="store_true")
    action.add_argument("--invoke", action="store_true")
    parser.add_argument(
        "--scenario",
        choices=("onboarding_user", "returning_user"),
        default="onboarding_user",
    )
    parser.add_argument("--user-id", type=int, default=999_999_999)
    parser.add_argument("--genre", action="append", default=[])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--request-file",
        type=Path,
        help="Optional exact RecommendationEngine JSON request.",
    )
    return parser.parse_args()


def load_request(arguments: argparse.Namespace) -> SageMakerRecommendationRequest:
    if arguments.request_file:
        payload = json.loads(
            arguments.request_file.read_text(encoding="utf-8")
        )
        return SageMakerRecommendationRequest.model_validate(payload)
    return SageMakerRecommendationRequest(
        user_id=arguments.user_id,
        scenario_hint=arguments.scenario,
        onboarding_completed=True,
        valid_interaction_count_90d=(
            5 if arguments.scenario == "returning_user" else 0
        ),
        selected_movie_ids=[],
        selected_genres=arguments.genre,
        recent_interactions=[],
        exclude_movie_ids=[],
        limit=arguments.limit,
    )


def main() -> int:
    arguments = parse_arguments()
    # This command diagnoses SageMaker only. Do not make it validate all
    # DynamoDB tables and S3 prefixes before it can report endpoint status.
    diagnostic_settings = replace(
        settings,
        aws=replace(settings.aws, validate_resources=False),
    )
    clients = create_aws_clients(diagnostic_settings)
    endpoint_name = settings.sagemaker.endpoint_name
    if not endpoint_name:
        raise SystemExit("AWS_SAGEMAKER_ENDPOINT_NAME is not configured")

    if arguments.describe:
        if clients.sagemaker_client is None:
            raise SystemExit(
                "Set AWS_SAGEMAKER_ENABLED=True before describing the endpoint"
            )
        try:
            response = clients.sagemaker_client.describe_endpoint(
                EndpointName=endpoint_name
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "ClientError")
            print(
                f"DescribeEndpoint failed: {code}. Verify endpoint name, "
                "AWS Region, IAM permission, and endpoint lifecycle.",
                file=sys.stderr,
            )
            return 2
        except BotoCoreError as exc:
            print(
                "DescribeEndpoint failed: "
                f"{type(exc).__name__}. Verify the AWS credential chain.",
                file=sys.stderr,
            )
            return 2
        print(
            json.dumps(
                {
                    "endpoint_name": endpoint_name,
                    "status": response.get("EndpointStatus"),
                    "endpoint_config": response.get("EndpointConfigName"),
                    "failure_reason": response.get("FailureReason"),
                },
                indent=2,
            )
        )
        return 0

    provider = SageMakerRecommendationProvider(
        runtime_client=clients.sagemaker_runtime_client,
        control_client=clients.sagemaker_client,
        endpoint_name=endpoint_name,
        recommendation_limit=settings.sagemaker.recommendation_limit,
        content_type=settings.sagemaker.content_type,
        accept=settings.sagemaker.accept,
        fallback_model_version=settings.cache.model_version,
        enabled=settings.sagemaker.enabled,
    )
    try:
        response = provider.invoke_endpoint(load_request(arguments))
    except RecommendationProviderError as exc:
        print(
            f"InvokeEndpoint failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    print(response.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
