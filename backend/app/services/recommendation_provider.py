from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.movie import MovieResponse


class RecommendationProviderUnavailableError(Exception):
    """Raised when personalized inference cannot currently be performed."""


class RecommendationProvider(ABC):
    """Stable provider boundary for personalized movie inference."""

    @abstractmethod
    def get_recommendations(
        self,
        user_id: Optional[str] = None,
    ) -> list[MovieResponse]:
        raise NotImplementedError
