from httpx import AsyncClient


async def test_healthcheck(test_client: AsyncClient) -> None:
    response = await test_client.get("/health/check")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
