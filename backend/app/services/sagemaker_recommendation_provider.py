from typing import Any


class SageMakerRecommendationProvider:
    """Placeholder boundary for a future Amazon SageMaker integration.

    The future implementation should create or receive a SageMaker Runtime
    client here and invoke the configured model endpoint inside ``recommend``.
    No AWS SDK dependency is included until that integration is implemented.
    """

    def recommend(self, user_id: int) -> list[Any]:
        """Return recommendations from a future SageMaker model endpoint.

        Add the SageMaker Runtime ``invoke_endpoint`` call here later, then
        translate its response into the application's recommendation format.
        """
        raise NotImplementedError(
            "SageMaker recommendation inference is not implemented."
        )

    def health_check(self) -> None:
        """Check future SageMaker endpoint availability.

        Add the SageMaker endpoint status or lightweight inference check here
        after the AWS client and endpoint configuration are introduced.
        """
        raise NotImplementedError(
            "SageMaker recommendation health checks are not implemented."
        )
