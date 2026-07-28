"""Canonical domain models backed by the five DynamoDB tables."""

from app.models.movie import Movie
from app.models.popular_movie import PopularMovie
from app.models.recommendation_cache import RecommendationCache, RecommendationCacheItem
from app.models.user import User
from app.models.user_interaction import (
    InteractionAction,
    InteractionType,
    UserInteraction,
)

__all__ = [
    "InteractionAction",
    "InteractionType",
    "Movie",
    "PopularMovie",
    "RecommendationCache",
    "RecommendationCacheItem",
    "User",
    "UserInteraction",
]
