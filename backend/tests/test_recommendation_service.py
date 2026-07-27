import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories.movie_repository import InMemoryMovieRepository
from app.schemas.movie import MovieResponse
from app.services.mock_recommendation_provider import MockRecommendationProvider
from app.services.recommendation_service import RecommendationService


class RecommendationServiceTests(unittest.TestCase):
    def test_build_payload_matches_contract(self) -> None:
        provider = MockRecommendationProvider(repository=InMemoryMovieRepository())
        service = RecommendationService(provider=provider)

        response = service.get_recommendation_payload(user_id=42, limit=2)

        self.assertEqual(response.user_id, 42)
        self.assertEqual(len(response.recommendations), 2)
        self.assertEqual(response.recommendations[0].movie_id, 1)
        self.assertEqual(response.recommendations[0].title, "Midnight Horizon")
        self.assertEqual(response.recommendations[0].score, 8.9)

    def test_invalid_limits_raise_value_error(self) -> None:
        provider = MockRecommendationProvider(repository=InMemoryMovieRepository())
        service = RecommendationService(provider=provider)

        with self.assertRaises(ValueError):
            service.get_recommendation_payload(user_id=1, limit=0)


if __name__ == "__main__":
    unittest.main()
