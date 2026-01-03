from abc import ABC
from datetime import datetime

from pydantic import BaseModel, Field, PositiveInt


class TemporalBaseModel(BaseModel, ABC):
    created_at: datetime | None = Field(
        None, description="Timestamp when the record was created."
    )
    updated_at: datetime | None = Field(
        None, description="Timestamp when the record was last updated."
    )


class OAuth2TokenModel(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    x_user_id: PositiveInt = Field(..., alias="user_id")


class TokenModel(OAuth2TokenModel, TemporalBaseModel):
    """Represents an OAuth2 token with user association and timestamps."""


class UserExtraInfoModel(BaseModel):
    """Represents extra information about a user."""

    value: str | int | float | bool
    index: int
    name: str


class UserModel(BaseModel):
    polar_user_id: PositiveInt = Field(..., alias="polar-user-id")
    member_id: PositiveInt = Field(..., alias="member-id")
    registration_date: datetime = Field(
        ...,
        description="Timestamp when the user was registered.",
        alias="registration-date",
    )
    first_name: str = Field(
        ..., description="First name of the user.", alias="first-name"
    )
    last_name: str = Field(..., description="Last name of the user.", alias="last-name")
    birth_date: datetime = Field(
        ..., description="Timestamp when the user was born.", alias="birthdate"
    )
    gender: str = Field(..., description="Gender of the user.")
    weight: float = Field(..., description="Weight of the user.")
    height: float = Field(..., description="Height of the user.")
    extra: list[UserExtraInfoModel] | None = Field(
        None, description="Extra information about the user."
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
