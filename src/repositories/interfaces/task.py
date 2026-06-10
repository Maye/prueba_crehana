from abc import ABC, abstractmethod

from src.database.models.task import TaskModel


class TaskRepositoryInterface(ABC):
    @abstractmethod
    async def get_all(
        self,
        task_list_id: int,
        status: str | None = None,
        priority: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[TaskModel]: ...

    @abstractmethod
    async def count_all(
        self,
        task_list_id: int,
        status: str | None = None,
        priority: str | None = None,
    ) -> tuple[int, int]: ...

    @abstractmethod
    async def count_completed(self, task_list_id: int) -> int: ...

    @abstractmethod
    async def get_by_id(self, task_id: int) -> TaskModel | None: ...

    @abstractmethod
    async def create(
        self,
        task_list_id: int,
        title: str,
        description: str | None,
        priority: str,
    ) -> TaskModel: ...

    @abstractmethod
    async def update(
        self,
        task_id: int,
        title: str | None,
        description: str | None,
        priority: str | None,
        status: str | None,
        assignee_id: int | None,
    ) -> TaskModel | None: ...

    @abstractmethod
    async def delete(self, task_id: int) -> bool: ...
