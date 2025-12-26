from typing import Protocol

import httpx

from .models import EndpointRequest, RouteMeta


class Routable(Protocol):
    _route_info: RouteMeta

    @property
    def __name__(self) -> str: ...
    def __call__(self, *args, **kwargs) -> None: ...


class AsyncClientProtocol(Protocol):
    async def send(self, request: EndpointRequest) -> httpx.Response: ...
