from typing import Optional

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    movie_id: int
    title: str
    score: Optional[float] = None


class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: list[RecommendationItem]
