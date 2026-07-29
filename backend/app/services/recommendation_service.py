from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from time import time
from typing import Callable, Optional, Protocol

from app.models.recommendation_cache import (
    RecommendationCache,
    RecommendationCacheItem,
)
from app.models.user import User
from app.models.user_interaction import (
    InteractionAction,
    InteractionType,
    StoredUserInteraction,
)
from app.repositories.dynamodb_base import DynamoDBRepositoryError
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.schemas.sagemaker import (
    SageMakerInteraction,
    SageMakerRecommendationRequest,
)
from app.services.recommendation_provider import (
    ProviderRecommendationItem,
    RecommendationProvider,
    RecommendationProviderResponseError,
)

logger = logging.getLogger("movie_recommendation.recommendation")

SCENARIO_ONBOARDING = "onboarding_user"
SCENARIO_RETURNING = "returning_user"
MIN_INTERACTIONS_FOR_RETURNING = 5
INTERACTION_RECENCY_DAYS = 90
MAX_PROFILE_EVENTS = 200
MAX_RECENT_INTERACTIONS = 50
WATCH_PROGRESS_THRESHOLD = 0.5
MAX_MODEL_USER_ID = (1 << 63) - 1


class RecommendationCacheStore(Protocol):
    """Persistence boundary used by RecommendationService."""

    def get(
        self,
        user_id: str,
        scenario: str,
    ) -> Optional[RecommendationCache]:
        ...

    def upsert(self, item: RecommendationCache) -> RecommendationCache:
        ...


class RecommendationUserStore(Protocol):
    def get(self, user_id: str) -> Optional[User]:
        ...


class RecommendationInteractionStore(Protocol):
    def list_by_user(self, user_id: str) -> list[StoredUserInteraction]:
        ...


class CachedRecommendationMovie(MovieResponse):
    """Movie metadata enriched with fields stored in RecommendationCache.items."""

    score: float
    reason_code: str


class RecommendationService:
    """Build model context, use cache, invoke provider, and persist ranking."""

    def __init__(
        self,
        provider: RecommendationProvider,
        cache: RecommendationCacheStore,
        movie_repository: MovieRepository,
        users: RecommendationUserStore,
        interactions: RecommendationInteractionStore,
        *,
        cache_ttl_seconds: int,
        model_version: str,
        clock: Callable[[], float] = time,
    ) -> None:
        if cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be a positive integer")

        self._provider = provider
        self._cache = cache
        self._movie_repository = movie_repository
        self._users = users
        self._interactions = interactions
        self._cache_ttl_seconds = cache_ttl_seconds
        self._model_version = model_version
        self._clock = clock

    def get_recommendations(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[MovieResponse]:
        if not user_id:
            raise ValueError("user_id must not be empty")
        if limit <= 0 or limit > 50:
            raise ValueError("limit must be between 1 and 50")

        user = self._users.get(user_id)
        if user is None:
            raise ValueError("User not found")

        # Returning-user cache can be checked without loading interaction
        # history. Interactions only accumulate, so an existing valid returning
        # result cannot transition back to onboarding.
        cached = self._get_valid_cached_movies(
            user_id=user_id,
            scenario=SCENARIO_RETURNING,
        )
        if cached is not None:
            logger.info(
                "Recommendation cache hit user_id=%s scenario=%s",
                user_id,
                SCENARIO_RETURNING,
            )
            return cached[:limit]

        stored_interactions = self._interactions.list_by_user(user_id)
        model_interactions = self._normalize_interactions(
            stored_interactions
        )
        valid_count = self._valid_interaction_count(
            model_interactions,
            now=datetime.fromtimestamp(self._clock(), tz=timezone.utc),
        )
        scenario = (
            SCENARIO_RETURNING
            if valid_count >= MIN_INTERACTIONS_FOR_RETURNING
            else SCENARIO_ONBOARDING
        )

        if scenario == SCENARIO_ONBOARDING:
            cached = self._get_valid_cached_movies(
                user_id=user_id,
                scenario=scenario,
            )
            if cached is not None:
                logger.info(
                    "Recommendation cache hit user_id=%s scenario=%s",
                    user_id,
                    scenario,
                )
                return cached[:limit]

        logger.info(
            "Recommendation cache miss user_id=%s scenario=%s",
            user_id,
            scenario,
        )
        request = SageMakerRecommendationRequest(
            user_id=self._model_user_id(user_id),
            scenario_hint=scenario,
            onboarding_completed=user.onboarding_completed,
            valid_interaction_count_90d=valid_count,
            selected_movie_ids=[],
            selected_genres=user.onboarding_genres or [],
            recent_interactions=model_interactions[
                :MAX_RECENT_INTERACTIONS
            ],
            exclude_movie_ids=sorted(
                {
                    item.movie_id
                    for item in model_interactions
                    if item.event_type == "dislike"
                }
            ),
            limit=limit,
        )
        provider_result = self._provider.get_recommendations(request)
        movies = self._enrich_provider_items(provider_result.items)
        self._save_to_cache(
            user_id=user_id,
            scenario=scenario,
            movies=movies,
            model_version=provider_result.model_version,
        )
        return movies[:limit]

    def get_recommendation_payload(
        self,
        user_id: str,
        limit: int = 10,
    ) -> RecommendationResponse:
        movies = self.get_recommendations(user_id=user_id, limit=limit)
        return RecommendationResponse(
            user_id=user_id,
            recommendations=[
                RecommendationItem.model_validate(movie.model_dump())
                for movie in movies
            ],
        )

    def _get_valid_cached_movies(
        self,
        *,
        user_id: str,
        scenario: str,
    ) -> Optional[list[CachedRecommendationMovie]]:
        try:
            cached = self._cache.get(
                user_id=user_id,
                scenario=scenario,
            )
        except DynamoDBRepositoryError as exc:
            logger.warning(
                "Recommendation cache read failed user_id=%s scenario=%s "
                "error_type=%s",
                user_id,
                scenario,
                type(exc).__name__,
            )
            return None

        if cached is None or cached.expire_at <= self._clock():
            return None

        movie_ids = [item.movie_id for item in cached.items]
        resolved = self._movie_repository.get_many(movie_ids)
        movies_by_id = {movie.movie_id: movie for movie in resolved}
        if any(movie_id not in movies_by_id for movie_id in movie_ids):
            return None

        return [
            CachedRecommendationMovie(
                **movies_by_id[item.movie_id].model_dump(),
                score=item.score,
                reason_code=item.reason_code,
            )
            for item in cached.items
        ]

    def _save_to_cache(
        self,
        *,
        user_id: str,
        scenario: str,
        movies: list[MovieResponse],
        model_version: str,
    ) -> None:
        now = self._clock()
        version = model_version.strip() or self._model_version
        if "mock" in version.casefold():
            logger.warning(
                "Skipping recommendation cache write for invalid model "
                "version user_id=%s scenario=%s",
                user_id,
                scenario,
            )
            return

        cache_entry = RecommendationCache(
            user_id=user_id,
            scenario=scenario,
            items=[
                RecommendationCacheItem(
                    movie_id=movie.movie_id,
                    score=float(getattr(movie, "score", 0.0) or 0.0),
                    reason_code=str(
                        getattr(movie, "reason_code", None)
                        or "provider_default"
                    ),
                )
                for movie in movies
            ],
            model_version=version,
            generated_at=datetime.fromtimestamp(now, tz=timezone.utc),
            expire_at=int(now) + self._cache_ttl_seconds,
        )
        try:
            self._cache.upsert(cache_entry)
        except DynamoDBRepositoryError as exc:
            logger.warning(
                "Recommendation cache write failed user_id=%s scenario=%s "
                "error_type=%s",
                user_id,
                scenario,
                type(exc).__name__,
            )

    def _enrich_provider_items(
        self,
        items: list[ProviderRecommendationItem],
    ) -> list[RecommendationItem]:
        movie_ids = [item.movie_id for item in items]
        resolved = self._movie_repository.get_many(movie_ids)
        movies_by_id = {movie.movie_id: movie for movie in resolved}
        missing_count = sum(
            movie_id not in movies_by_id for movie_id in movie_ids
        )
        if missing_count:
            logger.warning(
                "Recommendation provider returned %s IDs absent from Movies",
                missing_count,
            )

        enriched = [
            RecommendationItem(
                **movies_by_id[item.movie_id].model_dump(),
                score=item.score,
                reason_code=item.reason_code,
            )
            for item in items
            if item.movie_id in movies_by_id
        ]
        if not enriched:
            raise RecommendationProviderResponseError(
                "Recommendation IDs do not resolve to Movies records"
            )
        return enriched

    @classmethod
    def _normalize_interactions(
        cls,
        interactions: list[StoredUserInteraction],
    ) -> list[SageMakerInteraction]:
        ordered = sorted(
            interactions,
            key=lambda item: (item.timestamp, item.interaction_key),
            reverse=True,
        )
        normalized: list[SageMakerInteraction] = []
        state_seen: set[tuple[InteractionType, str]] = set()

        for item in ordered:
            try:
                movie_id = int(item.movie_id)
            except (TypeError, ValueError):
                continue

            event_type: str | None = None
            value = item.interaction_value
            if item.interaction_type in {
                InteractionType.RATING,
                InteractionType.REACTION,
            }:
                state_key = (item.interaction_type, item.movie_id)
                if state_key in state_seen:
                    continue
                state_seen.add(state_key)
                if (
                    item.interaction_action == InteractionAction.CLEAR
                    or value == 0
                ):
                    continue

            if item.interaction_type == InteractionType.REACTION:
                if (
                    item.interaction_action
                    == InteractionAction.REACTION_LIKE
                    or value == 1
                ):
                    event_type = "like"
                elif (
                    item.interaction_action
                    == InteractionAction.REACTION_DISLIKE
                    or value == -1
                ):
                    event_type = "dislike"
                value = None
            elif item.interaction_type == InteractionType.RATING:
                event_type = "rating"
            elif item.interaction_type == InteractionType.CLICK:
                event_type = "click"
            elif item.interaction_type == InteractionType.WATCH:
                event_type = "watch"
            elif item.interaction_type == InteractionType.SHARE:
                event_type = "share"

            if event_type is None:
                continue
            timestamp = item.timestamp
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            else:
                timestamp = timestamp.astimezone(timezone.utc)
            normalized.append(
                SageMakerInteraction(
                    movie_id=movie_id,
                    event_type=event_type,
                    value=value,
                    timestamp=(
                        timestamp.isoformat(timespec="milliseconds")
                        .replace("+00:00", "Z")
                    ),
                )
            )
            if len(normalized) >= MAX_PROFILE_EVENTS:
                break
        return normalized

    @staticmethod
    def _valid_interaction_count(
        interactions: list[SageMakerInteraction],
        *,
        now: datetime,
    ) -> int:
        cutoff = now - timedelta(days=INTERACTION_RECENCY_DAYS)
        valid_types = {"watch", "like", "rating", "share"}
        count = 0
        for item in interactions:
            if item.event_type not in valid_types:
                continue
            if (
                item.event_type == "watch"
                and (
                    item.value is None
                    or float(item.value) < WATCH_PROGRESS_THRESHOLD
                )
            ):
                continue
            if item.timestamp:
                timestamp = datetime.fromisoformat(
                    item.timestamp.replace("Z", "+00:00")
                )
                if timestamp < cutoff:
                    continue
            count += 1
        return count

    @staticmethod
    def _model_user_id(user_id: str) -> int:
        """Map application IDs deterministically into the model's int64 key."""

        try:
            numeric_id = int(user_id)
        except ValueError:
            numeric_id = 0
        if 0 < numeric_id <= MAX_MODEL_USER_ID:
            return numeric_id

        digest = hashlib.sha256(user_id.encode("utf-8")).digest()
        mapped = int.from_bytes(
            digest[:8],
            byteorder="big",
            signed=False,
        ) & MAX_MODEL_USER_ID
        return mapped or 1
