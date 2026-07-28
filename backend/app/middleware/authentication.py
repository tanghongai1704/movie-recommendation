from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.security import JWTService, TokenValidationError


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """Validate optional bearer tokens and attach claims to request.state."""

    def __init__(self, app: object, *, jwt_service: JWTService) -> None:
        super().__init__(app)
        self._jwt_service = jwt_service

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.auth = None
        authorization = request.headers.get("Authorization")
        if authorization is None:
            return await call_next(request)

        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.lower() != "bearer" or not token:
            return self._unauthorized_response()

        try:
            request.state.auth = self._jwt_service.decode_access_token(token)
        except TokenValidationError:
            return self._unauthorized_response()

        return await call_next(request)

    @staticmethod
    def _unauthorized_response() -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or expired access token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
