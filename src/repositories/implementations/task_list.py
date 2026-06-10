from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.task_list import TaskListModel
from src.repositories.interfaces.task_list import TaskListRepositoryInterface


class TaskListRepository(TaskListRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[TaskListModel]:
        query = select(TaskListModel).order_by(TaskListModel.id).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(TaskListModel))
        return result.scalar_one()

    async def get_by_id(self, task_list_id: int) -> TaskListModel | None:
        result = await self.session.execute(
            select(TaskListModel).where(TaskListModel.id == task_list_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, title: str, description: str | None, owner_id: int | None
    ) -> TaskListModel:
        task_list = TaskListModel(
            title=title, description=description, owner_id=owner_id
        )
        self.session.add(task_list)
        await self.session.commit()
        await self.session.refresh(task_list)
        return task_list

    async def update(
        self, task_list_id: int, title: str | None, description: str | None
    ) -> TaskListModel | None:
        task_list = await self.get_by_id(task_list_id)
        if not task_list:
            return None
        if title is not None:
            task_list.title = title
        if description is not None:
            task_list.description = description
        await self.session.commit()
        await self.session.refresh(task_list)
        return task_list

    async def delete(self, task_list_id: int) -> bool:
        task_list = await self.get_by_id(task_list_id)
        if not task_list:
            return False
        await self.session.delete(task_list)
        await self.session.commit()
        return True
