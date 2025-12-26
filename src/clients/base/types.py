from typing import (
    Literal,
    TypeVar,
)

import httpx

from .fields import PathTemplate

HTTPMeth = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
ResponseT = TypeVar("ResponseT", bound=httpx.Response)
RouteKey = tuple[HTTPMeth, PathTemplate]
