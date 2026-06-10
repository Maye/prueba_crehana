import pytest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from src.config.security import hash_password
from src.exceptions.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from src.services.auth import AuthService


def make_user(**kwargs):
    defaults = {
        "id": 1,
        "email": "test@crehana.com",
        "full_name": "Test User",
        "hashed_password": hash_password("pass123"),
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.fixture
def user_repo():
    return AsyncMock()


@pytest.fixture
def svc(user_repo):
    return AuthService(user_repo=user_repo)


# --- register ---


async def test_register_success(svc, user_repo):
    user_repo.get_by_email.return_value = None
    user_repo.create.return_value = make_user()

    result = await svc.register(
        email="test@crehana.com", password="pass123", full_name="Test User"
    )

    assert result.email == "test@crehana.com"
    assert result.id == 1
    user_repo.create.assert_called_once()


async def test_register_hashes_password(svc, user_repo):
    user_repo.get_by_email.return_value = None
    user_repo.create.return_value = make_user()

    await svc.register(email="test@crehana.com", password="pass123", full_name="Test")

    call_kwargs = user_repo.create.call_args.kwargs
    assert call_kwargs["hashed_password"] != "pass123"


async def test_register_email_already_exists(svc, user_repo):
    user_repo.get_by_email.return_value = make_user()

    with pytest.raises(EmailAlreadyExistsError):
        await svc.register(
            email="test@crehana.com", password="pass123", full_name="Test"
        )
    user_repo.create.assert_not_called()


# --- login ---


async def test_login_success(svc, user_repo):
    user_repo.get_by_email.return_value = make_user(
        hashed_password=hash_password("pass123")
    )

    result = await svc.login(email="test@crehana.com", password="pass123")

    assert result.access_token
    assert result.token_type == "bearer"


async def test_login_user_not_found(svc, user_repo):
    user_repo.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await svc.login(email="noexiste@test.com", password="pass123")


async def test_login_wrong_password(svc, user_repo):
    user_repo.get_by_email.return_value = make_user(
        hashed_password=hash_password("correct_pass")
    )

    with pytest.raises(InvalidCredentialsError):
        await svc.login(email="test@crehana.com", password="wrong_pass")


async def test_login_token_contains_user_id(svc, user_repo):
    from src.config.security import decode_access_token

    user_repo.get_by_email.return_value = make_user(id=42)

    result = await svc.login(email="test@crehana.com", password="pass123")
    payload = decode_access_token(result.access_token)

    assert payload["sub"] == "42"
    assert payload["email"] == "test@crehana.com"
