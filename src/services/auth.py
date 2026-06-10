from src.config.security import create_access_token, hash_password, verify_password
from src.exceptions.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from src.repositories.interfaces.user import UserRepositoryInterface
from src.schemas.user import TokenResponse, UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    async def register(self, email: str, password: str, full_name: str) -> UserResponse:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise EmailAlreadyExistsError(email)
        hashed = hash_password(password)
        user = await self.user_repo.create(
            email=email, hashed_password=hashed, full_name=full_name
        )
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        token = create_access_token({"sub": str(user.id), "email": user.email})
        return TokenResponse(access_token=token)
