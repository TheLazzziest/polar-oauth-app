import inspect
from abc import ABC
from collections.abc import Callable
from typing import ClassVar, cast, get_overloads

from .descriptors import EndpointCommand
from .fields import PathTemplate
from .models import RouteMeta
from .protocols import Routable
from .types import HTTPMeth, RouteKey


class Transportable[ClientT](ABC):
    transport: ClientT

    def __init__(self, transport: ClientT) -> None:
        self.transport = transport


class Discoverable(ABC):
    registry: ClassVar[dict[RouteKey, EndpointCommand]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        for name, member in inspect.getmembers(cls):
            if not (callable(member) and inspect.iscoroutinefunction(member)):
                continue

            overloads: list[Routable] = cast(list[Routable], get_overloads(member))
            if not overloads:
                continue

            # --- We found an endpoint ---
            # 'member' is the *real implementation* (e.g., def list_exercises(self...))

            for stub in overloads:
                try:
                    route_info: RouteMeta = stub._route_info
                    route_key = (route_info.method, cast(PathTemplate, route_info.path))
                except AttributeError:
                    continue

                if route_key in cls.registry:
                    endpoint_name = cls.registry[route_key].__name__
                    stub_name = stub.__name__
                    raise TypeError(
                        f"Duplicate route definition: {route_key} "
                        f"found on method '{name}'."
                        f"Previous: {endpoint_name}, New: {stub_name}"
                    )

                # Create a descriptor for each stub and replace the original method
                # The last one will win, but they all point to the same implementation
                descriptor = route_info.build_command(cast(Callable, stub), member)
                setattr(cls, name, descriptor)

                # Register the route for dynamic calls
                cls.registry[route_key] = descriptor

    def find(self, method: HTTPMeth, path: PathTemplate) -> RouteMeta:
        return self.registry[(method, path)]._route_info

    def discover(self, method: HTTPMeth, path: PathTemplate) -> EndpointCommand:
        route_key = (method, path)
        if route_key not in self.registry:
            raise ValueError(f"Route {route_key} not found")
        return self.registry[route_key]
