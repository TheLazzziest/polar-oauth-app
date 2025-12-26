import sqlite3


async def apply_migrations(db: sqlite3.Connection):
    db.execute(
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


async def revert_migrations(db: sqlite3.Connection):
    db.execute("DROP TABLE IF EXISTS tokens")
