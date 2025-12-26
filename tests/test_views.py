from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from pydantic import UUID4

from src.core.settings import ApplicationSettings


async def test_healthcheck(test_client: AsyncClient) -> None:
    response = await test_client.get("/health/check")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_login_with_default_scopes(
    settings: ApplicationSettings, test_client_id: UUID4, test_client: AsyncClient
) -> None:
    response = await test_client.get(
        "/oauth/authorize",
        params={"state": "test_state", "client_id": test_client_id.hex},
        follow_redirects=False,
    )
    assert response.status_code == 307
    redirect_url = urlparse(response.headers["location"])
    assert redirect_url.scheme == "https"
    assert redirect_url.netloc == "flow.polar.com"
    query_params = parse_qs(redirect_url.query)
    assert query_params["scope"] == [" ".join(settings.oauth.scopes.keys())]


async def test_login_with_custom_scopes(test_client: AsyncClient) -> None:
    response = await test_client.get(
        "/oauth/authorize",
        params={
            "state": "test_state",
            "client_id": "uuid@v4",
            "scope": "custom_scope",
        },
        follow_redirects=False,
    )
    assert response.status_code == 307
    redirect_url = urlparse(response.headers["location"])
    query_params = parse_qs(redirect_url.query)
    assert query_params["scope"] == ["custom_scope"]
    assert query_params["state"] == ["test_state"]


@pytest.mark.respx()
async def test_login_callback(
    respx_mock,
    seeded_state: str,
    test_client: AsyncClient,
    settings: ApplicationSettings,
) -> None:
    # Mock the external call to fetch the access token
    respx_mock.post(str(settings.oauth.access_token_url)).respond(
        json={
            "access_token": "test_access_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "user_id": 123,
        }
    )
    response = await test_client.get(
        "/oauth/callback", params={"code": "test_code", "state": seeded_state}
    )
    assert response.status_code == 307
    assert (
        response.headers["location"]
        == f"/docs/oauth2-redirect#state={seeded_state}&code=test_code"
    )
