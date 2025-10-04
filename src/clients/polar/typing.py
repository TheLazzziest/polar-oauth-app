from collections.abc import Sequence
from typing import IO, Annotated, Protocol, TypeVar

import httpx
import pydantic

from .models import EndpointConfig, HttpMethStr

EndpointArgT = TypeVar("EndpointArgT", str, int, float)
ClientT = TypeVar("ClientT", httpx.Client, httpx.AsyncClient)


class EndpointCallable(Protocol):
    """A protocol for callables that have endpoint metadata."""

    __endpoints__: Sequence[EndpointConfig]

    def __call__(
        self,
        *args: tuple[EndpointArgT, ...],
        query: pydantic.BaseModel | None,
        headers: httpx.Headers | None,
        body: pydantic.BaseModel | None,
    ) -> pydantic.BaseModel | IO | None: ...


class HTTPClient[ClientT]:
    client: ClientT
    registry: dict[str, EndpointCallable]

    async def request(
        self,
        method: Annotated[str, HttpMethStr],
        path: str,
        query_params: pydantic.BaseModel | None = None,
        headers: httpx.Headers | None = None,
        body: pydantic.BaseModel | None = None,
        **kwargs,
    ) -> httpx.Response: ...
