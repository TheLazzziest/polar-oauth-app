import tempfile
from typing import cast, overload

import httpx
from gpxpy import parse
from gpxpy.gpx import GPX
from tcxreader.tcxreader import TCXExercise, TCXReader

from src.clients.base.client import AsyncClient
from src.clients.base.contexts import ResponseContext
from src.clients.base.decorators import route
from src.clients.base.models import EndpointRequest, RouteMeta

from .contexts import ExerciseContext, ExerciseFormatContext, ListExercisesContext
from .models import Exercise


class PolarClient(AsyncClient):
    def __init__(self, transport):
        super().__init__(transport)

    async def send(self, request: EndpointRequest) -> httpx.Response:
        params = {}
        if request.params:
            params.update(
                request.params.model_dump(exclude_none=True, exclude_unset=True)
            )

        return await self.transport.request(
            request.method,
            request.url,
            params=params,
            headers=request.headers,
        )

    @overload
    @route(
        RouteMeta[list[Exercise]](
            method="GET",
            path="/v3/exercises",
            headers=httpx.Headers(
                {
                    "Accept": "application/json",
                }
            ),
        )
    )
    async def list_exercises(self, context: ListExercisesContext) -> list[Exercise]:
        """see: https://www.polar.com/accesslink-api/#list-exercises"""

    async def list_exercises(self, context: ResponseContext) -> list[Exercise]:
        """Fetches a list of exercises for the authenticated user.

        Args:
            response (httpx.Response): The HTTP response from the API.
        Returns:
            List[Exercise]: A list of Exercise models.
        """
        response = context.response
        json_response = cast(list[dict], response.json())
        return [Exercise.model_validate(item) for item in json_response]

    @overload
    @route(
        RouteMeta[Exercise](
            method="GET",
            path="/v3/exercises/{exercise_id:str}",
            headers=httpx.Headers(
                {
                    "Accept": "application/json",
                }
            ),
        )
    )
    async def get_exercise(self, context: ExerciseContext) -> Exercise: ...

    @overload
    @route(
        RouteMeta[GPX | TCXExercise](
            method="GET",
            path="/v3/exercises/{exercise_id:str}/{format:str}",
            headers=httpx.Headers(
                {
                    "Accept": "application/json",
                }
            ),
        )
    )
    async def get_exercise(
        self, context: ExerciseFormatContext
    ) -> GPX | TCXExercise: ...

    async def get_exercise(
        self, context: ResponseContext
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
        response = context.response
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
