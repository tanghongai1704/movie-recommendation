from typing import Any, Optional

from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MovieResponse
from app.schemas.recommendation import RecommendationItem
from app.schemas.sagemaker import (
    SageMakerRecommendationRequest,
    SageMakerRecommendationResponse,
)
from app.services.recommendation_provider import (
    RecommendationProvider,
    RecommendationProviderUnavailableError,
)


class SageMakerRecommendationProvider(RecommendationProvider):
    """SageMaker-ready provider that never generates local recommendations.

    Request construction, response validation, movie enrichment, endpoint
    configuration and endpoint health checks are complete. Implement only
    ``invoke_endpoint`` after a compatible model is deployed.
    """

    def __init__(
        self,
        *,
        movie_repository: MovieRepository,
        runtime_client: Any,
        control_client: Any,
        endpoint_name: str | None,
        scenario: str,
        recommendation_limit: int,
        content_type: str,
        accept: str,
        enabled: bool,
    ) -> None:
        if recommendation_limit <= 0:
            raise ValueError(
                "SageMaker recommendation_limit must be positive"
            )
        self._movie_repository = movie_repository
        self._runtime_client = runtime_client
        self._control_client = control_client
        self._endpoint_name = endpoint_name
        self._scenario = scenario
        self._recommendation_limit = recommendation_limit
        self._content_type = content_type
        self._accept = accept
        self._enabled = enabled

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
    ) -> list[MovieResponse]:
        if not user_id:
            raise ValueError(
                "SageMaker recommendations require a registered user_id"
            )
        return self.recommend(user_id)

    def recommend(self, user_id: str) -> list[MovieResponse]:
        """Validate inference output and enrich references from DynamoDB."""

        if not self._enabled or not self._endpoint_name:
            raise RecommendationProviderUnavailableError(
                "Personalized inference is not enabled"
            )
        request = SageMakerRecommendationRequest(
            user_id=user_id,
            scenario=self._scenario,
            limit=self._recommendation_limit,
        )
        try:
            response = self.invoke_endpoint(request)
        except NotImplementedError as exc:
            raise RecommendationProviderUnavailableError(
                "SageMaker endpoint invocation is not implemented"
            ) from exc

        movie_ids = [item.movie_id for item in response.items]
        movies = self._movie_repository.get_many(movie_ids)
        movies_by_id = {movie.movie_id: movie for movie in movies}
        if any(movie_id not in movies_by_id for movie_id in movie_ids):
            raise RecommendationProviderUnavailableError(
                "SageMaker returned a movie that is absent from Movies"
            )
        return [
            RecommendationItem(
                **movies_by_id[item.movie_id].model_dump(),
                score=item.score,
                reason_code=item.reason_code,
            )
            for item in response.items
        ]

    def invoke_endpoint(
        self,
        request: SageMakerRecommendationRequest,
    ) -> SageMakerRecommendationResponse:
        """Invoke the configured endpoint after a compatible model is deployed.

        Add exactly one boto3 ``self._runtime_client.invoke_endpoint`` call
        here. Send ``request.model_dump_json()`` as Body with the configured
        endpoint, content type and accept header, then validate the decoded
        JSON with ``SageMakerRecommendationResponse.model_validate``.
        """

        del request
        raise NotImplementedError(
            "SageMaker endpoint invocation awaits a deployed model"
        )

    def health_check(self) -> bool:
        """Return whether the configured SageMaker endpoint is InService."""

        if not self._enabled or not self._endpoint_name:
            return False
        response = self._control_client.describe_endpoint(
            EndpointName=self._endpoint_name
        )
        return response.get("EndpointStatus") == "InService"
