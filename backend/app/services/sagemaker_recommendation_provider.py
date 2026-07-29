from __future__ import annotations

import json
import logging
import math
from time import perf_counter
from typing import Any

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
    ProfileNotFound,
    ReadTimeoutError,
)
from pydantic import ValidationError

from app.schemas.sagemaker import (
    SageMakerRecommendationRequest,
    SageMakerRecommendationResponse,
    SageMakerRecommendationResult,
)
from app.services.recommendation_provider import (
    ProviderRecommendationItem,
    ProviderRecommendationResult,
    RecommendationProvider,
    RecommendationProviderResponseError,
    RecommendationProviderTimeoutError,
    RecommendationProviderUnavailableError,
)

logger = logging.getLogger("movie_recommendation.sagemaker")


class SageMakerRecommendationProvider(RecommendationProvider):
    """Invoke SageMaker Runtime and normalize model ranking output."""

    def __init__(
        self,
        *,
        runtime_client: Any,
        control_client: Any,
        endpoint_name: str | None,
        recommendation_limit: int,
        content_type: str,
        accept: str,
        fallback_model_version: str,
        enabled: bool,
    ) -> None:
        if recommendation_limit <= 0:
            raise ValueError(
                "SageMaker recommendation_limit must be positive"
            )
        self._runtime_client = runtime_client
        self._control_client = control_client
        self._endpoint_name = endpoint_name
        self._recommendation_limit = recommendation_limit
        self._content_type = content_type
        self._accept = accept
        self._fallback_model_version = fallback_model_version
        self._enabled = enabled

    def get_recommendations(
        self,
        request: SageMakerRecommendationRequest,
    ) -> ProviderRecommendationResult:
        if not self._enabled or not self._endpoint_name:
            raise RecommendationProviderUnavailableError(
                "Personalized inference is not enabled"
            )
        if self._runtime_client is None:
            raise RecommendationProviderUnavailableError(
                "SageMaker Runtime client is unavailable"
            )

        effective_request = (
            request.model_copy(
                update={
                    "limit": min(
                        request.limit,
                        self._recommendation_limit,
                    )
                }
            )
            if request.limit > self._recommendation_limit
            else request
        )
        response = self.invoke_endpoint(effective_request)
        return ProviderRecommendationResult(
            items=[
                ProviderRecommendationItem(
                    movie_id=item.movie_id,
                    score=item.score,
                    reason_code=item.reason_code,
                )
                for item in response.items
            ],
            model_version=response.model_version,
            scenario_applied=response.scenario,
        )

    def invoke_endpoint(
        self,
        request: SageMakerRecommendationRequest,
    ) -> SageMakerRecommendationResponse:
        """Invoke the configured endpoint exactly once and validate its body."""

        if not self._endpoint_name or self._runtime_client is None:
            raise RecommendationProviderUnavailableError(
                "SageMaker Runtime is not configured"
            )

        started = perf_counter()
        aws_request_id: str | None = None
        try:
            raw_response = self._runtime_client.invoke_endpoint(
                EndpointName=self._endpoint_name,
                ContentType=self._content_type,
                Accept=self._accept,
                Body=request.model_dump_json().encode("utf-8"),
            )
            metadata = raw_response.get("ResponseMetadata") or {}
            aws_request_id = metadata.get("RequestId")
            status_code = metadata.get("HTTPStatusCode", 200)
            if status_code < 200 or status_code >= 300:
                raise RecommendationProviderResponseError(
                    f"SageMaker returned HTTP {status_code}"
                )

            body_stream = raw_response.get("Body")
            body = body_stream.read() if body_stream is not None else b""
            if not body:
                raise RecommendationProviderResponseError(
                    "SageMaker returned an empty response body"
                )
            payload = json.loads(body.decode("utf-8"))
            normalized = self._normalize_response(payload, request)
        except (ConnectTimeoutError, ReadTimeoutError) as exc:
            self._log_failure(
                request=request,
                started=started,
                aws_request_id=aws_request_id,
                error=exc,
            )
            raise RecommendationProviderTimeoutError(
                "SageMaker inference timed out"
            ) from exc
        except (
            EndpointConnectionError,
            NoCredentialsError,
            PartialCredentialsError,
            ProfileNotFound,
        ) as exc:
            self._log_failure(
                request=request,
                started=started,
                aws_request_id=aws_request_id,
                error=exc,
            )
            raise RecommendationProviderUnavailableError(
                "SageMaker Runtime is unavailable"
            ) from exc
        except ClientError as exc:
            self._log_failure(
                request=request,
                started=started,
                aws_request_id=self._request_id_from_client_error(exc),
                error=exc,
            )
            code = str(
                exc.response.get("Error", {}).get("Code", "")
            )
            if code == "ModelError":
                raise RecommendationProviderResponseError(
                    "SageMaker model failed to process the request"
                ) from exc
            raise RecommendationProviderUnavailableError(
                "SageMaker endpoint request failed"
            ) from exc
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            ValidationError,
            TypeError,
            ValueError,
            RecommendationProviderResponseError,
        ) as exc:
            self._log_failure(
                request=request,
                started=started,
                aws_request_id=aws_request_id,
                error=exc,
            )
            if isinstance(exc, RecommendationProviderResponseError):
                raise
            raise RecommendationProviderResponseError(
                "SageMaker returned an invalid response"
            ) from exc

        logger.info(
            "SageMaker inference succeeded endpoint=%s scenario=%s "
            "aws_request_id=%s latency_ms=%.1f recommendations=%s",
            self._endpoint_name,
            request.scenario_hint,
            aws_request_id or "unknown",
            (perf_counter() - started) * 1000,
            len(normalized.items),
        )
        return normalized

    def _normalize_response(
        self,
        payload: Any,
        request: SageMakerRecommendationRequest,
    ) -> SageMakerRecommendationResponse:
        if not isinstance(payload, dict):
            raise RecommendationProviderResponseError(
                "SageMaker response must be a JSON object"
            )

        raw_items: Any
        if "recommendations" in payload:
            raw_items = payload["recommendations"]
        elif "items" in payload:
            raw_items = payload["items"]
        elif "movie_ids" in payload or "scores" in payload:
            movie_ids = payload.get("movie_ids")
            scores = payload.get("scores")
            if not isinstance(movie_ids, list) or not isinstance(scores, list):
                raise RecommendationProviderResponseError(
                    "movie_ids and scores must both be arrays"
                )
            if len(movie_ids) != len(scores):
                raise RecommendationProviderResponseError(
                    "movie_ids and scores must have equal lengths"
                )
            raw_items = [
                {
                    "movie_id": movie_id,
                    "score": score,
                    "reason_code": self._default_reason(
                        request.scenario_hint
                    ),
                }
                for movie_id, score in zip(movie_ids, scores, strict=True)
            ]
        else:
            raise RecommendationProviderResponseError(
                "SageMaker response contains no recommendation list"
            )

        if not isinstance(raw_items, list) or not raw_items:
            raise RecommendationProviderResponseError(
                "SageMaker returned no recommendations"
            )

        normalized_items: list[SageMakerRecommendationResult] = []
        seen_ids: set[str] = set()
        for raw_item in raw_items[: request.limit]:
            if not isinstance(raw_item, dict):
                raise RecommendationProviderResponseError(
                    "Each SageMaker recommendation must be an object"
                )
            item_data = dict(raw_item)
            item_data.setdefault(
                "reason_code",
                self._default_reason(request.scenario_hint),
            )
            item = SageMakerRecommendationResult.model_validate(item_data)
            if not math.isfinite(item.score):
                raise RecommendationProviderResponseError(
                    "SageMaker recommendation scores must be finite"
                )
            if item.movie_id in seen_ids:
                raise RecommendationProviderResponseError(
                    "SageMaker returned duplicate movie IDs"
                )
            seen_ids.add(item.movie_id)
            normalized_items.append(item)

        model_version = str(
            payload.get("model_version")
            or self._fallback_model_version
        ).strip()
        if not model_version or "mock" in model_version.casefold():
            raise RecommendationProviderResponseError(
                "A non-mock model version is required for SageMaker results"
            )

        scenario = str(
            payload.get("scenario_applied")
            or payload.get("scenario")
            or request.scenario_hint
        )
        return SageMakerRecommendationResponse.model_validate(
            {
                "scenario": scenario,
                "model_version": model_version,
                "items": normalized_items,
            }
        )

    def health_check(self) -> bool:
        """Describe endpoint status for explicit diagnostics, not inference."""

        if (
            not self._enabled
            or not self._endpoint_name
            or self._control_client is None
        ):
            return False
        try:
            response = self._control_client.describe_endpoint(
                EndpointName=self._endpoint_name
            )
            return response.get("EndpointStatus") == "InService"
        except (BotoCoreError, ClientError) as exc:
            logger.warning(
                "SageMaker health check failed endpoint=%s error_type=%s",
                self._endpoint_name,
                type(exc).__name__,
            )
            return False

    @staticmethod
    def _default_reason(scenario: str) -> str:
        return (
            "similar_to_onboarding"
            if scenario == "onboarding_user"
            else "personalized"
        )

    def _log_failure(
        self,
        *,
        request: SageMakerRecommendationRequest,
        started: float,
        aws_request_id: str | None,
        error: Exception,
    ) -> None:
        logger.error(
            "SageMaker inference failed endpoint=%s scenario=%s "
            "aws_request_id=%s latency_ms=%.1f error_type=%s",
            self._endpoint_name or "unconfigured",
            request.scenario_hint,
            aws_request_id or "unknown",
            (perf_counter() - started) * 1000,
            type(error).__name__,
        )

    @staticmethod
    def _request_id_from_client_error(error: ClientError) -> str | None:
        metadata = error.response.get("ResponseMetadata") or {}
        return metadata.get("RequestId")
