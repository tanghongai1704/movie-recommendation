import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.models.movie import Movie
from app.models.popular_movie import PopularMovie
from app.models.recommendation_cache import (
    RecommendationCache,
    RecommendationCacheItem,
)
from app.models.user import User, UserSettings
from app.models.user_interaction import InteractionType, UserInteraction


class DomainModelTests(unittest.TestCase):
    def test_movie_uses_only_canonical_fields(self) -> None:
        movie = Movie(
            movie_id="1",
            title="Example",
            release_year=2026,
            genres=["Drama"],
            overview="Example overview",
            poster_path="/poster.jpg",
            vote_average=8.0,
            vote_count=10,
            popularity=12.5,
            runtime=100,
            original_language="en",
            companies=["Example Studio"],
            countries=["Vietnam"],
            actors=["Example Actor"],
            directors=["Example Director"],
        )

        self.assertEqual(movie.movie_id, "1")
        with self.assertRaises(ValidationError):
            Movie.model_validate({**movie.model_dump(), "id": 1})

    def test_popular_list_contains_only_ranked_movie_references(self) -> None:
        generated_at = datetime.now(timezone.utc)
        popular = PopularMovie(
            list_id="global-daily",
            ranking_type="global",
            genre=None,
            movie_ids=["1", "2"],
            scores=[0.9, 0.8],
            generated_at=generated_at,
        )

        self.assertEqual(
            set(popular.model_dump()),
            {
                "list_id",
                "ranking_type",
                "genre",
                "movie_ids",
                "scores",
                "generated_at",
            },
        )
        with self.assertRaises(ValidationError):
            PopularMovie(
                list_id="invalid",
                ranking_type="global",
                genre=None,
                movie_ids=["1"],
                scores=[],
                generated_at=generated_at,
            )

    def test_user_model_contains_onboarding_state(self) -> None:
        timestamp = datetime.now(timezone.utc)
        user = User(
            user_id="user-1",
            recent_movie_ids=["movie-1"],
            schema_version=2,
            onboarding_genres=["Drama"],
            user_settings=UserSettings(
                email="user@example.com",
                username="example",
                password_hash="hashed-password",
                created_at=timestamp,
            ),
        )

        self.assertEqual(
            set(user.model_dump()),
            {
                "user_id",
                "recent_movie_ids",
                "schema_version",
                "onboarding_genres",
                "user_settings",
            },
        )
        self.assertTrue(user.onboarding_completed)
        self.assertEqual(user.username, "example")

    def test_interaction_key_and_fields_match_table_contract(self) -> None:
        timestamp = datetime.now(timezone.utc)
        interaction = UserInteraction(
            user_id="user-1",
            interaction_key=f"{timestamp.isoformat()}#movie-1",
            movie_id="movie-1",
            interaction_type=InteractionType.CLICK,
            interaction_value=None,
            timestamp=timestamp,
            session_id="session-1",
        )

        self.assertEqual(
            set(interaction.model_dump()),
            {
                "user_id",
                "interaction_key",
                "movie_id",
                "interaction_type",
                "interaction_value",
                "timestamp",
                "session_id",
            },
        )

    def test_cache_contains_references_without_movie_metadata(self) -> None:
        cache = RecommendationCache(
            user_id="user-1",
            scenario="home",
            items=[
                RecommendationCacheItem(
                    movie_id="movie-1",
                    score=0.95,
                    reason_code="similar_genres",
                )
            ],
            model_version="mock-v1",
            generated_at=datetime.now(timezone.utc),
            expire_at=1_800_000_000,
        )

        self.assertEqual(
            set(cache.model_dump()),
            {
                "user_id",
                "scenario",
                "items",
                "model_version",
                "generated_at",
                "expire_at",
            },
        )
        self.assertEqual(
            set(cache.items[0].model_dump()),
            {"movie_id", "score", "reason_code"},
        )


if __name__ == "__main__":
    unittest.main()
