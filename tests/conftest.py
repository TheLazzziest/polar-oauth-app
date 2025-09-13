from collections.abc import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.web import app


@pytest.fixture(scope="session")
async def application() -> AsyncGenerator[FastAPI]:
    async with LifespanManager(app) as _:
        yield app


@pytest.fixture(scope="session")
async def test_client(application: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://testserver"
    ) as client:
        yield client
