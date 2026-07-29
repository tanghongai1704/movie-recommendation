import json
import unittest
from typing import Any

from botocore.exceptions import ClientError, NoCredentialsError, ReadTimeoutError

from app.schemas.sagemaker import SageMakerRecommendationRequest
from app.services.recommendation_provider import (
    RecommendationProviderResponseError,
    RecommendationProviderTimeoutError,
    RecommendationProviderUnavailableError,
)
from app.services.sagemaker_recommendation_provider import (
    SageMakerRecommendationProvider,
)

class FakeBody:
    def __init__(self, value: bytes) -> None:
        self.value = value

    def read(self) -> bytes:
        return self.value


class FakeRuntimeClient:
    def __init__(
        self,
        payload: Any | None = None,
        error: Exception | None = None,
    ) -> None:
        self.payload = payload
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def invoke_endpoint(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        body = (
            self.payload
            if isinstance(self.payload, bytes)
            else json.dumps(self.payload).encode("utf-8")
        )
        return {
            "Body": FakeBody(body),
            "ResponseMetadata": {
                "HTTPStatusCode": 200,
                "RequestId": "request-1",
            },
        }


class FakeControlClient:
    def describe_endpoint(self, *, EndpointName: str) -> dict[str, str]:
        del EndpointName
        return {"EndpointStatus": "InService"}


class FailingControlClient:
    def describe_endpoint(self, *, EndpointName: str) -> dict[str, str]:
        del EndpointName
        raise ClientError(
            {"Error": {"Code": "ValidationException", "Message": "missing"}},
            "DescribeEndpoint",
        )


def recommendation_request() -> SageMakerRecommendationRequest:
    return SageMakerRecommendationRequest(
        user_id=42,
        scenario_hint="returning_user",
        onboarding_completed=True,
        valid_interaction_count_90d=5,
        selected_movie_ids=[],
        selected_genres=["Drama"],
        recent_interactions=[
            {
                "movie_id": 278,
                "event_type": "rating",
                "value": 4.5,
                "timestamp": "2026-07-29T10:00:00Z",
            }
        ],
        exclude_movie_ids=[],
        limit=10,
    )


def native_response() -> dict[str, Any]:
    return {
        "model_name": "hybrid_recommender",
        "model_version": "1.0.0",
        "scenario_applied": "returning_user",
        "recommendations": [
            {
                "movie_id": 278,
                "score": 0.95,
                "reason_code": "similar_users",
                "reason_context": {},
            },
            {
                "movie_id": 550,
                "score": 0.87,
                "reason_code": "similar_to_watched_movies",
                "reason_context": {"source_movie_id": "278"},
            },
        ],
    }


class SageMakerRecommendationProviderTests(unittest.TestCase):
    def make_provider(
        self,
        *,
        runtime: FakeRuntimeClient | None = None,
        enabled: bool = True,
    ) -> SageMakerRecommendationProvider:
        return SageMakerRecommendationProvider(
            runtime_client=runtime or FakeRuntimeClient(native_response()),
            control_client=FakeControlClient(),
            endpoint_name="movie-rec-endpoint",
            recommendation_limit=10,
            content_type="application/json",
            accept="application/json",
            fallback_model_version="endpoint-unversioned",
            enabled=enabled,
        )

    def test_invokes_runtime_with_exact_endpoint_and_payload(self) -> None:
        runtime = FakeRuntimeClient(native_response())
        provider = self.make_provider(runtime=runtime)

        result = provider.get_recommendations(recommendation_request())

        call = runtime.calls[0]
        self.assertEqual(call["EndpointName"], "movie-rec-endpoint")
        self.assertEqual(call["ContentType"], "application/json")
        self.assertEqual(call["Accept"], "application/json")
        payload = json.loads(call["Body"].decode("utf-8"))
        self.assertEqual(payload["scenario_hint"], "returning_user")
        self.assertEqual(payload["recent_interactions"][0]["event_type"], "rating")
        self.assertEqual(
            [item.movie_id for item in result.items],
            ["278", "550"],
        )
        self.assertEqual(result.model_version, "1.0.0")

    def test_parses_parallel_movie_id_and_score_arrays(self) -> None:
        runtime = FakeRuntimeClient(
            {
                "movie_ids": [278, 550],
                "scores": [0.9, 0.8],
                "model_version": "array-v1",
            }
        )
        provider = self.make_provider(runtime=runtime)

        result = provider.get_recommendations(recommendation_request())

        self.assertEqual(result.model_version, "array-v1")
        self.assertEqual(
            [item.reason_code for item in result.items],
            ["personalized", "personalized"],
        )

    def test_empty_or_invalid_json_response_is_rejected(self) -> None:
        for payload in (b"", b"{invalid"):
            with self.subTest(payload=payload):
                provider = self.make_provider(
                    runtime=FakeRuntimeClient(payload)
                )
                with self.assertRaises(
                    RecommendationProviderResponseError
                ):
                    provider.get_recommendations(
                        recommendation_request()
                    )

    def test_empty_recommendation_list_is_rejected(self) -> None:
        provider = self.make_provider(
            runtime=FakeRuntimeClient(
                {
                    "model_version": "1.0.0",
                    "scenario_applied": "returning_user",
                    "recommendations": [],
                }
            )
        )

        with self.assertRaises(RecommendationProviderResponseError):
            provider.get_recommendations(recommendation_request())

    def test_null_movie_id_is_rejected(self) -> None:
        provider = self.make_provider(
            runtime=FakeRuntimeClient(
                {
                    "model_version": "1.0.0",
                    "recommendations": [
                        {
                            "movie_id": None,
                            "score": 0.9,
                            "reason_code": "similar_users",
                        }
                    ],
                }
            )
        )

        with self.assertRaises(RecommendationProviderResponseError):
            provider.get_recommendations(recommendation_request())

    def test_duplicate_ids_and_mismatched_parallel_arrays_are_rejected(
        self,
    ) -> None:
        payloads = (
            {
                "model_version": "1.0.0",
                "recommendations": [
                    {
                        "movie_id": 278,
                        "score": 0.9,
                        "reason_code": "similar_users",
                    },
                    {
                        "movie_id": 278,
                        "score": 0.8,
                        "reason_code": "similar_users",
                    },
                ],
            },
            {
                "model_version": "1.0.0",
                "movie_ids": [278, 550],
                "scores": [0.9],
            },
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                provider = self.make_provider(
                    runtime=FakeRuntimeClient(payload)
                )
                with self.assertRaises(
                    RecommendationProviderResponseError
                ):
                    provider.get_recommendations(
                        recommendation_request()
                    )

    def test_model_error_is_bad_gateway_error(self) -> None:
        error = ClientError(
            {
                "Error": {"Code": "ModelError", "Message": "failed"},
                "ResponseMetadata": {"RequestId": "request-model-error"},
            },
            "InvokeEndpoint",
        )
        provider = self.make_provider(
            runtime=FakeRuntimeClient(error=error)
        )

        with self.assertRaises(RecommendationProviderResponseError):
            provider.get_recommendations(recommendation_request())

    def test_timeout_and_credential_errors_are_controlled(self) -> None:
        cases = (
            (
                ReadTimeoutError(endpoint_url="https://runtime"),
                RecommendationProviderTimeoutError,
            ),
            (
                NoCredentialsError(),
                RecommendationProviderUnavailableError,
            ),
        )
        for error, expected in cases:
            with self.subTest(error=type(error).__name__):
                provider = self.make_provider(
                    runtime=FakeRuntimeClient(error=error)
                )
                with self.assertRaises(expected):
                    provider.get_recommendations(
                        recommendation_request()
                    )

    def test_disabled_provider_never_invokes_runtime(self) -> None:
        runtime = FakeRuntimeClient(native_response())
        provider = self.make_provider(runtime=runtime, enabled=False)

        with self.assertRaises(RecommendationProviderUnavailableError):
            provider.get_recommendations(recommendation_request())

        self.assertEqual(runtime.calls, [])

    def test_health_check_uses_control_plane_only_on_demand(self) -> None:
        provider = self.make_provider()

        self.assertTrue(provider.health_check())

    def test_health_check_returns_false_when_endpoint_is_absent(self) -> None:
        provider = self.make_provider()
        provider._control_client = FailingControlClient()

        with self.assertLogs(
            "movie_recommendation.sagemaker",
            level="WARNING",
        ):
            self.assertFalse(provider.health_check())


if __name__ == "__main__":
    unittest.main()
