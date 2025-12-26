from collections.abc import Callable
from typing import cast

from .models import RouteMeta
from .protocols import Routable


def route(meta: RouteMeta) -> Callable[[Callable], Routable]:
    def decorator(func: Callable) -> Routable:
        if not hasattr(func, "_route_info"):
            setattr(func, "_route_info", meta)
        return cast(Routable, func)

    return decorator
