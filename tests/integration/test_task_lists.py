import pytest
from httpx import AsyncClient


@pytest.fixture
async def task_list(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        "/task-lists/", json={"title": "Lista de prueba"}, headers=auth_headers
    )
    return resp.json()


async def test_create_task_list_returns_201(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/task-lists/", json={"title": "Mi Lista"}, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Mi Lista"
    assert "id" in data


async def test_create_task_list_sets_current_user_as_owner(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.post(
        "/task-lists/", json={"title": "Lista"}, headers=auth_headers
    )
    assert resp.json()["owner_id"] is not None


async def test_list_task_lists_returns_paginated_response(
    client: AsyncClient, auth_headers: dict
):
    for i in range(3):
        await client.post(
            "/task-lists/", json={"title": f"Lista {i}"}, headers=auth_headers
        )

    resp = await client.get("/task-lists/?page=1&size=2", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["pages"] == 2
    assert len(data["items"]) == 2


async def test_list_task_lists_second_page(client: AsyncClient, auth_headers: dict):
    for i in range(3):
        await client.post(
            "/task-lists/", json={"title": f"Lista {i}"}, headers=auth_headers
        )

    resp = await client.get("/task-lists/?page=2&size=2", headers=auth_headers)
    data = resp.json()
    assert len(data["items"]) == 1


async def test_get_task_list_by_id(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    resp = await client.get(f"/task-lists/{task_list['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_list["id"]
    assert resp.json()["title"] == "Lista de prueba"


async def test_get_nonexistent_task_list_returns_404(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.get("/task-lists/99999", headers=auth_headers)
    assert resp.status_code == 404


async def test_update_task_list(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    resp = await client.put(
        f"/task-lists/{task_list['id']}",
        json={"title": "Actualizada", "description": "Con descripción"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Actualizada"
    assert resp.json()["description"] == "Con descripción"


async def test_delete_task_list_returns_204(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    resp = await client.delete(f"/task-lists/{task_list['id']}", headers=auth_headers)
    assert resp.status_code == 204

    get_resp = await client.get(f"/task-lists/{task_list['id']}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_delete_task_list_cascades_to_tasks(
    client: AsyncClient, auth_headers: dict, task_list: dict
):
    task_list_id = task_list["id"]
    await client.post(
        f"/task-lists/{task_list_id}/tasks/",
        json={"title": "Tarea"},
        headers=auth_headers,
    )

    await client.delete(f"/task-lists/{task_list_id}", headers=auth_headers)

    resp = await client.get(f"/task-lists/{task_list_id}/tasks/", headers=auth_headers)
    assert resp.status_code == 404
