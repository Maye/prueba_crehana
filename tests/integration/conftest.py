import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import src.database.models  # noqa: F401 — registra todos los modelos en Base.metadata
from src.database.base import Base
from src.database.session import get_db
from src.main import app

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/crehana_test"


@pytest.fixture(scope="session")
async def test_db():
    """Crea la DB de test y el engine UNA vez por sesión; mismo event loop que los tests."""
    conn = await asyncpg.connect(
        host="localhost",
        port=5434,
        user="postgres",
        password="postgres",
        database="postgres",
    )
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = 'crehana_test'"
    )
    if not exists:
        await conn.execute("CREATE DATABASE crehana_test")
    await conn.close()

    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables(test_db):
    """Trunca todas las tablas después de cada test."""
    yield
    async with test_db.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def client(test_db):
    """Cliente HTTP con get_db sobreescrito al engine de test."""
    session_factory = async_sessionmaker(test_db, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def db_session(test_db):
    """Sesión directa a crehana_test para verificar estado real de la DB."""
    session_factory = async_sessionmaker(test_db, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Registra un usuario y retorna los headers de autorización."""
    await client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "testpassword",
            "full_name": "Integration User",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "testpassword"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
