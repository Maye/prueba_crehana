import pytest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from src.exceptions.exceptions import TaskListNotFoundError
from src.schemas.task_list import PaginatedTaskListResponse
from src.services.task_list import TaskListService


def make_task_list(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "title": "Test List",
        "description": None,
        "owner_id": 1,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.fixture
def task_list_repo():
    return AsyncMock()


@pytest.fixture
def svc(task_list_repo):
    return TaskListService(task_list_repo=task_list_repo)


# --- get_all ---


async def test_get_all_returns_list(svc, task_list_repo):
    task_list_repo.get_all.return_value = [make_task_list(), make_task_list(id=2)]
    task_list_repo.count_all.return_value = 2

    result = await svc.get_all()

    assert isinstance(result, PaginatedTaskListResponse)
    assert len(result.items) == 2
    assert result.total == 2


async def test_get_all_empty(svc, task_list_repo):
    task_list_repo.get_all.return_value = []
    task_list_repo.count_all.return_value = 0

    result = await svc.get_all()

    assert result.items == []
    assert result.total == 0


async def test_get_all_pagination_fields(svc, task_list_repo):
    task_list_repo.get_all.return_value = [make_task_list()]
    task_list_repo.count_all.return_value = 45

    result = await svc.get_all(page=2, size=20)

    assert result.page == 2
    assert result.size == 20
    assert result.pages == 3


# --- get_by_id ---


async def test_get_by_id_found(svc, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(title="Mi Lista")

    result = await svc.get_by_id(1)

    assert result.id == 1
    assert result.title == "Mi Lista"


async def test_get_by_id_not_found(svc, task_list_repo):
    task_list_repo.get_by_id.return_value = None

    with pytest.raises(TaskListNotFoundError):
        await svc.get_by_id(99)


# --- create ---


async def test_create_success(svc, task_list_repo):
    task_list_repo.create.return_value = make_task_list(title="Nueva Lista")

    result = await svc.create(title="Nueva Lista", description=None, owner_id=1)

    assert result.title == "Nueva Lista"
    task_list_repo.create.assert_called_once_with(
        title="Nueva Lista", description=None, owner_id=1
    )


async def test_create_with_description(svc, task_list_repo):
    task_list_repo.create.return_value = make_task_list(description="Descripción")

    result = await svc.create(title="Lista", description="Descripción", owner_id=1)

    assert result.description == "Descripción"


# --- update ---


async def test_update_found(svc, task_list_repo):
    task_list_repo.update.return_value = make_task_list(title="Actualizada")

    result = await svc.update(1, title="Actualizada", description=None)

    assert result.title == "Actualizada"


async def test_update_not_found(svc, task_list_repo):
    task_list_repo.update.return_value = None

    with pytest.raises(TaskListNotFoundError):
        await svc.update(99, title="X", description=None)


# --- delete ---


async def test_delete_found(svc, task_list_repo):
    task_list_repo.delete.return_value = True

    await svc.delete(1)

    task_list_repo.delete.assert_called_once_with(1)


async def test_delete_not_found(svc, task_list_repo):
    task_list_repo.delete.return_value = False

    with pytest.raises(TaskListNotFoundError):
        await svc.delete(99)
