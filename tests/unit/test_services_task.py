import pytest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from src.exceptions.exceptions import (
    TaskListNotFoundError,
    TaskNotFoundError,
    UserNotFoundError,
)
from src.services.task import TaskService


def make_task(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "task_list_id": 1,
        "title": "Test Task",
        "description": None,
        "status": "pending",
        "priority": "medium",
        "assignee_id": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_task_list(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "title": "Test List",
        "description": None,
        "owner_id": 1,
        "task_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_user(**kwargs):
    defaults = {
        "id": 1,
        "email": "test@test.com",
        "full_name": "Test",
        "hashed_password": "hashed",
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.fixture
def task_repo():
    return AsyncMock()


@pytest.fixture
def task_list_repo():
    return AsyncMock()


@pytest.fixture
def user_repo():
    return AsyncMock()


@pytest.fixture
def svc(task_repo, task_list_repo, user_repo):
    return TaskService(
        task_repo=task_repo,
        task_list_repo=task_list_repo,
        user_repo=user_repo,
    )


# --- get_all / completion_percentage ---


async def test_get_all_no_tasks_returns_zero_percent(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(task_count=0)
    task_repo.get_all.return_value = []
    task_repo.count_completed.return_value = 0

    result = await svc.get_all(1)

    assert result.total == 0
    assert result.completion_percentage == 0.0


async def test_get_all_partial_completion(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(task_count=3)
    task_repo.get_all.return_value = [
        make_task(status="completed"),
        make_task(id=2, status="pending"),
        make_task(id=3, status="pending"),
    ]
    task_repo.count_completed.return_value = 1

    result = await svc.get_all(1)

    assert result.total == 3
    assert result.completion_percentage == 33.33


async def test_get_all_full_completion(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(task_count=2)
    task_repo.get_all.return_value = [
        make_task(status="completed"),
        make_task(id=2, status="completed"),
    ]
    task_repo.count_completed.return_value = 2

    result = await svc.get_all(1)

    assert result.completion_percentage == 100.0


async def test_get_all_no_filters_uses_cached_count(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(task_count=50)
    task_repo.get_all.return_value = []
    task_repo.count_completed.return_value = 0

    result = await svc.get_all(1)

    assert result.total == 50
    task_repo.count_all.assert_not_called()


async def test_get_all_with_filters_uses_count_query(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(task_count=50)
    task_repo.get_all.return_value = []
    task_repo.count_all.return_value = (5, 2)

    result = await svc.get_all(1, status="completed", priority="high")

    assert result.total == 5
    task_repo.count_all.assert_called_once()
    task_repo.count_completed.assert_not_called()


async def test_get_all_passes_filters_to_repo(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(task_count=10)
    task_repo.get_all.return_value = []
    task_repo.count_all.return_value = (0, 0)

    await svc.get_all(1, status="completed", priority="high")

    task_repo.get_all.assert_called_once_with(1, "completed", "high", skip=0, limit=20)


async def test_get_all_pagination_fields(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list(task_count=45)
    task_repo.get_all.return_value = [make_task()]
    task_repo.count_completed.return_value = 10

    result = await svc.get_all(1, page=2, size=20)

    assert result.page == 2
    assert result.size == 20
    assert result.pages == 3


async def test_get_all_list_not_found(svc, task_list_repo):
    task_list_repo.get_by_id.return_value = None

    with pytest.raises(TaskListNotFoundError):
        await svc.get_all(99)


# --- get_by_id ---


async def test_get_by_id_found(svc, task_repo):
    task_repo.get_by_id.return_value = make_task(title="Mi Tarea")

    result = await svc.get_by_id(1)

    assert result.id == 1
    assert result.title == "Mi Tarea"


async def test_get_by_id_not_found(svc, task_repo):
    task_repo.get_by_id.return_value = None

    with pytest.raises(TaskNotFoundError):
        await svc.get_by_id(99)


# --- create ---


async def test_create_success(svc, task_repo, task_list_repo):
    task_list_repo.get_by_id.return_value = make_task_list()
    task_repo.create.return_value = make_task(title="Nueva Tarea")

    result = await svc.create(1, "Nueva Tarea", None, "high")

    assert result.title == "Nueva Tarea"
    task_repo.create.assert_called_once_with(1, "Nueva Tarea", None, "high")


async def test_create_list_not_found(svc, task_list_repo):
    task_list_repo.get_by_id.return_value = None

    with pytest.raises(TaskListNotFoundError):
        await svc.create(99, "Tarea", None, "medium")


# --- update ---


async def test_update_success(svc, task_repo):
    task_repo.update.return_value = make_task(title="Actualizada")

    result = await svc.update(1, title="Actualizada", description=None, priority=None)

    assert result.title == "Actualizada"


async def test_update_not_found(svc, task_repo):
    task_repo.update.return_value = None

    with pytest.raises(TaskNotFoundError):
        await svc.update(99, title="X", description=None, priority=None)


# --- delete ---


async def test_delete_success(svc, task_repo):
    task_repo.delete.return_value = True

    await svc.delete(1)

    task_repo.delete.assert_called_once_with(1)


async def test_delete_not_found(svc, task_repo):
    task_repo.delete.return_value = False

    with pytest.raises(TaskNotFoundError):
        await svc.delete(99)


# --- change_status ---


async def test_change_status_success(svc, task_repo):
    task_repo.update.return_value = make_task(status="completed")

    result = await svc.change_status(1, "completed")

    assert result.status == "completed"


async def test_change_status_not_found(svc, task_repo):
    task_repo.update.return_value = None

    with pytest.raises(TaskNotFoundError):
        await svc.change_status(99, "completed")


# --- assign ---


async def test_assign_success(svc, task_repo, user_repo):
    task_repo.get_by_id.return_value = make_task()
    user_repo.get_by_id.return_value = make_user(id=2)
    task_repo.update.return_value = make_task(assignee_id=2)

    result = await svc.assign(1, 2)

    assert result.assignee_id == 2


async def test_assign_task_not_found(svc, task_repo):
    task_repo.get_by_id.return_value = None

    with pytest.raises(TaskNotFoundError):
        await svc.assign(99, 1)


async def test_assign_user_not_found(svc, task_repo, user_repo):
    task_repo.get_by_id.return_value = make_task()
    user_repo.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await svc.assign(1, 99)


# --- notify ---


async def test_notify_success(svc, task_repo):
    task_repo.get_by_id.return_value = make_task(title="Tarea Importante")

    result = await svc.notify(1)

    assert "Tarea Importante" in result["message"]


async def test_notify_not_found(svc, task_repo):
    task_repo.get_by_id.return_value = None

    with pytest.raises(TaskNotFoundError):
        await svc.notify(99)
