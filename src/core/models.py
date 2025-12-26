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
