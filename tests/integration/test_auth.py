from httpx import AsyncClient


async def test_register_returns_user_without_password(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"email": "nuevo@test.com", "password": "pass123", "full_name": "Nuevo Usuario"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "nuevo@test.com"
    assert data["full_name"] == "Nuevo Usuario"
    assert "hashed_password" not in data
    assert "password" not in data


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    payload = {"email": "dup@test.com", "password": "pass", "full_name": "Dup"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


async def test_login_returns_bearer_token(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "login@test.com", "password": "pass123", "full_name": "User"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "login@test.com", "password": "pass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"].split(".")) == 3


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "pass@test.com", "password": "correct", "full_name": "User"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "pass@test.com", "password": "equivocada"},
    )
    assert resp.status_code == 401


async def test_login_nonexistent_user_returns_401(client: AsyncClient):
    resp = await client.post(
        "/auth/login",
        json={"email": "noexiste@test.com", "password": "cualquiera"},
    )
    assert resp.status_code == 401


async def test_protected_endpoint_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/task-lists/")
    assert resp.status_code == 401


async def test_token_allows_access_to_protected_endpoints(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.get("/task-lists/", headers=auth_headers)
    assert resp.status_code == 200
