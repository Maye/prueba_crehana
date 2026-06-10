import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.task_list import TaskListModel


@pytest.fixture
async def task_list(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        "/task-lists/", json={"title": "Lista de prueba"}, headers=auth_headers
    )
    return resp.json()


async def test_create_task_returns_201_with_defaults(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    resp = await client.post(
        f"/task-lists/{task_list['id']}/tasks/",
        json={"title": "Mi Tarea", "priority": "high"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Mi Tarea"
    assert data["priority"] == "high"
    assert data["status"] == "pending"
    assert data["assignee_id"] is None


async def test_create_task_increments_task_count(
    client: AsyncClient,
    auth_headers: dict,
    task_list: dict,
    db_session: AsyncSession,
):
    task_list_id = task_list["id"]
    for i in range(3):
        await client.post(
            f"/task-lists/{task_list_id}/tasks/",
            json={"title": f"Tarea {i}"},
            headers=auth_headers,
        )

    result = await db_session.execute(
        select(TaskListModel).where(TaskListModel.id == task_list_id)
    )
    assert result.scalar_one().task_count == 3


async def test_delete_task_decrements_task_count(
    client: AsyncClient,
    auth_headers: dict,
    task_list: dict,
    db_session: AsyncSession,
):
    task_list_id = task_list["id"]
    create_resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Borrar esto"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    await client.delete(
        f"/task-lists/{task_list_id}/tasks/{task_id}", headers=auth_headers
    )

    result = await db_session.execute(
        select(TaskListModel).where(TaskListModel.id == task_list_id)
    )
    assert result.scalar_one().task_count == 0


async def test_list_tasks_returns_paginated_response(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]
    for i in range(5):
        await client.post(
            f"/task-lists/{task_list_id}/tasks/",
            json={"title": f"Tarea {i}"},
            headers=auth_headers,
        )

    resp = await client.get(
        f"/task-lists/{task_list_id}/tasks/?page=1&size=3", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["pages"] == 2
    assert len(data["tasks"]) == 3


async def test_list_tasks_filter_by_status(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]

    for i in range(2):
        await client.post(
            f"/task-lists/{task_list_id}/tasks/",
            json={"title": f"Pendiente {i}"},
            headers=auth_headers,
        )
    create_resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Completada"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]
    await client.patch(
        f"/task-lists/{task_list_id}/tasks/{task_id}/status",
        json={"status": "completed"},
        headers=auth_headers,
    )

    resp = await client.get(
        f"/task-lists/{task_list_id}/tasks/?status=completed", headers=auth_headers
    )
    data = resp.json()
    assert data["total"] == 1
    assert all(t["status"] == "completed" for t in data["tasks"])


async def test_list_tasks_filter_by_priority(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]

    await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Alta", "priority": "high"},
        headers=auth_headers,
    )
    await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Media", "priority": "medium"},
        headers=auth_headers,
    )
    await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Alta 2", "priority": "high"},
        headers=auth_headers,
    )

    resp = await client.get(
        f"/task-lists/{task_list_id}/tasks/?priority=high", headers=auth_headers
    )
    data = resp.json()
    assert data["total"] == 2
    assert all(t["priority"] == "high" for t in data["tasks"])


async def test_completion_percentage_calculation(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]

    task_ids = []
    for i in range(3):
        r = await client.post(
            f"/task-lists/{task_list_id}/tasks/",
            json={"title": f"Tarea {i}"},
            headers=auth_headers,
        )
        task_ids.append(r.json()["id"])

    await client.patch(
        f"/task-lists/{task_list_id}/tasks/{task_ids[0]}/status",
        json={"status": "completed"},
        headers=auth_headers,
    )

    resp = await client.get(f"/task-lists/{task_list_id}/tasks/", headers=auth_headers)
    assert resp.json()["completion_percentage"] == 33.33


async def test_update_task(client: AsyncClient, auth_headers: dict, task_list: dict):
    task_list_id = task_list["id"]
    create_resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Original", "priority": "low"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    resp = await client.put(
        f"/task-lists/{task_list_id}/tasks/{task_id}",
        json={"title": "Actualizada", "priority": "high"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Actualizada"
    assert resp.json()["priority"] == "high"


async def test_change_task_status(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]
    create_resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Tarea"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/task-lists/{task_list_id}/tasks/{task_id}/status",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_assign_task_to_another_user(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    reg_resp = await client.post(
        "/auth/register",
        json={"email": "asignee@test.com", "password": "pass", "full_name": "Asignee"},
    )
    assignee_id = reg_resp.json()["id"]

    task_list_id = task_list["id"]
    create_resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Tarea a asignar"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/task-lists/{task_list_id}/tasks/{task_id}/assign",
        json={"assignee_id": assignee_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["assignee_id"] == assignee_id


async def test_assign_task_to_nonexistent_user_returns_404(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]
    create_resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Tarea"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/task-lists/{task_list_id}/tasks/{task_id}/assign",
        json={"assignee_id": 99999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_create_task_in_nonexistent_list_returns_404(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.post(
        "/task-lists/99999/tasks/",
        json={"title": "Tarea"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_notify_task_returns_message(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]
    create_resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Tarea Importante"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    resp = await client.post(
        f"/task-lists/{task_list_id}/tasks/{task_id}/notify",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "message" in resp.json()
