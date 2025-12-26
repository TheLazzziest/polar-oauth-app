from collections.abc import Callable
from typing import Annotated

import httpx
import pydantic

from .fields import PathTemplate
from .types import HTTPMeth


class RouteMeta[ResponseT](pydantic.BaseModel):
    """A route metadata container for an endpoint command"""

    method: HTTPMeth
    path: Annotated[str, PathTemplate]
    params: pydantic.BaseModel | None = None
    headers: httpx.Headers | None = None

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    def build_command(self, stub: Callable, member: Callable):
        from .descriptors import EndpointCommand

        return EndpointCommand[ResponseT](self, stub, member)


class EndpointRequest(pydantic.BaseModel):
    method: HTTPMeth
    url: str
    params: pydantic.BaseModel | None = None
    headers: httpx.Headers | None = None

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
