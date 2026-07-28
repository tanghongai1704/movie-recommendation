"""Compatibility imports for the repository module's former location.

New backend code must import DynamoDB repositories from ``app.repositories``.
This module remains temporarily so external imports do not fail during migration.
"""

from app.repositories.dynamodb_repository import (
    BaseDynamoDBRepository,
    DynamoDBRepositoryError,
    MoviesRepository,
    PopularMoviesRepository,
    RecommendationCacheRepository,
    UserInteractionsRepository,
    UsersRepository,
)

__all__ = [
    "BaseDynamoDBRepository",
    "DynamoDBRepositoryError",
    "MoviesRepository",
    "PopularMoviesRepository",
    "RecommendationCacheRepository",
    "UserInteractionsRepository",
    "UsersRepository",
]
