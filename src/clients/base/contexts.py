import httpx
from pydantic import BaseModel, ConfigDict


class Context(BaseModel):
    pass


class RequestContext[TParamModel](Context):
    params: TParamModel | None = None
    headers: dict[str, str] | httpx.Headers | None = None
    cookies: dict[str, str] | httpx.Cookies | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ResponseContext(BaseModel):
    response: httpx.Response

    model_config = ConfigDict(arbitrary_types_allowed=True)
