from collections.abc import Generator
from dataclasses import dataclass

import typer

from src.clients import polar


@dataclass
class PolarContext:
    client: polar.PolarClient


def complete_path(ctx: typer.Context, path: str) -> Generator[str]:
    # client = cast(PolarContext, ctx.obj).client

    yield path


def complete_args(ctx: typer.Context, arg: str) -> Generator[str]:
    # client = cast(PolarContext, ctx.obj).client

    yield arg


def complete_query_param(ctx: typer.Context, query: str) -> Generator[str]:
    # client = cast(PolarContext, ctx.obj).client

    yield query
