from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.sagemaker import SageMakerRecommendationRequest


class RecommendationProviderError(Exception):
    """Base error raised by a recommendation inference provider."""


class RecommendationProviderUnavailableError(RecommendationProviderError):
    """Raised when personalized inference cannot currently be performed."""


class RecommendationProviderTimeoutError(RecommendationProviderError):
    """Raised when the inference provider exceeds its configured timeout."""


class RecommendationProviderResponseError(RecommendationProviderError):
    """Raised when a provider returns an invalid or unusable response."""


@dataclass(frozen=True)
class ProviderRecommendationItem:
    """Provider-neutral ranked movie reference without catalog metadata."""

    movie_id: str
    score: float
    reason_code: str


@dataclass(frozen=True)
class ProviderRecommendationResult:
    """Normalized inference output returned to the business service."""

    items: list[ProviderRecommendationItem]
    model_version: str
    scenario_applied: str


class RecommendationProvider(ABC):
    """Stable provider boundary for personalized movie inference."""

    @abstractmethod
    def get_recommendations(
        self,
        request: SageMakerRecommendationRequest,
    ) -> ProviderRecommendationResult:
        raise NotImplementedError
