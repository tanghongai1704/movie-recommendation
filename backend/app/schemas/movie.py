from pydantic import BaseModel


class MovieResponse(BaseModel):
    id: int
    title: str
    genre: str
    year: int
    rating: float
    description: str
    image_url: str
