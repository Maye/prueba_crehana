from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.repositories.implementations.user import UserRepository
from src.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from src.services.auth import AuthService


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(user_repo=UserRepository(db))


class AuthController:
    def __init__(self, service: AuthService = Depends(get_auth_service)):
        self.service = service

    async def register(self, data: UserRegisterRequest) -> UserResponse:
        return await self.service.register(
            email=data.email, password=data.password, full_name=data.full_name
        )

    async def login(self, data: UserLoginRequest) -> TokenResponse:
        return await self.service.login(email=data.email, password=data.password)
