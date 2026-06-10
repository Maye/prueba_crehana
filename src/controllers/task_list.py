from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import UserModel
from src.database.session import get_db
from src.dependencies import get_current_user
from src.repositories.implementations.task_list import TaskListRepository
from src.schemas.task_list import (
    PaginatedTaskListResponse,
    TaskListCreateRequest,
    TaskListResponse,
    TaskListUpdateRequest,
)
from src.services.task_list import TaskListService


def get_task_list_service(db: AsyncSession = Depends(get_db)) -> TaskListService:
    return TaskListService(task_list_repo=TaskListRepository(db))


class TaskListController:
    def __init__(
        self,
        service: TaskListService = Depends(get_task_list_service),
        current_user: UserModel = Depends(get_current_user),
    ):
        self.service = service
        self.current_user = current_user

    async def list_all(self, page: int, size: int) -> PaginatedTaskListResponse:
        return await self.service.get_all(page=page, size=size)

    async def get_one(self, task_list_id: int) -> TaskListResponse:
        return await self.service.get_by_id(task_list_id)

    async def create(self, data: TaskListCreateRequest) -> TaskListResponse:
        return await self.service.create(
            title=data.title,
            description=data.description,
            owner_id=self.current_user.id,
        )

    async def update(
        self, task_list_id: int, data: TaskListUpdateRequest
    ) -> TaskListResponse:
        return await self.service.update(task_list_id, data.title, data.description)

    async def delete(self, task_list_id: int) -> None:
        return await self.service.delete(task_list_id)
