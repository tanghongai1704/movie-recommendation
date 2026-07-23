from __future__ import annotations

from typing import Any, Dict, List


class MockRecommender:
    """A mock recommender that simulates ML inference.

    This class is intentionally simple and deterministic so the backend can
    depend on the same interface that a future SageMakerRecommender will use.
    """

    def __init__(self) -> None:
        self._mock_results = [
            {"movie_id": 10, "title": "Interstellar", "score": 0.95},
            {"movie_id": 20, "title": "Inception", "score": 0.92},
            {"movie_id": 30, "title": "The Matrix", "score": 0.90},
        ]

    def predict(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Return deterministic mock recommendations for a user."""
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id must be a positive integer")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        return self._mock_results[:limit]
