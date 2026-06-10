from abc import ABC, abstractmethod

from src.database.models.task_list import TaskListModel


class TaskListRepositoryInterface(ABC):
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 20) -> list[TaskListModel]: ...

    @abstractmethod
    async def count_all(self) -> int: ...

    @abstractmethod
    async def get_by_id(self, task_list_id: int) -> TaskListModel | None: ...

    @abstractmethod
    async def create(
        self, title: str, description: str | None, owner_id: int | None
    ) -> TaskListModel: ...

    @abstractmethod
    async def update(
        self, task_list_id: int, title: str | None, description: str | None
    ) -> TaskListModel | None: ...

    @abstractmethod
    async def delete(self, task_list_id: int) -> bool: ...
