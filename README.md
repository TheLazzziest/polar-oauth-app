# Polar CLI

[![Polar Accesslink](https://img.shields.io/badge/Polar_Accesslink-blue)](https://github.com/polarisai/polar-accesslink)
[![Docker](https://img.shields.io/badge/Docker-v20.10.12-blue)](https://docs.docker.com/engine/install/)
[![Docker Pulls](https://img.shields.io/docker/pulls/thelazzziest/polar-oauth-app)](https://hub.docker.com/r/thelazzziest/polar-oauth-app)
[![ngrok](https://img.shields.io/badge/ngrok-v3.1.0-blue)](https://ngrok.com/download)
[![Python](https://img.shields.io/badge/Python-v3.13-blue)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/SQLite-v3.39.2-blue)](https://www.sqlite.org/download.html)

## Prerequisites

1. You must have a [Polar](https://www.polar.com/welcome/) account.
2. You must have an oauth2 application registered on [Polar Admin](https://admin.polaraccesslink.com) page.

## Quickstart

1. Create .env file and fill it:
```bash
cp example.env .env
```
2. Run the application:
```bash
uv run uvicorn src.web:app --reload --host 0.0.0.0 --port 8000
```
3. Ready

### Docker flow

1. Run the Docker container:
```bash
docker run -d -p 8000:8000 --env-file .env thelazzziest/polar-oauth-app --host 0.0.0.0 --port 8000 --log-level debug
```

### Local flow

3. Create the virtual environment:
```bash
uv sync
```
4. Activate the virtual environment:
```bash
source venv/bin/activate
```
5. Run the application:
```bash
uvicorn src.web:app --reload --host localhost --port 8000 --log-level debug
```

## Resources

* [FastAPI](https://fastapi.tiangolo.com/)
* [Authlib](https://docs.authlib.org/en/latest/)
* [Accesslink](https://www.polar.com/accesslink-api/)
