from abc import ABC, abstractmethod

from src.database.models.user import UserModel


class UserRepositoryInterface(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> UserModel | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> UserModel | None: ...

    @abstractmethod
    async def create(
        self, email: str, hashed_password: str, full_name: str
    ) -> UserModel: ...
