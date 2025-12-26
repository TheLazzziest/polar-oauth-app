from abc import ABC, abstractmethod

import httpx
import pydantic
from authlib.integrations.httpx_client import AsyncOAuth2Client

from .descriptors import EndpointCommand
from .fields import PathTemplate
from .models import EndpointRequest
from .traits import Discoverable, Transportable
from .types import HTTPMeth


class AsyncClient(Discoverable, Transportable[AsyncOAuth2Client], ABC):
    @abstractmethod
    async def send(self, request: EndpointRequest) -> httpx.Response:
        raise NotImplementedError

    async def __call__(
        self,
        method: HTTPMeth,
        path: PathTemplate,
        *,
        params: pydantic.BaseModel,
        headers: httpx.Headers,
        **kwargs,
    ) -> EndpointCommand:
        """Dynamic dispatch for the client."""
        try:
            # The registry now holds the descriptor instance directly
            descriptor: EndpointCommand = self.registry[(method, path)]
            # Call the descriptor, passing the client instance
            return descriptor(self, **kwargs, query_model=params, headers=headers)
        except KeyError:
            raise ValueError(f"No route found for {method} {path}")
