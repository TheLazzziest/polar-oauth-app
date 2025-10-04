import inspect
import string
import tempfile
from collections.abc import Callable, Generator, Sequence
from types import FunctionType
from typing import (
    Annotated,
    cast,
    overload,
)

import httpx
from gpxpy import parse
from gpxpy.gpx import GPX
from pydantic import BaseModel, ConfigDict, validate_call
from tcxreader.tcxreader import TCXExercise, TCXReader

from .models import EndpointConfig, Exercise, ExerciseQueryParams, HttpMethStr
from .typing import EndpointArgT, EndpointCallable, HTTPClient


def _extract_path_args(path: str) -> Sequence[tuple[str, str | int | float]]:
    """Extracts path parameters and their types from a path string."""
    formatter = string.Formatter()
    params = []
    allowed_types = {"int", "str", "float"}

    for _, field_name, format_spec, _ in formatter.parse(path):
        if field_name:
            if format_spec not in allowed_types:
                raise ValueError(f"The type {format_spec} is not allowed")
            params.append((field_name, format_spec))

    return params


def endpoint(*configs: EndpointConfig) -> Callable[[Callable], EndpointCallable]:
    """
    A decorator to define an API endpoint method.

    It automatically handles path parameter formatting, query parameter
    construction, and response validation.

    Args:
        path: The URL path for the endpoint, with placeholders for path
              parameters (e.g., "/users/{user_id}").
        method: The HTTP method for the request (e.g., "GET", "POST").
        response_model: The Pydantic model to validate the response against.
    """
    overloads = []

    def decorator[R: httpx.Response, M: BaseModel](
        meth: Callable[[R], M],
    ) -> EndpointCallable:
        sig = inspect.signature(meth)

        for c in configs:
            model_fields = c.__class__.model_fields

            path_args = _extract_path_args(c.path)
            parameters = [
                inspect.Parameter(
                    "self",
                    inspect.Parameter.POSITIONAL_ONLY,
                    annotation=sig.parameters["self"].annotation,
                )
            ]

            for arg_name, annotation in path_args:
                parameters.append(
                    inspect.Parameter(
                        arg_name,
                        inspect.Parameter.POSITIONAL_ONLY,
                        annotation=annotation,
                    )
                )

            for field_name in {"query_model", "body_model"}:
                model_def = getattr(c, field_name)
                if not model_def:
                    continue
                parameters.append(
                    inspect.Parameter(
                        field_name,
                        inspect.Parameter.KEYWORD_ONLY,
                        annotation=model_def,
                    )
                )

            for field_name in {"method", "path", "headers"}:
                field_meta = model_fields[field_name]
                parameters.append(
                    inspect.Parameter(
                        field_name,
                        inspect.Parameter.KEYWORD_ONLY,
                        annotation=field_meta.annotation,
                        default=getattr(c, field_name),
                    )
                )

            parameters.append(
                inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD)
            )

            overload_signature = inspect.Signature(
                parameters, return_annotation=c.response_model
            )

            overloading_func = FunctionType(
                compile(
                    f"async def {meth.__name__}{str(overload_signature)}:...",
                    "<string>",
                    "exec",
                ),
                meth.__globals__,
                meth.__name__,
            )

            overloads.append(overload(overloading_func))

        @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
        async def wrapper(
            self: HTTPClient,
            /,
            *args: tuple[EndpointArgT],
            query_model: BaseModel,
            body_model: BaseModel,
            method: Annotated[str, HttpMethStr],
            path: str,
            headers: httpx.Headers,
            # **kwargs: P.kwargs,
        ):
            pass

        # Bind the provided arguments to the function's signature
        #     bound_args = sig.bind(
        #         self,
        #         method,
        #         path,
        #         query_param_model,
        #         body_model,
        #         response_model,
        #         **kwargs,
        #     )
        #     bound_args.apply_defaults()

        #     # Prepare path arguments
        #     formated_path = path
        #     query_params, body, kwargs = None, None, {}

        #     if arguments:
        #         formated_path = formated_path.format(**arguments)

        #     for _, param in bound_args.arguments.items():
        #         if query_param_model and isinstance(param, query_param_model):
        #             query_params = param
        #         elif body_model and isinstance(param, body_model):
        #             body = param
        #         else:
        #             kwargs[_] = param

        #     # Make the API call
        #     return func(
        #         await self._request(
        #             method,
        #             formated_path,
        #             params=query_params if query_params else None,
        #             body=body if body else None,
        #             **kwargs,
        #         ),
        #         response_model,
        #     )

        return cast(EndpointCallable, wrapper)

    return decorator


class BearerAuth(httpx.Auth):
    def __init__(self, token: str, token_type: str = "Bearer"):
        self.token = token
        self.token_type = token_type

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response]:
        request.headers["Authorization"] = f"{self.token_type} {self.token}"
        yield request


class PolarClient(HTTPClient[httpx.AsyncClient]):
    def __new__(cls, transport: httpx.AsyncClient):
        methods = inspect.getmembers(cls, inspect.ismethod)

        for name, method in methods:
            if name.startswith("_"):
                continue
            setattr(cls, name, method)

        return super().__new__(cls)

    def __init__(self, transport: httpx.AsyncClient):
        self.transport = transport
        assert self.transport.auth is not None, "OAuth client must have Bearer Auth set"

    async def request(
        self,
        method: Annotated[str, HttpMethStr],
        path: str,
        query: BaseModel | None = None,
        body: BaseModel | None = None,
        headers: httpx.Headers | None = None,
        **kwargs,
    ) -> httpx.Response:
        response = await self.transport.request(method, path, **kwargs)
        response.raise_for_status()
        return response

    async def call(
        self,
        method,
        path,
        *args,
        query_model: BaseModel | None = None,
        headers: httpx.Headers | None,
        body_model: BaseModel | None = None,
        **kwargs,
    ): ...

    @endpoint(
        EndpointConfig(
            method="GET",
            path="/v3/exercises",
            query_param_model=ExerciseQueryParams | None,
            response_model=list[Exercise],
        )
    )
    async def list_exercises(self, response: httpx.Response) -> list[Exercise]:
        """Fetches a list of exercises for the authenticated user.

        Args:
            response (httpx.Response): The HTTP response from the API.
        Returns:
            List[Exercise]: A list of Exercise models.
        """
        return [Exercise.model_validate(item) for item in response.json()]

    @endpoint(
        EndpointConfig(
            method="GET",
            path="/v3/exercises/{exercise_id:str}",
            query_param_model=ExerciseQueryParams | None,
            response_model=Exercise,
        ),
        EndpointConfig(
            method="GET",
            path="/v3/exercises/{exercise_id:str}/{format:str}",
            query_param_model=ExerciseQueryParams,
            response_model=GPX | TCXExercise,
        ),
    )
    async def get_exercise(
        self, response: httpx.Response
    ) -> Exercise | GPX | TCXExercise:
        """Fetches a specific exercise by ID for the authenticated user.

        Args:
            exercise_id (str): The ID of the exercise to fetch.
            format (str, optional): The format of the response
                ('gpx', 'tcx'). Defaults to 'json'.
        Returns:
            Exercise | GPX | TCXExercise:
                An Exercise model or GPX data depending on the requested format.
        """
        match response.headers["Content-Type"]:
            case "application/json":
                return Exercise.model_validate(response.json())
            case "application/gpx+xml" | "application/vnd.garmin.tcx+xml":
                return parse(response.text)
            case "application/octet-stream":  # Fit format
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                    return TCXReader().read(temp_file_path)
            case _:
                content_type = response.headers.get("Content-Type", "unknown")
                raise ValueError(f"Unsupported response content type: {content_type}")
