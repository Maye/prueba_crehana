import asyncio
import math

from src.exceptions.exceptions import TaskListNotFoundError
from src.repositories.interfaces.task_list import TaskListRepositoryInterface
from src.schemas.task_list import PaginatedTaskListResponse, TaskListResponse


class TaskListService:
    def __init__(self, task_list_repo: TaskListRepositoryInterface):
        self.task_list_repo = task_list_repo

    async def get_all(self, page: int = 1, size: int = 20) -> PaginatedTaskListResponse:
        skip = (page - 1) * size
        task_lists, total = await asyncio.gather(
            self.task_list_repo.get_all(skip=skip, limit=size),
            self.task_list_repo.count_all(),
        )
        return PaginatedTaskListResponse(
            items=[TaskListResponse.model_validate(tl) for tl in task_lists],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 1,
        )

    async def get_by_id(self, task_list_id: int) -> TaskListResponse:
        task_list = await self.task_list_repo.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)
        return TaskListResponse.model_validate(task_list)

    async def create(
        self, title: str, description: str | None, owner_id: int | None
    ) -> TaskListResponse:
        task_list = await self.task_list_repo.create(
            title=title, description=description, owner_id=owner_id
        )
        return TaskListResponse.model_validate(task_list)

    async def update(
        self, task_list_id: int, title: str | None, description: str | None
    ) -> TaskListResponse:
        task_list = await self.task_list_repo.update(task_list_id, title, description)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)
        return TaskListResponse.model_validate(task_list)

    async def delete(self, task_list_id: int) -> None:
        deleted = await self.task_list_repo.delete(task_list_id)
        if not deleted:
            raise TaskListNotFoundError(task_list_id)
