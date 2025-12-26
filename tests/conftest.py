import json
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import uuid4

import pytest
from _pytest.config.argparsing import Parser
from asgi_lifespan import LifespanManager
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import UUID4
from typer import Typer
from typer.testing import CliRunner

from src.cli import app as console
from src.clients.polar.client import PolarClient
from src.core.settings import ApplicationSettings
from src.web import app as web


# see: https://docs.pytest.org/en/stable/how-to/writing_hook_functions.html#using-hooks-in-pytest-addoption
def pytest_addoption(parser: Parser):
    parser.addoption(
        "--state",
        action="store",
        default=None,
        help="A path to the persisted state issued by Polar",
    )


@pytest.fixture(scope="session")
async def application() -> AsyncGenerator[FastAPI]:
    async with LifespanManager(web) as _:
        yield web


@pytest.fixture(scope="session")
def cli() -> Typer:
    return console


@pytest.fixture(scope="session")
async def settings(application: FastAPI) -> ApplicationSettings:
    return application.state.settings


@pytest.fixture(scope="session")
async def state(request) -> dict:
    return json.load(Path(request.config.getoption("--state")).open())


@pytest.fixture(scope="session")
async def test_client(application: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope="session")
async def test_polar_client(
    state: dict, settings: ApplicationSettings
) -> AsyncGenerator[PolarClient]:
    yield PolarClient(
        AsyncOAuth2Client(
            client_id=str(settings.oauth.client_id),
            client_secret=str(settings.oauth.client_secret),
            base_url=str(settings.oauth.accesslink_url),
            token=state,
        )
    )


@pytest.fixture(scope="session")
async def test_client_id() -> UUID4:
    return uuid4()


@pytest.fixture
async def seeded_state(test_client_id: UUID4, application: FastAPI) -> str:
    state = str(uuid4())
    conn = application.state.db
    conn.execute(
        "INSERT INTO tokens (client_id, session_id) VALUES (?, ?)",
        (test_client_id.hex, state),
    )
    return state
