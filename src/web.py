import asyncio
import sqlite3
from contextlib import asynccontextmanager
from http import HTTPStatus
from operator import itemgetter
from typing import Annotated

from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    Request,
)
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlowAuthorizationCode, OAuthFlows
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2
from pydantic.networks import HttpUrl

from src.clients.polar import PolarClient
from src.migrations import apply_migrations
from src.models import TokenModel as PolarAppTokenModel
from src.settings import ApplicationSettings, settings

oauth2_scheme = OAuth2(
    flows=OAuthFlows(
        authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl="/oauth/authorize",
            tokenUrl="/oauth/token",
            scopes=settings.oauth.scopes,
        )
    ),
    scheme_name="Polar OAuth2",
)


@asynccontextmanager
async def configure(app: FastAPI):
    app.state.settings = settings
    app.state.polar = PolarClient(
        oauth_client=AsyncOAuth2Client(
            client_id=str(app.state.settings.oauth.client_id),
            client_secret=str(app.state.settings.oauth.client_secret),
        )
    )
    app.state.db = sqlite3.connect(
        settings.server.sqlite_path, autocommit=True, check_same_thread=False
    )
    app.state.db.row_factory = sqlite3.Row
    await apply_migrations(asyncio.get_event_loop(), app.state.db)
    yield
    app.state.db.close()


def provision_settings(request: Request) -> ApplicationSettings:
    return request.app.state.settings


def provision_polar(request: Request) -> PolarClient:
    return request.app.state.polar


def provision_database(request: Request) -> sqlite3.Connection:
    return request.app.state.db


healthcheck_router = APIRouter(prefix="/health", tags=["Health"])
router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/authorize", name="oauth_authorize")
def login(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(provision_database)],
    settings: Annotated[ApplicationSettings, Depends(provision_settings)],
    client: Annotated[PolarClient, Depends(provision_polar)],
) -> RedirectResponse:
    state, client_id, scope = itemgetter("state", "client_id", "scope")(
        request.query_params
    )

    conn.execute(
        """
        INSERT INTO tokens (client_id, session_id) VALUES (?, ?)
        """,
        (str(client_id), state),
    )

    if not scope:
        scope = list(settings.oauth.scopes.keys())
    elif isinstance(scope, str):
        scope = [scope]

    # Create the authorization URL
    authorization_url, state = client.create_authorization_url(
        settings.oauth.authorization_url,
        HttpUrl(str(request.url_for("oauth_callback"))),
        state,  # Pass the generated state
        scope=scope,
    )

    return RedirectResponse(authorization_url, headers=request.headers)


@router.get("/callback", name="oauth_callback")
async def callback(
    request: Request,
    client: Annotated[PolarClient, Depends(provision_polar)],
    conn: Annotated[sqlite3.Connection, Depends(provision_database)],
    settings: Annotated[ApplicationSettings, Depends(provision_settings)],
) -> RedirectResponse:
    """
    Handles the OAuth2 callback from Polar
    to exchange the authorization code for an access token.
    """

    code, state = itemgetter("code", "state")(request.query_params)

    if not code or not state:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Missing code or state in callback",
        )

    # Retrieve the temporary user email associated with this state
    target_client = conn.execute(
        """
        SELECT client_id FROM tokens WHERE session_id = ?
        """,
        (state,),
    ).fetchone()

    if not target_client:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Invalid OAuth state"
        )

    token_model = await client.fetch_access_token(
        settings.oauth.access_token_url,
        HttpUrl(str(request.url)),
        HttpUrl(str(request.url_for("oauth_callback"))),
    )

    # Update the token entry for the specific temporary user email
    conn.execute(
        """
        UPDATE tokens
        SET
            user_id = ?,
            access_token = ?,
            token_type = ?,
            expires_at = ?,
            code = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
        """,
        (
            token_model.x_user_id,
            token_model.access_token,
            token_model.token_type,
            token_model.expires_at,
            code,
            state,
        ),
    )

    redirect_url = f"/docs/oauth2-redirect#state={state}&code={code}"
    return RedirectResponse(url=redirect_url)


@router.post("/token", name="oauth_token", response_model=PolarAppTokenModel)
async def issue_token(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(provision_database)],
) -> PolarAppTokenModel:
    """Implements the token endpoint for OAuth2 token exchange."""

    form_data = await request.form()
    code = form_data["code"]

    token_data = conn.execute(
        """
        SELECT
            user_id,
            access_token,
            token_type,
            expires_at,
            updated_at,
            created_at
        FROM tokens
        WHERE code = ?
        """,
        (code,),
    ).fetchone()

    if not token_data:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Token not found for user"
        )

    return PolarAppTokenModel.model_validate(
        {key: token_data[key] for key in token_data.keys()},
    )


@router.get("/token/fetch", name="oauth_fetch_token", response_model=PolarAppTokenModel)
async def fetch_token(
    conn: Annotated[sqlite3.Connection, Depends(provision_database)],
    authorization: Annotated[str, Depends(oauth2_scheme)],
) -> PolarAppTokenModel:
    parts = authorization.split(" ")
    if len(parts) != 2:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token_type, token = parts

    token_data = conn.execute(
        """
            user_id,
            access_token,
            token_type,
        (token, token_type),
            updated_at,
            created_at
        FROM tokens
        WHERE access_token = ? AND token_type = ?
        """,
        (token, token_type.lower()),
    ).fetchone()

    if not token_data:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Token not found for user"
        )

    return PolarAppTokenModel.model_validate(
        {key: token_data[key] for key in token_data.keys()},
    )


@healthcheck_router.get("/check", name="healthcheck")
async def healthcheck() -> dict:
    return {"status": "ok"}


app = FastAPI(
    title="Polar OAuth2 App",
    debug=settings.server.debug,
    description="A web server for providing authentication capabilities",
    version="0.1.0",
    lifespan=configure,
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "clientId": settings.oauth.client_id,
        "clientSecret": settings.oauth.client_secret,
        "useBasicAuthenticationWithAccessCodeGrant": True,
        "appName": "Polar API App",
    },
)
for r in (healthcheck_router, router):
    app.include_router(r)
