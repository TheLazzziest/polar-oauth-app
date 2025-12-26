import inspect
from abc import ABC
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from functools import wraps
from string import Template
from typing import Any

from .contexts import RequestContext, ResponseContext
from .models import EndpointRequest, RouteMeta
from .protocols import AsyncClientProtocol


class EndpointCommand[ReturnType](ABC):
    """
    A descriptor which builds a request command.
    The command is delegated to the attached client for execution.
    The response is delegated back
    """

    def __init__(
        self, route_info: RouteMeta, stub: Callable, response_handler: Callable
    ):
        self.stub = stub
        self._route_info = route_info
        self._original_handler = response_handler
        wraps(stub)(self)

    def __get__(
        self,
        instance: AsyncClientProtocol,
        owner: type[AsyncClientProtocol],
    ) -> Callable[..., Awaitable[Any]]:
        """
        Binds the method to the client instance and returns the dispatcher.
        """
        if instance is None:
            return self

        # Return a wrapper that passes the instance to __call__
        @wraps(self.stub)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self(instance, *args, **kwargs)

        return wrapper

    def build_request(self, arguments: OrderedDict) -> EndpointRequest:
        context: RequestContext = arguments.pop("context")
        route_info = self._route_info

        # process path arguments
        path_args = {}
        path_templ = Template(route_info.path)
        for field_name, field_spec in context.model_fields.items():
            if field_spec.is_required() or field_spec.annotation in (
                str,
                int,
                float,
                bool,
            ):
                if (
                    f"{{{field_name}}}" in route_info.path
                    or f"{{{field_name}:" in route_info.path
                ):
                    path_args[field_name] = getattr(context, field_name)

        path = route_info.path
        if path_args:
            try:
                path = path_templ.substitute(**path_args)
            except KeyError as e:
                raise TypeError(
                    f"Missing required path parameter {e} for route: {route_info.path}"
                )

        # Process query parameters
        params = route_info.params
        complement = context.params
        if params and complement:
            params.model_copy(update=complement)
        elif complement:
            params = complement

        request = EndpointRequest(
            method=route_info.method,
            url=path,
            headers=route_info.headers,
            params=params,
            **arguments,
        )
        return request

    def process_request(
        self, instance: AsyncClientProtocol, *args: Any, **kwargs: Any
    ) -> EndpointRequest:
        """Decorator to process the request and return the processed request."""
        bound_args = inspect.signature(self.stub).bind(instance, *args, **kwargs)
        bound_args.apply_defaults()
        call_args = bound_args.arguments
        call_args.pop("self")
        request = self.build_request(call_args)
        return request

    async def __call__(
        self, instance: AsyncClientProtocol, *args: Any, **kwargs: Any
    ) -> ReturnType:
        request = self.process_request(instance, *args, **kwargs)
        response = await instance.send(request)
        response.raise_for_status()
        return await self._original_handler(
            instance, ResponseContext(response=response)
        )
