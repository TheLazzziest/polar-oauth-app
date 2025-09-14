from collections.abc import Sequence

from authlib.integrations.httpx_client import AsyncOAuth2Client
from pydantic import HttpUrl

from src.clients.polar.models import TokenModel


class PolarClient:
    def __init__(self, oauth_client: AsyncOAuth2Client):
        self.oauth_client = oauth_client

    def create_authorization_url(
        self,
        authorization_url: HttpUrl,
        redirect_uri: HttpUrl,
        state: str,
        scope: Sequence[str] | None = None,
    ) -> tuple[str, str]:
        return self.oauth_client.create_authorization_url(
            str(authorization_url),
            redirect_uri=str(redirect_uri),
            state=state,
            response_type="code",
            scope=scope,
        )

    async def fetch_access_token(
        self,
        access_token_url: HttpUrl,
        authorization_response: HttpUrl,
        redirect_uri: HttpUrl,
    ) -> TokenModel:
        token_data = await self.oauth_client.fetch_token(
            str(access_token_url),
            authorization_response=str(authorization_response),
            grant_type="authorization_code",
            redirect_uri=str(redirect_uri),
        )
        return TokenModel.model_validate(token_data)
