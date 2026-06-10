from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import UserModel
from src.repositories.interfaces.user import UserRepositoryInterface


class UserRepository(UserRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def create(
        self, email: str, hashed_password: str, full_name: str
    ) -> UserModel:
        user = UserModel(
            email=email, hashed_password=hashed_password, full_name=full_name
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
