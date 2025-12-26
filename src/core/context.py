from collections.abc import Generator
from dataclasses import dataclass
from typing import cast

import typer

from src.clients import polar


@dataclass
class PolarContext:
    client: polar.PolarClient


def parse_path_arg(arg: str) -> tuple[str, str]:
    key, value = arg.split("=")
    return key, value


def parse_query_param(arg: str) -> tuple[str, str]:
    key, value = arg.split("=")
    return key, value


def parse_header(arg: str) -> tuple[str, str]:
    key, value = arg.split("=")
    return key, value


def complete_path(ctx: typer.Context, path: str) -> Generator[str]:
    client = cast(PolarContext, ctx.obj).client
    for _, path in client.registry.keys():
        if path.startswith(path):
            yield path
    yield path


def complete_args(ctx: typer.Context, arg: str) -> Generator[str]:
    # client = cast(PolarContext, ctx.obj).client

    yield arg


def complete_query_param(ctx: typer.Context, query: str) -> Generator[str]:
    # client = cast(PolarContext, ctx.obj).client

    yield query
