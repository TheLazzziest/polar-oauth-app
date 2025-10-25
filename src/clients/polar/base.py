import inspect
from collections.abc import Awaitable, Callable, Iterable
from string import Template
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    Optional,
    TypeVar,
    Union,
    get_overloads,
)

import httpx
import pydantic
from gpxpy.gpx import GPX
from tcxreader.tcxreader import TCXExercise

from .fields import PathTemplate

HTTPMeth = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
ClientT = TypeVar("ClientT", httpx.Client, httpx.AsyncClient)
ParamT = TypeVar("ParamT", bound=pydantic.BaseModel | type)
ResponseT = TypeVar(
    "ResponseT", bound=pydantic.BaseModel | GPX |  TCXExercise | type
)


class RouteInfo(pydantic.BaseModel):
    """Stores info from the @route(...) decorator."""

    method: HTTPMeth
    path: Annotated[str, PathTemplate]
    params_model: type[pydantic.BaseModel] | None = None
    response_model: (
        type[pydantic.BaseModel] |
        type[GPX] |
        type[TCXExercise] |
        Any # @TODO: In case we need to pass something more complex
    ) = None

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    def __call__(self, func: Callable) -> Callable:
        if not hasattr(func, "_route_info"):
            setattr(func, "_route_info", self)
        return func


class BoundDispatcher[ClientT]:
    """
    It holds the client instance and performs overload resolution
    at call time.
    """

    def __init__(
        self,
        instance: "HTTPClient[ClientT]",
        handler_name: str,
        routes: dict[tuple[str,str],Callable],
        handler: Callable
    ):
        self._instance = instance
        self._handler_name = handler_name
        self._routes = routes
        self._handler = handler

    async def __call__(self, method: str, path: str, *args: Any, **kwargs: Any) -> Any:
        try:
            stub = self._routes[(method, path)]
            sig = inspect.signature(stub)
            bound_args = sig.bind(self._instance, *args, **kwargs)
        except KeyError:
            raise ValueError(
                f"The method doesn't not exists for the given path {(method,path)}"
            )
        except TypeError as e:
            raise ValueError(f"Argumnents for the given endpoints are mismatched: {e}")
        else:
            bound_args.apply_defaults()
            call_args = bound_args.arguments
            call_args.pop("self", None)

        if not hasattr(stub, "_route_info"):
            raise TypeError(f"Overload {stub} for {self.name} is missing a @route decorator")

        selected_route: RouteInfo = stub._route_info

        path_args = {}
        path_templ = Template(selected_route.path)
        for arg_name, arg_value in call_args.items():

            if arg_value is None:
                continue

            if f"{{{arg_name}}}" in selected_route.path:
                path_args[arg_name] = arg_value


        if path_args:
            try:
                path = path_templ.substitute(**path_args)
            except KeyError as e:
                raise TypeError(
                    f"Missing required path parameter {e} for route: {selected_route.path}" # noqa: E501
                )

        response = self._instance.request(
            method=selected_route.method,
            url=str(path),
            **bound_args.kwargs
        )

        if inspect.iscoroutine(response):
            response = await response

        ret_value = self._handler(response)

        if inspect.iscoroutine(ret_value):
            ret_value = await ret_value

        return ret_value


class EndpointDescriptor[ClientT]:
    """
    A descriptor that holds all configurations for a handler and dispatches 
    to the correct wrapper based on runtime arguments.
    """

    def __init__(
        self,
        handler_name: str,
        routes: dict[tuple[str,str],RouteInfo],
        overloads: list[Callable],
        original_handler: Callable
    ):
        self._handler_name = handler_name
        self._routes = routes
        self._overloads = overloads
        self._original_handler = original_handler
        self._dispatcher_cache = None

    def __get__(
        self,
        instance: Optional["HTTPClient[ClientT]"],
        owner: type["HTTPClient[ClientT]"]
    ) -> Callable[..., Awaitable[Any]]:
        """
        Called when the method is accessed (e.g., client.get_exercise).
        Binds the method to the client instance and returns the dispatcher.
        """
        if instance is None:
            # Access via class (PolarClient.get_exercise) - return self for introspection
            return self

        return BoundDispatcher(
            instance,
            self._handler_name,
            self._routes,
            self._overloads,
            self._original_handler
        )


class HTTPClient[ClientT]:
    registry: ClassVar[dict[tuple[str,str], Callable[..., Awaitable[ResponseT]]]] = {}
    transport: ClientT

    def __init__(self, transport: ClientT) -> None:
        self.transport = transport

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        for name, member in inspect.getmembers(cls):
            if not (callable(member) and inspect.iscoroutinefunction(member)):
                continue

            overloads = get_overloads(member)
            if not overloads:
                continue

            # --- We found an endpoint ---
            # 'member' is the *real implementation* (e.g., def list_exercises(self, response...))

            routes: list[RouteInfo] = {}
            for stub in overloads:
                if hasattr(stub, "_route_info"):
                    route_info: RouteInfo = stub._route_info
                    route_key = (route_info.method, route_info.path)
                    if route_key in cls.registry:
                        raise TypeError(
                            f"Duplicate route definition: {route_key} "
                            f"found on method '{name}'"
                        )
                    routes[route_key] = stub._route_info

            if not routes:
                continue

            caller = EndpointDescriptor(name, routes, overloads, member)
            setattr(cls, name, caller)
            cls.registry.update(routes)

    def get_route(self, method: str, path: str) -> RouteInfo:
        return self.registry[(method, path)]._route_info

    def request(
        self,
        method: Literal[
            "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"
        ],
        url: str,
        *,
        params: pydantic.BaseModel,
        json: pydantic.BaseModel | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        response = self.transport.request(
            method=method,
            url=url,
            params=params.model_dump(by_alias=True, exclude_none=True) if params else None,
            json=json.model_dump(by_alias=True, exclude_none=True) if json else None,
            headers=headers,
        )

        response.raise_for_status()
        return response

    async def __call__(
        self,
        method: str,
        path: str,
        *,
        params: pydantic.BaseModel,
        json: pydantic.BaseModel | None = None,
        headers: dict[str, str] | None = None
    ) -> ResponseT:
        stub = await self.registry[method, path]
        return await getattr(self, stub.__name__)(method, path, params, json, headers)

