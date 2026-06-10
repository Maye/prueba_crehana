import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from httpx import ASGITransport, AsyncClient

from src.controllers.task_list import get_task_list_service
from src.dependencies import get_current_user
from src.exceptions.exceptions import TaskListNotFoundError
from src.main import app
from src.schemas.task_list import PaginatedTaskListResponse, TaskListResponse


def make_user():
    return SimpleNamespace(
        id=1,
        email="test@crehana.com",
        full_name="Test User",
        hashed_password="hashed",
        created_at=datetime.now(timezone.utc),
    )


def make_task_list_response(**kwargs):
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
    return TaskListResponse(**defaults)


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
async def client(mock_service):
    app.dependency_overrides[get_task_list_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --- GET /task-lists/ ---


async def test_list_task_lists_returns_200(client, mock_service):
    mock_service.get_all.return_value = PaginatedTaskListResponse(
        items=[make_task_list_response(), make_task_list_response(id=2, title="Segunda Lista")],
        total=2,
        page=1,
        size=20,
        pages=1,
    )

    response = await client.get("/task-lists/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    assert response.json()["total"] == 2


async def test_list_task_lists_empty(client, mock_service):
    mock_service.get_all.return_value = PaginatedTaskListResponse(
        items=[], total=0, page=1, size=20, pages=1
    )

    response = await client.get("/task-lists/")

    assert response.status_code == 200
    assert response.json()["items"] == []


# --- POST /task-lists/ ---


async def test_create_task_list_returns_201(client, mock_service):
    mock_service.create.return_value = make_task_list_response(title="Nueva Lista")

    response = await client.post("/task-lists/", json={"title": "Nueva Lista"})

    assert response.status_code == 201
    assert response.json()["title"] == "Nueva Lista"


async def test_create_task_list_sets_owner(client, mock_service):
    mock_service.create.return_value = make_task_list_response(owner_id=1)

    await client.post("/task-lists/", json={"title": "Lista"})

    call_kwargs = mock_service.create.call_args.kwargs
    assert call_kwargs["owner_id"] == 1


async def test_create_task_list_missing_title_returns_422(client):
    response = await client.post("/task-lists/", json={"description": "sin titulo"})

    assert response.status_code == 422


# --- GET /task-lists/{id} ---


async def test_get_task_list_returns_200(client, mock_service):
    mock_service.get_by_id.return_value = make_task_list_response(id=5)

    response = await client.get("/task-lists/5")

    assert response.status_code == 200
    assert response.json()["id"] == 5


async def test_get_task_list_not_found_returns_404(client, mock_service):
    mock_service.get_by_id.side_effect = TaskListNotFoundError(99)

    response = await client.get("/task-lists/99")

    assert response.status_code == 404
    assert "99" in response.json()["detail"]


# --- PUT /task-lists/{id} ---


async def test_update_task_list_returns_200(client, mock_service):
    mock_service.update.return_value = make_task_list_response(title="Actualizada")

    response = await client.put("/task-lists/1", json={"title": "Actualizada"})

    assert response.status_code == 200
    assert response.json()["title"] == "Actualizada"


async def test_update_task_list_not_found_returns_404(client, mock_service):
    mock_service.update.side_effect = TaskListNotFoundError(99)

    response = await client.put("/task-lists/99", json={"title": "X"})

    assert response.status_code == 404


# --- DELETE /task-lists/{id} ---


async def test_delete_task_list_returns_204(client, mock_service):
    mock_service.delete.return_value = None

    response = await client.delete("/task-lists/1")

    assert response.status_code == 204


async def test_delete_task_list_not_found_returns_404(client, mock_service):
    mock_service.delete.side_effect = TaskListNotFoundError(99)

    response = await client.delete("/task-lists/99")

    assert response.status_code == 404
