import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from httpx import ASGITransport, AsyncClient

from src.controllers.auth import get_auth_service
from src.exceptions.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from src.main import app
from src.schemas.user import TokenResponse, UserResponse


def make_user_response(**kwargs):
    defaults = {
        "id": 1,
        "email": "test@crehana.com",
        "full_name": "Test User",
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return UserResponse(**defaults)


@pytest.fixture
def mock_auth_service():
    return AsyncMock()


@pytest.fixture
async def client(mock_auth_service):
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --- POST /auth/register ---


async def test_register_returns_201(client, mock_auth_service):
    mock_auth_service.register.return_value = make_user_response()

    response = await client.post(
        "/auth/register",
        json={"email": "test@crehana.com", "password": "pass123", "full_name": "Test User"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@crehana.com"
    assert response.json()["id"] == 1


async def test_register_returns_user_data(client, mock_auth_service):
    mock_auth_service.register.return_value = make_user_response(
        full_name="Juan Pérez", email="juan@test.com"
    )

    response = await client.post(
        "/auth/register",
        json={"email": "juan@test.com", "password": "pass123", "full_name": "Juan Pérez"},
    )

    assert response.json()["full_name"] == "Juan Pérez"
    assert "hashed_password" not in response.json()


async def test_register_email_conflict_returns_409(client, mock_auth_service):
    mock_auth_service.register.side_effect = EmailAlreadyExistsError("test@crehana.com")

    response = await client.post(
        "/auth/register",
        json={"email": "test@crehana.com", "password": "pass123", "full_name": "Test"},
    )

    assert response.status_code == 409
    assert "test@crehana.com" in response.json()["detail"]


async def test_register_invalid_email_returns_422(client):
    response = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "pass123", "full_name": "Test"},
    )

    assert response.status_code == 422


async def test_register_missing_fields_returns_422(client):
    response = await client.post("/auth/register", json={"email": "test@test.com"})

    assert response.status_code == 422


# --- POST /auth/login ---


async def test_login_returns_token(client, mock_auth_service):
    mock_auth_service.login.return_value = TokenResponse(access_token="fake.jwt.token")

    response = await client.post(
        "/auth/login",
        json={"email": "test@crehana.com", "password": "pass123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "fake.jwt.token"
    assert response.json()["token_type"] == "bearer"


async def test_login_invalid_credentials_returns_401(client, mock_auth_service):
    mock_auth_service.login.side_effect = InvalidCredentialsError()

    response = await client.post(
        "/auth/login",
        json={"email": "test@crehana.com", "password": "wrong"},
    )

    assert response.status_code == 401
