from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import UserModel
from src.database.session import get_db
from src.dependencies import get_current_user
from src.repositories.implementations.task import TaskRepository
from src.repositories.implementations.task_list import TaskListRepository
from src.repositories.implementations.user import UserRepository
from src.schemas.task import (
    TaskAssignRequest,
    TaskCreateRequest,
    TaskListTasksResponse,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)

from src.services.task import TaskService


def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    return TaskService(
        task_repo=TaskRepository(db),
        task_list_repo=TaskListRepository(db),
        user_repo=UserRepository(db),
    )


class TaskController:
    def __init__(
        self,
        service: TaskService = Depends(get_task_service),
        current_user: UserModel = Depends(get_current_user),
    ):
        self.service = service
        self.current_user = current_user

    async def list_tasks(
        self,
        task_list_id: int,
        status: str | None,
        priority: str | None,
        page: int,
        size: int,
    ) -> TaskListTasksResponse:
        return await self.service.get_all(task_list_id, status, priority, page=page, size=size)

    async def get_one(self, task_id: int) -> TaskResponse:
        return await self.service.get_by_id(task_id)

    async def create(self, task_list_id: int, data: TaskCreateRequest) -> TaskResponse:
        return await self.service.create(
            task_list_id=task_list_id,
            title=data.title,
            description=data.description,
            priority=data.priority.value,
        )

    async def update(self, task_id: int, data: TaskUpdateRequest) -> TaskResponse:
        return await self.service.update(
            task_id=task_id,
            title=data.title,
            description=data.description,
            priority=data.priority.value if data.priority else None,
        )

    async def delete(self, task_id: int) -> None:
        await self.service.delete(task_id)

    async def change_status(
        self, task_id: int, data: TaskStatusUpdateRequest
    ) -> TaskResponse:
        return await self.service.change_status(task_id, data.status.value)

    async def assign(self, task_id: int, data: TaskAssignRequest) -> TaskResponse:
        return await self.service.assign(task_id, data.assignee_id)

    async def notify(self, task_id: int) -> dict:
        return await self.service.notify(task_id)
