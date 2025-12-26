from pathlib import Path

from pydantic import UUID4, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class PolarOauthSettings(BaseSettings):
    client_id: UUID4 = Field(description="An OAuth2 client ID for a polar account")
    client_secret: UUID4 = Field(
        description="An OAuth2 client secret for a polar account"
    )
    scopes: dict[str, str] = Field(
        default={"accesslink.read_all": "Read exercise data"},
        description="The scopes to OAuth2 credentials",
    )
    authorization_url: HttpUrl = Field(
        default=HttpUrl("https://flow.polar.com/oauth2/authorization"),
        description="The URL to authorize a user",
    )
    access_token_url: HttpUrl = Field(
        default=HttpUrl("https://polarremote.com/v2/oauth2/token"),
        description="The URL to get an access token",
    )
    accesslink_url: HttpUrl = Field(
        default=HttpUrl("https://www.polaraccesslink.com"),
        description="The URL to access the Polar Access Link API",
    )

    model_config = SettingsConfigDict(env_prefix="oauth")


class ServerSettings(BaseSettings):
    debug: bool = Field(
        default=False, description="Whether to run the server in debug mode"
    )
    sqlite_path: Path | str = Field(
        default=":memory:", description="The path to the SQLite database file"
    )
    model_config = SettingsConfigDict(env_prefix="server")


class ApplicationSettings(BaseSettings):
    server: ServerSettings
    oauth: PolarOauthSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="polar_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        nested_model_default_partial_update=True,
        case_sensitive=True,
        extra="ignore",
        frozen=True,
    )


settings = ApplicationSettings()
