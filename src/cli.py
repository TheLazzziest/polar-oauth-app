import asyncio
from functools import wraps
from typing import Annotated

import typer
from httpx import AsyncClient

from src.clients import polar
from src.context import PolarContext, complete_args, complete_path, complete_query_param
from src.settings import settings

polar_api = typer.Typer()


@polar_api.callback()
def lifecycle(ctx: typer.Context, token: str):
    ctx.obj = PolarContext(
        client=polar.PolarClient(
            AsyncClient(
                base_url=str(settings.oauth.accesslink_url),
                auth=polar.BearerAuth(token),
            )
        )
    )


@polar_api.command()
@lambda f: wraps(f)(lambda *a, **kw: asyncio.run(f(*a, **kw)))
async def call(
    ctx: typer.Context,
    method: Annotated[
        str,
        typer.Argument(
            ...,
            help="HTTP method to use.",
        ),
    ],
    path: Annotated[
        str,
        typer.Argument(..., help="API endpoint path.", autocompletion=complete_path),
    ],
    args: Annotated[
        tuple[str, str],
        typer.Option(
            None,
            help="Path arguments parameters for the request.",
            autocompletion=complete_args,
        ),
    ]
    | None,
    params: Annotated[
        tuple[str, str],
        typer.Option(
            None,
            help="Pass query parameters for the request",
            autocompletion=complete_query_param,
        ),
    ]
    | None,
):
    # client = cast(PolarContext, ctx.obj).client
    # await client.call(method=method, path=path, *args, **params)
    typer.echo("Run `polar-cli api call`")


app = typer.Typer(name="polar-cli")
app.add_typer(polar_api, name="api", help="Interact with the Polar API.")

if __name__ == "__main__":
    app()
