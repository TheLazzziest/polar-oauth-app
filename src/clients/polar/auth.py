from collections.abc import Generator

import httpx


class BearerAuth(httpx.Auth):
    def __init__(self, token: str, token_type: str = "Bearer"):
        self.token = token
        self.token_type = token_type

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response]:
        request.headers["Authorization"] = f"{self.token_type} {self.token}"
        yield request
