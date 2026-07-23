from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.movie import MovieResponse


class RecommendationProvider(ABC):
    """Abstraction for retrieving recommended movies.

    This interface is intentionally small so a future SageMaker-based
    implementation can replace the current mock provider without changing the
    router or the frontend-facing response contract.
    """

    @abstractmethod
    def get_recommendations(self, user_id: Optional[int] = None) -> List[MovieResponse]:
        raise NotImplementedError
