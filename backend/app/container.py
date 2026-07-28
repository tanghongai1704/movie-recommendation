"""Application composition root for security, services, and repositories."""

from app.core.config import settings
from app.core.security import JWTService, PasswordHasher
from app.repositories.users_repository import UsersRepository
from app.services.auth_service import AuthService

users_repository = UsersRepository(
    table_name=settings.AWS_DYNAMODB_TABLE_USERS,
    region_name=settings.AWS_REGION,
)
password_hasher = PasswordHasher(iterations=settings.PASSWORD_HASH_ITERATIONS)
jwt_service = JWTService(
    secret=settings.JWT_SECRET,
    issuer=settings.JWT_ISSUER,
    audience=settings.JWT_AUDIENCE,
    access_token_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
)
auth_service = AuthService(
    users=users_repository,
    password_hasher=password_hasher,
)
