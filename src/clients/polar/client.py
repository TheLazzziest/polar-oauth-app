import tempfile
from collections.abc import Generator
from typing import Literal, cast, overload

import httpx
from gpxpy import parse
from gpxpy.gpx import GPX
from tcxreader.tcxreader import TCXExercise, TCXReader
from typing_extensions import TypeForm

from .models import Exercise, ExerciseQueryParams
from .base import RouteInfo, HTTPClient


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

    def __init__(self, transport):
        super().__init__(transport)

        if getattr(self.transport, "auth", None) is None:
            raise ValueError("OAuth client must have Bearer Auth set")

    @overload
    @RouteInfo(
        method="GET",
        path="/v3/exercises",
        params_model=ExerciseQueryParams,
        response_model=list[Exercise]
    )
    async def list_exercises(
        self,
        query_model: ExerciseQueryParams | None = None,
    ) -> list[Exercise]:...

    async def list_exercises(self, response: httpx.Response) -> list[Exercise]:
        """Fetches a list of exercises for the authenticated user.

        Args:
            response (httpx.Response): The HTTP response from the API.
        Returns:
            List[Exercise]: A list of Exercise models.
        """
        json_response = cast(list[dict], response.json())
        return [Exercise.model_validate(item) for item in json_response]

    @overload
    @RouteInfo(
        method="GET",
        path="/v3/exercises/{exercise_id:str}",
        params_model=ExerciseQueryParams,
        response_model=Exercise
    )
    async def get_exercise(
        self,
        exercise_id: str,
        query_model: ExerciseQueryParams | None = None,
    ) -> Exercise:...

    @overload
    @RouteInfo(
        method="GET",
        path="/v3/exercises/{exercise_id:str}/{format:str}",
        params_model=ExerciseQueryParams,
        response_model=GPX | TCXExercise,
    )
    async def get_exercise(
        self,
        exercise_id: str,
        format: Literal["gpx", "tcx"],
        query: ExerciseQueryParams | None = None,
    ) -> GPX | TCXExercise:...

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
