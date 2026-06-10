import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from httpx import ASGITransport, AsyncClient

from src.controllers.task import get_task_service
from src.dependencies import get_current_user
from src.exceptions.exceptions import TaskListNotFoundError, TaskNotFoundError, UserNotFoundError
from src.main import app
from src.schemas.task import TaskListTasksResponse, TaskResponse


def make_user():
    return SimpleNamespace(
        id=1,
        email="test@crehana.com",
        full_name="Test User",
        hashed_password="hashed",
        created_at=datetime.now(timezone.utc),
    )


def make_task_response(**kwargs):
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
    return TaskResponse(**defaults)


def make_tasks_response(**kwargs):
    defaults = {
        "tasks": [make_task_response()],
        "total": 1,
        "completion_percentage": 0.0,
        "page": 1,
        "size": 20,
        "pages": 1,
    }
    defaults.update(kwargs)
    return TaskListTasksResponse(**defaults)


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
async def client(mock_service):
    app.dependency_overrides[get_task_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --- GET /task-lists/{id}/tasks/ ---


async def test_list_tasks_returns_200(client, mock_service):
    mock_service.get_all.return_value = make_tasks_response(total=1)

    response = await client.get("/task-lists/1/tasks/")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["completion_percentage"] == 0.0


async def test_list_tasks_passes_filters(client, mock_service):
    mock_service.get_all.return_value = make_tasks_response(tasks=[], total=0)

    await client.get("/task-lists/1/tasks/?status=completed&priority=high")

    mock_service.get_all.assert_called_once_with(1, "completed", "high", page=1, size=20)


async def test_list_tasks_list_not_found_returns_404(client, mock_service):
    mock_service.get_all.side_effect = TaskListNotFoundError(99)

    response = await client.get("/task-lists/99/tasks/")

    assert response.status_code == 404


# --- POST /task-lists/{id}/tasks/ ---


async def test_create_task_returns_201(client, mock_service):
    mock_service.create.return_value = make_task_response(title="Nueva Tarea")

    response = await client.post(
        "/task-lists/1/tasks/", json={"title": "Nueva Tarea", "priority": "high"}
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Nueva Tarea"


async def test_create_task_default_priority_is_medium(client, mock_service):
    mock_service.create.return_value = make_task_response(priority="medium")

    await client.post("/task-lists/1/tasks/", json={"title": "Tarea"})

    call_kwargs = mock_service.create.call_args.kwargs
    assert call_kwargs["priority"] == "medium"


async def test_create_task_missing_title_returns_422(client):
    response = await client.post("/task-lists/1/tasks/", json={"priority": "high"})

    assert response.status_code == 422


async def test_create_task_invalid_priority_returns_422(client):
    response = await client.post(
        "/task-lists/1/tasks/", json={"title": "Test", "priority": "ultra"}
    )

    assert response.status_code == 422


# --- GET /task-lists/{id}/tasks/{task_id} ---


async def test_get_task_returns_200(client, mock_service):
    mock_service.get_by_id.return_value = make_task_response(id=5)

    response = await client.get("/task-lists/1/tasks/5")

    assert response.status_code == 200
    assert response.json()["id"] == 5


async def test_get_task_not_found_returns_404(client, mock_service):
    mock_service.get_by_id.side_effect = TaskNotFoundError(99)

    response = await client.get("/task-lists/1/tasks/99")

    assert response.status_code == 404


# --- PUT /task-lists/{id}/tasks/{task_id} ---


async def test_update_task_returns_200(client, mock_service):
    mock_service.update.return_value = make_task_response(title="Actualizada")

    response = await client.put("/task-lists/1/tasks/1", json={"title": "Actualizada"})

    assert response.status_code == 200
    assert response.json()["title"] == "Actualizada"


async def test_update_task_not_found_returns_404(client, mock_service):
    mock_service.update.side_effect = TaskNotFoundError(99)

    response = await client.put("/task-lists/1/tasks/99", json={"title": "X"})

    assert response.status_code == 404


# --- DELETE /task-lists/{id}/tasks/{task_id} ---


async def test_delete_task_returns_204(client, mock_service):
    mock_service.delete.return_value = None

    response = await client.delete("/task-lists/1/tasks/1")

    assert response.status_code == 204


async def test_delete_task_not_found_returns_404(client, mock_service):
    mock_service.delete.side_effect = TaskNotFoundError(99)

    response = await client.delete("/task-lists/1/tasks/99")

    assert response.status_code == 404


# --- PATCH /task-lists/{id}/tasks/{task_id}/status ---


async def test_change_status_returns_200(client, mock_service):
    mock_service.change_status.return_value = make_task_response(status="completed")

    response = await client.patch(
        "/task-lists/1/tasks/1/status", json={"status": "completed"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


async def test_change_status_invalid_value_returns_422(client):
    response = await client.patch(
        "/task-lists/1/tasks/1/status", json={"status": "invalid_status"}
    )

    assert response.status_code == 422


async def test_change_status_task_not_found_returns_404(client, mock_service):
    mock_service.change_status.side_effect = TaskNotFoundError(99)

    response = await client.patch(
        "/task-lists/1/tasks/99/status", json={"status": "completed"}
    )

    assert response.status_code == 404


# --- PATCH /task-lists/{id}/tasks/{task_id}/assign ---


async def test_assign_task_returns_200(client, mock_service):
    mock_service.assign.return_value = make_task_response(assignee_id=2)

    response = await client.patch(
        "/task-lists/1/tasks/1/assign", json={"assignee_id": 2}
    )

    assert response.status_code == 200
    assert response.json()["assignee_id"] == 2


async def test_assign_task_user_not_found_returns_404(client, mock_service):
    mock_service.assign.side_effect = UserNotFoundError(99)

    response = await client.patch(
        "/task-lists/1/tasks/1/assign", json={"assignee_id": 99}
    )

    assert response.status_code == 404


async def test_assign_task_not_found_returns_404(client, mock_service):
    mock_service.assign.side_effect = TaskNotFoundError(99)

    response = await client.patch(
        "/task-lists/1/tasks/99/assign", json={"assignee_id": 1}
    )

    assert response.status_code == 404


# --- POST /task-lists/{id}/tasks/{task_id}/notify ---


async def test_notify_returns_200(client, mock_service):
    mock_service.notify.return_value = {
        "message": "Notificación enviada para la tarea 'Test Task'"
    }

    response = await client.post("/task-lists/1/tasks/1/notify")

    assert response.status_code == 200
    assert "message" in response.json()


async def test_notify_task_not_found_returns_404(client, mock_service):
    mock_service.notify.side_effect = TaskNotFoundError(99)

    response = await client.post("/task-lists/1/tasks/99/notify")

    assert response.status_code == 404
