ARG EXPOSED_PORT=8000

FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY uv.lock pyproject.toml /app/
COPY src/ /app/src

WORKDIR /app

RUN uv sync --locked

EXPOSE $EXPOSED_PORT

ENTRYPOINT [ "uv", "run", "uvicorn", "src.web:app" ]
