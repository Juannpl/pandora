import os
from uuid import uuid4

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Ne jamais utiliser la configuration locale ou la base applicative.
os.environ["SECRET_KEY"] = "pandora-test-signing-key-for-tests-only"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://unused:unused@localhost/unused"

import main
from db.database import get_db


@pytest_asyncio.fixture
async def client(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    engine = create_async_engine(url)
    schema = None
    try:
        if engine.dialect.name == "postgresql":
            schema = f"test_{uuid4().hex}"
            async with engine.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            engine = engine.execution_options(schema_translate_map={None: schema})
        sessions = async_sessionmaker(engine, expire_on_commit=False)

        async def test_db():
            async with sessions() as session:
                yield session

        monkeypatch.setattr(main, "engine", engine)
        main.app.dependency_overrides[get_db] = test_db
        # Exécute aussi le démarrage réel de l’application et la création des tables.
        async with LifespanManager(main.app):
            async with AsyncClient(
                transport=ASGITransport(app=main.app), base_url="http://test"
            ) as http_client:
                yield http_client
    finally:
        main.app.dependency_overrides.pop(get_db, None)
        if schema:
            async with engine.begin() as connection:
                await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await engine.dispose()
