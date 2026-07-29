import unittest
from typing import Optional

from app.models.movie import Movie
from app.repositories.movie_repository import MovieRepository
from app.schemas.sagemaker import (
    SageMakerRecommendationRequest,
    SageMakerRecommendationResponse,
)
from app.services.recommendation_provider import (
    RecommendationProviderUnavailableError,
)
from app.services.sagemaker_recommendation_provider import (
    SageMakerRecommendationProvider,
)


class StaticMovieStore(MovieRepository):
    def __init__(self) -> None:
        self.movie = Movie(
            movie_id="278",
            title="AWS movie",
            release_year=2024,
            genres=["Drama"],
            overview="DynamoDB metadata",
            poster_path="/poster.jpg",
            vote_average=8.5,
            vote_count=100,
            popularity=20.0,
            runtime=110,
            original_language="en",
            companies=["Studio"],
            countries=["Vietnam"],
            actors=["Actor"],
            directors=["Director"],
        )

    def list_all(self, limit: int | None = None) -> list[Movie]:
        del limit
        return [self.movie]

    def get(self, movie_id: str) -> Optional[Movie]:
        return self.movie if movie_id == self.movie.movie_id else None

    def get_many(self, movie_ids: list[str]) -> list[Movie]:
        return [self.movie] if self.movie.movie_id in movie_ids else []


class FakeControlClient:
    def describe_endpoint(self, *, EndpointName: str) -> dict[str, str]:
        del EndpointName
        return {"EndpointStatus": "InService"}


class ReadyProvider(SageMakerRecommendationProvider):
    def invoke_endpoint(
        self,
        request: SageMakerRecommendationRequest,
    ) -> SageMakerRecommendationResponse:
        self.last_request = request
        return SageMakerRecommendationResponse(
            model_version="model-v1",
            items=[
                {
                    "movie_id": "278",
                    "score": 0.95,
                    "reason_code": "personalized",
                }
            ],
        )


class SageMakerRecommendationProviderTests(unittest.TestCase):
    def make_provider(
        self,
        *,
        provider_type: type[SageMakerRecommendationProvider] = (
            SageMakerRecommendationProvider
        ),
        enabled: bool,
    ) -> SageMakerRecommendationProvider:
        return provider_type(
            movie_repository=StaticMovieStore(),
            runtime_client=object(),
            control_client=FakeControlClient(),
            endpoint_name="movie-recommendations-v1",
            scenario="default",
            recommendation_limit=10,
            content_type="application/json",
            accept="application/json",
            enabled=enabled,
        )

    def test_disabled_provider_never_generates_local_results(self) -> None:
        provider = self.make_provider(enabled=False)

        with self.assertRaises(RecommendationProviderUnavailableError):
            provider.get_recommendations("user-1")

    def test_unimplemented_invocation_returns_provider_unavailable(self) -> None:
        provider = self.make_provider(enabled=True)

        with self.assertRaises(RecommendationProviderUnavailableError):
            provider.get_recommendations("user-1")

    def test_completed_boundary_enriches_endpoint_references(self) -> None:
        provider = self.make_provider(
            provider_type=ReadyProvider,
            enabled=True,
        )

        movies = provider.get_recommendations("user-1")

        self.assertEqual([movie.movie_id for movie in movies], ["278"])
        self.assertEqual(movies[0].title, "AWS movie")
        self.assertEqual(movies[0].score, 0.95)
        self.assertEqual(provider.last_request.user_id, "user-1")

    def test_health_check_uses_sagemaker_control_plane(self) -> None:
        provider = self.make_provider(enabled=True)

        self.assertTrue(provider.health_check())


if __name__ == "__main__":
    unittest.main()
