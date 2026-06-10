from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.task import TaskModel
from src.database.models.task_list import TaskListModel
from src.repositories.interfaces.task import TaskRepositoryInterface


class TaskRepository(TaskRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _base_query(self, task_list_id: int, status: str | None, priority: str | None):
        query = select(TaskModel).where(TaskModel.task_list_id == task_list_id)
        if status:
            query = query.where(TaskModel.status == status)
        if priority:
            query = query.where(TaskModel.priority == priority)
        return query

    async def get_all(
        self,
        task_list_id: int,
        status: str | None = None,
        priority: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[TaskModel]:
        query = self._base_query(task_list_id, status, priority)
        query = query.order_by(TaskModel.id).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(
        self,
        task_list_id: int,
        status: str | None = None,
        priority: str | None = None,
    ) -> tuple[int, int]:
        query = select(
            func.count().label("total"),
            func.count().filter(TaskModel.status == "completed").label("completed"),
        ).where(TaskModel.task_list_id == task_list_id)
        if status:
            query = query.where(TaskModel.status == status)
        if priority:
            query = query.where(TaskModel.priority == priority)
        result = await self.session.execute(query)
        row = result.one()
        return row.total, row.completed

    async def count_completed(self, task_list_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).where(
                TaskModel.task_list_id == task_list_id,
                TaskModel.status == "completed",
            )
        )
        return result.scalar_one()

    async def get_by_id(self, task_id: int) -> TaskModel | None:
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        task_list_id: int,
        title: str,
        description: str | None,
        priority: str,
    ) -> TaskModel:
        task = TaskModel(
            task_list_id=task_list_id,
            title=title,
            description=description,
            priority=priority,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.execute(
            sql_update(TaskListModel)
            .where(TaskListModel.id == task_list_id)
            .values(task_count=TaskListModel.task_count + 1)
        )
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update(
        self,
        task_id: int,
        title: str | None,
        description: str | None,
        priority: str | None,
        status: str | None,
        assignee_id: int | None,
    ) -> TaskModel | None:
        task = await self.get_by_id(task_id)
        if not task:
            return None
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if status is not None:
            task.status = status
        if assignee_id is not None:
            task.assignee_id = assignee_id
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: int) -> bool:
        task = await self.get_by_id(task_id)
        if not task:
            return False
        task_list_id = task.task_list_id
        await self.session.delete(task)
        await self.session.execute(
            sql_update(TaskListModel)
            .where(TaskListModel.id == task_list_id)
            .values(task_count=TaskListModel.task_count - 1)
        )
        await self.session.commit()
        return True
