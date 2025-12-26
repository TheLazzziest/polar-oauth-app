import asyncio
import json
from functools import wraps
from pathlib import Path
from typing import Annotated

import typer
from authlib.integrations.httpx_client import AsyncOAuth2Client

from src.clients import polar
from src.core.context import (
    PolarContext,
    complete_args,
    complete_path,
    complete_query_param,
    parse_header,
    parse_path_arg,
    parse_query_param,
)
from src.core.settings import settings

polar_api = typer.Typer()


@polar_api.callback()
def lifecycle(ctx: typer.Context, token: str):
    token = json.load(Path(token).open())

    ctx.obj = PolarContext(
        client=polar.PolarClient(
            AsyncOAuth2Client(
                client_id=str(settings.oauth.client_id),
                client_secret=str(settings.oauth.client_secret),
                base_url=str(settings.oauth.accesslink_url),
                token=token,
            )
        )
    )


@polar_api.command()
@lambda f: wraps(f)(lambda *a, **kw: asyncio.run(f(*a, **kw)))
async def call(
    ctx: typer.Context,
    action: Annotated[
        str,
        typer.Argument(..., help="API action to call", autocompletion=complete_path),
    ],
    args: Annotated[
        list[tuple[str, str]] | None,
        typer.Option(
            "arg",
            parser=parse_path_arg,
            help="Path arguments parameters for the request.",
            autocompletion=complete_args,
        ),
    ] = None,
    params: Annotated[
        list[tuple[str, str]] | None,
        typer.Option(
            "param",
            parser=parse_query_param,
            help="Pass query parameters for the request",
            autocompletion=complete_query_param,
        ),
    ] = None,
    headers: Annotated[
        list[tuple[str, str]] | None,
        typer.Option(
            "header",
            parser=parse_header,
            help="Pass headers for the request",
        ),
    ] = None,
):
    # client = cast(PolarContext, ctx.obj).client
    typer.echo("Run `polar-cli api call`")


app = typer.Typer(name="polar-cli")
app.add_typer(polar_api, name="api", help="Interact with the Polar API.")

if __name__ == "__main__":
    app()
