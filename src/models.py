from datetime import datetime

from pydantic import BaseModel, PositiveInt


class TokenModel(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user_id: PositiveInt
    updated_at: datetime
    created_at: datetime
