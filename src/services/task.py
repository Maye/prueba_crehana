import asyncio
import logging
import math

from src.exceptions.exceptions import (
    TaskListNotFoundError,
    TaskNotFoundError,
    UserNotFoundError,
)
from src.repositories.interfaces.task import TaskRepositoryInterface
from src.repositories.interfaces.task_list import TaskListRepositoryInterface
from src.repositories.interfaces.user import UserRepositoryInterface
from src.schemas.task import TaskListTasksResponse, TaskResponse

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepositoryInterface,
        task_list_repo: TaskListRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.task_repo = task_repo
        self.task_list_repo = task_list_repo
        self.user_repo = user_repo

    async def get_all(
        self,
        task_list_id: int,
        status: str | None = None,
        priority: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> TaskListTasksResponse:
        task_list = await self.task_list_repo.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)
        skip = (page - 1) * size
        has_filters = status is not None or priority is not None
        if has_filters:
            tasks, (total, completed) = await asyncio.gather(
                self.task_repo.get_all(task_list_id, status, priority, skip=skip, limit=size),
                self.task_repo.count_all(task_list_id, status, priority),
            )
        else:
            total = task_list.task_count
            tasks, completed = await asyncio.gather(
                self.task_repo.get_all(task_list_id, None, None, skip=skip, limit=size),
                self.task_repo.count_completed(task_list_id),
            )
        percentage = round((completed / total) * 100, 2) if total > 0 else 0.0
        return TaskListTasksResponse(
            tasks=[TaskResponse.model_validate(t) for t in tasks],
            total=total,
            completion_percentage=percentage,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 1,
        )

    async def get_by_id(self, task_id: int) -> TaskResponse:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        return TaskResponse.model_validate(task)

    async def create(
        self,
        task_list_id: int,
        title: str,
        description: str | None,
        priority: str,
    ) -> TaskResponse:
        task_list = await self.task_list_repo.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)
        task = await self.task_repo.create(task_list_id, title, description, priority)
        return TaskResponse.model_validate(task)

    async def update(
        self,
        task_id: int,
        title: str | None,
        description: str | None,
        priority: str | None,
    ) -> TaskResponse:
        task = await self.task_repo.update(
            task_id,
            title=title,
            description=description,
            priority=priority,
            status=None,
            assignee_id=None,
        )
        if not task:
            raise TaskNotFoundError(task_id)
        return TaskResponse.model_validate(task)

    async def delete(self, task_id: int) -> None:
        deleted = await self.task_repo.delete(task_id)
        if not deleted:
            raise TaskNotFoundError(task_id)

    async def change_status(self, task_id: int, status: str) -> TaskResponse:
        task = await self.task_repo.update(
            task_id,
            title=None,
            description=None,
            priority=None,
            status=status,
            assignee_id=None,
        )
        if not task:
            raise TaskNotFoundError(task_id)
        return TaskResponse.model_validate(task)

    async def assign(self, task_id: int, assignee_id: int) -> TaskResponse:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        user = await self.user_repo.get_by_id(assignee_id)
        if not user:
            raise UserNotFoundError(assignee_id)
        updated = await self.task_repo.update(
            task_id,
            title=None,
            description=None,
            priority=None,
            status=None,
            assignee_id=assignee_id,
        )
        return TaskResponse.model_validate(updated)

    async def notify(self, task_id: int) -> dict:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        logger.info(
            "[NOTIFICACIÓN FICTICIA] Invitación enviada para la tarea '%s' (id=%s)",
            task.title,
            task.id,
        )
        return {"message": f"Notificación enviada para la tarea '{task.title}'"}
