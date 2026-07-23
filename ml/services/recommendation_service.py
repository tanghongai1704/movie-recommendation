from __future__ import annotations

from typing import Any, Dict, List, Optional

from ml.mock.mock_recommender import MockRecommender
from ml.utils.preprocessing import build_payload, normalize_user_id


class RecommendationServiceError(Exception):
    """Raised when recommendation generation fails."""


class RecommendationService:
    """Service layer for generating recommendations.

    The backend should depend only on this class. The implementation may later be
    swapped from MockRecommender to SageMakerRecommender without changing the
    backend API contract.
    """

    def __init__(self, recommender: Optional[MockRecommender] = None) -> None:
        self._recommender = recommender or MockRecommender()

    def recommend(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recommendations for a user using the configured recommender."""
        try:
            normalized_user_id = normalize_user_id(user_id)
            payload = build_payload(normalized_user_id, limit)
            results = self._recommender.predict(
                user_id=payload["user_id"],
                limit=payload["limit"],
            )
        except ValueError as exc:
            raise RecommendationServiceError(str(exc)) from exc

        if not results:
            raise RecommendationServiceError("No recommendations available")

        return results
