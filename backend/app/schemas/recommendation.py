from pydantic import BaseModel


class RecommendationItem(BaseModel):
    movie_id: int
    title: str
    score: float | None = None


class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: list[RecommendationItem]
