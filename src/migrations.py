import asyncio
import sqlite3


async def apply_migrations(loop: asyncio.AbstractEventLoop, db: sqlite3.Connection):
    await loop.run_in_executor(
        None,
        db.execute,
        """
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY,
            client_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            code TEXT,
            user_id INTEGER,
            access_token TEXT,
            token_type TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    )


async def revert_migrations(loop: asyncio.AbstractEventLoop, db: sqlite3.Connection):
    await loop.run_in_executor(None, db.execute, "DROP TABLE IF EXISTS tokens")
