import datetime
from abc import ABC
from typing import Annotated, Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

HttpMethStr = StringConstraints(
    strip_whitespace=True,
    to_upper=True,
    strict=True,
    pattern=r"^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)$",
)


class EndpointConfig(BaseModel):
    """Holds the configuration for a single API endpoint."""

    method: Annotated[str, HttpMethStr]
    path: str
    headers: httpx.Headers | None = None
    query_model: type[BaseModel] | None = None
    body_model: type[BaseModel] | None = None
    response_model: Any | None = None
    help_text: str | None = Field(None, description="An endpoint description")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DateModel(BaseModel, ABC):
    date: datetime.date = Field(
        ..., alias="date", description="Date of the activity in YYYY-MM-DD format."
    )

    @field_validator("date", mode="before")
    def parse_date(cls, value):
        if isinstance(value, str):
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        return value


class TrainingLoad(BaseModel):
    """Represents the training load data for an exercise."""

    training_load: float = Field(..., description="Numerical value of training load.")
    recovery_time: int = Field(..., description="Recovery time in seconds.")


class HeartRateZone(BaseModel):
    """Represents a heart rate zone with min and max heart rate."""

    index: int = Field(..., description="Index of the heart rate zone.")
    name: str = Field(
        ..., description="Name of the heart rate zone (e.g., 'FATBURN', 'CARB')."
    )
    in_zone: int = Field(..., description="Time spent in the zone in seconds.")
    max_heart_rate: int = Field(
        ..., description="Maximum heart rate in the zone in beats per minute."
    )
    min_heart_rate: int = Field(
        ..., description="Minimum heart rate in the zone in beats per minute."
    )


class HeartRate(BaseModel):
    """Represents the heart rate data for an exercise."""

    average: int | None = Field(
        None, description="Average heart rate in beats per minute."
    )
    maximum: int | None = Field(
        None, description="Maximum heart rate in beats per minute."
    )
    zones: list[HeartRateZone] | None = Field(
        None, description="List of heart rate zones."
    )


class ExerciseQueryParams(BaseModel):
    """Query parameters for the exercise endpoint."""

    samples: bool | None = Field(
        None, description="Return all sample data for this exercise."
    )
    zones: bool | None = Field(
        None, description="Return all heart rate zones for this exercise."
    )
    route: bool | None = Field(
        None, description="Return the route data for this exercise."
    )


class Exercise(BaseModel):
    """Represents a single exercise data set."""

    polar_user: str = Field(..., description="The ID of the Polar user.")
    start_time: datetime.datetime = Field(
        ..., description="Start time of the exercise in ISO 8601 format."
    )
    start_time_utc_offset: int = Field(
        ..., description="Start time UTC offset in seconds."
    )
    duration: str = Field(
        ..., description="Duration of the exercise in ISO 8601 format."
    )
    distance: float = Field(..., description="Distance in meters.")
    calories: int = Field(..., description="Calories burned in kcal.")
    device: str = Field(..., description="Polar device model used for the exercise.")
    has_route: bool = Field(
        ..., description="Boolean indicating if the exercise has GPS route data."
    )
    has_manual_lap: bool = Field(
        ..., description="Boolean indicating if the exercise has manual laps."
    )
    sport: str = Field(
        ..., description="Sport of the exercise (e.g., 'RUNNING', 'CYCLING')."
    )
    training_load: TrainingLoad | None = Field(
        None, description="Training load data for the exercise."
    )
    heart_rate: HeartRate | None = Field(
        None, description="Heart rate data for the exercise."
    )

    @field_validator("start_time", mode="before")
    def parse_start_time(cls, value):
        if isinstance(value, str):
            # Parse datetime string with timezone
            return datetime.datetime.fromisoformat(value)
        return value


class ActivitySummary(DateModel):
    """Represents a user's activity summary for a single day."""

    polar_user: str = Field(..., description="The ID of the Polar user.")
    active_calories: int = Field(..., description="Active calories burned in kcal.")
    inactivity_time: int = Field(..., description="Total inactivity time in seconds.")
    activity_steps: int = Field(..., description="Total number of steps taken.")
    activity_distance: float = Field(
        ..., description="Total activity distance in meters."
    )
    training_calories: int = Field(
        ..., description="Calories burned during training in kcal."
    )
    training_time: int = Field(..., description="Time spent training in seconds.")
    low_activity_time: int = Field(
        ..., description="Time of low-intensity activity in seconds."
    )
    medium_activity_time: int = Field(
        ..., description="Time of medium-intensity activity in seconds."
    )
    high_activity_time: int = Field(
        ..., description="Time of high-intensity activity in seconds."
    )


class NightlyRecharge(DateModel):
    """Represents a user's nightly recharge data."""

    polar_user: str = Field(..., description="The ID of the Polar user.")
    autonomic_nervous_system_recovery: str = Field(
        ..., description="Autonomic nervous system recovery status."
    )
    sleep_charge: str = Field(..., description="Sleep charge status.")
    recharge_status: str = Field(..., description="Overall nightly recharge status.")
