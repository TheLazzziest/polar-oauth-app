from typing import Literal

from pydantic import Field

from src.clients.base.contexts import RequestContext
from src.clients.polar.models import ExerciseQueryParams


class ListExercisesContext(RequestContext[ExerciseQueryParams]):
    samples: bool = False
    zones: bool = False
    route: bool = False


class ExerciseContext(RequestContext[ExerciseQueryParams]):
    exercise_id: str = Field(..., description="The ID of the exercise")


class ExerciseFormatContext(RequestContext[ExerciseQueryParams]):
    exercise_id: str = Field(..., description="The ID of the exercise")
    format: Literal["gpx", "tcx"] = Field(
        ..., description="The format of the exercise data"
    )
